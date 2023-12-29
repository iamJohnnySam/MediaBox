import logging
import os
from datetime import date, datetime

if not os.path.exists('log/'):
    os.makedirs('log/')

today_date = str(date.today())
logging.basicConfig(filename='log/log-' + today_date + '.log', level=logging.DEBUG)


def log(msg, source="MBOX", message_type="info"):
    message = str(msg)

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

    if len(source) > 4:
        pass
    else:
        source = "{:<4}".format(source)

    for segment in message.split("\n"):
        print(message_type + ",",
              datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ",",
              source + ", >,",
              segment)

