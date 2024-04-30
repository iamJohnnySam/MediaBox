#!/bin/sh
# launcher.sh
# navigate to home directory, then to this directory, then execute python script, then back home

sudo apt-get update -y
cd /home/hp/MediaBox
python -V
git pull origin master
. /home/hp/MediaBox/env/bin/activate
python main.py
deactivate