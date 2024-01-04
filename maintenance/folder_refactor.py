import os
import re
import shutil

import global_var
import logger


class RefactorFolder:
    source = "RFAC"

    def __init__(self, path):
        self.path = path

    def clean_torrent_downloads(self):
        files, directories = self.get_file_and_directory(self.path)
        self.sort_torrent_files(files, self.path)

        for directory in directories:
            directory_path = os.path.join(self.path, directory)
            sub_files, sub_directories = self.get_file_and_directory(directory_path)
            self.sort_torrent_files(sub_files, directory_path)

            sub_files, sub_directories = self.get_file_and_directory(directory_path)
            if len(sub_directories) == 0 and len(sub_files) == 0:
                try:
                    # os.rmdir(directory_path)
                    logger.log(f"Directory '{directory_path}' has been successfully deleted.", source=self.source)
                except OSError as e:
                    logger.log(f"Error: {str(e)}", source=self.source)
            else:
                logger.log(f"Cannot Delete '{directory_path}'. Not empty!", source=self.source, message_type="warn")

    def sort_torrent_files(self, files, directory):
        for file in files:
            file_name, tv_show, movie, subtitle, base_name = self.breakdown_torrent_file_name(file)
            logger.log(f'{file_name}, {tv_show}, {movie}, {subtitle}, {base_name}', source=self.source)
            if tv_show and not movie:
                self.move_file(os.path.join(directory, file),
                               os.path.join(global_var.torrent_tv_shows,
                                            base_name),
                               file_name)
            elif movie and not tv_show:
                self.move_file(os.path.join(directory, file),
                               os.path.join(global_var.torrent_movies,
                                            base_name),
                               file_name)
            else:
                self.move_file(os.path.join(directory, file),
                               os.path.join(global_var.torrent_unknown,
                                            base_name),
                               base_name + file_name)

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

        return files_list, directories_list

    def move_file(self, old_location, new_location, file):
        if not os.path.exists(new_location):
            os.makedirs(new_location)
        destination = shutil.move(old_location, os.path.join(new_location, file))
        return destination

    def breakdown_torrent_file_name(self, file_name):
        extension = str(file_name.split(".")[-1])
        if "srt" in extension.lower():
            subtitle = True
        else:
            subtitle = False

        match_video = any(ext in extension for ext in ("mp4", "flv", "mkv", "avi", "srt"))

        match_tv = re.search('S[0-9][0-9]E[0-9][0-9]', file_name, flags=re.IGNORECASE)
        match_quality = re.search('[0-9][0-9][0-9]p', file_name, flags=re.IGNORECASE)

        if match_tv:
            tv_show = True
            movie = False
            if "." in file_name:
                file_name = str(file_name[0:file_name.find('.', match_tv.end()-1)])
            else:
                file_name = str(file_name[0:match_tv.end()])
            base_name = str(file_name[0:match_tv.start()])
            if "." in file_name:
                file_name = file_name.replace(".", " ").strip()
                base_name = base_name.replace(".", " ").strip()
            file_name = file_name + "." + extension

        elif not match_tv and match_video and match_quality:
            tv_show = False
            movie = True
            file_name = str(file_name[0:match_quality.end()])
            base_name = str(file_name[0:match_quality.start() - 1])
            if "." in file_name:
                file_name = file_name.replace(".", " ").strip()
                base_name = base_name.replace(".", " ").strip()
            file_name = file_name + "." + extension

        else:
            tv_show = False
            movie = False
            base_name = ""

        return file_name, tv_show, movie, subtitle, base_name
