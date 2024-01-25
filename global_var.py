from maintenance import backup

ready_to_run = False
check_shows = False
check_cctv = False
check_news = False
stop_all = False
restart = False
reboot_pi = False

media_path = "/mnt/MediaBox"

telepot_accounts = 'communication/telepot_accounts.json'
telepot_commands = 'communication/commands/'
telepot_callback_database = 'database/telepot/'
backup.backup.copy_files.append(telepot_accounts)
backup.backup.copy_folders.append(telepot_commands)
backup.backup.copy_folders.append(telepot_callback_database)

feed_link = "https://showrss.info/user/275495.rss?magnets=true&namespaces=true&name=clean&quality=null&re=null"

news_adaderana = "https://www.adaderana.lk/rss.php"
news_cartoon = "https://www.dailymirror.lk/rss/cartoon_of_the_day/167"
news_caption = "https://www.dailymirror.lk/rss/caption_story/110"

cctv_download = "cctv/CCTVImages"
cctv_save = "/mnt/MediaBox/MediaBox/CCTVSaved"

cctv_model1 = "cctv/nn_models/modelA01.tflite"
cctv_model2 = "cctv/nn_models/modelA02.tflite"

telepot_image_dump = 'communication/chat_images'
backup.backup.move_folders.append(telepot_image_dump)

finance_images = 'database/finance_images'
backup.backup.move_folders_common.append(finance_images)

torrent_download = '/mnt/MediaBox/Downloads'
torrent_movies = '/mnt/MediaBox/Movies'
torrent_tv_shows = '/mnt/MediaBox/TVShows'
torrent_unknown = '/mnt/MediaBox/Unknown'
