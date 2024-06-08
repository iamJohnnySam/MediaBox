from common_workspace import queues
from shared_models.job import Job
from shared_models.message import Message
from shared_tools.logger import log


class Packer:
    def __init__(self, data_id, packet: dict):
        self.data_id = data_id
        self.packet = packet

    def handle_packet(self):
        if "packet_type" not in self.packet.keys():
            log(msg=f"Unknown packet type: {self.packet['packet_type']}", error_code=60003)

        if self.packet["packet_type"] == "job":
            log(job_id=self.data_id, msg=f"Job Packet Received [{self.packet['function']}].")
            job = Job(self.packet["function"])
            job.job_decompress(self.packet)
            job.bypass_channel_check = True
            queues.job_q.put(job)

        elif self.packet["packet_type"] == "message":
            log(job_id=self.data_id, msg=f"Message Packet Received [{self.packet['msg']}].")
            msg = Message(self.packet["msg"])
            msg.message_decompress(self.packet)
            queues.message_q.put(msg)

        elif self.packet["packet_type"] == "info":
            log(job_id=self.data_id, msg=f"Info Packet Received [].")

        else:
            log(job_id=self.data_id, msg=f"Unknown packet type: {self.packet['packet_type']}", error_code=60003)

    def get_module(self) -> (str, str):
        if self.packet["packet_type"] == "job":
            return self.packet["module"], ""

        elif self.packet["packet_type"] == "message":
            return "telegram", self.packet["channel"]
