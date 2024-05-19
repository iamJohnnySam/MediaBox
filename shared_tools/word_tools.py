import re
import string
from datetime import datetime

from common_workspace import global_var
from shared_models.job import Job
from shared_tools.logger import log


def remove_words(job: Job, sentence, words_to_remove):
    words = sentence.split()
    filtered_words = [word for word in words if word.lower() not in map(str.lower, words_to_remove)]
    filtered_sentence = ' '.join(filtered_words)
    log(job.job_id, f'Filtered words from {sentence} > {filtered_sentence}.')
    return filtered_sentence


def breakdown_torrent_file_name(job: Job, file_name):
    extension = str(file_name.split(".")[-1])
    if "srt" in extension.lower():
        subtitle = True
    else:
        subtitle = False

    no_words = ["EXTENDED", "REMASTERED", "REPACK", "BLURAY", "Dir Cut", "IMAX", "EDITION"]
    match_video = any(ext in extension for ext in ("mp4", "flv", "mkv", "avi", "srt"))

    match_tv = re.search('S[0-9][0-9]E[0-9][0-9]', file_name, flags=re.IGNORECASE)
    match_tv2 = re.search('[0-9]x[0-9][0-9]', file_name, flags=re.IGNORECASE)
    match_tv3 = re.search('S[0-9][0-9] E[0-9][0-9]', file_name, flags=re.IGNORECASE)
    match_quality = re.search('[0-9][0-9][0-9]p', file_name, flags=re.IGNORECASE)

    # todo remove year 2021

    if (match_tv or match_tv2 or match_tv3) and match_video:
        if match_tv:
            match_start = match_tv.start()
            match_end = match_tv.end()
        elif match_tv2:
            match_start = match_tv2.start()
            match_end = match_tv2.end()
        elif match_tv3:
            match_start = match_tv3.start()
            match_end = match_tv3.end()
        else:
            return
        tv_show = True
        movie = False
        if "." in file_name:
            file_name = str(file_name[0:file_name.find('.', match_end - 1)])
        elif "+" in file_name:
            file_name = str(file_name[0:file_name.find('+', match_end - 1)])
        else:
            file_name = str(file_name[0:match_end])
        base_name = str(file_name[0:match_start])
        if "." in file_name:
            file_name = file_name.replace(".", " ").strip()
            base_name = remove_words(job, base_name.replace(".", " ").strip(), no_words)
            base_name = string.capwords(base_name)
        elif "+" in file_name:
            file_name = file_name.replace("+", " ").strip()
            base_name = remove_words(job, base_name.replace("+", " ").strip(), no_words)
            base_name = string.capwords(base_name)
        file_name = file_name.strip().title()
        base_name = base_name.strip().title()
        file_name = file_name + "." + extension

    elif not match_tv and match_video and match_quality:
        tv_show = False
        movie = True
        file_name = str(file_name[0:match_quality.end()])
        base_name = str(file_name[0:match_quality.start() - 1])
        if "." in file_name:
            file_name = file_name.replace(".", " ").strip()
            base_name = remove_words(job, base_name.replace(".", " ").strip(), no_words)
            base_name = string.capwords(base_name)
        elif "+" in file_name:
            file_name = file_name.replace("+", " ").strip()
            base_name = remove_words(job, base_name.replace("+", " ").strip(), no_words)
            base_name = string.capwords(base_name)
        file_name = file_name.strip().title()
        base_name = base_name.strip().title()
        file_name = file_name + "." + extension

    else:
        tv_show = False
        movie = False
        base_name = ""

    return file_name, tv_show, movie, subtitle, base_name


def greeting() -> str:
    current_time = datetime.now()
    if current_time.hour < 12:
        return 'Good morning'
    elif 12 <= current_time.hour < 18:
        return 'Good afternoon'
    else:
        return 'Good evening'


def check_date_validity(job_id, value) -> (bool, str):
    date_formats = global_var.date_formats
    success = False
    for date_format in date_formats:
        try:
            date_obj = datetime.strptime(value, date_format)
            if '%Y' not in value:
                date_obj = date_obj.replace(year=datetime.now().year)
            value = date_obj.strftime('%Y-%m-%d')
            success = True
            log(job_id, f"Date format accepted {str(value)} for {date_format}")
            break
        except ValueError:
            success = False
            log(job_id, f"Date format mismatch {str(value)} for {date_format}")

    return success, value


def check_time_validity(job_id, value) -> (bool, str):
    time_formats = global_var.time_formats
    success = False
    for time_format in time_formats:
        try:
            time_obj = datetime.strptime(value, time_format).time()
            value = time_obj.strftime("%H:%M:%S")
            success = True
            log(job_id, f"Time format accepted {str(value)} for {time_format}")
            break
        except ValueError:
            success = False
            log(job_id, f"Time format mismatch {str(value)} for {time_format}")

    return success, value
