USE cuenta_cliente_star6;
SHOW TABLES;
SELECT * FROM dispositivo_marca;

INSERT INTO dispositivo_marca
(
    codigo,
    created_at,
    updated_at,
    is_active,
    nombre,
    sitio_web,
    descripcion,
    orden
)
VALUES
('MAR-000001', NOW(), NOW(), 1, 'Hikvision', 'https://www.hikvision.com/', 'Fabricante de soluciones de videovigilancia.', 1),
('MAR-000002', NOW(), NOW(), 1, 'Dahua', 'https://www.dahuasecurity.com/', 'Fabricante de equipos de videovigilancia.', 2),
('MAR-000003', NOW(), NOW(), 1, 'Axis', 'https://www.axis.com/', 'Fabricante de cámaras IP y soluciones de seguridad.', 3),
('MAR-000004', NOW(), NOW(), 1, 'Bosch', 'https://www.boschsecurity.com/', 'Soluciones de seguridad y automatización.', 4),
('MAR-000005', NOW(), NOW(), 1, 'Intelbras', 'https://www.intelbras.com/', 'Equipos de seguridad electrónica y redes.', 5),
('MAR-000006', NOW(), NOW(), 1, 'DSC', 'https://www.dsc.com/', 'Fabricante de sistemas de alarma.', 6),
('MAR-000007', NOW(), NOW(), 1, 'Paradox', 'https://www.paradox.com/', 'Fabricante de sistemas de intrusión.', 7),
('MAR-000008', NOW(), NOW(), 1, 'Honeywell', 'https://www.honeywell.com/', 'Soluciones de seguridad y automatización.', 8),
('MAR-000009', NOW(), NOW(), 1, 'TP-Link', 'https://www.tp-link.com/', 'Equipos de networking.', 9),
('MAR-000010', NOW(), NOW(), 1, 'Ubiquiti', 'https://ui.com/', 'Equipos de redes inalámbricas y switching.', 10),
('MAR-000011', NOW(), NOW(), 1, 'MikroTik', 'https://mikrotik.com/', 'Equipos RouterOS y networking.', 11),
('MAR-000012', NOW(), NOW(), 1, 'Cisco', 'https://www.cisco.com/', 'Infraestructura de redes.', 12),
('MAR-000013', NOW(), NOW(), 1, 'Fortinet', 'https://www.fortinet.com/', 'Firewalls y ciberseguridad.', 13),
('MAR-000014', NOW(), NOW(), 1, 'Grandstream', 'https://www.grandstream.com/', 'Telefonía IP y comunicaciones.', 14),
('MAR-000015', NOW(), NOW(), 1, 'Akuvox', 'https://www.akuvox.com/', 'Porteros IP y control de acceso.', 15),
('MAR-000016', NOW(), NOW(), 1, 'ZKTeco', 'https://www.zkteco.com/', 'Control de acceso y biometría.', 16),
('MAR-000017', NOW(), NOW(), 1, 'HID Global', 'https://www.hidglobal.com/', 'Credenciales y control de acceso.', 17),
('MAR-000018', NOW(), NOW(), 1, 'Ruijie', 'https://www.ruijienetworks.com/', 'Equipos de networking.', 18),
('MAR-000019', NOW(), NOW(), 1, 'Cambium Networks', 'https://www.cambiumnetworks.com/', 'Conectividad inalámbrica.', 19),
('MAR-000020', NOW(), NOW(), 1, 'Genetec', 'https://www.genetec.com/', 'Software de videovigilancia y seguridad.', 20);

SELECT * FROM dispositivo_tipodispositivo;
INSERT INTO dispositivo_tipodispositivo
(
    codigo,
    created_at,
    updated_at,
    is_active,
    nombre,
    descripcion,
    orden
)
VALUES
('TDI-000001', NOW(), NOW(), 1, 'Cámara IP', 'Cámara de videovigilancia IP.', 1),
('TDI-000002', NOW(), NOW(), 1, 'Cámara Analógica', 'Cámara CCTV analógica HD.', 2),
('TDI-000003', NOW(), NOW(), 1, 'Cámara PTZ', 'Cámara motorizada PTZ.', 3),
('TDI-000004', NOW(), NOW(), 1, 'DVR', 'Grabador digital de video.', 4),
('TDI-000005', NOW(), NOW(), 1, 'NVR', 'Grabador de video para cámaras IP.', 5),
('TDI-000006', NOW(), NOW(), 1, 'Encoder de Video', 'Codificador de video IP.', 6),
('TDI-000007', NOW(), NOW(), 1, 'Decoder de Video', 'Decodificador de video IP.', 7),
('TDI-000008', NOW(), NOW(), 1, 'Monitor', 'Monitor para CCTV.', 8),
('TDI-000009', NOW(), NOW(), 1, 'Videowall', 'Pantalla para centro de monitoreo.', 9),

