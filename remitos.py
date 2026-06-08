# -*- coding: utf-8 -*-
"""
Blueprint: Remitos
------------------
Módulo de remitos (comprobantes internos no electrónicos):
- Confección con numeración correlativa por punto de venta
- Descuento de stock al confeccionar
- Edición mientras está en estado 'pendiente'
- Anulación con devolución de stock
- Consolidación y facturación (integra con nueva_venta vía session)
- Impresión térmica
"""

from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime

from extensions import db
from sqlalchemy import text

remitos_bp = Blueprint('remitos', __name__, url_prefix='/remitos')


# =====================================================================
# HELPERS
# =====================================================================

def _d(v, default='0'):
    if v is None or v == '':
        return Decimal(default)
    try:
        return Decimal(str(v))
    except Exception:
        return Decimal(default)


def _r2(v):
    return _d(v).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def _r3(v):
    return _d(v).quantize(Decimal('0.001'), rounding=ROUND_HALF_UP)


def _r4(v):
    return _d(v).quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)


def _es_admin():
    return session.get('rol') == 'admin'


def _usuario_id():
    return session.get('usuario_id') or session.get('user_id')


def _punto_venta_default():
    """Devuelve el punto de venta que se usa para numerar remitos."""
    # Usamos '00001' por defecto. Si tu sistema tiene varios PV, se podría parametrizar.
    return '00001'


def _proximo_numero_remito(pv):
    """
    Toma el próximo número de remito del numerador, lo incrementa
    y devuelve el número zfilled a 8 dígitos. Atómico.
    """
    db.session.execute(text("""
        INSERT INTO remito_numerador (punto_venta, ultimo_numero)
        VALUES (:pv, 1)
        ON DUPLICATE KEY UPDATE ultimo_numero = ultimo_numero + 1
    """), {'pv': pv})

    nuevo = db.session.execute(
        text("SELECT ultimo_numero FROM remito_numerador WHERE punto_venta = :pv"),
        {'pv': pv}
    ).scalar()
    return str(nuevo).zfill(8)


# =====================================================================
# LISTADO
# =====================================================================

@remitos_bp.route('/')
def listado():
    clientes = db.session.execute(text("""
        SELECT id, nombre FROM cliente WHERE activo = 1 ORDER BY nombre
    """)).mappings().all()
    return render_template('remitos_lista.html',
                           clientes=clientes,
                           es_admin=_es_admin())


@remitos_bp.route('/api/listar')
def api_listar():
    cliente_id = request.args.get('cliente_id', type=int)
    estado = request.args.get('estado', '')
    desde = request.args.get('desde')
    hasta = request.args.get('hasta')
    numero = (request.args.get('numero') or '').strip()
    zona = (request.args.get('zona') or '').strip()

    sql = """
        SELECT r.id, r.fecha, r.tipo_comprobante, r.punto_venta, r.numero, r.estado,
               r.total_al_emitir, r.factura_venta_id, r.fecha_facturacion,
               r.zona_id, r.en_reparto_fecha,
               c.nombre AS cliente_nombre, c.documento, c.tipo_documento,
               z.nombre AS zona_nombre, z.color AS zona_color,
               CONCAT(r.tipo_comprobante, ' ', r.punto_venta, '-', r.numero) AS numero_completo,
               COUNT(rd.id) AS items_count
          FROM remito r
          JOIN cliente c ON c.id = r.cliente_id
     LEFT JOIN zona z ON z.id = r.zona_id
     LEFT JOIN remito_detalle rd ON rd.remito_id = r.id
         WHERE 1=1
    """
    params = {}
    if cliente_id:
        sql += " AND r.cliente_id = :cid"
        params['cid'] = cliente_id
    if estado:
        sql += " AND r.estado = :estado"
        params['estado'] = estado
    if desde:
        sql += " AND r.fecha >= :desde"
        params['desde'] = desde
    if hasta:
        sql += " AND r.fecha <= :hasta"
        params['hasta'] = hasta
    if numero:
        sql += " AND r.numero LIKE :numero"
        params['numero'] = f"%{numero}%"
    if zona == 'SIN_ZONA':
        sql += " AND r.zona_id IS NULL"
    elif zona:
        try:
            params['zona_id'] = int(zona)
            sql += " AND r.zona_id = :zona_id"
        except ValueError:
            pass

    sql += " GROUP BY r.id ORDER BY r.fecha DESC, r.id DESC"

    rows = db.session.execute(text(sql), params).mappings().all()
    return jsonify([{
        'id': r['id'],
        'fecha': r['fecha'].strftime('%Y-%m-%d') if r['fecha'] else '',
        'numero_completo': r['numero_completo'],
        'cliente': r['cliente_nombre'],
        'cuit': f"{r['tipo_documento'] or 'DNI'} {r['documento']}" if r['documento'] else '',
        'estado': r['estado'],
        'total': float(r['total_al_emitir'] or 0),
        'items_count': r['items_count'],
        'factura_venta_id': r['factura_venta_id'],
        'fecha_facturacion': r['fecha_facturacion'].strftime('%Y-%m-%d') if r['fecha_facturacion'] else None,
        'zona_id': r['zona_id'],
        'zona_nombre': r['zona_nombre'],
        'zona_color': r['zona_color'],
    } for r in rows])


# =====================================================================
# NUEVO / EDITAR
# =====================================================================

@remitos_bp.route('/nuevo')
def nuevo():
    clientes = db.session.execute(text("""
        SELECT id, nombre, documento, tipo_documento, direccion, condicion_iva, zona_id FROM cliente WHERE activo = 1 ORDER BY nombre
    """)).mappings().all()
    return render_template('remitos_form.html',
                           clientes=clientes,
                           remito_id=None,
                           es_admin=_es_admin())


