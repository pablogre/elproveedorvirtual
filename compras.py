# -*- coding: utf-8 -*-
"""
Blueprint: Compras con Detalle (SCHIRO)
---------------------------------------
Carga de facturas de compra con detalle de artículos:
- Actualiza stock
- Actualiza costo (con IVA) aplicando prorrateo de flete/descuento
- Recalcula precios de venta (precio, precio2..5) según margenes
- Registra snapshot en producto_costo_historico para poder revertir
- Registra cabecera en factura_compra (reutiliza libro IVA, con con_detalle=1)
- Permite alta rápida de producto desde el mismo formulario
- Guarda código del proveedor en producto_proveedor
"""

from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, date

from extensions import db
from sqlalchemy import text, bindparam
from lector_factura import extraer_factura_proveedor, estimar_costo_usd

# Importar registrar_movimiento_stock (defensivo: stub si falla import)
try:
    from stock_audit import registrar_movimiento_stock
except Exception as _e_audit:
    print(f"⚠️ compras.py: no se pudo importar registrar_movimiento_stock ({_e_audit}). Auditoría desactivada.")
    def registrar_movimiento_stock(*args, **kwargs):
        pass

compras_bp = Blueprint('compras', __name__, url_prefix='/compras')


# =====================================================================
# HELPERS
# =====================================================================

def _d(v, default='0'):
    """Convierte a Decimal de forma segura."""
    if v is None or v == '':
        return Decimal(default)
    try:
        return Decimal(str(v))
    except Exception:
        return Decimal(default)


def _r2(v):
    """Redondea a 2 decimales."""
    return _d(v).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def _r3(v):
    """Redondea a 3 decimales (stock)."""
    return _d(v).quantize(Decimal('0.001'), rounding=ROUND_HALF_UP)


def _r4(v):
    """Redondea a 4 decimales (precios unitarios internos)."""
    return _d(v).quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)


def _es_admin():
    return session.get('rol') == 'admin'


def _usuario_id():
    return session.get('usuario_id') or session.get('user_id')


# =====================================================================
# LISTADO
# =====================================================================

@compras_bp.route('/')
def listado():
    proveedores = db.session.execute(
        text("SELECT id, razon_social FROM proveedor WHERE activo=1 ORDER BY razon_social")
    ).mappings().all()
    return render_template('compras_detalle_lista.html',
                           proveedores=proveedores,
                           es_admin=_es_admin())


@compras_bp.route('/api/listar')
def api_listar():
    prov = request.args.get('proveedor_id', type=int)
    desde = request.args.get('desde')
    hasta = request.args.get('hasta')

    sql = """
        SELECT fc.id, fc.fecha, fc.tipo_comprobante, fc.punto_venta, fc.numero,
               fc.neto_gravado_21, fc.iva_21, fc.neto_gravado_105, fc.iva_105,
               fc.neto_no_gravado, fc.descuento, fc.flete,
               fc.percepcion_iva, fc.percepcion_iibb, fc.percepcion_ganancias,
               fc.otros_impuestos, fc.total,
               p.razon_social AS proveedor,
               CASE
                   WHEN fc.punto_venta IS NULL OR fc.punto_venta = ''
                       THEN CONCAT(fc.tipo_comprobante, ' ', fc.numero)
                   ELSE CONCAT(fc.tipo_comprobante, ' ', fc.punto_venta, '-', fc.numero)
               END AS numero_completo
        FROM factura_compra fc
        JOIN proveedor p ON p.id = fc.proveedor_id
        WHERE fc.con_detalle = 1
    """
    params = {}
    if prov:
        sql += " AND fc.proveedor_id = :prov"
        params['prov'] = prov
    if desde:
        sql += " AND fc.fecha >= :desde"
        params['desde'] = desde
    if hasta:
        sql += " AND fc.fecha <= :hasta"
        params['hasta'] = hasta
    sql += " ORDER BY fc.fecha DESC, fc.id DESC"

    rows = db.session.execute(text(sql), params).mappings().all()
    facturas = []
    for r in rows:
        facturas.append({
            'id': r['id'],
            'fecha': r['fecha'].strftime('%Y-%m-%d') if r['fecha'] else '',
            'proveedor': r['proveedor'],
            'tipo_comprobante': r['tipo_comprobante'],
            'numero_completo': r['numero_completo'],
            'neto_21': float(r['neto_gravado_21'] or 0),
            'iva_21': float(r['iva_21'] or 0),
            'neto_105': float(r['neto_gravado_105'] or 0),
            'iva_105': float(r['iva_105'] or 0),
            'total': float(r['total'] or 0),
        })
    return jsonify(facturas)


# =====================================================================
# NUEVA FACTURA - PANTALLA
# =====================================================================

@compras_bp.route('/nueva')
def nueva():
    proveedores = db.session.execute(
        text("SELECT id, razon_social, condicion_iva FROM proveedor WHERE activo=1 ORDER BY razon_social")
    ).mappings().all()
    oc_id = request.args.get('oc_id', type=int)
    return render_template('compras_detalle_nueva.html',
                           proveedores=proveedores,
                           es_admin=_es_admin(),
                           oc_id=oc_id)


# =====================================================================
# BÚSQUEDA DE PRODUCTOS (por código interno, código de proveedor o nombre)
# =====================================================================

@compras_bp.route('/api/buscar_producto')
def api_buscar_producto():
    q = (request.args.get('q') or '').strip()
    proveedor_id = request.args.get('proveedor_id', type=int)
    if not q:
        return jsonify([])

    like = f"%{q}%"
    params = {'q': q, 'like': like}

    # Busca por código interno, nombre, código de barras o código del proveedor
    sql = """
        SELECT DISTINCT p.id, p.codigo, p.nombre, p.iva, p.stock, p.costo,
               p.margen, p.margen2, p.margen3, p.margen4, p.margen5,
               p.precio, p.precio2, p.precio3, p.precio4, p.precio5,
               p.es_combo,
               pp.codigo_proveedor
        FROM producto p
        LEFT JOIN producto_proveedor pp
               ON pp.producto_id = p.id
              AND pp.proveedor_id = :prov
        WHERE p.activo = 1
          AND (p.codigo = :q
               OR p.codigo LIKE :like
               OR p.nombre LIKE :like
               OR p.codigo_barras = :q
               OR EXISTS (
                    SELECT 1 FROM producto_proveedor pp2
                     WHERE pp2.producto_id = p.id
                       AND pp2.codigo_proveedor = :q
                 )
              )
        ORDER BY
          CASE WHEN p.codigo = :q THEN 0
               WHEN EXISTS (SELECT 1 FROM producto_proveedor pp3
                             WHERE pp3.producto_id = p.id
                               AND pp3.codigo_proveedor = :q) THEN 1
               ELSE 2
          END,
          p.nombre
        LIMIT 20
    """
    params['prov'] = proveedor_id or 0
    rows = db.session.execute(text(sql), params).mappings().all()

    productos = []
    for r in rows:
        productos.append({
            'id': r['id'],
            'codigo': r['codigo'],
            'nombre': r['nombre'],
            'iva': float(r['iva'] or 21),
            'stock': float(r['stock'] or 0),
            'costo': float(r['costo'] or 0),
            'margen': float(r['margen']) if r['margen'] is not None else None,
            'margen2': float(r['margen2']) if r['margen2'] is not None else None,
            'margen3': float(r['margen3']) if r['margen3'] is not None else None,
            'margen4': float(r['margen4']) if r['margen4'] is not None else None,
            'margen5': float(r['margen5']) if r['margen5'] is not None else None,
            'precio': float(r['precio'] or 0),
            'es_combo': bool(r['es_combo']),
            'codigo_proveedor': r['codigo_proveedor'] or '',
        })
    return jsonify(productos)


