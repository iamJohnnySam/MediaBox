from datetime import datetime

from common_workspace import global_var
from shared_models import configuration
from shared_models.message import Message
from shared_tools.json_editor import JSONEditor
from shared_models.job import Job
from database_manager.sql_connector import SQLConnector
from job_handler.base_module import Module


class Admin(Module):
    def __int__(self, job: Job):
        super().__init__(job)
        self.telegram_config = configuration.Configuration().telegram
        self._db = SQLConnector(job.job_id, database=self.telegram_config["database"])

    def alive(self):
        self.send_message(Message(f"Hello {self._job.f_name} (chat id: {str(self._job.chat_id)})!\n"
                                  f"I'm Alive and kicking!"))
        self._job.complete()

    def time(self):
        self.send_message(Message(str(datetime.now())))
        self._job.complete()

    def help(self):
        message = "--- AVAILABLE COMMANDS ---"
        command_dictionary = JSONEditor(self.telegram_config["commands"]).read()
        add_command = ""

        for command in command_dictionary.keys():
            if type(command_dictionary[command]) != bool:
                if type(command_dictionary[command]) == str:
                    definition = command_dictionary[command]
                elif type(command_dictionary[command]) == dict and 'definition' in command_dictionary[command].keys():
                    definition = command_dictionary[command]['definition']
                else:
                    definition = command

                a = self._job.telepot_account in command_dictionary[command]
                b = self._job.telepot_account in self.telegram_config["accept_all_commands"]
                c = "all_bots" in command_dictionary[command]

                if a or b or c:
                    if add_command != "":
                        message = message + add_command
                        add_command = ""
                    message = f"{message}\n/{command} - {definition}"

            else:
                add_command = "\n\n" + command
        self.send_message(Message(message))

    def start_over(self):
        if self._job.is_master:
            global_var.flag_stop.value = True
            global_var.flag_restart.value = True
            self.send_message(Message("Completing ongoing tasks before restart. Please wait.", job=self._job))
        else:
            self.send_message(Message("This is a server command. Requesting admin...", job=self._job))
            self.send_admin(Message(f"/start_over requested by {self._job.f_name}."))
        self._job.complete()

    def exit_all(self):
        if self._job.is_master:
            global_var.flag_stop.value = True
            self.send_message(Message("Completing ongoing tasks before exit. Please wait.", job=self._job))
        else:
            self.send_message(Message("This is a server command. Requesting admin...", job=self._job))
            self.send_admin(Message(f"/exit_all requested by {self._job.f_name}."))
        self._job.complete()

    def reboot_pi(self):
        if self._job.is_master:
            global_var.flag_stop.value = True
            global_var.flag_reboot.value = True
            self.send_message(Message("Completing ongoing tasks before reboot. Please wait.", job=self._job))
        else:
            self.send_message(Message("This is a server command. Requesting admin...", job=self._job))
            self.send_admin(Message(f"/reboot_pi requested by {self._job.f_name}."))
        self._job.complete()
