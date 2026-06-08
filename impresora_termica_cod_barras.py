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

    def _buscar_impresora_termica(self):
        """Buscar impresora térmica automáticamente - EPSON TM-m30II prioritaria"""
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
            
            # Buscar por prioridad: primero el nombre prioritario, luego la impresora
            # (loop invertido para respetar el orden de prioridad)
            for prioritario in nombres_termicas_prioritarios:
                for impresora in impresoras:
                    nombre = impresora[2].lower()
                    if prioritario.lower() in nombre:
                        print(f"🖨️ ✅ EPSON detectada: {impresora[2]}")
                        print(f"🎯 Esta impresora térmica profesional será usada")
                        return impresora[2]
            
            # Si no encuentra EPSON, buscar otras térmicas
            nombres_termicas_secundarios = [
                'tm-t(203dpi)',
                'tm-t20',
                'pos-58', 'pos58',
                'tm-m30ii', 'tm-m30', 'epson tm-m30',
                'thermal', 'receipt', 'pos', 'tm-', 'rp-', 'sp-',
                'termica', 'ticket', 'epson', 'star', 'citizen',
                'xprinter', 'godex', 'zebra', 'bixolon'
            ]
            
            for impresora in impresoras:
                nombre = impresora[2].lower()
                for termico in nombres_termicas_secundarios:
                    if termico in nombre:
                        print(f"🖨️ ⚠️ Impresora térmica secundaria detectada: {impresora[2]}")
                        print(f"💡 Recomendación: Usar EPSON TM-m30II si está disponible")
                        return impresora[2]
            
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
            
            # ENCABEZADO DE PRODUCTOS
            lineas.append(f"{'PRODUCTO':<14} {'CANT':>6} {'P.U':>9} {'TOTAL':>10}")
            lineas.append(self.linea_separadora())
            
            # PRODUCTOS
            if hasattr(factura, 'detalles') and factura.detalles:
                # Verificar si es Factura B
                es_factura_b = str(factura.tipo_comprobante) in ['6', '06']
                
                for detalle in factura.detalles:
                    max_nombre = 14
                    cant_space = 6
                    precio_space = 9
                    total_space = 10
                    
                    if hasattr(detalle, 'producto') and detalle.producto:
                        nombre_producto = getattr(detalle.producto, 'nombre', 'Producto')
                    else:
                        nombre_producto = 'Producto'
                    
                    nombre = self.truncar_texto(nombre_producto, max_nombre)
                    
                    try:
                        cant_str = f"{float(detalle.cantidad):.3f}"
                        
                        # Para Factura C: mostrar precios CON IVA incluido
                        es_factura_c_item = str(factura.tipo_comprobante) in ['11', '12', '13']
                        if es_factura_c_item:
                            porcentaje_iva = float(getattr(detalle, 'porcentaje_iva', 21.0))
                            precio_sin_iva = float(detalle.precio_unitario)
                            precio_con_iva = precio_sin_iva * (1 + porcentaje_iva / 100)
                            
                            subtotal_sin_iva = float(detalle.subtotal)
                            importe_iva = float(getattr(detalle, 'importe_iva', 0))
                            total_con_iva = subtotal_sin_iva + importe_iva
                            
                            precio_str = f"{precio_con_iva:,.2f}"
                            total_str = f"{total_con_iva:,.2f}"
                        else:
                            # Para Factura A y B: mostrar precios SIN IVA (Ley 27.743)
                            precio_str = f"{float(detalle.precio_unitario):,.2f}"
                            total_str = f"{float(detalle.subtotal):,.2f}"
                            
                    except (ValueError, AttributeError):
                        cant_str = "1"
                        precio_str = "0"
                        total_str = "0"
                    
                    linea = f"{nombre:<{max_nombre}} {cant_str:>{cant_space}} {precio_str:>{precio_space}} {total_str:>{total_space}}"
                    lineas.append(linea[:self.ancho])
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
            cae = getattr(factura, 'cae', None)
            if cae:
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
            '13': 'NOTA CRED C'
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

    def imprimir_cartel_precio(self, producto, tiene_ofertas=False):
        """Imprimir cartel de precio individual para producto"""
        try:
            if not self.nombre_impresora:
                print("❌ Impresora no disponible para carteles")
                return False
            
            print(f"🏷️ Imprimiendo cartel para: {producto.codigo}")
            
            precio = float(producto.precio)
            nombre_corto = producto.nombre[:30] if len(producto.nombre) > 30 else producto.nombre
            
            contenido = []
            
            # contenido.append("=" * self.ancho)  # ✅ COMENTADO
            # Encabezado: depende si el producto es pesable o no.
            #   - NO pesable: código de barras (con el código humano legible debajo).
            #   - PESABLE: texto "Cód: X" agrandado y bold (no usamos barcode porque el
            #     código real de balanza incluye peso variable y se genera en la venta).
            es_pesable = bool(getattr(producto, 'es_pesable', False))
            codigo_str = str(producto.codigo or "").strip()

            if es_pesable or not codigo_str:
                # Código en texto, agrandado + bold (auto-fit como el nombre)
                codigo_texto = f"Cód: {codigo_str}"
                cod_largo = len(codigo_texto)
                if cod_largo * 2 <= self.ancho:
                    cmd_cod_size = "\x1D\x21\x11"  # 2x ancho + 2x alto
                    cod_mult_w = 2
                else:
                    cmd_cod_size = "\x1D\x21\x01"  # 1x ancho + 2x alto
                    cod_mult_w = 1
                ancho_eff_cod = self.ancho // cod_mult_w
                espacios_cod = max(0, (ancho_eff_cod - cod_largo) // 2)
                cod_centrado = " " * espacios_cod + codigo_texto
                contenido.append(
                    "\x1B\x45\x01"      # negrita ON
                    + "\x1B\x47\x01"    # double-strike ON (refuerza la negrita)
                    + cmd_cod_size      # tamaño grande
                    + cod_centrado
                    + "\x1D\x21\x00"    # reset tamaño
                    + "\x1B\x47\x00"    # double-strike OFF
                    + "\x1B\x45\x00"    # negrita OFF
                )
            else:
                # SELECCIÓN DEL TIPO DE BARCODE.
                # Como los códigos en SCHIRO están cargados a mano (códigos internos,
                # NO son EAN/UPC reales del fabricante), usamos CODE39 que es el
                # formato estándar para códigos internos:
                #   - No tiene check digit obligatorio → se imprime tal cual.
                #   - Lo lee cualquier lector retail sin configurar nada.
                #   - El lector devuelve EXACTAMENTE el código que está en la base.
                # Solo si el código tiene caracteres fuera del charset de CODE39
                # (minúsculas no convertibles, símbolos raros, llaves, etc.),
                # caemos a CODE128 como último recurso.
                code39_chars = set("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ -.$/+%")
                codigo_up = codigo_str.upper()

                if all(c in code39_chars for c in codigo_up):
                    # CODE39 (m=69, Function B). El asterisco "*" se agrega
                    # automáticamente como start/stop por la impresora.
                    barcode_data = "\x1D\x6B\x45" + chr(len(codigo_up)) + codigo_up
                else:
                    # CODE128 set B - último recurso. Escapar "{" como "{{".
                    safe = codigo_str.replace("{", "{{")
                    data128 = "{B" + safe
                    barcode_data = "\x1D\x6B\x49" + chr(len(data128)) + data128

                barcode_block = (
                    "\x1B\x61\x01"          # alineación: centro
                    + "\x1D\x68\x64"        # GS h 100: altura ~13mm
                    + "\x1D\x77\x02"        # GS w 2: módulo angosto (CODE39 ocupa más
                                            # ancho que EAN, bajamos para que entre
                                            # con buena quiet zone aún en códigos largos)
                    + "\x1D\x48\x02"        # GS H 2: HRI (texto) debajo
                    + "\x1D\x66\x00"        # GS f 0: fuente HRI A
                    + barcode_data          # comando completo del barcode
                    + "\x1B\x61\x00"        # alineación: izquierda (reset)
                )
                # Línea en blanco antes/después → asegura quiet zone vertical
                contenido.append("")
                contenido.append(barcode_block)
                contenido.append("")
            # contenido.append("=" * self.ancho)  # ✅ COMENTADO
            
            if tiene_ofertas:
                contenido.append("")
                contenido.append("*" * self.ancho)
                contenido.append(self.centrar_texto("¡OFERTA ESPECIAL!"))
                contenido.append("*" * self.ancho)
            
            contenido.append("")
            # Nombre del producto: SIEMPRE en 2x ancho + 2x alto + bold + double-strike.
            # Para conseguir el grosor "estilo precio", partimos el nombre en hasta
            # 2 líneas si no entra en una sola al doble ancho. Es preferible 2 líneas
            # gruesas que 1 línea fina y estirada.
            ancho_2x = self.ancho // 2  # chars que entran en una línea a 2x ancho

            def _wrap_2_lineas(texto, ancho_max):
                """Parte texto en hasta 2 líneas respetando palabras."""
                texto = (texto or "").strip()
                if len(texto) <= ancho_max:
                    return [texto]
                palabras = texto.split()
                if not palabras:
                    return [texto[:ancho_max]]
                linea1, i = "", 0
                while i < len(palabras):
                    cand = palabras[i] if not linea1 else linea1 + " " + palabras[i]
                    if len(cand) <= ancho_max:
                        linea1 = cand
                        i += 1
                    else:
                        break
                if not linea1:
                    # palabra única demasiado larga: truncar
                    return [palabras[0][:ancho_max]]
                resto = " ".join(palabras[i:])
                if not resto:
                    return [linea1]
                if len(resto) > ancho_max:
                    resto = resto[:ancho_max]
                return [linea1, resto]

            lineas_nombre = _wrap_2_lineas(nombre_corto, ancho_2x)
            for idx, linea in enumerate(lineas_nombre):
                nl = len(linea)
                if nl * 2 <= self.ancho:
                    cmd_size_l = "\x1D\x21\x11"  # 2x ancho + 2x alto
                    mw = 2
                else:
                    cmd_size_l = "\x1D\x21\x01"  # 1x ancho + 2x alto (fallback)
                    mw = 1
                ancho_eff = self.ancho // mw
                esp = max(0, (ancho_eff - nl) // 2)
                centrado_l = " " * esp + linea
                contenido.append(
                    "\x1B\x45\x01"      # negrita (emphasis) ON
                    + "\x1B\x47\x01"    # double-strike ON (refuerza la negrita)
                    + "\x1B\x20\x01"    # ESC SP 1: +1 dot entre letras
                    + cmd_size_l        # tamaño
                    + centrado_l
                    + "\x1D\x21\x00"    # reset tamaño
                    + "\x1B\x20\x00"    # reset spacing
                    + "\x1B\x47\x00"    # double-strike OFF
                    + "\x1B\x45\x00"    # negrita OFF
                )
            
            contenido.append("")
            contenido.append("-" * self.ancho)
            
            # Formato compacto: sin espacio entre $ y número.
            # Si el precio es redondo (.00), no mostrar decimales para ganar 3 chars
            # y poder usar un multiplicador más grande.
            if precio == int(precio):
                precio_texto = f"${int(precio)}"
            else:
                precio_texto = f"${precio:.2f}"

            # Buscar el multiplicador MÁS GRANDE (hasta 8x, máximo de ESC/POS)
            # que permita que el precio entre en UNA línea del papel.
            # GS ! n: nibble alto = ancho-1 (0-7), nibble bajo = alto-1 (0-7).
            # Para mult m (ancho = alto): n = (m-1) << 4 | (m-1) = 0x11 * (m-1)
            # 2x → \x11 · 3x → \x22 · 4x → \x33 · ... · 8x → \x77
            largo = len(precio_texto)
            mult = 2  # piso de seguridad (= tamaño original)
            for m in range(8, 1, -1):
                if largo * m <= self.ancho:
                    mult = m
                    break

            cmd_size = "\x1D\x21" + chr(0x11 * (mult - 1))
            cmd_reset = "\x1D\x21\x00"

            # Centrado fino: espacios NORMALES (1x) antes del comando de tamaño.
            # Si en cambio usara espacios "lógicos" agrandados, perdería precisión
            # (cada espacio ocuparía mult columnas físicas) y el texto quedaría
            # corrido a la izquierda cuando el ancho del papel no es múltiplo de mult.
            ancho_consumido = largo * mult
            espacios = max(0, (self.ancho - ancho_consumido) // 2)
            contenido.append(
                "\x1B\x45\x01"          # negrita ON
                + " " * espacios        # espacios NORMALES (centrado fino)
                + cmd_size              # tamaño gigante
                + precio_texto
                + cmd_reset             # reset tamaño
                + "\x1B\x45\x00"        # negrita OFF
            )
            contenido.append("")
                        
            contenido.append("-" * self.ancho)
            
            # codigo_texto = f"Codigo: {producto.codigo}"
            # contenido.append(self.centrar_texto(codigo_texto))
            
            if tiene_ofertas:
                if producto.es_combo and hasattr(producto, 'calcular_ahorro_combo'):
                    ahorro = producto.calcular_ahorro_combo()
                    if ahorro > 0:
                        contenido.append("")
                        ahorro_texto = f"Ahorro: $ {ahorro:.2f}"
                        contenido.append(self.centrar_texto(ahorro_texto))
            
            contenido.append("")
            # contenido.append("=" * self.ancho)  # ✅ COMENTADO
            
            # fecha_hora = datetime.now().strftime("%d/%m/%Y %H:%M")
            # contenido.append(self.centrar_texto(fecha_hora))
            
            # contenido.append("=" * self.ancho)  # ✅ COMENTADO
            contenido.extend([""] * 3)
            
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