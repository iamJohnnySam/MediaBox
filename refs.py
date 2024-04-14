# --- SETTINGS ---
import os

logs_location = 'log/'
log_level = "debug"                         # LOGGING LEVEL
log_print = True
main_channel = "spark"                      # TELEPOT

# --- EMAIL ---
# imap = 'outlook.office365.com'
imap = 'imap.gmail.com'

# sent_mail = "Sent"
sent_mail = '"[Gmail]/Sent Mail"'

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

# Tools
charts_save_location = "resources/charts/"
if not os.path.isdir(charts_save_location):
    os.makedirs(charts_save_location)

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

db_finance = "transactions"
tbl_fin_cat = 'categories'
tbl_fin_trans = 'transaction_lkr'
tbl_fin_vendor = 'vendors'
tbl_fin_raw_vendor = 'vendors_raw'

db_baby = "baby"
tbl_baby_feed = 'feed'
tbl_baby_diaper = 'diaper'
tbl_baby_weight = 'weight'
tbl_baby_pump = 'pump'

db_entertainment = "entertainment"
tbl_tv_shows = 'tv_show'

# Back up
backup_location = '/mnt/MediaBox/MediaBox/Backup'
terminal_output = '../nohup.out'
password_file = 'passwords.py'

# groups
group_tv_show = "show"
group_cctv = "cctv"
group_baby = "baby"
