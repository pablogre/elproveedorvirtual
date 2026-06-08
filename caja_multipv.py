# -*- coding: utf-8 -*-
"""
caja_multipv.py - Sistema de Caja MULTI PUNTO DE VENTA  (v6)
═══════════════════════════════════════════════════════════════════════════════
v6 (2026-05-02): + endpoint GET /api/caja-pv/<id>/desglose
                   - Desglose línea por línea para auditoría
                   - Cada factura, gasto, movimiento, transferencia
v5 (2026-05-01): + endpoint GET /api/caja-pv/resumen-consolidado
                   - Agrupa totales (ventas, gastos, transferencias, balance)
                   - Detalle por caja
                   - Filtros: fecha, fecha_desde/fecha_hasta, pv
                   - Día operativo (apertura→cierre de cada caja)
v4: transferir, anular, listar transferencias
v3: movimiento (ingreso/egreso) + listar movimientos
v2: cerrar + helper de cálculo filtrado por PV
v1: abrir, estado, listar-abiertas
═══════════════════════════════════════════════════════════════════════════════
"""

from flask import Blueprint, request, jsonify, session
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo
from sqlalchemy import text
from decimal import Decimal

TZ_AR = ZoneInfo("America/Argentina/Buenos_Aires")


# ─────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────

def _now_ar():
    return datetime.now(TZ_AR).replace(tzinfo=None)


def _pv_activo(default_pv=1):
    return int(session.get('punto_venta', default_pv))


def _user_id_activo(default_uid=3):
    return int(session.get('user_id', default_uid))


def _es_admin():
    return session.get('rol') == 'admin'


