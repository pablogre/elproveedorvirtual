# ============================================================
# opc_compra.py
# Generador de PDF de Orden de Compra
# Fase 3 — Módulo 5 (SCHIRO)
# ============================================================
# Uso:
#   from opc_compra import generar_pdf_orden_compra
#   buffer = generar_pdf_orden_compra(datos_dict)
#
# El PDF se arma A4 con ReportLab. Lee los datos de la empresa
# desde config_cliente.py (RAZON_SOCIAL, CUIT, DIRECCION, TELEFONO,
# EMAIL, LOGO_PATH).
# ============================================================

from io import BytesIO
from datetime import datetime
from decimal import Decimal

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

import os
import config_cliente as CFG


# ══════════════════════════════════════════════════════════════
# UTILIDADES
# ══════════════════════════════════════════════════════════════

def _cfg(nombre, default=''):
    """Lectura defensiva de config_cliente."""
    return getattr(CFG, nombre, default) or default


def _fmt_money(v):
    v = float(v or 0)
    return '$ ' + f'{v:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')


def _fmt_cantidad(v):
    v = float(v or 0)
    # Cantidad con hasta 3 decimales, sin ceros innecesarios
    s = f'{v:.3f}'.rstrip('0').rstrip('.')
    return s if s else '0'


# ══════════════════════════════════════════════════════════════
# ESTILOS
# ══════════════════════════════════════════════════════════════

def _build_styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='EmpresaNombre',
        fontName='Helvetica-Bold', fontSize=14, textColor=colors.HexColor('#0A2140'),
        leading=16))
    styles.add(ParagraphStyle(name='EmpresaDatos',
        fontName='Helvetica', fontSize=8, textColor=colors.HexColor('#444444'),
        leading=11))
    styles.add(ParagraphStyle(name='TituloOP',
        fontName='Helvetica-Bold', fontSize=22, textColor=colors.HexColor('#0A2140'),
        alignment=TA_CENTER, leading=26))
    styles.add(ParagraphStyle(name='NumeroOP',
        fontName='Helvetica-Bold', fontSize=12, textColor=colors.HexColor('#2D5AB2'),
        alignment=TA_CENTER, leading=14))
    styles.add(ParagraphStyle(name='SubTitulo',
        fontName='Helvetica-Bold', fontSize=10, textColor=colors.HexColor('#0A2140'),
        leading=12))
    styles.add(ParagraphStyle(name='Texto',
        fontName='Helvetica', fontSize=9, textColor=colors.black, leading=11))
    styles.add(ParagraphStyle(name='TextoChico',
        fontName='Helvetica', fontSize=8, textColor=colors.HexColor('#444444'),
        leading=10))
    styles.add(ParagraphStyle(name='EstadoBadge',
        fontName='Helvetica-Bold', fontSize=11, textColor=colors.white,
        alignment=TA_CENTER, leading=14))
    return styles


# ══════════════════════════════════════════════════════════════
# CABECERA (logo + datos empresa + título)
# ══════════════════════════════════════════════════════════════

