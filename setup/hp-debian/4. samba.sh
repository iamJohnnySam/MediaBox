sudo apt-get install samba samba-common-bin -y
sudo apt install cifs-utils -y
cd
mkdir media

sudo chmod 777 media

sudo nano /etc/samba/smb.conf

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