sudo mkdir /mnt/MediaBox
sudo mount /dev/sda1 /mnt/MediaBox

sudo blkid
# /dev/sda1: LABEL="data-ntfs" BLOCK_SIZE="512" UUID="27705CE4072C15B2" TYPE="ntfs" PARTLABEL="data-ntfs" PARTUUID="b62c5b39-5e0f-493c-95a5-032c5cb7adb7"

sudo nano /etc/fstab

# Add to Bottom
UUID=27705CE4072C15B2	/mnt/MediaBox	ntfs	defaults,auto,users,rw 0 0
