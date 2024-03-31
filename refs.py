# --- SETTINGS ---
logs_location = 'log/'
log_level = "debug"                         # LOGGING LEVEL
log_print = True
main_channel = "spark"                      # TELEPOT

# --- EMAIL ---
# imap = 'outlook.office365.com'
imap = 'imap.gmail.com'

# --- LINKS ---
# CCTV
cctv_download = "resources/CCTVImages"
cctv_save = "/mnt/MediaBox/MediaBox/CCTVSaved"
cctv_model1 = "ai_models/cctv/modelA01.tflite"
cctv_model2 = "ai_models/cctv/modelA02.tflite"
cctv_mailbox = 'CCTV'

# telepot
db_telepot_accounts = 'database/telepot_accounts.json'
db_telepot_commands = 'database/telepot_commands.json'
loc_telepot_callback = 'database/telepot/'
telepot_image_dump = 'communication/chat_images'
finance_images = 'database/finance_images'

# Media
feed_link = "https://showrss.info/user/275495.rss?magnets=true&namespaces=true&name=clean&quality=null&re=null"
media_path = "/mnt/MediaBox"
torrent_download = '/mnt/MediaBox/Downloads'
torrent_movies = '/mnt/MediaBox/Movies'
torrent_tv_shows = '/mnt/MediaBox/TVShows'
torrent_unknown = '/mnt/MediaBox/Unknown'

# JSON Databases
error_codes = "tools/error_codes.json"
news_sources = 'database/news_sources.json'

# SQL Databases
db_admin = "administration"
tbl_chats = "telepot_allowed_chats"
tbl_groups = "telepot_groups"
tbl_jobs = "jobs"

db_news = "news"
tbl_news = "news_articles"

# Back up
backup_location = '/mnt/MediaBox/MediaBox/Backup'
terminal_output = '../nohup.out'
charts_save_location = 'charts/'
password_file = 'passwords.py'

# groups
group_tv_show = "show"
group_cctv = "cctv"
group_baby = "baby"
