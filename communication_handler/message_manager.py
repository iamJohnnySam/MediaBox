import time

from common_workspace import queues
from communication_handler import communication_queues
from communication_handler.telegram.initialize_telegram import init_telegram
from communication_handler.telegram.messenger import Messenger
from shared_models import configuration
from shared_models.message import Message
from shared_tools.custom_exceptions import InvalidParameterException
from shared_tools.logger import log


def run_telegram():
    config = configuration.Configuration()
    telepot_channels: dict[str, Messenger] = init_telegram(config.telegram)

    while True:
        while not queues.message_q.empty():
            msg: Message = queues.message_q.get()

            if msg.channel not in telepot_channels.keys():
                # todo send to network
                continue

            if msg.get_input and msg.chat_id in communication_queues.wait_queue[msg.channel].keys():
                queues.message_q.put()
                log(job_id=msg.msg_id, msg=f"Chats in Queue: {communication_queues.wait_queue[msg.channel]}")
                continue

            try:
                telepot_channels[msg.channel].send_now(message=msg)
            except KeyError as e:
                log(job_id=msg.msg_id, error_code=10003, msg=str(e))
                raise InvalidParameterException

        time.sleep(1)
