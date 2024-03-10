from transmission_rpc import Client

import global_var
from job_handling.job import Job
from modules.base_module import Module
from tools import logger
from maintenance.folder_refactor import RefactorFolder


class Transmission(Module):
    def __init__(self, job: Job):
        super().__init__(job)
        self.client = Client()
        self.active_torrents = {}

    def list_torrents(self):
        torrent_list = self.client.get_torrents()
        self.active_torrents = {}
        for torrent in torrent_list:
            success, torrent_name = self.add_torrent_to_list(torrent)
            if not success:
                logger.log(job_id=self._job.job_id, error_code=50001)

    def add_torrent(self, path, paused=False):
        torrent = self.client.add_torrent(path, paused=paused)
        success, torrent_name = self.add_torrent_to_list(torrent)
        return success, torrent_name

    def add_torrent_to_list(self, torrent):
        torrent_id = torrent.id
        if torrent_id not in self.active_torrents.keys():
            self.active_torrents[torrent_id] = torrent
            logger.log(job_id=self._job.job_id, msg=f'Torrent Added - {torrent.name}')
            return True, torrent.name
        else:
            return False, ""

    def delete_downloaded(self):
        self.list_torrents()
        for torrent_number in self.active_torrents.keys():
            if self.active_torrents[torrent_number].percent_done == 1:
                torrent_id = self.active_torrents[torrent_number].id
                self.client.remove_torrent(torrent_id)
                logger.log(job_id=self._job.job_id,
                           msg=f'Torrent deleted - {self.active_torrents[torrent_number].name}')

# todo add as Task
# client = Transmission()
#
#
# def download(link, paused=False):
#     success, torrent_name = client.add_torrent(link, paused)
#     return success, torrent_name
#
#
# def list_all():
#     client.list_torrents()
#     if len(client.active_torrents.keys()) == 0:
#         return_string = "No Active Torrents"
#     else:
#         return_string = "- ACTIVE TORRENTS- "
#
#     for torrent_number in client.active_torrents.keys():
#         # torrent_path = str(client.active_torrents[torrent_number].torrent_file).split("/")
#         torrent_path = str(client.active_torrents[torrent_number].name)
#         completion = str(int(client.active_torrents[torrent_number].percent_done * 100)) + "%"
#         return_string = return_string + "\n" + str(torrent_number) + ": " + torrent_path + " - " + completion
#
#     return return_string
#
#
# def torrent_complete_sequence():
#     logger.log("Starting Transmission Cleanup")
#     client.delete_downloaded()
#     logger.log("Starting Downloads Refactor")
#     RefactorFolder(global_var.torrent_download).clean_torrent_downloads()
#     logger.log("Sequence Complete")
