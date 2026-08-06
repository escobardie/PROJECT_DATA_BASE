USE cuenta_cliente_star6;
SHOW TABLES;
SELECT * FROM catalogo_categoriacatalogo;

INSERT INTO catalogo_categoriacatalogo
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
(
    'CAT-000001',
    NOW(),
    NOW(),
    1,
    'Materiales',
    'Materiales, equipos, componentes y elementos utilizados en instalaciones y proyectos.',
    1
),
(
    'CAT-000002',
    NOW(),
    NOW(),
    1,
    'Insumos',
    'Insumos consumibles y accesorios necesarios para tareas técnicas y operativas.',
    2
),
(
    'CAT-000003',
    NOW(),
    NOW(),
    1,
    'Mano de obra',
    'Tareas de instalación, mantenimiento, configuración, reparación y soporte técnico.',
    3
),
(
    'CAT-000004',
    NOW(),
    NOW(),
    1,
    'Servicios',
    'Servicios técnicos, profesionales, operativos y comerciales.',
    4
),
(
    'CAT-000005',
    NOW(),
    NOW(),
    1,
    'Licencias',
    'Licencias de software, suscripciones, renovaciones y derechos de uso.',
    5
),
(
    'CAT-000006',
    NOW(),
    NOW(),
    1,
    'Viáticos',
    'Gastos asociados a alimentación, alojamiento y movilidad del personal.',
    6
),
(
    'CAT-000007',
    NOW(),
    NOW(),
    1,
    'Traslados',
    'Costos de transporte de personal, herramientas, equipos y materiales.',
    7
),
(
    'CAT-000008',
    NOW(),
    NOW(),
    1,
    'Alquileres',
    'Alquiler de herramientas, vehículos, medios de elevación y equipos especiales.',
    8
),
(
    'CAT-000009',
    NOW(),
    NOW(),
    1,
    'Herramientas',
    'Herramientas manuales, eléctricas, instrumentos y equipos de medición.',
    9
),
(
    'CAT-000010',
    NOW(),
    NOW(),
    1,
    'Equipos de seguridad',
    'Elementos de protección personal, señalización y seguridad laboral.',
    10
),
(
    'CAT-000011',
    NOW(),
    NOW(),
    1,
    'Obra civil',
    'Trabajos de zanjeado, perforación, canalización, mampostería y adecuación edilicia.',
    11
),
(
    'CAT-000012',
    NOW(),
    NOW(),
    1,
    'Electricidad',
    'Materiales y trabajos relacionados con alimentación, tableros y distribución eléctrica.',
    12
),
(
    'CAT-000013',
    NOW(),
    NOW(),
    1,
    'Telecomunicaciones',
    'Materiales, equipos y servicios de redes, fibra óptica y comunicaciones.',
    13
),
(
    'CAT-000014',
    NOW(),
    NOW(),
    1,
    'CCTV',
    'Equipos, materiales y servicios relacionados con videovigilancia.',
    14
),
(
    'CAT-000015',
    NOW(),
    NOW(),
    1,
    'Control de acceso',
    'Equipos, materiales y servicios para control de ingreso y egreso.',
    15
),
(
    'CAT-000016',
    NOW(),
    NOW(),
    1,
    'Intrusión',
    'Equipos, materiales y servicios para sistemas de alarma y detección de intrusión.',
    16
),
(
    'CAT-000017',
    NOW(),
    NOW(),
    1,
    'Detección de incendio',
    'Equipos, materiales y servicios para detección y aviso de incendios.',
    17
),
(
    'CAT-000018',
    NOW(),
    NOW(),
    1,
    'Mantenimiento',
    'Conceptos asociados a mantenimiento preventivo, correctivo y evolutivo.',
    18
),
(
    'CAT-000019',
    NOW(),
    NOW(),
    1,
    'Consultoría',
    'Servicios profesionales de relevamiento, diseño, documentación y asesoramiento.',
    19
),
(
    'CAT-000020',
    NOW(),
    NOW(),
    1,
    'Otros',
    'Conceptos que no corresponden a las categorías principales del catálogo.',
    20
);


INSERT INTO catalogo_itemcatalogo
(
    codigo,
    created_at,
    updated_at,
    is_active,
    categoria_id,
    tipo,
    nombre,
    descripcion,
    unidad,
    costo,
    precio_venta,
    controla_stock,
    orden
)
VALUES

