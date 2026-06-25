# -*- coding: utf-8 -*-
"""
factura_pdf.py — Generador de PDF A4 de facturas para FactuFácil
═══════════════════════════════════════════════════════════════════════════════
Genera un PDF en hoja A4 con el mismo contenido que el ticket térmico pero con
formato de factura argentina (letra en recuadro, datos del emisor/receptor,
detalle de ítems, totales, CAE + vencimiento y QR de AFIP).

Uso desde app.py:

    from factura_pdf import generar_pdf_factura
    pdf_bytes = generar_pdf_factura(factura, emisor=emisor_dict, qr_base64=qr_b64)

- factura    : objeto Factura (con .detalles, .cliente, .medios_pago, etc.)
- emisor     : dict con datos del emisor (ver EMISOR_DEFAULT). Opcional.
- qr_base64  : string base64 (sin encabezado data:) de la imagen QR de AFIP. Opcional.

Devuelve: bytes del PDF listo para enviar con send_file(BytesIO(...)).
═══════════════════════════════════════════════════════════════════════════════
"""

import base64
import os
from io import BytesIO
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, KeepTogether
)


# ─────────────────────────────────────────────────────────────────────────────
# LOGO DEL EMISOR
# ─────────────────────────────────────────────────────────────────────────────
# Reemplaza el nombre/razón social del emisor en el encabezado por una imagen.
# La ruta se construye relativa a este archivo, de modo que si se mueve la
# carpeta del proyecto (ej. de C:\FactuFacilDistribuidora\ a D:\FactuFacil\),
# el logo sigue resolviéndose sin tocar código.
#
# Para usar otro logo en otro cliente, cambiar solo el nombre del archivo
# en LOGO_FILENAME (o más adelante: poner 'logo_empresa.png' universal).
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGO_FILENAME = 'logo_lkd.png'
LOGO_PATH = os.path.join(_BASE_DIR, 'static', 'images', LOGO_FILENAME)


# ─────────────────────────────────────────────────────────────────────────────
# Valores por defecto del emisor (se sobreescriben con el dict `emisor`)
# ─────────────────────────────────────────────────────────────────────────────
EMISOR_DEFAULT = {
    'nombre_comercial': 'COMERCIO',
    'razon_social':     'Razón Social',
    'cuit':             '',
    'condicion_iva':    'Responsable Monotributo',
    'direccion':        '',
    'telefono':         '',
    'frase_extra':      'Gracias por su compra!',
}

# Color de marca (gris azulado oscuro)
COLOR_PRIMARIO = colors.HexColor('#1f2937')
COLOR_SUAVE = colors.HexColor('#6b7280')
COLOR_LINEA = colors.HexColor('#d1d5db')
COLOR_FONDO_HEADER = colors.HexColor('#f3f4f6')


# ─────────────────────────────────────────────────────────────────────────────
# Helpers de tipo de comprobante
# ─────────────────────────────────────────────────────────────────────────────
def _letra_nombre_codigo(tipo_comprobante):
    """Devuelve (letra, nombre, codigo_str) según el tipo de comprobante AFIP."""
    t = str(tipo_comprobante).zfill(2)
    mapa = {
        '01': ('A', 'FACTURA', '01'),
        '02': ('A', 'NOTA DE DÉBITO', '02'),
        '03': ('A', 'NOTA DE CRÉDITO', '03'),
        '06': ('B', 'FACTURA', '06'),
        '07': ('B', 'NOTA DE DÉBITO', '07'),
        '08': ('B', 'NOTA DE CRÉDITO', '08'),
        '11': ('C', 'FACTURA', '11'),
        '12': ('C', 'NOTA DE DÉBITO', '12'),
        '13': ('C', 'NOTA DE CRÉDITO', '13'),
        '51': ('M', 'FACTURA', '51'),
        '53': ('M', 'NOTA DE CRÉDITO', '53'),
        '99': ('X', 'COMPROBANTE INTERNO', '99'),
    }
    return mapa.get(t, ('X', 'COMPROBANTE', t))


def _discrimina_iva(letra):
    """Solo la Factura A (y M) discrimina IVA. B/C/X no."""
    return letra in ('A', 'M')


def _fmt(n):
    """Formatea un número como $ 1.234,56 (formato AR)."""
    try:
        v = float(n)
    except (TypeError, ValueError):
        v = 0.0
    s = f"{v:,.2f}"                      # 1,234.56
    s = s.replace(',', 'X').replace('.', ',').replace('X', '.')   # 1.234,56
    return f"$ {s}"


