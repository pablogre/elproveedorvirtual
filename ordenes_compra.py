# =====================================================================
# ORDENES DE COMPRA - Módulo 5
# =====================================================================
# Fase 1: Modelos + listado.
#
# Se registra en app.py con:
#     from ordenes_compra import ordenes_compra_bp
#     app.register_blueprint(ordenes_compra_bp)
#
# NOTA: Este módulo importa db desde proveedores.py para compartir
# la misma instancia de SQLAlchemy. Si tu proyecto tiene la instancia
# db en otro archivo (ej. extensions.py), ajustar el import.
# =====================================================================

from flask import Blueprint, render_template, request, jsonify, session
from sqlalchemy import func, and_, or_
from datetime import datetime, date
from decimal import Decimal, ROUND_HALF_UP

# Importar la instancia db compartida y modelos existentes
# (ajustar el import si tu proyecto lo tiene diferente)
from proveedores import db, Proveedor, FacturaCompra

# Si tenés un modelo Producto global, importalo también.
# from app import Producto   # ← ajustar según tu proyecto
# Dejamos un import lazy — se resuelve al momento de usarlo
def _get_producto_sql(producto_id):
    """Busca un producto por id usando SQL crudo.
    Devuelve dict con id, codigo, nombre, costo, precio, iva, stock, o None.
    Evita el problema de doble-declaración de clases en app.py.
    """
    row = db.session.execute(
        db.text("""
            SELECT id, codigo, nombre, COALESCE(costo, 0) AS costo,
                   COALESCE(precio, 0) AS precio, COALESCE(iva, 21) AS iva,
                   COALESCE(stock, 0) AS stock
            FROM producto
            WHERE id = :id
        """),
        {'id': producto_id}
    ).fetchone()
    if not row:
        return None
    return {
        'id':     int(row[0]),
        'codigo': row[1] or '',
        'nombre': row[2] or '',
        'costo':  float(row[3] or 0),
        'precio': float(row[4] or 0),
        'iva':    float(row[5] or 21),
        'stock':  float(row[6] or 0),
    }


ordenes_compra_bp = Blueprint('ordenes_compra', __name__)

# =====================================================================
# MODELOS
# =====================================================================

class OrdenCompra(db.Model):
    __tablename__ = 'orden_compra'

    id                      = db.Column(db.Integer, primary_key=True)
    numero                  = db.Column(db.Integer, nullable=False, default=0)
    punto_venta             = db.Column(db.Integer, nullable=False, default=1)
    proveedor_id            = db.Column(db.Integer, db.ForeignKey('proveedor.id'), nullable=False)
    fecha_emision           = db.Column(db.Date, nullable=False)
    fecha_entrega_estimada  = db.Column(db.Date)
    estado                  = db.Column(db.String(15), nullable=False, default='borrador')
    # borrador / enviada / confirmada / parcial / recibida / facturada / cerrada / cancelada

    subtotal                = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    iva                     = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    total                   = db.Column(db.Numeric(12, 2), nullable=False, default=0)

    observaciones           = db.Column(db.Text)
    condiciones_pago        = db.Column(db.String(200))

    factura_compra_id       = db.Column(db.Integer, db.ForeignKey('factura_compra.id'))
    motivo_cancelacion      = db.Column(db.String(200))

    usuario_id              = db.Column(db.Integer, db.ForeignKey('usuario.id'))
    fecha_creacion          = db.Column(db.DateTime, default=datetime.now)
    fecha_modificacion      = db.Column(db.DateTime, onupdate=datetime.now)

    # Relaciones
    proveedor   = db.relationship('Proveedor', backref='ordenes_compra')
    factura     = db.relationship('FacturaCompra', backref='ordenes_compra_asociadas', foreign_keys=[factura_compra_id])
    detalles    = db.relationship('OrdenCompraDetalle', backref='orden_compra', cascade='all, delete-orphan', lazy='dynamic')
    recepciones = db.relationship('OrdenCompraRecepcion', backref='orden_compra', cascade='all, delete-orphan', lazy='dynamic')

    def numero_completo(self):
        return f"OC {str(self.punto_venta).zfill(4)}-{str(self.numero).zfill(8)}"

    def cantidad_items(self):
        return self.detalles.count()

    def tiene_recepciones(self):
        return self.recepciones.count() > 0

    def to_dict(self):
        return {
            'id':                      self.id,
            'numero':                  self.numero,
            'punto_venta':             self.punto_venta,
            'numero_completo':         self.numero_completo(),
            'proveedor_id':            self.proveedor_id,
            'proveedor':               self.proveedor.razon_social if self.proveedor else '',
            'fecha_emision':           self.fecha_emision.strftime('%d/%m/%Y') if self.fecha_emision else '',
            'fecha_entrega_estimada':  self.fecha_entrega_estimada.strftime('%d/%m/%Y') if self.fecha_entrega_estimada else '',
            'estado':                  self.estado,
            'subtotal':                float(self.subtotal or 0),
            'iva':                     float(self.iva or 0),
            'total':                   float(self.total or 0),
            'observaciones':           self.observaciones or '',
            'condiciones_pago':        self.condiciones_pago or '',
            'factura_compra_id':       self.factura_compra_id,
            'motivo_cancelacion':      self.motivo_cancelacion or '',
            'cantidad_items':          self.cantidad_items(),
            'tiene_recepciones':       self.tiene_recepciones(),
            'fecha_creacion':          self.fecha_creacion.strftime('%d/%m/%Y %H:%M') if self.fecha_creacion else '',
        }