-- =====================================================
-- MANO DE OBRA
-- categoria_id = 3
-- tipo = MANO_OBRA
-- =====================================================

('ITE-000001', NOW(), NOW(), 1, 3, 'MANO_OBRA',
 'Reemplazo Panel de alarma',
 'Incluye gabinete, teclado, fuente, comunicador IP y batería.',
 'UN', 0.00, 145000.00, 0, 1),

('ITE-000002', NOW(), NOW(), 1, 3, 'MANO_OBRA',
 'Placa de Panel de alarma',
 'Incluye fijación, configuración en sitio y sistema de gestión, puesta a punto, conexionado y energía.',
 'UN', 0.00, 67425.00, 0, 2),

('ITE-000003', NOW(), NOW(), 1, 3, 'MANO_OBRA',
 'Gabinete adicional',
 'Incluye fuentes, transformadores, placas expansoras, térmicas, fusibles, baterías y comunicador IP.',
 'UN', 0.00, 54375.00, 0, 3),

('ITE-000004', NOW(), NOW(), 1, 3, 'MANO_OBRA',
 'Instalación de dispositivo de Intrusión',
 'Instalación, fijación, configuración, conexionado y puesta en funcionamiento de dispositivos de intrusión.',
 'UN', 0.00, 31537.50, 0, 4),

('ITE-000005', NOW(), NOW(), 1, 3, 'MANO_OBRA',
 'Gabinete exterior interior',
 'Incluye fijación, configuración, puesta a punto, conexionado y alimentación.',
 'UN', 0.00, 36250.00, 0, 5),

('ITE-000006', NOW(), NOW(), 1, 3, 'MANO_OBRA',
 'Software DVR / NVR',
 'Configuración y puesta en funcionamiento de software para DVR o NVR.',
 'SER', 0.00, 45312.00, 0, 6),

('ITE-000007', NOW(), NOW(), 1, 3, 'MANO_OBRA',
 'Instalación Dispositivo de CCTV',
 'Instalación, fijación, configuración, conexionado, actualización y puesta en funcionamiento de equipos CCTV.',
 'UN', 0.00, 32978.50, 0, 7),

('ITE-000008', NOW(), NOW(), 1, 3, 'MANO_OBRA',
 'Rack',
 'Instalación de rack, bandejas, PDU y ventilación.',
 'UN', 0.00, 36250.00, 0, 8),

('ITE-000009', NOW(), NOW(), 1, 3, 'MANO_OBRA',
 'Instalación Eléctrica de CCTV',
 'Instalación de PDB, balunes, UPS, patchera, inyector PoE y fuentes.',
 'UN', 0.00, 36250.00, 0, 9),

('ITE-000010', NOW(), NOW(), 1, 3, 'MANO_OBRA',
 'Patch FO de 50 y 100 mts',
 'Incluye fijación, configuración, conexionado y puesta en funcionamiento.',
 'UN', 0.00, 54375.00, 0, 10),

('ITE-000011', NOW(), NOW(), 1, 3, 'MANO_OBRA',
 'Instalación Dispositivo CDA',
 'Instalación y configuración de dispositivos de control de acceso.',
 'UN', 0.00, 36250.00, 0, 11),

('ITE-000012', NOW(), NOW(), 1, 3, 'MANO_OBRA',
 'Instalación Molinete',
 'Instalación, fijación, configuración y puesta en funcionamiento de molinetes y barreras.',
 'UN', 0.00, 145000.00, 0, 12),

('ITE-000013', NOW(), NOW(), 1, 3, 'MANO_OBRA',
 'Instalación Dispositivo CDA 2',
 'Instalación de cerradura electrónica, electropestillo, biométrico, tablet o cerradura motorizada.',
 'UN', 0.00, 54375.00, 0, 13),

('ITE-000014', NOW(), NOW(), 1, 3, 'MANO_OBRA',
 'Tablero Eléctrico',
 'Incluye fijación, configuración, conexionado y puesta en funcionamiento.',
 'UN', 0.00, 27185.50, 0, 14),

('ITE-000015', NOW(), NOW(), 1, 3, 'MANO_OBRA',
 'Enclosure',
 'Incluye fijación, configuración, conexionado y puesta en funcionamiento.',
 'UN', 0.00, 27185.50, 0, 15),

('ITE-000016', NOW(), NOW(), 1, 3, 'MANO_OBRA',
 'Controlador de Edificio IC',
 'Instalación, configuración y vinculación con sistemas de gestión.',
 'UN', 0.00, 36250.00, 0, 16),

