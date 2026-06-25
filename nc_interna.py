# -*- coding: utf-8 -*-
"""
nc_interna.py — Nota de Crédito INTERNA (parcial o total) sobre Comprobantes Internos.

Para cuando un cliente DEVUELVE mercadería de un comprobante interno (tipo 99,
no fiscal). NO toca AFIP. Por cada devolución:
  - registra una NC interna (tabla notas_credito, estado='interno', sin CAE),
    X-numerada como  PV-NCX0000001
  - reintegra el stock de lo devuelto
  - si el interno fue a CUENTA CORRIENTE, baja la deuda del cliente insertando
    una línea 'nota_credito' (Haber) por el monto devuelto — mismo criterio que
    la NC fiscal (la fórmula de saldo resta tipo='nota_credito').
  - si el interno fue al CONTADO (sin movimiento en cta cte) NO toca deuda:
    solo stock + registro.

Registro en app.py (después de definir los modelos, junto a init_estadisticas):

    from nc_interna import init_nc_interna
    init_nc_interna(app, db, Factura, DetalleFactura, NotaCredito,
                    DetalleNotaCredito, Producto, registrar_movimiento_stock)

Requisitos de BD ya presentes en esta instalación:
  - notas_credito.estado admite 'interno' (es VARCHAR, no ENUM -> OK)
  - cta_cte_movimiento.tipo admite 'nota_credito' (ya agregado por ALTER)
"""

from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from sqlalchemy import text
from datetime import datetime
from decimal import Decimal

nc_interna_bp = Blueprint('nc_interna', __name__)

_db = None
_Factura = None
_DetalleFactura = None
_NotaCredito = None
_DetalleNotaCredito = None
_Producto = None
_registrar_mov_stock = None


def init_nc_interna(app, db, Factura, DetalleFactura, NotaCredito,
                    DetalleNotaCredito, Producto, registrar_movimiento_stock=None):
    global _db, _Factura, _DetalleFactura, _NotaCredito, _DetalleNotaCredito
    global _Producto, _registrar_mov_stock
    _db = db
    _Factura = Factura
    _DetalleFactura = DetalleFactura
    _NotaCredito = NotaCredito
    _DetalleNotaCredito = DetalleNotaCredito
    _Producto = Producto
    _registrar_mov_stock = registrar_movimiento_stock
    app.register_blueprint(nc_interna_bp)
    print("[OK] NC Interna inicializada (devoluciones parciales de internos)")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _ya_devuelto_por_producto(interno_id):
    """{producto_id: cantidad ya devuelta} por NC internas previas de este interno."""
    rows = _db.session.execute(text("""
        SELECT dnc.producto_id AS pid, COALESCE(SUM(dnc.cantidad), 0) AS dev
        FROM detalle_nota_credito dnc
        JOIN notas_credito nc ON nc.id = dnc.nota_credito_id
        WHERE nc.factura_id = :fid AND nc.estado = 'interno'
        GROUP BY dnc.producto_id
    """), {'fid': interno_id}).fetchall()
    return {r.pid: float(r.dev or 0) for r in rows}


def _iva_pct_de(d):
    try:
        if d.porcentaje_iva is not None:
            return float(d.porcentaje_iva)
    except Exception:
        pass
    try:
        return float(d.producto.iva) if d.producto else 21.0
    except Exception:
        return 21.0


# ---------------------------------------------------------------------------
# Pantalla
# ---------------------------------------------------------------------------
@nc_interna_bp.route('/nc_interna')
def nc_interna_page():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('nc_interna.html')


# ---------------------------------------------------------------------------
# Buscar interno por número y devolver sus líneas con lo devolvible
# ---------------------------------------------------------------------------
@nc_interna_bp.route('/api/nc_interna/buscar')
def nc_interna_buscar():
    if 'user_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    try:
        numero = (request.args.get('numero') or '').strip()
        if not numero:
            return jsonify({'success': False, 'error': 'Ingresá un número de comprobante'}), 400

        interno = _Factura.query.filter_by(numero=numero, tipo_comprobante='99').first()
        if not interno:
            return jsonify({'success': False, 'error': f'No se encontró el comprobante interno {numero}'}), 404
        if interno.estado == 'anulada':
            return jsonify({'success': False, 'error': 'El comprobante está anulado'}), 400

        # ¿Fue a cuenta corriente? (existe movimiento venta_fiada de este interno)
        en_cta_cte = (_db.session.execute(text("""
            SELECT COUNT(*) FROM cta_cte_movimiento
            WHERE factura_id = :fid AND tipo = 'venta_fiada'
        """), {'fid': interno.id}).scalar() or 0) > 0

        detalles = _DetalleFactura.query.filter_by(factura_id=interno.id).all()
        ya_pool = _ya_devuelto_por_producto(interno.id)

        lineas = []
        for d in detalles:
            pid = d.producto_id
            orig = float(d.cantidad or 0)
            consumido = min(ya_pool.get(pid, 0.0), orig)
            ya_pool[pid] = ya_pool.get(pid, 0.0) - consumido
            devolvible = round(orig - consumido, 3)
            lineas.append({
                'detalle_id':      d.id,
                'producto_id':     pid,
                'codigo':          d.producto.codigo if d.producto else '',
                'nombre':          d.producto.nombre if d.producto else f'Producto #{pid}',
                'cantidad':        orig,
                'ya_devuelto':     round(consumido, 3),
                'devolvible':      devolvible,
                'precio_unitario': float(d.precio_unitario or 0),
                'porcentaje_iva':  _iva_pct_de(d),
            })

        cliente = interno.cliente
        return jsonify({
            'success': True,
            'interno': {
                'id':       interno.id,
                'numero':   interno.numero,
                'fecha':    interno.fecha.strftime('%d/%m/%Y') if interno.fecha else '',
                'cliente':  cliente.nombre if cliente else 'Consumidor Final',
                'total':    float(interno.total or 0),
                'en_cta_cte': en_cta_cte,
            },
            'lineas': lineas,
        })
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


