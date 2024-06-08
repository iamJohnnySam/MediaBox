import threading
import time

from common_workspace import queues, global_var
from communication_handler.socket.packet_handler import Packer
from communication_handler.socket.link import Link
from communication_handler.socket.network_client import Client
from communication_handler.socket.network_server import Server
from shared_models import configuration
from shared_tools.configuration_tools import get_host_with_module, get_ip_from_host
from shared_tools.logger import log

connected_clients: dict[str: Link] = {}
connection_threads: dict[str, threading.Thread] = {}


def connect_client(host, ip, port):
    client = Client(ip, port).connect()
    log(msg=f"Creating client connection: {host} at {ip} on port {port}")
    if type(client) is Link:
        connected_clients[host] = client
        log(msg=f"Client Connected: {host} at {ip} on port {port}")


def check_conn_threads():
    for host in list(connection_threads.keys()):
        if not connection_threads[host].is_alive():
            log(msg=f"Thread for {host} ended.")
            del connection_threads[host]


def run_sockets():
    config = configuration.Configuration()
    _ = Server(config.host, config.socket)

    while not global_var.flag_stop.value:
        while not queues.packet_q.empty():
            packet: dict = queues.packet_q.get()
            module, connect = Packer(data_id=0, packet=packet).get_module()
            hosts: list = get_host_with_module(module, connect)

            packet_id = packet["id"]

            if len(hosts) == 0:
                log(error_code=60004)
                log(job_id=packet_id, msg=f"Packet dropped: {packet}")
                continue

            for host in hosts:
                if host not in connected_clients.keys() and host not in connection_threads.keys():
                    ip, port = get_ip_from_host(config.socket, host)
                    if ip == "":
                        continue
                    connection_threads[host] = threading.Thread(target=connect_client, args=(host, ip, port),
                                                                daemon=True)
                    connection_threads[host].start()

            packet_sent = False
            while not packet_sent and len(connection_threads) != 0:
                check_conn_threads()
                for host in hosts:
                    if host in connected_clients.keys():
                        connected_clients[host].send_data(packet)
                        packet_sent = True
                        continue
                time.sleep(1)

            if not packet_sent:
                log(job_id=packet_id, msg=f"Packet for {module} was not sent to hosts: {hosts}")
                if packet["attempts"] > 3:
                    log(error_code=60007)
                    log(job_id=packet_id, msg=f"Packet dropped: {packet}")

                else:
                    packet["attempts"] = packet["attempts"] + 1
                    queues.packet_q.put(packet)
                    log(job_id=packet_id, msg="Packet {packet} added to back of queue.")

            # todo keep client connection open for some time (10 minutes) and check if any other packets need to be sent

            if queues.packet_q.empty():
                for client in list(connected_clients.keys()):
                    connected_clients[client].close_connection()
                    log(msg=f"Client, {client}, connection closed.")
                    del connected_clients[client]

        time.sleep(5)