@remitos_bp.route('/editar/<int:remito_id>')
def editar(remito_id):
    # Validar que exista y esté en pendiente
    r = db.session.execute(
        text("SELECT id, estado FROM remito WHERE id = :id"),
        {'id': remito_id}
    ).mappings().first()
    if not r:
        flash('Remito no encontrado', 'danger')
        return redirect(url_for('remitos.listado'))
    if r['estado'] != 'pendiente':
        flash(f'No se puede editar un remito {r["estado"]}. Solo los remitos pendientes son editables.', 'warning')
        return redirect(url_for('remitos.ver', remito_id=remito_id))

    clientes = db.session.execute(text("""
        SELECT id, nombre, documento, tipo_documento, direccion, condicion_iva, zona_id FROM cliente WHERE activo = 1 ORDER BY nombre
    """)).mappings().all()
    return render_template('remitos_form.html',
                           clientes=clientes,
                           remito_id=remito_id,
                           es_admin=_es_admin())


@remitos_bp.route('/api/cargar/<int:remito_id>')
def api_cargar(remito_id):
    """Devuelve la cabecera + detalle de un remito para cargarlo en el form."""
    cab = db.session.execute(text("""
        SELECT r.*, c.nombre AS cliente_nombre, c.documento, c.tipo_documento,
               c.direccion, c.condicion_iva,
               z.nombre AS zona_nombre, z.color AS zona_color
          FROM remito r
          JOIN cliente c ON c.id = r.cliente_id
     LEFT JOIN zona z ON z.id = r.zona_id
         WHERE r.id = :id
    """), {'id': remito_id}).mappings().first()
    if not cab:
        return jsonify({'error': 'Remito no encontrado'}), 404

    det = db.session.execute(text("""
        SELECT rd.*, p.codigo, p.nombre, p.stock, p.iva AS iva_actual, p.es_pesable
          FROM remito_detalle rd
          JOIN producto p ON p.id = rd.producto_id
         WHERE rd.remito_id = :id
         ORDER BY rd.id
    """), {'id': remito_id}).mappings().all()

    # Si el remito está liquidado, traer también la liquidación
    liquidacion = None
    if cab['estado'] in ('liquidado', 'facturado'):
        liq_cab = db.session.execute(text("""
            SELECT id, fecha_liquidacion, usuario_nombre, observaciones
              FROM remito_liquidacion
             WHERE remito_id = :rid
        """), {'rid': remito_id}).mappings().first()
        if liq_cab:
            liq_det = db.session.execute(text("""
                SELECT rld.remito_detalle_id, rld.producto_id,
                       rld.cant_original, rld.cant_entregada,
                       rld.cant_devuelta, rld.cant_rotura, rld.motivo
                  FROM remito_liquidacion_detalle rld
                 WHERE rld.liquidacion_id = :lid
            """), {'lid': liq_cab['id']}).mappings().all()
            liquidacion = {
                'id':                int(liq_cab['id']),
                'fecha':             liq_cab['fecha_liquidacion'].strftime('%Y-%m-%d %H:%M') if liq_cab['fecha_liquidacion'] else '',
                'usuario':           liq_cab['usuario_nombre'] or '',
                'observaciones':     liq_cab['observaciones'] or '',
                'detalle': {int(d['remito_detalle_id']): {
                    'cant_original':  float(d['cant_original']),
                    'cant_entregada': float(d['cant_entregada']),
                    'cant_devuelta':  float(d['cant_devuelta']),
                    'cant_rotura':    float(d['cant_rotura']),
                    'motivo':         d['motivo'] or '',
                } for d in liq_det},
            }

    return jsonify({
        'cabecera': {
            'id': cab['id'],
            'cliente_id': cab['cliente_id'],
            'cliente_nombre': cab['cliente_nombre'],
            'cuit': f"{cab['tipo_documento'] or 'DNI'} {cab['documento']}" if cab['documento'] else '',
            'direccion': cab['direccion'] or '',
            'condicion_iva': cab['condicion_iva'] or '',
            'fecha': cab['fecha'].strftime('%Y-%m-%d') if cab['fecha'] else '',
            'punto_venta': cab['punto_venta'],
            'numero': cab['numero'],
            'numero_completo': f"{cab['tipo_comprobante']} {cab['punto_venta']}-{cab['numero']}",
            'estado': cab['estado'],
            'total': float(cab['total_al_emitir'] or 0),
            'observaciones': cab['observaciones'] or '',
            'zona_id': cab['zona_id'],
            'zona_nombre': cab['zona_nombre'] or '',
            'zona_color': cab['zona_color'] or '',
            'en_reparto_fecha': cab['en_reparto_fecha'].strftime('%Y-%m-%d') if cab['en_reparto_fecha'] else None,
        },
        'items': [{
            'remito_detalle_id': int(r['id']),
            'producto_id': r['producto_id'],
            'codigo': r['codigo'],
            'nombre': r['nombre'],
            'cantidad': float(r['cantidad']),
            'precio_unitario': float(r['precio_unitario_al_emitir']),
            'iva': float(r['iva']),
            'subtotal': float(r['subtotal_al_emitir']),
            'stock_actual': float(r['stock'] or 0),
            'es_pesable': bool(r['es_pesable']),
        } for r in det],
        'liquidacion': liquidacion,
    })


# =====================================================================
# BÚSQUEDA DE PRODUCTOS (para el form)
# =====================================================================

@remitos_bp.route('/api/buscar_producto')
def api_buscar_producto():
    q = (request.args.get('q') or '').strip()
    if len(q) < 2:
        return jsonify([])
    like = f"%{q}%"
    rows = db.session.execute(text("""
        SELECT id, codigo, nombre, stock, precio, iva, es_pesable, es_combo
          FROM producto
         WHERE activo = 1
           AND (codigo = :q OR codigo LIKE :like OR nombre LIKE :like OR codigo_barras = :q)
         ORDER BY
           CASE WHEN codigo = :q THEN 0 ELSE 1 END,
           nombre
         LIMIT 15
    """), {'q': q, 'like': like}).mappings().all()
    return jsonify([{
        'id': r['id'],
        'codigo': r['codigo'],
        'nombre': r['nombre'],
        'stock': float(r['stock'] or 0),
        'precio': float(r['precio'] or 0),
        'iva': float(r['iva'] or 21),
        'es_pesable': bool(r['es_pesable']),
        'es_combo': bool(r['es_combo']),
    } for r in rows])


