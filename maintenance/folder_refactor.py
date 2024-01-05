import os
import re
import shutil
import string

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
            last_loc = self.sort_torrent_files(sub_files, directory_path)

            if "Subs" in sub_directories:
                self.move_subs_folder(directory_path, last_loc)

            sub_files, sub_directories = self.get_file_and_directory(directory_path)
            for sub_sub_directory in sub_directories:
                self.move_files_and_directories(os.path.join(directory_path, sub_sub_directory),
                                                last_loc)
                self.remove_directory(sub_sub_directory)

            self.remove_directory(directory_path)

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
            logger.log(f"Moved {file_path} -> {dst_path}", source=self.source)

        self.remove_directory(subs_folder)

    def sort_torrent_files(self, files, directory):
        base_loc = None
        for file in files:
            file_name, tv_show, movie, subtitle, base_name = self.breakdown_torrent_file_name(file)
            logger.log(f'{file_name}, {tv_show}, {movie}, {subtitle}, {base_name}', source=self.source)
            if tv_show and not movie:
                base_loc = os.path.join(global_var.torrent_tv_shows, base_name)
                self.move_file(os.path.join(directory, file),
                               base_loc,
                               file_name)
            elif movie and not tv_show:
                base_loc = os.path.join(global_var.torrent_movies, base_name)
                self.move_file(os.path.join(directory, file),
                               base_loc,
                               file_name)
            else:
                base_loc = os.path.join(global_var.torrent_unknown, base_name)
                self.move_file(os.path.join(directory, file),
                               base_loc,
                               base_name + file_name)
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

        logger.log(f'Got files in {path}.', source=self.source)
        return files_list, directories_list

    def move_file(self, old_location, new_location, file):
        if not os.path.exists(new_location):
            os.makedirs(new_location)
        destination = shutil.move(old_location, os.path.join(new_location, file))
        logger.log(f"Moved '{file}' to '{destination}'", source=self.source)
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
        match_quality = re.search('[0-9][0-9][0-9]p', file_name, flags=re.IGNORECASE)

        if match_tv and match_video:
            tv_show = True
            movie = False
            if "." in file_name:
                file_name = str(file_name[0:file_name.find('.', match_tv.end() - 1)])
            else:
                file_name = str(file_name[0:match_tv.end()])
            base_name = str(file_name[0:match_tv.start()])
            if "." in file_name:
                file_name = file_name.replace(".", " ").strip()
                base_name = self.remove_words(base_name.replace(".", " ").strip(), no_words)
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
        logger.log(f'Filtered words from {sentence} > {filtered_sentence}.', source=self.source)
        return filtered_sentence

    def move_files_and_directories(self, source_folder, destination_folder):
        items = os.listdir(source_folder)
        for item in items:
            source_path = os.path.join(source_folder, item)
            destination_path = os.path.join(destination_folder, item)
            try:
                # Move the item to the destination folder
                shutil.move(source_path, destination_path)
                logger.log(f"Moved '{item}' to '{destination_folder}'", source=self.source)
            except Exception as e:
                logger.log(f"Failed to move '{item}': {str(e)}", source=self.source)

    def remove_directory(self, path):
        sub_files, sub_directories = self.get_file_and_directory(path)
        if len(sub_directories) == 0 and len(sub_files) == 0:
            try:
                os.rmdir(path)
                logger.log(f"Directory '{path}' has been successfully deleted.", source=self.source)
            except OSError as e:
                logger.log(f"Error: {str(e)}", source=self.source)
        else:
            logger.log(f"Cannot Delete '{path}'. Not empty!", source=self.source, message_type="warn")
