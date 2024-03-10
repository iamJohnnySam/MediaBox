import global_var
from communication.message_handler import Messenger
from database_manager.json_editor import JSONEditor
from tools import logger
from tools.custom_exceptions import InvalidParameterException

channels = {}


def init_channel(channel):
    telepot_accounts: dict = JSONEditor(global_var.telepot_accounts).read()
    logger.log(msg=f"Found telepot accounts > {str(telepot_accounts)}")

    if channel == 'all':
        for account in telepot_accounts.keys():
            channels[account] = Messenger(account,
                                          telepot_accounts[account]["account"],
                                          telepot_accounts[account]["master"])

    elif channel in telepot_accounts.keys():
        channels[channel] = Messenger(channel,
                                      telepot_accounts[channel]["account"],
                                      telepot_accounts[channel]["master"])

    else:
        logger.log(error_code=20012)
        raise InvalidParameterException("Channel does not exist")