('TDI-000010', NOW(), NOW(), 1, 'Panel de Alarma', 'Central de alarma.', 10),
('TDI-000011', NOW(), NOW(), 1, 'Teclado', 'Teclado de alarma.', 11),
('TDI-000012', NOW(), NOW(), 1, 'Sensor PIR', 'Sensor infrarrojo pasivo.', 12),
('TDI-000013', NOW(), NOW(), 1, 'Sensor Magnético', 'Contacto magnético.', 13),
('TDI-000014', NOW(), NOW(), 1, 'Sensor Sísmico', 'Detector sísmico.', 14),
('TDI-000015', NOW(), NOW(), 1, 'Barrera Infrarroja', 'Barrera IR.', 15),
('TDI-000016', NOW(), NOW(), 1, 'Sirena', 'Sirena interior o exterior.', 16),
('TDI-000017', NOW(), NOW(), 1, 'Comunicador IP', 'Comunicador IP para alarmas.', 17),
('TDI-000018', NOW(), NOW(), 1, 'Comunicador Celular', 'Comunicador GSM/LTE.', 18),
('TDI-000019', NOW(), NOW(), 1, 'Expansora', 'Placa expansora.', 19),
('TDI-000020', NOW(), NOW(), 1, 'Fuente de Alimentación', 'Fuente de alimentación.', 20),

('TDI-000021', NOW(), NOW(), 1, 'Controladora de Acceso', 'Controladora de puertas.', 21),
('TDI-000022', NOW(), NOW(), 1, 'Lector de Proximidad', 'Lector RFID.', 22),
('TDI-000023', NOW(), NOW(), 1, 'Lector Biométrico', 'Lector biométrico.', 23),
('TDI-000024', NOW(), NOW(), 1, 'Electroimán', 'Cerradura electromagnética.', 24),
('TDI-000025', NOW(), NOW(), 1, 'Electropestillo', 'Electropestillo.', 25),
('TDI-000026', NOW(), NOW(), 1, 'Cerradura Eléctrica', 'Cerradura eléctrica.', 26),
('TDI-000027', NOW(), NOW(), 1, 'Botón REX', 'Botón de salida.', 27),
('TDI-000028', NOW(), NOW(), 1, 'Molinete', 'Molinete de acceso.', 28),
('TDI-000029', NOW(), NOW(), 1, 'Barrera Vehicular', 'Barrera automática.', 29),

('TDI-000030', NOW(), NOW(), 1, 'Router', 'Router.', 30),
('TDI-000031', NOW(), NOW(), 1, 'Switch', 'Switch Ethernet.', 31),
('TDI-000032', NOW(), NOW(), 1, 'Switch PoE', 'Switch con alimentación PoE.', 32),
('TDI-000033', NOW(), NOW(), 1, 'Access Point', 'Punto de acceso WiFi.', 33),
('TDI-000034', NOW(), NOW(), 1, 'Firewall', 'Firewall de red.', 34),
('TDI-000035', NOW(), NOW(), 1, 'Conversor de Fibra', 'Conversor FO/Cobre.', 35),
('TDI-000036', NOW(), NOW(), 1, 'Módulo SFP', 'Transceptor SFP.', 36),
('TDI-000037', NOW(), NOW(), 1, 'Patch Panel', 'Patch panel.', 37),
('TDI-000038', NOW(), NOW(), 1, 'Rack', 'Rack de comunicaciones.', 38),

