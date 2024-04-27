sudo nmcli connection modify 'Wired connection 1' ipv4.address 192.168.1.32/24
sudo nmcli connection modify 'Wired connection 1' ipv4.gateway 192.168.1.1
sudo nmcli connection modify 'Wired connection 1' ipv4.method manual
sudo nmcli connection modify 'Wired connection 1' ipv4.dns '1.1.1.1'
sudo nmcli connection down 'Wired connection 1'
sudo nmcli connection up 'Wired connection 1'
sudo nmcli connection up 'Wired connection 1'