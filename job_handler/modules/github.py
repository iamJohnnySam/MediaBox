import git

from job_handler.base_module import Module
from shared_models import configuration
from shared_models.job import Job
from shared_models.message import Message
from shared_tools.logger import log


class GitHub(Module):
    def __init__(self, job: Job):
        super().__init__(job)
        self.config = configuration.Configuration().admin
        self.repo = git.Repo(self.config["location"])

    def pull_repo(self):
        current = self.repo.head.commit
        self.repo.remotes.origin.pull()
        if current != self.repo.head.commit:
            log(job_id=self.job.job_id, msg="Starting to Pull")
            self.repo.remotes.origin.pull()
            log(job_id=self.job.job_id, msg=f"Pull complete.")
            self.send_message(Message(job=self.job, send_string="Pull Complete..."))
        else:
            log(job_id=self.job.job_id, msg="Nothing to pull.")
