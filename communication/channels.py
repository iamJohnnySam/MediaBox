from communication.message import Message
from refs import db_telepot_accounts
from communication import message_handler
from database_manager.json_editor import JSONEditor
from tools import logger, params

channels: dict[str, message_handler.Messenger] = {}
module = 'telepot'


def init_channel():
    telepot_accounts: dict = JSONEditor(db_telepot_accounts).read()
    for account in telepot_accounts.keys():
        message_handler.shutdown_bot[account] = True

    if params.is_module_available(module):
        logger.log(msg=f"Starting Telepot channels: {params.get_param(module, 'channels')}.")
        for account in params.get_param(module, 'channels'):
            channels[account] = message_handler.Messenger(account,
                                                          telepot_accounts[account]["account"],
                                                          telepot_accounts[account]["master"])
            del message_handler.shutdown_bot[account]

    else:
        logger.log(error_code=20012)


def send_message(msg: Message, account=None):
    if params.is_module_available(module):
        if account is None:
            account = params.get_param(module, 'main_channel')
        channels[account].send_now(msg)
    else:
        host = params.get_module_hosts(module)
        # todo pass to network
