import os
import re
import shutil
import string

import global_var
import logger
from communication import communicator


class RefactorFolder:

    def __init__(self, path):
        self.path = path
        self.send_string = ""

    def clean_torrent_downloads(self):
        self.send_string = "New additions to MediaBox:"
        files, directories = self.get_file_and_directory(self.path)
        if len(files) == 0 and len(directories) == 0:
            logger.log("Nothing to refactor")
            return

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
                        logger.log(f'Folder Refactor Error - {sub_directory_path}, Base location - {sub_last_loc}',
                                   message_type="error")
                    self.remove_directory(sub_directory_path)

            elif last_loc is not None:
                self.torrent_step_2(sub_directories, directory_path, last_loc)
            else:
                logger.log(f'Folder Refactor Error - {directory_path}, Base location - {last_loc}',
                           message_type="error")

            self.remove_directory(directory_path)

        communicator.send_to_group("main",
                                   self.send_string,
                                   group="show")

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
            logger.log(f"Moved {file_path} -> {dst_path}")

        self.remove_directory(subs_folder)

    def sort_torrent_files(self, files, directory):
        base_loc = None
        for file in files:
            file_name, tv_show, movie, subtitle, base_name = self.breakdown_torrent_file_name(file)
            logger.log(f'{file_name}, {tv_show}, {movie}, {subtitle}, {base_name}')
            if tv_show and not movie:
                base_loc = os.path.join(global_var.torrent_tv_shows, base_name)
                self.move_file(os.path.join(directory, file),
                               base_loc,
                               file_name)
                self.send_string = self.send_string + "\n" + file_name

            elif movie and not tv_show:
                base_loc = os.path.join(global_var.torrent_movies, base_name)
                self.move_file(os.path.join(directory, file),
                               base_loc,
                               file_name)
                self.send_string = self.send_string + "\n" + file_name

            else:
                base_loc = os.path.join(global_var.torrent_unknown, base_name)
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

        logger.log(f'Got files in {path}.')
        return files_list, directories_list

    def move_file(self, old_location, new_location, file):
        if not os.path.exists(new_location):
            os.makedirs(new_location)
        destination = shutil.move(old_location, os.path.join(new_location, file))
        logger.log(f"Moved '{file}' to '{destination}'")
        return destination

    def breakdown_torrent_file_name(self, file_name):
        extension = str(file_name.split(".")[-1])
        if "srt" in extension.lower():
            subtitle = True
        else:
            subtitle = False

        no_words = ["EXTENDED", "REMASTERED", "REPACK", "BLURAY", "Dir Cut", "IMAX", "EDITION"]
        match_video = any(ext in extension for ext in ("mp4", "flv", "mkv", "avi", "srt"))

        match_tv = re.search('S[0-9][0-9]E[0-9][0-9]', file_name, flags=re.IGNORECASE)
        match_tv2 = re.search('[0-9]x[0-9][0-9]', file_name, flags=re.IGNORECASE)
        match_tv3 = re.search('S[0-9][0-9] E[0-9][0-9]', file_name, flags=re.IGNORECASE)
        match_quality = re.search('[0-9][0-9][0-9]p', file_name, flags=re.IGNORECASE)

        if (match_tv or match_tv2 or match_tv3) and match_video:
            if match_tv:
                match_start = match_tv.start()
                match_end = match_tv.end()
            elif match_tv2:
                match_start = match_tv2.start()
                match_end = match_tv2.end()
            elif match_tv3:
                match_start = match_tv3.start()
                match_end = match_tv3.end()
            else:
                return
            tv_show = True
            movie = False
            if "." in file_name:
                file_name = str(file_name[0:file_name.find('.', match_end - 1)])
            elif "+" in file_name:
                file_name = str(file_name[0:file_name.find('+', match_end - 1)])
            else:
                file_name = str(file_name[0:match_end])
            base_name = str(file_name[0:match_start])
            if "." in file_name:
                file_name = file_name.replace(".", " ").strip()
                base_name = self.remove_words(base_name.replace(".", " ").strip(), no_words)
                base_name = string.capwords(base_name)
            elif "+" in file_name:
                file_name = file_name.replace("+", " ").strip()
                base_name = self.remove_words(base_name.replace("+", " ").strip(), no_words)
                base_name = string.capwords(base_name)
            file_name = file_name + "." + extension

        elif not match_tv and match_video and match_quality:
            tv_show = False
            movie = True
            file_name = str(file_name[0:match_quality.end()])
            base_name = str(file_name[0:match_quality.start() - 1])
            if "." in file_name:
                file_name = file_name.replace(".", " ").strip()
                base_name = self.remove_words(base_name.replace(".", " ").strip(), no_words)
                base_name = string.capwords(base_name)
            elif "+" in file_name:
                file_name = file_name.replace("+", " ").strip()
                base_name = self.remove_words(base_name.replace("+", " ").strip(), no_words)
                base_name = string.capwords(base_name)
            file_name = file_name + "." + extension

        else:
            tv_show = False
            movie = False
            base_name = ""

        return file_name, tv_show, movie, subtitle, base_name

    def remove_words(self, sentence, words_to_remove):
        words = sentence.split()
        filtered_words = [word for word in words if word.lower() not in map(str.lower, words_to_remove)]
        filtered_sentence = ' '.join(filtered_words)
        logger.log(f'Filtered words from {sentence} > {filtered_sentence}.')
        return filtered_sentence

    def move_files_and_directories(self, source_folder, destination_folder):
        items = os.listdir(source_folder)
        for item in items:
            source_path = os.path.join(source_folder, item)
            destination_path = os.path.join(destination_folder, item)
            try:
                # Move the item to the destination folder
                shutil.move(source_path, destination_path)
                logger.log(f"Moved '{item}' to '{destination_folder}'")
            except Exception as e:
                logger.log(f"Failed to move '{item}': {str(e)}")

    def remove_directory(self, path):
        sub_files, sub_directories = self.get_file_and_directory(path)
        if len(sub_directories) == 0 and len(sub_files) == 0:
            try:
                os.rmdir(path)
                logger.log(f"Directory '{path}' has been successfully deleted.")
            except OSError as e:
                logger.log(f"Error: {str(e)}")
        else:
            logger.log(f"Cannot Delete '{path}'. Not empty!", message_type="warn")
