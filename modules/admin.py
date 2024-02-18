from datetime import datetime

import global_var
from module.job import Job
from module.module import Module


class Admin(Module):
    def __int__(self, job: Job):
        super().__init__(job)

    def alive(self):
        self.send_message(message=f"{str(self._job.chat_id)}\nHello{self._job.f_name}! I'm Alive and kicking!")
        self._job.complete()

    def time(self):
        self.send_message(message=str(datetime.now()))
        self._job.complete()

    def start_over(self):
        if self._job.is_master:
            global_var.stop_all = True
            global_var.stop_cctv = True
            global_var.restart = True
            self.send_message(message="Completing ongoing tasks before restart. Please wait.")
        else:
            self.send_message(message="This is a server command. Requesting admin...")
            self.send_admin(message=f"/start_over requested by {self._job.f_name}.")
        self._job.complete()

    def exit_all(self):
        if self._job.is_master:
            global_var.stop_all = True
            global_var.stop_cctv = True
            self.send_message(message="Completing ongoing tasks before exit. Please wait.")
        else:
            self.send_message(message="This is a server command. Requesting admin...")
            self.send_admin(message=f"/exit_all requested by {self._job.f_name}.")
        self._job.complete()

    def reboot_pi(self):
        if self._job.is_master:
            global_var.stop_all = True
            global_var.stop_cctv = True
            global_var.reboot_pi = True
            self.send_message(message="Completing ongoing tasks before reboot. Please wait.")
        else:
            self.send_message(message="This is a server command. Requesting admin...")
            self.send_admin(message=f"/reboot_pi requested by {self._job.f_name}.")
        self._job.complete()