# =====================================================================
# GUARDAR (crear o actualizar) - TRANSACCIÓN ATÓMICA
# =====================================================================

@remitos_bp.route('/api/guardar', methods=['POST'])
def api_guardar():
    data = request.get_json() or {}
    remito_id = data.get('remito_id')  # None si es nuevo
    cliente_id = data.get('cliente_id')
    fecha = data.get('fecha')
    observaciones = (data.get('observaciones') or '').strip()
    zona_id = data.get('zona_id')  # puede venir explícito, None, o 0
    items = data.get('items') or []

    if not cliente_id:
        return jsonify({'error': 'Seleccioná un cliente'}), 400
    if not fecha:
        return jsonify({'error': 'Ingresá la fecha'}), 400
    if not items:
        return jsonify({'error': 'El remito debe tener al menos un artículo'}), 400

    # Si no viene zona_id explícita, heredar la del cliente
    if not zona_id:
        zona_cliente = db.session.execute(
            text("SELECT zona_id FROM cliente WHERE id = :cid"),
            {'cid': cliente_id}
        ).scalar()
        zona_id = zona_cliente  # puede ser None

    try:
        if remito_id:
            # ---- EDITAR ----
            actual = db.session.execute(
                text("SELECT estado FROM remito WHERE id = :id FOR UPDATE"),
                {'id': remito_id}
            ).mappings().first()
            if not actual:
                return jsonify({'error': 'Remito no encontrado'}), 404
            if actual['estado'] != 'pendiente':
                return jsonify({'error': f'No se puede editar un remito {actual["estado"]}'}), 400

            # Devolver stock de los items ANTIGUOS
            items_viejos = db.session.execute(text("""
                SELECT producto_id, cantidad FROM remito_detalle WHERE remito_id = :id
            """), {'id': remito_id}).mappings().all()
            for iv in items_viejos:
                # ═══ AUDITORÍA: capturar datos antes del UPDATE ═══
                prod_audit = db.session.execute(text("""
                    SELECT codigo, nombre, stock FROM producto WHERE id = :pid
                """), {'pid': iv['producto_id']}).mappings().first()

                db.session.execute(text("""
                    UPDATE producto SET stock = stock + :cant WHERE id = :pid
                """), {'cant': iv['cantidad'], 'pid': iv['producto_id']})

                # ═══ AUDITORÍA: registrar reversión por edición ═══
                if prod_audit:
                    stock_anterior_audit = float(prod_audit['stock'])
                    stock_nuevo_audit = stock_anterior_audit + float(iv['cantidad'])
                    registrar_movimiento_stock(
                        db=db,
                        producto_id=iv['producto_id'],
                        tipo='remito_edicion',
                        cantidad=float(iv['cantidad']),
                        signo='+',
                        stock_anterior=stock_anterior_audit,
                        stock_nuevo=stock_nuevo_audit,
                        referencia_tipo='remito',
                        referencia_id=remito_id,
                        motivo=f'Edición remito #{remito_id}: reversión items antiguos',
                        usuario_id=_usuario_id(),
                        usuario_nombre=session.get('nombre', 'Sistema'),
                        codigo_producto=prod_audit.get('codigo'),
                        nombre_producto=prod_audit.get('nombre'),
                    )

            # Borrar detalle viejo
            db.session.execute(text("DELETE FROM remito_detalle WHERE remito_id = :id"),
                               {'id': remito_id})

            # Actualizar cabecera
            db.session.execute(text("""
                UPDATE remito
                   SET cliente_id = :cid, fecha = :fecha, observaciones = :obs,
                       zona_id = :zona_id
                 WHERE id = :id
            """), {'cid': cliente_id, 'fecha': fecha, 'obs': observaciones,
                   'zona_id': zona_id, 'id': remito_id})

            factura_id_resp = remito_id
        else:
            # ---- NUEVO ----
            pv = _punto_venta_default()
            numero = _proximo_numero_remito(pv)

            db.session.execute(text("""
                INSERT INTO remito
                    (cliente_id, fecha, tipo_comprobante, punto_venta, numero,
                     estado, total_al_emitir, observaciones, usuario_id, zona_id)
                VALUES
                    (:cid, :fecha, 'R', :pv, :num,
                     'pendiente', 0, :obs, :uid, :zona_id)
            """), {
                'cid': cliente_id, 'fecha': fecha, 'pv': pv, 'num': numero,
                'obs': observaciones, 'uid': _usuario_id(), 'zona_id': zona_id
            })
            factura_id_resp = db.session.execute(text("SELECT LAST_INSERT_ID()")).scalar()

        # ---- Detalle + descuento de stock (común a ambos casos) ----
        total_remito = Decimal('0')
        for it in items:
            pid = it.get('producto_id')
            cant = _r3(it.get('cantidad', 0))
            precio_unit = _r4(it.get('precio_unitario', 0))  # con IVA
            iva_p = _d(it.get('iva', 21))

            if not pid or cant <= 0:
                raise Exception('Item inválido (cantidad o producto faltante)')

            # Validar stock y que no sea combo
            prod = db.session.execute(text("""
                SELECT id, codigo, nombre, stock, es_combo, es_pesable
                  FROM producto WHERE id = :pid FOR UPDATE
            """), {'pid': pid}).mappings().first()
            if not prod:
                raise Exception(f'Producto id={pid} no encontrado')
            if prod['es_combo']:
                raise Exception(f'Producto id={pid} es un combo. Cargá los productos base.')
            if not prod['es_pesable'] and cant > _d(prod['stock']) + Decimal('0.001'):
                raise Exception(f'Stock insuficiente para producto id={pid}. Disponible: {prod["stock"]}')

            subtotal = _r2(cant * precio_unit)
            total_remito += subtotal

            # Insertar detalle
            remito_id_actual = remito_id or factura_id_resp
            db.session.execute(text("""
                INSERT INTO remito_detalle
                    (remito_id, producto_id, cantidad, precio_unitario_al_emitir,
                     iva, subtotal_al_emitir)
                VALUES
                    (:rid, :pid, :cant, :precio, :iva, :sub)
            """), {
                'rid': remito_id_actual, 'pid': pid, 'cant': cant,
                'precio': precio_unit, 'iva': iva_p, 'sub': subtotal
            })

            # Descontar stock
            stock_anterior_audit = float(prod['stock'])
            stock_nuevo_audit = stock_anterior_audit - float(cant)
            db.session.execute(text("""
                UPDATE producto SET stock = stock - :cant WHERE id = :pid
            """), {'cant': cant, 'pid': pid})

            # ═══ AUDITORÍA: registrar salida de stock por remito ═══
            registrar_movimiento_stock(
                db=db,
                producto_id=pid,
                tipo='remito',
                cantidad=float(cant),
                signo='-',
                stock_anterior=stock_anterior_audit,
                stock_nuevo=stock_nuevo_audit,
                referencia_tipo='remito',
                referencia_id=remito_id_actual,
                motivo=f'Emisión remito #{remito_id_actual}',
                usuario_id=_usuario_id(),
                usuario_nombre=session.get('nombre', 'Sistema'),
                codigo_producto=prod.get('codigo'),
                nombre_producto=prod.get('nombre'),
            )

        # Actualizar total del remito
        remito_id_final = remito_id or factura_id_resp
        db.session.execute(text("""
            UPDATE remito SET total_al_emitir = :total WHERE id = :id
        """), {'total': _r2(total_remito), 'id': remito_id_final})

        db.session.commit()
        return jsonify({'ok': True, 'remito_id': remito_id_final})

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# =====================================================================
# VER REMITO (HTML)
# =====================================================================

