# -*- coding: utf-8 -*-
"""
Blueprint: Categorías de Productos (SCHIRO)
--------------------------------------------
ABM de categorías de productos con soporte para:
- Listar, crear, editar y eliminar categorías
- Renombrado masivo: si se cambia el nombre, actualiza los productos que la usaban
- Validación: no permite eliminar categorías con productos activos
- Colores personalizables para cada categoría (badges visuales)

UBICACIÓN: C:\\schiro\\categorias.py

REGISTRO EN app.py:
    from categorias import categorias_bp
    app.register_blueprint(categorias_bp)
"""

from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from extensions import db
from sqlalchemy import text

categorias_bp = Blueprint('categorias', __name__, url_prefix='/categorias')


# =====================================================================
# HELPERS
# =====================================================================

def _es_admin():
    return session.get('rol') == 'admin'


def _usuario_id():
    return session.get('usuario_id') or session.get('user_id')


# =====================================================================
# PÁGINA DEL ABM
# =====================================================================

@categorias_bp.route('/')
def listado():
    """Página ABM de categorías."""
    if not _usuario_id():
        return redirect(url_for('login'))
    return render_template('categorias.html')


# =====================================================================
# API - LISTAR
# =====================================================================

@categorias_bp.route('/api/listar')
def api_listar():
    """Devuelve todas las categorías con conteo de productos."""
    if not _usuario_id():
        return jsonify({'error': 'No autenticado'}), 401

    incluir_inactivas = request.args.get('incluir_inactivas') == '1'

    where_activo = '' if incluir_inactivas else 'WHERE c.activo = 1'

    sql = f"""
        SELECT c.id, c.nombre, c.color, c.activo, c.orden,
               DATE_FORMAT(c.fecha_creacion, '%Y-%m-%d %H:%i') AS fecha_creacion,
               (SELECT COUNT(*) FROM producto p
                 WHERE p.categoria = c.nombre AND p.activo = 1) AS cantidad_productos
          FROM categoria c
          {where_activo}
         ORDER BY c.orden, c.nombre
    """
    rows = db.session.execute(text(sql)).mappings().all()

    return jsonify([{
        'id': r['id'],
        'nombre': r['nombre'],
        'color': r['color'] or '#6c757d',
        'activo': bool(r['activo']),
        'orden': r['orden'] or 0,
        'fecha_creacion': r['fecha_creacion'],
        'cantidad_productos': r['cantidad_productos'],
    } for r in rows])


# =====================================================================
# API - GUARDAR (CREAR O ACTUALIZAR)
# =====================================================================

@categorias_bp.route('/api/guardar', methods=['POST'])
def api_guardar():
    """
    Crea o actualiza una categoría.
    Si se cambia el nombre, actualiza los productos que la usaban.
    """
    if not _usuario_id():
        return jsonify({'error': 'No autenticado'}), 401

    data = request.get_json() or {}
    categoria_id = data.get('id')
    nombre_nuevo = (data.get('nombre') or '').strip().lower()
    color = (data.get('color') or '#6c757d').strip()
    orden = int(data.get('orden') or 0)
    activo = 1 if data.get('activo', True) else 0

    # Validaciones
    if not nombre_nuevo:
        return jsonify({'error': 'El nombre es obligatorio'}), 400

    if len(nombre_nuevo) > 100:
        return jsonify({'error': 'El nombre no puede superar 100 caracteres'}), 400

    try:
        if categoria_id:
            # ========= UPDATE =========
            actual = db.session.execute(
                text("SELECT nombre FROM categoria WHERE id = :id"),
                {'id': categoria_id}
            ).first()
            if not actual:
                return jsonify({'error': 'Categoría no encontrada'}), 404

            nombre_viejo = actual[0]

            # Verificar que no haya duplicado con otro id
            dup = db.session.execute(
                text("SELECT id FROM categoria WHERE nombre = :n AND id != :id"),
                {'n': nombre_nuevo, 'id': categoria_id}
            ).first()
            if dup:
                return jsonify({
                    'error': f'Ya existe otra categoría con el nombre "{nombre_nuevo}"'
                }), 400

            # Actualizar categoría
            db.session.execute(text("""
                UPDATE categoria
                   SET nombre = :n, color = :c, orden = :o, activo = :a
                 WHERE id = :id
            """), {'n': nombre_nuevo, 'c': color, 'o': orden, 'a': activo, 'id': categoria_id})

            # Si cambió el nombre, actualizar productos
            productos_actualizados = 0
            if nombre_viejo != nombre_nuevo:
                resultado = db.session.execute(text("""
                    UPDATE producto SET categoria = :nuevo WHERE categoria = :viejo
                """), {'nuevo': nombre_nuevo, 'viejo': nombre_viejo})
                productos_actualizados = resultado.rowcount

            db.session.commit()

            mensaje = 'Categoría actualizada'
            if productos_actualizados > 0:
                mensaje += f' (se actualizaron {productos_actualizados} productos)'

            return jsonify({
                'success': True,
                'id': categoria_id,
                'mensaje': mensaje
            })

        else:
            # ========= INSERT =========
            dup = db.session.execute(
                text("SELECT id FROM categoria WHERE nombre = :n"),
                {'n': nombre_nuevo}
            ).first()
            if dup:
                return jsonify({
                    'error': f'Ya existe una categoría con el nombre "{nombre_nuevo}"'
                }), 400

            db.session.execute(text("""
                INSERT INTO categoria (nombre, color, orden, activo)
                VALUES (:n, :c, :o, :a)
            """), {'n': nombre_nuevo, 'c': color, 'o': orden, 'a': activo})

            nuevo_id = db.session.execute(text("SELECT LAST_INSERT_ID()")).scalar()
            db.session.commit()

            return jsonify({
                'success': True,
                'id': nuevo_id,
                'mensaje': 'Categoría creada'
            })

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error: {str(e)}'}), 500


# =====================================================================
# API - ELIMINAR
# =====================================================================

@categorias_bp.route('/api/eliminar/<int:id>', methods=['POST'])
def api_eliminar(id):
    """Elimina una categoría si no tiene productos asociados."""
    if not _usuario_id():
        return jsonify({'error': 'No autenticado'}), 401

    if not _es_admin():
        return jsonify({'error': 'Solo el administrador puede eliminar categorías'}), 403

    try:
        cat = db.session.execute(
            text("SELECT nombre FROM categoria WHERE id = :id"),
            {'id': id}
        ).first()
        if not cat:
            return jsonify({'error': 'Categoría no encontrada'}), 404

        nombre = cat[0]

        # Verificar que no tenga productos asociados
        productos = db.session.execute(
            text("SELECT COUNT(*) FROM producto WHERE categoria = :n AND activo = 1"),
            {'n': nombre}
        ).scalar()

        if productos > 0:
            return jsonify({
                'error': (
                    f'No se puede eliminar "{nombre}": hay {productos} producto(s) '
                    f'activos usando esta categoría. Cambiá los productos a otra '
                    f'categoría primero, o desactivala en vez de eliminar.'
                )
            }), 400

        db.session.execute(text("DELETE FROM categoria WHERE id = :id"), {'id': id})
        db.session.commit()

        return jsonify({'success': True, 'mensaje': f'Categoría "{nombre}" eliminada'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error: {str(e)}'}), 500