# -*- coding: utf-8 -*-
"""
reporte_vendedores.py — Informe de ventas por vendedor.

El vendedor está asignado en el cliente (cliente.vendedor_id), así que el
informe agrupa las ventas (factura -> cliente -> vendedor) por vendedor,
con filtro de fechas desde/hasta y opción de TODOS los vendedores o uno solo.

Se excluyen las anuladas (estado <> 'anulada'); cuentan autorizadas,
error_afip e internos (mismo criterio que tus estadísticas).

Registro en app.py (junto a init_estadisticas / init_nc_interna):

    from reporte_vendedores import init_reporte_vendedores
    init_reporte_vendedores(app, db)
"""

from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from sqlalchemy import text
from datetime import date

reporte_vendedores_bp = Blueprint('reporte_vendedores', __name__)
_db = None


def init_reporte_vendedores(app, db):
    global _db
    _db = db
    app.register_blueprint(reporte_vendedores_bp)
    print("[OK] Reporte de ventas por vendedor inicializado")


def _filtro_vendedor(vendedor_id):
    """Devuelve (clausula_sql, params_extra) según el selector."""
    v = (vendedor_id or '').strip().lower()
    if v in ('', 'todos'):
        return '', {}
    if v == 'sin':
        return 'AND c.vendedor_id IS NULL', {}
    try:
        return 'AND c.vendedor_id = :vid', {'vid': int(vendedor_id)}
    except (TypeError, ValueError):
        return '', {}


@reporte_vendedores_bp.route('/reporte_vendedores')
def reporte_vendedores_page():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    vendedores = _db.session.execute(text(
        "SELECT id, nombre FROM vendedor WHERE activo = 1 ORDER BY nombre"
    )).mappings().all()
    return render_template('reporte_vendedores.html',
                           vendedores=[dict(v) for v in vendedores])


@reporte_vendedores_bp.route('/api/reporte_vendedores')
def api_reporte_vendedores():
    if 'user_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    try:
        hoy = date.today().isoformat()
        desde = (request.args.get('desde') or '').strip() or hoy
        hasta = (request.args.get('hasta') or '').strip() or hoy
        vendedor_id = request.args.get('vendedor_id', '')

        fclause, fparams = _filtro_vendedor(vendedor_id)
        params = {'desde': desde, 'hasta': hasta}
        params.update(fparams)

        # Resumen por vendedor
        resumen = _db.session.execute(text(f"""
            SELECT c.vendedor_id AS vendedor_id,
                   COALESCE(v.nombre, 'Sin vendedor asignado') AS vendedor,
                   COUNT(f.id) AS cantidad,
                   COALESCE(SUM(f.total), 0)    AS total,
                   COALESCE(SUM(f.subtotal), 0) AS neto
            FROM factura f
            JOIN cliente c ON c.id = f.cliente_id
            LEFT JOIN vendedor v ON v.id = c.vendedor_id
            WHERE f.estado <> 'anulada'
              AND DATE(f.fecha) BETWEEN :desde AND :hasta
              {fclause}
            GROUP BY c.vendedor_id, v.nombre
            ORDER BY total DESC
        """), params).mappings().all()

        # Detalle de comprobantes
        detalle = _db.session.execute(text(f"""
            SELECT f.fecha, f.numero, f.tipo_comprobante, f.estado,
                   COALESCE(f.total, 0) AS total,
                   c.nombre AS cliente,
                   COALESCE(v.nombre, 'Sin vendedor') AS vendedor
            FROM factura f
            JOIN cliente c ON c.id = f.cliente_id
            LEFT JOIN vendedor v ON v.id = c.vendedor_id
            WHERE f.estado <> 'anulada'
              AND DATE(f.fecha) BETWEEN :desde AND :hasta
              {fclause}
            ORDER BY f.fecha DESC, f.numero DESC
        """), params).mappings().all()

        tipos = {
            '01': 'Factura A', '1': 'Factura A',
            '06': 'Factura B', '6': 'Factura B',
            '11': 'Factura C',
            '51': 'Factura M',
            '99': 'Comp. Interno',
        }

        resumen_out = [{
            'vendedor_id': r['vendedor_id'],
            'vendedor':    r['vendedor'],
            'cantidad':    int(r['cantidad'] or 0),
            'total':       float(r['total'] or 0),
            'neto':        float(r['neto'] or 0),
        } for r in resumen]

        detalle_out = [{
            'fecha':    d['fecha'].strftime('%d/%m/%Y') if d['fecha'] else '',
            'numero':   d['numero'],
            'tipo':     tipos.get(str(d['tipo_comprobante']), str(d['tipo_comprobante'])),
            'estado':   d['estado'],
            'cliente':  d['cliente'],
            'vendedor': d['vendedor'],
            'total':    float(d['total'] or 0),
        } for d in detalle]

        total_general = round(sum(r['total'] for r in resumen_out), 2)
        neto_general  = round(sum(r['neto'] for r in resumen_out), 2)
        cant_general  = sum(r['cantidad'] for r in resumen_out)

        return jsonify({
            'success': True,
            'desde': desde, 'hasta': hasta,
            'resumen': resumen_out,
            'detalle': detalle_out,
            'total_general': total_general,
            'neto_general': neto_general,
            'cantidad_general': cant_general,
        })
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
