#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cta_cte.py - MÓDULO DE CUENTA CORRIENTE
═══════════════════════════════════════════════════════════════════════════════
Maneja toda la lógica de ventas fiadas y pagos en cuenta corriente.
═══════════════════════════════════════════════════════════════════════════════
"""

from flask import Blueprint, jsonify, request, session, render_template
from extensions import db
from sqlalchemy import text, func
from datetime import datetime
from decimal import Decimal

# Importar auditoría de stock
try:
    from stock_audit import registrar_movimiento_stock
except ImportError:
    # Si no existe el módulo, crear función dummy
    def registrar_movimiento_stock(*args, **kwargs):
        pass

# Blueprint para las rutas de CTA.CTE
cta_cte_bp = Blueprint('cta_cte', __name__)


# ═══════════════════════════════════════════════════════════════════════════════
# FUNCIONES AUXILIARES
# ═══════════════════════════════════════════════════════════════════════════════

def ejecutar_query(db, query, params=None, commit=False):
    """
    Ejecuta una query SQL de forma segura
    
    Args:
        db: Instancia de SQLAlchemy
        query: Query SQL (puede usar :param para parámetros)
        params: Diccionario de parámetros
        commit: Si True, hace commit
    
    Returns:
        ResultProxy o lastrowid según el caso
    """
    try:
        if params:
            result = db.session.execute(text(query), params)
        else:
            result = db.session.execute(text(query))
        
        if commit:
            db.session.commit()
            return result.lastrowid if hasattr(result, 'lastrowid') else True
        
        return result
    except Exception as e:
        db.session.rollback()
        raise e


# ═══════════════════════════════════════════════════════════════════════════════
# FUNCIONES PRINCIPALES - GUARDAR VENTA FIADA
# ═══════════════════════════════════════════════════════════════════════════════

def guardar_venta_fiada(db, cliente_id, productos, usuario_id, observaciones=None):
    """
    Guarda una venta fiada en cuenta corriente
    - NO emite factura
    - SÍ descuenta stock (incluyendo combos)
    - Guarda como pendiente de pago
    """
    try:
        # Calcular total
        monto_total = sum(Decimal(str(p['subtotal'])) for p in productos)
        
        # 1. Crear el movimiento en CTA.CTE
        query_movimiento = """
            INSERT INTO cta_cte_movimiento 
            (cliente_id, tipo, estado, monto_total, usuario_id, observaciones, fecha)
            VALUES 
            (:cliente_id, 'venta_fiada', 'pendiente', :monto_total, :usuario_id, :observaciones, NOW())
        """
        
        result = ejecutar_query(db, query_movimiento, {
            'cliente_id': cliente_id,
            'monto_total': float(monto_total),
            'usuario_id': usuario_id,
            'observaciones': observaciones
        }, commit=True)
        
        movimiento_id = result
        
        # 2. Insertar los detalles de productos
        query_detalle = """
            INSERT INTO cta_cte_detalle 
            (movimiento_id, producto_id, descripcion, cantidad, precio_unitario, subtotal, porcentaje_iva, importe_iva)
            VALUES 
            (:movimiento_id, :producto_id, :descripcion, :cantidad, :precio_unitario, :subtotal, :porcentaje_iva, :importe_iva)
        """
        
        for producto in productos:
            ejecutar_query(db, query_detalle, {
                'movimiento_id': movimiento_id,
                'producto_id': producto['producto_id'],
                'descripcion': producto['descripcion'],
                'cantidad': float(producto['cantidad']),
                'precio_unitario': float(producto['precio_unitario']),
                'subtotal': float(producto['subtotal']),
                'porcentaje_iva': float(producto.get('porcentaje_iva', 21.00)),
                'importe_iva': float(producto.get('importe_iva', 0.00))
            }, commit=True)
        
        # 3. Descontar stock - CORREGIDO PARA COMBOS CON AUDITORÍA
        for producto in productos:
            producto_id = producto['producto_id']
            cantidad = float(producto['cantidad'])
            
            # Verificar si es combo
            query_check_combo = """
                SELECT id, codigo, nombre, es_combo, stock, producto_base_id, cantidad_combo,
                       producto_base_id_2, cantidad_combo_2,
                       producto_base_id_3, cantidad_combo_3
                FROM producto WHERE id = :producto_id
            """
            result_combo = ejecutar_query(db, query_check_combo, {'producto_id': producto_id})
            row = result_combo.fetchone()
            
            if row and row.es_combo:
                # Es combo - descontar de productos base
                if row.producto_base_id and row.cantidad_combo:
                    descuento = cantidad * float(row.cantidad_combo)
                    
                    # Obtener info del producto base para auditoría
                    query_base_info = "SELECT id, codigo, nombre, stock FROM producto WHERE id = :base_id"
                    result_base = ejecutar_query(db, query_base_info, {'base_id': row.producto_base_id})
                    base_info = result_base.fetchone()
                    
                    if base_info:
                        stock_anterior = float(base_info.stock)
                        stock_nuevo = stock_anterior - descuento
                        
                        query_stock_base = """
                            UPDATE producto 
                            SET stock = stock - :descuento 
                            WHERE id = :base_id
                        """
                        ejecutar_query(db, query_stock_base, {
                            'descuento': descuento,
                            'base_id': row.producto_base_id
                        }, commit=True)
                        print(f"📦 Combo: descontado {descuento} de producto base {row.producto_base_id}")
                        
                        # Auditoría
                        registrar_movimiento_stock(
                            db=db,
                            producto_id=base_info.id,
                            tipo='venta_fiada',
                            cantidad=descuento,
                            signo='-',
                            stock_anterior=stock_anterior,
                            stock_nuevo=stock_nuevo,
                            referencia_tipo='cta_cte',
                            referencia_id=movimiento_id,
                            motivo=f'Combo en CTA.CTE',
                            usuario_id=session.get('user_id'),
                            usuario_nombre=session.get('nombre', 'Sistema'),
                            codigo_producto=base_info.codigo,
                            nombre_producto=base_info.nombre
                        )
                
                if row.producto_base_id_2 and row.cantidad_combo_2:
                    descuento = cantidad * float(row.cantidad_combo_2)
                    
                    result_base = ejecutar_query(db, query_base_info, {'base_id': row.producto_base_id_2})
                    base_info = result_base.fetchone()
                    
                    if base_info:
                        stock_anterior = float(base_info.stock)
                        stock_nuevo = stock_anterior - descuento
                        
                        ejecutar_query(db, query_stock_base, {
                            'descuento': descuento,
                            'base_id': row.producto_base_id_2
                        }, commit=True)
                        print(f"📦 Combo: descontado {descuento} de producto base 2 {row.producto_base_id_2}")
                        
                        registrar_movimiento_stock(
                            db=db,
                            producto_id=base_info.id,
                            tipo='venta_fiada',
                            cantidad=descuento,
                            signo='-',
                            stock_anterior=stock_anterior,
                            stock_nuevo=stock_nuevo,
                            referencia_tipo='cta_cte',
                            referencia_id=movimiento_id,
                            motivo=f'Combo en CTA.CTE',
                            usuario_id=session.get('user_id'),
                            usuario_nombre=session.get('nombre', 'Sistema'),
                            codigo_producto=base_info.codigo,
                            nombre_producto=base_info.nombre
                        )
                
                if row.producto_base_id_3 and row.cantidad_combo_3:
                    descuento = cantidad * float(row.cantidad_combo_3)
                    
                    result_base = ejecutar_query(db, query_base_info, {'base_id': row.producto_base_id_3})
                    base_info = result_base.fetchone()
                    
                    if base_info:
                        stock_anterior = float(base_info.stock)
                        stock_nuevo = stock_anterior - descuento
                        
                        ejecutar_query(db, query_stock_base, {
                            'descuento': descuento,
                            'base_id': row.producto_base_id_3
                        }, commit=True)
                        print(f"📦 Combo: descontado {descuento} de producto base 3 {row.producto_base_id_3}")
                        
                        registrar_movimiento_stock(
                            db=db,
                            producto_id=base_info.id,
                            tipo='venta_fiada',
                            cantidad=descuento,
                            signo='-',
                            stock_anterior=stock_anterior,
                            stock_nuevo=stock_nuevo,
                            referencia_tipo='cta_cte',
                            referencia_id=movimiento_id,
                            motivo=f'Combo en CTA.CTE',
                            usuario_id=session.get('user_id'),
                            usuario_nombre=session.get('nombre', 'Sistema'),
                            codigo_producto=base_info.codigo,
                            nombre_producto=base_info.nombre
                        )
            else:
                # Producto normal - descontar directo
                stock_anterior = float(row.stock) if row else 0
                stock_nuevo = stock_anterior - cantidad
                
                query_stock = """
                    UPDATE producto 
                    SET stock = stock - :cantidad 
                    WHERE id = :producto_id
                """
                ejecutar_query(db, query_stock, {
                    'cantidad': cantidad,
                    'producto_id': producto_id
                }, commit=True)
                print(f"📦 Stock descontado: {cantidad} de producto {producto_id}")
                
                # Auditoría
                if row:
                    registrar_movimiento_stock(
                        db=db,
                        producto_id=producto_id,
                        tipo='venta_fiada',
                        cantidad=cantidad,
                        signo='-',
                        stock_anterior=stock_anterior,
                        stock_nuevo=stock_nuevo,
                        referencia_tipo='cta_cte',
                        referencia_id=movimiento_id,
                        usuario_id=session.get('user_id'),
                        usuario_nombre=session.get('nombre', 'Sistema'),
                        codigo_producto=row.codigo,
                        nombre_producto=row.nombre
                    )
        
        return {
            'success': True,
            'movimiento_id': movimiento_id,
            'mensaje': f'Venta fiada registrada correctamente. Total: ${monto_total:.2f}'
        }
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error en guardar_venta_fiada: {str(e)}")
        return {
            'success': False,
            'mensaje': f'Error al guardar venta fiada: {str(e)}'
        }
        

# ═══════════════════════════════════════════════════════════════════════════════
# FUNCIONES PRINCIPALES - OBTENER PRODUCTOS PENDIENTES
# ═══════════════════════════════════════════════════════════════════════════════

def obtener_productos_pendientes(db, cliente_id):
    """
    Obtiene todos los productos pendientes de pago de un cliente
    
    Args:
        db: Instancia de SQLAlchemy
        cliente_id: ID del cliente
    
    Returns:
        Lista de dict con productos pendientes agrupados por movimiento
    """
    try:
        query = """
            SELECT 
                m.id as movimiento_id,
                m.fecha,
                m.monto_total,
                d.id as detalle_id,
                d.producto_id,
                d.descripcion,
                d.cantidad,
                d.precio_unitario,
                d.subtotal,
                d.porcentaje_iva,
                d.importe_iva,
                p.codigo as producto_codigo,
                COALESCE(p.precio, d.precio_unitario) as precio_actual
            FROM cta_cte_movimiento m
            INNER JOIN cta_cte_detalle d ON m.id = d.movimiento_id
            LEFT JOIN producto p ON d.producto_id = p.id
            WHERE m.cliente_id = :cliente_id 
            AND m.estado = 'pendiente'
            AND m.tipo = 'venta_fiada'
            ORDER BY m.fecha DESC, d.id ASC
        """
        
        result = ejecutar_query(db, query, {'cliente_id': cliente_id})
        rows = result.fetchall()
        
        # Agrupar por movimiento
        movimientos = {}
        for row in rows:
            mov_id = row.movimiento_id
            
            if mov_id not in movimientos:
                movimientos[mov_id] = {
                    'movimiento_id': mov_id,
                    'fecha': row.fecha.strftime('%d/%m/%Y %H:%M') if row.fecha else '',
                    'monto_total': float(row.monto_total),
                    'productos': []
                }
            
            movimientos[mov_id]['productos'].append({
                'detalle_id': row.detalle_id,
                'producto_id': row.producto_id,
                'producto_codigo': row.producto_codigo,
                'descripcion': row.descripcion,
                'cantidad': float(row.cantidad),
                'precio_unitario': float(row.precio_unitario),
                'subtotal': float(row.subtotal),
                'porcentaje_iva': float(row.porcentaje_iva),
                'importe_iva': float(row.importe_iva),
                'precio_actual': float(row.precio_actual) if row.precio_actual else float(row.precio_unitario),
                'subtotal_actual': float(row.cantidad) * (float(row.precio_actual) if row.precio_actual else float(row.precio_unitario))
            })
        
        return list(movimientos.values())
        
    except Exception as e:
        print(f"Error al obtener productos pendientes: {str(e)}")
        return []


# ═══════════════════════════════════════════════════════════════════════════════
# FUNCIONES PRINCIPALES - PROCESAR PAGO
# ═══════════════════════════════════════════════════════════════════════════════

def marcar_productos_como_pagados(db, detalle_ids, factura_id):
    """
    Marca productos específicos como pagados y vincula con la factura
    
    Args:
        db: Instancia de SQLAlchemy
        detalle_ids: Lista de IDs de cta_cte_detalle que se están pagando
        factura_id: ID de la factura generada
    
    Returns:
        dict con {success: bool, mensaje: str}
    """
    try:
        if not detalle_ids:
            return {'success': False, 'mensaje': 'No se especificaron productos a pagar'}
        
        # Obtener los movimientos afectados
        query_movimientos = """
            SELECT DISTINCT movimiento_id 
            FROM cta_cte_detalle 
            WHERE id IN :detalle_ids
        """
        
        # Convertir lista a formato SQL
        detalle_ids_str = '(' + ','.join(map(str, detalle_ids)) + ')'
        
        result = db.session.execute(
            text(f"SELECT DISTINCT movimiento_id FROM cta_cte_detalle WHERE id IN {detalle_ids_str}")
        )
        movimientos_ids = [row.movimiento_id for row in result]
        
        # Para cada movimiento, verificar si todos sus productos fueron pagados
        for mov_id in movimientos_ids:
            # Contar productos totales del movimiento
            query_total = """
                SELECT COUNT(*) as total 
                FROM cta_cte_detalle 
                WHERE movimiento_id = :mov_id
            """
            result_total = ejecutar_query(db, query_total, {'mov_id': mov_id})
            total_productos = result_total.fetchone().total
            
            # Contar cuántos de esos productos están en detalle_ids
            query_pagados = f"""
                SELECT COUNT(*) as pagados 
                FROM cta_cte_detalle 
                WHERE movimiento_id = :mov_id 
                AND id IN {detalle_ids_str}
            """
            result_pagados = db.session.execute(text(query_pagados), {'mov_id': mov_id})
            productos_pagados = result_pagados.fetchone().pagados
            
            # Si se pagaron todos los productos, marcar movimiento como pagado
            if total_productos == productos_pagados:
                query_update_mov = """
                    UPDATE cta_cte_movimiento 
                    SET estado = 'pagado', factura_id = :factura_id 
                    WHERE id = :mov_id
                """
                ejecutar_query(db, query_update_mov, {
                    'factura_id': factura_id,
                    'mov_id': mov_id
                }, commit=True)
        
        return {
            'success': True,
            'mensaje': 'Productos marcados como pagados correctamente'
        }
        
    except Exception as e:
        db.session.rollback()
        return {
            'success': False,
            'mensaje': f'Error al marcar productos como pagados: {str(e)}'
        }


# ═══════════════════════════════════════════════════════════════════════════════
# FUNCIONES DE CONSULTA
# ═══════════════════════════════════════════════════════════════════════════════

def saldo_real_cliente(db, cliente_id):
    """
    FUENTE ÚNICA DE VERDAD del saldo de un cliente.

    Fórmula verificada contra 6 escenarios controlados + caso real Abella
    (ver test_saldo_cliente.py / PENDIENTES_VERIFACTU.md):

      SALDO = SUM(saldo_pendiente WHERE tipo='venta_fiada')
              − ( SUM(monto_total A_CUENTA|LIQUIDACION)
                  − SUM(monto_total SALDO_FAVOR_USADO|LIQUIDACION_PAGADA) )

    - saldo_pendiente ya tiene descontados los cobros parciales (el cobro
      hace UPDATE de saldo_pendiente). Por eso NO se hace ventas−pagos:
      contaría doble.
    - El bloque (A_CUENTA|LIQUIDACION) − (SALDO_FAVOR_USADO|LIQUIDACION_PAGADA)
      es el saldo a favor no aplicado. LIQUIDACION = crédito a un
      intermediario por liquidación "pagar después" (Siamotre le debe);
      LIQUIDACION_PAGADA lo cancela cuando se paga o se anula. Tienen la
      MISMA mecánica que A_CUENTA/SALDO_FAVOR_USADO, por eso entran en el
      mismo bloque sin cambiar la estructura de la fórmula.

    Returns: float. Positivo = el cliente debe. Negativo = saldo a favor.
    Es la MISMA fórmula que usa la grilla (/buscar_clientes) y la
    cta.cte desglosada (api_historial_completo).
    """
    try:
        query = """
            SELECT
              COALESCE((
                 SELECT SUM(m.saldo_pendiente) FROM cta_cte_movimiento m
                 WHERE m.cliente_id = :cid AND m.tipo = 'venta_fiada'
              ), 0)
              -
              COALESCE((
                 SELECT SUM(m.monto_total) FROM cta_cte_movimiento m
                 WHERE m.cliente_id = :cid AND m.tipo = 'nota_credito'
              ), 0)
              -
              (
                COALESCE((
                   SELECT SUM(m.saldo_pendiente) FROM cta_cte_movimiento m
                   WHERE m.cliente_id = :cid AND m.tipo_mov = 'pago'
                     AND m.numero_comprobante IN ('A_CUENTA', 'LIQUIDACION')
                ), 0)
                -
                COALESCE((
                   SELECT SUM(m.monto_total) FROM cta_cte_movimiento m
                   WHERE m.cliente_id = :cid AND m.tipo_mov = 'pago'
                     AND m.numero_comprobante IN ('SALDO_FAVOR_USADO', 'LIQUIDACION_PAGADA')
                ), 0)
              ) AS saldo
        """
        result = ejecutar_query(db, query, {'cid': cliente_id})
        row = result.fetchone()
        return float(row.saldo) if row and row.saldo is not None else 0.0
    except Exception as e:
        print(f"Error en saldo_real_cliente({cliente_id}): {str(e)}")
        return 0.0


def obtener_saldo_cliente(db, cliente_id):
    """
    Obtiene el saldo pendiente de un cliente
    
    Args:
        db: Instancia de SQLAlchemy
        cliente_id: ID del cliente
    
    Returns:
        float con el saldo pendiente
    """
    try:
        query = """
            SELECT COALESCE(SUM(monto_total), 0) as saldo
            FROM cta_cte_movimiento
            WHERE cliente_id = :cliente_id
            AND estado = 'pendiente'
            AND tipo = 'venta_fiada'
        """
        
        result = ejecutar_query(db, query, {'cliente_id': cliente_id})
        row = result.fetchone()
        
        return float(row.saldo) if row else 0.0
        
    except Exception as e:
        print(f"Error al obtener saldo: {str(e)}")
        return 0.0


def obtener_historial_cta_cte(db, cliente_id, limit=50):
    """
    Obtiene el historial completo de movimientos de un cliente
    
    Args:
        db: Instancia de SQLAlchemy
        cliente_id: ID del cliente
        limit: Cantidad máxima de registros
    
    Returns:
        Lista de movimientos
    """
    try:
        query = """
            SELECT 
                m.id,
                m.fecha,
                m.tipo,
                m.estado,
                m.monto_total,
                m.factura_id,
                f.numero as factura_numero,
                u.nombre as usuario_nombre
            FROM cta_cte_movimiento m
            LEFT JOIN factura f ON m.factura_id = f.id
            LEFT JOIN usuario u ON m.usuario_id = u.id
            WHERE m.cliente_id = :cliente_id
            ORDER BY m.fecha DESC
            LIMIT :limit
        """
        
        result = ejecutar_query(db, query, {
            'cliente_id': cliente_id,
            'limit': limit
        })
        
        movimientos = []
        for row in result:
            movimientos.append({
                'id': row.id,
                'fecha': row.fecha.strftime('%d/%m/%Y %H:%M') if row.fecha else '',
                'tipo': row.tipo,
                'estado': row.estado,
                'monto_total': float(row.monto_total),
                'factura_id': row.factura_id,
                'factura_numero': row.factura_numero,
                'usuario_nombre': row.usuario_nombre
            })
        
        return movimientos
        
    except Exception as e:
        print(f"Error al obtener historial: {str(e)}")
        return []


# ═══════════════════════════════════════════════════════════════════════════════
# RUTAS API (ENDPOINTS)
# ═══════════════════════════════════════════════════════════════════════════════

@cta_cte_bp.route('/api/cta_cte/productos_pendientes/<int:cliente_id>', methods=['GET'])
def api_productos_pendientes(cliente_id):
    """
    Endpoint para obtener productos pendientes de un cliente
    GET /api/cta_cte/productos_pendientes/123
    """
    
    productos = obtener_productos_pendientes(db, cliente_id)
    saldo = saldo_real_cliente(db, cliente_id)  # fuente única (antes obtener_saldo_cliente, daba mal)
    
    return jsonify({
        'success': True,
        'productos': productos,
        'saldo_total': saldo
    })


@cta_cte_bp.route('/api/cta_cte/saldo_favor/<int:cliente_id>', methods=['GET'])
def api_saldo_favor_cliente(cliente_id):
    """Devuelve el saldo a favor (pagos a cuenta no imputados) del cliente."""
    if 'user_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    try:
        # Suma de pagos a cuenta sin imputar (A_CUENTA + LIQUIDACION)
        # saldo_pendiente = monto NO imputado a facturas (con módulo de imputación)
        pagos = db.session.execute(text("""
            SELECT COALESCE(SUM(saldo_pendiente), 0)
            FROM cta_cte_movimiento
            WHERE cliente_id = :id AND tipo_mov = 'pago'
              AND numero_comprobante IN ('A_CUENTA', 'LIQUIDACION')
        """), {'id': cliente_id}).scalar() or 0.0
        # Resta los ya usados (SALDO_FAVOR_USADO + LIQUIDACION_PAGADA)
        usados = db.session.execute(text("""
            SELECT COALESCE(SUM(monto_total), 0)
            FROM cta_cte_movimiento
            WHERE cliente_id = :id AND tipo_mov = 'pago'
              AND numero_comprobante IN ('SALDO_FAVOR_USADO', 'LIQUIDACION_PAGADA')
        """), {'id': cliente_id}).scalar() or 0.0
        saldo_favor = max(0.0, float(pagos) - float(usados))
        return jsonify({'success': True, 'saldo_favor': round(saldo_favor, 2)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@cta_cte_bp.route('/api/cta_cte/saldo/<int:cliente_id>', methods=['GET'])
def api_saldo_cliente(cliente_id):
    """Saldo real del cliente desde cta_cte_movimiento"""
    try:
        from sqlalchemy import text
        result = db.session.execute(text("""
            SELECT COALESCE(SUM(saldo_pendiente), 0)
            FROM cta_cte_movimiento
            WHERE cliente_id = :id AND tipo_mov = 'venta'
        """), {'id': cliente_id}).fetchone()
        saldo = float(result[0]) if result else 0.0
    except:
        saldo = 0.0

    return jsonify({'success': True, 'saldo': saldo})


@cta_cte_bp.route('/api/cta_cte/historial/<int:cliente_id>', methods=['GET'])
def api_historial_cliente(cliente_id):
    """
    Endpoint para obtener historial de movimientos
    GET /api/cta_cte/historial/123
    """
    
    historial = obtener_historial_cta_cte(db, cliente_id)
    
    return jsonify({
        'success': True,
        'historial': historial
    })


# ═══════════════════════════════════════════════════════════════════════════════
# FUNCIÓN DE INICIALIZACIÓN
# ═══════════════════════════════════════════════════════════════════════════════

@cta_cte_bp.route('/cta_cte/historial_cliente/<int:cliente_id>')
def vista_historial_cliente(cliente_id):
    """Vista del historial de CTA.CTE de un cliente"""
    from flask import session, redirect, url_for
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    try:
        cliente = db.session.execute(
            text("SELECT id, nombre, documento FROM cliente WHERE id = :id"),
            {'id': cliente_id}
        ).fetchone()
        if not cliente:
            return "Cliente no encontrado", 404
    except Exception as e:
        return f"Error: {e}", 500
    
    return render_template('historial_ctacte.html', 
                          cliente_id=cliente_id,
                          cliente_nombre=cliente.nombre if cliente else '')


@cta_cte_bp.route('/api/cta_cte/historial_completo/<int:cliente_id>')
def api_historial_completo(cliente_id):
    """Historial completo CTA.CTE — formato Debe/Haber/Saldo corrido.
    
    Acepta ?incluir_anulados=1 para mostrar también los movimientos cancelados/anulados.
    Por defecto, esos movimientos NO se devuelven (vista normal limpia).
    """
    from flask import session
    if 'user_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    try:
        # Si incluir_anulados=1 traemos TODO; si no, ocultamos cancelados/anulados
        incluir_anulados = request.args.get('incluir_anulados', '0') == '1'
        filtro_estado = '' if incluir_anulados else "AND m.estado NOT IN ('cancelado','anulado','anulada')"
        
        movs = db.session.execute(text(f"""
            SELECT m.id, m.tipo_mov, m.estado, m.monto_total, m.saldo_pendiente,
                   m.fecha, m.observaciones, m.numero_comprobante,
                   COALESCE(f.numero, m.numero_comprobante) AS comprobante,
                   m.factura_id
            FROM cta_cte_movimiento m
            LEFT JOIN factura f ON f.id = m.factura_id
            WHERE m.cliente_id = :cid
              {filtro_estado}
            ORDER BY m.fecha ASC, m.id ASC
        """), {'cid': cliente_id}).fetchall()

        # ── Saldo total CORRECTO (se calcula PRIMERO) ─────────────────────
        # Misma fórmula que la grilla (/buscar_clientes), verificada contra
        # cliente real: deuda (SUM saldo_pendiente venta_fiada) menos saldo
        # a favor neto (A_CUENTA - SALDO_FAVOR_USADO). NO usar suma corrida
        # de monto_total: triplica el saldo a favor.
        saldo_total_correcto = float(db.session.execute(text("""
            SELECT
              COALESCE((
                SELECT SUM(m.saldo_pendiente) FROM cta_cte_movimiento m
                WHERE m.cliente_id = :cid AND m.tipo = 'venta_fiada'
              ), 0)
              -
              COALESCE((
                SELECT SUM(m.monto_total) FROM cta_cte_movimiento m
                WHERE m.cliente_id = :cid AND m.tipo = 'nota_credito'
              ), 0)
              -
              (
                COALESCE((
                  SELECT SUM(m.saldo_pendiente) FROM cta_cte_movimiento m
                  WHERE m.cliente_id = :cid AND m.tipo_mov = 'pago'
                    AND m.numero_comprobante IN ('A_CUENTA', 'LIQUIDACION')
                ), 0)
                -
                COALESCE((
                  SELECT SUM(m.monto_total) FROM cta_cte_movimiento m
                  WHERE m.cliente_id = :cid AND m.tipo_mov = 'pago'
                    AND m.numero_comprobante IN ('SALDO_FAVOR_USADO', 'LIQUIDACION_PAGADA')
                ), 0)
              )
        """), {'cid': cliente_id}).scalar() or 0.0)

        # ── Saldo corrido calculado HACIA ATRÁS desde el total correcto ───
        # La fila más nueva (última en orden ASC) debe mostrar el saldo
        # total actual. Cada fila más vieja muestra el saldo ANTES de su
        # propio movimiento (le deshacemos el efecto). Así, POR
        # CONSTRUCCIÓN, la fila más nueva = saldo_total_correcto y la
        # columna SIEMPRE cierra con el total grande.
        filas = []
        for m in movs:
            tipo_mov = (m.tipo_mov or 'venta').strip()
            monto = float(m.monto_total or 0)
            if tipo_mov == 'pago':
                debe, haber = 0.0, monto
            else:
                debe, haber = monto, 0.0
            filas.append({
                'id':              m.id,
                'factura_id':      m.factura_id,
                'fecha':           m.fecha.strftime('%d/%m/%Y') if m.fecha else '',
                'comprobante':     m.comprobante or '—',
                'descripcion':     m.observaciones or '',
                'tipo_mov':        tipo_mov,
                'estado':          m.estado or '',
                'debe':            debe,
                'haber':           haber,
                'saldo_pendiente': float(m.saldo_pendiente or 0),
            })

        # Recorremos de la fila MÁS NUEVA a la más vieja.
        # La más nueva muestra el total actual; a la anterior le
        # deshacemos el efecto del movimiento de la fila actual.
        saldo_acum = saldo_total_correcto
        for fila in reversed(filas):
            fila['saldo_corrido'] = round(saldo_acum, 2)
            # deshacer el efecto de ESTA fila para la fila más vieja:
            saldo_acum -= (fila['debe'] - fila['haber'])

        resultado = filas
        resultado.reverse()

        cliente = db.session.execute(
            text("SELECT nombre, documento FROM cliente WHERE id = :id"),
            {'id': cliente_id}
        ).fetchone()

        return jsonify({
            'success':     True,
            'movimientos': resultado,
            'saldo_total': round(saldo_total_correcto, 2),
            'cliente':     {'nombre': cliente.nombre, 'documento': cliente.documento} if cliente else {},
        })
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


# ═══════════════════════════════════════════════════════════════════════════════
# NUEVO SISTEMA: REGISTRO DE COMPROBANTE EN CTA.CTE
# ═══════════════════════════════════════════════════════════════════════════════

def registrar_comprobante_en_cta_cte(db, factura_id, numero_comprobante, monto_total,
                                      saldo_pendiente, cliente_id, usuario_id, observaciones=None):
    """
    Registra un comprobante (factura o interno) en CTA.CTE después de generarlo.
    Reemplaza la lógica de 'pisa el saldo' del sistema anterior.

    Args:
        factura_id:          ID de la factura/interno generado
        numero_comprobante:  Número visible del comprobante (ej: '0001-00000123')
        monto_total:         Total del comprobante
        saldo_pendiente:     Parte que quedó sin pagar (0 si pagó todo)
        cliente_id:          ID del cliente
        usuario_id:          ID del usuario que procesó la venta
        observaciones:       Texto libre opcional
    """
    try:
        estado = 'pendiente' if float(saldo_pendiente) > 0 else 'pagado'
        obs = observaciones or f'Comprobante {numero_comprobante}'

        db.session.execute(text("""
            INSERT INTO cta_cte_movimiento
                (cliente_id, tipo, tipo_mov, estado, monto_total, saldo_pendiente,
                 factura_id, numero_comprobante, usuario_id, observaciones, fecha)
            VALUES
                (:cliente_id, 'venta_fiada', 'venta', :estado, :monto_total, :saldo_pendiente,
                 :factura_id, :numero_comprobante, :usuario_id, :obs, NOW())
        """), {
            'cliente_id':          cliente_id,
            'estado':              estado,
            'monto_total':         float(monto_total),
            'saldo_pendiente':     float(saldo_pendiente),
            'factura_id':          factura_id,
            'numero_comprobante':  numero_comprobante,
            'usuario_id':          usuario_id,
            'obs':                 obs,
        })
        mov_id = db.session.execute(text("SELECT LAST_INSERT_ID()")).scalar()
        print(f"✅ Movimiento CTA.CTE registrado: #{mov_id} — {numero_comprobante} — saldo ${saldo_pendiente:.2f}")
        return mov_id
    except Exception as e:
        print(f"❌ Error registrando comprobante en CTA.CTE: {e}")
        raise


# ═══════════════════════════════════════════════════════════════════════════════
# ENDPOINTS: MOVIMIENTOS PENDIENTES Y COBRO
# ═══════════════════════════════════════════════════════════════════════════════

@cta_cte_bp.route('/api/cta_cte/movimientos_pendientes/<int:cliente_id>', methods=['GET'])
def api_movimientos_pendientes(cliente_id):
    """Devuelve los movimientos con saldo pendiente > 0 para un cliente."""
    if 'user_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    try:
        rows = db.session.execute(text("""
            SELECT m.id, m.fecha, m.numero_comprobante, m.monto_total,
                   m.saldo_pendiente, m.observaciones, m.tipo_mov
            FROM cta_cte_movimiento m
            WHERE m.cliente_id = :cid
              AND m.estado = 'pendiente'
              AND m.saldo_pendiente > 0
            ORDER BY m.fecha ASC
        """), {'cid': cliente_id}).fetchall()

        movimientos = []
        for r in rows:
            movimientos.append({
                'id':                  r.id,
                'fecha':               r.fecha.strftime('%d/%m/%Y') if r.fecha else '',
                'numero_comprobante':  r.numero_comprobante or '—',
                'monto_total':         float(r.monto_total or 0),
                'saldo_pendiente':     float(r.saldo_pendiente or 0),
                'observaciones':       r.observaciones or '',
                'a_pagar':             float(r.saldo_pendiente or 0),  # default = pagar todo
            })

        # Saldo total
        saldo = sum(m['saldo_pendiente'] for m in movimientos)

        # Info del cliente
        cliente = db.session.execute(
            text("SELECT nombre, documento FROM cliente WHERE id = :id"),
            {'id': cliente_id}
        ).fetchone()

        return jsonify({
            'success':     True,
            'movimientos': movimientos,
            'saldo_total': saldo,
            'cliente':     {'nombre': cliente.nombre, 'documento': cliente.documento} if cliente else {},
        })
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@cta_cte_bp.route('/api/cta_cte/cobrar', methods=['POST'])
def api_cobrar_cliente():
    """
    Genera un recibo de cobro imputando a movimientos pendientes.
    Permite pago parcial por movimiento.

    Payload:
    {
        "cliente_id": 5,
        "imputaciones": [
            {"movimiento_id": 12, "monto_imputado": 500.00},
            {"movimiento_id": 13, "monto_imputado": 1000.00}
        ],
        "medios_pago": [
            {"medio": "efectivo", "importe": 1500.00}
        ],
        "observaciones": "Pago parcial"
    }
    """
    if 'user_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    try:
        data = request.get_json()
        cliente_id   = data.get('cliente_id')
        imputaciones = data.get('imputaciones', [])
        medios_pago  = data.get('medios_pago', [])
        observaciones = (data.get('observaciones') or '').strip()

        if not cliente_id:
            return jsonify({'success': False, 'error': 'cliente_id requerido'}), 400
        if not imputaciones:
            return jsonify({'success': False, 'error': 'Seleccioná al menos un comprobante'}), 400
        if not medios_pago:
            return jsonify({'success': False, 'error': 'Agregá al menos un medio de pago'}), 400

        total_imputado = sum(float(i['monto_imputado']) for i in imputaciones)
        total_medios   = sum(float(m['importe']) for m in medios_pago)

        if abs(total_imputado - total_medios) > 0.01:
            return jsonify({
                'success': False,
                'error': f'El total imputado (${total_imputado:.2f}) no coincide con los medios de pago (${total_medios:.2f})'
            }), 400

        # Obtener siguiente número de recibo
        result = db.session.execute(
            text("SELECT ultimo_numero FROM recibo_cobro_numerador LIMIT 1 FOR UPDATE")
        ).fetchone()
        nuevo_numero = (result.ultimo_numero if result else 0) + 1
        numero_recibo = f"R{str(nuevo_numero).zfill(8)}"
        db.session.execute(
            text("UPDATE recibo_cobro_numerador SET ultimo_numero = :n"),
            {'n': nuevo_numero}
        )

        # Crear recibo cabecera
        db.session.execute(text("""
            INSERT INTO recibo_cobro (cliente_id, usuario_id, fecha, numero, total, observaciones)
            VALUES (:cid, :uid, NOW(), :numero, :total, :obs)
        """), {
            'cid':    cliente_id,
            'uid':    session['user_id'],
            'numero': numero_recibo,
            'total':  total_medios,
            'obs':    observaciones or None,
        })
        recibo_id = db.session.execute(text("SELECT LAST_INSERT_ID()")).scalar()

        # Imputar a cada movimiento
        imputaciones_detalle = []
        for imp in imputaciones:
            mov_id   = int(imp['movimiento_id'])
            monto    = Decimal(str(imp['monto_imputado']))

            # Verificar que el movimiento existe y es del cliente
            mov = db.session.execute(text("""
                SELECT id, saldo_pendiente FROM cta_cte_movimiento
                WHERE id = :id AND cliente_id = :cid AND estado = 'pendiente'
            """), {'id': mov_id, 'cid': cliente_id}).fetchone()

            if not mov:
                db.session.rollback()
                return jsonify({'success': False, 'error': f'Movimiento #{mov_id} no válido'}), 400

            saldo_actual = Decimal(str(mov.saldo_pendiente))
            if monto > saldo_actual + Decimal('0.01'):
                db.session.rollback()
                return jsonify({
                    'success': False,
                    'error': f'El monto a imputar (${monto:.2f}) supera el saldo del movimiento #{mov_id} (${saldo_actual:.2f})'
                }), 400

            # Registrar detalle de imputación
            db.session.execute(text("""
                INSERT INTO recibo_cobro_detalle (recibo_id, movimiento_id, monto_imputado)
                VALUES (:rid, :mid, :monto)
            """), {'rid': recibo_id, 'mid': mov_id, 'monto': float(monto)})

            # Guardar para impresión térmica
            num_cbte = db.session.execute(
                text("SELECT COALESCE(numero_comprobante, '—') FROM cta_cte_movimiento WHERE id=:id"),
                {'id': mov_id}
            ).scalar() or '—'
            imputaciones_detalle.append({'numero_comprobante': num_cbte, 'monto_imputado': float(monto)})

            # Actualizar saldo del movimiento
            nuevo_saldo = max(Decimal('0'), saldo_actual - monto)
            nuevo_estado = 'pagado' if nuevo_saldo <= Decimal('0.01') else 'pendiente'
            db.session.execute(text("""
                UPDATE cta_cte_movimiento
                   SET saldo_pendiente = :saldo, estado = :estado
                 WHERE id = :id
            """), {'saldo': float(nuevo_saldo), 'estado': nuevo_estado, 'id': mov_id})

        # Registrar medios de pago del recibo
        for mp in medios_pago:
            db.session.execute(text("""
                INSERT INTO recibo_cobro_medio (recibo_id, medio, importe, referencia)
                VALUES (:rid, :medio, :importe, :ref)
            """), {
                'rid':    recibo_id,
                'medio':  mp['medio'],
                'importe': float(mp['importe']),
                'ref':    mp.get('referencia') or None,
            })

        db.session.commit()

        # Registrar movimiento de PAGO en cta_cte_movimiento para el Debe/Haber
        db.session.execute(text("""
            INSERT INTO cta_cte_movimiento
                (cliente_id, tipo, tipo_mov, estado, monto_total, saldo_pendiente,
                 numero_comprobante, usuario_id, observaciones, fecha)
            VALUES
                (:cid, 'pago', 'pago', 'pagado', :monto, 0,
                 :numero, :uid, :obs, NOW())
        """), {
            'cid':    cliente_id,
            'monto':  total_medios,
            'numero': numero_recibo,
            'uid':    session['user_id'],
            'obs':    f'Recibo de cobro {numero_recibo}',
        })
        db.session.commit()

        # ── Registrar EFECTIVO del recibo en la caja (si hay caja abierta) ──
        # Solo la parte en efectivo entra a la caja física: débito, crédito,
        # transferencia y saldo_favor no mueven la caja.
        try:
            total_efectivo = sum(
                float(mp.get('importe', 0)) for mp in medios_pago
                if mp.get('medio') == 'efectivo'
            )
            if total_efectivo > 0:
                caja_row = db.session.execute(text("""
                    SELECT id, punto_venta FROM cajas
                    WHERE estado = 'abierta' ORDER BY fecha_apertura DESC LIMIT 1
                """)).fetchone()
                if caja_row:
                    db.session.execute(text("""
                        INSERT INTO movimientos_caja
                            (caja_id, tipo, descripcion, monto, notas, fecha, usuario_id, punto_venta)
                        VALUES (:cid, 'ingreso', :desc, :monto, :notas, NOW(), :uid, :pv)
                    """), {
                        'cid':   caja_row[0],
                        'desc':  f'Cobro {numero_recibo} — efectivo',
                        'monto': total_efectivo,
                        'notas': f'Recibo {numero_recibo}',
                        'uid':   session['user_id'],
                        'pv':    caja_row[1],
                    })
                    db.session.commit()
                    print(f"💵 Cobro {numero_recibo}: ${total_efectivo:.2f} efectivo registrado en caja #{caja_row[0]}")
                else:
                    print(f"⚠️ Cobro {numero_recibo}: NO hay caja abierta — efectivo sin registrar en caja")
        except Exception as e:
            print(f"⚠️ Error registrando cobro en caja (no bloqueante): {e}")

        # Saldo actualizado
        saldo_nuevo = saldo_real_cliente(db, cliente_id)  # fuente única (antes obtener_saldo_cliente, daba mal)

        print(f"✅ Recibo {numero_recibo} emitido — ${total_medios:.2f} — cliente #{cliente_id}")

        # ── Procesar saldo a favor usado ──────────────────────────────────────
        for mp in medios_pago:
            if mp.get('medio') == 'saldo_favor':
                monto_sf = float(mp.get('importe', 0))
                if monto_sf > 0:
                    db.session.execute(text("""
                        INSERT INTO cta_cte_movimiento
                            (cliente_id, tipo, tipo_mov, estado, monto_total, saldo_pendiente,
                             numero_comprobante, usuario_id, observaciones, fecha)
                        VALUES
                            (:cid, 'pago', 'pago', 'pagado', :monto, 0,
                             'SALDO_FAVOR_USADO', :uid, :obs, NOW())
                    """), {
                        'cid':   cliente_id,
                        'monto': monto_sf,
                        'uid':   session['user_id'],
                        'obs':   f'Saldo a favor aplicado en {numero_recibo}',
                    })
                    db.session.commit()
                    print(f"💚 Saldo a favor ${monto_sf:.2f} aplicado en {numero_recibo}")
        # ─────────────────────────────────────────────────────────────────────

        # Impresión térmica automática
        try:
            from impresora_termica import impresora_termica
            recibo_datos = {
                'numero':         numero_recibo,
                'fecha':          datetime.now().strftime('%d/%m/%Y %H:%M'),
                'total':          total_medios,
                'cliente_nombre': db.session.execute(
                    text("SELECT nombre FROM cliente WHERE id=:id"), {'id': cliente_id}
                ).scalar() or '',
                'cliente_doc':    db.session.execute(
                    text("SELECT documento FROM cliente WHERE id=:id"), {'id': cliente_id}
                ).scalar() or '',
                'detalles': imputaciones_detalle,
                'medios_pago':    [{'medio': mp['medio'], 'importe': mp['importe']} for mp in medios_pago],
            }
            impresora_termica.imprimir_recibo(recibo_datos)
        except Exception as e:
            print(f"⚠️ Error en impresión térmica del recibo: {e}")

        return jsonify({
            'success':       True,
            'recibo_id':     recibo_id,
            'numero_recibo': numero_recibo,
            'total':         total_medios,
            'saldo_nuevo':   saldo_nuevo,
        })

    except Exception as e:
        db.session.rollback()
        import traceback; traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@cta_cte_bp.route('/api/cta_cte/recibo/<int:recibo_id>/anular', methods=['POST'])
def api_anular_recibo(recibo_id):
    """
    Anula un recibo de cobro y revierte TODO lo que hizo al cobrar
    (hace lo inverso exacto de api_cobrar_cliente):
      1. Devuelve el monto_imputado a cada movimiento que el recibo
         había saldado (saldo_pendiente vuelve a subir, estado vuelve
         a 'pendiente' si corresponde).
      2. Elimina el movimiento 'pago' que el recibo había creado en
         cta_cte_movimiento (el R0000XXXX).
      3. Marca el recibo como estado='anulada' (NO se borra: queda
         trazabilidad, el recibo existió).
    No borra recibo_cobro_detalle ni recibo_cobro_medio: quedan como
    registro histórico de lo que el recibo había imputado.
    """
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'No autorizado'}), 401
    try:
        # 1. Validar que el recibo existe y no está ya anulado
        recibo = db.session.execute(text("""
            SELECT id, numero, cliente_id, total, estado
            FROM recibo_cobro WHERE id = :id
        """), {'id': recibo_id}).fetchone()

        if not recibo:
            return jsonify({'success': False, 'error': 'Recibo no encontrado'}), 404

        if recibo.estado == 'anulada':
            return jsonify({'success': False,
                            'error': f'El recibo {recibo.numero} ya está anulado'}), 400

        # 2. Devolver el saldo a cada movimiento que este recibo imputó
        imputaciones = db.session.execute(text("""
            SELECT movimiento_id, monto_imputado
            FROM recibo_cobro_detalle WHERE recibo_id = :rid
        """), {'rid': recibo_id}).fetchall()

        revertidos = 0
        for imp in imputaciones:
            # Sumar de nuevo el monto imputado al saldo_pendiente del
            # movimiento, y reabrir su estado a 'pendiente'.
            res = db.session.execute(text("""
                UPDATE cta_cte_movimiento
                   SET saldo_pendiente = saldo_pendiente + :monto,
                       estado = 'pendiente'
                 WHERE id = :mid
            """), {'monto': float(imp.monto_imputado),
                   'mid':   imp.movimiento_id})
            revertidos += res.rowcount

        # 3. Eliminar el movimiento 'pago' que generó el recibo
        #    (se identifica por numero_comprobante = número del recibo)
        db.session.execute(text("""
            DELETE FROM cta_cte_movimiento
             WHERE cliente_id = :cid
               AND tipo_mov = 'pago'
               AND numero_comprobante = :numero
        """), {'cid': recibo.cliente_id, 'numero': recibo.numero})

        # 4. Marcar el recibo como anulado (NO borrar: trazabilidad)
        db.session.execute(text("""
            UPDATE recibo_cobro
               SET estado = 'anulada',
                   observaciones = CONCAT(COALESCE(observaciones,''),
                        ' [ANULADO por usuario ', :uid, ' el ', NOW(), ']')
             WHERE id = :id
        """), {'id': recibo_id, 'uid': session['user_id']})

        # 5. Revertir el ingreso en caja (si el recibo tuvo efectivo):
        #    egreso espejo "ANULACIÓN: ..." en la misma caja del ingreso.
        try:
            mov_caja = db.session.execute(text("""
                SELECT id FROM movimientos_caja
                WHERE descripcion = :descr
                  AND tipo = 'ingreso'
                ORDER BY id DESC LIMIT 1
            """), {'descr': f'Cobro {recibo.numero} — efectivo'}).fetchone()
            if mov_caja:
                db.session.execute(text("""
                    INSERT INTO movimientos_caja
                        (caja_id, tipo, descripcion, monto, notas, fecha, usuario_id, punto_venta)
                    SELECT caja_id, 'egreso',
                           CONCAT('ANULACIÓN: ', descripcion),
                           monto,
                           CONCAT('Anulación recibo ', :numero),
                           NOW(), :uid, punto_venta
                    FROM movimientos_caja WHERE id = :mid
                """), {
                    'numero': recibo.numero,
                    'uid':    session['user_id'],
                    'mid':    mov_caja.id,
                })
                print(f"💵 Anulación {recibo.numero}: egreso espejo registrado en caja")
        except Exception as e:
            print(f"⚠️ No se pudo revertir en caja (no bloqueante): {e}")

        db.session.commit()

        saldo_nuevo = saldo_real_cliente(db, recibo.cliente_id)
        print(f"🔄 Recibo {recibo.numero} ANULADO — {revertidos} movimiento(s) "
              f"reabierto(s) — cliente #{recibo.cliente_id} — "
              f"nuevo saldo ${saldo_nuevo:.2f}")

        return jsonify({
            'success': True,
            'message': f'Recibo {recibo.numero} anulado correctamente. '
                       f'Se reabrieron {revertidos} movimiento(s).',
            'saldo_nuevo': saldo_nuevo
        })

    except Exception as e:
        db.session.rollback()
        import traceback; traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@cta_cte_bp.route('/api/cta_cte/pago_a_cuenta', methods=['POST'])
def api_pago_a_cuenta():
    """Registra un pago a cuenta del cliente sin imputar a comprobantes."""
    if 'user_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    try:
        data       = request.json
        cliente_id = int(data['cliente_id'])
        importe    = float(data['importe'])
        medio      = data.get('medio', 'efectivo')
        obs        = data.get('observaciones') or f'Pago a cuenta — {medio}'

        if importe <= 0:
            return jsonify({'success': False, 'error': 'Importe inválido'}), 400

        # Registrar movimiento de PAGO a cuenta
        db.session.execute(text("""
            INSERT INTO cta_cte_movimiento
                (cliente_id, tipo, tipo_mov, estado, monto_total, saldo_pendiente,
                 numero_comprobante, usuario_id, observaciones, fecha)
            VALUES
                (:cid, 'pago', 'pago', 'pagado', :monto, :monto,
                 'A_CUENTA', :uid, :obs, NOW())
        """), {
            'cid':   cliente_id,
            'monto': importe,
            'uid':   session['user_id'],
            'obs':   obs,
        })

        # Registrar en caja si hay caja abierta
        try:
            caja_row = db.session.execute(text("""
                SELECT id, punto_venta FROM cajas
                WHERE estado = 'abierta' ORDER BY fecha_apertura DESC LIMIT 1
            """)).fetchone()
            if caja_row:
                db.session.execute(text("""
                    INSERT INTO movimientos_caja
                        (caja_id, tipo, descripcion, monto, notas, fecha, usuario_id, punto_venta)
                    VALUES (:cid, 'ingreso', :desc, :monto, :notas, NOW(), :uid, :pv)
                """), {
                    'cid':   caja_row[0],
                    'desc':  f'Pago a cuenta cliente — {medio}',
                    'monto': importe,
                    'notas': obs,
                    'uid':   session['user_id'],
                    'pv':    caja_row[1],
                })
        except Exception as e:
            print(f"⚠️ Error registrando en caja: {e}")

        db.session.commit()

        # Saldo actualizado
        saldo_nuevo = db.session.execute(text("""
            SELECT COALESCE(SUM(saldo_pendiente), 0)
            FROM cta_cte_movimiento
            WHERE cliente_id = :id AND tipo_mov = 'venta'
        """), {'id': cliente_id}).scalar() or 0.0

        return jsonify({'success': True, 'saldo_nuevo': float(saldo_nuevo)})

    except Exception as e:
        db.session.rollback()
        import traceback; traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@cta_cte_bp.route('/api/cta_cte/recibo/buscar', methods=['GET'])
def api_recibo_buscar():
    """Busca un recibo por número."""
    if 'user_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    numero = (request.args.get('numero') or '').strip()
    if not numero:
        return jsonify({'success': False, 'error': 'Número requerido'}), 400
    try:
        r = db.session.execute(text("""
            SELECT r.id, r.numero, r.fecha, r.total, r.estado,
                   c.nombre as cliente_nombre
            FROM recibo_cobro r
            JOIN cliente c ON c.id = r.cliente_id
            WHERE r.numero = :numero
        """), {'numero': numero}).fetchone()
        if not r:
            return jsonify({'success': False, 'recibo': None})
        return jsonify({'success': True, 'recibo': {
            'id':             r.id,
            'numero':         r.numero,
            'fecha':          r.fecha.strftime('%d/%m/%Y %H:%M') if r.fecha else '',
            'total':          float(r.total),
            'estado':         r.estado,
            'cliente_nombre': r.cliente_nombre,
        }})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@cta_cte_bp.route('/api/cta_cte/recibo/ultimos', methods=['GET'])
def api_recibo_ultimos():
    """Devuelve los últimos N recibos emitidos."""
    if 'user_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    try:
        limite = int(request.args.get('limite', 20))
        rows = db.session.execute(text("""
            SELECT r.id, r.numero, r.fecha, r.total, r.estado,
                   c.nombre as cliente_nombre
            FROM recibo_cobro r
            JOIN cliente c ON c.id = r.cliente_id
            WHERE r.estado = 'emitido'
            ORDER BY r.fecha DESC, r.id DESC
            LIMIT :lim
        """), {'lim': limite}).fetchall()
        recibos = [{
            'id':             r.id,
            'numero':         r.numero,
            'fecha':          r.fecha.strftime('%d/%m/%Y %H:%M') if r.fecha else '',
            'total':          float(r.total),
            'cliente_nombre': r.cliente_nombre,
        } for r in rows]
        return jsonify({'success': True, 'recibos': recibos})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@cta_cte_bp.route('/api/cta_cte/recibo/<int:recibo_id>/imprimir_termica', methods=['POST'])
def api_recibo_imprimir_termica(recibo_id):
    """Reimprime un recibo en la térmica."""
    if 'user_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    try:
        r = db.session.execute(text("""
            SELECT r.id, r.numero, r.fecha, r.total,
                   c.nombre as cliente_nombre, c.documento as cliente_doc
            FROM recibo_cobro r JOIN cliente c ON c.id = r.cliente_id
            WHERE r.id = :id
        """), {'id': recibo_id}).fetchone()
        if not r:
            return jsonify({'success': False, 'error': 'Recibo no encontrado'}), 404
        detalles = db.session.execute(text("""
            SELECT d.monto_imputado, m.numero_comprobante
            FROM recibo_cobro_detalle d
            JOIN cta_cte_movimiento m ON m.id = d.movimiento_id
            WHERE d.recibo_id = :rid
        """), {'rid': recibo_id}).fetchall()
        medios = db.session.execute(text("""
            SELECT medio, importe FROM recibo_cobro_medio WHERE recibo_id = :rid
        """), {'rid': recibo_id}).fetchall()
        from impresora_termica import impresora_termica
        recibo_datos = {
            'numero':         r.numero,
            'fecha':          r.fecha.strftime('%d/%m/%Y %H:%M') if r.fecha else '',
            'total':          float(r.total),
            'cliente_nombre': r.cliente_nombre,
            'cliente_doc':    r.cliente_doc or '',
            'detalles':       [{'numero_comprobante': d.numero_comprobante or '—', 'monto_imputado': float(d.monto_imputado)} for d in detalles],
            'medios_pago':    [{'medio': m.medio, 'importe': float(m.importe)} for m in medios],
        }
        ok = impresora_termica.imprimir_recibo(recibo_datos)
        return jsonify({'success': ok})
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@cta_cte_bp.route('/api/cta_cte/recibo/<int:recibo_id>/pdf', methods=['GET'])
def api_recibo_pdf(recibo_id):
    """Genera PDF A4 del recibo de cobro."""
    if 'user_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.units import mm
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
        from reportlab.lib.enums import TA_CENTER
        import io
        from flask import send_file

        # Capturar variables de configuración en el scope local
        try:
            from config_cliente import TICKET_NOMBRE_COMERCIAL as _nombre, TICKET_CUIT_FORMATO as _cuit
        except Exception:
            _nombre = ''
            _cuit = ''

        recibo = db.session.execute(text("""
            SELECT r.id, r.numero, r.fecha, r.total, r.observaciones,
                   c.nombre as cliente_nombre, c.documento as cliente_doc,
                   u.nombre as usuario_nombre
            FROM recibo_cobro r
            JOIN cliente c ON c.id = r.cliente_id
            JOIN usuario u ON u.id = r.usuario_id
            WHERE r.id = :id
        """), {'id': recibo_id}).fetchone()
        if not recibo:
            return jsonify({'error': 'Recibo no encontrado'}), 404

        detalles = db.session.execute(text("""
            SELECT d.monto_imputado, m.numero_comprobante, m.fecha as fecha_comp, m.monto_total
            FROM recibo_cobro_detalle d
            JOIN cta_cte_movimiento m ON m.id = d.movimiento_id
            WHERE d.recibo_id = :rid
        """), {'rid': recibo_id}).fetchall()

        medios = db.session.execute(text("""
            SELECT medio, importe FROM recibo_cobro_medio WHERE recibo_id = :rid
        """), {'rid': recibo_id}).fetchall()

        AZUL  = colors.HexColor("#0A2140")
        AZULM = colors.HexColor("#2473C8")
        GRIS  = colors.HexColor("#444444")
        CLARO = colors.HexColor("#EEF3FA")
        BLANCO = colors.white
        W, H  = A4
        MARGIN = 18*mm
        CW = W - 2*MARGIN
        _numero = recibo.numero

        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4,
                                leftMargin=MARGIN, rightMargin=MARGIN,
                                topMargin=25*mm, bottomMargin=16*mm)

        def hf(canvas, doc):
            canvas.saveState()
            canvas.setFillColor(AZUL)
            canvas.rect(0, H-20*mm, W, 20*mm, fill=1, stroke=0)
            canvas.setFillColor(AZULM)
            canvas.rect(0, H-21.5*mm, W, 1.5*mm, fill=1, stroke=0)
            canvas.setFillColor(BLANCO)
            canvas.setFont("Helvetica-Bold", 13)
            canvas.drawString(MARGIN, H-12*mm, _nombre)
            canvas.setFont("Helvetica", 8.5)
            canvas.drawString(MARGIN, H-18*mm, f"CUIT: {_cuit}")
            canvas.setFont("Helvetica-Bold", 9)
            canvas.drawRightString(W-MARGIN, H-9*mm, "RECIBO DE COBRO")
            canvas.setFont("Helvetica", 7.5)
            canvas.drawRightString(W-MARGIN, H-15*mm, _numero)
            canvas.setFillColor(AZUL)
            canvas.rect(0, 0, W, 12*mm, fill=1, stroke=0)
            canvas.setFillColor(BLANCO)
            canvas.setFont("Helvetica", 7.5)
            canvas.drawCentredString(W/2, 4.5*mm, "FactuFácil · factufacil.ar")
            canvas.restoreState()

        def st(n, **kw):
            d = dict(fontName="Helvetica", fontSize=9, textColor=GRIS)
            d.update(kw)
            return ParagraphStyle(n, **d)

        SB = st("sb", fontName="Helvetica-Bold", fontSize=10, textColor=AZUL)
        SC = st("sc")
        TH = st("th", fontName="Helvetica-Bold", fontSize=8.5, textColor=BLANCO)
        TD = st("td", fontSize=8.5)

        story = [Spacer(1, 3*mm)]
        story.append(Paragraph("RECIBO DE COBRO", st("t", fontName="Helvetica-Bold", fontSize=15, textColor=AZUL, alignment=TA_CENTER, spaceAfter=4*mm)))
        story.append(Paragraph(f"Nro: {recibo.numero} — {recibo.fecha.strftime('%d/%m/%Y %H:%M') if recibo.fecha else ''}", st("s", fontSize=9, textColor=GRIS, alignment=TA_CENTER, spaceAfter=4*mm)))
        story.append(HRFlowable(width="100%", thickness=1.2, color=AZULM, spaceAfter=3*mm))
        story.append(Paragraph("Cliente", SB))
        story.append(Paragraph(f"{recibo.cliente_nombre} — {recibo.cliente_doc or ''}", SC))
        story.append(Spacer(1, 3*mm))

        story.append(Paragraph("Comprobantes Cobrados", SB))
        story.append(Spacer(1, 1*mm))
        det_data = [[Paragraph("Comprobante", TH), Paragraph("Fecha", TH), Paragraph("Total", TH), Paragraph("Cobrado", TH)]]
        for d in detalles:
            det_data.append([
                Paragraph(d.numero_comprobante or '—', TD),
                Paragraph(d.fecha_comp.strftime('%d/%m/%Y') if d.fecha_comp else '', TD),
                Paragraph(f"${float(d.monto_total):,.2f}", TD),
                Paragraph(f"${float(d.monto_imputado):,.2f}", TD),
            ])
        t1 = Table(det_data, colWidths=[CW*0.35, CW*0.2, CW*0.22, CW*0.23])
        t1.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,0),AZUL),
            ("ROWBACKGROUNDS",(0,1),(-1,-1),[CLARO,BLANCO]),
            ("GRID",(0,0),(-1,-1),0.4,colors.HexColor("#C0D4EE")),
            ("PADDING",(0,0),(-1,-1),5),
        ]))
        story.append(t1)
        story.append(Spacer(1, 3*mm))

        story.append(Paragraph("Formas de Cobro", SB))
        story.append(Spacer(1, 1*mm))
        med_data = [[Paragraph("Medio", TH), Paragraph("Importe", TH)]]
        for m in medios:
            med_data.append([Paragraph(m.medio.upper().replace('_',' '), TD), Paragraph(f"${float(m.importe):,.2f}", TD)])
        t2 = Table(med_data, colWidths=[CW*0.6, CW*0.4])
        t2.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,0),AZUL),
            ("ROWBACKGROUNDS",(0,1),(-1,-1),[CLARO,BLANCO]),
            ("GRID",(0,0),(-1,-1),0.4,colors.HexColor("#C0D4EE")),
            ("PADDING",(0,0),(-1,-1),5),
        ]))
        story.append(t2)
        story.append(Spacer(1, 3*mm))

        tot = Table([[
            Paragraph("TOTAL COBRADO:", st("tl", fontName="Helvetica-Bold", fontSize=12, textColor=AZUL)),
            Paragraph(f"${float(recibo.total):,.2f}", st("tv", fontName="Helvetica-Bold", fontSize=12, textColor=AZUL))
        ]], colWidths=[CW*0.6, CW*0.4])
        tot.setStyle(TableStyle([("PADDING",(0,0),(-1,-1),6),("LINEABOVE",(0,0),(-1,0),1.5,AZULM)]))
        story.append(tot)
        story.append(Spacer(1, 15*mm))

        firma = Table([["_"*30, "_"*30],["Firma del cliente","Firma y sello"]], colWidths=[CW*0.5, CW*0.5])
        firma.setStyle(TableStyle([("ALIGN",(0,0),(-1,-1),"CENTER"),("FONTSIZE",(0,1),(-1,1),8),("TEXTCOLOR",(0,1),(-1,1),GRIS)]))
        story.append(firma)

        doc.build(story, onFirstPage=hf, onLaterPages=hf)
        buf.seek(0)
        return send_file(buf, mimetype='application/pdf', as_attachment=False,
                         download_name=f'Recibo_{recibo.numero}.pdf')
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@cta_cte_bp.route('/api/cta_cte/recibo/<int:recibo_id>', methods=['GET'])
def api_recibo_detalle(recibo_id):
    """Detalle completo de un recibo para imprimir o consultar."""
    if 'user_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    try:
        recibo = db.session.execute(text("""
            SELECT r.id, r.numero, r.fecha, r.total, r.observaciones, r.estado,
                   c.nombre as cliente_nombre, c.documento as cliente_doc,
                   u.nombre as usuario_nombre
            FROM recibo_cobro r
            JOIN cliente c ON c.id = r.cliente_id
            JOIN usuario u ON u.id = r.usuario_id
            WHERE r.id = :id
        """), {'id': recibo_id}).fetchone()

        if not recibo:
            return jsonify({'success': False, 'error': 'Recibo no encontrado'}), 404

        detalles = db.session.execute(text("""
            SELECT d.monto_imputado, m.numero_comprobante, m.fecha as fecha_comp, m.monto_total
            FROM recibo_cobro_detalle d
            JOIN cta_cte_movimiento m ON m.id = d.movimiento_id
            WHERE d.recibo_id = :rid
        """), {'rid': recibo_id}).fetchall()

        medios = db.session.execute(text("""
            SELECT medio, importe, referencia
            FROM recibo_cobro_medio WHERE recibo_id = :rid
        """), {'rid': recibo_id}).fetchall()

        return jsonify({
            'success': True,
            'recibo': {
                'id':             recibo.id,
                'numero':         recibo.numero,
                'fecha':          recibo.fecha.strftime('%d/%m/%Y %H:%M') if recibo.fecha else '',
                'total':          float(recibo.total),
                'observaciones':  recibo.observaciones or '',
                'estado':         recibo.estado,
                'cliente_nombre': recibo.cliente_nombre,
                'cliente_doc':    recibo.cliente_doc,
                'usuario_nombre': recibo.usuario_nombre,
                'detalles': [{
                    'numero_comprobante': d.numero_comprobante or '—',
                    'fecha_comprobante':  d.fecha_comp.strftime('%d/%m/%Y') if d.fecha_comp else '',
                    'monto_total':        float(d.monto_total or 0),
                    'monto_imputado':     float(d.monto_imputado),
                } for d in detalles],
                'medios_pago': [{
                    'medio':      m.medio,
                    'importe':    float(m.importe),
                    'referencia': m.referencia or '',
                } for m in medios],
            }
        })
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@cta_cte_bp.route('/cobrar_cliente')
def vista_cobrar_cliente():
    """Pantalla para cobrar a un cliente."""
    if 'user_id' not in session:
        from flask import redirect, url_for
        return redirect(url_for('login'))
    clientes = db.session.execute(text("""
        SELECT id, nombre, documento FROM cliente
        WHERE activo = 1 AND id != 1 ORDER BY nombre
    """)).fetchall()
    return render_template('cobrar_cliente.html', clientes=clientes)


def init_cta_cte(app):
    """
    Inicializa el módulo de cuenta corriente en la app Flask
    
    Uso en app.py:
        from cta_cte import init_cta_cte
        init_cta_cte(app)
    """
    app.register_blueprint(cta_cte_bp)
    print("✅ Módulo CTA.CTE inicializado correctamente")


# ═══════════════════════════════════════════════════════════════════════════════
# CARGA DE SALDO INICIAL — para migración de saldos desde sistema anterior
# ═══════════════════════════════════════════════════════════════════════════════

@cta_cte_bp.route('/api/cta_cte/cargar_saldo_inicial/<int:cliente_id>', methods=['POST'])
def api_cargar_saldo_inicial_cliente(cliente_id):
    """
    Carga un saldo inicial para un cliente como movimiento de cta cte.
    Solo admin.

    Payload:
    {
        "monto":        1234.56,            # > 0 (deuda del cliente hacia el comercio)
        "observaciones": "texto descriptivo"
    }

    Inserta un movimiento tipo='venta_fiada', estado='pendiente', sin detalle de
    productos. Sirve para arrancar la cta cte con el saldo migrado del sistema
    anterior. La descripcion queda como "Saldo inicial: <observaciones>".
    """
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'No autorizado'}), 401

    if session.get('rol') != 'admin':
        return jsonify({'success': False,
                        'error': 'Solo un administrador puede cargar saldos iniciales'}), 403

    try:
        data = request.get_json() or {}

        # Validaciones
        try:
            monto = Decimal(str(data.get('monto') or 0))
        except Exception:
            return jsonify({'success': False, 'error': 'Monto invalido'}), 400
        if monto <= 0:
            return jsonify({'success': False, 'error': 'El monto debe ser mayor a 0'}), 400

        observaciones = (data.get('observaciones') or '').strip()
        if not observaciones:
            observaciones = 'Migrado desde sistema anterior'
        if len(observaciones) > 200:
            observaciones = observaciones[:200]

        # Verificar que el cliente existe
        check = db.session.execute(
            text("SELECT id, nombre FROM cliente WHERE id = :id"),
            {'id': cliente_id}
        ).fetchone()
        if not check:
            return jsonify({'success': False, 'error': 'Cliente no encontrado'}), 404

        descripcion = f'Saldo inicial: {observaciones}'

        # Insertar movimiento
        db.session.execute(text("""
            INSERT INTO cta_cte_movimiento
                (cliente_id, tipo, tipo_mov, estado, monto_total, saldo_pendiente, usuario_id, observaciones, fecha)
            VALUES
                (:cliente_id, 'venta_fiada', 'venta', 'pendiente', :monto, :monto, :uid, :obs, NOW())
        """), {
            'cliente_id': cliente_id,
            'monto':      float(monto),
            'uid':        session['user_id'],
            'obs':        descripcion,
        })

        db.session.commit()

        # Calcular saldo actualizado
        saldo_nuevo = saldo_real_cliente(db, cliente_id)  # fuente única (antes obtener_saldo_cliente, daba mal)

        return jsonify({
            'success': True,
            'saldo_actualizado': saldo_nuevo,
            'cliente_nombre':    check.nombre,
        })

    except Exception as e:
        db.session.rollback()
        import traceback; traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500



# ════════════════════════════════════════════════════════════════════════════
# MÓDULO IMPUTACIÓN DE PAGOS A_CUENTA A FACTURAS
# ════════════════════════════════════════════════════════════════════════════

@cta_cte_bp.route('/api/pago/<int:pago_id>/imputaciones', methods=['GET'])
def api_pago_imputaciones(pago_id):
    """Lista las imputaciones (activas y revertidas) de un pago A_CUENTA,
    con datos de las facturas a las que se imputó. Solo lectura.
    """
    if 'user_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    try:
        pago = db.session.execute(text("""
            SELECT id, cliente_id, fecha, monto_total, saldo_pendiente,
                   tipo, tipo_mov, numero_comprobante, estado, observaciones
            FROM cta_cte_movimiento
            WHERE id = :pid
        """), {'pid': pago_id}).fetchone()
        if pago is None:
            return jsonify({'success': False, 'error': 'Pago no encontrado'}), 404
        if pago.tipo_mov != 'pago' or pago.numero_comprobante != 'A_CUENTA':
            return jsonify({
                'success': False,
                'error': 'El movimiento no es un pago A_CUENTA imputable'
            }), 400

        cliente_row = db.session.execute(text("""
            SELECT id, nombre FROM cliente WHERE id = :cid
        """), {'cid': pago.cliente_id}).fetchone()
        cliente_nombre = cliente_row.nombre if cliente_row else ''

        imputaciones = db.session.execute(text("""
            SELECT
                pi.id, pi.pago_id, pi.factura_id, pi.monto_imputado,
                pi.fecha, pi.usuario_id, pi.estado, pi.fecha_reversion,
                pi.usuario_reversion_id, pi.observaciones,
                f.fecha              AS f_fecha,
                f.numero_comprobante AS f_numero,
                f.monto_total        AS f_total,
                f.saldo_pendiente    AS f_saldo,
                f.estado             AS f_estado
            FROM pago_imputacion pi
            JOIN cta_cte_movimiento f ON f.id = pi.factura_id
            WHERE pi.pago_id = :pid
            ORDER BY pi.fecha DESC, pi.id DESC
        """), {'pid': pago_id}).fetchall()

        result = []
        total_imputado_activo = 0.0
        for imp in imputaciones:
            monto = float(imp.monto_imputado or 0)
            if imp.estado == 'activa':
                total_imputado_activo += monto
            result.append({
                'id':                   imp.id,
                'pago_id':              imp.pago_id,
                'factura_id':           imp.factura_id,
                'monto_imputado':       monto,
                'fecha':                imp.fecha.strftime('%d/%m/%Y %H:%M') if imp.fecha else None,
                'usuario_id':           imp.usuario_id,
                'estado':               imp.estado,
                'fecha_reversion':      imp.fecha_reversion.strftime('%d/%m/%Y %H:%M') if imp.fecha_reversion else None,
                'usuario_reversion_id': imp.usuario_reversion_id,
                'observaciones':        imp.observaciones,
                'factura': {
                    'id':              imp.factura_id,
                    'numero':          imp.f_numero or '',
                    'fecha':           imp.f_fecha.strftime('%d/%m/%Y') if imp.f_fecha else None,
                    'total':           float(imp.f_total or 0),
                    'saldo_pendiente': float(imp.f_saldo or 0),
                    'estado':          imp.f_estado or '',
                },
            })

        return jsonify({
            'success': True,
            'pago': {
                'id':              pago.id,
                'cliente_id':      pago.cliente_id,
                'cliente_nombre':  cliente_nombre,
                'fecha':           pago.fecha.strftime('%d/%m/%Y %H:%M') if pago.fecha else None,
                'monto_total':     float(pago.monto_total or 0),
                'saldo_pendiente': float(pago.saldo_pendiente or 0),
                'estado':          pago.estado,
                'observaciones':   pago.observaciones,
            },
            'imputaciones':         result,
            'total_imputado_activo': total_imputado_activo,
        })
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@cta_cte_bp.route('/api/pago/<int:pago_id>/imputar', methods=['POST'])
def api_pago_imputar(pago_id):
    """Imputa un pago A_CUENTA a una o varias facturas (venta_fiada) del mismo cliente.
    
    SOLO ADMIN. Todo o nada. Optimistic locking. Movimiento decorativo
    en cta_cte_movimiento (debe=0, haber=0) por trazabilidad visual.
    """
    if 'user_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    if session.get('rol') != 'admin':
        return jsonify({'success': False, 'error': 'Solo el administrador puede imputar pagos'}), 403
    
    try:
        data = request.get_json(silent=True) or {}
        imputaciones_data = data.get('imputaciones', [])
        observaciones_in  = (data.get('observaciones') or '').strip()
        
        if not isinstance(imputaciones_data, list) or len(imputaciones_data) == 0:
            return jsonify({'success': False, 'error': 'No se enviaron imputaciones'}), 400
        
        # 1. Lock del pago
        pago = db.session.execute(text("""
            SELECT id, cliente_id, monto_total, saldo_pendiente,
                   tipo, tipo_mov, numero_comprobante, estado
            FROM cta_cte_movimiento
            WHERE id = :pid
            FOR UPDATE
        """), {'pid': pago_id}).fetchone()
        if pago is None:
            return jsonify({'success': False, 'error': 'Pago no encontrado'}), 404
        if pago.tipo_mov != 'pago' or pago.numero_comprobante != 'A_CUENTA':
            return jsonify({
                'success': False,
                'error': 'El movimiento no es un pago A_CUENTA imputable'
            }), 400
        if pago.estado in ('cancelado', 'anulado'):
            return jsonify({'success': False, 'error': f'El pago está {pago.estado}'}), 400
        
        pago_saldo_actual = Decimal(str(pago.saldo_pendiente or 0))
        if pago_saldo_actual <= 0:
            return jsonify({
                'success': False,
                'error': f'El pago ya está totalmente imputado (saldo disponible: ${float(pago_saldo_actual):.2f})'
            }), 400
        
        # 2. Parsear items
        monto_total = Decimal('0')
        parsed = []
        for idx, item in enumerate(imputaciones_data):
            try:
                f_id  = int(item.get('factura_id'))
                monto = Decimal(str(item.get('monto')))
            except (TypeError, ValueError, KeyError):
                return jsonify({
                    'success': False,
                    'error': f'Imputación #{idx+1} inválida: factura_id/monto mal formados'
                }), 400
            if monto <= 0:
                return jsonify({
                    'success': False,
                    'error': f'Imputación #{idx+1}: el monto debe ser positivo'
                }), 400
            parsed.append((f_id, monto))
            monto_total += monto
        
        # 3. Validar monto total ≤ saldo pago
        if monto_total > pago_saldo_actual:
            return jsonify({
                'success': False,
                'error': f'Querés imputar ${float(monto_total):.2f} pero el pago solo tiene ${float(pago_saldo_actual):.2f} disponibles'
            }), 400
        
        # 4. Validar cada factura
        facturas_lock = {}
        for idx, (f_id, monto) in enumerate(parsed):
            if f_id == pago.id:
                return jsonify({
                    'success': False,
                    'error': f'Imputación #{idx+1}: no se puede imputar un pago a sí mismo'
                }), 400
            
            f = db.session.execute(text("""
                SELECT id, cliente_id, monto_total, saldo_pendiente,
                       tipo, tipo_mov, numero_comprobante, estado
                FROM cta_cte_movimiento
                WHERE id = :fid
                FOR UPDATE
            """), {'fid': f_id}).fetchone()
            
            if f is None:
                return jsonify({
                    'success': False,
                    'error': f'Imputación #{idx+1}: factura id={f_id} no encontrada'
                }), 404
            if f.cliente_id != pago.cliente_id:
                return jsonify({
                    'success': False,
                    'error': f'Imputación #{idx+1}: la factura es de otro cliente que el pago'
                }), 400
            if f.tipo != 'venta_fiada':
                return jsonify({
                    'success': False,
                    'error': f'Imputación #{idx+1}: el destino debe ser una venta fiada (tipo actual: {f.tipo})'
                }), 400
            if f.estado in ('cancelado', 'anulado', 'pagado'):
                return jsonify({
                    'success': False,
                    'error': f'Imputación #{idx+1}: la factura {f.numero_comprobante} está {f.estado}'
                }), 400
            
            f_saldo = Decimal(str(f.saldo_pendiente or 0))
            if monto > f_saldo:
                return jsonify({
                    'success': False,
                    'error': f'Imputación #{idx+1}: querés imputar ${float(monto):.2f} a la factura {f.numero_comprobante} pero solo tiene ${float(f_saldo):.2f} pendientes'
                }), 400
            
            facturas_lock[f_id] = (f, monto)
        
        # 5. EJECUCIÓN
        imputaciones_creadas = []
        usuario_id = session.get('user_id')
        
        for f_id, (f, monto) in facturas_lock.items():
            # 5.a — INSERT pago_imputacion
            ins = db.session.execute(text("""
                INSERT INTO pago_imputacion
                    (pago_id, factura_id, monto_imputado, fecha,
                     usuario_id, estado, observaciones)
                VALUES
                    (:pago_id, :factura_id, :monto, NOW(),
                     :usuario_id, 'activa', :obs)
            """), {
                'pago_id':    pago.id,
                'factura_id': f.id,
                'monto':      float(monto),
                'usuario_id': usuario_id,
                'obs':        observaciones_in or None,
            })
            imp_id = ins.lastrowid
            
            # 5.b — Bajar saldo_pendiente de la factura
            nuevo_saldo_factura = Decimal(str(f.saldo_pendiente or 0)) - monto
            if nuevo_saldo_factura <= 0:
                nuevo_saldo_factura = Decimal('0')
                nuevo_estado_factura = 'pagado'
            else:
                nuevo_estado_factura = 'pendiente'  # cta_cte_movimiento usa pendiente/pagado/cancelado
            
            db.session.execute(text("""
                UPDATE cta_cte_movimiento
                SET saldo_pendiente = :saldo, estado = :estado
                WHERE id = :fid
            """), {
                'saldo':  float(nuevo_saldo_factura),
                'estado': nuevo_estado_factura,
                'fid':    f.id,
            })
            
            # 5.c — Movimiento decorativo (debe=0, haber=0) para trazabilidad
            db.session.execute(text("""
                INSERT INTO cta_cte_movimiento
                    (cliente_id, fecha, tipo, tipo_mov, estado,
                     monto_total, saldo_pendiente, factura_id,
                     numero_comprobante, observaciones, usuario_id)
                VALUES
                    (:cliente_id, NOW(), 'ajuste', 'ajuste', 'pagado',
                     0.00, 0.00, :factura_id,
                     :nro, :obs, :usuario_id)
            """), {
                'cliente_id': pago.cliente_id,
                'factura_id': f.id,
                'nro':        f'IMP-{imp_id}',
                'obs':        f'Imputación pago #{pago.id} → Factura #{f.id} por ${float(monto):.2f}',
                'usuario_id': usuario_id,
            })
            
            imputaciones_creadas.append({
                'imputacion_id':        imp_id,
                'factura_id':           f.id,
                'factura_numero':       f.numero_comprobante,
                'monto':                float(monto),
                'factura_estado_nuevo': nuevo_estado_factura,
                'factura_saldo_nuevo':  float(nuevo_saldo_factura),
            })
        
        # 5.d — Bajar saldo_pendiente del pago (estado sigue 'pagado')
        nuevo_saldo_pago = pago_saldo_actual - monto_total
        if nuevo_saldo_pago < 0:
            nuevo_saldo_pago = Decimal('0')
        
        db.session.execute(text("""
            UPDATE cta_cte_movimiento
            SET saldo_pendiente = :saldo
            WHERE id = :pid
        """), {
            'saldo': float(nuevo_saldo_pago),
            'pid':   pago.id,
        })
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'mensaje': f'Imputación realizada: {len(imputaciones_creadas)} factura(s)',
            'imputaciones_creadas': imputaciones_creadas,
            'pago': {
                'id':                       pago.id,
                'saldo_pendiente_nuevo':    float(nuevo_saldo_pago),
                'totalmente_imputado':      (float(nuevo_saldo_pago) == 0),
            },
        })
    
    except Exception as e:
        db.session.rollback()
        import traceback; traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500



@cta_cte_bp.route('/api/imputacion_pago/<int:imp_id>/revertir', methods=['POST'])
def api_imputacion_pago_revertir(imp_id):
    """Revierte una imputación de pago: devuelve el monto a la factura y al pago,
    marca la imputación como 'revertida' (NO la borra, queda historial).
    
    SOLO ADMIN. Optimistic locking. Movimiento decorativo de reversión.
    """
    if 'user_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    if session.get('rol') != 'admin':
        return jsonify({'success': False, 'error': 'Solo el administrador puede revertir imputaciones'}), 403
    
    try:
        data = request.get_json(silent=True) or {}
        motivo = (data.get('motivo') or '').strip()
        
        # 1. Lock de la imputación
        imp = db.session.execute(text("""
            SELECT id, pago_id, factura_id, monto_imputado, estado, observaciones
            FROM pago_imputacion
            WHERE id = :iid
            FOR UPDATE
        """), {'iid': imp_id}).fetchone()
        
        if imp is None:
            return jsonify({'success': False, 'error': 'Imputación no encontrada'}), 404
        if imp.estado != 'activa':
            return jsonify({
                'success': False,
                'error': f'La imputación ya está {imp.estado} (no se puede revertir)'
            }), 400
        
        monto = Decimal(str(imp.monto_imputado or 0))
        
        # 2. Lock del pago
        pago = db.session.execute(text("""
            SELECT id, cliente_id, monto_total, saldo_pendiente, estado,
                   numero_comprobante
            FROM cta_cte_movimiento
            WHERE id = :pid
            FOR UPDATE
        """), {'pid': imp.pago_id}).fetchone()
        if pago is None:
            return jsonify({'success': False, 'error': 'Pago no encontrado'}), 404
        
        # 3. Lock de la factura
        factura = db.session.execute(text("""
            SELECT id, cliente_id, monto_total, saldo_pendiente, estado,
                   numero_comprobante
            FROM cta_cte_movimiento
            WHERE id = :fid
            FOR UPDATE
        """), {'fid': imp.factura_id}).fetchone()
        if factura is None:
            return jsonify({'success': False, 'error': 'Factura no encontrada'}), 404
        if factura.estado in ('anulado', 'cancelado'):
            return jsonify({
                'success': False,
                'error': f'La factura está {factura.estado}, no se puede revertir la imputación'
            }), 400
        
        # 4. EJECUCIÓN
        # 4.a — Marcar imputación como revertida
        nueva_obs = imp.observaciones or ''
        if motivo:
            nueva_obs = (nueva_obs + ' | Revertida: ' + motivo).strip(' |')
        db.session.execute(text("""
            UPDATE pago_imputacion
            SET estado = 'revertida',
                fecha_reversion = NOW(),
                usuario_reversion_id = :uid,
                observaciones = :obs
            WHERE id = :iid
        """), {
            'iid': imp.id,
            'uid': session.get('user_id'),
            'obs': nueva_obs or None,
        })
        
        # 4.b — Devolver saldo a la factura y ajustar estado
        nuevo_saldo_factura = Decimal(str(factura.saldo_pendiente or 0)) + monto
        nuevo_total_factura = Decimal(str(factura.monto_total or 0))
        if nuevo_saldo_factura >= nuevo_total_factura:
            nuevo_saldo_factura = nuevo_total_factura
        nuevo_estado_factura = 'pendiente'
        
        db.session.execute(text("""
            UPDATE cta_cte_movimiento
            SET saldo_pendiente = :saldo, estado = :estado
            WHERE id = :fid
        """), {
            'saldo':  float(nuevo_saldo_factura),
            'estado': nuevo_estado_factura,
            'fid':    factura.id,
        })
        
        # 4.c — Devolver saldo al pago
        nuevo_saldo_pago = Decimal(str(pago.saldo_pendiente or 0)) + monto
        if nuevo_saldo_pago > Decimal(str(pago.monto_total or 0)):
            nuevo_saldo_pago = Decimal(str(pago.monto_total or 0))
        db.session.execute(text("""
            UPDATE cta_cte_movimiento
            SET saldo_pendiente = :saldo
            WHERE id = :pid
        """), {
            'saldo': float(nuevo_saldo_pago),
            'pid':   pago.id,
        })
        
        # 4.d — Movimiento decorativo de reversión (debe=0, haber=0)
        db.session.execute(text("""
            INSERT INTO cta_cte_movimiento
                (cliente_id, fecha, tipo, tipo_mov, estado,
                 monto_total, saldo_pendiente, factura_id,
                 numero_comprobante, observaciones, usuario_id)
            VALUES
                (:cliente_id, NOW(), 'ajuste', 'ajuste', 'pagado',
                 0.00, 0.00, :factura_id,
                 :nro, :obs, :usuario_id)
        """), {
            'cliente_id': pago.cliente_id,
            'factura_id': factura.id,
            'nro':        f'REV-{imp.id}',
            'obs':        f'REVERSIÓN imputación pago #{pago.id} ← Factura #{factura.id} por ${float(monto):.2f}' + (f' — Motivo: {motivo}' if motivo else ''),
            'usuario_id': session.get('user_id'),
        })
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'mensaje': f'Imputación revertida: ${float(monto):.2f}',
            'imputacion': {
                'id':                  imp.id,
                'estado':              'revertida',
                'fecha_reversion':     datetime.now().strftime('%d/%m/%Y %H:%M'),
            },
            'pago': {
                'id':                       pago.id,
                'saldo_pendiente_nuevo':    float(nuevo_saldo_pago),
            },
            'factura': {
                'id':                       factura.id,
                'numero':                   factura.numero_comprobante or '',
                'saldo_pendiente_nuevo':    float(nuevo_saldo_factura),
                'estado_nuevo':             nuevo_estado_factura,
            },
        })
    
    except Exception as e:
        db.session.rollback()
        import traceback; traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500



@cta_cte_bp.route('/api/pagos_a_cuenta_disponibles', methods=['GET'])
def api_pagos_a_cuenta_disponibles():
    """Devuelve todos los pagos A_CUENTA con saldo_pendiente > 0
    (= pagos que todavía tienen crédito por imputar a facturas).
    Sirve para la pantalla 'Pagos a cuenta disponibles' (listado global).
    Opcionalmente filtra por cliente_id.
    """
    if 'user_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    try:
        cliente_id = request.args.get('cliente_id', type=int)
        params = {}
        sql = """
            SELECT m.id, m.cliente_id, m.fecha, m.monto_total, m.saldo_pendiente,
                   m.observaciones, m.numero_comprobante,
                   c.nombre AS cliente_nombre, c.documento AS cliente_doc
            FROM cta_cte_movimiento m
            JOIN cliente c ON c.id = m.cliente_id
            WHERE m.tipo_mov = 'pago'
              AND m.numero_comprobante = 'A_CUENTA'
              AND m.saldo_pendiente > 0
              AND m.estado != 'cancelado'
        """
        if cliente_id:
            sql += " AND m.cliente_id = :cid"
            params['cid'] = cliente_id
        sql += " ORDER BY m.fecha DESC, m.id DESC"
        
        rows = db.session.execute(text(sql), params).fetchall()
        
        result = []
        total_disponible = 0.0
        for r in rows:
            saldo = float(r.saldo_pendiente or 0)
            total_disponible += saldo
            result.append({
                'id':              r.id,
                'cliente_id':      r.cliente_id,
                'cliente_nombre':  r.cliente_nombre,
                'cliente_doc':     r.cliente_doc or '',
                'fecha':           r.fecha.strftime('%d/%m/%Y') if r.fecha else None,
                'fecha_iso':       r.fecha.strftime('%Y-%m-%d') if r.fecha else None,
                'monto_total':     float(r.monto_total or 0),
                'saldo_pendiente': saldo,
                'observaciones':   r.observaciones or '',
            })
        
        return jsonify({
            'success':          True,
            'pagos':            result,
            'total':            len(result),
            'total_disponible': total_disponible,
        })
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500



@cta_cte_bp.route('/imputar_pago/<int:pago_id>', methods=['GET'])
def vista_imputar_pago(pago_id):
    """Pantalla para imputar un pago A_CUENTA a una o varias facturas del cliente."""
    from flask import redirect, url_for
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Buscar el pago
    pago = db.session.execute(text("""
        SELECT id, cliente_id, fecha, monto_total, saldo_pendiente,
               tipo, tipo_mov, numero_comprobante, estado, observaciones
        FROM cta_cte_movimiento
        WHERE id = :pid
    """), {'pid': pago_id}).fetchone()
    
    if pago is None:
        return "Pago no encontrado", 404
    if pago.tipo_mov != 'pago' or pago.numero_comprobante != 'A_CUENTA':
        return "El movimiento no es un pago A_CUENTA imputable", 400
    
    # Buscar cliente
    cliente = db.session.execute(text("""
        SELECT id, nombre, documento FROM cliente WHERE id = :cid
    """), {'cid': pago.cliente_id}).fetchone()
    if cliente is None:
        return "Cliente no encontrado", 404
    
    return render_template('imputar_pago.html', pago=pago, cliente=cliente)



@cta_cte_bp.route('/pagos_a_cuenta_disponibles', methods=['GET'])
def vista_pagos_a_cuenta_disponibles():
    """Pantalla con listado de todos los pagos A_CUENTA con saldo disponible para imputar."""
    from flask import redirect, url_for
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('pagos_a_cuenta_disponibles.html')



@cta_cte_bp.route('/api/pago_a_cuenta/<int:pago_id>/anular', methods=['POST'])
def api_pago_a_cuenta_anular(pago_id):
    """Anula un pago A_CUENTA. 
    
    Reglas:
      - SOLO ADMIN.
      - Si tiene imputaciones activas, las revierte primero (devuelve saldos a facturas).
      - Marca el movimiento como estado='cancelado' y pone monto_total=0, saldo_pendiente=0
        (neutralización matemática: no afecta el saldo del cliente).
      - Si hay movimiento en caja vinculado al pago, también lo marca como cancelado.
      - Guarda usuario + fecha + motivo en observaciones.
    
    Payload (JSON):
      { "motivo": "texto opcional" }
    """
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'No autorizado'}), 401
    if session.get('rol') != 'admin':
        return jsonify({'success': False, 'error': 'Solo el administrador puede anular pagos a cuenta'}), 403
    
    try:
        data = request.get_json(silent=True) or {}
        motivo = (data.get('motivo') or '').strip()
        usuario_id = session.get('user_id')
        
        # 1. Lock del pago
        pago = db.session.execute(text("""
            SELECT id, cliente_id, fecha, monto_total, saldo_pendiente,
                   tipo, tipo_mov, numero_comprobante, estado, observaciones
            FROM cta_cte_movimiento
            WHERE id = :pid
            FOR UPDATE
        """), {'pid': pago_id}).fetchone()
        
        if pago is None:
            return jsonify({'success': False, 'error': 'Pago no encontrado'}), 404
        if pago.tipo_mov != 'pago' or pago.numero_comprobante != 'A_CUENTA':
            return jsonify({
                'success': False,
                'error': 'El movimiento no es un pago A_CUENTA anulable'
            }), 400
        if pago.estado in ('cancelado', 'anulado', 'anulada'):
            return jsonify({
                'success': False,
                'error': f'El pago ya está {pago.estado}'
            }), 400
        
        # 2. Revertir imputaciones activas (si las hay)
        imps_activas = db.session.execute(text("""
            SELECT id, pago_id, factura_id, monto_imputado
            FROM pago_imputacion
            WHERE pago_id = :pid AND estado = 'activa'
            FOR UPDATE
        """), {'pid': pago_id}).fetchall()
        
        imps_revertidas = []
        for imp in imps_activas:
            monto_imp = Decimal(str(imp.monto_imputado or 0))
            
            # Lock factura
            factura = db.session.execute(text("""
                SELECT id, monto_total, saldo_pendiente, estado, numero_comprobante
                FROM cta_cte_movimiento
                WHERE id = :fid
                FOR UPDATE
            """), {'fid': imp.factura_id}).fetchone()
            
            if factura is None:
                return jsonify({
                    'success': False,
                    'error': f'Factura id={imp.factura_id} no encontrada al revertir imputación {imp.id}'
                }), 404
            
            # Devolver saldo a la factura
            nuevo_saldo_factura = Decimal(str(factura.saldo_pendiente or 0)) + monto_imp
            nuevo_total_factura = Decimal(str(factura.monto_total or 0))
            if nuevo_saldo_factura >= nuevo_total_factura and nuevo_total_factura > 0:
                nuevo_saldo_factura = nuevo_total_factura
            
            db.session.execute(text("""
                UPDATE cta_cte_movimiento
                SET saldo_pendiente = :saldo, estado = 'pendiente'
                WHERE id = :fid
            """), {
                'saldo': float(nuevo_saldo_factura),
                'fid':   factura.id,
            })
            
            # Marcar imputación como revertida
            obs_imp = f'Anulación pago #{pago.id}'
            if motivo:
                obs_imp += f' — Motivo: {motivo}'
            db.session.execute(text("""
                UPDATE pago_imputacion
                SET estado = 'revertida',
                    fecha_reversion = NOW(),
                    usuario_reversion_id = :uid,
                    observaciones = CONCAT(COALESCE(observaciones,''), ' | ', :obs)
                WHERE id = :iid
            """), {
                'iid': imp.id,
                'uid': usuario_id,
                'obs': obs_imp,
            })
            
            imps_revertidas.append({
                'imputacion_id':         imp.id,
                'factura_id':            factura.id,
                'factura_numero':        factura.numero_comprobante or '',
                'monto':                 float(monto_imp),
                'factura_saldo_nuevo':   float(nuevo_saldo_factura),
            })
        
        # 3. Anular el movimiento del pago (neutralización matemática)
        obs_nueva = (pago.observaciones or '').strip()
        marca_anulacion = f'[ANULADO {datetime.now().strftime("%d/%m/%Y %H:%M")} usuario={usuario_id}'
        if motivo:
            marca_anulacion += f' — Motivo: {motivo}'
        marca_anulacion += ']'
        obs_nueva = (obs_nueva + ' ' + marca_anulacion).strip()
        if len(obs_nueva) > 500:
            obs_nueva = obs_nueva[:500]
        
        db.session.execute(text("""
            UPDATE cta_cte_movimiento
            SET estado = 'cancelado',
                monto_total = 0,
                saldo_pendiente = 0,
                observaciones = :obs
            WHERE id = :pid
        """), {
            'obs': obs_nueva,
            'pid': pago.id,
        })
        
        # 4. Anular movimiento de caja si existe (buscar por descripción y fecha)
        caja_anulada = False
        try:
            mov_caja = db.session.execute(text("""
                SELECT id FROM movimientos_caja
                WHERE notas = :obs_pago
                  AND monto = :monto
                  AND DATE(fecha) = DATE(:fecha_pago)
                  AND tipo = 'ingreso'
                ORDER BY id DESC LIMIT 1
            """), {
                'obs_pago': pago.observaciones,
                'monto': float(pago.monto_total or 0),
                'fecha_pago': pago.fecha,
            }).fetchone()
            if mov_caja:
                db.session.execute(text("""
                    INSERT INTO movimientos_caja
                        (caja_id, tipo, descripcion, monto, notas, fecha, usuario_id, punto_venta)
                    SELECT caja_id, 'egreso',
                           CONCAT('ANULACIÓN: ', descripcion),
                           monto,
                           CONCAT('Anulación pago a cuenta #', :pid, COALESCE(NULLIF(:motivo, ''), '')),
                           NOW(), :uid, punto_venta
                    FROM movimientos_caja WHERE id = :mid
                """), {
                    'pid':    pago.id,
                    'motivo': f' — Motivo: {motivo}' if motivo else '',
                    'uid':    usuario_id,
                    'mid':    mov_caja.id,
                })
                caja_anulada = True
        except Exception as e:
            print(f"⚠️ No se pudo anular en caja (no es bloqueante): {e}")
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'mensaje': f'Pago a cuenta #{pago.id} anulado correctamente',
            'pago': {
                'id': pago.id,
                'estado_nuevo': 'cancelado',
                'monto_anulado': float(pago.monto_total or 0),
            },
            'imputaciones_revertidas': imps_revertidas,
            'caja_anulada': caja_anulada,
        })
    
    except Exception as e:
        db.session.rollback()
        import traceback; traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500



# =====================================================================
# PDF: TOP DE CLIENTES MOROSOS
# =====================================================================
@cta_cte_bp.route('/api/cta_cte/morosos_pdf')
def api_morosos_pdf():
    """PDF con el top de clientes con mayor saldo deudor.
    Usa la MISMA fórmula de saldo que la grilla y el historial:
    deuda (venta_fiada) - notas de crédito - saldo a favor neto."""
    if 'user_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    try:
        top = max(1, min(request.args.get('top', 20, type=int), 100))
        vendedor_id = request.args.get('vendedor_id', type=int)

        # Con vendedor: filtro + LIMIT en SQL. Sin vendedor: traigo todos los
        # deudores y el top N se aplica POR VENDEDOR al agrupar.
        filtro_vendedor = "AND c.vendedor_id = :vid" if vendedor_id else ""
        limite_sql = "LIMIT :top" if vendedor_id else ""
        params = {'top': top}
        if vendedor_id:
            params['vid'] = vendedor_id

        rows = db.session.execute(text(f"""
            SELECT c.id, c.nombre, c.vendedor_id,
                   COALESCE(c.telefono, '') AS telefono,
                   (
                     COALESCE((
                       SELECT SUM(m.saldo_pendiente) FROM cta_cte_movimiento m
                       WHERE m.cliente_id = c.id AND m.tipo = 'venta_fiada'
                     ), 0)
                     -
                     COALESCE((
                       SELECT SUM(m.monto_total) FROM cta_cte_movimiento m
                       WHERE m.cliente_id = c.id AND m.tipo = 'nota_credito'
                     ), 0)
                     -
                     (
                       COALESCE((
                         SELECT SUM(m.saldo_pendiente) FROM cta_cte_movimiento m
                         WHERE m.cliente_id = c.id AND m.tipo_mov = 'pago'
                           AND m.numero_comprobante IN ('A_CUENTA', 'LIQUIDACION')
                       ), 0)
                       -
                       COALESCE((
                         SELECT SUM(m.monto_total) FROM cta_cte_movimiento m
                         WHERE m.cliente_id = c.id AND m.tipo_mov = 'pago'
                           AND m.numero_comprobante IN ('SALDO_FAVOR_USADO', 'LIQUIDACION_PAGADA')
                       ), 0)
                     )
                   ) AS saldo
              FROM cliente c
             WHERE EXISTS (SELECT 1 FROM cta_cte_movimiento m WHERE m.cliente_id = c.id)
                   {filtro_vendedor}
            HAVING saldo > 0.009
             ORDER BY saldo DESC
             {limite_sql}
        """), params).mappings().all()

        # Nombres de vendedores (id -> nombre) para títulos y agrupado
        vendedores_map = {}
        try:
            for v in db.session.execute(text("SELECT id, nombre FROM vendedor")).mappings().all():
                vendedores_map[v['id']] = v['nombre']
        except Exception as e_v:
            print(f"WARN morosos_pdf: tabla vendedor no disponible ({e_v})")

        def _esc(s):
            return str(s).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

        nombre_vendedor = (vendedores_map.get(vendedor_id, f'Vendedor #{vendedor_id}')
                           if vendedor_id else None)

        # ── Membrete: datos del negocio (mismo origen que la factura) ──
        emisor_nombre, emisor_detalles, logo_path, simbolo = '', [], None, '$'
        try:
            import os
            import config_cliente as _cfg
            emisor_nombre = (getattr(_cfg, 'TICKET_NOMBRE_COMERCIAL', '') or
                             getattr(_cfg, 'RAZON_SOCIAL', '') or '')
            razon = getattr(_cfg, 'RAZON_SOCIAL', '') or ''
            if razon and razon != emisor_nombre:
                emisor_detalles.append(razon)
            doc_e = (getattr(_cfg, 'TICKET_CUIT_FORMATO', None) or getattr(_cfg, 'CUIT', None) or
                     getattr(_cfg, 'NIF', None) or getattr(_cfg, 'CIF', None))
            if doc_e:
                et = 'CUIT' if (getattr(_cfg, 'CUIT', None) or
                                getattr(_cfg, 'TICKET_CUIT_FORMATO', None)) else 'NIF'
                emisor_detalles.append(f"{et}: {doc_e}")
            if getattr(_cfg, 'NIF', None) or getattr(_cfg, 'CIF', None):
                simbolo = '€'
            # El logo del PDF sale SIEMPRE de static/logo.png de ESTA
            # instalación (ruta absoluta anclada a la carpeta de la app).
            # Sin logo => borrar/renombrar ese archivo.
            base_dir = os.path.dirname(os.path.abspath(__file__))
            cand = os.path.join(base_dir, 'static', 'logo.png')
            if os.path.exists(cand):
                logo_path = cand
            print(f"PDF logo: {logo_path or 'SIN LOGO'} (buscado en {cand})")
        except Exception as e_cfg:
            print(f"WARN morosos_pdf: sin datos de config_cliente ({e_cfg})")
        if not emisor_nombre:
            emisor_nombre = 'FactuFacil'

        # ── PDF ──
        from flask import send_file
        from io import BytesIO
        from datetime import datetime as _dt
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import mm
        from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                        Table, TableStyle)

        buf = BytesIO()
        pdf_doc = SimpleDocTemplate(buf, pagesize=A4,
                                    topMargin=18*mm, bottomMargin=18*mm,
                                    leftMargin=16*mm, rightMargin=16*mm)
        styles = getSampleStyleSheet()
        st_titulo = ParagraphStyle('t', parent=styles['Title'], fontSize=17, spaceAfter=2)
        st_sub = ParagraphStyle('s', parent=styles['Normal'], fontSize=9,
                                textColor=colors.grey)
        st_norm = styles['Normal']
        ahora = _dt.now()

        elems = []
        if logo_path:
            try:
                from reportlab.platypus import Image as RLImage
                from reportlab.lib.utils import ImageReader
                iw, ih = ImageReader(logo_path).getSize()
                alto = 16*mm
                elems.append(RLImage(logo_path, width=alto * iw / ih, height=alto,
                                     hAlign='LEFT'))
                elems.append(Spacer(1, 3*mm))
            except Exception as e_logo:
                print(f"WARN morosos_pdf: logo ({e_logo})")
        elems.append(Paragraph(f'CLIENTES MOROSOS — TOP {top}', st_titulo))
        if nombre_vendedor:
            elems.append(Paragraph(f"Vendedor: <b>{_esc(nombre_vendedor)}</b>", st_sub))
        cab = f"<b>{emisor_nombre}</b>"
        if emisor_detalles:
            cab += ' &nbsp;·&nbsp; ' + ' &nbsp;·&nbsp; '.join(str(d) for d in emisor_detalles)
        elems.append(Paragraph(cab, st_sub))
        elems.append(Paragraph(f"Fecha: {ahora.strftime('%d/%m/%Y %H:%M')} — "
                               f"Saldos de cuenta corriente al momento de emisión", st_sub))
        elems.append(Spacer(1, 6*mm))

        def _f(n):
            return f"{simbolo} {float(n):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

        ESTILO_TABLA = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#212529')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),
            ('ALIGN', (3, 0), (3, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#adb5bd')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#f8f9fa')]),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#f1d4d4')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ])

        def _tabla_morosos(filas):
            head = ['#', 'Cliente', 'Teléfono', 'Saldo deudor']
            body = [[str(i + 1), r['nombre'], r['telefono'], _f(r['saldo'])]
                    for i, r in enumerate(filas)]
            total = sum(float(r['saldo']) for r in filas)
            body.append(['', '', 'TOTAL', _f(total)])
            t = Table([head] + body,
                      colWidths=[12*mm, 88*mm, 38*mm, 36*mm], repeatRows=1)
            t.setStyle(ESTILO_TABLA)
            return t, total

        if not rows:
            elems.append(Paragraph('No hay clientes con saldo deudor. ¡Felicitaciones!', st_norm))
        elif vendedor_id:
            # ── Un solo vendedor: tabla simple (ya viene filtrada y limitada) ──
            tabla, _total = _tabla_morosos(rows)
            elems.append(tabla)
        else:
            # ── Todos: agrupado por vendedor, salto de hoja entre vendedores,
            #    top N POR vendedor, "Sin vendedor asignado" al final ──
            from reportlab.platypus import PageBreak
            st_vend = ParagraphStyle('v', parent=styles['Heading2'], fontSize=13,
                                     spaceAfter=3, textColor=colors.HexColor('#212529'))
            grupos = {}
            for r in rows:
                grupos.setdefault(r['vendedor_id'], []).append(r)
            claves = sorted([k for k in grupos.keys() if k is not None],
                            key=lambda k: (vendedores_map.get(k) or f'Vendedor #{k}').upper())
            if None in grupos:
                claves.append(None)
            total_general = 0.0
            for idx, k in enumerate(claves):
                filas = grupos[k][:top]  # ya vienen ordenadas por saldo DESC
                nombre_g = (vendedores_map.get(k, f'Vendedor #{k}')
                            if k is not None else 'Sin vendedor asignado')
                if idx > 0:
                    elems.append(PageBreak())
                elems.append(Paragraph(f'Vendedor: {_esc(nombre_g)}', st_vend))
                tabla, total_g = _tabla_morosos(filas)
                elems.append(tabla)
                total_general += total_g
            elems.append(Spacer(1, 5*mm))
            elems.append(Paragraph(
                f"Total general (todos los vendedores): <b>{_f(total_general)}</b>", st_norm))

        elems.append(Spacer(1, 8*mm))
        usuario = session.get('nombre', '') or ''
        pie = (f"Generado por {usuario} — FactuFácil — {ahora.strftime('%d/%m/%Y %H:%M')}"
               if usuario else
               f"Generado con FactuFácil — {ahora.strftime('%d/%m/%Y %H:%M')}")
        elems.append(Paragraph(pie, st_sub))

        pdf_doc.build(elems)
        buf.seek(0)
        return send_file(buf, mimetype='application/pdf', as_attachment=False,
                         download_name=f"morosos_top{top}_{ahora.strftime('%Y%m%d_%H%M')}.pdf")
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


# ═══════════════════════════════════════════════════════════════════════════════
# DEUDA POR CLIENTE — listado detallado de comprobantes pendientes
# (estilo "Vencimientos Pendientes": Cliente → comprobantes → Total Cliente)
# Usa la MISMA fórmula que saldo_real_cliente / morosos_pdf para que el
# Total Cliente coincida con la grilla y la cta.cte desglosada.
# ═══════════════════════════════════════════════════════════════════════════════

def _deuda_clientes_data(db):
    """Arma la estructura del listado de deuda agrupado por cliente.

    Returns: lista de dicts:
      { 'cliente_id', 'nombre', 'documento', 'telefono', 'saldo',
        'filas': [ {fecha, tipo, comprobante, importe, saldo, dias}, ... ] }

    Filas incluidas por cliente (para que el total cierre con saldo_real):
      - ventas fiadas con saldo_pendiente > 0 (facturas e internos)
      - notas de crédito (restan, monto_total completo)
      - pagos a cuenta sin imputar (resta el neto, una sola línea)
    Solo se listan clientes con saldo neto deudor (> 0).
    """
    # 1) Saldo neto por cliente (misma fórmula que saldo_real_cliente)
    saldos = db.session.execute(text("""
        SELECT c.id, c.nombre,
               COALESCE(c.documento, '') AS documento,
               COALESCE(c.telefono, '')  AS telefono,
               c.dias_vencimiento_factura AS dias_venc,
               (
                 COALESCE((
                   SELECT SUM(m.saldo_pendiente) FROM cta_cte_movimiento m
                   WHERE m.cliente_id = c.id AND m.tipo = 'venta_fiada'
                 ), 0)
                 -
                 COALESCE((
                   SELECT SUM(m.monto_total) FROM cta_cte_movimiento m
                   WHERE m.cliente_id = c.id AND m.tipo = 'nota_credito'
                 ), 0)
                 -
                 (
                   COALESCE((
                     SELECT SUM(m.saldo_pendiente) FROM cta_cte_movimiento m
                     WHERE m.cliente_id = c.id AND m.tipo_mov = 'pago'
                       AND m.numero_comprobante IN ('A_CUENTA', 'LIQUIDACION')
                   ), 0)
                   -
                   COALESCE((
                     SELECT SUM(m.monto_total) FROM cta_cte_movimiento m
                     WHERE m.cliente_id = c.id AND m.tipo_mov = 'pago'
                       AND m.numero_comprobante IN ('SALDO_FAVOR_USADO', 'LIQUIDACION_PAGADA')
                   ), 0)
                 )
               ) AS saldo
          FROM cliente c
         WHERE EXISTS (SELECT 1 FROM cta_cte_movimiento m WHERE m.cliente_id = c.id)
        HAVING saldo > 0.009
         ORDER BY c.nombre
    """)).mappings().all()
    if not saldos:
        return []

    ids = [r['id'] for r in saldos]

    # Días de vencimiento configurados por cliente (NULL = sin vencimiento)
    dias_venc_map = {r['id']: r['dias_venc'] for r in saldos}

    from datetime import date, timedelta
    hoy = date.today()

    def _fecha_a_date(fch):
        return fch.date() if hasattr(fch, 'date') else fch

    # 2) Detalle: ventas fiadas pendientes
    pend = db.session.execute(text("""
        SELECT m.cliente_id, m.fecha, m.numero_comprobante, m.monto_total,
               m.saldo_pendiente, DATEDIFF(NOW(), m.fecha) AS dias,
               COALESCE(f.tipo_comprobante, '') AS tipo_comprobante
          FROM cta_cte_movimiento m
          LEFT JOIN factura f ON m.factura_id = f.id
         WHERE m.cliente_id IN :ids
           AND m.tipo = 'venta_fiada'
           AND m.estado = 'pendiente'
           AND m.saldo_pendiente > 0.009
         ORDER BY m.cliente_id, m.fecha
    """), {'ids': tuple(ids)}).mappings().all()

    # 3) Detalle: notas de crédito (restan completas, igual que la fórmula)
    ncs = db.session.execute(text("""
        SELECT m.cliente_id, m.fecha, m.numero_comprobante, m.monto_total,
               DATEDIFF(NOW(), m.fecha) AS dias
          FROM cta_cte_movimiento m
         WHERE m.cliente_id IN :ids
           AND m.tipo = 'nota_credito'
           AND m.monto_total > 0.009
         ORDER BY m.cliente_id, m.fecha
    """), {'ids': tuple(ids)}).mappings().all()

    # 4) Saldo a favor neto (pagos a cuenta / liquidaciones sin imputar)
    favor = db.session.execute(text("""
        SELECT m.cliente_id,
               ( COALESCE(SUM(CASE WHEN m.numero_comprobante IN ('A_CUENTA', 'LIQUIDACION')
                                   THEN m.saldo_pendiente END), 0)
                 -
                 COALESCE(SUM(CASE WHEN m.numero_comprobante IN ('SALDO_FAVOR_USADO', 'LIQUIDACION_PAGADA')
                                   THEN m.monto_total END), 0)
               ) AS neto
          FROM cta_cte_movimiento m
         WHERE m.cliente_id IN :ids AND m.tipo_mov = 'pago'
         GROUP BY m.cliente_id
        HAVING neto > 0.009
    """), {'ids': tuple(ids)}).mappings().all()
    favor_map = {r['cliente_id']: float(r['neto']) for r in favor}

    # 5) Armar estructura
    por_cliente = {r['id']: {
        'cliente_id': r['id'],
        'nombre':     r['nombre'],
        'documento':  r['documento'],
        'telefono':   r['telefono'],
        'saldo':      float(r['saldo']),
        'filas':      [],
    } for r in saldos}

    for r in pend:
        cid = r['cliente_id']
        dv = dias_venc_map.get(cid)
        vto_str, dias_val = '', ''
        if dv is not None and r['fecha']:
            vto_d = _fecha_a_date(r['fecha']) + timedelta(days=int(dv))
            vto_str = vto_d.strftime('%d/%m/%Y')
            dias_val = (hoy - vto_d).days  # >0 vencida, <0 faltan días
        por_cliente[cid]['filas'].append({
            'fecha':       r['fecha'].strftime('%d/%m/%Y') if r['fecha'] else '',
            'vto':         vto_str,
            'tipo':        r['tipo_comprobante'] or 'CTA',
            'comprobante': r['numero_comprobante'] or chr(8212),
            'importe':     float(r['monto_total'] or 0),
            'saldo':       float(r['saldo_pendiente'] or 0),
            'dias':        dias_val,
        })
    for r in ncs:
        por_cliente[r['cliente_id']]['filas'].append({
            'fecha':       r['fecha'].strftime('%d/%m/%Y') if r['fecha'] else '',
            'vto':         '',
            'tipo':        'NC',
            'comprobante': r['numero_comprobante'] or 'Nota de crédito',
            'importe':     -float(r['monto_total'] or 0),
            'saldo':       -float(r['monto_total'] or 0),
            'dias':        '',
        })
    for cid, neto in favor_map.items():
        por_cliente[cid]['filas'].append({
            'fecha':       '',
            'vto':         '',
            'tipo':        'PAGO',
            'comprobante': 'Pagos a cuenta sin imputar',
            'importe':     -neto,
            'saldo':       -neto,
            'dias':        '',
        })

    # Orden ya viene por nombre desde la query de saldos
    return [por_cliente[r['id']] for r in saldos]


@cta_cte_bp.route('/deuda_clientes')
def vista_deuda_clientes():
    """Pantalla del listado de deuda por cliente."""
    if 'user_id' not in session:
        from flask import redirect, url_for
        return redirect(url_for('login'))
    return render_template('deuda_clientes.html')


@cta_cte_bp.route('/api/cta_cte/deuda_clientes')
def api_deuda_clientes():
    """JSON: comprobantes pendientes agrupados por cliente + totales."""
    if 'user_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    try:
        clientes = _deuda_clientes_data(db)
        total = sum(c['saldo'] for c in clientes)
        return jsonify({
            'success':       True,
            'clientes':      clientes,
            'total_general': total,
            'cantidad':      len(clientes),
            'fecha':         datetime.now().strftime('%d/%m/%Y %H:%M'),
        })
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@cta_cte_bp.route('/api/cta_cte/deuda_clientes_pdf')
def api_deuda_clientes_pdf():
    """PDF del listado de deuda agrupado por cliente (estilo vencimientos
    pendientes): por cada cliente sus comprobantes con saldo, subtotal por
    cliente y total general."""
    if 'user_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    try:
        clientes = _deuda_clientes_data(db)

        # ── Membrete: datos del negocio (mismo patrón que morosos_pdf) ──
        emisor_nombre, emisor_detalles, logo_path, simbolo = '', [], None, '$'
        try:
            import os
            import config_cliente as _cfg
            emisor_nombre = (getattr(_cfg, 'TICKET_NOMBRE_COMERCIAL', '') or
                             getattr(_cfg, 'RAZON_SOCIAL', '') or '')
            razon = getattr(_cfg, 'RAZON_SOCIAL', '') or ''
            if razon and razon != emisor_nombre:
                emisor_detalles.append(razon)
            doc_e = (getattr(_cfg, 'TICKET_CUIT_FORMATO', None) or getattr(_cfg, 'CUIT', None) or
                     getattr(_cfg, 'NIF', None) or getattr(_cfg, 'CIF', None))
            if doc_e:
                et = 'CUIT' if (getattr(_cfg, 'CUIT', None) or
                                getattr(_cfg, 'TICKET_CUIT_FORMATO', None)) else 'NIF'
                emisor_detalles.append(f"{et}: {doc_e}")
            if getattr(_cfg, 'NIF', None) or getattr(_cfg, 'CIF', None):
                simbolo = chr(8364)  # euro
            base_dir = os.path.dirname(os.path.abspath(__file__))
            cand = os.path.join(base_dir, 'static', 'logo.png')
            if os.path.exists(cand):
                logo_path = cand
        except Exception as e_cfg:
            print(f"WARN deuda_clientes_pdf: sin datos de config_cliente ({e_cfg})")
        if not emisor_nombre:
            emisor_nombre = 'FactuFacil'

        # ── PDF ──
        from flask import send_file
        from io import BytesIO
        from datetime import datetime as _dt
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import mm
        from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                        Table, TableStyle)

        buf = BytesIO()
        pdf_doc = SimpleDocTemplate(buf, pagesize=A4,
                                    topMargin=16*mm, bottomMargin=16*mm,
                                    leftMargin=14*mm, rightMargin=14*mm)
        styles = getSampleStyleSheet()
        st_titulo = ParagraphStyle('t', parent=styles['Title'], fontSize=16, spaceAfter=2)
        st_sub = ParagraphStyle('s', parent=styles['Normal'], fontSize=9,
                                textColor=colors.grey)
        st_norm = styles['Normal']
        ahora = _dt.now()

        def _f(n):
            return f"{simbolo} {float(n):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

        elems = []
        if logo_path:
            try:
                from reportlab.platypus import Image as RLImage
                from reportlab.lib.utils import ImageReader
                iw, ih = ImageReader(logo_path).getSize()
                alto = 16*mm
                elems.append(RLImage(logo_path, width=alto * iw / ih, height=alto,
                                     hAlign='LEFT'))
                elems.append(Spacer(1, 3*mm))
            except Exception as e_logo:
                print(f"WARN deuda_clientes_pdf: logo ({e_logo})")
        elems.append(Paragraph('DEUDA PENDIENTE POR CLIENTE', st_titulo))
        cab = f"<b>{emisor_nombre}</b>"
        if emisor_detalles:
            cab += ' &nbsp;&middot;&nbsp; ' + ' &nbsp;&middot;&nbsp; '.join(str(d) for d in emisor_detalles)
        elems.append(Paragraph(cab, st_sub))
        elems.append(Paragraph(f"Fecha: {ahora.strftime('%d/%m/%Y %H:%M')} &mdash; "
                               f"Saldos de cuenta corriente al momento de emisi&oacute;n", st_sub))
        elems.append(Spacer(1, 5*mm))

        if not clientes:
            elems.append(Paragraph('No hay clientes con saldo deudor. &iexcl;Felicitaciones!', st_norm))
        else:
            GRIS_CAB   = colors.HexColor('#212529')
            GRIS_CLI   = colors.HexColor('#dee2e6')
            GRIS_TOT   = colors.HexColor('#f1f3f5')
            ROJO_TOTAL = colors.HexColor('#f1d4d4')
            BORDE      = colors.HexColor('#adb5bd')

            head = ['Fecha', 'Vto', 'Tipo', 'Comprobante', 'Importe', 'Saldo', 'Dias']
            data = [head]
            estilos = [
                ('BACKGROUND', (0, 0), (-1, 0), GRIS_CAB),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8.2),
                ('GRID', (0, 0), (-1, -1), 0.35, BORDE),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ALIGN', (4, 0), (5, -1), 'RIGHT'),
                ('ALIGN', (6, 0), (6, -1), 'CENTER'),
                ('TOPPADDING', (0, 0), (-1, -1), 2.5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
            ]

            total_general = 0.0
            for c in clientes:
                # Fila encabezado de cliente (span completo)
                fila_cli = len(data)
                doc_cli = f" - {c['documento']}" if c['documento'] else ''
                data.append([f"{c['nombre']}{doc_cli}", '', '', '', '', '', ''])
                estilos += [
                    ('SPAN', (0, fila_cli), (-1, fila_cli)),
                    ('BACKGROUND', (0, fila_cli), (-1, fila_cli), GRIS_CLI),
                    ('FONTNAME', (0, fila_cli), (-1, fila_cli), 'Helvetica-Bold'),
                ]
                # Detalle
                for f_ in c['filas']:
                    fila_n = len(data)
                    data.append([
                        f_['fecha'], f_['vto'], f_['tipo'], f_['comprobante'],
                        _f(f_['importe']), _f(f_['saldo']),
                        str(f_['dias']) if f_['dias'] != '' else '',
                    ])
                    if isinstance(f_['dias'], int) and f_['dias'] > 0:
                        estilos += [
                            ('TEXTCOLOR', (6, fila_n), (6, fila_n), colors.HexColor('#dc3545')),
                            ('FONTNAME', (6, fila_n), (6, fila_n), 'Helvetica-Bold'),
                        ]
                # Total cliente
                fila_tot = len(data)
                data.append(['', '', '', 'Total Cliente', '', _f(c['saldo']), ''])
                estilos += [
                    ('BACKGROUND', (0, fila_tot), (-1, fila_tot), GRIS_TOT),
                    ('FONTNAME', (0, fila_tot), (-1, fila_tot), 'Helvetica-Bold'),
                ]
                total_general += c['saldo']

            # Total general
            fila_tg = len(data)
            data.append(['', '', '', 'TOTAL GENERAL', '', _f(total_general), ''])
            estilos += [
                ('BACKGROUND', (0, fila_tg), (-1, fila_tg), ROJO_TOTAL),
                ('FONTNAME', (0, fila_tg), (-1, fila_tg), 'Helvetica-Bold'),
                ('FONTSIZE', (0, fila_tg), (-1, fila_tg), 9),
            ]

            tabla = Table(data,
                          colWidths=[20*mm, 20*mm, 12*mm, 58*mm, 28*mm, 28*mm, 12*mm],
                          repeatRows=1)
            tabla.setStyle(TableStyle(estilos))
            elems.append(tabla)

            elems.append(Spacer(1, 4*mm))
            elems.append(Paragraph(
                f"Clientes con deuda: <b>{len(clientes)}</b> &mdash; "
                f"Total general: <b>{_f(total_general)}</b>", st_norm))

        elems.append(Spacer(1, 6*mm))
        usuario = session.get('nombre', '') or ''
        pie = (f"Generado por {usuario} &mdash; FactuF&aacute;cil &mdash; {ahora.strftime('%d/%m/%Y %H:%M')}"
               if usuario else
               f"Generado con FactuF&aacute;cil &mdash; {ahora.strftime('%d/%m/%Y %H:%M')}")
        elems.append(Paragraph(pie, st_sub))

        pdf_doc.build(elems)
        buf.seek(0)
        return send_file(buf, mimetype='application/pdf', as_attachment=False,
                         download_name=f"deuda_clientes_{ahora.strftime('%Y%m%d_%H%M')}.pdf")
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
