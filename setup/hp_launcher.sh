#!/bin/sh
# launcher.sh
# navigate to home directory, then to this directory, then execute python script, then back home

sudo apt-get update -y
cd /home/hp/MediaBox
python3 -V
git pull origin master
. /home/hp/MediaBox/env/bin/activate
echo $USER
python3 main.py
deactivate