import os
import platform
import re
from datetime import datetime
import win32print
import win32api
import tempfile
import logging

# Datos del cliente para el ticket (vienen de config_cliente.py)
# Si no se puede importar, usa valores por defecto para no romper.
try:
    from config_cliente import (
        TICKET_NOMBRE_COMERCIAL,
        TICKET_CUIT_FORMATO,
        TICKET_CONDICION_IVA,
        TICKET_DIRECCION,
        TICKET_FRASE_EXTRA,
    )
except ImportError:
    TICKET_NOMBRE_COMERCIAL = 'Mayorista LKD'
    TICKET_CUIT_FORMATO     = '20-29168729-7'
    TICKET_CONDICION_IVA    = 'Responsable Inscripto'
    TICKET_DIRECCION        = 'Pte. Peron 3764'
    TICKET_FRASE_EXTRA      = 'Mayorista LKD'

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ImpresoraTermica:
    def __init__(self, nombre_impresora=None, ancho_mm=80):
        # Para impresoras térmicas de 80mm, el ancho típico es 42-48 caracteres
        if ancho_mm == 80:
            self.ancho = 42  # Caracteres por línea para 80mm
        elif ancho_mm == 58:
            self.ancho = 32  # Caracteres por línea para 58mm
        else:
            self.ancho = ancho_mm  # Si se especifica directamente
            
        self.ancho_mm = ancho_mm
        self.nombre_impresora = nombre_impresora or self._buscar_impresora_termica()
        
        print(f"🖨️ Configuración: {ancho_mm}mm = {self.ancho} caracteres por línea")

    def _esta_online(self, nombre):
        """Devuelve True si la impresora está encendida y sin errores según Windows"""
        try:
            h = win32print.OpenPrinter(nombre)
            info = win32print.GetPrinter(h, 2)
            win32print.ClosePrinter(h)
            status = info['Status']
            OFFLINE = 0x00000080
            ERROR   = 0x00000002
            return not (status & OFFLINE) and not (status & ERROR)
        except Exception:
            return False

    def _buscar_impresora_termica(self):
        """Buscar impresora térmica automáticamente - EPSON TM-m30II prioritaria si está online"""
        try:
            # PRINTER_ENUM_LOCAL=2 lista todas las impresoras locales correctamente
            impresoras = win32print.EnumPrinters(2)
            
            # ORDEN DE PRIORIDAD: EPSON TM-m30II PRIMERO
            nombres_termicas_prioritarios = [
                'EPSON TM-m30II Receipt',
                'epson tm-m30ii receipt',
                'tm-m30ii receipt',
                'EPSON TM-T20II Receipt5', 
                'TMT20',
            ]
            
            # Buscar por prioridad: solo si está online
            for prioritario in nombres_termicas_prioritarios:
                for impresora in impresoras:
                    nombre = impresora[2].lower()
                    if prioritario.lower() in nombre:
                        if self._esta_online(impresora[2]):
                            print(f"🖨️ ✅ EPSON detectada: {impresora[2]}")
                            print(f"🎯 Esta impresora térmica profesional será usada")
                            return impresora[2]
                        else:
                            print(f"⚠️ {impresora[2]} instalada pero OFFLINE, buscando otra...")
            
            # Si no encuentra EPSON online, buscar otras térmicas
            nombres_termicas_secundarios = [
                'tm-t(203dpi)',
                'tm-t20',
                'pos-58', 'pos58',
                'tm-m30ii', 'tm-m30', 'epson tm-m30',
                'thermal', 'receipt', 'pos', 'tm-', 'rp-', 'sp-',
                'termica', 'ticket', 'epson', 'star', 'citizen',
                'xprinter', 'godex', 'zebra', 'bixolon',
                'pronter', 'gadnic', 'zjiang',
            ]
            
            for impresora in impresoras:
                nombre = impresora[2].lower()
                for termico in nombres_termicas_secundarios:
                    if termico in nombre:
                        if self._esta_online(impresora[2]):
                            print(f"🖨️ ⚠️ Impresora térmica secundaria detectada: {impresora[2]}")
                            print(f"💡 Recomendación: Usar EPSON TM-m30II si está disponible")
                            return impresora[2]
                        else:
                            print(f"⚠️ {impresora[2]} encontrada pero OFFLINE, saltando...")
            
            # Si no encuentra térmica, usar impresora por defecto
            try:
                impresora_default = win32print.GetDefaultPrinter()
                print(f"🖨️ 📄 Usando impresora por defecto: {impresora_default}")
                print(f"⚠️ Esta puede no ser una impresora térmica")
                return impresora_default
            except:
                print("❌ No se pudo obtener impresora por defecto")
                return None
            
        except Exception as e:
            print(f"❌ Error detectando impresora: {e}")
            return None
            
    def centrar_texto(self, texto, ancho=None):
        """Centrar texto en el ancho especificado"""
        ancho = ancho or self.ancho
        if len(texto) >= ancho:
            return texto[:ancho]
        espacios = (ancho - len(texto)) // 2
        return " " * espacios + texto
    
    def justificar_texto(self, izquierda, derecha, ancho=None):
        """Justificar texto a izquierda y derecha"""
        ancho = ancho or self.ancho
        espacios_necesarios = ancho - len(izquierda) - len(derecha)
        if espacios_necesarios <= 0:
            return (izquierda + derecha)[:ancho]
        return izquierda + " " * espacios_necesarios + derecha
    
    def justificar_texto_doble(self, izquierda, derecha, ancho=None):
        """Justificar texto en DOBLE tamano (negrita + doble alto + doble ancho).
        Cada caracter ocupa el DOBLE de espacio, asi que el ancho efectivo es la mitad.
        Retorna la linea con los codigos ESC/POS embebidos."""
        ancho = ancho or self.ancho
        # En doble ancho, cada caracter ocupa 2 columnas. Ancho efectivo = ancho/2
        ancho_efectivo = ancho // 2
        espacios_necesarios = ancho_efectivo - len(izquierda) - len(derecha)
        if espacios_necesarios <= 0:
            texto = (izquierda + derecha)[:ancho_efectivo]
        else:
            texto = izquierda + " " * espacios_necesarios + derecha
        # Codigos ESC/POS:
        # \x1B\x45\x01 = Negrita ON
        # \x1B\x21\x30 = Doble alto + doble ancho
        # \x1B\x21\x00 = Reset tamano normal
        # \x1B\x45\x00 = Negrita OFF
        return f"\x1B\x45\x01\x1B\x21\x30{texto}\x1B\x21\x00\x1B\x45\x00"
    
    def linea_separadora(self, caracter="-", ancho=None):
        """Crear línea separadora"""
        ancho = ancho or self.ancho
        return caracter * ancho
    
    def truncar_texto(self, texto, max_chars):
        """Truncar texto si es muy largo"""
        if len(texto) <= max_chars:
            return texto
        return texto[:max_chars-3] + "..."

    def formatear_factura_termica(self, factura):
        """Formatear factura para impresión térmica de 80mm"""
        lineas = []
        
        print("🔍 DEBUG - Iniciando formateo de factura")
        
        try:
            # ENCABEZADO
            lineas.append("")
            lineas.append("              \x1B\x45\x01\x1B\x21\x30" + TICKET_NOMBRE_COMERCIAL + "\x1B\x21\x00\x1B\x45\x00")
            lineas.append("")
            lineas.append(self.centrar_texto(f"CUIT: {TICKET_CUIT_FORMATO}"))
            lineas.append(self.centrar_texto(f"IVA: {TICKET_CONDICION_IVA}"))
            lineas.append(self.centrar_texto(f"Dir: {TICKET_DIRECCION}"))
            if TICKET_FRASE_EXTRA:
                lineas.append(self.centrar_texto(TICKET_FRASE_EXTRA))
            lineas.append("")
            
            # TIPO DE COMPROBANTE
            tipo_cbte = self._obtener_tipo_comprobante(factura.tipo_comprobante)
            lineas.append(self.centrar_texto(f"=== {tipo_cbte} ==="))
            lineas.append(self.centrar_texto(f"Nro: {factura.numero}"))
            lineas.append("")
            
            # FECHA Y HORA
            fecha_str = factura.fecha.strftime("%d/%m/%Y %H:%M")
            lineas.append(f"Fecha: {fecha_str}")
            
            # VENDEDOR
            vendedor = "Sistema"
            if hasattr(factura, 'usuario') and factura.usuario:
                vendedor = factura.usuario.nombre
            vendedor_corto = self.truncar_texto(vendedor, 20)
            lineas.append(f"Vendedor: {vendedor_corto}")
            
            lineas.append(self.linea_separadora())
            
            # CLIENTE
            if hasattr(factura, 'cliente') and factura.cliente:
                nombre_cliente = self.truncar_texto(factura.cliente.nombre, self.ancho)
                lineas.append(f"Cliente: {nombre_cliente}")
                if hasattr(factura.cliente, 'documento') and factura.cliente.documento:
                    tipo_doc = getattr(factura.cliente, 'tipo_documento', 'DNI') or "DNI"
                    lineas.append(f"{tipo_doc}: {factura.cliente.documento}")
            else:
                lineas.append("Cliente: Consumidor Final")
            
            lineas.append(self.linea_separadora())
            
            # ─── FORMATO ITEMS (2 LÍNEAS POR PRODUCTO, ESTILO VESTA) ───
            # Línea 1:  cantidad u. x precio_unitario        (alineada izq)
            # Línea 2:  NOMBRE_PRODUCTO        (% IVA)  TOTAL  (alineado der)
            
            # PRODUCTOS
            if hasattr(factura, 'detalles') and factura.detalles:
                # Determinar lógica de precios según tipo de comprobante
                # Factura B/C/Interno: precios CON IVA incluido
                # Factura A: precios SIN IVA
                es_factura_b_o_c = str(factura.tipo_comprobante) in ['6', '06', '11', '12', '13', '99']
                
                for detalle in factura.detalles:
                    if hasattr(detalle, 'producto') and detalle.producto:
                        nombre_producto = getattr(detalle.producto, 'nombre', 'Producto')
                    else:
                        nombre_producto = 'Producto'
                    
                    try:
                        cantidad = float(detalle.cantidad)
                        porcentaje_iva = float(getattr(detalle, 'porcentaje_iva', 21.0))
                        precio_sin_iva = float(detalle.precio_unitario)
                        subtotal_sin_iva = float(detalle.subtotal)
                        importe_iva = float(getattr(detalle, 'importe_iva', 0))
                        
                        # Si importe_iva viene en 0 (datos viejos), recalcularlo
                        if importe_iva == 0 and porcentaje_iva > 0:
                            importe_iva = subtotal_sin_iva * porcentaje_iva / 100
                        
                        if es_factura_b_o_c:
                            # Para tickets a Consumidor Final: mostrar precios CON IVA
                            precio_unitario_mostrar = precio_sin_iva * (1 + porcentaje_iva / 100)
                            total_mostrar = subtotal_sin_iva + importe_iva
                        else:
                            # Factura A: precios SIN IVA discriminados
                            precio_unitario_mostrar = precio_sin_iva
                            total_mostrar = subtotal_sin_iva
                        
                    except (ValueError, AttributeError):
                        cantidad = 1.0
                        porcentaje_iva = 21.0
                        precio_unitario_mostrar = 0.0
                        total_mostrar = 0.0
                    
                    # ─── LÍNEA 1: cantidad u. x precio_unitario ───
                    cant_str = f"{cantidad:.4f}".replace(".", ",")
                    pu_str = f"{precio_unitario_mostrar:.4f}".replace(".", ",")
                    linea1 = f"{cant_str} u. x {pu_str}"
                    lineas.append(linea1[:self.ancho])
                    
                    # ─── LÍNEA 2: NOMBRE  (IVA%)  TOTAL ───
                    iva_tag = f"({int(porcentaje_iva)})"
                    total_str = f"{total_mostrar:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                    
                    # Calcular espacios disponibles
                    # Formato:  NOMBRE...    (XX)  TOTAL
                    # Total ocupa al menos 12 caracteres (alineado derecha)
                    # IVA tag ocupa 4 caracteres incluyendo paréntesis
                    # Espacio mínimo entre nombre e IVA: 1
                    # Espacio entre IVA y total: 2
                    
                    espacio_total = 12
                    espacio_iva = 4
                    espacio_separadores = 3  # 1 espacio antes IVA + 2 entre IVA y total
                    espacio_nombre = self.ancho - espacio_total - espacio_iva - espacio_separadores
                    
                    nombre_truncado = self.truncar_texto(nombre_producto, espacio_nombre).upper()
                    
                    linea2 = f"{nombre_truncado:<{espacio_nombre}} {iva_tag:<{espacio_iva}}  {total_str:>{espacio_total}}"
                    lineas.append(linea2[:self.ancho])
            else:
                lineas.append("Sin productos")
            
            lineas.append(self.linea_separadora())
            
            # ═══ SALDO ANTERIOR DEL CLIENTE ═══
            observaciones = getattr(factura, 'observaciones', None)
            if observaciones and 'Saldo anterior' in observaciones:
                # Extraer el monto del saldo anterior de las observaciones
                match = re.search(r'Saldo anterior[:\s]*\$?([\d,.]+)', observaciones)
                if match:
                    saldo_ant_str = match.group(1)
                    lineas.append(self.justificar_texto("SALDO ANTERIOR:", f"${saldo_ant_str}"))
                    lineas.append(self.linea_separadora())
            
            # TOTALES
            try:
                # Verificar si es Factura B
                es_factura_b = str(factura.tipo_comprobante) in ['6', '06']
                
                subtotal = float(getattr(factura, 'subtotal', 0))
                iva_total = float(getattr(factura, 'iva', 0))
                total = float(getattr(factura, 'total', 0))
                
                # Calcular IVA por alícuota (para todas las facturas)
                iva_por_alicuota = {}
                if hasattr(factura, 'detalles') and factura.detalles:
                    for detalle in factura.detalles:
                        if hasattr(detalle, 'porcentaje_iva') and detalle.porcentaje_iva is not None:
                            porcentaje = float(detalle.porcentaje_iva)
                        else:
                            porcentaje = float(detalle.producto.iva) if hasattr(detalle, 'producto') and detalle.producto else 21.0
                        
                        importe_iva_detalle = float(getattr(detalle, 'importe_iva', 0))
                        if importe_iva_detalle == 0:
                            subtotal_detalle = float(detalle.subtotal)
                            importe_iva_detalle = round((subtotal_detalle * porcentaje / 100), 2)
                        
                        if porcentaje not in iva_por_alicuota:
                            iva_por_alicuota[porcentaje] = 0
                        iva_por_alicuota[porcentaje] += importe_iva_detalle
                
                # ═══ LEER DESCUENTO DESDE LA TABLA descuentos_factura ═══
                # (importacion local para evitar problemas de circularidad)
                descuento_porcentaje = 0
                descuento_monto = 0
                try:
                    from app import DescuentoFactura
                    desc_row = DescuentoFactura.query.filter_by(factura_id=factura.id).first()
                    if desc_row:
                        descuento_porcentaje = float(desc_row.porcentaje_descuento or 0)
                        descuento_monto = float(desc_row.monto_descuento or 0)
                except Exception as e:
                    # Si por alguna razon no se puede leer, caemos al calculo por diferencia
                    print(f"[impresora_termica] No se pudo leer descuentos_factura: {e}")

                # Para Factura B y C: TOTAL al pie (IVA contenido)
                es_factura_a = str(factura.tipo_comprobante) in ['1', '01', '2', '02', '3', '03']
                if not es_factura_a:
                    # Si no hay descuento en la tabla, intentamos calcularlo por diferencia
                    # (fallback para facturas viejas o si fallo la lectura de la tabla)
                    if descuento_monto <= 0:
                        subtotal_mas_iva = subtotal + iva_total
                        if total < subtotal_mas_iva - 0.01:
                            descuento_monto = subtotal_mas_iva - total
                            if subtotal_mas_iva > 0:
                                descuento_porcentaje = (descuento_monto / subtotal_mas_iva) * 100

                    # Si hay descuento, mostramos: Subtotal original / Descuento / Total
                    if descuento_monto > 0:
                        total_original = total + descuento_monto
                        lineas.append(self.justificar_texto("SUBTOTAL:", f"${total_original:,.2f}"))
                        if descuento_porcentaje > 0:
                            etiqueta_desc = f"DESCUENTO {descuento_porcentaje:g}%:"
                        else:
                            etiqueta_desc = "DESCUENTO:"
                        lineas.append(self.justificar_texto(etiqueta_desc, f"-${descuento_monto:,.2f}"))
                    lineas.append(self.linea_separadora())
                    lineas.append(self.justificar_texto_doble("TOTAL:", f"${total:,.2f}"))
                else:
                    # Para Factura A: SUBTOTAL, IVA discriminado, DESCUENTO y TOTAL
                    lineas.append(self.justificar_texto("SUBTOTAL:", f"${subtotal:,.2f}"))

                    if iva_por_alicuota:
                        for porcentaje in sorted(iva_por_alicuota.keys()):
                            importe_iva = iva_por_alicuota[porcentaje]
                            if importe_iva > 0:
                                if porcentaje == 0:
                                    etiqueta = "EXENTO:"
                                else:
                                    etiqueta = f"IVA {porcentaje:g}%:"
                                lineas.append(self.justificar_texto(etiqueta, f"${importe_iva:,.2f}"))
                    else:
                        if iva_total > 0:
                            lineas.append(self.justificar_texto("IVA 21%:", f"${iva_total:,.2f}"))

                    # Descuento: primero intentamos con la tabla, si no fallback a la diferencia
                    if descuento_monto > 0:
                        if descuento_porcentaje > 0:
                            etiqueta_desc = f"DESCUENTO {descuento_porcentaje:g}%:"
                        else:
                            etiqueta_desc = "DESCUENTO:"
                        lineas.append(self.justificar_texto(etiqueta_desc, f"-${descuento_monto:,.2f}"))
                    else:
                        # Fallback para facturas viejas sin registro en descuentos_factura
                        subtotal_mas_iva = subtotal + iva_total
                        if total < subtotal_mas_iva:
                            descuento_calc = subtotal_mas_iva - total
                            if descuento_calc > 0.01:  # tolerancia por redondeos
                                lineas.append(self.justificar_texto("DESCUENTO:", f"-${descuento_calc:,.2f}"))

                    lineas.append(self.linea_separadora())
                    lineas.append(self.justificar_texto_doble("TOTAL:", f"${total:,.2f}"))
                
            except (ValueError, AttributeError):
                lineas.append(self.justificar_texto_doble("TOTAL:", "$0.00"))
            
            lineas.append(self.linea_separadora())
            
            # ═══ MEDIOS DE PAGO ═══
            if hasattr(factura, 'medios_pago') and factura.medios_pago:
                total_factura = float(getattr(factura, 'total', 0))
                lineas.append(self.centrar_texto("FORMA DE PAGO"))
                total_pagado = 0
                for mp in factura.medios_pago:
                    medio_nombre = str(mp.medio_pago).upper().replace('_', ' ')
                    importe_mp = float(mp.importe)
                    total_pagado += importe_mp
                    lineas.append(self.justificar_texto(f"{medio_nombre}:", f"${importe_mp:,.2f}"))
                
                # Mostrar total pagado vs total factura si pagó menos
                if total_pagado < total_factura - 0.01:
                    lineas.append(self.linea_separadora())
                    lineas.append(self.justificar_texto("TOTAL PAGADO:", f"${total_pagado:,.2f}"))
                
                lineas.append(self.linea_separadora())
            
            # INFORMACIÓN AFIP
            es_comprobante_interno = str(factura.tipo_comprobante) == '99'
            cae = getattr(factura, 'cae', None)
            
            if es_comprobante_interno:
                # Comprobante Interno: NO mostrar info AFIP (no tiene CAE).
                # Solo dejamos un separador visual y seguimos al pie de página.
                lineas.append("")
                lineas.append(self.centrar_texto("--- Comprobante Interno ---"))
                lineas.append("")
            elif cae:
                lineas.append("")
                lineas.append("Transparencia Fiscal al Consumidor - Ley 27.743")
                lineas.append("")
                
                # Para Factura B y C: Agregar "I.V.A Contenido"
                es_factura_a = str(factura.tipo_comprobante) in ['1', '01', '2', '02', '3', '03']
                if not es_factura_a:
                    iva_total = float(getattr(factura, 'iva', 0))
                    lineas.append(self.centrar_texto(f"I.V.A Contenido ${iva_total:,.2f}"))
                    lineas.append("")
                
                lineas.append(self.centrar_texto("*** AUTORIZADO AFIP ***"))
                lineas.append("")
                
                cae_texto = f"CAE: {cae}"
                if len(cae_texto) > self.ancho:
                    lineas.append("CAE:")
                    lineas.append(f"  {cae}")
                else:
                    lineas.append(cae_texto)
                    
                vto_cae = getattr(factura, 'vto_cae', None)
                if vto_cae:
                    try:
                        if hasattr(vto_cae, 'strftime'):
                            vto_str = vto_cae.strftime("%d/%m/%Y")
                        else:
                            vto_str = str(vto_cae)
                        lineas.append(f"Vto CAE: {vto_str}")
                    except Exception:
                        lineas.append(f"Vto CAE: {vto_cae}")
                
                lineas.append("")
                lineas.append(self.centrar_texto("Verificar en:"))
                lineas.append(self.centrar_texto("www.arca.gob.ar"))
                
            else:
                lineas.append("")
                lineas.append("Transparencia Fiscal al Consumidor - Ley 27.743")
                lineas.append("")
                # No mostrar "NO AUTORIZADO" en facturas C (tipos 11/12/13)
                es_factura_c = str(factura.tipo_comprobante) in ['11', '12', '13']
                if not es_factura_c:
                    lineas.append(self.centrar_texto("*** NO AUTORIZADO ***"))
                    lineas.append(self.centrar_texto("VERIFICAR AFIP"))
            
            # PIE DE PÁGINA
            lineas.append("")
            
            # ═══ MOSTRAR INFO FINAL SEGÚN TIPO ═══
            if observaciones:
                if observaciones.startswith('Cobro CTA.CTE:'):
                    # Solo mostrar descripción de artículos, sin precios (para no confundir con el total)
                    lineas.append(self.linea_separadora())
                    lineas.append(self.centrar_texto("INCLUYE ARTICULOS DE CTA.CTE"))
                    lineas.append(self.linea_separadora())
                    for linea_obs in observaciones.split('\n'):
                        if linea_obs.startswith('  '):
                            # Mostrar solo descripción y cantidad, sin precio
                            partes = linea_obs.strip().split(' — ')
                            lineas.append(partes[0][:self.ancho])
                    lineas.append(self.linea_separadora())
                    lineas.append("")
                elif 'Saldo pendiente' in observaciones:
                    match = re.search(r'Saldo pendiente[:\s]*\$?([\d,.]+)', observaciones)
                    if match:
                        nuevo_saldo_str = match.group(1)
                        lineas.append(self.linea_separadora())
                        lineas.append(self.centrar_texto("*** SALDO PENDIENTE ***"))
                        lineas.append(self.centrar_texto(f"${nuevo_saldo_str}"))
                        lineas.append(self.linea_separadora())
                        lineas.append("")
                elif 'Saldo a favor' in observaciones:
                    match = re.search(r'Saldo a favor[:\s]*\$?([\d,.]+)', observaciones)
                    if match:
                        saldo_favor_str = match.group(1)
                        lineas.append(self.linea_separadora())
                        lineas.append(self.centrar_texto("*** SALDO A FAVOR ***"))
                        lineas.append(self.centrar_texto(f"${saldo_favor_str}"))
                        lineas.append(self.linea_separadora())
                        lineas.append("")
            
            lineas.append(self.centrar_texto("Gracias por elegirnos"))
            lineas.append("")
            lineas.append("")
            lineas.append("")
            lineas.append("")
            lineas.append("")
            lineas.append("")
            lineas.append("\x1B\x69")
            
        except Exception as e:
            print(f"❌ Error en formatear_factura_termica: {e}")
            import traceback
            traceback.print_exc()
            
            lineas = [
                "",
                self.centrar_texto("*** ERROR EN FACTURA ***"),
                "",
                f"Error: {str(e)}",
                "",
                self.centrar_texto("Contactar soporte"),
                "",
                "",
                ""
            ]
        
        return "\n".join(lineas)

    def imprimir_factura_con_qr_web(self, factura):
        """Imprimir factura y mostrar QR en navegador"""
        try:
            resultado_impresion = self.imprimir_factura(factura)
            info_qr = {'valido': False, 'mensaje': 'QR deshabilitado en impresión'}
            
            return {
                'impresion_exitosa': resultado_impresion,
                'qr_info': info_qr
            }
        except Exception as e:
            print(f"❌ Error en impresión con QR: {e}")
            return {
                'impresion_exitosa': False,
                'qr_info': {'valido': False, 'mensaje': str(e)}
            }

    def _obtener_tipo_comprobante(self, tipo):
        """Obtener descripción del tipo de comprobante"""
        tipos = {
            '01': 'FACTURA A',   '1': 'FACTURA A',
            '06': 'FACTURA B',   '6': 'FACTURA B',
            '11': 'PRESUPUESTO',                        # Factura C se imprime como PRESUPUESTO
            '03': 'NOTA CRED A', '3': 'NOTA CRED A',
            '08': 'NOTA CRED B', '8': 'NOTA CRED B',
            '13': 'NOTA CRED C',
            '99': 'COMPROBANTE INTERNO'
        }
        
        tipo_str = str(tipo)
        
        if tipo_str in tipos:
            return tipos[tipo_str]
        elif tipo_str.zfill(2) in tipos:
            return tipos[tipo_str.zfill(2)]
        else:
            return f'CBTE {tipo}'

    def imprimir_factura(self, factura):
        """Imprimir factura con método RAW"""
        try:
            if not self.nombre_impresora:
                raise Exception("No se encontró impresora térmica")
            
            print(f"🖨️ INICIANDO IMPRESIÓN - Factura: {getattr(factura, 'numero', 'SIN_NUMERO')}")
            
            contenido = self.formatear_factura_termica(factura)
            print(f"📄 Contenido formateado: {len(contenido)} caracteres")
            
            hPrinter = win32print.OpenPrinter(self.nombre_impresora)
            
            try:
                hJob = win32print.StartDocPrinter(hPrinter, 1, (f"Factura_{getattr(factura, 'numero', 'XXX')}", None, "RAW"))
                
                try:
                    win32print.StartPagePrinter(hPrinter)
                    
                    init_cmd = b'\x1B\x40'
                    datos_bytes = init_cmd + contenido.encode('cp850', errors='replace')
                    datos_bytes += b'\n\n\x1B\x69'
                    
                    win32print.WritePrinter(hPrinter, datos_bytes)
                    win32print.EndPagePrinter(hPrinter)
                    
                    print("✅ *** IMPRESIÓN EXITOSA ***")
                    return True
                    
                finally:
                    win32print.EndDocPrinter(hPrinter)
            finally:
                win32print.ClosePrinter(hPrinter)
                
        except Exception as e:
            print(f"❌ ERROR GENERAL: {e}")
            import traceback
            traceback.print_exc()
            return False

    # ═══════════════════════════════════════════════════════════════════
    # LIQUIDACIONES A INTERMEDIARIOS (consignación FASE 2)
    # ═══════════════════════════════════════════════════════════════════
    def formatear_liquidacion_termica(self, liquidacion, detalles_data=None):
        """Formatear comprobante de liquidación a intermediario para térmica 80mm.
        
        liquidacion: objeto LiquidacionIntermediario
        detalles_data: lista opcional de dicts con {interno_numero, factura_numero, 
                       monto_diferencia, monto_interno, monto_factura}.
                       Si no se pasa, intenta resolver desde la BD usando la sesión actual de Flask.
        """
        lineas = []
        
        try:
            print(f"📋 Formateando liquidación {liquidacion.numero}...")
            
            # ENCABEZADO (mismo formato que factura, doble ancho con ESC/POS)
            lineas.append("")
            lineas.append("              \x1B\x45\x01\x1B\x21\x30" + TICKET_NOMBRE_COMERCIAL + "\x1B\x21\x00\x1B\x45\x00")
            lineas.append("")
            lineas.append(self.centrar_texto(f"CUIT: {TICKET_CUIT_FORMATO}"))
            lineas.append(self.centrar_texto(f"IVA: {TICKET_CONDICION_IVA}"))
            lineas.append(self.centrar_texto(f"Dir: {TICKET_DIRECCION}"))
            lineas.append("")
            
            # TIPO DE COMPROBANTE
            lineas.append(self.centrar_texto("=== LIQUIDACION INTERMEDIARIO ==="))
            lineas.append(self.centrar_texto(f"Nro: {liquidacion.numero}"))
            lineas.append("")
            
            # Fecha y usuario
            fecha_str = liquidacion.fecha.strftime("%d/%m/%Y %H:%M") if liquidacion.fecha else ''
            lineas.append(f"Fecha: {fecha_str}")
            usuario_nombre = 'Sistema'
            try:
                if liquidacion.usuario:
                    usuario_nombre = liquidacion.usuario.nombre
            except Exception as e:
                print(f"⚠️ No se pudo obtener usuario: {e}")
            lineas.append(f"Usuario: {self.truncar_texto(usuario_nombre, 20)}")
            
            lineas.append(self.linea_separadora())
            
            # INTERMEDIARIO
            cliente_nombre = '?'
            cliente_doc = ''
            cliente_tipo_doc = 'DNI'
            try:
                cliente = liquidacion.intermediario
                if cliente:
                    cliente_nombre = cliente.nombre or '?'
                    cliente_doc = cliente.documento or ''
                    cliente_tipo_doc = cliente.tipo_documento or 'DNI'
            except Exception as e:
                print(f"⚠️ No se pudo obtener intermediario: {e}")
            
            lineas.append(f"Intermediario:")
            lineas.append(f"  {self.truncar_texto(cliente_nombre, self.ancho - 2)}")
            if cliente_doc:
                lineas.append(f"  {cliente_tipo_doc}: {cliente_doc}")
            
            base_label = 'Con IVA' if liquidacion.base_calculo == 'con_iva' else 'Sin IVA'
            lineas.append(f"Base de calculo: {base_label}")
            
            lineas.append(self.linea_separadora())
            
            # DETALLE DE COMPROBANTES
            lineas.append(f"{'INTERNO':<14}{'FACTURA':<14}{'DIF.':>10}")
            lineas.append(self.linea_separadora())
            
            # Si nos pasaron detalles_data úsalo, sino resolvelo aquí (sin importar app.py)
            if detalles_data is None:
                detalles_data = []
                try:
                    # Resolver desde la sesión activa de SQLAlchemy sin import circular
                    for d in liquidacion.detalles:
                        # interno y factura son relaciones definidas en el modelo
                        int_num = '?'
                        fac_num = '?'
                        try:
                            if d.interno:
                                int_num = d.interno.numero or '?'
                        except Exception:
                            pass
                        try:
                            if d.factura_derivada:
                                fac_num = d.factura_derivada.numero or '?'
                        except Exception:
                            pass
                        detalles_data.append({
                            'interno_numero': int_num,
                            'factura_numero': fac_num,
                            'monto_interno': float(d.monto_interno or 0),
                            'monto_factura': float(d.monto_factura or 0),
                            'monto_diferencia': float(d.monto_diferencia or 0),
                        })
                except Exception as e:
                    print(f"⚠️ No se pudieron resolver los detalles desde el modelo: {e}")
                    import traceback; traceback.print_exc()
                    # Continuar con detalles_data vacío para al menos imprimir el header
            
            for d in detalles_data:
                int_num = self.truncar_texto(d.get('interno_numero', '?'), 13)
                fac_num = self.truncar_texto(d.get('factura_numero', '?'), 13)
                
                dif = float(d.get('monto_diferencia', 0))
                dif_str = f"${dif:,.2f}"
                lineas.append(f"{int_num:<14}{fac_num:<14}{dif_str:>10}")
                
                # Línea adicional con costo y vendido
                costo = float(d.get('monto_interno', 0))
                vendido = float(d.get('monto_factura', 0))
                lineas.append(f"  Costo: ${costo:,.2f}  Vend: ${vendido:,.2f}")
            
            lineas.append(self.linea_separadora())
            lineas.append("")
            
            # TOTALES
            lineas.append(self.justificar_texto(
                "Total Vendido:",
                f"${float(liquidacion.total_vendido or 0):,.2f}"
            ))
            lineas.append(self.justificar_texto(
                "Total Costo (entregado):",
                f"${float(liquidacion.total_costo or 0):,.2f}"
            ))
            lineas.append("")
            
            # TOTAL A LIQUIDAR (en grande, ESC/POS doble ancho)
            total_liq = float(liquidacion.total_liquidar or 0)
            total_str = f"${total_liq:,.2f}"
            lineas.append("\x1B\x45\x01\x1B\x21\x30" + self.centrar_texto("TOTAL LIQUIDADO", 24) + "\x1B\x21\x00\x1B\x45\x00")
            lineas.append("\x1B\x45\x01\x1B\x21\x30" + self.centrar_texto(total_str, 24) + "\x1B\x21\x00\x1B\x45\x00")
            lineas.append("")
            lineas.append(self.linea_separadora())
            
            # ESTADO Y FORMA DE PAGO
            if liquidacion.estado == 'pagada':
                lineas.append(self.centrar_texto(f"*** PAGADO ***"))
                if liquidacion.medio_pago:
                    lineas.append(self.centrar_texto(f"Medio: {liquidacion.medio_pago}"))
                if liquidacion.fecha_pago:
                    lineas.append(self.centrar_texto(
                        f"Fecha pago: {liquidacion.fecha_pago.strftime('%d/%m/%Y %H:%M')}"
                    ))
            elif liquidacion.estado == 'pendiente_pago':
                lineas.append(self.centrar_texto("*** PENDIENTE DE PAGO ***"))
                lineas.append(self.centrar_texto("Registrado en Cta.Cte."))
            elif liquidacion.estado == 'anulada':
                lineas.append(self.centrar_texto("*** A N U L A D A ***"))
            
            # Motivo si hay
            if liquidacion.motivo:
                lineas.append("")
                lineas.append("Observaciones:")
                motivo_text = liquidacion.motivo.strip()
                for fragmento in motivo_text.split('\n'):
                    fragmento = fragmento.strip()
                    if not fragmento:
                        continue
                    while len(fragmento) > self.ancho:
                        lineas.append(fragmento[:self.ancho])
                        fragmento = fragmento[self.ancho:]
                    if fragmento:
                        lineas.append(fragmento)
            
            lineas.append("")
            lineas.append(self.linea_separadora())
            
            # ÁREA DE FIRMA
            lineas.append("")
            lineas.append("Recibi conforme:")
            lineas.append("")
            lineas.append("")
            lineas.append("_" * 30)
            lineas.append(f"  {self.truncar_texto(cliente_nombre, 28)}")
            if cliente_doc:
                lineas.append(f"  {cliente_tipo_doc}: {cliente_doc}")
            lineas.append("")
            lineas.append(self.centrar_texto("--- Comprobante interno ---"))
            lineas.append(self.centrar_texto("(no es factura, no es valido fiscalmente)"))
            lineas.append("")
            
            print(f"✅ Formateo OK ({len(lineas)} líneas)")
            return "\n".join(lineas)
            
        except Exception as e:
            print(f"❌ Error formateando liquidación: {e}")
            import traceback; traceback.print_exc()
            return None
    
    def imprimir_liquidacion(self, liquidacion, detalles_data=None):
        """Imprimir comprobante de liquidación con método RAW (mismo flujo que factura)."""
        try:
            if not self.nombre_impresora:
                raise Exception("No se encontró impresora térmica")
            
            print(f"🖨️ INICIANDO IMPRESIÓN - Liquidación: {liquidacion.numero}")
            
            contenido = self.formatear_liquidacion_termica(liquidacion, detalles_data=detalles_data)
            if not contenido:
                raise Exception("No se pudo formatear la liquidación (revisar consola para detalle)")
            
            print(f"📄 Contenido formateado: {len(contenido)} caracteres")
            
            hPrinter = win32print.OpenPrinter(self.nombre_impresora)
            
            try:
                hJob = win32print.StartDocPrinter(
                    hPrinter, 1,
                    (f"Liquidacion_{liquidacion.numero}", None, "RAW")
                )
                
                try:
                    win32print.StartPagePrinter(hPrinter)
                    
                    init_cmd = b'\x1B\x40'
                    datos_bytes = init_cmd + contenido.encode('cp850', errors='replace')
                    datos_bytes += b'\n\n\x1B\x69'  # avanzar papel + cortar
                    
                    win32print.WritePrinter(hPrinter, datos_bytes)
                    win32print.EndPagePrinter(hPrinter)
                    
                    print("✅ *** LIQUIDACIÓN IMPRESA ***")
                    return True
                    
                finally:
                    win32print.EndDocPrinter(hPrinter)
            finally:
                win32print.ClosePrinter(hPrinter)
                
        except Exception as e:
            print(f"❌ ERROR LIQUIDACIÓN: {e}")
            import traceback; traceback.print_exc()
            return False
    
    # ═══════════════════════════════════════════════════════════════════
    # REMITOS — formato propio (sin precios, marca CONSTANCIA DE ENTREGA)
    # ═══════════════════════════════════════════════════════════════════
    def formatear_remito_termico(self, remito):
        """Formatear remito (no fiscal, sin precios) para impresión térmica."""
        lineas = []
        try:
            # ENCABEZADO
            lineas.append("")
            lineas.append("              \x1B\x45\x01\x1B\x21\x30" + TICKET_NOMBRE_COMERCIAL + "\x1B\x21\x00\x1B\x45\x00")
            lineas.append("")
            lineas.append(self.centrar_texto(f"CUIT: {TICKET_CUIT_FORMATO}"))
            lineas.append(self.centrar_texto(f"IVA: {TICKET_CONDICION_IVA}"))
            lineas.append(self.centrar_texto(f"Dir: {TICKET_DIRECCION}"))
            lineas.append("")

            # TIPO DE COMPROBANTE — REMITO
            lineas.append(self.centrar_texto("=== REMITO ==="))
            lineas.append(self.centrar_texto("(NO VALIDO COMO FACTURA)"))
            lineas.append(self.centrar_texto(f"Nro: {remito.numero_completo}"))
            lineas.append("")

            # FECHA Y HORA
            try:
                fecha_str = remito.fecha.strftime("%d/%m/%Y %H:%M")
            except Exception:
                fecha_str = str(remito.fecha or "")
            lineas.append(f"Fecha: {fecha_str}")

            # USUARIO
            vendedor = self.truncar_texto(getattr(remito, 'usuario_nombre', '') or 'Sistema', 20)
            lineas.append(f"Vendedor: {vendedor}")

            # ZONA DE REPARTO (si tiene)
            if getattr(remito, 'zona_nombre', None):
                lineas.append(f"Zona: {self.truncar_texto(remito.zona_nombre, self.ancho - 6)}")

            lineas.append(self.linea_separadora())

            # CLIENTE
            nombre_cli = self.truncar_texto(getattr(remito, 'cliente_nombre', '') or 'Sin cliente', self.ancho)
            lineas.append(f"Cliente: {nombre_cli}")
            if getattr(remito, 'documento', None):
                tipo_doc = getattr(remito, 'tipo_documento', 'DNI') or 'DNI'
                lineas.append(f"{tipo_doc}: {remito.documento}")
            if getattr(remito, 'condicion_iva', None):
                lineas.append(f"Cond. IVA: {self.truncar_texto(remito.condicion_iva, self.ancho - 11)}")
            if getattr(remito, 'direccion', None):
                lineas.append(f"Dir: {self.truncar_texto(remito.direccion, self.ancho - 5)}")

            lineas.append(self.linea_separadora())

            # ENCABEZADO DE PRODUCTOS — sin precios
            lineas.append(f"{'PRODUCTO':<{self.ancho - 9}} {'CANT':>8}")
            lineas.append(self.linea_separadora())

            # PRODUCTOS — solo nombre + cantidad
            total_items = 0
            total_cant  = 0.0
            items = getattr(remito, 'items', None) or []
            for it in items:
                nombre_prod = it.get('nombre', 'Producto') if isinstance(it, dict) else getattr(it, 'nombre', 'Producto')
                cant        = it.get('cantidad', 0)         if isinstance(it, dict) else getattr(it, 'cantidad', 0)
                try:
                    cant_f = float(cant)
                except Exception:
                    cant_f = 0.0

                nombre_t = self.truncar_texto(nombre_prod, self.ancho - 9)
                cant_str = f"{cant_f:.3f}".rstrip('0').rstrip('.') if cant_f != int(cant_f) else f"{int(cant_f)}"
                cant_str = cant_str.rjust(8)
                lineas.append(f"{nombre_t:<{self.ancho - 9}} {cant_str}")

                total_items += 1
                total_cant  += cant_f

            lineas.append(self.linea_separadora())

            # TOTALES (sin importes)
            lineas.append(f"{'Items:':<{self.ancho - 9}} {total_items:>8}")
            cant_tot_str = f"{total_cant:.3f}".rstrip('0').rstrip('.') if total_cant != int(total_cant) else f"{int(total_cant)}"
            lineas.append(f"{'Cant. total:':<{self.ancho - 9}} {cant_tot_str:>8}")

            lineas.append("")
            lineas.append(self.linea_separadora())

            # OBSERVACIONES
            if getattr(remito, 'observaciones', None):
                lineas.append("Observaciones:")
                obs = remito.observaciones.strip()
                # cortar en lineas del ancho
                while obs:
                    lineas.append(obs[:self.ancho])
                    obs = obs[self.ancho:]
                lineas.append("")

            # FIRMAS
            lineas.append(self.centrar_texto("CONSTANCIA DE ENTREGA"))
            lineas.append("")
            lineas.append("")
            lineas.append("_" * self.ancho)
            lineas.append(self.centrar_texto("Firma y aclaracion del receptor"))
            lineas.append("")
            lineas.append(self.linea_separadora())
            lineas.append(self.centrar_texto("Gracias por su compra"))
            lineas.append("")
            lineas.append("")
            lineas.append("")

            return "\n".join(lineas)

        except Exception as e:
            print(f"❌ ERROR formateando remito: {e}")
            import traceback; traceback.print_exc()
            raise

    def imprimir_remito(self, remito):
        """Imprime remito en la térmica (RAW)."""
        try:
            if not self.nombre_impresora:
                raise Exception("No se encontró impresora térmica")

            print(f"🖨️ IMPRIMIENDO REMITO: {getattr(remito, 'numero_completo', 'SIN_NUMERO')}")
            contenido = self.formatear_remito_termico(remito)

            hPrinter = win32print.OpenPrinter(self.nombre_impresora)
            try:
                hJob = win32print.StartDocPrinter(hPrinter, 1, (f"Remito_{getattr(remito, 'numero', 'XXX')}", None, "RAW"))
                try:
                    win32print.StartPagePrinter(hPrinter)
                    init_cmd = b'\x1B\x40'
                    datos_bytes = init_cmd + contenido.encode('cp850', errors='replace')
                    datos_bytes += b'\n\n\x1B\x69'
                    win32print.WritePrinter(hPrinter, datos_bytes)
                    win32print.EndPagePrinter(hPrinter)
                    print("✅ REMITO IMPRESO")
                    return True
                finally:
                    win32print.EndDocPrinter(hPrinter)
            finally:
                win32print.ClosePrinter(hPrinter)

        except Exception as e:
            print(f"❌ ERROR imprimiendo remito: {e}")
            import traceback; traceback.print_exc()
            return False

    def test_impresion(self):
        """Test de impresión con método RAW"""
        try:
            if not self.nombre_impresora:
                raise Exception("No se encontró impresora")
                
            print(f"🧪 INICIANDO TEST - Impresora: {self.nombre_impresora}")
            
            contenido_test = """
=== PRUEBA DE IMPRESION ===

Test de sistema POS
Fecha: """ + datetime.now().strftime("%d/%m/%Y %H:%M") + """

Impresora detectada:
""" + self.nombre_impresora + """

------------------------------------------
ESTADO: FUNCIONANDO CORRECTAMENTE
------------------------------------------

*** EXITO ***




"""
            
            hPrinter = win32print.OpenPrinter(self.nombre_impresora)
            
            try:
                hJob = win32print.StartDocPrinter(hPrinter, 1, ("POS_Test", None, "RAW"))
                
                try:
                    win32print.StartPagePrinter(hPrinter)
                    
                    init_cmd = b'\x1B\x40'
                    datos_bytes = init_cmd + contenido_test.encode('cp850', errors='replace')
                    datos_bytes += b'\n\n\x1B\x69'
                    
                    win32print.WritePrinter(hPrinter, datos_bytes)
                    win32print.EndPagePrinter(hPrinter)
                    
                    print("✅ *** TEST EXITOSO ***")
                    return True
                    
                finally:
                    win32print.EndDocPrinter(hPrinter)
            finally:
                win32print.ClosePrinter(hPrinter)
                
        except Exception as e:
            print(f"❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
            return False

    def verificar_estado(self):
        """Verificar el estado de la impresora"""
        try:
            if not self.nombre_impresora:
                return {
                    'disponible': False,
                    'error': 'Impresora no detectada',
                    'nombre': None,
                    'ancho_mm': self.ancho_mm,
                    'caracteres_linea': self.ancho
                }
            
            try:
                handle = win32print.OpenPrinter(self.nombre_impresora)
                info = win32print.GetPrinter(handle, 2)
                win32print.ClosePrinter(handle)
                
                estado = info['Status']
                estado_texto = "Lista" if estado == 0 else f"Estado: {estado}"
                
                return {
                    'disponible': True,
                    'nombre': self.nombre_impresora,
                    'estado': estado_texto,
                    'ancho_mm': self.ancho_mm,
                    'caracteres_linea': self.ancho
                }
            except Exception as e:
                return {
                    'disponible': True,
                    'nombre': self.nombre_impresora,
                    'estado': 'Disponible (estado no verificable)',
                    'ancho_mm': self.ancho_mm,
                    'caracteres_linea': self.ancho,
                    'warning': str(e)
                }
                
        except Exception as e:
            logger.error(f"Error al verificar estado: {e}")
            return {
                'disponible': False,
                'error': str(e),
                'nombre': self.nombre_impresora,
                'ancho_mm': self.ancho_mm,
                'caracteres_linea': self.ancho
            }

    @staticmethod
    def listar_impresoras():
        """Listar todas las impresoras disponibles"""
        try:
            print("🖨️ Impresoras disponibles:")
            impresoras = win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL)
            for i, impresora in enumerate(impresoras, 1):
                print(f"   {i}. {impresora[2]}")
            
            try:
                impresoras_red = win32print.EnumPrinters(win32print.PRINTER_ENUM_NETWORK)
                if impresoras_red:
                    print("\n🌐 Impresoras de red:")
                    for i, impresora in enumerate(impresoras_red, 1):
                        print(f"   {i}. {impresora[2]}")
            except:
                pass
                
        except Exception as e:
            print(f"❌ Error listando impresoras: {e}")

    def formatear_recibo_termico(self, recibo):
        """Formatea un recibo de cobro para impresión térmica."""
        lineas = []
        try:
            lineas.append("")
            lineas.append("              \x1B\x45\x01\x1B\x21\x30" + TICKET_NOMBRE_COMERCIAL + "\x1B\x21\x00\x1B\x45\x00")
            lineas.append("")
            lineas.append(self.centrar_texto(f"CUIT: {TICKET_CUIT_FORMATO}"))
            lineas.append("")
            lineas.append(self.centrar_texto("=== RECIBO DE COBRO ==="))
            lineas.append(self.centrar_texto(f"Nro: {recibo.get('numero', '')}"))
            lineas.append("")
            lineas.append(f"Fecha: {recibo.get('fecha', '')}")
            lineas.append(f"Cliente: {self.truncar_texto(recibo.get('cliente_nombre', ''), self.ancho - 9)}")
            if recibo.get('cliente_doc'):
                lineas.append(f"Doc: {recibo.get('cliente_doc', '')}")
            lineas.append(self.linea_separadora())
            lineas.append(self.centrar_texto("COMPROBANTES COBRADOS"))
            lineas.append(self.linea_separadora())
            for d in recibo.get('detalles', []):
                cbte = self.truncar_texto(d.get('numero_comprobante', '—'), 20)
                monto = f"${d.get('monto_imputado', 0):,.2f}"
                lineas.append(self.justificar_texto(cbte, monto))
            lineas.append(self.linea_separadora())
            lineas.append(self.centrar_texto("FORMA DE COBRO"))
            for mp in recibo.get('medios_pago', []):
                medio = mp.get('medio', '').upper().replace('_', ' ')
                importe = f"${mp.get('importe', 0):,.2f}"
                lineas.append(self.justificar_texto(medio + ":", importe))
            lineas.append(self.linea_separadora())
            lineas.append(self.justificar_texto_doble("TOTAL:", f"${recibo.get('total', 0):,.2f}"))
            lineas.append(self.linea_separadora())
            lineas.append("")
            lineas.append(self.centrar_texto("Gracias por su pago"))
            lineas.append("")
            lineas.append("")
            lineas.append("")
            lineas.append("\x1B\x69")
        except Exception as e:
            print(f"❌ Error formateando recibo: {e}")
            import traceback; traceback.print_exc()
        return "\n".join(lineas)

    def imprimir_recibo(self, recibo):
        """Imprime recibo de cobro en térmica."""
        try:
            if not self.nombre_impresora:
                raise Exception("No se encontró impresora térmica")
            contenido = self.formatear_recibo_termico(recibo)
            hPrinter = win32print.OpenPrinter(self.nombre_impresora)
            try:
                hJob = win32print.StartDocPrinter(hPrinter, 1, (f"Recibo_{recibo.get('numero','')}", None, "RAW"))
                try:
                    win32print.StartPagePrinter(hPrinter)
                    datos = b'\x1B\x40' + contenido.encode('cp850', errors='replace') + b'\n\n\x1B\x69'
                    win32print.WritePrinter(hPrinter, datos)
                    win32print.EndPagePrinter(hPrinter)
                    print(f"✅ Recibo {recibo.get('numero','')} impreso en térmica")
                    return True
                finally:
                    win32print.EndDocPrinter(hPrinter)
            finally:
                win32print.ClosePrinter(hPrinter)
        except Exception as e:
            print(f"❌ Error imprimiendo recibo: {e}")
            import traceback; traceback.print_exc()
            return False

    def imprimir_cartel_precio(self, producto, tiene_ofertas=False):
        """Imprimir cartel de precio individual para producto"""
        try:
            if not self.nombre_impresora:
                print("❌ Impresora no disponible para carteles")
                return False
            
            print(f"🏷️ Imprimiendo cartel para: {producto.codigo}")
            
            precio = float(producto.precio)
            nombre_corto = (producto.nombre or "").strip()
            codigo_barras = str(getattr(producto, 'codigo_barras', '') or producto.codigo or '').strip()
            fecha_hoy = datetime.now().strftime("%d/%m/%y")

            contenido = []

            # ── Oferta banner (si aplica) ──────────────────────────────────
            if tiene_ofertas:
                contenido.append("*" * self.ancho)
                contenido.append(self.centrar_texto("¡OFERTA ESPECIAL!"))
                contenido.append("*" * self.ancho)

            contenido.append("")

            # ── Nombre del producto en DOBLE tamaño (2x ancho + 2x alto) ──
            # A 2x cada caracter ocupa el doble → ancho efectivo = ancho/2
            ANCHO_2X = self.ancho // 2  # 21 chars en 80mm

            def _wrap(texto, ancho_max, max_lineas=3):
                texto = (texto or "").strip()
                if not texto:
                    return [""]
                palabras = texto.split()
                lineas, actual = [], ""
                for palabra in palabras:
                    cand = palabra if not actual else actual + " " + palabra
                    if len(cand) <= ancho_max:
                        actual = cand
                    else:
                        if actual:
                            lineas.append(actual)
                            if len(lineas) >= max_lineas:
                                actual = ""
                                break
                        actual = palabra[:ancho_max]
                if actual and len(lineas) < max_lineas:
                    lineas.append(actual)
                return lineas[:max_lineas]

            lineas_nombre = _wrap(nombre_corto, ANCHO_2X)
            for linea in lineas_nombre:
                if not linea:
                    continue
                # GS ! \x11 = doble ancho + doble alto
                contenido.append(
                    "\x1D\x21\x11"          # 2x ancho + 2x alto
                    + "\x1B\x45\x01"        # negrita ON
                    + linea.upper()
                    + "\x1B\x45\x00"        # negrita OFF
                    + "\x1D\x21\x00"        # reset tamaño
                )

            contenido.append("")

            # ── Precio en el tamaño MÁS GRANDE posible ────────────────────
            if precio == int(precio):
                precio_texto = f"${int(precio)}"
            else:
                precio_texto = f"${precio:.2f}".replace(".", ",")

            largo = len(precio_texto)
            mult = 2
            for m in range(8, 1, -1):
                if largo * m <= self.ancho:
                    mult = m
                    break

            cmd_size  = "\x1D\x21" + chr(0x11 * (mult - 1))
            cmd_reset = "\x1D\x21\x00"
            ancho_consumido = largo * mult
            espacios = max(0, (self.ancho - ancho_consumido) // 2)

            contenido.append(
                "\x1B\x45\x01"
                + " " * espacios
                + cmd_size
                + precio_texto
                + cmd_reset
                + "\x1B\x45\x00"
            )
            contenido.append("")

            # ── Ahorro combo (si aplica) ───────────────────────────────────
            if tiene_ofertas and producto.es_combo and hasattr(producto, 'calcular_ahorro_combo'):
                ahorro = producto.calcular_ahorro_combo()
                if ahorro > 0:
                    contenido.append(self.centrar_texto(f"Ahorro: ${ahorro:.2f}"))

            # ── Footer: código de barras + fecha ──────────────────────────
            footer = f"{codigo_barras} ({fecha_hoy})" if codigo_barras else fecha_hoy
            contenido.append(
                "\x1B\x45\x01"          # negrita ON
                + self.centrar_texto(footer)
                + "\x1B\x45\x00"        # negrita OFF
            )
            contenido.append("")
            contenido.extend([""] * 2)

            texto_completo = "\n".join(contenido)

            print("📄 Enviando cartel a impresora...")
            hPrinter = win32print.OpenPrinter(self.nombre_impresora)
            try:
                hJob = win32print.StartDocPrinter(hPrinter, 1, (f"Cartel_{producto.codigo}", None, "RAW"))
                try:
                    win32print.StartPagePrinter(hPrinter)
                    init_cmd = b'\x1B\x40'
                    datos_bytes = init_cmd + texto_completo.encode('cp850', errors='replace')
                    datos_bytes += b'\n\n\x1B\x69'
                    win32print.WritePrinter(hPrinter, datos_bytes)
                    win32print.EndPagePrinter(hPrinter)
                    print(f"✅ *** CARTEL IMPRESO: {producto.codigo} ***")
                    return True
                finally:
                    win32print.EndDocPrinter(hPrinter)
            finally:
                win32print.ClosePrinter(hPrinter)
            
        except Exception as e:
            print(f"❌ Error imprimiendo cartel para {producto.codigo}: {e}")
            import traceback
            traceback.print_exc()
            return False


    def imprimir_qr_escaner(self, url='https://lakapp.dyndns.info/escaner', titulo='Lakapp'):
        """Imprime un cartel para góndola con QR del escáner público.

        El QR se genera con el comando ESC/POS nativo GS ( k (no como imagen raster).
        Esto evita problemas de drivers de Windows escalando PNGs.

        Args:
            url: URL que se codifica en el QR.
            titulo: nombre del negocio que aparece arriba del QR.
        Returns:
            True si imprimió OK, False si error.
        """
        try:
            if not self.nombre_impresora:
                print("❌ Impresora no disponible para QR")
                return False

            print(f"📱 Imprimiendo QR del escáner para: {titulo}")
            print(f"   URL: {url}")

            # ═══ ARMADO DEL TICKET ═══
            # 1) Comandos de inicialización + texto en parte de arriba
            # 2) Comando ESC/POS de QR (binario, no string)
            # 3) Texto debajo + corte

            # Parte 1: header de texto
            CENTER = b'\x1B\x61\x01'   # alineación centro
            LEFT   = b'\x1B\x61\x00'   # alineación izquierda
            BOLD_ON  = b'\x1B\x45\x01'
            BOLD_OFF = b'\x1B\x45\x00'
            INIT     = b'\x1B\x40'     # reset

            datos = bytearray()
            datos += INIT
            datos += CENTER

            # Título del negocio en doble tamaño
            datos += b'\x1D\x21\x11'   # 2x ancho + 2x alto
            datos += BOLD_ON
            datos += titulo.upper().encode('cp850', errors='replace')
            datos += BOLD_OFF
            datos += b'\x1D\x21\x00'   # reset tamaño
            datos += b'\n\n'

            # ═══ Parte 2: QR CODE nativo ═══
            # ESC/POS QR Code commands:
            #   Function 165 (0x41): Select model (model 2)
            #   Function 167 (0x43): Set module size (cell size)
            #   Function 169 (0x45): Set error correction level (L=48, M=49, Q=50, H=51)
            #   Function 180 (0x50): Store QR data
            #   Function 181 (0x51): Print QR

            url_bytes = url.encode('utf-8')

            # 2.a) Modelo 2 (estándar)
            datos += b'\x1D\x28\x6B\x04\x00\x31\x41\x32\x00'

            # 2.b) Tamaño de módulo: 8 (grande, queda bien visible)
            datos += b'\x1D\x28\x6B\x03\x00\x31\x43\x08'

            # 2.c) Nivel corrección H (más resistente, 30% redundancia)
            datos += b'\x1D\x28\x6B\x03\x00\x31\x45\x33'

            # 2.d) Cargar datos del QR
            pL = (len(url_bytes) + 3) % 256
            pH = (len(url_bytes) + 3) // 256
            datos += b'\x1D\x28\x6B' + bytes([pL, pH]) + b'\x31\x50\x30' + url_bytes

            # 2.e) Imprimir QR
            datos += b'\x1D\x28\x6B\x03\x00\x31\x51\x30'

            datos += b'\n'

            # ═══ Parte 3: textos abajo ═══
            datos += b'\x1D\x21\x11'   # 2x tamaño
            datos += BOLD_ON
            datos += 'ESCANEÁ PARA'.encode('cp850', errors='replace')
            datos += b'\n'
            datos += 'VER EL PRECIO'.encode('cp850', errors='replace')
            datos += BOLD_OFF
            datos += b'\x1D\x21\x00'
            datos += b'\n\n'

            datos += BOLD_ON
            datos += 'Apuntá la cámara del celular al QR'.encode('cp850', errors='replace')
            datos += BOLD_OFF
            datos += b'\n\n'

            # Footer chiquito
            datos += 'Powered by FactuFácil'.encode('cp850', errors='replace')
            datos += b'\n\n\n'

            # Corte de papel
            datos += b'\x1B\x69'

            # ═══ ENVIAR A IMPRESORA ═══
            print("📄 Enviando QR a impresora...")
            hPrinter = win32print.OpenPrinter(self.nombre_impresora)
            try:
                hJob = win32print.StartDocPrinter(hPrinter, 1, ("QR_Escaner", None, "RAW"))
                try:
                    win32print.StartPagePrinter(hPrinter)
                    win32print.WritePrinter(hPrinter, bytes(datos))
                    win32print.EndPagePrinter(hPrinter)
                    print(f"✅ *** QR IMPRESO ***")
                    return True
                finally:
                    win32print.EndDocPrinter(hPrinter)
            finally:
                win32print.ClosePrinter(hPrinter)

        except Exception as e:
            print(f"❌ Error imprimiendo QR: {e}")
            import traceback
            traceback.print_exc()
            return False

    def imprimir_qr_cobro_mp(self, url_pago, monto, descripcion='Cobro'):
        """Imprime un ticket con el QR de cobro MercadoPago.

        Pensado para que el cajero arranque el ticket y se lo dé al cliente
        para que escanee con su billetera (MP, Cuenta DNI, Naranja X, Ualá...).

        Args:
            url_pago: URL del init_point de MP (lo que va dentro del QR).
            monto: float con el monto a cobrar.
            descripcion: texto corto (ej: "Venta #123" o "FactuFácil").

        Returns:
            True si imprimió OK, False si error.
        """
        try:
            if not self.nombre_impresora:
                print("❌ Impresora no disponible para QR de cobro MP")
                return False

            print(f"📱 Imprimiendo QR de cobro MP — $ {monto:,.2f}")

            # Comandos ESC/POS base
            CENTER   = b'\x1B\x61\x01'
            LEFT     = b'\x1B\x61\x00'
            BOLD_ON  = b'\x1B\x45\x01'
            BOLD_OFF = b'\x1B\x45\x00'
            INIT     = b'\x1B\x40'

            datos = bytearray()
            datos += INIT
            datos += CENTER

            # ─── Header del comercio ───
            datos += BOLD_ON
            datos += TICKET_NOMBRE_COMERCIAL.encode('cp850', errors='replace')
            datos += BOLD_OFF
            datos += b'\n'

            # ─── Título "PAGÁ CON QR" en doble alto ───
            datos += b'\x1D\x21\x01'   # 1x ancho, 2x alto
            datos += BOLD_ON
            datos += 'PAGA CON QR'.encode('cp850', errors='replace')
            datos += BOLD_OFF
            datos += b'\x1D\x21\x00'
            datos += b'\n'

            datos += self.linea_separadora('=').encode('cp850', errors='replace')
            datos += b'\n'

            # ─── MONTO bien grande (2x ancho + 2x alto) ───
            monto_str = f"$ {monto:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            datos += b'\x1D\x21\x11'   # 2x ancho + 2x alto
            datos += BOLD_ON
            datos += monto_str.encode('cp850', errors='replace')
            datos += BOLD_OFF
            datos += b'\x1D\x21\x00'   # reset tamaño
            datos += b'\n'

            datos += self.linea_separadora('=').encode('cp850', errors='replace')
            datos += b'\n\n'

            # ─── QR Code nativo (ESC/POS GS ( k) ───
            url_bytes = url_pago.encode('utf-8')

            # Modelo 2
            datos += b'\x1D\x28\x6B\x04\x00\x31\x41\x32\x00'
            # Tamaño módulo: 8 (grande)
            datos += b'\x1D\x28\x6B\x03\x00\x31\x43\x08'
            # Corrección H (30% redundancia, robusto)
            datos += b'\x1D\x28\x6B\x03\x00\x31\x45\x33'
            # Cargar datos
            pL = (len(url_bytes) + 3) % 256
            pH = (len(url_bytes) + 3) // 256
            datos += b'\x1D\x28\x6B' + bytes([pL, pH]) + b'\x31\x50\x30' + url_bytes
            # Imprimir QR
            datos += b'\x1D\x28\x6B\x03\x00\x31\x51\x30'
            datos += b'\n'

            # ─── Instrucciones para el cliente ───
            datos += BOLD_ON
            datos += b'\x1D\x21\x01'   # 2x alto
            datos += 'ESCANEALO CON'.encode('cp850', errors='replace')
            datos += b'\n'
            datos += 'TU BILLETERA'.encode('cp850', errors='replace')
            datos += b'\x1D\x21\x00'
            datos += BOLD_OFF
            datos += b'\n\n'

            datos += 'MercadoPago * Cuenta DNI'.encode('cp850', errors='replace')
            datos += b'\n'
            datos += 'Naranja X * Uala * Brubank'.encode('cp850', errors='replace')
            datos += b'\n'
            datos += 'y cualquier billetera con QR'.encode('cp850', errors='replace')
            datos += b'\n\n'

            datos += self.linea_separadora('-').encode('cp850', errors='replace')
            datos += b'\n'

            # ─── Descripción y fecha ───
            datos += descripcion.encode('cp850', errors='replace')[:40]
            datos += b'\n'
            datos += datetime.now().strftime('%d/%m/%Y %H:%M').encode('cp850', errors='replace')
            datos += b'\n\n'

            # Footer
            datos += 'Powered by FactuFacil'.encode('cp850', errors='replace')
            datos += b'\n\n\n'

            # Corte de papel - GS V B (moderno, no duplica como ESC i en algunas EPSON)
            datos += b'\x1D\x56\x42\x00'

            # ─── Enviar a impresora ───
            print("📄 Enviando QR de cobro a impresora...")
            hPrinter = win32print.OpenPrinter(self.nombre_impresora)
            try:
                hJob = win32print.StartDocPrinter(hPrinter, 1, ("QR_Cobro_MP", None, "RAW"))
                try:
                    win32print.StartPagePrinter(hPrinter)
                    win32print.WritePrinter(hPrinter, bytes(datos))
                    win32print.EndPagePrinter(hPrinter)
                    print(f"✅ QR de cobro impreso ($ {monto:,.2f})")
                    return True
                finally:
                    win32print.EndDocPrinter(hPrinter)
            finally:
                win32print.ClosePrinter(hPrinter)

        except Exception as e:
            print(f"❌ Error imprimiendo QR de cobro: {e}")
            import traceback
            traceback.print_exc()
            return False


# ============================================
# AQUÍ TERMINA LA CLASE - TODO LO DE ABAJO VA SIN INDENTACIÓN
# ============================================

# Instancia global de la impresora (80mm = 42 caracteres)
impresora_termica = ImpresoraTermica(ancho_mm=80)

# *** FUNCIONES PARA USAR EN FLASK ***
def obtener_estado_impresora():
    """Función para endpoint Flask"""
    return impresora_termica.verificar_estado()

def imprimir_factura_termica(datos_factura):
    """Función para endpoint Flask - recibe datos en formato dict"""
    try:
        class FacturaSimulada:
            def __init__(self, datos):
                self.numero = datos.get('numero', '0001-00000001')
                self.tipo_comprobante = datos.get('tipo_comprobante', '11')
                self.fecha = datetime.now()
                self.subtotal = datos.get('subtotal', 0)
                self.iva = datos.get('iva', 0)
                self.total = datos.get('total', 0)
                self.cae = datos.get('cae', None)
                self.vto_cae = datos.get('vto_cae', None)
                
                class ClienteSimulado:
                    def __init__(self, cliente_data):
                        if cliente_data:
                            self.nombre = cliente_data.get('nombre', 'Consumidor Final')
                            self.documento = cliente_data.get('documento', None)
                            self.tipo_documento = cliente_data.get('tipo_documento', 'DNI')
                        else:
                            self.nombre = 'Consumidor Final'
                            self.documento = None
                            self.tipo_documento = None
                
                self.cliente = ClienteSimulado(datos.get('cliente'))
                
                class UsuarioSimulado:
                    def __init__(self):
                        self.nombre = 'Sistema'
                
                self.usuario = UsuarioSimulado()
                
                class DetalleSimulado:
                    def __init__(self, item_data):
                        self.cantidad = item_data.get('cantidad', 1)
                        self.precio_unitario = item_data.get('precio_unitario', 0)
                        self.subtotal = item_data.get('subtotal', 0)
                        
                        class ProductoSimulado:
                            def __init__(self, item_data):
                                self.nombre = item_data.get('nombre', 'Producto')
                        
                        self.producto = ProductoSimulado(item_data)
                
                self.detalles = [DetalleSimulado(item) for item in datos.get('items', [])]
        
        factura_sim = FacturaSimulada(datos_factura)
        resultado = impresora_termica.imprimir_factura(factura_sim)
        
        if resultado:
            return {
                'success': True,
                'mensaje': f'Factura impresa correctamente en {impresora_termica.nombre_impresora}'
            }
        else:
            return {
                'success': False,
                'error': 'Error al imprimir factura'
            }
            
    except Exception as e:
        logger.error(f"Error en imprimir_factura_termica: {e}")
        return {
            'success': False,
            'error': str(e)
        }

def imprimir_remito_termico(datos_remito):
    """Función para endpoint Flask - imprime remito a partir de dict.

    Espera dict con: numero_completo, punto_venta, numero, fecha, cliente_nombre,
    documento, tipo_documento, direccion, condicion_iva, zona_nombre,
    usuario_nombre, observaciones, items=[{nombre, cantidad, subtotal}].
    """
    try:
        class RemitoSimulado:
            def __init__(self, d):
                self.numero_completo = d.get('numero_completo', '')
                self.punto_venta     = d.get('punto_venta', '')
                self.numero          = d.get('numero', '')
                # fecha puede venir como datetime o como datei
                f = d.get('fecha')
                if f is None:
                    self.fecha = datetime.now()
                else:
                    # si es date sin time, convertir a datetime
                    try:
                        if hasattr(f, 'hour'):
                            self.fecha = f
                        else:
                            self.fecha = datetime.combine(f, datetime.min.time())
                    except Exception:
                        self.fecha = datetime.now()
                self.cliente_nombre  = d.get('cliente_nombre', 'Sin cliente')
                self.documento       = d.get('documento')
                self.tipo_documento  = d.get('tipo_documento') or 'DNI'
                self.direccion       = d.get('direccion')
                self.condicion_iva   = d.get('condicion_iva')
                self.zona_nombre     = d.get('zona_nombre')
                self.usuario_nombre  = d.get('usuario_nombre', 'Sistema')
                self.observaciones   = d.get('observaciones', '')
                self.items           = d.get('items', [])

        remito_sim = RemitoSimulado(datos_remito)
        ok = impresora_termica.imprimir_remito(remito_sim)
        if ok:
            return {
                'success': True,
                'mensaje': f'Remito impreso correctamente en {impresora_termica.nombre_impresora}',
            }
        return {'success': False, 'error': 'Error al imprimir remito'}

    except Exception as e:
        logger.error(f"Error en imprimir_remito_termico: {e}")
        return {'success': False, 'error': str(e)}


def imprimir_qr_escaner_termica(url='https://lakapp.dyndns.info/escaner', titulo='Lakapp'):
    """Wrapper para usar desde Flask (o desde script standalone).
    Imprime un cartel A4 de góndola con QR del escáner público en la térmica.

    Returns dict con {'success': bool, 'mensaje': str} o {'success': False, 'error': str}.
    """
    try:
        ok = impresora_termica.imprimir_qr_escaner(url=url, titulo=titulo)
        if ok:
            return {
                'success': True,
                'mensaje': f'QR del escáner impreso correctamente en {impresora_termica.nombre_impresora}',
            }
        return {'success': False, 'error': 'No se pudo imprimir el QR'}

    except Exception as e:
        logger.error(f"Error en imprimir_qr_escaner_termica: {e}")
        return {'success': False, 'error': str(e)}