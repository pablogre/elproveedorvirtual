# presupuestos.py — Módulo Presupuestos para FactuFácil
# Patrón: Blueprint propio con modelos adentro, similar a compras.py / pedidos.py

from flask import Blueprint, render_template, request, jsonify, redirect, session
from sqlalchemy import Numeric, func, desc
from datetime import datetime, timedelta, date
from decimal import Decimal
from extensions import db

presupuestos_bp = Blueprint('presupuestos', __name__, url_prefix='/presupuestos')

# Modelos externos — los inyecta init_presupuestos() para evitar
# circular imports (app.py corre como __main__, no como módulo 'app')
Cliente = None
Usuario = None


# ============================================================================
# MODELOS
# ============================================================================

class Presupuesto(db.Model):
    __tablename__ = 'presupuesto'

    id = db.Column(db.Integer, primary_key=True)

    # Numeración (display: PRES-00001-00000001)
    punto_venta = db.Column(db.Integer, nullable=False, default=1)
    numero_secuencial = db.Column(db.Integer, nullable=False)
    numero_completo = db.Column(db.String(30), nullable=False)

    # Fechas y validez
    fecha_emision = db.Column(db.Date, nullable=False, default=date.today)
    fecha_validez = db.Column(db.Date, nullable=False)
    validez_dias = db.Column(db.Integer, nullable=False, default=15)

    # Cliente
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)

    # Totales
    subtotal = db.Column(Numeric(12, 2), nullable=False, default=0)
    iva = db.Column(Numeric(12, 2), nullable=False, default=0)
    total = db.Column(Numeric(12, 2), nullable=False, default=0)

    # Estado: borrador | enviado | aceptado | rechazado | convertido | vencido
    estado = db.Column(db.String(20), nullable=False, default='borrador')

    # Conversión a factura (NULL hasta que se convierta)
    factura_id = db.Column(db.Integer, db.ForeignKey('factura.id'), nullable=True)
    fecha_conversion = db.Column(db.DateTime, nullable=True)

    # Otros
    observaciones = db.Column(db.Text, nullable=True)
    usuario_creacion = db.Column(db.String(100), nullable=True)

    # Auditoría
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    # Relaciones
    cliente = db.relationship('Cliente', backref='presupuestos')
    factura = db.relationship('Factura', backref='presupuesto_origen', uselist=False)
    detalles = db.relationship(
        'PresupuestoDetalle',
        backref='presupuesto',
        cascade='all, delete-orphan',
        order_by='PresupuestoDetalle.orden'
    )

    @property
    def esta_vencido(self):
        """True si ya pasó la fecha de validez (independiente del estado guardado)."""
        return self.fecha_validez < date.today()


class PresupuestoDetalle(db.Model):
    __tablename__ = 'presupuesto_detalle'

    id = db.Column(db.Integer, primary_key=True)
    presupuesto_id = db.Column(db.Integer, db.ForeignKey('presupuesto.id'), nullable=False)

    # Producto (snapshot: código y descripción se copian para preservar historial)
    producto_id = db.Column(db.Integer, db.ForeignKey('producto.id'), nullable=True)
    codigo_producto = db.Column(db.String(50), nullable=True)
    descripcion = db.Column(db.String(255), nullable=False)

    # Cantidades y precios (se respetan los del momento de cotización)
    cantidad = db.Column(Numeric(10, 3), nullable=False, default=1)
    precio_unitario = db.Column(Numeric(12, 2), nullable=False, default=0)
    iva_alicuota = db.Column(Numeric(5, 2), nullable=False, default=21)
    subtotal = db.Column(Numeric(12, 2), nullable=False, default=0)

    # Flags
    es_pesable = db.Column(db.Boolean, nullable=False, default=False)
    orden = db.Column(db.Integer, nullable=False, default=0)

    producto = db.relationship('Producto', backref='en_presupuestos')


# ============================================================================
# HELPERS
# ============================================================================

def siguiente_numero(punto_venta=1):
    """Próximo numero_secuencial para un punto de venta."""
    ultimo = db.session.query(func.max(Presupuesto.numero_secuencial))\
        .filter(Presupuesto.punto_venta == punto_venta).scalar()
    return (ultimo or 0) + 1


def formatear_numero(punto_venta, numero_secuencial):
    """Formato display: PRES-00001-00000001"""
    return f"PRES-{punto_venta:05d}-{numero_secuencial:08d}"


def marcar_vencidos():
    """Actualiza a 'vencido' los presupuestos con fecha_validez pasada.
    Solo afecta estados 'borrador' y 'enviado' (no toca aceptado/rechazado/convertido)."""
    hoy = date.today()
    n = Presupuesto.query.filter(
        Presupuesto.estado.in_(['borrador', 'enviado']),
        Presupuesto.fecha_validez < hoy
    ).update({'estado': 'vencido'}, synchronize_session=False)
    if n:
        db.session.commit()
    return n


