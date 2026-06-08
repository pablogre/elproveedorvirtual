# -*- coding: utf-8 -*-
"""
Blueprint: Armar Reparto del Día
--------------------------------
Pantalla para organizar el reparto diario del camión.
Agrupa remitos pendientes + pedidos `listo` (no retiro) por zona.
Genera PDF A4 con la hoja de ruta.

Entrega 2 del módulo de distribución.
"""

from flask import Blueprint, render_template, request, jsonify, session, make_response
from extensions import db
from sqlalchemy import text
from datetime import date, datetime
from io import BytesIO

reparto_bp = Blueprint('reparto', __name__, url_prefix='/reparto')


def _es_admin():
    return session.get('rol') == 'admin'


# =====================================================================
# PANTALLA PRINCIPAL
# =====================================================================

@reparto_bp.route('/')
def pantalla():
    if 'user_id' not in session:
        from flask import redirect, url_for
        return redirect(url_for('login'))
    return render_template('reparto.html', es_admin=_es_admin())


# =====================================================================
# API: ARMAR REPARTO (remitos pendientes + pedidos listo no retiro)
# =====================================================================

@reparto_bp.route('/api/armar')
def api_armar():
    """
    Devuelve remitos pendientes + pedidos listo (no retiro) agrupados por zona.
    Solo los que NO están marcados con en_reparto_fecha (o la fecha es distinta a hoy).
    Respeta el orden manual guardado en `orden_reparto_manual` de cada fila.
    """
    fecha_str = request.args.get('fecha') or date.today().isoformat()

    # Remitos pendientes SIN en_reparto_fecha (o asignados a otro día pero revertidos)
    remitos = db.session.execute(text("""
        SELECT r.id, r.tipo_comprobante, r.punto_venta, r.numero,
               r.total_al_emitir, r.fecha,
               r.zona_id, r.en_reparto_fecha,
               COALESCE(r.orden_reparto_manual, 9999) AS orden_manual,
               c.id AS cliente_id, c.nombre AS cliente_nombre,
               c.direccion, c.telefono,
               z.nombre AS zona_nombre, z.color AS zona_color,
               z.orden_reparto AS zona_orden
          FROM remito r
          JOIN cliente c ON c.id = r.cliente_id
     LEFT JOIN zona z ON z.id = r.zona_id
         WHERE r.estado = 'pendiente'
           AND (r.en_reparto_fecha IS NULL OR r.en_reparto_fecha != :fecha)
         ORDER BY COALESCE(z.orden_reparto, 99999), z.nombre, orden_manual, c.nombre
    """), {'fecha': fecha_str}).mappings().all()

    # Pedidos listo (no retiro) SIN en_reparto_fecha
    pedidos = db.session.execute(text("""
        SELECT p.id, p.fecha, p.total, p.notas, p.tipo_entrega,
               p.zona_id, p.en_reparto_fecha,
               COALESCE(p.orden_reparto_manual, 9999) AS orden_manual,
               c.id AS cliente_id, c.nombre AS cliente_nombre,
               c.direccion, c.telefono,
               z.nombre AS zona_nombre, z.color AS zona_color,
               z.orden_reparto AS zona_orden
          FROM pedido p
          JOIN cliente c ON c.id = p.cliente_id
     LEFT JOIN zona z ON z.id = p.zona_id
         WHERE p.estado = 'listo'
           AND (p.tipo_entrega IS NULL OR p.tipo_entrega != 'retiro')
           AND (p.en_reparto_fecha IS NULL OR p.en_reparto_fecha != :fecha)
         ORDER BY COALESCE(z.orden_reparto, 99999), z.nombre, orden_manual, c.nombre
    """), {'fecha': fecha_str}).mappings().all()

    # Agrupar por zona
    grupos = {}  # {zona_id_or_0: {nombre, color, orden, items:[...]}}
    for r in remitos:
        zid = r['zona_id'] or 0
        if zid not in grupos:
            grupos[zid] = {
                'zona_id': r['zona_id'],
                'zona_nombre': r['zona_nombre'] or 'Sin zona',
                'zona_color': r['zona_color'] or '#6c757d',
                'zona_orden': r['zona_orden'] if r['zona_orden'] is not None else 99999,
                'items': []
            }
        grupos[zid]['items'].append({
            'tipo': 'remito',
            'id': r['id'],
            'numero': f"R {r['punto_venta']}-{r['numero']}",
            'cliente_id': r['cliente_id'],
            'cliente_nombre': r['cliente_nombre'],
            'direccion': r['direccion'] or '',
            'telefono': r['telefono'] or '',
            'total': float(r['total_al_emitir'] or 0),
            'orden_manual': r['orden_manual'],
            'fecha_creacion': r['fecha'].strftime('%d/%m/%Y') if r['fecha'] else ''
        })

    for p in pedidos:
        zid = p['zona_id'] or 0
        if zid not in grupos:
            grupos[zid] = {
                'zona_id': p['zona_id'],
                'zona_nombre': p['zona_nombre'] or 'Sin zona',
                'zona_color': p['zona_color'] or '#6c757d',
                'zona_orden': p['zona_orden'] if p['zona_orden'] is not None else 99999,
                'items': []
            }
        grupos[zid]['items'].append({
            'tipo': 'pedido',
            'id': p['id'],
            'numero': f"Pedido #{p['id']}",
            'cliente_id': p['cliente_id'],
            'cliente_nombre': p['cliente_nombre'],
            'direccion': p['direccion'] or '',
            'telefono': p['telefono'] or '',
            'total': float(p['total'] or 0),
            'orden_manual': p['orden_manual'],
            'fecha_creacion': p['fecha'].strftime('%d/%m/%Y') if p['fecha'] else '',
            'notas': p['notas'] or ''
        })

    # Ordenar por orden_manual + cliente dentro de cada zona
    for zid in grupos:
        grupos[zid]['items'].sort(key=lambda x: (x['orden_manual'], x['cliente_nombre']))

    # Devolver como lista ordenada por orden_reparto de zona
    lista = sorted(grupos.values(), key=lambda g: (g['zona_orden'], g['zona_nombre']))
    return jsonify({
        'fecha': fecha_str,
        'zonas': lista,
        'total_items': sum(len(g['items']) for g in lista),
        'total_monto': sum(it['total'] for g in lista for it in g['items'])
    })


