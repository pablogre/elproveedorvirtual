# -*- coding: utf-8 -*-
"""
Blueprint: Sugerencia de Compra (SCHIRO - Módulo 1 del Ciclo de Compras)
--------------------------------------------------------------------------
Genera un informe que sugiere qué comprar, cuánto, y a qué proveedor.

Fórmula de cálculo:
    venta_promedio_diaria = ventas_últimos_30_días / 30
    cobertura_recomendada = venta_promedio_diaria × 30
    cantidad_sugerida = cobertura_recomendada + stock_minimo - stock_actual

Si cantidad_sugerida <= 0 → no hay que comprar todavía.

Criterios:
- Solo productos activos (activo = 1)
- Excluye combos (es_combo = 1)
- Cuenta ventas de facturas autorizadas + error_afip (ambas descontaron stock)
- Excluye facturas anuladas

UBICACIÓN: C:\\schiro\\sugerencia_compra.py

REGISTRO EN app.py:
    from sugerencia_compra import sugerencia_compra_bp
    app.register_blueprint(sugerencia_compra_bp)
"""

from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from extensions import db
from sqlalchemy import text
from datetime import datetime, timedelta

sugerencia_compra_bp = Blueprint('sugerencia_compra', __name__, url_prefix='/sugerencia_compra')


# =====================================================================
# HELPERS
# =====================================================================

def _usuario_id():
    return session.get('usuario_id') or session.get('user_id')


# =====================================================================
# PÁGINA PRINCIPAL
# =====================================================================

@sugerencia_compra_bp.route('/')
def listado():
    """Página con el informe de sugerencia de compra."""
    if not _usuario_id():
        return redirect(url_for('login'))
    return render_template('sugerencia_compra.html')


# =====================================================================
# API - CÁLCULO DE SUGERENCIAS
# =====================================================================

