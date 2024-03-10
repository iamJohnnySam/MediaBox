from datetime import datetime, timedelta

import global_var
from communication.channels import channels
from communication.message import Message
from job_handling import task_queue
from tools import logger
from job_handling.job import Job
from tools.custom_exceptions import *


class Module:
    def __init__(self, job: Job):
        self._job = job
        logger.log(self._job.job_id, f"Module Created")

    def check_value(self, index: int = 0, replace_str: str = "",
                    check_int: bool = False, check_float: bool = False,
                    check_date: bool = False,
                    check_time: bool = False,
                    check_list=None,
                    default: str = "",
                    option_list=None,
                    description: str = "") -> (bool, str):

        if sum([check_int, check_float, check_date, check_date]) > 1:
            raise InvalidParameterException("Contradicting check items are selected")

        success = True

        if option_list is None:
            option_list = [] if check_list is None else check_list

        if len(self._job.collection) <= index:
            if default != "":
                value = default
                logger.log(self._job.job_id, f"Index not available. Default used")
            else:
                success = False
                value = ""
                logger.log(self._job.job_id, f"Index not available and no default")
        else:
            try:
                value = self._job.collection[index]
            except ValueError:
                success = False
                value = ""
                logger.log(self._job.job_id, f"Unexpected index fail", log_type="warn")

        if success and value == "":
            if default != "":
                value = default
                logger.log(self._job.job_id, f"No message available. Default used")
            else:
                success = False
                logger.log(self._job.job_id, f"No message available and no default")

        if success and not check_time and not check_date and " " in value:
            value = value.split(" ")[0].strip()

        if success and replace_str != "" and replace_str in value:
            value = value.replace(replace_str, "").strip()

        if success and check_int:
            try:
                int(value)
            except ValueError:
                success = False
                logger.log(self._job.job_id, f"Unable to convert to int")

        if success and check_float:
            try:
                float(value)
            except ValueError:
                success = False
                logger.log(self._job.job_id, f"Unable to convert to float")

        if success and check_list is not None:
            if value not in check_list:
                success = False
                logger.log(self._job.job_id, f"Expected item not in list")

        if success and check_date and value.lower() == "yesterday":
            value = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

        if success and check_date and value.lower() == "tomorrow":
            value = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')

        if success and check_date:
            date_formats = global_var.date_formats
            for date_format in date_formats:
                try:
                    date_obj = datetime.strptime(value, date_format)
                    if '%Y' not in value:
                        date_obj = date_obj.replace(year=datetime.now().year)
                    value = date_obj.strftime('%Y-%m-%d')
                    success = True
                    logger.log(self._job.job_id, f"Date format accepted {str(value)} for {date_format}")
                    break
                except ValueError:
                    success = False
                    logger.log(self._job.job_id, f"Date format mismatch {str(value)} for {date_format}")

        if success and check_time:
            time_formats = global_var.time_formats
            for time_format in time_formats:
                try:
                    time_obj = datetime.strptime(value, time_format).time()
                    value = time_obj.strftime("%H:%M:%S")
                    success = True
                    logger.log(self._job.job_id, f"Time format accepted {str(value)} for {time_format}")
                    break
                except ValueError:
                    success = False
                    logger.log(self._job.job_id, f"Time format mismatch {str(value)} for {time_format}")

        # If anything failed
        if not success:
            self._job.store_message()
            get_manual = check_int or check_float or check_date or check_time

            if option_list:
                if description != "":
                    send_val = "Please select the " + description + "."
                else:
                    send_val = "Please select from the list below."
            else:
                if replace_str != "":
                    send_val = f"Please enter the amount in {replace_str}"
                else:
                    send_val = "Please enter the amount"
                if description != "":
                    send_val = send_val + " for the " + description + "."

            if option_list:
                msg = Message(send_string=send_val, job=self._job)
                msg.keyboard_extractor(index=index, options=option_list, add_cancel=True, add_other=get_manual)
                self.send_message(message=msg)
            else:
                self.send_message(message=Message(send_string=send_val, job=self._job), get_input=True)

        return success, value

    def send_message(self, message: Message, get_input=False):
        if get_input and self._job.chat_id in channels[self._job.telepot_account].waiting_user_input.keys():
            task_queue.add_message(message)
        else:
            channels[self._job.telepot_account].send_now(message=message)

    def send_admin(self, message: Message):
        message.send_to_master()
        self.send_message(message=message)
