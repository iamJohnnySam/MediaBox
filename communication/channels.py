import global_var
from communication.message_handler import Messenger
from database_manager.json_editor import JSONEditor

channels = {}
telepot_accounts = JSONEditor(global_var.telepot_accounts).read()
for account in telepot_accounts.keys():
    channels[account] = Messenger(account,
                                  telepot_accounts[account]["account"],
                                  telepot_accounts[account]["master"])
    