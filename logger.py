import inspect
import logging
import os
from datetime import date, datetime

today_date = str(date.today())


def log(msg, message_type="info"):
    message_types = ["info", "error", "warn", "debug"]
    if message_type not in message_types:
        raise ValueError("Invalid Error type: " + message_type)

    message = str(msg)

    stack = inspect.stack()
    caller_frame = stack[1][0]
    if 'self' not in caller_frame.f_locals:
        caller_name = caller_frame.f_code.co_name
    else:
        the_class = caller_frame.f_locals["self"].__class__.__name__
        the_method = caller_frame.f_code.co_name
        caller_name = f"{the_class}>{the_method}"

    if today_date != str(date.today()):
        logging.basicConfig(filename='log/log-' + today_date + '.log', level=logging.DEBUG)

    if message_type == "warn":
        logging.warning(message)
        m_type = "WRN"
    elif message_type == "error":
        m_type = "ERR"
        logging.error(message)
    elif message_type == "debug":
        logging.debug(message)
        m_type = "DBG"
    else:
        logging.info(message)
        m_type = "INF"

    for segment in message.split("\n"):
        print(f'{m_type},{datetime.now().strftime("%H:%M:%S")},{caller_name.ljust(25)},>,{segment}')


if not os.path.exists('log/'):
    os.makedirs('log/')

try:
    logging.basicConfig(filename='log/log-' + today_date + '.log', level=logging.DEBUG)
except PermissionError:
    log("PERMISSION ERROR", message_type="error")