def _build_header(styles, datos):
    logo_path = _cfg('LOGO_PATH', '')
    logo_cell = ''
    if logo_path and os.path.isfile(logo_path):
        try:
            img = Image(logo_path, width=32*mm, height=28*mm, kind='proportional')
            logo_cell = img
        except Exception:
            logo_cell = ''

    razon    = _cfg('RAZON_SOCIAL', 'Empresa')
    cuit     = _cfg('CUIT', '')
    direcc   = _cfg('DIRECCION', '')
    telef    = _cfg('TELEFONO', '')
    email    = _cfg('EMAIL', '')

    datos_emp = f'<b>{razon}</b>'
    if cuit:   datos_emp += f'<br/>CUIT: {cuit}'
    if direcc: datos_emp += f'<br/>{direcc}'
    if telef:  datos_emp += f'<br/>Tel: {telef}'
    if email:  datos_emp += f'<br/>{email}'

    celda_emp = Paragraph(datos_emp, styles['EmpresaDatos'])

    # Badge con estado
    estado_labels = {
        'borrador':'BORRADOR','enviada':'ENVIADA','confirmada':'CONFIRMADA',
        'parcial':'PARCIAL','recibida':'RECIBIDA','facturada':'FACTURADA',
        'cerrada':'CERRADA','cancelada':'CANCELADA'
    }
    estado_colors = {
        'borrador':'#6C757D','enviada':'#0D6EFD','confirmada':'#198754',
        'parcial':'#FFC107','recibida':'#0DCAF0','facturada':'#20C997',
        'cerrada':'#343A40','cancelada':'#DC3545'
    }
    estado_txt = estado_labels.get(datos['estado'], datos['estado'].upper())
    estado_color = estado_colors.get(datos['estado'], '#6C757D')

    titulo = f'<para align="right"><font color="{estado_color}"><b>ORDEN DE COMPRA</b></font></para>'
    numero = f'<para align="right"><b>Nº {datos["numero_completo"]}</b></para>'
    estado = f'<para align="right"><font color="{estado_color}">Estado: <b>{estado_txt}</b></font></para>'

    celda_titulo = [
        Paragraph(titulo, styles['TituloOP']),
        Spacer(1, 2*mm),
        Paragraph(numero, styles['NumeroOP']),
        Spacer(1, 1*mm),
        Paragraph(estado, styles['TextoChico']),
    ]

    tabla_header = Table(
        [[logo_cell, celda_emp, celda_titulo]],
        colWidths=[35*mm, 70*mm, 75*mm]
    )
    tabla_header.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING',   (0,0), (-1,-1), 0),
        ('RIGHTPADDING',  (0,0), (-1,-1), 0),
        ('TOPPADDING',    (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
    ]))
    return tabla_header


# ══════════════════════════════════════════════════════════════
# FECHAS Y DATOS DE LA OC
# ══════════════════════════════════════════════════════════════

def _build_fechas(styles, datos):
    fila1 = [
        Paragraph(f"<b>Fecha emisión:</b> {datos.get('fecha_emision','')}", styles['Texto']),
        Paragraph(f"<b>Entrega estimada:</b> {datos.get('fecha_entrega_estimada','') or '—'}", styles['Texto']),
    ]
    tabla = Table([fila1], colWidths=[90*mm, 90*mm])
    tabla.setStyle(TableStyle([
        ('BACKGROUND',     (0,0), (-1,-1), colors.HexColor('#F4F6FA')),
        ('BOX',            (0,0), (-1,-1), 0.5, colors.HexColor('#CCCCCC')),
        ('LEFTPADDING',    (0,0), (-1,-1), 6),
        ('RIGHTPADDING',   (0,0), (-1,-1), 6),
        ('TOPPADDING',     (0,0), (-1,-1), 4),
        ('BOTTOMPADDING',  (0,0), (-1,-1), 4),
    ]))
    return tabla


# ══════════════════════════════════════════════════════════════
# DATOS DEL PROVEEDOR
# ══════════════════════════════════════════════════════════════

def _build_proveedor(styles, datos):
    nombre    = datos.get('proveedor_razon_social', '') or '—'
    cuit      = datos.get('proveedor_cuit', '')
    direccion = datos.get('proveedor_direccion', '')
    telefono  = datos.get('proveedor_telefono', '')
    email     = datos.get('proveedor_email', '')

    texto = f'<b>{nombre}</b>'
    if cuit:      texto += f'<br/>CUIT: {cuit}'
    if direccion: texto += f'<br/>{direccion}'
    extra = []
    if telefono: extra.append(f'Tel: {telefono}')
    if email:    extra.append(email)
    if extra:    texto += '<br/>' + ' · '.join(extra)

    p_titulo = Paragraph('<b>PROVEEDOR</b>', styles['SubTitulo'])
    p_datos  = Paragraph(texto, styles['Texto'])

    tabla = Table([[p_titulo], [p_datos]], colWidths=[180*mm])
    tabla.setStyle(TableStyle([
        ('BACKGROUND',     (0,0), (0,0), colors.HexColor('#0A2140')),
        ('TEXTCOLOR',      (0,0), (0,0), colors.white),
        ('LEFTPADDING',    (0,0), (-1,-1), 8),
        ('RIGHTPADDING',   (0,0), (-1,-1), 8),
        ('TOPPADDING',     (0,0), (-1,-1), 5),
        ('BOTTOMPADDING',  (0,0), (-1,-1), 5),
        ('BOX',            (0,0), (-1,-1), 0.5, colors.HexColor('#0A2140')),
        ('LINEBELOW',      (0,0), (0,0), 0.5, colors.HexColor('#0A2140')),
    ]))
    return tabla


