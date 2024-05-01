sudo apt-get install net-tools
sudo apt-get install ifmetric

ip a
ip r | grep default

sudo nano /etc/network/interfaces

# Add to bottom
allow-hotplug wlx00e05d0b1b82
iface wlx00e05d0b1b82 inet dhcp
        up ifmetric wlx00e05d0b1b82 10
        wpa-ssid xxx
        wpa-psk  xxx

auto enp0s25
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

sudo systemctl restart networking