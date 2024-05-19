from shared_models.job import Job
from job_handler.base_module import Module


# todo

class Fitness(Module):
    def __init__(self, job: Job):
        super().__init__(job)
