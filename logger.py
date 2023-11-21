import logging
import os
from datetime import date


if not os.path.exists('log/'):
    os.makedirs('log/')

today_date = str(date.today())
logging.basicConfig(filename='log/log-'+today_date+'.log', level=logging.DEBUG)


def log(message_type, message):
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
