import os
import shutil

from shared_models.job import Job
from shared_tools.logger import log


def create_folder_if_not_exist(job: Job, location: str):
    if not os.path.exists(location):
        os.makedirs(location)
        log(job.job_id, f"Created folder at {location}")


def move_file(job: Job, old_location, new_location, file):
    create_folder_if_not_exist(job, new_location)
    destination = shutil.move(old_location, os.path.join(new_location, file))
    log(job.job_id, f"Moved '{file}' to '{destination}'")
    return destination


def move_files_and_directories(job: Job, source_folder, destination_folder):
    items = os.listdir(source_folder)
    for item in items:
        source_path = os.path.join(source_folder, item)
        destination_path = os.path.join(destination_folder, item)
        try:
            # Move the item to the destination folder
            shutil.move(source_path, destination_path)
            log(job.job_id, f"Moved '{item}' to '{destination_folder}'")
        except Exception as e:
            log(job.job_id, f"Failed to move '{item}': {str(e)}")


def get_file_and_directory(job: Job, path):
    files_list = []
    directories_list = []
    if os.path.exists(path):
        contents = os.listdir(path)
        for item in contents:
            item_path = os.path.join(path, item)
            if os.path.isfile(item_path):
                files_list.append(item)
            elif os.path.isdir(item_path):
                directories_list.append(item)

    log(job.job_id, f'Got files in {path}.')
    return files_list, directories_list


def remove_directory(job: Job, path):
    sub_files, sub_directories = get_file_and_directory(job, path)
    if len(sub_directories) == 0 and len(sub_files) == 0:
        try:
            os.rmdir(path)
            log(job.job_id, f"Directory '{path}' has been successfully deleted.")
        except OSError as e:
            log(job.job_id, f"Error: {str(e)}")
    else:
        log(job.job_id, f"Cannot Delete '{path}'. Not empty!", log_type="warn")
