USE cuenta_cliente_star5;
SHOW TABLES;
SELECT * FROM telecom_zonatelecom;

INSERT INTO telecom_zonatelecom
(
    codigo,
    created_at,
    updated_at,
    is_active,
    region,
    provincia,
    ciudad_cabecera,
    factor_multiplicador
)
VALUES
('ZTE-000001', NOW(), NOW(), 1, 'Capital Federal y AMBA', 'AMBA y Capital', 'CABA', 1.00),
('ZTE-000002', NOW(), NOW(), 1, 'Capital Federal y AMBA', 'Buenos Aires', 'CABA', 1.50),

('ZTE-000003', NOW(), NOW(), 1, 'Pcia Buenos Aires, Centro-SUR', 'La Pampa', 'Santa Rosa', 1.80),
('ZTE-000004', NOW(), NOW(), 1, 'Pcia Buenos Aires, Centro-SUR', 'Neuquén', 'Neuquén', 1.80),
('ZTE-000005', NOW(), NOW(), 1, 'Pcia Buenos Aires, Centro-SUR', 'Río Negro', 'Viedma', 1.80),

('ZTE-000006', NOW(), NOW(), 1, 'NOA', 'Santiago del Estero', 'Santiago del Estero', 1.30),
('ZTE-000007', NOW(), NOW(), 1, 'NOA', 'Catamarca', 'San Fernando del Valle de Catamarca', 1.30),
('ZTE-000008', NOW(), NOW(), 1, 'NOA', 'Salta', 'Salta', 1.30),
('ZTE-000009', NOW(), NOW(), 1, 'NOA', 'Jujuy', 'San Salvador de Jujuy', 1.30),
('ZTE-000010', NOW(), NOW(), 1, 'NOA', 'Tucumán', 'San Miguel de Tucumán', 1.30),

('ZTE-000011', NOW(), NOW(), 1, 'SUR', 'Chubut', 'Rawson', 2.00),
('ZTE-000012', NOW(), NOW(), 1, 'SUR', 'Santa Cruz', 'Río Gallegos', 2.00),
('ZTE-000013', NOW(), NOW(), 1, 'SUR', 'Tierra del Fuego', 'Ushuaia', 2.00),

('ZTE-000014', NOW(), NOW(), 1, 'Mediterránea y CUYO', 'Córdoba', 'Córdoba', 1.30),
('ZTE-000015', NOW(), NOW(), 1, 'Mediterránea y CUYO', 'La Rioja', 'La Rioja', 1.30),
('ZTE-000016', NOW(), NOW(), 1, 'Mediterránea y CUYO', 'Mendoza', 'Mendoza', 1.30),
('ZTE-000017', NOW(), NOW(), 1, 'Mediterránea y CUYO', 'San Luis', 'San Luis', 1.30),
('ZTE-000018', NOW(), NOW(), 1, 'Mediterránea y CUYO', 'San Juan', 'San Juan', 1.30),

('ZTE-000019', NOW(), NOW(), 1, 'Litoral', 'Santa Fe', 'Santa Fe', 1.20),
('ZTE-000020', NOW(), NOW(), 1, 'Litoral', 'Entre Ríos', 'Paraná', 1.20),
('ZTE-000021', NOW(), NOW(), 1, 'Litoral', 'Chaco', 'Resistencia', 1.20),
('ZTE-000022', NOW(), NOW(), 1, 'Litoral', 'Formosa', 'Formosa', 1.20),
('ZTE-000023', NOW(), NOW(), 1, 'Litoral', 'Misiones', 'Posadas', 1.20),
('ZTE-000024', NOW(), NOW(), 1, 'Litoral', 'Corrientes', 'Corrientes', 1.20);

