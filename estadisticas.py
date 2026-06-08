# estadisticas.py
from flask import Blueprint, jsonify, request, render_template, session, redirect, url_for
from datetime import datetime, timedelta
from sqlalchemy import func, extract, text
from decimal import Decimal
import calendar
from functools import wraps

# Crear blueprint para estadísticas
estadisticas_bp = Blueprint('estadisticas', __name__)

# Decorador personalizado para verificar sesión (compatible con tu app.py)
def login_required(f):
    """Decorador personalizado para verificar sesión"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def init_estadisticas(db, Factura, DetalleFactura, Producto, Cliente=None):
    """
    Inicializar el blueprint con las dependencias necesarias
    
    Args:
        db: Instancia de SQLAlchemy
        Factura: Modelo de Factura
        DetalleFactura: Modelo de DetalleFactura  
        Producto: Modelo de Producto
        Cliente: Modelo de Cliente (opcional, para reporte IVA ventas)
    """
    
    @estadisticas_bp.route('/api/estadisticas_ventas')
    def estadisticas_ventas():
        try:
            # Obtener parámetros
            ano = request.args.get('ano', datetime.now().year, type=int)
            
            # Consulta para ventas por mes del año especificado
            ventas_mensuales = db.session.query(
                extract('month', Factura.fecha).label('mes'),
                func.count(Factura.id).label('cantidad_ventas'),
                func.sum(Factura.total).label('total_ventas'),
                func.avg(Factura.total).label('promedio_venta')
            ).filter(
                extract('year', Factura.fecha) == ano,
                Factura.estado != 'cancelada'
            ).group_by(
                extract('month', Factura.fecha)
            ).order_by('mes').all()
            
            # Crear estructura de datos completa (todos los 12 meses)
            datos_mensuales = []
            ventas_dict = {v.mes: v for v in ventas_mensuales}
            
            for mes in range(1, 13):
                venta_mes = ventas_dict.get(mes)
                datos_mensuales.append({
                    'mes': mes,
                    'nombre_mes': calendar.month_name[mes],
                    'nombre_corto': calendar.month_abbr[mes],
                    'cantidad_ventas': int(venta_mes.cantidad_ventas) if venta_mes else 0,
                    'total_ventas': float(venta_mes.total_ventas) if venta_mes else 0.0,
                    'promedio_venta': float(venta_mes.promedio_venta) if venta_mes else 0.0
                })
            
            # Estadísticas generales del año
            total_ano = sum(m['total_ventas'] for m in datos_mensuales)
            total_ventas_ano = sum(m['cantidad_ventas'] for m in datos_mensuales)
            promedio_mensual = total_ano / 12 if total_ano > 0 else 0
            
            # Mes con mayores ventas
            mes_mayor = max(datos_mensuales, key=lambda x: x['total_ventas'])
            mes_menor = min(datos_mensuales, key=lambda x: x['total_ventas'])
            
            # Comparación con año anterior
            ano_anterior = ano - 1
            total_ano_anterior = db.session.query(
                func.sum(Factura.total)
            ).filter(
                extract('year', Factura.fecha) == ano_anterior,
                Factura.estado != 'cancelada'
            ).scalar() or 0
            total_ano_anterior = float(total_ano_anterior)  # Convertir a float para evitar error con Decimal
            
            crecimiento = 0
            if total_ano_anterior > 0:
                crecimiento = ((total_ano - total_ano_anterior) / total_ano_anterior) * 100
            
            return jsonify({
                'success': True,
                'ano': ano,
                'datos_mensuales': datos_mensuales,
                'resumen': {
                    'total_ventas_ano': total_ventas_ano,
                    'total_dinero_ano': round(total_ano, 2),
                    'promedio_mensual': round(promedio_mensual, 2),
                    'mes_mayor': {
                        'mes': mes_mayor['nombre_mes'],
                        'total': mes_mayor['total_ventas']
                    },
                    'mes_menor': {
                        'mes': mes_menor['nombre_mes'],
                        'total': mes_menor['total_ventas']
                    },
                    'crecimiento_anual': round(crecimiento, 1),
                    'total_ano_anterior': round(total_ano_anterior, 2)
                }
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @estadisticas_bp.route('/api/comparacion_anos')
    def comparacion_anos():
        try:
            anos = request.args.getlist('anos', type=int)
            if not anos:
                # Por defecto: año actual y anterior
                ano_actual = datetime.now().year
                anos = [ano_actual - 1, ano_actual]
            
            datos_comparacion = []
            
            for ano in anos:
                ventas_ano = db.session.query(
                    extract('month', Factura.fecha).label('mes'),
                    func.sum(Factura.total).label('total')
                ).filter(
                    extract('year', Factura.fecha) == ano,
                    Factura.estado != 'cancelada'
                ).group_by(
                    extract('month', Factura.fecha)
                ).all()
                
                # Crear array con todos los meses
                ventas_mensuales = [0.0] * 12
                for venta in ventas_ano:
                    ventas_mensuales[int(venta.mes) - 1] = float(venta.total) if venta.total else 0.0
                
                datos_comparacion.append({
                    'ano': ano,
                    'ventas_mensuales': ventas_mensuales,
                    'total_ano': sum(ventas_mensuales)
                })
            
            return jsonify({
                'success': True,
                'datos': datos_comparacion,
                'meses': [calendar.month_abbr[i] for i in range(1, 13)]
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @estadisticas_bp.route('/api/top_productos_mes')
    def top_productos_mes():
        try:
            mes = request.args.get('mes', type=int)
            ano = request.args.get('ano', type=int)
            limite = request.args.get('limite', 10, type=int)
            
            nombres_meses = [
                '', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
            ]
            
            # Consulta usando SQLAlchemy en lugar de SQL crudo
            top_productos = db.session.query(
                Producto.codigo,
                Producto.nombre,
                func.sum(DetalleFactura.cantidad).label('cantidad_vendida'),
                func.sum(DetalleFactura.cantidad * DetalleFactura.precio_unitario).label('total_vendido')
            ).join(
                DetalleFactura, Producto.id == DetalleFactura.producto_id
            ).join(
                Factura, DetalleFactura.factura_id == Factura.id
            ).filter(
                extract('month', Factura.fecha) == mes,
                extract('year', Factura.fecha) == ano,
                Factura.estado == 'autorizada'
            ).group_by(
                Producto.id, Producto.codigo, Producto.nombre
            ).order_by(
                func.sum(DetalleFactura.cantidad).desc()
            ).limit(limite).all()
            
            productos = []
            for producto in top_productos:
                productos.append({
                    'codigo': producto.codigo,
                    'nombre': producto.nombre,
                    'cantidad_vendida': int(producto.cantidad_vendida) if producto.cantidad_vendida else 0,
                    'total_vendido': float(producto.total_vendido) if producto.total_vendido else 0.0
                })
            
            return jsonify({
                'success': True,
                'productos': productos,
                'nombre_mes': nombres_meses[mes] if 1 <= mes <= 12 else f'Mes {mes}'
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @estadisticas_bp.route('/api/ventas_diarias')
    def ventas_diarias():
        """Estadísticas de ventas por día (últimos 30 días)"""
        try:
            dias = request.args.get('dias', 30, type=int)
            fecha_inicio = datetime.now() - timedelta(days=dias-1)
            
            ventas_diarias = db.session.query(
                func.date(Factura.fecha).label('fecha'),
                func.count(Factura.id).label('cantidad_ventas'),
                func.sum(Factura.total).label('total_ventas')
            ).filter(
                Factura.fecha >= fecha_inicio,
                Factura.estado != 'cancelada'
            ).group_by(
                func.date(Factura.fecha)
            ).order_by('fecha').all()
            
            # Crear estructura completa de días
            datos_diarios = []
            ventas_dict = {str(v.fecha): v for v in ventas_diarias}
            
            for i in range(dias):
                fecha = (fecha_inicio + timedelta(days=i)).date()
                fecha_str = str(fecha)
                venta_dia = ventas_dict.get(fecha_str)
                
                datos_diarios.append({
                    'fecha': fecha_str,
                    'fecha_formateada': fecha.strftime('%d/%m'),
                    'dia_semana': fecha.strftime('%A'),
                    'cantidad_ventas': int(venta_dia.cantidad_ventas) if venta_dia else 0,
                    'total_ventas': float(venta_dia.total_ventas) if venta_dia else 0.0
                })
            
            return jsonify({
                'success': True,
                'datos_diarios': datos_diarios,
                'periodo': f'Últimos {dias} días'
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @estadisticas_bp.route('/api/resumen_dashboard')
    def resumen_dashboard():
        """Resumen general para el dashboard"""
        try:
            # Ventas de hoy
            hoy = datetime.now().date()
            ventas_hoy = db.session.query(
                func.count(Factura.id).label('cantidad'),
                func.sum(Factura.total).label('total')
            ).filter(
                func.date(Factura.fecha) == hoy,
                Factura.estado != 'cancelada'
            ).first()
            
            # Ventas del mes actual
            mes_actual = datetime.now().month
            ano_actual = datetime.now().year
            ventas_mes = db.session.query(
                func.count(Factura.id).label('cantidad'),
                func.sum(Factura.total).label('total')
            ).filter(
                extract('month', Factura.fecha) == mes_actual,
                extract('year', Factura.fecha) == ano_actual,
                Factura.estado != 'cancelada'
            ).first()
            
            # Top 5 productos del mes
            top_productos = db.session.query(
                Producto.nombre,
                func.sum(DetalleFactura.cantidad).label('cantidad_vendida')
            ).join(
                DetalleFactura, Producto.id == DetalleFactura.producto_id
            ).join(
                Factura, DetalleFactura.factura_id == Factura.id
            ).filter(
                extract('month', Factura.fecha) == mes_actual,
                extract('year', Factura.fecha) == ano_actual,
                Factura.estado != 'cancelada'
            ).group_by(
                Producto.id, Producto.nombre
            ).order_by(
                func.sum(DetalleFactura.cantidad).desc()
            ).limit(5).all()
            
            return jsonify({
                'success': True,
                'ventas_hoy': {
                    'cantidad': int(ventas_hoy.cantidad) if ventas_hoy.cantidad else 0,
                    'total': float(ventas_hoy.total) if ventas_hoy.total else 0.0
                },
                'ventas_mes': {
                    'cantidad': int(ventas_mes.cantidad) if ventas_mes.cantidad else 0,
                    'total': float(ventas_mes.total) if ventas_mes.total else 0.0
                },
                'top_productos': [
                    {
                        'nombre': p.nombre,
                        'cantidad': float(p.cantidad_vendida) if p.cantidad_vendida else 0.0
                    } for p in top_productos
                ]
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @estadisticas_bp.route('/api/reporte_medios_pago_completo')
    def reporte_medios_pago_completo():
        """Reporte completo de medios de pago con estadísticas detalladas"""
        try:
            fecha_desde = request.args.get('desde')
            fecha_hasta = request.args.get('hasta')
            
            if not fecha_desde or not fecha_hasta:
                return jsonify({
                    'success': False,
                    'error': 'Debe proporcionar fechas desde y hasta'
                }), 400
            
            # Convertir strings a datetime
            try:
                desde_dt = datetime.strptime(fecha_desde, '%Y-%m-%d')
                hasta_dt = datetime.strptime(fecha_hasta, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': 'Formato de fecha inválido. Use YYYY-MM-DD'
                }), 400
            
            # IMPORTAR MedioPago dinámicamente desde el contexto
            from flask import current_app
            MedioPago = current_app.config.get('MEDIO_PAGO_MODEL')
            
            # Si no está configurado, intentar importar directamente
            if not MedioPago:
                try:
                    from app import MedioPago
                except ImportError:
                    return jsonify({
                        'success': False,
                        'error': 'Modelo MedioPago no disponible'
                    }), 500
            
            # 1. ESTADÍSTICAS GENERALES
            estadisticas_generales = db.session.query(
                func.count(Factura.id).label('cantidad_tickets'),
                func.sum(Factura.total).label('total_general'),
                func.sum(Factura.subtotal).label('total_neto'),
                func.sum(Factura.iva).label('total_iva'),
                func.avg(Factura.total).label('ticket_promedio')
            ).filter(
                Factura.fecha >= desde_dt,
                Factura.fecha <= hasta_dt,
                Factura.estado != 'cancelada'
            ).first()
            
            # 2. IVA DISCRIMINADO POR ALÍCUOTA
            iva_discriminado = db.session.query(
                DetalleFactura.porcentaje_iva.label('alicuota'),
                func.sum(DetalleFactura.importe_iva).label('total_iva')
            ).join(
                Factura, DetalleFactura.factura_id == Factura.id
            ).filter(
                Factura.fecha >= desde_dt,
                Factura.fecha <= hasta_dt,
                Factura.estado != 'cancelada'
            ).group_by(
                DetalleFactura.porcentaje_iva
            ).order_by(
                DetalleFactura.porcentaje_iva
            ).all()
            
            # 3. MEDIOS DE PAGO
            medios_pago = db.session.query(
                MedioPago.medio_pago,
                func.count(MedioPago.id).label('cantidad'),
                func.sum(MedioPago.importe).label('total')
            ).join(
                Factura, MedioPago.factura_id == Factura.id
            ).filter(
                Factura.fecha >= desde_dt,
                Factura.fecha <= hasta_dt,
                Factura.estado != 'cancelada'
            ).group_by(
                MedioPago.medio_pago
            ).order_by(
                func.sum(MedioPago.importe).desc()
            ).all()
            
            # Formatear IVA discriminado
            iva_detalle = []
            for iva in iva_discriminado:
                if iva.alicuota and iva.total_iva:
                    iva_detalle.append({
                        'alicuota': float(iva.alicuota),
                        'total': round(float(iva.total_iva), 2)
                    })
            
            # Formatear medios de pago
            medios_pago_lista = []
            for medio in medios_pago:
                medios_pago_lista.append({
                    'medio_pago': medio.medio_pago,
                    'cantidad': int(medio.cantidad) if medio.cantidad else 0,
                    'total': round(float(medio.total), 2) if medio.total else 0.0,
                    'porcentaje': 0
                })
            
            # Calcular porcentajes
            total_general = float(estadisticas_generales.total_general or 0)
            if total_general > 0:
                for medio in medios_pago_lista:
                    medio['porcentaje'] = round((medio['total'] / total_general) * 100, 1)
            
            # Preparar respuesta
            return jsonify({
                'success': True,
                'periodo': {
                    'desde': fecha_desde,
                    'hasta': fecha_hasta,
                    'desde_formateado': desde_dt.strftime('%d/%m/%Y'),
                    'hasta_formateado': hasta_dt.strftime('%d/%m/%Y')
                },
                'estadisticas': {
                    'cantidad_tickets': int(estadisticas_generales.cantidad_tickets or 0),
                    'total_general': round(total_general, 2),
                    'total_neto': round(float(estadisticas_generales.total_neto or 0), 2),
                    'total_iva': round(float(estadisticas_generales.total_iva or 0), 2),
                    'ticket_promedio': round(float(estadisticas_generales.ticket_promedio or 0), 2)
                },
                'iva_discriminado': iva_detalle,
                'medios_pago': medios_pago_lista
            })
            
        except Exception as e:
            import traceback
            print(f"❌ Error en reporte_medios_pago_completo: {str(e)}")
            print(traceback.format_exc())
            return jsonify({
                'success': False,
                'error': f'Error interno: {str(e)}'
            }), 500
    
    @estadisticas_bp.route('/api/estadisticas_periodo')
    def estadisticas_periodo():
        """Estadísticas resumidas para cualquier período"""
        try:
            fecha_desde = request.args.get('desde')
            fecha_hasta = request.args.get('hasta')
            
            if not fecha_desde or not fecha_hasta:
                return jsonify({
                    'success': False,
                    'error': 'Debe proporcionar fechas desde y hasta'
                }), 400
            
            desde_dt = datetime.strptime(fecha_desde, '%Y-%m-%d')
            hasta_dt = datetime.strptime(fecha_hasta, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
            
            # Consulta rápida
            stats = db.session.query(
                func.count(Factura.id).label('tickets'),
                func.sum(Factura.total).label('total'),
                func.sum(Factura.subtotal).label('neto'),
                func.sum(Factura.iva).label('iva'),
                func.avg(Factura.total).label('promedio')
            ).filter(
                Factura.fecha >= desde_dt,
                Factura.fecha <= hasta_dt,
                Factura.estado != 'cancelada'
            ).first()
            
            return jsonify({
                'success': True,
                'tickets': int(stats.tickets or 0),
                'total': round(float(stats.total or 0), 2),
                'neto': round(float(stats.neto or 0), 2),
                'iva': round(float(stats.iva or 0), 2),
                'promedio': round(float(stats.promedio or 0), 2)
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @estadisticas_bp.route('/estadisticas/imprimir_estadisticas')
    @login_required
    def imprimir_estadisticas():
        """Genera vista para imprimir/exportar a PDF las estadísticas"""
        try:
            fecha_desde = request.args.get('desde')
            fecha_hasta = request.args.get('hasta')
            
            if not fecha_desde or not fecha_hasta:
                return "<h3>Error: Debe especificar rango de fechas</h3>", 400
            
            # Convertir fechas
            desde_dt = datetime.strptime(fecha_desde, '%Y-%m-%d')
            hasta_dt = datetime.strptime(fecha_hasta, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
            
            # Importar MedioPago
            from flask import current_app
            MedioPago = current_app.config.get('MEDIO_PAGO_MODEL')
            if not MedioPago:
                from app import MedioPago
            
            # 1. ESTADÍSTICAS GENERALES
            estadisticas_generales = db.session.query(
                func.count(Factura.id).label('cantidad_tickets'),
                func.sum(Factura.total).label('total_general'),
                func.sum(Factura.subtotal).label('total_neto'),
                func.sum(Factura.iva).label('total_iva'),
                func.avg(Factura.total).label('ticket_promedio')
            ).filter(
                Factura.fecha >= desde_dt,
                Factura.fecha <= hasta_dt,
                Factura.estado != 'cancelada'
            ).first()
            
            # 2. MEDIOS DE PAGO
            medios_pago = db.session.query(
                MedioPago.medio_pago,
                func.count(MedioPago.id).label('cantidad'),
                func.sum(MedioPago.importe).label('total')
            ).join(
                Factura, MedioPago.factura_id == Factura.id
            ).filter(
                Factura.fecha >= desde_dt,
                Factura.fecha <= hasta_dt,
                Factura.estado != 'cancelada'
            ).group_by(
                MedioPago.medio_pago
            ).order_by(
                func.sum(MedioPago.importe).desc()
            ).all()
            
            # 3. IVA DISCRIMINADO
            iva_discriminado = db.session.query(
                DetalleFactura.porcentaje_iva.label('alicuota'),
                func.sum(DetalleFactura.importe_iva).label('total_iva')
            ).join(
                Factura, DetalleFactura.factura_id == Factura.id
            ).filter(
                Factura.fecha >= desde_dt,
                Factura.fecha <= hasta_dt,
                Factura.estado != 'cancelada'
            ).group_by(
                DetalleFactura.porcentaje_iva
            ).order_by(
                DetalleFactura.porcentaje_iva
            ).all()
            
            # 4. TOP 10 PRODUCTOS
            top_productos = db.session.query(
                Producto.codigo,
                Producto.nombre,
                func.sum(DetalleFactura.cantidad).label('cantidad_vendida'),
                func.sum(DetalleFactura.subtotal).label('total_vendido')
            ).join(
                DetalleFactura, Producto.id == DetalleFactura.producto_id
            ).join(
                Factura, DetalleFactura.factura_id == Factura.id
            ).filter(
                Factura.fecha >= desde_dt,
                Factura.fecha <= hasta_dt,
                Factura.estado != 'cancelada'
            ).group_by(
                Producto.id, Producto.codigo, Producto.nombre
            ).order_by(
                func.sum(DetalleFactura.cantidad).desc()
            ).limit(10).all()
            
            # Formatear datos
            total_general = float(estadisticas_generales.total_general or 0)
            
            medios_pago_lista = []
            for medio in medios_pago:
                medio_total = float(medio.total) if medio.total else 0.0
                medios_pago_lista.append({
                    'medio': medio.medio_pago,
                    'cantidad': int(medio.cantidad) if medio.cantidad else 0,
                    'total': medio_total,
                    'porcentaje': round((medio_total / total_general * 100), 1) if total_general > 0 else 0
                })
            
            iva_lista = []
            for iva in iva_discriminado:
                if iva.alicuota and iva.total_iva:
                    iva_lista.append({
                        'alicuota': float(iva.alicuota),
                        'total': float(iva.total_iva)
                    })
            
            productos_lista = []
            for prod in top_productos:
                productos_lista.append({
                    'codigo': prod.codigo,
                    'nombre': prod.nombre,
                    'cantidad': float(prod.cantidad_vendida) if prod.cantidad_vendida else 0.0,
                    'total': float(prod.total_vendido) if prod.total_vendido else 0.0
                })
            
            # Generar HTML
            html = f"""
            <!DOCTYPE html>
            <html lang="es">
            <head>
                <meta charset="UTF-8">
                <title>Reporte de Estadísticas - {fecha_desde} al {fecha_hasta}</title>
                <style>
                    @media print {{
                        @page {{ margin: 1cm; }}
                        body {{ margin: 0; }}
                    }}
                    
                    body {{
                        font-family: 'Arial', sans-serif;
                        margin: 20px;
                        color: #333;
                        background: #f5f5f5;
                    }}
                    
                    .container {{
                        max-width: 1200px;
                        margin: 0 auto;
                        background: white;
                        padding: 30px;
                        box-shadow: 0 0 10px rgba(0,0,0,0.1);
                    }}
                    
                    h1 {{
                        color: #2c3e50;
                        border-bottom: 3px solid #3498db;
                        padding-bottom: 10px;
                        margin-bottom: 20px;
                    }}
                    
                    .header {{
                        margin-bottom: 30px;
                    }}
                    
                    .header-row {{
                        display: flex;
                        justify-content: space-between;
                        margin-bottom: 15px;
                        padding: 15px;
                        background: #ecf0f1;
                        border-radius: 5px;
                    }}
                    
                    .header-item {{
                        text-align: center;
                        flex: 1;
                    }}
                    
                    .header-label {{
                        font-size: 12px;
                        color: #7f8c8d;
                        text-transform: uppercase;
                    }}
                    
                    .header-value {{
                        font-size: 24px;
                        font-weight: bold;
                        color: #2c3e50;
                        margin-top: 5px;
                    }}
                    
                    .section {{
                        margin-bottom: 30px;
                        page-break-inside: avoid;
                    }}
                    
                    h2 {{
                        color: #34495e;
                        background: #3498db;
                        color: white;
                        padding: 10px 15px;
                        border-radius: 5px;
                        margin-bottom: 15px;
                    }}
                    
                    table {{
                        width: 100%;
                        border-collapse: collapse;
                        margin-bottom: 20px;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    }}
                    
                    th {{
                        background: #34495e;
                        color: white;
                        padding: 12px;
                        text-align: left;
                        font-weight: bold;
                    }}
                    
                    td {{
                        padding: 10px 12px;
                        border-bottom: 1px solid #ecf0f1;
                    }}
                    
                    tr:hover {{
                        background: #f8f9fa;
                    }}
                    
                    .text-right {{
                        text-align: right;
                    }}
                    
                    .text-center {{
                        text-align: center;
                    }}
                    
                    .total-row {{
                        font-weight: bold;
                        background: #f1c40f !important;
                        color: #2c3e50;
                    }}
                    
                    .footer {{
                        margin-top: 40px;
                        padding-top: 20px;
                        border-top: 2px solid #bdc3c7;
                        text-align: center;
                        color: #7f8c8d;
                        font-size: 12px;
                    }}
                    
                    .print-button {{
                        position: fixed;
                        top: 20px;
                        right: 20px;
                        background: #27ae60;
                        color: white;
                        padding: 15px 30px;
                        border: none;
                        border-radius: 5px;
                        cursor: pointer;
                        font-size: 16px;
                        box-shadow: 0 4px 6px rgba(0,0,0,0.2);
                        z-index: 1000;
                    }}
                    
                    .print-button:hover {{
                        background: #229954;
                    }}
                    
                    @media print {{
                        .print-button {{
                            display: none;
                        }}
                        body {{
                            background: white;
                        }}
                        .container {{
                            box-shadow: none;
                        }}
                    }}
                    
                    .badge {{
                        display: inline-block;
                        padding: 4px 8px;
                        border-radius: 3px;
                        font-size: 12px;
                        font-weight: bold;
                    }}
                    
                    .badge-efectivo {{ background: #2ecc71; color: white; }}
                    .badge-credito {{ background: #3498db; color: white; }}
                    .badge-debito {{ background: #9b59b6; color: white; }}
                    .badge-mercado_pago {{ background: #f1c40f; color: #2c3e50; }}
                </style>
            </head>
            <body>
                <button class="print-button" onclick="window.print()">🖨️ Imprimir / Guardar PDF</button>
                
                <div class="container">
                    <h1>📊 Reporte de Estadísticas de Ventas</h1>
                    
                    <div class="header">
                        <!-- Primera fila: Período y Total Ventas -->
                        <div class="header-row">
                            <div class="header-item">
                                <div class="header-label">Período</div>
                                <div class="header-value">{desde_dt.strftime('%d/%m/%Y')} - {hasta_dt.strftime('%d/%m/%Y')}</div>
                            </div>
                            <div class="header-item">
                                <div class="header-label">Total Ventas</div>
                                <div class="header-value">${total_general:,.2f}</div>
                            </div>
                        </div>
                        
                        <!-- Segunda fila: Total Tickets y Ticket Promedio -->
                        <div class="header-row">
                            <div class="header-item">
                                <div class="header-label">Total Tickets</div>
                                <div class="header-value">{int(estadisticas_generales.cantidad_tickets or 0)}</div>
                            </div>
                            <div class="header-item">
                                <div class="header-label">Ticket Promedio</div>
                                <div class="header-value">${float(estadisticas_generales.ticket_promedio or 0):,.2f}</div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- MEDIOS DE PAGO -->
                    <div class="section">
                        <h2>💳 Medios de Pago</h2>
                        <table>
                            <thead>
                                <tr>
                                    <th>Medio de Pago</th>
                                    <th class="text-center">Cantidad</th>
                                    <th class="text-right">Total</th>
                                    <th class="text-right">Porcentaje</th>
                                </tr>
                            </thead>
                            <tbody>
            """
            
            for medio in medios_pago_lista:
                badge_class = f"badge badge-{medio['medio']}"
                html += f"""
                                <tr>
                                    <td><span class="{badge_class}">{medio['medio'].upper()}</span></td>
                                    <td class="text-center">{medio['cantidad']}</td>
                                    <td class="text-right">${medio['total']:,.2f}</td>
                                    <td class="text-right">{medio['porcentaje']}%</td>
                                </tr>
                """
            
            html += f"""
                                <tr class="total-row">
                                    <td><strong>TOTAL</strong></td>
                                    <td class="text-center"><strong>{sum(m['cantidad'] for m in medios_pago_lista)}</strong></td>
                                    <td class="text-right"><strong>${total_general:,.2f}</strong></td>
                                    <td class="text-right"><strong>100%</strong></td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                    
                    <!-- IVA DISCRIMINADO -->
                    <div class="section">
                        <h2>📋 IVA Discriminado</h2>
                        <table>
                            <thead>
                                <tr>
                                    <th>Alícuota</th>
                                    <th class="text-right">Total IVA</th>
                                </tr>
                            </thead>
                            <tbody>
            """
            
            total_iva = 0
            for iva in iva_lista:
                total_iva += iva['total']
                html += f"""
                                <tr>
                                    <td>IVA {iva['alicuota']}%</td>
                                    <td class="text-right">${iva['total']:,.2f}</td>
                                </tr>
                """
            
            html += f"""
                                <tr class="total-row">
                                    <td><strong>TOTAL IVA</strong></td>
                                    <td class="text-right"><strong>${total_iva:,.2f}</strong></td>
                                </tr>
                                <tr>
                                    <td><strong>NETO (sin IVA)</strong></td>
                                    <td class="text-right"><strong>${float(estadisticas_generales.total_neto or 0):,.2f}</strong></td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                    
                    <!-- TOP 10 PRODUCTOS -->
                    <div class="section">
                        <h2>🏆 Top 10 Productos Más Vendidos</h2>
                        <table>
                            <thead>
                                <tr>
                                    <th>Código</th>
                                    <th>Producto</th>
                                    <th class="text-right">Cantidad</th>
                                    <th class="text-right">Total Vendido</th>
                                </tr>
                            </thead>
                            <tbody>
            """
            
            for i, prod in enumerate(productos_lista, 1):
                html += f"""
                                <tr>
                                    <td><strong>#{i}</strong> {prod['codigo']}</td>
                                    <td>{prod['nombre']}</td>
                                    <td class="text-right">{prod['cantidad']:,.0f}</td>
                                    <td class="text-right">${prod['total']:,.2f}</td>
                                </tr>
                """
            
            html += f"""
                            </tbody>
                        </table>
                    </div>
                    
                    <div class="footer">
                        <p><strong>Reporte generado el:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
                        <p>Sistema de Punto de Venta - FactuFacil</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            return html
            
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            return f"""
            <h3>Error generando reporte</h3>
            <p>{str(e)}</p>
            <pre>{error_detail}</pre>
            """, 500

    @estadisticas_bp.route('/api/margen_productos')
    @login_required
    def margen_productos():
        """Margen de ganancia por producto en un período"""
        try:
            fecha_desde = request.args.get('desde')
            fecha_hasta = request.args.get('hasta')
            categoria   = request.args.get('categoria', '')
            orden       = request.args.get('orden', 'ganancia_desc')
            limite      = request.args.get('limite', 0, type=int)  # 0 = todos

            if not fecha_desde or not fecha_hasta:
                return jsonify({'success': False, 'error': 'Debe proporcionar fechas desde y hasta'}), 400

            desde_dt = datetime.strptime(fecha_desde, '%Y-%m-%d')
            hasta_dt = datetime.strptime(fecha_hasta, '%Y-%m-%d').replace(hour=23, minute=59, second=59)

            query = db.session.query(
                Producto.codigo,
                Producto.nombre,
                Producto.categoria,
                func.sum(DetalleFactura.cantidad).label('unidades'),
                # ═══ CAUSA RAÍZ CONFIRMADA CON DATOS DE LA BASE:
                # DetalleFactura.precio_unitario se guarda SIN IVA (verificado:
                # 5 ventas de cód 100012 = 8767.56 = precio lista 10608.75 / 1.21).
                # Producto.costo se guarda CON IVA (confirmado con el negocio).
                # Para un margen real hay que comparar mismo criterio: se deja
                # el ingreso tal cual (ya neto) y se pasa el costo a NETO.
                # Resultado verificado: BARRA CASTELMAR da 20% (markup 25%).
                func.sum(
                    DetalleFactura.cantidad * DetalleFactura.precio_unitario
                ).label('ingresos'),
                func.sum(
                    DetalleFactura.cantidad * func.coalesce(
                        # Costo histórico de la venta (se guarda con IVA, como
                        # Producto.costo) → pasar a NETO con el IVA de la línea.
                        func.nullif(DetalleFactura.costo_unitario, 0)
                            / (1 + func.coalesce(func.nullif(DetalleFactura.porcentaje_iva, 0), 21) / 100),
                        # Fallback: costo actual del producto (con IVA) → a NETO.
                        Producto.costo / (1 + func.coalesce(func.nullif(Producto.iva, 0), 21) / 100)
                    )
                ).label('costo_total'),
            ).join(
                DetalleFactura, Producto.id == DetalleFactura.producto_id
            ).join(
                Factura, DetalleFactura.factura_id == Factura.id
            ).filter(
                Factura.fecha >= desde_dt,
                Factura.fecha <= hasta_dt,
                Factura.estado != 'cancelada',
                Producto.costo != None,
                Producto.costo > 0,
                Producto.es_combo == False,
            )

            if categoria:
                query = query.filter(Producto.categoria == categoria)

            resultados = query.group_by(
                Producto.id, Producto.codigo, Producto.nombre, Producto.categoria
            ).all()

            productos = []
            for r in resultados:
                ingresos    = float(r.ingresos    or 0)
                unidades    = float(r.unidades    or 0)
                costo_total = float(r.costo_total or 0)
                ganancia    = ingresos - costo_total
                margen_pct  = round((ganancia / ingresos * 100), 1) if ingresos > 0 else 0.0
                productos.append({
                    'codigo':      r.codigo,
                    'nombre':      r.nombre,
                    'categoria':   r.categoria or '',
                    'costo_unit':  round(costo_total / unidades, 2) if unidades > 0 else 0,
                    'unidades':    round(unidades, 2),
                    'ingresos':    round(ingresos, 2),
                    'costo_total': round(costo_total, 2),
                    'ganancia':    round(ganancia, 2),
                    'margen_pct':  margen_pct,
                })

            # Ordenar
            ordenes = {
                'ganancia_desc':  lambda x: -x['ganancia'],
                'ganancia_asc':   lambda x:  x['ganancia'],
                'margen_desc':    lambda x: -x['margen_pct'],
                'margen_asc':     lambda x:  x['margen_pct'],
                'ingresos_desc':  lambda x: -x['ingresos'],
                'nombre':         lambda x:  x['nombre'],
            }
            productos.sort(key=ordenes.get(orden, ordenes['ganancia_desc']))

            if limite > 0:
                productos = productos[:limite]

            # Totales
            total_ingresos    = sum(p['ingresos']    for p in productos)
            total_costo       = sum(p['costo_total'] for p in productos)
            total_ganancia    = sum(p['ganancia']     for p in productos)
            margen_gral       = round((total_ganancia / total_ingresos * 100), 1) if total_ingresos > 0 else 0

            return jsonify({
                'success':  True,
                'productos': productos,
                'totales': {
                    'ingresos':  round(total_ingresos, 2),
                    'costo':     round(total_costo, 2),
                    'ganancia':  round(total_ganancia, 2),
                    'margen':    margen_gral,
                    'cantidad':  len(productos),
                }
            })

        except Exception as e:
            import traceback
            print(traceback.format_exc())
            return jsonify({'success': False, 'error': str(e)}), 500


    @estadisticas_bp.route('/api/problemas_costos')
    @login_required
    def api_problemas_costos():
        desde = request.args.get('desde')
        hasta = request.args.get('hasta')
        if not desde or not hasta:
            return jsonify({'success': False, 'error': 'Faltan fechas'}), 400

        try:
            # 1. Productos SIN costo que se vendieron en el período
            sin_costo = db.session.execute(text("""
                SELECT p.codigo, p.nombre, p.categoria, p.precio,
                       COALESCE(SUM(df.cantidad), 0) AS unidades
                FROM producto p
                JOIN detalle_factura df ON df.producto_id = p.id
                JOIN factura f ON f.id = df.factura_id
                WHERE f.fecha BETWEEN :desde AND :hasta
                  AND f.estado != 'cancelada'
                  AND p.es_combo = 0
                  AND (p.costo IS NULL OR p.costo = 0)
                GROUP BY p.id
            """), {'desde': desde, 'hasta': hasta}).fetchall()

            # 2. Productos con costo > precio de venta actual
            costo_mayor = db.session.execute(text("""
                SELECT p.codigo, p.nombre, p.precio, p.costo
                FROM producto p
                WHERE p.activo = 1 AND p.es_combo = 0
                  AND p.costo > p.precio AND p.costo > 0
            """)).fetchall()

            # 3. Vendidos a pérdida en el período (margen negativo real)
            perdida = db.session.execute(text("""
                SELECT p.codigo, p.nombre,
                       SUM(df.cantidad * df.precio_unitario) AS ingresos,
                       SUM(df.cantidad * p.costo)            AS costo_total
                FROM producto p
                JOIN detalle_factura df ON df.producto_id = p.id
                JOIN factura f ON f.id = df.factura_id
                WHERE f.fecha BETWEEN :desde AND :hasta
                  AND f.estado != 'cancelada'
                  AND p.es_combo = 0 AND p.costo > 0
                GROUP BY p.id
                HAVING ingresos < costo_total
            """), {'desde': desde, 'hasta': hasta}).fetchall()

            # 4. Margen > 80% (posible costo mal cargado)
            margen_alto = db.session.execute(text("""
                SELECT p.codigo, p.nombre, p.precio, p.costo,
                       ((p.precio - p.costo) / p.precio * 100) AS margen_pct
                FROM producto p
                WHERE p.activo = 1 AND p.es_combo = 0
                  AND p.costo > 0 AND p.precio > 0
                  AND ((p.precio - p.costo) / p.precio * 100) > 80
            """)).fetchall()

            def row(r): return {k: (float(v) if isinstance(v, Decimal) else v)
                                for k, v in r._mapping.items()}

            perdida_list = [r for r in [row(r) for r in perdida]]
            for p in perdida_list:
                p['margen_pct'] = (p['ingresos'] - p['costo_total']) / p['ingresos'] * 100 if p['ingresos'] else 0

            return jsonify({
                'success': True,
                'sin_costo':          [row(r) for r in sin_costo],
                'costo_mayor_precio': [row(r) for r in costo_mayor],
                'perdida':            perdida_list,
                'margen_alto':        [row(r) for r in margen_alto],
            })

        except Exception as e:
            import traceback; print(traceback.format_exc())
            return jsonify({'success': False, 'error': str(e)}), 500


    @estadisticas_bp.route('/margen_productos')
    @login_required
    def vista_margen_productos():
        """Vista del reporte de margen por producto"""
        from flask import current_app
        # Obtener categorías únicas para el filtro
        try:
            categorias = db.session.query(Producto.categoria).filter(
                Producto.activo == True,
                Producto.categoria != None,
                Producto.es_combo == False,
            ).distinct().order_by(Producto.categoria).all()
            categorias = [c[0] for c in categorias if c[0]]
        except Exception:
            categorias = []
        return render_template('margen_productos.html', categorias=categorias)

    # ──────────────────────────────────────────────────────────
    # VENTAS POR DÍA DE LA SEMANA
    # ──────────────────────────────────────────────────────────
    @estadisticas_bp.route('/api/ventas_por_dia_semana')
    @login_required
    def ventas_por_dia_semana():
        try:
            fecha_desde = request.args.get('desde')
            fecha_hasta = request.args.get('hasta')
            ano         = request.args.get('ano', datetime.now().year, type=int)

            if fecha_desde and fecha_hasta:
                desde_dt = datetime.strptime(fecha_desde, '%Y-%m-%d')
                hasta_dt = datetime.strptime(fecha_hasta, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
            else:
                desde_dt = datetime(ano, 1, 1)
                hasta_dt = datetime(ano, 12, 31, 23, 59, 59)

            resultados = db.session.query(
                func.dayofweek(Factura.fecha).label('dow'),
                func.count(Factura.id).label('cantidad'),
                func.sum(Factura.total).label('total'),
                func.avg(Factura.total).label('promedio'),
            ).filter(
                Factura.fecha >= desde_dt,
                Factura.fecha <= hasta_dt,
                Factura.estado == 'autorizada',
            ).group_by(func.dayofweek(Factura.fecha)).all()

            nombres = ['Domingo', 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado']
            datos   = {r.dow: r for r in resultados}

            dias = []
            for i, nombre in enumerate(nombres):
                dow = i + 1
                r   = datos.get(dow)
                dias.append({
                    'dia':      nombre,
                    'cantidad': int(r.cantidad)  if r else 0,
                    'total':    float(r.total)   if r else 0.0,
                    'promedio': float(r.promedio) if r else 0.0,
                })

            dias = dias[1:] + [dias[0]]  # Lun primero

            total_gral = sum(d['total'] for d in dias)
            for d in dias:
                d['porcentaje'] = round((d['total'] / total_gral * 100), 1) if total_gral > 0 else 0

            return jsonify({'success': True, 'dias': dias})

        except Exception as e:
            import traceback; print(traceback.format_exc())
            return jsonify({'success': False, 'error': str(e)}), 500

    # ──────────────────────────────────────────────────────────
    # PRODUCTOS SIN MOVIMIENTO
    # ──────────────────────────────────────────────────────────
    @estadisticas_bp.route('/api/productos_sin_movimiento')
    @login_required
    def productos_sin_movimiento():
        try:
            dias      = request.args.get('dias', 30, type=int)
            categoria = request.args.get('categoria', '')
            desde_dt  = datetime.now() - timedelta(days=dias)

            ids_con_venta = db.session.query(
                DetalleFactura.producto_id
            ).join(
                Factura, DetalleFactura.factura_id == Factura.id
            ).filter(
                Factura.fecha >= desde_dt,
                Factura.estado != 'cancelada',
            ).distinct().subquery()

            query = db.session.query(Producto).filter(
                Producto.activo == True,
                Producto.es_combo == False,
                ~Producto.id.in_(ids_con_venta),
            )
            if categoria:
                query = query.filter(Producto.categoria == categoria)

            productos = query.order_by(Producto.categoria, Producto.nombre).all()

            return jsonify({
                'success':   True,
                'dias':      dias,
                'productos': [{
                    'codigo':    p.codigo,
                    'nombre':    p.nombre,
                    'categoria': p.categoria or '-',
                    'stock':     float(p.stock) if p.stock else 0,
                    'precio':    float(p.precio) if p.precio else 0,
                } for p in productos],
                'cantidad': len(productos),
            })

        except Exception as e:
            import traceback; print(traceback.format_exc())
            return jsonify({'success': False, 'error': str(e)}), 500

    # ──────────────────────────────────────────────────────────
    # VENTAS POR TIPO DE COMPROBANTE
    # ──────────────────────────────────────────────────────────
    @estadisticas_bp.route('/api/ventas_por_comprobante')
    @login_required
    def ventas_por_comprobante():
        try:
            fecha_desde = request.args.get('desde')
            fecha_hasta = request.args.get('hasta')
            ano         = request.args.get('ano', datetime.now().year, type=int)

            if fecha_desde and fecha_hasta:
                desde_dt = datetime.strptime(fecha_desde, '%Y-%m-%d')
                hasta_dt = datetime.strptime(fecha_hasta, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
            else:
                desde_dt = datetime(ano, 1, 1)
                hasta_dt = datetime(ano, 12, 31, 23, 59, 59)

            resultados = db.session.query(
                Factura.tipo_comprobante,
                func.count(Factura.id).label('cantidad'),
                func.sum(Factura.total).label('total'),
                func.avg(Factura.total).label('promedio'),
            ).filter(
                Factura.fecha >= desde_dt,
                Factura.fecha <= hasta_dt,
                Factura.estado == 'autorizada',
            ).group_by(Factura.tipo_comprobante).order_by(Factura.tipo_comprobante).all()

            nombres = {
                1: 'Factura A', 2: 'Nota Débito A', 3: 'Nota Crédito A',
                6: 'Factura B', 7: 'Nota Débito B', 8: 'Nota Crédito B',
                11: 'Factura C', 12: 'Nota Débito C', 13: 'Nota Crédito C',
            }

            total_gral = sum(float(r.total or 0) for r in resultados)
            tipos = []
            for r in resultados:
                total = float(r.total or 0)
                tipos.append({
                    'tipo':       r.tipo_comprobante,
                    'nombre':     nombres.get(int(r.tipo_comprobante), f'Tipo {r.tipo_comprobante}'),
                    'cantidad':   int(r.cantidad),
                    'total':      round(total, 2),
                    'promedio':   round(float(r.promedio or 0), 2),
                    'porcentaje': round((total / total_gral * 100), 1) if total_gral > 0 else 0,
                })

            return jsonify({'success': True, 'tipos': tipos, 'total_general': round(total_gral, 2)})

        except Exception as e:
            import traceback; print(traceback.format_exc())
            return jsonify({'success': False, 'error': str(e)}), 500

    # ──────────────────────────────────────────────────────────
    # TICKET PROMEDIO MENSUAL (TENDENCIA)
    # ──────────────────────────────────────────────────────────
    @estadisticas_bp.route('/api/ticket_promedio_tendencia')
    @login_required
    def ticket_promedio_tendencia():
        try:
            ano = request.args.get('ano', datetime.now().year, type=int)

            resultados = db.session.query(
                extract('month', Factura.fecha).label('mes'),
                func.count(Factura.id).label('cantidad'),
                func.sum(Factura.total).label('total'),
                func.avg(Factura.total).label('promedio'),
                func.max(Factura.total).label('maximo'),
                func.min(Factura.total).label('minimo'),
            ).filter(
                extract('year', Factura.fecha) == ano,
                Factura.estado != 'cancelada',
            ).group_by(extract('month', Factura.fecha)).order_by('mes').all()

            MESES_CORTO = ['','Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic']
            MESES_LARGO = ['','Enero','Febrero','Marzo','Abril','Mayo','Junio',
                           'Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre']

            datos = {int(r.mes): r for r in resultados}
            meses = []
            for mes in range(1, 13):
                r = datos.get(mes)
                meses.append({
                    'mes':          mes,
                    'nombre':       MESES_CORTO[mes],
                    'nombre_largo': MESES_LARGO[mes],
                    'cantidad':     int(r.cantidad)  if r else 0,
                    'total':        float(r.total)   if r else 0.0,
                    'promedio':     round(float(r.promedio) if r else 0.0, 2),
                    'maximo':       round(float(r.maximo)  if r else 0.0, 2),
                    'minimo':       round(float(r.minimo)  if r else 0.0, 2),
                })

            promedios_con_datos = [m['promedio'] for m in meses if m['cantidad'] > 0]
            promedio_anual      = round(sum(promedios_con_datos) / len(promedios_con_datos), 2) if promedios_con_datos else 0

            return jsonify({
                'success':        True,
                'ano':            ano,
                'meses':          meses,
                'promedio_anual': promedio_anual,
            })

        except Exception as e:
            import traceback; print(traceback.format_exc())
            return jsonify({'success': False, 'error': str(e)}), 500

    # ──────────────────────────────────────────────────────────
    # VISTA UNIFICADA — ANÁLISIS AVANZADO
    # ──────────────────────────────────────────────────────────
    @estadisticas_bp.route('/analisis_avanzado')
    @login_required
    def vista_analisis_avanzado():
        try:
            categorias = db.session.query(Producto.categoria).filter(
                Producto.activo == True,
                Producto.categoria != None,
                Producto.es_combo == False,
            ).distinct().order_by(Producto.categoria).all()
            categorias = [c[0] for c in categorias if c[0]]
        except Exception:
            categorias = []
        return render_template('analisis_avanzado.html', categorias=categorias)


    @estadisticas_bp.route('/api/evolucion_margen')
    @login_required
    def api_evolucion_margen():
        try:
            meses = int(request.args.get('meses', 12))
            rows = db.session.execute(text("""
                SELECT 
                    DATE_FORMAT(f.fecha, '%Y-%m') as mes,
                    DATE_FORMAT(f.fecha, '%b %Y') as mes_label,
                    SUM(df.cantidad * df.precio_unitario) as ingresos,
                    SUM(df.cantidad * p.costo) as costos
                FROM factura f
                JOIN detalle_factura df ON df.factura_id = f.id
                JOIN producto p ON p.id = df.producto_id
                WHERE f.estado != 'cancelada'
                  AND p.costo > 0
                  AND f.fecha >= DATE_SUB(CURDATE(), INTERVAL :meses MONTH)
                GROUP BY mes, mes_label
                ORDER BY mes ASC
            """), {'meses': meses}).fetchall()

            resultado = []
            for r in rows:
                ingresos = float(r.ingresos or 0)
                costos = float(r.costos or 0)
                ganancia = ingresos - costos
                margen = round((ganancia / ingresos * 100), 1) if ingresos > 0 else 0
                resultado.append({
                    'mes': r.mes,
                    'label': r.mes_label,
                    'ingresos': round(ingresos, 2),
                    'costos': round(costos, 2),
                    'ganancia': round(ganancia, 2),
                    'margen': margen
                })
            return jsonify({'success': True, 'datos': resultado})
        except Exception as e:
            import traceback; traceback.print_exc()
            return jsonify({'success': False, 'error': str(e)}), 500

    @estadisticas_bp.route('/api/ranking_clientes')
    @login_required
    def api_ranking_clientes():
        try:
            desde = request.args.get('desde', '')
            hasta = request.args.get('hasta', '')
            limit = int(request.args.get('limit', 15))

            filtro = "f.estado != 'cancelada'"
            params = {'limit': limit}
            if desde:
                filtro += " AND f.fecha >= :desde"
                params['desde'] = desde
            if hasta:
                filtro += " AND f.fecha <= :hasta"
                params['hasta'] = hasta

            rows = db.session.execute(text(f"""
                SELECT 
                    c.id, c.nombre,
                    COUNT(f.id) as num_facturas,
                    SUM(f.total) as total_facturado,
                    AVG(f.total) as ticket_promedio
                FROM factura f
                JOIN cliente c ON c.id = f.cliente_id
                WHERE {filtro} AND c.id != 1
                GROUP BY c.id, c.nombre
                ORDER BY total_facturado DESC
                LIMIT :limit
            """), params).fetchall()

            resultado = [{
                'id': r.id,
                'nombre': r.nombre,
                'facturas': r.num_facturas,
                'total': round(float(r.total_facturado or 0), 2),
                'ticket_promedio': round(float(r.ticket_promedio or 0), 2)
            } for r in rows]

            return jsonify({'success': True, 'clientes': resultado})
        except Exception as e:
            import traceback; traceback.print_exc()
            return jsonify({'success': False, 'error': str(e)}), 500

    @estadisticas_bp.route('/api/ventas_por_lista')
    @login_required
    def api_ventas_por_lista():
        try:
            desde = request.args.get('desde', '')
            hasta = request.args.get('hasta', '')

            filtro = "f.estado != 'cancelada'"
            params = {}
            if desde:
                filtro += " AND f.fecha >= :desde"
                params['desde'] = desde
            if hasta:
                filtro += " AND f.fecha <= :hasta"
                params['hasta'] = hasta

            rows = db.session.execute(text(f"""
                SELECT 
                    COALESCE(c.lista_precio, 1) as lista,
                    COUNT(DISTINCT f.id) as num_facturas,
                    SUM(f.total) as total,
                    COUNT(DISTINCT f.cliente_id) as clientes_distintos
                FROM factura f
                JOIN cliente c ON c.id = f.cliente_id
                WHERE {filtro}
                GROUP BY lista
                ORDER BY lista ASC
            """), params).fetchall()

            nombres = {1: 'Minorista', 2: 'Mayorista', 3: 'Distribuidor', 4: 'Especial', 5: 'Promocional'}
            colores = {1: '#0d6efd', 2: '#198754', 3: '#0dcaf0', 4: '#ffc107', 5: '#dc3545'}

            resultado = [{
                'lista': r.lista,
                'nombre': nombres.get(r.lista, f'Lista {r.lista}'),
                'color': colores.get(r.lista, '#6c757d'),
                'facturas': r.num_facturas,
                'total': round(float(r.total or 0), 2),
                'clientes': r.clientes_distintos
            } for r in rows]

            return jsonify({'success': True, 'listas': resultado})
        except Exception as e:
            import traceback; traceback.print_exc()
            return jsonify({'success': False, 'error': str(e)}), 500

    # ================================================================
    # REPORTE IVA VENTAS
    # ================================================================

    @estadisticas_bp.route('/iva_ventas')
    @login_required
    def vista_iva_ventas():
        return render_template('iva_ventas.html')

    @estadisticas_bp.route('/api/iva_ventas')
    @login_required
    def api_iva_ventas():
        """Libro IVA Ventas con discriminación por alícuota"""
        try:
            fecha_desde = request.args.get('desde')
            fecha_hasta = request.args.get('hasta')
            tipo_filtro = request.args.get('tipo_comprobante')  # 'A', 'B', 'C' o vacío = todos

            if not fecha_desde or not fecha_hasta:
                return jsonify({'success': False, 'error': 'Debe proporcionar fechas desde y hasta'}), 400

            desde_dt = datetime.strptime(fecha_desde, '%Y-%m-%d')
            hasta_dt = datetime.strptime(fecha_hasta, '%Y-%m-%d').replace(hour=23, minute=59, second=59)

            # Mapeo de tipo (A/B/C) a códigos internos de ARCA.
            # Se incluyen Factura y Nota de Crédito del mismo grupo:
            #   A → 01 (Factura A) + 03 (NC A)
            #   B → 06 (Factura B) + 08 (NC B)
            #   C → 11 (Factura C) + 13 (NC C)
            TIPOS_MAP = {
                'A': ('01', '03'),
                'B': ('06', '08'),
                'C': ('11', '13'),
            }
            codigos_filtrar = None
            if tipo_filtro and tipo_filtro.upper() in TIPOS_MAP:
                codigos_filtrar = TIPOS_MAP[tipo_filtro.upper()]

            # Traer facturas con datos de cliente
            q_facturas = db.session.query(
                Factura.id,
                Factura.numero,
                Factura.tipo_comprobante,
                Factura.punto_venta,
                Factura.fecha,
                Factura.subtotal,
                Factura.iva,
                Factura.total,
                Factura.cae,
                Factura.estado,
                Cliente.nombre.label('cliente_nombre'),
                Cliente.documento.label('cliente_cuit'),
                Cliente.tipo_documento.label('tipo_doc'),
                Cliente.condicion_iva.label('condicion_iva'),
            ).outerjoin(
                Cliente, Factura.cliente_id == Cliente.id
            ).filter(
                Factura.fecha >= desde_dt,
                Factura.fecha <= hasta_dt,
                Factura.estado == 'autorizada',
            )
            if codigos_filtrar:
                q_facturas = q_facturas.filter(Factura.tipo_comprobante.in_(codigos_filtrar))

            facturas = q_facturas.order_by(Factura.fecha.asc(), Factura.id.asc()).all()

            # IVA discriminado por alícuota para cada factura
            iva_por_factura = {}
            q_detalles = db.session.query(
                DetalleFactura.factura_id,
                DetalleFactura.porcentaje_iva,
                func.sum(DetalleFactura.subtotal).label('neto'),
                func.sum(DetalleFactura.importe_iva).label('iva'),
            ).join(
                Factura, DetalleFactura.factura_id == Factura.id
            ).filter(
                Factura.fecha >= desde_dt,
                Factura.fecha <= hasta_dt,
                Factura.estado == 'autorizada',
            )
            if codigos_filtrar:
                q_detalles = q_detalles.filter(Factura.tipo_comprobante.in_(codigos_filtrar))

            detalles_iva = q_detalles.group_by(
                DetalleFactura.factura_id,
                DetalleFactura.porcentaje_iva,
            ).all()

            for d in detalles_iva:
                if d.factura_id not in iva_por_factura:
                    iva_por_factura[d.factura_id] = {}
                alicuota = str(int(float(d.porcentaje_iva or 0)))
                iva_por_factura[d.factura_id][alicuota] = {
                    'neto': round(float(d.neto or 0), 2),
                    'iva':  round(float(d.iva  or 0), 2),
                }

            # Armar lista de comprobantes
            comprobantes = []
            total_neto     = 0
            total_iva_21   = 0
            total_iva_105  = 0
            total_iva_otro = 0
            total_general  = 0

            # Subtotales por grupo A/B/C
            por_tipo = {'A': {'cant': 0, 'total': 0.0, 'iva': 0.0},
                        'B': {'cant': 0, 'total': 0.0, 'iva': 0.0},
                        'C': {'cant': 0, 'total': 0.0, 'iva': 0.0}}
            # Mapa inverso: código → grupo (para saber a qué grupo suma cada factura)
            CODIGO_A_GRUPO = {
                '01': 'A', '03': 'A',
                '06': 'B', '08': 'B',
                '11': 'C', '13': 'C',
            }

            for f in facturas:
                desglose = iva_por_factura.get(f.id, {})
                neto_21   = desglose.get('21',  {}).get('neto', 0)
                iva_21    = desglose.get('21',  {}).get('iva',  0)
                neto_105  = desglose.get('10',  {}).get('neto', 0)
                iva_105   = desglose.get('10',  {}).get('iva',  0)
                neto_otro = sum(v['neto'] for k, v in desglose.items() if k not in ('21','10'))
                iva_otro  = sum(v['iva']  for k, v in desglose.items() if k not in ('21','10'))

                neto_total_fac = round(neto_21 + neto_105 + neto_otro, 2)

                # Tipo comprobante legible
                tipos = {'01':'Factura A','06':'Factura B','11':'Factura C',
                         '03':'NC A','08':'NC B','13':'NC C'}
                codigo = str(f.tipo_comprobante).zfill(2)
                tipo_leg = tipos.get(codigo, f.tipo_comprobante)
                grupo = CODIGO_A_GRUPO.get(codigo)

                comprobantes.append({
                    'id':            f.id,
                    'fecha':         f.fecha.strftime('%d/%m/%Y'),
                    'tipo':          tipo_leg,
                    'tipo_grupo':    grupo or '',
                    'punto_venta':   str(f.punto_venta).zfill(4),
                    'numero':        f.numero,
                    'cae':           f.cae or '',
                    'cliente':       f.cliente_nombre,
                    'cuit':          f.cliente_cuit or '',
                    'condicion_iva': f.condicion_iva or '',
                    'neto_21':       neto_21,
                    'iva_21':        iva_21,
                    'neto_105':      neto_105,
                    'iva_105':       iva_105,
                    'neto_otro':     round(neto_otro, 2),
                    'iva_otro':      round(iva_otro, 2),
                    'neto_total':    neto_total_fac,
                    'total':         round(float(f.total), 2),
                })

                total_neto     += neto_total_fac
                total_iva_21   += iva_21
                total_iva_105  += iva_105
                total_iva_otro += iva_otro
                total_general  += float(f.total)

                # Sumar al grupo correspondiente
                if grupo and grupo in por_tipo:
                    por_tipo[grupo]['cant']  += 1
                    por_tipo[grupo]['total'] += float(f.total)
                    por_tipo[grupo]['iva']   += iva_21 + iva_105 + iva_otro

            # Limpiar grupos vacíos y redondear
            por_tipo_final = {}
            for k, v in por_tipo.items():
                if v['cant'] > 0:
                    por_tipo_final[k] = {
                        'cant':  v['cant'],
                        'total': round(v['total'], 2),
                        'iva':   round(v['iva'], 2),
                    }

            totales = {
                'comprobantes': len(comprobantes),
                'neto':         round(total_neto, 2),
                'iva_21':       round(total_iva_21, 2),
                'iva_105':      round(total_iva_105, 2),
                'iva_otro':     round(total_iva_otro, 2),
                'iva_total':    round(total_iva_21 + total_iva_105 + total_iva_otro, 2),
                'total':        round(total_general, 2),
            }

            return jsonify({
                'success':       True,
                'comprobantes':  comprobantes,
                'totales':       totales,
                'por_tipo':      por_tipo_final,
                'periodo':       f"{fecha_desde} al {fecha_hasta}",
            })

        except Exception as e:
            import traceback; traceback.print_exc()
            return jsonify({'success': False, 'error': str(e)}), 500


    # =====================================================================
    # EXPORTACIÓN CITI (RG 3685) - VENTAS + COMPRAS
    # =====================================================================
    @estadisticas_bp.route('/api/citi/exportar_zip')
    @login_required
    def api_citi_exportar_zip():
        """
        Genera un ZIP con los 4 archivos TXT del Régimen de Información de
        Compras y Ventas (RG 3685):
            - VENTAS_CBTE.txt
            - VENTAS_ALICUOTAS.txt
            - COMPRAS_CBTE.txt
            - COMPRAS_ALICUOTAS.txt
            + LEEME.txt con instrucciones

        Parámetros:
            ?desde=YYYY-MM-DD
            ?hasta=YYYY-MM-DD
            ?cuit_informante=20123456789 (opcional, para el nombre del archivo)
        """
        try:
            from flask import send_file
            from exportador_citi import (
                generar_ventas_cbte, generar_ventas_alicuotas,
                generar_compras_cbte, generar_compras_alicuotas,
                armar_zip_citi,
            )

            fecha_desde = request.args.get('desde')
            fecha_hasta = request.args.get('hasta')
            cuit_inf = request.args.get('cuit_informante', '').strip()

            if not fecha_desde or not fecha_hasta:
                return jsonify({'success': False, 'error': 'Fechas requeridas'}), 400

            desde_dt = datetime.strptime(fecha_desde, '%Y-%m-%d')
            hasta_dt = datetime.strptime(fecha_hasta, '%Y-%m-%d').replace(
                hour=23, minute=59, second=59
            )

            # ────────── VENTAS ──────────
            ventas_cbte_data = []
            ventas_alic_data = []

            facturas_v = db.session.query(
                Factura.id, Factura.numero, Factura.tipo_comprobante,
                Factura.punto_venta, Factura.fecha, Factura.total, Factura.cae,
                Cliente.nombre.label('cli_nombre'),
                Cliente.documento.label('cli_doc'),
                Cliente.tipo_documento.label('cli_tipo_doc'),
                Cliente.condicion_iva.label('cli_cond_iva'),
            ).outerjoin(
                Cliente, Factura.cliente_id == Cliente.id
            ).filter(
                Factura.fecha >= desde_dt,
                Factura.fecha <= hasta_dt,
                Factura.estado == 'autorizada',
            ).order_by(Factura.fecha.asc(), Factura.id.asc()).all()

            # Detalles para calcular alícuotas por factura
            detalles_v = db.session.query(
                DetalleFactura.factura_id,
                DetalleFactura.porcentaje_iva,
                func.sum(DetalleFactura.subtotal).label('neto'),
                func.sum(DetalleFactura.importe_iva).label('iva'),
            ).join(
                Factura, DetalleFactura.factura_id == Factura.id
            ).filter(
                Factura.fecha >= desde_dt,
                Factura.fecha <= hasta_dt,
                Factura.estado == 'autorizada',
            ).group_by(
                DetalleFactura.factura_id,
                DetalleFactura.porcentaje_iva,
            ).all()

            iva_por_fac = {}
            for d in detalles_v:
                iva_por_fac.setdefault(d.factura_id, []).append({
                    'porcentaje': float(d.porcentaje_iva or 0),
                    'neto': float(d.neto or 0),
                    'iva': float(d.iva or 0),
                })

            # Extraer número "puro" del comprobante (solo la parte numérica
            # después del guión si viene como "0001-00000123")
            def _nro_puro(numero):
                if not numero:
                    return '0'
                s = str(numero)
                if '-' in s:
                    s = s.split('-')[-1]
                return ''.join(c for c in s if c.isdigit()) or '0'

            for f in facturas_v:
                desglose = iva_por_fac.get(f.id, [])
                neto_gravado_total = sum(d['neto'] for d in desglose)
                iva_total = sum(d['iva'] for d in desglose)
                cant_alic = len(desglose) if desglose else 1

                # Comprobantes C no discriminan IVA
                cod_cbte = str(f.tipo_comprobante or '').zfill(2)
                if cod_cbte in ('11', '12', '13'):
                    cant_alic = 0
                    neto_gravado_total = 0
                    iva_total = 0

                ventas_cbte_data.append({
                    'fecha': f.fecha.date() if hasattr(f.fecha, 'date') else f.fecha,
                    'tipo_comprobante': f.tipo_comprobante,
                    'punto_venta': f.punto_venta,
                    'numero': _nro_puro(f.numero),
                    'cliente_nombre': f.cli_nombre or 'CONSUMIDOR FINAL',
                    'cliente_cuit': f.cli_doc or '',
                    'cliente_tipo_doc': f.cli_tipo_doc or '',
                    'cliente_condicion_iva': f.cli_cond_iva or '',
                    'total': float(f.total or 0),
                    'neto_gravado': neto_gravado_total,
                    'iva': iva_total,
                    'cant_alicuotas': cant_alic,
                    'cae': f.cae or '',
                })

                # Alícuotas (solo si corresponde)
                for d in desglose:
                    ventas_alic_data.append({
                        'tipo_comprobante': f.tipo_comprobante,
                        'punto_venta': f.punto_venta,
                        'numero': _nro_puro(f.numero),
                        'neto_gravado': d['neto'],
                        'porcentaje_iva': d['porcentaje'],
                        'iva_liquidado': d['iva'],
                    })

            # ────────── COMPRAS ──────────
            # Lectura con SQL crudo porque las columnas de percepciones no
            # están en el modelo SQLAlchemy (según lo discutido antes).
            compras_cbte_data = []
            compras_alic_data = []

            desde_date = desde_dt.date()
            hasta_date = hasta_dt.date()

            sql_c = """
                SELECT fc.id, fc.fecha, fc.tipo_comprobante, fc.punto_venta, fc.numero,
                       fc.neto_gravado_21, fc.iva_21, fc.neto_gravado_105, fc.iva_105,
                       fc.neto_no_gravado, fc.otros_impuestos, fc.total,
                       COALESCE(fc.percepcion_iva, 0)       AS percepcion_iva,
                       COALESCE(fc.percepcion_iibb, 0)      AS percepcion_iibb,
                       COALESCE(fc.percepcion_ganancias, 0) AS percepcion_ganancias,
                       p.razon_social AS prov_nombre,
                       p.cuit         AS prov_cuit
                  FROM factura_compra fc
                  JOIN proveedor p ON p.id = fc.proveedor_id
                 WHERE fc.fecha BETWEEN :desde AND :hasta
                   AND (fc.estado IS NULL OR fc.estado != 'anulada')
                 ORDER BY fc.fecha ASC, fc.id ASC
            """
            rows_c = db.session.execute(text(sql_c), {
                'desde': desde_date, 'hasta': hasta_date
            }).mappings().all()

            for r in rows_c:
                neto21 = float(r['neto_gravado_21'] or 0)
                iva21 = float(r['iva_21'] or 0)
                neto105 = float(r['neto_gravado_105'] or 0)
                iva105 = float(r['iva_105'] or 0)

                alicuotas_esta_compra = []
                if neto21 > 0 or iva21 > 0:
                    alicuotas_esta_compra.append({
                        'porcentaje': 21, 'neto': neto21, 'iva': iva21
                    })
                if neto105 > 0 or iva105 > 0:
                    alicuotas_esta_compra.append({
                        'porcentaje': 10.5, 'neto': neto105, 'iva': iva105
                    })

                compras_cbte_data.append({
                    'fecha': r['fecha'],
                    'tipo_comprobante': r['tipo_comprobante'],
                    'punto_venta': r['punto_venta'],
                    'numero': _nro_puro(r['numero']),
                    'prov_nombre': r['prov_nombre'] or 'SIN NOMBRE',
                    'prov_cuit': r['prov_cuit'] or '',
                    'prov_tipo_doc': 'CUIT',
                    'total': float(r['total'] or 0),
                    'neto_gravado': neto21 + neto105,
                    'iva': iva21 + iva105,
                    'no_gravado': float(r['neto_no_gravado'] or 0),
                    'percepcion_iva': float(r['percepcion_iva'] or 0),
                    'percepcion_iibb': float(r['percepcion_iibb'] or 0),
                    'credito_fiscal_computable': iva21 + iva105,
                    'cant_alicuotas': len(alicuotas_esta_compra),
                })

                for a in alicuotas_esta_compra:
                    compras_alic_data.append({
                        'tipo_comprobante': r['tipo_comprobante'],
                        'punto_venta': r['punto_venta'],
                        'numero': _nro_puro(r['numero']),
                        'neto_gravado': a['neto'],
                        'porcentaje_iva': a['porcentaje'],
                        'iva_liquidado': a['iva'],
                    })

            # ────────── ARMAR ZIP ──────────
            periodo_aaaamm = desde_dt.strftime('%Y%m')
            zip_buf = armar_zip_citi(
                ventas_cbte=generar_ventas_cbte(ventas_cbte_data),
                ventas_alic=generar_ventas_alicuotas(ventas_alic_data),
                compras_cbte=generar_compras_cbte(compras_cbte_data),
                compras_alic=generar_compras_alicuotas(compras_alic_data),
                cuit_informante=cuit_inf,
                periodo_aaaamm=periodo_aaaamm,
            )

            nombre_zip = f"CITI_{periodo_aaaamm}.zip"
            return send_file(
                zip_buf,
                as_attachment=True,
                download_name=nombre_zip,
                mimetype='application/zip'
            )

        except Exception as e:
            import traceback; traceback.print_exc()
            return jsonify({'success': False, 'error': str(e)}), 500


    # =====================================================================
    # EXPORTACIÓN LIBRO IVA DIGITAL (RG 4597) - VENTAS
    # =====================================================================
    @estadisticas_bp.route('/api/libro_iva/exportar_ventas_zip')
    @login_required
    def api_libro_iva_exportar_ventas_zip():
        """
        Genera un ZIP con los archivos del Libro IVA Digital de Ventas (RG 4597):
            - LIBRO_IVA_DIGITAL_VENTAS_CBTE.txt
            - LIBRO_IVA_DIGITAL_VENTAS_ALICUOTAS.txt
            - LEEME.txt

        Parámetros GET:
            ?desde=YYYY-MM-DD
            ?hasta=YYYY-MM-DD   (debe ser del MISMO mes que 'desde')
        """
        try:
            from flask import send_file
            from exportador_libro_iva import (
                generar_ventas_cbte,
                generar_ventas_alicuotas,
                armar_zip_libro_iva,
            )
            try:
                from config_cliente import CUIT as CUIT_EMISOR
            except Exception:
                CUIT_EMISOR = ''

            fecha_desde = request.args.get('desde')
            fecha_hasta = request.args.get('hasta')

            if not fecha_desde or not fecha_hasta:
                return jsonify({'success': False, 'error': 'Fechas requeridas'}), 400

            desde_dt = datetime.strptime(fecha_desde, '%Y-%m-%d')
            hasta_dt = datetime.strptime(fecha_hasta, '%Y-%m-%d').replace(
                hour=23, minute=59, second=59
            )

            # Validación: mismo mes calendario (requisito AFIP)
            if desde_dt.year != hasta_dt.year or desde_dt.month != hasta_dt.month:
                return jsonify({
                    'success': False,
                    'error': 'El período debe ser de un único mes calendario. '
                             'AFIP no permite mezclar meses en un mismo Libro IVA.'
                }), 400

            # ────────── QUERY FACTURAS + NC (mismo filtro que /api/iva_ventas) ──────────
            facturas = db.session.query(
                Factura.id, Factura.numero, Factura.tipo_comprobante,
                Factura.punto_venta, Factura.fecha, Factura.total, Factura.cae,
                Cliente.nombre.label('cli_nombre'),
                Cliente.documento.label('cli_doc'),
                Cliente.tipo_documento.label('cli_tipo_doc'),
            ).outerjoin(
                Cliente, Factura.cliente_id == Cliente.id
            ).filter(
                Factura.fecha >= desde_dt,
                Factura.fecha <= hasta_dt,
                Factura.estado == 'autorizada',
            ).order_by(Factura.fecha.asc(), Factura.id.asc()).all()

            if not facturas:
                return jsonify({
                    'success': False,
                    'error': 'No hay comprobantes autorizados en el período seleccionado.'
                }), 400

            # Detalles agrupados por factura+alícuota
            detalles = db.session.query(
                DetalleFactura.factura_id,
                DetalleFactura.porcentaje_iva,
                func.sum(DetalleFactura.subtotal).label('neto'),
                func.sum(DetalleFactura.importe_iva).label('iva'),
            ).join(
                Factura, DetalleFactura.factura_id == Factura.id
            ).filter(
                Factura.fecha >= desde_dt,
                Factura.fecha <= hasta_dt,
                Factura.estado == 'autorizada',
            ).group_by(
                DetalleFactura.factura_id,
                DetalleFactura.porcentaje_iva,
            ).all()

            # Agrupar alícuotas por factura (preservando orden de inserción)
            alic_por_factura = {}
            for d in detalles:
                alic_por_factura.setdefault(d.factura_id, []).append({
                    'porcentaje': float(d.porcentaje_iva or 0),
                    'neto':       float(d.neto or 0),
                    'iva':        float(d.iva or 0),
                })

            # ────────── ARMAR DATOS PARA EL EXPORTADOR ──────────
            cbte_rows = []
            alic_rows = []

            for f in facturas:
                cod_cbte = str(f.tipo_comprobante or '').zfill(2)
                es_clase_c = cod_cbte in ('11', '12', '13')

                desglose = alic_por_factura.get(f.id, [])

                # Para comprobantes clase C: cant_alic = 0, neto e IVA = 0 en cabecera
                if es_clase_c:
                    cant_alic = 0
                    neto_total = 0.0
                    iva_total  = 0.0
                else:
                    cant_alic  = len(desglose) if desglose else 1
                    neto_total = sum(d['neto'] for d in desglose)
                    iva_total  = sum(d['iva']  for d in desglose)

                cbte_rows.append({
                    'fecha':              f.fecha.date() if hasattr(f.fecha, 'date') else f.fecha,
                    'tipo_comprobante':   cod_cbte,
                    'punto_venta':        f.punto_venta,
                    'numero':             f.numero,
                    'cliente_doc_tipo':   f.cli_tipo_doc or '',
                    'cliente_doc_numero': f.cli_doc or '0',
                    'cliente_nombre':     f.cli_nombre or 'CONSUMIDOR FINAL',
                    'total':              float(f.total or 0),
                    'neto_gravado':       neto_total,
                    'iva':                iva_total,
                    'cant_alicuotas':     cant_alic,
                })

                # Alícuotas (solo para NO clase C)
                if not es_clase_c:
                    for d in desglose:
                        alic_rows.append({
                            'tipo_comprobante': cod_cbte,
                            'punto_venta':      f.punto_venta,
                            'numero':           f.numero,
                            'neto_gravado':     d['neto'],
                            'porcentaje_iva':   d['porcentaje'],
                            'iva_liquidado':    d['iva'],
                        })

            # ────────── GENERAR ARCHIVOS Y ZIP ──────────
            cbte_txt = generar_ventas_cbte(cbte_rows)
            alic_txt = generar_ventas_alicuotas(alic_rows)

            periodo_aaaamm = desde_dt.strftime('%Y%m')
            zip_buf = armar_zip_libro_iva(
                ventas_cbte_txt=cbte_txt,
                ventas_alic_txt=alic_txt,
                cuit_informante=CUIT_EMISOR,
                periodo_aaaamm=periodo_aaaamm,
            )

            cuit_str = CUIT_EMISOR or 'SINCUIT'
            nombre_zip = f"Libro_IVA_Digital_Ventas_{cuit_str}_{periodo_aaaamm}.zip"
            return send_file(
                zip_buf,
                as_attachment=True,
                download_name=nombre_zip,
                mimetype='application/zip'
            )

        except Exception as e:
            import traceback; traceback.print_exc()
            return jsonify({'success': False, 'error': str(e)}), 500


    return estadisticas_bp