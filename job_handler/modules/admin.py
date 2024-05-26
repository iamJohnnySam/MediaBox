from datetime import datetime

from common_workspace import global_var
from shared_models import configuration
from shared_models.message import Message
from shared_tools.json_editor import JSONEditor
from shared_models.job import Job
from job_handler.base_module import Module


class Admin(Module):
    def __init__(self, job: Job):
        super().__init__(job)
        config = configuration.Configuration()
        self.telegram_config = config.telegram
        self.command_config = config.commands

    def alive(self):
        self.send_message(Message(f"Hello {self.job.username} (chat id: {str(self.job.chat_id)})!\n"
                                  f"I'm Alive and kicking!"))

    def time(self):
        self.send_message(Message(str(datetime.now())))

    def help(self):
        message = "--- AVAILABLE COMMANDS ---"
        command_dict = JSONEditor(self.command_config["commands"]).read()
        add_command = ""

        for command in command_dict.keys():
            if type(command_dict[command]) != bool:
                if type(command_dict[command]) == str:
                    definition = command_dict[command]
                elif type(command_dict[command]) == dict and 'definition' in command_dict[command].keys():
                    definition = command_dict[command]['definition']
                else:
                    definition = command

                a = "bots" in command_dict[command].keys() and self.job.channel not in command_dict[command]["bots"]
                b = self.job.channel in self.telegram_config["accept_all_commands"]
                c = "all_bots" in command_dict[command] and command_dict[command]["all_bots"]
                d = not ("skip_bots" in command_dict[command] and command_dict[command]["skip_bots"])

                if d and (a or b or c):
                    if add_command != "":
                        message = message + add_command
                        add_command = ""
                    message = f"{message}\n/{command} - {definition}"

            else:
                add_command = "\n\n" + command
        self.send_message(Message(message))

    def start_over(self):
        if self.is_master:
            global_var.flag_stop.value = True
            global_var.flag_restart.value = True
            self.send_message(Message("Completing ongoing tasks before restart. Please wait.", job=self.job))
        else:
            self.send_message(Message("This is a server command. Requesting admin...", job=self.job))
            self.send_admin(Message(f"/start_over requested by {self.job.username}."))

    def exit_all(self):
        if self.is_master:
            global_var.flag_stop.value = True
            self.send_message(Message("Completing ongoing tasks before exit. Please wait.", job=self.job))
        else:
            self.send_message(Message("This is a server command. Requesting admin...", job=self.job))
            self.send_admin(Message(f"/exit_all requested by {self.job.username}."))

    def reboot_pi(self):
        if self.is_master:
            global_var.flag_stop.value = True
            global_var.flag_reboot.value = True
            self.send_message(Message("Completing ongoing tasks before reboot. Please wait.", job=self.job))
        else:
            self.send_message(Message("This is a server command. Requesting admin...", job=self.job))
            self.send_admin(Message(f"/reboot_pi requested by {self.job.username}."))