SELECT * FROM telecom_conceptotelecom;
INSERT INTO telecom_conceptotelecom
(
    codigo,
    created_at,
    updated_at,
    is_active,
    tipo,
    nombre,
    descripcion,
    moneda,
    precio_unitario
)
VALUES
('CON-000001', NOW(), NOW(), 1, 'MANO_DE_OBRA', 'Reemplazo Panel de alarma', 'Incluye: gabinete, teclado, fuente, comunicador IP y batería', 'PESOS', 145000.00),
('CON-000002', NOW(), NOW(), 1, 'MANO_DE_OBRA', 'Placa de Panel de alarma', 'Incluye: fijación, configuración en sitio y en sistema de gestión, puesta a punto, conexionado, energía, etc', 'PESOS', 67425.00),
('CON-000003', NOW(), NOW(), 1, 'MANO_DE_OBRA', 'Gabinete adicional', 'Incluye: Fuentes, transformadores, placas expansoras, térmicas, fusibles, baterías, comunicador IP', 'PESOS', 54375.00),
('CON-000004', NOW(), NOW(), 1, 'MANO_DE_OBRA', 'Instalación de dispositivo de Intrusión', 'Tipo: Magnetico; PIR; Placa expansora; Fuente de alimentación; Sensor Sísmico; Barrera Infraroja; Teclado; Pulsador Fijo e Inalámbrico; Sirena; Backup Celular; Comunicador IP; Módulo de Relé; Receptor Inalámbrico; Magnetico Inalámbrico; PIR Inalámbrico. (Incluye: fijación, configuración en sitio y en sistemas de gestión, puesta a punto, conexionado, accesorios, energía, etc.)', 'PESOS', 31537.50),
('CON-000005', NOW(), NOW(), 1, 'MANO_DE_OBRA', 'Gabinete exterior interior', 'Incluye: fijación, configuración en sitio y en sistemas de gestión, puesta a punto, conexionado, energía, etc', 'PESOS', 36250.00),
('CON-000006', NOW(), NOW(), 1, 'MANO_DE_OBRA', 'Software DVR / NVR', '', 'PESOS', 45312.00),
('CON-000007', NOW(), NOW(), 1, 'MANO_DE_OBRA', 'Instalación Dispositivo de CCTV', 'Tipo: DVR /NVR / DVR; Cámara CCTV; Domo PTZ; Gabinete Exterior Cámara; Convertidor de Cu a FO y de FO a Cu; Cámara IP; Switch POE Fortinet (incluye: completo, fijación, configuración, puesta a punto, conexionado, energía, actualización firmware, etc)', 'PESOS', 32978.50),
('CON-000008', NOW(), NOW(), 1, 'MANO_DE_OBRA', 'Rack', 'Incluye: bandejas, PDU, coolers', 'PESOS', 36250.00),
('CON-000009', NOW(), NOW(), 1, 'MANO_DE_OBRA', 'Instalación Eléctrica de CCTV', 'Tipo: PDB; Ballonera; UPS; Patchera; Inyector POE; Fuente para riel; Fuente', 'PESOS', 36250.00),
('CON-000010', NOW(), NOW(), 1, 'MANO_DE_OBRA', 'Patch FO de 50 y 100 mts', 'Incluye: fijación, configuración, conexionado, energía, etc', 'PESOS', 54375.00),
('CON-000011', NOW(), NOW(), 1, 'MANO_DE_OBRA', 'Instalación Dispositivo CDA', 'Tipo: Tableros; Golpe de Puño; Retención Electromagnética 600lb y 1200lb; Contactor Tetrapolar; Pulsador REX; Switch; Fuentes; Lectores Proximidad; Disyuntor (incluye: fijación, configuración, puesta a punto, conexionado, red, etc)', 'PESOS', 36250.00),
('CON-000012', NOW(), NOW(), 1, 'MANO_DE_OBRA', 'Instalación Molinete', 'Tipo: Molinete con Buzón; Sin Buzón; Ciego; Puerta discapacitado; Barrera Vehicular (incluye: fijación, configuración en sitio y en sistemas de gestión, puesta a punto, conexionado, energía, red, etc)', 'PESOS', 145000.00),
('CON-000013', NOW(), NOW(), 1, 'MANO_DE_OBRA', 'Instalación Dispositivo CDA 2', 'Tipo: Cerradura Automática Electrónica; Electro Pestillo; Biométrico; Tablet; Cerradura Motorizada (incluye: fijación, configuración en sitio y en sistemas de gestión, puesta a punto, conexionado, energía, red, etc)', 'PESOS', 54375.00),
('CON-000014', NOW(), NOW(), 1, 'MANO_DE_OBRA', 'Tablero Eléctrico', 'Incluye: fijación, configuración, puesta a punto, conexionado, energía, etc', 'PESOS', 27185.50),
('CON-000015', NOW(), NOW(), 1, 'MANO_DE_OBRA', 'Enclosure', 'Incluye: fijación, configuración, puesta a punto, conexionado, energía, etc', 'PESOS', 27185.50),
('CON-000016', NOW(), NOW(), 1, 'MANO_DE_OBRA', 'Controlador de Edificio IC', 'Incluye: fijación, configuración, puesta a punto, conexionado, energía, en sistemas de gestión, etc', 'PESOS', 36250.00),
('CON-000017', NOW(), NOW(), 1, 'MANO_DE_OBRA', 'Controladora de puerta R2', 'Incluye: fijación, configuración, puesta a punto, conexionado, energía, etc', 'PESOS', 27185.50),
('CON-000018', NOW(), NOW(), 1, 'MANO_DE_OBRA', 'Prot. Antivandálica Lector de tarjetas de proximidad', '', 'PESOS', 18125.00),
('CON-000019', NOW(), NOW(), 1, 'MANO_DE_OBRA', 'Ranura seguridad extraíble', 'Incluye fijación, etc', 'PESOS', 27185.50),
('CON-000020', NOW(), NOW(), 1, 'MANO_DE_OBRA', 'Inverter 48VCC 220 VAC', 'Incluye: fijación, configuración, puesta a punto, conexionado, energía, etc', 'PESOS', 54375.00),
('CON-000021', NOW(), NOW(), 1, 'MANO_DE_OBRA', 'Valor fijo x relevamiento', 'Sólo a partir de 50 km', 'PESOS', 283394.84),
('CON-000022', NOW(), NOW(), 1, 'MANO_DE_OBRA', 'Valor por cada km entre cabecera y sitio de obra', 'Suma ida y vuelta. Sólo a partir de 50 km', 'PESOS', 255.84),
('CON-000023', NOW(), NOW(), 1, 'MANO_DE_OBRA', 'Traslado de materiales por cada km entre cabecera y obra', 'Suma ida y vuelta', 'PESOS', 166.30),
('CON-000024', NOW(), NOW(), 1, 'MANO_DE_OBRA', 'Medios de elevación', '', 'PESOS', 745000.00),
('CON-000025', NOW(), NOW(), 1, 'MANO_DE_OBRA', 'Zanjeado y soterrado de caño 1", 1,5" y 2"', 'Caño flexible sobre entre arena y ladrillo superior', 'PESOS', 80000.00),
('CON-000026', NOW(), NOW(), 1, 'MANO_DE_OBRA', 'Instalación de ménsulas', 'Ej.: para UPS 1º 2kva', 'PESOS', 9000.00);


