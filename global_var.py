import platform

operation_mode = True if platform.machine() == 'armv7l' else False
platform = platform.machine()

stop_all = False
restart = False
reboot_pi = False

log_type = "debug"
error_codes = "record/error_codes.json"

media_path = "/mnt/MediaBox"

telepot_accounts = 'communication/telepot_accounts.json'
telepot_commands = 'communication/telepot_commands.json'
telepot_callback_database = 'database/telepot/'
main_telepot_account = "main"

# todo move to task creation
# backup.backup.copy_files.append(telepot_accounts)
# backup.backup.copy_folders.append(telepot_commands)
# backup.backup.copy_folders.append(telepot_callback_database)

feed_link = "https://showrss.info/user/275495.rss?magnets=true&namespaces=true&name=clean&quality=null&re=null"

news_sources = 'news/sources.json'

cctv_download = "cctv/CCTVImages"
cctv_save = "/mnt/MediaBox/MediaBox/CCTVSaved"

cctv_model1 = "cctv/nn_models/modelA01.tflite"
cctv_model2 = "cctv/nn_models/modelA02.tflite"

telepot_image_dump = 'communication/chat_images'
# todo move to task creation
# backup.backup.move_folders.append(telepot_image_dump)

finance_images = 'database/finance_images'
# todo move to task creation
# backup.backup.move_folders_common.append(finance_images)

torrent_download = '/mnt/MediaBox/Downloads'
torrent_movies = '/mnt/MediaBox/Movies'
torrent_tv_shows = '/mnt/MediaBox/TVShows'
torrent_unknown = '/mnt/MediaBox/Unknown'

# Databases
db_admin = "administration"
tbl_chats = "telepot_allowed_chats"
tbl_groups = "telepot_groups"
tbl_jobs = "jobs"

db_news = "news"
tbl_news = "news_articles"

date_formats = ["%Y/%m/%d", "%d/%m/%Y", "%Y/%b/%d", "%d/%b/%Y",
                "%m/%d", "%d/%m", "%b/%d", "%d/%b",
                "%Y-%m-%d", "%d-%m-%Y", "%Y-%b-%d", "%d-%b-%Y", "%m-%d-%y", "%b-%d-%y",
                "%m-%d", "%d-%m", "%b-%d", "%d-%b",
                "%Y,%m,%d", "%d,%m,%Y", "%Y,%b,%d", "%d,%b,%Y",
                "%m,%d", "%d,%m", "%b,%d", "%d,%b"]

time_formats = ["%H:%M:%S", "%H:%M",
                "%H-%M-%S", "%H-%M"]


