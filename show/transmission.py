import requests
from transmission_rpc import Client

import logger


class Transmission:
    def __init__(self):
        self.client = Client()
        self.active_torrents = {}
        self.source = "TRM"

    def list_torrents(self):
        torrent_list = self.client.get_torrents()
        self.active_torrents = {}
        for torrent in torrent_list:
            success, torrent_id = self.add_torrent_to_list(torrent)
            if not success:
                logger.log("Torrent Listing Error", self.source, message_type="error")

    def add_torrent(self, path, paused=False):
        torrent = self.client.add_torrent(path, paused=paused)
        success, torrent_id = self.add_torrent_to_list(torrent)
        return success, torrent_id

    def add_torrent_to_list(self, torrent):
        torrent_id = torrent.id
        if torrent_id not in self.active_torrents.keys():
            self.active_torrents[torrent_id] = torrent
            return True, torrent_id
        else:
            return False, ""


client = Transmission()


def download(link, paused=False):
    success, torrent_id = client.add_torrent(link, paused)
    return success, torrent_id


def list_all():
    client.list_torrents()
    if len(client.active_torrents.keys()) == 0:
        return_string = "No Active Torrents"
    else:
        return_string = "- ACTIVE TORRENTS- "

    number = 0
    for torrent in client.active_torrents.keys():
        torrent_path = str(client.active_torrents[torrent].torrent_file).split("/")
        completion = str(client.active_torrents[torrent].percent_complete*100) + "%"
        return_string = return_string + "\n" + str(number) + ": " + str(torrent_path[-1] + " - " + completion)
        number = number + 1

    return return_string