('TDI-000039', NOW(), NOW(), 1, 'UPS', 'Sistema de alimentación ininterrumpida.', 39),
('TDI-000040', NOW(), NOW(), 1, 'Inversor', 'Inversor de tensión.', 40),
('TDI-000041', NOW(), NOW(), 1, 'Banco de Baterías', 'Banco de baterías.', 41),
('TDI-000042', NOW(), NOW(), 1, 'Transformador', 'Transformador.', 42),

('TDI-000043', NOW(), NOW(), 1, 'Servidor', 'Servidor físico.', 43),
('TDI-000044', NOW(), NOW(), 1, 'PC Industrial', 'Computadora industrial.', 44),
('TDI-000045', NOW(), NOW(), 1, 'Tablet', 'Tablet industrial.', 45),

('TDI-000046', NOW(), NOW(), 1, 'Detector de Humo', 'Detector de incendio.', 46),
('TDI-000047', NOW(), NOW(), 1, 'Detector de Temperatura', 'Detector térmico.', 47),
('TDI-000048', NOW(), NOW(), 1, 'Pulsador Manual', 'Pulsador de incendio.', 48),
('TDI-000049', NOW(), NOW(), 1, 'Sirena Estroboscópica', 'Sirena con baliza.', 49),
('TDI-000050', NOW(), NOW(), 1, 'Central de Incendio', 'Panel de incendio.', 50);

INSERT INTO dispositivo_modelodispositivo
(
    codigo,
    created_at,
    updated_at,
    is_active,
    marca_id,
    tipo_dispositivo_id,
    nombre,
    codigo_fabricante,
    descripcion,
    especificaciones,
    orden
)
VALUES

-- =====================================================
-- HIKVISION (marca_id = 1)
-- =====================================================

('MOD-000001', NOW(), NOW(), 1, 1, 1, 'DS-2CD1023G0-I', 'DS-2CD1023G0-I', 'Cámara IP Bullet 2 MP', '2 MP, H.265+, IR 30 m, IP67', 1),
('MOD-000002', NOW(), NOW(), 1, 1, 1, 'DS-2CD2043G2-I', 'DS-2CD2043G2-I', 'Cámara IP Bullet 4 MP', '4 MP, AcuSense, H.265+, IP67', 2),
('MOD-000003', NOW(), NOW(), 1, 1, 1, 'DS-2CD2143G2-I', 'DS-2CD2143G2-I', 'Cámara IP Domo 4 MP', '4 MP, AcuSense, IK10', 3),
('MOD-000004', NOW(), NOW(), 1, 1, 4, 'iDS-7208HQHI-M1', 'iDS-7208HQHI-M1', 'DVR 8 canales', 'H.265 Pro+', 4),
('MOD-000005', NOW(), NOW(), 1, 1, 5, 'DS-7608NXI-K2', 'DS-7608NXI-K2', 'NVR 8 canales', 'AcuSense, 4K', 5),
('MOD-000006', NOW(), NOW(), 1, 1, 32, 'DS-3E1310P-EI', 'DS-3E1310P-EI', 'Switch PoE', '8 PoE + 2 Uplink', 6),
('MOD-000007', NOW(), NOW(), 1, 1, 30, 'DS-3WR12GC', 'DS-3WR12GC', 'Router Gigabit', 'WiFi Dual Band', 7),

-- =====================================================
-- DAHUA (marca_id = 2)
-- =====================================================

('MOD-000008', NOW(), NOW(), 1, 2, 1, 'IPC-HFW2431S-S-S2', 'IPC-HFW2431S-S-S2', 'Cámara IP Bullet 4 MP', 'Starlight, H.265', 8),
('MOD-000009', NOW(), NOW(), 1, 2, 1, 'IPC-HDW2431T-AS-S2', 'IPC-HDW2431T-AS-S2', 'Cámara IP Domo 4 MP', 'Starlight', 9),
('MOD-000010', NOW(), NOW(), 1, 2, 4, 'XVR5108HS-I3', 'XVR5108HS-I3', 'DVR/XVR 8 canales', 'H.265+', 10),
('MOD-000011', NOW(), NOW(), 1, 2, 5, 'NVR2108HS-I2', 'NVR2108HS-I2', 'NVR 8 canales', '4K', 11),
('MOD-000012', NOW(), NOW(), 1, 2, 32, 'PFS3010-8ET-96', 'PFS3010-8ET-96', 'Switch PoE', '8 PoE', 12),

