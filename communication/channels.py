import threading

import global_variables
from communication.message import Message
from refs import db_telepot_accounts
from communication import message_handler, network_handler
from database_manager.json_editor import JSONEditor
from tools import params
from tools.logger import log

channels: dict[str, message_handler.Messenger] = {}
sockets: dict[str, network_handler.Spider] = {}

tp_module = 'telepot'
sk_module = 'socket'


def init_channel():
    telepot_accounts: dict = JSONEditor(db_telepot_accounts).read()
    for account in telepot_accounts.keys():
        message_handler.shutdown_bot[account] = True

    if params.is_module_available(tp_module):
        log(msg=f"Starting Telepot channels: {params.get_param(tp_module, 'channels')}.")
        for account in params.get_param(tp_module, 'channels'):
            channels[account] = message_handler.Messenger(account,
                                                          telepot_accounts[account]["account"],
                                                          telepot_accounts[account]["master"])
            del message_handler.shutdown_bot[account]

    else:
        log(error_code=20012)


def init_socket():
    if params.is_module_available(sk_module):
        log(msg=f"Starting Sockets.")
        if params.get_param(sk_module, 'server'):
            host = global_variables.host
            sockets[host] = network_handler.Spider(port=params.get_param("socket", "port"),
                                                   connection_count=params.get_param("socket", "connection_count"))
        else:
            connections: dict = params.get_param("socket", "connect")
            for connection in connections.keys():
                threading.Thread(target=connect_client, args=(connection, connections[connection])).start()


def connect_client(connection, port):
    try:
        network = network_handler.Spider(hostname=connection, port=port)
    except (ConnectionRefusedError, TimeoutError) as e:
        log(msg=f"Could not connect {connection}. {e}", log_type="error")
        return
    sockets[connection] = network


def send_message(msg: Message, account=None):
    if params.is_module_available(tp_module):
        if account is None:
            account = params.get_param(tp_module, 'main_channel')
        channels[account].send_now(msg)
    else:
        host = params.get_module_hosts(tp_module)
        # todo pass to network
