mkdir /home/hp/IncompleteDownloads
mkdir /home/hp/media/Downloads

sudo apt-get install transmission-daemon -y
sudo systemctl stop transmission-daemon
sudo nano /etc/transmission-daemon/settings.json

sudo usermod -g hp debian-transmission

sudo chmod 777 /home/hp/
sudo chmod 771 /home/hp/IncompleteDownloads/
sudo chmod 777 /home/hp/media/
sudo chmod 777 /home/hp/media/Downloads

sudo systemctl start transmission-daemon

