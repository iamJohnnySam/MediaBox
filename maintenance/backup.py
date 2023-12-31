import glob
import os
import shutil
from datetime import datetime

import logger


class BackUp:
    def __init__(self, loc):
        self.backup_location = os.path.join(loc, datetime.now().strftime("%Y%m%d%H%M%S"))
        if not os.path.exists(self.backup_location):
            os.makedirs(self.backup_location)

        self.copy_folders = []
        self.copy_files = []
        self.move_folders = []
        self.move_files = []
        self.move_png_files = []

    def run_code(self):
        for file in self.copy_files:
            destination = os.path.join(self.backup_location, file)
            if not os.path.exists(os.path.dirname(destination)):
                os.makedirs(os.path.dirname(destination))
                logger.log(f"Directories created for {os.path.dirname(destination)}")

            shutil.copy(file, destination)
            logger.log(f"Copied {file} -> {destination}")

        for file in self.move_files:
            destination = os.path.join(self.backup_location, file)
            if not os.path.exists(os.path.dirname(destination)):
                os.makedirs(os.path.dirname(destination))
                logger.log(f"Directories created for {os.path.dirname(destination)}")

            shutil.move(file, destination)
            logger.log(f"Moved {file} -> {destination}")

        for folder in self.copy_folders:
            destination = os.path.join(self.backup_location, folder)
            if not os.path.exists(destination):
                os.makedirs(destination)

            shutil.copytree(folder, destination)
            logger.log(f"Copied {folder} -> {destination}")

        for folder in self.move_folders:
            allfiles = glob.glob(os.path.join(folder, '*_A_*'), recursive=True)
            destination = os.path.join(self.backup_location, folder)
            if not os.path.exists(destination):
                os.makedirs(destination)

            for file_path in allfiles:
                dst_path = os.path.join(destination, os.path.basename(file_path))
                shutil.move(file_path, dst_path)
                logger.log(f"Moved {file_path} -> {dst_path}")

