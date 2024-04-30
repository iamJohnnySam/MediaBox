sudo apt install mariadb-server -y
sudo mysql_secure_installation

sudo apt install phpmyadmin -y


sudo mysql -u root -p
CREATE USER 'mediabox'@'localhost' IDENTIFIED BY 'xxx';
GRANT ALL PRIVILEGES ON *.* TO 'mediabox'@'localhost';

# GRANT ALL PRIVILEGES ON *.* TO 'MediaBox'@'localhost' IDENTIFIED BY 'xxx2' WITH GRANT OPTION;

sudo nano /etc/apache2/apache2.conf

#Add to bottom
Include /etc/phpmyadmin/apache.conf

sudo service apache2 restart
sudo ln -s /usr/share/phpmyadmin /var/www/html