def _parse_fecha(s):
    """Parsea string YYYY-MM-DD a date. Retorna None si inválido."""
    if not s:
        return None
    try:
        return datetime.strptime(s, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return None


def _calcular_efectivo_teorico_pv(db, caja_id, punto_venta,
                                  fecha_apertura, fecha_cierre=None):
    """Calcula el efectivo teórico de una caja, filtrando ventas por PV."""
    try:
        if fecha_cierre is None:
            fecha_cierre = _now_ar()

        row = db.session.execute(text("""
            SELECT monto_inicial FROM cajas WHERE id = :id
        """), {'id': caja_id}).first()

        if not row:
            return 0.0

        efectivo = float(row[0] or 0)
        monto_inicial = efectivo

        movs = db.session.execute(text("""
            SELECT tipo, COALESCE(SUM(monto), 0)
            FROM movimientos_caja
            WHERE caja_id = :cid
            GROUP BY tipo
        """), {'cid': caja_id}).fetchall()

        ingresos_man = 0.0
        egresos_man = 0.0
        for tipo, total in movs:
            total = float(total or 0)
            if tipo == 'ingreso':
                ingresos_man = total
                efectivo += total
            elif tipo == 'egreso':
                egresos_man = total
                efectivo -= total

        ventas_row = db.session.execute(text("""
            SELECT COALESCE(SUM(mp.importe), 0)
            FROM medios_pago mp
            INNER JOIN factura f ON mp.factura_id = f.id
            WHERE mp.medio_pago = 'efectivo'
              AND f.estado != 'anulada'
              AND f.punto_venta = :pv
              AND f.fecha BETWEEN :fi AND :ff
        """), {
            'pv': punto_venta, 'fi': fecha_apertura, 'ff': fecha_cierre
        }).first()
        ventas_efectivo = float(ventas_row[0] or 0)
        efectivo += ventas_efectivo

        gastos_row = db.session.execute(text("""
            SELECT COALESCE(SUM(monto), 0)
            FROM gastos
            WHERE metodo_pago = 'efectivo' AND activo = 1 AND caja_id = :cid
        """), {'cid': caja_id}).first()
        gastos_efectivo = float(gastos_row[0] or 0)
        efectivo -= gastos_efectivo

        print(f"🧮 Efectivo teórico Caja {caja_id} (PV {punto_venta}):")
        print(f"   - Monto inicial:        ${monto_inicial:.2f}")
        print(f"   - Movimientos manuales: +${ingresos_man:.2f} / -${egresos_man:.2f}")
        print(f"   - Ventas efectivo PV:   +${ventas_efectivo:.2f}")
        print(f"   - Gastos efectivo:      -${gastos_efectivo:.2f}")
        print(f"   ═══ TOTAL: ${efectivo:.2f}")

        return efectivo

    except Exception as e:
        print(f"❌ Error calculando efectivo teórico: {e}")
        import traceback; traceback.print_exc()
        return 0.0


def _detalle_caja_resumen(db, caja_row):
    """
    Devuelve el detalle completo de una caja para el resumen consolidado.
    
    caja_row: tuple con (id, fecha_apertura, fecha_cierre, monto_inicial,
                        efectivo_teorico, efectivo_real, diferencia,
                        estado, punto_venta, usuario_apertura_id, usuario_cierre_id)
    """
    caja_id = int(caja_row[0])
    fecha_apertura = caja_row[1]
    fecha_cierre = caja_row[2]
    monto_inicial = float(caja_row[3] or 0)
    estado = caja_row[7]
    punto_venta = int(caja_row[8])

    fecha_fin_calculo = fecha_cierre if fecha_cierre else _now_ar()

    # ── Movimientos manuales (no incluye los de transferencia) ──
    # Los movimientos de transferencia tienen notas que empiezan con 'TRANSFERENCIA'
    # o 'ANULACIÓN'. Los separamos para no contar dos veces.
    movs = db.session.execute(text("""
        SELECT tipo, COALESCE(SUM(monto), 0), COUNT(*)
        FROM movimientos_caja
        WHERE caja_id = :cid
          AND (notas IS NULL 
               OR (notas NOT LIKE 'TRANSFERENCIA%' 
                   AND notas NOT LIKE 'ANULACI%'))
        GROUP BY tipo
    """), {'cid': caja_id}).fetchall()

    ingresos_manuales = 0.0
    egresos_manuales = 0.0
    cantidad_movs = 0
    for tipo, total, qty in movs:
        total = float(total or 0)
        cantidad_movs += int(qty or 0)
        if tipo == 'ingreso':
            ingresos_manuales = total
        elif tipo == 'egreso':
            egresos_manuales = total

    # ── Transferencias activas (no anuladas) ───────────────────
    trans_recibidas = db.session.execute(text("""
        SELECT COALESCE(SUM(monto), 0), COUNT(*)
        FROM transferencia_caja
        WHERE caja_destino_id = :cid AND anulada = 0
    """), {'cid': caja_id}).first()

    trans_enviadas = db.session.execute(text("""
        SELECT COALESCE(SUM(monto), 0), COUNT(*)
        FROM transferencia_caja
        WHERE caja_origen_id = :cid AND anulada = 0
    """), {'cid': caja_id}).first()

    monto_recibido = float(trans_recibidas[0] or 0)
    cantidad_recibidas = int(trans_recibidas[1] or 0)
    monto_enviado = float(trans_enviadas[0] or 0)
    cantidad_enviadas = int(trans_enviadas[1] or 0)

    # ── Ventas en efectivo del PV en el rango ──────────────────
    ventas_row = db.session.execute(text("""
        SELECT COALESCE(SUM(mp.importe), 0), COUNT(DISTINCT f.id)
        FROM medios_pago mp
        INNER JOIN factura f ON mp.factura_id = f.id
        WHERE mp.medio_pago = 'efectivo'
          AND f.estado != 'anulada'
          AND f.punto_venta = :pv
          AND f.fecha BETWEEN :fi AND :ff
    """), {
        'pv': punto_venta, 'fi': fecha_apertura, 'ff': fecha_fin_calculo
    }).first()
    ventas_efectivo = float(ventas_row[0] or 0)
    cantidad_facturas = int(ventas_row[1] or 0)

    # ── Ventas por TODOS los medios de pago ────────────────────
    ventas_por_medio = db.session.execute(text("""
        SELECT mp.medio_pago, COALESCE(SUM(mp.importe), 0), COUNT(DISTINCT f.id)
        FROM medios_pago mp
        INNER JOIN factura f ON mp.factura_id = f.id
        WHERE f.estado != 'anulada'
          AND f.punto_venta = :pv
          AND f.fecha BETWEEN :fi AND :ff
        GROUP BY mp.medio_pago
        ORDER BY SUM(mp.importe) DESC
    """), {
        'pv': punto_venta, 'fi': fecha_apertura, 'ff': fecha_fin_calculo
    }).fetchall()

    ventas_desglose = {}
    ventas_total = 0.0
    cantidad_facturas_total = 0
    for medio, total, qty in ventas_por_medio:
        ventas_desglose[medio] = float(total or 0)
        ventas_total += float(total or 0)
        cantidad_facturas_total = max(cantidad_facturas_total, int(qty or 0))

    cantidad_facturas = cantidad_facturas_total or cantidad_facturas

    # ── Gastos en efectivo de esta caja ────────────────────────
    gastos_row = db.session.execute(text("""
        SELECT COALESCE(SUM(monto), 0), COUNT(*)
        FROM gastos
        WHERE metodo_pago = 'efectivo' AND activo = 1 AND caja_id = :cid
    """), {'cid': caja_id}).first()
    gastos_efectivo = float(gastos_row[0] or 0)
    cantidad_gastos = int(gastos_row[1] or 0)

    # ── Calcular efectivo teórico actual ───────────────────────
    efectivo_teorico = (
        monto_inicial
        + ingresos_manuales
        - egresos_manuales
        + ventas_efectivo
        - gastos_efectivo
        + monto_recibido    # transferencias entrantes
        - monto_enviado     # transferencias salientes
    )

    # ── Si la caja está cerrada, usar valores reales del cierre ──
    efectivo_real = float(caja_row[5] or 0) if estado == 'cerrada' else None
    diferencia = float(caja_row[6] or 0) if estado == 'cerrada' else None

    return {
        'id': caja_id,
        'punto_venta': punto_venta,
        'estado': estado,
        'fecha_apertura': fecha_apertura.isoformat() if fecha_apertura else None,
        'fecha_cierre': fecha_cierre.isoformat() if fecha_cierre else None,
        'usuario_apertura_id': caja_row[9],
        'usuario_cierre_id': caja_row[10],
        'monto_inicial': monto_inicial,
        'ventas_efectivo': ventas_efectivo,
        'ventas_total': ventas_total,
        'ventas_desglose': ventas_desglose,
        'cantidad_facturas': cantidad_facturas,
        'gastos_efectivo': gastos_efectivo,
        'cantidad_gastos': cantidad_gastos,
        'ingresos_manuales': ingresos_manuales,
        'egresos_manuales': egresos_manuales,
        'cantidad_movimientos': cantidad_movs,
        'transferencias_recibidas': monto_recibido,
        'cantidad_recibidas': cantidad_recibidas,
        'transferencias_enviadas': monto_enviado,
        'cantidad_enviadas': cantidad_enviadas,
        'efectivo_teorico': efectivo_teorico,
        'efectivo_real': efectivo_real,
        'diferencia': diferencia,
    }


def _validar_caja_y_permisos(db, caja_id, requerir_abierta=True):
    """Valida que la caja exista y el usuario tenga permisos."""
    if not caja_id:
        return None, (jsonify({
            'success': False, 'error': 'caja_id es requerido'
        }), 400)

    try:
        caja_id = int(caja_id)
    except (TypeError, ValueError):
        return None, (jsonify({
            'success': False, 'error': 'caja_id debe ser entero'
        }), 400)

    row = db.session.execute(text("""
        SELECT id, punto_venta, fecha_apertura, monto_inicial, estado
        FROM cajas
        WHERE id = :id AND activa = 1
    """), {'id': caja_id}).first()

    if not row:
        return None, (jsonify({
            'success': False,
            'error': f'Caja {caja_id} no encontrada o inactiva'
        }), 404)

    caja_pv = int(row[1])
    estado_actual = row[4]

    if requerir_abierta and estado_actual != 'abierta':
        return None, (jsonify({
            'success': False,
            'error': f'Caja {caja_id} no está abierta (estado: {estado_actual})'
        }), 400)

    pv_sesion = _pv_activo()
    if caja_pv != pv_sesion and not _es_admin():
        return None, (jsonify({
            'success': False,
            'error': f'No podés operar la caja del PV {caja_pv}. Tu PV es {pv_sesion}.'
        }), 403)

    return row, None


# ─────────────────────────────────────────────────────────────
# RUTAS
# ─────────────────────────────────────────────────────────────

def init_caja_multipv_routes(db):
    """Crea el Blueprint con todas las rutas multi-PV."""
    bp = Blueprint('caja_multipv', __name__)

    # ════════════════════════════════════════════════════════
    # GET /api/caja-pv/estado
    # ════════════════════════════════════════════════════════
    @bp.route('/api/caja-pv/estado', methods=['GET'])
    def estado_caja_pv():
        try:
            pv_query = request.args.get('pv', type=int)

            if pv_query is not None and pv_query != _pv_activo():
                if not _es_admin():
                    return jsonify({
                        'success': False,
                        'error': 'Sólo admin puede consultar otros PV'
                    }), 403
                pv = pv_query
            else:
                pv = _pv_activo()

            row = db.session.execute(text("""
                SELECT id, fecha_apertura, fecha_cierre,
                       monto_inicial, monto_cierre,
                       efectivo_teorico, efectivo_real, diferencia,
                       observaciones_apertura, observaciones_cierre,
                       usuario_apertura_id, usuario_cierre_id,
                       estado, activa, punto_venta
                FROM cajas
                WHERE punto_venta = :pv AND estado = 'abierta' AND activa = 1
                ORDER BY id DESC LIMIT 1
            """), {'pv': pv}).first()

            if row:
                return jsonify({
                    'success': True, 'caja_abierta': True, 'punto_venta': pv,
                    'caja': {
                        'id': row[0],
                        'fecha_apertura': row[1].isoformat() if row[1] else None,
                        'fecha_cierre': row[2].isoformat() if row[2] else None,
                        'monto_inicial': float(row[3]) if row[3] else 0.0,
                        'monto_cierre': float(row[4]) if row[4] else 0.0,
                        'efectivo_teorico': float(row[5]) if row[5] else 0.0,
                        'efectivo_real': float(row[6]) if row[6] else 0.0,
                        'diferencia': float(row[7]) if row[7] else 0.0,
                        'observaciones_apertura': row[8],
                        'observaciones_cierre': row[9],
                        'usuario_apertura_id': row[10],
                        'usuario_cierre_id': row[11],
                        'estado': row[12], 'activa': bool(row[13]),
                        'punto_venta': row[14],
                    }
                })

            return jsonify({
                'success': True, 'caja_abierta': False,
                'punto_venta': pv, 'caja': None
            })

        except Exception as e:
            print(f"❌ Error en /api/caja-pv/estado: {e}")
            import traceback; traceback.print_exc()
            return jsonify({'success': False, 'error': str(e)}), 500

    # ════════════════════════════════════════════════════════
    # POST /api/caja-pv/abrir
    # ════════════════════════════════════════════════════════
    @bp.route('/api/caja-pv/abrir', methods=['POST'])
    def abrir_caja_pv():
        try:
            data = request.get_json() or {}

            pv_solicitado = data.get('punto_venta')
            if pv_solicitado is not None:
                if not _es_admin():
                    return jsonify({
                        'success': False,
                        'error': 'Sólo admin puede abrir caja de otro PV'
                    }), 403
                try:
                    pv = int(pv_solicitado)
                except (TypeError, ValueError):
                    return jsonify({
                        'success': False, 'error': 'punto_venta debe ser entero'
                    }), 400
            else:
                pv = _pv_activo()

            if pv <= 0:
                return jsonify({
                    'success': False, 'error': f'Punto de venta inválido: {pv}'
                }), 400

            try:
                monto_inicial = float(data.get('monto_inicial', 0))
            except (TypeError, ValueError):
                return jsonify({
                    'success': False, 'error': 'monto_inicial debe ser numérico'
                }), 400

            if monto_inicial < 0:
                return jsonify({
                    'success': False,
                    'error': 'El monto inicial no puede ser negativo'
                }), 400

            existente = db.session.execute(text("""
                SELECT id FROM cajas
                WHERE punto_venta = :pv AND estado = 'abierta' AND activa = 1
                LIMIT 1
            """), {'pv': pv}).first()

            if existente:
                return jsonify({
                    'success': False,
                    'error': f'Ya hay una caja abierta para el PV {pv} '
                             f'(ID {existente[0]}). Cerrarla primero.'
                }), 400

            ahora = _now_ar()
            uid = _user_id_activo()
            obs = (data.get('observaciones') or '').strip()

            result = db.session.execute(text("""
                INSERT INTO cajas (
                    fecha_apertura, monto_inicial, efectivo_teorico,
                    observaciones_apertura, usuario_apertura_id,
                    estado, activa, punto_venta
                ) VALUES (
                    :fa, :mi, :et, :obs, :uid, 'abierta', 1, :pv
                )
            """), {
                'fa': ahora, 'mi': Decimal(str(monto_inicial)),
                'et': Decimal(str(monto_inicial)), 'obs': obs,
                'uid': uid, 'pv': pv,
            })

            db.session.commit()
            nueva_id = result.lastrowid

            print(f"✅ Caja multi-PV abierta — ID {nueva_id}, PV {pv}, "
                  f"Monto ${monto_inicial}, Usuario {uid}")

            return jsonify({
                'success': True,
                'message': f'Caja abierta para PV {pv}',
                'caja': {
                    'id': nueva_id,
                    'fecha_apertura': ahora.isoformat(),
                    'monto_inicial': monto_inicial,
                    'efectivo_teorico': monto_inicial,
                    'observaciones_apertura': obs,
                    'usuario_apertura_id': uid,
                    'estado': 'abierta', 'activa': True,
                    'punto_venta': pv,
                }
            })

        except Exception as e:
            db.session.rollback()
            print(f"❌ Error abriendo caja: {e}")
            import traceback; traceback.print_exc()
            return jsonify({
                'success': False, 'error': f'Error interno: {str(e)}'
            }), 500

    # ════════════════════════════════════════════════════════
    # POST /api/caja-pv/cerrar
    # ════════════════════════════════════════════════════════
    @bp.route('/api/caja-pv/cerrar', methods=['POST'])
    def cerrar_caja_pv():
        try:
            data = request.get_json() or {}
            caja_id = data.get('caja_id')

            try:
                efectivo_real = float(data.get('efectivo_real', 0))
            except (TypeError, ValueError):
                return jsonify({
                    'success': False, 'error': 'efectivo_real debe ser numérico'
                }), 400

            if efectivo_real < 0:
                return jsonify({
                    'success': False,
                    'error': 'efectivo_real no puede ser negativo'
                }), 400

            row, error = _validar_caja_y_permisos(db, caja_id, requerir_abierta=True)
            if error:
                return error

            caja_id = int(row[0])
            caja_pv = int(row[1])
            fecha_apertura = row[2]

            ahora = _now_ar()
            efectivo_teorico = _calcular_efectivo_teorico_pv(
                db, caja_id=caja_id, punto_venta=caja_pv,
                fecha_apertura=fecha_apertura, fecha_cierre=ahora,
            )

            diferencia = efectivo_real - efectivo_teorico
            obs = (data.get('observaciones') or '').strip()
            uid = _user_id_activo()

            db.session.execute(text("""
                UPDATE cajas SET
                    fecha_cierre = :fc, monto_cierre = :mc,
                    efectivo_teorico = :et, efectivo_real = :er,
                    diferencia = :dif, observaciones_cierre = :obs,
                    usuario_cierre_id = :uid, estado = 'cerrada'
                WHERE id = :id
            """), {
                'fc': ahora, 'mc': Decimal(str(efectivo_real)),
                'et': Decimal(str(efectivo_teorico)),
                'er': Decimal(str(efectivo_real)),
                'dif': Decimal(str(diferencia)),
                'obs': obs, 'uid': uid, 'id': caja_id,
            })

            db.session.commit()

            print(f"✅ Caja multi-PV CERRADA — ID {caja_id} PV {caja_pv}")
            print(f"   Teórico: ${efectivo_teorico:.2f} | "
                  f"Real: ${efectivo_real:.2f} | Dif: ${diferencia:+.2f}")

            if abs(diferencia) < 0.01:
                msg = '✅ Caja cerrada exactamente'
            elif diferencia > 0:
                msg = f'⚠ Caja cerrada con sobrante de ${diferencia:.2f}'
            else:
                msg = f'⚠ Caja cerrada con faltante de ${abs(diferencia):.2f}'

            return jsonify({
                'success': True, 'message': msg,
                'caja': {
                    'id': caja_id, 'punto_venta': caja_pv,
                    'fecha_cierre': ahora.isoformat(),
                    'efectivo_teorico': efectivo_teorico,
                    'efectivo_real': efectivo_real,
                    'diferencia': diferencia,
                    'observaciones_cierre': obs,
                    'usuario_cierre_id': uid, 'estado': 'cerrada',
                }
            })

        except Exception as e:
            db.session.rollback()
            print(f"❌ Error cerrando caja: {e}")
            import traceback; traceback.print_exc()
            return jsonify({
                'success': False, 'error': f'Error interno: {str(e)}'
            }), 500

    # ════════════════════════════════════════════════════════
    # POST /api/caja-pv/movimiento
    # ════════════════════════════════════════════════════════
    @bp.route('/api/caja-pv/movimiento', methods=['POST'])
    def registrar_movimiento_pv():
        try:
            data = request.get_json() or {}
            caja_id = data.get('caja_id')
            row, error = _validar_caja_y_permisos(db, caja_id, requerir_abierta=True)
            if error:
                return error

            caja_id = int(row[0])
            caja_pv = int(row[1])

            tipo = (data.get('tipo') or '').strip().lower()
            if tipo not in ('ingreso', 'egreso'):
                return jsonify({
                    'success': False,
                    'error': "tipo debe ser 'ingreso' o 'egreso'"
                }), 400

            descripcion = (data.get('descripcion') or '').strip()
            if not descripcion:
                return jsonify({
                    'success': False, 'error': 'descripcion es requerida'
                }), 400
            if len(descripcion) > 255:
                return jsonify({
                    'success': False,
                    'error': 'descripcion no puede superar 255 caracteres'
                }), 400

            try:
                monto = float(data.get('monto', 0))
            except (TypeError, ValueError):
                return jsonify({
                    'success': False, 'error': 'monto debe ser numérico'
                }), 400

            if monto <= 0:
                return jsonify({
                    'success': False, 'error': 'monto debe ser mayor a 0'
                }), 400

            ahora = _now_ar()
            uid = _user_id_activo()
            notas = (data.get('notas') or '').strip()

            result = db.session.execute(text("""
                INSERT INTO movimientos_caja (
                    caja_id, tipo, descripcion, monto, notas,
                    fecha, usuario_id, punto_venta
                ) VALUES (:cid, :tipo, :desc, :monto, :notas, :fecha, :uid, :pv)
            """), {
                'cid': caja_id, 'tipo': tipo, 'desc': descripcion,
                'monto': Decimal(str(monto)), 'notas': notas,
                'fecha': ahora, 'uid': uid, 'pv': caja_pv,
            })

            db.session.commit()
            mov_id = result.lastrowid

            fecha_apertura = row[2]
            efectivo_actualizado = _calcular_efectivo_teorico_pv(
                db, caja_id=caja_id, punto_venta=caja_pv,
                fecha_apertura=fecha_apertura, fecha_cierre=ahora,
            )

            db.session.execute(text("""
                UPDATE cajas SET efectivo_teorico = :et WHERE id = :id
            """), {'et': Decimal(str(efectivo_actualizado)), 'id': caja_id})
            db.session.commit()

            simbolo = '+' if tipo == 'ingreso' else '-'
            print(f"💰 Movimiento Caja {caja_id} (PV {caja_pv}): "
                  f"{simbolo}${monto:.2f} {tipo} - {descripcion}")
            print(f"   Efectivo teórico actualizado: ${efectivo_actualizado:.2f}")

            return jsonify({
                'success': True,
                'message': f'{tipo.capitalize()} de ${monto:.2f} registrado',
                'movimiento': {
                    'id': mov_id, 'caja_id': caja_id, 'tipo': tipo,
                    'descripcion': descripcion, 'monto': monto,
                    'notas': notas, 'fecha': ahora.isoformat(),
                    'usuario_id': uid, 'punto_venta': caja_pv,
                },
                'efectivo_teorico_actualizado': efectivo_actualizado,
            })

        except Exception as e:
            db.session.rollback()
            print(f"❌ Error registrando movimiento: {e}")
            import traceback; traceback.print_exc()
            return jsonify({
                'success': False, 'error': f'Error interno: {str(e)}'
            }), 500

    # ════════════════════════════════════════════════════════
    # GET /api/caja-pv/<caja_id>/movimientos
    # ════════════════════════════════════════════════════════
    @bp.route('/api/caja-pv/<int:caja_id>/movimientos', methods=['GET'])
    def listar_movimientos_pv(caja_id):
        try:
            row, error = _validar_caja_y_permisos(db, caja_id, requerir_abierta=False)
            if error:
                return error

            caja_pv = int(row[1])

            rows = db.session.execute(text("""
                SELECT id, caja_id, tipo, descripcion, monto, notas,
                       fecha, usuario_id, punto_venta, created_at
                FROM movimientos_caja
                WHERE caja_id = :cid
                ORDER BY fecha DESC, id DESC
            """), {'cid': caja_id}).fetchall()

            movimientos = [{
                'id': r[0], 'caja_id': r[1], 'tipo': r[2],
                'descripcion': r[3], 'monto': float(r[4]) if r[4] else 0.0,
                'notas': r[5],
                'fecha': r[6].isoformat() if r[6] else None,
                'usuario_id': r[7], 'punto_venta': r[8],
                'created_at': r[9].isoformat() if r[9] else None,
            } for r in rows]

            total_ingresos = sum(m['monto'] for m in movimientos if m['tipo'] == 'ingreso')
            total_egresos  = sum(m['monto'] for m in movimientos if m['tipo'] == 'egreso')

            return jsonify({
                'success': True, 'caja_id': caja_id,
                'punto_venta': caja_pv, 'cantidad': len(movimientos),
                'totales': {
                    'ingresos': total_ingresos,
                    'egresos': total_egresos,
                    'balance': total_ingresos - total_egresos,
                },
                'movimientos': movimientos,
            })

        except Exception as e:
            print(f"❌ Error listando movimientos: {e}")
            import traceback; traceback.print_exc()
            return jsonify({'success': False, 'error': str(e)}), 500

    # ════════════════════════════════════════════════════════
    # POST /api/caja-pv/transferir
    # ════════════════════════════════════════════════════════
    @bp.route('/api/caja-pv/transferir', methods=['POST'])
    def transferir_entre_cajas():
        try:
            if not _es_admin():
                return jsonify({
                    'success': False,
                    'error': 'Sólo admin puede transferir entre cajas'
                }), 403

            data = request.get_json() or {}

            try:
                origen_id = int(data.get('caja_origen_id', 0))
                destino_id = int(data.get('caja_destino_id', 0))
            except (TypeError, ValueError):
                return jsonify({
                    'success': False,
                    'error': 'caja_origen_id y caja_destino_id deben ser enteros'
                }), 400

            if not origen_id or not destino_id:
                return jsonify({
                    'success': False,
                    'error': 'caja_origen_id y caja_destino_id son requeridos'
                }), 400

            if origen_id == destino_id:
                return jsonify({
                    'success': False,
                    'error': 'No podés transferir a la misma caja'
                }), 400

            try:
                monto = float(data.get('monto', 0))
            except (TypeError, ValueError):
                return jsonify({
                    'success': False, 'error': 'monto debe ser numérico'
                }), 400

            if monto <= 0:
                return jsonify({
                    'success': False, 'error': 'monto debe ser mayor a 0'
                }), 400

            origen_row = db.session.execute(text("""
                SELECT id, punto_venta, fecha_apertura, estado
                FROM cajas WHERE id = :id AND activa = 1
            """), {'id': origen_id}).first()

            if not origen_row:
                return jsonify({
                    'success': False,
                    'error': f'Caja origen {origen_id} no encontrada'
                }), 404

            destino_row = db.session.execute(text("""
                SELECT id, punto_venta, estado
                FROM cajas WHERE id = :id AND activa = 1
            """), {'id': destino_id}).first()

            if not destino_row:
                return jsonify({
                    'success': False,
                    'error': f'Caja destino {destino_id} no encontrada'
                }), 404

            if origen_row[3] != 'abierta':
                return jsonify({
                    'success': False,
                    'error': f'Caja origen {origen_id} está {origen_row[3]}'
                }), 400

            if destino_row[2] != 'abierta':
                return jsonify({
                    'success': False,
                    'error': f'Caja destino {destino_id} está {destino_row[2]}'
                }), 400

            origen_pv = int(origen_row[1])
            destino_pv = int(destino_row[1])
            origen_fecha_apertura = origen_row[2]

            saldo_origen = _calcular_efectivo_teorico_pv(
                db, caja_id=origen_id, punto_venta=origen_pv,
                fecha_apertura=origen_fecha_apertura,
            )

            warning = None
            saldo_post = saldo_origen - monto
            if saldo_post < 0:
                warning = (
                    f'⚠ Atención: la caja origen quedará con saldo negativo '
                    f'de ${abs(saldo_post):.2f} (saldo actual: ${saldo_origen:.2f}, '
                    f'transferís: ${monto:.2f})'
                )

            ahora = _now_ar()
            uid = _user_id_activo()
            motivo = (data.get('motivo') or '').strip()
            descripcion = f'Transferencia a caja PV {destino_pv} (ID {destino_id})'
            descripcion_destino = f'Recibido de caja PV {origen_pv} (ID {origen_id})'

            try:
                mov_egreso = db.session.execute(text("""
                    INSERT INTO movimientos_caja (
                        caja_id, tipo, descripcion, monto, notas,
                        fecha, usuario_id, punto_venta
                    ) VALUES (:cid, 'egreso', :desc, :monto, :notas,
                              :fecha, :uid, :pv)
                """), {
                    'cid': origen_id, 'desc': descripcion,
                    'monto': Decimal(str(monto)),
                    'notas': f'TRANSFERENCIA - {motivo}' if motivo else 'TRANSFERENCIA',
                    'fecha': ahora, 'uid': uid, 'pv': origen_pv,
                })

                mov_ingreso = db.session.execute(text("""
                    INSERT INTO movimientos_caja (
                        caja_id, tipo, descripcion, monto, notas,
                        fecha, usuario_id, punto_venta
                    ) VALUES (:cid, 'ingreso', :desc, :monto, :notas,
                              :fecha, :uid, :pv)
                """), {
                    'cid': destino_id, 'desc': descripcion_destino,
                    'monto': Decimal(str(monto)),
                    'notas': f'TRANSFERENCIA - {motivo}' if motivo else 'TRANSFERENCIA',
                    'fecha': ahora, 'uid': uid, 'pv': destino_pv,
                })

                transf = db.session.execute(text("""
                    INSERT INTO transferencia_caja (
                        fecha, caja_origen_id, caja_destino_id,
                        punto_venta_origen, punto_venta_destino,
                        monto, motivo, usuario_id, anulada
                    ) VALUES (:fecha, :oid, :did, :opv, :dpv,
                              :monto, :motivo, :uid, 0)
                """), {
                    'fecha': ahora,
                    'oid': origen_id, 'did': destino_id,
                    'opv': origen_pv, 'dpv': destino_pv,
                    'monto': Decimal(str(monto)),
                    'motivo': motivo or None,
                    'uid': uid,
                })

                db.session.commit()
                transf_id = transf.lastrowid

                fecha_apertura_destino = db.session.execute(text("""
                    SELECT fecha_apertura FROM cajas WHERE id = :id
                """), {'id': destino_id}).first()[0]

                origen_nuevo = _calcular_efectivo_teorico_pv(
                    db, caja_id=origen_id, punto_venta=origen_pv,
                    fecha_apertura=origen_fecha_apertura,
                )
                destino_nuevo = _calcular_efectivo_teorico_pv(
                    db, caja_id=destino_id, punto_venta=destino_pv,
                    fecha_apertura=fecha_apertura_destino,
                )

                db.session.execute(text("""
                    UPDATE cajas SET efectivo_teorico = :et WHERE id = :id
                """), {'et': Decimal(str(origen_nuevo)), 'id': origen_id})
                db.session.execute(text("""
                    UPDATE cajas SET efectivo_teorico = :et WHERE id = :id
                """), {'et': Decimal(str(destino_nuevo)), 'id': destino_id})
                db.session.commit()

            except Exception as e:
                db.session.rollback()
                raise

            print(f"💸 TRANSFERENCIA — ID {transf_id}: "
                  f"PV{origen_pv} → PV{destino_pv} | ${monto:.2f}")
            print(f"   Caja origen {origen_id}: saldo ${origen_nuevo:.2f}")
            print(f"   Caja destino {destino_id}: saldo ${destino_nuevo:.2f}")
            if motivo:
                print(f"   Motivo: {motivo}")
            if warning:
                print(f"   {warning}")

            response = {
                'success': True,
                'message': f'Transferencia de ${monto:.2f} realizada',
                'transferencia': {
                    'id': transf_id,
                    'fecha': ahora.isoformat(),
                    'caja_origen_id': origen_id,
                    'caja_destino_id': destino_id,
                    'punto_venta_origen': origen_pv,
                    'punto_venta_destino': destino_pv,
                    'monto': monto, 'motivo': motivo,
                    'usuario_id': uid, 'anulada': False,
                    'movimientos': {
                        'egreso_id': mov_egreso.lastrowid,
                        'ingreso_id': mov_ingreso.lastrowid,
                    },
                },
                'saldos_actualizados': {
                    'origen': {
                        'caja_id': origen_id, 'punto_venta': origen_pv,
                        'efectivo_teorico': origen_nuevo,
                    },
                    'destino': {
                        'caja_id': destino_id, 'punto_venta': destino_pv,
                        'efectivo_teorico': destino_nuevo,
                    },
                },
            }

            if warning:
                response['warning'] = warning

            return jsonify(response)

        except Exception as e:
            db.session.rollback()
            print(f"❌ Error transfiriendo entre cajas: {e}")
            import traceback; traceback.print_exc()
            return jsonify({
                'success': False, 'error': f'Error interno: {str(e)}'
            }), 500

    # ════════════════════════════════════════════════════════
    # POST /api/caja-pv/transferencia/<id>/anular
    # ════════════════════════════════════════════════════════
    @bp.route('/api/caja-pv/transferencia/<int:transf_id>/anular',
              methods=['POST'])
    def anular_transferencia(transf_id):
        try:
            if not _es_admin():
                return jsonify({
                    'success': False,
                    'error': 'Sólo admin puede anular transferencias'
                }), 403

            data = request.get_json() or {}
            motivo_anulacion = (data.get('motivo_anulacion') or '').strip()
            if not motivo_anulacion:
                return jsonify({
                    'success': False,
                    'error': 'motivo_anulacion es requerido'
                }), 400

            row = db.session.execute(text("""
                SELECT id, fecha, caja_origen_id, caja_destino_id,
                       punto_venta_origen, punto_venta_destino,
                       monto, motivo, anulada
                FROM transferencia_caja WHERE id = :id
            """), {'id': transf_id}).first()

            if not row:
                return jsonify({
                    'success': False,
                    'error': f'Transferencia {transf_id} no encontrada'
                }), 404

            if row[8]:
                return jsonify({
                    'success': False,
                    'error': f'Transferencia {transf_id} ya está anulada'
                }), 400

            origen_id = int(row[2])
            destino_id = int(row[3])
            origen_pv = int(row[4])
            destino_pv = int(row[5])
            monto = float(row[6])

            origen_caja = db.session.execute(text("""
                SELECT estado, fecha_apertura FROM cajas WHERE id = :id
            """), {'id': origen_id}).first()

            destino_caja = db.session.execute(text("""
                SELECT estado, fecha_apertura FROM cajas WHERE id = :id
            """), {'id': destino_id}).first()

            if origen_caja[0] != 'abierta':
                return jsonify({
                    'success': False,
                    'error': f'No se puede anular: caja origen {origen_id} '
                             f'está {origen_caja[0]}'
                }), 400

            if destino_caja[0] != 'abierta':
                return jsonify({
                    'success': False,
                    'error': f'No se puede anular: caja destino {destino_id} '
                             f'está {destino_caja[0]}'
                }), 400

            ahora = _now_ar()
            uid = _user_id_activo()
            descripcion_origen = f'ANULACIÓN transf {transf_id} - devolución'
            descripcion_destino = f'ANULACIÓN transf {transf_id} - devolución'

            try:
                db.session.execute(text("""
                    INSERT INTO movimientos_caja (
                        caja_id, tipo, descripcion, monto, notas,
                        fecha, usuario_id, punto_venta
                    ) VALUES (:cid, 'ingreso', :desc, :monto, :notas,
                              :fecha, :uid, :pv)
                """), {
                    'cid': origen_id, 'desc': descripcion_origen,
                    'monto': Decimal(str(monto)),
                    'notas': f'ANULACIÓN: {motivo_anulacion}',
                    'fecha': ahora, 'uid': uid, 'pv': origen_pv,
                })

                db.session.execute(text("""
                    INSERT INTO movimientos_caja (
                        caja_id, tipo, descripcion, monto, notas,
                        fecha, usuario_id, punto_venta
                    ) VALUES (:cid, 'egreso', :desc, :monto, :notas,
                              :fecha, :uid, :pv)
                """), {
                    'cid': destino_id, 'desc': descripcion_destino,
                    'monto': Decimal(str(monto)),
                    'notas': f'ANULACIÓN: {motivo_anulacion}',
                    'fecha': ahora, 'uid': uid, 'pv': destino_pv,
                })

                db.session.execute(text("""
                    UPDATE transferencia_caja SET
                        anulada = 1, fecha_anulacion = :fa,
                        motivo_anulacion = :motivo, usuario_anulacion_id = :uid
                    WHERE id = :id
                """), {
                    'fa': ahora, 'motivo': motivo_anulacion,
                    'uid': uid, 'id': transf_id,
                })

                db.session.commit()

                origen_nuevo = _calcular_efectivo_teorico_pv(
                    db, caja_id=origen_id, punto_venta=origen_pv,
                    fecha_apertura=origen_caja[1],
                )
                destino_nuevo = _calcular_efectivo_teorico_pv(
                    db, caja_id=destino_id, punto_venta=destino_pv,
                    fecha_apertura=destino_caja[1],
                )

                db.session.execute(text("""
                    UPDATE cajas SET efectivo_teorico = :et WHERE id = :id
                """), {'et': Decimal(str(origen_nuevo)), 'id': origen_id})
                db.session.execute(text("""
                    UPDATE cajas SET efectivo_teorico = :et WHERE id = :id
                """), {'et': Decimal(str(destino_nuevo)), 'id': destino_id})
                db.session.commit()

            except Exception as e:
                db.session.rollback()
                raise

            print(f"🔄 TRANSFERENCIA ANULADA — ID {transf_id}")
            print(f"   Devuelto: PV{destino_pv} → PV{origen_pv} | ${monto:.2f}")
            print(f"   Motivo: {motivo_anulacion}")

            return jsonify({
                'success': True,
                'message': f'Transferencia {transf_id} anulada y plata devuelta',
                'transferencia_id': transf_id,
                'monto_devuelto': monto,
                'motivo_anulacion': motivo_anulacion,
                'saldos_actualizados': {
                    'origen': {
                        'caja_id': origen_id, 'punto_venta': origen_pv,
                        'efectivo_teorico': origen_nuevo,
                    },
                    'destino': {
                        'caja_id': destino_id, 'punto_venta': destino_pv,
                        'efectivo_teorico': destino_nuevo,
                    },
                },
            })

        except Exception as e:
            db.session.rollback()
            print(f"❌ Error anulando transferencia: {e}")
            import traceback; traceback.print_exc()
            return jsonify({
                'success': False, 'error': f'Error interno: {str(e)}'
            }), 500

    # ════════════════════════════════════════════════════════
    # GET /api/caja-pv/transferencias
    # ════════════════════════════════════════════════════════
    @bp.route('/api/caja-pv/transferencias', methods=['GET'])
    def listar_transferencias():
        try:
            caja_id_filter = request.args.get('caja_id', type=int)
            pv_filter = request.args.get('pv', type=int)
            solo_activas = request.args.get('solo_activas', '0') == '1'
            limite = request.args.get('limite', 100, type=int)
            limite = max(1, min(limite, 500))

            where_parts = []
            params = {'limite': limite}

            if not _es_admin():
                pv_sesion = _pv_activo()
                where_parts.append(
                    "(punto_venta_origen = :pv_sesion OR punto_venta_destino = :pv_sesion)"
                )
                params['pv_sesion'] = pv_sesion

            if caja_id_filter:
                where_parts.append(
                    "(caja_origen_id = :cid OR caja_destino_id = :cid)"
                )
                params['cid'] = caja_id_filter

            if pv_filter:
                where_parts.append(
                    "(punto_venta_origen = :pv OR punto_venta_destino = :pv)"
                )
                params['pv'] = pv_filter

            if solo_activas:
                where_parts.append("anulada = 0")

            where_clause = ('WHERE ' + ' AND '.join(where_parts)) if where_parts else ''

            sql = f"""
                SELECT id, fecha, caja_origen_id, caja_destino_id,
                       punto_venta_origen, punto_venta_destino,
                       monto, motivo, usuario_id,
                       anulada, fecha_anulacion, motivo_anulacion,
                       usuario_anulacion_id, created_at
                FROM transferencia_caja
                {where_clause}
                ORDER BY fecha DESC, id DESC
                LIMIT :limite
            """

            rows = db.session.execute(text(sql), params).fetchall()

            transfs = [{
                'id': r[0],
                'fecha': r[1].isoformat() if r[1] else None,
                'caja_origen_id': r[2], 'caja_destino_id': r[3],
                'punto_venta_origen': r[4], 'punto_venta_destino': r[5],
                'monto': float(r[6]) if r[6] else 0.0,
                'motivo': r[7], 'usuario_id': r[8],
                'anulada': bool(r[9]),
                'fecha_anulacion': r[10].isoformat() if r[10] else None,
                'motivo_anulacion': r[11], 'usuario_anulacion_id': r[12],
                'created_at': r[13].isoformat() if r[13] else None,
            } for r in rows]

            total_activas = sum(t['monto'] for t in transfs if not t['anulada'])
            total_anuladas = sum(t['monto'] for t in transfs if t['anulada'])

            return jsonify({
                'success': True, 'cantidad': len(transfs),
                'totales': {
                    'monto_activas': total_activas,
                    'monto_anuladas': total_anuladas,
                    'cantidad_activas': sum(1 for t in transfs if not t['anulada']),
                    'cantidad_anuladas': sum(1 for t in transfs if t['anulada']),
                },
                'transferencias': transfs,
                'filtros_aplicados': {
                    'caja_id': caja_id_filter, 'pv': pv_filter,
                    'solo_activas': solo_activas, 'limite': limite,
                },
            })

        except Exception as e:
            print(f"❌ Error listando transferencias: {e}")
            import traceback; traceback.print_exc()
            return jsonify({'success': False, 'error': str(e)}), 500

    # ════════════════════════════════════════════════════════
    # GET /api/caja-pv/listar-abiertas
    # ════════════════════════════════════════════════════════
    @bp.route('/api/caja-pv/listar-abiertas', methods=['GET'])
    def listar_cajas_abiertas():
        try:
            if _es_admin():
                rows = db.session.execute(text("""
                    SELECT id, fecha_apertura, monto_inicial, efectivo_teorico,
                           usuario_apertura_id, punto_venta
                    FROM cajas
                    WHERE estado = 'abierta' AND activa = 1
                    ORDER BY punto_venta, id DESC
                """)).fetchall()
            else:
                pv = _pv_activo()
                rows = db.session.execute(text("""
                    SELECT id, fecha_apertura, monto_inicial, efectivo_teorico,
                           usuario_apertura_id, punto_venta
                    FROM cajas
                    WHERE estado = 'abierta' AND activa = 1
                      AND punto_venta = :pv
                    ORDER BY id DESC
                """), {'pv': pv}).fetchall()

            cajas = [{
                'id': r[0],
                'fecha_apertura': r[1].isoformat() if r[1] else None,
                'monto_inicial': float(r[2]) if r[2] else 0.0,
                'efectivo_teorico': float(r[3]) if r[3] else 0.0,
                'usuario_apertura_id': r[4], 'punto_venta': r[5],
            } for r in rows]

            return jsonify({
                'success': True, 'cantidad': len(cajas), 'cajas': cajas,
                'pv_sesion': _pv_activo(), 'es_admin': _es_admin(),
            })

        except Exception as e:
            print(f"❌ Error listando cajas abiertas: {e}")
            import traceback; traceback.print_exc()
            return jsonify({'success': False, 'error': str(e)}), 500

    # ════════════════════════════════════════════════════════
    # GET /api/caja-pv/resumen-consolidado    [NUEVO en v5]
    # ════════════════════════════════════════════════════════
    @bp.route('/api/caja-pv/resumen-consolidado', methods=['GET'])
    def resumen_consolidado():
        """
        Resumen consolidado de cajas con totales agrupados + detalle por caja.
        
        Query params (todos opcionales):
            ?fecha=YYYY-MM-DD          → cajas abiertas ese día
            ?fecha_desde=YYYY-MM-DD    → desde esta fecha
            ?fecha_hasta=YYYY-MM-DD    → hasta esta fecha (inclusive)
            ?pv=N                      → solo este PV
            ?solo_abiertas=1           → solo abiertas (default)
            ?incluir_cerradas=1        → incluir las cerradas también
        
        Sin filtros de fecha → cajas abiertas en este momento (vista operativa).
        Con fecha → busca cajas cuya fecha_apertura caiga en el rango (día operativo).
        
        Permisos:
            - Admin: ve todas las cajas
            - Vendedor: solo su PV
        """
        try:
            # ── Parsear filtros ───────────────────────────────
            fecha_str = request.args.get('fecha')
            fecha_desde_str = request.args.get('fecha_desde')
            fecha_hasta_str = request.args.get('fecha_hasta')
            pv_filter = request.args.get('pv', type=int)
            solo_abiertas = request.args.get('solo_abiertas', '0') == '1'
            incluir_cerradas = request.args.get('incluir_cerradas', '0') == '1'

            fecha_dia = _parse_fecha(fecha_str)
            fecha_desde = _parse_fecha(fecha_desde_str)
            fecha_hasta = _parse_fecha(fecha_hasta_str)

            # ── Construir WHERE ──────────────────────────────
            where_parts = ["activa = 1"]
            params = {}

            # Por defecto: si no hay filtros de fecha, mostrar abiertas
            usar_filtro_fecha = bool(fecha_dia or fecha_desde or fecha_hasta)

            if not usar_filtro_fecha and not incluir_cerradas:
                # Sin filtros + sin incluir_cerradas → solo abiertas
                where_parts.append("estado = 'abierta'")
            elif solo_abiertas:
                where_parts.append("estado = 'abierta'")

            # Filtro por fecha (día operativo: cajas abiertas en ese día)
            if fecha_dia:
                where_parts.append("DATE(fecha_apertura) = :fecha_dia")
                params['fecha_dia'] = fecha_dia
            else:
                if fecha_desde:
                    where_parts.append("DATE(fecha_apertura) >= :fecha_desde")
                    params['fecha_desde'] = fecha_desde
                if fecha_hasta:
                    where_parts.append("DATE(fecha_apertura) <= :fecha_hasta")
                    params['fecha_hasta'] = fecha_hasta

            # Filtro por PV
            if pv_filter:
                where_parts.append("punto_venta = :pv")
                params['pv'] = pv_filter

            # Filtro por permisos: vendedor solo su PV
            if not _es_admin():
                pv_sesion = _pv_activo()
                where_parts.append("punto_venta = :pv_sesion")
                params['pv_sesion'] = pv_sesion

            where_clause = "WHERE " + " AND ".join(where_parts)

            sql = f"""
                SELECT id, fecha_apertura, fecha_cierre, monto_inicial,
                       efectivo_teorico, efectivo_real, diferencia,
                       estado, punto_venta,
                       usuario_apertura_id, usuario_cierre_id
                FROM cajas
                {where_clause}
                ORDER BY punto_venta, fecha_apertura DESC
            """

            rows = db.session.execute(text(sql), params).fetchall()

            # ── Construir detalle por caja ────────────────────
            cajas_detalle = [_detalle_caja_resumen(db, r) for r in rows]

            # ── Calcular totales consolidados ─────────────────
            totales = {
                'cantidad_cajas': len(cajas_detalle),
                'cantidad_abiertas': sum(1 for c in cajas_detalle if c['estado'] == 'abierta'),
                'cantidad_cerradas': sum(1 for c in cajas_detalle if c['estado'] == 'cerrada'),
                'monto_inicial_total': sum(c['monto_inicial'] for c in cajas_detalle),
                'ventas_efectivo_total': sum(c['ventas_efectivo'] for c in cajas_detalle),
                'ventas_total': sum(c.get('ventas_total', c['ventas_efectivo']) for c in cajas_detalle),
                'cantidad_facturas_total': sum(c['cantidad_facturas'] for c in cajas_detalle),
                'gastos_efectivo_total': sum(c['gastos_efectivo'] for c in cajas_detalle),
                'cantidad_gastos_total': sum(c['cantidad_gastos'] for c in cajas_detalle),
                'movimientos_manuales': {
                    'ingresos': sum(c['ingresos_manuales'] for c in cajas_detalle),
                    'egresos': sum(c['egresos_manuales'] for c in cajas_detalle),
                    'balance': sum(c['ingresos_manuales'] - c['egresos_manuales']
                                   for c in cajas_detalle),
                    'cantidad': sum(c['cantidad_movimientos'] for c in cajas_detalle),
                },
                'transferencias': {
                    'salieron': sum(c['transferencias_enviadas'] for c in cajas_detalle),
                    'entraron': sum(c['transferencias_recibidas'] for c in cajas_detalle),
                    'cantidad_enviadas': sum(c['cantidad_enviadas'] for c in cajas_detalle),
                    'cantidad_recibidas': sum(c['cantidad_recibidas'] for c in cajas_detalle),
                },
                'efectivo_teorico_total': sum(c['efectivo_teorico'] for c in cajas_detalle),
            }

            # Diferencia total: solo de las cajas cerradas
            diferencias_cerradas = [c['diferencia'] for c in cajas_detalle
                                    if c['estado'] == 'cerrada' and c['diferencia'] is not None]
            if diferencias_cerradas:
                totales['diferencia_total'] = sum(diferencias_cerradas)
                totales['efectivo_real_total'] = sum(
                    c['efectivo_real'] for c in cajas_detalle
                    if c['estado'] == 'cerrada' and c['efectivo_real'] is not None
                )
            else:
                totales['diferencia_total'] = None
                totales['efectivo_real_total'] = None

            # ── Agrupar por PV (mini-resumen) ─────────────────
            por_pv = {}
            for c in cajas_detalle:
                pv = c['punto_venta']
                if pv not in por_pv:
                    por_pv[pv] = {
                        'punto_venta': pv,
                        'cantidad_cajas': 0,
                        'monto_inicial': 0.0,
                        'ventas_efectivo': 0.0,
                        'gastos_efectivo': 0.0,
                        'efectivo_teorico': 0.0,
                    }
                por_pv[pv]['cantidad_cajas'] += 1
                por_pv[pv]['monto_inicial'] += c['monto_inicial']
                por_pv[pv]['ventas_efectivo'] += c['ventas_efectivo']
                por_pv[pv]['gastos_efectivo'] += c['gastos_efectivo']
                por_pv[pv]['efectivo_teorico'] += c['efectivo_teorico']

            return jsonify({
                'success': True,
                'filtros': {
                    'fecha': fecha_str, 'fecha_desde': fecha_desde_str,
                    'fecha_hasta': fecha_hasta_str,
                    'pv': pv_filter, 'solo_abiertas': solo_abiertas,
                    'incluir_cerradas': incluir_cerradas,
                },
                'totales_consolidados': totales,
                'por_punto_venta': sorted(por_pv.values(), key=lambda x: x['punto_venta']),
                'cajas': cajas_detalle,
                'es_admin': _es_admin(),
                'pv_sesion': _pv_activo(),
            })

        except Exception as e:
            print(f"❌ Error en resumen consolidado: {e}")
            import traceback; traceback.print_exc()
            return jsonify({'success': False, 'error': str(e)}), 500

    # ════════════════════════════════════════════════════════
    # GET /api/caja-pv/<caja_id>/desglose      [NUEVO en v6]
    # ════════════════════════════════════════════════════════
    @bp.route('/api/caja-pv/<int:caja_id>/desglose', methods=['GET'])
    def desglose_caja(caja_id):
        """
        Devuelve el desglose COMPLETO del cálculo de efectivo teórico de una caja.
        
        Incluye línea por línea:
            - Apertura (monto inicial)
            - Cada factura en efectivo (con número, cliente, fecha, monto)
            - Cada gasto en efectivo (con descripción, fecha, monto)
            - Cada movimiento manual (ingreso/egreso, descripción, fecha, monto)
            - Cada transferencia recibida y enviada
            - Cierre (si está cerrada)
        
        Útil para auditar y entender de dónde sale cada peso.
        """
        try:
            row, error = _validar_caja_y_permisos(db, caja_id, requerir_abierta=False)
            if error:
                return error

            caja_id = int(row[0])
            caja_pv = int(row[1])
            fecha_apertura = row[2]
            monto_inicial = float(row[3] or 0)

            # Datos completos de la caja
            caja_full = db.session.execute(text("""
                SELECT id, fecha_apertura, fecha_cierre, monto_inicial,
                       monto_cierre, efectivo_teorico, efectivo_real, diferencia,
                       observaciones_apertura, observaciones_cierre,
                       usuario_apertura_id, usuario_cierre_id,
                       estado, punto_venta
                FROM cajas WHERE id = :id
            """), {'id': caja_id}).first()

            estado = caja_full[12]
            fecha_cierre = caja_full[2]
            fecha_fin_calc = fecha_cierre if fecha_cierre else _now_ar()

            # ── 1. Ventas en efectivo (cada factura) ─────────
            ventas = db.session.execute(text("""
                SELECT f.id, f.numero, f.tipo_comprobante, f.fecha,
                       COALESCE(c.nombre, 'Consumidor Final') AS cliente_nombre,
                       mp.importe
                FROM medios_pago mp
                INNER JOIN factura f ON mp.factura_id = f.id
                LEFT JOIN cliente c ON f.cliente_id = c.id
                WHERE mp.medio_pago = 'efectivo'
                  AND f.estado != 'anulada'
                  AND f.punto_venta = :pv
                  AND f.fecha BETWEEN :fi AND :ff
                ORDER BY f.fecha, f.id
            """), {
                'pv': caja_pv, 'fi': fecha_apertura, 'ff': fecha_fin_calc
            }).fetchall()

            # Mapeo de tipo_comprobante AFIP a etiqueta legible
            tipo_labels = {
                '01': 'Factura A', '02': 'Nota Débito A', '03': 'Nota Crédito A',
                '06': 'Factura B', '07': 'Nota Débito B', '08': 'Nota Crédito B',
                '11': 'Factura C', '12': 'Nota Débito C', '13': 'Nota Crédito C',
                '51': 'Factura M', '81': 'Tique Factura A', '82': 'Tique Factura B',
            }

            ventas_lista = [{
                'id': v[0],
                'numero': v[1],
                'tipo': tipo_labels.get(v[2], v[2] or '—'),
                'tipo_codigo': v[2],
                'fecha': v[3].isoformat() if v[3] else None,
                'cliente_nombre': v[4] or 'Consumidor Final',
                'importe': float(v[5]) if v[5] else 0.0,
            } for v in ventas]
            total_ventas = sum(v['importe'] for v in ventas_lista)

            # ── 2. Gastos en efectivo (cada gasto) ──────────
            # Usamos fecha_creacion (DATETIME con hora real) en vez de fecha (DATE solo)
            # para que el desglose muestre cuándo se cargó cada gasto.
            gastos = db.session.execute(text("""
                SELECT id, descripcion, fecha_creacion, monto, notas, categoria
                FROM gastos
                WHERE metodo_pago = 'efectivo' AND activo = 1 AND caja_id = :cid
                ORDER BY fecha_creacion, id
            """), {'cid': caja_id}).fetchall()

            gastos_lista = [{
                'id': g[0],
                'descripcion': g[1],
                'fecha': g[2].isoformat() if g[2] else None,
                'monto': float(g[3]) if g[3] else 0.0,
                'notas': g[4],
                'categoria': g[5],
            } for g in gastos]
            total_gastos = sum(g['monto'] for g in gastos_lista)

            # ── 3. Movimientos manuales (ingreso/egreso) ───
            # Separamos los de transferencia (notas TRANSFERENCIA o ANULACIÓN)
            movs = db.session.execute(text("""
                SELECT id, tipo, descripcion, monto, notas, fecha, usuario_id
                FROM movimientos_caja
                WHERE caja_id = :cid
                  AND (notas IS NULL 
                       OR (notas NOT LIKE 'TRANSFERENCIA%' 
                           AND notas NOT LIKE 'ANULACI%'))
                ORDER BY fecha, id
            """), {'cid': caja_id}).fetchall()

            ingresos_manuales = []
            egresos_manuales = []
            for m in movs:
                item = {
                    'id': m[0],
                    'tipo': m[1],
                    'descripcion': m[2],
                    'monto': float(m[3]) if m[3] else 0.0,
                    'notas': m[4],
                    'fecha': m[5].isoformat() if m[5] else None,
                    'usuario_id': m[6],
                }
                if m[1] == 'ingreso':
                    ingresos_manuales.append(item)
                else:
                    egresos_manuales.append(item)

            total_ingresos_man = sum(i['monto'] for i in ingresos_manuales)
            total_egresos_man = sum(e['monto'] for e in egresos_manuales)

            # ── 4. Transferencias activas (recibidas y enviadas) ──
            recibidas = db.session.execute(text("""
                SELECT id, fecha, caja_origen_id, punto_venta_origen,
                       monto, motivo
                FROM transferencia_caja
                WHERE caja_destino_id = :cid AND anulada = 0
                ORDER BY fecha, id
            """), {'cid': caja_id}).fetchall()

            recibidas_lista = [{
                'id': r[0],
                'fecha': r[1].isoformat() if r[1] else None,
                'caja_origen_id': r[2],
                'punto_venta_origen': r[3],
                'monto': float(r[4]) if r[4] else 0.0,
                'motivo': r[5],
            } for r in recibidas]
            total_recibidas = sum(r['monto'] for r in recibidas_lista)

            enviadas = db.session.execute(text("""
                SELECT id, fecha, caja_destino_id, punto_venta_destino,
                       monto, motivo
                FROM transferencia_caja
                WHERE caja_origen_id = :cid AND anulada = 0
                ORDER BY fecha, id
            """), {'cid': caja_id}).fetchall()

            enviadas_lista = [{
                'id': e[0],
                'fecha': e[1].isoformat() if e[1] else None,
                'caja_destino_id': e[2],
                'punto_venta_destino': e[3],
                'monto': float(e[4]) if e[4] else 0.0,
                'motivo': e[5],
            } for e in enviadas]
            total_enviadas = sum(e['monto'] for e in enviadas_lista)

            # ── 5. Anulaciones (movimientos de tipo ANULACIÓN) ──
            anulaciones = db.session.execute(text("""
                SELECT id, tipo, descripcion, monto, notas, fecha
                FROM movimientos_caja
                WHERE caja_id = :cid AND notas LIKE 'ANULACI%'
                ORDER BY fecha, id
            """), {'cid': caja_id}).fetchall()

            anulaciones_lista = [{
                'id': a[0],
                'tipo': a[1],
                'descripcion': a[2],
                'monto': float(a[3]) if a[3] else 0.0,
                'notas': a[4],
                'fecha': a[5].isoformat() if a[5] else None,
            } for a in anulaciones]
            total_anul_ingresos = sum(a['monto'] for a in anulaciones_lista if a['tipo'] == 'ingreso')
            total_anul_egresos = sum(a['monto'] for a in anulaciones_lista if a['tipo'] == 'egreso')

            # ── 6. CÁLCULO FINAL ────────────────────────────
            # Las anulaciones NO se cuentan en el total: son informativas y
            # ya cancelan una transferencia original que también está oculta.
            # Si una transferencia está anulada → no aparece como activa Y la
            # anulación tampoco suma. Resultado: ambas se "ignoran" del cálculo.
            efectivo_teorico = (
                monto_inicial
                + total_ventas
                + total_ingresos_man
                + total_recibidas
                - total_gastos
                - total_egresos_man
                - total_enviadas
            )

            return jsonify({
                'success': True,
                'caja': {
                    'id': caja_id,
                    'punto_venta': caja_pv,
                    'estado': estado,
                    'fecha_apertura': fecha_apertura.isoformat() if fecha_apertura else None,
                    'fecha_cierre': fecha_cierre.isoformat() if fecha_cierre else None,
                    'monto_inicial': monto_inicial,
                    'efectivo_teorico': efectivo_teorico,
                    'efectivo_real': float(caja_full[6]) if caja_full[6] is not None and estado == 'cerrada' else None,
                    'diferencia': float(caja_full[7]) if caja_full[7] is not None and estado == 'cerrada' else None,
                    'observaciones_apertura': caja_full[8],
                    'observaciones_cierre': caja_full[9],
                    'usuario_apertura_id': caja_full[10],
                    'usuario_cierre_id': caja_full[11],
                },
                'apertura': {
                    'monto_inicial': monto_inicial,
                    'fecha': fecha_apertura.isoformat() if fecha_apertura else None,
                    'observaciones': caja_full[8],
                },
                'ventas': {
                    'lista': ventas_lista,
                    'cantidad': len(ventas_lista),
                    'total': total_ventas,
                },
                'gastos': {
                    'lista': gastos_lista,
                    'cantidad': len(gastos_lista),
                    'total': total_gastos,
                },
                'movimientos': {
                    'ingresos': ingresos_manuales,
                    'egresos': egresos_manuales,
                    'cantidad_ingresos': len(ingresos_manuales),
                    'cantidad_egresos': len(egresos_manuales),
                    'total_ingresos': total_ingresos_man,
                    'total_egresos': total_egresos_man,
                },
                'transferencias': {
                    'recibidas': recibidas_lista,
                    'enviadas': enviadas_lista,
                    'cantidad_recibidas': len(recibidas_lista),
                    'cantidad_enviadas': len(enviadas_lista),
                    'total_recibidas': total_recibidas,
                    'total_enviadas': total_enviadas,
                },
                'anulaciones': {
                    'lista': anulaciones_lista,
                    'cantidad': len(anulaciones_lista),
                    'total_ingresos': total_anul_ingresos,
                    'total_egresos': total_anul_egresos,
                },
                'totales': {
                    'monto_inicial': monto_inicial,
                    'sumas': total_ventas + total_ingresos_man + total_recibidas,
                    'restas': total_gastos + total_egresos_man + total_enviadas,
                    'efectivo_teorico': efectivo_teorico,
                },
            })

        except Exception as e:
            print(f"❌ Error en desglose: {e}")
            import traceback; traceback.print_exc()
            return jsonify({'success': False, 'error': str(e)}), 500

    return bp


# ─────────────────────────────────────────────────────────────
# ENTRYPOINT
# ─────────────────────────────────────────────────────────────

def init_caja_multipv_system(db):
    bp = init_caja_multipv_routes(db)
    print("✅ Sistema de caja MULTI-PV inicializado (v6)")
    print("   Rutas disponibles:")
    print("   ── Caja ────────────────────────────────────────")
    print("   - GET  /api/caja-pv/estado              (estado del PV de sesión)")
    print("   - POST /api/caja-pv/abrir               (abrir caja del PV)")
    print("   - POST /api/caja-pv/cerrar              (cerrar con cálculo PV)")
    print("   - GET  /api/caja-pv/listar-abiertas     (admin: todas / vendedor: la suya)")
    print("   ── Movimientos ─────────────────────────────────")
    print("   - POST /api/caja-pv/movimiento          (ingreso/egreso manual)")
    print("   - GET  /api/caja-pv/<id>/movimientos    (listar)")
    print("   ── Transferencias ──────────────────────────────")
    print("   - POST /api/caja-pv/transferir          (admin only)")
    print("   - POST /api/caja-pv/transferencia/<id>/anular (admin only)")
    print("   - GET  /api/caja-pv/transferencias      (filtros: caja_id, pv, etc.)")
    print("   ── Resumen consolidado ─────────────────────────")
    print("   - GET  /api/caja-pv/resumen-consolidado (totales + por PV + por caja)")
    print("   ── Desglose [v6] ───────────────────────────────")
    print("   - GET  /api/caja-pv/<id>/desglose       (detalle línea por línea)")
    return bp