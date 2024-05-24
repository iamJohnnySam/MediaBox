from communication_handler.socket.network_server import Server
from shared_models import configuration


def run_sockets():
    config = configuration.Configuration()
    server_socket = Server(config.host, config.socket)
