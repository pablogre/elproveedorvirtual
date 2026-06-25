# -*- coding: utf-8 -*-
"""
reporte_facturas_pdf.py
Genera el PDF del LISTADO de facturas filtrado (reporte por vendedor / fecha).
Convención igual a reporte_ctacte_pdf / reporte_ventas_pdf:
    generar_pdf_listado_facturas(facturas, resumen, parametros) -> bytes
"""

from io import BytesIO
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
)


# Colores corporativos (mismos tonos que usa el front: success / warning / danger / morado interno)
_AZUL    = colors.HexColor('#0d6efd')
_GRIS_OS = colors.HexColor('#343a40')
_GRIS_CL = colors.HexColor('#f1f3f5')
_VERDE   = colors.HexColor('#198754')
_AMBAR   = colors.HexColor('#996b00')
_ROJO    = colors.HexColor('#dc3545')
_MORADO  = colors.HexColor('#6f42c1')
_GRIS    = colors.HexColor('#6c757d')


def _fmt_money(n):
    try:
        n = float(n or 0)
    except (TypeError, ValueError):
        n = 0.0
    s = f'{n:,.2f}'
    # es-AR: separador de miles '.' y decimales ','
    s = s.replace(',', 'X').replace('.', ',').replace('X', '.')
    return f'${s}'


def _color_estado(estado):
    return {
        'autorizada': _VERDE,
        'error_afip': _AMBAR,
        'anulada':    _ROJO,
        'interno':    _MORADO,
        'pendiente':  _GRIS,
    }.get((estado or '').lower(), _GRIS_OS)


def _label_estado(estado):
    return {
        'autorizada': 'Autorizada',
        'error_afip': 'Error AFIP',
        'anulada':    'Anulada',
        'interno':    'Interno',
        'pendiente':  'Pendiente',
    }.get((estado or '').lower(), (estado or '').title())


