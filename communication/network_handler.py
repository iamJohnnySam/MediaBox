import socket
import threading
import time

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
            for i in range(connection_count):
                self.__start_thread_to_accept()

        else:
            self.is_server = False
            try:
                hostname, alias_list, ip_addr_list = socket.gethostbyname_ex(hostname)
                log(msg=f"Scanning hostname {hostname} resulted in alias list: {alias_list} and "
                        f"IP addresses: {ip_addr_list}.")
                ip = ip_addr_list[0]
            except socket.gaierror as e:
                log(msg=f"Error Getting Hostname: {e}", log_type="error")
                ip = params.get_static_ip(hostname)
                if ip is None:
                    raise socket.gaierror
            address = (ip, port)
            self.__connect(address)

    def __start_thread_to_accept(self):
        threading.Thread(target=self.__accept, daemon=True).start()

    def __accept(self):
        host_unknown = True
        c, addr, host = None, None, None

        while host_unknown:
            log(msg=f"Server is listening on {self.my_socket.getsockname()}...")
            c, addr = self.my_socket.accept()
            log(msg=f"Following address is attempting to connect: {addr}")
            try:
                host, alias_list, ip_addr_list = socket.gethostbyaddr(addr[0])
                log(msg=f"Scanning IP {addr} resulted in hostname {host}, alias list: {alias_list} and "
                        f"IP addresses: {ip_addr_list}.")
            except Exception as e:
                log(msg=str(e), log_type="error")
                host = params.get_host_from_ip(addr[0])

            if params.is_host_known(host):
                host_unknown = False
            else:
                c.close()

        log(msg=f"{host} Connected via {addr}")
        self.connections[host] = c
        threading.Thread(target=self.__listen, args=(host,), daemon=True).start()

    def __listen(self, host=None):
        if host is not None:
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
        log(msg=f"Connecting to socket, port {address}")
        connected = False
        attempts = 10
        while not connected:
            attempts = attempts - 1
            try:
                self.my_socket.connect(address)
            except ConnectionRefusedError:
                log(msg=f"Connection Refused {address}. {attempts} attempts remaining.", log_type="error")
                if attempts == 0:
                    raise ConnectionRefusedError
                log(msg=f"Sleeping for 1 minute before retrying.")
                time.sleep(60)
            except TimeoutError:
                log(msg=f"Connection Timed out {address}. {attempts} attempts remaining.", log_type="error")
                if attempts == 0:
                    raise TimeoutError
                log(msg=f"Sleeping for 1 minute before retrying.")
                time.sleep(60)
        log(msg=f"Connected to socket, port {address}")
        self.__listen()

    def send_data(self, host, data: str):
        connection: socket.socket = self.connections[host]
        connection.sendall(data.encode())

