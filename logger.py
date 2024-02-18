import inspect
import logging
import os
from datetime import date, datetime

import global_var

today_date = str(date.today())


def log(job_id, msg, log_type="debug"):
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
        if global_var.log_type in ["debug", "info", "warn"]:
            print_message = True
    elif log_type == "error":
        log_type = "ERR"
        logging.error(message)
        if global_var.log_type in ["debug", "info", "warn", "error"]:
            print_message = True
    elif log_type == "debug":
        logging.debug(message)
        log_type = "DBG"
        if global_var.log_type in ["debug"]:
            print_message = True
    else:
        logging.info(message)
        log_type = "INF"
        if global_var.log_type in ["debug", "info"]:
            print_message = True

    if print_message:
        for segment in message.split("\n"):
            print(f'{log_type},{datetime.now().strftime("%m-%d %H:%M:%S")},{caller.ljust(10)},>,'
                  f'{str(job_id)},>,{segment}')


if not os.path.exists('log/'):
    os.makedirs('log/')

try:
    logging.basicConfig(filename='log/log-' + today_date + '.log', level=logging.DEBUG)
except PermissionError:
    log(0, "PERMISSION ERROR", log_type="error")
