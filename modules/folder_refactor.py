import os
import shutil

import refs
from brains.job import Job
from communication.message import Message
from modules.base_module import Module
from tools.logger import log
from tools.word_tools import breakdown_torrent_file_name


class RefactorFolder(Module):

    def __init__(self, job: Job, path):
        super().__init__(job)
        self.path = path
        self.send_string = ""

    def clean_torrent_downloads(self):
        self.send_string = "New additions to MediaBox:"
        files, directories = self.get_file_and_directory(self.path)
        if len(files) == 0 and len(directories) == 0:
            log(self._job.job_id, "Nothing to refactor")
            return

        self._job.is_background_task = False

        self.sort_torrent_files(files, self.path)

        for directory in directories:
            last_loc = None
            directory_path, sub_directories, get_last_loc = self.torrent_step_1(self.path, directory)
            if get_last_loc is not None:
                last_loc = get_last_loc

            if last_loc is None and len(sub_directories) > 0:
                for sub_directory in sub_directories:
                    sub_last_loc = None
                    sub_directory_path, sub_sub_directories, get_sub_last_loc = self.torrent_step_1(directory_path,
                                                                                                    sub_directory)
                    if get_sub_last_loc is not None:
                        sub_last_loc = get_sub_last_loc

                    if sub_last_loc is not None:
                        self.torrent_step_2(sub_sub_directories, sub_directory_path, sub_last_loc)
                    else:
                        log(self._job.job_id, f'{sub_directory_path}, Base location - {sub_last_loc}',
                            log_type="error", error_code=50005)
                    self.remove_directory(sub_directory_path)

            elif last_loc is not None:
                self.torrent_step_2(sub_directories, directory_path, last_loc)
            else:
                log(self._job.job_id, f'Folder Refactor Error - {directory_path}, Base location - {last_loc}',
                    log_type="error", error_code=50004)

            self.remove_directory(directory_path)

        self.send_message(Message(send_string=self.send_string, group=refs.group_tv_show))

    def torrent_step_1(self, path, directory):
        directory_path = os.path.join(path, directory)
        sub_files, sub_directories = self.get_file_and_directory(directory_path)
        last_loc = self.sort_torrent_files(sub_files, directory_path)
        return directory_path, sub_directories, last_loc

    def torrent_step_2(self, sub_directories, directory_path, last_loc):
        if "Subs" in sub_directories:
            self.move_subs_folder(directory_path, last_loc)

        sub_files, sub_directories = self.get_file_and_directory(directory_path)
        for sub_directory in sub_directories:
            self.move_files_and_directories(os.path.join(directory_path, sub_directory),
                                            last_loc)
            self.remove_directory(os.path.join(directory_path, sub_directory))

    def move_subs_folder(self, directory_path, last_loc):
        subs_folder = os.path.join(directory_path, "Subs")
        sub_files, sub_directories = self.get_file_and_directory(subs_folder)

        destination = os.path.join(last_loc, "Subs")
        if not os.path.exists(os.path.dirname(destination)):
            os.makedirs(os.path.dirname(destination))

        for file in sub_files:
            dst_path = os.path.join(destination, file)
            file_path = os.path.join(subs_folder, file)
            shutil.move(file_path, dst_path)
            log(self._job.job_id, f"Moved {file_path} -> {dst_path}")

        self.remove_directory(subs_folder)

    def sort_torrent_files(self, files, directory):
        base_loc = None
        for file in files:
            file_name, tv_show, movie, subtitle, base_name = breakdown_torrent_file_name(self._job, file)
            log(self._job.job_id, f'{file_name}, {tv_show}, {movie}, {subtitle}, {base_name}')
            if tv_show and not movie:
                base_loc = os.path.join(refs.torrent_tv_shows, base_name)
                self.move_file(os.path.join(directory, file),
                               base_loc,
                               file_name)
                self.send_string = self.send_string + "\n" + file_name

            elif movie and not tv_show:
                base_loc = os.path.join(refs.torrent_movies, base_name)
                self.move_file(os.path.join(directory, file),
                               base_loc,
                               file_name)
                self.send_string = self.send_string + "\n" + file_name

            else:
                base_loc = os.path.join(refs.torrent_unknown, base_name)
                self.move_file(os.path.join(directory, file),
                               base_loc,
                               base_name + file_name)
                base_loc = None
        return base_loc

    def get_file_and_directory(self, path):
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

        log(self._job.job_id, f'Got files in {path}.')
        return files_list, directories_list

    def move_file(self, old_location, new_location, file):
        if not os.path.exists(new_location):
            os.makedirs(new_location)
        destination = shutil.move(old_location, os.path.join(new_location, file))
        log(self._job.job_id, f"Moved '{file}' to '{destination}'")
        return destination

    def move_files_and_directories(self, source_folder, destination_folder):
        items = os.listdir(source_folder)
        for item in items:
            source_path = os.path.join(source_folder, item)
            destination_path = os.path.join(destination_folder, item)
            try:
                # Move the item to the destination folder
                shutil.move(source_path, destination_path)
                log(self._job.job_id, f"Moved '{item}' to '{destination_folder}'")
            except Exception as e:
                log(self._job.job_id, f"Failed to move '{item}': {str(e)}")

    def remove_directory(self, path):
        sub_files, sub_directories = self.get_file_and_directory(path)
        if len(sub_directories) == 0 and len(sub_files) == 0:
            try:
                os.rmdir(path)
                log(self._job.job_id, f"Directory '{path}' has been successfully deleted.")
            except OSError as e:
                log(self._job.job_id, f"Error: {str(e)}")
        else:
            log(self._job.job_id, f"Cannot Delete '{path}'. Not empty!", log_type="warn")
