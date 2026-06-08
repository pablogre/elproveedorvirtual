#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pedidos.py - MÓDULO DE PEDIDOS ONLINE
═══════════════════════════════════════════════════════════════════════════════
Sistema de pedidos para clientes - Integrado con FactuFacil
═══════════════════════════════════════════════════════════════════════════════
"""

from flask import Blueprint, jsonify, request, session, render_template, redirect, url_for
from sqlalchemy import text, and_, or_
from datetime import datetime
from decimal import Decimal

# Blueprint para las rutas de pedidos
pedidos_bp = Blueprint('pedidos', __name__)

# Variable global para db (se inicializa en init_pedidos)
db = None


# ═══════════════════════════════════════════════════════════════════════════════
# FUNCIÓN DE INICIALIZACIÓN
# ═══════════════════════════════════════════════════════════════════════════════

def init_pedidos(app, database):
    """
    Inicializa el módulo de pedidos en la app Flask
    
    Uso en app.py:
        from pedidos import init_pedidos, pedidos_bp
        init_pedidos(app, db)
        app.register_blueprint(pedidos_bp)
    """
    global db
    db = database
    app.register_blueprint(pedidos_bp)
    print("✅ Módulo de Pedidos Online inicializado correctamente")


# ═══════════════════════════════════════════════════════════════════════════════
# FUNCIONES AUXILIARES
# ═══════════════════════════════════════════════════════════════════════════════

def ejecutar_query(query, params=None, commit=False):
    """Ejecuta una query SQL de forma segura"""
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


def obtener_cliente_por_documento(documento):
    """Busca un cliente por su documento (CUIT/DNI)"""
    query = """
        SELECT id, nombre, documento, tipo_documento, condicion_iva, 
               email, telefono, direccion, lista_precio
        FROM cliente 
        WHERE documento = :documento
        LIMIT 1
    """
    result = ejecutar_query(query, {'documento': documento.strip()})
    row = result.fetchone()
    
    if row:
        return {
            'id': row.id,
            'nombre': row.nombre,
            'documento': row.documento,
            'tipo_documento': row.tipo_documento,
            'condicion_iva': row.condicion_iva,
            'email': row.email,
            'telefono': row.telefono,
            'direccion': row.direccion,
            'lista_precio': row.lista_precio or 1
        }
    return None


def obtener_productos_catalogo(lista_precio=1, buscar=None, categoria=None):
    """Obtiene productos activos para el catálogo"""
    
    # Seleccionar precio según lista
    precio_campo = 'precio'
    if lista_precio == 2:
        precio_campo = 'COALESCE(precio2, precio)'
    elif lista_precio == 3:
        precio_campo = 'COALESCE(precio3, precio)'
    elif lista_precio == 4:
        precio_campo = 'COALESCE(precio4, precio)'
    elif lista_precio == 5:
        precio_campo = 'COALESCE(precio5, precio)'
    
    query = f"""
        SELECT 
            p.id,
            p.codigo,
            p.nombre,
            p.descripcion,
            {precio_campo} as precio,
            p.precio as precio_base,
            p.stock,
            p.iva,
            p.categoria,
            p.es_combo,
            p.producto_base_id,
            p.cantidad_combo,
            p.producto_base_2_id,
            p.cantidad_combo_2,
            p.producto_base_3_id,
            p.cantidad_combo_3,
            p.imagen_url
        FROM producto p
        WHERE p.activo = 1
    """
    
    params = {}
    
    if buscar:
        query += """ AND (p.codigo LIKE :buscar OR p.nombre LIKE :buscar OR p.descripcion LIKE :buscar)"""
        params['buscar'] = f'%{buscar}%'
    
    if categoria:
        query += """ AND p.categoria = :categoria"""
        params['categoria'] = categoria
    
    query += """ ORDER BY p.categoria, p.nombre"""
    
    result = ejecutar_query(query, params if params else None)
    
    productos = []
    for row in result:
        # Calcular stock dinámico para combos
        stock = float(row.stock) if row.stock else 0
        
        if row.es_combo:
            # Para combos, calcular stock basado en productos base
            stock = calcular_stock_combo(
                row.producto_base_id, row.cantidad_combo,
                row.producto_base_2_id, row.cantidad_combo_2,
                row.producto_base_3_id, row.cantidad_combo_3
            )
        
        productos.append({
            'id': row.id,
            'codigo': row.codigo,
            'nombre': row.nombre,
            'descripcion': row.descripcion or '',
            'precio': float(row.precio) if row.precio else 0,
            'stock': stock,
            'iva': float(row.iva) if row.iva else 21,
            'categoria': row.categoria or 'Sin categoría',
            'es_combo': row.es_combo or False,
            'imagen_url': row.imagen_url or '',
            'disponible': stock > 0
        })
    
    return productos


def calcular_stock_combo(base_id_1, cant_1, base_id_2, cant_2, base_id_3, cant_3):
    """Calcula stock disponible de un combo basado en productos base"""
    stocks_disponibles = []
    
    if base_id_1 and cant_1:
        query = "SELECT stock FROM producto WHERE id = :id"
        result = ejecutar_query(query, {'id': base_id_1})
        row = result.fetchone()
        if row and row.stock:
            stock_posible = int(float(row.stock) / float(cant_1))
            stocks_disponibles.append(stock_posible)
    
    if base_id_2 and cant_2:
        result = ejecutar_query(query, {'id': base_id_2})
        row = result.fetchone()
        if row and row.stock:
            stock_posible = int(float(row.stock) / float(cant_2))
            stocks_disponibles.append(stock_posible)
    
    if base_id_3 and cant_3:
        result = ejecutar_query(query, {'id': base_id_3})
        row = result.fetchone()
        if row and row.stock:
            stock_posible = int(float(row.stock) / float(cant_3))
            stocks_disponibles.append(stock_posible)
    
    return min(stocks_disponibles) if stocks_disponibles else 0


def obtener_categorias():
    """Obtiene lista de categorías únicas"""
    query = """
        SELECT DISTINCT categoria 
        FROM producto 
        WHERE activo = 1 AND categoria IS NOT NULL AND categoria != ''
        ORDER BY categoria
    """
    result = ejecutar_query(query)
    return [row.categoria for row in result]


# ═══════════════════════════════════════════════════════════════════════════════
# RUTAS PÚBLICAS - TIENDA PARA CLIENTES
# ═══════════════════════════════════════════════════════════════════════════════

@pedidos_bp.route('/pedidos')
def tienda():
    """Página principal de la tienda de pedidos"""
    return render_template('pedidos_tienda.html')


@pedidos_bp.route('/api/pedidos/login', methods=['POST'])
def api_login_cliente():
    """Login de cliente por documento"""
    try:
        data = request.json
        documento = data.get('documento', '').strip()
        
        if not documento:
            return jsonify({'success': False, 'error': 'Ingrese su documento'}), 400
        
        # Limpiar documento (quitar guiones, espacios)
        documento = documento.replace('-', '').replace(' ', '').replace('.', '')
        
        cliente = obtener_cliente_por_documento(documento)
        
        if not cliente:
            return jsonify({
                'success': False, 
                'error': 'Cliente no encontrado. Contacte al administrador para registrarse.'
            }), 404
        
        # Guardar en sesión
        session['pedidos_cliente_id'] = cliente['id']
        session['pedidos_cliente_nombre'] = cliente['nombre']
        session['pedidos_cliente_documento'] = cliente['documento']
        session['pedidos_lista_precio'] = cliente['lista_precio']
        
        return jsonify({
            'success': True,
            'cliente': cliente
        })
        
    except Exception as e:
        print(f"❌ Error en login cliente: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@pedidos_bp.route('/api/pedidos/logout', methods=['POST'])
def api_logout_cliente():
    """Logout de cliente"""
    session.pop('pedidos_cliente_id', None)
    session.pop('pedidos_cliente_nombre', None)
    session.pop('pedidos_cliente_documento', None)
    session.pop('pedidos_lista_precio', None)
    return jsonify({'success': True})


@pedidos_bp.route('/api/pedidos/cliente_actual')
def api_cliente_actual():
    """Obtiene datos del cliente logueado"""
    if 'pedidos_cliente_id' not in session:
        return jsonify({'success': False, 'logueado': False})
    
    return jsonify({
        'success': True,
        'logueado': True,
        'cliente': {
            'id': session['pedidos_cliente_id'],
            'nombre': session['pedidos_cliente_nombre'],
            'documento': session['pedidos_cliente_documento'],
            'lista_precio': session['pedidos_lista_precio']
        }
    })


@pedidos_bp.route('/api/pedidos/catalogo')
def api_catalogo():
    """Obtiene catálogo de productos"""
    try:
        # Obtener lista de precios (del cliente logueado o default 1)
        lista_precio = session.get('pedidos_lista_precio', 1)
        
        buscar = request.args.get('buscar', '').strip()
        categoria = request.args.get('categoria', '').strip()
        
        productos = obtener_productos_catalogo(
            lista_precio=lista_precio,
            buscar=buscar if buscar else None,
            categoria=categoria if categoria else None
        )
        
        categorias = obtener_categorias()
        
        return jsonify({
            'success': True,
            'productos': productos,
            'categorias': categorias,
            'lista_precio': lista_precio,
            'total': len(productos)
        })
        
    except Exception as e:
        print(f"❌ Error en catálogo: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@pedidos_bp.route('/api/pedidos/crear', methods=['POST'])
def api_crear_pedido():
    """Crea un nuevo pedido - SIN CÁLCULO DE PRECIOS (productos pesables)"""
    try:
        # Verificar cliente logueado
        if 'pedidos_cliente_id' not in session:
            return jsonify({'success': False, 'error': 'Debe iniciar sesión'}), 401
        
        data = request.json
        items = data.get('items', [])
        notas = data.get('notas', '')
        tipo_entrega = data.get('tipo_entrega', 'retiro')  # 'retiro' o 'envio'
        
        if not items:
            return jsonify({'success': False, 'error': 'El carrito está vacío'}), 400
        
        if tipo_entrega not in ['retiro', 'envio']:
            tipo_entrega = 'retiro'
        
        cliente_id = session['pedidos_cliente_id']
        
        # Obtener lista de precios según configuración y tipo de entrega
        query_config = "SELECT lista_retiro, lista_envio FROM configuracion_pedidos WHERE id = 1"
        result_config = ejecutar_query(query_config)
        config = result_config.fetchone()
        
        if config:
            lista_precio = config.lista_retiro if tipo_entrega == 'retiro' else config.lista_envio
        else:
            lista_precio = 1  # Default si no hay configuración
        
        # NO calcular totales - se calcularán al preparar/facturar
        # Guardar con total = 0
        
        # Crear pedido con totales en 0
        query_pedido = """
            INSERT INTO pedido (cliente_id, estado, subtotal, iva, total, notas, tipo_entrega, fecha)
            VALUES (:cliente_id, 'pendiente', 0, 0, 0, :notas, :tipo_entrega, NOW())
        """
        
        pedido_id = ejecutar_query(query_pedido, {
            'cliente_id': cliente_id,
            'notas': notas,
            'tipo_entrega': tipo_entrega
        }, commit=True)
        
        # Insertar detalles SIN precios (solo producto y cantidad)
        query_detalle = """
            INSERT INTO pedido_detalle (pedido_id, producto_id, cantidad, precio_unitario, subtotal, lista_precio)
            VALUES (:pedido_id, :producto_id, :cantidad, 0, 0, :lista_precio)
        """
        
        for item in items:
            ejecutar_query(query_detalle, {
                'pedido_id': pedido_id,
                'producto_id': item['producto_id'],
                'cantidad': float(item['cantidad']),
                'lista_precio': lista_precio
            }, commit=True)
        
        tipo_texto = 'Retiro en local' if tipo_entrega == 'retiro' else 'Envío a domicilio'
        print(f"✅ Pedido #{pedido_id} creado para cliente {cliente_id} - {tipo_texto} (Lista {lista_precio})")
        
        return jsonify({
            'success': True,
            'pedido_id': pedido_id,
            'total': 0,
            'tipo_entrega': tipo_entrega,
            'mensaje': f'Pedido #{pedido_id} enviado. El precio se calculará al preparar el pedido.'
        })
        
    except Exception as e:
        print(f"❌ Error creando pedido: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@pedidos_bp.route('/api/pedidos/mis_pedidos')
def api_mis_pedidos():
    """Obtiene pedidos del cliente logueado"""
    try:
        if 'pedidos_cliente_id' not in session:
            return jsonify({'success': False, 'error': 'Debe iniciar sesión'}), 401
        
        cliente_id = session['pedidos_cliente_id']
        
        query = """
            SELECT 
                p.id,
                p.fecha,
                p.estado,
                p.subtotal,
                p.iva,
                p.total,
                p.notas,
                p.factura_id,
                f.numero as factura_numero
            FROM pedido p
            LEFT JOIN factura f ON p.factura_id = f.id
            WHERE p.cliente_id = :cliente_id
            ORDER BY p.fecha DESC
            LIMIT 50
        """
        
        result = ejecutar_query(query, {'cliente_id': cliente_id})
        
        pedidos = []
        for row in result:
            pedidos.append({
                'id': row.id,
                'fecha': row.fecha.strftime('%d/%m/%Y %H:%M') if row.fecha else '',
                'estado': row.estado,
                'subtotal': float(row.subtotal) if row.subtotal else 0,
                'iva': float(row.iva) if row.iva else 0,
                'total': float(row.total) if row.total else 0,
                'notas': row.notas or '',
                'factura_id': row.factura_id,
                'factura_numero': row.factura_numero
            })
        
        return jsonify({
            'success': True,
            'pedidos': pedidos
        })
        
    except Exception as e:
        print(f"❌ Error obteniendo pedidos: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@pedidos_bp.route('/api/pedidos/detalle/<int:pedido_id>')
def api_detalle_pedido(pedido_id):
    """Obtiene detalle de un pedido - Expandiendo productos pesables
    
    - En modo edición (pendiente/preparando): expande líneas para ingresar peso
    - En modo lectura (cotizado+): muestra los pesos individuales guardados
    """
    try:
        # Verificar que el pedido sea del cliente logueado (si es cliente)
        cliente_id = session.get('pedidos_cliente_id')
        es_admin = 'user_id' in session
        
        if not cliente_id and not es_admin:
            return jsonify({'success': False, 'error': 'No autorizado'}), 401
        
        # Obtener pedido
        query_pedido = """
            SELECT 
                p.id, p.cliente_id, p.fecha, p.estado, p.subtotal, p.iva, p.total, p.notas,
                c.nombre as cliente_nombre, c.documento as cliente_documento
            FROM pedido p
            INNER JOIN cliente c ON p.cliente_id = c.id
            WHERE p.id = :pedido_id
        """
        
        if cliente_id and not es_admin:
            query_pedido += " AND p.cliente_id = :cliente_id"
        
        params = {'pedido_id': pedido_id}
        if cliente_id and not es_admin:
            params['cliente_id'] = cliente_id
        
        result = ejecutar_query(query_pedido, params)
        row = result.fetchone()
        
        if not row:
            return jsonify({'success': False, 'error': 'Pedido no encontrado'}), 404
        
        estado_pedido = row.estado
        pedido = {
            'id': row.id,
            'cliente_id': row.cliente_id,
            'cliente_nombre': row.cliente_nombre,
            'cliente_documento': row.cliente_documento,
            'fecha': row.fecha.strftime('%d/%m/%Y %H:%M') if row.fecha else '',
            'estado': estado_pedido,
            'subtotal': float(row.subtotal) if row.subtotal else 0,
            'iva': float(row.iva) if row.iva else 0,
            'total': float(row.total) if row.total else 0,
            'notas': row.notas or ''
        }
        
        # Determinar modo
        puede_editar = es_admin and estado_pedido in ['pendiente', 'preparando']
        
        # Obtener productos CON campo es_pesable Y todos los precios
        query_detalle = """
            SELECT 
                d.id,
                d.producto_id,
                d.cantidad,
                d.precio_unitario,
                d.subtotal,
                d.lista_precio,
                p.codigo,
                p.nombre,
                p.iva,
                p.precio as precio1,
                COALESCE(p.precio2, p.precio) as precio2,
                COALESCE(p.precio3, p.precio) as precio3,
                COALESCE(p.precio4, p.precio) as precio4,
                COALESCE(p.precio5, p.precio) as precio5,
                COALESCE(p.es_pesable, 0) as es_pesable
            FROM pedido_detalle d
            INNER JOIN producto p ON d.producto_id = p.id
            WHERE d.pedido_id = :pedido_id
        """
        
        result_detalle = ejecutar_query(query_detalle, {'pedido_id': pedido_id})
        
        productos = []
        for item in result_detalle:
            cantidad_original = int(item.cantidad) if item.cantidad == int(item.cantidad) else float(item.cantidad)
            es_pesable = bool(item.es_pesable)
            detalle_id = item.id
            
            # Obtener el precio según la lista de precios del detalle
            lista = item.lista_precio or 1
            if lista == 1:
                precio_real = float(item.precio1) if item.precio1 else 0
            elif lista == 2:
                precio_real = float(item.precio2) if item.precio2 else 0
            elif lista == 3:
                precio_real = float(item.precio3) if item.precio3 else 0
            elif lista == 4:
                precio_real = float(item.precio4) if item.precio4 else 0
            elif lista == 5:
                precio_real = float(item.precio5) if item.precio5 else 0
            else:
                precio_real = float(item.precio1) if item.precio1 else 0
            
            # Si ya tiene precio guardado, usar ese; si no, el precio real
            precio_unitario = float(item.precio_unitario) if item.precio_unitario and float(item.precio_unitario) > 0 else precio_real
            
            # ═══════════════════════════════════════════════════════════════════
            # PRIMERO: Buscar si hay pesos individuales guardados
            # (sin importar el valor de es_pesable)
            # ═══════════════════════════════════════════════════════════════════
            query_pesos = """
                SELECT numero_unidad, peso, subtotal
                FROM pedido_detalle_peso
                WHERE pedido_detalle_id = :detalle_id
                ORDER BY numero_unidad
            """
            result_pesos = ejecutar_query(query_pesos, {'detalle_id': detalle_id})
            pesos = result_pesos.fetchall()
            
            # CASO 1: HAY PESOS GUARDADOS - Mostrar expandido SIEMPRE
            if pesos and len(pesos) > 0:
                print(f"✅ Detalle {detalle_id}: Encontrados {len(pesos)} pesos guardados")
                total_unidades = len(pesos)
                for peso_row in pesos:
                    productos.append({
                        'id': item.id,
                        'detalle_id': f"{item.id}_{peso_row.numero_unidad}",
                        'producto_id': item.producto_id,
                        'codigo': item.codigo,
                        'nombre': item.nombre,
                        'cantidad': float(peso_row.peso),
                        'precio_unitario': precio_unitario,
                        'subtotal': float(peso_row.subtotal),
                        'iva': float(item.iva) if item.iva else 21,
                        'lista_precio': lista,
                        'es_pesable': True,
                        'linea_expandida': True,
                        'indice_unidad': peso_row.numero_unidad,
                        'total_unidades': total_unidades,
                        'modo': 'lectura'
                    })
            
            # CASO 2: Modo edición para pesables - expandir para ingresar pesos
            elif es_pesable and puede_editar and cantidad_original > 1:
                print(f"📝 Detalle {detalle_id}: Modo edición, expandir {int(cantidad_original)} líneas")
                for i in range(int(cantidad_original)):
                    productos.append({
                        'id': item.id,
                        'detalle_id': f"{item.id}_{i}",
                        'producto_id': item.producto_id,
                        'codigo': item.codigo,
                        'nombre': item.nombre,
                        'cantidad': 0,
                        'cantidad_original': 1,
                        'precio_unitario': precio_unitario,
                        'subtotal': 0,
                        'iva': float(item.iva) if item.iva else 21,
                        'lista_precio': lista,
                        'es_pesable': True,
                        'linea_expandida': True,
                        'indice_unidad': i + 1,
                        'total_unidades': int(cantidad_original),
                        'modo': 'edicion'
                    })
            
            # CASO 3: Producto normal (sin pesos guardados)
            else:
                print(f"📦 Detalle {detalle_id}: Producto normal, cantidad={cantidad_original}")
                subtotal_item = float(item.subtotal) if item.subtotal and float(item.subtotal) > 0 else (float(item.cantidad) * precio_unitario)
                productos.append({
                    'id': item.id,
                    'detalle_id': item.id,
                    'producto_id': item.producto_id,
                    'codigo': item.codigo,
                    'nombre': item.nombre,
                    'cantidad': float(item.cantidad),
                    'precio_unitario': precio_unitario,
                    'subtotal': subtotal_item,
                    'iva': float(item.iva) if item.iva else 21,
                    'lista_precio': lista,
                    'es_pesable': es_pesable,
                    'linea_expandida': False,
                    'modo': 'normal'
                })
        
        print(f"📋 Pedido #{pedido_id}: Devolviendo {len(productos)} líneas de productos")
        pedido['productos'] = productos
        
        return jsonify({
            'success': True,
            'pedido': pedido
        })
        
    except Exception as e:
        print(f"❌ Error obteniendo detalle: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500



# ═══════════════════════════════════════════════════════════════════════════════
# RUTAS ADMIN - GESTIÓN DE PEDIDOS
# ═══════════════════════════════════════════════════════════════════════════════

@pedidos_bp.route('/admin/pedidos')
def admin_pedidos():
    """Panel de administración de pedidos"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('pedidos_admin.html')