INSERT INTO telecom_conceptotelecom
(
    codigo,
    created_at,
    updated_at,
    is_active,
    tipo,
    nombre,
    descripcion,
    moneda,
    precio_unitario
)
VALUES
('CON-000027', NOW(), NOW(), 1, 'MATERIAL', 'Cable UTP cat 6 ext.', 'Incl. acces incluyen terminales, capuchones, RJ45', 'DOLAR', 3.91),
('CON-000028', NOW(), NOW(), 1, 'MATERIAL', 'Cable Unipolar 1,5 mm', 'Incluyen terminales', 'DOLAR', 1.42),
('CON-000029', NOW(), NOW(), 1, 'MATERIAL', 'Cable RG59', 'Incluye fichas BNC', 'DOLAR', 2.69),
('CON-000030', NOW(), NOW(), 1, 'MATERIAL', 'Cable Unipolar 2,5 mm', 'Incluyen terminales', 'DOLAR', 2.12),
('CON-000031', NOW(), NOW(), 1, 'MATERIAL', 'Cable Unipolar 4 mm', 'Incluye terminales', 'DOLAR', 3.25),
('CON-000032', NOW(), NOW(), 1, 'MATERIAL', 'Cable Unipolar 10 mm', 'Incluye terminales', 'DOLAR', 3.77),
('CON-000033', NOW(), NOW(), 1, 'MATERIAL', 'Cable Unipolar 16 mm', 'Incluye terminales', 'DOLAR', 5.49),
('CON-000034', NOW(), NOW(), 1, 'MATERIAL', 'Cable t/taller 3 hilos c/acc 3 x 2,5 mm', 'Incluye terminales', 'DOLAR', 7.20),
('CON-000035', NOW(), NOW(), 1, 'MATERIAL', 'Cable sintenax 3 x 2,5 mm', 'Incluye terminales', 'DOLAR', 7.33),
('CON-000036', NOW(), NOW(), 1, 'MATERIAL', 'Cable multipar 4 pares', 'Incluyen terminales', 'DOLAR', 1.82),
('CON-000037', NOW(), NOW(), 1, 'MATERIAL', 'Cable Belden 9537', 'Incl. acces.', 'DOLAR', 1.60),
('CON-000038', NOW(), NOW(), 1, 'MATERIAL', 'Cable Belden 9538', 'Incl. acces.', 'DOLAR', 2.93),
('CON-000039', NOW(), NOW(), 1, 'MATERIAL', 'Cable Belden 9842', 'Incl. acces.', 'DOLAR', 3.90),
('CON-000040', NOW(), NOW(), 1, 'MATERIAL', 'Interruptor termomagnético hasta 32 amp (2 Polos)', '', 'DOLAR', 35.46),
('CON-000041', NOW(), NOW(), 1, 'MATERIAL', 'Pase de losa 15 x 15', '', 'DOLAR', 15.03),
('CON-000042', NOW(), NOW(), 1, 'MATERIAL', 'Suministro e instalación exterior de caño galvanizado marca Daysa Sección Ø 3/4"', 'En trazado vertical y horizontal, incluido provisión de elementos de fijación (grampas Olmar y rieles) y accesorios (conectores, cajas y cuplas), totalmente instalado, conectado y funcionando.', 'DOLAR', 31.47),
('CON-000043', NOW(), NOW(), 1, 'MATERIAL', 'Suministro e instalación exterior de caño galvanizado marca Daysa Sección Ø 1"', 'En trazado vertical y horizontal, incluido provisión de elementos de fijación (grampas Olmar y rieles) y accesorios (conectores, cajas y cuplas), totalmente instalado, conectado y funcionando.', 'DOLAR', 34.00),
('CON-000044', NOW(), NOW(), 1, 'MATERIAL', 'Suministro e instalación exterior de caño galvanizado marca Daysa Sección Ø 2"', 'En trazado vertical y horizontal, incluido provisión de elementos de fijación (grampas Olmar y rieles) y accesorios (conectores, cajas y cuplas), totalmente instalado, conectado y funcionando.', 'DOLAR', 103.19),
('CON-000045', NOW(), NOW(), 1, 'MATERIAL', 'Suministro e instalación de caño flexible metálico envainado en PVC Sección Ø 3/4"', 'En trazado vertical y horizontal, incluido provisión de elementos de fijación (grampas Olmar y rieles) y accesorios (conectores, cajas), totalmente instalado, conectado y funcionando.', 'DOLAR', 24.94),
('CON-000046', NOW(), NOW(), 1, 'MATERIAL', 'Suministro e instalación de caño flexible metálico envainado en PVC Sección Ø 1"', 'En trazado vertical y horizontal, incluido provisión de elementos de fijación (grampas Olmar y rieles) y accesorios (conectores, cajas), totalmente instalado, conectado y funcionando.', 'DOLAR', 28.58),
('CON-000047', NOW(), NOW(), 1, 'MATERIAL', 'Suministro e instalación de caño flexible metálico envainado en PVC Sección Ø 2"', 'En trazado vertical y horizontal, incluido provisión de elementos de fijación (grampas Olmar y rieles) y accesorios (conectores, cajas), totalmente instalado, conectado y funcionando.', 'DOLAR', 33.71),
('CON-000048', NOW(), NOW(), 1, 'MATERIAL', 'Suministro e instalación de bandeja portacable 50 mm a 100 mm (con tapa)', 'Con protección anticorrosiva de zincado electrolítico en trazado horizontal y vertical, incluido elementos de sujeción, accesorios (uniones y curvas) y herrería, tipo chapa perforada o escalera.', 'DOLAR', 30.00),
('CON-000049', NOW(), NOW(), 1, 'MATERIAL', 'Suministro e instalación de bandeja portacable 150 mm a 200 mm (con tapa)', 'Con protección anticorrosiva de zincado electrolítico en trazado horizontal y vertical, incluido elementos de sujeción, accesorios (uniones y curvas) y herrería, tipo chapa perforada o escalera.', 'DOLAR', 37.00),
('CON-000050', NOW(), NOW(), 1, 'MATERIAL', 'Suministro e instalación de zócaloducto de PVC hasta 100 x 50 mm Tipo Zoloda', 'En trazado vertical y horizontal, incluido elementos de sujeción, accesorios y tapa, totalmente instalado, conectado y funcionando.', 'DOLAR', 22.50);


SELECT * FROM telecom_recargotelecom;
INSERT INTO telecom_recargotelecom
(
    codigo,
    created_at,
    updated_at,
    is_active,
    tipo,
    factor
)
VALUES
('REC-000001', NOW(), NOW(), 1, 'INSTALACION_NOCTURNO_0_50', 1.20),
('REC-000002', NOW(), NOW(), 1, 'INSTALACION_NOCTURNO_50_MAS', 1.25),
('REC-000003', NOW(), NOW(), 1, 'DESINSTALACION_DIURNO_50_MAS', 1.25),
('REC-000004', NOW(), NOW(), 1, 'DESINSTALACION_NOCTURNO_0_50', 1.25),
('REC-000005', NOW(), NOW(), 1, 'REINSTALACION_NOCTURNO_0_50', 1.25),
('REC-000006', NOW(), NOW(), 1, 'REINSTALACION_NOCTURNO_50_MAS', 1.25),
('REC-000007', NOW(), NOW(), 1, 'SABADO', 1.20),
('REC-000008', NOW(), NOW(), 1, 'DOMINGO', 1.35),
('REC-000009', NOW(), NOW(), 1, 'FERIADO', 1.35);