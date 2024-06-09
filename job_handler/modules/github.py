import git

from job_handler.base_module import Module
from shared_models.job import Job


class GitHub(Module):
    def __init__(self, job: Job):
        super().__init__(job)
        self.repo = git.Repo('/')

    def pull_repo(self):
        current = self.repo.head.commit
        self.repo.remotes.origin.pull()
        if current != self.repo.head.commit:
            self.repo.remotes.origin.pull()
