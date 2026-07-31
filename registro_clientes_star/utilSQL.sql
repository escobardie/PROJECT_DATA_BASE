CREATE DATABASE cuenta_cliente_star;
USE cuenta_cliente_star4;
SHOW TABLES;

CREATE USER 'user1_star1'@'localhost' IDENTIFIED BY 'user1_star1-1';
GRANT ALL PRIVILEGES ON cuenta_cliente_star.* TO 'user1_star1'@'localhost';

DROP DATABASE IF EXISTS cuenta_cliente_star5;

CREATE DATABASE cuenta_cliente_star4;
GRANT ALL PRIVILEGES ON cuenta_cliente_star4.* TO 'user1_star1'@'localhost';

CREATE DATABASE cuenta_cliente_star5;
GRANT ALL PRIVILEGES ON cuenta_cliente_star5.* TO 'user1_star1'@'localhost';