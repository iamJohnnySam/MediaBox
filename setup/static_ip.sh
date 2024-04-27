sudo apt-get install net-tools

ip a
ifconfig -a
ip r | grep default

sudo nano /etc/network/interfaces

# Add to bottom
iface enp0s25 inet static
address 192.168.1.30
network 192.168.1.0
netmask 255.255.255.0
gateway 192.168.1.1
dns-nameservers 1.1.1.1

# Rpi
interface eth0
static ip_address=192.168.1.32/24
static routers=192.168.1.1
static domain_name_servers=1.1.1.1