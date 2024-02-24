import global_var
from communication.message_handler import Messenger
from database_manager.json_editor import JSONEditor
from record import logger

channels = {}
telepot_accounts = JSONEditor(global_var.telepot_accounts).read()
logger.log(job_id=0, msg=f"Found telepot accounts > {str(telepot_accounts)}")

for account in telepot_accounts.keys():
    channels[account] = Messenger(account,
                                  telepot_accounts[account]["account"],
                                  telepot_accounts[account]["master"])
    