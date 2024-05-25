import socket
import time

from common_workspace import queues
from communication_handler.socket.link import Link
from shared_models.message import Message
from shared_tools.logger import log


class Client:
    def __init__(self, ip_address: str, port: int):
        self.my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        log(msg="Socket Initialized")

        try:
            host_names, _, _ = socket.gethostbyaddr(ip_address)
            self.host_name = host_names[0]
            log(msg=f"Scanning IP address {ip_address} resulted host name: {self.host_name}.")
        except socket.gaierror as e:
            log(msg=f"Error Getting Hostname: {e}.", log_type="error")
            self.host_name = ip_address

        self._client_address = (ip_address, port)

    def connect(self):
        log(msg=f"Attempting to connect to socket, port {self._client_address}")

        is_server_connected = False
        attempts = 3
        delay_time = 5

        while not is_server_connected:
            try:
                attempts = attempts - 1
                self.my_socket.connect(self._client_address)
                is_server_connected = True
            except (ConnectionRefusedError, TimeoutError, OSError) as e:
                if attempts == 0:
                    log(msg=f"Could not connect to server due to {e}.")
                    return None

                log(msg=f"Could not connect to server due to {e}.Retrying in {delay_time} seconds.")
                time.sleep(delay_time)

        con_msg = f"Connected to socket, port {self._client_address}"
        log(msg=con_msg)
        queues.message_q.put(Message(con_msg))
        return Link(host_name=self.host_name, connection=self.my_socket)