@sugerencia_compra_bp.route('/api/calcular')
def api_calcular():
    """
    Calcula la sugerencia de compra para cada producto activo.

    Parámetros opcionales (query string):
        dias_analisis: cuántos días hacia atrás mirar para calcular ventas (default 30)
        dias_cobertura: cuántos días de cobertura querés tener (default 30)
        proveedor_id: filtrar solo productos de un proveedor (a través de producto_proveedor)
        solo_criticos: '1' para mostrar solo productos con stock <= stock_minimo

    Devuelve:
        Lista de productos con datos de sugerencia, ordenada por urgencia.
    """
    if not _usuario_id():
        return jsonify({'error': 'No autenticado'}), 401

    dias_analisis = int(request.args.get('dias_analisis', 30))
    dias_cobertura = int(request.args.get('dias_cobertura', 30))
    proveedor_id = request.args.get('proveedor_id', '').strip()
    solo_criticos = request.args.get('solo_criticos') == '1'

    fecha_desde = (datetime.now() - timedelta(days=dias_analisis)).strftime('%Y-%m-%d')

    # ===== QUERY PRINCIPAL =====
    # Mostramos TODOS los productos activos no-combo y calculamos:
    # - ventas en los últimos N días (autorizada + error_afip)
    # - venta promedio diaria
    # - cantidad sugerida a comprar
    #
    # NOTA sobre rendimiento: usamos subqueries correlacionadas que son
    # fáciles de leer. Si con 1200 productos se pone lento, optimizamos.

    sql = """
        SELECT
            p.id,
            p.codigo,
            p.nombre,
            p.categoria,
            p.stock AS stock_actual,
            COALESCE(p.stock_minimo, 0) AS stock_minimo,
            p.costo,
            (
                SELECT COALESCE(SUM(df.cantidad), 0)
                FROM detalle_factura df
                JOIN factura f ON f.id = df.factura_id
                WHERE df.producto_id = p.id
                  AND f.estado IN ('autorizada', 'error_afip')
                  AND f.fecha >= :fecha_desde
            ) AS ventas_periodo
        FROM producto p
        WHERE p.activo = 1
          AND (p.es_combo = 0 OR p.es_combo IS NULL)
    """

    rows = db.session.execute(text(sql), {'fecha_desde': fecha_desde}).mappings().all()

    # Procesar resultados en Python (más claro que un SQL gigante)
    resultados = []
    for r in rows:
        stock_actual = float(r['stock_actual'] or 0)
        stock_minimo = float(r['stock_minimo'] or 0)
        ventas_periodo = float(r['ventas_periodo'] or 0)
        costo = float(r['costo'] or 0)

        # Venta promedio diaria
        venta_diaria = ventas_periodo / dias_analisis if dias_analisis > 0 else 0

        # Días de cobertura actuales (cuántos días me dura el stock actual)
        dias_cobertura_actual = (stock_actual / venta_diaria) if venta_diaria > 0 else None

        # Cantidad sugerida a comprar
        cobertura_necesaria = venta_diaria * dias_cobertura
        cantidad_sugerida = cobertura_necesaria + stock_minimo - stock_actual

        # Redondear hacia arriba (no comprás 2.5 unidades de algo que se vende por unidad)
        if cantidad_sugerida > 0:
            import math
            cantidad_sugerida = math.ceil(cantidad_sugerida)
        else:
            cantidad_sugerida = 0

        # Nivel de urgencia
        if stock_actual <= 0:
            urgencia = 'critico'  # sin stock
        elif stock_actual <= stock_minimo:
            urgencia = 'alto'  # bajo mínimo
        elif dias_cobertura_actual is not None and dias_cobertura_actual <= 7:
            urgencia = 'medio'  # menos de 7 días de stock
        elif cantidad_sugerida > 0:
            urgencia = 'bajo'
        else:
            urgencia = 'ok'

        # Filtro: solo críticos
        if solo_criticos and urgencia not in ('critico', 'alto'):
            continue

        # Si la cantidad sugerida es 0 y no hay stock mínimo ni ventas, no lo mostramos
        # (producto sin actividad, no hay nada que sugerir)
        if cantidad_sugerida == 0 and ventas_periodo == 0 and stock_minimo == 0:
            continue

        # Monto estimado de compra (útil para saber cuánto vas a gastar total)
        monto_estimado = cantidad_sugerida * costo

        resultados.append({
            'id': r['id'],
            'codigo': r['codigo'],
            'nombre': r['nombre'],
            'categoria': r['categoria'] or '',
            'stock_actual': stock_actual,
            'stock_minimo': stock_minimo,
            'ventas_periodo': ventas_periodo,
            'venta_diaria': round(venta_diaria, 3),
            'dias_cobertura_actual': round(dias_cobertura_actual, 1) if dias_cobertura_actual is not None else None,
            'cantidad_sugerida': cantidad_sugerida,
            'costo_unitario': costo,
            'monto_estimado': round(monto_estimado, 2),
            'urgencia': urgencia,
        })

    # Buscar proveedores por producto (agrupadamente, no una query por item)
    if resultados:
        producto_ids = [r['id'] for r in resultados]
        # Necesitamos un placeholder para cada ID
        placeholders = ','.join([f':id{i}' for i in range(len(producto_ids))])
        params = {f'id{i}': pid for i, pid in enumerate(producto_ids)}

        sql_prov = f"""
            SELECT pp.producto_id,
                   pr.id AS proveedor_id,
                   pr.razon_social,
                   pp.codigo_proveedor
              FROM producto_proveedor pp
              JOIN proveedor pr ON pr.id = pp.proveedor_id
             WHERE pp.producto_id IN ({placeholders})
               AND pr.activo = 1
        """
        try:
            prov_rows = db.session.execute(text(sql_prov), params).mappings().all()
            # Armar dict: producto_id → [proveedores]
            provs_por_prod = {}
            for pr in prov_rows:
                pid = pr['producto_id']
                if pid not in provs_por_prod:
                    provs_por_prod[pid] = []
                provs_por_prod[pid].append({
                    'id': pr['proveedor_id'],
                    'razon_social': pr['razon_social'],
                    'codigo_proveedor': pr['codigo_proveedor'],
                })

            # Asignar a resultados
            for r in resultados:
                r['proveedores'] = provs_por_prod.get(r['id'], [])
        except Exception as e:
            # Si la tabla producto_proveedor no existe o hay algún problema,
            # devolvemos sin proveedores (no rompe el informe)
            for r in resultados:
                r['proveedores'] = []

    # Filtro por proveedor (después de cargar los proveedores)
    if proveedor_id:
        try:
            prov_id_int = int(proveedor_id)
            resultados = [
                r for r in resultados
                if any(p['id'] == prov_id_int for p in r.get('proveedores', []))
            ]
        except ValueError:
            pass

    # Ordenar por urgencia (crítico primero) y después por monto estimado desc
    orden_urgencia = {'critico': 0, 'alto': 1, 'medio': 2, 'bajo': 3, 'ok': 4}
    resultados.sort(key=lambda x: (orden_urgencia.get(x['urgencia'], 9), -x['monto_estimado']))

    # Resumen
    resumen = {
        'total_productos': len(resultados),
        'criticos': sum(1 for r in resultados if r['urgencia'] == 'critico'),
        'altos': sum(1 for r in resultados if r['urgencia'] == 'alto'),
        'medios': sum(1 for r in resultados if r['urgencia'] == 'medio'),
        'bajos': sum(1 for r in resultados if r['urgencia'] == 'bajo'),
        'monto_total_estimado': round(sum(r['monto_estimado'] for r in resultados if r['cantidad_sugerida'] > 0), 2),
        'parametros': {
            'dias_analisis': dias_analisis,
            'dias_cobertura': dias_cobertura,
            'fecha_desde': fecha_desde,
        }
    }

    return jsonify({
        'resumen': resumen,
        'productos': resultados,
    })


# =====================================================================
# API - LISTAR PROVEEDORES (para filtro)
# =====================================================================

@sugerencia_compra_bp.route('/api/proveedores')
def api_proveedores():
    """Lista de proveedores activos para el dropdown de filtro."""
    if not _usuario_id():
        return jsonify({'error': 'No autenticado'}), 401

    rows = db.session.execute(text("""
        SELECT id, razon_social
          FROM proveedor
         WHERE activo = 1
         ORDER BY razon_social
    """)).mappings().all()

    return jsonify([{'id': r['id'], 'razon_social': r['razon_social']} for r in rows])