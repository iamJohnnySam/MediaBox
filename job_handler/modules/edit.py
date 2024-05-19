from shared_models.job import Job
from job_handler.base_module import Module


class Edit(Module):
    def __init__(self, job: Job):
        super().__init__(job)

    def edit(self):
        pass
        # todo get job id
        # todo check if complete
        # todo check if master or author
        # todo print keyboard with options
