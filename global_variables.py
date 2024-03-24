import platform

operation_mode = True if platform.machine() == 'armv7l' else False
platform = platform.machine()

ready_to_run = False
stop_all = False
restart = False
reboot_pi = False

# todo move to task creation
# backup.backup.copy_files.append(telepot_accounts)
# backup.backup.copy_folders.append(telepot_commands)
# backup.backup.copy_folders.append(telepot_callback_database)

# todo move to task creation
# backup.backup.move_folders.append(telepot_image_dump)

# todo move to task creation
# backup.backup.move_folders_common.append(finance_images)

date_formats = ["%Y-%m-%d", "%d-%m-%Y", "%Y-%b-%d", "%d-%b-%Y", "%m-%d-%y", "%b-%d-%y",
                "%Y/%m/%d", "%d/%m/%Y", "%Y/%b/%d", "%d/%b/%Y",
                "%m/%d", "%d/%m", "%b/%d", "%d/%b",
                "%m-%d", "%d-%m", "%b-%d", "%d-%b",
                "%Y,%m,%d", "%d,%m,%Y", "%Y,%b,%d", "%d,%b,%Y",
                "%m,%d", "%d,%m", "%b,%d", "%d,%b"]

time_formats = ["%H:%M:%S", "%H:%M",
                "%H-%M-%S", "%H-%M"]


