from communication_handler.socket import network_handler
from communication_handler.telegram import message_handler

bots: dict[str, message_handler.Messenger] = {}
sockets: dict[str, network_handler.Spider] = {}
