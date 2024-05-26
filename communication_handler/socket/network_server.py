import socket
import threading
import time

from common_workspace import global_var, queues
from communication_handler.socket.link import Link
from shared_models.message import Message
from shared_tools.configuration_tools import is_config_enabled, get_host_from_ip
from shared_tools.logger import log


class Server:
    def __init__(self, host_name: str, config: dict):
        self._host_name = host_name
        self._config: dict = config
        self.connections: dict[str, Link] = {}

        if not is_config_enabled(self._config, "Sockets"):
            log(error_code=60001)
            self._expected_connections: dict = {}
            self._port = global_var.default_port
        else:
            self._expected_connections: dict = self._config["connect"]
            self._port = config["port"]

        host_name = host_name.lower()
        if host_name in self._expected_connections.keys():
            del self._expected_connections[host_name]

        self._connection_count = len(self._expected_connections)
        if self._connection_count == 0:
            log(msg=f"Socket is enabled but no connections to connect.", error_code=60017)

        log(msg=f"Attempting to start server on: {self._port}.")
        self._my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        log(msg="Socket Initialized")

        self._my_socket.bind(('', self._port))
        log(msg=f"Socket bound to {self._port}")

        threading.Thread(target=self.__run_server, daemon=True).start()

    def __run_server(self):
        log(msg=f"Socket listening to {self._connection_count} connections.")
        self._my_socket.listen(self._connection_count)
        t_accepts = []

        for i in range(self._connection_count):
            t_accepts.append(threading.Thread(target=self.__accept, args=(i,), daemon=True))

        while not global_var.flag_stop:
            for i in range(len(t_accepts)):
                if not t_accepts[i].is_alive():
                    log(msg=f"Listening to connection [id: {i}]...")
                    t_accepts[i].start()
            time.sleep(60)

    def __accept(self, connect_id):
        host_unknown = True
        c, addr, host = None, None, None

        while host_unknown:
            log(msg=f"Server {connect_id} is listening on {self._my_socket.getsockname()}...")
            c, addr = self._my_socket.accept()

            log(msg=f"Server {connect_id}: Following address is attempting to connect: {addr}")

            try:
                host, _, ip_addr_list = socket.gethostbyaddr(addr[0])
                host = host.lower()
                log(msg=f"Server {connect_id}: "
                        f"Scanning IP {addr} resulted in hostname {host} and IP addresses: {ip_addr_list}.")
            except Exception as e:
                log(msg=f"Server {connect_id}: Could not resolve IP address: {e}", log_type="error")
                host = get_host_from_ip(config=self._expected_connections, ip=addr[0])

            if host != "":
                host_unknown = False
            else:
                log(msg=f"Server {connect_id}: Rejected connection from {addr}", log_type="warn")
                c.close()

        con_msg = f"Server {connect_id}: {host} connected via {addr}"
        log(msg=con_msg)
        queues.message_q.put(Message(send_string=con_msg))

        self.connections[host] = Link(host, c)
        self.connections[host].listen()
