from datetime import datetime, timedelta

import global_var
from record import logger
from job_handling.job import Job
from record.custom_exceptions import *


class Module:
    def __init__(self, job: Job):
        self._job = job
        logger.log(self._job.job_id, f"Module Created")

    def execute(self):
        pass

    def send_message(self, message, group=None, image=None, admin=False):
        # todo write message sending script
        pass

    def send_admin(self, message):
        self.send_message(message=message, admin=True)

    def check_value(self, index: int = 0, replace_str: str = "",
                    check_int: bool = False, check_float: bool = False,
                    check_date: bool = False,
                    check_time: bool = False,
                    check_list=None,
                    default: str = "",
                    option_list=None) -> (bool, str):

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
            # todo handle message and send options_list as keyboard and prompt user to input a value
            pass

        return success, value
