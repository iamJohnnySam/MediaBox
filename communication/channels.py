import global_var
from communication.message_handler import MessageHandler
from database_manager.json_editor import JSONEditor
from tasker import task_queue

channels = {}
for account in JSONEditor(global_var.telepot_accounts).read().keys():
    channels[account] = MessageHandler(account, task_queue.msg_q)
    