def generar_pdf_listado_facturas(facturas, resumen, parametros):
    """
    facturas: list[dict] con claves:
        numero, fecha, cliente_nombre, cliente_doc, vendedor,
        tipo_nombre, total, estado, cae
    resumen:  dict con totales por estado: {'autorizadas': {'cantidad','total'}, ...}
              y 'total_general' (float), 'cantidad_total' (int)
    parametros: dict para el encabezado: {'vendedor','cliente','numero','estado',
              'fecha_desde','fecha_hasta','emisor'}
    """
    parametros = parametros or {}
    resumen = resumen or {}
    facturas = facturas or []

    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=landscape(A4),
        leftMargin=12 * mm, rightMargin=12 * mm,
        topMargin=12 * mm, bottomMargin=14 * mm,
        title='Listado de Facturas',
    )

    styles = getSampleStyleSheet()
    st_titulo = ParagraphStyle('titulo', parent=styles['Heading1'],
                               fontSize=16, textColor=_GRIS_OS, spaceAfter=2,
                               alignment=TA_LEFT)
    st_sub = ParagraphStyle('sub', parent=styles['Normal'],
                            fontSize=9, textColor=_GRIS, spaceAfter=1)
    st_cell = ParagraphStyle('cell', parent=styles['Normal'], fontSize=8,
                             leading=10)
    st_cell_r = ParagraphStyle('cellr', parent=st_cell, alignment=TA_RIGHT)
    st_th = ParagraphStyle('th', parent=styles['Normal'], fontSize=8.5,
                           textColor=colors.white, leading=10)

    elementos = []

    # ── Encabezado ───────────────────────────────────────────────
    emisor = parametros.get('emisor') or 'Reporte de Facturas'
    elementos.append(Paragraph(f'<b>{emisor}</b>', st_titulo))
    elementos.append(Paragraph('Listado de Facturas', st_sub))

    # Línea de filtros aplicados
    filtros_txt = []
    if parametros.get('vendedor'):
        filtros_txt.append(f"Vendedor: <b>{parametros['vendedor']}</b>")
    if parametros.get('cliente'):
        filtros_txt.append(f"Cliente: {parametros['cliente']}")
    if parametros.get('numero'):
        filtros_txt.append(f"N°: {parametros['numero']}")
    if parametros.get('estado'):
        filtros_txt.append(f"Estado: {_label_estado(parametros['estado'])}")
    rango = []
    if parametros.get('fecha_desde'):
        rango.append(f"desde {parametros['fecha_desde']}")
    if parametros.get('fecha_hasta'):
        rango.append(f"hasta {parametros['fecha_hasta']}")
    if rango:
        filtros_txt.append('Período: ' + ' '.join(rango))
    if not filtros_txt:
        filtros_txt.append('Sin filtros (todas las facturas)')

    elementos.append(Paragraph(' &nbsp;|&nbsp; '.join(filtros_txt), st_sub))
    elementos.append(Paragraph(
        'Emitido: ' + datetime.now().strftime('%d/%m/%Y %H:%M') +
        f' &nbsp;|&nbsp; {len(facturas)} comprobante(s)', st_sub))
    elementos.append(Spacer(1, 6))

    # ── Tabla ────────────────────────────────────────────────────
    encabezados = ['#', 'Número', 'Fecha', 'Cliente', 'Vendedor',
                   'Tipo', 'Estado', 'CAE', 'Total']
    data = [[Paragraph(f'<b>{h}</b>', st_th) for h in encabezados]]

    for i, f in enumerate(facturas, start=1):
        data.append([
            Paragraph(str(i), st_cell),
            Paragraph(str(f.get('numero') or ''), st_cell),
            Paragraph(str(f.get('fecha') or ''), st_cell),
            Paragraph(str(f.get('cliente_nombre') or ''), st_cell),
            Paragraph(str(f.get('vendedor') or '—'), st_cell),
            Paragraph(str(f.get('tipo_nombre') or ''), st_cell),
            Paragraph(_label_estado(f.get('estado')), st_cell),
            Paragraph(str(f.get('cae') or '—'), st_cell),
            Paragraph(_fmt_money(f.get('total')), st_cell_r),
        ])

    # Anchos (A4 landscape útil ≈ 273mm)
    col_widths = [10*mm, 30*mm, 30*mm, 58*mm, 38*mm, 24*mm, 22*mm, 33*mm, 28*mm]
    tabla = Table(data, colWidths=col_widths, repeatRows=1)

    estilo = [
        ('BACKGROUND', (0, 0), (-1, 0), _GRIS_OS),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (-1, 0), (-1, -1), 'RIGHT'),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('LINEBELOW', (0, 0), (-1, 0), 0.6, _GRIS_OS),
        ('GRID', (0, 1), (-1, -1), 0.25, colors.HexColor('#dee2e6')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, _GRIS_CL]),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]
    # Color del texto de la columna estado por fila
    for idx, f in enumerate(facturas, start=1):
        estilo.append(('TEXTCOLOR', (6, idx), (6, idx), _color_estado(f.get('estado'))))
    tabla.setStyle(TableStyle(estilo))
    elementos.append(tabla)
    elementos.append(Spacer(1, 10))

    # ── Resumen por estado ───────────────────────────────────────
    def _blk(key, label, color):
        b = (resumen.get(key) or {})
        cant = int(b.get('cantidad') or 0)
        tot = float(b.get('total') or 0)
        return [
            Paragraph(f'<b>{label}</b>', ParagraphStyle('rl', parent=st_cell, textColor=color)),
            Paragraph(str(cant), st_cell_r),
            Paragraph(_fmt_money(tot), st_cell_r),
        ]

    res_data = [[
        Paragraph('<b>Resumen por estado</b>', st_cell),
        Paragraph('<b>Cant.</b>', st_cell_r),
        Paragraph('<b>Monto</b>', st_cell_r),
    ]]
    res_data.append(_blk('autorizadas', 'Autorizadas', _VERDE))
    res_data.append(_blk('con_error',   'Error AFIP',  _AMBAR))
    res_data.append(_blk('pendientes',  'Pendientes',  _GRIS))
    res_data.append(_blk('anuladas',    'Anuladas',    _ROJO))
    res_data.append(_blk('internos',    'Internos',    _MORADO))

    cant_total = int(resumen.get('cantidad_total') or len(facturas))
    total_general = float(resumen.get('total_general') or 0)
    res_data.append([
        Paragraph('<b>TOTAL</b>', st_cell),
        Paragraph(f'<b>{cant_total}</b>', st_cell_r),
        Paragraph(f'<b>{_fmt_money(total_general)}</b>', st_cell_r),
    ])

    tabla_res = Table(res_data, colWidths=[55*mm, 30*mm, 40*mm], hAlign='RIGHT')
    tabla_res.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), _GRIS_OS),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.25, colors.HexColor('#dee2e6')),
        ('BACKGROUND', (0, -1), (-1, -1), _AZUL),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.white),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    elementos.append(tabla_res)

    # ── Footer con número de página ──────────────────────────────
    def _footer(canvas, doc_):
        canvas.saveState()
        canvas.setFont('Helvetica', 7)
        canvas.setFillColor(_GRIS)
        canvas.drawRightString(
            landscape(A4)[0] - 12 * mm, 8 * mm,
            f'Página {doc_.page}'
        )
        canvas.drawString(12 * mm, 8 * mm, 'FactuFácil · Listado de Facturas')
        canvas.restoreState()

    doc.build(elementos, onFirstPage=_footer, onLaterPages=_footer)
    pdf_bytes = buf.getvalue()
    buf.close()
    return pdf_bytes
