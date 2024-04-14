import glob
import os
import shutil
from datetime import datetime

import global_variables
from brains.job import Job
from database_manager.sql_connector import SQLConnector
from modules.base_module import Module
from tools import logger
import passwords


class BackUp(Module):

    def __init__(self, job: Job, loc):
        super().__init__(job)
        self.backup_location = os.path.join(loc, datetime.now().strftime("%Y%m%d%H%M%S"))
        self.common_backup_location = loc
        if global_variables.operation_mode and not os.path.exists(self.backup_location):
            os.makedirs(self.backup_location)

        self.copy_folders = []
        self.copy_files = []
        self.move_folders = []
        self.move_folders_common = []
        self.move_files = []
        self.move_png_files = []
        self.databases = []

        logger.log(self._job.job_id, "Object Created")

    def run_backup(self):
        logger.log(self._job.job_id, "Backup Started")
        if global_variables.operation_mode:
            self.cp_files()
            self.mv_files()
            self.cp_folders()
            self.mv_folders()
            self.cp_databases()
        logger.log(self._job.job_id, "Backup Ended")

    def cp_files(self):
        if global_variables.operation_mode:
            for file in self.copy_files:
                destination = os.path.join(self.backup_location, file)
                if not os.path.exists(os.path.dirname(destination)):
                    os.makedirs(os.path.dirname(destination))
                    logger.log(self._job.job_id, f"Directory created > {os.path.dirname(destination)}")

                shutil.copy(file, destination)
                logger.log(self._job.job_id, f"Copied {file} -> {destination}")

    def mv_files(self):
        for file in self.move_files:
            if "../" in file:
                ufile = str(file).replace("../", "")
            else:
                ufile = file

            destination = os.path.join(self.backup_location, ufile)
            if not os.path.exists(os.path.dirname(destination)):
                os.makedirs(os.path.dirname(destination))
                logger.log(self._job.job_id, f"Directory created > {os.path.dirname(destination)}")

            try:
                shutil.move(file, destination)
                logger.log(self._job.job_id, f"Moved {file} -> {destination}")
            except FileNotFoundError:
                pass

    def cp_folders(self):
        for folder in self.copy_folders:
            destination = os.path.join(self.backup_location, folder)

            shutil.copytree(folder, destination)
            logger.log(self._job.job_id, f"Copied {folder} -> {destination}")

    def mv_folders(self):
        for folder in self.move_folders:
            allfiles = glob.glob(os.path.join(folder, '*_A_*'), recursive=True)
            destination = os.path.join(self.backup_location, folder)
            if not os.path.exists(os.path.dirname(destination)):
                os.makedirs(os.path.dirname(destination))
                logger.log(self._job.job_id, f"Directory created > {os.path.dirname(destination)}")

            for file_path in allfiles:
                dst_path = os.path.join(destination, os.path.basename(file_path))
                shutil.move(file_path, dst_path)
                logger.log(self._job.job_id, f"Moved {file_path} -> {dst_path}")

        for folder in self.move_folders_common:
            allfiles = glob.glob(os.path.join(folder, '*_A_*'), recursive=True)
            destination = os.path.join(self.common_backup_location, folder)
            if not os.path.exists(os.path.dirname(destination)):
                os.makedirs(os.path.dirname(destination))
                logger.log(self._job.job_id, f"Directory created > {os.path.dirname(destination)}")

            for file_path in allfiles:
                dst_path = os.path.join(destination, os.path.basename(file_path))
                shutil.move(file_path, dst_path)
                logger.log(self._job.job_id, f"Moved {file_path} -> {dst_path}")

        for folder in self.move_png_files:
            allfiles = glob.glob(os.path.join(folder, '*_A_*'), recursive=True)
            destination = os.path.join(self.backup_location, folder)
            if not os.path.exists(os.path.dirname(destination)):
                os.makedirs(os.path.dirname(destination))
                logger.log(self._job.job_id, f"Directory created > {os.path.dirname(destination)}")

            for file_path in allfiles:
                dst_path = os.path.join(destination, os.path.basename(file_path))
                if ".png" in dst_path.lower():
                    shutil.move(file_path, dst_path)
                    logger.log(self._job.job_id, f"Moved {file_path} -> {dst_path}")

    def cp_databases(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        for database in self.databases:
            backup_file = f'{database}_{timestamp}_database_backup.sql'
            backup_file_path = os.path.join(self.backup_location, backup_file)
            self._backup_database(database, backup_file_path)

    def cp_all_databases(self):
        db = SQLConnector(self._job)
        database_list = db.get_databases()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        for database in database_list:
            if database == 'information_schema':
                continue
            backup_file = f'{database}_{timestamp}_database_backup.sql'
            backup_file_path = os.path.join(self.backup_location, backup_file)
            self._backup_database(database, backup_file_path)

    def _backup_database(self, database, backup_file_path):
        mysqldump_cmd = f'mysqldump -h localhost -u {passwords.database_user} -p{passwords.database_password}' \
                        f' {database} > {backup_file_path}'
        os.system(mysqldump_cmd)

        gzip_cmd = f'gzip {backup_file_path}'
        os.system(gzip_cmd)
        logger.log(self._job.job_id, f'BackUp {database} database > {backup_file_path}.')
