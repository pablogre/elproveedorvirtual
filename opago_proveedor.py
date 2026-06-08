# ============================================================
# opago_proveedor.py
# Generador de PDF de Orden de Pago a Proveedor
# Fase 3d — Ciclo de Compras (SCHIRO / LK-D Mayorista)
# ============================================================
# Uso:
#   from opago_proveedor import generar_pdf_orden_pago
#   pdf_bytes = generar_pdf_orden_pago(pago_id)
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
    """Lectura defensiva de config_cliente (devuelve default si no existe)."""
    return getattr(CFG, nombre, default) or default


def _fmt_money(v):
    v = float(v or 0)
    return '$ ' + f'{v:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')


def _numero_a_letras(monto):
    """
    Convierte un monto a letras en español (pesos argentinos).
    Implementación básica — maneja hasta miles de millones.
    """
    monto = Decimal(str(monto)).quantize(Decimal('0.01'))
    entero = int(monto)
    cent = int((monto - entero) * 100)

    unidades = ['', 'UNO', 'DOS', 'TRES', 'CUATRO', 'CINCO', 'SEIS', 'SIETE', 'OCHO', 'NUEVE',
                'DIEZ', 'ONCE', 'DOCE', 'TRECE', 'CATORCE', 'QUINCE', 'DIECISEIS',
                'DIECISIETE', 'DIECIOCHO', 'DIECINUEVE', 'VEINTE']
    decenas = ['', '', 'VEINTI', 'TREINTA', 'CUARENTA', 'CINCUENTA',
               'SESENTA', 'SETENTA', 'OCHENTA', 'NOVENTA']
    centenas = ['', 'CIENTO', 'DOSCIENTOS', 'TRESCIENTOS', 'CUATROCIENTOS',
                'QUINIENTOS', 'SEISCIENTOS', 'SETECIENTOS', 'OCHOCIENTOS', 'NOVECIENTOS']

    def _menor_mil(n):
        if n == 0: return ''
        if n == 100: return 'CIEN'
        s = ''
        c = n // 100
        r = n % 100
        if c:
            s += centenas[c]
        if r:
            if s: s += ' '
            if r <= 20:
                s += unidades[r]
            else:
                d = r // 10
                u = r % 10
                if d == 2 and u:
                    s += 'VEINTI' + unidades[u].lower()
                else:
                    s += decenas[d]
                    if u:
                        s += ' Y ' + unidades[u]
        return s.upper()

    if entero == 0:
        parte_entera = 'CERO'
    else:
        partes = []
        millones = entero // 1_000_000
        miles    = (entero % 1_000_000) // 1000
        resto    = entero % 1000

        if millones:
            if millones == 1:
                partes.append('UN MILLON')
            else:
                partes.append(_menor_mil(millones) + ' MILLONES')
        if miles:
            if miles == 1:
                partes.append('MIL')
            else:
                partes.append(_menor_mil(miles) + ' MIL')
        if resto:
            partes.append(_menor_mil(resto))
        parte_entera = ' '.join(partes)

    return f'PESOS {parte_entera} CON {cent:02d}/100'


# ══════════════════════════════════════════════════════════════
# FUNCIÓN PRINCIPAL
# ══════════════════════════════════════════════════════════════

