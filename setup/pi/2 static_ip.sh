ip a
ip r | grep default

sudo nano /etc/network/interfaces

# Rpi
interface eth0
static ip_address=192.168.1.32/24
static routers=192.168.1.1
static domain_name_servers=1.1.1.1

sudo systemctl restart networking