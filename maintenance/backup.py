import glob
import pyodbc
import os
import shutil
from datetime import datetime
import pandas as pd

import logger
import settings


class BackUp:
    source = "BKUP"

    def __init__(self, loc):
        self.backup_location = os.path.join(loc, datetime.now().strftime("%Y%m%d%H%M%S"))
        if not os.path.exists(self.backup_location):
            os.makedirs(self.backup_location)

        self.copy_folders = []
        self.copy_files = []
        self.move_folders = []
        self.move_files = []
        self.move_png_files = []
        self.databases = []

    def run_code(self):
        for file in self.copy_files:
            destination = os.path.join(self.backup_location, file)
            if not os.path.exists(os.path.dirname(destination)):
                os.makedirs(os.path.dirname(destination))
                logger.log(f"Directories created for {os.path.dirname(destination)}", source=self.source)

            shutil.copy(file, destination)
            logger.log(f"Copied {file} -> {destination}", source=self.source)

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

        for folder in self.copy_folders:
            destination = os.path.join(self.backup_location, folder)

            shutil.copytree(folder, destination)
            logger.log(f"Copied {folder} -> {destination}", source=self.source)

        for folder in self.move_folders:
            allfiles = glob.glob(os.path.join(folder, '*_A_*'), recursive=True)
            destination = os.path.join(self.backup_location, folder)
            if not os.path.exists(os.path.dirname(destination)):
                os.makedirs(os.path.dirname(destination))

            for file_path in allfiles:
                dst_path = os.path.join(destination, os.path.basename(file_path))
                shutil.move(file_path, dst_path)
                logger.log(f"Moved {file_path} -> {dst_path}", source=self.source)

        for database in self.databases:
            self.sql_backup(database, settings.database_user, settings.database_password)

    def sql_backup(self, database, username,password):
        conn = pyodbc.connect('DRIVER={SQL Server};SERVER=' + 'localhost' +
                              ';DATABASE=' + database +
                              ';UID=' + username +
                              ';PWD=' + password)
        cursor = conn.cursor()
        backup_file = database + '_backup_' + str(datetime.now().strftime('%Y%m%d_%H%M%S')) + '.bak'
        backup_command = 'BACKUP DATABASE ' + database + \
                         ' TO DISK=\'' + os.path.join(self.backup_location, backup_file) + '\''
        cursor.execute(backup_command)
        backup_details = {'database': [database], 'backup_file': [backup_file], 'backup_datetime': [datetime.now()]}
        backup_df = pd.DataFrame(data=backup_details)

        backup_details_file = os.path.join(self.backup_location, 'backup_details.csv')
        backup_df.to_csv(backup_details_file, index=False)
