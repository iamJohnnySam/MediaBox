import logging
import os
from datetime import date, datetime

if not os.path.exists('log/'):
    os.makedirs('log/')

today_date = str(date.today())
logging.basicConfig(filename='log/log-' + today_date + '.log', level=logging.DEBUG)


def log(message, source="MBOX", message_type="info"):
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

    print(message_type + ",",
          str(datetime.now()) + ",",
          source + ", >,",
          message)
