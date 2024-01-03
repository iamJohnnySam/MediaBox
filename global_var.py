from maintenance.backup import BackUp
backup = BackUp('/mnt/MediaBox/MediaBox/Backup')

check_shows = False
check_cctv = False
check_news = False
stop_cctv = False
stop_all = False
ready_to_run = False
reboot_pi = False

backup.move_folders.append('log/')
backup.move_png_files.append('charts/')
backup.copy_files.append('settings.py')
backup.move_files.append('../nohup.out')
backup.databases.append('transactions')
backup.databases.append('entertainment')

media_path = "/mnt/MediaBox"

telepot_accounts = 'communication/telepot_accounts.json'
telepot_groups = 'communication/telepot_groups.json'
telepot_allowed_chats = 'communication/telepot_allowed_chats.json'
telepot_commands = 'communication/commands/'
telepot_callback_database = 'database/telepot/'
backup.copy_files.append(telepot_accounts)
backup.copy_files.append(telepot_groups)
backup.copy_files.append(telepot_allowed_chats)
backup.copy_folders.append(telepot_commands)
backup.copy_folders.append(telepot_callback_database)

feed_link = "https://showrss.info/user/275495.rss?magnets=true&namespaces=true&name=clean&quality=null&re=null"
requested_show_database = 'database/requested_shows.json'
backup.copy_files.append(requested_show_database)

news_link = "https://www.adaderana.lk/rss.php"
news_database = 'database/newsRSS.json'
backup.copy_files.append(news_database)
backup.databases.append('news')

cctv_download = "cctv/CCTVImages"
cctv_save = "/mnt/MediaBox/MediaBox/CCTVSaved"

cctv_model1_google = 'https://drive.google.com/file/d/1-1i0UqlOT46jTQZP980FOhBcdHFGfaPW/view?usp=sharing'
cctv_model2_google = 'https://drive.google.com/file/d/1qkNWVF28CRyTo96fLCgB2BvELqPFTdcO/view?usp=sharing'
cctv_model1 = "cctv/nn_models/modelA01.tflite"
cctv_model2 = "cctv/nn_models/modelA02.tflite"

backup.databases.append('baby')

telepot_image_dump = 'communication/chat_images'
backup.move_folders.append(telepot_image_dump)

finance_images = 'database/finance_images'
backup.move_folders.append(finance_images, common=True)