('ITE-000017', NOW(), NOW(), 1, 3, 'MANO_OBRA',
 'Controladora de puerta R2',
 'Incluye fijación, configuración, conexionado y puesta en funcionamiento.',
 'UN', 0.00, 27185.50, 0, 17),

('ITE-000018', NOW(), NOW(), 1, 3, 'MANO_OBRA',
 'Protección antivandálica para lector de proximidad',
 'Instalación de protección antivandálica para lector de tarjetas.',
 'UN', 0.00, 18125.00, 0, 18),

('ITE-000019', NOW(), NOW(), 1, 3, 'MANO_OBRA',
 'Ranura seguridad extraíble',
 'Incluye fijación y ajuste del dispositivo.',
 'UN', 0.00, 27185.50, 0, 19),

('ITE-000020', NOW(), NOW(), 1, 3, 'MANO_OBRA',
 'Inverter 48VCC 220VAC',
 'Incluye fijación, configuración, conexionado y puesta en funcionamiento.',
 'UN', 0.00, 54375.00, 0, 20),

('ITE-000021', NOW(), NOW(), 1, 3, 'MANO_OBRA',
 'Valor fijo por relevamiento',
 'Valor aplicable a relevamientos realizados a partir de 50 km.',
 'SER', 0.00, 283394.84, 0, 21),

('ITE-000022', NOW(), NOW(), 1, 3, 'MANO_OBRA',
 'Valor por kilómetro entre cabecera y sitio de obra',
 'Se calcula considerando ida y vuelta. Aplicable a partir de 50 km.',
 'M', 0.00, 255.84, 0, 22),

('ITE-000023', NOW(), NOW(), 1, 3, 'MANO_OBRA',
 'Traslado de materiales por kilómetro',
 'Traslado de materiales entre ciudad cabecera y sitio de obra, considerando ida y vuelta.',
 'M', 0.00, 166.30, 0, 23),

('ITE-000024', NOW(), NOW(), 1, 3, 'MANO_OBRA',
 'Medios de elevación',
 'Servicio de utilización de plataforma, hidrogrúa u otro medio de elevación.',
 'D', 0.00, 745000.00, 0, 24),

('ITE-000025', NOW(), NOW(), 1, 3, 'MANO_OBRA',
 'Zanjeado y soterrado de caño',
 'Zanjeado y soterrado de caño de 1, 1.5 o 2 pulgadas, con protección de arena y ladrillo.',
 'M', 0.00, 80000.00, 0, 25),

('ITE-000026', NOW(), NOW(), 1, 3, 'MANO_OBRA',
 'Instalación de ménsulas',
 'Instalación de ménsulas para equipamiento técnico, UPS u otros dispositivos.',
 'UN', 0.00, 9000.00, 0, 26),

-- =====================================================
-- MATERIALES
-- categoria_id = 1
-- tipo = MATERIAL
-- =====================================================

('ITE-000027', NOW(), NOW(), 1, 1, 'MATERIAL',
 'Cable UTP categoría 6 exterior',
 'Incluye terminales, capuchones y conectores RJ45.',
 'M', 0.00, 3.91, 1, 1),

('ITE-000028', NOW(), NOW(), 1, 1, 'MATERIAL',
 'Cable unipolar 1,5 mm',
 'Incluye terminales.',
 'M', 0.00, 1.42, 1, 2),

('ITE-000029', NOW(), NOW(), 1, 1, 'MATERIAL',
 'Cable RG59',
 'Incluye conectores BNC.',
 'M', 0.00, 2.69, 1, 3),

('ITE-000030', NOW(), NOW(), 1, 1, 'MATERIAL',
 'Cable unipolar 2,5 mm',
 'Incluye terminales.',
 'M', 0.00, 2.12, 1, 4),

('ITE-000031', NOW(), NOW(), 1, 1, 'MATERIAL',
 'Cable unipolar 4 mm',
 'Incluye terminales.',
 'M', 0.00, 3.25, 1, 5),

('ITE-000032', NOW(), NOW(), 1, 1, 'MATERIAL',
 'Cable unipolar 10 mm',
 'Incluye terminales.',
 'M', 0.00, 3.77, 1, 6),

('ITE-000033', NOW(), NOW(), 1, 1, 'MATERIAL',
 'Cable unipolar 16 mm',
 'Incluye terminales.',
 'M', 0.00, 5.49, 1, 7),

