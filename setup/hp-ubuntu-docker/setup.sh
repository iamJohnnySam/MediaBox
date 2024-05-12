apt-get install sudo
sudo usermod -aG sudo hp
sudo nano /etc/sudoers

hp ALL=(ALL) NOPASSWD:ALL

sudo apt-get update
sudo apt-get upgrade
sudo apt-get update

sudo timedatectl set-timezone Asia/Colombo

sudo nano /etc/netplan/99_config.yaml

network:
  version: 2
  renderer: networkd
  ethernets:
    enp0s25:
      addresses:
        - 192.168.1.30/24
      routes:
        - to: default
          via: 192.168.1.1
      nameservers:
          addresses: [1.1.1.1, 8.8.8.8]

cd
mkdir media
sudo chmod 777 media

UUID=680d5551-6fc0-43fd-8445-3a76bd170605    /home/hp/media/setup ext4  auto,nofail,noatime,rw,user    0   0

sudo apt-get install samba samba-common-bin -y
sudo apt install cifs-utils -y

rsync -av /home/hp/media/setup/media/media/Movies /home/hp/media/Movies
rsync -av /home/hp/media/setup/media/media/TVShows /home/hp/media/TVShows

# Add to Bottom
[media]
    path = /home/hp/media
    writeable=Yes
    create mask=0777
    directory mask=0777
    public=yes

[hp]
    path = /home/hp
    writeable=Yes
    create mask=0777
    directory mask=0777
    public=no

sudo smbpasswd -a hp
sudo systemctl restart smbd


