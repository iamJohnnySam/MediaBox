from schedule import Job

from job_handler.base_module import Module


class SyncMe(Module):
    def __init__(self, job: Job):
        # todo
        super().__init__(job)


class FolderManager(Module):
    def __init__(self, job: Job):
        super().__init__(job)