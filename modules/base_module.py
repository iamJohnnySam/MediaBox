from datetime import datetime, timedelta

import global_variables
from communication.channels import channels
from communication.message import Message
from brains import message_queue
from brains.job import Job
from tools.custom_exceptions import *
from tools.logger import log


class Module:
    def __init__(self, job: Job):
        self._job = job
        log(self._job.job_id, f"Module Created")

    def check_index(self) -> int:
        val = len(self._job.collection)
        log(self._job.job_id, f"Collection has {val} units.")
        return val

    def get_index(self, index) -> str:
        val = self._job.collection[index]
        log(self._job.job_id, f"Return from collection {val} from index {index}.")
        return val

    def check_value(self, index: int = 0, replace_str: str = "",
                    check_int: bool = False, check_float: bool = False,
                    check_date: bool = False,
                    check_time: bool = False,
                    check_list=None,
                    default: str = "",
                    option_list=None,
                    description: str = "",
                    no_recover: bool = False) -> (bool, str):

        if sum([check_int, check_float, check_date, check_time]) > 1:
            raise InvalidParameterException("Contradicting check items are selected")

        success = True
        no_save = (index <= 0)
        no_save = no_save or (len(self._job.collection) == 1 and self._job.collection[0] != "")

        if option_list is None:
            option_list = [] if check_list is None else check_list

        if len(self._job.collection) <= index:
            if default != "":
                value = default
                self._job.collect(default, index)
                log(self._job.job_id, f"Index not available. Default used")
            else:
                success = False
                value = ""
                log(self._job.job_id, f"Index not available and no default")
        else:
            col = self._job.collection

            if index < 0:
                try:
                    value = " ".join([str(ele) for ele in col])
                except IndexError:
                    success = False
                    value = ""
                    log(self._job.job_id, f"Unexpected index fail", log_type="warn")
            else:
                try:
                    value = col[index]
                    log(self._job.job_id, f"Checking {value} for errors.")
                except IndexError:
                    success = False
                    value = ""
                    log(self._job.job_id, f"Unexpected index fail", log_type="warn")

        if success and value == "":
            if default != "":
                value = default
                log(self._job.job_id, f"No message available. Default used")
            else:
                success = False
                log(self._job.job_id, f"No message available and no default")

        # if success and not check_time and not check_date and " " in value:
        #     value = value.split(" ")[0].strip()

        if success and replace_str != "" and replace_str in value:
            value = value.replace(replace_str, "").strip()

        if success and check_int:
            try:
                int(value)
            except ValueError:
                success = False
                log(self._job.job_id, f"Unable to convert to int")

        if success and check_float:
            try:
                float(value)
            except ValueError:
                success = False
                log(self._job.job_id, f"Unable to convert to float")

        if success and check_list is not None:
            if value not in check_list:
                success = False
                log(self._job.job_id, f"Expected item not in list")

        if success and check_date and value.lower() == "yesterday":
            value = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

        if success and check_date and value.lower() == "tomorrow":
            value = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')

        if success and check_date:
            date_formats = global_variables.date_formats
            for date_format in date_formats:
                try:
                    date_obj = datetime.strptime(value, date_format)
                    if '%Y' not in value:
                        date_obj = date_obj.replace(year=datetime.now().year)
                    value = date_obj.strftime('%Y-%m-%d')
                    success = True
                    log(self._job.job_id, f"Date format accepted {str(value)} for {date_format}")
                    break
                except ValueError:
                    success = False
                    log(self._job.job_id, f"Date format mismatch {str(value)} for {date_format}")

        if success and check_time:
            time_formats = global_variables.time_formats
            for time_format in time_formats:
                try:
                    time_obj = datetime.strptime(value, time_format).time()
                    value = time_obj.strftime("%H:%M:%S")
                    success = True
                    log(self._job.job_id, f"Time format accepted {str(value)} for {time_format}")
                    break
                except ValueError:
                    success = False
                    log(self._job.job_id, f"Time format mismatch {str(value)} for {time_format}")

        # If anything failed
        if (not success) and (not no_recover):
            if not (option_list and no_save):
                self._job.store_message()
            get_manual = check_int or check_float or check_date or check_time

            send_val = f"Please enter the {description if description!='' else 'value'}" \
                       f"{' in ' if replace_str != '' else ''}{replace_str}" \
                       f"{' from the options below' if option_list else ''}."

            if option_list and not no_save:
                msg = Message(send_string=send_val, job=self._job)
                msg.job_keyboard_extractor(index=index, options=option_list, add_cancel=True, add_other=get_manual)
                self.send_message(message=msg)
            elif option_list and no_save:
                msg = Message(send_string=send_val, job=self._job)
                msg.function_keyboard_extractor(self._job.function, options=option_list,
                                                add_cancel=True, add_other=get_manual)
                # msg.job_keyboard_extractor(index=index, options=option_list, add_cancel=True, add_other=get_manual)
                self.send_message(message=msg)
            else:
                self.send_message(message=Message(send_string=send_val+"\nSend /cancel to cancel Job", job=self._job),
                                  get_input=True, index=index)

        return success, value

    def send_message(self, message: Message, get_input=False, index=0, channel=None):
        if channel is not None and channel != self._job.telepot_account:
            message_temp = message
            message_temp.group = None
            self.__send_message(self._job.telepot_account, message_temp, get_input, index)
            self.__send_message(channel, message, get_input, index)
        else:
            self.__send_message(self._job.telepot_account, message, get_input, index)

    def __send_message(self, channel, message: Message, get_input=False, index=0):
        try:
            in_queue = channels[channel].waiting_user_input.keys()
        except KeyError as e:
            self.channel_error(e, channel)
            return

        message.job = self._job

        if get_input and self._job.chat_id in in_queue:
            log(job_id=self._job.job_id, msg="Chats in Queue: " + str(in_queue))
            message_queue.add_message(message)
            log(job_id=self._job.job_id, msg="Message added to Queue.")
        else:
            try:
                channels[self._job.telepot_account].send_now(message=message)
            except KeyError as e:
                self.channel_error(e, channel)
                return

            if get_input:
                try:
                    channels[self._job.telepot_account].get_user_input(job=self._job, index=index)
                except KeyError as e:
                    self.channel_error(e, channel)
                    return

    def close_all_callbacks(self):
        replies = self._job.replies
        for reply in replies.keys():
            channels[self._job.telepot_account].update_keyboard(self._job, replies[reply])

    def send_admin(self, message: Message):
        message.send_to_master()
        self.send_message(message=message)

    def channel_error(self, e, channel):
        if global_variables.operation_mode:
            log(job_id=self._job.job_id, error_code=10003, msg=str(e))
            raise InvalidParameterException
        else:
            log(job_id=self._job.job_id, log_type="warn",
                msg=f"Unable to send message. Channel, {channel} may not be available due not in operation mode.")