# ============================================================================
# RUTAS
# ============================================================================

@presupuestos_bp.route('/')
def listado():
    if 'user_id' not in session:
        return redirect('/login')

    # Actualizar vencidos al entrar
    marcar_vencidos()

    # Filtros
    estado = request.args.get('estado', '')
    cliente_id = request.args.get('cliente_id', type=int)
    desde = request.args.get('desde', '')
    hasta = request.args.get('hasta', '')

    q = Presupuesto.query
    if estado:
        q = q.filter(Presupuesto.estado == estado)
    if cliente_id:
        q = q.filter(Presupuesto.cliente_id == cliente_id)
    if desde:
        try:
            q = q.filter(Presupuesto.fecha_emision >= datetime.strptime(desde, '%Y-%m-%d').date())
        except ValueError:
            pass
    if hasta:
        try:
            q = q.filter(Presupuesto.fecha_emision <= datetime.strptime(hasta, '%Y-%m-%d').date())
        except ValueError:
            pass

    presupuestos = q.order_by(
        desc(Presupuesto.fecha_emision),
        desc(Presupuesto.numero_secuencial)
    ).limit(500).all()

    clientes = Cliente.query.order_by(Cliente.nombre).all()

    return render_template(
        'presupuestos_listado.html',
        presupuestos=presupuestos,
        clientes=clientes,
        filtros={'estado': estado, 'cliente_id': cliente_id, 'desde': desde, 'hasta': hasta}
    )


@presupuestos_bp.route('/nuevo', methods=['GET'])
def nuevo():
    if 'user_id' not in session:
        return redirect('/login')

    clientes = Cliente.query.order_by(Cliente.nombre).all()
    return render_template('presupuestos_nuevo.html', clientes=clientes)


@presupuestos_bp.route('/crear', methods=['POST'])
def crear():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'No autorizado'}), 401

    try:
        data = request.get_json()
        cliente_id = int(data.get('cliente_id'))
        validez_dias = int(data.get('validez_dias', 15))
        observaciones = (data.get('observaciones') or '').strip()
        items = data.get('items', [])

        if not items:
            return jsonify({'success': False, 'error': 'Agregá al menos un ítem'}), 400

        cliente = Cliente.query.get(cliente_id)
        if not cliente:
            return jsonify({'success': False, 'error': 'Cliente no encontrado'}), 404

        usuario = Usuario.query.get(session['user_id'])
        punto_venta = usuario.punto_venta if usuario else 1

        # Crear presupuesto
        seq = siguiente_numero(punto_venta)
        hoy = date.today()

        presu = Presupuesto(
            punto_venta=punto_venta,
            numero_secuencial=seq,
            numero_completo=formatear_numero(punto_venta, seq),
            fecha_emision=hoy,
            fecha_validez=hoy + timedelta(days=validez_dias),
            validez_dias=validez_dias,
            cliente_id=cliente_id,
            observaciones=observaciones,
            usuario_creacion=usuario.nombre if usuario else None,
            estado='borrador'
        )
        db.session.add(presu)
        db.session.flush()

        # Detalle
        # IMPORTANTE: asumo que el precio_unitario que llega del frontend es NETO (sin IVA).
        # Si querés que sea con IVA incluido, avisame y cambio esta parte.
        subtotal_total = Decimal('0')
        iva_total = Decimal('0')

        for idx, it in enumerate(items):
            cantidad = Decimal(str(it.get('cantidad', 1)))
            precio = Decimal(str(it.get('precio_unitario', 0)))
            alicuota = Decimal(str(it.get('iva_alicuota', 21)))
            producto_id = it.get('producto_id')

            sub_item = (precio * cantidad).quantize(Decimal('0.01'))
            iva_item = (sub_item * alicuota / Decimal('100')).quantize(Decimal('0.01'))

            det = PresupuestoDetalle(
                presupuesto_id=presu.id,
                producto_id=producto_id if producto_id else None,
                codigo_producto=(it.get('codigo') or '')[:50] or None,
                descripcion=(it.get('descripcion') or 'Sin descripción')[:255],
                cantidad=cantidad,
                precio_unitario=precio,
                iva_alicuota=alicuota,
                subtotal=sub_item,
                es_pesable=bool(it.get('es_pesable', False)),
                orden=idx
            )
            db.session.add(det)

            subtotal_total += sub_item
            iva_total += iva_item

        presu.subtotal = subtotal_total
        presu.iva = iva_total
        presu.total = subtotal_total + iva_total

        db.session.commit()
        return jsonify({
            'success': True,
            'id': presu.id,
            'numero': presu.numero_completo
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@presupuestos_bp.route('/<int:id>')
def ver(id):
    if 'user_id' not in session:
        return redirect('/login')

    presu = Presupuesto.query.get_or_404(id)
    return render_template('presupuestos_ver.html', presu=presu)


@presupuestos_bp.route('/<int:id>/cambiar_estado', methods=['POST'])
def cambiar_estado(id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'No autorizado'}), 401

    presu = Presupuesto.query.get_or_404(id)
    nuevo_estado = (request.get_json() or {}).get('estado')

    validos = ['borrador', 'enviado', 'aceptado', 'rechazado']
    if nuevo_estado not in validos:
        return jsonify({'success': False, 'error': 'Estado inválido'}), 400

    if presu.estado == 'convertido':
        return jsonify({'success': False, 'error': 'Ya fue convertido a factura — no se puede cambiar'}), 400

    presu.estado = nuevo_estado
    db.session.commit()
    return jsonify({'success': True, 'estado': nuevo_estado})


@presupuestos_bp.route('/<int:id>/eliminar', methods=['POST'])
def eliminar(id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'No autorizado'}), 401

    presu = Presupuesto.query.get_or_404(id)

    if presu.estado == 'convertido':
        return jsonify({
            'success': False,
            'error': 'No se puede eliminar un presupuesto convertido a factura'
        }), 400

    db.session.delete(presu)  # cascade borra detalle
    db.session.commit()
    return jsonify({'success': True})


