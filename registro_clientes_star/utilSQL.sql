CREATE DATABASE cuenta_cliente_star;
USE cuenta_cliente_star6;
SHOW TABLES;

CREATE USER 'user1_star1'@'localhost' IDENTIFIED BY 'user1_star1-1';
GRANT ALL PRIVILEGES ON cuenta_cliente_star.* TO 'user1_star1'@'localhost';

DROP DATABASE IF EXISTS cuenta_cliente_star6;

CREATE DATABASE cuenta_cliente_star4;
GRANT ALL PRIVILEGES ON cuenta_cliente_star4.* TO 'user1_star1'@'localhost';

CREATE DATABASE cuenta_cliente_star5;
GRANT ALL PRIVILEGES ON cuenta_cliente_star5.* TO 'user1_star1'@'localhost';

CREATE DATABASE cuenta_cliente_star6;
GRANT ALL PRIVILEGES ON cuenta_cliente_star6.* TO 'user1_star1'@'localhost';

SELECT * FROM telecom_presupuestotelecom;
DELETE FROM telecom_presupuestotelecom;
DELETE FROM telecom_presupuestotelecom WHERE id = 1;


DELETE FROM telecom_detallepresupuestotelecom;
DELETE FROM telecom_presupuestotelecom;


SELECT id, nombre
FROM dispositivo_marca
ORDER BY nombre;

SELECT id, nombre
FROM dispositivo_tipodispositivo
ORDER BY nombre;

SELECT
    id,
    nombre,
    marca_id,
    tipo_dispositivo_id
FROM dispositivo_modelodispositivo
ORDER BY id;
