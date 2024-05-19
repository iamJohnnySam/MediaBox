import os
import shutil

import refs
from shared_models.job import Job
from shared_models.message import Message
from job_handler.base_module import Module
from tools import params
from shared_tools import file_tools
from shared_tools.logger import log
from tools.word_tools import breakdown_torrent_file_name


class RefactorFolder(Module):
    module = 'media'

    def __init__(self, job: Job):
        super().__init__(job)
        self.path = params.get_param(self.module, 'download')
        self.send_string = ""

    def clean_torrent_downloads(self):
        self.send_string = "New additions to MediaBox:"
        files, directories = file_tools.get_file_and_directory(self._job, self.path)
        if len(files) == 0 and len(directories) == 0:
            log(self._job.job_id, "Nothing to refactor")
            return

        self._job.is_background_task = False

        self._sort_torrent_files(files, self.path)

        for directory in directories:
            last_loc = None
            directory_path, sub_directories, get_last_loc = self._torrent_step_1(self.path, directory)
            if get_last_loc is not None:
                last_loc = get_last_loc

            if last_loc is None and len(sub_directories) > 0:
                for sub_directory in sub_directories:
                    sub_last_loc = None
                    sub_directory_path, sub_sub_directories, get_sub_last_loc = self._torrent_step_1(directory_path,
                                                                                                     sub_directory)
                    if get_sub_last_loc is not None:
                        sub_last_loc = get_sub_last_loc

                    if sub_last_loc is not None:
                        self._torrent_step_2(sub_sub_directories, sub_directory_path, sub_last_loc)
                    else:
                        log(self._job.job_id, f'{sub_directory_path}, Base location - {sub_last_loc}',
                            log_type="error", error_code=50005)
                    file_tools.remove_directory(self._job, sub_directory_path)

            elif last_loc is not None:
                self._torrent_step_2(sub_directories, directory_path, last_loc)
            else:
                log(self._job.job_id, f'Folder Refactor Error - {directory_path}, Base location - {last_loc}',
                    log_type="error", error_code=50004)

            file_tools.remove_directory(self._job, directory_path)

        self.send_message(Message(send_string=self.send_string, group=refs.group_tv_show))

    def _torrent_step_1(self, path, directory):
        directory_path = os.path.join(path, directory)
        sub_files, sub_directories = file_tools.get_file_and_directory(self._job, directory_path)
        last_loc = self._sort_torrent_files(sub_files, directory_path)
        return directory_path, sub_directories, last_loc

    def _torrent_step_2(self, sub_directories, directory_path, last_loc):
        if "Subs" in sub_directories:
            self._move_subs_folder(directory_path, last_loc)

        sub_files, sub_directories = file_tools.get_file_and_directory(self._job, directory_path)
        for sub_directory in sub_directories:
            file_tools.move_files_and_directories(self._job, os.path.join(directory_path, sub_directory),
                                                  last_loc)
            file_tools.remove_directory(self._job, os.path.join(directory_path, sub_directory))

    def _move_subs_folder(self, directory_path, last_loc):
        subs_folder = os.path.join(directory_path, "Subs")
        sub_files, sub_directories = file_tools.get_file_and_directory(self._job, subs_folder)

        destination = os.path.join(last_loc, "Subs")
        file_tools.create_folder_if_not_exist(self._job, os.path.dirname(destination))

        for file in sub_files:
            dst_path = os.path.join(destination, file)
            file_tools.create_folder_if_not_exist(self._job, destination)
            file_path = os.path.join(subs_folder, file)
            shutil.move(file_path, dst_path)
            log(self._job.job_id, f"Moved {file_path} -> {dst_path}")

        file_tools.remove_directory(self._job, subs_folder)

    def _sort_torrent_files(self, files, directory):
        base_loc = None
        for file in files:
            file_name, tv_show, movie, subtitle, base_name = breakdown_torrent_file_name(self._job, file)
            log(self._job.job_id, f'{file_name}, {tv_show}, {movie}, {subtitle}, {base_name}')
            if tv_show and not movie:
                base_loc = os.path.join(params.get_param(self.module, 'tv_shows'), base_name)
                file_tools.move_file(self._job, os.path.join(directory, file),
                                     base_loc,
                                     file_name)
                self.send_string = self.send_string + "\n" + file_name

            elif movie and not tv_show:
                base_loc = os.path.join(params.get_param(self.module, 'movies'), base_name)
                file_tools.move_file(self._job, os.path.join(directory, file),
                                     base_loc,
                                     file_name)
                self.send_string = self.send_string + "\n" + file_name

            else:
                base_loc = os.path.join(params.get_param(self.module, 'unknown_files'), base_name)
                file_tools.move_file(self._job, os.path.join(directory, file),
                                     base_loc,
                                     base_name + file_name)
                base_loc = None
        return base_loc
