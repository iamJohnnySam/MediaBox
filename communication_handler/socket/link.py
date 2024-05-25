import json
import socket

from common_workspace import global_var
from communication_handler.packet_handler import Packer
from shared_tools.logger import log

data_id = 0


class Link:
    def __init__(self, host_name: str, connection: socket.socket):
        self._host_name: str = host_name
        self.connection: socket.socket = connection

    def listen(self):
        global data_id
        while not global_var.flag_stop:
            try:
                data = self.connection.recv(4096)
            except ConnectionResetError as e:
                log(msg=f"{self._host_name}: connection dropped with host: {e}.")
                self.connection.close()
                break

            if not data:
                log(msg=f"{self._host_name}: No data received. Connection will close.")
                self.connection.close()
                break

            data = data.decode()
            r_data: dict = json.loads(data)
            log(msg=f"{self._host_name}: Data Received: {data}")

            data_id = data_id + 1
            if data_id >= 1000:
                data_id = 1
            Packer(f"d{data_id}", r_data).handle_packet()

        self.connection.close()

    def send_data(self, data: dict):
        if type(data) is dict:
            self.connection.sendall(str.encode(json.dumps(data)))
        else:
            log(error_code=60002)

    def close_connection(self):
        self.connection.close()

    # todo send acknowledgement
