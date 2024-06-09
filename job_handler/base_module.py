import copy
from datetime import datetime, timedelta

import passwords
from common_workspace import queues
from shared_models.message import Message
from shared_models.job import Job
from shared_tools.custom_exceptions import *
from shared_tools.logger import log
from shared_tools.word_tools import check_time_validity, check_date_validity


class Module:
    def __init__(self, job: Job):
        self.job = job
        log(self.job.job_id, f"Module Created")

    @property
    def is_master(self):
        return self.job.chat_id == passwords.telegram_chat_id

    def check_index(self) -> int:
        val = len(self.job.collection)
        log(self.job.job_id, f"Collection has {val} units.")
        return val

    def get_index(self, index) -> str:
        val = self.job.collection[index]
        log(self.job.job_id, f"Return from collection {val} from index {index}.")
        return val

    def check_value(self, index: int = 0, replace_str: str = "",
                    check_int: bool = False, check_float: bool = False,
                    check_date: bool = False,
                    check_time: bool = False,
                    check_list=None,
                    default: str = "",
                    option_list=None,
                    description: str = "",
                    no_recover: bool = False,
                    manual_option: bool = False) -> (bool, str):

        if sum([check_int, check_float, check_date, check_time]) > 1:
            raise InvalidParameterException("Contradicting check items are selected")

        success = True

        if option_list is None:
            option_list = [] if check_list is None else check_list

        if len(self.job.collection) <= index:
            if default != "" and default is not None:
                value = default
                self.job.collect(default, index)
                log(self.job.job_id, f"Index not available. Default used")
            else:
                success = False
                value = ""
                log(self.job.job_id, f"Index not available and no default")
        else:
            col = self.job.collection

            if index < 0:
                try:
                    value = " ".join([str(ele) for ele in col])
                except IndexError:
                    success = False
                    value = ""
                    log(self.job.job_id, f"Unexpected index fail", log_type="warn")
            else:
                try:
                    value = col[index]
                    log(self.job.job_id, f"Checking {value} for errors.")
                except IndexError:
                    success = False
                    value = ""
                    log(self.job.job_id, f"Unexpected index fail", log_type="warn")

        if success and value == "":
            if default != "":
                value = default
                log(self.job.job_id, f"No message available. Default used")
            else:
                success = False
                log(self.job.job_id, f"No message available and no default")

        if success and replace_str != "" and replace_str in value:
            value = value.replace(replace_str, "").strip()

        if success and check_int:
            try:
                int(value)
            except ValueError:
                success = False
                log(self.job.job_id, f"Unable to convert to int")

        if success and check_float:
            try:
                float(value)
            except ValueError:
                success = False
                log(self.job.job_id, f"Unable to convert to float")

        if success and check_list is not None:
            if value not in check_list:
                success = False
                log(self.job.job_id, f"Expected item not in list")

        if success and check_date and value.lower() == "yesterday":
            value = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

        if success and check_date and value.lower() == "today":
            value = datetime.now().strftime('%Y-%m-%d')

        if success and check_date and value.lower() == "tomorrow":
            value = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')

        if success and check_date:
            success, value = check_date_validity(self.job.job_id, value)

        if success and check_time:
            success, value = check_time_validity(self.job.job_id, value)

        # If anything failed
        if (not success) and (not no_recover):
            get_manual = check_int or check_float or check_date or check_time or manual_option

            send_val = f"Please enter the {description if description != '' else 'value'}" \
                       f"{' in ' if replace_str != '' else ''}{replace_str}" \
                       f"{' from the options below' if option_list else ''}."

            if option_list:
                msg = Message(send_string=send_val, job=self.job)

                bpr = 1 if sum([len(string) for string in option_list])/len(option_list) > 20 else 3

                msg.keyboard_extractor(function=self.job.function,
                                       index=index, options=option_list, bpr=bpr,
                                       add_cancel=True, add_other=get_manual, reply_to=self.job.reply_to,
                                       collection=self.job.collection)
                self.send_message(message=msg)
            else:
                self.send_message(message=Message(send_string=send_val + "\nSend /cancel to stop waiting.",
                                                  job=self.job,
                                                  get_input=True,
                                                  index=index))
        return success, value

    def send_message(self, message: Message, channel=None):
        if channel is not None and channel != self.job.channel:
            message_temp = copy.deepcopy(message)
            message_temp.group = None
            message.this_telepot_account = channel
            message.channel = channel
            self.__send_message(message_temp)
            self.__send_message(message)

        else:
            self.__send_message(message)

    def __send_message(self, message: Message):
        message.job = self.job
        queues.message_q.put(message)
        log(job_id=self.job.job_id, msg="Message added to Queue.")

    def send_admin(self, message: Message):
        message.send_to_master()
        self.send_message(message=message)
