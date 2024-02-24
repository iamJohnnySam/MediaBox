import global_var
from communication.message_handler import Messenger
from database_manager.json_editor import JSONEditor
from tasker import task_queue

channels = {}
for account in JSONEditor(global_var.telepot_accounts).read().keys():
    channels[account] = Messenger(account, task_queue.msg_q)
    