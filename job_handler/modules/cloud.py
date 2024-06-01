import os

from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

from job_handler.base_module import Module
from shared_models import configuration
from shared_models.job import Job
from shared_tools.logger import log


class Cloud(Module):
    def __init__(self, job: Job):
        super().__init__(job)
        self.config = configuration.Configuration().google

        settings = {
            "client_config_backend": "service",
            "service_config": {
                "client_json_file_path": self.config["secret_location"],
            }
        }

        gauth = GoogleAuth(settings=settings)
        gauth.ServiceAuth()
        log(msg="Google drive authenticated")

        self.drive = GoogleDrive(gauth)

    def upload(self):
        success, path = self.check_value(index=0, description="upload files path")
        if not success:
            return

        for x in os.listdir(path):
            f = self.drive.CreateFile({'title': x})
            f.SetContentFile(os.path.join(path, x))
            f.Upload()
            log(msg=f"Uploaded: {path}")
            f = None
            log(msg=f"Stream cleared: {f}")
