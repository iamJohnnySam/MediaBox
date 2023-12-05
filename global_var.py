check_shows = False
check_cctv = False
check_news = False
stop_cctv = False
stop_all = False
ready_to_run = False

media_path = "/mnt/MediaBox"

feed_link = "https://showrss.info/user/275495.rss?magnets=true&namespaces=true&name=clean&quality=null&re=null"
show_download_database = 'database/downloadedFiles.json'

news_link = "https://www.adaderana.lk/rss.php"
news_database = 'database/newsRSS.json'

cctv_download = "cctv/CCTVImages"
cctv_save = "/mnt/MediaBox/MediaBox/CCTVSaved"

cctv_model1_google = 'https://drive.google.com/file/d/1-1i0UqlOT46jTQZP980FOhBcdHFGfaPW/view?usp=sharing'
cctv_model2_google = 'https://drive.google.com/file/d/1qkNWVF28CRyTo96fLCgB2BvELqPFTdcO/view?usp=sharing'
cctv_model1 = "cctv/nn_models/modelA01.tflite"
cctv_model2 = "cctv/nn_models/modelA02.tflite"
