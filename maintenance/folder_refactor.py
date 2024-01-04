import os
import re
import shutil

import global_var


class RefactorFolder:
    def __init__(self, path):
        self.path = path

    def clean_torrent_downloads(self):
        for root, dirs, files in os.walk(self.path):
            for file in files:
                file_name, tv_show, movie, subtitle = self.breakdown_torrent_file_name(file)
                if tv_show:
                    self.move_file(os.path.join(self.path, file),
                                   os.path.join(global_var.torrent_tv_shows,
                                                os.path.splitext(os.path.basename(file))[0],
                                                file_name))

    def move_file(self, old_location, new_location):
        loc = os.path.dirname(os.path.abspath(new_location))
        if not os.path.exists(loc):
            os.makedirs(loc)
        destination = shutil.move(old_location, new_location)
        return destination

    def breakdown_torrent_file_name(self, file_name):
        extension = str(file_name.split(".")[-1])
        if "srt" in extension.lower():
            subtitle = True
        else:
            subtitle = False

        match_video = any(ext in extension for ext in ("mp4", "flv", "mkv"))

        match_tv = re.search('S[0-9][0-9]E[0-9][0-9]', file_name, flags=re.IGNORECASE)
        match_quality = re.search('[0-9][0-9][0-9]p', file_name, flags=re.IGNORECASE)

        if match_tv:
            tv_show = True
            movie = False
            file_name = str(file_name[0:match_tv.end()])
            if "." in file_name:
                file_name.replace(".", " ")
            file_name = file_name + extension

        elif match_video and match_quality:
            tv_show = False
            movie = True
            file_name = str(file_name[0:match_quality.end()])
            if "." in file_name:
                file_name.replace(".", " ")
            file_name = file_name + extension

        else:
            tv_show = False
            movie = False

        return file_name, tv_show, movie, subtitle