('ITE-000034', NOW(), NOW(), 1, 1, 'MATERIAL',
 'Cable tipo taller 3 x 2,5 mm',
 'Cable de tres conductores con accesorios y terminales.',
 'M', 0.00, 7.20, 1, 8),

('ITE-000035', NOW(), NOW(), 1, 1, 'MATERIAL',
 'Cable Sintenax 3 x 2,5 mm',
 'Incluye terminales.',
 'M', 0.00, 7.33, 1, 9),

('ITE-000036', NOW(), NOW(), 1, 1, 'MATERIAL',
 'Cable multipar 4 pares',
 'Incluye terminales.',
 'M', 0.00, 1.82, 1, 10),

('ITE-000037', NOW(), NOW(), 1, 1, 'MATERIAL',
 'Cable Belden 9537',
 'Cable Belden con accesorios.',
 'M', 0.00, 1.60, 1, 11),

('ITE-000038', NOW(), NOW(), 1, 1, 'MATERIAL',
 'Cable Belden 9538',
 'Cable Belden con accesorios.',
 'M', 0.00, 2.93, 1, 12),

('ITE-000039', NOW(), NOW(), 1, 1, 'MATERIAL',
 'Cable Belden 9842',
 'Cable Belden con accesorios.',
 'M', 0.00, 3.90, 1, 13),

('ITE-000040', NOW(), NOW(), 1, 1, 'MATERIAL',
 'Interruptor termomagnético hasta 32 A de 2 polos',
 'Interruptor termomagnético bipolar de hasta 32 amperes.',
 'UN', 0.00, 35.46, 1, 14),

('ITE-000041', NOW(), NOW(), 1, 1, 'MATERIAL',
 'Pase de losa 15 x 15',
 'Material y accesorios para pase de losa.',
 'UN', 0.00, 15.03, 1, 15),

('ITE-000042', NOW(), NOW(), 1, 1, 'MATERIAL',
 'Caño galvanizado 3/4 pulgada',
 'Caño galvanizado con grampas, rieles, conectores, cajas y cuplas.',
 'M', 0.00, 31.47, 1, 16),

('ITE-000043', NOW(), NOW(), 1, 1, 'MATERIAL',
 'Caño galvanizado 1 pulgada',
 'Caño galvanizado con grampas, rieles, conectores, cajas y cuplas.',
 'M', 0.00, 34.00, 1, 17),

('ITE-000044', NOW(), NOW(), 1, 1, 'MATERIAL',
 'Caño galvanizado 2 pulgadas',
 'Caño galvanizado con grampas, rieles, conectores, cajas y cuplas.',
 'M', 0.00, 103.19, 1, 18),

('ITE-000045', NOW(), NOW(), 1, 1, 'MATERIAL',
 'Caño flexible metálico envainado PVC 3/4 pulgada',
 'Incluye elementos de fijación, conectores y cajas.',
 'M', 0.00, 24.94, 1, 19),

('ITE-000046', NOW(), NOW(), 1, 1, 'MATERIAL',
 'Caño flexible metálico envainado PVC 1 pulgada',
 'Incluye elementos de fijación, conectores y cajas.',
 'M', 0.00, 28.58, 1, 20),

('ITE-000047', NOW(), NOW(), 1, 1, 'MATERIAL',
 'Caño flexible metálico envainado PVC 2 pulgadas',
 'Incluye elementos de fijación, conectores y cajas.',
 'M', 0.00, 33.71, 1, 21),

('ITE-000048', NOW(), NOW(), 1, 1, 'MATERIAL',
 'Bandeja portacable de 50 a 100 mm con tapa',
 'Bandeja zincada con elementos de sujeción, uniones, curvas y accesorios.',
 'M', 0.00, 30.00, 1, 22),

('ITE-000049', NOW(), NOW(), 1, 1, 'MATERIAL',
 'Bandeja portacable de 150 a 200 mm con tapa',
 'Bandeja zincada con elementos de sujeción, uniones, curvas y accesorios.',
 'M', 0.00, 37.00, 1, 23),

('ITE-000050', NOW(), NOW(), 1, 1, 'MATERIAL',
 'Zócaloducto PVC hasta 100 x 50 mm',
 'Zócaloducto tipo Zoloda con tapa, accesorios y elementos de sujeción.',
 'M', 0.00, 22.50, 1, 24);