class OrdenCompraDetalle(db.Model):
    __tablename__ = 'orden_compra_detalle'

    id                = db.Column(db.Integer, primary_key=True)
    oc_id             = db.Column(db.Integer, db.ForeignKey('orden_compra.id'), nullable=False)
    producto_id       = db.Column(db.Integer, db.ForeignKey('producto.id'), nullable=False)
    cantidad_pedida   = db.Column(db.Numeric(12, 3), nullable=False, default=0)
    cantidad_recibida = db.Column(db.Numeric(12, 3), nullable=False, default=0)
    precio_unitario   = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    subtotal          = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    observaciones     = db.Column(db.String(200))

    def cantidad_pendiente(self):
        return float(self.cantidad_pedida or 0) - float(self.cantidad_recibida or 0)

    def to_dict(self):
        # Resolver el producto a nombre usando SQL crudo
        try:
            prod = _get_producto_sql(self.producto_id)
            if prod:
                nombre = prod['nombre']
                codigo = prod['codigo']
            else:
                nombre = f'(Producto #{self.producto_id})'
                codigo = ''
        except Exception:
            nombre = f'(Producto #{self.producto_id})'
            codigo = ''

        return {
            'id':                 self.id,
            'oc_id':              self.oc_id,
            'producto_id':        self.producto_id,
            'producto_nombre':    nombre,
            'producto_codigo':    codigo,
            'cantidad_pedida':    float(self.cantidad_pedida or 0),
            'cantidad_recibida':  float(self.cantidad_recibida or 0),
            'cantidad_pendiente': self.cantidad_pendiente(),
            'precio_unitario':    float(self.precio_unitario or 0),
            'subtotal':           float(self.subtotal or 0),
            'observaciones':      self.observaciones or '',
        }


class OrdenCompraRecepcion(db.Model):
    __tablename__ = 'orden_compra_recepcion'

    id              = db.Column(db.Integer, primary_key=True)
    oc_id           = db.Column(db.Integer, db.ForeignKey('orden_compra.id'), nullable=False)
    fecha           = db.Column(db.Date, nullable=False)
    nro_remito      = db.Column(db.String(30))
    observaciones   = db.Column(db.Text)
    usuario_id      = db.Column(db.Integer, db.ForeignKey('usuario.id'))
    fecha_creacion  = db.Column(db.DateTime, default=datetime.now)

    detalles = db.relationship('OrdenCompraRecepcionDetalle', backref='recepcion', cascade='all, delete-orphan', lazy='dynamic')

    def to_dict(self):
        return {
            'id':             self.id,
            'oc_id':          self.oc_id,
            'fecha':          self.fecha.strftime('%d/%m/%Y') if self.fecha else '',
            'nro_remito':     self.nro_remito or '',
            'observaciones':  self.observaciones or '',
            'fecha_creacion': self.fecha_creacion.strftime('%d/%m/%Y %H:%M') if self.fecha_creacion else '',
            'cantidad_items': self.detalles.count(),
        }


class OrdenCompraRecepcionDetalle(db.Model):
    __tablename__ = 'orden_compra_recepcion_detalle'

    id                = db.Column(db.Integer, primary_key=True)
    recepcion_id      = db.Column(db.Integer, db.ForeignKey('orden_compra_recepcion.id'), nullable=False)
    oc_detalle_id     = db.Column(db.Integer, db.ForeignKey('orden_compra_detalle.id'), nullable=False)
    producto_id       = db.Column(db.Integer, db.ForeignKey('producto.id'), nullable=False)
    cantidad_recibida = db.Column(db.Numeric(12, 3), nullable=False, default=0)
    observaciones     = db.Column(db.String(200))

    oc_detalle = db.relationship('OrdenCompraDetalle', backref='recepciones_detalle')


class OrdenCompraNumerador(db.Model):
    __tablename__ = 'orden_compra_numerador'

    id             = db.Column(db.Integer, primary_key=True)
    punto_venta    = db.Column(db.Integer, nullable=False, default=1, unique=True)
    ultimo_numero  = db.Column(db.Integer, nullable=False, default=0)

    @staticmethod
    def siguiente_numero(pv=1):
        """Toma el próximo correlativo, con FOR UPDATE para evitar race conditions."""
        num = OrdenCompraNumerador.query.with_for_update().filter_by(punto_venta=pv).first()
        if not num:
            num = OrdenCompraNumerador(punto_venta=pv, ultimo_numero=0)
            db.session.add(num)
            db.session.flush()
        num.ultimo_numero += 1
        return num.ultimo_numero


# =====================================================================
# RUTAS
# =====================================================================

@ordenes_compra_bp.route('/ordenes_compra')
def listado_ordenes_compra():
    proveedores = Proveedor.query.filter_by(activo=True).order_by(Proveedor.razon_social).all()
    return render_template('ordenes_compra.html', proveedores=proveedores)


# =====================================================================
# APIs
# =====================================================================

@ordenes_compra_bp.route('/api/ordenes_compra/listar', methods=['GET'])
def api_oc_listar():
    """Listado con filtros: proveedor_id, estado, desde, hasta."""
    try:
        q = OrdenCompra.query

        proveedor_id = request.args.get('proveedor_id', type=int)
        estado       = request.args.get('estado', '').strip()
        desde        = request.args.get('desde', '').strip()
        hasta        = request.args.get('hasta', '').strip()

        if proveedor_id:
            q = q.filter(OrdenCompra.proveedor_id == proveedor_id)
        if estado:
            q = q.filter(OrdenCompra.estado == estado)
        if desde:
            try:
                q = q.filter(OrdenCompra.fecha_emision >= datetime.strptime(desde, '%Y-%m-%d').date())
            except ValueError:
                pass
        if hasta:
            try:
                q = q.filter(OrdenCompra.fecha_emision <= datetime.strptime(hasta, '%Y-%m-%d').date())
            except ValueError:
                pass

        # Ordenamos por fecha desc y luego por número desc
        q = q.order_by(OrdenCompra.fecha_emision.desc(), OrdenCompra.numero.desc())

        ordenes = [oc.to_dict() for oc in q.all()]

        # Totales
        resumen = {
            'cantidad':    len(ordenes),
            'total':       sum(o['total'] for o in ordenes),
            'por_estado':  {},
        }
        for o in ordenes:
            est = o['estado']
            resumen['por_estado'][est] = resumen['por_estado'].get(est, 0) + 1

        return jsonify({'success': True, 'ordenes': ordenes, 'resumen': resumen})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@ordenes_compra_bp.route('/api/ordenes_compra/<int:oc_id>/detalle', methods=['GET'])
