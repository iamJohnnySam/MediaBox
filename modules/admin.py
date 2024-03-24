from datetime import datetime

import global_variables
import refs
from communication.message import Message
from database_manager.json_editor import JSONEditor
from brains.job import Job
from database_manager.sql_connector import sql_databases
from modules.base_module import Module
from tools.logger import log


class Admin(Module):
    def __int__(self, job: Job):
        super().__init__(job)
        self._db = sql_databases["administration"]

    def alive(self):
        self.send_message(Message(f"Hello {self._job.f_name} (chat id: {str(self._job.chat_id)})!\n"
                                  f"I'm Alive and kicking!"))
        self._job.complete()

    def time(self):
        self.send_message(Message(str(datetime.now())))
        self._job.complete()

    def help(self):
        message = "--- AVAILABLE COMMANDS ---"
        command_dictionary = JSONEditor(refs.db_telepot_commands).read()

        for command in command_dictionary.keys():
            if type(command_dictionary[command]) != bool:
                if type(command_dictionary[command]) == str:
                    definition = command_dictionary[command]
                elif type(command_dictionary[command]) == dict and 'definition' in command_dictionary[command].keys():
                    definition = command_dictionary[command]['definition']
                else:
                    definition = command
                message = f"{message}\n/{command} - {definition}"
            else:
                message = message + "\n\n" + command
        self.send_message(Message(message))

    def start_over(self):
        if self._job.is_master:
            global_variables.stop_all = True
            global_variables.stop_cctv = True
            global_variables.restart = True
            self.send_message(Message("Completing ongoing tasks before restart. Please wait."))
        else:
            self.send_message(Message("This is a server command. Requesting admin..."))
            self.send_admin(Message(f"/start_over requested by {self._job.f_name}."))
        self._job.complete()

    def exit_all(self):
        if self._job.is_master:
            global_variables.stop_all = True
            global_variables.stop_cctv = True
            self.send_message(Message("Completing ongoing tasks before exit. Please wait."))
        else:
            self.send_message(Message("This is a server command. Requesting admin..."))
            self.send_admin(Message(f"/exit_all requested by {self._job.f_name}."))
        self._job.complete()

    def reboot_pi(self):
        if self._job.is_master:
            global_variables.stop_all = True
            global_variables.stop_cctv = True
            global_variables.reboot_pi = True
            self.send_message(Message("Completing ongoing tasks before reboot. Please wait."))
        else:
            self.send_message(Message("This is a server command. Requesting admin..."))
            self.send_admin(Message(f"/reboot_pi requested by {self._job.f_name}."))
        self._job.complete()

    def add_me_to_cctv(self):
        self.manage_chat_group("cctv", self._job.chat_id)
        self.send_message(Message("Done", job=self._job))
        self._job.complete()

    def add_me_to_news(self):
        self.manage_chat_group("news", self._job.chat_id)
        self.send_message(Message("Done", job=self._job))
        self._job.complete()

    def add_me_to_baby(self):
        self.manage_chat_group("modules", self._job.chat_id)
        self.send_message(Message("Done", job=self._job))
        self._job.complete()

    def remove_me_from_cctv(self):
        self.manage_chat_group("cctv", self._job.chat_id, add=False, remove=True)
        self.send_message(Message("Done", job=self._job))
        self._job.complete()

    def remove_me_from_news(self):
        self.manage_chat_group("news", self._job.chat_id, add=False, remove=True)
        self.send_message(Message("Done", job=self._job))
        self._job.complete()

    def remove_me_from_baby(self):
        self.manage_chat_group("modules", self._job.chat_id, add=False, remove=True)
        self.send_message(Message("Done", job=self._job))
        self._job.complete()

    def manage_chat_group(self, group, chat_id, add=True, remove=False):
        message_type = "debug"
        where = f"chat_id = '{chat_id}' AND group_name = '{group}';"
        if not add ^ remove:
            msg = "Invalid command"
            message_type = "error"
        elif add and self._db.exists(refs.tbl_groups, where) == 0:
            cols = "chat_id, group_name"
            vals = (chat_id, group)
            self._db.insert(refs.tbl_groups, cols, vals)
            msg = f"Added {chat_id} to {group} group"
        elif remove and self._db.exists(refs.tbl_groups, where) != 0:
            self._db.run_sql(f"DELETE FROM {refs.tbl_groups} WHERE " + where)
            msg = f"Removed {chat_id} from {group} group"
        else:
            msg = "Nothing to do"

        log(job_id=self._job.job_id, msg=msg, log_type=message_type)
        return msg
