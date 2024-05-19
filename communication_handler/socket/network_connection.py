import json
import socket

from common_workspace import global_var
from shared_tools.logger import log


class Link:
    def __init__(self, host_name: str, connection: socket.socket):
        self._host_name: str = host_name
        self.connection: socket.socket = connection

    def listen(self):
        while not global_var.flag_stop:
            try:
                data = self.connection.recv(4096)
            except ConnectionResetError as e:
                log(msg=f"{self._host_name}: connection dropped with client: {e}.")
                self.connection.close()
                break

            if not data:
                log(msg=f"{self._host_name}: No data received. Connection will close.")
                self.connection.close()
                break

            data = data.decode()
            r_data: dict = json.loads(data)
            log(msg=f"{self._host_name}: Data Received: {data}")

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

        self.connection.close()

    def send_data(self, data: dict):
        if type(data) is dict:
            self.connection.sendall(str.encode(json.dumps(data)))
        else:
            log(error_code=60002)

    # todo send acknowledgement
