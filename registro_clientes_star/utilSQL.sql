CREATE DATABASE cuenta_cliente_star;
USE cuenta_cliente_star;
SHOW TABLES;

CREATE USER 'user1_star1'@'localhost' IDENTIFIED BY 'user1_star1-1';
GRANT ALL PRIVILEGES ON cuenta_cliente_star.* TO 'user1_star1'@'localhost';

DROP TABLE IF EXISTS nombre_tabla;

CREATE DATABASE cuenta_cliente_star2;
GRANT ALL PRIVILEGES ON cuenta_cliente_star2.* TO 'user1_star1'@'localhost';