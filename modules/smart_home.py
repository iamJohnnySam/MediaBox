from brains.job import Job
from modules.base_module import Module
from tools.package_installer import import_or_install

import_or_install("tinytuya")

# todo


class TuyaSmartHome(Module):
    def __init__(self, job: Job):
        super().__init__(job)
