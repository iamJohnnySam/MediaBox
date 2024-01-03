import glob
import os
import shutil
from datetime import datetime

import logger
import settings


class BackUp:
    source = "BKUP"

    def __init__(self, loc):
        self.backup_location = os.path.join(loc, datetime.now().strftime("%Y%m%d%H%M%S"))
        self.common_backup_location = loc
        if not os.path.exists(self.backup_location):
            os.makedirs(self.backup_location)

        self.copy_folders = []
        self.copy_files = []
        self.move_folders = []
        self.move_files = []
        self.move_png_files = []
        self.databases = []

    def run_code(self):
        self.backup_copy_files()
        self.backup_move_files()
        self.backup_copy_folders()
        self.backup_move_folders()
        self.backup_databases()

    def backup_copy_files(self):
        for file in self.copy_files:
            destination = os.path.join(self.backup_location, file)
            if not os.path.exists(os.path.dirname(destination)):
                os.makedirs(os.path.dirname(destination))
                logger.log(f"Directories created for {os.path.dirname(destination)}", source=self.source)

            shutil.copy(file, destination)
            logger.log(f"Copied {file} -> {destination}", source=self.source)

    def backup_move_files(self):
        for file in self.move_files:
            if "../" in file:
                ufile = str(file).replace("../", "")
            else:
                ufile = file

            destination = os.path.join(self.backup_location, ufile)
            if not os.path.exists(os.path.dirname(destination)):
                os.makedirs(os.path.dirname(destination))
                logger.log(f"Directories created for {os.path.dirname(destination)}", source=self.source)

            try:
                shutil.move(file, destination)
                logger.log(f"Moved {file} -> {destination}", source=self.source)
            except FileNotFoundError:
                pass

    def backup_copy_folders(self):
        for folder in self.copy_folders:
            destination = os.path.join(self.backup_location, folder)

            shutil.copytree(folder, destination)
            logger.log(f"Copied {folder} -> {destination}", source=self.source)

    def backup_move_folders(self, common=False):
        for folder in self.move_folders:
            allfiles = glob.glob(os.path.join(folder, '*_A_*'), recursive=True)
            if common:
                destination = self.common_backup_location
            else:
                destination = os.path.join(self.backup_location, folder)
            if not os.path.exists(os.path.dirname(destination)):
                os.makedirs(os.path.dirname(destination))

            for file_path in allfiles:
                dst_path = os.path.join(destination, os.path.basename(file_path))
                shutil.move(file_path, dst_path)
                logger.log(f"Moved {file_path} -> {dst_path}", source=self.source)

        for folder in self.move_png_files:
            allfiles = glob.glob(os.path.join(folder, '*_A_*'), recursive=True)
            destination = os.path.join(self.backup_location, folder)
            if not os.path.exists(os.path.dirname(destination)):
                os.makedirs(os.path.dirname(destination))

            for file_path in allfiles:
                dst_path = os.path.join(destination, os.path.basename(file_path))
                if ".png" in dst_path.lower():
                    shutil.move(file_path, dst_path)
                    logger.log(f"Moved {file_path} -> {dst_path}", source=self.source)

    def backup_databases(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        for database in self.databases:
            backup_file = f'{database}_{timestamp}_database_backup.sql'
            backup_file_path = os.path.join(self.backup_location, backup_file)

            mysqldump_cmd = f'mysqldump -h localhost -u {settings.database_user} -p{settings.database_password}' \
                            f' {database} > {backup_file_path}'
            os.system(mysqldump_cmd)

            gzip_cmd = f'gzip {backup_file_path}'
            os.system(gzip_cmd)