-- =====================================================
-- TP-LINK (marca_id = 9)
-- =====================================================

('MOD-000013', NOW(), NOW(), 1, 9, 30, 'ER605', 'ER605', 'Router VPN', 'Multi WAN Gigabit', 13),
('MOD-000014', NOW(), NOW(), 1, 9, 31, 'TL-SG1024D', 'TL-SG1024D', 'Switch 24 puertos', 'Gigabit', 14),
('MOD-000015', NOW(), NOW(), 1, 9, 32, 'TL-SG1210P', 'TL-SG1210P', 'Switch PoE', '8 PoE + 2 Uplink', 15),
('MOD-000016', NOW(), NOW(), 1, 9, 33, 'EAP225', 'EAP225', 'Access Point', 'WiFi AC1350', 16),
('MOD-000017', NOW(), NOW(), 1, 9, 33, 'EAP610', 'EAP610', 'Access Point WiFi 6', 'AX1800', 17),

-- =====================================================
-- DSC (marca_id = 6)
-- =====================================================

('MOD-000018', NOW(), NOW(), 1, 6, 10, 'PowerSeries NEO HS2032', 'HS2032', 'Panel de alarma', '8 zonas expandible', 18),
('MOD-000019', NOW(), NOW(), 1, 6, 10, 'PowerSeries NEO HS2064', 'HS2064', 'Panel de alarma', '64 zonas', 19),
('MOD-000020', NOW(), NOW(), 1, 6, 11, 'HS2LCD', 'HS2LCD', 'Teclado LCD', 'PowerSeries NEO', 20),
('MOD-000021', NOW(), NOW(), 1, 6, 12, 'LC-100-PI', 'LC-100-PI', 'Sensor PIR', 'Inmunidad mascotas', 21),
('MOD-000022', NOW(), NOW(), 1, 6, 13, 'EV-DW4975', 'EV-DW4975', 'Sensor Magnético', 'Puertas/Ventanas', 22),

-- =====================================================
-- HONEYWELL (marca_id = 8)
-- =====================================================

('MOD-000023', NOW(), NOW(), 1, 8, 10, 'Vista 48LA', 'Vista48LA', 'Panel de alarma', '8 zonas', 23),
('MOD-000024', NOW(), NOW(), 1, 8, 12, 'IS3050', 'IS3050', 'Sensor PIR', 'Infrarrojo pasivo', 24),
('MOD-000025', NOW(), NOW(), 1, 8, 13, '951WG', '951WG', 'Sensor Magnético', 'Uso interior', 25),
('MOD-000026', NOW(), NOW(), 1, 8, 16, 'WAVE2', 'WAVE2', 'Sirena', 'Interior 106 dB', 26),
('MOD-000027', NOW(), NOW(), 1, 8, 20, 'AD12612', 'AD12612', 'Fuente de Alimentación', '12 VCC 1.2 A', 27);


INSERT INTO dispositivo_dispositivo
(
    codigo,
    created_at,
    updated_at,
    is_active,
    modelo_id,
    nombre_comercial,
    descripcion,
    precio_mercado,
    costo,
    orden
)
VALUES
('DIS-000001', NOW(), NOW(), 1, 1, 'Hikvision DS-2CD1023G0-I', 'Cámara IP Hikvision DS-2CD1023G0-I.', 0.00, 0.00, 1),
('DIS-000002', NOW(), NOW(), 1, 2, 'Hikvision DS-2CD2043G2-I', 'Cámara IP Hikvision DS-2CD2043G2-I.', 0.00, 0.00, 2),
('DIS-000003', NOW(), NOW(), 1, 3, 'Hikvision DS-2CD2143G2-I', 'Cámara IP Hikvision DS-2CD2143G2-I.', 0.00, 0.00, 3),
('DIS-000004', NOW(), NOW(), 1, 4, 'Hikvision iDS-7208HQHI-M1', 'DVR Hikvision iDS-7208HQHI-M1.', 0.00, 0.00, 4),
('DIS-000005', NOW(), NOW(), 1, 5, 'Hikvision DS-7608NXI-K2', 'NVR Hikvision DS-7608NXI-K2.', 0.00, 0.00, 5),
('DIS-000006', NOW(), NOW(), 1, 6, 'Hikvision DS-3E1310P-EI', 'Switch PoE Hikvision DS-3E1310P-EI.', 0.00, 0.00, 6),
('DIS-000007', NOW(), NOW(), 1, 7, 'Hikvision DS-3WR12GC', 'Router Hikvision DS-3WR12GC.', 0.00, 0.00, 7),