# =====================================================================
# API: GUARDAR ORDEN MANUAL (drag-and-drop)
# =====================================================================

@reparto_bp.route('/api/ordenar', methods=['POST'])
def api_ordenar():
    """
    Guarda el orden manual de los items dentro de una zona.
    Payload: {items: [{tipo: 'remito'|'pedido', id: 123, orden: 0}, ...]}
    """
    data = request.get_json() or {}
    items = data.get('items') or []

    try:
        for it in items:
            tipo = it.get('tipo')
            iid = it.get('id')
            orden = int(it.get('orden') or 0)
            if tipo == 'remito':
                db.session.execute(
                    text("UPDATE remito SET orden_reparto_manual = :o WHERE id = :id"),
                    {'o': orden, 'id': iid}
                )
            elif tipo == 'pedido':
                db.session.execute(
                    text("UPDATE pedido SET orden_reparto_manual = :o WHERE id = :id"),
                    {'o': orden, 'id': iid}
                )
        db.session.commit()
        return jsonify({'ok': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# =====================================================================
# API: INICIAR REPARTO (marcar como en_reparto_fecha = hoy)
# =====================================================================

@reparto_bp.route('/api/iniciar', methods=['POST'])
def api_iniciar():
    """
    Marca los items seleccionados como "en reparto" en la fecha indicada.
    Payload: {fecha: '2026-04-17', items: [{tipo, id}, ...]}
    """
    data = request.get_json() or {}
    fecha_str = data.get('fecha') or date.today().isoformat()
    items = data.get('items') or []

    if not items:
        return jsonify({'error': 'No hay items seleccionados'}), 400

    try:
        remitos_ids = [it['id'] for it in items if it.get('tipo') == 'remito']
        pedidos_ids = [it['id'] for it in items if it.get('tipo') == 'pedido']

        if remitos_ids:
            db.session.execute(
                text("UPDATE remito SET en_reparto_fecha = :f WHERE id IN :ids"),
                {'f': fecha_str, 'ids': tuple(remitos_ids)}
            )
        if pedidos_ids:
            db.session.execute(
                text("UPDATE pedido SET en_reparto_fecha = :f WHERE id IN :ids"),
                {'f': fecha_str, 'ids': tuple(pedidos_ids)}
            )

        db.session.commit()
        return jsonify({
            'ok': True,
            'remitos_count': len(remitos_ids),
            'pedidos_count': len(pedidos_ids)
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# =====================================================================
# API: EN REPARTO HOY
# =====================================================================

@reparto_bp.route('/api/en_reparto_hoy')
def api_en_reparto_hoy():
    """
    Lista los remitos y pedidos que están EN REPARTO en una fecha determinada.
    """
    fecha_str = request.args.get('fecha') or date.today().isoformat()

    remitos = db.session.execute(text("""
        SELECT r.id, r.punto_venta, r.numero, r.total_al_emitir,
               c.nombre AS cliente_nombre, c.direccion, c.telefono,
               z.nombre AS zona_nombre, z.color AS zona_color
          FROM remito r
          JOIN cliente c ON c.id = r.cliente_id
     LEFT JOIN zona z ON z.id = r.zona_id
         WHERE r.en_reparto_fecha = :f
           AND r.estado = 'pendiente'
         ORDER BY z.orden_reparto, z.nombre, c.nombre
    """), {'f': fecha_str}).mappings().all()

    pedidos = db.session.execute(text("""
        SELECT p.id, p.total,
               c.nombre AS cliente_nombre, c.direccion, c.telefono,
               z.nombre AS zona_nombre, z.color AS zona_color
          FROM pedido p
          JOIN cliente c ON c.id = p.cliente_id
     LEFT JOIN zona z ON z.id = p.zona_id
         WHERE p.en_reparto_fecha = :f
           AND p.estado = 'listo'
         ORDER BY z.orden_reparto, z.nombre, c.nombre
    """), {'f': fecha_str}).mappings().all()

    items = []
    for r in remitos:
        items.append({
            'tipo': 'remito', 'id': r['id'],
            'numero': f"R {r['punto_venta']}-{r['numero']}",
            'cliente_nombre': r['cliente_nombre'],
            'direccion': r['direccion'] or '', 'telefono': r['telefono'] or '',
            'total': float(r['total_al_emitir'] or 0),
            'zona_nombre': r['zona_nombre'] or 'Sin zona',
            'zona_color': r['zona_color'] or '#6c757d'
        })
    for p in pedidos:
        items.append({
            'tipo': 'pedido', 'id': p['id'],
            'numero': f"Pedido #{p['id']}",
            'cliente_nombre': p['cliente_nombre'],
            'direccion': p['direccion'] or '', 'telefono': p['telefono'] or '',
            'total': float(p['total'] or 0),
            'zona_nombre': p['zona_nombre'] or 'Sin zona',
            'zona_color': p['zona_color'] or '#6c757d'
        })

    return jsonify({'fecha': fecha_str, 'items': items})


# =====================================================================
# API: DEVOLVER A PENDIENTE (saca del reparto)
# =====================================================================

@reparto_bp.route('/api/devolver_pendiente', methods=['POST'])
def api_devolver_pendiente():
    """
    Limpia en_reparto_fecha de un item puntual.
    Payload: {tipo: 'remito'|'pedido', id: 123}
    """
    data = request.get_json() or {}
    tipo = data.get('tipo')
    iid = data.get('id')

    if not tipo or not iid:
        return jsonify({'error': 'Faltan parámetros'}), 400

    try:
        if tipo == 'remito':
            db.session.execute(
                text("UPDATE remito SET en_reparto_fecha = NULL WHERE id = :id"),
                {'id': iid}
            )
        elif tipo == 'pedido':
            db.session.execute(
                text("UPDATE pedido SET en_reparto_fecha = NULL WHERE id = :id"),
                {'id': iid}
            )
        else:
            return jsonify({'error': 'Tipo inválido'}), 400

        db.session.commit()
        return jsonify({'ok': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# =====================================================================
# PDF: HOJA DE REPARTO (A4)
# =====================================================================

@reparto_bp.route('/pdf', methods=['POST'])
def pdf():
    """
    Genera un PDF A4 con la hoja de reparto.
    Payload: {
        fecha: '2026-04-17',
        chofer: 'Juan Pérez',           # opcional
        items: [{tipo, id}, ...]        # los seleccionados
    }
    El PDF se agrupa por zona con salto de página entre zonas.
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import mm
        from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle,
                                         Paragraph, Spacer, PageBreak)
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
    except ImportError:
        return jsonify({'error': 'reportlab no está instalado. Ejecutá: pip install reportlab'}), 500

    data = request.get_json() or {}
    fecha_str = data.get('fecha') or date.today().isoformat()
    chofer = (data.get('chofer') or '').strip() or '____________________'
    items_payload = data.get('items') or []

    if not items_payload:
        return jsonify({'error': 'No hay items para imprimir'}), 400

    # Traer info completa para los items seleccionados
    remitos_ids = [it['id'] for it in items_payload if it.get('tipo') == 'remito']
    pedidos_ids = [it['id'] for it in items_payload if it.get('tipo') == 'pedido']

    grupos = {}  # {zona_id: {nombre, color, items:[]}}

    if remitos_ids:
        remitos = db.session.execute(text("""
            SELECT r.id, r.tipo_comprobante, r.punto_venta, r.numero, r.total_al_emitir,
                   c.nombre AS cliente_nombre, c.direccion, c.telefono,
                   z.id AS zona_id, z.nombre AS zona_nombre, z.color AS zona_color,
                   z.orden_reparto AS zona_orden,
                   COALESCE(r.orden_reparto_manual, 9999) AS orden_manual
              FROM remito r
              JOIN cliente c ON c.id = r.cliente_id
         LEFT JOIN zona z ON z.id = r.zona_id
             WHERE r.id IN :ids
        """), {'ids': tuple(remitos_ids)}).mappings().all()

        for r in remitos:
            zid = r['zona_id'] or 0
            if zid not in grupos:
                grupos[zid] = {
                    'nombre': r['zona_nombre'] or 'Sin zona',
                    'color': r['zona_color'] or '#6c757d',
                    'orden': r['zona_orden'] if r['zona_orden'] is not None else 99999,
                    'items': []
                }
            grupos[zid]['items'].append({
                'orden_manual': r['orden_manual'],
                'comprobante': f"R {r['punto_venta']}-{r['numero']}",
                'cliente': r['cliente_nombre'],
                'direccion': r['direccion'] or '',
                'telefono': r['telefono'] or '',
                'total': float(r['total_al_emitir'] or 0)
            })

    if pedidos_ids:
        pedidos = db.session.execute(text("""
            SELECT p.id, p.total,
                   c.nombre AS cliente_nombre, c.direccion, c.telefono,
                   z.id AS zona_id, z.nombre AS zona_nombre, z.color AS zona_color,
                   z.orden_reparto AS zona_orden,
                   COALESCE(p.orden_reparto_manual, 9999) AS orden_manual
              FROM pedido p
              JOIN cliente c ON c.id = p.cliente_id
         LEFT JOIN zona z ON z.id = p.zona_id
             WHERE p.id IN :ids
        """), {'ids': tuple(pedidos_ids)}).mappings().all()

        for p in pedidos:
            zid = p['zona_id'] or 0
            if zid not in grupos:
                grupos[zid] = {
                    'nombre': p['zona_nombre'] or 'Sin zona',
                    'color': p['zona_color'] or '#6c757d',
                    'orden': p['zona_orden'] if p['zona_orden'] is not None else 99999,
                    'items': []
                }
            grupos[zid]['items'].append({
                'orden_manual': p['orden_manual'],
                'comprobante': f"Pedido #{p['id']}",
                'cliente': p['cliente_nombre'],
                'direccion': p['direccion'] or '',
                'telefono': p['telefono'] or '',
                'total': float(p['total'] or 0)
            })

    # Ordenar items dentro de cada zona
    for zid in grupos:
        grupos[zid]['items'].sort(key=lambda x: x['orden_manual'])

    zonas_ordenadas = sorted(grupos.items(), key=lambda kv: (kv[1]['orden'], kv[1]['nombre']))

    # ============ GENERAR PDF ============
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=15*mm, rightMargin=15*mm,
        topMargin=15*mm, bottomMargin=15*mm
    )

    styles = getSampleStyleSheet()
    style_title = ParagraphStyle('T', parent=styles['Heading1'], alignment=TA_CENTER, fontSize=18, spaceAfter=4)
    style_sub = ParagraphStyle('Sub', parent=styles['Normal'], alignment=TA_CENTER, fontSize=11, spaceAfter=10)
    style_zona = ParagraphStyle('Z', parent=styles['Heading2'], alignment=TA_LEFT, fontSize=14, spaceAfter=6, textColor=colors.white)
    style_normal = styles['Normal']

    try:
        fecha_obj = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        fecha_fmt = fecha_obj.strftime('%d/%m/%Y')
    except Exception:
        fecha_fmt = fecha_str

    story = []
    total_general = 0
    total_items = 0

    for idx, (zid, grupo) in enumerate(zonas_ordenadas):
        if idx > 0:
            story.append(PageBreak())

        story.append(Paragraph("<b>HOJA DE REPARTO</b>", style_title))
        story.append(Paragraph(
            f"Fecha: <b>{fecha_fmt}</b>  &nbsp;&nbsp;|&nbsp;&nbsp;  "
            f"Chofer: <b>{chofer}</b>",
            style_sub
        ))

        try:
            color_zona = colors.HexColor(grupo['color'])
        except Exception:
            color_zona = colors.HexColor('#6c757d')

        zona_table = Table(
            [[Paragraph(f"<b>ZONA: {grupo['nombre'].upper()}</b>", style_zona)]],
            colWidths=[180*mm]
        )
        zona_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), color_zona),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(zona_table)
        story.append(Spacer(1, 4*mm))

        header = ['#', 'Comprobante', 'Cliente', 'Dirección', 'Teléfono', 'Total', 'Firma / Observ.']
        filas = [header]
        subtotal_zona = 0
        for i, it in enumerate(grupo['items'], 1):
            filas.append([
                str(i),
                it['comprobante'],
                it['cliente'][:32],
                it['direccion'][:42],
                it['telefono'],
                f"$ {it['total']:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
                ''
            ])
            subtotal_zona += it['total']

        filas.append([
            '', '', '', '', 'Subtotal:',
            f"$ {subtotal_zona:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
            ''
        ])

        t = Table(filas, colWidths=[8*mm, 25*mm, 40*mm, 45*mm, 25*mm, 22*mm, 25*mm], repeatRows=1)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#343a40')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.3, colors.grey),
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),
            ('ALIGN', (5, 1), (5, -1), 'RIGHT'),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#f1f3f5')),
            ('FONTNAME', (4, -1), (5, -1), 'Helvetica-Bold'),
            ('ALIGN', (4, -1), (4, -1), 'RIGHT'),
            ('TOPPADDING', (0, 1), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 10),
        ]))
        story.append(t)
        story.append(Spacer(1, 6*mm))

        total_general += subtotal_zona
        total_items += len(grupo['items'])

    # Pie con totales globales
    story.append(Spacer(1, 8*mm))
    pie_data = [[
        Paragraph(f"<b>TOTAL COMPROBANTES:</b> {total_items}", style_normal),
        Paragraph(f"<b>TOTAL GENERAL:</b> $ {total_general:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'), style_normal)
    ]]
    pie_table = Table(pie_data, colWidths=[90*mm, 90*mm])
    pie_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#e9ecef')),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
    ]))
    story.append(pie_table)

    story.append(Spacer(1, 15*mm))

    firmas_data = [[
        Paragraph("Firma del chofer al <b>retirar</b>:<br/><br/><br/>_____________________________", style_normal),
        Paragraph("Firma del chofer al <b>regresar</b>:<br/><br/><br/>_____________________________", style_normal)
    ]]
    firmas_table = Table(firmas_data, colWidths=[90*mm, 90*mm])
    firmas_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(firmas_table)

    doc.build(story)
    pdf_bytes = buf.getvalue()
    buf.close()

    response = make_response(pdf_bytes)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename="hoja_reparto_{fecha_str}.pdf"'
    return response