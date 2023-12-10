import requests
from transmission_rpc import Client

client = Client()


def list_torrents():
    x = client.get_torrents()
    print(x)
