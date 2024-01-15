import logging
import os
from datetime import date, datetime

today_date = str(date.today())


def log(msg, source="MBOX", message_type="info"):
    message_types = ["info", "error", "warn", "debug"]
    if message_type not in message_types:
        raise ValueError("Invalid Error type: " + message_type)

    message = str(msg)

    if len(source) > 4:
        pass
    else:
        source = "{:<4}".format(source)

    if today_date != str(date.today()):
        logging.basicConfig(filename='log/log-' + today_date + '.log', level=logging.DEBUG)

    if message_type == "info":
        logging.info(message)
    elif message_type == "warn":
        logging.warning(message)
    elif message_type == "error":
        logging.error(message)
    elif message_type == "debug":
        logging.debug(message)

    for segment in message.split("\n"):
        print(message_type + ",",
              datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ",",
              source + ", >,",
              segment)


if not os.path.exists('log/'):
    os.makedirs('log/')

try:
    logging.basicConfig(filename='log/log-' + today_date + '.log', level=logging.DEBUG)
except PermissionError:
    log("PERMISSION ERROR", source="LOG", message_type="error")
