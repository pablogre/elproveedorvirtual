"""
═══════════════════════════════════════════════════════════════════════════════
WEBAPP MÓVIL — Para dueños del comercio (consulta y monitoreo desde el celu)
═══════════════════════════════════════════════════════════════════════════════

Módulo independiente — no contamina app.py. Solo expone:
  - Blueprint con todas las rutas bajo /mob/
  - Función init_mobile(app, db, **modelos) para registrarlo

Uso desde app.py:
    from mobile import init_mobile
    init_mobile(app, db,
                Usuario=Usuario, Factura=Factura, DetalleFactura=DetalleFactura,
                Cliente=Cliente, Producto=Producto,
                MedioPago=MedioPago, Proveedor=Proveedor,  # opcionales
                CajaApertura=_CajaApertura)                # opcional

PWA installable. Funciona en HTTP por ahora (HTTPS recomendado para v2).
═══════════════════════════════════════════════════════════════════════════════
"""

from flask import Blueprint, render_template, request, jsonify, redirect, session, url_for, flash
from datetime import datetime, timedelta, date
from decimal import Decimal
from sqlalchemy import func, and_

mobile_bp = Blueprint('mobile', __name__, url_prefix='/mob')

# ════════════════════════════════════════════════════════════════════════════
# Modelos inyectados
# ════════════════════════════════════════════════════════════════════════════
_db = None
_models = {}


# ════════════════════════════════════════════════════════════════════════════
# DECORADOR: requiere login
# ════════════════════════════════════════════════════════════════════════════
def _require_login(f):
    from functools import wraps
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            if request.is_json or request.path.startswith('/mob/api/'):
                return jsonify({'success': False, 'error': 'No autorizado'}), 401
            return redirect(url_for('mobile.login'))
        return f(*args, **kwargs)
    return wrapper


# ════════════════════════════════════════════════════════════════════════════
# RUTAS DE AUTENTICACIÓN
# ════════════════════════════════════════════════════════════════════════════
@mobile_bp.route('/')
def home():
    """Redirige a dashboard si está logueado, sino al login."""
    if 'user_id' in session:
        return redirect(url_for('mobile.dashboard'))
    return redirect(url_for('mobile.login'))