@remitos_bp.route('/ver/<int:remito_id>')
def ver(remito_id):
    return render_template('remitos_ver.html',
                           remito_id=remito_id,
                           es_admin=_es_admin())


# =====================================================================
# IMPRESIÓN TÉRMICA (usa impresora_termica.py — módulo de la impresora EPSON)
# =====================================================================

@remitos_bp.route('/imprimir/<int:remito_id>', methods=['POST', 'GET'])
def imprimir(remito_id):
    """
    Arma los datos del remito y llama a `imprimir_remito_termico` del módulo
    `impresora_termica`. Se puede llamar por GET o POST; devuelve JSON con
    success/error.
    """
    cab = db.session.execute(text("""
        SELECT r.*, c.nombre AS cliente_nombre, c.documento, c.tipo_documento,
               c.direccion, c.condicion_iva,
               u.nombre AS usuario_nombre,
               z.nombre AS zona_nombre
          FROM remito r
          JOIN cliente c ON c.id = r.cliente_id
     LEFT JOIN usuario u ON u.id = r.usuario_id
     LEFT JOIN zona z ON z.id = r.zona_id
         WHERE r.id = :id
    """), {'id': remito_id}).mappings().first()
    if not cab:
        return jsonify({'success': False, 'error': 'Remito no encontrado'}), 404

    det = db.session.execute(text("""
        SELECT rd.cantidad, rd.precio_unitario_al_emitir AS precio_unitario,
               rd.subtotal_al_emitir AS subtotal, rd.iva,
               p.codigo, p.nombre
          FROM remito_detalle rd
          JOIN producto p ON p.id = rd.producto_id
         WHERE rd.remito_id = :id
         ORDER BY rd.id
    """), {'id': remito_id}).mappings().all()

    datos = {
        'numero_completo': f"{cab['tipo_comprobante']} {cab['punto_venta']}-{cab['numero']}",
        'punto_venta': cab['punto_venta'],
        'numero': cab['numero'],
        'fecha': cab['fecha_creacion'] or cab['fecha'],
        'cliente_nombre': cab['cliente_nombre'],
        'documento': cab['documento'],
        'tipo_documento': cab['tipo_documento'],
        'direccion': cab['direccion'],
        'condicion_iva': cab['condicion_iva'],
        'zona_nombre': cab['zona_nombre'] or '',
        'usuario_nombre': cab['usuario_nombre'] or 'Sistema',
        'observaciones': cab['observaciones'] or '',
        'items': [{
            'nombre': r['nombre'],
            'cantidad': float(r['cantidad']),
            'subtotal': float(r['subtotal']),
        } for r in det]
    }

    try:
        from impresora_termica import imprimir_remito_termico
        resultado = imprimir_remito_termico(datos)
        if resultado.get('success'):
            return jsonify({'success': True, 'mensaje': resultado.get('mensaje', 'Remito impreso')})
        return jsonify({'success': False, 'error': resultado.get('error', 'Error desconocido')}), 500
    except ImportError as e:
        return jsonify({
            'success': False,
            'error': f'Módulo de impresión no disponible ({e}). Usá el botón "Imprimir (navegador)" en la vista del remito.'
        }), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# =====================================================================
# ANULAR (revierte stock)
# =====================================================================

