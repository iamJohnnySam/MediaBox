# --- SETTINGS ---
import os

# --- SYSTEM INFORMATION ---
known_hosts: dict[str, dict[str, str]] = {
    'spark': {
        'platform': 'armv7l',
        'system': 'Linux'},
    'mediabox': {
        'platform': 'x86_64',
        'system': 'Linux'},
    'iamjohnnysam-dell': {
        'platform': 'AMD64',
        'system': 'Windows'}}

# --- MODULES INSTALLED ON WHICH SYSTEM ---
modules: dict[str, dict[str, dict[str, str | bool]]] = {
    'socket': {
        'spark': {
            'server': True,
        },
        'mediabox': {
            'server': False,
            'connect': 'spark'
        }
    },
    'telepot': {
        'spark': {
            'channels': ['spark', 'baby'],
            'main_channel': 'spark'
        },
        'iamjohnnysam-dell': {
            'channels': ['test'],
            'main_channel': 'test'
        }
    },
    'finance': {
        'images': 'database/finance_images'
    },
    'web': {
        'spark': {}
    },
    'media': {
        'mediabox': {
            'media_path': "/home/hp/media",
            'download': '/home/hp/media/Downloads',
            'movies': '/home/hp/media/Movies',
            'tv_shows': '/home/hp/media/TVShows',
            'unknown_files': '/home/hp/media/Unknown'
        }
    },
    'cctv': {
        'mediabox': {
            'imap': 'imap.gmail.com',
            'mailbox': 'CCTV',
            'sent': '"[Gmail]/Sent Mail"',
            'model1': 'ai_models/cctv/modelA01.tflite',
            'model2': 'ai_models/cctv/modelA02.tflite',
            'download_loc': 'resources/CCTVImages',
            'save_loc': '/home/hp/media/CCTVSaved'
        }
    },
    'backup': {
        'spark': {
            'backup_location': '/home/pi/backup'
        },
        'mediabox': {
            'backup_location': '/home/hp/backup'
        }
    }
}

logs_location = 'log/'
log_level = "debug"  # LOGGING LEVEL
log_print = True

# telepot
db_telepot_accounts = 'database/telepot_accounts.json'
db_telepot_commands = 'database/telepot_commands.json'
loc_telepot_callback = 'database/telepot/'
telepot_image_dump = 'communication/chat_images'

# Media
feed_link = "https://showrss.info/user/275495.rss?magnets=true&namespaces=true&name=clean&quality=null&re=null"

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
terminal_output = '../nohup.out'
password_file = 'passwords.py'

# groups
group_tv_show = "show"
group_cctv = "cctv"
group_baby = "baby"
