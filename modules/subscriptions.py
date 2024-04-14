import refs
from brains.job import Job
from database_manager.sql_connector import SQLConnector
from modules.base_module import Module
from tools.logger import log


class Subscriptions(Module):
    def __init__(self, job: Job):
        super().__init__(job)
        self.admin_db = SQLConnector(job.job_id, database=refs.db_admin)

    def manage_chat_group(self, group, add=True, remove=False):
        message_type = "info"
        where = f"chat_id = '{self._job.chat_id}' AND group_name = '{group}';"
        if not add ^ remove:
            msg = "Invalid command"
            message_type = "error"
        elif add and self.admin_db.check_exists(refs.tbl_groups, where) == 0:
            cols = "chat_id, group_name"
            vals = (self._job.chat_id, group)
            self.admin_db.insert(refs.tbl_groups, cols, vals)
            msg = f"Added {self._job.chat_id} to {group} group"
        elif remove and self.admin_db.check_exists(refs.tbl_groups, where) != 0:
            self.admin_db.delete(refs.tbl_groups, where)
            msg = f"Removed {self._job.chat_id} from {group} group"
        else:
            msg = "Nothing to do"

        log(self._job.job_id, msg, log_type=message_type)
        return msg