# =====================================================================
# ALTA RÁPIDA DE PRODUCTO
# =====================================================================

@compras_bp.route('/api/alta_rapida_producto', methods=['POST'])
def api_alta_rapida_producto():
    data = request.get_json() or {}
    codigo = (data.get('codigo') or '').strip()
    nombre = (data.get('nombre') or '').strip()
    iva = _d(data.get('iva', 21))
    margen = _d(data.get('margen', 0))
    codigo_proveedor = (data.get('codigo_proveedor') or '').strip()
    proveedor_id = data.get('proveedor_id')

    if not codigo or not nombre:
        return jsonify({'error': 'Código y nombre son obligatorios'}), 400

    # Validar que no exista
    existe = db.session.execute(
        text("SELECT id FROM producto WHERE codigo = :c"),
        {'c': codigo}
    ).first()
    if existe:
        return jsonify({'error': f'Ya existe un producto con código {codigo}'}), 400

    try:
        db.session.execute(text("""
            INSERT INTO producto (codigo, nombre, precio, stock, iva, activo, costo, margen)
            VALUES (:codigo, :nombre, 0, 0, :iva, 1, 0, :margen)
        """), {'codigo': codigo, 'nombre': nombre, 'iva': iva, 'margen': margen})

        nuevo_id = db.session.execute(text("SELECT LAST_INSERT_ID() AS id")).scalar()

        # Guardar código del proveedor si viene
        if codigo_proveedor and proveedor_id:
            db.session.execute(text("""
                INSERT INTO producto_proveedor (producto_id, proveedor_id, codigo_proveedor)
                VALUES (:pid, :prov, :cp)
                ON DUPLICATE KEY UPDATE codigo_proveedor = :cp
            """), {'pid': nuevo_id, 'prov': proveedor_id, 'cp': codigo_proveedor})

        db.session.commit()
        return jsonify({
            'id': nuevo_id,
            'codigo': codigo,
            'nombre': nombre,
            'iva': float(iva),
            'stock': 0.0,
            'costo': 0.0,
            'margen': float(margen),
            'margen2': None, 'margen3': None, 'margen4': None, 'margen5': None,
            'precio': 0.0,
            'es_combo': False,
            'codigo_proveedor': codigo_proveedor,
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al crear producto: {str(e)}'}), 500


# =====================================================================
# GUARDAR FACTURA CON DETALLE (TRANSACCIÓN ATÓMICA)
# =====================================================================

@compras_bp.route('/api/guardar', methods=['POST'])
def api_guardar():
    data = request.get_json() or {}

    # --- Cabecera ---
    proveedor_id = data.get('proveedor_id')
    fecha = data.get('fecha')
    tipo = (data.get('tipo_comprobante') or 'A').upper()
    # CI (Comprobante Interno) = recibo/remito/orden del proveedor que NO es factura oficial.
    # Numeración LIBRE (la tipea el usuario tal cual viene en el papel). NO se hace zfill.
    # No va al Libro IVA Compras, pero SÍ actualiza stock, costos, precios y cta cte.
    if tipo == 'CI':
        pv = (data.get('punto_venta') or '').strip()
        numero = (data.get('numero') or '').strip()
    else:
        pv = (data.get('punto_venta') or '').strip().zfill(5)
        numero = (data.get('numero') or '').strip().zfill(8)

    # --- OC vinculada (Fase 5): si viene, NO se suma stock y al final se marca la OC ---
    oc_id = data.get('oc_id')
    oc_row = None
    if oc_id:
        try:
            oc_id = int(oc_id)
        except (TypeError, ValueError):
            return jsonify({'error': 'oc_id inválido'}), 400

        oc_row = db.session.execute(text("""
            SELECT id, proveedor_id, estado, factura_compra_id
              FROM orden_compra WHERE id = :oc
        """), {'oc': oc_id}).mappings().first()

        if not oc_row:
            return jsonify({'error': f'OC #{oc_id} no encontrada'}), 404
        if oc_row['estado'] in ('borrador', 'enviada'):
            return jsonify({'error': f'La OC está en estado "{oc_row["estado"]}". Primero confirmar y recibir.'}), 400
        if oc_row['estado'] == 'cancelada':
            return jsonify({'error': 'La OC está cancelada.'}), 400
        if oc_row['estado'] == 'facturada' or oc_row['factura_compra_id']:
            return jsonify({'error': f'La OC ya fue facturada (factura #{oc_row["factura_compra_id"]}).'}), 400
        if str(oc_row['proveedor_id']) != str(proveedor_id):
            return jsonify({'error': 'El proveedor de la factura no coincide con el de la OC.'}), 400

    # Validación de obligatorios.
    # En A/B/C: proveedor, fecha, PV y número son obligatorios.
    # En CI (numeración libre): proveedor, fecha y número son obligatorios; el PV es opcional
    # (algunos remitos/recibos no tienen punto de venta).
    if not proveedor_id or not fecha or not numero:
        return jsonify({'error': 'Faltan datos de cabecera (proveedor, fecha o número)'}), 400
    if tipo != 'CI' and not pv:
        return jsonify({'error': 'Falta el Punto de Venta'}), 400

    # --- Chequeo amigable de duplicado ANTES de intentar el INSERT ---
    # La tabla tiene UNIQUE KEY (proveedor_id, tipo_comprobante, punto_venta, numero)
    # para evitar cargar dos veces la misma factura. En lugar de mostrar el error
    # técnico de SQLAlchemy/MySQL, devolvemos un mensaje claro al usuario.
    dup = db.session.execute(text("""
        SELECT fc.id, fc.fecha, fc.total, fc.con_detalle, p.razon_social
          FROM factura_compra fc
          JOIN proveedor p ON p.id = fc.proveedor_id
         WHERE fc.proveedor_id = :prov
           AND fc.tipo_comprobante = :tipo
           AND fc.punto_venta = :pv
           AND fc.numero = :numero
         LIMIT 1
    """), {
        'prov': proveedor_id, 'tipo': tipo, 'pv': pv, 'numero': numero
    }).mappings().first()
    if dup:
        fecha_str = dup['fecha'].strftime('%d/%m/%Y') if dup['fecha'] else '-'
        modulo = 'Compras con Detalle' if dup['con_detalle'] else 'Facturas sin Detalle'
        # Identificador legible: en CI puede no haber PV, en A/B/C siempre hay
        comprobante_str = f'{pv}-{numero}' if pv else numero
        if tipo == 'CI':
            msg = (
                f'⚠️ El comprobante interno {comprobante_str} de {dup["razon_social"]} '
                f'ya está cargado (#{dup["id"]}, fecha {fecha_str}, '
                f'total ${float(dup["total"]):,.2f}) en el módulo "{modulo}". '
                f'No se puede cargar dos veces el mismo comprobante.'
            )
        else:
            msg = (
                f'⚠️ La factura {tipo} {comprobante_str} de {dup["razon_social"]} '
                f'ya está cargada (#{dup["id"]}, fecha {fecha_str}, '
                f'total ${float(dup["total"]):,.2f}) en el módulo "{modulo}". '
                f'No se puede cargar dos veces el mismo comprobante.'
            )
        return jsonify({
            'error': msg,
            'duplicate': True,
            'factura_existente_id': dup['id']
        }), 409

    neto_21 = _r2(data.get('neto_21', 0))
    iva_21 = _r2(data.get('iva_21', 0))
    neto_105 = _r2(data.get('neto_105', 0))
    iva_105 = _r2(data.get('iva_105', 0))
    neto_no_grav = _r2(data.get('neto_no_gravado', 0))
    descuento = _r2(data.get('descuento', 0))
    flete = _r2(data.get('flete', 0))
    perc_iva = _r2(data.get('percepcion_iva', 0))
    perc_iibb = _r2(data.get('percepcion_iibb', 0))
    perc_gan = _r2(data.get('percepcion_ganancias', 0))
    otros = _r2(data.get('otros_impuestos', 0))
    total = _r2(data.get('total', 0))
    observaciones = (data.get('observaciones') or '').strip()

    items = data.get('items') or []
    if not items:
        return jsonify({'error': 'Debe cargar al menos un artículo'}), 400

    # --- Validar items y calcular prorrateo ---
    # Suma total con IVA de las líneas (para prorratear flete/descuento)
    # NOTA: el precio_unitario es el precio de lista del proveedor (sin IVA).
    # Si el item trae descuento_porcentaje (%), se aplica para obtener el precio NETO
    # con el que se calcula subtotal, IVA y costo final.
    subtotales_con_iva = []
    for it in items:
        pid = it.get('producto_id')
        cant = _r3(it.get('cantidad', 0))
        precio_u = _r4(it.get('precio_unitario', 0))
        desc_p = _d(it.get('descuento_porcentaje', 0))
        iva_p = _d(it.get('iva', 21))
        if not pid or cant <= 0 or precio_u <= 0:
            return jsonify({'error': 'Hay items con datos inválidos (cantidad o precio en cero)'}), 400
        if desc_p < 0 or desc_p >= 100:
            return jsonify({'error': f'Descuento inválido en item ({desc_p}%). Debe estar entre 0 y 99.99.'}), 400
        precio_neto = precio_u * (Decimal('1') - desc_p / Decimal('100'))
        subtotal_con_iva = (cant * precio_neto * (Decimal('1') + iva_p / Decimal('100')))
        subtotales_con_iva.append(subtotal_con_iva)

    suma_con_iva = sum(subtotales_con_iva) if subtotales_con_iva else Decimal('0')
    if suma_con_iva <= 0:
        return jsonify({'error': 'Suma de items en cero'}), 400

    # Factor de ajuste: positivo si hay flete, negativo si hay descuento
    ajuste_total = flete - descuento
    factor_ajuste = (ajuste_total / suma_con_iva) if suma_con_iva > 0 else Decimal('0')

    usuario_id = _usuario_id()

    # Clase de comprobante: si es CI lo marcamos como 'interno' para que QUEDE FUERA
    # del Libro IVA Compras. El resto del sistema (cta cte proveedor, stock, costos,
    # exportar Excel/PDF/Libro IVA Digital) ya filtra clase_comprobante='interno'.
    # Para tipos fiscales (A/B/C/M) queda como 'factura' (es el default histórico).
    clase = 'interno' if tipo == 'CI' else 'factura'

    try:
        # --- 1) Insertar cabecera ---
        db.session.execute(text("""
            INSERT INTO factura_compra
                (proveedor_id, fecha, tipo_comprobante, clase_comprobante, punto_venta, numero,
                 neto_gravado_21, iva_21, neto_gravado_105, iva_105,
                 neto_no_gravado, otros_impuestos, total, observaciones,
                 usuario_id, con_detalle,
                 descuento, flete, percepcion_iva, percepcion_iibb, percepcion_ganancias,
                 saldo_pendiente, estado)
            VALUES
                (:prov, :fecha, :tipo, :clase, :pv, :numero,
                 :n21, :i21, :n105, :i105,
                 :nng, :otros, :total, :obs,
                 :uid, 1,
                 :desc, :flete, :piva, :piibb, :pgan,
                 :total, 'pendiente')
        """), {
            'prov': proveedor_id, 'fecha': fecha, 'tipo': tipo, 'clase': clase, 'pv': pv, 'numero': numero,
            'n21': neto_21, 'i21': iva_21, 'n105': neto_105, 'i105': iva_105,
            'nng': neto_no_grav, 'otros': otros, 'total': total, 'obs': observaciones,
            'uid': usuario_id,
            'desc': descuento, 'flete': flete,
            'piva': perc_iva, 'piibb': perc_iibb, 'pgan': perc_gan
        })
        factura_id = db.session.execute(text("SELECT LAST_INSERT_ID() AS id")).scalar()

        # --- 2) Procesar cada item ---
        for idx, it in enumerate(items):
            pid = it['producto_id']
            cant = _r3(it.get('cantidad', 0))
            precio_u = _r4(it.get('precio_unitario', 0))  # precio de LISTA sin IVA (como figura en factura)
            desc_p = _d(it.get('descuento_porcentaje', 0))
            iva_p = _d(it.get('iva', 21))
            # Precio NETO unitario = precio de lista − descuento por línea
            precio_neto_u = _r4(precio_u * (Decimal('1') - desc_p / Decimal('100')))
            subtotal_sin_iva = _r2(cant * precio_neto_u)
            codigo_proveedor_it = (it.get('codigo_proveedor') or '').strip()

            # Traer producto actual (para snapshot y verificar)
            prod = db.session.execute(text("""
                SELECT id, codigo, nombre, stock, costo, margen, margen2, margen3, margen4, margen5,
                       precio, precio2, precio3, precio4, precio5, es_combo
                  FROM producto WHERE id = :pid FOR UPDATE
            """), {'pid': pid}).mappings().first()

            if not prod:
                raise Exception(f'Producto id={pid} no encontrado')
            if prod['es_combo']:
                raise Exception(f'El producto id={pid} es un combo, no se puede comprar')

            # Costo base con IVA + prorrateo (sobre el precio NETO con descuento aplicado)
            costo_base = precio_neto_u * (Decimal('1') + iva_p / Decimal('100'))
            costo_final = _r2(costo_base * (Decimal('1') + factor_ajuste))
            if costo_final <= 0:
                costo_final = _r2(costo_base)  # fallback por si el ajuste es muy negativo

            # Recalcular precios según margen guardado (solo si el margen no es NULL)
            def _calc_precio(costo, margen):
                if margen is None:
                    return None
                return _r2(costo * (Decimal('1') + _d(margen) / Decimal('100')))

            nuevo_precio = _calc_precio(costo_final, prod['margen'])
            nuevo_precio2 = _calc_precio(costo_final, prod['margen2'])
            nuevo_precio3 = _calc_precio(costo_final, prod['margen3'])
            nuevo_precio4 = _calc_precio(costo_final, prod['margen4'])
            nuevo_precio5 = _calc_precio(costo_final, prod['margen5'])

            # --- Snapshot al histórico ANTES de actualizar ---
            db.session.execute(text("""
                INSERT INTO producto_costo_historico
                    (producto_id, factura_compra_id,
                     costo_anterior, costo_nuevo,
                     margen_anterior, margen2_anterior, margen3_anterior,
                     margen4_anterior, margen5_anterior,
                     precio_anterior, precio2_anterior, precio3_anterior,
                     precio4_anterior, precio5_anterior,
                     stock_anterior, usuario_id, motivo)
                VALUES
                    (:pid, :fid,
                     :ca, :cn,
                     :ma, :ma2, :ma3, :ma4, :ma5,
                     :pa, :pa2, :pa3, :pa4, :pa5,
                     :sa, :uid, 'compra')
            """), {
                'pid': pid, 'fid': factura_id,
                'ca': prod['costo'], 'cn': costo_final,
                'ma': prod['margen'], 'ma2': prod['margen2'], 'ma3': prod['margen3'],
                'ma4': prod['margen4'], 'ma5': prod['margen5'],
                'pa': prod['precio'], 'pa2': prod['precio2'], 'pa3': prod['precio3'],
                'pa4': prod['precio4'], 'pa5': prod['precio5'],
                'sa': prod['stock'], 'uid': usuario_id
            })

            # --- Actualizar producto ---
            # Si la factura viene de una OC, el stock YA se sumó en la recepción,
            # por lo tanto NO se vuelve a sumar acá. En todos los demás casos sí se suma.
            if oc_id:
                db.session.execute(text("""
                    UPDATE producto
                       SET costo = :costo,
                           precio = COALESCE(:p1, precio),
                           precio2 = COALESCE(:p2, precio2),
                           precio3 = COALESCE(:p3, precio3),
                           precio4 = COALESCE(:p4, precio4),
                           precio5 = COALESCE(:p5, precio5),
                           fecha_actualizacion_precio = CURDATE()
                     WHERE id = :pid
                """), {
                    'costo': costo_final,
                    'p1': nuevo_precio, 'p2': nuevo_precio2, 'p3': nuevo_precio3,
                    'p4': nuevo_precio4, 'p5': nuevo_precio5,
                    'pid': pid
                })
            else:
                db.session.execute(text("""
                    UPDATE producto
                       SET stock = stock + :cant,
                           costo = :costo,
                           precio = COALESCE(:p1, precio),
                           precio2 = COALESCE(:p2, precio2),
                           precio3 = COALESCE(:p3, precio3),
                           precio4 = COALESCE(:p4, precio4),
                           precio5 = COALESCE(:p5, precio5),
                           fecha_actualizacion_precio = CURDATE()
                     WHERE id = :pid
                """), {
                    'cant': cant, 'costo': costo_final,
                    'p1': nuevo_precio, 'p2': nuevo_precio2, 'p3': nuevo_precio3,
                    'p4': nuevo_precio4, 'p5': nuevo_precio5,
                    'pid': pid
                })

                # ═══ AUDITORÍA: registrar entrada de stock por compra ═══
                stock_anterior_audit = float(prod['stock'])
                stock_nuevo_audit = stock_anterior_audit + float(cant)
                registrar_movimiento_stock(
                    db=db,
                    producto_id=pid,
                    tipo='compra',
                    cantidad=float(cant),
                    signo='+',
                    stock_anterior=stock_anterior_audit,
                    stock_nuevo=stock_nuevo_audit,
                    referencia_tipo='factura_compra',
                    referencia_id=factura_id,
                    motivo=f'Compra a proveedor (factura compra #{factura_id})',
                    usuario_id=usuario_id,
                    usuario_nombre=session.get('nombre', 'Sistema'),
                    codigo_producto=prod.get('codigo'),
                    nombre_producto=prod.get('nombre'),
                )

            # --- Detalle ---
            # precio_unitario = precio de LISTA s/IVA (como figura en factura)
            # descuento_porcentaje = % de bonificación aplicado a la línea
            # subtotal = cant * precio_unitario * (1 - desc/100), es decir el subtotal NETO
            db.session.execute(text("""
                INSERT INTO factura_compra_detalle
                    (factura_compra_id, producto_id, cantidad, precio_unitario, descuento_porcentaje,
                     iva, subtotal, costo_final_unitario)
                VALUES
                    (:fid, :pid, :cant, :pu, :desc, :iva, :sub, :cfu)
            """), {
                'fid': factura_id, 'pid': pid, 'cant': cant, 'pu': precio_u, 'desc': desc_p,
                'iva': iva_p, 'sub': subtotal_sin_iva, 'cfu': costo_final
            })

            # --- Código del proveedor para este producto (si vino cargado) ---
            if codigo_proveedor_it:
                db.session.execute(text("""
                    INSERT INTO producto_proveedor (producto_id, proveedor_id, codigo_proveedor)
                    VALUES (:pid, :prov, :cp)
                    ON DUPLICATE KEY UPDATE codigo_proveedor = :cp
                """), {'pid': pid, 'prov': proveedor_id, 'cp': codigo_proveedor_it})

        # --- 3) Actualizar saldo del proveedor ---
        db.session.execute(text("""
            UPDATE proveedor SET saldo = saldo + :total WHERE id = :pid
        """), {'total': total, 'pid': proveedor_id})

        # --- 4) Si viene de una OC, vincular factura y cambiar estado a 'facturada' ---
        if oc_id:
            db.session.execute(text("""
                UPDATE orden_compra
                   SET factura_compra_id = :fid,
                       estado = 'facturada'
                 WHERE id = :oc
            """), {'fid': factura_id, 'oc': oc_id})

        db.session.commit()
        return jsonify({
            'ok': True,
            'factura_id': factura_id,
            'oc_facturada': oc_id if oc_id else None,
        })

    except Exception as e:
        db.session.rollback()
        # Detectar si fue un error de duplicado (race condition: dos cargas
        # simultáneas, o INSERT directo a la API saltando el chequeo previo)
        msg = str(e)
        if '1062' in msg and 'Duplicate entry' in msg:
            comprobante_str = f'{pv}-{numero}' if pv else numero
            if tipo == 'CI':
                err_msg = (
                    f'⚠️ El comprobante interno {comprobante_str} ya está cargado en el sistema. '
                    f'No se puede cargar dos veces el mismo comprobante.'
                )
            else:
                err_msg = (
                    f'⚠️ La factura {tipo} {comprobante_str} ya está cargada en el sistema. '
                    f'No se puede cargar dos veces el mismo comprobante.'
                )
            return jsonify({
                'error': err_msg,
                'duplicate': True
            }), 409
        return jsonify({'error': f'Error al guardar: {str(e)}'}), 500


# =====================================================================
# VER FACTURA (pantalla HTML)
# =====================================================================

@compras_bp.route('/ver/<int:factura_id>')
def ver(factura_id):
    return render_template('compras_detalle_ver.html',
                           factura_id=factura_id,
                           es_admin=_es_admin())


# =====================================================================
# VER FACTURA (con detalle)
# =====================================================================

@compras_bp.route('/api/ver/<int:factura_id>')
def api_ver(factura_id):
    cab = db.session.execute(text("""
        SELECT fc.*, p.razon_social AS proveedor
          FROM factura_compra fc
          JOIN proveedor p ON p.id = fc.proveedor_id
         WHERE fc.id = :fid
    """), {'fid': factura_id}).mappings().first()
    if not cab:
        return jsonify({'error': 'Factura no encontrada'}), 404

    det = db.session.execute(text("""
        SELECT fcd.*, pr.codigo, pr.nombre
          FROM factura_compra_detalle fcd
          JOIN producto pr ON pr.id = fcd.producto_id
         WHERE fcd.factura_compra_id = :fid
         ORDER BY fcd.id
    """), {'fid': factura_id}).mappings().all()

    return jsonify({
        'cabecera': {
            'id': cab['id'],
            'fecha': cab['fecha'].strftime('%Y-%m-%d') if cab['fecha'] else '',
            'proveedor': cab['proveedor'],
            'proveedor_id': cab['proveedor_id'],
            'tipo_comprobante': cab['tipo_comprobante'],
            'punto_venta': cab['punto_venta'],
            'numero': cab['numero'],
            'neto_21': float(cab['neto_gravado_21'] or 0),
            'iva_21': float(cab['iva_21'] or 0),
            'neto_105': float(cab['neto_gravado_105'] or 0),
            'iva_105': float(cab['iva_105'] or 0),
            'neto_no_gravado': float(cab['neto_no_gravado'] or 0),
            'descuento': float(cab['descuento'] or 0),
            'flete': float(cab['flete'] or 0),
            'percepcion_iva': float(cab['percepcion_iva'] or 0),
            'percepcion_iibb': float(cab['percepcion_iibb'] or 0),
            'percepcion_ganancias': float(cab['percepcion_ganancias'] or 0),
            'otros_impuestos': float(cab['otros_impuestos'] or 0),
            'total': float(cab['total'] or 0),
            'observaciones': cab['observaciones'] or '',
        },
        'items': [{
            'codigo': r['codigo'],
            'nombre': r['nombre'],
            'cantidad': float(r['cantidad']),
            'precio_unitario': float(r['precio_unitario']),
            'descuento_porcentaje': float(r['descuento_porcentaje'] or 0),
            'iva': float(r['iva']),
            'subtotal': float(r['subtotal']),
            'costo_final_unitario': float(r['costo_final_unitario']),
        } for r in det]
    })


# =====================================================================
# GESTIÓN DE CÓDIGOS DE PRODUCTO POR PROVEEDOR
# =====================================================================

@compras_bp.route('/codigos_proveedor')
def codigos_proveedor():
    proveedores = db.session.execute(
        text("SELECT id, razon_social FROM proveedor WHERE activo=1 ORDER BY razon_social")
    ).mappings().all()
    return render_template('compras_codigos_proveedor.html',
                           proveedores=proveedores,
                           es_admin=_es_admin())


@compras_bp.route('/api/codigos_proveedor/<int:proveedor_id>')
def api_codigos_listar(proveedor_id):
    """Lista todos los códigos cargados para un proveedor."""
    rows = db.session.execute(text("""
        SELECT pp.id, pp.producto_id, pp.codigo_proveedor, pp.fecha_creacion,
               p.codigo AS codigo_interno, p.nombre, p.activo
          FROM producto_proveedor pp
          JOIN producto p ON p.id = pp.producto_id
         WHERE pp.proveedor_id = :prov
         ORDER BY p.nombre
    """), {'prov': proveedor_id}).mappings().all()

    return jsonify([{
        'id': r['id'],
        'producto_id': r['producto_id'],
        'codigo_interno': r['codigo_interno'],
        'nombre': r['nombre'],
        'codigo_proveedor': r['codigo_proveedor'],
        'activo': bool(r['activo']),
        'fecha_creacion': r['fecha_creacion'].strftime('%Y-%m-%d') if r['fecha_creacion'] else '',
    } for r in rows])


@compras_bp.route('/api/codigo_proveedor/guardar', methods=['POST'])
def api_codigo_proveedor_guardar():
    """Crea o actualiza un código de producto para un proveedor."""
    data = request.get_json() or {}
    producto_id = data.get('producto_id')
    proveedor_id = data.get('proveedor_id')
    codigo_proveedor = (data.get('codigo_proveedor') or '').strip()

    if not producto_id or not proveedor_id:
        return jsonify({'error': 'Falta producto o proveedor'}), 400
    if not codigo_proveedor:
        return jsonify({'error': 'El código del proveedor no puede estar vacío'}), 400

    try:
        db.session.execute(text("""
            INSERT INTO producto_proveedor (producto_id, proveedor_id, codigo_proveedor)
            VALUES (:pid, :prov, :cp)
            ON DUPLICATE KEY UPDATE codigo_proveedor = :cp
        """), {'pid': producto_id, 'prov': proveedor_id, 'cp': codigo_proveedor})
        db.session.commit()
        return jsonify({'ok': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@compras_bp.route('/api/codigo_proveedor/eliminar/<int:codigo_id>', methods=['POST'])
def api_codigo_proveedor_eliminar(codigo_id):
    """Elimina un código de proveedor (solo admin)."""
    if not _es_admin():
        return jsonify({'error': 'Solo el administrador puede eliminar códigos'}), 403
    try:
        db.session.execute(text("DELETE FROM producto_proveedor WHERE id = :id"), {'id': codigo_id})
        db.session.commit()
        return jsonify({'ok': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@compras_bp.route('/api/buscar_producto_abm')
def api_buscar_producto_abm():
    """Búsqueda simple de productos para agregar códigos (sin filtrar por proveedor)."""
    q = (request.args.get('q') or '').strip()
    if len(q) < 2:
        return jsonify([])
    like = f"%{q}%"
    rows = db.session.execute(text("""
        SELECT id, codigo, nombre
          FROM producto
         WHERE activo = 1
           AND (codigo = :q OR codigo LIKE :like OR nombre LIKE :like OR codigo_barras = :q)
           AND es_combo = 0
         ORDER BY nombre
         LIMIT 15
    """), {'q': q, 'like': like}).mappings().all()
    return jsonify([{'id': r['id'], 'codigo': r['codigo'], 'nombre': r['nombre']} for r in rows])


@compras_bp.route('/api/eliminar/<int:factura_id>', methods=['POST'])
def api_eliminar(factura_id):
    if not _es_admin():
        return jsonify({'error': 'Solo el administrador puede eliminar facturas de compra'}), 403

    cab = db.session.execute(
        text("SELECT * FROM factura_compra WHERE id = :fid AND con_detalle = 1"),
        {'fid': factura_id}
    ).mappings().first()
    if not cab:
        return jsonify({'error': 'Factura no encontrada o no tiene detalle'}), 404

    try:
        # Traer el histórico de esta factura (con los valores anteriores)
        historicos = db.session.execute(text("""
            SELECT * FROM producto_costo_historico
             WHERE factura_compra_id = :fid AND motivo = 'compra'
        """), {'fid': factura_id}).mappings().all()

        # Traer detalle (para revertir stock)
        detalle = db.session.execute(text("""
            SELECT producto_id, cantidad
              FROM factura_compra_detalle
             WHERE factura_compra_id = :fid
        """), {'fid': factura_id}).mappings().all()

        # Revertir stock
        for d in detalle:
            # ═══ AUDITORÍA: capturar stock anterior y datos del producto ANTES del UPDATE ═══
            prod_audit = db.session.execute(text("""
                SELECT codigo, nombre, stock FROM producto WHERE id = :pid
            """), {'pid': d['producto_id']}).mappings().first()

            db.session.execute(text("""
                UPDATE producto SET stock = stock - :cant WHERE id = :pid
            """), {'cant': d['cantidad'], 'pid': d['producto_id']})

            # ═══ AUDITORÍA: registrar la anulación ═══
            if prod_audit:
                stock_anterior_audit = float(prod_audit['stock'])
                stock_nuevo_audit = stock_anterior_audit - float(d['cantidad'])
                registrar_movimiento_stock(
                    db=db,
                    producto_id=d['producto_id'],
                    tipo='compra_anulada',
                    cantidad=float(d['cantidad']),
                    signo='-',
                    stock_anterior=stock_anterior_audit,
                    stock_nuevo=stock_nuevo_audit,
                    referencia_tipo='factura_compra',
                    referencia_id=factura_id,
                    motivo=f'Anulación factura compra #{factura_id}',
                    usuario_id=session.get('user_id'),
                    usuario_nombre=session.get('nombre', 'Sistema'),
                    codigo_producto=prod_audit.get('codigo'),
                    nombre_producto=prod_audit.get('nombre'),
                )

        # Restaurar costo/margenes/precios desde el histórico de ESTA factura
        for h in historicos:
            db.session.execute(text("""
                UPDATE producto
                   SET costo = :ca,
                       margen = :ma, margen2 = :ma2, margen3 = :ma3,
                       margen4 = :ma4, margen5 = :ma5,
                       precio = :pa, precio2 = :pa2, precio3 = :pa3,
                       precio4 = :pa4, precio5 = :pa5
                 WHERE id = :pid
            """), {
                'ca': h['costo_anterior'],
                'ma': h['margen_anterior'], 'ma2': h['margen2_anterior'],
                'ma3': h['margen3_anterior'], 'ma4': h['margen4_anterior'],
                'ma5': h['margen5_anterior'],
                'pa': h['precio_anterior'], 'pa2': h['precio2_anterior'],
                'pa3': h['precio3_anterior'], 'pa4': h['precio4_anterior'],
                'pa5': h['precio5_anterior'],
                'pid': h['producto_id']
            })

        # Registrar anulación en histórico (para trazabilidad)
        for h in historicos:
            db.session.execute(text("""
                INSERT INTO producto_costo_historico
                    (producto_id, factura_compra_id,
                     costo_anterior, costo_nuevo,
                     margen_anterior, margen2_anterior, margen3_anterior,
                     margen4_anterior, margen5_anterior,
                     precio_anterior, precio2_anterior, precio3_anterior,
                     precio4_anterior, precio5_anterior,
                     stock_anterior, usuario_id, motivo)
                VALUES
                    (:pid, NULL,
                     :cn, :ca,
                     :ma, :ma2, :ma3, :ma4, :ma5,
                     :pa, :pa2, :pa3, :pa4, :pa5,
                     NULL, :uid, 'anulacion')
            """), {
                'pid': h['producto_id'],
                'cn': h['costo_nuevo'], 'ca': h['costo_anterior'],
                'ma': h['margen_anterior'], 'ma2': h['margen2_anterior'],
                'ma3': h['margen3_anterior'], 'ma4': h['margen4_anterior'],
                'ma5': h['margen5_anterior'],
                'pa': h['precio_anterior'], 'pa2': h['precio2_anterior'],
                'pa3': h['precio3_anterior'], 'pa4': h['precio4_anterior'],
                'pa5': h['precio5_anterior'],
                'uid': _usuario_id()
            })

        # Revertir saldo del proveedor
        db.session.execute(text("""
            UPDATE proveedor SET saldo = saldo - :total WHERE id = :pid
        """), {'total': cab['total'], 'pid': cab['proveedor_id']})

        # Borrar detalle (ON DELETE CASCADE lo haría, pero explícito para claridad)
        db.session.execute(text("""
            DELETE FROM factura_compra_detalle WHERE factura_compra_id = :fid
        """), {'fid': factura_id})

        # Borrar cabecera
        db.session.execute(text("""
            DELETE FROM factura_compra WHERE id = :fid
        """), {'fid': factura_id})

        db.session.commit()
        return jsonify({'ok': True})

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al eliminar: {str(e)}'}), 500


@compras_bp.route('/api/extraer_factura_ocr', methods=['POST'])
def api_extraer_factura_ocr():
    """
    Recibe una imagen o PDF de factura de proveedor y devuelve JSON
    con los datos extraídos por Claude Vision.
    """
    # Control de sesión
    if not _usuario_id():
        return jsonify({'success': False, 'error': 'No autenticado'}), 401

    # Validar que vino el archivo
    if 'archivo' not in request.files:
        return jsonify({'success': False, 'error': 'No se envió archivo'}), 400

    archivo = request.files['archivo']
    if not archivo or not archivo.filename:
        return jsonify({'success': False, 'error': 'Archivo vacío'}), 400

    # Validar tipo
    content_type = archivo.content_type or 'application/octet-stream'
    tipos_ok = ('image/jpeg', 'image/jpg', 'image/png', 'image/webp', 'application/pdf')
    if content_type not in tipos_ok:
        return jsonify({
            'success': False,
            'error': f'Tipo no soportado: {content_type}. Usar JPG, PNG, WebP o PDF.'
        }), 400

    # Validar tamaño (10MB max)
    imagen_bytes = archivo.read()
    if len(imagen_bytes) > 10 * 1024 * 1024:
        return jsonify({
            'success': False,
            'error': 'Archivo supera 10MB. Reducir calidad de imagen.'
        }), 400

    # Procesar con Claude Vision
    resultado = extraer_factura_proveedor(imagen_bytes, content_type)

    if not resultado['success']:
        return jsonify({
            'success': False,
            'error': resultado.get('error', 'Error desconocido'),
        }), 500

    # Agregar costo al response
    resultado['costo_usd'] = estimar_costo_usd(resultado.get('tokens_usados', {}))

    return jsonify(resultado), 200

# =====================================================================
# ACTUALIZACIÓN MASIVA DE COSTOS
# =====================================================================
# Permite aplicar +%, -% o costo absoluto a todos los productos filtrados
# por proveedor (habitual o última compra) y/o categoría.
# Recálculo de las 5 listas de precios opcional.
# Snapshot completo en producto_costo_historico (motivo='actualizacion_masiva').
#
# IMPORTANTE: NUNCA actualiza combos (es_combo=1), porque sus precios
# salen del recálculo de los productos base.
# =====================================================================

def _calc_precio_masivo(costo, margen):
    """Calcula precio = costo * (1 + margen/100). Si margen es None, devuelve None.
    Reutilizado del flujo de carga de factura para mantener consistencia."""
    if margen is None:
        return None
    return _r2(_d(costo) * (Decimal('1') + _d(margen) / Decimal('100')))


@compras_bp.route('/actualizacion_masiva_costos')
def actualizacion_masiva_costos():
    """Pantalla de actualización masiva de costos. Solo admin."""
    if not _es_admin():
        return "Acceso denegado: solo administradores pueden actualizar costos masivamente.", 403

    proveedores = db.session.execute(
        text("SELECT id, razon_social FROM proveedor WHERE activo=1 ORDER BY razon_social")
    ).mappings().all()

    categorias = db.session.execute(
        text("""SELECT DISTINCT categoria FROM producto
                 WHERE categoria IS NOT NULL AND categoria <> ''
                 ORDER BY categoria""")
    ).mappings().all()

    return render_template('compras_actualizacion_masiva.html',
                           proveedores=proveedores,
                           categorias=categorias,
                           es_admin=_es_admin())


@compras_bp.route('/api/actualizacion_masiva/buscar', methods=['POST'])
def actualizacion_masiva_buscar():
    """Devuelve productos que coinciden con los filtros del paso 1.

    El proveedor de cada producto se deduce SIEMPRE de su última factura de
    compra (tabla factura_compra_detalle + factura_compra). Los productos que
    nunca fueron comprados no tienen proveedor asignado y se manejan según
    los filtros (si no hay filtro de proveedor, igual aparecen)."""
    if not _es_admin():
        return jsonify({'error': 'Solo administradores'}), 403

    data = request.get_json() or {}
    proveedor_id = data.get('proveedor_id')
    categoria = (data.get('categoria') or '').strip() or None
    solo_activos = bool(data.get('solo_activos', True))

    # WHERE base
    where = ["p.es_combo = 0"]  # NUNCA combos
    params = {}

    if solo_activos:
        where.append("p.activo = 1")

    if categoria:
        where.append("p.categoria = :cat")
        params['cat'] = categoria

    # Si filtra por proveedor: INNER JOIN con la última factura de compra de ese proveedor
    # Si NO filtra por proveedor: LEFT JOIN para mostrar el último proveedor (si existe)
    if proveedor_id:
        join_proveedor = """
            INNER JOIN (
                SELECT fcd.producto_id, MAX(fc.fecha) AS ultima_fecha
                  FROM factura_compra_detalle fcd
                  JOIN factura_compra fc ON fc.id = fcd.factura_compra_id
                 GROUP BY fcd.producto_id
            ) ult ON ult.producto_id = p.id
            INNER JOIN factura_compra_detalle fcd2 ON fcd2.producto_id = p.id
            INNER JOIN factura_compra fc2 ON fc2.id = fcd2.factura_compra_id
                   AND fc2.fecha = ult.ultima_fecha
            INNER JOIN proveedor pr ON pr.id = fc2.proveedor_id AND pr.id = :prov_id
        """
        params['prov_id'] = proveedor_id
    else:
        join_proveedor = """
            LEFT JOIN (
                SELECT fcd.producto_id, MAX(fc.fecha) AS ultima_fecha
                  FROM factura_compra_detalle fcd
                  JOIN factura_compra fc ON fc.id = fcd.factura_compra_id
                 GROUP BY fcd.producto_id
            ) ult ON ult.producto_id = p.id
            LEFT JOIN factura_compra_detalle fcd2 ON fcd2.producto_id = p.id
                   AND fcd2.factura_compra_id IN (
                       SELECT id FROM factura_compra
                        WHERE id = fcd2.factura_compra_id AND fecha = ult.ultima_fecha
                   )
            LEFT JOIN factura_compra fc2 ON fc2.id = fcd2.factura_compra_id
            LEFT JOIN proveedor pr ON pr.id = fc2.proveedor_id
        """

    sql = f"""
        SELECT DISTINCT
               p.id, p.codigo, p.nombre, p.categoria, p.stock,
               p.costo, p.margen, p.margen2, p.margen3, p.margen4, p.margen5,
               p.precio, p.precio2, p.precio3, p.precio4, p.precio5,
               pr.razon_social AS proveedor_nombre
          FROM producto p
          {join_proveedor}
         WHERE {' AND '.join(where)}
         ORDER BY p.nombre
         LIMIT 2000
    """

    productos = db.session.execute(text(sql), params).mappings().all()

    return jsonify({
        'productos': [{
            'id': r['id'],
            'codigo': r['codigo'],
            'nombre': r['nombre'],
            'categoria': r['categoria'] or '',
            'proveedor_nombre': r['proveedor_nombre'] or '',
            'stock': float(r['stock'] or 0),
            'costo': float(r['costo'] or 0),
            'margen': float(r['margen']) if r['margen'] is not None else None,
            'margen2': float(r['margen2']) if r['margen2'] is not None else None,
            'margen3': float(r['margen3']) if r['margen3'] is not None else None,
            'margen4': float(r['margen4']) if r['margen4'] is not None else None,
            'margen5': float(r['margen5']) if r['margen5'] is not None else None,
            'precio': float(r['precio'] or 0),
            'precio2': float(r['precio2']) if r['precio2'] is not None else None,
            'precio3': float(r['precio3']) if r['precio3'] is not None else None,
            'precio4': float(r['precio4']) if r['precio4'] is not None else None,
            'precio5': float(r['precio5']) if r['precio5'] is not None else None,
        } for r in productos],
    })


@compras_bp.route('/api/actualizacion_masiva/aplicar', methods=['POST'])
def actualizacion_masiva_aplicar():
    """Aplica el cambio de costo a los productos seleccionados.
    Transacción atómica: si falla algo en cualquier producto, rollback completo.
    Snapshot en producto_costo_historico antes de cada UPDATE."""
    if not _es_admin():
        return jsonify({'error': 'Solo administradores'}), 403

    data = request.get_json() or {}
    producto_ids = data.get('producto_ids') or []
    tipo_op = data.get('tipo_op')  # 'aumento', 'descuento', 'absoluto'
    valor = data.get('valor')
    recalcular_precios = bool(data.get('recalcular_precios', False))

    # Validaciones
    if not producto_ids:
        return jsonify({'error': 'No hay productos seleccionados'}), 400
    if tipo_op not in ('aumento', 'descuento', 'absoluto'):
        return jsonify({'error': 'Tipo de operación inválido'}), 400
    try:
        valor_d = _d(valor)
    except Exception:
        return jsonify({'error': 'Valor inválido'}), 400
    if valor_d <= 0:
        return jsonify({'error': 'El valor debe ser mayor a 0'}), 400
    if tipo_op in ('aumento', 'descuento') and valor_d >= 100 and tipo_op == 'descuento':
        return jsonify({'error': 'El descuento debe ser menor a 100%'}), 400
    if len(producto_ids) > 2000:
        return jsonify({'error': 'Máximo 2000 productos por operación'}), 400

    usuario_id = _usuario_id()

    try:
        actualizados = 0
        errores = []

        # Lockear productos y obtener snapshot
        sql_select = """
            SELECT id, codigo, nombre, costo, stock,
                   margen, margen2, margen3, margen4, margen5,
                   precio, precio2, precio3, precio4, precio5
              FROM producto
             WHERE id IN :ids
               AND es_combo = 0
             FOR UPDATE
        """
        productos = db.session.execute(
            text(sql_select).bindparams(bindparam('ids', expanding=True)),
            {'ids': list(producto_ids)}
        ).mappings().all()

        if not productos:
            return jsonify({'error': 'No se encontraron productos válidos'}), 400

        for prod in productos:
            costo_anterior = _d(prod['costo'] or 0)

            # Calcular nuevo costo según tipo de operación
            if tipo_op == 'aumento':
                costo_nuevo = _r2(costo_anterior * (Decimal('1') + valor_d / Decimal('100')))
            elif tipo_op == 'descuento':
                costo_nuevo = _r2(costo_anterior * (Decimal('1') - valor_d / Decimal('100')))
            else:  # absoluto
                costo_nuevo = _r2(valor_d)

            if costo_nuevo <= 0:
                errores.append(f"Producto {prod['codigo']}: costo nuevo sería <= 0, omitido")
                continue

            # Recalcular precios si corresponde
            if recalcular_precios:
                nuevo_precio = _calc_precio_masivo(costo_nuevo, prod['margen'])
                nuevo_precio2 = _calc_precio_masivo(costo_nuevo, prod['margen2'])
                nuevo_precio3 = _calc_precio_masivo(costo_nuevo, prod['margen3'])
                nuevo_precio4 = _calc_precio_masivo(costo_nuevo, prod['margen4'])
                nuevo_precio5 = _calc_precio_masivo(costo_nuevo, prod['margen5'])
            else:
                nuevo_precio = nuevo_precio2 = nuevo_precio3 = nuevo_precio4 = nuevo_precio5 = None

            # Snapshot al histórico ANTES de actualizar
            db.session.execute(text("""
                INSERT INTO producto_costo_historico
                    (producto_id, factura_compra_id,
                     costo_anterior, costo_nuevo,
                     margen_anterior, margen2_anterior, margen3_anterior,
                     margen4_anterior, margen5_anterior,
                     precio_anterior, precio2_anterior, precio3_anterior,
                     precio4_anterior, precio5_anterior,
                     stock_anterior, usuario_id, motivo)
                VALUES
                    (:pid, NULL,
                     :ca, :cn,
                     :ma, :ma2, :ma3, :ma4, :ma5,
                     :pa, :pa2, :pa3, :pa4, :pa5,
                     :sa, :uid, 'actualizacion_masiva')
            """), {
                'pid': prod['id'],
                'ca': costo_anterior, 'cn': costo_nuevo,
                'ma': prod['margen'], 'ma2': prod['margen2'], 'ma3': prod['margen3'],
                'ma4': prod['margen4'], 'ma5': prod['margen5'],
                'pa': prod['precio'], 'pa2': prod['precio2'], 'pa3': prod['precio3'],
                'pa4': prod['precio4'], 'pa5': prod['precio5'],
                'sa': prod['stock'], 'uid': usuario_id
            })

            # Actualizar producto: costo siempre, precios solo si recalcular_precios=True
            if recalcular_precios:
                db.session.execute(text("""
                    UPDATE producto
                       SET costo = :costo,
                           precio = COALESCE(:p1, precio),
                           precio2 = COALESCE(:p2, precio2),
                           precio3 = COALESCE(:p3, precio3),
                           precio4 = COALESCE(:p4, precio4),
                           precio5 = COALESCE(:p5, precio5),
                           fecha_actualizacion_precio = CURDATE()
                     WHERE id = :pid
                """), {
                    'costo': costo_nuevo,
                    'p1': nuevo_precio, 'p2': nuevo_precio2, 'p3': nuevo_precio3,
                    'p4': nuevo_precio4, 'p5': nuevo_precio5,
                    'pid': prod['id']
                })
            else:
                # Solo actualizar costo (precios congelados)
                db.session.execute(text("""
                    UPDATE producto
                       SET costo = :costo
                     WHERE id = :pid
                """), {'costo': costo_nuevo, 'pid': prod['id']})

            actualizados += 1

        db.session.commit()

        return jsonify({
            'success': True,
            'actualizados': actualizados,
            'errores': errores,
            'mensaje': f'Se actualizaron {actualizados} productos correctamente.'
                       + (f' ({len(errores)} omitidos por errores)' if errores else '')
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al aplicar cambios: {str(e)}'}), 500