# ---------------------------------------------------------------------------
# Emitir la NC interna (parcial o total)
# ---------------------------------------------------------------------------
@nc_interna_bp.route('/api/nc_interna/emitir/<int:interno_id>', methods=['POST'])
def nc_interna_emitir(interno_id):
    if 'user_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    try:
        interno = _Factura.query.get_or_404(interno_id)
        if interno.tipo_comprobante != '99':
            return jsonify({'success': False, 'error': 'Solo aplica a comprobantes internos (tipo 99)'}), 400
        if interno.estado == 'anulada':
            return jsonify({'success': False, 'error': 'El comprobante está anulado'}), 400

        data = request.json or {}
        motivo = (data.get('motivo') or 'Devolución de mercadería').strip()
        lineas_in = data.get('lineas') or []
        # Normalizar: {detalle_id: cantidad} con cantidad > 0
        pedido = {}
        for l in lineas_in:
            try:
                did = int(l.get('detalle_id'))
                cant = float(l.get('cantidad') or 0)
            except (TypeError, ValueError):
                continue
            if cant > 0:
                pedido[did] = pedido.get(did, 0.0) + cant
        if not pedido:
            return jsonify({'success': False, 'error': 'No indicaste ninguna cantidad a devolver'}), 400

        # Traer las líneas pedidas y validar que pertenecen al interno
        detalles = _DetalleFactura.query.filter(
            _DetalleFactura.id.in_(list(pedido.keys())),
            _DetalleFactura.factura_id == interno.id
        ).all()
        if len(detalles) != len(pedido):
            return jsonify({'success': False, 'error': 'Hay líneas que no pertenecen a este comprobante'}), 400

        # Validar cantidades: por línea (<= vendida) y por producto (<= vendido - ya devuelto)
        ya = _ya_devuelto_por_producto(interno.id)
        orig_por_prod, pedido_por_prod = {}, {}
        todas_lineas = _DetalleFactura.query.filter_by(factura_id=interno.id).all()
        for d in todas_lineas:
            orig_por_prod[d.producto_id] = orig_por_prod.get(d.producto_id, 0.0) + float(d.cantidad or 0)

        for d in detalles:
            cant = pedido[d.id]
            if cant > float(d.cantidad or 0) + 1e-6:
                return jsonify({'success': False,
                                'error': f'Línea {d.producto.nombre if d.producto else d.id}: '
                                         f'no podés devolver más de {float(d.cantidad)} (vendido)'}), 400
            pedido_por_prod[d.producto_id] = pedido_por_prod.get(d.producto_id, 0.0) + cant

        for pid, ped in pedido_por_prod.items():
            disponible = orig_por_prod.get(pid, 0.0) - ya.get(pid, 0.0)
            if ped > disponible + 1e-6:
                return jsonify({'success': False,
                                'error': f'Te quedan {round(disponible, 3)} unidades devolvibles de un producto; '
                                         f'pediste {round(ped, 3)}'}), 400

        # Totales de la NC (solo lo devuelto)
        subtotal_nc, iva_nc = 0.0, 0.0
        lineas_nc = []
        for d in detalles:
            cant = pedido[d.id]
            pu = float(d.precio_unitario or 0)
            pct = _iva_pct_de(d)
            sub = round(pu * cant, 2)
            iva = round(sub * pct / 100, 2)
            subtotal_nc += sub
            iva_nc += iva
            lineas_nc.append({'d': d, 'cant': cant, 'pu': pu, 'pct': pct, 'sub': sub, 'iva': iva})
        subtotal_nc = round(subtotal_nc, 2)
        iva_nc = round(iva_nc, 2)
        total_nc = round(subtotal_nc + iva_nc, 2)
        if total_nc <= 0:
            return jsonify({'success': False, 'error': 'El total de la devolución es 0'}), 400

        pv = int(interno.punto_venta or 1)

        # Numeración X de la NC interna: PV-NCX0000001 (única)
        n = int(_db.session.execute(text("""
            SELECT COALESCE(MAX(CAST(SUBSTRING_INDEX(numero, 'NCX', -1) AS UNSIGNED)), 0)
            FROM notas_credito WHERE numero LIKE :pat
        """), {'pat': f'{pv:04d}-NCX%'}).scalar() or 0) + 1
        numero_nc = f'{pv:04d}-NCX{n:07d}'
        while _NotaCredito.query.filter_by(numero=numero_nc).first():
            n += 1
            numero_nc = f'{pv:04d}-NCX{n:07d}'

        # 1) Cabecera NC interna
        nc = _NotaCredito(
            numero=numero_nc,
            tipo_comprobante='99',          # interno (no fiscal)
            punto_venta=pv,
            fecha=datetime.now(),
            factura_id=interno.id,
            factura_numero=interno.numero,
            cliente_id=interno.cliente_id,
            usuario_id=session['user_id'],
            subtotal=Decimal(str(subtotal_nc)),
            iva=Decimal(str(iva_nc)),
            total=Decimal(str(total_nc)),
            estado='interno',              # <- NO fiscal, sin CAE
            cae=None,
            vto_cae=None,
            motivo=f'[NC INTERNA] {motivo}',
            fecha_creacion=datetime.now(),
        )
        _db.session.add(nc)
        _db.session.flush()  # nc.id

        # 2) Detalle + reintegro de stock
        for ln in lineas_nc:
            d = ln['d']
            _db.session.add(_DetalleNotaCredito(
                nota_credito_id=nc.id,
                producto_id=d.producto_id,
                cantidad=Decimal(str(ln['cant'])),
                precio_unitario=Decimal(str(ln['pu'])),
                subtotal=Decimal(str(ln['sub'])),
                porcentaje_iva=Decimal(str(ln['pct'])),
                importe_iva=Decimal(str(ln['iva'])),
            ))

            prod = _Producto.query.get(d.producto_id)
            if prod is not None:
                stock_ant = float(prod.stock or 0)
                prod.stock = stock_ant + ln['cant']
                if _registrar_mov_stock:
                    try:
                        _registrar_mov_stock(
                            db=_db, producto_id=prod.id, tipo='devolucion_interno',
                            cantidad=float(ln['cant']), signo='+',
                            stock_anterior=stock_ant, stock_nuevo=float(prod.stock),
                            referencia_tipo='nota_credito', referencia_id=nc.id,
                            motivo=f'NC interna {numero_nc} s/ {interno.numero} - {motivo}',
                            usuario_id=session.get('user_id'),
                            usuario_nombre=session.get('nombre', 'Sistema'),
                            codigo_producto=prod.codigo, nombre_producto=prod.nombre,
                        )
                    except Exception as e_audit:
                        print(f"[WARN] auditoría stock NC interna: {e_audit}")

        # 3) Cuenta corriente: solo si el interno fue a cta cte (tenía venta_fiada).
        #    Se inserta una línea 'nota_credito' (Haber) por el total devuelto,
        #    igual que la NC fiscal: la fórmula de saldo resta tipo='nota_credito'.
        tiene_cc = (_db.session.execute(text("""
            SELECT COUNT(*) FROM cta_cte_movimiento
            WHERE factura_id = :fid AND tipo = 'venta_fiada'
        """), {'fid': interno.id}).scalar() or 0) > 0

        if tiene_cc:
            _db.session.execute(text("""
                INSERT INTO cta_cte_movimiento
                    (cliente_id, fecha, tipo, tipo_mov, estado, monto_total,
                     saldo_pendiente, factura_id, usuario_id, numero_comprobante, observaciones)
                VALUES
                    (:cliente_id, NOW(), 'nota_credito', 'pago', 'pagado', :monto,
                     0.00, :factura_id, :usuario_id, :nc_numero, :obs)
            """), {
                'cliente_id': interno.cliente_id,
                'monto':      total_nc,
                'factura_id': interno.id,
                'usuario_id': session['user_id'],
                'nc_numero':  numero_nc,
                'obs':        f'NC interna {numero_nc} s/ {interno.numero} (devolución)',
            })

        _db.session.commit()

        return jsonify({
            'success': True,
            'message': f'NC interna {numero_nc} emitida' + (' y descontada de cuenta corriente' if tiene_cc else ''),
            'numero_nc': numero_nc,
            'total': total_nc,
            'en_cta_cte': tiene_cc,
            'lineas': len(lineas_nc),
        })

    except Exception as e:
        _db.session.rollback()
        import traceback; traceback.print_exc()
        return jsonify({'success': False, 'error': f'Error al emitir NC interna: {str(e)}'}), 500