@presupuestos_bp.route('/<int:id>/preparar_conversion', methods=['POST'])
def preparar_conversion(id):
    """Devuelve los items del presupuesto listos para cargar en nueva_venta.
    Body JSON: { actualizar_precios: bool }
      - False: usa precios cotizados originalmente
      - True:  usa precios actuales del maestro (para presupuestos vencidos)"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'No autorizado'}), 401

    presu = Presupuesto.query.get_or_404(id)

    if presu.estado != 'aceptado':
        return jsonify({
            'success': False,
            'error': f'Solo se puede convertir un presupuesto ACEPTADO. Estado actual: {presu.estado.upper()}'
        }), 400

    if presu.factura_id:
        return jsonify({
            'success': False,
            'error': 'Este presupuesto ya fue convertido a factura'
        }), 400

    data = request.get_json() or {}
    actualizar_precios = bool(data.get('actualizar_precios', False))

    productos_out = []
    for d in presu.detalles:
        precio = float(d.precio_unitario)
        iva = float(d.iva_alicuota)
        nombre = d.descripcion
        codigo = d.codigo_producto or ''
        stock = 999.0

        # Si el producto todavía existe en el maestro, leemos info actual
        if d.producto:
            stock = float(d.producto.stock or 0)
            if actualizar_precios:
                precio = float(d.producto.precio or precio)
                iva = float(d.producto.iva or iva)
                codigo = d.producto.codigo
                nombre = d.producto.nombre

        productos_out.append({
            'producto_id': d.producto_id,
            'codigo': codigo,
            'nombre': nombre,
            'cantidad': float(d.cantidad),
            'precio_unitario': precio,
            'subtotal': precio * float(d.cantidad),
            'iva': iva,
            'stock': stock,
            'es_combo': False,
        })

    return jsonify({
        'success': True,
        'presupuesto_id': presu.id,
        'numero': presu.numero_completo,
        'cliente_id': presu.cliente_id,
        'lista_precio': getattr(presu.cliente, 'lista_precio', 1) or 1,
        'productos': productos_out,
        'precios_actualizados': actualizar_precios
    })


@presupuestos_bp.route('/<int:id>/marcar_convertido', methods=['POST'])
def marcar_convertido(id):
    """Marca el presupuesto como CONVERTIDO y vincula la factura generada.
    Lo llama nueva_venta.html después de /procesar_venta exitoso."""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'No autorizado'}), 401

    presu = Presupuesto.query.get_or_404(id)

    factura_id = (request.get_json() or {}).get('factura_id')
    if not factura_id:
        return jsonify({'success': False, 'error': 'Falta factura_id'}), 400

    presu.estado = 'convertido'
    presu.factura_id = int(factura_id)
    presu.fecha_conversion = datetime.now()
    db.session.commit()

    return jsonify({'success': True})


# ============================================================================
# INIT
# ============================================================================

def init_presupuestos(app, cliente_cls, usuario_cls):
    """Registra el blueprint y recibe las clases de modelos para evitar
    circular imports. Llamar DESPUÉS de que Cliente y Usuario estén definidos
    en app.py (no al principio)."""
    global Cliente, Usuario
    Cliente = cliente_cls
    Usuario = usuario_cls
    app.register_blueprint(presupuestos_bp)