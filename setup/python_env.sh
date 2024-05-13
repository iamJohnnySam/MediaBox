sudo apt-get install git -y
sudo apt install python -y
sudo apt install python3.10-venv
sudo apt install python-pip -y

cd MediaBox || exit
python3 -m venv env || exit
source env/bin/activate || exit

pip install numpy
pip install schedule
pip install logger
pip install Flask
pip install telepot
pip install Pillow
pip install feedparser
pip install urllib3
pip install imaplib2
pip install transmission-rpc
pip install mysqlclient
pip install mysql-connector-python
pip install psycopg2
pip install psycopg2-binary
pip install dirsync
pip install IMDbPY
pip install tflite-runtime
pip install gdown
pip install matplotlib
pip install pyodbc
pip install pandas
pip install opencv-python
pip install python-git-info

deactivate
cd || exit

sudo nano launcher.sh
# Install the launcher
sudo chmod 755 launcher.sh