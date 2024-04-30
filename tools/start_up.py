import os
import gitinfo

import global_variables
import refs

if refs.known_hosts[global_variables.host]['system'] == 'Linux':
    print("")
    print("")
    print("")


def keep_gap():
    print("")
    print("")
    print("")


def print_logo():
    if refs.known_hosts[global_variables.host]['system'] == 'Linux':
        os.system("reset")

    print("   _                           _           _                               ____                      ")
    print("  (_)   __ _   _ __ ___       | |   ___   | |__    _ __    _ __    _   _  / ___|    __ _   _ __ ___  ")
    print("  | |  / _\\ | |  _   _ \\   _  | |  / _ \\  |  _ \\  |  _ \\  |  _ \\  | "
          "| | | \\___ \\   / _\\ | |  _   _ \\")
    print("  | | | (_| | | | | | | | | |_| | | (_) | | | | | | | | | | | | | | |_| |  ___) | | (_| | | | | | | |")
    print("  |_|  \\__,_| |_| |_| |_|  \\___/   \\___/  |_| |_| |_| |_| |_| |_|  \\__, | |____/   \\__,_| |_| |_| |_|")
    print("                                                                   |___/                             ")
    if global_variables.host == "spark":
        print("   _____                  __  ")
        print("  / ___/____  ____ ______/ /__")
        print("  \\__ \\/ __ \\/ __ `/ ___/ //_/")
        print(" ___/ / /_/ / /_/ / /  / ,<   ")
        print("/____/ .___/\\__,_/_/  /_/|_|  ")
        print("    /_/                       ")
    elif global_variables.host == "mediabox":
        print("    __  ___         ___       ____             ")
        print("   /  |/  /__  ____/ (_)___ _/ __ )____  _  __ ")
        print("  / /|_/ / _ \\/ __  / / __ `/ __  / __ \\| |/_/ ")
        print(" / /  / /  __/ /_/ / / /_/ / /_/ / /_/ />  <   ")
        print("/_/  /_/\\___/\\__,_/_/\\__,_/_____/\\____/_/|_|   ")

    print("Author: John Neuman Gayan Samarasinghe")
    print("Email: iamJohnnySam@outlook.com")
    print("Domain: iamJohnnySam.com")
    print("Project: Personal Assistant")
    print("Project Details: https://iamjohnnysam.com/post/Personal_Assistant")
    print("")
    print(f"Commit Date: {gitinfo.get_git_info()['author_date']}")
    print(f"Git Author: {gitinfo.get_git_info()['author']}")
    print("")
    print("")