# ══════════════════════════════════════════════════════════════
# TABLA DE ITEMS
# ══════════════════════════════════════════════════════════════

def _build_items(styles, datos):
    # Headers
    headers = [
        Paragraph('<b>Código</b>',   styles['Texto']),
        Paragraph('<b>Descripción</b>', styles['Texto']),
        Paragraph('<b>Cant.</b>',    styles['Texto']),
        Paragraph('<b>Precio U.</b>', styles['Texto']),
        Paragraph('<b>Subtotal</b>', styles['Texto']),
    ]
    filas = [headers]

    for d in datos.get('detalles', []):
        filas.append([
            Paragraph(d.get('codigo') or '', styles['TextoChico']),
            Paragraph(d.get('nombre') or '', styles['TextoChico']),
            Paragraph(_fmt_cantidad(d.get('cantidad')), styles['TextoChico']),
            Paragraph(_fmt_money(d.get('precio_unitario')), styles['TextoChico']),
            Paragraph(_fmt_money(d.get('subtotal')), styles['TextoChico']),
        ])

    tabla = Table(filas, colWidths=[22*mm, 84*mm, 18*mm, 28*mm, 28*mm], repeatRows=1)
    tabla.setStyle(TableStyle([
        # Header
        ('BACKGROUND',   (0,0), (-1,0), colors.HexColor('#2D5AB2')),
        ('TEXTCOLOR',    (0,0), (-1,0), colors.white),
        ('ALIGN',        (0,0), (-1,0), 'CENTER'),
        # Cuerpo
        ('ALIGN',        (2,1), (2,-1), 'RIGHT'),
        ('ALIGN',        (3,1), (4,-1), 'RIGHT'),
        ('VALIGN',       (0,0), (-1,-1), 'TOP'),
        ('GRID',         (0,0), (-1,-1), 0.25, colors.HexColor('#DDDDDD')),
        ('LEFTPADDING',  (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
        ('TOPPADDING',   (0,0), (-1,-1), 3),
        ('BOTTOMPADDING',(0,0), (-1,-1), 3),
        # Zebra
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F8F9FA')]),
    ]))
    return tabla


# ══════════════════════════════════════════════════════════════
# TOTALES
# ══════════════════════════════════════════════════════════════

def _build_totales(styles, datos):
    filas = [
        ['Subtotal:',  _fmt_money(datos.get('subtotal'))],
        ['IVA:',       _fmt_money(datos.get('iva'))],
        ['TOTAL:',     _fmt_money(datos.get('total'))],
    ]
    tabla = Table(filas, colWidths=[40*mm, 50*mm], hAlign='RIGHT')
    tabla.setStyle(TableStyle([
        ('ALIGN',         (0,0), (0,-1), 'RIGHT'),
        ('ALIGN',         (1,0), (1,-1), 'RIGHT'),
        ('FONTNAME',      (0,0), (-1,-2), 'Helvetica'),
        ('FONTNAME',      (0,-1), (-1,-1), 'Helvetica-Bold'),
        ('FONTSIZE',      (0,0), (-1,-2), 9),
        ('FONTSIZE',      (0,-1), (-1,-1), 12),
        ('TEXTCOLOR',     (0,-1), (-1,-1), colors.white),
        ('BACKGROUND',    (0,-1), (-1,-1), colors.HexColor('#0A2140')),
        ('LEFTPADDING',   (0,0), (-1,-1), 8),
        ('RIGHTPADDING',  (0,0), (-1,-1), 8),
        ('TOPPADDING',    (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LINEABOVE',     (0,-1), (-1,-1), 1.5, colors.HexColor('#0A2140')),
    ]))
    return tabla


# ══════════════════════════════════════════════════════════════
# OBSERVACIONES Y CONDICIONES
# ══════════════════════════════════════════════════════════════

def _build_observaciones(styles, datos):
    bloques = []
    cond = datos.get('condiciones_pago', '').strip()
    obs  = datos.get('observaciones', '').strip()
    motivo = datos.get('motivo_cancelacion', '').strip()

    if cond:
        bloques.append(Paragraph(f'<b>Condiciones de pago:</b> {cond}', styles['Texto']))
        bloques.append(Spacer(1, 2*mm))
    if obs:
        bloques.append(Paragraph(f'<b>Observaciones:</b> {obs}', styles['Texto']))
        bloques.append(Spacer(1, 2*mm))
    if motivo and datos.get('estado') == 'cancelada':
        bloques.append(Spacer(1, 2*mm))
        bloques.append(Paragraph(
            f'<font color="#DC3545"><b>CANCELADA — Motivo:</b> {motivo}</font>',
            styles['Texto']))

    if not bloques:
        return None

    # Marco
    tabla = Table([[b] for b in bloques if b], colWidths=[180*mm])
    tabla.setStyle(TableStyle([
        ('BACKGROUND',     (0,0), (-1,-1), colors.HexColor('#FFFBEA')),
        ('BOX',            (0,0), (-1,-1), 0.5, colors.HexColor('#E7C95A')),
        ('LEFTPADDING',    (0,0), (-1,-1), 8),
        ('RIGHTPADDING',   (0,0), (-1,-1), 8),
        ('TOPPADDING',     (0,0), (-1,-1), 5),
        ('BOTTOMPADDING',  (0,0), (-1,-1), 5),
    ]))
    return tabla


# ══════════════════════════════════════════════════════════════
# FIRMAS
# ══════════════════════════════════════════════════════════════

def _build_firmas(styles):
    p = ParagraphStyle(
        name='Firma',
        parent=styles['Texto'],
        alignment=TA_CENTER,
        fontSize=9
    )
    filas = [
        ['', '', ''],
        [
            Paragraph('_____________________<br/>Emisor', p),
            '',
            Paragraph('_____________________<br/>Recepción proveedor', p),
        ],
    ]
    tabla = Table(filas, colWidths=[70*mm, 40*mm, 70*mm])
    tabla.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN',(0,0), (-1,-1), 'BOTTOM'),
        ('TOPPADDING', (0,0), (-1,0), 10*mm),
    ]))
    return tabla


# ══════════════════════════════════════════════════════════════
# MAIN — generar_pdf_orden_compra(datos)
# ══════════════════════════════════════════════════════════════

def generar_pdf_orden_compra(datos):
    """
    datos = {
        'numero_completo', 'fecha_emision', 'fecha_entrega_estimada',
        'estado',
        'proveedor_razon_social', 'proveedor_cuit',
        'proveedor_direccion', 'proveedor_telefono', 'proveedor_email',
        'detalles': [{codigo, nombre, cantidad, precio_unitario, subtotal, observaciones}],
        'subtotal', 'iva', 'total',
        'condiciones_pago', 'observaciones',
        'motivo_cancelacion'
    }
    Retorna BytesIO con el PDF.
    """
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=15*mm, rightMargin=15*mm,
        topMargin=12*mm, bottomMargin=15*mm,
        title=f"OC {datos.get('numero_completo','')}",
        author=_cfg('RAZON_SOCIAL', 'SCHIRO'),
    )

    styles = _build_styles()
    story = []

    story.append(_build_header(styles, datos))
    story.append(Spacer(1, 5*mm))

    story.append(_build_fechas(styles, datos))
    story.append(Spacer(1, 4*mm))

    story.append(_build_proveedor(styles, datos))
    story.append(Spacer(1, 5*mm))

    story.append(_build_items(styles, datos))
    story.append(Spacer(1, 4*mm))

    story.append(_build_totales(styles, datos))
    story.append(Spacer(1, 5*mm))

    obs = _build_observaciones(styles, datos)
    if obs:
        story.append(obs)
        story.append(Spacer(1, 8*mm))
    else:
        story.append(Spacer(1, 5*mm))

    story.append(_build_firmas(styles))

    doc.build(story)
    return buf