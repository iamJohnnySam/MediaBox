import os
import shutil

from common_workspace import queues
from shared_models import configuration
from shared_models.job import Job
from shared_models.message import Message
from job_handler.base_module import Module
from shared_tools import file_tools
from shared_tools.job_tools import duplicate_and_transform_job
from shared_tools.logger import log
from shared_tools.movie_tools import get_movie_info
from shared_tools.sql_connector import SQLConnector
from shared_tools.word_tools import breakdown_torrent_file_name


class RefactorFolder(Module):

    def __init__(self, job: Job):
        super().__init__(job)
        self.config = configuration.Configuration().media

        self.downloads_path = self.config['download']
        self.movies_path = self.config['movies']
        self.shows_path = self.config['tv_shows']
        self.send_string = ""

    def clean_torrent_downloads(self):
        self.send_string = "New additions to MediaBox:"
        files, directories = file_tools.get_file_and_directory(self.job, self.downloads_path)
        if len(files) == 0 and len(directories) == 0:
            log(self.job.job_id, "Nothing to refactor")
            return

        self.job.is_background_task = False

        self._sort_torrent_files(files, self.downloads_path)

        for directory in directories:
            last_loc = None
            directory_path, sub_directories, get_last_loc = self._torrent_step_1(self.downloads_path, directory)
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
                        log(self.job.job_id, f'{sub_directory_path}, Base location - {sub_last_loc}',
                            log_type="error", error_code=50005)
                    file_tools.remove_directory(self.job, sub_directory_path)

            elif last_loc is not None:
                self._torrent_step_2(sub_directories, directory_path, last_loc)
            else:
                log(self.job.job_id, f'Folder Refactor Error - {directory_path}, Base location - {last_loc}',
                    log_type="error", error_code=50004)

            file_tools.remove_directory(self.job, directory_path)

        self.send_message(Message(send_string=self.send_string, group=self.config["telegram_group"]))

    def _torrent_step_1(self, path, directory):
        directory_path = os.path.join(path, directory)
        sub_files, sub_directories = file_tools.get_file_and_directory(self.job, directory_path)
        last_loc = self._sort_torrent_files(sub_files, directory_path)
        return directory_path, sub_directories, last_loc

    def _torrent_step_2(self, sub_directories, directory_path, last_loc):
        if "Subs" in sub_directories:
            self._move_subs_folder(directory_path, last_loc)

        sub_files, sub_directories = file_tools.get_file_and_directory(self.job, directory_path)
        for sub_directory in sub_directories:
            file_tools.move_files_and_directories(self.job, os.path.join(directory_path, sub_directory),
                                                  last_loc)
            file_tools.remove_directory(self.job, os.path.join(directory_path, sub_directory))

    def _move_subs_folder(self, directory_path, last_loc):
        subs_folder = os.path.join(directory_path, "Subs")
        sub_files, sub_directories = file_tools.get_file_and_directory(self.job, subs_folder)

        destination = os.path.join(last_loc, "Subs")
        file_tools.create_folder_if_not_exist(self.job, os.path.dirname(destination))

        for file in sub_files:
            dst_path = os.path.join(destination, file)
            file_tools.create_folder_if_not_exist(self.job, destination)
            file_path = os.path.join(subs_folder, file)
            shutil.move(file_path, dst_path)
            log(self.job.job_id, f"Moved {file_path} -> {dst_path}")

        file_tools.remove_directory(self.job, subs_folder)

    def _sort_torrent_files(self, files, directory):
        base_loc = None
        for file in files:
            file_name, tv_show, movie, subtitle, base_name = breakdown_torrent_file_name(self.job, file)
            log(self.job.job_id, f'{file_name}, {tv_show}, {movie}, {subtitle}, {base_name}')
            if tv_show and not movie:
                base_loc = os.path.join(self.shows_path, base_name)
                file_tools.move_file(self.job, os.path.join(directory, file),
                                     base_loc,
                                     file_name)
                self.send_string = self.send_string + "\n" + file_name

            elif movie and not tv_show:
                base_loc = os.path.join(self.movies_path, base_name)
                file_tools.move_file(self.job, os.path.join(directory, file),
                                     base_loc,
                                     file_name)
                self.send_string = self.send_string + "\n" + file_name

            else:
                base_loc = os.path.join(self.config['unknown_files'], base_name)
                file_tools.move_file(self.job, os.path.join(directory, file),
                                     base_loc,
                                     base_name + file_name)
                base_loc = None
        return base_loc

    def update_movie_db(self):
        db = SQLConnector(job_id=self.job.job_id, database=self.config["database"])

        files, directories = file_tools.get_file_and_directory(self.job, self.movies_path)
        if len(directories) == 0:
            log(self.job.job_id, "Nothing to update")
            return

        for movie in directories:
            if not db.check_exists(table=self.config["tbl_available_movies"], where={"folder_name": movie}):
                new_job = duplicate_and_transform_job(self.job, new_function="add_movie_to_db", new_collection=[movie])
                queues.job_q.put(new_job)
            else:
                db.update(table=self.config["tbl_available_movies"],
                          update={"available": 1},
                          where={"folder_name": movie})

    def update_show_db(self):
        db = SQLConnector(job_id=self.job.job_id, database=self.config["database"])

        files, directories = file_tools.get_file_and_directory(self.job, self.shows_path)
        if len(directories) == 0:
            log(self.job.job_id, "Nothing to update")
            return

        for show in directories:
            files, directories = file_tools.get_file_and_directory(self.job, os.path.join(self.shows_path, show))
            for episode in files:
                if not db.check_exists(table=self.config["tbl_available_shows"],
                                       where={"folder_name": show, "file_name": episode}):
                    new_job = duplicate_and_transform_job(self.job, new_function="add_show_to_db",
                                                          new_collection=[show, episode])
                    queues.job_q.put(new_job)
                else:
                    db.update(table=self.config["tbl_available_shows"],
                              update={"available": 1},
                              where={"folder_name": show, "file_name": episode})

    def add_movie_to_db(self):
        # 0 - Original Title
        # 1 - Actual Title

        success, movie_name = self.check_value(index=0, description="movie title")
        if not success:
            return

        movie_titles, movie_posters = get_movie_info(job_id=self.job.job_id, movie=movie_name)

        if len(movie_titles) == 1:
            default = movie_titles[0]
        elif len(movie_titles) == 0:
            log(job_id=self.job.job_id, msg=f"Movie {movie_name} not found in database")
            return
        else:
            default = ""

        success, movie = self.check_value(index=1, description=f"actual movie title of {movie_name}",
                                          option_list=movie_titles, default=default)
        if not success:
            return

        SQLConnector(job_id=self.job.job_id,
                     database=self.config["database"]).insert(table=self.config["tbl_available_movies"],
                                                              columns="folder_name, name",
                                                              val=(movie_name, movie))

    def add_show_to_db(self):
        # 0 - Folder Name
        # 1 - File Name

        success, show_name = self.check_value(index=0, description="show title")
        if not success:
            return

        success, show_name = self.check_value(index=1, description="episode name")
        if not success:
            return

        # todo
