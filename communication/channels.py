from refs import db_telepot_accounts
from communication import message_handler
from database_manager.json_editor import JSONEditor
from tools import logger
from tools.custom_exceptions import InvalidParameterException

channels: dict[str:message_handler.Messenger] = {}


def init_channel(channel):
    telepot_accounts: dict = JSONEditor(db_telepot_accounts).read()
    for account in telepot_accounts.keys():
        message_handler.shutdown_bot[account] = True

    if channel == 'all':
        logger.log(msg=f"Starting all Telepot channels")
        for account in telepot_accounts.keys():
            if account == "test":
                logger.log(msg="Skip Test Account")
                continue
            channels[account] = message_handler.Messenger(account,
                                                          telepot_accounts[account]["account"],
                                                          telepot_accounts[account]["master"])
            del message_handler.shutdown_bot[account]

    elif channel in telepot_accounts.keys():
        logger.log(msg=f"Starting Telepot Channel - {channel}")
        channels[channel] = message_handler.Messenger(channel,
                                                      telepot_accounts[channel]["account"],
                                                      telepot_accounts[channel]["master"])
        del message_handler.shutdown_bot[channel]

    else:
        logger.log(error_code=20012)
        raise InvalidParameterException("Channel does not exist")