@mobile_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login móvil. Reusa la misma auth que el sistema web."""
    if 'user_id' in session:
        return redirect(url_for('mobile.dashboard'))

    if request.method == 'POST':
        Usuario = _models['Usuario']
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if not username or not password:
            flash('Ingresá usuario y contraseña', 'error')
            return redirect(url_for('mobile.login'))

        usuario = Usuario.query.filter_by(username=username, activo=True).first()

        # Misma lógica que el login del sistema web
        if usuario and usuario.password_hash == password:
            session['user_id'] = usuario.id
            session['username'] = usuario.username
            session['nombre'] = usuario.nombre
            session['rol'] = usuario.rol
            try:
                session['punto_venta'] = int(usuario.punto_venta) if usuario.punto_venta else 1
            except Exception:
                session['punto_venta'] = 1
            return redirect(url_for('mobile.dashboard'))
        else:
            flash('Usuario o contraseña incorrectos', 'error')
            return redirect(url_for('mobile.login'))

    return render_template('mob/login.html')


@mobile_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('mobile.login'))


# ════════════════════════════════════════════════════════════════════════════
# DASHBOARD (pantalla principal)
# ════════════════════════════════════════════════════════════════════════════
@mobile_bp.route('/dashboard')
@_require_login
def dashboard():
    """Pantalla principal — la página HTML.
    Los datos los carga el frontend vía /api/dashboard cada 30 segundos."""
    return render_template('mob/dashboard.html',
                           nombre=session.get('nombre', ''),
                           rol=session.get('rol', ''))


# ════════════════════════════════════════════════════════════════════════════
# API: datos del dashboard (JSON, refrescable)
# ════════════════════════════════════════════════════════════════════════════
@mobile_bp.route('/api/dashboard')
@_require_login
def api_dashboard():
    """Devuelve todos los datos del dashboard en un solo JSON.
    Acepta query params:
      ?desde=YYYY-MM-DD  (default: hoy)
      ?hasta=YYYY-MM-DD  (default: hoy)
    Si desde == hasta == hoy, muestra alertas. Si es otro rango, las oculta.
    """
    Factura = _models['Factura']
    DetalleFactura = _models['DetalleFactura']
    Producto = _models['Producto']
    Cliente = _models['Cliente']

    hoy = date.today()

    # Parsear fechas del request
    def _parse_fecha(s, default):
        if not s:
            return default
        try:
            return datetime.strptime(s, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            return default

    desde = _parse_fecha(request.args.get('desde'), hoy)
    hasta = _parse_fecha(request.args.get('hasta'), hoy)

    # Validar: desde no puede ser posterior a hasta
    if desde > hasta:
        desde, hasta = hasta, desde

    # Determinar si es "hoy" (rango = solo hoy) para mostrar alertas
    es_hoy = (desde == hoy and hasta == hoy)

    # Período anterior comparativo (mismo largo, justo antes)
    dias_rango = (hasta - desde).days + 1
    desde_anterior = desde - timedelta(days=dias_rango)
    hasta_anterior = desde - timedelta(days=1)

    # ─── Ventas del período ───
    ventas_periodo = _ventas_del_rango(Factura, desde, hasta)
    ventas_anterior = _ventas_del_rango(Factura, desde_anterior, hasta_anterior)

    # Variación porcentual vs período anterior
    variacion = None
    if ventas_anterior['total'] > 0:
        variacion = ((ventas_periodo['total'] - ventas_anterior['total']) / ventas_anterior['total']) * 100

    # ─── Producto top del período ───
    producto_top = _producto_top_rango(Factura, DetalleFactura, Producto, desde, hasta)

    # ─── Cliente top del período ───
    cliente_top = _cliente_top_rango(Factura, Cliente, desde, hasta)

    # ─── Estado de caja (efectivo del período) ───
    efectivo_periodo = _efectivo_del_rango(Factura, desde, hasta)

    # ─── NUEVO: Ticket promedio ───
    ticket_promedio = None
    if ventas_periodo['cantidad'] > 0:
        ticket_promedio = ventas_periodo['total'] / ventas_periodo['cantidad']

    # ─── NUEVO: Desglose por medio de pago ───
    medios_pago = _medios_pago_rango(Factura, desde, hasta)

    # ─── NUEVO: Top 5 productos del período ───
    top_productos = _top_productos_rango(Factura, DetalleFactura, Producto, desde, hasta, limite=5)

    # ─── NUEVO: Top 5 clientes del período ───
    top_clientes = _top_clientes_rango(Factura, Cliente, desde, hasta, limite=5)

    # ─── NUEVO: Margen del período ───
    margen = _margen_del_rango(Factura, DetalleFactura, Producto, desde, hasta)

    # ─── NUEVO 2B: Ventas por hora (solo si rango = 1 día) ───
    ventas_por_hora = None
    if desde == hasta:
        ventas_por_hora = _ventas_por_hora(Factura, desde)

    # ─── NUEVO 2B: Comparativa semana pasada (mismo rango -7 días) ───
    desde_sem_pasada = desde - timedelta(days=7)
    hasta_sem_pasada = hasta - timedelta(days=7)
    ventas_sem_pasada = _ventas_del_rango(Factura, desde_sem_pasada, hasta_sem_pasada)
    variacion_sem = None
    if ventas_sem_pasada['total'] > 0:
        variacion_sem = ((ventas_periodo['total'] - ventas_sem_pasada['total']) / ventas_sem_pasada['total']) * 100

    if desde_sem_pasada == hasta_sem_pasada:
        label_sem_pasada = desde_sem_pasada.strftime('%d/%m/%Y')
    else:
        label_sem_pasada = f"{desde_sem_pasada.strftime('%d/%m')} al {hasta_sem_pasada.strftime('%d/%m/%Y')}"

    # ─── NUEVO 2B: Estado AFIP ───
    estado_afip = _estado_afip(Factura)

    # ─── NUEVO 2B: Récord — ventas de hoy vs mejor día del mes pasado ───
    record_info = None
    if es_hoy:
        record_info = _check_record_dia(Factura, hoy, ventas_periodo['total'])

    # ─── NUEVO 2B: Resumen del mes en curso (para barra de objetivo) ───
    mes_actual = _ventas_mes_actual(Factura, hoy)

    # ─── ALERTAS (solo si el rango es "hoy") ───
    alertas = []
    if es_hoy:
        # Errores AFIP de hoy
        facturas_error = Factura.query.filter(
            func.date(Factura.fecha) == hoy,
            Factura.estado == 'error_afip'
        ).count()
        if facturas_error > 0:
            alertas.append({
                'tipo': 'error_afip',
                'icono': 'fa-times-circle',
                'titulo': f'{facturas_error} factura(s) con error AFIP',
                'detalle': 'Sin CAE asignado. Revisar conexión con ARCA.',
                'severidad': 'alta'
            })

        # Stock crítico
        try:
            stock_critico_count = Producto.query.filter(
                Producto.stock_minimo > 0,
                Producto.stock < Producto.stock_minimo
            ).count()
            if stock_critico_count > 0:
                alertas.append({
                    'tipo': 'stock_critico',
                    'icono': 'fa-box-open',
                    'titulo': f'{stock_critico_count} producto(s) con stock crítico',
                    'detalle': 'Por debajo del mínimo configurado.',
                    'severidad': 'media'
                })
        except Exception:
            pass

        # Pedidos online sin atender
        PedidoOnline = _models.get('PedidoOnline')
        if PedidoOnline is not None:
            try:
                pedidos_pendientes = PedidoOnline.query.filter_by(estado='pendiente').count()
                if pedidos_pendientes > 0:
                    alertas.append({
                        'tipo': 'pedidos_online',
                        'icono': 'fa-shopping-cart',
                        'titulo': f'{pedidos_pendientes} pedido(s) online pendiente(s)',
                        'detalle': 'Esperando ser atendidos.',
                        'severidad': 'alta'
                    })
            except Exception:
                pass

        # Clientes con deuda
        try:
            clientes_deudores = Cliente.query.filter(Cliente.saldo > 0).count()
            if clientes_deudores > 0:
                total_deuda = _db.session.query(func.coalesce(func.sum(Cliente.saldo), 0)).filter(Cliente.saldo > 0).scalar() or 0
                alertas.append({
                    'tipo': 'deuda_clientes',
                    'icono': 'fa-user-clock',
                    'titulo': f'{clientes_deudores} cliente(s) con deuda',
                    'detalle': f'Total: ${float(total_deuda):,.2f}',
                    'severidad': 'baja'
                })
        except Exception:
            pass

    # ─── LABELS para mostrar ───
    if desde == hasta:
        label_periodo = desde.strftime('%d/%m/%Y')
    else:
        label_periodo = f"{desde.strftime('%d/%m')} al {hasta.strftime('%d/%m/%Y')}"

    if desde_anterior == hasta_anterior:
        label_anterior = desde_anterior.strftime('%d/%m/%Y')
    else:
        label_anterior = f"{desde_anterior.strftime('%d/%m')} al {hasta_anterior.strftime('%d/%m/%Y')}"

    return jsonify({
        'success': True,
        'timestamp': datetime.now().strftime('%H:%M:%S'),
        'desde': desde.strftime('%Y-%m-%d'),
        'hasta': hasta.strftime('%Y-%m-%d'),
        'es_hoy': es_hoy,
        'label_periodo': label_periodo,
        'label_anterior': label_anterior,
        'dias_rango': dias_rango,
        'ventas_periodo': ventas_periodo,
        'ventas_anterior': ventas_anterior,
        'variacion_pct': round(variacion, 1) if variacion is not None else None,
        'ticket_promedio': ticket_promedio,
        'producto_top': producto_top,
        'cliente_top': cliente_top,
        'top_productos': top_productos,
        'top_clientes': top_clientes,
        'medios_pago': medios_pago,
        'margen': margen,
        'efectivo_periodo': efectivo_periodo,
        'alertas': alertas,
        # ── Sesión 2B ──
        'ventas_por_hora': ventas_por_hora,
        'ventas_sem_pasada': ventas_sem_pasada,
        'variacion_sem_pct': round(variacion_sem, 1) if variacion_sem is not None else None,
        'label_sem_pasada': label_sem_pasada,
        'estado_afip': estado_afip,
        'record_info': record_info,
        'mes_actual': mes_actual,
    })


# ════════════════════════════════════════════════════════════════════════════
# HELPERS DE CONSULTA
# ════════════════════════════════════════════════════════════════════════════
def _ventas_del_rango(Factura, desde, hasta):
    """Devuelve dict con ventas de un rango de fechas (inclusivo en ambos extremos)."""
    try:
        query = Factura.query.filter(
            func.date(Factura.fecha) >= desde,
            func.date(Factura.fecha) <= hasta
        )
        try:
            query = query.filter(Factura.estado != 'anulada')
        except Exception:
            pass

        cantidad = query.count()
        total = _db.session.query(
            func.coalesce(func.sum(Factura.total), 0)
        ).filter(
            func.date(Factura.fecha) >= desde,
            func.date(Factura.fecha) <= hasta
        )
        try:
            total = total.filter(Factura.estado != 'anulada')
        except Exception:
            pass
        total_value = float(total.scalar() or 0)

        return {'cantidad': cantidad, 'total': total_value}
    except Exception as e:
        return {'cantidad': 0, 'total': 0.0, 'error': str(e)}


def _producto_top_rango(Factura, DetalleFactura, Producto, desde, hasta):
    """Producto más vendido en el rango (por cantidad)."""
    try:
        result = _db.session.query(
            DetalleFactura.producto_id,
            func.sum(DetalleFactura.cantidad).label('total_qty'),
            func.sum(DetalleFactura.subtotal).label('total_monto')
        ).join(Factura, Factura.id == DetalleFactura.factura_id
        ).filter(
            func.date(Factura.fecha) >= desde,
            func.date(Factura.fecha) <= hasta,
            Factura.estado != 'anulada'
        ).group_by(DetalleFactura.producto_id
        ).order_by(func.sum(DetalleFactura.cantidad).desc()
        ).first()

        if not result or not result.producto_id:
            return None

        producto = Producto.query.get(result.producto_id)
        if not producto:
            return None

        return {
            'codigo': producto.codigo,
            'nombre': producto.nombre,
            'cantidad': float(result.total_qty or 0),
            'monto': float(result.total_monto or 0)
        }
    except Exception:
        return None


def _cliente_top_rango(Factura, Cliente, desde, hasta):
    """Cliente que más facturó en el rango (por monto)."""
    try:
        result = _db.session.query(
            Factura.cliente_id,
            func.count(Factura.id).label('cant_facturas'),
            func.sum(Factura.total).label('total_monto')
        ).filter(
            func.date(Factura.fecha) >= desde,
            func.date(Factura.fecha) <= hasta,
            Factura.cliente_id.isnot(None),
            Factura.estado != 'anulada'
        ).group_by(Factura.cliente_id
        ).order_by(func.sum(Factura.total).desc()
        ).first()

        if not result or not result.cliente_id:
            return None

        cliente = Cliente.query.get(result.cliente_id)
        if not cliente:
            return None

        return {
            'nombre': cliente.nombre,
            'cant_facturas': result.cant_facturas,
            'monto': float(result.total_monto or 0)
        }
    except Exception:
        return None


def _efectivo_del_rango(Factura, desde, hasta):
    """Calcula el efectivo cobrado en el rango."""
    MedioPago = _models.get('MedioPago')
    if MedioPago is None:
        return None

    try:
        result = _db.session.query(
            func.coalesce(func.sum(MedioPago.importe), 0)
        ).join(Factura, Factura.id == MedioPago.factura_id
        ).filter(
            func.date(Factura.fecha) >= desde,
            func.date(Factura.fecha) <= hasta,
            MedioPago.medio_pago.ilike('%efectivo%'),
            Factura.estado != 'anulada'
        ).scalar()

        return float(result or 0)
    except Exception:
        return None


def _medios_pago_rango(Factura, desde, hasta):
    """Devuelve desglose de cobros por medio de pago en el rango.
    Ej: [{'medio': 'efectivo', 'monto': 50000, 'operaciones': 23, 'pct': 35.5}, ...]"""
    MedioPago = _models.get('MedioPago')
    if MedioPago is None:
        return []

    try:
        rows = _db.session.query(
            MedioPago.medio_pago,
            func.sum(MedioPago.importe).label('monto'),
            func.count(MedioPago.id).label('operaciones')
        ).join(Factura, Factura.id == MedioPago.factura_id
        ).filter(
            func.date(Factura.fecha) >= desde,
            func.date(Factura.fecha) <= hasta,
            Factura.estado != 'anulada'
        ).group_by(MedioPago.medio_pago
        ).order_by(func.sum(MedioPago.importe).desc()
        ).all()

        if not rows:
            return []

        total = sum(float(r.monto or 0) for r in rows)
        result = []
        for r in rows:
            monto = float(r.monto or 0)
            result.append({
                'medio': r.medio_pago,
                'monto': monto,
                'operaciones': r.operaciones,
                'pct': round((monto / total * 100), 1) if total > 0 else 0
            })
        return result
    except Exception:
        return []


def _top_productos_rango(Factura, DetalleFactura, Producto, desde, hasta, limite=5):
    """Top N productos más vendidos del período por cantidad."""
    try:
        rows = _db.session.query(
            DetalleFactura.producto_id,
            func.sum(DetalleFactura.cantidad).label('total_qty'),
            func.sum(DetalleFactura.subtotal).label('total_monto')
        ).join(Factura, Factura.id == DetalleFactura.factura_id
        ).filter(
            func.date(Factura.fecha) >= desde,
            func.date(Factura.fecha) <= hasta,
            Factura.estado != 'anulada'
        ).group_by(DetalleFactura.producto_id
        ).order_by(func.sum(DetalleFactura.cantidad).desc()
        ).limit(limite).all()

        result = []
        for r in rows:
            if not r.producto_id:
                continue
            producto = Producto.query.get(r.producto_id)
            if not producto:
                continue
            result.append({
                'codigo': producto.codigo,
                'nombre': producto.nombre,
                'cantidad': float(r.total_qty or 0),
                'monto': float(r.total_monto or 0)
            })
        return result
    except Exception:
        return []


def _top_clientes_rango(Factura, Cliente, desde, hasta, limite=5):
    """Top N clientes que más facturaron en el rango por monto."""
    try:
        rows = _db.session.query(
            Factura.cliente_id,
            func.count(Factura.id).label('cant_facturas'),
            func.sum(Factura.total).label('total_monto')
        ).filter(
            func.date(Factura.fecha) >= desde,
            func.date(Factura.fecha) <= hasta,
            Factura.cliente_id.isnot(None),
            Factura.estado != 'anulada'
        ).group_by(Factura.cliente_id
        ).order_by(func.sum(Factura.total).desc()
        ).limit(limite).all()

        result = []
        for r in rows:
            cliente = Cliente.query.get(r.cliente_id)
            if not cliente:
                continue
            result.append({
                'nombre': cliente.nombre,
                'cant_facturas': r.cant_facturas,
                'monto': float(r.total_monto or 0)
            })
        return result
    except Exception:
        return []


def _margen_del_rango(Factura, DetalleFactura, Producto, desde, hasta):
    """Calcula margen bruto del período: (ventas - costo de mercadería vendida).
    Devuelve dict con: ventas, costo, margen_monto, margen_pct, cobertura_pct.
    O None si no hay datos de costo.

    NOTA SCHIRO (abr/2026):
    Producto.costo está guardado CON IVA incluido (Diego carga el total
    de la factura del proveedor). DetalleFactura.subtotal viene SIN IVA.
    Para que la comparación sea válida, dividimos el costo por
    (1 + producto.iva/100) usando la alícuota REAL de cada producto.

    Lógica alineada con el reporte /api/margen_productos (estadisticas.py):
      - Costo: COALESCE(detalle.costo_unitario si > 0, producto.costo / (1 + iva/100)).
      - Filtra facturas canceladas, combos y productos sin costo cargado.
      - Una sola query agregada (sin N+1).

    SI MIGRÁS ESTE ARCHIVO A FACTUFÁCIL O CARNAVE: revisar estos supuestos,
    porque en esos sistemas el costo está guardado SIN IVA.
    """
    try:
        # COALESCE(NULLIF(detalle.costo_unitario, 0), producto.costo / (1 + iva/100))
        costo_expr = func.coalesce(
            func.nullif(DetalleFactura.costo_unitario, 0),
            Producto.costo / (1 + Producto.iva / 100)
        )

        row = _db.session.query(
            func.sum(DetalleFactura.subtotal).label('venta'),
            func.sum(DetalleFactura.cantidad * costo_expr).label('costo'),
            func.count(func.distinct(Producto.id)).label('productos_con_costo'),
        ).join(
            Factura, Factura.id == DetalleFactura.factura_id
        ).join(
            Producto, Producto.id == DetalleFactura.producto_id
        ).filter(
            func.date(Factura.fecha) >= desde,
            func.date(Factura.fecha) <= hasta,
            Factura.estado != 'anulada',
            Producto.costo != None,
            Producto.costo > 0,
            Producto.es_combo == False,
        ).one()

        total_venta = float(row.venta or 0)
        total_costo = float(row.costo or 0)
        productos_con_costo = int(row.productos_con_costo or 0)

        if total_venta <= 0 or productos_con_costo == 0:
            return None

        margen_monto = total_venta - total_costo
        margen_pct = (margen_monto / total_venta * 100) if total_venta > 0 else 0

        return {
            'ventas': total_venta,
            'costo': total_costo,
            'margen_monto': margen_monto,
            'margen_pct': round(margen_pct, 1),
            'cobertura_pct': 100  # productos sin costo ya excluidos en el filtro
        }
    except Exception:
        return None


# ════════════════════════════════════════════════════════════════════════════
# HELPERS SESIÓN 2B
# ════════════════════════════════════════════════════════════════════════════
def _ventas_por_hora(Factura, fecha):
    """Ventas agrupadas por hora del día.
    Devuelve lista de 24 elementos con monto e count por hora (00 a 23)."""
    try:
        rows = _db.session.query(
            func.extract('hour', Factura.fecha).label('hora'),
            func.count(Factura.id).label('cant'),
            func.sum(Factura.total).label('monto')
        ).filter(
            func.date(Factura.fecha) == fecha
        )
        try:
            rows = rows.filter(Factura.estado != 'anulada')
        except Exception:
            pass
        rows = rows.group_by(func.extract('hour', Factura.fecha)).all()

        # Inicializo todas las horas en 0
        horas = {h: {'monto': 0.0, 'cant': 0} for h in range(24)}
        for r in rows:
            if r.hora is not None:
                h = int(r.hora)
                if 0 <= h <= 23:
                    horas[h] = {
                        'monto': float(r.monto or 0),
                        'cant': r.cant or 0
                    }

        # Convertir a lista ordenada
        resultado = []
        for h in range(24):
            resultado.append({
                'hora': h,
                'label': f'{h:02d}',
                'monto': horas[h]['monto'],
                'cant': horas[h]['cant']
            })
        return resultado
    except Exception:
        return None


def _estado_afip(Factura):
    """Estado de la integración con AFIP/ARCA.
    Devuelve dict con: status (ok/warn/error), label, ultima_factura, errores_24h."""
    try:
        hace_24h = datetime.now() - timedelta(hours=24)

        # Total facturas en 24h
        total_24h = Factura.query.filter(Factura.fecha >= hace_24h).count()

        # Errores en 24h
        errores_24h = 0
        try:
            errores_24h = Factura.query.filter(
                Factura.fecha >= hace_24h,
                Factura.estado == 'error_afip'
            ).count()
        except Exception:
            pass

        # Última factura autorizada
        ultima_autorizada = None
        try:
            ult = Factura.query.filter(
                Factura.estado == 'autorizada'
            ).order_by(Factura.fecha.desc()).first()
            if ult:
                ultima_autorizada = ult.fecha.strftime('%d/%m %H:%M')
        except Exception:
            pass

        # Determinar estado
        if total_24h == 0:
            status = 'idle'
            label = 'Sin actividad reciente'
        elif errores_24h == 0:
            status = 'ok'
            label = 'Conectado y operando'
        elif errores_24h < total_24h * 0.1:  # menos del 10% de errores
            status = 'warn'
            label = f'{errores_24h} error(es) en 24h'
        else:
            status = 'error'
            label = f'{errores_24h} de {total_24h} facturas con error'

        return {
            'status': status,
            'label': label,
            'ultima_autorizada': ultima_autorizada,
            'errores_24h': errores_24h,
            'total_24h': total_24h
        }
    except Exception:
        return None


def _check_record_dia(Factura, hoy, ventas_hoy_total):
    """Verifica si las ventas de hoy superaron el mejor día del mes pasado.
    Devuelve dict si rompió récord, None si no."""
    try:
        # Mes pasado: primer y último día
        primer_dia_mes = hoy.replace(day=1)
        ultimo_dia_mes_pasado = primer_dia_mes - timedelta(days=1)
        primer_dia_mes_pasado = ultimo_dia_mes_pasado.replace(day=1)

        # Mejor día del mes pasado
        mejor_dia = _db.session.query(
            func.date(Factura.fecha).label('dia'),
            func.sum(Factura.total).label('total')
        ).filter(
            func.date(Factura.fecha) >= primer_dia_mes_pasado,
            func.date(Factura.fecha) <= ultimo_dia_mes_pasado
        )
        try:
            mejor_dia = mejor_dia.filter(Factura.estado != 'anulada')
        except Exception:
            pass
        mejor_dia = mejor_dia.group_by(func.date(Factura.fecha)
        ).order_by(func.sum(Factura.total).desc()).first()

        if not mejor_dia or not mejor_dia.total:
            return None

        mejor_dia_total = float(mejor_dia.total)
        if ventas_hoy_total > mejor_dia_total:
            return {
                'es_record': True,
                'mejor_anterior': mejor_dia_total,
                'fecha_anterior': mejor_dia.dia.strftime('%d/%m/%Y') if hasattr(mejor_dia.dia, 'strftime') else str(mejor_dia.dia),
                'diferencia': ventas_hoy_total - mejor_dia_total,
                'diferencia_pct': round(((ventas_hoy_total - mejor_dia_total) / mejor_dia_total) * 100, 1)
            }
        return None
    except Exception:
        return None


def _ventas_mes_actual(Factura, hoy):
    """Devuelve ventas del mes en curso (1° del mes hasta hoy).
    Útil para calcular el progreso vs objetivo mensual."""
    try:
        primer_dia = hoy.replace(day=1)
        return _ventas_del_rango(Factura, primer_dia, hoy)
    except Exception:
        return {'cantidad': 0, 'total': 0.0}


# ════════════════════════════════════════════════════════════════════════════
# PWA: manifest.json (servimos via blueprint para que la URL coincida)
# ════════════════════════════════════════════════════════════════════════════
@mobile_bp.route('/manifest.json')
def manifest():
    """Manifest PWA dinámico."""
    return jsonify({
        "name": "FactuFácil Móvil",
        "short_name": "FactuFácil",
        "description": "Control en la palma de tu mano",
        "start_url": "/mob/",
        "display": "standalone",
        "orientation": "portrait",
        "background_color": "#0d6efd",
        "theme_color": "#0d6efd",
        "scope": "/mob/",
        "icons": [
            {
                "src": "/static/mob/icon-192.png",
                "sizes": "192x192",
                "type": "image/png",
                "purpose": "any maskable"
            },
            {
                "src": "/static/mob/icon-512.png",
                "sizes": "512x512",
                "type": "image/png",
                "purpose": "any maskable"
            }
        ]
    })


# ════════════════════════════════════════════════════════════════════════════
# INIT
# ════════════════════════════════════════════════════════════════════════════
def init_mobile(app, db, **modelos):
    """Registra el blueprint y guarda los modelos.
    Modelos esperados: Usuario, Factura, DetalleFactura, Cliente, Producto.
    Opcionales: MedioPago, Proveedor, PedidoOnline, CajaApertura."""
    global _db, _models
    _db = db
    _models = modelos
    app.register_blueprint(mobile_bp)
