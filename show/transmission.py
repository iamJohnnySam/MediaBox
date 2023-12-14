import requests
from transmission_rpc import Client


class Transmission:
    def __init__(self):
        self.client = Client()

        self.active_torrents = {}

    def list_torrents(self):
        x = self.client.get_torrents()
        return x

    def add_torrent(self, path, paused=False):
        torrent = self.client.add_torrent(path, paused=paused)

        self.add_torrent_to_list(torrent_id, torrent)

    def add_torrent_to_list(self, torrent_id, torrent):
        pass
