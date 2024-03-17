import inspect
import json
import logging
import os
from datetime import date, datetime

from refs import log_level, error_codes

today_date = str(date.today())


def log(job_id: int = 0, msg: str = "", log_type: str = "debug", error_code: int = 0, error: str = ""):
    if error_code == 0 and msg == "":
        raise ValueError("Invalid Parameters for record")

    elif error_code != 0 and msg == "":
        with open(error_codes, 'r') as file:
            errors: dict = json.load(file)

        if str(error_code) in errors.keys():
            msg = f"{str(error_code)},{errors[str(error_code)]}"
            if log_type == "debug":
                log_type = "error"
            elif log_type == "debug" and str(error_code).startswith("3"):
                log_type = "info"
        else:
            raise LookupError("Error code not found")

    message_types = ["info", "error", "warn", "debug"]
    if log_type not in message_types:
        raise ValueError("Invalid Error type: " + log_type)

    message = str(msg)

    stack = inspect.stack()
    caller_frame = stack[1][0]
    if 'self' not in caller_frame.f_locals:
        caller = caller_frame.f_code.co_name
    else:
        the_class = caller_frame.f_locals["self"].__class__.__name__
        caller = f"{the_class}"

    if today_date != str(date.today()):
        logging.basicConfig(filename='log/log-' + today_date + '.log', level=logging.DEBUG)

    print_message = False
    if log_type == "warn":
        log_type = "WRN"
        logging.warning(message)
        if log_level in ["debug", "info", "warn"]:
            print_message = True
    elif log_type == "error":
        log_type = "ERR"
        logging.error(message)
        if log_level in ["debug", "info", "warn", "error"]:
            print_message = True
    elif log_type == "debug":
        logging.debug(message)
        log_type = "DBG"
        if log_level in ["debug"]:
            print_message = True
    else:
        logging.info(message)
        log_type = "INF"
        if log_level in ["debug", "info"]:
            print_message = True

    if error != "":
        logging.error(error)

    if print_message:
        for segment in message.split("\n"):
            print(f'{log_type},{datetime.now().strftime("%m-%d %H:%M:%S")},{caller.ljust(15)},'
                  f'{str(job_id)},>,{segment}')


if not os.path.exists('log/'):
    os.makedirs('log/')

try:
    logging.basicConfig(filename='log/log-' + today_date + '.log', level=logging.DEBUG)
except PermissionError:
    log(0, "PERMISSION ERROR", log_type="error")
