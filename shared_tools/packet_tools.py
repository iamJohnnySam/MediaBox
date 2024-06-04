from common_workspace import queues
from shared_models.job import Job
from shared_models.message import Message
from shared_tools.logger import log


def packet_and_queue(obj: Job | Message):
    if type(obj) is Job:
        packet = obj.job_compress()
        job_id = obj.job_id
    elif type(obj) is Message:
        packet = obj.message_compress()
        job_id = obj.msg_id
    else:
        log(error_code=10005)
        return

    packet["attempts"] = 0

    queues.packet_q.put(packet)
    log(job_id=job_id, msg="Added to Packet Queue")