@pedidos_bp.route('/api/admin/pedidos')
def api_admin_pedidos():
    """Lista todos los pedidos para admin"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'No autorizado'}), 401
    
    try:
        estado = request.args.get('estado', '').strip()
        
        query = """
            SELECT 
                p.id,
                p.fecha,
                p.estado,
                p.subtotal,
                p.iva,
                p.total,
                p.notas,
                p.tipo_entrega,
                p.factura_id,
                c.nombre as cliente_nombre,
                c.documento as cliente_documento,
                c.telefono as cliente_telefono,
                f.numero as factura_numero
            FROM pedido p
            INNER JOIN cliente c ON p.cliente_id = c.id
            LEFT JOIN factura f ON p.factura_id = f.id
        """
        
        params = {}
        if estado:
            query += " WHERE p.estado = :estado"
            params['estado'] = estado
        
        query += " ORDER BY p.fecha DESC LIMIT 100"
        
        result = ejecutar_query(query, params if params else None)
        
        pedidos = []
        for row in result:
            pedidos.append({
                'id': row.id,
                'fecha': row.fecha.strftime('%d/%m/%Y %H:%M') if row.fecha else '',
                'estado': row.estado,
                'subtotal': float(row.subtotal) if row.subtotal else 0,
                'iva': float(row.iva) if row.iva else 0,
                'total': float(row.total) if row.total else 0,
                'notas': row.notas or '',
                'tipo_entrega': row.tipo_entrega or 'retiro',
                'cliente_nombre': row.cliente_nombre,
                'cliente_documento': row.cliente_documento,
                'cliente_telefono': row.cliente_telefono or '',
                'factura_id': row.factura_id,
                'factura_numero': row.factura_numero
            })
        
        # Contar por estado
        query_conteo = """
            SELECT estado, COUNT(*) as cantidad
            FROM pedido
            GROUP BY estado
        """
        result_conteo = ejecutar_query(query_conteo)
        conteo = {row.estado: row.cantidad for row in result_conteo}
        
        return jsonify({
            'success': True,
            'pedidos': pedidos,
            'conteo': conteo
        })
        
    except Exception as e:
        print(f"❌ Error listando pedidos: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@pedidos_bp.route('/api/admin/pedidos/<int:pedido_id>/estado', methods=['POST'])
def api_cambiar_estado_pedido(pedido_id):
    """Cambia el estado de un pedido"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'No autorizado'}), 401
    
    try:
        data = request.json
        nuevo_estado = data.get('estado')
        
        estados_validos = ['pendiente', 'preparando', 'cotizado', 'aceptado', 'listo', 'facturado', 'rechazado', 'cancelado']
        if nuevo_estado not in estados_validos:
            return jsonify({'success': False, 'error': 'Estado no válido'}), 400
        
        query = """
            UPDATE pedido 
            SET estado = :estado, fecha_actualizacion = NOW()
            WHERE id = :pedido_id
        """
        
        ejecutar_query(query, {
            'estado': nuevo_estado,
            'pedido_id': pedido_id
        }, commit=True)
        
        print(f"✅ Pedido #{pedido_id} cambiado a estado: {nuevo_estado}")
        
        return jsonify({
            'success': True,
            'mensaje': f'Pedido actualizado a {nuevo_estado}'
        })
        
    except Exception as e:
        print(f"❌ Error cambiando estado: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@pedidos_bp.route('/api/admin/pedidos/<int:pedido_id>/cargar_venta')
def api_cargar_pedido_en_venta(pedido_id):
    """Obtiene los datos del pedido para cargarlos en nueva_venta"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'No autorizado'}), 401
    
    try:
        # Primero verificar que el pedido existe y ver su estado
        query_check = "SELECT id, estado FROM pedido WHERE id = :pedido_id"
        result_check = ejecutar_query(query_check, {'pedido_id': pedido_id})
        pedido_check = result_check.fetchone()
        
        if not pedido_check:
            return jsonify({
                'success': False, 
                'error': f'Pedido #{pedido_id} no existe en la base de datos'
            }), 404
        
        print(f"📋 Pedido #{pedido_id} encontrado, estado: {pedido_check.estado}")
        
        # Estados válidos para facturar (excluimos 'facturado', 'cancelado', 'rechazado')
        estados_validos = ['pendiente', 'preparando', 'cotizado', 'aceptado', 'listo']
        
        if pedido_check.estado not in estados_validos:
            return jsonify({
                'success': False, 
                'error': f'El pedido está en estado "{pedido_check.estado}" y no se puede facturar'
            }), 400
        
        # Obtener pedido con cliente
        query_pedido = """
            SELECT 
                p.id, p.cliente_id, p.total, p.estado,
                c.nombre as cliente_nombre,
                COALESCE(c.lista_precio, 1) as lista_precio
            FROM pedido p
            INNER JOIN cliente c ON p.cliente_id = c.id
            WHERE p.id = :pedido_id
        """
        
        result = ejecutar_query(query_pedido, {'pedido_id': pedido_id})
        pedido = result.fetchone()
        
        if not pedido:
            return jsonify({
                'success': False, 
                'error': 'Error al obtener datos del cliente del pedido'
            }), 404
        
        # Obtener productos del pedido (con pesos individuales si existen)
        # Incluimos los precios actuales del producto y la lista para fallback
        # cuando precio_unitario en pedido_detalle no haya sido seteado correctamente.
        query_detalle = """
            SELECT 
                d.id as detalle_id,
                d.producto_id,
                d.cantidad,
                d.precio_unitario,
                d.subtotal,
                d.lista_precio,
                p.codigo,
                p.nombre,
                p.iva,
                p.stock,
                p.es_combo,
                p.precio as precio1,
                COALESCE(p.precio2, p.precio) as precio2,
                COALESCE(p.precio3, p.precio) as precio3,
                COALESCE(p.precio4, p.precio) as precio4,
                COALESCE(p.precio5, p.precio) as precio5,
                COALESCE(p.es_pesable, 0) as es_pesable
            FROM pedido_detalle d
            INNER JOIN producto p ON d.producto_id = p.id
            WHERE d.pedido_id = :pedido_id
        """
        
        result_detalle = ejecutar_query(query_detalle, {'pedido_id': pedido_id})
        
        productos = []
        for item in result_detalle:
            # ─── Determinar precio unitario CON IVA ─────────────────────────────
            # Patrón idéntico a api_detalle_pedido: si precio_unitario guardado
            # es 0 o nulo (cotización pendiente o fallida), caer al precio actual
            # del producto según la lista del detalle.
            lista_pd = item.lista_precio or 1
            if lista_pd == 1:
                precio_lista = float(item.precio1) if item.precio1 else 0
            elif lista_pd == 2:
                precio_lista = float(item.precio2) if item.precio2 else 0
            elif lista_pd == 3:
                precio_lista = float(item.precio3) if item.precio3 else 0
            elif lista_pd == 4:
                precio_lista = float(item.precio4) if item.precio4 else 0
            elif lista_pd == 5:
                precio_lista = float(item.precio5) if item.precio5 else 0
            else:
                precio_lista = float(item.precio1) if item.precio1 else 0

            precio_guardado = float(item.precio_unitario) if item.precio_unitario else 0
            precio_con_iva = precio_guardado if precio_guardado > 0 else precio_lista

            # Frontend de nueva_venta espera precio SIN IVA (ver comentario en
            # verificarPedidoPendiente). Los precios en la tabla producto y en
            # pedido_detalle vienen CON IVA, así que extraemos el neto acá.
            iva_pct = float(item.iva) if item.iva else 21.0
            precio_sin_iva = precio_con_iva / (1 + iva_pct / 100.0)
            # ────────────────────────────────────────────────────────────────────

            # Verificar si tiene pesos individuales
            query_pesos = """
                SELECT numero_unidad, peso, subtotal
                FROM pedido_detalle_peso
                WHERE pedido_detalle_id = :detalle_id
                ORDER BY numero_unidad
            """
            result_pesos = ejecutar_query(query_pesos, {'detalle_id': item.detalle_id})
            pesos = result_pesos.fetchall()
            
            if pesos and len(pesos) > 0:
                # Producto pesable con pesos individuales - crear una línea por cada peso
                for peso_row in pesos:
                    productos.append({
                        'producto_id': item.producto_id,
                        'codigo': item.codigo,
                        'nombre': f"{item.nombre} (U{peso_row.numero_unidad})",
                        'cantidad': float(peso_row.peso),
                        'precio_unitario': precio_sin_iva,
                        'subtotal': float(peso_row.peso) * precio_sin_iva,
                        'iva': iva_pct,
                        'stock': float(item.stock) if item.stock else 0,
                        'es_combo': item.es_combo or False,
                        'es_pesable': True
                    })
            else:
                # Producto normal o pesable sin pesos individuales
                productos.append({
                    'producto_id': item.producto_id,
                    'codigo': item.codigo,
                    'nombre': item.nombre,
                    'cantidad': float(item.cantidad),
                    'precio_unitario': precio_sin_iva,
                    'subtotal': float(item.cantidad) * precio_sin_iva,
                    'iva': iva_pct,
                    'stock': float(item.stock) if item.stock else 0,
                    'es_combo': item.es_combo or False,
                    'es_pesable': bool(item.es_pesable)
                })
        
        print(f"✅ Pedido #{pedido_id} listo para facturar: {len(productos)} productos")
        
        return jsonify({
            'success': True,
            'pedido_id': pedido.id,
            'cliente_id': pedido.cliente_id,
            'cliente_nombre': pedido.cliente_nombre,
            'lista_precio': pedido.lista_precio or 1,
            'productos': productos,
            'total': float(pedido.total) if pedido.total else 0
        })
        
    except Exception as e:
        print(f"❌ Error cargando pedido: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
        

@pedidos_bp.route('/api/admin/pedidos/<int:pedido_id>/cotizar', methods=['POST'])
def api_cotizar_pedido(pedido_id):
    """Cotiza un pedido: actualiza cantidades, calcula totales y cambia estado a 'cotizado'
    
    Maneja productos pesables que vienen como líneas expandidas
    Guarda los pesos individuales en pedido_detalle_peso
    """
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'No autorizado'}), 401
    
    try:
        data = request.json
        items = data.get('items', [])
        
        if not items:
            return jsonify({'success': False, 'error': 'No hay items para cotizar'}), 400
        
        # Verificar que el pedido existe y está en estado correcto
        query_pedido = "SELECT id, estado FROM pedido WHERE id = :pedido_id"
        result = ejecutar_query(query_pedido, {'pedido_id': pedido_id})
        pedido = result.fetchone()
        
        if not pedido:
            return jsonify({'success': False, 'error': 'Pedido no encontrado'}), 404
        
        if pedido.estado not in ['pendiente', 'preparando']:
            return jsonify({'success': False, 'error': f'No se puede cotizar un pedido en estado {pedido.estado}'}), 400
        
        # Agrupar items por producto_id (para productos pesables expandidos)
        # Guardamos también los pesos individuales
        productos_agrupados = {}
        
        for item in items:
            producto_id = item.get('producto_id')
            detalle_id = str(item.get('detalle_id', ''))
            cantidad = float(item.get('cantidad', 0))
            es_pesable = item.get('es_pesable', 'false')
            
            # Convertir es_pesable a booleano
            if isinstance(es_pesable, str):
                es_pesable = es_pesable.lower() == 'true'
            
            # Extraer el detalle_id real (sin el sufijo _N de líneas expandidas)
            if '_' in detalle_id:
                detalle_id_real = detalle_id.split('_')[0]
                numero_unidad = int(detalle_id.split('_')[1]) + 1  # Convertir índice 0-based a 1-based
            else:
                detalle_id_real = detalle_id
                numero_unidad = 1
            
            if producto_id not in productos_agrupados:
                productos_agrupados[producto_id] = {
                    'detalle_id_real': detalle_id_real,
                    'cantidad_total': 0,
                    'es_pesable': es_pesable,
                    'pesos_individuales': []  # Lista de (numero_unidad, peso)
                }
            
            productos_agrupados[producto_id]['cantidad_total'] += cantidad
            
            # Si es pesable, guardar el peso individual
            if es_pesable or '_' in str(item.get('detalle_id', '')):
                productos_agrupados[producto_id]['pesos_individuales'].append({
                    'numero_unidad': numero_unidad,
                    'peso': cantidad
                })
                productos_agrupados[producto_id]['es_pesable'] = True
        
        # Procesar cada producto agrupado
        # Los precios en la tabla producto incluyen IVA
        subtotal_neto = 0
        iva_total = 0
        subtotal = 0  # subtotal CON IVA (para compatibilidad con el loop)
        
        for producto_id, grupo in productos_agrupados.items():
            cantidad_total = grupo['cantidad_total']
            detalle_id_real = grupo['detalle_id_real']
            es_pesable = grupo.get('es_pesable', False)
            pesos_individuales = grupo.get('pesos_individuales', [])
            
            # Obtener la lista de precios del detalle
            query_lista = """
                SELECT id, lista_precio FROM pedido_detalle 
                WHERE pedido_id = :pedido_id AND producto_id = :producto_id
                LIMIT 1
            """
            lista_result = ejecutar_query(query_lista, {
                'pedido_id': pedido_id,
                'producto_id': producto_id
            })
            lista_row = lista_result.fetchone()
            
            if not lista_row:
                continue
                
            detalle_id_db = lista_row.id
            lista_precio = lista_row.lista_precio if lista_row.lista_precio else 1
            
            # Obtener precios del producto
            query_prod = """
                SELECT precio, 
                       COALESCE(precio2, precio) as precio2,
                       COALESCE(precio3, precio) as precio3,
                       COALESCE(precio4, precio) as precio4,
                       COALESCE(precio5, precio) as precio5,
                       costo, iva 
                FROM producto WHERE id = :id
            """
            prod_result = ejecutar_query(query_prod, {'id': producto_id})
            prod = prod_result.fetchone()
            
            if prod:
                # Seleccionar precio según lista
                if lista_precio == 1:
                    precio_unitario = float(prod.precio) if prod.precio else 0
                elif lista_precio == 2:
                    precio_unitario = float(prod.precio2) if prod.precio2 else 0
                elif lista_precio == 3:
                    precio_unitario = float(prod.precio3) if prod.precio3 else 0
                elif lista_precio == 4:
                    precio_unitario = float(prod.precio4) if prod.precio4 else 0
                elif lista_precio == 5:
                    precio_unitario = float(prod.precio5) if prod.precio5 else 0
                else:
                    precio_unitario = float(prod.precio) if prod.precio else 0
                
                # Los precios incluyen IVA — extraer neto e IVA
                iva_rate = float(prod.iva) / 100 if prod.iva else 0.21
                item_total_con_iva = cantidad_total * precio_unitario
                item_neto = item_total_con_iva / (1 + iva_rate)
                item_iva = item_total_con_iva - item_neto
                
                subtotal_neto += item_neto
                iva_total += item_iva
                subtotal += item_total_con_iva  # mantener para compatibilidad
                
                # Actualizar detalle del pedido con la cantidad TOTAL sumada
                query_update = """
                    UPDATE pedido_detalle 
                    SET cantidad = :cantidad,
                        precio_unitario = :precio,
                        subtotal = :subtotal
                    WHERE pedido_id = :pedido_id AND producto_id = :producto_id
                """
                ejecutar_query(query_update, {
                    'cantidad': cantidad_total,
                    'precio': precio_unitario,
                    'subtotal': item_total_con_iva,
                    'pedido_id': pedido_id,
                    'producto_id': producto_id
                }, commit=True)
                
                # Si es pesable, guardar los pesos individuales
                if es_pesable and pesos_individuales:
                    # Primero eliminar pesos anteriores (por si se está re-cotizando)
                    query_delete_pesos = """
                        DELETE FROM pedido_detalle_peso 
                        WHERE pedido_detalle_id = :detalle_id
                    """
                    ejecutar_query(query_delete_pesos, {'detalle_id': detalle_id_db}, commit=True)
                    
                    # Insertar cada peso individual
                    query_insert_peso = """
                        INSERT INTO pedido_detalle_peso 
                        (pedido_detalle_id, numero_unidad, peso, subtotal)
                        VALUES (:detalle_id, :numero, :peso, :subtotal)
                    """
                    for peso_info in pesos_individuales:
                        peso_subtotal = peso_info['peso'] * precio_unitario
                        ejecutar_query(query_insert_peso, {
                            'detalle_id': detalle_id_db,
                            'numero': peso_info['numero_unidad'],
                            'peso': peso_info['peso'],
                            'subtotal': peso_subtotal
                        }, commit=True)
        
        # Calcular totales (subtotal_neto e iva_total ya calculados por producto)
        total = subtotal_neto + iva_total
        
        # Actualizar pedido
        query_pedido_update = """
            UPDATE pedido 
            SET subtotal = :subtotal,
                iva = :iva,
                total = :total,
                estado = 'cotizado',
                fecha_actualizacion = NOW()
            WHERE id = :pedido_id
        """
        ejecutar_query(query_pedido_update, {
            'subtotal': round(subtotal_neto, 2),
            'iva': round(iva_total, 2),
            'total': round(total, 2),
            'pedido_id': pedido_id
        }, commit=True)
        
        print(f"✅ Pedido #{pedido_id} cotizado. Total: ${total:.2f}")
        
        return jsonify({
            'success': True,
            'mensaje': 'Pedido cotizado correctamente',
            'subtotal': round(subtotal, 2),
            'iva': round(iva_total, 2),
            'total': round(total, 2)
        })
        
    except Exception as e:
        print(f"❌ Error cotizando pedido: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@pedidos_bp.route('/api/pedidos/<int:pedido_id>/responder', methods=['POST'])
def api_responder_cotizacion(pedido_id):
    """Cliente acepta o rechaza una cotización"""
    if 'pedidos_cliente_id' not in session:
        return jsonify({'success': False, 'error': 'Debe iniciar sesión'}), 401
    
    try:
        data = request.json
        accion = data.get('accion')  # 'aceptar' o 'rechazar'
        
        if accion not in ['aceptar', 'rechazar']:
            return jsonify({'success': False, 'error': 'Acción no válida'}), 400
        
        cliente_id = session['pedidos_cliente_id']
        
        # Verificar que el pedido existe, es del cliente y está cotizado
        query_pedido = """
            SELECT id, estado FROM pedido 
            WHERE id = :pedido_id AND cliente_id = :cliente_id
        """
        result = ejecutar_query(query_pedido, {
            'pedido_id': pedido_id,
            'cliente_id': cliente_id
        })
        pedido = result.fetchone()
        
        if not pedido:
            return jsonify({'success': False, 'error': 'Pedido no encontrado'}), 404
        
        if pedido.estado != 'cotizado':
            return jsonify({'success': False, 'error': 'Este pedido no está pendiente de aceptación'}), 400
        
        nuevo_estado = 'aceptado' if accion == 'aceptar' else 'rechazado'
        
        query_update = """
            UPDATE pedido 
            SET estado = :estado, fecha_actualizacion = NOW()
            WHERE id = :pedido_id
        """
        ejecutar_query(query_update, {
            'estado': nuevo_estado,
            'pedido_id': pedido_id
        }, commit=True)
        
        print(f"✅ Pedido #{pedido_id} {nuevo_estado} por cliente {cliente_id}")
        
        return jsonify({
            'success': True,
            'mensaje': f'Pedido {nuevo_estado}',
            'estado': nuevo_estado
        })
        
    except Exception as e:
        print(f"❌ Error respondiendo cotización: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@pedidos_bp.route('/api/admin/pedidos/<int:pedido_id>/vincular_factura', methods=['POST'])
def api_vincular_factura(pedido_id):
    """Vincula una factura al pedido y lo marca como facturado"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'No autorizado'}), 401
    
    try:
        data = request.json
        factura_id = data.get('factura_id')
        
        if not factura_id:
            return jsonify({'success': False, 'error': 'Falta ID de factura'}), 400
        
        query = """
            UPDATE pedido 
            SET estado = 'facturado', factura_id = :factura_id, fecha_actualizacion = NOW()
            WHERE id = :pedido_id
        """
        
        ejecutar_query(query, {
            'factura_id': factura_id,
            'pedido_id': pedido_id
        }, commit=True)
        
        print(f"✅ Pedido #{pedido_id} vinculado a factura #{factura_id}")
        
        return jsonify({
            'success': True,
            'mensaje': f'Pedido facturado correctamente'
        })
        
    except Exception as e:
        print(f"❌ Error vinculando factura: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ═══════════════════════════════════════════════════════════════════════════════
# ESTADÍSTICAS
# ═══════════════════════════════════════════════════════════════════════════════

@pedidos_bp.route('/api/admin/pedidos/estadisticas')
def api_estadisticas_pedidos():
    """Estadísticas de pedidos"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'No autorizado'}), 401
    
    try:
        # Pedidos de hoy
        query_hoy = """
            SELECT COUNT(*) as total, COALESCE(SUM(total), 0) as monto
            FROM pedido
            WHERE DATE(fecha) = CURDATE()
        """
        result_hoy = ejecutar_query(query_hoy)
        row_hoy = result_hoy.fetchone()
        
        # Pedidos pendientes
        query_pendientes = """
            SELECT COUNT(*) as total, COALESCE(SUM(total), 0) as monto
            FROM pedido
            WHERE estado IN ('pendiente', 'preparando', 'listo')
        """
        result_pendientes = ejecutar_query(query_pendientes)
        row_pendientes = result_pendientes.fetchone()
        
        # Pedidos del mes
        query_mes = """
            SELECT COUNT(*) as total, COALESCE(SUM(total), 0) as monto
            FROM pedido
            WHERE MONTH(fecha) = MONTH(CURDATE()) AND YEAR(fecha) = YEAR(CURDATE())
        """
        result_mes = ejecutar_query(query_mes)
        row_mes = result_mes.fetchone()
        
        return jsonify({
            'success': True,
            'hoy': {
                'cantidad': row_hoy.total,
                'monto': float(row_hoy.monto)
            },
            'pendientes': {
                'cantidad': row_pendientes.total,
                'monto': float(row_pendientes.monto)
            },
            'mes': {
                'cantidad': row_mes.total,
                'monto': float(row_mes.monto)
            }
        })
        
    except Exception as e:
        print(f"❌ Error en estadísticas: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURACIÓN DE PEDIDOS
# ═══════════════════════════════════════════════════════════════════════════════

@pedidos_bp.route('/api/admin/pedidos/configuracion')
def api_obtener_configuracion():
    """Obtiene la configuración de listas de precios para pedidos"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'No autorizado'}), 401
    
    try:
        query = "SELECT lista_retiro, lista_envio FROM configuracion_pedidos WHERE id = 1"
        result = ejecutar_query(query)
        config = result.fetchone()
        
        if config:
            return jsonify({
                'success': True,
                'lista_retiro': config.lista_retiro,
                'lista_envio': config.lista_envio
            })
        else:
            # Crear configuración por defecto
            query_insert = """
                INSERT INTO configuracion_pedidos (id, lista_retiro, lista_envio) 
                VALUES (1, 1, 2)
            """
            ejecutar_query(query_insert, commit=True)
            return jsonify({
                'success': True,
                'lista_retiro': 1,
                'lista_envio': 2
            })
            
    except Exception as e:
        print(f"❌ Error obteniendo configuración: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@pedidos_bp.route('/api/admin/pedidos/configuracion', methods=['POST'])
def api_guardar_configuracion():
    """Guarda la configuración de listas de precios para pedidos"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'No autorizado'}), 401
    
    try:
        data = request.json
        lista_retiro = int(data.get('lista_retiro', 1))
        lista_envio = int(data.get('lista_envio', 2))
        
        # Validar que estén entre 1 y 5
        if not (1 <= lista_retiro <= 5) or not (1 <= lista_envio <= 5):
            return jsonify({'success': False, 'error': 'Las listas deben estar entre 1 y 5'}), 400
        
        query = """
            INSERT INTO configuracion_pedidos (id, lista_retiro, lista_envio) 
            VALUES (1, :lista_retiro, :lista_envio)
            ON DUPLICATE KEY UPDATE 
                lista_retiro = :lista_retiro,
                lista_envio = :lista_envio
        """
        
        ejecutar_query(query, {
            'lista_retiro': lista_retiro,
            'lista_envio': lista_envio
        }, commit=True)
        
        print(f"✅ Configuración guardada: Retiro=Lista {lista_retiro}, Envío=Lista {lista_envio}")
        
        return jsonify({
            'success': True,
            'mensaje': 'Configuración guardada correctamente'
        })
        
    except Exception as e:
        print(f"❌ Error guardando configuración: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

# =====================================================================
# GENERAR REMITO DESDE PEDIDO
# =====================================================================

@pedidos_bp.route('/api/admin/pedidos/<int:pedido_id>/generar_remito', methods=['POST'])
def api_generar_remito_desde_pedido(pedido_id):
    """Genera un remito a partir de un pedido cotizado.

    - Solo se puede remitar pedidos en estado 'cotizado' o 'aceptado'.
    - Crea registro en `remito` y `remito_detalle` (descuenta stock).
    - Marca el pedido como 'remitado' y guarda la referencia al remito creado.
    - Actualiza los totales del pedido (subtotal/iva/total) por si quedaron en 0.
    - El pedido queda disponible para facturar después (vía remitos.api_preparar_facturacion).
    """
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'No autorizado'}), 401

    try:
        # ─── 1) Cargar pedido y validar estado ───
        pedido = db.session.execute(text("""
            SELECT id, cliente_id, estado, notas, remito_id
            FROM pedido WHERE id = :pid
        """), {'pid': pedido_id}).mappings().first()

        if not pedido:
            return jsonify({'success': False, 'error': 'Pedido no encontrado'}), 404

        # Solo se puede remitar un pedido COTIZADO o ACEPTADO (que tiene precios calculados).
        # Pedidos en otros estados (pendiente, preparando, listo, facturado, etc.) NO.
        if pedido['estado'] not in ('cotizado', 'aceptado'):
            return jsonify({
                'success': False,
                'error': f"Solo se pueden remitar pedidos cotizados o aceptados. Estado actual: '{pedido['estado']}'. Cotizá el pedido antes de remitar."
            }), 400

        if pedido['remito_id']:
            return jsonify({
                'success': False,
                'error': f"Este pedido ya tiene generado el remito #{pedido['remito_id']}"
            }), 400

        cliente_id = pedido['cliente_id']

        # ─── 2) Cargar items del pedido ───
        items = db.session.execute(text("""
            SELECT
                d.producto_id, d.cantidad, d.precio_unitario, d.lista_precio,
                p.nombre, p.iva, p.stock, p.es_combo, p.es_pesable,
                p.precio as precio1,
                COALESCE(p.precio2, p.precio) as precio2,
                COALESCE(p.precio3, p.precio) as precio3,
                COALESCE(p.precio4, p.precio) as precio4,
                COALESCE(p.precio5, p.precio) as precio5
            FROM pedido_detalle d
            INNER JOIN producto p ON p.id = d.producto_id
            WHERE d.pedido_id = :pid
        """), {'pid': pedido_id}).mappings().all()

        if not items:
            return jsonify({'success': False, 'error': 'El pedido no tiene productos'}), 400

        # ─── 3) Validar stock, combos y que los items tengan precio cargado ───
        for it in items:
            if it['es_combo']:
                return jsonify({
                    'success': False,
                    'error': f"El producto '{it['nombre']}' es un combo. Los remitos no aceptan combos. Cargalo como productos base."
                }), 400

            # Validar que el item tenga precio (que el pedido haya sido cotizado).
            # Esto blinda el caso "estado cambiado a mano por el dropdown sin
            # apretar el botón Cotizar": el estado queda 'cotizado' pero los
            # precios siguen en 0 → el remito saldría en $0. Mejor abortar.
            precio_item = float(it['precio_unitario'] or 0)
            if precio_item <= 0:
                return jsonify({
                    'success': False,
                    'error': f"El producto '{it['nombre']}' no tiene precio cargado. Cotizá el pedido con el botón 'Cotizar' antes de remitar."
                }), 400

            if not it['es_pesable']:
                stock_disp = float(it['stock'] or 0)
                if float(it['cantidad']) > stock_disp + 0.001:
                    return jsonify({
                        'success': False,
                        'error': f"Stock insuficiente para '{it['nombre']}'. Disponible: {stock_disp}"
                    }), 400

        # ─── 4) Crear registro en `remito` ───
        # Numerar el remito usando la tabla `remito_numerador` (mismo patrón
        # que remitos.py:_proximo_numero_remito). El número es VARCHAR(8)
        # zfilled, no un INT.
        pv_default = db.session.execute(text("""
            SELECT MAX(punto_venta) FROM remito
        """)).scalar() or 1

        # Insertar/incrementar atómicamente el numerador
        db.session.execute(text("""
            INSERT INTO remito_numerador (punto_venta, ultimo_numero)
            VALUES (:pv, 1)
            ON DUPLICATE KEY UPDATE ultimo_numero = ultimo_numero + 1
        """), {'pv': pv_default})

        ultimo_numero_int = db.session.execute(
            text("SELECT ultimo_numero FROM remito_numerador WHERE punto_venta = :pv"),
            {'pv': pv_default}
        ).scalar()
        numero_remito = str(ultimo_numero_int).zfill(8)

        # Heredar zona del cliente (si tiene)
        zona_id = db.session.execute(text("""
            SELECT zona_id FROM cliente WHERE id = :cid
        """), {'cid': cliente_id}).scalar()

        observaciones_remito = f"Generado desde pedido #{pedido_id}"
        if pedido['notas']:
            observaciones_remito += f" — {pedido['notas']}"

        db.session.execute(text("""
            INSERT INTO remito
                (cliente_id, fecha, tipo_comprobante, punto_venta, numero,
                 estado, total_al_emitir, observaciones, usuario_id, zona_id)
            VALUES
                (:cid, :fecha, 'R', :pv, :num,
                 'pendiente', 0, :obs, :uid, :zona_id)
        """), {
            'cid': cliente_id,
            'fecha': datetime.now().date(),
            'pv': pv_default,
            'num': numero_remito,
            'obs': observaciones_remito,
            'uid': session['user_id'],
            'zona_id': zona_id
        })

        remito_id = db.session.execute(text("SELECT LAST_INSERT_ID()")).scalar()

        # ─── 5) Crear detalle del remito y descontar stock ───
        total_remito = Decimal('0')
        # También calculamos los totales del pedido (subtotal/iva por separado)
        subtotal_pedido = Decimal('0')
        iva_pedido = Decimal('0')

        for it in items:
            cant = Decimal(str(it['cantidad']))

            # El precio_unitario del pedido viene SIN IVA (lo conversamos en cargar_venta)
            precio_sin_iva = Decimal(str(it['precio_unitario'] or 0))
            iva_pct = Decimal(str(it['iva'] or 21))
            precio_con_iva = (precio_sin_iva * (Decimal('1') + iva_pct / Decimal('100'))).quantize(Decimal('0.0001'))

            subtotal_con_iva = (cant * precio_con_iva).quantize(Decimal('0.01'))
            total_remito += subtotal_con_iva

            # Para el pedido: subtotal SIN IVA + IVA por separado
            sub_neto = (cant * precio_sin_iva).quantize(Decimal('0.01'))
            sub_iva = (sub_neto * iva_pct / Decimal('100')).quantize(Decimal('0.01'))
            subtotal_pedido += sub_neto
            iva_pedido += sub_iva

            db.session.execute(text("""
                INSERT INTO remito_detalle
                    (remito_id, producto_id, cantidad, precio_unitario_al_emitir,
                     iva, subtotal_al_emitir)
                VALUES
                    (:rid, :pid, :cant, :precio, :iva, :sub)
            """), {
                'rid': remito_id,
                'pid': it['producto_id'],
                'cant': cant,
                'precio': precio_con_iva,
                'iva': iva_pct,
                'sub': subtotal_con_iva
            })

            # Descontar stock
            db.session.execute(text("""
                UPDATE producto SET stock = stock - :cant WHERE id = :pid
            """), {'cant': cant, 'pid': it['producto_id']})

        # Total del remito
        db.session.execute(text("""
            UPDATE remito SET total_al_emitir = :total WHERE id = :id
        """), {'total': total_remito, 'id': remito_id})

        # ─── 6) Marcar pedido como remitado, vincular y actualizar totales ───
        # Si el pedido quedó con totales en 0 (ej: estado cambiado a mano sin cotizar
        # con el botón), los recalculamos desde los items para que la vista de pedidos
        # muestre los importes correctos.
        db.session.execute(text("""
            UPDATE pedido
            SET estado = 'remitado',
                remito_id = :rid,
                subtotal = :subtotal,
                iva = :iva,
                total = :total,
                fecha_actualizacion = NOW()
            WHERE id = :pid
        """), {
            'rid': remito_id,
            'subtotal': subtotal_pedido,
            'iva': iva_pedido,
            'total': subtotal_pedido + iva_pedido,
            'pid': pedido_id
        })

        db.session.commit()

        print(f"✅ Remito #{remito_id} generado desde pedido #{pedido_id}")

        return jsonify({
            'success': True,
            'remito_id': remito_id,
            'numero_remito': f"{str(pv_default).zfill(4)}-{numero_remito}",
            'total': float(total_remito),
            'mensaje': 'Remito generado correctamente'
        })

    except Exception as e:
        db.session.rollback()
        print(f"❌ Error generando remito desde pedido #{pedido_id}: {e}")
        import traceback; traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500