def _fmt_fecha(f):
    if not f:
        return datetime.now().strftime('%d/%m/%Y')
    if hasattr(f, 'strftime'):
        return f.strftime('%d/%m/%Y')
    return str(f)


# ─────────────────────────────────────────────────────────────────────────────
# Generador principal
# ─────────────────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────
# Canvas que numera "Hoja X de Y". Guarda cada página y al cerrar dibuja el
# número con el total ya conocido. Es el patrón canónico de ReportLab.
# ─────────────────────────────────────────────────────────────────────────────
from reportlab.pdfgen import canvas as _rl_canvas


class _NumberedCanvas(_rl_canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_pages = []

    def showPage(self):
        self._saved_pages.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total = len(self._saved_pages)
        for state in self._saved_pages:
            self.__dict__.update(state)
            if total > 1:  # solo numerar si hay más de una hoja
                self.saveState()
                self.setFont('Helvetica', 7)
                self.setFillColor(COLOR_SUAVE)
                self.drawRightString(A4[0] - 14 * mm, 8 * mm,
                                     f"Hoja {self._pageNumber} de {total}")
                self.restoreState()
            super().showPage()
        super().save()


def generar_pdf_factura(factura, emisor=None, qr_base64=None):
    em = dict(EMISOR_DEFAULT)
    if emisor:
        em.update({k: v for k, v in emisor.items() if v is not None})

    letra, nombre_comp, codigo = _letra_nombre_codigo(factura.tipo_comprobante)
    discrimina = _discrimina_iva(letra)

    # Estilos
    ss = getSampleStyleSheet()
    st_emisor_nombre = ParagraphStyle('em_nom', parent=ss['Normal'], fontName='Helvetica-Bold',
                                      fontSize=15, leading=18, textColor=COLOR_PRIMARIO)
    st_emisor = ParagraphStyle('em', parent=ss['Normal'], fontSize=8.5, leading=12,
                               textColor=COLOR_PRIMARIO)
    st_comp_tit = ParagraphStyle('comp_tit', parent=ss['Normal'], fontName='Helvetica-Bold',
                                 fontSize=14, leading=17, alignment=TA_LEFT, textColor=COLOR_PRIMARIO)
    st_comp = ParagraphStyle('comp', parent=ss['Normal'], fontSize=9, leading=13,
                             textColor=COLOR_PRIMARIO)
    st_letra = ParagraphStyle('letra', parent=ss['Normal'], fontName='Helvetica-Bold',
                              fontSize=34, leading=36, alignment=TA_CENTER, textColor=COLOR_PRIMARIO)
    st_cod = ParagraphStyle('cod', parent=ss['Normal'], fontSize=7, leading=9,
                            alignment=TA_CENTER, textColor=COLOR_SUAVE)
    st_label = ParagraphStyle('label', parent=ss['Normal'], fontName='Helvetica-Bold',
                              fontSize=8.5, leading=12, textColor=COLOR_PRIMARIO)
    st_val = ParagraphStyle('val', parent=ss['Normal'], fontSize=8.5, leading=12,
                            textColor=COLOR_PRIMARIO)
    st_th = ParagraphStyle('th', parent=ss['Normal'], fontName='Helvetica-Bold',
                           fontSize=8.5, leading=11, textColor=colors.white)
    st_td = ParagraphStyle('td', parent=ss['Normal'], fontSize=8.5, leading=11,
                           textColor=COLOR_PRIMARIO)
    st_td_r = ParagraphStyle('td_r', parent=st_td, alignment=TA_RIGHT)
    st_foot = ParagraphStyle('foot', parent=ss['Normal'], fontSize=8, leading=11,
                             alignment=TA_CENTER, textColor=COLOR_SUAVE)
    st_orig = ParagraphStyle('orig', parent=ss['Normal'], fontName='Helvetica-Bold',
                             fontSize=9, alignment=TA_CENTER, textColor=COLOR_SUAVE)

    ancho_util = A4[0] - 28 * mm  # márgenes 14mm cada lado

    # ── ENCABEZADO: emisor | letra | comprobante ────────────────────────────
    # En lugar del nombre comercial + razón social, mostrar el logo del emisor.
    # Si el logo no existe en disco, caemos a los textos como respaldo seguro
    # (para no romper la factura por un archivo faltante).
    emisor_cell = []
    if os.path.exists(LOGO_PATH):
        try:
            # Logo a tamaño razonable para el encabezado (alto ~22mm, ancho auto)
            logo_img = Image(LOGO_PATH, width=50 * mm, height=22 * mm, kind='proportional')
            emisor_cell.append(logo_img)
            emisor_cell.append(Spacer(1, 4))
        except Exception:
            # Si la imagen está corrupta o reportlab no la puede abrir,
            # usar el nombre como respaldo
            emisor_cell.append(Paragraph(em['nombre_comercial'], st_emisor_nombre))
            emisor_cell.append(Spacer(1, 2))
            emisor_cell.append(Paragraph(em['razon_social'], st_emisor))
    else:
        # Respaldo si el archivo de logo no está en disco
        emisor_cell.append(Paragraph(em['nombre_comercial'], st_emisor_nombre))
        emisor_cell.append(Spacer(1, 2))
        emisor_cell.append(Paragraph(em['razon_social'], st_emisor))
    if em['direccion']:
        emisor_cell.append(Paragraph(em['direccion'], st_emisor))
    if em['telefono']:
        emisor_cell.append(Paragraph(f"Tel: {em['telefono']}", st_emisor))
    emisor_cell.append(Paragraph(em['condicion_iva'], st_emisor))

    letra_cell = [Paragraph(letra, st_letra), Paragraph(f"COD. {codigo}", st_cod)]

    comp_cell = [
        Paragraph(nombre_comp, st_comp_tit),
        Spacer(1, 3),
        Paragraph(f"<b>Nº:</b> {factura.numero or '-'}", st_comp),
        Paragraph(f"<b>Fecha:</b> {_fmt_fecha(factura.fecha)}", st_comp),
        Paragraph(f"<b>CUIT:</b> {em['cuit']}", st_comp),
    ]

    header = Table([[emisor_cell, letra_cell, comp_cell]],
                   colWidths=[ancho_util * 0.42, ancho_util * 0.16, ancho_util * 0.42])
    header.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1, COLOR_PRIMARIO),
        ('LINEAFTER', (0, 0), (0, 0), 1, COLOR_PRIMARIO),
        ('LINEBEFORE', (2, 0), (2, 0), 1, COLOR_PRIMARIO),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (1, 0), (1, 0), 'CENTER'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))

    story = [header, Spacer(1, 2), Paragraph('ORIGINAL', st_orig), Spacer(1, 6)]

    # ── DATOS DEL CLIENTE ────────────────────────────────────────────────────
    cli = getattr(factura, 'cliente', None)
    cli_nombre = getattr(cli, 'nombre', 'Consumidor Final') if cli else 'Consumidor Final'
    cli_doc = getattr(cli, 'documento', '') if cli else ''
    cli_tipo_doc = getattr(cli, 'tipo_documento', '') if cli else ''
    cli_cond = getattr(cli, 'condicion_iva', '') if cli else ''
    cli_dir = getattr(cli, 'direccion', '') if cli else ''

    doc_label = cli_tipo_doc or 'Doc'
    cliente_data = [
        [Paragraph('Señor/es:', st_label), Paragraph(cli_nombre or '-', st_val),
         Paragraph(f'{doc_label}:', st_label), Paragraph(cli_doc or '-', st_val)],
        [Paragraph('Condición IVA:', st_label), Paragraph(cli_cond or '-', st_val),
         Paragraph('Domicilio:', st_label), Paragraph(cli_dir or '-', st_val)],
    ]
    cliente_tbl = Table(cliente_data,
                        colWidths=[ancho_util * 0.13, ancho_util * 0.37,
                                   ancho_util * 0.13, ancho_util * 0.37])
    cliente_tbl.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 0.7, COLOR_LINEA),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story += [cliente_tbl, Spacer(1, 8)]

    # Leyenda obligatoria (RG 5022/2021 - Ley 27.618):
    # Factura A emitida a un Monotributista debe llevar esta leyenda.
    # Se detecta igual que en el resto del sistema: condicion_iva con 'MONOTRIB'.
    if letra == 'A' and 'MONOTRIB' in str(cli_cond or '').upper():
        st_leyenda_mono = ParagraphStyle('leyenda_mono', parent=ss['Normal'],
                                         fontName='Helvetica-Bold', fontSize=8, leading=11)
        story += [Paragraph('Receptor del comprobante - Responsable Monotributo',
                            st_leyenda_mono),
                  Spacer(1, 8)]

    # ── DETALLE DE ÍTEMS ─────────────────────────────────────────────────────
    # En Factura A/M se agrega la columna "% IVA" (alícuota por ítem).
    if discrimina:
        encabezados = [
            Paragraph('Código', st_th), Paragraph('Descripción', st_th),
            Paragraph('Cant.', st_th), Paragraph('P. Unit.', st_th),
            Paragraph('% IVA', st_th), Paragraph('Importe', st_th),
        ]
        col_widths = [ancho_util * 0.13, ancho_util * 0.39, ancho_util * 0.09,
                      ancho_util * 0.15, ancho_util * 0.09, ancho_util * 0.15]
    else:
        encabezados = [
            Paragraph('Código', st_th), Paragraph('Descripción', st_th),
            Paragraph('Cant.', st_th), Paragraph('P. Unit.', st_th),
            Paragraph('Importe', st_th),
        ]
        col_widths = [ancho_util * 0.14, ancho_util * 0.44, ancho_util * 0.10,
                      ancho_util * 0.16, ancho_util * 0.16]
    filas = [encabezados]

    total_neto = 0.0
    total_iva = 0.0
    iva_por_alicuota = {}   # {21.0: {'neto': x, 'iva': y}, 10.5: {...}}
    detalles = getattr(factura, 'detalles', []) or []
    for d in detalles:
        prod = getattr(d, 'producto', None)
        cod = getattr(prod, 'codigo', '') if prod else ''
        desc = getattr(prod, 'nombre', 'Producto') if prod else 'Producto'
        cant = float(getattr(d, 'cantidad', 0) or 0)
        subt = float(getattr(d, 'subtotal', 0) or 0)          # neto (sin IVA)
        iva_imp = float(getattr(d, 'importe_iva', 0) or 0)
        iva_pct = float(getattr(d, 'porcentaje_iva', 0) or 0)
        punit_neto = float(getattr(d, 'precio_unitario', 0) or 0)

        total_neto += subt
        total_iva += iva_imp

        # Acumular por alícuota (para el desglose de la Factura A)
        if iva_pct not in iva_por_alicuota:
            iva_por_alicuota[iva_pct] = {'neto': 0.0, 'iva': 0.0}
        iva_por_alicuota[iva_pct]['neto'] += subt
        iva_por_alicuota[iva_pct]['iva'] += iva_imp

        if discrimina:
            # Factura A/M: se muestran valores netos (IVA discriminado abajo)
            punit_disp = punit_neto
            importe_disp = subt
        else:
            # Factura B/C/X: precios finales con IVA incluido
            punit_disp = punit_neto * (1 + iva_pct / 100.0)
            importe_disp = subt + iva_imp

        # cantidad: entero si es entero, si no 3 decimales
        cant_str = f"{cant:.0f}" if abs(cant - round(cant)) < 1e-6 else f"{cant:.3f}"

        fila = [
            Paragraph(cod, st_td),
            Paragraph(desc, st_td),
            Paragraph(cant_str, st_td_r),
            Paragraph(_fmt(punit_disp), st_td_r),
        ]
        if discrimina:
            fila.append(Paragraph(f"{iva_pct:g}%", st_td_r))
        fila.append(Paragraph(_fmt(importe_disp), st_td_r))
        filas.append(fila)

    items_tbl = Table(filas, colWidths=col_widths, repeatRows=1)
    items_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), COLOR_PRIMARIO),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('LINEBELOW', (0, 1), (-1, -1), 0.4, COLOR_LINEA),
        ('BOX', (0, 0), (-1, -1), 0.7, COLOR_LINEA),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, COLOR_FONDO_HEADER]),
    ]))
    story += [items_tbl, Spacer(1, 8)]

    total = float(getattr(factura, 'total', total_neto + total_iva) or 0)

    # ── Descuento aplicado (si la factura tiene uno) ─────────────────────────
    # Se lee de la relación DescuentoFactura (factura.descuento_aplicado).
    descuento_monto = 0.0
    descuento_pct = 0.0
    total_pre_desc = total_neto + total_iva
    desc_obj = getattr(factura, 'descuento_aplicado', None)
    if desc_obj:
        try:
            descuento_monto = float(getattr(desc_obj, 'monto_descuento', 0) or 0)
            descuento_pct = float(getattr(desc_obj, 'porcentaje_descuento', 0) or 0)
            _to = getattr(desc_obj, 'total_original', None)
            if _to:
                total_pre_desc = float(_to)
        except Exception:
            pass
    hay_descuento = descuento_monto > 0
    desc_label = f"Descuento ({descuento_pct:g}%):" if descuento_pct else "Descuento:"
    st_desc = ParagraphStyle('desc', parent=st_td_r, textColor=colors.HexColor('#b91c1c'))

    # ── TOTALES (alineados a la derecha) ─────────────────────────────────────
    if discrimina:
        tot_rows = [
            [Paragraph('Importe Neto Gravado:', st_label), Paragraph(_fmt(total_neto), st_td_r)],
        ]
        # Desglose del IVA por alícuota (21%, 10,5%, 27%, ...), de mayor a menor.
        for pct in sorted(iva_por_alicuota.keys(), reverse=True):
            datos = iva_por_alicuota[pct]
            if datos['iva'] > 0 or pct > 0:
                tot_rows.append([
                    Paragraph(f"IVA {pct:g}%:", st_label),
                    Paragraph(_fmt(datos['iva']), st_td_r),
                ])
        if hay_descuento:
            tot_rows.append([Paragraph('Subtotal:', st_label), Paragraph(_fmt(total_pre_desc), st_td_r)])
            tot_rows.append([Paragraph(desc_label, st_label), Paragraph('- ' + _fmt(descuento_monto), st_desc)])
        tot_rows.append([Paragraph('<b>TOTAL:</b>', st_label), Paragraph(f'<b>{_fmt(total)}</b>', st_td_r)])
    elif letra == 'B':
        tot_rows = [[Paragraph('Subtotal:', st_label), Paragraph(_fmt(total_pre_desc), st_td_r)]]
        if hay_descuento:
            tot_rows.append([Paragraph(desc_label, st_label), Paragraph('- ' + _fmt(descuento_monto), st_desc)])
        tot_rows.append([Paragraph('IVA incluido:', st_label), Paragraph(_fmt(total_iva), st_td_r)])
        tot_rows.append([Paragraph('<b>TOTAL:</b>', st_label), Paragraph(f'<b>{_fmt(total)}</b>', st_td_r)])
    else:
        # Factura C / interno: sin IVA discriminado
        tot_rows = [[Paragraph('Subtotal:', st_label), Paragraph(_fmt(total_pre_desc), st_td_r)]]
        if hay_descuento:
            tot_rows.append([Paragraph(desc_label, st_label), Paragraph('- ' + _fmt(descuento_monto), st_desc)])
        tot_rows.append([Paragraph('<b>TOTAL:</b>', st_label), Paragraph(f'<b>{_fmt(total)}</b>', st_td_r)])

    tot_tbl = Table(tot_rows, colWidths=[ancho_util * 0.22, ancho_util * 0.20])
    tot_tbl.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('LINEABOVE', (0, -1), (-1, -1), 0.8, COLOR_PRIMARIO),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('FONTSIZE', (0, -1), (-1, -1), 11),
    ]))
    # Empujar la tabla de totales a la derecha
    wrap_tot = Table([['', tot_tbl]], colWidths=[ancho_util * 0.58, ancho_util * 0.42])
    wrap_tot.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'),
                                  ('LEFTPADDING', (0, 0), (-1, -1), 0),
                                  ('RIGHTPADDING', (0, 0), (-1, -1), 0)]))

    # ═══════════════════════════════════════════════════════════════════════
    # BLOQUE DE CIERRE — se mantiene JUNTO y aparece SOLO en la última hoja.
    # Si los ítems no entran en una hoja, fluyen a la siguiente; este bloque
    # (totales → medios de pago → CAE/QR → leyenda Ley → frase) nunca se parte
    # gracias a KeepTogether, así que el comprobante siempre cierra prolijo.
    # ═══════════════════════════════════════════════════════════════════════
    cierre = [wrap_tot, Spacer(1, 8)]

    # ── MEDIOS DE PAGO ───────────────────────────────────────────────────────
    medios = getattr(factura, 'medios_pago', []) or []
    if medios:
        nombres_medio = {
            'efectivo': 'Efectivo', 'credito': 'Tarjeta Crédito',
            'debito': 'Tarjeta Débito', 'mercado_pago': 'Mercado Pago',
            'transferencia': 'Transferencia', 'CTA.CTE': 'Cuenta Corriente',
        }
        mp_rows = [[Paragraph('<b>Medios de pago</b>', st_label), '']]
        for mp in medios:
            nombre_mp = nombres_medio.get(getattr(mp, 'medio_pago', ''), getattr(mp, 'medio_pago', ''))
            mp_rows.append([Paragraph(nombre_mp, st_td),
                            Paragraph(_fmt(getattr(mp, 'importe', 0)), st_td_r)])
        mp_tbl = Table(mp_rows, colWidths=[ancho_util * 0.30, ancho_util * 0.20])
        mp_tbl.setStyle(TableStyle([
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ]))
        cierre += [mp_tbl, Spacer(1, 8)]

    # ── CAE + QR ─────────────────────────────────────────────────────────────
    cae = getattr(factura, 'cae', None)
    vto_cae = getattr(factura, 'vto_cae', None)
    if cae:
        qr_img = None
        if qr_base64:
            try:
                qr_bytes = base64.b64decode(qr_base64)
                qr_img = Image(BytesIO(qr_bytes), width=28 * mm, height=28 * mm)
            except Exception:
                qr_img = None

        cae_text = [
            Paragraph(f"<b>CAE Nº:</b> {cae}", st_comp),
            Paragraph(f"<b>Vto. CAE:</b> {_fmt_fecha(vto_cae)}", st_comp),
        ]
        cae_row = [[qr_img if qr_img else '', cae_text]]
        cae_tbl = Table(cae_row, colWidths=[32 * mm, ancho_util - 32 * mm])
        cae_tbl.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOX', (0, 0), (-1, -1), 0.7, COLOR_LINEA),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        cierre += [cae_tbl, Spacer(1, 6)]
    elif letra == 'X':
        cierre += [Paragraph('Comprobante interno — sin validez fiscal', st_orig), Spacer(1, 6)]

    # ── LEYENDA LEY 27.743 (Transparencia Fiscal al Consumidor) ──────────────
    # Solo en comprobantes que NO discriminan IVA (B y C): ahí el IVA va incluido
    # en el precio y la ley exige mostrar el "I.V.A. Contenido". En Factura A no
    # se muestra (el IVA ya está discriminado en los totales) ni en el interno (X).
    if not discrimina and letra != 'X':
        st_ley = ParagraphStyle('ley', parent=ss['Normal'], fontSize=8.5, leading=12,
                                alignment=TA_CENTER, fontName='Helvetica-Bold',
                                textColor=COLOR_PRIMARIO)
        st_ley_iva = ParagraphStyle('ley_iva', parent=ss['Normal'], fontSize=9, leading=13,
                                    alignment=TA_CENTER, fontName='Helvetica-Bold',
                                    textColor=COLOR_PRIMARIO)
        ley_cell = [
            Paragraph('Régimen de Transparencia Fiscal al Consumidor (Ley 27.743)', st_ley),
            Spacer(1, 2),
            Paragraph(f"I.V.A. Contenido: {_fmt(total_iva)}", st_ley_iva),
        ]
        ley_tbl = Table([[ley_cell]], colWidths=[ancho_util])
        ley_tbl.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 0.7, COLOR_LINEA),
            ('BACKGROUND', (0, 0), (-1, -1), COLOR_FONDO_HEADER),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ]))
        cierre += [ley_tbl, Spacer(1, 8)]

    # ── FRASE FINAL ──────────────────────────────────────────────────────────
    if em.get('frase_extra'):
        cierre.append(Paragraph(em['frase_extra'], st_foot))
    st_dev = ParagraphStyle('dev', parent=st_foot, fontSize=7, leading=9,
                            textColor=COLOR_SUAVE)
    cierre.append(Spacer(1, 2))
    cierre.append(Paragraph('Desarrollado por FactuFácil — factufacil.ar', st_dev))

    # Mantener TODO el cierre junto: si no entra en la hoja actual, salta entero
    # a la siguiente. Así nunca queda una hoja con solo el pie.
    story.append(KeepTogether(cierre))

    # ── BUILD ─────────────────────────────────────────────────────────────────
    # canvasmaker=_NumberedCanvas dibuja "Hoja X de Y" al pie (solo si hay >1 hoja).
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            leftMargin=14 * mm, rightMargin=14 * mm,
                            topMargin=14 * mm, bottomMargin=16 * mm,
                            title=f"Factura {getattr(factura, 'numero', '')}")
    doc.build(story, canvasmaker=_NumberedCanvas)
    buffer.seek(0)
    return buffer.read()
