import socket
import threading

import global_variables
from tools import params
from tools.logger import log


def is_server():
    return params.get_param('socket', 'server')


class Spider:
    def __init__(self, hostname: str = None, port: int = 12345, connection_count: int = 1):
        self.my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connections = {}
        log(msg="Socket Initialized")

        if hostname is None or hostname == global_variables.host:
            self.is_server = True
            self.my_socket.bind(('', port))
            log(msg=f"Socket bound to {port}")
            self.my_socket.listen(connection_count)
            log(msg="Server is listening...")
            for i in range(connection_count):
                self.__start_thread_to_accept()

        else:
            self.is_server = False
            address = (socket.gethostbyname(hostname), port)
            threading.Thread(target=self.__connect, args=address, daemon=True)

    def __start_thread_to_accept(self):
        threading.Thread(target=self.__accept, daemon=True).start()

    def __accept(self):
        host_unknown = True
        c, addr, host = None, None, None

        while host_unknown:
            c, addr = self.my_socket.accept()
            host = socket.gethostbyaddr(addr)
            if params.is_host_known():
                host_unknown = False
            else:
                c.close()
                return

        log(msg=f"{host} Connected via {addr}")
        self.connections[host] = c
        threading.Thread(target=self.__listen, args=host, daemon=True)

    def __listen(self, host=None):
        if host is None:
            connection: socket.socket = self.connections[host]
        else:
            connection = self.my_socket

        while not global_variables.stop_all:
            data = connection.recv(1024)
            if not data:
                log(msg=f"{host}: No data received. Connection will close.")
                self.__start_thread_to_accept()
                break
            data = data.decode()
            log(msg=f"{host}: Data Received: {data}")
        connection.close()

    def __connect(self, address):
        self.my_socket.connect(address)
        self.__listen()

    def send_data(self, host, data: str):
        connection: socket.socket = self.connections[host]
        connection.sendall(data.encode())

