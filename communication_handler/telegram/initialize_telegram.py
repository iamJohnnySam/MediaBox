from common_workspace import global_var
from communication_handler.telegram.messenger import Messenger
from shared_tools.configuration_tools import is_config_enabled
from shared_tools.json_editor import JSONEditor
from shared_tools.logger import log


def init_telegram(config: dict) -> dict:
    channels = {}

    if not is_config_enabled(config, "Telepot"):
        return channels

    accounts: list = config["connect"]
    if len(accounts) == 0:
        log(msg=f"Telegram is enabled but no accounts to connect.", error_code=20017)
        return channels

    log(msg=f"Attempting to start telepot channels: {accounts}.")

    try:
        telepot_accounts: dict = JSONEditor(config["db_telepot_accounts"]).read()
    except KeyError:
        log(error_code=20018)
        return channels

    try:
        global_var.main_telegram_channel = accounts[config["main_account"]]
    except (IndexError, KeyError):
        log(error_code=20016)

    for account in accounts:
        if account in telepot_accounts.keys():
            log(msg=f"Starting telepot channel: {account}.")
            channels[account] = Messenger(telepot_account=account,
                                          telepot_key=telepot_accounts[account]["account"],
                                          telepot_master=telepot_accounts[account]["master"],
                                          )
        else:
            log(error_code=20012)

    return channels
