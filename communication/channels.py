from refs import db_telepot_accounts
from communication.message_handler import Messenger
from database_manager.json_editor import JSONEditor
from tools import logger
from tools.custom_exceptions import InvalidParameterException

channels = {}


def init_channel(channel):
    telepot_accounts: dict = JSONEditor(db_telepot_accounts).read()

    if channel == 'all':
        logger.log(msg=f"Starting all Telepot channels")
        for account in telepot_accounts.keys():
            channels[account] = Messenger(account,
                                          telepot_accounts[account]["account"],
                                          telepot_accounts[account]["master"])

    elif channel in telepot_accounts.keys():
        logger.log(msg=f"Starting Telepot Channel - {channel}")
        channels[channel] = Messenger(channel,
                                      telepot_accounts[channel]["account"],
                                      telepot_accounts[channel]["master"])

    else:
        logger.log(error_code=20012)
        raise InvalidParameterException("Channel does not exist")
