sudo apt-get install samba samba-common-bin
sudo nano /etc/samba/smb.conf

# Add to Bottom
[media]
path = /home/iamjohnnysam/media
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

[pi]
path = /home/pi
writeable=Yes
create mask=0777
directory mask=0777
public=no

sudo smbpasswd -a pi
sudo systemctl restart smbd