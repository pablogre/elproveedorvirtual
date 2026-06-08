# -*- coding: utf-8 -*-
"""
Blueprint: Zonas de Reparto
---------------------------
ABM de zonas + endpoints para filtrar clientes/remitos/pedidos por zona.
Entrega 1 del módulo de distribución.
"""

from flask import Blueprint, render_template, request, jsonify, session
from extensions import db
from sqlalchemy import text

zonas_bp = Blueprint('zonas', __name__, url_prefix='/zonas')


def _es_admin():
    return session.get('rol') == 'admin'


# =====================================================================
# ABM DE ZONAS
# =====================================================================

@zonas_bp.route('/')
def listado():
    return render_template('zonas_lista.html', es_admin=_es_admin())


@zonas_bp.route('/api/listar')
def api_listar():
    solo_activas = request.args.get('solo_activas', '0') == '1'
    sql = """
        SELECT z.id, z.nombre, z.descripcion, z.color, z.orden_reparto, z.activo,
               (SELECT COUNT(*) FROM cliente c WHERE c.zona_id = z.id AND c.activo = 1) AS clientes_count
          FROM zona z
    """
    if solo_activas:
        sql += " WHERE z.activo = 1"
    sql += " ORDER BY z.orden_reparto, z.nombre"
    rows = db.session.execute(text(sql)).mappings().all()
    return jsonify([{
        'id': r['id'],
        'nombre': r['nombre'],
        'descripcion': r['descripcion'] or '',
        'color': r['color'],
        'orden_reparto': r['orden_reparto'],
        'activo': bool(r['activo']),
        'clientes_count': r['clientes_count']
    } for r in rows])


@zonas_bp.route('/api/guardar', methods=['POST'])
def api_guardar():
    data = request.get_json() or {}
    zona_id = data.get('id')
    nombre = (data.get('nombre') or '').strip()
    descripcion = (data.get('descripcion') or '').strip()
    color = (data.get('color') or '#0d6efd').strip()
    orden = int(data.get('orden_reparto') or 0)
    activo = 1 if data.get('activo', True) else 0

    if not nombre:
        return jsonify({'error': 'El nombre es obligatorio'}), 400
    if len(color) != 7 or not color.startswith('#'):
        color = '#0d6efd'

    try:
        if zona_id:
            # Actualizar
            db.session.execute(text("""
                UPDATE zona SET nombre = :n, descripcion = :d, color = :c,
                                orden_reparto = :o, activo = :a
                 WHERE id = :id
            """), {'n': nombre, 'd': descripcion, 'c': color, 'o': orden, 'a': activo, 'id': zona_id})
        else:
            # Insertar
            db.session.execute(text("""
                INSERT INTO zona (nombre, descripcion, color, orden_reparto, activo)
                VALUES (:n, :d, :c, :o, :a)
            """), {'n': nombre, 'd': descripcion, 'c': color, 'o': orden, 'a': activo})
            zona_id = db.session.execute(text("SELECT LAST_INSERT_ID()")).scalar()

        db.session.commit()
        return jsonify({'ok': True, 'zona_id': zona_id})
    except Exception as e:
        db.session.rollback()
        msg = str(e)
        if 'Duplicate' in msg or 'uk_zona_nombre' in msg:
            return jsonify({'error': f'Ya existe una zona con el nombre "{nombre}"'}), 400
        return jsonify({'error': msg}), 500


@zonas_bp.route('/api/eliminar/<int:zona_id>', methods=['POST'])
def api_eliminar(zona_id):
    """
    Eliminar una zona: la desasigna de clientes/remitos/pedidos (gracias a ON DELETE SET NULL)
    y borra la zona.
    Solo admin.
    """
    if not _es_admin():
        return jsonify({'error': 'Solo el administrador puede eliminar zonas'}), 403

    # Chequeo suave: si tiene clientes, devolver advertencia para que confirmen
    data = request.get_json() or {}
    forzar = data.get('forzar', False)

    count = db.session.execute(text("""
        SELECT COUNT(*) FROM cliente WHERE zona_id = :id AND activo = 1
    """), {'id': zona_id}).scalar() or 0

    if count > 0 and not forzar:
        return jsonify({
            'error': f'Esta zona está asignada a {count} cliente(s). '
                     f'Si la eliminás, esos clientes quedarán sin zona. '
                     f'Llamá de nuevo con forzar=true para confirmar.',
            'requiere_confirmacion': True,
            'clientes_afectados': count
        }), 400

    try:
        db.session.execute(text("DELETE FROM zona WHERE id = :id"), {'id': zona_id})
        db.session.commit()
        return jsonify({'ok': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# =====================================================================
# API auxiliar: listar zonas activas (para dropdowns de otros módulos)
# =====================================================================

@zonas_bp.route('/api/activas')
def api_activas():
    """Devuelve las zonas activas ordenadas — para dropdowns en clientes/remitos/pedidos."""
    rows = db.session.execute(text("""
        SELECT id, nombre, color FROM zona
         WHERE activo = 1
         ORDER BY orden_reparto, nombre
    """)).mappings().all()
    return jsonify([{'id': r['id'], 'nombre': r['nombre'], 'color': r['color']} for r in rows])


# =====================================================================
# Asignación masiva de zona por prefijo de dirección
# (herramienta útil para asignar muchos clientes de una)
# =====================================================================

@zonas_bp.route('/api/asignar_masivo', methods=['POST'])
def api_asignar_masivo():
    """
    Asigna una zona a todos los clientes cuya dirección contenga el texto dado.
    Útil para clasificar en lotes (ej: buscar "Av Pellegrini" → asignar zona "Centro").
    Solo admin.
    """
    if not _es_admin():
        return jsonify({'error': 'Solo el administrador puede asignar zonas masivamente'}), 403

    data = request.get_json() or {}
    zona_id = data.get('zona_id')
    patron = (data.get('patron') or '').strip()
    solo_sin_zona = data.get('solo_sin_zona', True)

    if not zona_id or not patron:
        return jsonify({'error': 'Faltan parámetros (zona_id y patrón de dirección)'}), 400

    try:
        sql = "UPDATE cliente SET zona_id = :zid WHERE direccion LIKE :patron AND activo = 1"
        if solo_sin_zona:
            sql += " AND zona_id IS NULL"
        result = db.session.execute(text(sql), {'zid': zona_id, 'patron': f'%{patron}%'})
        db.session.commit()
        return jsonify({'ok': True, 'clientes_actualizados': result.rowcount})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500