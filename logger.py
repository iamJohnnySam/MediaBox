import logging
from datetime import date

today_date = str(date.today())
logging.basicConfig(filename='log/log-'+today_date+'.log', encoding='utf-8', level=logging.DEBUG)


def log(message_type, message):
    if today_date != str(date.today()):
        logging.basicConfig(filename='log/log-' + today_date + '.log', encoding='utf-8', level=logging.DEBUG)

    if message_type == "info":
        logging.info(message)
    elif message_type == "warn":
        logging.warning(message)
    elif message_type == "error":
        logging.error(message)
    elif message_type == "debug":
        logging.debug(message)
