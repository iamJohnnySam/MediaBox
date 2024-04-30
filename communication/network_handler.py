import socket

import global_variables
from tools import params
from tools.logger import log


def is_server():
    return params.get_param('socket', 'server')


class Spider:
    def __init__(self):
        self.my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connection = None

        if is_server():
            self.listen()
        else:
            self.connect(params.get_param('socket', 'connect'))

    def listen(self):
        address = ('0.0.0.0', 9999)
        self.my_socket.bind(address)
        self.my_socket.listen(1)
        log(msg="Server is listening...")

        self.connection, addr = self.my_socket.accept()
        log(msg=f"Connected to: {addr}")

    def connect(self, hostname):
        address = (socket.gethostbyname(hostname), 9999)
        self.my_socket.connect(address)

    def get_data(self):
        while not global_variables.stop_all:
            if is_server():
                data = self.connection.recv(1024)
            else:
                data = False
                pass

            if not data:
                break
            # output_queue.put(data.decode())
            # todo create job

    def put_data(self, data):
        if is_server():
            self.connection.sendall(data.encode())
