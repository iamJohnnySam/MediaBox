from transmission_rpc import Client

from shared_models.job import Job
from shared_models.message import Message
from job_handler.base_module import Module
from shared_tools.logger import log


class Transmission(Module):
    def __init__(self, job: Job):
        super().__init__(job)
        self.client = Client()
        self.active_torrents = {}

    def list_torrents(self):
        torrent_list = self.client.get_torrents()
        self.active_torrents = {}
        for torrent in torrent_list:
            success, torrent_name = self._add_torrent_to_list(torrent)
            if not success:
                log(job_id=self.job.job_id, error_code=50001)

        return self.active_torrents

    def add_torrent(self):
        success, path = self.check_value(index=0, description="torrent path")
        success, paused = self.check_value(index=1, description="torrent paused", check_int=True, default='0')

        torrent = self.client.add_torrent(path, paused=paused)
        success, torrent_name = self._add_torrent_to_list(torrent)
        log(self.job.job_id, msg=f"Torrent Added: {torrent_name}")
        if success:
            self.send_message(Message(f"Torrent {torrent_name} added to queue."))
            if not self.is_master:
                self.send_admin(Message(f"Torrent {torrent_name} added to queue."))

        return success, torrent_name

    def _add_torrent_to_list(self, torrent):
        torrent_id = torrent.id
        if torrent_id not in self.active_torrents.keys():
            self.active_torrents[torrent_id] = torrent
            log(job_id=self.job.job_id, msg=f'Torrent Added - {torrent.name}')
            return True, torrent.name
        else:
            return False, ""

    def delete_downloaded(self):
        self.list_torrents()
        for torrent_number in self.active_torrents.keys():
            if self.active_torrents[torrent_number].percent_done == 1:
                torrent_id = self.active_torrents[torrent_number].id
                self.client.remove_torrent(torrent_id)
                log(job_id=self.job.job_id,
                    msg=f'Torrent deleted - {self.active_torrents[torrent_number].name}')

    def send_list(self):
        self.list_torrents()

        if len(self.active_torrents.keys()) == 0:
            return_string = "No Active Torrents"
        else:
            return_string = "- ACTIVE TORRENTS- "

        for torrent_number in self.active_torrents.keys():
            torrent_path = str(self.active_torrents[torrent_number].name)
            completion = str(int(self.active_torrents[torrent_number].percent_done * 100)) + "%"
            return_string = return_string + "\n" + str(torrent_number) + ": " + torrent_path + " - " + completion

        self.send_message(Message(return_string, job=self.job))