('DIS-000008', NOW(), NOW(), 1, 8, 'Dahua IPC-HFW2431S-S-S2', 'Cámara IP Dahua IPC-HFW2431S-S-S2.', 0.00, 0.00, 8),
('DIS-000009', NOW(), NOW(), 1, 9, 'Dahua IPC-HDW2431T-AS-S2', 'Cámara IP Dahua IPC-HDW2431T-AS-S2.', 0.00, 0.00, 9),
('DIS-000010', NOW(), NOW(), 1, 10, 'Dahua XVR5108HS-I3', 'DVR Dahua XVR5108HS-I3.', 0.00, 0.00, 10),
('DIS-000011', NOW(), NOW(), 1, 11, 'Dahua NVR2108HS-I2', 'NVR Dahua NVR2108HS-I2.', 0.00, 0.00, 11),
('DIS-000012', NOW(), NOW(), 1, 12, 'Dahua PFS3010-8ET-96', 'Switch PoE Dahua PFS3010-8ET-96.', 0.00, 0.00, 12),

('DIS-000013', NOW(), NOW(), 1, 13, 'TP-Link ER605', 'Router TP-Link ER605.', 0.00, 0.00, 13),
('DIS-000014', NOW(), NOW(), 1, 14, 'TP-Link TL-SG1024D', 'Switch TP-Link TL-SG1024D.', 0.00, 0.00, 14),
('DIS-000015', NOW(), NOW(), 1, 15, 'TP-Link TL-SG1210P', 'Switch PoE TP-Link TL-SG1210P.', 0.00, 0.00, 15),
('DIS-000016', NOW(), NOW(), 1, 16, 'TP-Link EAP225', 'Access Point TP-Link EAP225.', 0.00, 0.00, 16),
('DIS-000017', NOW(), NOW(), 1, 17, 'TP-Link EAP610', 'Access Point WiFi 6 TP-Link EAP610.', 0.00, 0.00, 17),

('DIS-000018', NOW(), NOW(), 1, 18, 'DSC PowerSeries NEO HS2032', 'Panel de alarma DSC PowerSeries NEO HS2032.', 0.00, 0.00, 18),
('DIS-000019', NOW(), NOW(), 1, 19, 'DSC PowerSeries NEO HS2064', 'Panel de alarma DSC PowerSeries NEO HS2064.', 0.00, 0.00, 19),
('DIS-000020', NOW(), NOW(), 1, 20, 'DSC HS2LCD', 'Teclado DSC HS2LCD.', 0.00, 0.00, 20),
('DIS-000021', NOW(), NOW(), 1, 21, 'DSC LC-100-PI', 'Sensor PIR DSC LC-100-PI.', 0.00, 0.00, 21),
('DIS-000022', NOW(), NOW(), 1, 22, 'DSC EV-DW4975', 'Sensor magnético DSC EV-DW4975.', 0.00, 0.00, 22),

('DIS-000023', NOW(), NOW(), 1, 23, 'Honeywell Vista 48LA', 'Panel de alarma Honeywell Vista 48LA.', 0.00, 0.00, 23),
('DIS-000024', NOW(), NOW(), 1, 24, 'Honeywell IS3050', 'Sensor PIR Honeywell IS3050.', 0.00, 0.00, 24),
('DIS-000025', NOW(), NOW(), 1, 25, 'Honeywell 951WG', 'Sensor magnético Honeywell 951WG.', 0.00, 0.00, 25),
('DIS-000026', NOW(), NOW(), 1, 26, 'Honeywell WAVE2', 'Sirena Honeywell WAVE2.', 0.00, 0.00, 26),
('DIS-000027', NOW(), NOW(), 1, 27, 'Honeywell AD12612', 'Fuente de alimentación Honeywell AD12612.', 0.00, 0.00, 27);