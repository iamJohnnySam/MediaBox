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
        torrent_id = torrent.hashString
        success = self.add_torrent_to_list(torrent_id, torrent)
        return success, torrent_id

    def add_torrent_to_list(self, torrent_id, torrent):
        if torrent_id not in self.active_torrents.keys():
            self.active_torrents[torrent_id] = torrent
            return True
        else:
            return False


client = Transmission()


def download(link, paused=False):
    success, torrent_id = client.add_torrent(link, paused)
    return success, torrent_id