@remitos_bp.route('/api/anular/<int:remito_id>', methods=['POST'])
def api_anular(remito_id):
    data = request.get_json() or {}
    motivo = (data.get('motivo') or '').strip()

    try:
        r = db.session.execute(
            text("SELECT estado FROM remito WHERE id = :id FOR UPDATE"),
            {'id': remito_id}
        ).mappings().first()
        if not r:
            return jsonify({'error': 'Remito no encontrado'}), 404
        if r['estado'] == 'facturado':
            return jsonify({
                'error': 'No se puede anular un remito ya facturado. Si hay devoluciones, generá una Nota de Crédito desde el módulo correspondiente.'
            }), 400
        if r['estado'] == 'liquidado':
            return jsonify({
                'error': 'No se puede anular un remito ya liquidado. Si necesitás corregir, contactá al administrador.'
            }), 400
        if r['estado'] == 'anulado':
            return jsonify({'error': 'El remito ya está anulado'}), 400

        # Devolver stock
        items = db.session.execute(text("""
            SELECT producto_id, cantidad FROM remito_detalle WHERE remito_id = :id
        """), {'id': remito_id}).mappings().all()
        for it in items:
            # ═══ AUDITORÍA: capturar datos antes del UPDATE ═══
            prod_audit = db.session.execute(text("""
                SELECT codigo, nombre, stock FROM producto WHERE id = :pid
            """), {'pid': it['producto_id']}).mappings().first()

            db.session.execute(text("""
                UPDATE producto SET stock = stock + :cant WHERE id = :pid
            """), {'cant': it['cantidad'], 'pid': it['producto_id']})

            # ═══ AUDITORÍA: registrar la anulación del remito ═══
            if prod_audit:
                stock_anterior_audit = float(prod_audit['stock'])
                stock_nuevo_audit = stock_anterior_audit + float(it['cantidad'])
                registrar_movimiento_stock(
                    db=db,
                    producto_id=it['producto_id'],
                    tipo='remito_anulado',
                    cantidad=float(it['cantidad']),
                    signo='+',
                    stock_anterior=stock_anterior_audit,
                    stock_nuevo=stock_nuevo_audit,
                    referencia_tipo='remito',
                    referencia_id=remito_id,
                    motivo=f'Anulación remito #{remito_id}' + (f': {motivo}' if motivo else ''),
                    usuario_id=_usuario_id(),
                    usuario_nombre=session.get('nombre', 'Sistema'),
                    codigo_producto=prod_audit.get('codigo'),
                    nombre_producto=prod_audit.get('nombre'),
                )

        db.session.execute(text("""
            UPDATE remito
               SET estado = 'anulado',
                   fecha_anulacion = NOW(),
                   motivo_anulacion = :motivo
             WHERE id = :id
        """), {'motivo': motivo or 'Sin motivo especificado', 'id': remito_id})

        # Si el remito había sido generado desde un pedido, liberar el pedido:
        # vuelve al estado 'cotizado' y se desvincula del remito anulado.
        # Así puede volver a remitarse o facturarse desde la vista de pedidos.
        db.session.execute(text("""
            UPDATE pedido
               SET estado = 'cotizado',
                   remito_id = NULL,
                   fecha_actualizacion = NOW()
             WHERE remito_id = :rid
        """), {'rid': remito_id})

        db.session.commit()
        return jsonify({'ok': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# =====================================================================
# PREPARAR FACTURACIÓN: consolida items y los deja en session
# =====================================================================

@remitos_bp.route('/api/preparar_facturacion', methods=['POST'])
def api_preparar_facturacion():
    """
    Recibe lista de remito_ids, valida que sean todos del mismo cliente
    y estén en pendiente o liquidado, consolida items y los guarda en
    session para que nueva_venta.html los precargue.

    Si un remito está LIQUIDADO, usa las cantidades entregadas reales
    (de remito_liquidacion_detalle) en vez de la cantidad original.
    """
    data = request.get_json() or {}
    remito_ids = data.get('remito_ids') or []
    if not remito_ids:
        return jsonify({'error': 'No se seleccionó ningún remito'}), 400

    # Validar: traer los remitos uno por uno (más simple que tuple binding)
    rows = []
    for rid in remito_ids:
        r = db.session.execute(text("""
            SELECT id, cliente_id, estado, tipo_comprobante, punto_venta, numero
              FROM remito WHERE id = :id
        """), {'id': rid}).mappings().first()
        if r:
            rows.append(r)

    if len(rows) != len(remito_ids):
        return jsonify({'error': 'Alguno de los remitos no existe'}), 404

    clientes_distintos = set(r['cliente_id'] for r in rows)
    if len(clientes_distintos) > 1:
        return jsonify({'error': 'Todos los remitos deben ser del mismo cliente'}), 400

    estados_validos = ('pendiente', 'liquidado')
    no_facturables = [f"R {r['punto_venta']}-{r['numero']} ({r['estado']})"
                      for r in rows if r['estado'] not in estados_validos]
    if no_facturables:
        return jsonify({'error': f'Solo remitos pendientes o liquidados se pueden facturar. No cumplen: {", ".join(no_facturables)}'}), 400

    cliente_id = list(clientes_distintos)[0]

    # Consolidar items: si está liquidado usa cant_entregada, sino cantidad original.
    # Se hace en Python por si hay mezcla de estados (improbable pero contemplado).
    # Para cada producto guardamos cantidad acumulada + datos (precio histórico, nombre, etc.)
    consolidados = {}   # pid -> cantidad
    datos_prod = {}     # pid -> dict con codigo, nombre, precio_sin_iva, iva, stock
    for r in rows:
        if r['estado'] == 'liquidado':
            # Usar cant_entregada de la liquidación, pero el precio histórico sale del remito_detalle
            items_r = db.session.execute(text("""
                SELECT rld.producto_id,
                       rld.cant_entregada AS cantidad,
                       rd.precio_unitario_al_emitir AS precio_con_iva,
                       rd.iva AS iva,
                       p.codigo, p.nombre, p.stock
                  FROM remito_liquidacion_detalle rld
                  JOIN remito_liquidacion rl ON rl.id = rld.liquidacion_id
                  JOIN remito_detalle rd ON rd.remito_id = rl.remito_id AND rd.producto_id = rld.producto_id
                  JOIN producto p ON p.id = rld.producto_id
                 WHERE rl.remito_id = :rid
                   AND rld.cant_entregada > 0
            """), {'rid': r['id']}).mappings().all()
        else:
            # Pendiente: usar cantidad original
            items_r = db.session.execute(text("""
                SELECT rd.producto_id,
                       rd.cantidad,
                       rd.precio_unitario_al_emitir AS precio_con_iva,
                       rd.iva AS iva,
                       p.codigo, p.nombre, p.stock
                  FROM remito_detalle rd
                  JOIN producto p ON p.id = rd.producto_id
                 WHERE rd.remito_id = :rid
            """), {'rid': r['id']}).mappings().all()

        for it in items_r:
            pid = int(it['producto_id'])
            cant = float(it['cantidad'])
            consolidados[pid] = consolidados.get(pid, 0.0) + cant
            if pid not in datos_prod:
                iva = float(it['iva']) if it['iva'] is not None else 21.0
                precio_con_iva = float(it['precio_con_iva']) if it['precio_con_iva'] is not None else 0.0
                # nueva_venta espera el precio SIN IVA (igual que el flujo de pedidos)
                precio_sin_iva = round(precio_con_iva / (1 + iva / 100), 4) if iva else precio_con_iva
                datos_prod[pid] = {
                    'codigo': it['codigo'],
                    'nombre': it['nombre'],
                    'iva': iva,
                    'precio_unitario': precio_sin_iva,
                    'stock': float(it['stock']) if it['stock'] is not None else 999,
                }

    if not consolidados:
        return jsonify({'error': 'No hay items para facturar (los remitos liquidados no tienen cantidades entregadas)'}), 400

    # Nombre del cliente para precargar en nueva_venta
    cli = db.session.execute(
        text("SELECT nombre FROM cliente WHERE id = :cid"), {'cid': cliente_id}
    ).mappings().first()
    cliente_nombre = cli['nombre'] if cli else ''

    # Armar lista de productos en el MISMO formato que usa el flujo de pedidos
    # (nueva_venta.html -> verificarPedidoPendiente los lee de sessionStorage)
    productos = []
    for pid, cant in consolidados.items():
        d = datos_prod.get(pid, {})
        productos.append({
            'producto_id': pid,
            'codigo': d.get('codigo', ''),
            'nombre': d.get('nombre', ''),
            'cantidad': cant,
            'precio_unitario': d.get('precio_unitario', 0),
            'iva': d.get('iva', 21),
            'stock': d.get('stock', 999),
            'es_combo': False,
        })

    # Guardar también en session (compatibilidad / vinculación posterior de remitos)
    session['remitos_a_facturar'] = {
        'remito_ids': list(remito_ids),
        'cliente_id': cliente_id,
        'items': [{'producto_id': p['producto_id'], 'cantidad': p['cantidad']} for p in productos]
    }

    # Devolver el paquete completo para que remitos_lista.html lo guarde en
    # sessionStorage['pedido_para_facturar'] y nueva_venta lo precargue.
    return jsonify({
        'ok': True,
        'redirect': '/nueva_venta',
        'remito_ids': list(remito_ids),
        'cliente_id': cliente_id,
        'cliente_nombre': cliente_nombre,
        'lista_precio': 1,
        'productos': productos
    })


@remitos_bp.route('/api/items_a_facturar')
def api_items_a_facturar():
    """Devuelve los items pendientes de facturar que hay en session (para nueva_venta.html)."""
    data = session.get('remitos_a_facturar')
    if not data:
        return jsonify({'hay_remitos': False})
    return jsonify({
        'hay_remitos': True,
        'remito_ids': data['remito_ids'],
        'cliente_id': data['cliente_id'],
        'items': data['items']
    })


@remitos_bp.route('/api/cancelar_facturacion', methods=['POST'])
def api_cancelar_facturacion():
    """Limpia la session si el usuario cancela la facturación antes de emitir."""
    session.pop('remitos_a_facturar', None)
    return jsonify({'ok': True})


@remitos_bp.route('/api/marcar_facturados', methods=['POST'])
def api_marcar_facturados():
    """
    Marca los remitos indicados como facturados y los vincula con la factura_venta_id.
    Se llama desde nueva_venta.html después de emitir exitosamente la factura.
    """
    data = request.get_json() or {}
    remito_ids = data.get('remito_ids') or []
    factura_venta_id = data.get('factura_venta_id')

    if not remito_ids:
        return jsonify({'error': 'No se recibieron remitos a marcar'}), 400

    try:
        for rid in remito_ids:
            db.session.execute(text("""
                UPDATE remito
                   SET estado = 'facturado',
                       factura_venta_id = :fid,
                       fecha_facturacion = NOW()
                 WHERE id = :id AND estado IN ('pendiente','liquidado')
            """), {'fid': factura_venta_id, 'id': rid})
        db.session.commit()
        # Limpiar session
        session.pop('remitos_a_facturar', None)
        return jsonify({'ok': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@remitos_bp.route('/api/marcar_facturado_manual/<int:remito_id>', methods=['POST'])
def api_marcar_facturado_manual(remito_id):
    """
    Permite marcar un remito como facturado manualmente (fallback por si falló
    el marcado automático desde nueva_venta.html). Solo admin.
    """
    if not _es_admin():
        return jsonify({'error': 'Solo el administrador puede marcar remitos manualmente'}), 403

    data = request.get_json() or {}
    factura_venta_id = data.get('factura_venta_id')

    try:
        r = db.session.execute(
            text("SELECT estado FROM remito WHERE id = :id"),
            {'id': remito_id}
        ).mappings().first()
        if not r:
            return jsonify({'error': 'Remito no encontrado'}), 404
        if r['estado'] not in ('pendiente', 'liquidado'):
            return jsonify({'error': f'El remito ya está {r["estado"]}'}), 400

        db.session.execute(text("""
            UPDATE remito
               SET estado = 'facturado',
                   factura_venta_id = :fid,
                   fecha_facturacion = NOW()
             WHERE id = :id
        """), {'fid': factura_venta_id, 'id': remito_id})
        db.session.commit()
        return jsonify({'ok': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# =====================================================================
# LIQUIDACION DE REMITOS
# =====================================================================
# Cuando vuelve el camion del reparto, antes de facturar se liquida el
# remito: por cada item se indica cuanto se entrego, cuanto se devolvio
# (vuelve a stock), y cuanto se rompio en el viaje (merma propia, no
# vuelve a stock y no se factura).
#
# Restriccion:  cant_entregada + cant_devuelta + cant_rotura = cant_original
# =====================================================================

@remitos_bp.route('/api/liquidar/<int:remito_id>', methods=['POST'])
def api_liquidar(remito_id):
    """
    Liquida un remito pendiente.

    Payload:
    {
        "items": [
            {
                "remito_detalle_id": 123,
                "cant_entregada": 10.000,
                "cant_devuelta": 0.000,
                "cant_rotura": 0.000,
                "motivo": "Cliente queria mas chico"   # opcional, max 200
            },
            ...
        ],
        "observaciones": "..."   # opcional, comentario general
    }

    Efectos:
    - Suma stock por cant_devuelta (devuelve al deposito).
    - Registra movimientos en stock_movimiento: tipo='devolucion' para devueltos,
      tipo='merma' para roturas (no afecta stock fisico, ya estaba descontado).
    - Inserta filas en remito_liquidacion + remito_liquidacion_detalle.
    - Cambia el estado del remito a 'liquidado'.
    """
    if 'user_id' not in session and 'usuario_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401

    data = request.get_json() or {}
    items = data.get('items') or []
    observaciones = (data.get('observaciones') or '').strip()

    if not items:
        return jsonify({'error': 'No se enviaron items'}), 400

    # Importar registrar_movimiento_stock (defensivo)
    try:
        from stock_audit import registrar_movimiento_stock
    except ImportError:
        def registrar_movimiento_stock(*args, **kwargs):
            return False

    try:
        # Lockear el remito
        r = db.session.execute(text("""
            SELECT id, estado FROM remito WHERE id = :id FOR UPDATE
        """), {'id': remito_id}).mappings().first()

        if not r:
            return jsonify({'error': 'Remito no encontrado'}), 404
        if r['estado'] != 'pendiente':
            return jsonify({'error': f"Solo se pueden liquidar remitos pendientes. Estado actual: {r['estado']}"}), 400

        # Verificar que no este liquidado ya (defensivo, hay UK pero por las dudas)
        ya = db.session.execute(text("""
            SELECT id FROM remito_liquidacion WHERE remito_id = :rid
        """), {'rid': remito_id}).mappings().first()
        if ya:
            return jsonify({'error': 'Este remito ya tiene una liquidacion cargada'}), 400

        # Traer todos los detalles del remito para validar
        detalles_rem = db.session.execute(text("""
            SELECT rd.id, rd.producto_id, rd.cantidad, p.codigo, p.nombre, p.stock
              FROM remito_detalle rd
              JOIN producto p ON p.id = rd.producto_id
             WHERE rd.remito_id = :rid
        """), {'rid': remito_id}).mappings().all()
        det_by_id = {int(d['id']): d for d in detalles_rem}

        # Validar que vengan TODOS los detalles del remito
        ids_enviados = {int(it.get('remito_detalle_id') or 0) for it in items}
        ids_remito   = set(det_by_id.keys())
        if ids_enviados != ids_remito:
            faltantes = ids_remito - ids_enviados
            extras    = ids_enviados - ids_remito
            msgs = []
            if faltantes:
                msgs.append(f'Faltan items: {sorted(faltantes)}')
            if extras:
                msgs.append(f'Items que no son del remito: {sorted(extras)}')
            return jsonify({'error': '; '.join(msgs)}), 400

        # Validar cantidades: cant_entregada + cant_devuelta + cant_rotura = cant_original
        items_validados = []
        for it in items:
            rid = int(it.get('remito_detalle_id') or 0)
            d = det_by_id[rid]
            cant_orig = _r3(d['cantidad'])
            cant_ent  = _r3(it.get('cant_entregada') or 0)
            cant_dev  = _r3(it.get('cant_devuelta') or 0)
            cant_rot  = _r3(it.get('cant_rotura') or 0)

            if cant_ent < 0 or cant_dev < 0 or cant_rot < 0:
                return jsonify({'error': f'Las cantidades no pueden ser negativas (item {d["codigo"]})'}), 400

            suma = cant_ent + cant_dev + cant_rot
            if abs(suma - cant_orig) > Decimal('0.001'):
                return jsonify({
                    'error': f'En "{d["codigo"]} - {d["nombre"]}" la suma de entregada + devuelta + rotura ({suma}) no coincide con la cantidad del remito ({cant_orig})'
                }), 400

            motivo = (it.get('motivo') or '').strip()[:200]

            items_validados.append({
                'remito_detalle_id': rid,
                'producto_id':       int(d['producto_id']),
                'codigo':            d['codigo'],
                'nombre':            d['nombre'],
                'stock':             d['stock'],
                'cant_original':     cant_orig,
                'cant_entregada':    cant_ent,
                'cant_devuelta':     cant_dev,
                'cant_rotura':       cant_rot,
                'motivo':            motivo,
            })

        # Insertar cabecera de liquidacion
        usuario_id     = _usuario_id()
        usuario_nombre = session.get('usuario_nombre') or session.get('username') or ''

        ins = db.session.execute(text("""
            INSERT INTO remito_liquidacion
                (remito_id, fecha_liquidacion, usuario_id, usuario_nombre, observaciones)
            VALUES
                (:rid, NOW(), :uid, :uname, :obs)
        """), {
            'rid':   remito_id,
            'uid':   usuario_id,
            'uname': usuario_nombre,
            'obs':   observaciones or None,
        })
        liquidacion_id = ins.lastrowid

        # Procesar cada item
        for v in items_validados:
            # Insertar detalle de liquidacion
            db.session.execute(text("""
                INSERT INTO remito_liquidacion_detalle
                    (liquidacion_id, remito_detalle_id, producto_id,
                     cant_original, cant_entregada, cant_devuelta, cant_rotura, motivo)
                VALUES
                    (:lid, :rdid, :pid,
                     :corig, :cent, :cdev, :crot, :mot)
            """), {
                'lid':   liquidacion_id,
                'rdid':  v['remito_detalle_id'],
                'pid':   v['producto_id'],
                'corig': float(v['cant_original']),
                'cent':  float(v['cant_entregada']),
                'cdev':  float(v['cant_devuelta']),
                'crot':  float(v['cant_rotura']),
                'mot':   v['motivo'] or None,
            })

            # Si hay devolucion, sumar stock al producto + registrar movimiento
            if v['cant_devuelta'] > 0:
                stock_anterior = _d(v['stock'])
                stock_nuevo    = stock_anterior + v['cant_devuelta']

                db.session.execute(text("""
                    UPDATE producto SET stock = stock + :cant WHERE id = :pid
                """), {'cant': float(v['cant_devuelta']), 'pid': v['producto_id']})

                registrar_movimiento_stock(
                    db                = db,
                    producto_id       = v['producto_id'],
                    tipo              = 'devolucion',
                    cantidad          = float(v['cant_devuelta']),
                    signo             = '+',
                    stock_anterior    = float(stock_anterior),
                    stock_nuevo       = float(stock_nuevo),
                    referencia_tipo   = 'remito_liquidacion',
                    referencia_id     = liquidacion_id,
                    motivo            = f'Devolucion (remito #{remito_id}): {v["motivo"]}' if v['motivo'] else f'Devolucion (remito #{remito_id})',
                    usuario_id        = usuario_id,
                    usuario_nombre    = usuario_nombre,
                    codigo_producto   = v['codigo'],
                    nombre_producto   = v['nombre'],
                )

            # Si hay rotura, NO toca stock fisico (ya estaba descontado al emitir)
            # pero registra movimiento informativo de tipo 'merma'
            if v['cant_rotura'] > 0:
                # Para auditoria: stock_anterior y stock_nuevo iguales (no cambia)
                # pero queda el movimiento como merma para reportes.
                stock_actual = _d(v['stock'])
                # Si hubo devolucion, el stock ya cambio; usar el real actual desde DB
                if v['cant_devuelta'] > 0:
                    stock_actual_db = db.session.execute(text("""
                        SELECT stock FROM producto WHERE id = :pid
                    """), {'pid': v['producto_id']}).scalar()
                    stock_actual = _d(stock_actual_db)

                registrar_movimiento_stock(
                    db                = db,
                    producto_id       = v['producto_id'],
                    tipo              = 'merma',
                    cantidad          = float(v['cant_rotura']),
                    signo             = '-',
                    stock_anterior    = float(stock_actual),
                    stock_nuevo       = float(stock_actual),  # no cambia el stock fisico
                    referencia_tipo   = 'remito_liquidacion',
                    referencia_id     = liquidacion_id,
                    motivo            = f'Rotura en viaje (remito #{remito_id}): {v["motivo"]}' if v['motivo'] else f'Rotura en viaje (remito #{remito_id})',
                    usuario_id        = usuario_id,
                    usuario_nombre    = usuario_nombre,
                    codigo_producto   = v['codigo'],
                    nombre_producto   = v['nombre'],
                )

        # Cambiar estado del remito a 'liquidado'
        db.session.execute(text("""
            UPDATE remito SET estado = 'liquidado' WHERE id = :id
        """), {'id': remito_id})

        db.session.commit()

        # Resumen para devolver al frontend
        total_ent = sum(v['cant_entregada'] for v in items_validados)
        total_dev = sum(v['cant_devuelta']  for v in items_validados)
        total_rot = sum(v['cant_rotura']    for v in items_validados)

        return jsonify({
            'ok': True,
            'liquidacion_id': liquidacion_id,
            'totales': {
                'entregado': float(total_ent),
                'devuelto':  float(total_dev),
                'rotura':    float(total_rot),
            },
        })

    except Exception as e:
        db.session.rollback()
        import traceback; traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@remitos_bp.route('/api/liquidacion/<int:remito_id>')
def api_cargar_liquidacion(remito_id):
    """
    Devuelve la liquidacion de un remito (si existe), con todos sus detalles.
    Sirve para mostrar la liquidacion en remitos_ver.html.
    """
    cab = db.session.execute(text("""
        SELECT id, fecha_liquidacion, usuario_nombre, observaciones
          FROM remito_liquidacion WHERE remito_id = :rid
    """), {'rid': remito_id}).mappings().first()

    if not cab:
        return jsonify({'tiene_liquidacion': False})

    det = db.session.execute(text("""
        SELECT rld.*, p.codigo, p.nombre
          FROM remito_liquidacion_detalle rld
          JOIN producto p ON p.id = rld.producto_id
         WHERE rld.liquidacion_id = :lid
         ORDER BY rld.id
    """), {'lid': cab['id']}).mappings().all()

    return jsonify({
        'tiene_liquidacion': True,
        'cabecera': {
            'id':            int(cab['id']),
            'fecha':         cab['fecha_liquidacion'].strftime('%Y-%m-%d %H:%M') if cab['fecha_liquidacion'] else '',
            'usuario':       cab['usuario_nombre'] or '',
            'observaciones': cab['observaciones'] or '',
        },
        'items': [{
            'codigo':         d['codigo'],
            'nombre':         d['nombre'],
            'cant_original':  float(d['cant_original']),
            'cant_entregada': float(d['cant_entregada']),
            'cant_devuelta':  float(d['cant_devuelta']),
            'cant_rotura':    float(d['cant_rotura']),
            'motivo':         d['motivo'] or '',
        } for d in det],
    })