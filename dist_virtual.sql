-- MySQL dump 10.13  Distrib 8.0.19, for Win64 (x86_64)
--
-- Host: localhost    Database: distribuidora_virtual
-- ------------------------------------------------------
-- Server version	12.0.2-MariaDB

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `caja_aperturas`
--

DROP TABLE IF EXISTS `caja_aperturas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `caja_aperturas` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `fecha_apertura` datetime NOT NULL,
  `fecha_cierre` datetime DEFAULT NULL,
  `monto_inicial` decimal(10,2) NOT NULL,
  `monto_cierre` decimal(10,2) DEFAULT NULL,
  `efectivo_teorico` decimal(10,2) DEFAULT NULL,
  `efectivo_real` decimal(10,2) DEFAULT NULL,
  `diferencia` decimal(10,2) DEFAULT NULL,
  `observaciones_apertura` text DEFAULT NULL,
  `observaciones_cierre` text DEFAULT NULL,
  `usuario_apertura_id` int(11) NOT NULL,
  `usuario_cierre_id` int(11) DEFAULT NULL,
  `estado` varchar(20) DEFAULT NULL,
  `activa` tinyint(1) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `usuario_apertura_id` (`usuario_apertura_id`),
  KEY `usuario_cierre_id` (`usuario_cierre_id`),
  CONSTRAINT `caja_aperturas_ibfk_1` FOREIGN KEY (`usuario_apertura_id`) REFERENCES `usuario` (`id`),
  CONSTRAINT `caja_aperturas_ibfk_2` FOREIGN KEY (`usuario_cierre_id`) REFERENCES `usuario` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `caja_aperturas`
--

LOCK TABLES `caja_aperturas` WRITE;
/*!40000 ALTER TABLE `caja_aperturas` DISABLE KEYS */;
/*!40000 ALTER TABLE `caja_aperturas` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `cajas`
--

DROP TABLE IF EXISTS `cajas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `cajas` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `fecha_apertura` datetime NOT NULL,
  `fecha_cierre` datetime DEFAULT NULL,
  `monto_inicial` decimal(10,2) NOT NULL,
  `efectivo_teorico` decimal(10,2) DEFAULT NULL,
  `efectivo_real` decimal(10,2) DEFAULT NULL,
  `monto_cierre` decimal(10,2) DEFAULT NULL,
  `diferencia` decimal(10,2) DEFAULT NULL,
  `estado` enum('abierta','cerrada') DEFAULT 'abierta',
  `observaciones_apertura` text DEFAULT NULL,
  `observaciones_cierre` text DEFAULT NULL,
  `usuario_apertura_id` int(11) NOT NULL DEFAULT 3,
  `usuario_cierre_id` int(11) DEFAULT NULL,
  `punto_venta` int(11) NOT NULL DEFAULT 1,
  `activa` tinyint(1) DEFAULT 1,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `fk_cajas_usuario_apertura` (`usuario_apertura_id`),
  KEY `fk_cajas_usuario_cierre` (`usuario_cierre_id`),
  KEY `idx_cajas_fecha_apertura` (`fecha_apertura`),
  KEY `idx_cajas_estado` (`estado`),
  KEY `idx_cajas_activa` (`activa`),
  KEY `idx_cajas_pv` (`punto_venta`),
  CONSTRAINT `fk_cajas_usuario_apertura` FOREIGN KEY (`usuario_apertura_id`) REFERENCES `usuario` (`id`),
  CONSTRAINT `fk_cajas_usuario_cierre` FOREIGN KEY (`usuario_cierre_id`) REFERENCES `usuario` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `cajas`
--

LOCK TABLES `cajas` WRITE;
/*!40000 ALTER TABLE `cajas` DISABLE KEYS */;
INSERT INTO `cajas` VALUES (1,'2026-05-28 17:29:12',NULL,10000.00,1225780.22,NULL,NULL,NULL,'abierta','',NULL,3,NULL,6,1,'2026-05-28 20:29:12');
/*!40000 ALTER TABLE `cajas` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `cancelacion_venta`
--

DROP TABLE IF EXISTS `cancelacion_venta`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `cancelacion_venta` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `fecha` datetime DEFAULT current_timestamp(),
  `usuario_id` int(11) DEFAULT NULL,
  `usuario_nombre` varchar(100) DEFAULT NULL,
  `total` decimal(12,2) DEFAULT NULL,
  `cliente_nombre` varchar(100) DEFAULT NULL,
  `detalle` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`detalle`)),
  `tipo` varchar(30) DEFAULT 'cancelacion_medios_pago',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE='utf8mb4_general_ci';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `cancelacion_venta`
--

LOCK TABLES `cancelacion_venta` WRITE;
/*!40000 ALTER TABLE `cancelacion_venta` DISABLE KEYS */;
INSERT INTO `cancelacion_venta` VALUES (1,'2026-05-28 19:57:43',3,'Administrador',15522.68,'Consumidor Final','[{\"codigo\": \"230\", \"nombre\": \"GOMA FANTASIA MISKY .......x1k\", \"cantidad\": 1, \"precio\": 7200.561983471075, \"subtotal\": 7200.561983471075}, {\"codigo\": \"1014\", \"nombre\": \"GALL TRIO PEPAS..........x320g\", \"cantidad\": 6, \"precio\": 938.0165289256198, \"subtotal\": 5628.099173553719}]','cancelacion_medios_pago'),(2,'2026-05-28 20:49:06',3,'Administrador',15522.68,'Consumidor Final','[{\"codigo\": \"230\", \"nombre\": \"GOMA FANTASIA MISKY .......x1k\", \"cantidad\": 1, \"precio\": 7200.561983471075, \"subtotal\": 7200.561983471075}, {\"codigo\": \"1014\", \"nombre\": \"GALL TRIO PEPAS..........x320g\", \"cantidad\": 6, \"precio\": 938.0165289256198, \"subtotal\": 5628.099173553719}]','cancelacion_medios_pago'),(3,'2026-05-30 14:26:51',3,'Administrador',1747397.11,'Consumidor Final','[{\"codigo\": \"144\", \"nombre\": \"TOP LINE SEVEN MENTA\", \"cantidad\": 1, \"precio\": 9740.99173553719, \"subtotal\": 9740.99173553719}, {\"codigo\": \"230\", \"nombre\": \"GOMA FANTASIA MISKY .......x1k\", \"cantidad\": 1, \"precio\": 7200.561983471075, \"subtotal\": 7200.561983471075}, {\"codigo\": \"240\", \"nombre\": \"GOMAS LA PIÑATA HUESOS ACIDOS X 700 GR\", \"cantidad\": 1, \"precio\": 4231.297520661157, \"subtotal\": 4231.297520661157}, {\"codigo\": \"252\", \"nombre\": \"GOMA BULL DOG.REGALIZ TUTTI F.CJAx12u\", \"cantidad\": 1, \"precio\": 2842.9752, \"subtotal\": 2842.9752}, {\"codigo\": \"266\", \"nombre\": \"MOGUL MORAS X 500G\", \"cantidad\": 268, \"precio\": 4996.0495867768595, \"subtotal\": 1338941.2892561983}, {\"codigo\": \"271\", \"nombre\": \"MOGUL EXTREME LADRILLOS MIX FRUTAL X 500G\", \"cantidad\": 1, \"precio\": 5619.834710743802, \"subtotal\": 5619.834710743802}, {\"codigo\": \"275\", \"nombre\": \"MOGUL EXTREME OSITOS X 500G\", \"cantidad\": 1, \"precio\": 5619.834710743802, \"subtotal\": 5619.834710743802}, {\"codigo\": \"302\", \"nombre\": \"MR.POPS EVOLUTION CEREZA..x24u\", \"cantidad\": 1, \"precio\": 4049.5867768595044, \"subtotal\": 4049.5867768595044}, {\"codigo\": \"304\", \"nombre\": \"MR.POPS EVOLUTION EXTREME.x24u\", \"cantidad\": 1, \"precio\": 4049.5867768595044, \"subtotal\": 4049.5867768595044}, {\"codigo\": \"400\", \"nombre\": \"MASTICABLE SURTIDO MISKY X 800gs\", \"cantidad\": 1, \"precio\": 5454.5455, \"subtotal\": 5454.5455}, {\"codigo\": \"404\", \"nombre\": \"PALITO DE LA SELVA.......x660g\", \"cantidad\": 1, \"precio\": 7107.438, \"subtotal\": 7107.438}, {\"codigo\": \"704\", \"nombre\": \"ROCKLETS 24 X 20GS\", \"cantidad\": 1, \"precio\": 14016.528925619836, \"subtotal\": 14016.528925619836}, {\"codigo\": \"707\", \"nombre\": \"CREMA KROOMY SURTIDOS ( 48u )\", \"cantidad\": 1, \"precio\": 7107.438, \"subtotal\": 7107.438}, {\"codigo\": \"1000\", \"nombre\": \"MAGDAL DON SATUR REL.D/LEx250g\", \"cantidad\": 2, \"precio\": 1727.2727272727273, \"subtotal\": 3454.5454545454545}, {\"codigo\": \"1001\", \"nombre\": \"MAGDAL DON SATUR VAINILLAx250g\", \"cantidad\": 3, \"precio\": 1727.2727272727273, \"subtotal\": 5181.818181818182}, {\"codigo\": \"1002\", \"nombre\": \"MAGDAL DON SATUR MARMOLADx250g\", \"cantidad\": 3, \"precio\": 1727.2727272727273, \"subtotal\": 5181.818181818182}, {\"codigo\": \"1004\", \"nombre\": \"MAGDAL DON SATUR C/CHIPS.x250g\", \"cantidad\": 3, \"precio\": 1727.2727272727273, \"subtotal\": 5181.818181818182}, {\"codigo\": \"961\", \"nombre\": \"MANI TARRO CERVECERO PIZZA\", \"cantidad\": 3, \"precio\": 1176.0330578512396, \"subtotal\": 3528.099173553719}, {\"codigo\": \"268\", \"nombre\": \"MOGUL FRUTILLAS CON CREMA X 500G\", \"cantidad\": 1, \"precio\": 5619.834710743802, \"subtotal\": 5619.834710743802}]','cancelacion_medios_pago'),(4,'2026-06-01 14:06:40',3,'Administrador',37964.08,'Consumidor Final','[{\"codigo\": \"253\", \"nombre\": \"GOMA BULL DOG.REGALIZ FRAMB.CJAx12u\", \"cantidad\": 1, \"precio\": 2644.694214876033, \"subtotal\": 2644.694214876033}, {\"codigo\": \"400\", \"nombre\": \"MASTICABLE SURTIDO MISKY X 800gs\", \"cantidad\": 1, \"precio\": 5363.636363636364, \"subtotal\": 5363.636363636364}, {\"codigo\": \"402\", \"nombre\": \"(x32u)MAST.LENGUETAZO T.FRUTI...\", \"cantidad\": 1, \"precio\": 5322.314049586777, \"subtotal\": 5322.314049586777}, {\"codigo\": \"600\", \"nombre\": \"MARSHMALLOW GONGYS STICK CAJAx216g 18UNID\", \"cantidad\": 1, \"precio\": 3471.0743801652893, \"subtotal\": 3471.0743801652893}, {\"codigo\": \"741\", \"nombre\": \"ALF PESCADO RAUL SIMPLE BLANCO.x50g\", \"cantidad\": 12, \"precio\": 566.1157024793389, \"subtotal\": 6793.388429752067}, {\"codigo\": \"934\", \"nombre\": \"BAGGIO MULTIFRUTAL.......x200m\", \"cantidad\": 18, \"precio\": 432.2314049586777, \"subtotal\": 7780.165289256198}]','cancelacion_medios_pago'),(5,'2026-06-01 14:08:12',3,'Administrador',37964.08,'Consumidor Final','[{\"codigo\": \"253\", \"nombre\": \"GOMA BULL DOG.REGALIZ FRAMB.CJAx12u\", \"cantidad\": 1, \"precio\": 2644.694214876033, \"subtotal\": 2644.694214876033}, {\"codigo\": \"400\", \"nombre\": \"MASTICABLE SURTIDO MISKY X 800gs\", \"cantidad\": 1, \"precio\": 5363.636363636364, \"subtotal\": 5363.636363636364}, {\"codigo\": \"402\", \"nombre\": \"(x32u)MAST.LENGUETAZO T.FRUTI...\", \"cantidad\": 1, \"precio\": 5322.314049586777, \"subtotal\": 5322.314049586777}, {\"codigo\": \"600\", \"nombre\": \"MARSHMALLOW GONGYS STICK CAJAx216g 18UNID\", \"cantidad\": 1, \"precio\": 3471.0743801652893, \"subtotal\": 3471.0743801652893}, {\"codigo\": \"741\", \"nombre\": \"ALF PESCADO RAUL SIMPLE BLANCO.x50g\", \"cantidad\": 12, \"precio\": 566.1157024793389, \"subtotal\": 6793.388429752067}, {\"codigo\": \"934\", \"nombre\": \"BAGGIO MULTIFRUTAL.......x200m\", \"cantidad\": 18, \"precio\": 432.2314049586777, \"subtotal\": 7780.165289256198}]','cancelacion_medios_pago'),(6,'2026-06-03 20:45:59',3,'Administrador',23242.46,'Consumidor Final','[{\"codigo\": \"221\", \"nombre\": \"YUMMY DINO X 12 UND\", \"cantidad\": 1, \"precio\": 4305.892561983471, \"subtotal\": 4305.892561983471}, {\"codigo\": \"224\", \"nombre\": \"YUMMY OSITOS X 12 UND\", \"cantidad\": 1, \"precio\": 4305.94214876033, \"subtotal\": 4305.94214876033}, {\"codigo\": \"225\", \"nombre\": \"YUMMY PECECITOS X 12 UND\", \"cantidad\": 1, \"precio\": 4305.834710743802, \"subtotal\": 4305.834710743802}, {\"codigo\": \"900\", \"nombre\": \"JUGO ARCOR POLVO NARANJA..x18u\", \"cantidad\": 1, \"precio\": 3646.347107438017, \"subtotal\": 3646.347107438017}, {\"codigo\": \"3333\", \"nombre\": \"GOMA BULL DOG.REGALIZ (((SURTIDAS))).CJAx12u\", \"cantidad\": 1, \"precio\": 2644.628099173554, \"subtotal\": 2644.628099173554}]','cancelacion_medios_pago'),(7,'2026-06-04 09:10:53',3,'Administrador',98369.93,'Consumidor Final','[{\"codigo\": \"206\", \"nombre\": \"GOMITAS YUMMY MORITAS X500G\", \"cantidad\": 1, \"precio\": 4032.9586776859505, \"subtotal\": 4032.9586776859505}, {\"codigo\": \"230\", \"nombre\": \"GOMA FANTASIA MISKY .......x1k\", \"cantidad\": 1, \"precio\": 7347.933884297521, \"subtotal\": 7347.933884297521}, {\"codigo\": \"266\", \"nombre\": \"MOGUL MORAS X 500G\", \"cantidad\": 1, \"precio\": 4501.347107438017, \"subtotal\": 4501.347107438017}, {\"codigo\": \"267\", \"nombre\": \"MOGUL DIENTES X 500G\", \"cantidad\": 1, \"precio\": 4497.090909090909, \"subtotal\": 4497.090909090909}, {\"codigo\": \"270\", \"nombre\": \"MOGUL EXTREME LADRILLOS X 500G\", \"cantidad\": 1, \"precio\": 5619.834710743802, \"subtotal\": 5619.834710743802}, {\"codigo\": \"271\", \"nombre\": \"MOGUL EXTREME LADRILLOS MIX FRUTAL X 500G\", \"cantidad\": 1, \"precio\": 5619.834710743802, \"subtotal\": 5619.834710743802}, {\"codigo\": \"702\", \"nombre\": \"CHOCOLATE MISKY  NGRO x25g\", \"cantidad\": 6, \"precio\": 653.9256198347108, \"subtotal\": 3923.553719008265}, {\"codigo\": \"703\", \"nombre\": \"CHOCOLATE MISKY  BCO x25g\", \"cantidad\": 6, \"precio\": 653.9256198347108, \"subtotal\": 3923.553719008265}, {\"codigo\": \"706\", \"nombre\": \"BOCADITO NEVARES DUL.D/LECx15u\", \"cantidad\": 1, \"precio\": 2975.2066115702482, \"subtotal\": 2975.2066115702482}, {\"codigo\": \"718\", \"nombre\": \"ALF FANTOCHE TRI.CHOCOLATEx85g\", \"cantidad\": 6, \"precio\": 687.3140495867768, \"subtotal\": 4123.884297520661}, {\"codigo\": \"719\", \"nombre\": \"ALF FANTOCHE TRIPLE BLANCO.x85g\", \"cantidad\": 6, \"precio\": 676.8595041322315, \"subtotal\": 4061.1570247933887}, {\"codigo\": \"729\", \"nombre\": \"ALFAJOR CHOCOTORTA 71,5\", \"cantidad\": 6, \"precio\": 953.9834710743802, \"subtotal\": 5723.900826446281}, {\"codigo\": \"736\", \"nombre\": \"ALF COFLER BLOCK TRIPLE...x60g\", \"cantidad\": 6, \"precio\": 953.9834710743802, \"subtotal\": 5723.900826446281}, {\"codigo\": \"743\", \"nombre\": \"ALF MINI TORTA AGUILA BROWNIE X74G\", \"cantidad\": 6, \"precio\": 1112.9752066115702, \"subtotal\": 6677.851239669421}, {\"codigo\": \"1030\", \"nombre\": \"SURTIDO BAGLEY...........x400g\", \"cantidad\": 6, \"precio\": 2090.909090909091, \"subtotal\": 12545.454545454546}]','cancelacion_medios_pago');
/*!40000 ALTER TABLE `cancelacion_venta` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `categoria`
--

DROP TABLE IF EXISTS `categoria`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `categoria` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `color` varchar(7) DEFAULT '#6c757d',
  `activo` tinyint(1) DEFAULT 1,
  `orden` int(11) DEFAULT 0,
  `fecha_creacion` timestamp NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `nombre` (`nombre`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE='utf8mb4_general_ci';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `categoria`
--

LOCK TABLES `categoria` WRITE;
/*!40000 ALTER TABLE `categoria` DISABLE KEYS */;
INSERT INTO `categoria` VALUES (1,'gomitas','#22bf6e',1,0,'2026-05-12 22:38:35'),(2,'chicles','#645379',1,0,'2026-05-12 22:55:37');
/*!40000 ALTER TABLE `categoria` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `cheque_propio`
--

DROP TABLE IF EXISTS `cheque_propio`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `cheque_propio` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `banco` varchar(50) NOT NULL,
  `cuenta` varchar(30) DEFAULT NULL,
  `numero` varchar(20) NOT NULL,
  `fecha_emision` date NOT NULL,
  `fecha_vencimiento` date DEFAULT NULL,
  `monto` decimal(12,2) NOT NULL DEFAULT 0.00,
  `estado` varchar(15) NOT NULL DEFAULT 'pendiente' COMMENT 'pendiente/entregado/cobrado/rechazado/anulado',
  `proveedor_id` int(11) DEFAULT NULL,
  `pago_id` int(11) DEFAULT NULL,
  `fecha_entrega` date DEFAULT NULL,
  `fecha_cobro` date DEFAULT NULL,
  `observaciones` text DEFAULT NULL,
  `fecha_carga` datetime NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_ch_prop_banco_num` (`banco`,`numero`),
  KEY `idx_ch_prop_estado` (`estado`),
  KEY `idx_ch_prop_vto` (`fecha_vencimiento`),
  KEY `idx_ch_prop_prov` (`proveedor_id`),
  KEY `idx_ch_prop_pago` (`pago_id`),
  CONSTRAINT `fk_ch_prop_pago` FOREIGN KEY (`pago_id`) REFERENCES `pago_proveedor` (`id`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `fk_ch_prop_prov` FOREIGN KEY (`proveedor_id`) REFERENCES `proveedor` (`id`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE='utf8mb4_general_ci';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `cheque_propio`
--

LOCK TABLES `cheque_propio` WRITE;
/*!40000 ALTER TABLE `cheque_propio` DISABLE KEYS */;
/*!40000 ALTER TABLE `cheque_propio` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `cheque_tercero`
--

DROP TABLE IF EXISTS `cheque_tercero`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `cheque_tercero` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `banco` varchar(50) NOT NULL,
  `numero` varchar(20) NOT NULL,
  `librador` varchar(100) DEFAULT NULL,
  `cuit_librador` varchar(13) DEFAULT NULL,
  `fecha_emision` date DEFAULT NULL,
  `fecha_vencimiento` date DEFAULT NULL,
  `monto` decimal(12,2) NOT NULL DEFAULT 0.00,
  `estado` varchar(15) NOT NULL DEFAULT 'en_cartera' COMMENT 'en_cartera/depositado/endosado/cobrado/rechazado',
  `cliente_origen_id` int(11) DEFAULT NULL,
  `proveedor_destino_id` int(11) DEFAULT NULL,
  `pago_id` int(11) DEFAULT NULL,
  `fecha_recepcion` date DEFAULT NULL,
  `fecha_endoso` date DEFAULT NULL,
  `observaciones` text DEFAULT NULL,
  `fecha_carga` datetime NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `idx_ch_terc_estado` (`estado`),
  KEY `idx_ch_terc_vto` (`fecha_vencimiento`),
  KEY `idx_ch_terc_cli` (`cliente_origen_id`),
  KEY `idx_ch_terc_prov` (`proveedor_destino_id`),
  KEY `idx_ch_terc_pago` (`pago_id`),
  CONSTRAINT `fk_ch_terc_cli` FOREIGN KEY (`cliente_origen_id`) REFERENCES `cliente` (`id`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `fk_ch_terc_pago` FOREIGN KEY (`pago_id`) REFERENCES `pago_proveedor` (`id`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `fk_ch_terc_prov` FOREIGN KEY (`proveedor_destino_id`) REFERENCES `proveedor` (`id`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE='utf8mb4_general_ci';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `cheque_tercero`
--

LOCK TABLES `cheque_tercero` WRITE;
/*!40000 ALTER TABLE `cheque_tercero` DISABLE KEYS */;
/*!40000 ALTER TABLE `cheque_tercero` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `cliente`
--

DROP TABLE IF EXISTS `cliente`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `cliente` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(100) NOT NULL,
  `documento` varchar(20) DEFAULT NULL,
  `tipo_documento` varchar(10) DEFAULT 'DNI',
  `email` varchar(100) DEFAULT NULL,
  `telefono` varchar(20) DEFAULT NULL,
  `direccion` text DEFAULT NULL,
  `condicion_iva` varchar(50) DEFAULT 'CONSUMIDOR_FINAL',
  `fecha_creacion` timestamp NOT NULL DEFAULT current_timestamp(),
  `activo` tinyint(1) DEFAULT 1,
  `lista_precio` int(11) DEFAULT 1,
  `tipo_precio` varchar(10) DEFAULT 'venta',
  `saldo` decimal(12,2) DEFAULT 0.00 COMMENT 'Saldo pendiente del cliente. Positivo=debe, Negativo=a favor',
  `zona_id` int(11) DEFAULT NULL COMMENT 'Zona de reparto del cliente',
  `es_intermediario` tinyint(1) NOT NULL DEFAULT 0 COMMENT 'Cliente intermediario para consignaciones',
  `vendedor_id` int(11) DEFAULT NULL COMMENT 'Vendedor asignado al cliente',
  PRIMARY KEY (`id`),
  KEY `idx_documento` (`documento`),
  KEY `fk_cliente_zona_rep` (`zona_id`),
  KEY `fk_cliente_vendedor_asig` (`vendedor_id`),
  CONSTRAINT `fk_cliente_vendedor_asig` FOREIGN KEY (`vendedor_id`) REFERENCES `vendedor` (`id`) ON DELETE SET NULL,
  CONSTRAINT `fk_cliente_zona_rep` FOREIGN KEY (`zona_id`) REFERENCES `zona` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB AUTO_INCREMENT=95 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `cliente`
--

LOCK TABLES `cliente` WRITE;
/*!40000 ALTER TABLE `cliente` DISABLE KEYS */;
INSERT INTO `cliente` VALUES (1,'Consumidor Final','1111111111','DNI',NULL,NULL,NULL,'CONSUMIDOR_FINAL','2026-05-10 11:14:10',1,1,'venta',0.00,NULL,0,NULL),(2,'CARLA ACUÑA',NULL,'DNI',NULL,'3364176853','ALBERDI 552','CONSUMIDOR_FINAL','2026-05-14 23:58:04',1,1,'venta',0.00,NULL,0,2),(3,'SASANO MARIELA',NULL,'DNI',NULL,'3364633775','MORENO Y LEON GURUCIAGA','CONSUMIDOR_FINAL','2026-05-14 23:58:59',1,1,'venta',0.00,NULL,0,2),(4,'QUIROZ GABRIELA',NULL,'DNI',NULL,'3364279197','LEON GURUCIAGA 561','CONSUMIDOR_FINAL','2026-05-14 23:59:45',1,1,'venta',0.00,NULL,0,2),(5,'MUÑIZ SILVIA',NULL,'DNI',NULL,'3364564728','BELGRANO 681','CONSUMIDOR_FINAL','2026-05-15 00:00:43',1,1,'venta',0.00,NULL,0,2),(6,'ESTEVANO MARIANA',NULL,'DNI',NULL,'3364272434','LAVALLE 614','CONSUMIDOR_FINAL','2026-05-15 00:01:23',1,1,'venta',0.00,NULL,0,2),(7,'CARDOZO ROBERTA',NULL,'DNI',NULL,'3364580078','LAVALLE Y OBLIGADO','CONSUMIDOR_FINAL','2026-05-15 00:01:59',1,1,'venta',0.00,NULL,0,2),(8,'RANELLI AMALIA',NULL,'DNI',NULL,'3364579972','LAVALLE Y OBLIGADO','CONSUMIDOR_FINAL','2026-05-15 00:02:42',1,1,'venta',0.00,NULL,0,2),(9,'SORRENTINO NATALIA',NULL,'DNI',NULL,'3364510117','LAVALLE 521','CONSUMIDOR_FINAL','2026-05-15 00:03:18',1,1,'venta',0.00,NULL,0,2),(10,'VOLKER HECTOR',NULL,'DNI',NULL,'3364298626','MITRE 520','CONSUMIDOR_FINAL','2026-05-15 00:03:59',1,1,'venta',0.00,NULL,0,NULL),(11,'CABRERA NATALIA',NULL,'DNI',NULL,'3364526733','ECHEVERRIA 43','CONSUMIDOR_FINAL','2026-05-15 00:04:33',1,1,'venta',0.00,NULL,0,NULL),(12,'THE MARKET',NULL,'DNI',NULL,'3364350178','NACION Y ECHEVERRIA','CONSUMIDOR_FINAL','2026-05-15 00:05:08',1,1,'venta',0.00,NULL,0,2),(13,'MISERE FRANCO',NULL,'DNI',NULL,'3364287301','NACION 546','CONSUMIDOR_FINAL','2026-05-15 00:05:44',1,1,'venta',0.00,NULL,0,2),(14,'NN',NULL,'DNI',NULL,NULL,'NACION 656','CONSUMIDOR_FINAL','2026-05-15 00:06:18',1,1,'venta',0.00,NULL,0,NULL),(15,'ESCUELA NORMAL',NULL,'DNI',NULL,NULL,NULL,'CONSUMIDOR_FINAL','2026-05-15 00:06:43',1,1,'venta',0.00,NULL,0,2),(16,'SCALISE WALTER',NULL,'DNI',NULL,'3364213373','PELLEGRINI 582','CONSUMIDOR_FINAL','2026-05-15 00:07:30',1,1,'venta',0.00,NULL,0,2),(17,'LOPEZ KARINA',NULL,'DNI',NULL,'3364027632','PELLEGRINI 499 (ESQUINA ROCA)','CONSUMIDOR_FINAL','2026-05-15 00:08:21',1,1,'venta',0.00,NULL,0,2),(18,'SALINAS VALERIA',NULL,'DNI',NULL,'3364200416','PELLEGRINI 483','CONSUMIDOR_FINAL','2026-05-15 00:09:19',1,1,'venta',0.00,NULL,0,2),(19,'GUALDONI MARINA',NULL,'DNI',NULL,'3364386328','SAVIO Y PELLEGRINI','CONSUMIDOR_FINAL','2026-05-15 00:10:12',1,1,'venta',0.00,NULL,0,2),(20,'GEROMINI ROXANA',NULL,'DNI',NULL,'3364646711','SAVIO 54','CONSUMIDOR_FINAL','2026-05-15 00:10:56',1,1,'venta',0.00,NULL,0,2),(21,'GRAZIANI AGUSTINA',NULL,'DNI',NULL,'3364205308','GARIBALDI 543','CONSUMIDOR_FINAL','2026-05-15 00:11:42',1,1,'venta',0.00,NULL,0,2),(22,'VERONICA',NULL,'DNI',NULL,'3364526733','BALCARCE 171','CONSUMIDOR_FINAL','2026-05-15 00:12:42',1,1,'venta',0.00,NULL,0,2),(23,'OZUNA NOELIA',NULL,'DNI',NULL,'3364011077','ESPAÑA 529','CONSUMIDOR_FINAL','2026-05-15 00:13:27',1,1,'venta',0.00,NULL,0,2),(24,'TATO LO DEL CHIMI',NULL,'DNI',NULL,'3364343177','ROCA 177','CONSUMIDOR_FINAL','2026-05-15 00:14:08',1,1,'venta',0.00,NULL,0,2),(25,'PARO DAMIAN',NULL,'DNI',NULL,'3364669861','JUAN B JUSTO 512','CONSUMIDOR_FINAL','2026-05-15 00:14:52',1,1,'venta',0.00,NULL,0,2),(26,'ALEGRETE MARIEL',NULL,'DNI',NULL,'3364568370','FALCON Y ALVEAR','CONSUMIDOR_FINAL','2026-05-15 00:15:34',1,1,'venta',0.00,NULL,0,2),(27,'PAOLA',NULL,'DNI',NULL,'3364544851','SAVIO Y AMEGHINO','CONSUMIDOR_FINAL','2026-05-15 00:16:07',1,1,'venta',0.00,NULL,0,2),(28,'BORDA YASMIN',NULL,'DNI',NULL,'3364544851','ALEM Y GARIBALDI','CONSUMIDOR_FINAL','2026-05-15 00:18:05',1,1,'venta',0.00,NULL,0,2),(29,'GONZALEZ RAMON',NULL,'DNI',NULL,'3364661952','NECOCHEA 559','CONSUMIDOR_FINAL','2026-05-15 00:18:53',1,1,'venta',0.00,NULL,0,2),(30,'RAMIREZ PATRICIA',NULL,'DNI',NULL,'3364255260','NECOCHEA 578','CONSUMIDOR_FINAL','2026-05-15 00:19:26',1,1,'venta',0.00,NULL,0,2),(31,'DIAZ VICTOR',NULL,'DNI',NULL,'3364275914','NECOCHEA 654','CONSUMIDOR_FINAL','2026-05-15 00:20:08',1,1,'venta',0.00,NULL,0,2),(32,'FUGLINI ALICIA',NULL,'DNI',NULL,'3364670049','PRINGLES 614','CONSUMIDOR_FINAL','2026-05-15 00:20:48',1,1,'venta',0.00,NULL,0,2),(33,'GONZALEZ CELESTE',NULL,'DNI',NULL,'3364259530','SAN JOSE 578','CONSUMIDOR_FINAL','2026-05-15 00:21:27',1,1,'venta',0.00,NULL,0,NULL),(34,'FRESART CARLOS',NULL,'DNI',NULL,'3364669223','MORTEO 272','CONSUMIDOR_FINAL','2026-05-15 00:22:01',1,1,'venta',0.00,NULL,0,2),(35,'CINTIA',NULL,'DNI',NULL,'3364307989','SAVIO','CONSUMIDOR_FINAL','2026-05-15 00:23:09',1,1,'venta',0.00,NULL,0,2),(36,'ORTOLANI CAROLINA',NULL,'DNI',NULL,'3364025906','COCHABAMBA 598','CONSUMIDOR_FINAL','2026-05-15 00:24:03',1,1,'venta',0.00,NULL,0,2),(37,'SCARINZI MARTA',NULL,'DNI',NULL,'3364320853','ALVEAR 643','CONSUMIDOR_FINAL','2026-05-15 00:24:38',1,1,'venta',0.00,NULL,0,2),(38,'PEDOTTO GABRIELA',NULL,'DNI',NULL,'3364010298','BENITEZ 578','CONSUMIDOR_FINAL','2026-05-15 00:25:15',1,1,'venta',0.00,NULL,0,2),(39,'FLORENTIN MARIEL',NULL,'DNI',NULL,'3364376016','SAN LORENZO 573','CONSUMIDOR_FINAL','2026-05-15 00:25:53',1,1,'venta',0.00,NULL,0,2),(40,'CASAS AZUCENA',NULL,'DNI',NULL,'3364619294','TERRAZON Y BALCARCE','CONSUMIDOR_FINAL','2026-05-15 00:26:44',1,1,'venta',0.00,NULL,0,2),(41,'TROTTA MIRTA',NULL,'DNI',NULL,'3364381175','COCHABAMBA 750','CONSUMIDOR_FINAL','2026-05-15 00:27:17',1,1,'venta',0.00,NULL,0,2),(42,'TOTRO LUCIANA',NULL,'DNI',NULL,'3364582190','MONTEVIDEO 672','CONSUMIDOR_FINAL','2026-05-15 00:28:07',1,1,'venta',0.00,NULL,0,2),(43,'WEISS URIEL',NULL,'DNI',NULL,'3364676814','COCHABAMBA 648','CONSUMIDOR_FINAL','2026-05-15 00:29:53',1,1,'venta',0.00,NULL,0,2),(44,'JAIME CRISTIAN',NULL,'DNI',NULL,'3364185780','LAS HERAS 677','CONSUMIDOR_FINAL','2026-05-15 00:30:30',1,1,'venta',0.00,NULL,0,2),(45,'MUÑOZ BARBARA',NULL,'DNI',NULL,'3364297352','ROCA 714','CONSUMIDOR_FINAL','2026-05-15 00:31:03',1,1,'venta',0.00,NULL,0,2),(46,'EUCALYPTUS FUSION SAN NICOLAS S.A','30718983343','CUIT',NULL,NULL,'SANTIAGO DERQUI 967','IVA_RESPONSABLE_INSCRIPTO','2026-05-29 20:32:52',1,1,'venta',0.00,NULL,0,1),(47,'LEGUIZAMON MARIELA',NULL,'DNI',NULL,'3364312586','BOGADO 616','CONSUMIDOR_FINAL','2026-05-30 16:19:27',1,2,'venta',0.00,NULL,0,1),(48,'VELAZQUEZ MICAELA',NULL,'DNI',NULL,'3364312586','BROWN 1675','CONSUMIDOR_FINAL','2026-06-01 14:45:16',1,1,'venta',0.00,NULL,0,1),(49,'CORDOBA NORA',NULL,'DNI',NULL,'3364697750','PALERMO 1332','CONSUMIDOR_FINAL','2026-06-01 14:58:34',1,1,'venta',0.00,NULL,0,1),(50,'ACOSTA MARIELA',NULL,'DNI',NULL,'3364289079','MONTIEL 1514','CONSUMIDOR_FINAL','2026-06-01 15:06:40',1,1,'venta',0.00,NULL,0,1),(51,'START UP ORUE VANESA',NULL,'DNI',NULL,'3364201698','MORENO 6','CONSUMIDOR_FINAL','2026-06-01 15:34:22',1,1,'venta',0.00,NULL,0,1),(52,'ASOCIACION MUTUAL ALBOR','30707754075','CUIT',NULL,'3364597066','PELLEGRINI 750','IVA_SUJETO_EXENTO','2026-06-01 15:52:47',1,1,'venta',0.00,NULL,0,NULL),(53,'DAVIDT LUCIANA',NULL,'DNI',NULL,'3364315669','ALVEAR 1704','CONSUMIDOR_FINAL','2026-06-01 15:55:05',1,1,'venta',0.00,NULL,0,1),(54,'FERNANDEZ EMILIA',NULL,'DNI',NULL,NULL,'BV.ITURBURU 297 . GRAL ROJO','CONSUMIDOR_FINAL','2026-06-01 16:00:52',1,1,'venta',0.00,NULL,0,1),(55,'RODRIGUEZ SOLEDAD',NULL,'DNI',NULL,'3364615254','DEL POZO 993','CONSUMIDOR_FINAL','2026-06-01 16:03:57',1,1,'venta',0.00,NULL,0,1),(56,'GARCIA SUSANA',NULL,'DNI',NULL,'3364650126','DEL POZO 2384','CONSUMIDOR_FINAL','2026-06-01 16:06:08',1,1,'venta',0.00,NULL,0,1),(57,'JOURDAN PABLO',NULL,'DNI',NULL,'3416935811','ARAMBURU 1190','CONSUMIDOR_FINAL','2026-06-01 16:08:09',1,1,'venta',0.00,NULL,0,1),(58,'MEZZERA MARIANA',NULL,'DNI',NULL,NULL,'MORENO 406 (FRAY LUIS BELTRAN)','CONSUMIDOR_FINAL','2026-06-01 16:22:56',1,1,'venta',0.00,NULL,0,1),(59,'PIEDRA ANABELLA',NULL,'DNI',NULL,'3364582680','ACEVEDO 2397','CONSUMIDOR_FINAL','2026-06-01 16:24:23',1,1,'venta',0.00,NULL,0,1),(60,'BASUALDO PATRICIA',NULL,'DNI',NULL,'3364185029','DEL POZO 943','CONSUMIDOR_FINAL','2026-06-01 16:26:21',1,1,'venta',0.00,NULL,0,1),(61,'GUTIERREZ MILAGROS',NULL,'DNI',NULL,'3364031382','JUJUY 1335','CONSUMIDOR_FINAL','2026-06-01 16:30:57',1,1,'venta',0.00,NULL,0,1),(62,'SOTO ADELINA',NULL,'DNI',NULL,'3364330864','BERNARDINO DEL POZO 1079','CONSUMIDOR_FINAL','2026-06-01 16:31:58',1,1,'venta',0.00,NULL,0,1),(63,'MARIA ROSA (EP N2)',NULL,'DNI',NULL,NULL,NULL,'CONSUMIDOR_FINAL','2026-06-01 16:33:41',1,1,'venta',0.00,NULL,0,1),(64,'ALMADA MELINA',NULL,'DNI',NULL,'3364356760','ALVEAR 1672','CONSUMIDOR_FINAL','2026-06-01 16:34:44',1,1,'venta',0.00,NULL,0,1),(65,'SADOUX FABIANA',NULL,'DNI',NULL,'3364667842','LA PLATA 1382','CONSUMIDOR_FINAL','2026-06-01 16:43:08',1,1,'venta',0.00,NULL,0,1),(66,'BIERMANN GLENDA (EP 34)',NULL,'DNI',NULL,NULL,NULL,'CONSUMIDOR_FINAL','2026-06-01 16:44:59',1,1,'venta',0.00,NULL,0,1),(67,'CONTRERAS NATALIA',NULL,'DNI',NULL,'3364278186','DEL ACUERDO 1394','CONSUMIDOR_FINAL','2026-06-01 16:47:28',1,1,'venta',0.00,NULL,0,1),(68,'MOSQUERA CESAR',NULL,'DNI',NULL,'3364666134','AUTOPISTA TTE. GRAL ARAMBURU (RN9) KM 223 Y ARROYO RAMALLO (CAMPING)','CONSUMIDOR_FINAL','2026-06-01 17:03:43',1,1,'venta',0.00,NULL,0,1),(69,'SANGASIS CAROLINA',NULL,'DNI',NULL,'3364034729','AV.HIPOLITO IRIGOYEN 402','CONSUMIDOR_FINAL','2026-06-01 17:05:00',1,1,'venta',0.00,NULL,0,1),(70,'RODRIGUEZ ABRIL',NULL,'DNI',NULL,'3364018286','POMBO 911','CONSUMIDOR_FINAL','2026-06-01 17:05:52',1,1,'venta',0.00,NULL,0,1),(71,'MONTALDO MONICA',NULL,'DNI',NULL,'3364656915','RIVADAVIA Y CAVALLI','CONSUMIDOR_FINAL','2026-06-01 17:12:52',1,1,'venta',0.00,NULL,0,2),(72,'MARIANELLI MONICA',NULL,'DNI',NULL,'3364278899','BROWN 1760','CONSUMIDOR_FINAL','2026-06-04 11:38:39',1,1,'venta',0.00,NULL,0,1),(73,'UBAL CLAUDIA',NULL,'DNI',NULL,'3364352304','GENDARMERIA NACIONA 668','CONSUMIDOR_FINAL','2026-06-04 11:40:20',1,1,'venta',0.00,NULL,0,1),(74,'RIGALI MAIRA ALEJANDRA',NULL,'DNI',NULL,'3364182191','HOWARD 1571','CONSUMIDOR_FINAL','2026-06-04 12:48:40',1,1,'venta',0.00,NULL,0,1),(75,'SOLOAGA ALEJO',NULL,'DNI',NULL,'3364285537',NULL,'CONSUMIDOR_FINAL','2026-06-04 15:43:57',1,1,'venta',0.00,NULL,0,2),(76,'SUSTO MIRIAM',NULL,'DNI',NULL,'3364332465','25 DE MAYO 477','CONSUMIDOR_FINAL','2026-06-04 15:53:53',1,1,'venta',0.00,NULL,0,2),(77,'HERRERA MIRTA',NULL,'DNI',NULL,'3364374164','PAOLINI 137','CONSUMIDOR_FINAL','2026-06-04 15:58:52',1,1,'venta',0.00,NULL,0,2),(78,'ENGELBRECHT ULISES',NULL,'DNI',NULL,'3364290508','ALVEAR 470','CONSUMIDOR_FINAL','2026-06-04 16:04:50',1,1,'venta',0.00,NULL,0,1),(79,'RABO ALICIA',NULL,'DNI',NULL,'3364214154','TERRAZON 302','CONSUMIDOR_FINAL','2026-06-04 16:08:30',1,1,'venta',0.00,NULL,0,2),(80,'KERPS GIMENA ( EP31 )',NULL,'DNI',NULL,NULL,'URQUIZA 529','CONSUMIDOR_FINAL','2026-06-04 22:19:45',1,1,'venta',0.00,NULL,0,1),(81,'BERTI JUAN CRUZ',NULL,'DNI',NULL,'3364549778','REYNOSO 319','CONSUMIDOR_FINAL','2026-06-05 13:20:28',1,1,'venta',0.00,NULL,0,1),(82,'FERREYRA MARIA',NULL,'DNI',NULL,'3364635372','LA PLATA 1333','CONSUMIDOR_FINAL','2026-06-05 22:48:06',1,1,'venta',0.00,NULL,0,1),(83,'PELLIERINO SERGIO',NULL,'DNI',NULL,'3364657960','SAN JOSE 578','CONSUMIDOR_FINAL','2026-06-07 22:15:51',1,1,'venta',0.00,NULL,0,2),(84,'NAVARRO HECTOR',NULL,'DNI',NULL,'3364564163','VARELA 731','CONSUMIDOR_FINAL','2026-06-07 22:19:31',1,1,'venta',0.00,NULL,0,2),(85,'SIVORI MARIA SOL',NULL,'DNI',NULL,'3364196448','AV.FALCON 242','CONSUMIDOR_FINAL','2026-06-07 22:21:31',1,1,'venta',0.00,NULL,0,2),(86,'CLERICI ALICIA',NULL,'DNI',NULL,'3364206994','RIVADAVIA Y NECOCHEA','CONSUMIDOR_FINAL','2026-06-07 22:22:12',1,1,'venta',0.00,NULL,0,2),(87,'IMAZ CARLOS',NULL,'DNI',NULL,'3364006775','DON BOSCO 478','CONSUMIDOR_FINAL','2026-06-07 22:23:08',1,1,'venta',0.00,NULL,0,2),(88,'VICTORIA MARKET 275',NULL,'DNI',NULL,'3364272119','SAVIO 275','CONSUMIDOR_FINAL','2026-06-07 22:23:55',1,1,'venta',0.00,NULL,0,2),(89,'DIAZ DAIANA',NULL,'DNI',NULL,'3364670208','POMBO 941','CONSUMIDOR_FINAL','2026-06-07 22:28:19',1,1,'venta',0.00,NULL,0,1),(90,'AREVALO SANDRA',NULL,'DNI',NULL,'3364185783','PALERMO 1337','CONSUMIDOR_FINAL','2026-06-07 22:29:42',1,1,'venta',0.00,NULL,0,1),(91,'RICHARD PATRICIA',NULL,'DNI',NULL,'3364645260','PALERMO 1368','CONSUMIDOR_FINAL','2026-06-07 22:30:21',1,1,'venta',0.00,NULL,0,1),(92,'YACUZZI PAOLA',NULL,'DNI',NULL,'3364317961','MALVINAS ARGENTINAS 1045','CONSUMIDOR_FINAL','2026-06-07 22:32:53',1,1,'venta',0.00,NULL,0,1),(93,'SOSA MAURICIO',NULL,'DNI',NULL,'3364319760','SECTOR N CASA 4','CONSUMIDOR_FINAL','2026-06-07 22:34:21',1,1,'venta',0.00,NULL,0,1),(94,'MONTES NATALIA',NULL,'DNI',NULL,'3364617107','DEL POZO 2335','CONSUMIDOR_FINAL','2026-06-07 22:35:13',1,1,'venta',0.00,NULL,0,1);
/*!40000 ALTER TABLE `cliente` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `configuracion`
--

DROP TABLE IF EXISTS `configuracion`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `configuracion` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `clave` varchar(100) NOT NULL,
  `valor` text DEFAULT NULL,
  `descripcion` varchar(255) DEFAULT NULL,
  `fecha_modificacion` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `clave` (`clave`)
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `configuracion`
--

LOCK TABLES `configuracion` WRITE;
/*!40000 ALTER TABLE `configuracion` DISABLE KEYS */;
INSERT INTO `configuracion` VALUES (1,'empresa_razon_social','DISTRIBUIDORA DEMO SRL','Razón social de la empresa','2026-05-09 23:58:19'),(2,'empresa_cuit','20000000000','CUIT de la empresa','2026-05-09 23:58:19'),(3,'empresa_direccion','Sin definir','Dirección de la empresa','2026-05-09 23:58:19'),(4,'empresa_telefono','Sin definir','Teléfono de la empresa','2026-05-09 23:58:19'),(5,'empresa_email','demo@distribuidora.com','Email de la empresa','2026-05-09 23:58:19'),(6,'punto_venta','1','Número de punto de venta AFIP','2025-08-09 18:39:16'),(7,'usa_afip','true','Si usa integración con AFIP','2025-08-09 18:39:16'),(8,'ambiente_afip','homologacion','Ambiente AFIP: homologacion o produccion','2025-08-09 18:39:16'),(9,'redondear_precios','false','Si es true, redondea precios de venta al entero más cercano (10.58 → 11)','2026-05-07 21:56:32');
/*!40000 ALTER TABLE `configuracion` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `configuracion_pedidos`
--

DROP TABLE IF EXISTS `configuracion_pedidos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `configuracion_pedidos` (
  `id` int(11) NOT NULL DEFAULT 1,
  `lista_retiro` int(11) DEFAULT 1,
  `lista_envio` int(11) DEFAULT 2,
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `configuracion_pedidos`
--

LOCK TABLES `configuracion_pedidos` WRITE;
/*!40000 ALTER TABLE `configuracion_pedidos` DISABLE KEYS */;
INSERT INTO `configuracion_pedidos` VALUES (1,1,1,'2026-05-09 01:42:13');
/*!40000 ALTER TABLE `configuracion_pedidos` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `cta_cte_detalle`
--

DROP TABLE IF EXISTS `cta_cte_detalle`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `cta_cte_detalle` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `movimiento_id` int(11) NOT NULL,
  `producto_id` int(11) NOT NULL,
  `descripcion` varchar(200) DEFAULT NULL,
  `cantidad` decimal(10,3) NOT NULL,
  `precio_unitario` decimal(10,2) NOT NULL,
  `subtotal` decimal(12,2) NOT NULL,
  `porcentaje_iva` decimal(5,2) DEFAULT 21.00,
  `importe_iva` decimal(10,2) DEFAULT 0.00,
  `estado` varchar(20) DEFAULT 'pendiente',
  `factura_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_movimiento_id` (`movimiento_id`),
  CONSTRAINT `fk_ctacte_movimiento` FOREIGN KEY (`movimiento_id`) REFERENCES `cta_cte_movimiento` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE='utf8mb4_general_ci';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `cta_cte_detalle`
--

LOCK TABLES `cta_cte_detalle` WRITE;
/*!40000 ALTER TABLE `cta_cte_detalle` DISABLE KEYS */;
/*!40000 ALTER TABLE `cta_cte_detalle` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `cta_cte_movimiento`
--

DROP TABLE IF EXISTS `cta_cte_movimiento`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `cta_cte_movimiento` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `cliente_id` int(11) NOT NULL,
  `fecha` datetime DEFAULT current_timestamp(),
  `tipo` enum('venta_fiada','pago','nota_credito','ajuste') NOT NULL DEFAULT 'venta_fiada',
  `estado` enum('pendiente','pagado','cancelado') DEFAULT 'pendiente',
  `monto_total` decimal(10,2) NOT NULL,
  `factura_id` int(11) DEFAULT NULL,
  `usuario_id` int(11) NOT NULL,
  `observaciones` text DEFAULT NULL,
  `numero_comprobante` varchar(30) DEFAULT NULL,
  `saldo_pendiente` decimal(12,2) DEFAULT 0.00,
  `tipo_mov` enum('venta','pago','ajuste') DEFAULT 'venta',
  PRIMARY KEY (`id`),
  KEY `idx_cliente` (`cliente_id`),
  KEY `idx_estado` (`estado`),
  KEY `idx_fecha` (`fecha`),
  KEY `fk_cta_cte_factura` (`factura_id`),
  KEY `fk_cta_cte_usuario` (`usuario_id`),
  CONSTRAINT `fk_cta_cte_cliente` FOREIGN KEY (`cliente_id`) REFERENCES `cliente` (`id`),
  CONSTRAINT `fk_cta_cte_factura` FOREIGN KEY (`factura_id`) REFERENCES `factura` (`id`),
  CONSTRAINT `fk_cta_cte_usuario` FOREIGN KEY (`usuario_id`) REFERENCES `usuario` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=84 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `cta_cte_movimiento`
--

LOCK TABLES `cta_cte_movimiento` WRITE;
/*!40000 ALTER TABLE `cta_cte_movimiento` DISABLE KEYS */;
INSERT INTO `cta_cte_movimiento` VALUES (1,47,'2026-05-30 14:28:55','venta_fiada','pendiente',133323.37,7,3,'Comprobante 0006-X0000003','0006-X0000003',133323.37,'venta'),(2,48,'2026-06-01 11:55:23','venta_fiada','pendiente',78549.87,8,3,'Comprobante 0006-X0000004','0006-X0000004',78549.87,'venta'),(3,49,'2026-06-01 12:00:09','venta_fiada','pagado',45142.00,9,3,'Comprobante 0006-X0000005','0006-X0000005',0.00,'venta'),(5,50,'2026-06-01 12:26:33','venta_fiada','pendiente',31115.00,NULL,3,'Saldo inicial: Migrado desde sistema anterior',NULL,16115.00,'venta'),(6,19,'2026-06-01 12:29:23','venta_fiada','pagado',26761.00,NULL,3,'Saldo inicial: Migrado desde sistema anterior',NULL,0.00,'venta'),(7,51,'2026-06-01 12:46:29','venta_fiada','pendiente',119317.50,NULL,3,'Saldo inicial: Migrado desde sistema anterior',NULL,119317.50,'venta'),(8,17,'2026-06-01 12:47:26','venta_fiada','pagado',36152.00,NULL,3,'Saldo inicial: Migrado desde sistema anterior',NULL,0.00,'venta'),(9,36,'2026-06-01 12:47:54','venta_fiada','pendiente',47760.00,NULL,3,'Saldo inicial: Migrado desde sistema anterior',NULL,3310.00,'venta'),(10,52,'2026-06-01 12:53:48','venta_fiada','pagado',68750.00,NULL,3,'Saldo inicial: Migrado desde sistema anterior',NULL,0.00,'venta'),(11,53,'2026-06-01 12:57:20','venta_fiada','pendiente',87880.00,NULL,3,'Saldo inicial: Migrado desde sistema anterior',NULL,87880.00,'venta'),(12,54,'2026-06-01 13:01:24','venta_fiada','pendiente',1075892.00,NULL,3,'Saldo inicial: Migrado desde sistema anterior',NULL,1075892.00,'venta'),(13,55,'2026-06-01 13:04:29','venta_fiada','pagado',106143.00,NULL,3,'Saldo inicial: Migrado desde sistema anterior',NULL,0.00,'venta'),(14,56,'2026-06-01 13:06:31','venta_fiada','pendiente',111678.00,NULL,3,'Saldo inicial: Migrado desde sistema anterior',NULL,111678.00,'venta'),(15,57,'2026-06-01 13:11:11','venta_fiada','pendiente',400115.00,NULL,3,'Saldo inicial: Migrado desde sistema anterior',NULL,400115.00,'venta'),(16,58,'2026-06-01 13:23:27','venta_fiada','pendiente',210780.00,NULL,3,'Saldo inicial: Migrado desde sistema anterior',NULL,210780.00,'venta'),(17,59,'2026-06-01 13:24:54','venta_fiada','pagado',60000.00,NULL,3,'Saldo inicial: Migrado desde sistema anterior',NULL,0.00,'venta'),(18,60,'2026-06-01 13:26:53','venta_fiada','pagado',57348.00,NULL,3,'Saldo inicial: Migrado desde sistema anterior',NULL,0.00,'venta'),(19,61,'2026-06-01 13:31:14','venta_fiada','pendiente',33155.00,NULL,3,'Saldo inicial: Migrado desde sistema anterior',NULL,33155.00,'venta'),(20,62,'2026-06-01 13:32:18','venta_fiada','pagado',30046.00,NULL,3,'Saldo inicial: Migrado desde sistema anterior',NULL,0.00,'venta'),(21,63,'2026-06-01 13:34:01','venta_fiada','pendiente',134544.00,NULL,3,'Saldo inicial: Migrado desde sistema anterior',NULL,94544.00,'venta'),(22,64,'2026-06-01 13:35:01','venta_fiada','pagado',52014.00,NULL,3,'Saldo inicial: Migrado desde sistema anterior',NULL,0.00,'venta'),(23,65,'2026-06-01 13:43:23','venta_fiada','pendiente',181669.00,NULL,3,'Saldo inicial: Migrado desde sistema anterior',NULL,181669.00,'venta'),(24,66,'2026-06-01 13:45:17','venta_fiada','pagado',98836.00,NULL,3,'Saldo inicial: Migrado desde sistema anterior',NULL,0.00,'venta'),(25,67,'2026-06-01 13:47:46','venta_fiada','pendiente',15000.00,NULL,3,'Saldo inicial: Migrado desde sistema anterior',NULL,15000.00,'venta'),(26,46,'2026-06-01 14:01:54','venta_fiada','pendiente',669110.60,NULL,3,'Saldo inicial: Migrado desde sistema anterior',NULL,316901.00,'venta'),(27,68,'2026-06-01 14:04:04','venta_fiada','pendiente',358324.00,NULL,3,'Saldo inicial: Migrado desde sistema anterior',NULL,236324.00,'venta'),(28,69,'2026-06-01 14:05:18','venta_fiada','pagado',45914.00,NULL,3,'Saldo inicial: Migrado desde sistema anterior',NULL,0.00,'venta'),(29,70,'2026-06-01 14:06:23','venta_fiada','pagado',26796.00,NULL,3,'Saldo inicial: Migrado desde sistema anterior',NULL,0.00,'venta'),(30,63,'2026-06-01 14:10:04','venta_fiada','pendiente',37964.08,10,3,'Comprobante 0006-X0000006','0006-X0000006',37964.08,'venta'),(31,71,'2026-06-01 14:13:28','venta_fiada','pendiente',192927.00,NULL,3,'Saldo inicial: Migrado desde sistema anterior',NULL,142927.00,'venta'),(32,62,'2026-06-01 20:04:43','venta_fiada','pendiente',56818.00,11,3,'Comprobante 0006-X0000007','0006-X0000007',56818.00,'venta'),(33,46,'2026-06-02 14:55:03','venta_fiada','pendiente',145741.50,12,3,'Comprobante 0006-00000005','0006-00000005',145741.50,'venta'),(34,52,'2026-06-02 17:24:10','pago','pagado',68750.00,NULL,3,'Recibo de cobro R00000001','R00000001',0.00,'pago'),(35,46,'2026-06-02 18:13:17','pago','pagado',352209.60,NULL,3,'Recibo de cobro R00000002','R00000002',0.00,'pago'),(36,66,'2026-06-02 18:14:29','pago','pagado',38600.00,NULL,3,'Recibo de cobro R00000003','R00000003',0.00,'pago'),(37,63,'2026-06-02 18:30:06','pago','pagado',40000.00,NULL,3,'Recibo de cobro R00000004','R00000004',0.00,'pago'),(38,70,'2026-06-02 18:30:43','pago','pagado',26796.00,NULL,3,'Recibo de cobro R00000005','R00000005',0.00,'pago'),(39,62,'2026-06-02 18:31:55','pago','pagado',30046.00,NULL,3,'Recibo de cobro R00000006','R00000006',0.00,'pago'),(40,66,'2026-06-02 18:33:07','pago','pagado',40100.00,NULL,3,'Recibo de cobro R00000007','R00000007',0.00,'pago'),(41,64,'2026-06-03 20:27:55','venta_fiada','pendiente',92129.43,13,3,'Comprobante 0006-X0000008','0006-X0000008',92129.43,'venta'),(42,60,'2026-06-04 08:30:07','venta_fiada','pendiente',68528.76,14,3,'Comprobante 0006-X0000009','0006-X0000009',68528.76,'venta'),(43,71,'2026-06-04 08:34:44','venta_fiada','pendiente',36511.70,15,3,'Comprobante 0006-X0000010','0006-X0000010',36511.70,'venta'),(44,73,'2026-06-04 08:52:12','venta_fiada','pendiente',23242.46,16,3,'Comprobante 0006-X0000011','0006-X0000011',23242.46,'venta'),(45,72,'2026-06-04 08:57:08','venta_fiada','pagado',36511.70,17,3,'Comprobante 0006-X0000012','0006-X0000012',0.00,'venta'),(46,55,'2026-06-04 09:07:01','venta_fiada','pendiente',89395.12,18,3,'Comprobante 0006-X0000013','0006-X0000013',89395.12,'venta'),(47,65,'2026-06-04 09:11:20','venta_fiada','pendiente',98369.93,19,3,'Comprobante 0006-X0000014','0006-X0000014',98369.93,'venta'),(48,51,'2026-06-04 09:43:48','venta_fiada','pendiente',118922.29,20,3,'Comprobante 0006-X0000015','0006-X0000015',118922.29,'venta'),(49,74,'2026-06-04 10:05:27','venta_fiada','pendiente',121730.94,21,3,'Comprobante 0006-X0000016','0006-X0000016',121730.94,'venta'),(50,66,'2026-06-04 10:34:35','venta_fiada','pendiente',249441.65,22,3,'Comprobante 0006-X0000017','0006-X0000017',205391.65,'venta'),(51,4,'2026-06-04 11:03:57','venta_fiada','pendiente',79416.96,23,3,'Comprobante 0006-X0000018','0006-X0000018',79416.96,'venta'),(52,19,'2026-06-04 12:34:40','venta_fiada','pendiente',20362.00,24,3,'Comprobante 0006-X0000019','0006-X0000019',20362.00,'venta'),(53,30,'2026-06-04 12:36:59','venta_fiada','pendiente',87201.38,25,3,'Comprobante 0006-X0000020','0006-X0000020',87201.38,'venta'),(54,39,'2026-06-04 12:38:56','venta_fiada','pagado',32095.80,26,3,'Comprobante 0006-X0000021','0006-X0000021',0.00,'venta'),(55,38,'2026-06-04 12:41:34','venta_fiada','pagado',39571.46,27,3,'Comprobante 0006-X0000022','0006-X0000022',0.00,'venta'),(56,75,'2026-06-04 12:46:13','venta_fiada','pendiente',46999.78,28,3,'Comprobante 0006-X0000023','0006-X0000023',46999.78,'venta'),(57,52,'2026-06-04 19:17:18','venta_fiada','pendiente',110782.30,34,3,'Comprobante 0006-X0000029','0006-X0000029',110782.30,'venta'),(58,80,'2026-06-04 19:26:48','venta_fiada','pendiente',40633.00,35,3,'Comprobante 0006-X0000030','0006-X0000030',40633.00,'venta'),(59,80,'2026-06-04 19:55:59','venta_fiada','pendiente',280427.82,36,3,'Comprobante 0006-X0000031','0006-X0000031',280427.82,'venta'),(60,81,'2026-06-05 10:22:47','venta_fiada','pendiente',60800.00,38,3,'Comprobante 0006-X0000033','0006-X0000033',60800.00,'venta'),(61,61,'2026-06-05 19:30:13','venta_fiada','pendiente',51832.91,39,3,'Comprobante 0006-X0000034','0006-X0000034',51832.91,'venta'),(62,50,'2026-06-05 19:37:41','venta_fiada','pendiente',53203.52,40,3,'Comprobante 0006-X0000035','0006-X0000035',53203.52,'venta'),(63,50,'2026-06-05 19:40:31','venta_fiada','pendiente',43968.96,41,3,'Comprobante 0006-X0000036','0006-X0000036',43968.96,'venta'),(64,82,'2026-06-05 19:52:12','venta_fiada','pendiente',31256.00,42,3,'Comprobante 0006-X0000037','0006-X0000037',31256.00,'venta'),(65,59,'2026-06-06 13:44:30','venta_fiada','pendiente',152710.04,43,3,'Comprobante 0006-X0000038','0006-X0000038',152710.04,'venta'),(66,69,'2026-06-07 19:56:36','pago','pagado',45914.00,NULL,3,'Recibo de cobro R00000008','R00000008',0.00,'pago'),(67,64,'2026-06-07 19:57:47','pago','pagado',52014.00,NULL,3,'Recibo de cobro R00000009','R00000009',0.00,'pago'),(68,60,'2026-06-07 19:58:29','pago','pagado',57348.00,NULL,3,'Recibo de cobro R00000010','R00000010',0.00,'pago'),(69,68,'2026-06-07 20:11:12','pago','pagado',122000.00,NULL,3,'Recibo de cobro R00000011','R00000011',0.00,'pago'),(70,55,'2026-06-07 20:12:33','pago','pagado',106143.00,NULL,3,'Recibo de cobro R00000012','R00000012',0.00,'pago'),(71,49,'2026-06-07 20:13:05','pago','pagado',45142.00,NULL,3,'Recibo de cobro R00000013','R00000013',0.00,'pago'),(72,38,'2026-06-07 20:13:37','pago','pagado',39571.46,NULL,3,'Recibo de cobro R00000014','R00000014',0.00,'pago'),(73,17,'2026-06-07 20:18:45','pago','pagado',8152.00,NULL,3,'Recibo de cobro R00000015','R00000015',0.00,'pago'),(74,59,'2026-06-07 20:19:20','pago','pagado',60000.00,NULL,3,'Recibo de cobro R00000016','R00000016',0.00,'pago'),(75,72,'2026-06-07 20:21:29','pago','pagado',36511.70,NULL,3,'Recibo de cobro R00000017','R00000017',0.00,'pago'),(76,39,'2026-06-07 20:22:50','pago','pagado',32095.80,NULL,3,'Recibo de cobro R00000018','R00000018',0.00,'pago'),(77,66,'2026-06-07 20:24:55','pago','pagado',64186.00,NULL,3,'Recibo de cobro R00000019','R00000019',0.00,'pago'),(78,36,'2026-06-07 20:35:51','pago','pagado',44450.00,NULL,3,'Recibo de cobro R00000020','R00000020',0.00,'pago'),(79,19,'2026-06-07 20:36:34','pago','pagado',26761.00,NULL,3,'Recibo de cobro R00000021','R00000021',0.00,'pago'),(80,71,'2026-06-07 20:37:30','pago','pagado',50000.00,NULL,3,'Recibo de cobro R00000022','R00000022',0.00,'pago'),(81,17,'2026-06-07 20:38:12','pago','pagado',28000.00,NULL,3,'Recibo de cobro R00000023','R00000023',0.00,'pago'),(82,63,'2026-06-08 07:34:46','venta_fiada','pendiente',14194.28,44,3,'Comprobante 0006-X0000039','0006-X0000039',14194.28,'venta'),(83,50,'2026-06-08 11:03:36','pago','pagado',15000.00,NULL,3,'Recibo de cobro R00000024','R00000024',0.00,'pago');
/*!40000 ALTER TABLE `cta_cte_movimiento` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `descuentos_factura`
--

DROP TABLE IF EXISTS `descuentos_factura`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `descuentos_factura` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `factura_id` int(11) NOT NULL,
  `porcentaje_descuento` decimal(5,2) NOT NULL,
  `monto_descuento` decimal(10,2) NOT NULL,
  `total_original` decimal(10,2) NOT NULL,
  `fecha_aplicacion` datetime DEFAULT NULL,
  `usuario_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `factura_id` (`factura_id`),
  KEY `usuario_id` (`usuario_id`),
  CONSTRAINT `descuentos_factura_ibfk_1` FOREIGN KEY (`factura_id`) REFERENCES `factura` (`id`),
  CONSTRAINT `descuentos_factura_ibfk_2` FOREIGN KEY (`usuario_id`) REFERENCES `usuario` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `descuentos_factura`
--

LOCK TABLES `descuentos_factura` WRITE;
/*!40000 ALTER TABLE `descuentos_factura` DISABLE KEYS */;
INSERT INTO `descuentos_factura` VALUES (1,6,7.00,20882.96,298328.00,'2026-05-29 17:56:29',3);
/*!40000 ALTER TABLE `descuentos_factura` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `detalle_factura`
--

DROP TABLE IF EXISTS `detalle_factura`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `detalle_factura` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `factura_id` int(11) NOT NULL,
  `producto_id` int(11) NOT NULL,
  `cantidad` decimal(10,3) NOT NULL,
  `precio_unitario` decimal(10,2) NOT NULL,
  `subtotal` decimal(10,2) NOT NULL,
  `porcentaje_iva` decimal(5,2) DEFAULT 21.00,
  `importe_iva` decimal(10,2) DEFAULT 0.00,
  `costo_unitario` decimal(10,2) DEFAULT 0.00,
  PRIMARY KEY (`id`),
  KEY `idx_factura` (`factura_id`),
  KEY `idx_producto` (`producto_id`),
  CONSTRAINT `detalle_factura_ibfk_1` FOREIGN KEY (`factura_id`) REFERENCES `factura` (`id`) ON DELETE CASCADE,
  CONSTRAINT `detalle_factura_ibfk_2` FOREIGN KEY (`producto_id`) REFERENCES `producto` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=417 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `detalle_factura`
--

LOCK TABLES `detalle_factura` WRITE;
/*!40000 ALTER TABLE `detalle_factura` DISABLE KEYS */;
INSERT INTO `detalle_factura` VALUES (1,1,10,1.000,82.64,82.64,21.00,17.36,4091.02),(2,2,10,1.000,82.64,82.64,21.00,17.36,4091.02),(3,3,10,1.000,82.64,82.64,21.00,17.36,4091.02),(4,4,10,1.000,82.64,82.64,21.00,17.36,4091.02),(5,5,10,1.000,4033.21,4033.21,21.00,846.97,4091.02),(6,6,61,1.000,8909.09,8909.09,21.00,1870.91,8983.33),(7,6,64,2.000,5322.31,10644.63,21.00,2235.37,5366.67),(8,6,65,2.000,6942.15,13884.30,21.00,2915.70,7000.00),(9,6,66,2.000,5454.55,10909.09,21.00,2290.91,5500.00),(10,6,79,2.000,3388.43,6776.86,21.00,1423.14,3416.67),(11,6,100,40.000,676.03,27041.32,21.00,5678.68,681.67),(12,6,105,24.000,549.59,13190.08,21.00,2769.92,552.50),(13,6,109,48.000,379.34,18208.26,21.00,3823.74,382.50),(14,6,110,48.000,379.34,18208.26,21.00,3823.74,382.50),(15,6,113,48.000,676.86,32489.26,21.00,6822.74,682.50),(16,6,114,48.000,676.86,32489.26,21.00,6822.74,682.50),(17,6,127,24.000,566.12,13586.78,21.00,2853.22,570.83),(18,6,128,24.000,566.12,13586.78,21.00,2853.22,570.83),(19,6,155,10.000,887.60,8876.03,21.00,1863.97,895.00),(20,6,156,10.000,887.60,8876.03,21.00,1863.97,895.00),(21,6,157,10.000,887.60,8876.03,21.00,1863.97,895.00),(22,7,190,1.000,9740.99,9740.99,21.00,2045.61,8419.00),(23,7,27,1.000,7200.56,7200.56,21.00,1512.12,7417.57),(24,7,30,1.000,4231.30,4231.30,21.00,888.57,4370.73),(25,7,34,1.000,2842.98,2842.98,21.00,597.02,2741.74),(26,7,38,1.000,4996.05,4996.05,21.00,1049.17,5198.40),(27,7,43,1.000,5619.83,5619.83,21.00,1180.17,5874.73),(28,7,47,1.000,5619.83,5619.83,21.00,1180.17,5896.56),(29,7,53,1.000,4049.59,4049.59,21.00,850.41,4083.33),(30,7,55,1.000,4049.59,4049.59,21.00,850.41,4083.33),(31,7,63,1.000,5454.55,5454.55,21.00,1145.45,5408.33),(32,7,65,1.000,7107.44,7107.44,21.00,1492.56,7000.00),(33,7,96,1.000,14016.53,14016.53,21.00,2943.47,14133.33),(34,7,99,1.000,7107.44,7107.44,21.00,1492.56,7058.33),(35,7,150,2.000,1727.27,3454.55,21.00,725.45,1741.67),(36,7,151,3.000,1727.27,5181.82,21.00,1088.18,1741.67),(37,7,152,3.000,1727.27,5181.82,21.00,1088.18,1741.67),(38,7,154,3.000,1727.27,5181.82,21.00,1088.18,1741.67),(39,7,170,3.000,1176.03,3528.10,21.00,740.90,1185.83),(40,7,40,1.000,5619.83,5619.83,21.00,1180.17,5858.46),(41,8,39,2.000,4995.87,9991.74,21.00,2098.26,5203.20),(42,8,30,1.000,4231.30,4231.30,21.00,888.57,4370.73),(43,8,52,3.000,2644.63,7933.88,21.00,1666.12,2500.00),(44,8,60,1.000,8181.82,8181.82,21.00,1718.18,8250.00),(45,8,71,2.000,1768.60,3537.19,21.00,742.81,1783.33),(46,8,100,3.000,676.03,2028.10,21.00,425.90,681.67),(47,8,111,10.000,238.02,2380.17,21.00,499.83,240.00),(48,8,112,10.000,238.02,2380.17,21.00,499.83,240.00),(49,8,120,8.000,811.57,6492.56,21.00,1363.44,779.17),(50,8,131,1.000,6000.00,6000.00,21.00,1260.00,6000.00),(51,8,170,3.000,1176.03,3528.10,21.00,740.90,1185.83),(52,8,171,3.000,1176.03,3528.10,21.00,740.90,1185.83),(53,8,175,2.000,1176.03,2352.07,21.00,493.93,1185.83),(54,8,177,2.000,1176.03,2352.07,21.00,493.93,1185.83),(55,9,166,10.000,2214.88,22148.76,21.00,4651.24,2108.33),(56,9,114,12.000,676.86,8122.31,21.00,1705.69,682.50),(57,9,129,43.000,163.64,7036.36,21.00,1477.64,165.00),(58,10,35,1.000,2644.69,2644.69,21.00,555.39,2744.26),(59,10,63,1.000,5363.64,5363.64,21.00,1126.36,5408.33),(60,10,64,1.000,5322.31,5322.31,21.00,1117.69,5366.67),(61,10,88,1.000,3471.07,3471.07,21.00,728.93,3500.00),(62,10,128,12.000,566.12,6793.39,21.00,1426.61,570.83),(63,10,148,18.000,432.23,7780.17,21.00,1633.83,435.83),(64,11,131,1.000,5950.41,5950.41,21.00,1249.59,6000.00),(65,11,94,16.000,641.32,10261.16,21.00,2154.84,646.67),(66,11,52,1.000,2644.63,2644.63,21.00,555.37,2500.00),(67,11,56,1.000,5454.55,5454.55,21.00,1145.45,5500.00),(68,11,109,6.000,379.34,2276.03,21.00,477.97,382.50),(69,11,110,3.000,379.34,1138.02,21.00,238.98,382.50),(70,11,113,6.000,676.86,4061.16,21.00,852.84,682.50),(71,11,114,3.000,676.86,2030.58,21.00,426.42,682.50),(72,11,127,4.000,566.12,2264.46,21.00,475.54,570.83),(73,11,128,4.000,566.12,2264.46,21.00,475.54,570.83),(74,11,126,4.000,1380.17,5520.66,21.00,1159.34,1391.67),(75,11,120,4.000,772.73,3090.91,21.00,649.09,779.17),(76,12,130,4.000,6033.06,24132.23,21.00,5067.77,6083.33),(77,12,145,36.000,432.23,15560.33,21.00,3267.67,435.83),(78,12,146,36.000,432.23,15560.33,21.00,3267.67,435.83),(79,12,147,18.000,432.23,7780.17,21.00,1633.83,435.83),(80,12,148,36.000,432.23,15560.33,21.00,3267.67,435.83),(81,12,204,40.000,697.57,27902.81,21.00,5859.59,766.91),(82,12,203,10.000,697.56,6975.62,21.00,1464.88,766.90),(83,12,202,10.000,697.57,6975.70,21.00,1464.90,766.91),(84,13,13,1.000,4110.48,4110.48,21.00,863.20,3829.15),(85,13,34,1.000,2644.53,2644.53,21.00,555.35,2741.74),(86,13,52,1.000,2641.50,2641.50,21.00,554.71,2461.46),(87,13,54,1.000,4049.59,4049.59,21.00,850.41,4083.33),(88,13,135,2.000,3884.30,7768.60,21.00,1631.40,3916.67),(89,13,138,1.000,3646.35,3646.35,21.00,765.73,3676.73),(90,13,38,1.000,4501.35,4501.35,21.00,945.28,4683.66),(91,13,43,2.000,5619.83,11239.67,21.00,2360.33,5874.73),(92,13,21,1.000,4305.89,4305.89,21.00,904.24,4411.25),(93,13,190,1.000,9740.99,9740.99,21.00,2045.61,8419.00),(94,13,65,1.000,6942.15,6942.15,21.00,1457.85,7000.00),(95,13,27,1.000,7347.93,7347.93,21.00,1543.07,6839.76),(96,13,28,1.000,7201.01,7201.01,21.00,1512.21,7424.35),(97,14,130,1.000,6033.06,6033.06,21.00,1266.94,6083.33),(98,14,155,10.000,1017.55,10175.45,21.00,2136.85,947.10),(99,14,156,10.000,1017.55,10175.45,21.00,2136.85,947.10),(100,14,157,10.000,1017.55,10175.45,21.00,2136.85,947.10),(101,14,197,14.000,1056.19,14786.66,21.00,3105.20,907.15),(102,14,188,1.000,5289.26,5289.26,21.00,1110.74,5333.33),(103,15,13,1.000,4110.48,4110.48,21.00,863.20,3829.15),(104,15,14,1.000,4033.16,4033.16,21.00,846.96,4105.77),(105,15,37,1.000,3173.47,3173.47,21.00,666.43,3299.17),(106,15,117,4.000,983.47,3933.88,21.00,826.12,991.67),(107,15,118,4.000,983.47,3933.88,21.00,826.12,991.67),(108,15,119,4.000,983.47,3933.88,21.00,826.12,991.67),(109,15,175,3.000,1176.03,3528.10,21.00,740.90,1185.83),(110,15,176,3.000,1176.03,3528.10,21.00,740.90,1185.83),(111,16,21,1.000,4305.89,4305.89,21.00,904.24,4411.25),(112,16,24,1.000,4305.94,4305.94,21.00,904.25,4423.29),(113,16,25,1.000,4305.83,4305.83,21.00,904.23,4427.31),(114,16,132,1.000,3646.35,3646.35,21.00,765.73,3676.73),(115,16,184,1.000,2644.63,2644.63,21.00,555.37,2666.67),(116,17,13,1.000,4110.48,4110.48,21.00,863.20,3829.15),(117,17,14,1.000,4033.16,4033.16,21.00,846.96,4105.77),(118,17,37,1.000,3173.47,3173.47,21.00,666.43,3299.17),(119,17,117,4.000,983.47,3933.88,21.00,826.12,991.67),(120,17,118,4.000,983.47,3933.88,21.00,826.12,991.67),(121,17,119,4.000,983.47,3933.88,21.00,826.12,991.67),(122,17,175,3.000,1176.03,3528.10,21.00,740.90,1185.83),(123,17,176,3.000,1176.03,3528.10,21.00,740.90,1185.83),(124,18,17,2.000,4110.80,8221.60,21.00,1726.54,3829.15),(125,18,18,2.000,4110.17,8220.33,21.00,1726.27,3829.15),(126,18,27,1.000,7347.93,7347.93,21.00,1543.07,6839.76),(127,18,38,1.000,4501.35,4501.35,21.00,945.28,4683.66),(128,18,98,1.000,2975.21,2975.21,21.00,624.79,3000.00),(129,18,100,10.000,608.88,6088.84,21.00,1278.66,613.96),(130,18,102,6.000,247.11,1482.64,21.00,311.36,249.17),(131,18,113,8.000,687.31,5498.51,21.00,1154.69,639.73),(132,18,114,4.000,676.86,2707.44,21.00,568.56,682.50),(133,18,122,6.000,953.98,5723.90,21.00,1202.02,961.93),(134,18,148,6.000,438.03,2628.20,21.00,551.92,407.83),(135,18,155,4.000,1017.55,4070.18,21.00,854.74,947.10),(136,18,162,4.000,988.17,3952.66,21.00,830.06,919.26),(137,18,163,5.000,988.17,4940.83,21.00,1037.57,919.26),(138,18,197,3.000,1056.19,3168.57,21.00,665.40,907.15),(139,18,170,2.000,1176.03,2352.07,21.00,493.93,1185.83),(140,19,16,1.000,4032.96,4032.96,21.00,846.92,4113.18),(141,19,27,1.000,7347.93,7347.93,21.00,1543.07,6839.76),(142,19,38,1.000,4501.35,4501.35,21.00,945.28,4683.66),(143,19,39,1.000,4497.09,4497.09,21.00,944.39,4683.66),(144,19,42,1.000,5619.83,5619.83,21.00,1180.17,5869.30),(145,19,43,1.000,5619.83,5619.83,21.00,1180.17,5874.73),(146,19,94,6.000,653.93,3923.55,21.00,823.95,608.65),(147,19,95,6.000,653.93,3923.55,21.00,823.95,608.65),(148,19,98,1.000,2975.21,2975.21,21.00,624.79,3000.00),(149,19,113,6.000,687.31,4123.88,21.00,866.02,639.73),(150,19,114,6.000,676.86,4061.16,21.00,852.84,682.50),(151,19,121,6.000,953.98,5723.90,21.00,1202.02,961.93),(152,19,123,6.000,953.98,5723.90,21.00,1202.02,961.93),(153,19,195,6.000,1112.98,6677.85,21.00,1402.35,961.93),(154,19,166,6.000,2090.91,12545.45,21.00,2634.55,2108.33),(155,20,12,1.000,4094.70,4094.70,21.00,859.89,3811.22),(156,20,13,1.000,4094.70,4094.70,21.00,859.89,3811.22),(157,20,15,1.000,4094.70,4094.70,21.00,859.89,3811.22),(158,20,16,1.000,4094.70,4094.70,21.00,859.89,3811.22),(159,20,17,2.000,4094.70,8189.40,21.00,1719.78,3811.22),(160,20,27,1.000,7314.16,7314.16,21.00,1535.97,6807.79),(161,20,28,1.000,7314.16,7314.16,21.00,1535.97,6807.79),(162,20,29,1.000,7314.16,7314.16,21.00,1535.97,6807.79),(163,20,32,1.000,2644.66,2644.66,21.00,555.38,2736.71),(164,20,33,1.000,2644.60,2644.60,21.00,555.36,2739.22),(165,20,34,1.000,2644.53,2644.53,21.00,555.35,2741.74),(166,20,35,1.000,2644.69,2644.69,21.00,555.39,2744.26),(167,20,109,12.000,379.34,4552.07,21.00,955.93,382.50),(168,20,110,12.000,379.34,4552.07,21.00,955.93,382.50),(169,20,111,12.000,238.02,2856.20,21.00,599.80,240.00),(170,20,112,12.000,238.02,2856.20,21.00,599.80,240.00),(171,20,113,12.000,687.31,8247.77,21.00,1732.03,639.73),(172,20,114,12.000,687.31,8247.77,21.00,1732.03,639.73),(173,20,162,10.000,988.17,9881.65,21.00,2075.15,919.26),(174,21,7,1.000,10123.83,10123.83,21.00,2126.01,9449.85),(175,21,60,1.000,8181.82,8181.82,21.00,1718.18,8250.00),(176,21,113,12.000,687.31,8247.77,21.00,1732.03,639.73),(177,21,114,12.000,687.31,8247.77,21.00,1732.03,639.73),(178,21,195,5.000,1112.98,5564.88,21.00,1168.62,961.93),(179,21,158,8.000,938.02,7504.13,21.00,1575.87,945.83),(180,21,159,5.000,1026.45,5132.23,21.00,1077.77,1035.00),(181,21,160,5.000,1026.45,5132.23,21.00,1077.77,1035.00),(182,21,161,5.000,1026.45,5132.23,21.00,1077.77,1035.00),(183,21,166,6.000,2090.91,12545.45,21.00,2634.55,2108.33),(184,21,167,6.000,1950.41,11702.48,21.00,2457.52,1966.67),(185,21,170,2.000,1176.03,2352.07,21.00,493.93,1185.83),(186,21,171,2.000,1176.03,2352.07,21.00,493.93,1185.83),(187,21,172,2.000,1176.03,2352.07,21.00,493.93,1185.83),(188,21,181,1.000,6033.06,6033.06,21.00,1266.94,6083.33),(189,22,30,3.000,4231.30,12693.89,21.00,2665.72,4370.73),(190,22,48,1.000,4628.10,4628.10,21.00,971.90,4860.51),(191,22,199,2.000,2644.63,5289.26,21.00,1110.74,2500.00),(192,22,68,3.000,4297.52,12892.56,21.00,2707.44,4333.33),(193,22,72,1.000,3553.72,3553.72,21.00,746.28,3583.33),(194,22,74,1.000,3553.72,3553.72,21.00,746.28,3583.33),(195,22,75,1.000,3553.72,3553.72,21.00,746.28,3583.33),(196,22,76,1.000,3553.72,3553.72,21.00,746.28,3583.33),(197,22,80,2.000,3388.43,6776.86,21.00,1423.14,3416.67),(198,22,81,3.000,3388.43,10165.29,21.00,2134.71,3416.67),(199,22,82,3.000,3388.43,10165.29,21.00,2134.71,3416.67),(200,22,94,30.000,653.93,19617.77,21.00,4119.73,608.65),(201,22,95,30.000,653.93,19617.77,21.00,4119.73,608.65),(202,22,96,1.000,14016.53,14016.53,21.00,2943.47,14133.33),(203,22,98,1.000,2975.21,2975.21,21.00,624.79,3000.00),(204,22,99,1.000,7000.00,7000.00,21.00,1470.00,7058.33),(205,22,102,48.000,247.11,11861.16,21.00,2490.84,249.17),(206,22,103,1.000,5363.64,5363.64,21.00,1126.36,5408.33),(207,22,109,24.000,379.34,9104.13,21.00,1911.87,382.50),(208,22,111,20.000,238.02,4760.33,21.00,999.67,240.00),(209,22,112,20.000,238.02,4760.33,21.00,999.67,240.00),(210,22,113,12.000,687.31,8247.77,21.00,1732.03,639.73),(211,22,114,12.000,687.31,8247.77,21.00,1732.03,639.73),(212,22,127,24.000,572.98,13751.60,21.00,2887.84,537.20),(213,23,190,1.000,9740.99,9740.99,21.00,2045.61,8419.00),(214,23,109,24.000,379.34,9104.13,21.00,1911.87,382.50),(215,23,113,12.000,687.31,8247.77,21.00,1732.03,639.73),(216,23,115,4.000,917.36,3669.42,21.00,770.58,925.00),(217,23,116,4.000,917.36,3669.42,21.00,770.58,925.00),(218,23,117,4.000,983.47,3933.88,21.00,826.12,991.67),(219,23,118,4.000,983.47,3933.88,21.00,826.12,991.67),(220,23,122,4.000,953.98,3815.93,21.00,801.35,961.93),(221,23,123,4.000,953.98,3815.93,21.00,801.35,961.93),(222,23,188,1.000,5289.26,5289.26,21.00,1110.74,5333.33),(223,23,189,1.000,10413.22,10413.22,21.00,2186.78,10500.00),(224,24,166,3.000,2090.91,6272.73,21.00,1317.27,2108.33),(225,24,167,3.000,1950.41,5851.24,21.00,1228.76,1966.67),(226,24,170,2.000,1176.03,2352.07,21.00,493.93,1185.83),(227,24,172,2.000,1176.03,2352.07,21.00,493.93,1185.83),(228,25,2,1.000,2495.87,2495.87,21.00,524.13,2516.67),(229,25,3,1.000,2363.64,2363.64,21.00,496.36,2383.33),(230,25,7,1.000,10123.83,10123.83,21.00,2126.01,9449.85),(231,25,27,2.000,7314.16,14628.31,21.00,3071.95,6807.79),(232,25,56,1.000,5454.55,5454.55,21.00,1145.45,5500.00),(233,25,67,1.000,3578.51,3578.51,21.00,751.49,3608.33),(234,25,104,1.000,9911.67,9911.67,21.00,2081.45,9994.27),(235,25,122,6.000,953.98,5723.90,21.00,1202.02,961.93),(236,25,162,6.000,988.17,5928.99,21.00,1245.09,919.26),(237,25,163,6.000,988.17,5928.99,21.00,1245.09,919.26),(238,25,164,6.000,988.17,5928.99,21.00,1245.09,919.26),(239,26,109,12.000,379.34,4552.07,21.00,955.93,382.50),(240,26,110,12.000,379.34,4552.07,21.00,955.93,382.50),(241,26,114,12.000,687.31,8247.77,21.00,1732.03,639.73),(242,26,115,5.000,917.36,4586.78,21.00,963.22,925.00),(243,26,116,5.000,917.36,4586.78,21.00,963.22,925.00),(244,27,61,1.000,8909.09,8909.09,21.00,1870.91,8983.33),(245,27,156,6.000,1017.55,6105.27,21.00,1282.11,947.10),(246,27,163,6.000,988.17,5928.99,21.00,1245.09,919.26),(247,27,170,2.000,1176.03,2352.07,21.00,493.93,1185.83),(248,27,172,2.000,1176.03,2352.07,21.00,493.93,1185.83),(249,27,174,2.000,1176.03,2352.07,21.00,493.93,1185.83),(250,27,175,2.000,1176.03,2352.07,21.00,493.93,1185.83),(251,27,176,2.000,1176.03,2352.07,21.00,493.93,1185.83),(252,28,29,1.000,7314.16,7314.16,21.00,1535.97,6807.79),(253,28,87,1.000,4496.20,4496.20,21.00,944.20,4533.67),(254,28,121,3.000,953.98,2861.95,21.00,601.01,961.93),(255,28,131,1.000,6198.58,6198.58,21.00,1301.70,5769.45),(256,28,148,9.000,438.03,3942.30,21.00,827.88,407.83),(257,28,145,9.000,438.03,3942.30,21.00,827.88,407.83),(258,28,155,3.000,1017.55,3052.64,21.00,641.05,947.10),(259,28,156,3.000,1017.55,3052.64,21.00,641.05,947.10),(260,28,157,1.000,1017.55,1017.55,21.00,213.68,947.10),(261,28,162,3.000,988.17,2964.50,21.00,622.54,919.26),(262,29,173,2.000,1176.03,2352.07,21.00,493.93,1185.83),(263,29,174,2.000,1176.03,2352.07,21.00,493.93,1185.83),(264,29,175,4.000,1176.03,4704.13,21.00,987.87,1185.83),(265,30,113,12.000,687.31,8247.77,21.00,1732.03,639.73),(266,31,6,1.000,9415.84,9415.84,21.00,1977.33,9494.31),(267,31,7,1.000,10123.83,10123.83,21.00,2126.01,9449.85),(268,31,190,1.000,9740.99,9740.99,21.00,2045.61,8419.00),(269,31,52,1.000,2641.50,2641.50,21.00,554.71,2461.46),(270,31,199,1.000,2644.63,2644.63,21.00,555.37,2500.00),(271,31,200,1.000,2644.63,2644.63,21.00,555.37,2500.00),(272,31,109,12.000,379.34,4552.07,21.00,955.93,382.50),(273,31,110,12.000,379.34,4552.07,21.00,955.93,382.50),(274,32,84,1.000,4496.20,4496.20,21.00,944.20,4533.67),(275,32,87,1.000,4496.20,4496.20,21.00,944.20,4533.67),(276,32,115,9.000,917.36,8256.20,21.00,1733.80,925.00),(277,33,115,6.000,917.36,5504.13,21.00,1155.87,925.00),(278,33,116,6.000,917.36,5504.13,21.00,1155.87,925.00),(279,33,117,6.000,983.47,5900.83,21.00,1239.17,991.67),(280,33,118,6.000,983.47,5900.83,21.00,1239.17,991.67),(281,33,161,6.000,1026.45,6158.68,21.00,1293.32,1035.00),(282,34,94,10.000,653.93,6539.26,21.00,1373.24,608.65),(283,34,95,10.000,653.93,6539.26,21.00,1373.24,608.65),(284,34,136,1.000,3646.35,3646.35,21.00,765.73,3676.73),(285,34,156,30.000,1017.55,30526.36,21.00,6410.54,947.10),(286,34,162,24.000,988.17,23715.97,21.00,4980.35,919.26),(287,34,198,16.000,1286.78,20588.43,21.00,4323.57,1112.14),(288,35,16,2.000,4429.75,8859.50,21.00,1860.50,3811.22),(289,35,113,10.000,687.31,6873.14,21.00,1443.36,639.73),(290,35,114,10.000,687.31,6873.14,21.00,1443.36,639.73),(291,35,122,5.000,1097.52,5487.60,21.00,1152.40,961.93),(292,35,123,5.000,1097.52,5487.60,21.00,1152.40,961.93),(293,36,17,2.000,4094.70,8189.40,21.00,1719.78,3811.22),(294,36,18,1.000,4094.70,4094.70,21.00,859.89,3811.22),(295,36,33,2.000,2842.98,5685.95,21.00,1194.05,2739.22),(296,36,35,2.000,2842.98,5685.95,21.00,1194.05,2744.26),(297,36,66,1.000,5454.55,5454.55,21.00,1145.45,5500.00),(298,36,69,2.000,4297.52,8595.04,21.00,1804.96,4333.33),(299,36,72,2.000,3801.65,7603.31,21.00,1596.69,3583.33),(300,36,76,2.000,3801.65,7603.31,21.00,1596.69,3583.33),(301,36,80,2.000,3388.43,6776.86,21.00,1423.14,3416.67),(302,36,81,2.000,3388.43,6776.86,21.00,1423.14,3416.67),(303,36,82,2.000,3388.43,6776.86,21.00,1423.14,3416.67),(304,36,89,20.000,309.09,6181.82,21.00,1298.18,311.67),(305,36,90,20.000,309.09,6181.82,21.00,1298.18,311.67),(306,36,92,6.000,1537.19,9223.14,21.00,1936.86,1550.00),(307,36,93,6.000,1537.19,9223.14,21.00,1936.86,1550.00),(308,36,94,20.000,653.93,13078.51,21.00,2746.49,608.65),(309,36,95,15.000,653.93,9808.88,21.00,2059.87,608.65),(310,36,96,2.000,14016.53,28033.06,21.00,5886.94,14133.33),(311,36,97,6.000,1223.14,7338.84,21.00,1541.16,1029.17),(312,36,99,2.000,7107.44,14214.88,21.00,2985.12,7058.33),(313,36,100,15.000,700.83,10512.40,21.00,2207.60,613.96),(314,36,109,15.000,700.83,10512.40,21.00,2207.60,382.50),(315,36,106,6.000,596.69,3580.17,21.00,751.83,600.83),(316,36,148,15.000,438.03,6570.50,21.00,1379.80,407.83),(317,36,180,6.000,527.27,3163.64,21.00,664.36,531.67),(318,36,34,2.000,2842.98,5685.95,21.00,1194.05,2741.74),(319,36,73,2.000,3801.65,7603.31,21.00,1596.69,3583.33),(320,36,74,2.000,3801.65,7603.31,21.00,1596.69,3583.33),(321,37,17,2.000,4094.70,8189.40,21.00,1719.78,3811.22),(322,37,18,1.000,4094.70,4094.70,21.00,859.89,3811.22),(323,37,33,2.000,2644.60,5289.19,21.00,1110.73,2739.22),(324,37,35,2.000,2644.69,5289.39,21.00,1110.77,2744.26),(325,37,66,1.000,5454.55,5454.55,21.00,1145.45,5500.00),(326,37,69,2.000,4297.52,8595.04,21.00,1804.96,4333.33),(327,37,72,2.000,3553.72,7107.44,21.00,1492.56,3583.33),(328,37,76,2.000,3553.72,7107.44,21.00,1492.56,3583.33),(329,37,80,2.000,3388.43,6776.86,21.00,1423.14,3416.67),(330,37,81,2.000,3388.43,6776.86,21.00,1423.14,3416.67),(331,37,82,2.000,3388.43,6776.86,21.00,1423.14,3416.67),(332,37,89,20.000,309.09,6181.82,21.00,1298.18,311.67),(333,37,90,20.000,309.09,6181.82,21.00,1298.18,311.67),(334,37,92,6.000,1537.19,9223.14,21.00,1936.86,1550.00),(335,37,93,6.000,1537.19,9223.14,21.00,1936.86,1550.00),(336,37,94,20.000,653.93,13078.51,21.00,2746.49,608.65),(337,37,95,15.000,653.93,9808.88,21.00,2059.87,608.65),(338,37,96,2.000,14016.53,28033.06,21.00,5886.94,14133.33),(339,37,97,6.000,1020.66,6123.97,21.00,1286.03,1029.17),(340,37,99,2.000,7000.00,14000.00,21.00,2940.00,7058.33),(341,37,100,15.000,608.88,9133.26,21.00,1917.99,613.96),(342,37,109,15.000,379.34,5690.08,21.00,1194.92,382.50),(343,37,106,6.000,595.87,3575.21,21.00,750.79,600.83),(344,37,148,15.000,438.03,6570.50,21.00,1379.80,407.83),(345,37,34,2.000,2644.53,5289.06,21.00,1110.70,2741.74),(346,37,73,2.000,3553.72,7107.44,21.00,1492.56,3583.33),(347,37,74,2.000,3553.72,7107.44,21.00,1492.56,3583.33),(348,38,172,10.000,1256.20,12561.98,21.00,2638.02,1013.33),(349,38,173,10.000,1256.20,12561.98,21.00,2638.02,1013.33),(350,38,174,10.000,1256.20,12561.98,21.00,2638.02,1013.33),(351,38,175,5.000,1256.20,6280.99,21.00,1319.01,1013.33),(352,38,176,5.000,1256.20,6280.99,21.00,1319.01,1013.33),(353,39,4,1.000,2363.64,2363.64,21.00,496.36,2383.33),(354,39,92,1.000,1537.19,1537.19,21.00,322.81,1550.00),(355,39,93,1.000,1537.19,1537.19,21.00,322.81,1550.00),(356,39,94,4.000,653.93,2615.70,21.00,549.30,608.65),(357,39,95,4.000,653.93,2615.70,21.00,549.30,608.65),(358,39,109,4.000,379.34,1517.36,21.00,318.64,382.50),(359,39,110,4.000,379.34,1517.36,21.00,318.64,382.50),(360,39,111,6.000,238.02,1428.10,21.00,299.90,240.00),(361,39,112,6.000,238.02,1428.10,21.00,299.90,240.00),(362,39,113,3.000,687.31,2061.94,21.00,433.01,639.73),(363,39,114,3.000,687.31,2061.94,21.00,433.01,639.73),(364,39,115,2.000,917.36,1834.71,21.00,385.29,925.00),(365,39,121,2.000,953.98,1907.97,21.00,400.67,961.93),(366,39,122,2.000,953.98,1907.97,21.00,400.67,961.93),(367,39,123,2.000,953.98,1907.97,21.00,400.67,961.93),(368,39,125,2.000,1121.49,2242.98,21.00,471.02,1130.83),(369,39,127,4.000,572.98,2291.93,21.00,481.31,537.20),(370,39,128,4.000,534.04,2136.17,21.00,448.59,500.73),(371,39,194,2.000,1112.98,2225.95,21.00,467.45,961.93),(372,39,155,3.000,1017.55,3052.64,21.00,641.05,947.10),(373,39,184,1.000,2644.63,2644.63,21.00,555.37,2666.67),(374,40,10,1.000,4094.70,4094.70,21.00,859.89,3811.22),(375,40,14,1.000,4094.70,4094.70,21.00,859.89,3811.22),(376,40,16,1.000,4094.70,4094.70,21.00,859.89,3811.22),(377,40,27,1.000,7314.16,7314.16,21.00,1535.97,6807.79),(378,40,56,1.000,5454.55,5454.55,21.00,1145.45,5500.00),(379,40,100,6.000,608.88,3653.31,21.00,767.19,613.96),(380,40,121,4.000,953.98,3815.93,21.00,801.35,961.93),(381,40,122,12.000,953.98,11447.80,21.00,2404.04,961.93),(382,41,10,1.000,4094.70,4094.70,21.00,859.89,3811.22),(383,41,14,1.000,4094.70,4094.70,21.00,859.89,3811.22),(384,41,16,1.000,4094.70,4094.70,21.00,859.89,3811.22),(385,41,27,1.000,7314.16,7314.16,21.00,1535.97,6807.79),(386,41,56,1.000,5454.55,5454.55,21.00,1145.45,5500.00),(387,41,100,6.000,608.88,3653.31,21.00,767.19,613.96),(388,41,121,4.000,953.98,3815.93,21.00,801.35,961.93),(389,41,122,4.000,953.98,3815.93,21.00,801.35,961.93),(390,42,159,6.000,1026.45,6158.68,21.00,1293.32,1035.00),(391,42,160,12.000,1026.45,12317.36,21.00,2586.64,1035.00),(392,42,179,1.000,7355.37,7355.37,21.00,1544.63,7416.67),(393,43,53,1.000,4049.59,4049.59,21.00,850.41,4083.33),(394,43,63,1.000,5363.64,5363.64,21.00,1126.36,5408.33),(395,43,94,10.000,653.93,6539.26,21.00,1373.24,608.65),(396,43,95,10.000,653.93,6539.26,21.00,1373.24,608.65),(397,43,109,10.000,379.34,3793.39,21.00,796.61,382.50),(398,43,110,10.000,379.34,3793.39,21.00,796.61,382.50),(399,43,111,10.000,238.02,2380.17,21.00,499.83,240.00),(400,43,113,12.000,687.31,8247.77,21.00,1732.03,639.73),(401,43,114,12.000,687.31,8247.77,21.00,1732.03,639.73),(402,43,131,1.000,6198.58,6198.58,21.00,1301.70,5769.45),(403,43,132,1.000,3646.35,3646.35,21.00,765.73,3676.73),(404,43,136,1.000,3646.35,3646.35,21.00,765.73,3676.73),(405,43,151,2.000,1727.27,3454.55,21.00,725.45,1741.67),(406,43,152,3.000,1727.27,5181.82,21.00,1088.18,1741.67),(407,43,153,3.000,1727.27,5181.82,21.00,1088.18,1741.67),(408,43,155,10.000,1017.55,10175.45,21.00,2136.85,947.10),(409,43,158,6.000,938.02,5628.10,21.00,1181.90,945.83),(410,43,160,6.000,1026.45,6158.68,21.00,1293.32,1035.00),(411,43,162,10.000,988.17,9881.65,21.00,2075.15,919.26),(412,43,197,10.000,1056.19,10561.90,21.00,2218.00,907.15),(413,43,172,4.000,1256.20,5024.79,21.00,1055.21,1013.33),(414,43,173,2.000,1256.20,2512.40,21.00,527.60,1013.33),(415,44,64,1.000,5322.31,5322.31,21.00,1117.69,5366.67),(416,44,128,12.000,534.04,6408.50,21.00,1345.78,500.73);
/*!40000 ALTER TABLE `detalle_factura` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `detalle_nota_credito`
--

DROP TABLE IF EXISTS `detalle_nota_credito`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `detalle_nota_credito` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `nota_credito_id` int(11) DEFAULT NULL,
  `producto_id` int(11) DEFAULT NULL,
  `cantidad` decimal(10,3) NOT NULL,
  `precio_unitario` decimal(10,2) NOT NULL,
  `subtotal` decimal(10,2) NOT NULL,
  `porcentaje_iva` decimal(5,2) NOT NULL,
  `importe_iva` decimal(10,2) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `nota_credito_id` (`nota_credito_id`),
  KEY `producto_id` (`producto_id`),
  CONSTRAINT `detalle_nota_credito_ibfk_1` FOREIGN KEY (`nota_credito_id`) REFERENCES `notas_credito` (`id`),
  CONSTRAINT `detalle_nota_credito_ibfk_2` FOREIGN KEY (`producto_id`) REFERENCES `producto` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `detalle_nota_credito`
--

LOCK TABLES `detalle_nota_credito` WRITE;
/*!40000 ALTER TABLE `detalle_nota_credito` DISABLE KEYS */;
/*!40000 ALTER TABLE `detalle_nota_credito` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `factura`
--

DROP TABLE IF EXISTS `factura`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `factura` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `numero` varchar(50) NOT NULL,
  `tipo_comprobante` varchar(10) DEFAULT '01',
  `punto_venta` int(11) NOT NULL,
  `fecha` datetime DEFAULT current_timestamp(),
  `cliente_id` int(11) NOT NULL,
  `usuario_id` int(11) NOT NULL,
  `subtotal` decimal(10,2) NOT NULL,
  `iva` decimal(10,2) NOT NULL,
  `total` decimal(10,2) NOT NULL,
  `estado` varchar(20) DEFAULT 'pendiente',
  `cae` varchar(50) DEFAULT NULL,
  `vto_cae` date DEFAULT NULL,
  `observaciones` text DEFAULT NULL,
  `fecha_anulacion` datetime DEFAULT NULL,
  `motivo_anulacion` text DEFAULT NULL,
  `interno_origen_id` int(11) DEFAULT NULL COMMENT 'Si esta factura proviene de un Comprobante Interno',
  PRIMARY KEY (`id`),
  UNIQUE KEY `numero` (`numero`),
  UNIQUE KEY `uk_interno_origen` (`interno_origen_id`),
  KEY `idx_numero` (`numero`),
  KEY `idx_fecha` (`fecha`),
  KEY `idx_cliente` (`cliente_id`),
  KEY `idx_estado` (`estado`),
  KEY `usuario_id` (`usuario_id`),
  KEY `idx_interno_origen` (`interno_origen_id`),
  CONSTRAINT `factura_ibfk_1` FOREIGN KEY (`cliente_id`) REFERENCES `cliente` (`id`),
  CONSTRAINT `factura_ibfk_2` FOREIGN KEY (`usuario_id`) REFERENCES `usuario` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=45 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `factura`
--

LOCK TABLES `factura` WRITE;
/*!40000 ALTER TABLE `factura` DISABLE KEYS */;
INSERT INTO `factura` VALUES (1,'0006-00000001','11',6,'2026-05-28 17:30:50',1,3,82.64,17.36,100.00,'autorizada','86227353286920','2026-06-07',NULL,NULL,NULL,NULL),(2,'0006-00000002','11',6,'2026-05-28 18:14:00',1,3,82.64,17.36,100.00,'autorizada','86227353224873','2026-06-07',NULL,NULL,NULL,NULL),(3,'0006-X0000001','99',6,'2026-05-28 18:33:05',1,3,82.64,17.36,100.00,'anulada',NULL,NULL,NULL,NULL,NULL,NULL),(4,'0006-00000003','11',6,'2026-05-28 18:34:53',1,3,82.64,17.36,100.00,'autorizada','86227353035941','2026-06-07',NULL,NULL,NULL,NULL),(5,'0006-X0000002','99',6,'2026-05-28 20:32:26',1,3,4033.21,846.97,4880.18,'interno',NULL,NULL,NULL,NULL,NULL,NULL),(6,'0006-00000004','11',6,'2026-05-29 17:56:24',46,3,246552.07,51775.93,277445.04,'autorizada','86227506810510','2026-06-08',NULL,NULL,NULL,NULL),(7,'0006-X0000003','99',6,'2026-05-30 14:28:55',47,3,110184.60,23138.77,133323.37,'interno',NULL,NULL,NULL,NULL,NULL,NULL),(8,'0006-X0000004','99',6,'2026-06-01 11:55:23',48,3,64917.25,13632.62,78549.87,'interno',NULL,NULL,NULL,NULL,NULL,NULL),(9,'0006-X0000005','99',6,'2026-06-01 12:00:09',49,3,37307.44,7834.56,45142.00,'anulada',NULL,NULL,NULL,NULL,NULL,NULL),(10,'0006-X0000006','99',6,'2026-06-01 14:10:04',63,3,31375.27,6588.81,37964.08,'interno',NULL,NULL,NULL,NULL,NULL,NULL),(11,'0006-X0000007','99',6,'2026-06-01 20:04:43',62,3,46957.02,9860.98,56818.00,'interno',NULL,NULL,NULL,NULL,NULL,NULL),(12,'0006-00000005','11',6,'2026-06-02 14:54:58',46,3,120447.52,25293.98,145741.50,'autorizada','86228061909817','2026-06-12',NULL,NULL,NULL,NULL),(13,'0006-X0000008','99',6,'2026-06-03 20:27:55',64,3,76140.02,15989.41,92129.43,'interno',NULL,NULL,NULL,NULL,NULL,NULL),(14,'0006-X0000009','99',6,'2026-06-04 08:30:07',60,3,56635.34,11893.42,68528.76,'interno',NULL,NULL,NULL,NULL,NULL,NULL),(15,'0006-X0000010','99',6,'2026-06-04 08:34:44',71,3,30174.96,6336.74,36511.70,'anulada',NULL,NULL,NULL,NULL,NULL,NULL),(16,'0006-X0000011','99',6,'2026-06-04 08:52:12',73,3,19208.64,4033.82,23242.46,'interno',NULL,NULL,NULL,NULL,NULL,NULL),(17,'0006-X0000012','99',6,'2026-06-04 08:57:08',72,3,30174.96,6336.74,36511.70,'interno',NULL,NULL,NULL,NULL,NULL,NULL),(18,'0006-X0000013','99',6,'2026-06-04 09:07:01',55,3,73880.26,15514.86,89395.12,'interno',NULL,NULL,NULL,NULL,NULL,NULL),(19,'0006-X0000014','99',6,'2026-06-04 09:11:20',65,3,81297.46,17072.47,98369.93,'interno',NULL,NULL,NULL,NULL,NULL,NULL),(20,'0006-X0000015','99',6,'2026-06-04 09:43:48',51,3,98282.88,20639.41,118922.29,'interno',NULL,NULL,NULL,NULL,NULL,NULL),(21,'0006-X0000016','99',6,'2026-06-04 10:05:26',74,3,100604.08,21126.86,121730.94,'interno',NULL,NULL,NULL,NULL,NULL,NULL),(22,'0006-X0000017','99',6,'2026-06-04 10:34:35',66,3,206150.12,43291.53,249441.65,'interno',NULL,NULL,NULL,NULL,NULL,NULL),(23,'0006-X0000018','99',6,'2026-06-04 11:03:57',4,3,65633.85,13783.11,79416.96,'interno',NULL,NULL,NULL,NULL,NULL,NULL),(24,'0006-X0000019','99',6,'2026-06-04 12:34:39',19,3,16828.10,3533.90,20362.00,'interno',NULL,NULL,NULL,NULL,NULL,NULL),(25,'0006-X0000020','99',6,'2026-06-04 12:36:59',30,3,72067.26,15134.12,87201.38,'interno',NULL,NULL,NULL,NULL,NULL,NULL),(26,'0006-X0000021','99',6,'2026-06-04 12:38:56',39,3,26525.45,5570.35,32095.80,'interno',NULL,NULL,NULL,NULL,NULL,NULL),(27,'0006-X0000022','99',6,'2026-06-04 12:41:34',38,3,32703.69,6867.77,39571.46,'interno',NULL,NULL,NULL,NULL,NULL,NULL),(28,'0006-X0000023','99',6,'2026-06-04 12:46:13',75,3,38842.79,8156.99,46999.78,'interno',NULL,NULL,NULL,NULL,NULL,NULL),(29,'0006-X0000024','99',6,'2026-06-04 12:50:55',20,3,9408.26,1975.74,11384.00,'interno',NULL,NULL,NULL,NULL,NULL,NULL),(30,'0006-X0000025','99',6,'2026-06-04 12:54:48',76,3,8247.77,1732.03,9979.80,'interno',NULL,NULL,NULL,NULL,NULL,NULL),(31,'0006-X0000026','99',6,'2026-06-04 13:01:13',77,3,46315.55,9726.27,56041.82,'interno',NULL,NULL,NULL,NULL,NULL,NULL),(32,'0006-X0000027','99',6,'2026-06-04 13:06:31',78,3,17248.60,3622.20,20870.80,'interno',NULL,NULL,NULL,NULL,NULL,NULL),(33,'0006-X0000028','99',6,'2026-06-04 13:09:30',79,3,28968.60,6083.40,35052.00,'interno',NULL,NULL,NULL,NULL,NULL,NULL),(34,'0006-X0000029','99',6,'2026-06-04 19:17:18',52,3,91555.62,19226.68,110782.30,'interno',NULL,NULL,NULL,NULL,NULL,NULL),(35,'0006-X0000030','99',6,'2026-06-04 19:26:48',80,3,33580.99,7052.01,40633.00,'interno',NULL,NULL,NULL,NULL,NULL,NULL),(36,'0006-X0000031','99',6,'2026-06-04 19:55:59',80,3,231758.53,48669.29,280427.82,'anulada',NULL,NULL,NULL,NULL,NULL,NULL),(37,'0006-X0000032','99',6,'2026-06-05 09:31:33',80,3,217785.05,45734.86,263519.91,'interno',NULL,NULL,NULL,NULL,NULL,NULL),(38,'0006-X0000033','99',6,'2026-06-05 10:22:46',81,3,50247.93,10552.07,60800.00,'interno',NULL,NULL,NULL,NULL,NULL,NULL),(39,'0006-X0000034','99',6,'2026-06-05 19:30:13',61,3,42837.12,8995.79,51832.91,'interno',NULL,NULL,NULL,NULL,NULL,NULL),(40,'0006-X0000035','99',6,'2026-06-05 19:37:41',50,3,43969.85,9233.67,53203.52,'anulada',NULL,NULL,NULL,NULL,NULL,NULL),(41,'0006-X0000036','99',6,'2026-06-05 19:40:31',50,3,36337.98,7630.98,43968.96,'interno',NULL,NULL,NULL,NULL,NULL,NULL),(42,'0006-X0000037','99',6,'2026-06-05 19:52:12',82,3,25831.40,5424.60,31256.00,'interno',NULL,NULL,NULL,NULL,NULL,NULL),(43,'0006-X0000038','99',6,'2026-06-06 13:44:30',59,3,126206.64,26503.40,152710.04,'interno',NULL,NULL,NULL,NULL,NULL,NULL),(44,'0006-X0000039','99',6,'2026-06-08 07:34:46',63,3,11730.81,2463.47,14194.28,'interno',NULL,NULL,NULL,NULL,NULL,NULL);
/*!40000 ALTER TABLE `factura` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `factura_compra`
--

DROP TABLE IF EXISTS `factura_compra`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `factura_compra` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `proveedor_id` int(11) NOT NULL,
  `fecha` date NOT NULL,
  `fecha_vencimiento` date DEFAULT NULL,
  `tipo_comprobante` varchar(5) NOT NULL DEFAULT 'A' COMMENT 'A, B o C',
  `clase_comprobante` varchar(15) NOT NULL DEFAULT 'factura' COMMENT 'factura / nota_credito / nota_debito',
  `punto_venta` varchar(5) NOT NULL,
  `numero` varchar(10) NOT NULL,
  `neto_gravado_21` decimal(12,2) NOT NULL DEFAULT 0.00 COMMENT 'Base imponible alícuota 21%',
  `iva_21` decimal(12,2) NOT NULL DEFAULT 0.00 COMMENT 'IVA 21%',
  `neto_gravado_105` decimal(12,2) NOT NULL DEFAULT 0.00 COMMENT 'Base imponible alícuota 10.5%',
  `iva_105` decimal(12,2) NOT NULL DEFAULT 0.00 COMMENT 'IVA 10.5%',
  `neto_no_gravado` decimal(12,2) NOT NULL DEFAULT 0.00,
  `otros_impuestos` decimal(12,2) NOT NULL DEFAULT 0.00,
  `total` decimal(12,2) NOT NULL,
  `saldo_pendiente` decimal(12,2) NOT NULL DEFAULT 0.00,
  `estado` varchar(15) NOT NULL DEFAULT 'pendiente' COMMENT 'pendiente/parcial/pagada/anulada',
  `cae` varchar(20) DEFAULT NULL,
  `fecha_vto_cae` date DEFAULT NULL,
  `observaciones` text DEFAULT NULL,
  `usuario_id` int(11) DEFAULT NULL,
  `fecha_creacion` datetime NOT NULL DEFAULT current_timestamp(),
  `con_detalle` tinyint(1) NOT NULL DEFAULT 0 COMMENT '1 = factura con detalle de artículos',
  `descuento` decimal(12,2) NOT NULL DEFAULT 0.00 COMMENT 'Bonificación comercial (prorratea al costo)',
  `flete` decimal(12,2) NOT NULL DEFAULT 0.00 COMMENT 'Flete (prorratea al costo)',
  `percepcion_iva` decimal(12,2) NOT NULL DEFAULT 0.00,
  `percepcion_iibb` decimal(12,2) NOT NULL DEFAULT 0.00,
  `percepcion_ganancias` decimal(12,2) NOT NULL DEFAULT 0.00,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_factura_compra` (`proveedor_id`,`clase_comprobante`,`tipo_comprobante`,`punto_venta`,`numero`),
  KEY `fk_fc_usuario` (`usuario_id`),
  KEY `idx_fc_estado` (`estado`),
  KEY `idx_fc_vto` (`fecha_vencimiento`),
  CONSTRAINT `fk_fc_proveedor` FOREIGN KEY (`proveedor_id`) REFERENCES `proveedor` (`id`),
  CONSTRAINT `fk_fc_usuario` FOREIGN KEY (`usuario_id`) REFERENCES `usuario` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE='utf8mb4_general_ci';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `factura_compra`
--

LOCK TABLES `factura_compra` WRITE;
/*!40000 ALTER TABLE `factura_compra` DISABLE KEYS */;
INSERT INTO `factura_compra` VALUES (1,1,'2026-05-30',NULL,'CI','interno','1','293',0.00,0.00,0.00,0.00,0.00,0.00,1801380.00,1801380.00,'pendiente',NULL,NULL,'',NULL,'2026-06-01 18:17:05',1,131.54,0.00,0.00,0.00,0.00),(2,2,'2026-06-02',NULL,'B','factura','00153','00066572',51134.64,0.00,0.00,0.00,0.00,0.00,51134.64,0.00,'pagada',NULL,NULL,'',3,'2026-06-02 18:23:14',1,0.00,0.00,0.00,0.00,0.00),(3,2,'2026-06-02',NULL,'CI','interno','980','44612',0.00,0.00,0.00,0.00,0.00,0.00,932229.61,932229.61,'pendiente',NULL,NULL,'',3,'2026-06-02 20:48:53',1,0.00,4364.41,0.00,0.00,0.00);
/*!40000 ALTER TABLE `factura_compra` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `factura_compra_detalle`
--

DROP TABLE IF EXISTS `factura_compra_detalle`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `factura_compra_detalle` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `factura_compra_id` int(11) NOT NULL,
  `producto_id` int(11) NOT NULL,
  `cantidad` decimal(10,3) NOT NULL,
  `precio_unitario` decimal(12,4) NOT NULL COMMENT 'Precio unitario sin IVA (como viene en la factura del proveedor)',
  `descuento_porcentaje` decimal(5,2) NOT NULL DEFAULT 0.00,
  `iva` decimal(5,2) NOT NULL DEFAULT 21.00,
  `subtotal` decimal(12,2) NOT NULL COMMENT 'cantidad * precio_unitario (sin IVA)',
  `costo_final_unitario` decimal(12,4) NOT NULL COMMENT 'Costo con IVA y prorrateo aplicado (va a producto.costo)',
  PRIMARY KEY (`id`),
  KEY `fk_fcd_factura` (`factura_compra_id`),
  KEY `fk_fcd_producto` (`producto_id`),
  CONSTRAINT `fk_fcd_factura` FOREIGN KEY (`factura_compra_id`) REFERENCES `factura_compra` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_fcd_producto` FOREIGN KEY (`producto_id`) REFERENCES `producto` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=45 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `factura_compra_detalle`
--

LOCK TABLES `factura_compra_detalle` WRITE;
/*!40000 ALTER TABLE `factura_compra_detalle` DISABLE KEYS */;
INSERT INTO `factura_compra_detalle` VALUES (1,1,38,6.000,3871.0744,0.00,21.00,23226.45,4683.6600),(2,1,39,6.000,3871.0740,0.00,21.00,23226.44,4683.6600),(3,1,100,320.000,507.4380,0.00,21.00,162380.16,613.9600),(4,1,201,160.000,507.4380,0.00,21.00,81190.08,613.9600),(5,1,123,168.000,795.0400,0.00,21.00,133566.72,961.9300),(6,1,86,12.000,3747.1070,0.00,21.00,44965.28,4533.6700),(7,1,84,12.000,3747.1070,0.00,21.00,44965.28,4533.6700),(8,1,87,12.000,3747.1070,0.00,21.00,44965.28,4533.6700),(9,1,1,12.000,3747.1070,0.00,21.00,44965.28,4533.6700),(10,1,40,6.000,3871.0740,0.00,21.00,23226.44,4683.6600),(11,1,104,12.000,8260.3300,0.00,21.00,99123.96,9994.2700),(12,1,191,6.000,3871.0740,0.00,21.00,23226.44,4683.6600),(13,1,47,6.000,3871.0740,0.00,21.00,23226.44,4683.6600),(14,1,194,168.000,795.0413,0.00,21.00,133566.94,961.9300),(15,1,195,168.000,795.0413,0.00,21.00,133566.94,961.9300),(16,1,132,12.000,3038.8430,0.00,21.00,36466.12,3676.7300),(17,1,136,12.000,3038.8430,0.00,21.00,36466.12,3676.7300),(18,1,139,12.000,3038.8430,0.00,21.00,36466.12,3676.7300),(19,1,141,12.000,3038.8430,0.00,21.00,36466.12,3676.7300),(20,1,138,12.000,3038.8430,0.00,21.00,36466.12,3676.7300),(21,1,122,168.000,795.0410,0.00,21.00,133566.89,961.9300),(22,1,121,168.000,795.0410,0.00,21.00,133566.89,961.9300),(23,2,206,1.000,42259.5041,0.00,21.00,42259.50,51134.0000),(24,3,120,180.000,528.7020,0.00,21.00,95166.36,642.7400),(25,3,95,180.000,500.6600,0.00,21.00,90118.80,608.6500),(26,3,94,180.000,500.6600,0.00,21.00,90118.80,608.6500),(27,3,128,120.000,411.8900,0.00,21.00,49426.80,500.7300),(28,3,127,120.000,441.8900,0.00,21.00,53026.80,537.2000),(29,3,6,6.000,7809.8000,0.00,21.00,46858.80,9494.3100),(30,3,163,60.000,756.1630,0.00,21.00,45369.78,919.2600),(31,3,164,28.000,756.1630,0.00,21.00,21172.56,919.2600),(32,3,162,24.000,756.1630,0.00,21.00,18147.91,919.2600),(33,3,52,20.000,2024.7400,0.00,21.00,40494.80,2461.4600),(34,3,29,1.000,5626.3000,0.00,21.00,5626.30,6839.8500),(35,3,27,4.000,5626.2300,0.00,21.00,22504.92,6839.7600),(36,3,13,3.000,3149.7700,0.00,21.00,9449.31,3829.1500),(37,3,19,3.000,3149.7700,0.00,21.00,9449.31,3829.1500),(38,3,17,12.000,3149.7700,0.00,21.00,37797.24,3829.1500),(39,3,12,6.000,3149.7700,0.00,21.00,18898.62,3829.1500),(40,3,18,3.000,3149.7700,0.00,21.00,9449.31,3829.1500),(41,3,10,3.000,3149.7700,0.00,21.00,9449.31,3829.1500),(42,3,11,3.000,3149.7700,0.00,21.00,9449.31,3829.1500),(43,3,129,200.000,126.7580,0.00,21.00,25351.60,154.1000),(44,3,144,60.000,991.7350,0.00,21.00,59504.10,1205.6400);
/*!40000 ALTER TABLE `factura_compra_detalle` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `gastos`
--

DROP TABLE IF EXISTS `gastos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `gastos` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `fecha` date NOT NULL,
  `descripcion` text NOT NULL,
  `monto` decimal(10,2) NOT NULL,
  `categoria` varchar(50) NOT NULL DEFAULT 'general',
  `metodo_pago` varchar(30) NOT NULL DEFAULT 'efectivo',
  `notas` text DEFAULT NULL,
  `fecha_creacion` timestamp NOT NULL DEFAULT current_timestamp(),
  `fecha_modificacion` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `activo` tinyint(1) DEFAULT 1,
  `usuario_id` int(11) DEFAULT NULL,
  `caja_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_gastos_fecha` (`fecha`),
  KEY `idx_gastos_categoria` (`categoria`),
  KEY `idx_gastos_metodo_pago` (`metodo_pago`),
  KEY `idx_gastos_activo` (`activo`),
  KEY `idx_gastos_fecha_activo` (`fecha`,`activo`),
  KEY `caja_id` (`caja_id`),
  CONSTRAINT `gastos_ibfk_1` FOREIGN KEY (`caja_id`) REFERENCES `cajas` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `gastos`
--

LOCK TABLES `gastos` WRITE;
/*!40000 ALTER TABLE `gastos` DISABLE KEYS */;
INSERT INTO `gastos` VALUES (1,'2026-06-01','COMBUSTIBLE TOYOTA',111019.82,'transporte','efectivo',NULL,'2026-06-02 21:27:33','2026-06-02 21:27:33',1,3,1);
/*!40000 ALTER TABLE `gastos` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `liquidacion_detalle`
--

DROP TABLE IF EXISTS `liquidacion_detalle`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `liquidacion_detalle` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `liquidacion_id` int(11) NOT NULL,
  `interno_id` int(11) NOT NULL,
  `factura_derivada_id` int(11) DEFAULT NULL,
  `monto_interno` decimal(12,2) DEFAULT NULL,
  `monto_factura` decimal(12,2) DEFAULT NULL,
  `monto_diferencia` decimal(12,2) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_interno_no_duplicado` (`interno_id`),
  KEY `idx_liquidacion` (`liquidacion_id`),
  KEY `idx_interno` (`interno_id`),
  KEY `fk_liqdet_factura` (`factura_derivada_id`),
  CONSTRAINT `fk_liqdet_factura` FOREIGN KEY (`factura_derivada_id`) REFERENCES `factura` (`id`),
  CONSTRAINT `fk_liqdet_interno` FOREIGN KEY (`interno_id`) REFERENCES `factura` (`id`),
  CONSTRAINT `fk_liqdet_liquidacion` FOREIGN KEY (`liquidacion_id`) REFERENCES `liquidacion_intermediario` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE='utf8mb4_general_ci';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `liquidacion_detalle`
--

LOCK TABLES `liquidacion_detalle` WRITE;
/*!40000 ALTER TABLE `liquidacion_detalle` DISABLE KEYS */;
/*!40000 ALTER TABLE `liquidacion_detalle` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `liquidacion_intermediario`
--

DROP TABLE IF EXISTS `liquidacion_intermediario`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `liquidacion_intermediario` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `numero` varchar(50) NOT NULL,
  `fecha` datetime DEFAULT current_timestamp(),
  `intermediario_id` int(11) NOT NULL,
  `total_vendido` decimal(12,2) DEFAULT 0.00,
  `total_costo` decimal(12,2) DEFAULT 0.00,
  `total_liquidar` decimal(12,2) DEFAULT 0.00,
  `base_calculo` varchar(20) DEFAULT 'con_iva',
  `estado` varchar(20) DEFAULT 'pendiente_pago',
  `medio_pago` varchar(50) DEFAULT NULL,
  `fecha_pago` datetime DEFAULT NULL,
  `usuario_id` int(11) DEFAULT NULL,
  `motivo` text DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `numero` (`numero`),
  KEY `idx_intermediario` (`intermediario_id`),
  KEY `idx_estado` (`estado`),
  KEY `idx_fecha` (`fecha`),
  KEY `fk_liq_usuario` (`usuario_id`),
  CONSTRAINT `fk_liq_intermediario` FOREIGN KEY (`intermediario_id`) REFERENCES `cliente` (`id`),
  CONSTRAINT `fk_liq_usuario` FOREIGN KEY (`usuario_id`) REFERENCES `usuario` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE='utf8mb4_general_ci';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `liquidacion_intermediario`
--

LOCK TABLES `liquidacion_intermediario` WRITE;
/*!40000 ALTER TABLE `liquidacion_intermediario` DISABLE KEYS */;
/*!40000 ALTER TABLE `liquidacion_intermediario` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `medios_pago`
--

DROP TABLE IF EXISTS `medios_pago`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `medios_pago` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `factura_id` int(11) NOT NULL,
  `medio_pago` varchar(20) NOT NULL,
  `importe` decimal(10,2) NOT NULL,
  `fecha_registro` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `factura_id` (`factura_id`),
  CONSTRAINT `medios_pago_ibfk_1` FOREIGN KEY (`factura_id`) REFERENCES `factura` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=45 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `medios_pago`
--

LOCK TABLES `medios_pago` WRITE;
/*!40000 ALTER TABLE `medios_pago` DISABLE KEYS */;
INSERT INTO `medios_pago` VALUES (1,1,'efectivo',100.00,'2026-05-28 17:30:51'),(2,2,'efectivo',100.00,'2026-05-28 18:14:00'),(3,3,'efectivo',100.00,'2026-05-28 18:33:06'),(4,4,'efectivo',100.00,'2026-05-28 18:34:54'),(5,5,'efectivo',4880.18,'2026-05-28 20:32:26'),(6,6,'efectivo',277445.04,'2026-05-29 17:56:24'),(7,7,'CTA.CTE',133323.37,'2026-05-30 14:28:55'),(8,8,'CTA.CTE',78549.87,'2026-06-01 11:55:23'),(9,9,'CTA.CTE',45142.00,'2026-06-01 12:00:09'),(10,10,'CTA.CTE',37964.08,'2026-06-01 14:10:04'),(11,11,'CTA.CTE',56818.00,'2026-06-01 20:04:43'),(12,12,'CTA.CTE',145741.50,'2026-06-02 14:54:58'),(13,13,'CTA.CTE',92129.43,'2026-06-03 20:27:55'),(14,14,'CTA.CTE',68528.76,'2026-06-04 08:30:07'),(15,15,'CTA.CTE',36511.70,'2026-06-04 08:34:44'),(16,16,'CTA.CTE',23242.46,'2026-06-04 08:52:12'),(17,17,'CTA.CTE',36511.70,'2026-06-04 08:57:08'),(18,18,'CTA.CTE',89395.12,'2026-06-04 09:07:01'),(19,19,'CTA.CTE',98369.93,'2026-06-04 09:11:20'),(20,20,'CTA.CTE',118922.29,'2026-06-04 09:43:48'),(21,21,'CTA.CTE',121730.94,'2026-06-04 10:05:27'),(22,22,'CTA.CTE',249441.65,'2026-06-04 10:34:35'),(23,23,'CTA.CTE',79416.96,'2026-06-04 11:03:57'),(24,24,'CTA.CTE',20362.00,'2026-06-04 12:34:40'),(25,25,'CTA.CTE',87201.38,'2026-06-04 12:36:59'),(26,26,'CTA.CTE',32095.80,'2026-06-04 12:38:56'),(27,27,'CTA.CTE',39571.46,'2026-06-04 12:41:34'),(28,28,'CTA.CTE',46999.78,'2026-06-04 12:46:13'),(29,29,'efectivo',11384.00,'2026-06-04 12:50:55'),(30,30,'efectivo',9979.80,'2026-06-04 12:54:48'),(31,31,'efectivo',56041.82,'2026-06-04 13:01:13'),(32,32,'efectivo',20870.80,'2026-06-04 13:06:31'),(33,33,'efectivo',35052.00,'2026-06-04 13:09:30'),(34,34,'CTA.CTE',110782.30,'2026-06-04 19:17:18'),(35,35,'CTA.CTE',40633.00,'2026-06-04 19:26:48'),(36,36,'CTA.CTE',280427.82,'2026-06-04 19:55:59'),(37,37,'efectivo',263519.91,'2026-06-05 09:31:33'),(38,38,'CTA.CTE',60800.00,'2026-06-05 10:22:46'),(39,39,'CTA.CTE',51832.91,'2026-06-05 19:30:13'),(40,40,'CTA.CTE',53203.52,'2026-06-05 19:37:41'),(41,41,'CTA.CTE',43968.96,'2026-06-05 19:40:31'),(42,42,'CTA.CTE',31256.00,'2026-06-05 19:52:12'),(43,43,'CTA.CTE',152710.04,'2026-06-06 13:44:30'),(44,44,'CTA.CTE',14194.28,'2026-06-08 07:34:46');
/*!40000 ALTER TABLE `medios_pago` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `movimiento_stock`
--

DROP TABLE IF EXISTS `movimiento_stock`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `movimiento_stock` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `producto_id` int(11) NOT NULL,
  `tipo_movimiento` enum('entrada','salida','ajuste') NOT NULL,
  `cantidad` int(11) NOT NULL,
  `stock_anterior` int(11) NOT NULL,
  `stock_nuevo` int(11) NOT NULL,
  `motivo` varchar(100) DEFAULT NULL,
  `factura_id` int(11) DEFAULT NULL,
  `usuario_id` int(11) NOT NULL,
  `fecha` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `idx_producto` (`producto_id`),
  KEY `idx_fecha` (`fecha`),
  KEY `factura_id` (`factura_id`),
  KEY `usuario_id` (`usuario_id`),
  CONSTRAINT `movimiento_stock_ibfk_1` FOREIGN KEY (`producto_id`) REFERENCES `producto` (`id`),
  CONSTRAINT `movimiento_stock_ibfk_2` FOREIGN KEY (`factura_id`) REFERENCES `factura` (`id`),
  CONSTRAINT `movimiento_stock_ibfk_3` FOREIGN KEY (`usuario_id`) REFERENCES `usuario` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `movimiento_stock`
--

LOCK TABLES `movimiento_stock` WRITE;
/*!40000 ALTER TABLE `movimiento_stock` DISABLE KEYS */;
/*!40000 ALTER TABLE `movimiento_stock` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `movimientos_caja`
--

DROP TABLE IF EXISTS `movimientos_caja`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `movimientos_caja` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `caja_id` int(11) NOT NULL,
  `tipo` enum('ingreso','egreso') NOT NULL,
  `descripcion` varchar(255) NOT NULL,
  `monto` decimal(10,2) NOT NULL,
  `notas` text DEFAULT NULL,
  `fecha` datetime NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `usuario_id` int(11) NOT NULL DEFAULT 3,
  `punto_venta` int(11) NOT NULL DEFAULT 1,
  PRIMARY KEY (`id`),
  KEY `caja_id` (`caja_id`),
  KEY `fk_movimientos_usuario` (`usuario_id`),
  KEY `idx_movimientos_fecha` (`fecha`),
  KEY `idx_movimientos_tipo` (`tipo`),
  KEY `idx_movimientos_pv` (`punto_venta`),
  CONSTRAINT `fk_movimientos_usuario` FOREIGN KEY (`usuario_id`) REFERENCES `usuario` (`id`),
  CONSTRAINT `movimientos_caja_ibfk_1` FOREIGN KEY (`caja_id`) REFERENCES `cajas` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=13 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `movimientos_caja`
--

LOCK TABLES `movimientos_caja` WRITE;
/*!40000 ALTER TABLE `movimientos_caja` DISABLE KEYS */;
INSERT INTO `movimientos_caja` VALUES (1,1,'ingreso','SALDO INICIAL',900000.00,'COMIENZO DE ACTIVIDAD EN SISTEMA','2026-06-01 10:15:01','2026-06-01 13:15:01',3,6),(2,1,'ingreso','TRANSFERENCIA',33155.00,'MILAGROS YAMILA GUTIERREZ 01-06','2026-06-01 10:37:08','2026-06-01 13:37:08',3,6),(3,1,'egreso','Pago proveedor: PEDRO BALESTRINO E HIJOS — R 0001-00000001',51134.64,'Pago a PEDRO BALESTRINO E HIJOS','2026-06-02 18:24:06','2026-06-02 21:24:06',3,6),(4,1,'ingreso','Cobro R00000009 — efectivo',32014.00,'Recibo R00000009','2026-06-07 19:57:47','2026-06-07 22:57:47',3,6),(5,1,'ingreso','Cobro R00000010 — efectivo',57348.00,'Recibo R00000010','2026-06-07 19:58:29','2026-06-07 22:58:29',3,6),(6,1,'ingreso','Cobro R00000017 — efectivo',36511.70,'Recibo R00000017','2026-06-07 20:21:29','2026-06-07 23:21:29',3,6),(7,1,'ingreso','Cobro R00000018 — efectivo',32095.80,'Recibo R00000018','2026-06-07 20:22:50','2026-06-07 23:22:50',3,6),(8,1,'ingreso','Cobro R00000019 — efectivo',64186.00,'Recibo R00000019','2026-06-07 20:24:55','2026-06-07 23:24:55',3,6),(9,1,'ingreso','Cobro R00000020 — efectivo',44450.00,'Recibo R00000020','2026-06-07 20:35:51','2026-06-07 23:35:51',3,6),(10,1,'ingreso','Cobro R00000021 — efectivo',26761.00,'Recibo R00000021','2026-06-07 20:36:34','2026-06-07 23:36:34',3,6),(11,1,'ingreso','Cobro R00000022 — efectivo',50000.00,'Recibo R00000022','2026-06-07 20:37:30','2026-06-07 23:37:30',3,6),(12,1,'ingreso','Cobro R00000023 — efectivo',28000.00,'Recibo R00000023','2026-06-07 20:38:12','2026-06-07 23:38:12',3,6);
/*!40000 ALTER TABLE `movimientos_caja` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `mp_config`
--

DROP TABLE IF EXISTS `mp_config`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `mp_config` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `access_token` varchar(255) NOT NULL,
  `public_key` varchar(255) DEFAULT NULL,
  `user_id_mp` varchar(50) DEFAULT NULL,
  `ambiente` enum('sandbox','prod') NOT NULL DEFAULT 'prod',
  `activo` tinyint(1) NOT NULL DEFAULT 1,
  `timeout_segundos` int(11) NOT NULL DEFAULT 300,
  `fecha_alta` datetime NOT NULL DEFAULT current_timestamp(),
  `fecha_modificacion` datetime NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `mp_config`
--

LOCK TABLES `mp_config` WRITE;
/*!40000 ALTER TABLE `mp_config` DISABLE KEYS */;
/*!40000 ALTER TABLE `mp_config` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `mp_pago`
--

DROP TABLE IF EXISTS `mp_pago`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `mp_pago` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `preference_id` varchar(100) DEFAULT NULL,
  `payment_id` varchar(100) DEFAULT NULL,
  `external_reference` varchar(80) NOT NULL,
  `monto` decimal(12,2) NOT NULL,
  `estado` enum('pending','approved','rejected','cancelled','expired') NOT NULL DEFAULT 'pending',
  `factura_id` int(11) DEFAULT NULL,
  `metodo_detalle` varchar(50) DEFAULT NULL,
  `qr_data` text DEFAULT NULL,
  `raw_response` longtext DEFAULT NULL,
  `fecha_creacion` datetime NOT NULL DEFAULT current_timestamp(),
  `fecha_aprobacion` datetime DEFAULT NULL,
  `fecha_actualizacion` datetime NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_mp_pago_external_ref` (`external_reference`),
  KEY `idx_mp_pago_estado` (`estado`),
  KEY `idx_mp_pago_fecha` (`fecha_creacion`),
  KEY `idx_mp_pago_factura` (`factura_id`),
  CONSTRAINT `fk_mp_pago_factura` FOREIGN KEY (`factura_id`) REFERENCES `factura` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `mp_pago`
--

LOCK TABLES `mp_pago` WRITE;
/*!40000 ALTER TABLE `mp_pago` DISABLE KEYS */;
/*!40000 ALTER TABLE `mp_pago` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `nc_imputacion_compra`
--

DROP TABLE IF EXISTS `nc_imputacion_compra`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `nc_imputacion_compra` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `nc_id` int(11) NOT NULL,
  `factura_id` int(11) NOT NULL,
  `monto_imputado` decimal(12,2) NOT NULL,
  `fecha` datetime NOT NULL DEFAULT current_timestamp(),
  `usuario_id` int(11) DEFAULT NULL,
  `estado` enum('activa','revertida') NOT NULL DEFAULT 'activa',
  `fecha_reversion` datetime DEFAULT NULL,
  `usuario_reversion_id` int(11) DEFAULT NULL,
  `observaciones` text DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_nc_imp_compra_usuario` (`usuario_id`),
  KEY `idx_nc_imp_compra_nc` (`nc_id`),
  KEY `idx_nc_imp_compra_factura` (`factura_id`),
  KEY `idx_nc_imp_compra_estado` (`estado`),
  CONSTRAINT `fk_nc_imp_compra_factura` FOREIGN KEY (`factura_id`) REFERENCES `factura_compra` (`id`),
  CONSTRAINT `fk_nc_imp_compra_nc` FOREIGN KEY (`nc_id`) REFERENCES `factura_compra` (`id`),
  CONSTRAINT `fk_nc_imp_compra_usuario` FOREIGN KEY (`usuario_id`) REFERENCES `usuario` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `nc_imputacion_compra`
--

LOCK TABLES `nc_imputacion_compra` WRITE;
/*!40000 ALTER TABLE `nc_imputacion_compra` DISABLE KEYS */;
/*!40000 ALTER TABLE `nc_imputacion_compra` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `notas_credito`
--

DROP TABLE IF EXISTS `notas_credito`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `notas_credito` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `numero` varchar(50) DEFAULT NULL,
  `tipo_comprobante` varchar(10) DEFAULT NULL,
  `punto_venta` int(11) DEFAULT NULL,
  `fecha` datetime DEFAULT NULL,
  `factura_id` int(11) NOT NULL,
  `factura_numero` varchar(50) DEFAULT NULL,
  `cliente_id` int(11) DEFAULT NULL,
  `usuario_id` int(11) DEFAULT NULL,
  `subtotal` decimal(10,2) DEFAULT NULL,
  `iva` decimal(10,2) DEFAULT NULL,
  `total` decimal(10,2) DEFAULT NULL,
  `estado` varchar(20) DEFAULT NULL,
  `cae` varchar(50) DEFAULT NULL,
  `vto_cae` date DEFAULT NULL,
  `error_afip` text DEFAULT NULL,
  `motivo` varchar(500) DEFAULT NULL,
  `fecha_creacion` datetime DEFAULT NULL,
  `fecha_autorizacion` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `numero` (`numero`),
  KEY `factura_id` (`factura_id`),
  KEY `cliente_id` (`cliente_id`),
  KEY `usuario_id` (`usuario_id`),
  CONSTRAINT `notas_credito_ibfk_1` FOREIGN KEY (`factura_id`) REFERENCES `factura` (`id`),
  CONSTRAINT `notas_credito_ibfk_2` FOREIGN KEY (`cliente_id`) REFERENCES `cliente` (`id`),
  CONSTRAINT `notas_credito_ibfk_3` FOREIGN KEY (`usuario_id`) REFERENCES `usuario` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `notas_credito`
--

LOCK TABLES `notas_credito` WRITE;
/*!40000 ALTER TABLE `notas_credito` DISABLE KEYS */;
/*!40000 ALTER TABLE `notas_credito` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ofertas_volumen`
--

DROP TABLE IF EXISTS `ofertas_volumen`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ofertas_volumen` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `producto_id` int(11) NOT NULL,
  `cantidad_minima` decimal(10,3) NOT NULL,
  `precio_oferta` decimal(10,2) NOT NULL,
  `descripcion` varchar(200) DEFAULT NULL,
  `activo` tinyint(1) DEFAULT 1,
  `fecha_creacion` datetime DEFAULT current_timestamp(),
  `fecha_modificacion` datetime DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `producto_id` (`producto_id`),
  CONSTRAINT `ofertas_volumen_ibfk_1` FOREIGN KEY (`producto_id`) REFERENCES `producto` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ofertas_volumen`
--

LOCK TABLES `ofertas_volumen` WRITE;
/*!40000 ALTER TABLE `ofertas_volumen` DISABLE KEYS */;
/*!40000 ALTER TABLE `ofertas_volumen` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `orden_compra`
--

DROP TABLE IF EXISTS `orden_compra`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `orden_compra` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `numero` int(11) NOT NULL,
  `punto_venta` int(11) NOT NULL,
  `proveedor_id` int(11) NOT NULL,
  `fecha_emision` date NOT NULL,
  `fecha_entrega_estimada` date DEFAULT NULL,
  `estado` varchar(15) NOT NULL,
  `subtotal` decimal(12,2) NOT NULL,
  `iva` decimal(12,2) NOT NULL,
  `total` decimal(12,2) NOT NULL,
  `observaciones` text DEFAULT NULL,
  `condiciones_pago` varchar(200) DEFAULT NULL,
  `factura_compra_id` int(11) DEFAULT NULL,
  `motivo_cancelacion` varchar(200) DEFAULT NULL,
  `usuario_id` int(11) DEFAULT NULL,
  `fecha_creacion` datetime DEFAULT NULL,
  `fecha_modificacion` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `proveedor_id` (`proveedor_id`),
  KEY `factura_compra_id` (`factura_compra_id`),
  KEY `usuario_id` (`usuario_id`),
  CONSTRAINT `orden_compra_ibfk_1` FOREIGN KEY (`proveedor_id`) REFERENCES `proveedor` (`id`),
  CONSTRAINT `orden_compra_ibfk_2` FOREIGN KEY (`factura_compra_id`) REFERENCES `factura_compra` (`id`),
  CONSTRAINT `orden_compra_ibfk_3` FOREIGN KEY (`usuario_id`) REFERENCES `usuario` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE='utf8mb4_general_ci';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `orden_compra`
--

LOCK TABLES `orden_compra` WRITE;
/*!40000 ALTER TABLE `orden_compra` DISABLE KEYS */;
/*!40000 ALTER TABLE `orden_compra` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `orden_compra_detalle`
--

DROP TABLE IF EXISTS `orden_compra_detalle`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `orden_compra_detalle` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `oc_id` int(11) NOT NULL,
  `producto_id` int(11) NOT NULL,
  `cantidad_pedida` decimal(12,3) NOT NULL,
  `cantidad_recibida` decimal(12,3) NOT NULL,
  `precio_unitario` decimal(12,2) NOT NULL,
  `subtotal` decimal(12,2) NOT NULL,
  `observaciones` varchar(200) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `oc_id` (`oc_id`),
  KEY `producto_id` (`producto_id`),
  CONSTRAINT `orden_compra_detalle_ibfk_1` FOREIGN KEY (`oc_id`) REFERENCES `orden_compra` (`id`),
  CONSTRAINT `orden_compra_detalle_ibfk_2` FOREIGN KEY (`producto_id`) REFERENCES `producto` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE='utf8mb4_general_ci';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `orden_compra_detalle`
--

LOCK TABLES `orden_compra_detalle` WRITE;
/*!40000 ALTER TABLE `orden_compra_detalle` DISABLE KEYS */;
/*!40000 ALTER TABLE `orden_compra_detalle` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `orden_compra_numerador`
--

DROP TABLE IF EXISTS `orden_compra_numerador`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `orden_compra_numerador` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `punto_venta` int(11) NOT NULL,
  `ultimo_numero` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `punto_venta` (`punto_venta`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE='utf8mb4_general_ci';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `orden_compra_numerador`
--

LOCK TABLES `orden_compra_numerador` WRITE;
/*!40000 ALTER TABLE `orden_compra_numerador` DISABLE KEYS */;
/*!40000 ALTER TABLE `orden_compra_numerador` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `orden_compra_recepcion`
--

DROP TABLE IF EXISTS `orden_compra_recepcion`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `orden_compra_recepcion` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `oc_id` int(11) NOT NULL,
  `fecha` date NOT NULL,
  `nro_remito` varchar(30) DEFAULT NULL,
  `observaciones` text DEFAULT NULL,
  `usuario_id` int(11) DEFAULT NULL,
  `fecha_creacion` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `oc_id` (`oc_id`),
  KEY `usuario_id` (`usuario_id`),
  CONSTRAINT `orden_compra_recepcion_ibfk_1` FOREIGN KEY (`oc_id`) REFERENCES `orden_compra` (`id`),
  CONSTRAINT `orden_compra_recepcion_ibfk_2` FOREIGN KEY (`usuario_id`) REFERENCES `usuario` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE='utf8mb4_general_ci';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `orden_compra_recepcion`
--

LOCK TABLES `orden_compra_recepcion` WRITE;
/*!40000 ALTER TABLE `orden_compra_recepcion` DISABLE KEYS */;
/*!40000 ALTER TABLE `orden_compra_recepcion` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `orden_compra_recepcion_detalle`
--

DROP TABLE IF EXISTS `orden_compra_recepcion_detalle`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `orden_compra_recepcion_detalle` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `recepcion_id` int(11) NOT NULL,
  `oc_detalle_id` int(11) NOT NULL,
  `producto_id` int(11) NOT NULL,
  `cantidad_recibida` decimal(12,3) NOT NULL,
  `observaciones` varchar(200) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `recepcion_id` (`recepcion_id`),
  KEY `oc_detalle_id` (`oc_detalle_id`),
  KEY `producto_id` (`producto_id`),
  CONSTRAINT `orden_compra_recepcion_detalle_ibfk_1` FOREIGN KEY (`recepcion_id`) REFERENCES `orden_compra_recepcion` (`id`),
  CONSTRAINT `orden_compra_recepcion_detalle_ibfk_2` FOREIGN KEY (`oc_detalle_id`) REFERENCES `orden_compra_detalle` (`id`),
  CONSTRAINT `orden_compra_recepcion_detalle_ibfk_3` FOREIGN KEY (`producto_id`) REFERENCES `producto` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE='utf8mb4_general_ci';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `orden_compra_recepcion_detalle`
--

LOCK TABLES `orden_compra_recepcion_detalle` WRITE;
/*!40000 ALTER TABLE `orden_compra_recepcion_detalle` DISABLE KEYS */;
/*!40000 ALTER TABLE `orden_compra_recepcion_detalle` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `pago_imputacion`
--

DROP TABLE IF EXISTS `pago_imputacion`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `pago_imputacion` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `pago_id` int(11) NOT NULL,
  `factura_id` int(11) NOT NULL,
  `monto_imputado` decimal(12,2) NOT NULL,
  `fecha` datetime NOT NULL DEFAULT current_timestamp(),
  `usuario_id` int(11) DEFAULT NULL,
  `estado` enum('activa','revertida') NOT NULL DEFAULT 'activa',
  `fecha_reversion` datetime DEFAULT NULL,
  `usuario_reversion_id` int(11) DEFAULT NULL,
  `observaciones` text DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_pago_imp_usuario` (`usuario_id`),
  KEY `idx_pago_imp_pago` (`pago_id`),
  KEY `idx_pago_imp_factura` (`factura_id`),
  KEY `idx_pago_imp_estado` (`estado`),
  CONSTRAINT `fk_pago_imp_factura` FOREIGN KEY (`factura_id`) REFERENCES `cta_cte_movimiento` (`id`),
  CONSTRAINT `fk_pago_imp_pago` FOREIGN KEY (`pago_id`) REFERENCES `cta_cte_movimiento` (`id`),
  CONSTRAINT `fk_pago_imp_usuario` FOREIGN KEY (`usuario_id`) REFERENCES `usuario` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `pago_imputacion`
--

LOCK TABLES `pago_imputacion` WRITE;
/*!40000 ALTER TABLE `pago_imputacion` DISABLE KEYS */;
/*!40000 ALTER TABLE `pago_imputacion` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `pago_proveedor`
--

DROP TABLE IF EXISTS `pago_proveedor`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `pago_proveedor` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `proveedor_id` int(11) NOT NULL,
  `fecha` date NOT NULL,
  `importe` decimal(12,2) NOT NULL,
  `numero_recibo` int(11) NOT NULL DEFAULT 0,
  `punto_venta_recibo` int(11) NOT NULL DEFAULT 1,
  `estado` varchar(15) NOT NULL DEFAULT 'activo' COMMENT 'activo/anulado',
  `forma_pago` varchar(30) NOT NULL DEFAULT 'efectivo' COMMENT 'efectivo, transferencia, cheque, otro',
  `referencia` varchar(100) DEFAULT NULL COMMENT 'N° cheque, N° transferencia, etc.',
  `observaciones` text DEFAULT NULL,
  `usuario_id` int(11) DEFAULT NULL,
  `fecha_creacion` datetime NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_pp_num` (`punto_venta_recibo`,`numero_recibo`,`estado`),
  KEY `fk_pp_proveedor` (`proveedor_id`),
  KEY `fk_pp_usuario` (`usuario_id`),
  KEY `idx_pp_estado` (`estado`),
  CONSTRAINT `fk_pp_proveedor` FOREIGN KEY (`proveedor_id`) REFERENCES `proveedor` (`id`),
  CONSTRAINT `fk_pp_usuario` FOREIGN KEY (`usuario_id`) REFERENCES `usuario` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE='utf8mb4_general_ci';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `pago_proveedor`
--

LOCK TABLES `pago_proveedor` WRITE;
/*!40000 ALTER TABLE `pago_proveedor` DISABLE KEYS */;
INSERT INTO `pago_proveedor` VALUES (1,2,'2026-06-02',51134.64,1,1,'activo','Efectivo',NULL,NULL,3,'2026-06-02 18:24:06');
/*!40000 ALTER TABLE `pago_proveedor` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `pago_proveedor_detalle`
--

DROP TABLE IF EXISTS `pago_proveedor_detalle`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `pago_proveedor_detalle` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `pago_id` int(11) NOT NULL,
  `factura_id` int(11) NOT NULL,
  `monto_imputado` decimal(12,2) NOT NULL DEFAULT 0.00,
  PRIMARY KEY (`id`),
  KEY `idx_pp_det_pago` (`pago_id`),
  KEY `idx_pp_det_fact` (`factura_id`),
  CONSTRAINT `fk_pp_det_fact` FOREIGN KEY (`factura_id`) REFERENCES `factura_compra` (`id`) ON UPDATE CASCADE,
  CONSTRAINT `fk_pp_det_pago` FOREIGN KEY (`pago_id`) REFERENCES `pago_proveedor` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE='utf8mb4_general_ci';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `pago_proveedor_detalle`
--

LOCK TABLES `pago_proveedor_detalle` WRITE;
/*!40000 ALTER TABLE `pago_proveedor_detalle` DISABLE KEYS */;
INSERT INTO `pago_proveedor_detalle` VALUES (1,1,2,51134.64);
/*!40000 ALTER TABLE `pago_proveedor_detalle` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `pago_proveedor_medio`
--

DROP TABLE IF EXISTS `pago_proveedor_medio`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `pago_proveedor_medio` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `pago_id` int(11) NOT NULL,
  `medio` varchar(20) NOT NULL COMMENT 'efectivo/transferencia/cheque_propio/cheque_tercero/otro',
  `monto` decimal(12,2) NOT NULL DEFAULT 0.00,
  `cheque_propio_id` int(11) DEFAULT NULL,
  `cheque_tercero_id` int(11) DEFAULT NULL,
  `banco_destino` varchar(50) DEFAULT NULL,
  `cbu_destino` varchar(22) DEFAULT NULL,
  `observaciones` varchar(200) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_pp_medio_pago` (`pago_id`),
  KEY `idx_pp_medio_chp` (`cheque_propio_id`),
  KEY `idx_pp_medio_cht` (`cheque_tercero_id`),
  CONSTRAINT `fk_pp_medio_chp` FOREIGN KEY (`cheque_propio_id`) REFERENCES `cheque_propio` (`id`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `fk_pp_medio_cht` FOREIGN KEY (`cheque_tercero_id`) REFERENCES `cheque_tercero` (`id`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `fk_pp_medio_pago` FOREIGN KEY (`pago_id`) REFERENCES `pago_proveedor` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE='utf8mb4_general_ci';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `pago_proveedor_medio`
--

LOCK TABLES `pago_proveedor_medio` WRITE;
/*!40000 ALTER TABLE `pago_proveedor_medio` DISABLE KEYS */;
INSERT INTO `pago_proveedor_medio` VALUES (1,1,'efectivo',51134.64,NULL,NULL,NULL,NULL,NULL);
/*!40000 ALTER TABLE `pago_proveedor_medio` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `pago_proveedor_numerador`
--

DROP TABLE IF EXISTS `pago_proveedor_numerador`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `pago_proveedor_numerador` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `punto_venta` int(11) NOT NULL DEFAULT 1,
  `ultimo_numero` int(11) NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_pp_num_pv` (`punto_venta`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE='utf8mb4_general_ci';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `pago_proveedor_numerador`
--

LOCK TABLES `pago_proveedor_numerador` WRITE;
/*!40000 ALTER TABLE `pago_proveedor_numerador` DISABLE KEYS */;
INSERT INTO `pago_proveedor_numerador` VALUES (1,1,1);
/*!40000 ALTER TABLE `pago_proveedor_numerador` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `pedido`
--

DROP TABLE IF EXISTS `pedido`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `pedido` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `cliente_id` int(11) NOT NULL,
  `fecha` datetime DEFAULT current_timestamp(),
  `estado` enum('pendiente','preparando','cotizado','aceptado','listo','facturado','remitado','rechazado','cancelado') DEFAULT 'pendiente',
  `subtotal` decimal(12,2) DEFAULT 0.00,
  `iva` decimal(12,2) DEFAULT 0.00,
  `total` decimal(12,2) DEFAULT 0.00,
  `notas` text DEFAULT NULL,
  `factura_id` int(11) DEFAULT NULL,
  `fecha_actualizacion` datetime DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `tipo_entrega` varchar(20) DEFAULT 'retiro',
  `zona_id` int(11) DEFAULT NULL COMMENT 'Zona de reparto (heredada del cliente)',
  `en_reparto_fecha` date DEFAULT NULL COMMENT 'Fecha asignada al reparto',
  `orden_reparto_manual` int(11) DEFAULT NULL COMMENT 'Orden manual drag-and-drop',
  `remito_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `cliente_id` (`cliente_id`),
  KEY `factura_id` (`factura_id`),
  KEY `idx_pedido_reparto` (`en_reparto_fecha`,`orden_reparto_manual`),
  KEY `fk_pedido_zona` (`zona_id`),
  KEY `fk_pedido_remito` (`remito_id`),
  CONSTRAINT `fk_pedido_remito` FOREIGN KEY (`remito_id`) REFERENCES `remito` (`id`) ON DELETE SET NULL,
  CONSTRAINT `fk_pedido_zona` FOREIGN KEY (`zona_id`) REFERENCES `zona` (`id`) ON DELETE SET NULL,
  CONSTRAINT `fk_pedido_zona_rep` FOREIGN KEY (`zona_id`) REFERENCES `zona` (`id`) ON DELETE SET NULL,
  CONSTRAINT `pedido_ibfk_1` FOREIGN KEY (`cliente_id`) REFERENCES `cliente` (`id`),
  CONSTRAINT `pedido_ibfk_2` FOREIGN KEY (`factura_id`) REFERENCES `factura` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `pedido`
--

LOCK TABLES `pedido` WRITE;
/*!40000 ALTER TABLE `pedido` DISABLE KEYS */;
/*!40000 ALTER TABLE `pedido` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `pedido_detalle`
--

DROP TABLE IF EXISTS `pedido_detalle`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `pedido_detalle` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `pedido_id` int(11) NOT NULL,
  `producto_id` int(11) NOT NULL,
  `cantidad` decimal(10,3) NOT NULL,
  `precio_unitario` decimal(12,2) NOT NULL,
  `subtotal` decimal(12,2) NOT NULL,
  `lista_precio` int(11) DEFAULT 1,
  PRIMARY KEY (`id`),
  KEY `pedido_id` (`pedido_id`),
  KEY `producto_id` (`producto_id`),
  CONSTRAINT `pedido_detalle_ibfk_1` FOREIGN KEY (`pedido_id`) REFERENCES `pedido` (`id`) ON DELETE CASCADE,
  CONSTRAINT `pedido_detalle_ibfk_2` FOREIGN KEY (`producto_id`) REFERENCES `producto` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `pedido_detalle`
--

LOCK TABLES `pedido_detalle` WRITE;
/*!40000 ALTER TABLE `pedido_detalle` DISABLE KEYS */;
/*!40000 ALTER TABLE `pedido_detalle` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `pedido_detalle_peso`
--

DROP TABLE IF EXISTS `pedido_detalle_peso`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `pedido_detalle_peso` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `pedido_detalle_id` int(11) NOT NULL,
  `numero_unidad` int(11) NOT NULL,
  `peso` decimal(10,3) NOT NULL DEFAULT 0.000,
  `subtotal` decimal(10,2) NOT NULL DEFAULT 0.00,
  `fecha_creacion` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_detalle_unidad` (`pedido_detalle_id`,`numero_unidad`),
  KEY `idx_pedido_detalle` (`pedido_detalle_id`),
  CONSTRAINT `pedido_detalle_peso_ibfk_1` FOREIGN KEY (`pedido_detalle_id`) REFERENCES `pedido_detalle` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `pedido_detalle_peso`
--

LOCK TABLES `pedido_detalle_peso` WRITE;
/*!40000 ALTER TABLE `pedido_detalle_peso` DISABLE KEYS */;
/*!40000 ALTER TABLE `pedido_detalle_peso` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `presupuesto`
--

DROP TABLE IF EXISTS `presupuesto`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `presupuesto` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `punto_venta` int(11) NOT NULL DEFAULT 1,
  `numero_secuencial` int(11) NOT NULL,
  `numero_completo` varchar(30) NOT NULL,
  `fecha_emision` date NOT NULL,
  `fecha_validez` date NOT NULL,
  `validez_dias` int(11) NOT NULL DEFAULT 15,
  `cliente_id` int(11) NOT NULL,
  `subtotal` decimal(12,2) NOT NULL DEFAULT 0.00,
  `iva` decimal(12,2) NOT NULL DEFAULT 0.00,
  `total` decimal(12,2) NOT NULL DEFAULT 0.00,
  `estado` varchar(20) NOT NULL DEFAULT 'borrador',
  `factura_id` int(11) DEFAULT NULL,
  `fecha_conversion` datetime DEFAULT NULL,
  `observaciones` text DEFAULT NULL,
  `usuario_creacion` varchar(100) DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT current_timestamp(),
  `updated_at` datetime NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_presupuesto_numero_ff` (`punto_venta`,`numero_secuencial`),
  KEY `idx_presupuesto_fecha_ff` (`fecha_emision`),
  KEY `idx_presupuesto_cliente_ff` (`cliente_id`),
  KEY `idx_presupuesto_estado_ff` (`estado`),
  KEY `idx_presupuesto_validez_ff` (`fecha_validez`),
  KEY `fk_presupuesto_factura_ff` (`factura_id`),
  CONSTRAINT `fk_presupuesto_cliente_ff` FOREIGN KEY (`cliente_id`) REFERENCES `cliente` (`id`) ON UPDATE CASCADE,
  CONSTRAINT `fk_presupuesto_factura_ff` FOREIGN KEY (`factura_id`) REFERENCES `factura` (`id`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `chk_presupuesto_estado_ff` CHECK (`estado` in ('borrador','enviado','aceptado','rechazado','convertido','vencido'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `presupuesto`
--

LOCK TABLES `presupuesto` WRITE;
/*!40000 ALTER TABLE `presupuesto` DISABLE KEYS */;
/*!40000 ALTER TABLE `presupuesto` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `presupuesto_detalle`
--

DROP TABLE IF EXISTS `presupuesto_detalle`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `presupuesto_detalle` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `presupuesto_id` int(11) NOT NULL,
  `producto_id` int(11) DEFAULT NULL,
  `codigo_producto` varchar(50) DEFAULT NULL,
  `descripcion` varchar(255) NOT NULL,
  `cantidad` decimal(10,3) NOT NULL DEFAULT 1.000,
  `precio_unitario` decimal(12,2) NOT NULL DEFAULT 0.00,
  `iva_alicuota` decimal(5,2) NOT NULL DEFAULT 21.00,
  `subtotal` decimal(12,2) NOT NULL DEFAULT 0.00,
  `es_pesable` tinyint(1) NOT NULL DEFAULT 0,
  `orden` int(11) NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`),
  KEY `idx_presudet_presu_ff` (`presupuesto_id`),
  KEY `idx_presudet_producto_ff` (`producto_id`),
  CONSTRAINT `fk_presudet_presupuesto_ff` FOREIGN KEY (`presupuesto_id`) REFERENCES `presupuesto` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_presudet_producto_ff` FOREIGN KEY (`producto_id`) REFERENCES `producto` (`id`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `presupuesto_detalle`
--

LOCK TABLES `presupuesto_detalle` WRITE;
/*!40000 ALTER TABLE `presupuesto_detalle` DISABLE KEYS */;
/*!40000 ALTER TABLE `presupuesto_detalle` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `producto`
--

DROP TABLE IF EXISTS `producto`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `producto` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `codigo` varchar(50) NOT NULL,
  `nombre` varchar(200) NOT NULL,
  `descripcion` text DEFAULT NULL,
  `precio` decimal(10,2) NOT NULL,
  `stock` decimal(10,3) DEFAULT 0.000,
  `stock_minimo` decimal(10,3) DEFAULT 0.000,
  `categoria` varchar(100) DEFAULT NULL,
  `iva` decimal(5,2) DEFAULT 21.00,
  `activo` tinyint(1) DEFAULT 1,
  `fecha_creacion` timestamp NOT NULL DEFAULT current_timestamp(),
  `fecha_modificacion` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `costo` decimal(10,2) DEFAULT 0.00,
  `margen` decimal(10,2) DEFAULT 0.00,
  `es_combo` tinyint(1) DEFAULT 0,
  `producto_base_id` int(11) DEFAULT NULL,
  `cantidad_combo` decimal(8,3) DEFAULT 1.000,
  `precio_unitario_base` decimal(10,2) DEFAULT NULL,
  `descuento_porcentaje` decimal(5,2) DEFAULT 0.00,
  `acceso_rapido` tinyint(1) DEFAULT 0,
  `orden_acceso_rapido` int(11) DEFAULT 0,
  `tiene_ofertas_volumen` tinyint(1) DEFAULT 0,
  `producto_base_2_id` int(11) DEFAULT NULL,
  `cantidad_combo_2` decimal(10,3) DEFAULT 0.000,
  `producto_base_3_id` int(11) DEFAULT NULL,
  `cantidad_combo_3` decimal(10,3) DEFAULT 0.000,
  `margen2` decimal(5,2) DEFAULT NULL,
  `margen3` decimal(5,2) DEFAULT NULL,
  `margen4` decimal(5,2) DEFAULT NULL,
  `margen5` decimal(5,2) DEFAULT NULL,
  `precio2` decimal(10,2) DEFAULT NULL,
  `precio3` decimal(10,2) DEFAULT NULL,
  `precio4` decimal(10,2) DEFAULT NULL,
  `precio5` decimal(10,2) DEFAULT NULL,
  `es_pesable` tinyint(1) DEFAULT 0,
  `codigo_barras` varchar(50) DEFAULT NULL,
  `fecha_actualizacion_precio` date DEFAULT NULL,
  `imagen_url` varchar(500) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `codigo` (`codigo`),
  KEY `idx_codigo` (`codigo`),
  KEY `idx_nombre` (`nombre`),
  KEY `idx_categoria` (`categoria`),
  KEY `idx_es_combo` (`es_combo`),
  KEY `idx_producto_base` (`producto_base_id`),
  KEY `fk_producto_base_2` (`producto_base_2_id`),
  KEY `fk_producto_base_3` (`producto_base_3_id`),
  KEY `idx_stock_minimo` (`stock_minimo`),
  CONSTRAINT `fk_producto_base` FOREIGN KEY (`producto_base_id`) REFERENCES `producto` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_producto_base_2` FOREIGN KEY (`producto_base_2_id`) REFERENCES `producto` (`id`),
  CONSTRAINT `fk_producto_base_3` FOREIGN KEY (`producto_base_3_id`) REFERENCES `producto` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=207 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `producto`
--

LOCK TABLES `producto` WRITE;
/*!40000 ALTER TABLE `producto` DISABLE KEYS */;
INSERT INTO `producto` VALUES (1,'102','CHICLE FIERITA RECARGADO MENTA X50U',NULL,5485.74,16.000,0.000,'chicles',21.00,1,'2026-05-12 22:35:58','2026-06-03 09:58:45',4533.67,21.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-01','/static/productos_img/CHICLE FIERITA RECARGADO MENTA X50U (cod 102 ).jpeg'),(2,'103','CHICLE FIERITA RECARGADO TUTTI FRUTTI X50U',NULL,3020.00,2.000,0.000,'chicles',21.00,1,'2026-05-12 22:35:58','2026-06-05 20:51:11',2516.67,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'/static/productos_img/CHICLE FIERITA RECARGADO TUTTI FRUTTI X50U (cod 103 ).jpeg'),(3,'104','CHICLE FIERITA MENTA X100U',NULL,2860.00,3.000,0.000,'chicles',21.00,1,'2026-05-12 22:35:58','2026-06-04 15:36:59',2383.33,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'/static/productos_img/CHICLE FIERITA MENTA X100U (cod 104 ).jpeg'),(4,'105','CHICLE FIERITA TUTTI X100U',NULL,2860.00,3.000,0.000,'chicles',21.00,1,'2026-05-12 22:35:58','2026-06-05 22:30:13',2383.33,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'/static/productos_img/CHICLE FIERITA TUTTI X100U (cod 105 ).jpeg'),(5,'115','CHICLE OPEN CANDY MAESTROS DEL TERROR C/TATOO X 50',NULL,4092.00,0.000,0.000,'chicles',21.00,1,'2026-05-12 22:35:58','2026-06-03 09:58:45',3410.00,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'/static/productos_img/CHICLE OPEN CANDY MAESTROS DEL TERROR C TATOO X 50 (cod 115 ).jpeg'),(6,'140','BELDENT FRESH SPARKS MENTAx20u',NULL,11393.17,4.000,0.000,'chicles',21.00,1,'2026-05-12 22:35:58','2026-06-04 16:01:13',9494.31,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-02','/static/productos_img/BELDENT FRESH SPARKS MENTAx20u (cod 140 ).jpeg'),(7,'141','BELDENT FRESH SPARKS MTA.Fx20u',NULL,12249.84,2.000,0.000,'chicles',21.00,1,'2026-05-12 22:35:58','2026-06-04 16:01:13',9449.85,29.63,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-02','/static/productos_img/BELDENT FRESH SPARKS MTA.Fx20u (cod 141 ).jpeg'),(8,'142','BELDENT FRESH SPARKS MENTOx20u',NULL,12599.55,2.000,0.000,'chicles',21.00,1,'2026-05-12 22:35:58','2026-06-04 13:55:02',10525.06,19.71,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-05-12','/static/productos_img/BELDENT FRESH SPARKS MENTOx20u (cod 142 ).jpeg'),(9,'143','BELDENT FRESH SPARKS FRUTIx20u',NULL,12600.30,5.000,0.000,'chicles',21.00,1,'2026-05-12 22:35:58','2026-06-04 13:54:36',10534.49,19.61,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-05-12','/static/productos_img/BELDENT FRESH SPARKS FRUTIx20u (cod 143 ).jpeg'),(10,'200','GOMITAS YUMMY OSITOS ACIDOS X 500 GR',NULL,4954.59,3.000,0.000,'gomitas',21.00,1,'2026-05-12 22:35:58','2026-06-05 22:40:31',3811.22,30.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04','/static/productos_img/GOMITAS YUMMY OSITOS ACIDOS X 500 GR (cod 200 ).jpeg'),(11,'201','GOMITAS YUMMY OSITOS X 500 GR',NULL,4954.59,4.000,0.000,'gomitas',21.00,1,'2026-05-12 22:35:58','2026-06-04 12:33:18',3811.22,30.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04','/static/productos_img/GOMITAS YUMMY OSITOS X 500 GR (cod 201 ).jpeg'),(12,'202','GOMITAS YUMMY FRUTILLITAS CON CREMA X 500 GR',NULL,4954.59,5.000,0.000,'gomitas',21.00,1,'2026-05-12 22:35:58','2026-06-04 12:43:48',3811.22,30.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04','/static/productos_img/GOMITAS YUMMY FRUTILLITAS CON CREMA X 500 GR (cod 202 ).jpeg'),(13,'203','GOMITAS YUMMY 100 PIES ACIDAS X 500 GR',NULL,4954.59,1.000,0.000,'gomitas',21.00,1,'2026-05-12 22:35:58','2026-06-04 12:43:48',3811.22,30.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04','/static/productos_img/GOMITAS YUMMY 100 PIES ACIDAS X 500 GR (cod 203 ).jpeg'),(14,'204','GOMITAS YUMMY SANDIA  X500GR',NULL,4954.59,1.000,0.000,'gomitas',21.00,1,'2026-05-12 22:35:58','2026-06-05 22:40:31',3811.22,30.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04','/static/productos_img/GOMITAS YUMMY SANDIA X500GR (cod 204 ).jpeg'),(15,'205','YUMMY BANANITAS BOLSA....x500g',NULL,4954.59,0.000,0.000,'gomitas',21.00,1,'2026-05-12 22:35:58','2026-06-04 12:43:48',3811.22,30.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04','/static/productos_img/YUMMY BANANITAS BOLSA....x500g (cod 205 ).jpeg'),(16,'206','GOMITAS YUMMY MORITAS X500G',NULL,4954.59,2.000,0.000,'gomitas',21.00,1,'2026-05-12 22:35:58','2026-06-05 22:40:31',3811.22,30.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04','/static/productos_img/GOMITAS YUMMY MORITAS X500G (cod 206 ).jpeg'),(17,'207','GOMITAS YUMMY DIENTITOS X 500 GR',NULL,4954.59,6.000,0.000,'gomitas',21.00,1,'2026-05-12 22:35:58','2026-06-05 12:31:33',3811.22,30.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04','/static/productos_img/GOMITAS YUMMY DIENTITOS X 500 GR (cod 207 ).jpeg'),(18,'208','YUMMY HUEVOS FRITOS BOLSA.x500g',NULL,4954.59,0.000,0.000,'gomitas',21.00,1,'2026-05-12 22:35:58','2026-06-05 12:31:33',3811.22,30.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04','/static/productos_img/YUMMY HUEVOS FRITOS BOLSA.x500g (cod 208 ).jpeg'),(19,'209','YUMMY BOTELLITAS BOLSA...x500g',NULL,4954.59,3.000,0.000,'gomitas',21.00,1,'2026-05-12 22:35:58','2026-06-04 12:36:30',3811.22,30.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04','/static/productos_img/YUMMY BOTELLITAS BOLSA...x500g (cod 209 ).jpeg'),(20,'220','YUMMY ANIMALITOS X 12 UND',NULL,5209.81,4.000,0.000,'gomitas',21.00,1,'2026-05-12 22:35:58','2026-06-03 09:58:45',4407.25,18.21,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-05-12','/static/productos_img/YUMMY ANIMALITOS X 12 UND (cod 220 ).jpeg'),(21,'221','YUMMY DINO X 12 UND',NULL,5210.13,2.000,0.000,'gomitas',21.00,1,'2026-05-12 22:35:58','2026-06-04 11:52:12',4411.25,18.11,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-05-12','/static/productos_img/YUMMY DINO X 12 UND (cod 221 ).jpeg'),(22,'222','YUMMY FRUTITAS X 12 UND',NULL,5209.99,0.000,0.000,'gomitas',21.00,1,'2026-05-12 22:35:58','2026-06-03 09:58:45',4415.25,18.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-05-12','/static/productos_img/YUMMY FRUTITAS X 12 UND (cod 222 ).jpeg'),(23,'223','YUMMY OSITOS ACIDOS X 12 UND',NULL,5209.88,4.000,0.000,'gomitas',21.00,1,'2026-05-12 22:35:58','2026-06-03 09:58:45',4419.27,17.89,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-05-12','/static/productos_img/YUMMY OSITOS ACIDOS X 12 UND (cod 223 ).jpeg'),(24,'224','YUMMY OSITOS X 12 UND',NULL,5210.19,2.000,0.000,'gomitas',21.00,1,'2026-05-12 22:35:58','2026-06-04 11:52:12',4423.29,17.79,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-05-12','/static/productos_img/YUMMY OSITOS X 12 UND (cod 224 ).jpeg'),(25,'225','YUMMY PECECITOS X 12 UND',NULL,5210.06,3.000,0.000,'gomitas',21.00,1,'2026-05-12 22:35:58','2026-06-04 11:52:12',4427.31,17.68,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-05-12','/static/productos_img/YUMMY PECECITOS X 12 UND (cod 225 ).jpeg'),(26,'226','YUMMY PIECITOS ACIDOS X 12 UND',NULL,5209.94,4.000,0.000,'gomitas',21.00,1,'2026-05-12 22:35:58','2026-06-03 09:58:45',4431.35,17.57,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-05-12','/static/productos_img/YUMMY PIECITOS ACIDOS X 12 UND (cod 226 ).jpeg'),(27,'230','GOMA FANTASIA MISKY .......x1k',NULL,8850.13,3.000,0.000,'gomitas',21.00,1,'2026-05-12 22:35:58','2026-06-05 22:40:31',6807.79,30.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04','/static/productos_img/GOMA FANTASIA MISKY .......x1k (cod 230 ).jpeg'),(28,'231','GOMA JELLY ROLL MISKY......x1k',NULL,8850.13,3.000,0.000,'gomitas',21.00,1,'2026-05-12 22:35:58','2026-06-04 12:43:48',6807.79,30.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04','/static/productos_img/GOMA JELLY ROLL MISKY......x1k (cod 231 ).jpeg'),(29,'232','GOMA EUCALIPTUS MISKY......x1k',NULL,8850.13,3.000,0.000,'gomitas',21.00,1,'2026-05-12 22:35:58','2026-06-04 15:46:13',6807.79,30.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04','/static/productos_img/GOMA EUCALIPTUS MISKY......x1k (cod 232 ).jpeg'),(30,'240','GOMAS LA PIÑATA HUESOS ACIDOS X 700 GR',NULL,5119.87,0.000,0.000,'gomitas',21.00,1,'2026-05-12 22:35:58','2026-06-04 13:34:35',4370.73,17.14,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-05-12','/static/productos_img/GOMAS LA PIÑATA HUESOS ACIDOS X 700 GR (cod 240 ).jpeg'),(31,'241','GOMAS LA PIÑATA ANILLOS X 700 GR',NULL,5120.18,12.000,0.000,'gomitas',21.00,1,'2026-05-12 22:35:58','2026-06-03 09:58:45',4374.73,17.04,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-05-12','/static/productos_img/GOMAS LA PIÑATA ANILLOS X 700 GR (cod 241 ).jpeg'),(32,'250','GOMA BULL DOG.REGALIZ SANDIA CJAx12u',NULL,3200.04,0.000,0.000,'gomitas',21.00,1,'2026-05-12 22:35:58','2026-06-04 12:43:48',2736.71,16.93,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-05-12','/static/productos_img/GOMA BULL DOG.REGALIZ SANDIA CJAx12u (cod 250 ).jpeg'),(33,'251','GOMA BULL DOG.REGALIZ FRUT.CJAx12u',NULL,3199.96,8.000,0.000,'gomitas',21.00,1,'2026-05-12 22:35:58','2026-06-05 12:31:33',2739.22,16.82,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-05-12','/static/productos_img/GOMA BULL DOG.REGALIZ FRUT.CJAx12u (cod 251 ).jpeg'),(34,'252','GOMA BULL DOG.REGALIZ TUTTI F.CJAx12u',NULL,3199.88,7.000,0.000,'gomitas',21.00,1,'2026-05-12 22:35:58','2026-06-05 12:31:33',2741.74,16.71,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-05-12','/static/productos_img/GOMA BULL DOG.REGALIZ TUTTI F.CJAx12u (cod 252 ).jpeg'),(35,'253','GOMA BULL DOG.REGALIZ FRAMB.CJAx12u',NULL,3200.08,8.000,0.000,'gomitas',21.00,1,'2026-05-12 22:35:58','2026-06-05 12:31:33',2744.26,16.61,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-05-12','/static/productos_img/GOMA BULL DOG.REGALIZ FRAMB.CJAx12u (cod 253 ).jpeg'),(36,'254','ROLLO GOMITA BILLIKEN FRUTx12u',NULL,4160.00,4.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-03 09:58:45',3570.82,16.50,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'/static/productos_img/ROLLO GOMITA BILLIKEN FRUTx12u (cod 254 ).jpeg'),(37,'260','(12ux35g)GOMA MISKY ROLL......',NULL,3839.90,3.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-04 11:57:08',3299.17,16.39,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-03','/static/productos_img/(12ux35g)GOMA MISKY ROLL...... (cod 260 ).jpeg'),(38,'266','MOGUL MORAS X 500G',NULL,5446.63,6.000,0.000,'gomitas',21.00,1,'2026-05-12 22:35:58','2026-06-04 12:11:20',4683.66,16.29,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-01','/static/productos_img/MOGUL MORAS X 500G (cod 266 ).jpeg'),(39,'267','MOGUL DIENTES X 500G',NULL,5441.48,12.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-04 12:11:20',4683.66,16.18,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-01','/static/productos_img/MOGUL DIENTES X 500G (cod 267 ).jpeg'),(40,'268','MOGUL FRUTILLAS CON CREMA X 500G',NULL,5436.32,12.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-03 09:58:45',4683.66,16.07,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-01','/static/productos_img/MOGUL FRUTILLAS CON CREMA X 500G (cod 268 ).jpeg'),(41,'269','MOGUL EXTREME SANDIA  X 500G',NULL,6800.00,4.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-03 09:58:45',5863.87,15.96,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'/static/productos_img/MOGUL EXTREME SANDIA X 500G (cod 269 ).jpeg'),(42,'270','MOGUL EXTREME LADRILLOS X 500G',NULL,6800.00,19.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-04 12:11:20',5869.30,15.86,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'/static/productos_img/MOGUL EXTREME LADRILLOS X 500G (cod 270 ).jpeg'),(43,'271','MOGUL EXTREME LADRILLOS MIX FRUTAL X 500G',NULL,6800.00,6.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-04 12:11:20',5874.73,15.75,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'/static/productos_img/MOGUL EXTREME LADRILLOS MIX FRUTAL X 500G (cod 271 ).jpeg'),(44,'272','MOGUL EXTREME TUBITOS FRUTILLA  X 500G',NULL,6800.00,28.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-03 09:58:45',5880.17,15.64,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'/static/productos_img/MOGUL EXTREME TUBITOS FRUTILLA X 500G (cod 272 ).jpeg'),(45,'273','MOGUL EXTREME TUBITOS MIX FRUTAL X 500G',NULL,6800.00,23.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-03 09:58:45',5885.63,15.54,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'/static/productos_img/MOGUL EXTREME TUBITOS MIX FRUTAL X 500G (cod 273 ).jpeg'),(46,'274','MOGUL JELLY BEANS X 500G',NULL,6800.00,0.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-03 09:58:45',5891.09,15.43,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'/static/productos_img/MOGUL JELLY BEANS X 500G (cod 274 ).jpeg'),(47,'275','MOGUL EXTREME OSITOS X 500G',NULL,5401.20,6.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-03 09:58:45',4683.66,15.32,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-01','/static/productos_img/MOGUL EXTREME OSITOS X 500G (cod 275 ).jpeg'),(48,'281','GOMAS MOGUL COLA X 12 UNIDADES',NULL,5600.00,3.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-04 13:34:35',4860.51,15.21,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'/static/productos_img/GOMAS MOGUL COLA X 12 UNIDADES (cod 281 ).jpeg'),(49,'282','YUMMY OJITOS CAJA.....x360g',NULL,10996.00,2.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-03 09:58:45',9552.84,15.11,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'/static/productos_img/YUMMY OJITOS CAJA.....x360g (cod 282 ).jpeg'),(50,'283','CARAM.GOMA JELLY STICKS FRUT.x10u',NULL,1690.00,19.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-03 09:58:45',1469.57,15.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'/static/productos_img/CARAM.GOMA JELLY STICKS FRUT.x10u (cod 283 ).jpeg'),(51,'284','YUMMY ROLLO SURTIDOSx12u',NULL,4834.00,1.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-03 09:58:45',4028.33,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'/static/productos_img/YUMMY ROLLO SURTIDOSx12u (cod 284 ).jpeg'),(52,'285','GOMITA DOCILE MIX DULCE/ACIDO X500',NULL,3196.21,34.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-04 16:01:13',2461.46,29.85,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-02','/static/productos_img/GOMITA DOCILE MIX DULCE ACIDO.x500g (cod 285 ).jpeg'),(53,'302','MR.POPS EVOLUTION CEREZA..x24u',NULL,4900.00,13.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-06 16:44:30',4083.33,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'/static/productos_img/MR.POPS EVOLUTION CEREZA..x24u (cod 302 ).jpeg'),(54,'303','MR.POPS EVOLUT.BLUE BERRY.x24u',NULL,4900.00,4.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-03 23:27:55',4083.33,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'/static/productos_img/MR.POPS EVOLUT.BLUE BERRY.x24u (cod 303 ).jpeg'),(55,'304','MR.POPS EVOLUTION EXTREME.x24u',NULL,4900.00,3.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-03 09:58:45',4083.33,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'/static/productos_img/MR.POPS EVOLUTION EXTREME.x24u (cod 304 ).jpeg'),(56,'305','MR.POPS ARQUIT.FTAL.......x50u',NULL,6600.00,6.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-05 22:40:31',5500.00,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'/static/productos_img/MR.POPS ARQUIT.FTAL.......x50u (cod 305 ).jpeg'),(57,'307','CHUPETIN MAST. TATOO FRUTILLA X50U',NULL,6320.00,4.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-03 09:58:45',5266.67,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'/static/productos_img/CHUPETIN MAST. TATOO FRUTILLA X50U (cod 307 ).jpeg'),(58,'308','CHUPETIN MAST. TATOO TUTTI FRUT X50U',NULL,6320.00,3.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-03 09:58:45',5266.67,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'/static/productos_img/CHUPETIN MAST. TATOO TUTTI FRUT X50U (cod 308 ).jpeg'),(59,'309','CHUPETIN MASTICABLE PINTA LENGUA X 50UND',NULL,4840.00,5.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-03 09:58:45',4033.33,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'/static/productos_img/CHUPETIN MASTICABLE PINTA LENGUA X 50UND (cod 309 ).jpeg'),(60,'310','CHUPETIN PUSH POP.........x20u',NULL,9900.00,4.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-04 13:05:26',8250.00,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'/static/productos_img/CHUPETIN PUSH POP.........x20u (cod 310 ).jpeg'),(61,'311','CHUPETIN PICO-DULCE.......x48u',NULL,10780.00,5.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-04 15:41:34',8983.33,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'/static/productos_img/CHUPETIN PICO-DULCE.......x48u (cod 311 ).jpeg'),(62,'312','CRAZY BULL DOG CHUPETIN + POLVO X 10 UND',NULL,5800.00,6.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-03 09:58:45',4833.33,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'/static/productos_img/CRAZY BULL DOG CHUPETIN + POLVO X 10 UND (cod 312 ).jpeg'),(63,'400','MASTICABLE SURTIDO MISKY X 800gs',NULL,6490.00,19.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-06 16:44:30',5408.33,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'/static/productos_img/MASTICABLE SURTIDO MISKY X 800gs (cod 400 ).jpeg'),(64,'402','(x32u)MAST.LENGUETAZO T.FRUTI...',NULL,6440.00,6.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-08 10:34:46',5366.67,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'/static/productos_img/(x32u)MAST.LENGUETAZO T.FRUTI... (cod 402 ).jpeg'),(65,'404','PALITO DE LA SELVA.......x660g',NULL,8400.00,10.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-03 23:27:55',7000.00,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'/static/productos_img/PALITO DE LA SELVA.......x660g (cod 404 ).jpeg'),(66,'406','CARAM.FLYNN PAFF TUTTI....x70u',NULL,6600.00,13.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-05 12:31:33',5500.00,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'/static/productos_img/CARAM.FLYNN PAFF TUTTI....x70u (cod 406 ).jpeg'),(67,'407','MASTICABLE BILLIKEN YOGURT',NULL,4330.00,17.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-04 15:36:59',3608.33,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'/static/productos_img/MASTICABLE BILLIKEN YOGURT (cod 407 ).jpeg'),(68,'408','MASTICABLE BULLDOG X 700G',NULL,5200.00,0.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-04 13:34:35',4333.33,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'/static/productos_img/MASTICABLE BULLDOG X 700G (cod 408 ).jpeg'),(69,'409','CARAM.MAST.DROPSY SELVA..x700g',NULL,5200.00,6.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-05 12:31:33',4333.33,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'/static/productos_img/CARAM.MAST.DROPSY SELVA..x700g (cod 409 ).jpeg'),(70,'28288','CAR.FLYNN PAFF TUTTI BOLSx504g',NULL,6370.00,11.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-03 09:58:46',5308.33,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'/static/productos_img/CAR.FLYNN PAFF TUTTI BOLSx504g (cod 28288 ).jpeg'),(71,'29508','MAST.RICOMAS FRUTIL/LIMONx280g',NULL,2140.00,6.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-03 09:58:46',1783.33,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'/static/productos_img/MAST.RICOMAS FRUTIL LIMONx280g (cod 29508 ).jpeg'),(72,'501','PASTILLAS BULL DOG UVA X12U',NULL,4300.00,2.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-05 12:31:33',3583.33,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'/static/productos_img/PASTILLAS BULL DOG UVA X12U (cod 501 ).jpeg'),(73,'504','PASTILLAS BULL DOG MIX TUITTI FRUTTI ACIDA X12U',NULL,4300.00,6.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-05 12:31:33',3583.33,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'/static/productos_img/PASTILLAS BULL DOG MIX TUITTI FRUTTI ACIDA X12U (cod 504 ).jpeg'),(74,'505','PASTILLAS BULL DOG SANDIA ACIDA X 12 UND',NULL,4300.00,2.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-05 12:31:33',3583.33,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'/static/productos_img/PASTILLAS BULL DOG SANDIA ACIDA X 12 UND (cod 505 ).jpeg'),(75,'506','PASTILLAS BULL DOG TUTTI FRUTTI  LIMONX 12 UND',NULL,4300.00,5.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-04 13:34:35',3583.33,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'/static/productos_img/PASTILLAS BULL DOG TUTTI FRUTTI LIMONX 12 UND (cod 506 ).jpeg'),(76,'507','PASTILLAS BULL DOG LIMON EXTREME X12 UND',NULL,4300.00,8.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-05 12:31:33',3583.33,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'/static/productos_img/PASTILLAS BULL DOG LIMON EXTREME X12 UND (cod 507 ).jpeg'),(77,'508','LA YAPA...................x36u',NULL,10490.00,2.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-03 09:58:45',8741.67,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'/static/productos_img/LA YAPA...................x36u (cod 508 ).jpeg'),(78,'509','PASTILLA PUNCH X60U',NULL,4710.00,4.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-03 09:58:46',3925.00,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'/static/productos_img/PASTILLA PUNCH X60U (cod 509 ).jpeg'),(79,'511','MENTITAS MENTA X 12 UND',NULL,4100.00,13.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-03 09:58:46',3416.67,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'/static/productos_img/MENTITAS MENTA X 12 UND (cod 511 ).jpeg'),(80,'512','MENTITAS FRUTAL X 12 UND',NULL,4100.00,13.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-05 12:31:33',3416.67,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'/static/productos_img/MENTITAS FRUTAL X 12 UND (cod 512 ).jpeg'),(81,'513','MENTITAS KIDS TUTTI FRUTTI X12U',NULL,4100.00,12.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-05 12:31:33',3416.67,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'/static/productos_img/MENTITAS KIDS TUTTI FRUTTI X12U (cod 513 ).jpeg'),(82,'514','MENTITAS KIDS DULCE DE LECHE X 12 UND',NULL,4100.00,13.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-05 12:31:33',3416.67,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'/static/productos_img/MENTITAS KIDS DULCE DE LECHE X 12 UND (cod 514 ).jpeg'),(83,'526','MENTHO PLUS MENTOL........x12u',NULL,6400.00,4.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-03 09:58:46',5333.33,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'/static/productos_img/MENTHO PLUS MENTOL........x12u (cod 526 ).jpeg'),(84,'527','MENTHO PLUS STRONG........x12u',NULL,5440.40,12.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-04 16:06:31',4533.67,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-01','/static/productos_img/MENTHO PLUS STRONG........x12u (cod 527 ).jpeg'),(85,'528','MENTHO PLUS MENTA.........x12u',NULL,6400.00,3.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-03 09:58:46',5333.33,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'/static/productos_img/MENTHO PLUS MENTA.........x12u (cod 528 ).jpeg'),(86,'529','MENTHO PLUS CEREZA........x12u',NULL,5440.40,13.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-03 09:58:46',4533.67,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-01','/static/productos_img/MENTHO PLUS CEREZA........x12u (cod 529 ).jpeg'),(87,'530','MENTHO PLUS MIEL..........x12u',NULL,5440.40,10.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-04 16:06:31',4533.67,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-01','/static/productos_img/MENTHO PLUS MIEL..........x12u (cod 530 ).jpeg'),(88,'600','MARSHMALLOW GONGYS STICK CAJAx216g 18UNID',NULL,4200.00,1.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-03 09:58:46',3500.00,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'/static/productos_img/MARSHMALLOW GONGYS STICK CAJAx216g 18UNID (cod 600 ).jpeg'),(89,'601','(28g)MARSHMALLOW GONGYS FRUTIL',NULL,374.00,108.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-05 12:31:33',311.67,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'/static/productos_img/(28g)MARSHMALLOW GONGYS FRUTIL (cod 601 ).jpeg'),(90,'602','(28g)MARSHMALLOW GONGYS NUBECI',NULL,374.00,88.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-05 12:31:33',311.67,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'/static/productos_img/(28g)MARSHMALLOW GONGYS NUBECI (cod 602 ).jpeg'),(91,'603','(28g)MARSHMALLOW GONGYS.......',NULL,374.00,34.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-03 09:58:46',311.67,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'/static/productos_img/(28g)MARSHMALLOW GONGYS....... (cod 603 ).jpeg'),(92,'700','CHOC TOKKE C/LECHE Y MANI 62G',NULL,1860.00,0.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-05 22:30:13',1550.00,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'/static/productos_img/CHOC TOKKE C LECHE Y MANI 62G (cod 700 ).jpeg'),(93,'701','CHOC.TOKKE RELLE.D/LECHE..x72g',NULL,1860.00,23.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-05 22:30:13',1550.00,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'/static/productos_img/CHOC.TOKKE RELLE.D LECHE..x72g (cod 701 ).jpeg'),(94,'702','CHOCOLATE MISKY  NGRO x25g',NULL,791.25,160.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-06 16:44:30',608.65,30.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-02','/static/productos_img/CHOCOLATE MISKY NGRO x25g (cod 702 ).jpeg'),(95,'703','CHOCOLATE MISKY  BCO x25g',NULL,791.25,183.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-06 16:44:30',608.65,30.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-02','/static/productos_img/CHOCOLATE MISKY BCO x25g (cod 703 ).jpeg'),(96,'704','ROCKLETS 24 X 20GS',NULL,16960.00,10.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-05 12:31:33',14133.33,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'/static/productos_img/ROCKLETS 24 X 20GS (cod 704 ).jpeg'),(97,'705','CHOC. C/MANI COF. BLOCK 20X38GS',NULL,1235.00,114.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-05 12:31:33',1029.17,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'/static/productos_img/CHOC. C MANI COF. BLOCK 20X38GS (cod 705 ).jpeg'),(98,'706','BOCADITO NEVARES DUL.D/LECx15u',NULL,3600.00,16.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-04 13:34:35',3000.00,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'/static/productos_img/BOCADITO NEVARES DUL.D LECx15u (cod 706 ).jpeg'),(99,'707','CREMA KROOMY SURTIDOS ( 48u )',NULL,8470.00,9.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-05 12:31:33',7058.33,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'/static/productos_img/CREMA KROOMY SURTIDOS ( 48u ) (cod 707 ).jpeg'),(100,'708','BONOBON OBLEA LECHE....20ux30g',NULL,736.75,289.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-05 22:40:31',613.96,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-01','/static/productos_img/BONOBON OBLEA LECHE....20ux30g (cod 708 ).jpeg'),(101,'709','SMACK BAR X12U',NULL,4838.00,9.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-03 09:58:46',4031.67,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'/static/productos_img/SMACK BAR X12U (cod 709 ).jpeg'),(102,'710','OBLEA SMACK RELLENA X33g',NULL,299.00,180.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-04 13:34:35',249.17,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'/static/productos_img/OBLEA SMACK RELLENA X33g (cod 710 ).jpeg'),(103,'712','BOMBON SMACKX 30u',NULL,6490.00,3.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-04 13:34:35',5408.33,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'/static/productos_img/BOMBON SMACKX 30u (cod 712 ).jpeg'),(104,'713','BOMBONES BON O BON 30 X 15GS',NULL,11993.12,11.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-04 15:36:59',9994.27,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-01','/static/productos_img/BOMBONES BON O BON 30 X 15GS (cod 713 ).jpeg'),(105,'760','CHOC.NUGATON LECHE........x27g',NULL,663.00,144.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-03 09:58:46',552.50,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'/static/productos_img/CHOC.NUGATON LECHE........x27g (cod 760 ).jpeg'),(106,'761','MECANO....................x19g',NULL,721.00,42.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-05 12:31:33',600.83,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'/static/productos_img/MECANO....................x19g (cod 761 ).jpeg'),(107,'762','CREMA DUCREM DIP + CEREAL BAL 18unid',NULL,5700.00,0.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-03 09:58:46',4750.00,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'/static/productos_img/CREMA DUCREM DIP + CEREAL BAL 18unid (cod 762 ).jpeg'),(108,'763','CREMA DUCREM DIP + GRANULETI 18unid',NULL,5700.00,0.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-03 09:58:46',4750.00,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'/static/productos_img/CREMA DUCREM DIP + GRANULETI 18unid (cod 763 ).jpeg'),(109,'714','GUAYMALLEN TRIPLE CHOCOLATE',NULL,459.00,79.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-06 16:44:30',382.50,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'/static/productos_img/BONOBON OBLEA BLANCO....20ux30g (cod 714 ).jpeg'),(110,'715','GUAYMALLEN TRIPLE BLANCO',NULL,459.00,71.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-06 16:44:30',382.50,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'/static/productos_img/GUAYMALLEN TRIPLE BLANCO (cod 715 ).jpeg'),(111,'716','GUAYMALLEN SIMPLE BLANCO',NULL,288.00,462.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-06 16:44:30',240.00,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'/static/productos_img/GUAYMALLEN SIMPLE BLANCO (cod 716 ).jpeg'),(112,'717','GUAYMALLEN SIMPLE CHOCOLATE',NULL,288.00,494.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-05 22:30:13',240.00,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'/static/productos_img/GUAYMALLEN SIMPLE CHOCOLATE (cod 717 ).jpeg'),(113,'718','ALF FANTOCHE TRI.CHOCOLATEx85g',NULL,831.65,110.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-06 16:44:30',639.73,30.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-02','/static/productos_img/ALF FANTOCHE TRI.CHOCOLATEx85g (cod 718 ).jpeg'),(114,'719','ALF FANTOCHE TRIPLE BLANCO.x85g',NULL,831.65,24.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-06 16:44:30',639.73,30.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04','/static/productos_img/ALF FANTOCHE TRIPLE BLANCO.x85g (cod 719 ).jpeg'),(115,'720','ALFAJOR RASTA NEGRO X 18U',NULL,1110.00,0.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-05 22:30:13',925.00,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'/static/productos_img/ALFAJOR RASTA NEGRO X 18U (cod 720 ).jpeg'),(116,'721','ALFAJOR RASTA BLANCO X 18U',NULL,1110.00,10021.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-04 16:09:30',925.00,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'/static/productos_img/ALFAJOR RASTA BLANCO X 18U (cod 721 ).jpeg'),(117,'722','ALFAJOR GULA NEGRO X 18U',NULL,1190.00,37.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-04 16:09:30',991.67,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'/static/productos_img/ALFAJOR GULA NEGRO X 18U (cod 722 ).jpeg'),(118,'723','ALFAJOR GULA BLANCO X 18U',NULL,1190.00,4.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-04 16:09:30',991.67,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'/static/productos_img/ALFAJOR GULA BLANCO X 18U (cod 723 ).jpeg'),(119,'724','ALFAJOR GULA KING RALLADO X 18U',NULL,1190.00,14.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-04 11:57:08',991.67,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'/static/productos_img/ALFAJOR GULA KING RALLADO X 18U (cod 724 ).jpeg'),(120,'728','ALF FANTOCHE SUPER TRIPLE NEGx100g',NULL,771.29,285.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-03 09:58:46',642.74,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-02','/static/productos_img/ALF FANTOCHE SUPER TRIPLE NEGx100g (cod 728 ).jpeg'),(121,'729','ALFAJOR CHOCOTORTA 71,5',NULL,1154.32,153.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-05 22:40:31',961.93,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-01','/static/productos_img/ALFAJOR CHOCOTORTA 71,5 (cod 729 ).jpeg'),(122,'735','ALF BON O BON TRIPLE NEGROx60g',NULL,1154.32,141.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-05 22:40:31',961.93,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-01','/static/productos_img/ALF BON O BON TRIPLE NEGROx60g (cod 735 ).jpeg'),(123,'736','ALF COFLER BLOCK TRIPLE...x60g',NULL,1154.32,151.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-05 22:30:13',961.93,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-01','/static/productos_img/ALF COFLER BLOCK TRIPLE...x60g (cod 736 ).jpeg'),(124,'737','ALF OREO TRIPLE...........x55g',NULL,1432.60,0.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-03 09:58:46',1102.00,30.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-02','/static/productos_img/ALF OREO TRIPLE...........x55g (cod 737 ).jpeg'),(125,'738','ALF PEPITOS TRIPLE........x57g',NULL,1357.00,73.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-05 22:30:13',1130.83,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'/static/productos_img/ALF PEPITOS TRIPLE........x57g (cod 738 ).jpeg'),(126,'739','ALF RASTA MAICENA TRICOx100g',NULL,1670.00,9.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-03 09:58:46',1391.67,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'/static/productos_img/ALF RASTA MAICENA TRICOx100g (cod 739 ).jpeg'),(127,'740','ALF PESCADO RAUL SIMPLE NEGRO.x50g',NULL,693.31,221.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-05 22:30:13',537.20,29.06,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-02','/static/productos_img/ALF PESCADO RAUL SIMPLE NEGRO.x50g (cod 740 ).jpeg'),(128,'741','ALF PESCADO RAUL SIMPLE BLANCO.x50g',NULL,646.19,151.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-08 10:34:46',500.73,29.05,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-02','/static/productos_img/ALF PESCADO RAUL SIMPLE BLANCO.x50g (cod 741 ).jpeg'),(129,'751','TURRON MISKY',NULL,199.94,243.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-03 09:58:46',154.10,29.75,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-02','/static/productos_img/TURRON MISKY (cod 751 ).jpeg'),(130,'800','GIRASOL PIPAS..........30ux18g',NULL,7300.00,3.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-04 11:30:07',6083.33,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'/static/productos_img/GIRASOL PIPAS..........30ux18g (cod 800 ).jpeg'),(131,'801','GIRASOL PIPAS GIGANTES.12ux50g',NULL,7500.28,4.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-06 16:44:30',5769.45,30.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-02','/static/productos_img/GIRASOL PIPAS GIGANTES.12ux50g (cod 801 ).jpeg'),(132,'900','JUGO ARCOR POLVO NARANJA..x18u',NULL,4412.08,10.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-06 16:44:30',3676.73,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-01','/static/productos_img/JUGO ARCOR POLVO NARANJA..x18u (cod 900 ).jpeg'),(133,'901','JUGO ARCOR POLVO NARANJA DULCE..x18u',NULL,4700.00,0.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-03 09:58:46',3916.67,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'/static/productos_img/JUGO ARCOR POLVO NARANJA DULCE..x18u (cod 901 ).jpeg'),(134,'902','JUGO ARCOR POLVO NARAN.DURAZNOx18u',NULL,4700.00,7.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-03 09:58:46',3916.67,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'/static/productos_img/JUGO ARCOR POLVO NARAN.DURAZNOx18u (cod 902 ).jpeg'),(135,'903','JUGO ARCOR POLVO MANZANA..x18u',NULL,4700.00,13.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-03 23:27:55',3916.67,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'/static/productos_img/JUGO ARCOR POLVO MANZANA..x18u (cod 903 ).jpeg'),(136,'904','JUGO ARCOR POLVO MULTIFRUTx18u',NULL,4412.08,10.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-06 16:44:30',3676.73,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-01','/static/productos_img/JUGO ARCOR POLVO MULTIFRUTx18u (cod 904 ).jpeg'),(137,'905','JUGO ARCOR POLVO LIMONADA.x18u',NULL,4700.00,0.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-03 09:58:46',3916.67,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'/static/productos_img/JUGO ARCOR POLVO LIMONADA.x18u (cod 905 ).jpeg'),(138,'906','JUGO ARCOR POLVO FRUT/ANANA/BANANA',NULL,4412.08,11.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-03 23:27:55',3676.73,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-01','/static/productos_img/JUGO ARCOR POLVO FRUT ANANA BANANA (cod 906 ).jpeg'),(139,'907','JUGO ARCOR POLVO NARANJA BANANA.x18u',NULL,4412.08,12.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-03 09:58:46',3676.73,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-01','/static/productos_img/JUGO ARCOR POLVO NARANJA BANANA.x18u (cod 907 ).jpeg'),(140,'908','JUGO ARCOR POLVO ANANA.x18u',NULL,4700.00,28.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-03 09:58:46',3916.67,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'/static/productos_img/JUGO ARCOR POLVO ANANA.x18u (cod 908 ).jpeg'),(141,'909','JUGO ARCOR POLVO NARANJA MANGO.x18u',NULL,4412.08,15.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-03 09:58:46',3676.73,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-01','/static/productos_img/JUGO ARCOR POLVO NARANJA MANGO.x18u (cod 909 ).jpeg'),(142,'910','JUGO ARCOR POLVO POM.ROSADx18u',NULL,4700.00,0.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-03 09:58:46',3916.67,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'/static/productos_img/JUGO ARCOR POLVO POM.ROSADx18u (cod 910 ).jpeg'),(143,'911','JUGO ARCOR POLVO DURAZNO..x18u',NULL,4700.00,0.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-03 09:58:46',3916.67,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'/static/productos_img/JUGO ARCOR POLVO DURAZNO..x18u (cod 911 ).jpeg'),(144,'918','CERVEZA 361 PET............x1l',NULL,1567.33,104.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-03 09:58:46',1205.64,30.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-02','/static/productos_img/CERVEZA 361 PET............x1l (cod 918 ).jpeg'),(145,'931','BAGGIO DURAZNO...........x200m',NULL,530.02,0.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-04 15:46:13',407.83,29.96,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-02','/static/productos_img/BAGGIO DURAZNO...........x200m (cod 931 ).jpeg'),(146,'932','BAGGIO MANZANA...........x200m',NULL,530.02,0.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-03 09:58:46',407.83,29.96,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-02','/static/productos_img/BAGGIO MANZANA...........x200m (cod 932 ).jpeg'),(147,'933','BAGGIO NARANJA...........x200m',NULL,530.02,3.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-03 09:58:46',407.83,29.96,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-02','/static/productos_img/BAGGIO NARANJA...........x200m (cod 933 ).jpeg'),(148,'934','BAGGIO MULTIFRUTAL.......x200m',NULL,530.02,0.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-05 12:31:33',407.83,29.96,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-02','/static/productos_img/BAGGIO MULTIFRUTAL.......x200m (cod 934 ).jpeg'),(149,'937','LECHE CHOCOLATADA FANTOCHE.....x200m',NULL,928.00,0.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-03 09:58:46',773.33,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'/static/productos_img/LECHE CHOCOLATADA FANTOCHE.....x200m (cod 937 ).jpeg'),(150,'1000','MAGDAL DON SATUR REL.D/LEx250g',NULL,2090.00,0.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-03 09:58:46',1741.67,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'/static/productos_img/MAGDAL DON SATUR REL.D LEx250g (cod 1000 ).jpeg'),(151,'1001','MAGDAL DON SATUR VAINILLAx250g',NULL,2090.00,0.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-06 16:44:30',1741.67,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'/static/productos_img/MAGDAL DON SATUR VAINILLAx250g (cod 1001 ).jpeg'),(152,'1002','MAGDAL DON SATUR MARMOLADx250g',NULL,2090.00,4.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-06 16:44:30',1741.67,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'/static/productos_img/MAGDAL DON SATUR MARMOLADx250g (cod 1002 ).jpeg'),(153,'1003','MAGD DON SATUR CHOC/D/D/Lx250g',NULL,2090.00,11.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-06 16:44:30',1741.67,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'/static/productos_img/MAGD DON SATUR CHOC D D Lx250g (cod 1003 ).jpeg'),(154,'1004','MAGDAL DON SATUR C/CHIPS.x250g',NULL,2090.00,5.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-03 09:58:46',1741.67,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'/static/productos_img/MAGDAL DON SATUR C CHIPS.x250g (cod 1004 ).jpeg'),(155,'1010','DON SATUR BIZCOCH.GRASA x200g',NULL,1231.23,84.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-06 16:44:30',947.10,30.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04','/static/productos_img/DON SATUR BIZCOCH.GRASA x200g (cod 1010 ).jpeg'),(156,'1011','DON SATUR BIZCOCHO DULCE.x200g',NULL,1231.23,-17.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-04 22:17:18',947.10,30.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04','/static/productos_img/DON SATUR BIZCOCHO DULCE.x200g (cod 1011 ).jpeg'),(157,'1012','DON SATUR BIZCOCH.NEGRITOx200g',NULL,1231.23,31.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-04 15:46:13',947.10,30.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04','/static/productos_img/DON SATUR BIZCOCH.NEGRITOx200g (cod 1012 ).jpeg'),(158,'1014','GALL TRIO PEPAS..........x320g',NULL,1135.00,18.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-06 16:44:30',945.83,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'/static/productos_img/GALL TRIO PEPAS..........x320g (cod 1014 ).jpeg'),(159,'1015','GALL TRIO PEPAS C/CHIPS..x300g',NULL,1242.00,44.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-05 22:52:12',1035.00,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'/static/productos_img/GALL TRIO PEPAS C CHIPS..x300g (cod 1015 ).jpeg'),(160,'1017','GALL TRIO TRICHOC........x300g',NULL,1242.00,40.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-06 16:44:30',1035.00,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'/static/productos_img/GALL TRIO TRICHOC........x300g (cod 1017 ).jpeg'),(161,'1018','GALL TRIO GLASY..........x300g',NULL,1242.00,31.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-04 16:09:30',1035.00,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'/static/productos_img/GALL TRIO GLASY..........x300g (cod 1018 ).jpeg'),(162,'1022','.9 DE ORO GRASA',NULL,1195.68,67.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-06 16:44:30',919.26,30.07,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-02','/static/productos_img/.9 DE ORO GRASA (cod 1022 ).jpeg'),(163,'1023','.9 DE ORO AGRIDULCE',NULL,1195.68,50.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-04 15:41:34',919.26,30.07,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-02','/static/productos_img/.9 DE ORO AGRIDULCE (cod 1023 ).jpeg'),(164,'1024','.9 DE ORO AZUCARADO',NULL,1195.68,47.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-04 15:36:59',919.26,30.07,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-02','/static/productos_img/.9 DE ORO AZUCARADO (cod 1024 ).jpeg'),(165,'1029','VARIEDAD.................x390g',NULL,2620.00,31.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-03 09:58:46',2183.33,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'/static/productos_img/VARIEDAD.................x390g (cod 1029 ).jpeg'),(166,'1030','SURTIDO BAGLEY...........x400g',NULL,2530.00,80.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-04 15:34:39',2108.33,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'/static/productos_img/SURTIDO BAGLEY...........x400g (cod 1030 ).jpeg'),(167,'1031','GALL.DIVERSION SURTIDA...x400g',NULL,2360.00,88.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-04 15:34:40',1966.67,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'/static/productos_img/GALL.DIVERSION SURTIDA...x400g (cod 1031 ).jpeg'),(168,'1032','GALL LA PROVIDENCIA TRIP.x303g',NULL,1212.00,40.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-03 09:58:46',1010.00,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'/static/productos_img/GALL LA PROVIDENCIA TRIP.x303g (cod 1032 ).jpeg'),(169,'960','MANI TARRO CERVECERO ORIGINAL',NULL,1520.00,0.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-04 22:58:59',1013.33,50.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04','/static/productos_img/MANI TARRO CERVECERO ORIGINAL (cod 960 ).jpeg'),(170,'961','MANI TARRO CERVECERO PIZZA',NULL,1520.00,1.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-04 22:59:32',1013.33,50.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04','/static/productos_img/MANI TARRO CERVECERO PIZZA (cod 961 ).jpeg'),(171,'962','MANI TARRO CERVECERO JAMON',NULL,1520.00,1.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-04 22:59:57',1013.33,50.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04','/static/productos_img/MANI TARRO CERVECERO JAMON (cod 962 ).jpeg'),(172,'963','MANI TARRO  CERVECERO SALAME',NULL,1520.00,6.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-06 16:44:30',1013.33,50.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04','/static/productos_img/MANI TARRO CERVECERO SALAME (cod 963 ).jpeg'),(173,'964','MANI TARRO CERVECERO QUESO',NULL,1520.00,10.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-06 16:44:30',1013.33,50.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04','/static/productos_img/MANI TARRO CERVECERO QUESO (cod 964 ).jpeg'),(174,'965','MANI TARRO CERVECERO PROVENZAL',NULL,1520.00,1.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-05 13:22:46',1013.33,50.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04','/static/productos_img/MANI TARRO CERVECERO PROVENZAL (cod 965 ).jpeg'),(175,'968','MANI TARRO CON PIEL',NULL,1520.00,16.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-05 13:22:46',1013.33,50.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04','/static/productos_img/MANI TARRO CON PIEL (cod 968 ).jpeg'),(176,'969','MANI TARRO SIN PIEL',NULL,1520.00,13.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-05 13:22:46',1013.33,50.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04','/static/productos_img/MANI TARRO SIN PIEL (cod 969 ).jpeg'),(177,'970','MANI CON CASCARA',NULL,1520.00,40.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-04 23:02:52',1013.33,50.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04','/static/productos_img/MANI CON CASCARA (cod 970 ).jpeg'),(178,'972','MANI TARRO SIN PIEL \"SIN SAL\"',NULL,1520.00,9.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-04 23:02:15',1013.33,50.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04','/static/productos_img/MANI TARRO SIN PIEL SIN SAL (cod 972 ).jpeg'),(179,'980','PAPAS FRITAS COPETIN PEÑA \"1KG\"',NULL,8900.00,0.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-05 22:52:12',7416.67,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'/static/productos_img/PAPAS FRITAS COPETIN PEÑA 1KG (cod 980 ).jpeg'),(180,'1100','PAPEL DRPIN CELLULOSE....',NULL,638.00,53.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-05 12:19:53',531.67,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'/static/productos_img/PAPEL DRPIN CELLULOSE.... (cod 1100 ).jpeg'),(181,'1120','ENC COCINA CANDELA CLASICO x25',NULL,7300.00,8.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-04 13:05:27',6083.33,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'/static/productos_img/ENC COCINA CANDELA CLASICO x25 (cod 1120 ).jpeg'),(182,'1121','ENC COCINA ECONOMICO TRANSPARENTE x 25 unid',NULL,6720.00,7.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-03 09:58:46',5600.00,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'/static/productos_img/ENC COCINA ECONOMICO TRANSPARENTE x 25 unid (cod 1121 ).jpeg'),(183,'2222','PASTILLAS BULL DOG MIX (((SURTIDAS))) X12U',NULL,4300.00,2.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-03 09:58:46',3583.33,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'/static/productos_img/PASTILLAS BULL DOG MIX (((SURTIDAS))) X12U (cod 2222 ).jpeg'),(184,'3333','GOMA BULL DOG.REGALIZ (((SURTIDAS))).CJAx12u',NULL,3200.00,1.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-05 22:30:13',2666.67,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'/static/productos_img/GOMA BULL DOG.REGALIZ (((SURTIDAS))).CJAx12u (cod 3333 ).jpeg'),(185,'4444','YUMMY  (((SURTIDAS))) X 12 UND',NULL,5011.00,2.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-03 09:58:46',4175.83,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'/static/productos_img/YUMMY (((SURTIDAS))) X 12 UND (cod 4444 ).jpeg'),(186,'1212','MENTITAS (((SURTIDAS))) X 12 UND',NULL,4100.00,0.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-03 09:58:46',3416.67,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'/static/productos_img/MENTITAS (((SURTIDAS))) X 12 UND (cod 1212 ).jpeg'),(187,'1111','MENTITAS KIDS (((SURTIDAS))) X 12 UND',NULL,4100.00,2.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-03 09:58:46',3416.67,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'/static/productos_img/MENTITAS KIDS (((SURTIDAS))) X 12 UND (cod 1111 ).jpeg'),(188,'6886','MENTHO PLUS ((SURTIDO))......x12u',NULL,6400.00,1.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-04 14:03:57',5333.33,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'/static/productos_img/MENTHO PLUS ((SURTIDO))......x12u (cod 6886 ).jpeg'),(189,'7076','BELDENT FRESH SPARKS SURTIDO',NULL,12600.00,3.000,0.000,NULL,21.00,1,'2026-05-12 22:35:58','2026-06-04 14:03:57',10500.00,20.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'/static/productos_img/BELDENT FRESH SPARKS SURTIDO (cod 7076 ).jpeg'),(190,'144','TOP LINE SEVEN MENTA',NULL,11786.60,10.000,100.000,'chicles',21.00,1,'2026-05-30 16:44:53','2026-06-04 16:01:13',8419.00,40.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-05-30','/static/productos_img/TOP LINE SEVEN MENTA (cod 144 ).jpeg'),(191,'276','MOGUL FRUTILLA ACIDA X 500',NULL,6557.12,6.000,1.000,'gomitas',21.00,1,'2026-05-30 17:09:07','2026-06-03 09:58:45',4683.66,40.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-01','/static/productos_img/MOGUL FRUTILLA ACIDA.....x500g (cod 276 ).jpeg'),(192,'936','LECHE CHOCOLATADA NAGGIO X200',NULL,949.99,0.000,0.000,NULL,21.00,1,'2026-06-01 00:40:55','2026-06-03 09:58:46',742.18,28.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-05-31','/static/productos_img/LECHE CHOCOLATADA BAGGIO.x200m (cod 936 ).jpeg'),(193,'711','BOMBON VAUQUITA',NULL,7890.54,0.000,0.000,NULL,21.00,1,'2026-06-01 00:42:19','2026-06-03 09:58:46',6164.00,28.01,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-05-31','/static/productos_img/BOMBON VAUQUITA X 30u (cod 711 ).jpeg'),(194,'742','ALF MINI TORTA AGUILA X69G',NULL,1346.70,172.000,0.000,NULL,21.00,1,'2026-06-01 00:43:53','2026-06-05 22:30:13',961.93,40.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-01','/static/productos_img/ALF MINI TORTA AGUILA.....x69g (cod 742 ).jpeg'),(195,'743','ALF MINI TORTA AGUILA BROWNIE X74G',NULL,1346.70,161.000,0.000,NULL,21.00,1,'2026-06-01 00:44:40','2026-06-04 13:05:27',961.93,40.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-01','/static/productos_img/ALF MINITOR.AGUILA BROWNIEx74g (cod 743 ).jpeg'),(196,'502','PASTILLAS BULL DOG UVA/MANDARINA  X12U',NULL,4600.00,11.000,0.000,NULL,21.00,1,'2026-06-01 00:46:41','2026-06-01 00:54:29',3593.75,28.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-05-31',NULL),(197,'1033','SERRANITAS OFERTA 14 X3 X315G',NULL,1277.99,43.000,0.000,NULL,21.00,1,'2026-06-01 00:49:17','2026-06-06 16:44:30',907.15,40.88,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-05-31','/static/productos_img/SERRANITAS OFERTA 14 X 3 X 315g (cod 1033 ).jpeg'),(198,'1034','SERRANAS SANDWICH 16 X3X 112G',NULL,1557.00,69.000,0.000,NULL,21.00,1,'2026-06-01 00:51:06','2026-06-04 22:17:18',1112.14,40.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-05-31','/static/productos_img/SERRANAS SANDWICH 16 X 3 X 112GR (cod 1034 ).jpeg'),(199,'286','GOMITAS DOCILE GAJOS SURTIDO X500',NULL,3200.00,23.000,0.000,NULL,21.00,1,'2026-06-01 00:56:34','2026-06-04 16:01:13',2500.00,28.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-05-31','/static/productos_img/GOMITA DOCILE GAJOS SURTIDO..x500g (cod 286 ).jpeg'),(200,'287','GOMITAS DOCILE CONITO SINO SUTIDO X500',NULL,3200.00,8.000,0.000,NULL,21.00,1,'2026-06-01 00:57:24','2026-06-04 16:01:13',2500.00,28.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-05-31','/static/productos_img/GOMITA DOCILE CONITO SINO SURTIDO..x500g (cod 287 ).jpeg'),(201,'3466','BONOBON OBLEA BLANCO 20X30G',NULL,847.26,160.000,0.000,NULL,21.00,1,'2026-06-01 20:56:43','2026-06-01 21:17:05',613.96,38.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-01',NULL),(202,'973','CEREAL MIX PLACERES CHOCOL X23G',NULL,844.06,0.000,0.000,NULL,21.00,1,'2026-06-02 17:25:01','2026-06-02 17:54:58',766.91,10.06,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-02',NULL),(203,'974','CEREAL MIX ORIGINAL X23G',NULL,844.05,0.000,0.000,NULL,21.00,1,'2026-06-02 17:30:09','2026-06-02 17:54:58',766.90,10.06,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-02',NULL),(204,'975','CEREAL MIX YOGH/FRUT.LIGHT X28G',NULL,844.06,0.000,0.000,NULL,21.00,1,'2026-06-02 17:31:25','2026-06-02 17:54:58',766.91,10.06,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-02',NULL),(205,'288','GOMITA DOCILE MIX DIVERTIDO X250',NULL,2764.04,2.000,0.000,NULL,21.00,1,'2026-06-02 17:37:06','2026-06-02 17:37:06',2512.76,10.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-02',NULL),(206,'3000','PROD VARIOS',NULL,66474.20,1.000,0.000,NULL,21.00,1,'2026-06-02 21:20:25','2026-06-02 21:23:14',51134.00,30.00,0,NULL,1.000,NULL,0.00,0,0,0,NULL,0.000,NULL,0.000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-02',NULL);
/*!40000 ALTER TABLE `producto` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `producto_costo_historico`
--

DROP TABLE IF EXISTS `producto_costo_historico`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `producto_costo_historico` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `producto_id` int(11) NOT NULL,
  `factura_compra_id` int(11) DEFAULT NULL,
  `costo_anterior` decimal(10,2) DEFAULT NULL,
  `costo_nuevo` decimal(10,2) DEFAULT NULL,
  `margen_anterior` decimal(10,2) DEFAULT NULL,
  `margen2_anterior` decimal(5,2) DEFAULT NULL,
  `margen3_anterior` decimal(5,2) DEFAULT NULL,
  `margen4_anterior` decimal(5,2) DEFAULT NULL,
  `margen5_anterior` decimal(5,2) DEFAULT NULL,
  `precio_anterior` decimal(10,2) DEFAULT NULL,
  `precio2_anterior` decimal(10,2) DEFAULT NULL,
  `precio3_anterior` decimal(10,2) DEFAULT NULL,
  `precio4_anterior` decimal(10,2) DEFAULT NULL,
  `precio5_anterior` decimal(10,2) DEFAULT NULL,
  `stock_anterior` decimal(10,3) DEFAULT NULL,
  `fecha` datetime NOT NULL DEFAULT current_timestamp(),
  `usuario_id` int(11) DEFAULT NULL,
  `motivo` varchar(100) DEFAULT NULL COMMENT 'compra, anulacion, manual',
  PRIMARY KEY (`id`),
  KEY `fk_pch_producto` (`producto_id`),
  KEY `fk_pch_factura` (`factura_compra_id`),
  KEY `fk_pch_usuario` (`usuario_id`),
  KEY `idx_pch_producto_fecha` (`producto_id`,`fecha`),
  CONSTRAINT `fk_pch_factura` FOREIGN KEY (`factura_compra_id`) REFERENCES `factura_compra` (`id`) ON DELETE SET NULL,
  CONSTRAINT `fk_pch_producto` FOREIGN KEY (`producto_id`) REFERENCES `producto` (`id`),
  CONSTRAINT `fk_pch_usuario` FOREIGN KEY (`usuario_id`) REFERENCES `usuario` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=45 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `producto_costo_historico`
--

LOCK TABLES `producto_costo_historico` WRITE;
/*!40000 ALTER TABLE `producto_costo_historico` DISABLE KEYS */;
INSERT INTO `producto_costo_historico` VALUES (1,38,1,5198.40,4683.66,16.29,NULL,NULL,NULL,NULL,6045.22,NULL,NULL,NULL,NULL,3.000,'2026-06-01 18:17:05',NULL,'compra'),(2,39,1,5203.20,4683.66,16.18,NULL,NULL,NULL,NULL,6045.00,NULL,NULL,NULL,NULL,7.000,'2026-06-01 18:17:05',NULL,'compra'),(3,100,1,681.67,613.96,20.00,NULL,NULL,NULL,NULL,818.00,NULL,NULL,NULL,NULL,0.000,'2026-06-01 18:17:05',NULL,'compra'),(4,201,1,0.00,613.96,38.00,NULL,NULL,NULL,NULL,0.00,NULL,NULL,NULL,NULL,0.000,'2026-06-01 18:17:05',NULL,'compra'),(5,123,1,1070.83,961.93,20.00,NULL,NULL,NULL,NULL,1285.00,NULL,NULL,NULL,NULL,0.000,'2026-06-01 18:17:05',NULL,'compra'),(6,86,1,5333.33,4533.67,20.00,NULL,NULL,NULL,NULL,6400.00,NULL,NULL,NULL,NULL,1.000,'2026-06-01 18:17:05',NULL,'compra'),(7,84,1,5333.33,4533.67,20.00,NULL,NULL,NULL,NULL,6400.00,NULL,NULL,NULL,NULL,1.000,'2026-06-01 18:17:05',NULL,'compra'),(8,87,1,5333.33,4533.67,20.00,NULL,NULL,NULL,NULL,6400.00,NULL,NULL,NULL,NULL,0.000,'2026-06-01 18:17:05',NULL,'compra'),(9,1,1,2495.87,4533.67,21.00,NULL,NULL,NULL,NULL,3020.00,NULL,NULL,NULL,NULL,4.000,'2026-06-01 18:17:05',NULL,'compra'),(10,40,1,5858.46,4683.66,16.07,NULL,NULL,NULL,NULL,6800.00,NULL,NULL,NULL,NULL,6.000,'2026-06-01 18:17:05',NULL,'compra'),(11,104,1,11333.33,9994.27,20.00,NULL,NULL,NULL,NULL,13600.00,NULL,NULL,NULL,NULL,0.000,'2026-06-01 18:17:05',NULL,'compra'),(12,191,1,4718.00,4683.66,40.00,NULL,NULL,NULL,NULL,6605.20,NULL,NULL,NULL,NULL,0.000,'2026-06-01 18:17:05',NULL,'compra'),(13,47,1,5896.56,4683.66,15.32,NULL,NULL,NULL,NULL,6800.00,NULL,NULL,NULL,NULL,0.000,'2026-06-01 18:17:05',NULL,'compra'),(14,194,1,921.42,961.93,40.00,NULL,NULL,NULL,NULL,1289.99,NULL,NULL,NULL,NULL,6.000,'2026-06-01 18:17:05',NULL,'compra'),(15,195,1,921.42,961.93,40.00,NULL,NULL,NULL,NULL,1289.99,NULL,NULL,NULL,NULL,4.000,'2026-06-01 18:17:05',NULL,'compra'),(16,132,1,3916.67,3676.73,20.00,NULL,NULL,NULL,NULL,4700.00,NULL,NULL,NULL,NULL,0.000,'2026-06-01 18:17:05',NULL,'compra'),(17,136,1,3916.67,3676.73,20.00,NULL,NULL,NULL,NULL,4700.00,NULL,NULL,NULL,NULL,0.000,'2026-06-01 18:17:05',NULL,'compra'),(18,139,1,3916.67,3676.73,20.00,NULL,NULL,NULL,NULL,4700.00,NULL,NULL,NULL,NULL,0.000,'2026-06-01 18:17:05',NULL,'compra'),(19,141,1,3916.67,3676.73,20.00,NULL,NULL,NULL,NULL,4700.00,NULL,NULL,NULL,NULL,3.000,'2026-06-01 18:17:05',NULL,'compra'),(20,138,1,3916.67,3676.73,20.00,NULL,NULL,NULL,NULL,4700.00,NULL,NULL,NULL,NULL,0.000,'2026-06-01 18:17:05',NULL,'compra'),(21,122,1,1038.33,961.93,20.00,NULL,NULL,NULL,NULL,1246.00,NULL,NULL,NULL,NULL,0.000,'2026-06-01 18:17:05',NULL,'compra'),(22,121,1,1070.83,961.93,20.00,NULL,NULL,NULL,NULL,1285.00,NULL,NULL,NULL,NULL,0.000,'2026-06-01 18:17:05',NULL,'compra'),(23,206,2,0.00,51134.00,30.00,NULL,NULL,NULL,NULL,0.00,NULL,NULL,NULL,NULL,0.000,'2026-06-02 18:23:14',3,'compra'),(24,120,3,779.17,642.74,20.00,NULL,NULL,NULL,NULL,935.00,NULL,NULL,NULL,NULL,105.000,'2026-06-02 20:48:53',3,'compra'),(25,95,3,605.80,608.65,30.00,NULL,NULL,NULL,NULL,787.54,NULL,NULL,NULL,NULL,78.000,'2026-06-02 20:48:53',3,'compra'),(26,94,3,605.80,608.65,30.00,NULL,NULL,NULL,NULL,787.54,NULL,NULL,NULL,NULL,60.000,'2026-06-02 20:48:54',3,'compra'),(27,128,3,534.70,500.73,29.05,NULL,NULL,NULL,NULL,690.03,NULL,NULL,NULL,NULL,47.000,'2026-06-02 20:48:54',3,'compra'),(28,127,3,534.70,537.20,29.06,NULL,NULL,NULL,NULL,690.08,NULL,NULL,NULL,NULL,129.000,'2026-06-02 20:48:54',3,'compra'),(29,6,3,10500.00,9494.31,20.00,NULL,NULL,NULL,NULL,12600.00,NULL,NULL,NULL,NULL,0.000,'2026-06-02 20:48:54',3,'compra'),(30,163,3,914.95,919.26,30.07,NULL,NULL,NULL,NULL,1190.08,NULL,NULL,NULL,NULL,7.000,'2026-06-02 20:48:54',3,'compra'),(31,164,3,914.95,919.26,30.07,NULL,NULL,NULL,NULL,1190.08,NULL,NULL,NULL,NULL,25.000,'2026-06-02 20:48:54',3,'compra'),(32,162,3,914.95,919.26,30.07,NULL,NULL,NULL,NULL,1190.08,NULL,NULL,NULL,NULL,100.000,'2026-06-02 20:48:54',3,'compra'),(33,52,3,2448.90,2461.46,29.85,NULL,NULL,NULL,NULL,3179.90,NULL,NULL,NULL,NULL,16.000,'2026-06-02 20:48:54',3,'compra'),(34,29,3,6807.80,6839.85,29.99,NULL,NULL,NULL,NULL,8849.46,NULL,NULL,NULL,NULL,4.000,'2026-06-02 20:48:54',3,'compra'),(35,27,3,6807.78,6839.76,29.99,NULL,NULL,NULL,NULL,8849.43,NULL,NULL,NULL,NULL,6.000,'2026-06-02 20:48:54',3,'compra'),(36,13,3,3811.22,3829.15,29.89,NULL,NULL,NULL,NULL,4950.39,NULL,NULL,NULL,NULL,1.000,'2026-06-02 20:48:54',3,'compra'),(37,19,3,3811.22,3829.15,29.90,NULL,NULL,NULL,NULL,4950.77,NULL,NULL,NULL,NULL,0.000,'2026-06-02 20:48:54',3,'compra'),(38,17,3,3811.22,3829.15,29.90,NULL,NULL,NULL,NULL,4950.77,NULL,NULL,NULL,NULL,0.000,'2026-06-02 20:48:54',3,'compra'),(39,12,3,3811.22,3829.15,29.88,NULL,NULL,NULL,NULL,4950.01,NULL,NULL,NULL,NULL,0.000,'2026-06-02 20:48:54',3,'compra'),(40,18,3,3811.22,3829.15,29.88,NULL,NULL,NULL,NULL,4950.01,NULL,NULL,NULL,NULL,0.000,'2026-06-02 20:48:54',3,'compra'),(41,10,3,3811.22,3829.15,29.88,NULL,NULL,NULL,NULL,4950.01,NULL,NULL,NULL,NULL,1.000,'2026-06-02 20:48:54',3,'compra'),(42,11,3,3811.22,3829.15,29.88,NULL,NULL,NULL,NULL,4950.01,NULL,NULL,NULL,NULL,1.000,'2026-06-02 20:48:54',3,'compra'),(43,129,3,153.38,154.10,29.75,NULL,NULL,NULL,NULL,199.01,NULL,NULL,NULL,NULL,43.000,'2026-06-02 20:48:54',3,'compra'),(44,144,3,1200.00,1205.64,30.00,NULL,NULL,NULL,NULL,1560.00,NULL,NULL,NULL,NULL,44.000,'2026-06-02 20:48:54',3,'compra');
/*!40000 ALTER TABLE `producto_costo_historico` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `producto_proveedor`
--

DROP TABLE IF EXISTS `producto_proveedor`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `producto_proveedor` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `producto_id` int(11) NOT NULL,
  `proveedor_id` int(11) NOT NULL,
  `codigo_proveedor` varchar(50) NOT NULL,
  `fecha_creacion` datetime NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_pp_producto_proveedor` (`producto_id`,`proveedor_id`),
  KEY `idx_pp_codigo_proveedor` (`proveedor_id`,`codigo_proveedor`),
  CONSTRAINT `fk_pp_producto_schiro` FOREIGN KEY (`producto_id`) REFERENCES `producto` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_pp_proveedor_schiro` FOREIGN KEY (`proveedor_id`) REFERENCES `proveedor` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `producto_proveedor`
--

LOCK TABLES `producto_proveedor` WRITE;
/*!40000 ALTER TABLE `producto_proveedor` DISABLE KEYS */;
/*!40000 ALTER TABLE `producto_proveedor` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `proveedor`
--

DROP TABLE IF EXISTS `proveedor`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `proveedor` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `razon_social` varchar(150) NOT NULL,
  `cuit` varchar(20) DEFAULT NULL,
  `condicion_iva` varchar(50) NOT NULL DEFAULT 'Responsable Inscripto',
  `direccion` varchar(200) DEFAULT NULL,
  `telefono` varchar(30) DEFAULT NULL,
  `email` varchar(100) DEFAULT NULL,
  `saldo` decimal(12,2) NOT NULL DEFAULT 0.00 COMMENT 'Deuda acumulada (positivo = le debo)',
  `activo` tinyint(1) NOT NULL DEFAULT 1,
  `fecha_creacion` datetime NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE='utf8mb4_general_ci';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `proveedor`
--

LOCK TABLES `proveedor` WRITE;
/*!40000 ALTER TABLE `proveedor` DISABLE KEYS */;
INSERT INTO `proveedor` VALUES (1,'DIMSA SA',NULL,'Responsable Inscripto',NULL,NULL,NULL,1801380.00,1,'2026-06-01 17:39:06'),(2,'PEDRO BALESTRINO E HIJOS','30330567393','Responsable Inscripto','AV. ALVAREZ 347',NULL,NULL,932229.61,1,'2026-06-02 18:17:38');
/*!40000 ALTER TABLE `proveedor` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `proveedor_movimiento`
--

DROP TABLE IF EXISTS `proveedor_movimiento`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `proveedor_movimiento` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `proveedor_id` int(11) NOT NULL,
  `fecha` date NOT NULL,
  `tipo` varchar(20) NOT NULL COMMENT 'factura/pago/nota_credito/saldo_inicial/ajuste',
  `referencia_id` int(11) DEFAULT NULL,
  `descripcion` varchar(200) DEFAULT NULL,
  `debe` decimal(12,2) NOT NULL DEFAULT 0.00,
  `haber` decimal(12,2) NOT NULL DEFAULT 0.00,
  `saldo_acumulado` decimal(12,2) NOT NULL DEFAULT 0.00,
  `fecha_carga` datetime NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `idx_prov_mov_prov` (`proveedor_id`),
  KEY `idx_prov_mov_fecha` (`fecha`),
  KEY `idx_prov_mov_tipo` (`tipo`),
  CONSTRAINT `fk_prov_mov_prov` FOREIGN KEY (`proveedor_id`) REFERENCES `proveedor` (`id`) ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE='utf8mb4_general_ci';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `proveedor_movimiento`
--

LOCK TABLES `proveedor_movimiento` WRITE;
/*!40000 ALTER TABLE `proveedor_movimiento` DISABLE KEYS */;
INSERT INTO `proveedor_movimiento` VALUES (1,2,'2026-06-02','pago',1,'Pago OP R 0001-00000001 (imputado $51134.64)',0.00,51134.64,0.00,'2026-06-02 18:24:06');
/*!40000 ALTER TABLE `proveedor_movimiento` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `recibo_cobro`
--

DROP TABLE IF EXISTS `recibo_cobro`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `recibo_cobro` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `cliente_id` int(11) NOT NULL,
  `usuario_id` int(11) NOT NULL,
  `fecha` datetime NOT NULL DEFAULT current_timestamp(),
  `numero` varchar(20) DEFAULT NULL,
  `total` decimal(12,2) NOT NULL,
  `observaciones` text DEFAULT NULL,
  `estado` varchar(10) NOT NULL DEFAULT 'emitido',
  PRIMARY KEY (`id`),
  KEY `cliente_id` (`cliente_id`),
  CONSTRAINT `recibo_cobro_ibfk_1` FOREIGN KEY (`cliente_id`) REFERENCES `cliente` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=25 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `recibo_cobro`
--

LOCK TABLES `recibo_cobro` WRITE;
/*!40000 ALTER TABLE `recibo_cobro` DISABLE KEYS */;
INSERT INTO `recibo_cobro` VALUES (1,52,3,'2026-06-02 17:24:10','R00000001',68750.00,NULL,'emitido'),(2,46,3,'2026-06-02 18:13:17','R00000002',352209.60,NULL,'emitido'),(3,66,3,'2026-06-02 18:14:29','R00000003',38600.00,NULL,'emitido'),(4,63,3,'2026-06-02 18:30:06','R00000004',40000.00,NULL,'emitido'),(5,70,3,'2026-06-02 18:30:43','R00000005',26796.00,NULL,'emitido'),(6,62,3,'2026-06-02 18:31:55','R00000006',30046.00,NULL,'emitido'),(7,66,3,'2026-06-02 18:33:07','R00000007',40100.00,NULL,'emitido'),(8,69,3,'2026-06-07 19:56:36','R00000008',45914.00,NULL,'emitido'),(9,64,3,'2026-06-07 19:57:47','R00000009',52014.00,NULL,'emitido'),(10,60,3,'2026-06-07 19:58:29','R00000010',57348.00,NULL,'emitido'),(11,68,3,'2026-06-07 20:11:12','R00000011',122000.00,NULL,'emitido'),(12,55,3,'2026-06-07 20:12:33','R00000012',106143.00,NULL,'emitido'),(13,49,3,'2026-06-07 20:13:05','R00000013',45142.00,NULL,'emitido'),(14,38,3,'2026-06-07 20:13:37','R00000014',39571.46,NULL,'emitido'),(15,17,3,'2026-06-07 20:18:44','R00000015',8152.00,NULL,'emitido'),(16,59,3,'2026-06-07 20:19:20','R00000016',60000.00,NULL,'emitido'),(17,72,3,'2026-06-07 20:21:29','R00000017',36511.70,NULL,'emitido'),(18,39,3,'2026-06-07 20:22:50','R00000018',32095.80,NULL,'emitido'),(19,66,3,'2026-06-07 20:24:55','R00000019',64186.00,NULL,'emitido'),(20,36,3,'2026-06-07 20:35:51','R00000020',44450.00,NULL,'emitido'),(21,19,3,'2026-06-07 20:36:34','R00000021',26761.00,NULL,'emitido'),(22,71,3,'2026-06-07 20:37:30','R00000022',50000.00,NULL,'emitido'),(23,17,3,'2026-06-07 20:38:12','R00000023',28000.00,NULL,'emitido'),(24,50,3,'2026-06-08 11:03:36','R00000024',15000.00,NULL,'emitido');
/*!40000 ALTER TABLE `recibo_cobro` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `recibo_cobro_detalle`
--

DROP TABLE IF EXISTS `recibo_cobro_detalle`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `recibo_cobro_detalle` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `recibo_id` int(11) NOT NULL,
  `movimiento_id` int(11) NOT NULL,
  `monto_imputado` decimal(12,2) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `recibo_id` (`recibo_id`),
  KEY `movimiento_id` (`movimiento_id`),
  CONSTRAINT `recibo_cobro_detalle_ibfk_1` FOREIGN KEY (`recibo_id`) REFERENCES `recibo_cobro` (`id`),
  CONSTRAINT `recibo_cobro_detalle_ibfk_2` FOREIGN KEY (`movimiento_id`) REFERENCES `cta_cte_movimiento` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=26 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `recibo_cobro_detalle`
--

LOCK TABLES `recibo_cobro_detalle` WRITE;
/*!40000 ALTER TABLE `recibo_cobro_detalle` DISABLE KEYS */;
INSERT INTO `recibo_cobro_detalle` VALUES (1,1,10,68750.00),(2,2,26,352209.60),(3,3,24,38600.00),(4,4,21,40000.00),(5,5,29,26796.00),(6,6,20,30046.00),(7,7,24,40100.00),(8,8,28,45914.00),(9,9,22,52014.00),(10,10,18,57348.00),(11,11,27,122000.00),(12,12,13,106143.00),(13,13,3,45142.00),(14,14,55,39571.46),(15,15,8,8152.00),(16,16,17,60000.00),(17,17,45,36511.70),(18,18,54,32095.80),(19,19,24,20136.00),(20,19,50,44050.00),(21,20,9,44450.00),(22,21,6,26761.00),(23,22,31,50000.00),(24,23,8,28000.00),(25,24,5,15000.00);
/*!40000 ALTER TABLE `recibo_cobro_detalle` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `recibo_cobro_medio`
--

DROP TABLE IF EXISTS `recibo_cobro_medio`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `recibo_cobro_medio` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `recibo_id` int(11) NOT NULL,
  `medio` enum('efectivo','debito','credito','transferencia','mercado_pago','otro') NOT NULL,
  `importe` decimal(12,2) NOT NULL,
  `referencia` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `recibo_id` (`recibo_id`),
  CONSTRAINT `recibo_cobro_medio_ibfk_1` FOREIGN KEY (`recibo_id`) REFERENCES `recibo_cobro` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=26 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `recibo_cobro_medio`
--

LOCK TABLES `recibo_cobro_medio` WRITE;
/*!40000 ALTER TABLE `recibo_cobro_medio` DISABLE KEYS */;
INSERT INTO `recibo_cobro_medio` VALUES (1,1,'transferencia',68750.00,NULL),(2,2,'efectivo',352209.60,NULL),(3,3,'efectivo',38600.00,NULL),(4,4,'efectivo',40000.00,NULL),(5,5,'efectivo',26796.00,NULL),(6,6,'efectivo',30046.00,NULL),(7,7,'efectivo',40100.00,NULL),(8,8,'transferencia',45914.00,NULL),(9,9,'transferencia',20000.00,NULL),(10,9,'efectivo',32014.00,NULL),(11,10,'efectivo',57348.00,NULL),(12,11,'transferencia',122000.00,NULL),(13,12,'transferencia',106143.00,NULL),(14,13,'transferencia',45142.00,NULL),(15,14,'transferencia',39571.46,NULL),(16,15,'transferencia',8152.00,NULL),(17,16,'transferencia',60000.00,NULL),(18,17,'efectivo',36511.70,NULL),(19,18,'efectivo',32095.80,NULL),(20,19,'efectivo',64186.00,NULL),(21,20,'efectivo',44450.00,NULL),(22,21,'efectivo',26761.00,NULL),(23,22,'efectivo',50000.00,NULL),(24,23,'efectivo',28000.00,NULL),(25,24,'transferencia',15000.00,NULL);
/*!40000 ALTER TABLE `recibo_cobro_medio` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `recibo_cobro_numerador`
--

DROP TABLE IF EXISTS `recibo_cobro_numerador`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `recibo_cobro_numerador` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `ultimo_numero` int(11) NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE='utf8mb4_general_ci';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `recibo_cobro_numerador`
--

LOCK TABLES `recibo_cobro_numerador` WRITE;
/*!40000 ALTER TABLE `recibo_cobro_numerador` DISABLE KEYS */;
INSERT INTO `recibo_cobro_numerador` VALUES (1,24);
/*!40000 ALTER TABLE `recibo_cobro_numerador` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `remito`
--

DROP TABLE IF EXISTS `remito`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `remito` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `cliente_id` int(11) NOT NULL,
  `fecha` date NOT NULL,
  `fecha_creacion` datetime NOT NULL DEFAULT current_timestamp(),
  `tipo_comprobante` varchar(5) NOT NULL DEFAULT 'R',
  `punto_venta` varchar(5) NOT NULL DEFAULT '00001',
  `numero` varchar(10) NOT NULL,
  `estado` enum('pendiente','liquidado','facturado','anulado') NOT NULL DEFAULT 'pendiente',
  `total_al_emitir` decimal(12,2) NOT NULL DEFAULT 0.00,
  `observaciones` text DEFAULT NULL,
  `motivo_anulacion` text DEFAULT NULL,
  `fecha_anulacion` datetime DEFAULT NULL,
  `factura_venta_id` int(11) DEFAULT NULL,
  `fecha_facturacion` datetime DEFAULT NULL,
  `usuario_id` int(11) DEFAULT NULL,
  `zona_id` int(11) DEFAULT NULL COMMENT 'Zona de reparto (heredada del cliente)',
  `en_reparto_fecha` date DEFAULT NULL COMMENT 'Fecha asignada al reparto (NULL = no asignado)',
  `orden_reparto_manual` int(11) DEFAULT NULL COMMENT 'Orden manual drag-and-drop',
  PRIMARY KEY (`id`),
  KEY `idx_remito_cliente` (`cliente_id`),
  KEY `idx_remito_estado` (`estado`),
  KEY `idx_remito_fecha` (`fecha`),
  KEY `fk_remito_zona_rep` (`zona_id`),
  KEY `idx_remito_reparto` (`en_reparto_fecha`,`orden_reparto_manual`),
  CONSTRAINT `fk_remito_cliente_schiro` FOREIGN KEY (`cliente_id`) REFERENCES `cliente` (`id`),
  CONSTRAINT `fk_remito_zona_rep` FOREIGN KEY (`zona_id`) REFERENCES `zona` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `remito`
--

LOCK TABLES `remito` WRITE;
/*!40000 ALTER TABLE `remito` DISABLE KEYS */;
/*!40000 ALTER TABLE `remito` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `remito_detalle`
--

DROP TABLE IF EXISTS `remito_detalle`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `remito_detalle` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `remito_id` int(11) NOT NULL,
  `producto_id` int(11) NOT NULL,
  `cantidad` decimal(10,3) NOT NULL,
  `precio_unitario_al_emitir` decimal(12,2) NOT NULL,
  `subtotal_al_emitir` decimal(12,2) NOT NULL,
  `iva` decimal(5,2) NOT NULL DEFAULT 21.00,
  PRIMARY KEY (`id`),
  KEY `idx_rd_remito` (`remito_id`),
  KEY `idx_rd_producto` (`producto_id`),
  CONSTRAINT `fk_rd_producto_schiro` FOREIGN KEY (`producto_id`) REFERENCES `producto` (`id`),
  CONSTRAINT `fk_rd_remito_schiro` FOREIGN KEY (`remito_id`) REFERENCES `remito` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `remito_detalle`
--

LOCK TABLES `remito_detalle` WRITE;
/*!40000 ALTER TABLE `remito_detalle` DISABLE KEYS */;
/*!40000 ALTER TABLE `remito_detalle` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `remito_liquidacion`
--

DROP TABLE IF EXISTS `remito_liquidacion`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `remito_liquidacion` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `remito_id` int(11) NOT NULL,
  `fecha_liquidacion` datetime NOT NULL DEFAULT current_timestamp(),
  `usuario_id` int(11) DEFAULT NULL,
  `usuario_nombre` varchar(100) DEFAULT NULL,
  `observaciones` text DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_rl_remito` (`remito_id`),
  CONSTRAINT `fk_rl_remito` FOREIGN KEY (`remito_id`) REFERENCES `remito` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `remito_liquidacion`
--

LOCK TABLES `remito_liquidacion` WRITE;
/*!40000 ALTER TABLE `remito_liquidacion` DISABLE KEYS */;
/*!40000 ALTER TABLE `remito_liquidacion` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `remito_liquidacion_detalle`
--

DROP TABLE IF EXISTS `remito_liquidacion_detalle`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `remito_liquidacion_detalle` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `liquidacion_id` int(11) NOT NULL,
  `remito_detalle_id` int(11) NOT NULL,
  `producto_id` int(11) NOT NULL,
  `cant_original` decimal(10,3) NOT NULL,
  `cant_entregada` decimal(10,3) NOT NULL DEFAULT 0.000,
  `cant_devuelta` decimal(10,3) NOT NULL DEFAULT 0.000,
  `cant_rotura` decimal(10,3) NOT NULL DEFAULT 0.000,
  `motivo` varchar(200) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_rld_liq` (`liquidacion_id`),
  KEY `idx_rld_remito_detalle` (`remito_detalle_id`),
  KEY `idx_rld_producto` (`producto_id`),
  CONSTRAINT `fk_rld_liq` FOREIGN KEY (`liquidacion_id`) REFERENCES `remito_liquidacion` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_rld_producto` FOREIGN KEY (`producto_id`) REFERENCES `producto` (`id`),
  CONSTRAINT `fk_rld_remito_detalle` FOREIGN KEY (`remito_detalle_id`) REFERENCES `remito_detalle` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `remito_liquidacion_detalle`
--

LOCK TABLES `remito_liquidacion_detalle` WRITE;
/*!40000 ALTER TABLE `remito_liquidacion_detalle` DISABLE KEYS */;
/*!40000 ALTER TABLE `remito_liquidacion_detalle` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `remito_numerador`
--

DROP TABLE IF EXISTS `remito_numerador`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `remito_numerador` (
  `punto_venta` varchar(5) NOT NULL,
  `ultimo_numero` int(11) NOT NULL DEFAULT 0,
  PRIMARY KEY (`punto_venta`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `remito_numerador`
--

LOCK TABLES `remito_numerador` WRITE;
/*!40000 ALTER TABLE `remito_numerador` DISABLE KEYS */;
/*!40000 ALTER TABLE `remito_numerador` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `stock_audit`
--

DROP TABLE IF EXISTS `stock_audit`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `stock_audit` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `fecha` datetime DEFAULT current_timestamp(),
  `producto_id` int(11) NOT NULL,
  `codigo_producto` varchar(50) DEFAULT NULL,
  `nombre_producto` varchar(200) DEFAULT NULL,
  `tipo` varchar(50) NOT NULL,
  `cantidad` decimal(15,3) NOT NULL,
  `signo` char(1) NOT NULL,
  `stock_anterior` decimal(15,3) DEFAULT NULL,
  `stock_nuevo` decimal(15,3) DEFAULT NULL,
  `referencia_tipo` varchar(50) DEFAULT NULL,
  `referencia_id` int(11) DEFAULT NULL,
  `motivo` text DEFAULT NULL,
  `usuario_id` int(11) DEFAULT NULL,
  `usuario_nombre` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_fecha` (`fecha`),
  KEY `idx_producto` (`producto_id`),
  KEY `idx_tipo` (`tipo`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `stock_audit`
--

LOCK TABLES `stock_audit` WRITE;
/*!40000 ALTER TABLE `stock_audit` DISABLE KEYS */;
/*!40000 ALTER TABLE `stock_audit` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `stock_movimiento`
--

DROP TABLE IF EXISTS `stock_movimiento`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `stock_movimiento` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `producto_id` int(11) NOT NULL,
  `codigo_producto` varchar(50) DEFAULT NULL,
  `nombre_producto` varchar(200) DEFAULT NULL,
  `tipo` varchar(30) NOT NULL,
  `cantidad` decimal(10,3) NOT NULL,
  `signo` char(1) NOT NULL,
  `stock_anterior` decimal(10,3) DEFAULT NULL,
  `stock_nuevo` decimal(10,3) DEFAULT NULL,
  `referencia_tipo` varchar(30) DEFAULT NULL,
  `referencia_id` int(11) DEFAULT NULL,
  `motivo` text DEFAULT NULL,
  `usuario_id` int(11) DEFAULT NULL,
  `usuario_nombre` varchar(100) DEFAULT NULL,
  `fecha` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `idx_producto` (`producto_id`),
  KEY `idx_fecha` (`fecha`),
  KEY `idx_tipo` (`tipo`)
) ENGINE=InnoDB AUTO_INCREMENT=751 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `stock_movimiento`
--

LOCK TABLES `stock_movimiento` WRITE;
/*!40000 ALTER TABLE `stock_movimiento` DISABLE KEYS */;
INSERT INTO `stock_movimiento` VALUES (2,10,'200','GOMITAS YUMMY OSITOS ACIDOS X 500 GR','venta',1.000,'-',10000.000,9999.000,'factura',1,NULL,3,'Administrador','2026-05-28 20:30:51'),(3,10,'200','GOMITAS YUMMY OSITOS ACIDOS X 500 GR','venta',1.000,'-',9999.000,9998.000,'factura',2,NULL,3,'Administrador','2026-05-28 21:14:00'),(4,10,'200','GOMITAS YUMMY OSITOS ACIDOS X 500 GR','venta',1.000,'-',9998.000,9997.000,'factura',3,NULL,3,'Administrador','2026-05-28 21:33:06'),(5,10,'200','GOMITAS YUMMY OSITOS ACIDOS X 500 GR','devolucion',1.000,'+',9997.000,9998.000,'factura',3,'Anulación factura 0006-X0000001 - por error',3,'Administrador','2026-05-28 21:33:49'),(6,10,'200','GOMITAS YUMMY OSITOS ACIDOS X 500 GR','venta',1.000,'-',9998.000,9997.000,'factura',4,NULL,3,'Administrador','2026-05-28 21:34:53'),(7,10,'200','GOMITAS YUMMY OSITOS ACIDOS X 500 GR','venta',1.000,'-',9997.000,9996.000,'factura',5,NULL,3,'Administrador','2026-05-28 23:32:26'),(8,61,'311','CHUPETIN PICO-DULCE.......x48u','venta',1.000,'-',10000.000,9999.000,'factura',6,NULL,3,'Administrador','2026-05-29 20:56:24'),(9,64,'402','(x32u)MAST.LENGUETAZO T.FRUTI...','venta',2.000,'-',10000.000,9998.000,'factura',6,NULL,3,'Administrador','2026-05-29 20:56:24'),(10,65,'404','PALITO DE LA SELVA.......x660g','venta',2.000,'-',10000.000,9998.000,'factura',6,NULL,3,'Administrador','2026-05-29 20:56:24'),(11,66,'406','CARAM.FLYNN PAFF TUTTI....x70u','venta',2.000,'-',10000.000,9998.000,'factura',6,NULL,3,'Administrador','2026-05-29 20:56:24'),(12,79,'511','MENTITAS MENTA X 12 UND','venta',2.000,'-',10000.000,9998.000,'factura',6,NULL,3,'Administrador','2026-05-29 20:56:24'),(13,100,'708','BONOBON OBLEA LECHE....20ux30g','venta',40.000,'-',10000.000,9960.000,'factura',6,NULL,3,'Administrador','2026-05-29 20:56:24'),(14,105,'760','CHOC.NUGATON LECHE........x27g','venta',24.000,'-',10000.000,9976.000,'factura',6,NULL,3,'Administrador','2026-05-29 20:56:24'),(15,109,'714','GUAYMALLEN TRIPLE CHOCOLATE','venta',48.000,'-',10000.000,9952.000,'factura',6,NULL,3,'Administrador','2026-05-29 20:56:24'),(16,110,'715','GUAYMALLEN TRIPLE BLANCO','venta',48.000,'-',10000.000,9952.000,'factura',6,NULL,3,'Administrador','2026-05-29 20:56:24'),(17,113,'718','ALF FANTOCHE TRI.CHOCOLATEx85g','venta',48.000,'-',10000.000,9952.000,'factura',6,NULL,3,'Administrador','2026-05-29 20:56:24'),(18,114,'719','ALF FANTOCHE TRIPLE BLANCO.x85g','venta',48.000,'-',10000.000,9952.000,'factura',6,NULL,3,'Administrador','2026-05-29 20:56:24'),(19,127,'740','ALF PESCADO RAUL SIMPLE NEGRO.x50g','venta',24.000,'-',10000.000,9976.000,'factura',6,NULL,3,'Administrador','2026-05-29 20:56:24'),(20,128,'741','ALF PESCADO RAUL SIMPLE BLANCO.x50g','venta',24.000,'-',10000.000,9976.000,'factura',6,NULL,3,'Administrador','2026-05-29 20:56:24'),(21,155,'1010','DON SATUR BIZCOCH.GRASA x200g','venta',10.000,'-',10000.000,9990.000,'factura',6,NULL,3,'Administrador','2026-05-29 20:56:24'),(22,156,'1011','DON SATUR BIZCOCHO DULCE.x200g','venta',10.000,'-',10000.000,9990.000,'factura',6,NULL,3,'Administrador','2026-05-29 20:56:24'),(23,157,'1012','DON SATUR BIZCOCH.NEGRITOx200g','venta',10.000,'-',10000.000,9990.000,'factura',6,NULL,3,'Administrador','2026-05-29 20:56:24'),(26,190,'144','TOP LINE SEVEN MENTA','venta',1.000,'-',16.000,15.000,'factura',7,NULL,3,'Administrador','2026-05-30 17:28:55'),(27,27,'230','GOMA FANTASIA MISKY .......x1k','venta',1.000,'-',10000.000,9999.000,'factura',7,NULL,3,'Administrador','2026-05-30 17:28:55'),(28,30,'240','GOMAS LA PIÑATA HUESOS ACIDOS X 700 GR','venta',1.000,'-',10000.000,9999.000,'factura',7,NULL,3,'Administrador','2026-05-30 17:28:55'),(29,34,'252','GOMA BULL DOG.REGALIZ TUTTI F.CJAx12u','venta',1.000,'-',10000.000,9999.000,'factura',7,NULL,3,'Administrador','2026-05-30 17:28:55'),(30,38,'266','MOGUL MORAS X 500G','venta',1.000,'-',10000.000,9999.000,'factura',7,NULL,3,'Administrador','2026-05-30 17:28:55'),(31,43,'271','MOGUL EXTREME LADRILLOS MIX FRUTAL X 500G','venta',1.000,'-',10000.000,9999.000,'factura',7,NULL,3,'Administrador','2026-05-30 17:28:55'),(32,47,'275','MOGUL EXTREME OSITOS X 500G','venta',1.000,'-',10000.000,9999.000,'factura',7,NULL,3,'Administrador','2026-05-30 17:28:55'),(33,53,'302','MR.POPS EVOLUTION CEREZA..x24u','venta',1.000,'-',10000.000,9999.000,'factura',7,NULL,3,'Administrador','2026-05-30 17:28:55'),(34,55,'304','MR.POPS EVOLUTION EXTREME.x24u','venta',1.000,'-',10000.000,9999.000,'factura',7,NULL,3,'Administrador','2026-05-30 17:28:55'),(35,63,'400','MASTICABLE SURTIDO MISKY X 800gs','venta',1.000,'-',10000.000,9999.000,'factura',7,NULL,3,'Administrador','2026-05-30 17:28:55'),(36,65,'404','PALITO DE LA SELVA.......x660g','venta',1.000,'-',9998.000,9997.000,'factura',7,NULL,3,'Administrador','2026-05-30 17:28:55'),(37,96,'704','ROCKLETS 24 X 20GS','venta',1.000,'-',10000.000,9999.000,'factura',7,NULL,3,'Administrador','2026-05-30 17:28:55'),(38,99,'707','CREMA KROOMY SURTIDOS ( 48u )','venta',1.000,'-',10000.000,9999.000,'factura',7,NULL,3,'Administrador','2026-05-30 17:28:55'),(39,150,'1000','MAGDAL DON SATUR REL.D/LEx250g','venta',2.000,'-',10000.000,9998.000,'factura',7,NULL,3,'Administrador','2026-05-30 17:28:55'),(40,151,'1001','MAGDAL DON SATUR VAINILLAx250g','venta',3.000,'-',10000.000,9997.000,'factura',7,NULL,3,'Administrador','2026-05-30 17:28:55'),(41,152,'1002','MAGDAL DON SATUR MARMOLADx250g','venta',3.000,'-',10000.000,9997.000,'factura',7,NULL,3,'Administrador','2026-05-30 17:28:55'),(42,154,'1004','MAGDAL DON SATUR C/CHIPS.x250g','venta',3.000,'-',10000.000,9997.000,'factura',7,NULL,3,'Administrador','2026-05-30 17:28:55'),(43,170,'961','MANI TARRO CERVECERO PIZZA','venta',3.000,'-',10000.000,9997.000,'factura',7,NULL,3,'Administrador','2026-05-30 17:28:55'),(44,40,'268','MOGUL FRUTILLAS CON CREMA X 500G','venta',1.000,'-',10000.000,9999.000,'factura',7,NULL,3,'Administrador','2026-05-30 17:28:55'),(250,39,'267','MOGUL DIENTES X 500G','venta',2.000,'-',9.000,7.000,'factura',8,NULL,3,'Administrador','2026-06-01 14:55:23'),(251,30,'240','GOMAS LA PIÑATA HUESOS ACIDOS X 700 GR','venta',1.000,'-',5.000,4.000,'factura',8,NULL,3,'Administrador','2026-06-01 14:55:23'),(252,52,'285','GOMITA DOCILE MIX DULCE/ACIDO X500','venta',3.000,'-',20.000,17.000,'factura',8,NULL,3,'Administrador','2026-06-01 14:55:23'),(253,60,'310','CHUPETIN PUSH POP.........x20u','venta',1.000,'-',6.000,5.000,'factura',8,NULL,3,'Administrador','2026-06-01 14:55:23'),(254,71,'29508','MAST.RICOMAS FRUTIL/LIMONx280g','venta',2.000,'-',8.000,6.000,'factura',8,NULL,3,'Administrador','2026-06-01 14:55:23'),(255,100,'708','BONOBON OBLEA LECHE....20ux30g','venta',3.000,'-',3.000,0.000,'factura',8,NULL,3,'Administrador','2026-06-01 14:55:23'),(256,111,'716','GUAYMALLEN SIMPLE BLANCO','venta',10.000,'-',520.000,510.000,'factura',8,NULL,3,'Administrador','2026-06-01 14:55:23'),(257,112,'717','GUAYMALLEN SIMPLE CHOCOLATE','venta',10.000,'-',542.000,532.000,'factura',8,NULL,3,'Administrador','2026-06-01 14:55:23'),(258,120,'728','ALF FANTOCHE SUPER TRIPLE NEGx100g','venta',8.000,'-',117.000,109.000,'factura',8,NULL,3,'Administrador','2026-06-01 14:55:23'),(259,131,'801','GIRASOL PIPAS GIGANTES.12ux50g','venta',1.000,'-',8.000,7.000,'factura',8,NULL,3,'Administrador','2026-06-01 14:55:23'),(260,170,'961','MANI TARRO CERVECERO PIZZA','venta',3.000,'-',15.000,12.000,'factura',8,NULL,3,'Administrador','2026-06-01 14:55:23'),(261,171,'962','MANI TARRO CERVECERO JAMON','venta',3.000,'-',6.000,3.000,'factura',8,NULL,3,'Administrador','2026-06-01 14:55:23'),(262,175,'968','MANI TARRO CON PIEL','venta',2.000,'-',32.000,30.000,'factura',8,NULL,3,'Administrador','2026-06-01 14:55:23'),(263,177,'970','MANI CON CASCARA','venta',2.000,'-',42.000,40.000,'factura',8,NULL,3,'Administrador','2026-06-01 14:55:23'),(264,166,'1030','SURTIDO BAGLEY...........x400g','venta',10.000,'-',95.000,85.000,'factura',9,NULL,3,'Administrador','2026-06-01 15:00:09'),(265,114,'719','ALF FANTOCHE TRIPLE BLANCO.x85g','venta',12.000,'-',110.000,98.000,'factura',9,NULL,3,'Administrador','2026-06-01 15:00:09'),(266,129,'751','TURRON MISKY','venta',43.000,'-',43.000,0.000,'factura',9,NULL,3,'Administrador','2026-06-01 15:00:09'),(267,166,'1030','SURTIDO BAGLEY...........x400g','devolucion',10.000,'+',85.000,95.000,'factura',9,'Anulación factura 0006-X0000005 - CARGUE MAL SALDO INICIAL',3,'Administrador','2026-06-01 15:25:24'),(268,114,'719','ALF FANTOCHE TRIPLE BLANCO.x85g','devolucion',12.000,'+',98.000,110.000,'factura',9,'Anulación factura 0006-X0000005 - CARGUE MAL SALDO INICIAL',3,'Administrador','2026-06-01 15:25:24'),(269,129,'751','TURRON MISKY','devolucion',43.000,'+',0.000,43.000,'factura',9,'Anulación factura 0006-X0000005 - CARGUE MAL SALDO INICIAL',3,'Administrador','2026-06-01 15:25:24'),(270,35,'253','GOMA BULL DOG.REGALIZ FRAMB.CJAx12u','venta',1.000,'-',12.000,11.000,'factura',10,NULL,3,'Administrador','2026-06-01 17:10:04'),(271,63,'400','MASTICABLE SURTIDO MISKY X 800gs','venta',1.000,'-',22.000,21.000,'factura',10,NULL,3,'Administrador','2026-06-01 17:10:04'),(272,64,'402','(x32u)MAST.LENGUETAZO T.FRUTI...','venta',1.000,'-',8.000,7.000,'factura',10,NULL,3,'Administrador','2026-06-01 17:10:04'),(273,88,'600','MARSHMALLOW GONGYS STICK CAJAx216g 18UNID','venta',1.000,'-',2.000,1.000,'factura',10,NULL,3,'Administrador','2026-06-01 17:10:04'),(274,128,'741','ALF PESCADO RAUL SIMPLE BLANCO.x50g','venta',12.000,'-',63.000,51.000,'factura',10,NULL,3,'Administrador','2026-06-01 17:10:04'),(275,148,'934','BAGGIO MULTIFRUTAL.......x200m','venta',18.000,'-',84.000,66.000,'factura',10,NULL,3,'Administrador','2026-06-01 17:10:04'),(295,38,'266','MOGUL MORAS X 500G','compra',6.000,'+',3.000,9.000,'factura_compra',1,'Compra a proveedor (factura compra #1)',NULL,'Sistema','2026-06-01 21:17:05'),(296,39,'267','MOGUL DIENTES X 500G','compra',6.000,'+',7.000,13.000,'factura_compra',1,'Compra a proveedor (factura compra #1)',NULL,'Sistema','2026-06-01 21:17:05'),(297,100,'708','BONOBON OBLEA LECHE....20ux30g','compra',320.000,'+',0.000,320.000,'factura_compra',1,'Compra a proveedor (factura compra #1)',NULL,'Sistema','2026-06-01 21:17:05'),(298,201,'3466','BONOBON OBLEA BLANCO 20X30G','compra',160.000,'+',0.000,160.000,'factura_compra',1,'Compra a proveedor (factura compra #1)',NULL,'Sistema','2026-06-01 21:17:05'),(299,123,'736','ALF COFLER BLOCK TRIPLE...x60g','compra',168.000,'+',0.000,168.000,'factura_compra',1,'Compra a proveedor (factura compra #1)',NULL,'Sistema','2026-06-01 21:17:05'),(300,86,'529','MENTHO PLUS CEREZA........x12u','compra',12.000,'+',1.000,13.000,'factura_compra',1,'Compra a proveedor (factura compra #1)',NULL,'Sistema','2026-06-01 21:17:05'),(301,84,'527','MENTHO PLUS STRONG........x12u','compra',12.000,'+',1.000,13.000,'factura_compra',1,'Compra a proveedor (factura compra #1)',NULL,'Sistema','2026-06-01 21:17:05'),(302,87,'530','MENTHO PLUS MIEL..........x12u','compra',12.000,'+',0.000,12.000,'factura_compra',1,'Compra a proveedor (factura compra #1)',NULL,'Sistema','2026-06-01 21:17:05'),(303,1,'102','CHICLE FIERITA RECARGADO MENTA X50U','compra',12.000,'+',4.000,16.000,'factura_compra',1,'Compra a proveedor (factura compra #1)',NULL,'Sistema','2026-06-01 21:17:05'),(304,40,'268','MOGUL FRUTILLAS CON CREMA X 500G','compra',6.000,'+',6.000,12.000,'factura_compra',1,'Compra a proveedor (factura compra #1)',NULL,'Sistema','2026-06-01 21:17:05'),(305,104,'713','BOMBONES BON O BON 30 X 15GS','compra',12.000,'+',0.000,12.000,'factura_compra',1,'Compra a proveedor (factura compra #1)',NULL,'Sistema','2026-06-01 21:17:05'),(306,191,'276','MOGUL FRUTILLA ACIDA X 500','compra',6.000,'+',0.000,6.000,'factura_compra',1,'Compra a proveedor (factura compra #1)',NULL,'Sistema','2026-06-01 21:17:05'),(307,47,'275','MOGUL EXTREME OSITOS X 500G','compra',6.000,'+',0.000,6.000,'factura_compra',1,'Compra a proveedor (factura compra #1)',NULL,'Sistema','2026-06-01 21:17:05'),(308,194,'742','ALF MINI TORTA AGUILA X69G','compra',168.000,'+',6.000,174.000,'factura_compra',1,'Compra a proveedor (factura compra #1)',NULL,'Sistema','2026-06-01 21:17:05'),(309,195,'743','ALF MINI TORTA AGUILA BROWNIE X74G','compra',168.000,'+',4.000,172.000,'factura_compra',1,'Compra a proveedor (factura compra #1)',NULL,'Sistema','2026-06-01 21:17:05'),(310,132,'900','JUGO ARCOR POLVO NARANJA..x18u','compra',12.000,'+',0.000,12.000,'factura_compra',1,'Compra a proveedor (factura compra #1)',NULL,'Sistema','2026-06-01 21:17:05'),(311,136,'904','JUGO ARCOR POLVO MULTIFRUTx18u','compra',12.000,'+',0.000,12.000,'factura_compra',1,'Compra a proveedor (factura compra #1)',NULL,'Sistema','2026-06-01 21:17:05'),(312,139,'907','JUGO ARCOR POLVO NARANJA BANANA.x18u','compra',12.000,'+',0.000,12.000,'factura_compra',1,'Compra a proveedor (factura compra #1)',NULL,'Sistema','2026-06-01 21:17:05'),(313,141,'909','JUGO ARCOR POLVO NARANJA MANGO.x18u','compra',12.000,'+',3.000,15.000,'factura_compra',1,'Compra a proveedor (factura compra #1)',NULL,'Sistema','2026-06-01 21:17:05'),(314,138,'906','JUGO ARCOR POLVO FRUT/ANANA/BANANA','compra',12.000,'+',0.000,12.000,'factura_compra',1,'Compra a proveedor (factura compra #1)',NULL,'Sistema','2026-06-01 21:17:05'),(315,122,'735','ALF BON O BON TRIPLE NEGROx60g','compra',168.000,'+',0.000,168.000,'factura_compra',1,'Compra a proveedor (factura compra #1)',NULL,'Sistema','2026-06-01 21:17:05'),(316,121,'729','ALFAJOR CHOCOTORTA 71,5','compra',168.000,'+',0.000,168.000,'factura_compra',1,'Compra a proveedor (factura compra #1)',NULL,'Sistema','2026-06-01 21:17:05'),(320,131,'801','GIRASOL PIPAS GIGANTES.12ux50g','venta',1.000,'-',7.000,6.000,'factura',11,NULL,3,'Administrador','2026-06-01 23:04:43'),(321,94,'702','CHOCOLATE MISKY  NGRO x25g','venta',16.000,'-',76.000,60.000,'factura',11,NULL,3,'Administrador','2026-06-01 23:04:43'),(322,52,'285','GOMITA DOCILE MIX DULCE/ACIDO X500','venta',1.000,'-',17.000,16.000,'factura',11,NULL,3,'Administrador','2026-06-01 23:04:43'),(323,56,'305','MR.POPS ARQUIT.FTAL.......x50u','venta',1.000,'-',9.000,8.000,'factura',11,NULL,3,'Administrador','2026-06-01 23:04:43'),(324,109,'714','GUAYMALLEN TRIPLE CHOCOLATE','venta',6.000,'-',198.000,192.000,'factura',11,NULL,3,'Administrador','2026-06-01 23:04:43'),(325,110,'715','GUAYMALLEN TRIPLE BLANCO','venta',3.000,'-',124.000,121.000,'factura',11,NULL,3,'Administrador','2026-06-01 23:04:43'),(326,113,'718','ALF FANTOCHE TRI.CHOCOLATEx85g','venta',6.000,'-',35.000,29.000,'factura',11,NULL,3,'Administrador','2026-06-01 23:04:43'),(327,114,'719','ALF FANTOCHE TRIPLE BLANCO.x85g','venta',3.000,'-',110.000,107.000,'factura',11,NULL,3,'Administrador','2026-06-01 23:04:43'),(328,127,'740','ALF PESCADO RAUL SIMPLE NEGRO.x50g','venta',4.000,'-',133.000,129.000,'factura',11,NULL,3,'Administrador','2026-06-01 23:04:43'),(329,128,'741','ALF PESCADO RAUL SIMPLE BLANCO.x50g','venta',4.000,'-',51.000,47.000,'factura',11,NULL,3,'Administrador','2026-06-01 23:04:43'),(330,126,'739','ALF RASTA MAICENA TRICOx100g','venta',4.000,'-',13.000,9.000,'factura',11,NULL,3,'Administrador','2026-06-01 23:04:43'),(331,120,'728','ALF FANTOCHE SUPER TRIPLE NEGx100g','venta',4.000,'-',109.000,105.000,'factura',11,NULL,3,'Administrador','2026-06-01 23:04:43'),(336,130,'800','GIRASOL PIPAS..........30ux18g','venta',4.000,'-',8.000,4.000,'factura',12,NULL,3,'Administrador','2026-06-02 17:54:58'),(337,145,'931','BAGGIO DURAZNO...........x200m','venta',36.000,'-',45.000,9.000,'factura',12,NULL,3,'Administrador','2026-06-02 17:54:58'),(338,146,'932','BAGGIO MANZANA...........x200m','venta',36.000,'-',36.000,0.000,'factura',12,NULL,3,'Administrador','2026-06-02 17:54:58'),(339,147,'933','BAGGIO NARANJA...........x200m','venta',18.000,'-',21.000,3.000,'factura',12,NULL,3,'Administrador','2026-06-02 17:54:58'),(340,148,'934','BAGGIO MULTIFRUTAL.......x200m','venta',36.000,'-',66.000,30.000,'factura',12,NULL,3,'Administrador','2026-06-02 17:54:58'),(341,204,'975','CEREAL MIX YOGH/FRUT.LIGHT X28G','venta',40.000,'-',40.000,0.000,'factura',12,NULL,3,'Administrador','2026-06-02 17:54:58'),(342,203,'974','CEREAL MIX ORIGINAL X23G','venta',10.000,'-',10.000,0.000,'factura',12,NULL,3,'Administrador','2026-06-02 17:54:58'),(343,202,'973','CEREAL MIX PLACERES CHOCOL X23G','venta',10.000,'-',10.000,0.000,'factura',12,NULL,3,'Administrador','2026-06-02 17:54:58'),(344,206,'3000','PROD VARIOS','compra',1.000,'+',0.000,1.000,'factura_compra',2,'Compra a proveedor (factura compra #2)',3,'Administrador','2026-06-02 21:23:14'),(345,120,'728','ALF FANTOCHE SUPER TRIPLE NEGx100g','compra',180.000,'+',105.000,285.000,'factura_compra',3,'Compra a proveedor (factura compra #3)',3,'Administrador','2026-06-02 23:48:53'),(346,95,'703','CHOCOLATE MISKY  BCO x25g','compra',180.000,'+',78.000,258.000,'factura_compra',3,'Compra a proveedor (factura compra #3)',3,'Administrador','2026-06-02 23:48:53'),(347,94,'702','CHOCOLATE MISKY  NGRO x25g','compra',180.000,'+',60.000,240.000,'factura_compra',3,'Compra a proveedor (factura compra #3)',3,'Administrador','2026-06-02 23:48:54'),(348,128,'741','ALF PESCADO RAUL SIMPLE BLANCO.x50g','compra',120.000,'+',47.000,167.000,'factura_compra',3,'Compra a proveedor (factura compra #3)',3,'Administrador','2026-06-02 23:48:54'),(349,127,'740','ALF PESCADO RAUL SIMPLE NEGRO.x50g','compra',120.000,'+',129.000,249.000,'factura_compra',3,'Compra a proveedor (factura compra #3)',3,'Administrador','2026-06-02 23:48:54'),(350,6,'140','BELDENT FRESH SPARKS MENTAx20u','compra',6.000,'+',0.000,6.000,'factura_compra',3,'Compra a proveedor (factura compra #3)',3,'Administrador','2026-06-02 23:48:54'),(351,163,'1023','.9 DE ORO AGRIDULCE','compra',60.000,'+',7.000,67.000,'factura_compra',3,'Compra a proveedor (factura compra #3)',3,'Administrador','2026-06-02 23:48:54'),(352,164,'1024','.9 DE ORO AZUCARADO','compra',28.000,'+',25.000,53.000,'factura_compra',3,'Compra a proveedor (factura compra #3)',3,'Administrador','2026-06-02 23:48:54'),(353,162,'1022','.9 DE ORO GRASA','compra',24.000,'+',100.000,124.000,'factura_compra',3,'Compra a proveedor (factura compra #3)',3,'Administrador','2026-06-02 23:48:54'),(354,52,'285','GOMITA DOCILE MIX DULCE/ACIDO X500','compra',20.000,'+',16.000,36.000,'factura_compra',3,'Compra a proveedor (factura compra #3)',3,'Administrador','2026-06-02 23:48:54'),(355,29,'232','GOMA EUCALIPTUS MISKY......x1k','compra',1.000,'+',4.000,5.000,'factura_compra',3,'Compra a proveedor (factura compra #3)',3,'Administrador','2026-06-02 23:48:54'),(356,27,'230','GOMA FANTASIA MISKY .......x1k','compra',4.000,'+',6.000,10.000,'factura_compra',3,'Compra a proveedor (factura compra #3)',3,'Administrador','2026-06-02 23:48:54'),(357,13,'203','GOMITAS YUMMY 100 PIES ACIDAS X 500 GR','compra',3.000,'+',1.000,4.000,'factura_compra',3,'Compra a proveedor (factura compra #3)',3,'Administrador','2026-06-02 23:48:54'),(358,19,'209','YUMMY BOTELLITAS BOLSA...x500g','compra',3.000,'+',0.000,3.000,'factura_compra',3,'Compra a proveedor (factura compra #3)',3,'Administrador','2026-06-02 23:48:54'),(359,17,'207','GOMITAS YUMMY DIENTITOS X 500 GR','compra',12.000,'+',0.000,12.000,'factura_compra',3,'Compra a proveedor (factura compra #3)',3,'Administrador','2026-06-02 23:48:54'),(360,12,'202','GOMITAS YUMMY FRUTILLITAS CON CREMA X 500 GR','compra',6.000,'+',0.000,6.000,'factura_compra',3,'Compra a proveedor (factura compra #3)',3,'Administrador','2026-06-02 23:48:54'),(361,18,'208','YUMMY HUEVOS FRITOS BOLSA.x500g','compra',3.000,'+',0.000,3.000,'factura_compra',3,'Compra a proveedor (factura compra #3)',3,'Administrador','2026-06-02 23:48:54'),(362,10,'200','GOMITAS YUMMY OSITOS ACIDOS X 500 GR','compra',3.000,'+',1.000,4.000,'factura_compra',3,'Compra a proveedor (factura compra #3)',3,'Administrador','2026-06-02 23:48:54'),(363,11,'201','GOMITAS YUMMY OSITOS X 500 GR','compra',3.000,'+',1.000,4.000,'factura_compra',3,'Compra a proveedor (factura compra #3)',3,'Administrador','2026-06-02 23:48:54'),(364,129,'751','TURRON MISKY','compra',200.000,'+',43.000,243.000,'factura_compra',3,'Compra a proveedor (factura compra #3)',3,'Administrador','2026-06-02 23:48:54'),(365,144,'918','CERVEZA 361 PET............x1l','compra',60.000,'+',44.000,104.000,'factura_compra',3,'Compra a proveedor (factura compra #3)',3,'Administrador','2026-06-02 23:48:54'),(366,13,'203','GOMITAS YUMMY 100 PIES ACIDAS X 500 GR','venta',1.000,'-',4.000,3.000,'factura',13,NULL,3,'Administrador','2026-06-03 23:27:55'),(367,34,'252','GOMA BULL DOG.REGALIZ TUTTI F.CJAx12u','venta',1.000,'-',11.000,10.000,'factura',13,NULL,3,'Administrador','2026-06-03 23:27:55'),(368,52,'285','GOMITA DOCILE MIX DULCE/ACIDO X500','venta',1.000,'-',36.000,35.000,'factura',13,NULL,3,'Administrador','2026-06-03 23:27:55'),(369,54,'303','MR.POPS EVOLUT.BLUE BERRY.x24u','venta',1.000,'-',5.000,4.000,'factura',13,NULL,3,'Administrador','2026-06-03 23:27:55'),(370,135,'903','JUGO ARCOR POLVO MANZANA..x18u','venta',2.000,'-',15.000,13.000,'factura',13,NULL,3,'Administrador','2026-06-03 23:27:55'),(371,138,'906','JUGO ARCOR POLVO FRUT/ANANA/BANANA','venta',1.000,'-',12.000,11.000,'factura',13,NULL,3,'Administrador','2026-06-03 23:27:55'),(372,38,'266','MOGUL MORAS X 500G','venta',1.000,'-',9.000,8.000,'factura',13,NULL,3,'Administrador','2026-06-03 23:27:55'),(373,43,'271','MOGUL EXTREME LADRILLOS MIX FRUTAL X 500G','venta',2.000,'-',9.000,7.000,'factura',13,NULL,3,'Administrador','2026-06-03 23:27:55'),(374,21,'221','YUMMY DINO X 12 UND','venta',1.000,'-',4.000,3.000,'factura',13,NULL,3,'Administrador','2026-06-03 23:27:55'),(375,190,'144','TOP LINE SEVEN MENTA','venta',1.000,'-',13.000,12.000,'factura',13,NULL,3,'Administrador','2026-06-03 23:27:55'),(376,65,'404','PALITO DE LA SELVA.......x660g','venta',1.000,'-',11.000,10.000,'factura',13,NULL,3,'Administrador','2026-06-03 23:27:55'),(377,27,'230','GOMA FANTASIA MISKY .......x1k','venta',1.000,'-',10.000,9.000,'factura',13,NULL,3,'Administrador','2026-06-03 23:27:55'),(378,28,'231','GOMA JELLY ROLL MISKY......x1k','venta',1.000,'-',5.000,4.000,'factura',13,NULL,3,'Administrador','2026-06-03 23:27:55'),(379,130,'800','GIRASOL PIPAS..........30ux18g','venta',1.000,'-',4.000,3.000,'factura',14,NULL,3,'Administrador','2026-06-04 11:30:07'),(380,155,'1010','DON SATUR BIZCOCH.GRASA x200g','venta',10.000,'-',114.000,104.000,'factura',14,NULL,3,'Administrador','2026-06-04 11:30:07'),(381,156,'1011','DON SATUR BIZCOCHO DULCE.x200g','venta',10.000,'-',32.000,22.000,'factura',14,NULL,3,'Administrador','2026-06-04 11:30:07'),(382,157,'1012','DON SATUR BIZCOCH.NEGRITOx200g','venta',10.000,'-',42.000,32.000,'factura',14,NULL,3,'Administrador','2026-06-04 11:30:07'),(383,197,'1033','SERRANITAS OFERTA 14 X3 X315G','venta',14.000,'-',70.000,56.000,'factura',14,NULL,3,'Administrador','2026-06-04 11:30:07'),(384,188,'6886','MENTHO PLUS ((SURTIDO))......x12u','venta',1.000,'-',3.000,2.000,'factura',14,NULL,3,'Administrador','2026-06-04 11:30:07'),(385,13,'203','GOMITAS YUMMY 100 PIES ACIDAS X 500 GR','venta',1.000,'-',3.000,2.000,'factura',15,NULL,3,'Administrador','2026-06-04 11:34:44'),(386,14,'204','GOMITAS YUMMY SANDIA  X500GR','venta',1.000,'-',3.000,2.000,'factura',15,NULL,3,'Administrador','2026-06-04 11:34:44'),(387,37,'260','(12ux35g)GOMA MISKY ROLL......','venta',1.000,'-',4.000,3.000,'factura',15,NULL,3,'Administrador','2026-06-04 11:34:44'),(388,117,'722','ALFAJOR GULA NEGRO X 18U','venta',4.000,'-',51.000,47.000,'factura',15,NULL,3,'Administrador','2026-06-04 11:34:44'),(389,118,'723','ALFAJOR GULA BLANCO X 18U','venta',4.000,'-',18.000,14.000,'factura',15,NULL,3,'Administrador','2026-06-04 11:34:44'),(390,119,'724','ALFAJOR GULA KING RALLADO X 18U','venta',4.000,'-',18.000,14.000,'factura',15,NULL,3,'Administrador','2026-06-04 11:34:44'),(391,175,'968','MANI TARRO CON PIEL','venta',3.000,'-',30.000,27.000,'factura',15,NULL,3,'Administrador','2026-06-04 11:34:44'),(392,176,'969','MANI TARRO SIN PIEL','venta',3.000,'-',23.000,20.000,'factura',15,NULL,3,'Administrador','2026-06-04 11:34:44'),(393,13,'203','GOMITAS YUMMY 100 PIES ACIDAS X 500 GR','devolucion',1.000,'+',2.000,3.000,'factura',15,'Anulación factura 0006-X0000010 - OTRO CLIENTE',3,'Administrador','2026-06-04 11:35:32'),(394,14,'204','GOMITAS YUMMY SANDIA  X500GR','devolucion',1.000,'+',2.000,3.000,'factura',15,'Anulación factura 0006-X0000010 - OTRO CLIENTE',3,'Administrador','2026-06-04 11:35:32'),(395,37,'260','(12ux35g)GOMA MISKY ROLL......','devolucion',1.000,'+',3.000,4.000,'factura',15,'Anulación factura 0006-X0000010 - OTRO CLIENTE',3,'Administrador','2026-06-04 11:35:32'),(396,117,'722','ALFAJOR GULA NEGRO X 18U','devolucion',4.000,'+',47.000,51.000,'factura',15,'Anulación factura 0006-X0000010 - OTRO CLIENTE',3,'Administrador','2026-06-04 11:35:32'),(397,118,'723','ALFAJOR GULA BLANCO X 18U','devolucion',4.000,'+',14.000,18.000,'factura',15,'Anulación factura 0006-X0000010 - OTRO CLIENTE',3,'Administrador','2026-06-04 11:35:32'),(398,119,'724','ALFAJOR GULA KING RALLADO X 18U','devolucion',4.000,'+',14.000,18.000,'factura',15,'Anulación factura 0006-X0000010 - OTRO CLIENTE',3,'Administrador','2026-06-04 11:35:32'),(399,175,'968','MANI TARRO CON PIEL','devolucion',3.000,'+',27.000,30.000,'factura',15,'Anulación factura 0006-X0000010 - OTRO CLIENTE',3,'Administrador','2026-06-04 11:35:32'),(400,176,'969','MANI TARRO SIN PIEL','devolucion',3.000,'+',20.000,23.000,'factura',15,'Anulación factura 0006-X0000010 - OTRO CLIENTE',3,'Administrador','2026-06-04 11:35:32'),(401,21,'221','YUMMY DINO X 12 UND','venta',1.000,'-',3.000,2.000,'factura',16,NULL,3,'Administrador','2026-06-04 11:52:12'),(402,24,'224','YUMMY OSITOS X 12 UND','venta',1.000,'-',3.000,2.000,'factura',16,NULL,3,'Administrador','2026-06-04 11:52:12'),(403,25,'225','YUMMY PECECITOS X 12 UND','venta',1.000,'-',4.000,3.000,'factura',16,NULL,3,'Administrador','2026-06-04 11:52:12'),(404,132,'900','JUGO ARCOR POLVO NARANJA..x18u','venta',1.000,'-',12.000,11.000,'factura',16,NULL,3,'Administrador','2026-06-04 11:52:12'),(405,184,'3333','GOMA BULL DOG.REGALIZ (((SURTIDAS))).CJAx12u','venta',1.000,'-',3.000,2.000,'factura',16,NULL,3,'Administrador','2026-06-04 11:52:12'),(406,13,'203','GOMITAS YUMMY 100 PIES ACIDAS X 500 GR','venta',1.000,'-',3.000,2.000,'factura',17,NULL,3,'Administrador','2026-06-04 11:57:08'),(407,14,'204','GOMITAS YUMMY SANDIA  X500GR','venta',1.000,'-',3.000,2.000,'factura',17,NULL,3,'Administrador','2026-06-04 11:57:08'),(408,37,'260','(12ux35g)GOMA MISKY ROLL......','venta',1.000,'-',4.000,3.000,'factura',17,NULL,3,'Administrador','2026-06-04 11:57:08'),(409,117,'722','ALFAJOR GULA NEGRO X 18U','venta',4.000,'-',51.000,47.000,'factura',17,NULL,3,'Administrador','2026-06-04 11:57:08'),(410,118,'723','ALFAJOR GULA BLANCO X 18U','venta',4.000,'-',18.000,14.000,'factura',17,NULL,3,'Administrador','2026-06-04 11:57:08'),(411,119,'724','ALFAJOR GULA KING RALLADO X 18U','venta',4.000,'-',18.000,14.000,'factura',17,NULL,3,'Administrador','2026-06-04 11:57:08'),(412,175,'968','MANI TARRO CON PIEL','venta',3.000,'-',30.000,27.000,'factura',17,NULL,3,'Administrador','2026-06-04 11:57:08'),(413,176,'969','MANI TARRO SIN PIEL','venta',3.000,'-',23.000,20.000,'factura',17,NULL,3,'Administrador','2026-06-04 11:57:08'),(414,17,'207','GOMITAS YUMMY DIENTITOS X 500 GR','venta',2.000,'-',12.000,10.000,'factura',18,NULL,3,'Administrador','2026-06-04 12:07:01'),(415,18,'208','YUMMY HUEVOS FRITOS BOLSA.x500g','venta',2.000,'-',3.000,1.000,'factura',18,NULL,3,'Administrador','2026-06-04 12:07:01'),(416,27,'230','GOMA FANTASIA MISKY .......x1k','venta',1.000,'-',9.000,8.000,'factura',18,NULL,3,'Administrador','2026-06-04 12:07:01'),(417,38,'266','MOGUL MORAS X 500G','venta',1.000,'-',8.000,7.000,'factura',18,NULL,3,'Administrador','2026-06-04 12:07:01'),(418,98,'706','BOCADITO NEVARES DUL.D/LECx15u','venta',1.000,'-',19.000,18.000,'factura',18,NULL,3,'Administrador','2026-06-04 12:07:01'),(419,100,'708','BONOBON OBLEA LECHE....20ux30g','venta',10.000,'-',320.000,310.000,'factura',18,NULL,3,'Administrador','2026-06-04 12:07:01'),(420,102,'710','OBLEA SMACK RELLENA X33g','venta',6.000,'-',42.000,36.000,'factura',18,NULL,3,'Administrador','2026-06-04 12:07:01'),(421,113,'718','ALF FANTOCHE TRI.CHOCOLATEx85g','venta',8.000,'-',29.000,21.000,'factura',18,NULL,3,'Administrador','2026-06-04 12:07:01'),(422,114,'719','ALF FANTOCHE TRIPLE BLANCO.x85g','venta',4.000,'-',107.000,103.000,'factura',18,NULL,3,'Administrador','2026-06-04 12:07:01'),(423,122,'735','ALF BON O BON TRIPLE NEGROx60g','venta',6.000,'-',168.000,162.000,'factura',18,NULL,3,'Administrador','2026-06-04 12:07:01'),(424,148,'934','BAGGIO MULTIFRUTAL.......x200m','venta',6.000,'-',30.000,24.000,'factura',18,NULL,3,'Administrador','2026-06-04 12:07:01'),(425,155,'1010','DON SATUR BIZCOCH.GRASA x200g','venta',4.000,'-',104.000,100.000,'factura',18,NULL,3,'Administrador','2026-06-04 12:07:01'),(426,162,'1022','.9 DE ORO GRASA','venta',4.000,'-',124.000,120.000,'factura',18,NULL,3,'Administrador','2026-06-04 12:07:01'),(427,163,'1023','.9 DE ORO AGRIDULCE','venta',5.000,'-',67.000,62.000,'factura',18,NULL,3,'Administrador','2026-06-04 12:07:01'),(428,197,'1033','SERRANITAS OFERTA 14 X3 X315G','venta',3.000,'-',56.000,53.000,'factura',18,NULL,3,'Administrador','2026-06-04 12:07:01'),(429,170,'961','MANI TARRO CERVECERO PIZZA','venta',2.000,'-',9.000,7.000,'factura',18,NULL,3,'Administrador','2026-06-04 12:07:01'),(430,16,'206','GOMITAS YUMMY MORITAS X500G','venta',1.000,'-',7.000,6.000,'factura',19,NULL,3,'Administrador','2026-06-04 12:11:20'),(431,27,'230','GOMA FANTASIA MISKY .......x1k','venta',1.000,'-',8.000,7.000,'factura',19,NULL,3,'Administrador','2026-06-04 12:11:20'),(432,38,'266','MOGUL MORAS X 500G','venta',1.000,'-',7.000,6.000,'factura',19,NULL,3,'Administrador','2026-06-04 12:11:20'),(433,39,'267','MOGUL DIENTES X 500G','venta',1.000,'-',13.000,12.000,'factura',19,NULL,3,'Administrador','2026-06-04 12:11:20'),(434,42,'270','MOGUL EXTREME LADRILLOS X 500G','venta',1.000,'-',20.000,19.000,'factura',19,NULL,3,'Administrador','2026-06-04 12:11:20'),(435,43,'271','MOGUL EXTREME LADRILLOS MIX FRUTAL X 500G','venta',1.000,'-',7.000,6.000,'factura',19,NULL,3,'Administrador','2026-06-04 12:11:20'),(436,94,'702','CHOCOLATE MISKY  NGRO x25g','venta',6.000,'-',240.000,234.000,'factura',19,NULL,3,'Administrador','2026-06-04 12:11:20'),(437,95,'703','CHOCOLATE MISKY  BCO x25g','venta',6.000,'-',258.000,252.000,'factura',19,NULL,3,'Administrador','2026-06-04 12:11:20'),(438,98,'706','BOCADITO NEVARES DUL.D/LECx15u','venta',1.000,'-',18.000,17.000,'factura',19,NULL,3,'Administrador','2026-06-04 12:11:20'),(439,113,'718','ALF FANTOCHE TRI.CHOCOLATEx85g','venta',6.000,'-',21.000,15.000,'factura',19,NULL,3,'Administrador','2026-06-04 12:11:20'),(440,114,'719','ALF FANTOCHE TRIPLE BLANCO.x85g','venta',6.000,'-',103.000,97.000,'factura',19,NULL,3,'Administrador','2026-06-04 12:11:20'),(441,121,'729','ALFAJOR CHOCOTORTA 71,5','venta',6.000,'-',168.000,162.000,'factura',19,NULL,3,'Administrador','2026-06-04 12:11:20'),(442,123,'736','ALF COFLER BLOCK TRIPLE...x60g','venta',6.000,'-',168.000,162.000,'factura',19,NULL,3,'Administrador','2026-06-04 12:11:20'),(443,195,'743','ALF MINI TORTA AGUILA BROWNIE X74G','venta',6.000,'-',172.000,166.000,'factura',19,NULL,3,'Administrador','2026-06-04 12:11:20'),(444,166,'1030','SURTIDO BAGLEY...........x400g','venta',6.000,'-',95.000,89.000,'factura',19,NULL,3,'Administrador','2026-06-04 12:11:20'),(445,12,'202','GOMITAS YUMMY FRUTILLITAS CON CREMA X 500 GR','venta',1.000,'-',6.000,5.000,'factura',20,NULL,3,'Administrador','2026-06-04 12:43:48'),(446,13,'203','GOMITAS YUMMY 100 PIES ACIDAS X 500 GR','venta',1.000,'-',2.000,1.000,'factura',20,NULL,3,'Administrador','2026-06-04 12:43:48'),(447,15,'205','YUMMY BANANITAS BOLSA....x500g','venta',1.000,'-',1.000,0.000,'factura',20,NULL,3,'Administrador','2026-06-04 12:43:48'),(448,16,'206','GOMITAS YUMMY MORITAS X500G','venta',1.000,'-',6.000,5.000,'factura',20,NULL,3,'Administrador','2026-06-04 12:43:48'),(449,17,'207','GOMITAS YUMMY DIENTITOS X 500 GR','venta',2.000,'-',10.000,8.000,'factura',20,NULL,3,'Administrador','2026-06-04 12:43:48'),(450,27,'230','GOMA FANTASIA MISKY .......x1k','venta',1.000,'-',7.000,6.000,'factura',20,NULL,3,'Administrador','2026-06-04 12:43:48'),(451,28,'231','GOMA JELLY ROLL MISKY......x1k','venta',1.000,'-',4.000,3.000,'factura',20,NULL,3,'Administrador','2026-06-04 12:43:48'),(452,29,'232','GOMA EUCALIPTUS MISKY......x1k','venta',1.000,'-',5.000,4.000,'factura',20,NULL,3,'Administrador','2026-06-04 12:43:48'),(453,32,'250','GOMA BULL DOG.REGALIZ SANDIA CJAx12u','venta',1.000,'-',1.000,0.000,'factura',20,NULL,3,'Administrador','2026-06-04 12:43:48'),(454,33,'251','GOMA BULL DOG.REGALIZ FRUT.CJAx12u','venta',1.000,'-',11.000,10.000,'factura',20,NULL,3,'Administrador','2026-06-04 12:43:48'),(455,34,'252','GOMA BULL DOG.REGALIZ TUTTI F.CJAx12u','venta',1.000,'-',10.000,9.000,'factura',20,NULL,3,'Administrador','2026-06-04 12:43:48'),(456,35,'253','GOMA BULL DOG.REGALIZ FRAMB.CJAx12u','venta',1.000,'-',11.000,10.000,'factura',20,NULL,3,'Administrador','2026-06-04 12:43:48'),(457,109,'714','GUAYMALLEN TRIPLE CHOCOLATE','venta',12.000,'-',192.000,180.000,'factura',20,NULL,3,'Administrador','2026-06-04 12:43:48'),(458,110,'715','GUAYMALLEN TRIPLE BLANCO','venta',12.000,'-',121.000,109.000,'factura',20,NULL,3,'Administrador','2026-06-04 12:43:48'),(459,111,'716','GUAYMALLEN SIMPLE BLANCO','venta',12.000,'-',510.000,498.000,'factura',20,NULL,3,'Administrador','2026-06-04 12:43:48'),(460,112,'717','GUAYMALLEN SIMPLE CHOCOLATE','venta',12.000,'-',532.000,520.000,'factura',20,NULL,3,'Administrador','2026-06-04 12:43:48'),(461,113,'718','ALF FANTOCHE TRI.CHOCOLATEx85g','venta',12.000,'-',15.000,3.000,'factura',20,NULL,3,'Administrador','2026-06-04 12:43:48'),(462,114,'719','ALF FANTOCHE TRIPLE BLANCO.x85g','venta',12.000,'-',97.000,85.000,'factura',20,NULL,3,'Administrador','2026-06-04 12:43:48'),(463,162,'1022','.9 DE ORO GRASA','venta',10.000,'-',120.000,110.000,'factura',20,NULL,3,'Administrador','2026-06-04 12:43:48'),(465,7,'141','BELDENT FRESH SPARKS MTA.Fx20u','venta',1.000,'-',6.000,5.000,'factura',21,NULL,3,'Administrador','2026-06-04 13:05:26'),(466,60,'310','CHUPETIN PUSH POP.........x20u','venta',1.000,'-',5.000,4.000,'factura',21,NULL,3,'Administrador','2026-06-04 13:05:26'),(467,113,'718','ALF FANTOCHE TRI.CHOCOLATEx85g','venta',12.000,'-',183.000,171.000,'factura',21,NULL,3,'Administrador','2026-06-04 13:05:26'),(468,114,'719','ALF FANTOCHE TRIPLE BLANCO.x85g','venta',12.000,'-',85.000,73.000,'factura',21,NULL,3,'Administrador','2026-06-04 13:05:27'),(469,195,'743','ALF MINI TORTA AGUILA BROWNIE X74G','venta',5.000,'-',166.000,161.000,'factura',21,NULL,3,'Administrador','2026-06-04 13:05:27'),(470,158,'1014','GALL TRIO PEPAS..........x320g','venta',8.000,'-',32.000,24.000,'factura',21,NULL,3,'Administrador','2026-06-04 13:05:27'),(471,159,'1015','GALL TRIO PEPAS C/CHIPS..x300g','venta',5.000,'-',55.000,50.000,'factura',21,NULL,3,'Administrador','2026-06-04 13:05:27'),(472,160,'1017','GALL TRIO TRICHOC........x300g','venta',5.000,'-',63.000,58.000,'factura',21,NULL,3,'Administrador','2026-06-04 13:05:27'),(473,161,'1018','GALL TRIO GLASY..........x300g','venta',5.000,'-',42.000,37.000,'factura',21,NULL,3,'Administrador','2026-06-04 13:05:27'),(474,166,'1030','SURTIDO BAGLEY...........x400g','venta',6.000,'-',89.000,83.000,'factura',21,NULL,3,'Administrador','2026-06-04 13:05:27'),(475,167,'1031','GALL.DIVERSION SURTIDA...x400g','venta',6.000,'-',97.000,91.000,'factura',21,NULL,3,'Administrador','2026-06-04 13:05:27'),(476,170,'961','MANI TARRO CERVECERO PIZZA','venta',2.000,'-',7.000,5.000,'factura',21,NULL,3,'Administrador','2026-06-04 13:05:27'),(477,171,'962','MANI TARRO CERVECERO JAMON','venta',2.000,'-',3.000,1.000,'factura',21,NULL,3,'Administrador','2026-06-04 13:05:27'),(478,172,'963','MANI TARRO  CERVECERO SALAME','venta',2.000,'-',26.000,24.000,'factura',21,NULL,3,'Administrador','2026-06-04 13:05:27'),(479,181,'1120','ENC COCINA CANDELA CLASICO x25','venta',1.000,'-',9.000,8.000,'factura',21,NULL,3,'Administrador','2026-06-04 13:05:27'),(481,30,'240','GOMAS LA PIÑATA HUESOS ACIDOS X 700 GR','venta',3.000,'-',3.000,0.000,'factura',22,NULL,3,'Administrador','2026-06-04 13:34:35'),(482,48,'281','GOMAS MOGUL COLA X 12 UNIDADES','venta',1.000,'-',4.000,3.000,'factura',22,NULL,3,'Administrador','2026-06-04 13:34:35'),(483,199,'286','GOMITAS DOCILE GAJOS SURTIDO X500','venta',2.000,'-',26.000,24.000,'factura',22,NULL,3,'Administrador','2026-06-04 13:34:35'),(484,68,'408','MASTICABLE BULLDOG X 700G','venta',3.000,'-',3.000,0.000,'factura',22,NULL,3,'Administrador','2026-06-04 13:34:35'),(485,72,'501','PASTILLAS BULL DOG UVA X12U','venta',1.000,'-',5.000,4.000,'factura',22,NULL,3,'Administrador','2026-06-04 13:34:35'),(486,74,'505','PASTILLAS BULL DOG SANDIA ACIDA X 12 UND','venta',1.000,'-',5.000,4.000,'factura',22,NULL,3,'Administrador','2026-06-04 13:34:35'),(487,75,'506','PASTILLAS BULL DOG TUTTI FRUTTI  LIMONX 12 UND','venta',1.000,'-',6.000,5.000,'factura',22,NULL,3,'Administrador','2026-06-04 13:34:35'),(488,76,'507','PASTILLAS BULL DOG LIMON EXTREME X12 UND','venta',1.000,'-',11.000,10.000,'factura',22,NULL,3,'Administrador','2026-06-04 13:34:35'),(489,80,'512','MENTITAS FRUTAL X 12 UND','venta',2.000,'-',17.000,15.000,'factura',22,NULL,3,'Administrador','2026-06-04 13:34:35'),(490,81,'513','MENTITAS KIDS TUTTI FRUTTI X12U','venta',3.000,'-',17.000,14.000,'factura',22,NULL,3,'Administrador','2026-06-04 13:34:35'),(491,82,'514','MENTITAS KIDS DULCE DE LECHE X 12 UND','venta',3.000,'-',18.000,15.000,'factura',22,NULL,3,'Administrador','2026-06-04 13:34:35'),(492,94,'702','CHOCOLATE MISKY  NGRO x25g','venta',30.000,'-',234.000,204.000,'factura',22,NULL,3,'Administrador','2026-06-04 13:34:35'),(493,95,'703','CHOCOLATE MISKY  BCO x25g','venta',30.000,'-',252.000,222.000,'factura',22,NULL,3,'Administrador','2026-06-04 13:34:35'),(494,96,'704','ROCKLETS 24 X 20GS','venta',1.000,'-',13.000,12.000,'factura',22,NULL,3,'Administrador','2026-06-04 13:34:35'),(495,98,'706','BOCADITO NEVARES DUL.D/LECx15u','venta',1.000,'-',17.000,16.000,'factura',22,NULL,3,'Administrador','2026-06-04 13:34:35'),(496,99,'707','CREMA KROOMY SURTIDOS ( 48u )','venta',1.000,'-',12.000,11.000,'factura',22,NULL,3,'Administrador','2026-06-04 13:34:35'),(497,102,'710','OBLEA SMACK RELLENA X33g','venta',48.000,'-',228.000,180.000,'factura',22,NULL,3,'Administrador','2026-06-04 13:34:35'),(498,103,'712','BOMBON SMACKX 30u','venta',1.000,'-',4.000,3.000,'factura',22,NULL,3,'Administrador','2026-06-04 13:34:35'),(499,109,'714','GUAYMALLEN TRIPLE CHOCOLATE','venta',24.000,'-',180.000,156.000,'factura',22,NULL,3,'Administrador','2026-06-04 13:34:35'),(500,111,'716','GUAYMALLEN SIMPLE BLANCO','venta',20.000,'-',498.000,478.000,'factura',22,NULL,3,'Administrador','2026-06-04 13:34:35'),(501,112,'717','GUAYMALLEN SIMPLE CHOCOLATE','venta',20.000,'-',520.000,500.000,'factura',22,NULL,3,'Administrador','2026-06-04 13:34:35'),(502,113,'718','ALF FANTOCHE TRI.CHOCOLATEx85g','venta',12.000,'-',171.000,159.000,'factura',22,NULL,3,'Administrador','2026-06-04 13:34:35'),(503,114,'719','ALF FANTOCHE TRIPLE BLANCO.x85g','venta',12.000,'-',73.000,61.000,'factura',22,NULL,3,'Administrador','2026-06-04 13:34:35'),(504,127,'740','ALF PESCADO RAUL SIMPLE NEGRO.x50g','venta',24.000,'-',249.000,225.000,'factura',22,NULL,3,'Administrador','2026-06-04 13:34:35'),(510,190,'144','TOP LINE SEVEN MENTA','venta',1.000,'-',12.000,11.000,'factura',23,NULL,3,'Administrador','2026-06-04 14:03:57'),(511,109,'714','GUAYMALLEN TRIPLE CHOCOLATE','venta',24.000,'-',156.000,132.000,'factura',23,NULL,3,'Administrador','2026-06-04 14:03:57'),(512,113,'718','ALF FANTOCHE TRI.CHOCOLATEx85g','venta',12.000,'-',159.000,147.000,'factura',23,NULL,3,'Administrador','2026-06-04 14:03:57'),(513,115,'720','ALFAJOR RASTA NEGRO X 18U','venta',4.000,'-',26.000,22.000,'factura',23,NULL,3,'Administrador','2026-06-04 14:03:57'),(514,116,'721','ALFAJOR RASTA BLANCO X 18U','venta',4.000,'-',10036.000,10032.000,'factura',23,NULL,3,'Administrador','2026-06-04 14:03:57'),(515,117,'722','ALFAJOR GULA NEGRO X 18U','venta',4.000,'-',47.000,43.000,'factura',23,NULL,3,'Administrador','2026-06-04 14:03:57'),(516,118,'723','ALFAJOR GULA BLANCO X 18U','venta',4.000,'-',14.000,10.000,'factura',23,NULL,3,'Administrador','2026-06-04 14:03:57'),(517,122,'735','ALF BON O BON TRIPLE NEGROx60g','venta',4.000,'-',162.000,158.000,'factura',23,NULL,3,'Administrador','2026-06-04 14:03:57'),(518,123,'736','ALF COFLER BLOCK TRIPLE...x60g','venta',4.000,'-',162.000,158.000,'factura',23,NULL,3,'Administrador','2026-06-04 14:03:57'),(519,188,'6886','MENTHO PLUS ((SURTIDO))......x12u','venta',1.000,'-',2.000,1.000,'factura',23,NULL,3,'Administrador','2026-06-04 14:03:57'),(520,189,'7076','BELDENT FRESH SPARKS SURTIDO','venta',1.000,'-',4.000,3.000,'factura',23,NULL,3,'Administrador','2026-06-04 14:03:57'),(521,166,'1030','SURTIDO BAGLEY...........x400g','venta',3.000,'-',83.000,80.000,'factura',24,NULL,3,'Administrador','2026-06-04 15:34:39'),(522,167,'1031','GALL.DIVERSION SURTIDA...x400g','venta',3.000,'-',91.000,88.000,'factura',24,NULL,3,'Administrador','2026-06-04 15:34:39'),(523,170,'961','MANI TARRO CERVECERO PIZZA','venta',2.000,'-',5.000,3.000,'factura',24,NULL,3,'Administrador','2026-06-04 15:34:40'),(524,172,'963','MANI TARRO  CERVECERO SALAME','venta',2.000,'-',24.000,22.000,'factura',24,NULL,3,'Administrador','2026-06-04 15:34:40'),(525,2,'103','CHICLE FIERITA RECARGADO TUTTI FRUTTI X50U','venta',1.000,'-',3.000,2.000,'factura',25,NULL,3,'Administrador','2026-06-04 15:36:59'),(526,3,'104','CHICLE FIERITA MENTA X100U','venta',1.000,'-',4.000,3.000,'factura',25,NULL,3,'Administrador','2026-06-04 15:36:59'),(527,7,'141','BELDENT FRESH SPARKS MTA.Fx20u','venta',1.000,'-',4.000,3.000,'factura',25,NULL,3,'Administrador','2026-06-04 15:36:59'),(528,27,'230','GOMA FANTASIA MISKY .......x1k','venta',2.000,'-',6.000,4.000,'factura',25,NULL,3,'Administrador','2026-06-04 15:36:59'),(529,56,'305','MR.POPS ARQUIT.FTAL.......x50u','venta',1.000,'-',8.000,7.000,'factura',25,NULL,3,'Administrador','2026-06-04 15:36:59'),(530,67,'407','MASTICABLE BILLIKEN YOGURT','venta',1.000,'-',18.000,17.000,'factura',25,NULL,3,'Administrador','2026-06-04 15:36:59'),(531,104,'713','BOMBONES BON O BON 30 X 15GS','venta',1.000,'-',12.000,11.000,'factura',25,NULL,3,'Administrador','2026-06-04 15:36:59'),(532,122,'735','ALF BON O BON TRIPLE NEGROx60g','venta',6.000,'-',158.000,152.000,'factura',25,NULL,3,'Administrador','2026-06-04 15:36:59'),(533,162,'1022','.9 DE ORO GRASA','venta',6.000,'-',110.000,104.000,'factura',25,NULL,3,'Administrador','2026-06-04 15:36:59'),(534,163,'1023','.9 DE ORO AGRIDULCE','venta',6.000,'-',62.000,56.000,'factura',25,NULL,3,'Administrador','2026-06-04 15:36:59'),(535,164,'1024','.9 DE ORO AZUCARADO','venta',6.000,'-',53.000,47.000,'factura',25,NULL,3,'Administrador','2026-06-04 15:36:59'),(536,109,'714','GUAYMALLEN TRIPLE CHOCOLATE','venta',12.000,'-',132.000,120.000,'factura',26,NULL,3,'Administrador','2026-06-04 15:38:56'),(537,110,'715','GUAYMALLEN TRIPLE BLANCO','venta',12.000,'-',109.000,97.000,'factura',26,NULL,3,'Administrador','2026-06-04 15:38:56'),(538,114,'719','ALF FANTOCHE TRIPLE BLANCO.x85g','venta',12.000,'-',61.000,49.000,'factura',26,NULL,3,'Administrador','2026-06-04 15:38:56'),(539,115,'720','ALFAJOR RASTA NEGRO X 18U','venta',5.000,'-',22.000,17.000,'factura',26,NULL,3,'Administrador','2026-06-04 15:38:56'),(540,116,'721','ALFAJOR RASTA BLANCO X 18U','venta',5.000,'-',10032.000,10027.000,'factura',26,NULL,3,'Administrador','2026-06-04 15:38:56'),(541,61,'311','CHUPETIN PICO-DULCE.......x48u','venta',1.000,'-',6.000,5.000,'factura',27,NULL,3,'Administrador','2026-06-04 15:41:34'),(542,156,'1011','DON SATUR BIZCOCHO DULCE.x200g','venta',6.000,'-',22.000,16.000,'factura',27,NULL,3,'Administrador','2026-06-04 15:41:34'),(543,163,'1023','.9 DE ORO AGRIDULCE','venta',6.000,'-',56.000,50.000,'factura',27,NULL,3,'Administrador','2026-06-04 15:41:34'),(544,170,'961','MANI TARRO CERVECERO PIZZA','venta',2.000,'-',3.000,1.000,'factura',27,NULL,3,'Administrador','2026-06-04 15:41:34'),(545,172,'963','MANI TARRO  CERVECERO SALAME','venta',2.000,'-',22.000,20.000,'factura',27,NULL,3,'Administrador','2026-06-04 15:41:34'),(546,174,'965','MANI TARRO CERVECERO PROVENZAL','venta',2.000,'-',15.000,13.000,'factura',27,NULL,3,'Administrador','2026-06-04 15:41:34'),(547,175,'968','MANI TARRO CON PIEL','venta',2.000,'-',27.000,25.000,'factura',27,NULL,3,'Administrador','2026-06-04 15:41:34'),(548,176,'969','MANI TARRO SIN PIEL','venta',2.000,'-',20.000,18.000,'factura',27,NULL,3,'Administrador','2026-06-04 15:41:34'),(549,29,'232','GOMA EUCALIPTUS MISKY......x1k','venta',1.000,'-',4.000,3.000,'factura',28,NULL,3,'Administrador','2026-06-04 15:46:13'),(550,87,'530','MENTHO PLUS MIEL..........x12u','venta',1.000,'-',12.000,11.000,'factura',28,NULL,3,'Administrador','2026-06-04 15:46:13'),(551,121,'729','ALFAJOR CHOCOTORTA 71,5','venta',3.000,'-',162.000,159.000,'factura',28,NULL,3,'Administrador','2026-06-04 15:46:13'),(552,131,'801','GIRASOL PIPAS GIGANTES.12ux50g','venta',1.000,'-',6.000,5.000,'factura',28,NULL,3,'Administrador','2026-06-04 15:46:13'),(553,148,'934','BAGGIO MULTIFRUTAL.......x200m','venta',9.000,'-',24.000,15.000,'factura',28,NULL,3,'Administrador','2026-06-04 15:46:13'),(554,145,'931','BAGGIO DURAZNO...........x200m','venta',9.000,'-',9.000,0.000,'factura',28,NULL,3,'Administrador','2026-06-04 15:46:13'),(555,155,'1010','DON SATUR BIZCOCH.GRASA x200g','venta',3.000,'-',100.000,97.000,'factura',28,NULL,3,'Administrador','2026-06-04 15:46:13'),(556,156,'1011','DON SATUR BIZCOCHO DULCE.x200g','venta',3.000,'-',16.000,13.000,'factura',28,NULL,3,'Administrador','2026-06-04 15:46:13'),(557,157,'1012','DON SATUR BIZCOCH.NEGRITOx200g','venta',1.000,'-',32.000,31.000,'factura',28,NULL,3,'Administrador','2026-06-04 15:46:13'),(558,162,'1022','.9 DE ORO GRASA','venta',3.000,'-',104.000,101.000,'factura',28,NULL,3,'Administrador','2026-06-04 15:46:13'),(559,173,'964','MANI TARRO CERVECERO QUESO','venta',2.000,'-',24.000,22.000,'factura',29,NULL,3,'Administrador','2026-06-04 15:50:55'),(560,174,'965','MANI TARRO CERVECERO PROVENZAL','venta',2.000,'-',13.000,11.000,'factura',29,NULL,3,'Administrador','2026-06-04 15:50:55'),(561,175,'968','MANI TARRO CON PIEL','venta',4.000,'-',25.000,21.000,'factura',29,NULL,3,'Administrador','2026-06-04 15:50:55'),(562,113,'718','ALF FANTOCHE TRI.CHOCOLATEx85g','venta',12.000,'-',147.000,135.000,'factura',30,NULL,3,'Administrador','2026-06-04 15:54:48'),(563,6,'140','BELDENT FRESH SPARKS MENTAx20u','venta',1.000,'-',5.000,4.000,'factura',31,NULL,3,'Administrador','2026-06-04 16:01:13'),(564,7,'141','BELDENT FRESH SPARKS MTA.Fx20u','venta',1.000,'-',3.000,2.000,'factura',31,NULL,3,'Administrador','2026-06-04 16:01:13'),(565,190,'144','TOP LINE SEVEN MENTA','venta',1.000,'-',11.000,10.000,'factura',31,NULL,3,'Administrador','2026-06-04 16:01:13'),(566,52,'285','GOMITA DOCILE MIX DULCE/ACIDO X500','venta',1.000,'-',35.000,34.000,'factura',31,NULL,3,'Administrador','2026-06-04 16:01:13'),(567,199,'286','GOMITAS DOCILE GAJOS SURTIDO X500','venta',1.000,'-',24.000,23.000,'factura',31,NULL,3,'Administrador','2026-06-04 16:01:13'),(568,200,'287','GOMITAS DOCILE CONITO SINO SUTIDO X500','venta',1.000,'-',9.000,8.000,'factura',31,NULL,3,'Administrador','2026-06-04 16:01:13'),(569,109,'714','GUAYMALLEN TRIPLE CHOCOLATE','venta',12.000,'-',120.000,108.000,'factura',31,NULL,3,'Administrador','2026-06-04 16:01:13'),(570,110,'715','GUAYMALLEN TRIPLE BLANCO','venta',12.000,'-',97.000,85.000,'factura',31,NULL,3,'Administrador','2026-06-04 16:01:13'),(571,84,'527','MENTHO PLUS STRONG........x12u','venta',1.000,'-',13.000,12.000,'factura',32,NULL,3,'Administrador','2026-06-04 16:06:31'),(572,87,'530','MENTHO PLUS MIEL..........x12u','venta',1.000,'-',11.000,10.000,'factura',32,NULL,3,'Administrador','2026-06-04 16:06:31'),(573,115,'720','ALFAJOR RASTA NEGRO X 18U','venta',9.000,'-',17.000,8.000,'factura',32,NULL,3,'Administrador','2026-06-04 16:06:31'),(574,115,'720','ALFAJOR RASTA NEGRO X 18U','venta',6.000,'-',8.000,2.000,'factura',33,NULL,3,'Administrador','2026-06-04 16:09:30'),(575,116,'721','ALFAJOR RASTA BLANCO X 18U','venta',6.000,'-',10027.000,10021.000,'factura',33,NULL,3,'Administrador','2026-06-04 16:09:30'),(576,117,'722','ALFAJOR GULA NEGRO X 18U','venta',6.000,'-',43.000,37.000,'factura',33,NULL,3,'Administrador','2026-06-04 16:09:30'),(577,118,'723','ALFAJOR GULA BLANCO X 18U','venta',6.000,'-',10.000,4.000,'factura',33,NULL,3,'Administrador','2026-06-04 16:09:30'),(578,161,'1018','GALL TRIO GLASY..........x300g','venta',6.000,'-',37.000,31.000,'factura',33,NULL,3,'Administrador','2026-06-04 16:09:30'),(579,94,'702','CHOCOLATE MISKY  NGRO x25g','venta',10.000,'-',204.000,194.000,'factura',34,NULL,3,'Administrador','2026-06-04 22:17:18'),(580,95,'703','CHOCOLATE MISKY  BCO x25g','venta',10.000,'-',222.000,212.000,'factura',34,NULL,3,'Administrador','2026-06-04 22:17:18'),(581,136,'904','JUGO ARCOR POLVO MULTIFRUTx18u','venta',1.000,'-',12.000,11.000,'factura',34,NULL,3,'Administrador','2026-06-04 22:17:18'),(582,156,'1011','DON SATUR BIZCOCHO DULCE.x200g','venta',30.000,'-',13.000,-17.000,'factura',34,NULL,3,'Administrador','2026-06-04 22:17:18'),(583,162,'1022','.9 DE ORO GRASA','venta',24.000,'-',101.000,77.000,'factura',34,NULL,3,'Administrador','2026-06-04 22:17:18'),(584,198,'1034','SERRANAS SANDWICH 16 X3X 112G','venta',16.000,'-',85.000,69.000,'factura',34,NULL,3,'Administrador','2026-06-04 22:17:18'),(585,16,'206','GOMITAS YUMMY MORITAS X500G','venta',2.000,'-',5.000,3.000,'factura',35,NULL,3,'Administrador','2026-06-04 22:26:48'),(586,113,'718','ALF FANTOCHE TRI.CHOCOLATEx85g','venta',10.000,'-',135.000,125.000,'factura',35,NULL,3,'Administrador','2026-06-04 22:26:48'),(587,114,'719','ALF FANTOCHE TRIPLE BLANCO.x85g','venta',10.000,'-',49.000,39.000,'factura',35,NULL,3,'Administrador','2026-06-04 22:26:48'),(588,122,'735','ALF BON O BON TRIPLE NEGROx60g','venta',5.000,'-',152.000,147.000,'factura',35,NULL,3,'Administrador','2026-06-04 22:26:48'),(589,123,'736','ALF COFLER BLOCK TRIPLE...x60g','venta',5.000,'-',158.000,153.000,'factura',35,NULL,3,'Administrador','2026-06-04 22:26:48'),(590,17,'207','GOMITAS YUMMY DIENTITOS X 500 GR','venta',2.000,'-',8.000,6.000,'factura',36,NULL,3,'Administrador','2026-06-04 22:55:59'),(591,18,'208','YUMMY HUEVOS FRITOS BOLSA.x500g','venta',1.000,'-',1.000,0.000,'factura',36,NULL,3,'Administrador','2026-06-04 22:55:59'),(592,33,'251','GOMA BULL DOG.REGALIZ FRUT.CJAx12u','venta',2.000,'-',10.000,8.000,'factura',36,NULL,3,'Administrador','2026-06-04 22:55:59'),(593,35,'253','GOMA BULL DOG.REGALIZ FRAMB.CJAx12u','venta',2.000,'-',10.000,8.000,'factura',36,NULL,3,'Administrador','2026-06-04 22:55:59'),(594,66,'406','CARAM.FLYNN PAFF TUTTI....x70u','venta',1.000,'-',14.000,13.000,'factura',36,NULL,3,'Administrador','2026-06-04 22:55:59'),(595,69,'409','CARAM.MAST.DROPSY SELVA..x700g','venta',2.000,'-',8.000,6.000,'factura',36,NULL,3,'Administrador','2026-06-04 22:55:59'),(596,72,'501','PASTILLAS BULL DOG UVA X12U','venta',2.000,'-',4.000,2.000,'factura',36,NULL,3,'Administrador','2026-06-04 22:55:59'),(597,76,'507','PASTILLAS BULL DOG LIMON EXTREME X12 UND','venta',2.000,'-',10.000,8.000,'factura',36,NULL,3,'Administrador','2026-06-04 22:55:59'),(598,80,'512','MENTITAS FRUTAL X 12 UND','venta',2.000,'-',15.000,13.000,'factura',36,NULL,3,'Administrador','2026-06-04 22:55:59'),(599,81,'513','MENTITAS KIDS TUTTI FRUTTI X12U','venta',2.000,'-',14.000,12.000,'factura',36,NULL,3,'Administrador','2026-06-04 22:55:59'),(600,82,'514','MENTITAS KIDS DULCE DE LECHE X 12 UND','venta',2.000,'-',15.000,13.000,'factura',36,NULL,3,'Administrador','2026-06-04 22:55:59'),(601,89,'601','(28g)MARSHMALLOW GONGYS FRUTIL','venta',20.000,'-',128.000,108.000,'factura',36,NULL,3,'Administrador','2026-06-04 22:55:59'),(602,90,'602','(28g)MARSHMALLOW GONGYS NUBECI','venta',20.000,'-',108.000,88.000,'factura',36,NULL,3,'Administrador','2026-06-04 22:55:59'),(603,92,'700','CHOC TOKKE C/LECHE Y MANI 62G','venta',6.000,'-',7.000,1.000,'factura',36,NULL,3,'Administrador','2026-06-04 22:55:59'),(604,93,'701','CHOC.TOKKE RELLE.D/LECHE..x72g','venta',6.000,'-',30.000,24.000,'factura',36,NULL,3,'Administrador','2026-06-04 22:55:59'),(605,94,'702','CHOCOLATE MISKY  NGRO x25g','venta',20.000,'-',194.000,174.000,'factura',36,NULL,3,'Administrador','2026-06-04 22:55:59'),(606,95,'703','CHOCOLATE MISKY  BCO x25g','venta',15.000,'-',212.000,197.000,'factura',36,NULL,3,'Administrador','2026-06-04 22:55:59'),(607,96,'704','ROCKLETS 24 X 20GS','venta',2.000,'-',12.000,10.000,'factura',36,NULL,3,'Administrador','2026-06-04 22:55:59'),(608,97,'705','CHOC. C/MANI COF. BLOCK 20X38GS','venta',6.000,'-',120.000,114.000,'factura',36,NULL,3,'Administrador','2026-06-04 22:55:59'),(609,99,'707','CREMA KROOMY SURTIDOS ( 48u )','venta',2.000,'-',11.000,9.000,'factura',36,NULL,3,'Administrador','2026-06-04 22:55:59'),(610,100,'708','BONOBON OBLEA LECHE....20ux30g','venta',15.000,'-',310.000,295.000,'factura',36,NULL,3,'Administrador','2026-06-04 22:55:59'),(611,109,'714','GUAYMALLEN TRIPLE CHOCOLATE','venta',15.000,'-',108.000,93.000,'factura',36,NULL,3,'Administrador','2026-06-04 22:55:59'),(612,106,'761','MECANO....................x19g','venta',6.000,'-',48.000,42.000,'factura',36,NULL,3,'Administrador','2026-06-04 22:55:59'),(613,148,'934','BAGGIO MULTIFRUTAL.......x200m','venta',15.000,'-',15.000,0.000,'factura',36,NULL,3,'Administrador','2026-06-04 22:55:59'),(614,180,'1100','PAPEL DRPIN CELLULOSE....','venta',6.000,'-',53.000,47.000,'factura',36,NULL,3,'Administrador','2026-06-04 22:55:59'),(615,34,'252','GOMA BULL DOG.REGALIZ TUTTI F.CJAx12u','venta',2.000,'-',9.000,7.000,'factura',36,NULL,3,'Administrador','2026-06-04 22:55:59'),(616,73,'504','PASTILLAS BULL DOG MIX TUITTI FRUTTI ACIDA X12U','venta',2.000,'-',8.000,6.000,'factura',36,NULL,3,'Administrador','2026-06-04 22:55:59'),(617,74,'505','PASTILLAS BULL DOG SANDIA ACIDA X 12 UND','venta',2.000,'-',4.000,2.000,'factura',36,NULL,3,'Administrador','2026-06-04 22:55:59'),(618,17,'207','GOMITAS YUMMY DIENTITOS X 500 GR','devolucion',2.000,'+',6.000,8.000,'factura',36,'Anulación factura 0006-X0000031 - REFACTURACION',3,'Administrador','2026-06-05 12:19:53'),(619,18,'208','YUMMY HUEVOS FRITOS BOLSA.x500g','devolucion',1.000,'+',0.000,1.000,'factura',36,'Anulación factura 0006-X0000031 - REFACTURACION',3,'Administrador','2026-06-05 12:19:53'),(620,33,'251','GOMA BULL DOG.REGALIZ FRUT.CJAx12u','devolucion',2.000,'+',8.000,10.000,'factura',36,'Anulación factura 0006-X0000031 - REFACTURACION',3,'Administrador','2026-06-05 12:19:53'),(621,35,'253','GOMA BULL DOG.REGALIZ FRAMB.CJAx12u','devolucion',2.000,'+',8.000,10.000,'factura',36,'Anulación factura 0006-X0000031 - REFACTURACION',3,'Administrador','2026-06-05 12:19:53'),(622,66,'406','CARAM.FLYNN PAFF TUTTI....x70u','devolucion',1.000,'+',13.000,14.000,'factura',36,'Anulación factura 0006-X0000031 - REFACTURACION',3,'Administrador','2026-06-05 12:19:53'),(623,69,'409','CARAM.MAST.DROPSY SELVA..x700g','devolucion',2.000,'+',6.000,8.000,'factura',36,'Anulación factura 0006-X0000031 - REFACTURACION',3,'Administrador','2026-06-05 12:19:53'),(624,72,'501','PASTILLAS BULL DOG UVA X12U','devolucion',2.000,'+',2.000,4.000,'factura',36,'Anulación factura 0006-X0000031 - REFACTURACION',3,'Administrador','2026-06-05 12:19:53'),(625,76,'507','PASTILLAS BULL DOG LIMON EXTREME X12 UND','devolucion',2.000,'+',8.000,10.000,'factura',36,'Anulación factura 0006-X0000031 - REFACTURACION',3,'Administrador','2026-06-05 12:19:53'),(626,80,'512','MENTITAS FRUTAL X 12 UND','devolucion',2.000,'+',13.000,15.000,'factura',36,'Anulación factura 0006-X0000031 - REFACTURACION',3,'Administrador','2026-06-05 12:19:53'),(627,81,'513','MENTITAS KIDS TUTTI FRUTTI X12U','devolucion',2.000,'+',12.000,14.000,'factura',36,'Anulación factura 0006-X0000031 - REFACTURACION',3,'Administrador','2026-06-05 12:19:53'),(628,82,'514','MENTITAS KIDS DULCE DE LECHE X 12 UND','devolucion',2.000,'+',13.000,15.000,'factura',36,'Anulación factura 0006-X0000031 - REFACTURACION',3,'Administrador','2026-06-05 12:19:53'),(629,89,'601','(28g)MARSHMALLOW GONGYS FRUTIL','devolucion',20.000,'+',108.000,128.000,'factura',36,'Anulación factura 0006-X0000031 - REFACTURACION',3,'Administrador','2026-06-05 12:19:53'),(630,90,'602','(28g)MARSHMALLOW GONGYS NUBECI','devolucion',20.000,'+',88.000,108.000,'factura',36,'Anulación factura 0006-X0000031 - REFACTURACION',3,'Administrador','2026-06-05 12:19:53'),(631,92,'700','CHOC TOKKE C/LECHE Y MANI 62G','devolucion',6.000,'+',1.000,7.000,'factura',36,'Anulación factura 0006-X0000031 - REFACTURACION',3,'Administrador','2026-06-05 12:19:53'),(632,93,'701','CHOC.TOKKE RELLE.D/LECHE..x72g','devolucion',6.000,'+',24.000,30.000,'factura',36,'Anulación factura 0006-X0000031 - REFACTURACION',3,'Administrador','2026-06-05 12:19:53'),(633,94,'702','CHOCOLATE MISKY  NGRO x25g','devolucion',20.000,'+',174.000,194.000,'factura',36,'Anulación factura 0006-X0000031 - REFACTURACION',3,'Administrador','2026-06-05 12:19:53'),(634,95,'703','CHOCOLATE MISKY  BCO x25g','devolucion',15.000,'+',197.000,212.000,'factura',36,'Anulación factura 0006-X0000031 - REFACTURACION',3,'Administrador','2026-06-05 12:19:53'),(635,96,'704','ROCKLETS 24 X 20GS','devolucion',2.000,'+',10.000,12.000,'factura',36,'Anulación factura 0006-X0000031 - REFACTURACION',3,'Administrador','2026-06-05 12:19:53'),(636,97,'705','CHOC. C/MANI COF. BLOCK 20X38GS','devolucion',6.000,'+',114.000,120.000,'factura',36,'Anulación factura 0006-X0000031 - REFACTURACION',3,'Administrador','2026-06-05 12:19:53'),(637,99,'707','CREMA KROOMY SURTIDOS ( 48u )','devolucion',2.000,'+',9.000,11.000,'factura',36,'Anulación factura 0006-X0000031 - REFACTURACION',3,'Administrador','2026-06-05 12:19:53'),(638,100,'708','BONOBON OBLEA LECHE....20ux30g','devolucion',15.000,'+',295.000,310.000,'factura',36,'Anulación factura 0006-X0000031 - REFACTURACION',3,'Administrador','2026-06-05 12:19:53'),(639,109,'714','GUAYMALLEN TRIPLE CHOCOLATE','devolucion',15.000,'+',93.000,108.000,'factura',36,'Anulación factura 0006-X0000031 - REFACTURACION',3,'Administrador','2026-06-05 12:19:53'),(640,106,'761','MECANO....................x19g','devolucion',6.000,'+',42.000,48.000,'factura',36,'Anulación factura 0006-X0000031 - REFACTURACION',3,'Administrador','2026-06-05 12:19:53'),(641,148,'934','BAGGIO MULTIFRUTAL.......x200m','devolucion',15.000,'+',0.000,15.000,'factura',36,'Anulación factura 0006-X0000031 - REFACTURACION',3,'Administrador','2026-06-05 12:19:53'),(642,180,'1100','PAPEL DRPIN CELLULOSE....','devolucion',6.000,'+',47.000,53.000,'factura',36,'Anulación factura 0006-X0000031 - REFACTURACION',3,'Administrador','2026-06-05 12:19:53'),(643,34,'252','GOMA BULL DOG.REGALIZ TUTTI F.CJAx12u','devolucion',2.000,'+',7.000,9.000,'factura',36,'Anulación factura 0006-X0000031 - REFACTURACION',3,'Administrador','2026-06-05 12:19:53'),(644,73,'504','PASTILLAS BULL DOG MIX TUITTI FRUTTI ACIDA X12U','devolucion',2.000,'+',6.000,8.000,'factura',36,'Anulación factura 0006-X0000031 - REFACTURACION',3,'Administrador','2026-06-05 12:19:53'),(645,74,'505','PASTILLAS BULL DOG SANDIA ACIDA X 12 UND','devolucion',2.000,'+',2.000,4.000,'factura',36,'Anulación factura 0006-X0000031 - REFACTURACION',3,'Administrador','2026-06-05 12:19:53'),(646,17,'207','GOMITAS YUMMY DIENTITOS X 500 GR','venta',2.000,'-',8.000,6.000,'factura',37,NULL,3,'Administrador','2026-06-05 12:31:33'),(647,18,'208','YUMMY HUEVOS FRITOS BOLSA.x500g','venta',1.000,'-',1.000,0.000,'factura',37,NULL,3,'Administrador','2026-06-05 12:31:33'),(648,33,'251','GOMA BULL DOG.REGALIZ FRUT.CJAx12u','venta',2.000,'-',10.000,8.000,'factura',37,NULL,3,'Administrador','2026-06-05 12:31:33'),(649,35,'253','GOMA BULL DOG.REGALIZ FRAMB.CJAx12u','venta',2.000,'-',10.000,8.000,'factura',37,NULL,3,'Administrador','2026-06-05 12:31:33'),(650,66,'406','CARAM.FLYNN PAFF TUTTI....x70u','venta',1.000,'-',14.000,13.000,'factura',37,NULL,3,'Administrador','2026-06-05 12:31:33'),(651,69,'409','CARAM.MAST.DROPSY SELVA..x700g','venta',2.000,'-',8.000,6.000,'factura',37,NULL,3,'Administrador','2026-06-05 12:31:33'),(652,72,'501','PASTILLAS BULL DOG UVA X12U','venta',2.000,'-',4.000,2.000,'factura',37,NULL,3,'Administrador','2026-06-05 12:31:33'),(653,76,'507','PASTILLAS BULL DOG LIMON EXTREME X12 UND','venta',2.000,'-',10.000,8.000,'factura',37,NULL,3,'Administrador','2026-06-05 12:31:33'),(654,80,'512','MENTITAS FRUTAL X 12 UND','venta',2.000,'-',15.000,13.000,'factura',37,NULL,3,'Administrador','2026-06-05 12:31:33'),(655,81,'513','MENTITAS KIDS TUTTI FRUTTI X12U','venta',2.000,'-',14.000,12.000,'factura',37,NULL,3,'Administrador','2026-06-05 12:31:33'),(656,82,'514','MENTITAS KIDS DULCE DE LECHE X 12 UND','venta',2.000,'-',15.000,13.000,'factura',37,NULL,3,'Administrador','2026-06-05 12:31:33'),(657,89,'601','(28g)MARSHMALLOW GONGYS FRUTIL','venta',20.000,'-',128.000,108.000,'factura',37,NULL,3,'Administrador','2026-06-05 12:31:33'),(658,90,'602','(28g)MARSHMALLOW GONGYS NUBECI','venta',20.000,'-',108.000,88.000,'factura',37,NULL,3,'Administrador','2026-06-05 12:31:33'),(659,92,'700','CHOC TOKKE C/LECHE Y MANI 62G','venta',6.000,'-',7.000,1.000,'factura',37,NULL,3,'Administrador','2026-06-05 12:31:33'),(660,93,'701','CHOC.TOKKE RELLE.D/LECHE..x72g','venta',6.000,'-',30.000,24.000,'factura',37,NULL,3,'Administrador','2026-06-05 12:31:33'),(661,94,'702','CHOCOLATE MISKY  NGRO x25g','venta',20.000,'-',194.000,174.000,'factura',37,NULL,3,'Administrador','2026-06-05 12:31:33'),(662,95,'703','CHOCOLATE MISKY  BCO x25g','venta',15.000,'-',212.000,197.000,'factura',37,NULL,3,'Administrador','2026-06-05 12:31:33'),(663,96,'704','ROCKLETS 24 X 20GS','venta',2.000,'-',12.000,10.000,'factura',37,NULL,3,'Administrador','2026-06-05 12:31:33'),(664,97,'705','CHOC. C/MANI COF. BLOCK 20X38GS','venta',6.000,'-',120.000,114.000,'factura',37,NULL,3,'Administrador','2026-06-05 12:31:33'),(665,99,'707','CREMA KROOMY SURTIDOS ( 48u )','venta',2.000,'-',11.000,9.000,'factura',37,NULL,3,'Administrador','2026-06-05 12:31:33'),(666,100,'708','BONOBON OBLEA LECHE....20ux30g','venta',15.000,'-',310.000,295.000,'factura',37,NULL,3,'Administrador','2026-06-05 12:31:33'),(667,109,'714','GUAYMALLEN TRIPLE CHOCOLATE','venta',15.000,'-',108.000,93.000,'factura',37,NULL,3,'Administrador','2026-06-05 12:31:33'),(668,106,'761','MECANO....................x19g','venta',6.000,'-',48.000,42.000,'factura',37,NULL,3,'Administrador','2026-06-05 12:31:33'),(669,148,'934','BAGGIO MULTIFRUTAL.......x200m','venta',15.000,'-',15.000,0.000,'factura',37,NULL,3,'Administrador','2026-06-05 12:31:33'),(670,34,'252','GOMA BULL DOG.REGALIZ TUTTI F.CJAx12u','venta',2.000,'-',9.000,7.000,'factura',37,NULL,3,'Administrador','2026-06-05 12:31:33'),(671,73,'504','PASTILLAS BULL DOG MIX TUITTI FRUTTI ACIDA X12U','venta',2.000,'-',8.000,6.000,'factura',37,NULL,3,'Administrador','2026-06-05 12:31:33'),(672,74,'505','PASTILLAS BULL DOG SANDIA ACIDA X 12 UND','venta',2.000,'-',4.000,2.000,'factura',37,NULL,3,'Administrador','2026-06-05 12:31:33'),(673,172,'963','MANI TARRO  CERVECERO SALAME','venta',10.000,'-',20.000,10.000,'factura',38,NULL,3,'Administrador','2026-06-05 13:22:46'),(674,173,'964','MANI TARRO CERVECERO QUESO','venta',10.000,'-',22.000,12.000,'factura',38,NULL,3,'Administrador','2026-06-05 13:22:46'),(675,174,'965','MANI TARRO CERVECERO PROVENZAL','venta',10.000,'-',11.000,1.000,'factura',38,NULL,3,'Administrador','2026-06-05 13:22:46'),(676,175,'968','MANI TARRO CON PIEL','venta',5.000,'-',21.000,16.000,'factura',38,NULL,3,'Administrador','2026-06-05 13:22:46'),(677,176,'969','MANI TARRO SIN PIEL','venta',5.000,'-',18.000,13.000,'factura',38,NULL,3,'Administrador','2026-06-05 13:22:46'),(678,4,'105','CHICLE FIERITA TUTTI X100U','venta',1.000,'-',4.000,3.000,'factura',39,NULL,3,'Administrador','2026-06-05 22:30:13'),(679,92,'700','CHOC TOKKE C/LECHE Y MANI 62G','venta',1.000,'-',1.000,0.000,'factura',39,NULL,3,'Administrador','2026-06-05 22:30:13'),(680,93,'701','CHOC.TOKKE RELLE.D/LECHE..x72g','venta',1.000,'-',24.000,23.000,'factura',39,NULL,3,'Administrador','2026-06-05 22:30:13'),(681,94,'702','CHOCOLATE MISKY  NGRO x25g','venta',4.000,'-',174.000,170.000,'factura',39,NULL,3,'Administrador','2026-06-05 22:30:13'),(682,95,'703','CHOCOLATE MISKY  BCO x25g','venta',4.000,'-',197.000,193.000,'factura',39,NULL,3,'Administrador','2026-06-05 22:30:13'),(683,109,'714','GUAYMALLEN TRIPLE CHOCOLATE','venta',4.000,'-',93.000,89.000,'factura',39,NULL,3,'Administrador','2026-06-05 22:30:13'),(684,110,'715','GUAYMALLEN TRIPLE BLANCO','venta',4.000,'-',85.000,81.000,'factura',39,NULL,3,'Administrador','2026-06-05 22:30:13'),(685,111,'716','GUAYMALLEN SIMPLE BLANCO','venta',6.000,'-',478.000,472.000,'factura',39,NULL,3,'Administrador','2026-06-05 22:30:13'),(686,112,'717','GUAYMALLEN SIMPLE CHOCOLATE','venta',6.000,'-',500.000,494.000,'factura',39,NULL,3,'Administrador','2026-06-05 22:30:13'),(687,113,'718','ALF FANTOCHE TRI.CHOCOLATEx85g','venta',3.000,'-',125.000,122.000,'factura',39,NULL,3,'Administrador','2026-06-05 22:30:13'),(688,114,'719','ALF FANTOCHE TRIPLE BLANCO.x85g','venta',3.000,'-',39.000,36.000,'factura',39,NULL,3,'Administrador','2026-06-05 22:30:13'),(689,115,'720','ALFAJOR RASTA NEGRO X 18U','venta',2.000,'-',2.000,0.000,'factura',39,NULL,3,'Administrador','2026-06-05 22:30:13'),(690,121,'729','ALFAJOR CHOCOTORTA 71,5','venta',2.000,'-',159.000,157.000,'factura',39,NULL,3,'Administrador','2026-06-05 22:30:13'),(691,122,'735','ALF BON O BON TRIPLE NEGROx60g','venta',2.000,'-',147.000,145.000,'factura',39,NULL,3,'Administrador','2026-06-05 22:30:13'),(692,123,'736','ALF COFLER BLOCK TRIPLE...x60g','venta',2.000,'-',153.000,151.000,'factura',39,NULL,3,'Administrador','2026-06-05 22:30:13'),(693,125,'738','ALF PEPITOS TRIPLE........x57g','venta',2.000,'-',75.000,73.000,'factura',39,NULL,3,'Administrador','2026-06-05 22:30:13'),(694,127,'740','ALF PESCADO RAUL SIMPLE NEGRO.x50g','venta',4.000,'-',225.000,221.000,'factura',39,NULL,3,'Administrador','2026-06-05 22:30:13'),(695,128,'741','ALF PESCADO RAUL SIMPLE BLANCO.x50g','venta',4.000,'-',167.000,163.000,'factura',39,NULL,3,'Administrador','2026-06-05 22:30:13'),(696,194,'742','ALF MINI TORTA AGUILA X69G','venta',2.000,'-',174.000,172.000,'factura',39,NULL,3,'Administrador','2026-06-05 22:30:13'),(697,155,'1010','DON SATUR BIZCOCH.GRASA x200g','venta',3.000,'-',97.000,94.000,'factura',39,NULL,3,'Administrador','2026-06-05 22:30:13'),(698,184,'3333','GOMA BULL DOG.REGALIZ (((SURTIDAS))).CJAx12u','venta',1.000,'-',2.000,1.000,'factura',39,NULL,3,'Administrador','2026-06-05 22:30:13'),(699,10,'200','GOMITAS YUMMY OSITOS ACIDOS X 500 GR','venta',1.000,'-',4.000,3.000,'factura',40,NULL,3,'Administrador','2026-06-05 22:37:41'),(700,14,'204','GOMITAS YUMMY SANDIA  X500GR','venta',1.000,'-',2.000,1.000,'factura',40,NULL,3,'Administrador','2026-06-05 22:37:41'),(701,16,'206','GOMITAS YUMMY MORITAS X500G','venta',1.000,'-',3.000,2.000,'factura',40,NULL,3,'Administrador','2026-06-05 22:37:41'),(702,27,'230','GOMA FANTASIA MISKY .......x1k','venta',1.000,'-',4.000,3.000,'factura',40,NULL,3,'Administrador','2026-06-05 22:37:41'),(703,56,'305','MR.POPS ARQUIT.FTAL.......x50u','venta',1.000,'-',7.000,6.000,'factura',40,NULL,3,'Administrador','2026-06-05 22:37:41'),(704,100,'708','BONOBON OBLEA LECHE....20ux30g','venta',6.000,'-',295.000,289.000,'factura',40,NULL,3,'Administrador','2026-06-05 22:37:41'),(705,121,'729','ALFAJOR CHOCOTORTA 71,5','venta',4.000,'-',157.000,153.000,'factura',40,NULL,3,'Administrador','2026-06-05 22:37:41'),(706,122,'735','ALF BON O BON TRIPLE NEGROx60g','venta',12.000,'-',145.000,133.000,'factura',40,NULL,3,'Administrador','2026-06-05 22:37:41'),(707,10,'200','GOMITAS YUMMY OSITOS ACIDOS X 500 GR','devolucion',1.000,'+',3.000,4.000,'factura',40,'Anulación factura 0006-X0000035',3,'Administrador','2026-06-05 22:39:28'),(708,14,'204','GOMITAS YUMMY SANDIA  X500GR','devolucion',1.000,'+',1.000,2.000,'factura',40,'Anulación factura 0006-X0000035',3,'Administrador','2026-06-05 22:39:28'),(709,16,'206','GOMITAS YUMMY MORITAS X500G','devolucion',1.000,'+',2.000,3.000,'factura',40,'Anulación factura 0006-X0000035',3,'Administrador','2026-06-05 22:39:28'),(710,27,'230','GOMA FANTASIA MISKY .......x1k','devolucion',1.000,'+',3.000,4.000,'factura',40,'Anulación factura 0006-X0000035',3,'Administrador','2026-06-05 22:39:28'),(711,56,'305','MR.POPS ARQUIT.FTAL.......x50u','devolucion',1.000,'+',6.000,7.000,'factura',40,'Anulación factura 0006-X0000035',3,'Administrador','2026-06-05 22:39:28'),(712,100,'708','BONOBON OBLEA LECHE....20ux30g','devolucion',6.000,'+',289.000,295.000,'factura',40,'Anulación factura 0006-X0000035',3,'Administrador','2026-06-05 22:39:28'),(713,121,'729','ALFAJOR CHOCOTORTA 71,5','devolucion',4.000,'+',153.000,157.000,'factura',40,'Anulación factura 0006-X0000035',3,'Administrador','2026-06-05 22:39:28'),(714,122,'735','ALF BON O BON TRIPLE NEGROx60g','devolucion',12.000,'+',133.000,145.000,'factura',40,'Anulación factura 0006-X0000035',3,'Administrador','2026-06-05 22:39:28'),(715,10,'200','GOMITAS YUMMY OSITOS ACIDOS X 500 GR','venta',1.000,'-',4.000,3.000,'factura',41,NULL,3,'Administrador','2026-06-05 22:40:31'),(716,14,'204','GOMITAS YUMMY SANDIA  X500GR','venta',1.000,'-',2.000,1.000,'factura',41,NULL,3,'Administrador','2026-06-05 22:40:31'),(717,16,'206','GOMITAS YUMMY MORITAS X500G','venta',1.000,'-',3.000,2.000,'factura',41,NULL,3,'Administrador','2026-06-05 22:40:31'),(718,27,'230','GOMA FANTASIA MISKY .......x1k','venta',1.000,'-',4.000,3.000,'factura',41,NULL,3,'Administrador','2026-06-05 22:40:31'),(719,56,'305','MR.POPS ARQUIT.FTAL.......x50u','venta',1.000,'-',7.000,6.000,'factura',41,NULL,3,'Administrador','2026-06-05 22:40:31'),(720,100,'708','BONOBON OBLEA LECHE....20ux30g','venta',6.000,'-',295.000,289.000,'factura',41,NULL,3,'Administrador','2026-06-05 22:40:31'),(721,121,'729','ALFAJOR CHOCOTORTA 71,5','venta',4.000,'-',157.000,153.000,'factura',41,NULL,3,'Administrador','2026-06-05 22:40:31'),(722,122,'735','ALF BON O BON TRIPLE NEGROx60g','venta',4.000,'-',145.000,141.000,'factura',41,NULL,3,'Administrador','2026-06-05 22:40:31'),(724,159,'1015','GALL TRIO PEPAS C/CHIPS..x300g','venta',6.000,'-',50.000,44.000,'factura',42,NULL,3,'Administrador','2026-06-05 22:52:12'),(725,160,'1017','GALL TRIO TRICHOC........x300g','venta',12.000,'-',58.000,46.000,'factura',42,NULL,3,'Administrador','2026-06-05 22:52:12'),(726,179,'980','PAPAS FRITAS COPETIN PEÑA \"1KG\"','venta',1.000,'-',1.000,0.000,'factura',42,NULL,3,'Administrador','2026-06-05 22:52:12'),(727,53,'302','MR.POPS EVOLUTION CEREZA..x24u','venta',1.000,'-',14.000,13.000,'factura',43,NULL,3,'Administrador','2026-06-06 16:44:30'),(728,63,'400','MASTICABLE SURTIDO MISKY X 800gs','venta',1.000,'-',20.000,19.000,'factura',43,NULL,3,'Administrador','2026-06-06 16:44:30'),(729,94,'702','CHOCOLATE MISKY  NGRO x25g','venta',10.000,'-',170.000,160.000,'factura',43,NULL,3,'Administrador','2026-06-06 16:44:30'),(730,95,'703','CHOCOLATE MISKY  BCO x25g','venta',10.000,'-',193.000,183.000,'factura',43,NULL,3,'Administrador','2026-06-06 16:44:30'),(731,109,'714','GUAYMALLEN TRIPLE CHOCOLATE','venta',10.000,'-',89.000,79.000,'factura',43,NULL,3,'Administrador','2026-06-06 16:44:30'),(732,110,'715','GUAYMALLEN TRIPLE BLANCO','venta',10.000,'-',81.000,71.000,'factura',43,NULL,3,'Administrador','2026-06-06 16:44:30'),(733,111,'716','GUAYMALLEN SIMPLE BLANCO','venta',10.000,'-',472.000,462.000,'factura',43,NULL,3,'Administrador','2026-06-06 16:44:30'),(734,113,'718','ALF FANTOCHE TRI.CHOCOLATEx85g','venta',12.000,'-',122.000,110.000,'factura',43,NULL,3,'Administrador','2026-06-06 16:44:30'),(735,114,'719','ALF FANTOCHE TRIPLE BLANCO.x85g','venta',12.000,'-',36.000,24.000,'factura',43,NULL,3,'Administrador','2026-06-06 16:44:30'),(736,131,'801','GIRASOL PIPAS GIGANTES.12ux50g','venta',1.000,'-',5.000,4.000,'factura',43,NULL,3,'Administrador','2026-06-06 16:44:30'),(737,132,'900','JUGO ARCOR POLVO NARANJA..x18u','venta',1.000,'-',11.000,10.000,'factura',43,NULL,3,'Administrador','2026-06-06 16:44:30'),(738,136,'904','JUGO ARCOR POLVO MULTIFRUTx18u','venta',1.000,'-',11.000,10.000,'factura',43,NULL,3,'Administrador','2026-06-06 16:44:30'),(739,151,'1001','MAGDAL DON SATUR VAINILLAx250g','venta',2.000,'-',2.000,0.000,'factura',43,NULL,3,'Administrador','2026-06-06 16:44:30'),(740,152,'1002','MAGDAL DON SATUR MARMOLADx250g','venta',3.000,'-',7.000,4.000,'factura',43,NULL,3,'Administrador','2026-06-06 16:44:30'),(741,153,'1003','MAGD DON SATUR CHOC/D/D/Lx250g','venta',3.000,'-',14.000,11.000,'factura',43,NULL,3,'Administrador','2026-06-06 16:44:30'),(742,155,'1010','DON SATUR BIZCOCH.GRASA x200g','venta',10.000,'-',94.000,84.000,'factura',43,NULL,3,'Administrador','2026-06-06 16:44:30'),(743,158,'1014','GALL TRIO PEPAS..........x320g','venta',6.000,'-',24.000,18.000,'factura',43,NULL,3,'Administrador','2026-06-06 16:44:30'),(744,160,'1017','GALL TRIO TRICHOC........x300g','venta',6.000,'-',46.000,40.000,'factura',43,NULL,3,'Administrador','2026-06-06 16:44:30'),(745,162,'1022','.9 DE ORO GRASA','venta',10.000,'-',77.000,67.000,'factura',43,NULL,3,'Administrador','2026-06-06 16:44:30'),(746,197,'1033','SERRANITAS OFERTA 14 X3 X315G','venta',10.000,'-',53.000,43.000,'factura',43,NULL,3,'Administrador','2026-06-06 16:44:30'),(747,172,'963','MANI TARRO  CERVECERO SALAME','venta',4.000,'-',10.000,6.000,'factura',43,NULL,3,'Administrador','2026-06-06 16:44:30'),(748,173,'964','MANI TARRO CERVECERO QUESO','venta',2.000,'-',12.000,10.000,'factura',43,NULL,3,'Administrador','2026-06-06 16:44:30'),(749,64,'402','(x32u)MAST.LENGUETAZO T.FRUTI...','venta',1.000,'-',7.000,6.000,'factura',44,NULL,3,'Administrador','2026-06-08 10:34:46'),(750,128,'741','ALF PESCADO RAUL SIMPLE BLANCO.x50g','venta',12.000,'-',163.000,151.000,'factura',44,NULL,3,'Administrador','2026-06-08 10:34:46');
/*!40000 ALTER TABLE `stock_movimiento` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `transferencia_caja`
--

DROP TABLE IF EXISTS `transferencia_caja`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `transferencia_caja` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `fecha` datetime NOT NULL,
  `caja_origen_id` int(11) NOT NULL,
  `caja_destino_id` int(11) NOT NULL,
  `punto_venta_origen` int(11) NOT NULL,
  `punto_venta_destino` int(11) NOT NULL,
  `monto` decimal(10,2) NOT NULL,
  `motivo` varchar(255) DEFAULT NULL,
  `usuario_id` int(11) NOT NULL,
  `anulada` tinyint(1) NOT NULL DEFAULT 0,
  `fecha_anulacion` datetime DEFAULT NULL,
  `motivo_anulacion` varchar(255) DEFAULT NULL,
  `usuario_anulacion_id` int(11) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `idx_fecha` (`fecha`),
  KEY `idx_origen` (`caja_origen_id`),
  KEY `idx_destino` (`caja_destino_id`),
  KEY `idx_pv_origen` (`punto_venta_origen`),
  KEY `idx_pv_destino` (`punto_venta_destino`),
  KEY `idx_usuario` (`usuario_id`),
  CONSTRAINT `fk_tc_destino_schiro` FOREIGN KEY (`caja_destino_id`) REFERENCES `cajas` (`id`),
  CONSTRAINT `fk_tc_origen_schiro` FOREIGN KEY (`caja_origen_id`) REFERENCES `cajas` (`id`),
  CONSTRAINT `fk_tc_usuario_schiro` FOREIGN KEY (`usuario_id`) REFERENCES `usuario` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `transferencia_caja`
--

LOCK TABLES `transferencia_caja` WRITE;
/*!40000 ALTER TABLE `transferencia_caja` DISABLE KEYS */;
/*!40000 ALTER TABLE `transferencia_caja` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `usuario`
--

DROP TABLE IF EXISTS `usuario`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `usuario` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `username` varchar(80) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `nombre` varchar(100) NOT NULL,
  `rol` varchar(50) DEFAULT 'vendedor',
  `activo` tinyint(1) DEFAULT 1,
  `fecha_creacion` timestamp NOT NULL DEFAULT current_timestamp(),
  `punto_venta` int(11) NOT NULL DEFAULT 3,
  `puede_liquidar` tinyint(1) NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `usuario`
--

LOCK TABLES `usuario` WRITE;
/*!40000 ALTER TABLE `usuario` DISABLE KEYS */;
INSERT INTO `usuario` VALUES (3,'admin','admin123','Administrador','admin',1,'2025-08-09 21:14:22',6,1);
/*!40000 ALTER TABLE `usuario` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `vendedor`
--

DROP TABLE IF EXISTS `vendedor`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `vendedor` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(150) NOT NULL COMMENT 'Nombre y Apellido',
  `tipo_documento` varchar(20) NOT NULL DEFAULT 'DNI',
  `documento` varchar(20) DEFAULT NULL,
  `direccion` varchar(200) DEFAULT NULL,
  `telefono` varchar(30) DEFAULT NULL,
  `notas` text DEFAULT NULL,
  `activo` tinyint(1) NOT NULL DEFAULT 1,
  `fecha_creacion` datetime DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `idx_vendedor_nombre` (`nombre`),
  KEY `idx_vendedor_documento` (`documento`),
  KEY `idx_vendedor_activo` (`activo`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `vendedor`
--

LOCK TABLES `vendedor` WRITE;
/*!40000 ALTER TABLE `vendedor` DISABLE KEYS */;
INSERT INTO `vendedor` VALUES (1,'FERNANDO DENEGRI','DNI',NULL,NULL,NULL,NULL,1,'2026-06-06 18:21:45'),(2,'TORAL','DNI',NULL,NULL,NULL,NULL,1,'2026-06-06 18:22:09');
/*!40000 ALTER TABLE `vendedor` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `zona`
--

DROP TABLE IF EXISTS `zona`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `zona` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(60) NOT NULL,
  `descripcion` varchar(255) DEFAULT NULL,
  `color` varchar(7) NOT NULL DEFAULT '#0d6efd' COMMENT 'Color HEX para el badge',
  `orden_reparto` int(11) NOT NULL DEFAULT 0 COMMENT 'Orden de recorrido (menor primero)',
  `activo` tinyint(1) NOT NULL DEFAULT 1,
  `fecha_creacion` datetime NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_zona_nombre` (`nombre`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `zona`
--

LOCK TABLES `zona` WRITE;
/*!40000 ALTER TABLE `zona` DISABLE KEYS */;
/*!40000 ALTER TABLE `zona` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping routines for database 'distribuidora_virtual'
--
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-06-08 12:02:19