def api_oc_detalle(oc_id):
    """Devuelve una OC con todos sus detalles + recepciones."""
    try:
        oc = OrdenCompra.query.get_or_404(oc_id)
        detalles    = [d.to_dict() for d in oc.detalles]
        recepciones = [r.to_dict() for r in oc.recepciones.order_by(OrdenCompraRecepcion.fecha.asc())]

        return jsonify({
            'success':    True,
            'orden':      oc.to_dict(),
            'detalles':   detalles,
            'recepciones': recepciones,
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# =====================================================================
# FASE 2 — Rutas y APIs para crear/editar/eliminar OCs
# =====================================================================

@ordenes_compra_bp.route('/orden_compra/nueva')
def pantalla_oc_nueva():
    """Pantalla para crear una OC nueva (borrador)."""
    proveedores = Proveedor.query.filter_by(activo=True).order_by(Proveedor.razon_social).all()
    return render_template('orden_compra_form.html',
                           proveedores=proveedores,
                           modo='nueva', oc_id=None)


@ordenes_compra_bp.route('/orden_compra/<int:oc_id>')
def pantalla_oc_detalle(oc_id):
    """Pantalla de detalle/edición de una OC existente."""
    oc = OrdenCompra.query.get_or_404(oc_id)
    proveedores = Proveedor.query.filter_by(activo=True).order_by(Proveedor.razon_social).all()
    # Si está en borrador y vienen con ?edit=1, modo edición
    edit = request.args.get('edit', '0') == '1'
    modo = 'editar' if (edit and oc.estado == 'borrador') else 'ver'
    return render_template('orden_compra_form.html',
                           proveedores=proveedores,
                           modo=modo, oc_id=oc_id)


# -----------------------------------------------------------------
# API: Buscador de productos para el autocomplete de la OC
# -----------------------------------------------------------------
@ordenes_compra_bp.route('/api/ordenes_compra/productos_buscar', methods=['GET'])
def api_oc_productos_buscar():
    """Busca productos activos por codigo/nombre para agregar a una OC.

    Usamos SQL crudo para evitar el problema de doble-declaración de clases
    en app.py (Usuario, Producto, etc. están declaradas dos veces y SQLAlchemy
    tira 'Table X is already defined' al importar).
    """
    try:
        q_text = (request.args.get('q') or '').strip()
        if len(q_text) < 2:
            return jsonify({'success': True, 'productos': []})

        like = f'%{q_text}%'
        rows = db.session.execute(
            db.text("""
                SELECT id, codigo, nombre, COALESCE(costo, 0) AS costo,
                       COALESCE(precio, 0) AS precio, COALESCE(iva, 21) AS iva,
                       COALESCE(stock, 0) AS stock
                FROM producto
                WHERE activo = 1
                  AND (codigo LIKE :like OR nombre LIKE :like)
                ORDER BY nombre ASC
                LIMIT 20
            """),
            {'like': like}
        ).fetchall()

        productos = [{
            'id':     int(r[0]),
            'codigo': r[1] or '',
            'nombre': r[2] or '',
            'costo':  float(r[3] or 0),
            'precio': float(r[4] or 0),
            'iva':    float(r[5] or 21),
            'stock':  float(r[6] or 0),
        } for r in rows]

        return jsonify({'success': True, 'productos': productos})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# -----------------------------------------------------------------
# API: Producto por ID (para cuando cargamos una OC existente)
# -----------------------------------------------------------------
@ordenes_compra_bp.route('/api/ordenes_compra/producto/<int:producto_id>', methods=['GET'])
def api_oc_producto_por_id(producto_id):
    try:
        row = db.session.execute(
            db.text("""
                SELECT id, codigo, nombre, COALESCE(costo, 0) AS costo,
                       COALESCE(precio, 0) AS precio, COALESCE(iva, 21) AS iva,
                       COALESCE(stock, 0) AS stock
                FROM producto
                WHERE id = :id
            """),
            {'id': producto_id}
        ).fetchone()

        if not row:
            return jsonify({'success': False, 'error': 'Producto no encontrado'}), 404

        return jsonify({
            'success': True,
            'producto': {
                'id':     int(row[0]),
                'codigo': row[1] or '',
                'nombre': row[2] or '',
                'costo':  float(row[3] or 0),
                'precio': float(row[4] or 0),
                'iva':    float(row[5] or 21),
                'stock':  float(row[6] or 0),
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# -----------------------------------------------------------------
# API: Crear OC (en borrador)
# -----------------------------------------------------------------
@ordenes_compra_bp.route('/api/ordenes_compra/nueva', methods=['POST'])
def api_oc_nueva():
    """Crea una OC nueva en estado 'borrador' con sus detalles."""
    try:
        data = request.get_json(force=True) or {}

        proveedor_id = int(data.get('proveedor_id') or 0)
        if not proveedor_id:
            return jsonify({'success': False, 'error': 'Falta proveedor'}), 400

        prov = Proveedor.query.get(proveedor_id)
        if not prov:
            return jsonify({'success': False, 'error': 'Proveedor inválido'}), 400

        fecha_em  = _parse_date(data.get('fecha_emision')) or date.today()
        fecha_ent = _parse_date(data.get('fecha_entrega_estimada'))

        detalles_in = data.get('detalles', []) or []
        if not detalles_in:
            return jsonify({'success': False, 'error': 'La OC no tiene ítems'}), 400

        # Numeración correlativa
        pv = int(data.get('punto_venta') or 1)
        numero = OrdenCompraNumerador.siguiente_numero(pv)

        oc = OrdenCompra(
            numero                  = numero,
            punto_venta             = pv,
            proveedor_id            = proveedor_id,
            fecha_emision           = fecha_em,
            fecha_entrega_estimada  = fecha_ent,
            estado                  = 'borrador',
            observaciones           = (data.get('observaciones') or '').strip() or None,
            condiciones_pago        = (data.get('condiciones_pago') or '').strip() or None,
            usuario_id              = session.get('user_id'),
        )
        db.session.add(oc)
        db.session.flush()

        subtotal_total = Decimal('0')
        iva_total      = Decimal('0')

        for d in detalles_in:
            try:
                producto_id = int(d.get('producto_id'))
                cantidad    = Decimal(str(d.get('cantidad') or 0))
                precio_u    = Decimal(str(d.get('precio_unitario') or 0))
            except Exception:
                db.session.rollback()
                return jsonify({'success': False, 'error': 'Datos de detalle inválidos'}), 400

            if cantidad <= 0 or precio_u < 0:
                db.session.rollback()
                return jsonify({'success': False, 'error': 'Cantidad debe ser > 0'}), 400

            # Calcular subtotal e IVA usando el IVA del producto (SQL crudo)
            prod = _get_producto_sql(producto_id)
            if not prod:
                db.session.rollback()
                return jsonify({'success': False, 'error': f'Producto {producto_id} no encontrado'}), 400

            iva_pct = Decimal(str(prod['iva'] or 21))

            subtot_linea = (cantidad * precio_u).quantize(Decimal('0.01'))
            iva_linea    = (subtot_linea * iva_pct / Decimal('100')).quantize(Decimal('0.01'))

            subtotal_total += subtot_linea
            iva_total      += iva_linea

            det = OrdenCompraDetalle(
                oc_id           = oc.id,
                producto_id     = producto_id,
                cantidad_pedida = cantidad,
                precio_unitario = precio_u,
                subtotal        = subtot_linea,
                observaciones   = (d.get('observaciones') or '').strip() or None,
            )
            db.session.add(det)

        oc.subtotal = subtotal_total
        oc.iva      = iva_total
        oc.total    = subtotal_total + iva_total

        db.session.commit()

        return jsonify({'success': True, 'oc_id': oc.id, 'numero_completo': oc.numero_completo()})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


# -----------------------------------------------------------------
# API: Actualizar OC (solo si está en borrador)
# -----------------------------------------------------------------
@ordenes_compra_bp.route('/api/ordenes_compra/<int:oc_id>/editar', methods=['POST'])
def api_oc_editar(oc_id):
    """Actualiza una OC existente. Solo permitido si estado='borrador'."""
    try:
        oc = OrdenCompra.query.get_or_404(oc_id)

        # Permitir edición libre solo en borrador
        if oc.estado != 'borrador':
            return jsonify({
                'success': False,
                'error': f'Solo se puede editar en borrador. Estado actual: {oc.estado}.'
            }), 400

        data = request.get_json(force=True) or {}

        # Cabecera
        proveedor_id = int(data.get('proveedor_id') or 0)
        if not proveedor_id:
            return jsonify({'success': False, 'error': 'Falta proveedor'}), 400

        oc.proveedor_id           = proveedor_id
        oc.fecha_emision          = _parse_date(data.get('fecha_emision')) or oc.fecha_emision
        oc.fecha_entrega_estimada = _parse_date(data.get('fecha_entrega_estimada'))
        oc.observaciones          = (data.get('observaciones') or '').strip() or None
        oc.condiciones_pago       = (data.get('condiciones_pago') or '').strip() or None

        detalles_in = data.get('detalles', []) or []
        if not detalles_in:
            return jsonify({'success': False, 'error': 'La OC no tiene ítems'}), 400

        # Borramos los detalles actuales y rehacemos (es más simple y seguro
        # porque estamos en borrador, no hay dependencias).
        for d in oc.detalles.all():
            db.session.delete(d)
        db.session.flush()

        subtotal_total = Decimal('0')
        iva_total      = Decimal('0')

        for d in detalles_in:
            try:
                producto_id = int(d.get('producto_id'))
                cantidad    = Decimal(str(d.get('cantidad') or 0))
                precio_u    = Decimal(str(d.get('precio_unitario') or 0))
            except Exception:
                db.session.rollback()
                return jsonify({'success': False, 'error': 'Datos de detalle inválidos'}), 400

            if cantidad <= 0 or precio_u < 0:
                db.session.rollback()
                return jsonify({'success': False, 'error': 'Cantidad debe ser > 0'}), 400

            Producto = None  # (sin uso — SQL crudo)
            prod = _get_producto_sql(producto_id)
            if not prod:
                db.session.rollback()
                return jsonify({'success': False, 'error': f'Producto {producto_id} no encontrado'}), 400

            iva_pct = Decimal(str(prod['iva'] or 21))

            subtot_linea = (cantidad * precio_u).quantize(Decimal('0.01'))
            iva_linea    = (subtot_linea * iva_pct / Decimal('100')).quantize(Decimal('0.01'))

            subtotal_total += subtot_linea
            iva_total      += iva_linea

            det = OrdenCompraDetalle(
                oc_id           = oc.id,
                producto_id     = producto_id,
                cantidad_pedida = cantidad,
                precio_unitario = precio_u,
                subtotal        = subtot_linea,
                observaciones   = (d.get('observaciones') or '').strip() or None,
            )
            db.session.add(det)

        oc.subtotal = subtotal_total
        oc.iva      = iva_total
        oc.total    = subtotal_total + iva_total

        db.session.commit()

        return jsonify({'success': True, 'oc_id': oc.id, 'numero_completo': oc.numero_completo()})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


# -----------------------------------------------------------------
# API: Editar solo observaciones (para estados posteriores a borrador)
# -----------------------------------------------------------------
@ordenes_compra_bp.route('/api/ordenes_compra/<int:oc_id>/observaciones', methods=['POST'])
def api_oc_observaciones(oc_id):
    """Edita solo observaciones. Permitido en cualquier estado no-final."""
    try:
        oc = OrdenCompra.query.get_or_404(oc_id)
        if oc.estado in ('cerrada', 'cancelada'):
            return jsonify({'success': False, 'error': f'OC en estado {oc.estado}. No editable.'}), 400

        data = request.get_json(force=True) or {}
        oc.observaciones = (data.get('observaciones') or '').strip() or None
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


# -----------------------------------------------------------------
# API: Eliminar OC (solo si está en borrador)
# -----------------------------------------------------------------
@ordenes_compra_bp.route('/api/ordenes_compra/<int:oc_id>/eliminar', methods=['POST'])
def api_oc_eliminar(oc_id):
    """Elimina una OC. Solo permitido si estado='borrador'."""
    try:
        oc = OrdenCompra.query.get_or_404(oc_id)

        if oc.estado != 'borrador':
            return jsonify({
                'success': False,
                'error': f'Solo se eliminan borradores. La OC está en estado {oc.estado}. '
                         f'Si querés descartarla, usá "Cancelar".'
            }), 400

        db.session.delete(oc)  # los detalles caen por CASCADE
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


# =====================================================================
# FASE 3 — Acciones de estado + PDF
# =====================================================================

@ordenes_compra_bp.route('/api/ordenes_compra/<int:oc_id>/enviar', methods=['POST'])
def api_oc_enviar(oc_id):
    """Marca la OC como enviada. Si el proveedor tiene email, manda el PDF
    automáticamente. Solo permitido desde estado 'borrador'.
    """
    try:
        oc = OrdenCompra.query.get_or_404(oc_id)
        if oc.estado != 'borrador':
            return jsonify({
                'success': False,
                'error': f'Solo se puede enviar una OC en borrador. Estado actual: {oc.estado}.'
            }), 400

        if not oc.detalles.count():
            return jsonify({'success': False, 'error': 'La OC no tiene items'}), 400

        # Marcamos como enviada primero
        oc.estado = 'enviada'
        db.session.commit()

        mail_info = {
            'intentado': False,
            'enviado':   False,
            'destino':   None,
            'motivo':    None,
        }

        prov = oc.proveedor
        email_prov = (getattr(prov, 'email', None) or '').strip() if prov else ''

        if email_prov:
            mail_info['intentado'] = True
            mail_info['destino']   = email_prov
            try:
                from email_sender import enviar_email
                from opc_compra import generar_pdf_orden_compra

                # Generar PDF
                datos_pdf = _armar_datos_pdf_oc(oc)
                pdf_buffer = generar_pdf_orden_compra(datos_pdf)
                pdf_bytes  = pdf_buffer.getvalue()

                nombre_archivo = f"OC_{oc.numero_completo().replace(' ', '_').replace('-', '_')}.pdf"

                # Armar cuerpo
                import config_cliente as CFG
                razon_emp   = getattr(CFG, 'RAZON_SOCIAL', 'Nuestra empresa') or 'Nuestra empresa'
                tel_emp     = getattr(CFG, 'TELEFONO', '') or ''
                email_emp   = getattr(CFG, 'EMAIL', '') or ''

                # Formato de monto argentino (miles con . decimales con ,)
                monto_fmt = f'{float(oc.total or 0):,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')

                asunto = f'Orden de Compra {oc.numero_completo()} - {razon_emp}'

                cond_pago = oc.condiciones_pago or 'A convenir'
                fecha_ent = oc.fecha_entrega_estimada.strftime('%d/%m/%Y') if oc.fecha_entrega_estimada else 'A coordinar'
                fecha_em  = oc.fecha_emision.strftime('%d/%m/%Y') if oc.fecha_emision else ''

                obs_html = f'<p><strong>Observaciones:</strong> {oc.observaciones}</p>' if oc.observaciones else ''

                cuerpo_html = (
                    f'<p>Estimados {prov.razon_social if prov else ""},</p>'
                    f'<p>Les enviamos adjunta la <strong>Orden de Compra {oc.numero_completo()}</strong> '
                    f'emitida el {fecha_em}.</p>'
                    f'<ul>'
                    f'  <li><strong>Total:</strong> $ {monto_fmt}</li>'
                    f'  <li><strong>Entrega estimada:</strong> {fecha_ent}</li>'
                    f'  <li><strong>Condiciones de pago:</strong> {cond_pago}</li>'
                    f'</ul>'
                    f'{obs_html}'
                    f'<p>Por favor confirmen recepcion y disponibilidad.</p>'
                    f'<p>Saludos cordiales,<br>'
                    f'<strong>{razon_emp}</strong>'
                    f'{("<br>Tel: " + tel_emp) if tel_emp else ""}'
                    f'{("<br>" + email_emp) if email_emp else ""}'
                    f'</p>'
                    f'<hr style="border:none;border-top:1px solid #ccc;margin-top:20px">'
                    f'<p style="color:#888;font-size:11px">'
                    f'Este correo fue generado automaticamente por el sistema de gestion de {razon_emp}.'
                    f'</p>'
                )

                ok, msg = enviar_email(
                    destinatario  = email_prov,
                    asunto        = asunto,
                    cuerpo_html   = cuerpo_html,
                    adjunto_bytes = pdf_bytes,
                    nombre_adjunto= nombre_archivo,
                    mime_adjunto  = 'application/pdf',
                )
                mail_info['enviado'] = ok
                mail_info['motivo']  = msg if not ok else 'OK'

            except Exception as e:
                mail_info['motivo'] = f'Error interno: {str(e)}'
        else:
            mail_info['motivo'] = 'El proveedor no tiene email cargado'

        return jsonify({
            'success':      True,
            'estado_nuevo': 'enviada',
            'mail':         mail_info,
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


def _armar_datos_pdf_oc(oc):
    """Helper: arma el dict de datos para generar_pdf_orden_compra desde una OrdenCompra."""
    prov = oc.proveedor
    detalles = []
    for d in oc.detalles:
        prod = _get_producto_sql(d.producto_id)
        detalles.append({
            'codigo':          (prod['codigo'] if prod else ''),
            'nombre':          (prod['nombre'] if prod else f'(Producto #{d.producto_id})'),
            'cantidad':        float(d.cantidad_pedida or 0),
            'precio_unitario': float(d.precio_unitario or 0),
            'subtotal':        float(d.subtotal or 0),
            'observaciones':   d.observaciones or '',
        })
    return {
        'numero_completo':        oc.numero_completo(),
        'fecha_emision':          oc.fecha_emision.strftime('%d/%m/%Y') if oc.fecha_emision else '',
        'fecha_entrega_estimada': oc.fecha_entrega_estimada.strftime('%d/%m/%Y') if oc.fecha_entrega_estimada else '',
        'estado':                 oc.estado,
        'proveedor_razon_social': prov.razon_social if prov else '',
        'proveedor_cuit':         getattr(prov, 'cuit', '') if prov else '',
        'proveedor_direccion':    getattr(prov, 'direccion', '') if prov else '',
        'proveedor_telefono':     getattr(prov, 'telefono', '') if prov else '',
        'proveedor_email':        getattr(prov, 'email', '') if prov else '',
        'detalles':               detalles,
        'subtotal':               float(oc.subtotal or 0),
        'iva':                    float(oc.iva or 0),
        'total':                  float(oc.total or 0),
        'observaciones':          oc.observaciones or '',
        'condiciones_pago':       oc.condiciones_pago or '',
        'motivo_cancelacion':     oc.motivo_cancelacion or '',
    }


@ordenes_compra_bp.route('/api/ordenes_compra/<int:oc_id>/confirmar', methods=['POST'])
def api_oc_confirmar(oc_id):
    """Marca la OC como confirmada. Permitido desde 'enviada'."""
    try:
        oc = OrdenCompra.query.get_or_404(oc_id)
        if oc.estado != 'enviada':
            return jsonify({
                'success': False,
                'error': f'Solo se puede confirmar una OC enviada. Estado actual: {oc.estado}.'
            }), 400

        oc.estado = 'confirmada'
        db.session.commit()
        return jsonify({'success': True, 'estado_nuevo': 'confirmada'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@ordenes_compra_bp.route('/api/ordenes_compra/<int:oc_id>/cancelar', methods=['POST'])
def api_oc_cancelar(oc_id):
    """Cancela la OC con motivo obligatorio. Permitido salvo facturada/cerrada/cancelada."""
    try:
        oc = OrdenCompra.query.get_or_404(oc_id)
        if oc.estado in ('facturada', 'cerrada', 'cancelada'):
            return jsonify({
                'success': False,
                'error': f'No se puede cancelar una OC en estado {oc.estado}.'
            }), 400

        data = request.get_json(force=True) or {}
        motivo = (data.get('motivo') or '').strip()
        if not motivo:
            return jsonify({'success': False, 'error': 'El motivo es obligatorio'}), 400

        oc.motivo_cancelacion = motivo
        oc.estado = 'cancelada'
        db.session.commit()
        return jsonify({'success': True, 'estado_nuevo': 'cancelada'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


# -----------------------------------------------------------------
# PDF de la Orden de Compra
# -----------------------------------------------------------------
@ordenes_compra_bp.route('/api/ordenes_compra/<int:oc_id>/pdf', methods=['GET'])
def api_oc_pdf(oc_id):
    """Genera el PDF de una OC y lo devuelve inline para abrir en pestaña nueva."""
    try:
        from flask import send_file
        from opc_compra import generar_pdf_orden_compra

        oc = OrdenCompra.query.get_or_404(oc_id)
        datos = _armar_datos_pdf_oc(oc)
        pdf_buffer = generar_pdf_orden_compra(datos)
        pdf_buffer.seek(0)

        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=False,
            download_name=f'OC_{oc.numero_completo().replace(" ", "_")}.pdf'
        )
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500




def _parse_date(s):
    if not s:
        return None
    try:
        return datetime.strptime(s, '%Y-%m-%d').date()
    except Exception:
        return None


# =====================================================================
# FASE 4 — Recepción de mercadería (impacto en stock)
# =====================================================================

@ordenes_compra_bp.route('/orden_compra/<int:oc_id>/recibir')
def pantalla_oc_recibir(oc_id):
    """Pantalla para registrar una nueva recepción de una OC."""
    oc = OrdenCompra.query.get_or_404(oc_id)
    return render_template('orden_compra_recepcion.html', oc_id=oc_id)


@ordenes_compra_bp.route('/api/ordenes_compra/<int:oc_id>/pendiente', methods=['GET'])
def api_oc_pendiente(oc_id):
    """Devuelve los ítems de la OC con su cantidad pendiente de recibir."""
    try:
        oc = OrdenCompra.query.get_or_404(oc_id)
        if oc.estado not in ('confirmada', 'parcial'):
            return jsonify({
                'success': False,
                'error': f'No se pueden registrar recepciones en estado {oc.estado}. '
                         f'La OC debe estar en "confirmada" o "parcial".'
            }), 400

        items = []
        for d in oc.detalles:
            prod = _get_producto_sql(d.producto_id)
            pendiente = float(d.cantidad_pedida or 0) - float(d.cantidad_recibida or 0)
            if pendiente <= 0:
                continue
            items.append({
                'detalle_id':         d.id,
                'producto_id':        d.producto_id,
                'codigo':             prod['codigo'] if prod else '',
                'nombre':             prod['nombre'] if prod else f'(#{d.producto_id})',
                'cantidad_pedida':    float(d.cantidad_pedida or 0),
                'cantidad_recibida':  float(d.cantidad_recibida or 0),
                'cantidad_pendiente': pendiente,
                'precio_unitario':    float(d.precio_unitario or 0),
            })

        return jsonify({
            'success': True,
            'oc':      oc.to_dict(),
            'items':   items,
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@ordenes_compra_bp.route('/api/ordenes_compra/<int:oc_id>/recibir', methods=['POST'])
def api_oc_recibir(oc_id):
    """Registra una recepción (total o parcial) y suma stock."""
    try:
        oc = OrdenCompra.query.get_or_404(oc_id)
        if oc.estado not in ('confirmada', 'parcial'):
            return jsonify({
                'success': False,
                'error': f'No se puede recibir en estado {oc.estado}.'
            }), 400

        data = request.get_json(force=True) or {}
        fecha       = _parse_date(data.get('fecha')) or date.today()
        nro_remito  = (data.get('nro_remito') or '').strip() or None
        obs_general = (data.get('observaciones') or '').strip() or None
        items_in    = data.get('items', []) or []

        if not items_in:
            return jsonify({'success': False, 'error': 'No hay ítems para recibir'}), 400

        # Validar cada ítem
        items_validados = []
        for it in items_in:
            try:
                detalle_id = int(it.get('detalle_id'))
                cant_rec   = Decimal(str(it.get('cantidad_recibida') or 0))
            except Exception:
                return jsonify({'success': False, 'error': 'Datos de ítem inválidos'}), 400

            if cant_rec <= 0:
                continue

            det = OrdenCompraDetalle.query.get(detalle_id)
            if not det or det.oc_id != oc_id:
                return jsonify({'success': False, 'error': f'Detalle {detalle_id} inválido'}), 400

            pendiente = Decimal(str(det.cantidad_pedida or 0)) - Decimal(str(det.cantidad_recibida or 0))
            if cant_rec > pendiente:
                return jsonify({
                    'success': False,
                    'error': f'No se puede recibir más que lo pendiente. '
                             f'Producto #{det.producto_id}: pendiente {pendiente}, intentaste recibir {cant_rec}.'
                }), 400

            items_validados.append({
                'detalle':           det,
                'cantidad_recibida': cant_rec,
                'observaciones':     (it.get('observaciones') or '').strip() or None,
            })

        if not items_validados:
            return jsonify({'success': False, 'error': 'No hay cantidades a recibir > 0'}), 400

        # Transacción
        recepcion = OrdenCompraRecepcion(
            oc_id         = oc_id,
            fecha         = fecha,
            nro_remito    = nro_remito,
            observaciones = obs_general,
            usuario_id    = session.get('user_id'),
        )
        db.session.add(recepcion)
        db.session.flush()

        for iv in items_validados:
            det = iv['detalle']
            cant_rec = iv['cantidad_recibida']

            # 1) Detalle de la recepción
            rd = OrdenCompraRecepcionDetalle(
                recepcion_id      = recepcion.id,
                oc_detalle_id     = det.id,
                producto_id       = det.producto_id,
                cantidad_recibida = cant_rec,
                observaciones     = iv['observaciones'],
            )
            db.session.add(rd)

            # 2) Actualizar detalle de la OC
            det.cantidad_recibida = Decimal(str(det.cantidad_recibida or 0)) + cant_rec

            # 3) Sumar stock al producto
            db.session.execute(
                db.text("UPDATE producto SET stock = COALESCE(stock, 0) + :c WHERE id = :pid"),
                {'c': float(cant_rec), 'pid': det.producto_id}
            )

        # 4) Recalcular estado
        db.session.flush()
        total_pedido   = Decimal('0')
        total_recibido = Decimal('0')
        for d in oc.detalles:
            total_pedido   += Decimal(str(d.cantidad_pedida or 0))
            total_recibido += Decimal(str(d.cantidad_recibida or 0))

        if total_recibido >= total_pedido:
            oc.estado = 'recibida'
        else:
            oc.estado = 'parcial'

        db.session.commit()
        return jsonify({
            'success':       True,
            'recepcion_id':  recepcion.id,
            'estado_nuevo':  oc.estado,
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@ordenes_compra_bp.route('/api/ordenes_compra/<int:oc_id>/recepciones', methods=['GET'])
def api_oc_recepciones(oc_id):
    """Listado de todas las recepciones registradas para una OC."""
    try:
        oc = OrdenCompra.query.get_or_404(oc_id)
        recepciones = []
        for rec in oc.recepciones.order_by(OrdenCompraRecepcion.fecha.desc(), OrdenCompraRecepcion.id.desc()):
            items = []
            for rd in rec.detalles:
                prod = _get_producto_sql(rd.producto_id)
                items.append({
                    'producto_id':       rd.producto_id,
                    'codigo':            prod['codigo'] if prod else '',
                    'nombre':            prod['nombre'] if prod else f'(#{rd.producto_id})',
                    'cantidad_recibida': float(rd.cantidad_recibida or 0),
                    'observaciones':     rd.observaciones or '',
                })
            recepciones.append({
                'id':            rec.id,
                'fecha':         rec.fecha.strftime('%d/%m/%Y') if rec.fecha else '',
                'nro_remito':    rec.nro_remito or '',
                'observaciones': rec.observaciones or '',
                'fecha_creacion': rec.fecha_creacion.strftime('%d/%m/%Y %H:%M') if rec.fecha_creacion else '',
                'items':         items,
                'cantidad_items': len(items),
            })

        # Calcular totales por producto (pedido vs recibido) para resumen
        resumen_items = []
        for d in oc.detalles:
            prod = _get_producto_sql(d.producto_id)
            resumen_items.append({
                'producto_id':       d.producto_id,
                'codigo':            prod['codigo'] if prod else '',
                'nombre':            prod['nombre'] if prod else f'(#{d.producto_id})',
                'cantidad_pedida':   float(d.cantidad_pedida or 0),
                'cantidad_recibida': float(d.cantidad_recibida or 0),
                'cantidad_pendiente': float(d.cantidad_pedida or 0) - float(d.cantidad_recibida or 0),
            })

        return jsonify({
            'success': True,
            'recepciones': recepciones,
            'resumen_items': resumen_items,
            'oc_estado': oc.estado,
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500



def api_oc_recepcion_eliminar(recepcion_id):
    """Elimina una recepción y revierte el stock. No permitido si OC facturada/cerrada."""
    try:
        rec = OrdenCompraRecepcion.query.get_or_404(recepcion_id)
        oc  = OrdenCompra.query.get(rec.oc_id)
        if not oc:
            return jsonify({'success': False, 'error': 'OC no encontrada'}), 404
        if oc.estado in ('facturada', 'cerrada'):
            return jsonify({
                'success': False,
                'error': f'No se puede eliminar recepción de una OC {oc.estado}.'
            }), 400

        # Revertir stock y cantidades
        for rd in rec.detalles:
            cant = Decimal(str(rd.cantidad_recibida or 0))

            db.session.execute(
                db.text("UPDATE producto SET stock = COALESCE(stock, 0) - :c WHERE id = :pid"),
                {'c': float(cant), 'pid': rd.producto_id}
            )

            det = OrdenCompraDetalle.query.get(rd.oc_detalle_id)
            if det:
                nuevo = Decimal(str(det.cantidad_recibida or 0)) - cant
                det.cantidad_recibida = nuevo if nuevo > 0 else Decimal('0')

        db.session.delete(rec)
        db.session.flush()

        # Recalcular estado
        total_pedido   = Decimal('0')
        total_recibido = Decimal('0')
        for d in oc.detalles:
            total_pedido   += Decimal(str(d.cantidad_pedida or 0))
            total_recibido += Decimal(str(d.cantidad_recibida or 0))

        if total_recibido <= 0:
            oc.estado = 'confirmada'
        elif total_recibido >= total_pedido:
            oc.estado = 'recibida'
        else:
            oc.estado = 'parcial'

        db.session.commit()
        return jsonify({'success': True, 'estado_nuevo': oc.estado})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


# =============================================================
# FASE 5 — DATOS PARA GENERAR FACTURA DESDE OC
# =============================================================

@ordenes_compra_bp.route('/api/ordenes_compra/<int:oc_id>/datos_para_factura', methods=['GET'])
def api_oc_datos_para_factura(oc_id):
    """
    Devuelve cabecera + items RECIBIDOS (agregados por producto) + totales sugeridos
    por alicuota IVA, para precargar la pantalla de factura de compra con detalle.

    IMPORTANTE:
    - Solo toma items con cantidad_recibida > 0 (lo que efectivamente llego).
    - Si hay varias recepciones del mismo producto, suma.
    - Usa el precio_unitario de la OC (el proveedor puede haber facturado distinto,
      el usuario podra corregirlo en la pantalla antes de guardar).
    - Los totales por alicuota se calculan con producto.iva de cada item.
    """
    try:
        oc = OrdenCompra.query.get_or_404(oc_id)

        # Validaciones de estado
        if oc.estado in ('borrador', 'enviada'):
            return jsonify({
                'success': False,
                'error': f'La OC esta en estado "{oc.estado}". Primero hay que confirmarla y recibir mercaderia.'
            }), 400
        if oc.estado == 'cancelada':
            return jsonify({'success': False, 'error': 'La OC esta cancelada.'}), 400
        if oc.estado == 'facturada':
            return jsonify({
                'success': False,
                'error': f'La OC ya fue facturada (factura #{oc.factura_compra_id}).'
            }), 400

        # Armar items desde los detalles de OC (con cantidad_recibida > 0)
        items = []
        neto_21_acum  = Decimal('0')
        neto_105_acum = Decimal('0')
        neto_ng_acum  = Decimal('0')

        for d in oc.detalles:
            cant_recibida = Decimal(str(d.cantidad_recibida or 0))
            if cant_recibida <= 0:
                continue

            prod = _get_producto_sql(d.producto_id)
            if not prod:
                continue

            iva_prod = Decimal(str(prod.get('iva') or 21))
            precio_u = Decimal(str(d.precio_unitario or 0))

            # Subtotal sin IVA (lo que va al neto gravado segun alicuota)
            subtotal_sin_iva = cant_recibida * precio_u

            if iva_prod == Decimal('21'):
                neto_21_acum += subtotal_sin_iva
            elif iva_prod == Decimal('10.5'):
                neto_105_acum += subtotal_sin_iva
            else:
                # 0% u otras alicuotas poco frecuentes: van al neto no gravado como fallback
                neto_ng_acum += subtotal_sin_iva

            # Buscar codigo del proveedor para este producto (si lo hay cargado)
            cod_prov_row = db.session.execute(
                db.text("""
                    SELECT codigo_proveedor FROM producto_proveedor
                     WHERE producto_id = :pid AND proveedor_id = :prov
                     LIMIT 1
                """),
                {'pid': d.producto_id, 'prov': oc.proveedor_id}
            ).mappings().first()
            codigo_prov = cod_prov_row['codigo_proveedor'] if cod_prov_row else ''

            items.append({
                'producto_id':     d.producto_id,
                'codigo':          prod.get('codigo', ''),
                'nombre':          prod.get('nombre', ''),
                'cantidad':        float(cant_recibida),
                'precio_unitario': float(precio_u),
                'iva':             float(iva_prod),
                'codigo_proveedor': codigo_prov,
            })

        if not items:
            return jsonify({
                'success': False,
                'error': 'La OC no tiene items recibidos todavia.'
            }), 400

        # Totales IVA calculados (2 decimales)
        neto_21_r  = float(neto_21_acum.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
        neto_105_r = float(neto_105_acum.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
        neto_ng_r  = float(neto_ng_acum.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))

        iva_21_r  = float((neto_21_acum  * Decimal('0.21')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
        iva_105_r = float((neto_105_acum * Decimal('0.105')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))

        total_sugerido = round(neto_21_r + iva_21_r + neto_105_r + iva_105_r + neto_ng_r, 2)

        # Datos del proveedor
        prov_row = db.session.execute(
            db.text("SELECT id, razon_social, cuit, condicion_iva FROM proveedor WHERE id = :pid"),
            {'pid': oc.proveedor_id}
        ).mappings().first()

        return jsonify({
            'success': True,
            'oc': {
                'id':              oc.id,
                'numero_completo': oc.numero_completo(),
                'estado':          oc.estado,
                'fecha_emision':   oc.fecha_emision.strftime('%d/%m/%Y') if oc.fecha_emision else '',
                'observaciones':   oc.observaciones or '',
            },
            'proveedor': {
                'id':            prov_row['id'] if prov_row else oc.proveedor_id,
                'razon_social':  prov_row['razon_social'] if prov_row else '',
                'cuit':          prov_row['cuit'] if prov_row else '',
                'condicion_iva': prov_row['condicion_iva'] if prov_row else '',
            },
            'items': items,
            'totales_sugeridos': {
                'neto_21':         neto_21_r,
                'iva_21':          iva_21_r,
                'neto_105':        neto_105_r,
                'iva_105':         iva_105_r,
                'neto_no_gravado': neto_ng_r,
                'total':           total_sugerido,
            },
        })

    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500