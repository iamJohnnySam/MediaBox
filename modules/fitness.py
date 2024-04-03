from brains.job import Job
from modules.base_module import Module


# todo

class Fitness(Module):
    def __init__(self, job: Job):
        super().__init__(job)
