# -*- coding: utf-8 -*-
"""
═══════════════════════════════════════════════════════════════════════════════
 FACTUFACIL — INTEGRACIÓN MERCADO PAGO QR (POLLING)
═══════════════════════════════════════════════════════════════════════════════
Arquitectura: token por cliente, polling sin webhook.
Cada cliente FactuFácil pega su access_token de MP en /mp/config.
El POS genera una preferencia, muestra QR, hace polling cada 2 seg al
endpoint /api/mp/estado_pago/<id>. Cuando se aprueba, cierra la venta.

Sin SDK externo. Solo `requests`.
═══════════════════════════════════════════════════════════════════════════════
"""
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy import text
from functools import wraps
import requests
import uuid
import json
import traceback

from extensions import db

mp_qr_bp = Blueprint('mp_qr', __name__)

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURACIÓN / CONSTANTES
# ─────────────────────────────────────────────────────────────────────────────
MP_API_BASE = "https://api.mercadopago.com"
TIMEOUT_HTTP = 15  # segundos para llamadas a MP

# Código del medio de pago en la tabla `medios_pago`
MEDIO_PAGO_CODIGO = 'mp_qr'


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def login_required(f):
    """Mismo patrón de auth que usa app.py."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'No autorizado'}), 401
        return f(*args, **kwargs)
    return wrapper


def _get_config():
    """Devuelve la fila de mp_config (o None si no hay)."""
    row = db.session.execute(text("""
        SELECT id, access_token, public_key, user_id_mp, ambiente, activo, timeout_segundos
          FROM mp_config
         WHERE activo = 1
         ORDER BY id DESC
         LIMIT 1
    """)).fetchone()
    if not row:
        return None
    return {
        'id': row.id,
        'access_token': row.access_token,
        'public_key': row.public_key,
        'user_id_mp': row.user_id_mp,
        'ambiente': row.ambiente,
        'activo': row.activo,
        'timeout_segundos': row.timeout_segundos or 300,
    }


def _mp_headers(access_token):
    return {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
    }


def _consultar_pago_mp(payment_id, access_token):
    """Consulta /v1/payments/<id> en MP."""
    url = f"{MP_API_BASE}/v1/payments/{payment_id}"
    r = requests.get(url, headers=_mp_headers(access_token), timeout=TIMEOUT_HTTP)
    r.raise_for_status()
    return r.json()


def _buscar_pago_por_external_ref(external_reference, access_token):
    """
    Busca pagos en MP filtrando por external_reference.
    Esto es lo que usamos para el polling: como NO tenemos webhook,
    le preguntamos a MP "¿hay algún pago aprobado con esta ref?"
    """
    url = f"{MP_API_BASE}/v1/payments/search"
    params = {
        'external_reference': external_reference,
        'sort': 'date_created',
        'criteria': 'desc',
        'limit': 5,
    }
    r = requests.get(url, headers=_mp_headers(access_token), params=params, timeout=TIMEOUT_HTTP)
    r.raise_for_status()
    return r.json()


# ─────────────────────────────────────────────────────────────────────────────
# 1) PANTALLA DE CONFIGURACIÓN
# ─────────────────────────────────────────────────────────────────────────────
@mp_qr_bp.route('/mp/config', methods=['GET', 'POST'])
def mp_config_view():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        access_token = (request.form.get('access_token') or '').strip()
        public_key = (request.form.get('public_key') or '').strip()
        ambiente = request.form.get('ambiente', 'prod')
        timeout_segundos = int(request.form.get('timeout_segundos') or 300)

        if not access_token:
            return jsonify({'success': False, 'error': 'Access token requerido'}), 400

        # Test rápido contra MP: pedir info de la cuenta del usuario
        try:
            r = requests.get(
                f"{MP_API_BASE}/users/me",
                headers=_mp_headers(access_token),
                timeout=TIMEOUT_HTTP
            )
            if r.status_code != 200:
                return jsonify({
                    'success': False,
                    'error': f'Token inválido (MP respondió {r.status_code}): {r.text[:200]}'
                }), 400
            user_info = r.json()
            user_id_mp = str(user_info.get('id', ''))
        except Exception as e:
            return jsonify({'success': False, 'error': f'No se pudo validar el token: {e}'}), 400

        # Reemplazar config existente (mantenemos una sola activa)
        db.session.execute(text("UPDATE mp_config SET activo = 0"))
        db.session.execute(text("""
            INSERT INTO mp_config (access_token, public_key, user_id_mp, ambiente, activo, timeout_segundos)
            VALUES (:tok, :pk, :uid, :amb, 1, :tout)
        """), {
            'tok': access_token,
            'pk': public_key or None,
            'uid': user_id_mp,
            'amb': ambiente,
            'tout': timeout_segundos,
        })
        db.session.commit()

        return jsonify({
            'success': True,
            'mensaje': f'Credenciales OK — Cuenta MP #{user_id_mp} ({user_info.get("nickname","")})',
            'user_id_mp': user_id_mp,
        })

    # GET
    cfg = _get_config()
    return render_template('mp_qr_config.html', cfg=cfg)


# ─────────────────────────────────────────────────────────────────────────────
# 2) TEST DE CREDENCIALES (opcional, botón en la pantalla de config)
# ─────────────────────────────────────────────────────────────────────────────
@mp_qr_bp.route('/mp/test_credenciales', methods=['POST'])
@login_required
def mp_test_credenciales():
    cfg = _get_config()
    if not cfg:
        return jsonify({'success': False, 'error': 'No hay credenciales configuradas'}), 400
    try:
        r = requests.get(
            f"{MP_API_BASE}/users/me",
            headers=_mp_headers(cfg['access_token']),
            timeout=TIMEOUT_HTTP
        )
        if r.status_code != 200:
            return jsonify({'success': False, 'error': f'MP respondió {r.status_code}: {r.text[:200]}'}), 400
        info = r.json()
        return jsonify({
            'success': True,
            'user_id_mp': info.get('id'),
            'nickname': info.get('nickname'),
            'email': info.get('email'),
            'site_id': info.get('site_id'),
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ─────────────────────────────────────────────────────────────────────────────
# 3) CREAR QR  → desde el modal de medios de pago
# ─────────────────────────────────────────────────────────────────────────────
@mp_qr_bp.route('/api/mp/crear_qr', methods=['POST'])
@login_required
def api_mp_crear_qr():
    """
    Body: { monto: 12345.67, descripcion: "Venta #..." }
    Devuelve: { mp_pago_id, qr_data, external_reference, timeout_segundos }
    """
    cfg = _get_config()
    if not cfg:
        return jsonify({
            'success': False,
            'error': 'MercadoPago no está configurado. Ir a Sistema → MercadoPago QR.'
        }), 400

    data = request.get_json() or {}
    try:
        monto = float(data.get('monto') or 0)
    except (TypeError, ValueError):
        return jsonify({'success': False, 'error': 'Monto inválido'}), 400

    if monto <= 0:
        return jsonify({'success': False, 'error': 'El monto debe ser mayor a 0'}), 400

    descripcion = (data.get('descripcion') or 'Cobro FactuFácil')[:250]
    external_reference = f"ff_{uuid.uuid4().hex[:16]}"

    # Crear preferencia en MP
    preferencia = {
        "items": [{
            "title": descripcion,
            "quantity": 1,
            "unit_price": round(monto, 2),
            "currency_id": "ARS",
        }],
        "external_reference": external_reference,
        "expires": True,
        "expiration_date_to": (datetime.utcnow() + timedelta(seconds=cfg['timeout_segundos'] + 60))
            .strftime('%Y-%m-%dT%H:%M:%S.000-00:00'),
        "binary_mode": True,  # solo aprobado/rechazado, sin "in_process"
    }

    try:
        r = requests.post(
            f"{MP_API_BASE}/checkout/preferences",
            headers=_mp_headers(cfg['access_token']),
            json=preferencia,
            timeout=TIMEOUT_HTTP
        )
        if r.status_code not in (200, 201):
            return jsonify({
                'success': False,
                'error': f'MP rechazó la preferencia ({r.status_code}): {r.text[:300]}'
            }), 400
        pref = r.json()
    except Exception as e:
        return jsonify({'success': False, 'error': f'Error contactando MP: {e}'}), 500

    preference_id = pref.get('id')
    init_point = pref.get('init_point')  # URL del checkout — esto va dentro del QR
    if not init_point:
        return jsonify({'success': False, 'error': 'MP no devolvió init_point'}), 500

    # Guardar localmente
    res = db.session.execute(text("""
        INSERT INTO mp_pago (preference_id, external_reference, monto, estado, qr_data, raw_response)
        VALUES (:pref, :ext, :monto, 'pending', :qr, :raw)
    """), {
        'pref': preference_id,
        'ext': external_reference,
        'monto': round(monto, 2),
        'qr': init_point,
        'raw': json.dumps(pref)[:60000],
    })
    db.session.commit()
    mp_pago_id = res.lastrowid

    return jsonify({
        'success': True,
        'mp_pago_id': mp_pago_id,
        'preference_id': preference_id,
        'external_reference': external_reference,
        'qr_data': init_point,
        'monto': round(monto, 2),
        'timeout_segundos': cfg['timeout_segundos'],
    })


# ─────────────────────────────────────────────────────────────────────────────
# 4) POLLING DE ESTADO  → el modal llama cada 2 seg
# ─────────────────────────────────────────────────────────────────────────────
@mp_qr_bp.route('/api/mp/estado_pago/<int:mp_pago_id>', methods=['GET'])
@login_required
def api_mp_estado_pago(mp_pago_id):
    """
    El POS llama cada 2 segundos. Devuelve:
      { estado: 'pending'|'approved'|'rejected'|'cancelled'|'expired',
        payment_id, metodo_detalle, monto }
    """
    cfg = _get_config()
    if not cfg:
        return jsonify({'success': False, 'error': 'MP no configurado'}), 400

    row = db.session.execute(text("""
        SELECT id, preference_id, payment_id, external_reference, monto, estado, fecha_creacion
          FROM mp_pago WHERE id = :id
    """), {'id': mp_pago_id}).fetchone()

    if not row:
        return jsonify({'success': False, 'error': 'Pago no encontrado'}), 404

    # Si ya está aprobado/rechazado/cancelado, devolver lo guardado sin pegarle a MP
    if row.estado in ('approved', 'rejected', 'cancelled', 'expired'):
        return jsonify({
            'success': True,
            'estado': row.estado,
            'payment_id': row.payment_id,
            'monto': float(row.monto),
        })

    # Si pasó el timeout, marcar como expired
    edad = (datetime.now() - row.fecha_creacion).total_seconds()
    if edad > cfg['timeout_segundos']:
        db.session.execute(text("UPDATE mp_pago SET estado = 'expired' WHERE id = :id"),
                           {'id': row.id})
        db.session.commit()
        return jsonify({'success': True, 'estado': 'expired', 'monto': float(row.monto)})

    # Consultar a MP por external_reference
    try:
        search = _buscar_pago_por_external_ref(row.external_reference, cfg['access_token'])
        results = search.get('results') or []
    except Exception as e:
        # Error transitorio: devolvemos pending para que el POS siga reintentando
        print(f"⚠️ MP search error: {e}")
        return jsonify({'success': True, 'estado': 'pending', 'monto': float(row.monto)})

    if not results:
        return jsonify({'success': True, 'estado': 'pending', 'monto': float(row.monto)})

    # Tomamos el más reciente
    pago_mp = results[0]
    status = pago_mp.get('status')  # approved / pending / in_process / rejected / cancelled / refunded
    payment_id_mp = str(pago_mp.get('id') or '')
    metodo = pago_mp.get('payment_method_id') or pago_mp.get('payment_type_id') or ''

    if status == 'approved':
        db.session.execute(text("""
            UPDATE mp_pago
               SET estado = 'approved',
                   payment_id = :pid,
                   metodo_detalle = :met,
                   fecha_aprobacion = NOW(),
                   raw_response = :raw
             WHERE id = :id
        """), {
            'pid': payment_id_mp,
            'met': metodo[:50],
            'raw': json.dumps(pago_mp)[:60000],
            'id': row.id,
        })
        db.session.commit()
        return jsonify({
            'success': True,
            'estado': 'approved',
            'payment_id': payment_id_mp,
            'metodo_detalle': metodo,
            'monto': float(row.monto),
        })

    if status in ('rejected', 'cancelled'):
        db.session.execute(text("""
            UPDATE mp_pago
               SET estado = :est, payment_id = :pid, metodo_detalle = :met, raw_response = :raw
             WHERE id = :id
        """), {
            'est': status,
            'pid': payment_id_mp,
            'met': metodo[:50],
            'raw': json.dumps(pago_mp)[:60000],
            'id': row.id,
        })
        db.session.commit()
        return jsonify({'success': True, 'estado': status, 'monto': float(row.monto)})

    return jsonify({'success': True, 'estado': 'pending', 'monto': float(row.monto)})


# ─────────────────────────────────────────────────────────────────────────────
# 5) CANCELAR un QR  (el cajero apretó "Cancelar")
# ─────────────────────────────────────────────────────────────────────────────
@mp_qr_bp.route('/api/mp/cancelar/<int:mp_pago_id>', methods=['POST'])
@login_required
def api_mp_cancelar(mp_pago_id):
    db.session.execute(text("""
        UPDATE mp_pago SET estado = 'cancelled'
         WHERE id = :id AND estado = 'pending'
    """), {'id': mp_pago_id})
    db.session.commit()
    return jsonify({'success': True})


# ─────────────────────────────────────────────────────────────────────────────
# 5.b) IMPRIMIR el QR en la térmica (para que el cliente lo escanee del ticket)
# ─────────────────────────────────────────────────────────────────────────────
@mp_qr_bp.route('/api/mp/imprimir_qr/<int:mp_pago_id>', methods=['POST'])
@login_required
def api_mp_imprimir_qr(mp_pago_id):
    """Imprime el QR de cobro en la impresora térmica configurada."""
    row = db.session.execute(text("""
        SELECT qr_data, monto, estado, external_reference
          FROM mp_pago WHERE id = :id
    """), {'id': mp_pago_id}).fetchone()

    if not row:
        return jsonify({'success': False, 'error': 'Pago no encontrado'}), 404
    if row.estado not in ('pending',):
        return jsonify({'success': False, 'error': f'El QR está en estado {row.estado}, no se puede imprimir'}), 400
    if not row.qr_data:
        return jsonify({'success': False, 'error': 'El pago no tiene QR data'}), 400

    try:
        # Import diferido: la impresora puede no estar disponible en algunos clientes
        from impresora_termica import impresora_termica
    except Exception as e:
        return jsonify({'success': False, 'error': f'Módulo de impresión no disponible: {e}'}), 500

    try:
        ok = impresora_termica.imprimir_qr_cobro_mp(
            url_pago=row.qr_data,
            monto=float(row.monto),
            descripcion=f'Cobro QR - Ref {row.external_reference}'
        )
        if ok:
            return jsonify({'success': True, 'mensaje': 'QR impreso correctamente'})
        else:
            return jsonify({'success': False, 'error': 'La impresora no respondió. Revisá que esté encendida y con papel.'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ─────────────────────────────────────────────────────────────────────────────
# 6) VINCULAR pago QR con la factura final (lo llama el front DESPUÉS de procesar_venta)
# ─────────────────────────────────────────────────────────────────────────────
@mp_qr_bp.route('/api/mp/vincular_factura', methods=['POST'])
@login_required
def api_mp_vincular_factura():
    data = request.get_json() or {}
    mp_pago_id = data.get('mp_pago_id')
    factura_id = data.get('factura_id')
    if not mp_pago_id or not factura_id:
        return jsonify({'success': False, 'error': 'Faltan datos'}), 400
    db.session.execute(text("""
        UPDATE mp_pago SET factura_id = :fid WHERE id = :id
    """), {'fid': factura_id, 'id': mp_pago_id})
    db.session.commit()
    return jsonify({'success': True})


# ─────────────────────────────────────────────────────────────────────────────
# 7) HISTORIAL / CONCILIACIÓN
# ─────────────────────────────────────────────────────────────────────────────
@mp_qr_bp.route('/mp/pagos', methods=['GET'])
def mp_pagos_listado():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    desde = request.args.get('desde')
    hasta = request.args.get('hasta')
    estado = request.args.get('estado', '')

    sql = """
        SELECT p.id, p.preference_id, p.payment_id, p.external_reference,
               p.monto, p.estado, p.metodo_detalle, p.factura_id,
               p.fecha_creacion, p.fecha_aprobacion,
               f.numero AS factura_numero
          FROM mp_pago p
     LEFT JOIN factura f ON f.id = p.factura_id
         WHERE 1=1
    """
    params = {}
    if desde:
        sql += " AND p.fecha_creacion >= :desde "
        params['desde'] = desde + ' 00:00:00'
    if hasta:
        sql += " AND p.fecha_creacion <= :hasta "
        params['hasta'] = hasta + ' 23:59:59'
    if estado:
        sql += " AND p.estado = :est "
        params['est'] = estado
    sql += " ORDER BY p.fecha_creacion DESC LIMIT 500 "

    rows = db.session.execute(text(sql), params).fetchall()
    pagos = [{
        'id': r.id,
        'preference_id': r.preference_id,
        'payment_id': r.payment_id,
        'external_reference': r.external_reference,
        'monto': float(r.monto),
        'estado': r.estado,
        'metodo_detalle': r.metodo_detalle,
        'factura_id': r.factura_id,
        'factura_numero': r.factura_numero,
        'fecha_creacion': r.fecha_creacion.strftime('%Y-%m-%d %H:%M:%S') if r.fecha_creacion else '',
        'fecha_aprobacion': r.fecha_aprobacion.strftime('%Y-%m-%d %H:%M:%S') if r.fecha_aprobacion else '',
    } for r in rows]

    return render_template('mp_qr_pagos.html', pagos=pagos, filtros={
        'desde': desde or '', 'hasta': hasta or '', 'estado': estado
    })


# ─────────────────────────────────────────────────────────────────────────────
# REGISTRO
# ─────────────────────────────────────────────────────────────────────────────
def init_mp_qr(app):
    """Registra el blueprint en la app Flask."""
    app.register_blueprint(mp_qr_bp)
    print("✅ MercadoPago QR integrado")