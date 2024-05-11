import json
import socket
import threading
import time

import global_variables
from brains import task_queue
from brains.job import Job
from communication import channel_control
from communication.message import Message
from tools import params
from tools.logger import log


class Spider:
    def __init__(self, hostname: str = None, port: int = 12345, connection_count: int = 1):
        self.connections: dict[str, socket.socket] = {}
        self.is_server_connected = False

        self.my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        log(msg="Socket Initialized")

        if hostname is None or hostname == global_variables.host:
            self.is_server = True
            self.__init_server(port, connection_count)

        else:
            self.is_server = False
            self.__init_clients(hostname, port)

    def __init_server(self, port: int, connection_count: int):
        self.my_socket.bind(('', port))
        log(msg=f"Socket bound to {port}")
        self.my_socket.listen(connection_count)
        for i in range(connection_count):
            self.__start_thread_to_accept()

    def __start_thread_to_accept(self):
        threading.Thread(target=self.__accept, daemon=True).start()

    def __accept(self):
        host_unknown = True
        c, addr, host = None, None, None

        while host_unknown and not global_variables.stop_all:
            log(msg=f"Server is listening on {self.my_socket.getsockname()}...")
            c, addr = self.my_socket.accept()

            log(msg=f"Following address is attempting to connect: {addr}")

            try:
                host, _, ip_addr_list = socket.gethostbyaddr(addr[0])
                host = host.lower()
                log(msg=f"Scanning IP {addr} resulted in hostname {host} and IP addresses: {ip_addr_list}.")
            except Exception as e:
                log(msg=f"Could not resolve IP address: {e}", log_type="error")
                host = params.get_host_from_ip(addr[0])

            if params.is_host_known(host):
                host_unknown = False
            else:
                log(msg=f"Rejected connection from {addr}", log_type="warn")
                c.close()

        con_msg = f"{host}: Connected via {addr}"
        log(msg= con_msg)
        channel_control.send_message(Message(con_msg))
        self.connections[host] = c
        self.__listen(host)

    def __init_clients(self, hostname: str, port: int):
        try:
            _, _, ip_addr_list = socket.gethostbyname_ex(hostname)
            log(msg=f"Scanning hostname {hostname} resulted IP addresses: {ip_addr_list}.")
            ip = ip_addr_list[0]
        except socket.gaierror as e:
            log(msg=f"Error Getting Hostname: {e}\nChecking system parameters for static IP.", log_type="error")
            ip = params.get_static_ip(hostname)
            if ip is None:
                log(msg=f"Could not obtain static IP from system parameters", log_type="error")
                raise socket.gaierror

        self._client_address = (ip, port)
        self.__start_thread_to_connect()

    def __start_thread_to_connect(self):
        threading.Thread(target=self.__connect, daemon=True).start()

    def __connect(self):
        self.is_server_connected = False
        warn_show = 3
        delay_time = 60

        log(msg=f"Attempting to connect to socket, port {self._client_address}")

        while not self.is_server_connected:
            try:
                warn_show = warn_show - 1
                self.my_socket.connect(self._client_address)
                self.is_server_connected = True
            except (ConnectionRefusedError, TimeoutError, OSError) as e:
                if warn_show >= 0:
                    log(msg=f"Could not connect to server due to {e}.\n"
                            f"This loop will iterate every {delay_time} seconds until connected.\n"
                            f"This error message will stop appearing after {warn_show} attempt(s).")
                time.sleep(delay_time)

        con_msg = f"Connected to socket, port {self._client_address}"
        log(msg=con_msg)
        channel_control.send_message(Message(con_msg))
        self.__listen()

    def __listen(self, host=None):
        if host is not None:
            connection: socket.socket = self.connections[host]
        else:
            host = global_variables.host
            connection = self.my_socket

        while not global_variables.stop_all:
            try:
                data = connection.recv(4096)
            except ConnectionResetError as e:
                log(msg=f"{host}: connection dropped with server {self._client_address}: {e}.")
                connection.close()
                self.__reconnect(host)
                break

            if not data:
                log(msg=f"{host}: No data received. Connection will close.")
                connection.close()
                self.__reconnect(host)
                break

            data = data.decode()
            r_data: dict = json.loads(data)
            log(msg=f"{host}: Data Received: {data}")

            if r_data["type"] == "job":
                job = Job(telepot_account=r_data["account"],
                          job_id=r_data["job"],
                          chat_id=r_data["chat"],
                          username=r_data["username"],
                          reply_to=r_data["reply"],
                          function=r_data["function"],
                          collection=r_data["collection"],
                          other_host=True,
                          orig_job_id=r_data["original_job_id"])
                task_queue.add_job(job)

        connection.close()

    def __reconnect(self, host):
        log(msg="Short sleep before reconnecting...")
        time.sleep(3)
        if not self.is_server:
            self.my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.__start_thread_to_connect()
        else:
            del self.connections[host]
            self.__start_thread_to_accept()

    def send_data(self, data: dict, host):
        if self.is_server:
            connection: socket.socket = self.connections[host]
            connection.sendall(str.encode(json.dumps(data)))
        else:
            self.my_socket.sendall(str.encode(json.dumps(data)))
