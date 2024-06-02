from shared_models.job import Job
from job_handler.base_module import Module
from shared_tools import group_tools
from shared_tools.logger import log


class Subscriptions(Module):
    def __init__(self, job: Job):
        super().__init__(job)

    def manage_chat_group(self, group, remove=False):
        if not remove:
            success = group_tools.add_to_group(group=group, chat_id=self.job.chat_id)
            op_type = "Added"
        else:
            success = group_tools.remove_from_group(group=group, chat_id=self.job.chat_id)
            op_type = "Removed"

        if not success:
            log(job_id=self.job.job_id, msg="Nothing to do")
        else:
            log(job_id=self.job.job_id, msg=f"{op_type} {self.job.chat_id} to {group} group")
