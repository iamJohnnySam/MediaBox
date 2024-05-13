import global_variables
from brains.job import Job
from communication import channels
from communication.message import Message
from refs import db_telepot_accounts
from communication import message_handler, network_handler
from shared_tools.json_editor import JSONEditor
from tools import params
from shared_tools.logger import log

tp_module = 'telepot'
sk_module = 'socket'


def init_channel():
    telepot_accounts: dict = JSONEditor(db_telepot_accounts).read()
    for account in telepot_accounts.keys():
        message_handler.shutdown_bot[account] = True

    if params.is_module_available(tp_module):
        log(msg=f"Starting Telepot channels: {params.get_param(tp_module, 'channels')}.")
        for account in params.get_param(tp_module, 'channels'):
            channels.bots[account] = message_handler.Messenger(account,
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
            channels.sockets[host] = network_handler.Spider(port=params.get_param("socket", "port"),
                                                            connection_count=params.get_param("socket",
                                                                                              "connection_count"))
        else:
            connections: dict = params.get_param("socket", "connect")
            for connection in connections.keys():
                network = network_handler.Spider(hostname=connection, port=connections[connection])
                channels.sockets[connection] = network


def send_message(msg: Message, account=None):
    if params.is_module_available(tp_module):
        if account is None:
            account = params.get_param(tp_module, 'main_channel')
        channels.bots[account].send_now(msg)
    else:
        host = params.get_module_hosts(tp_module)
        # todo pass to network


def send_job_to_host(job: Job, account):
    send_to_host(job.compress(), account, "job")


def send_message_to_host(msg: Message, account):
    send_to_host(msg.compress(), account, "msg")


def send_to_host(val: dict, account: str, m_type: str):
    send_id = f"{params.get_param('socket', 'identifier')}-{global_variables.socket_id}"
    global_variables.socket_id = global_variables.socket_id + 1

    val["id"] = send_id
    val["type"] = m_type

    for host in channels.sockets.keys():
        if host == account:
            channels.sockets[host].send_data(val, account)
            return

        if channels.sockets[host].is_server:
            for connection in channels.sockets[host].connections.keys():
                if connection == account:
                    channels.sockets[host].send_data(val, account)
                    return


def send_to_network(job, module):
    host = params.get_connected_host_with_module(module)
    if host is None:
        log(job_id=job.job_id, msg=f"No connected host detected for module {module}.", log_type="error")
    else:
        log(job_id=job.job_id, msg=f"Sending job to host {host} for executing module {module}.")
        send_job_to_host(job, host)


def inform_network(job):
    for socket in channels.sockets.keys():
        if channels.sockets[socket].is_server:
            for connection in channels.sockets[socket].connections:
                send_job_to_host(job, connection)
        else:
            send_job_to_host(job, socket)
