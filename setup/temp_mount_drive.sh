sudo apt-get install ntfs-3g -y

sudo parted -l


sudo mkdir /mnt/ntfs1
sudo mount -t ntfs /dev/sdb1 /mnt/ntfs1