def generar_pdf_orden_pago(pago):
    """
    Genera el PDF de la Orden de Pago a partir de un objeto PagoProveedor
    ya cargado con sus relaciones (detalles y medios). Devuelve bytes del PDF.

    pago: instancia de PagoProveedor con .detalles, .medios, .proveedor cargados
    """
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
        title=f'Orden de Pago {pago.numero_recibo_completo()}',
    )

    styles = getSampleStyleSheet()
    st_normal = ParagraphStyle('normal',  parent=styles['Normal'], fontSize=9,  leading=11)
    st_small  = ParagraphStyle('small',   parent=styles['Normal'], fontSize=8,  leading=10)
    st_title  = ParagraphStyle('title',   parent=styles['Normal'], fontSize=16, leading=20,
                                alignment=TA_CENTER, textColor=colors.HexColor('#1F3864'),
                                fontName='Helvetica-Bold')
    st_h2     = ParagraphStyle('h2',      parent=styles['Normal'], fontSize=11, leading=14,
                                fontName='Helvetica-Bold', textColor=colors.HexColor('#2E75B6'))
    st_bold   = ParagraphStyle('bold',    parent=st_normal, fontName='Helvetica-Bold')
    st_right  = ParagraphStyle('right',   parent=st_normal, alignment=TA_RIGHT)

    elements = []

    # ─── ENCABEZADO EMPRESA ───────────────────────────────────
    razon   = _cfg('RAZON_SOCIAL')
    cuit    = _cfg('CUIT')
    direc   = _cfg('DIRECCION')
    tel     = _cfg('TELEFONO')
    email   = _cfg('EMAIL')
    logopath = _cfg('LOGO_PATH')

    empresa_html = f'<b>{razon}</b><br/>CUIT: {cuit}'
    if direc: empresa_html += f'<br/>{direc}'
    if tel:   empresa_html += f'<br/>Tel: {tel}'
    if email: empresa_html += f'<br/>{email}'

    if logopath and os.path.isfile(logopath):
        try:
            img = Image(logopath, width=35*mm, height=25*mm)
            img.hAlign = 'LEFT'
            enc = Table(
                [[img, Paragraph(empresa_html, st_normal)]],
                colWidths=[40*mm, None]
            )
        except Exception:
            enc = Table([[Paragraph(empresa_html, st_normal)]])
    else:
        enc = Table([[Paragraph(empresa_html, st_normal)]])

    enc.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOX',    (0,0), (-1,-1), 0.5, colors.HexColor('#BFBFBF')),
        ('LEFTPADDING',  (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING',   (0,0), (-1,-1), 6),
        ('BOTTOMPADDING',(0,0), (-1,-1), 6),
    ]))
    elements.append(enc)
    elements.append(Spacer(1, 6))

    # ─── TÍTULO + NÚMERO + FECHA ──────────────────────────────
    nro = pago.numero_recibo_completo()
    fecha_str = pago.fecha.strftime('%d/%m/%Y') if pago.fecha else ''
    titulo_tab = Table([
        [Paragraph('ORDEN DE PAGO', st_title),
         Paragraph(f'<b>N°</b> {nro}<br/><b>Fecha:</b> {fecha_str}', st_normal)]
    ], colWidths=[None, 60*mm])
    titulo_tab.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN',  (1,0), (1,0), 'RIGHT'),
        ('BOX',    (1,0), (1,0), 0.5, colors.HexColor('#BFBFBF')),
        ('LEFTPADDING',  (1,0), (1,0), 8),
        ('RIGHTPADDING', (1,0), (1,0), 8),
        ('TOPPADDING',   (1,0), (1,0), 6),
        ('BOTTOMPADDING',(1,0), (1,0), 6),
    ]))
    elements.append(titulo_tab)
    elements.append(Spacer(1, 10))

    # ─── DATOS DEL PROVEEDOR ──────────────────────────────────
    prov = pago.proveedor
    prov_html = f'<b>Proveedor:</b> {prov.razon_social}<br/>'
    prov_html += f'<b>CUIT:</b> {prov.cuit or "-"}'
    if prov.direccion:
        prov_html += f'<br/><b>Dirección:</b> {prov.direccion}'
    prov_tab = Table([[Paragraph(prov_html, st_normal)]])
    prov_tab.setStyle(TableStyle([
        ('BOX',    (0,0), (-1,-1), 0.5, colors.HexColor('#BFBFBF')),
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F2F2F2')),
        ('LEFTPADDING',  (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING',   (0,0), (-1,-1), 6),
        ('BOTTOMPADDING',(0,0), (-1,-1), 6),
    ]))
    elements.append(prov_tab)
    elements.append(Spacer(1, 10))

    # ─── FACTURAS IMPUTADAS ───────────────────────────────────
    elements.append(Paragraph('Facturas imputadas', st_h2))
    elements.append(Spacer(1, 4))

    fact_data = [['Comprobante', 'Fecha', 'Total', 'Saldo anterior', 'Monto imputado']]
    for det in pago.detalles:
        f = det.factura
        if not f:
            continue
        # saldo_anterior = saldo actual + monto imputado (porque ya se descontó al crear el pago)
        saldo_anterior = float(f.saldo_pendiente or 0) + float(det.monto_imputado)
        fact_data.append([
            f.numero_completo(),
            f.fecha.strftime('%d/%m/%Y') if f.fecha else '',
            _fmt_money(f.total),
            _fmt_money(saldo_anterior),
            _fmt_money(det.monto_imputado),
        ])
    total_imp = sum(float(d.monto_imputado) for d in pago.detalles)
    fact_data.append(['', '', '', 'TOTAL IMPUTADO', _fmt_money(total_imp)])

    fact_tab = Table(fact_data, colWidths=[45*mm, 22*mm, 33*mm, 35*mm, 35*mm])
    fact_tab.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1F3864')),
        ('TEXTCOLOR',  (0,0), (-1,0), colors.white),
        ('FONTNAME',   (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE',   (0,0), (-1,-1), 9),
        ('ALIGN',      (2,0), (-1,-1), 'RIGHT'),
        ('BOX',        (0,0), (-1,-1), 0.5, colors.grey),
        ('INNERGRID',  (0,0), (-1,-1), 0.25, colors.lightgrey),
        ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor('#E2EFDA')),
        ('FONTNAME',   (0,-1), (-1,-1), 'Helvetica-Bold'),
        ('LEFTPADDING',  (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
        ('TOPPADDING',   (0,0), (-1,-1), 4),
        ('BOTTOMPADDING',(0,0), (-1,-1), 4),
    ]))
    elements.append(fact_tab)
    elements.append(Spacer(1, 12))

    # ─── MEDIOS DE PAGO ───────────────────────────────────────
    elements.append(Paragraph('Medios de pago', st_h2))
    elements.append(Spacer(1, 4))

    med_data = [['Tipo', 'Detalle', 'Monto']]
    for m in pago.medios:
        if m.medio == 'efectivo':
            tipo = 'Efectivo'
            detalle = '-'
        elif m.medio == 'transferencia':
            tipo = 'Transferencia'
            detalle_parts = []
            if m.banco_destino: detalle_parts.append(f'Banco: {m.banco_destino}')
            if m.cbu_destino:   detalle_parts.append(f'CBU: {m.cbu_destino}')
            detalle = ' — '.join(detalle_parts) if detalle_parts else '-'
        elif m.medio == 'cheque_propio':
            tipo = 'Cheque propio'
            if m.cheque_propio:
                ch = m.cheque_propio
                vto = ch.fecha_vencimiento.strftime('%d/%m/%Y') if ch.fecha_vencimiento else 's/f'
                detalle = f'{ch.banco} — N° {ch.numero} — Vto. {vto}'
            else:
                detalle = '-'
        elif m.medio == 'cheque_tercero':
            tipo = 'Cheque de 3° (endoso)'
            if m.cheque_tercero:
                ch = m.cheque_tercero
                vto = ch.fecha_vencimiento.strftime('%d/%m/%Y') if ch.fecha_vencimiento else 's/f'
                lib = ch.librador or 's/librador'
                detalle = f'{ch.banco} — N° {ch.numero} — Lib.: {lib} — Vto. {vto}'
            else:
                detalle = '-'
        else:
            tipo = (m.medio or '').capitalize()
            detalle = '-'
        med_data.append([tipo, detalle, _fmt_money(m.monto)])

    total_med = sum(float(m.monto) for m in pago.medios)
    med_data.append(['', 'TOTAL MEDIOS', _fmt_money(total_med)])

    med_tab = Table(med_data, colWidths=[40*mm, 95*mm, 35*mm])
    med_tab.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1F3864')),
        ('TEXTCOLOR',  (0,0), (-1,0), colors.white),
        ('FONTNAME',   (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE',   (0,0), (-1,-1), 9),
        ('ALIGN',      (2,0), (-1,-1), 'RIGHT'),
        ('ALIGN',      (1,-1), (1,-1), 'RIGHT'),
        ('BOX',        (0,0), (-1,-1), 0.5, colors.grey),
        ('INNERGRID',  (0,0), (-1,-1), 0.25, colors.lightgrey),
        ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor('#E2EFDA')),
        ('FONTNAME',   (0,-1), (-1,-1), 'Helvetica-Bold'),
        ('LEFTPADDING',  (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
        ('TOPPADDING',   (0,0), (-1,-1), 4),
        ('BOTTOMPADDING',(0,0), (-1,-1), 4),
    ]))
    elements.append(med_tab)
    elements.append(Spacer(1, 10))

    # ─── TOTAL EN LETRAS ──────────────────────────────────────
    total_pago = float(pago.importe)
    letras = _numero_a_letras(total_pago)
    total_tab = Table([
        [Paragraph(f'<b>TOTAL PAGADO:</b> {_fmt_money(total_pago)}', st_h2)],
        [Paragraph(f'<i>Son: {letras}</i>', st_small)]
    ], colWidths=[None])
    total_tab.setStyle(TableStyle([
        ('BOX',    (0,0), (-1,-1), 0.5, colors.HexColor('#1F3864')),
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#FFF2CC')),
        ('LEFTPADDING',  (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING',   (0,0), (-1,-1), 6),
        ('BOTTOMPADDING',(0,0), (-1,-1), 6),
    ]))
    elements.append(total_tab)
    elements.append(Spacer(1, 12))

    # ─── OBSERVACIONES ────────────────────────────────────────
    if pago.observaciones:
        elements.append(Paragraph('<b>Observaciones:</b>', st_normal))
        elements.append(Paragraph(pago.observaciones, st_normal))
        elements.append(Spacer(1, 14))

    # ─── FIRMAS ───────────────────────────────────────────────
    elements.append(Spacer(1, 25))
    firmas_tab = Table([
        ['_' * 35,                           '_' * 35],
        ['Recibí conforme (Proveedor)',      'Emitió (Empresa)'],
    ], colWidths=[85*mm, 85*mm])
    firmas_tab.setStyle(TableStyle([
        ('ALIGN',    (0,0), (-1,-1), 'CENTER'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('TOPPADDING', (0,1), (-1,1), 4),
    ]))
    elements.append(firmas_tab)

    # ─── BUILD ────────────────────────────────────────────────
    doc.build(elements)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes