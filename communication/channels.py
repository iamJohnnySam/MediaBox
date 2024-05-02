from communication import message_handler, network_handler

bots: dict[str, message_handler.Messenger] = {}
sockets: dict[str, network_handler.Spider] = {}
