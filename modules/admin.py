from datetime import datetime

import global_var
from database_manager.json_editor import JSONEditor
from job_handling.job import Job
from modules.base_module import Module


class Admin(Module):
    def __int__(self, job: Job):
        super().__init__(job)

    def alive(self):
        self.send_message(message=f"{str(self._job.chat_id)}\nHello{self._job.f_name}! I'm Alive and kicking!")
        self._job.complete()

    def time(self):
        self.send_message(message=str(datetime.now()))
        self._job.complete()

    def help(self):
        message = "--- AVAILABLE COMMANDS ---"

        # todo replace with sql table
        command_dictionary = JSONEditor(f'{global_var.telepot_commands}telepot_commands_'
                                        f'{self._job.telepot_account}.json').read()

        for command in command_dictionary.keys():
            if command.startswith('/'):
                message = message + "\n" + command + " - " + command_dictionary[command]["definition"]
            else:
                message = message + "\n\n" + command
        self.send_message(message=message)

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
