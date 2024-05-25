import inspect
import json
import logging
import os.path
from datetime import date, datetime

today_date = str(date.today())

logs_location = ""
log_level = "error"
error_codes = ""
log_to_console = True
log_to_file = False
file_created = False


def log_file_name():
    if logs_location != "" and not os.path.exists(logs_location):
        os.makedirs(logs_location)
    return os.path.join(logs_location, f"log-{today_date}.log")


def log(job_id: int | str = 0, msg: str = "", log_type: str = "debug", error_code: int = 0, error: str = ""):
    global file_created
    if error_code == 0 and msg == "":
        raise ValueError("Invalid Parameters for record")

    elif error_code != 0 and error_codes != "":
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

    if log_to_file and (today_date != str(date.today()) or not file_created):
        if log_type == "warn":
            level = logging.WARNING
        elif log_type == "error":
            level = logging.ERROR
        elif log_type == "debug":
            level = logging.DEBUG
        else:
            level = logging.INFO
        logging.basicConfig(filename=log_file_name(), level=level)
        file_created = True

    print_message = False
    if log_type == "warn":
        log_type = "WRN"
        if log_to_file:
            logging.warning(message)
        if log_to_console and log_level in ["debug", "info", "warn"]:
            print_message = True
    elif log_type == "error":
        log_type = "ERR"
        if log_to_file:
            logging.error(message)
        if log_to_console and log_level in ["debug", "info", "warn", "error"]:
            print_message = True
    elif log_type == "debug":
        log_type = "DBG"
        if log_to_file:
            logging.debug(message)
        if log_to_console and log_level in ["debug"]:
            print_message = True
    else:
        log_type = "INF"
        if log_to_file:
            logging.info(message)
        if log_to_console and log_level in ["debug", "info"]:
            print_message = True

    if error != "":
        logging.error(error)

    if print_message:
        for segment in message.split("\n"):
            print(f"{os.getpid():0>6},{log_type},{datetime.now().strftime('%m-%d %H:%M:%S')},{caller:_<20},"
                  f"{job_id:_>6},>,{segment}")
