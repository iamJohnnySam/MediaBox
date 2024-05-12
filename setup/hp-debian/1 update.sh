# HP
su
apt-get update
apt-get install sudo
sudo usermod -aG sudo hp
sudo nano /etc/sudoers

hp ALL=(ALL) NOPASSWD:ALL

sudo hostnamectl set-hostname mediabox

sudo apt-get update
sudo apt-get upgrade
sudo apt-get update

