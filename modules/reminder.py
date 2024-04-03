from brains.job import Job
from modules.base_module import Module


# todo


class Reminder(Module):
    def __init__(self, job: Job):
        super().__init__(job)

    # todo create job as reminder complete. Example Invest. If done how much invested and where to be added.