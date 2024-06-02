import copy
from datetime import datetime

from common_workspace import global_var, queues
from shared_models.job import Job
from shared_tools.custom_exceptions import UnexpectedOperation
from shared_tools.logger import log


def transform_job(job: Job, new_function: str,
                  new_collection: list | str | bool | int | float | datetime = None,
                  keep_collection: bool = False) -> Job:
    job.function = new_function
    log(msg=f"Function updated to {job.function}")
    job.bypass_channel_check = True

    if not keep_collection:
        if new_collection is not None:
            if type(new_collection) is list:
                job.collection = new_collection
            elif type(new_collection) is datetime:
                job.collection = [new_collection.strftime(global_var.date_formats[0])]
            elif isinstance(new_collection, (str, bool, int, float)):
                job.collection = [new_collection]
            else:
                log(error_code=40002)
                raise UnexpectedOperation

        else:
            job.collection = []

    log(msg=f"Collection is {job.collection}")

    return job


def transform_and_queue_job(job: Job, new_function: str,
                            new_collection: list | str | bool | int | float | datetime = None,
                            keep_collection: bool = False):
    log(msg=f"Transforming job {job.function} to {new_function} and collection {new_collection}")
    job = transform_job(job, new_function, new_collection, keep_collection)
    queues.job_q.put(job)


def duplicate_and_transform_job(job: Job, new_function: str = None,
                                new_collection: list | str | bool | int | float | datetime = None,
                                keep_collection: bool = False) -> Job:
    new_job = copy.deepcopy(job)
    new_job.generate_new_id()
    if new_function is None:
        return new_job

    new_job = transform_job(new_job, new_function, new_collection, keep_collection)
    return new_job
