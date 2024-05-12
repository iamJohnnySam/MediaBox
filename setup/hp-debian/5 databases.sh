sudo mysql -u root -p

CREATE DATABASE administration;
CREATE DATABASE entertainment;
GRANT ALL PRIVILEGES ON administration.* TO 'mediabox'@'localhost';
GRANT ALL PRIVILEGES ON entertainment.* TO 'mediabox'@'localhost';
quit
