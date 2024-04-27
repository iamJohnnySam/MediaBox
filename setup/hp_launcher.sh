#!/bin/sh
# launcher.sh
# navigate to home directory, then to this directory, then execute python script, then back home

sudo apt-get update -y

reset
echo "   _                           _           _                               ____                      "
echo "  (_)   __ _   _ __ ___       | |   ___   | |__    _ __    _ __    _   _  / ___|    __ _   _ __ ___  "
echo "  | |  / _\ | |  _   _ \   _  | |  / _ \  |  _ \  |  _ \  |  _ \  | | | | \___ \   / _\ | |  _   _ \ "
echo "  | | | (_| | | | | | | | | |_| | | (_) | | | | | | | | | | | | | | |_| |  ___) | | (_| | | | | | | |"
echo "  |_|  \__,_| |_| |_| |_|  \___/   \___/  |_| |_| |_| |_| |_| |_|  \__, | |____/   \__,_| |_| |_| |_|"
echo "                                                                   |___/                             "
echo
echo
echo
cd /home/hp/MediaBox
python -V
git pull origin master
. /home/hp/MediaBox/env/bin/activate
python main.py
deactivate