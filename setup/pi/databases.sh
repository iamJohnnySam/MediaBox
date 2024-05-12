sudo mysql -u root -p

CREATE DATABASE transactions;
CREATE DATABASE administration;
CREATE DATABASE news;
CREATE DATABASE baby;
GRANT ALL PRIVILEGES ON transactions.* TO 'mediabox'@'localhost';
GRANT ALL PRIVILEGES ON administration.* TO 'mediabox'@'localhost';
GRANT ALL PRIVILEGES ON news.* TO 'mediabox'@'localhost';
GRANT ALL PRIVILEGES ON baby.* TO 'mediabox'@'localhost';
FLUSH PRIVILEGES;

CREATE DATABASE administration;
CREATE DATABASE entertainment;
GRANT ALL PRIVILEGES ON administration.* TO 'mediabox'@'localhost';
GRANT ALL PRIVILEGES ON entertainment.* TO 'mediabox'@'localhost';
