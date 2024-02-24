import glob
import os
import shutil
from datetime import datetime

from logging import logger
import settings


class BackUp:

    def __init__(self, loc):
        self.backup_location = os.path.join(loc, datetime.now().strftime("%Y%m%d%H%M%S"))
        self.common_backup_location = loc
        if not os.path.exists(self.backup_location):
            os.makedirs(self.backup_location)

        self.copy_folders = []
        self.copy_files = []
        self.move_folders = []
        self.move_folders_common = []
        self.move_files = []
        self.move_png_files = []
        self.databases = []

        logger.log("Object Created")

    def run_code(self):
        logger.log("Backup Started")
        self.cp_files()
        self.mv_files()
        self.cp_folders()
        self.mv_folders()
        self.cp_databases()
        logger.log("Backup Ended")

    def cp_files(self):
        for file in self.copy_files:
            destination = os.path.join(self.backup_location, file)
            if not os.path.exists(os.path.dirname(destination)):
                os.makedirs(os.path.dirname(destination))
                logger.log(f"Directory created > {os.path.dirname(destination)}")

            shutil.copy(file, destination)
            logger.log(f"Copied {file} -> {destination}")

    def mv_files(self):
        for file in self.move_files:
            if "../" in file:
                ufile = str(file).replace("../", "")
            else:
                ufile = file

            destination = os.path.join(self.backup_location, ufile)
            if not os.path.exists(os.path.dirname(destination)):
                os.makedirs(os.path.dirname(destination))
                logger.log(f"Directory created > {os.path.dirname(destination)}")

            try:
                shutil.move(file, destination)
                logger.log(f"Moved {file} -> {destination}")
            except FileNotFoundError:
                pass

    def cp_folders(self):
        for folder in self.copy_folders:
            destination = os.path.join(self.backup_location, folder)

            shutil.copytree(folder, destination)
            logger.log(f"Copied {folder} -> {destination}")

    def mv_folders(self):
        for folder in self.move_folders:
            allfiles = glob.glob(os.path.join(folder, '*_A_*'), recursive=True)
            destination = os.path.join(self.backup_location, folder)
            if not os.path.exists(os.path.dirname(destination)):
                os.makedirs(os.path.dirname(destination))
                logger.log(f"Directory created > {os.path.dirname(destination)}")

            for file_path in allfiles:
                dst_path = os.path.join(destination, os.path.basename(file_path))
                shutil.move(file_path, dst_path)
                logger.log(f"Moved {file_path} -> {dst_path}")

        for folder in self.move_folders_common:
            allfiles = glob.glob(os.path.join(folder, '*_A_*'), recursive=True)
            destination = os.path.join(self.common_backup_location, folder)
            if not os.path.exists(os.path.dirname(destination)):
                os.makedirs(os.path.dirname(destination))
                logger.log(f"Directory created > {os.path.dirname(destination)}")

            for file_path in allfiles:
                dst_path = os.path.join(destination, os.path.basename(file_path))
                shutil.move(file_path, dst_path)
                logger.log(f"Moved {file_path} -> {dst_path}")

        for folder in self.move_png_files:
            allfiles = glob.glob(os.path.join(folder, '*_A_*'), recursive=True)
            destination = os.path.join(self.backup_location, folder)
            if not os.path.exists(os.path.dirname(destination)):
                os.makedirs(os.path.dirname(destination))
                logger.log(f"Directory created > {os.path.dirname(destination)}")

            for file_path in allfiles:
                dst_path = os.path.join(destination, os.path.basename(file_path))
                if ".png" in dst_path.lower():
                    shutil.move(file_path, dst_path)
                    logger.log(f"Moved {file_path} -> {dst_path}")

    def cp_databases(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        for database in self.databases:
            backup_file = f'{database}_{timestamp}_database_backup.sql'
            backup_file_path = os.path.join(self.backup_location, backup_file)

            mysqldump_cmd = f'mysqldump -h localhost -u {settings.database_user} -p{settings.database_password}' \
                            f' {database} > {backup_file_path}'
            os.system(mysqldump_cmd)

            gzip_cmd = f'gzip {backup_file_path}'
            os.system(gzip_cmd)
            logger.log(f'BackUp {database} database > {backup_file_path}.')


backup = BackUp('/mnt/MediaBox/MediaBox/Backup')

backup.move_folders.append('log/')
backup.move_png_files.append('charts/')
backup.copy_files.append('settings.py')
backup.move_files.append('../nohup.out')
