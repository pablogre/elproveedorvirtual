# exportador_citi.py
# =========================================================================
# Generador de archivos TXT para el Régimen de Información de Compras y
# Ventas — RG 3685/2014 (ARCA, ex AFIP).
#
# IMPORTANTE — LEER ANTES DE USAR:
# ---------------------------------------------------------------------
# Este módulo genera 4 archivos TXT de ancho fijo:
#     - VENTAS_CBTE.txt
#     - VENTAS_ALICUOTAS.txt
#     - COMPRAS_CBTE.txt
#     - COMPRAS_ALICUOTAS.txt
#
# El formato está basado en el Anexo V de la RG 3685/2014 y en el Manual
# del aplicativo SIAP "Régimen de Información de Compras y Ventas".
#
# Sin embargo, el diseño de registro EXACTO del aplicativo de importación
# puede tener pequeñas diferencias que solo se detectan al intentar
# importar el archivo al aplicativo. Antes de usar en producción:
#
#   1. Instalar SIAP + módulo "Régimen de Información de Compras y Ventas".
#   2. Generar un período de prueba (2-3 facturas).
#   3. Intentar importar el TXT al aplicativo.
#   4. Si el aplicativo tira "El diseño del archivo no se corresponde con
#      el diseño de registro establecido", revisar anchos y posiciones.
#
# NUNCA presentar al fisco un archivo que no haya sido validado por el
# aplicativo oficial.
# =========================================================================

from datetime import datetime
from decimal import Decimal
from io import BytesIO
import zipfile


# ─────────────────────────────────────────────────────────────────────────
# HELPERS DE FORMATO
# ─────────────────────────────────────────────────────────────────────────

def _num(v, n):
    """Numérico sin signo, rellenado con ceros a la izquierda."""
    s = str(v or 0).strip()
    # Quitamos guiones y puntos (por si viene CUIT '20-12345678-9' o nro
    # con puntos)
    s = s.replace('-', '').replace('.', '').replace(' ', '')
    if not s.isdigit():
        s = ''.join(c for c in s if c.isdigit()) or '0'
    return s.zfill(n)[:n]


def _txt(v, n, upper=True):
    """Alfanumérico, rellenado con blancos a la derecha, truncado a n."""
    s = str(v or '').strip()
    if upper:
        s = s.upper()
    # Normalizar acentos para que no rompa ANSI
    reemplazos = {
        'Á': 'A', 'É': 'E', 'Í': 'I', 'Ó': 'O', 'Ú': 'U',
        'Ñ': 'N', 'Ü': 'U',
        'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
        'ñ': 'n', 'ü': 'u',
    }
    for k, v2 in reemplazos.items():
        s = s.replace(k, v2)
    return s[:n].ljust(n)


def _money(v, n=15, permitir_negativo=False):
    """
    Importe en formato entero sin punto decimal (se multiplica por 100 para
    incluir centavos). n enteros por defecto (15).

    Reglas de la RG 3685:
    - Importes positivos: rellenar con ceros a la izquierda.
    - Importes negativos: primer carácter '-', el resto son los dígitos.
    - Notas de crédito: se ENVÍAN EN POSITIVO y el aplicativo les asigna el
      signo. NO poner signo negativo en NCs.
    """
    try:
        dec = Decimal(str(v or 0))
    except Exception:
        dec = Decimal('0')
    centavos = int(round(dec * 100))
    if centavos < 0 and permitir_negativo:
        s = str(abs(centavos)).zfill(n - 1)
        return '-' + s[:n - 1]
    return str(abs(centavos)).zfill(n)


def _money16(v):
    """Como _money pero con 16 posiciones (para precio unitario con 3 decimales)."""
    try:
        dec = Decimal(str(v or 0))
    except Exception:
        dec = Decimal('0')
    millares = int(round(dec * 1000))
    return str(abs(millares)).zfill(16)


def _fecha_yyyymmdd(f):
    """Fecha AAAAMMDD (8 dígitos). Acepta datetime, date o string."""
    if f is None:
        return '00000000'
    if isinstance(f, str):
        try:
            f = datetime.strptime(f[:10], '%Y-%m-%d').date()
        except Exception:
            try:
                f = datetime.strptime(f[:10], '%d/%m/%Y').date()
            except Exception:
                return '00000000'
    return f.strftime('%Y%m%d')


# ─────────────────────────────────────────────────────────────────────────
# MAPEOS
# ─────────────────────────────────────────────────────────────────────────

def _cod_tipo_comprobante(tc):
    """
    Devuelve el código numérico de 3 dígitos del tipo de comprobante.
    Soporta que venga como 'A', 'B', 'C' (factura), código ARCA o string.
    """
    if not tc:
        return '099'
    s = str(tc).strip().upper()
    mapa = {
        'A': '001', 'B': '006', 'C': '011',
        'NCA': '003', 'NCB': '008', 'NCC': '013',
        'NDA': '002', 'NDB': '007', 'NDC': '012',
        # Códigos ya numéricos
        '1': '001', '01': '001', '001': '001',   # FA
        '2': '002', '02': '002', '002': '002',   # NDA
        '3': '003', '03': '003', '003': '003',   # NCA
        '6': '006', '06': '006', '006': '006',   # FB
        '7': '007', '07': '007', '007': '007',   # NDB
        '8': '008', '08': '008', '008': '008',   # NCB
        '11': '011', '011': '011',               # FC
        '12': '012', '012': '012',               # NDC
        '13': '013', '013': '013',               # NCC
        '19': '019', '019': '019',               # Factura Exportación
        '51': '051', '051': '051',               # Factura M
        '81': '081', '081': '081',               # Tique factura A
        '82': '082', '082': '082',               # Tique factura B
        '83': '083', '083': '083',               # Tique
        '99': '099', '099': '099',               # Otros sin RG 1415
    }
    if s in mapa:
        return mapa[s]
    # Último intento: si son dígitos, padding a 3
    try:
        return str(int(s)).zfill(3)
    except Exception:
        return '099'


def _es_nota_credito(cod_cbte):
    """Detecta si un código corresponde a Nota de Crédito (003, 008, 013)."""
    return cod_cbte in ('003', '008', '013', '053', '054', '055')


def _cod_doc_comprador(tipo_doc, condicion_iva=None, total=0, cuit=None):
    """
    Devuelve el código de tipo de documento del comprador según la tabla de
    ARCA:
      80 = CUIT
      86 = CUIL
      87 = CDI
      89 = LE
      90 = LC
      91 = CI Extranjera
      94 = Pasaporte
      96 = DNI
      99 = Sin identificar (venta global diaria o CF < $1000)
    """
    # Si tiene CUIT válido (11 dígitos), siempre CUIT
    if cuit:
        cuit_str = str(cuit).replace('-', '').replace(' ', '').strip()
        if len(cuit_str) == 11 and cuit_str.isdigit():
            return '80'

    td = str(tipo_doc or '').strip().upper()
    if td in ('CUIT',):
        return '80'
    if td in ('CUIL',):
        return '86'
    if td in ('CDI',):
        return '87'
    if td in ('DNI',):
        return '96'
    if td in ('LE',):
        return '89'
    if td in ('LC',):
        return '90'
    if td in ('PASAPORTE',):
        return '94'

    # Si es consumidor final sin doc y monto < 1000, el código es 99
    try:
        total_f = float(total or 0)
    except Exception:
        total_f = 0
    ci = (condicion_iva or '').upper()
    if 'CONSUMIDOR' in ci and total_f < 1000:
        return '99'
    if not tipo_doc and not cuit:
        return '99'
    return '96'  # DNI por defecto


def _cod_alicuota_iva(porc):
    """
    Código de alícuota de IVA según tabla ARCA.
      0003 = 0%
      0004 = 10,5%
      0005 = 21%
      0006 = 27%
      0008 = 5%
      0009 = 2,5%
    """
    try:
        p = float(porc or 0)
    except Exception:
        p = 0
    # Redondeo para tolerar 21.0, 21.00, 10.5, etc.
    if abs(p - 21) < 0.01:
        return '0005'
    if abs(p - 10.5) < 0.01:
        return '0004'
    if abs(p - 27) < 0.01:
        return '0006'
    if abs(p - 5) < 0.01:
        return '0008'
    if abs(p - 2.5) < 0.01:
        return '0009'
    if abs(p) < 0.01:
        return '0003'
    # Por default 21%
    return '0005'


# ─────────────────────────────────────────────────────────────────────────
# GENERACIÓN DE ARCHIVOS DE VENTAS
# ─────────────────────────────────────────────────────────────────────────

def generar_ventas_cbte(comprobantes):
    """
    Genera el contenido del archivo VENTAS_CBTE.txt.

    Cada elemento de `comprobantes` debe ser un dict con estas claves:
        fecha                 : date/datetime/str (obligatorio)
        tipo_comprobante      : 'A'/'B'/'C'/código ARCA (obligatorio)
        punto_venta           : int/str (obligatorio)
        numero                : int/str (obligatorio)
        numero_hasta          : int/str (opcional, default = numero)
        cliente_nombre        : str (obligatorio)
        cliente_cuit          : str (puede ser vacío)
        cliente_tipo_doc      : 'DNI'/'CUIT'/'CUIL'/... (opcional)
        cliente_condicion_iva : str (opcional)
        total                 : Decimal/float (obligatorio)
        neto_gravado          : Decimal/float
        iva                   : Decimal/float
        no_gravado            : Decimal/float (opcional)
        exento                : Decimal/float (opcional)
        percepcion_no_cat     : Decimal/float (opcional)
        percepcion_iva        : Decimal/float (opcional)
        percepcion_iibb       : Decimal/float (opcional)
        percepcion_municipal  : Decimal/float (opcional)
        impuestos_internos    : Decimal/float (opcional)
        cant_alicuotas        : int (obligatorio; 0 solo para cbtes que no
                                discriminan IVA — tickets C, exportación, etc.)
        codigo_operacion      : 'Z'/'X'/'E'/'N'/' ' (opcional)
        cae                   : str (opcional)
        fecha_vto_pago        : date/str (opcional, para liquidaciones 17/18)
        otros_tributos        : Decimal/float (opcional)
    """
    lineas = []
    for c in comprobantes:
        cod_cbte = _cod_tipo_comprobante(c.get('tipo_comprobante'))

        # Para NC, los importes se envían en positivo (el aplicativo les pone
        # el signo negativo automáticamente).
        total = abs(float(c.get('total') or 0))
        neto_gravado = abs(float(c.get('neto_gravado') or 0))
        iva = abs(float(c.get('iva') or 0))
        no_gravado = abs(float(c.get('no_gravado') or 0))
        exento = abs(float(c.get('exento') or 0))
        perc_no_cat = abs(float(c.get('percepcion_no_cat') or 0))
        perc_iva = abs(float(c.get('percepcion_iva') or 0))
        perc_iibb = abs(float(c.get('percepcion_iibb') or 0))
        perc_muni = abs(float(c.get('percepcion_municipal') or 0))
        imp_internos = abs(float(c.get('impuestos_internos') or 0))
        otros_trib = abs(float(c.get('otros_tributos') or 0))

        # Código de documento
        cod_doc = _cod_doc_comprador(
            c.get('cliente_tipo_doc'),
            c.get('cliente_condicion_iva'),
            total,
            c.get('cliente_cuit')
        )

        # Si es consumidor final sin identificar
        if cod_doc == '99':
            nro_doc = '0'
            nombre = 'CONSUMIDOR FINAL'
        else:
            nro_doc = c.get('cliente_cuit') or '0'
            nombre = c.get('cliente_nombre') or 'SIN NOMBRE'

        cant_alic = int(c.get('cant_alicuotas') or 0)
        cod_op = str(c.get('codigo_operacion') or ' ').strip()[:1] or ' '

        nro_desde = c.get('numero')
        nro_hasta = c.get('numero_hasta') or nro_desde

        # Armado de la línea campo por campo
        # ─ Campo 1: Fecha (8)
        linea = _fecha_yyyymmdd(c.get('fecha'))
        # ─ Campo 2: Tipo de Comprobante (3)
        linea += cod_cbte
        # ─ Campo 3: Punto de Venta (5)
        linea += _num(c.get('punto_venta'), 5)
        # ─ Campo 4: Número desde (20)
        linea += _num(nro_desde, 20)
        # ─ Campo 5: Número hasta (20)
        linea += _num(nro_hasta, 20)
        # ─ Campo 6: Código de documento (2)
        linea += _num(cod_doc, 2)
        # ─ Campo 7: Número de documento (20)
        linea += _num(nro_doc, 20)
        # ─ Campo 8: Apellido y nombre / Denominación (30)
        linea += _txt(nombre, 30)
        # ─ Campo 9: Importe total (15)
        linea += _money(total)
        # ─ Campo 10: Conceptos que no integran el precio neto gravado (15)
        linea += _money(no_gravado)
        # ─ Campo 11: Percepción a no categorizado (15)
        linea += _money(perc_no_cat)
        # ─ Campo 12: Importe de operaciones exentas (15)
        linea += _money(exento)
        # ─ Campo 13: Percepciones o pagos a cuenta de impuestos nacionales (15)
        linea += _money(perc_iva)
        # ─ Campo 14: Percepción de Ingresos Brutos (15)
        linea += _money(perc_iibb)
        # ─ Campo 15: Percepción de Impuestos Municipales (15)
        linea += _money(perc_muni)
        # ─ Campo 16: Impuestos internos (15)
        linea += _money(imp_internos)
        # ─ Campo 17: Código de moneda (3)  — 'PES' para pesos argentinos
        linea += 'PES'
        # ─ Campo 18: Tipo de cambio (10) = 4 enteros + 6 decimales
        #   Para pesos siempre es 1.000000 = "0001000000"
        linea += '0001000000'
        # ─ Campo 19: Cantidad de alícuotas de IVA (1)
        linea += str(cant_alic)[:1]
        # ─ Campo 20: Código de operación (1)
        linea += cod_op
        # ─ Campo 21: Otros tributos (15)
        linea += _money(otros_trib)
        # ─ Campo 22: Fecha de vencimiento de pago (8) - solo obligatorio
        #   para liquidaciones 17/18. Resto puede ser 00000000.
        fecha_vto = c.get('fecha_vto_pago')
        linea += _fecha_yyyymmdd(fecha_vto) if fecha_vto else '00000000'

        lineas.append(linea)
    return '\r\n'.join(lineas) + ('\r\n' if lineas else '')


def generar_ventas_alicuotas(alicuotas):
    """
    Genera VENTAS_ALICUOTAS.txt.

    Cada alícuota es un dict:
        tipo_comprobante  : igual que en cbte
        punto_venta       : int/str
        numero            : int/str
        neto_gravado      : Decimal/float  (base imponible para esa alícuota)
        porcentaje_iva    : 21/10.5/27/5/2.5/0
        iva_liquidado     : Decimal/float  (importe de IVA para esa alícuota)
    """
    lineas = []
    for a in alicuotas:
        cod_cbte = _cod_tipo_comprobante(a.get('tipo_comprobante'))
        cod_alic = _cod_alicuota_iva(a.get('porcentaje_iva'))
        neto = abs(float(a.get('neto_gravado') or 0))
        iva = abs(float(a.get('iva_liquidado') or 0))

        # ─ Campo 1: Tipo de Comprobante (3)
        linea = cod_cbte
        # ─ Campo 2: Punto de Venta (5)
        linea += _num(a.get('punto_venta'), 5)
        # ─ Campo 3: Número de Comprobante (20)
        linea += _num(a.get('numero'), 20)
        # ─ Campo 4: Importe Neto Gravado (15)
        linea += _money(neto)
        # ─ Campo 5: Alícuota de IVA (4)
        linea += cod_alic
        # ─ Campo 6: Impuesto Liquidado (15)
        linea += _money(iva)

        lineas.append(linea)
    return '\r\n'.join(lineas) + ('\r\n' if lineas else '')


# ─────────────────────────────────────────────────────────────────────────
# GENERACIÓN DE ARCHIVOS DE COMPRAS
# ─────────────────────────────────────────────────────────────────────────

def generar_compras_cbte(comprobantes):
    """
    Genera COMPRAS_CBTE.txt.

    Claves del dict (similares a ventas pero con proveedor):
        fecha
        tipo_comprobante
        punto_venta
        numero
        despacho             : str (opcional, solo para cod 066)
        prov_nombre
        prov_cuit
        prov_tipo_doc        : 'CUIT' en el 99% de los casos
        total
        neto_gravado
        iva
        no_gravado
        exento
        percepcion_iva
        percepcion_iibb
        percepcion_municipal
        impuestos_internos
        credito_fiscal_computable : Decimal/float (igual al IVA liquidado
                                     si se informa sin prorrateo)
        cant_alicuotas
        codigo_operacion
        otros_tributos
        cuit_emisor_corredor : str (solo para liquidaciones 033/058/059/060/063)
        denominacion_emisor  : str (solo para liquidaciones)
        iva_comision         : Decimal/float (solo para liquidaciones)
    """
    lineas = []
    for c in comprobantes:
        cod_cbte = _cod_tipo_comprobante(c.get('tipo_comprobante'))

        total = abs(float(c.get('total') or 0))
        neto_gravado = abs(float(c.get('neto_gravado') or 0))
        iva = abs(float(c.get('iva') or 0))
        no_gravado = abs(float(c.get('no_gravado') or 0))
        exento = abs(float(c.get('exento') or 0))
        perc_iva = abs(float(c.get('percepcion_iva') or 0))
        perc_iibb = abs(float(c.get('percepcion_iibb') or 0))
        perc_muni = abs(float(c.get('percepcion_municipal') or 0))
        imp_internos = abs(float(c.get('impuestos_internos') or 0))
        cred_fiscal_comp = abs(float(c.get('credito_fiscal_computable') or iva))
        otros_trib = abs(float(c.get('otros_tributos') or 0))
        iva_comision = abs(float(c.get('iva_comision') or 0))

        # Para compras siempre el vendedor (proveedor) lleva CUIT (tipo 80)
        cod_doc = _cod_doc_comprador(
            c.get('prov_tipo_doc') or 'CUIT',
            None, total, c.get('prov_cuit')
        )

        # ─ Campo 1: Fecha (8)
        linea = _fecha_yyyymmdd(c.get('fecha'))
        # ─ Campo 2: Tipo de Comprobante (3)
        linea += cod_cbte
        # ─ Campo 3: Punto de Venta (5) — en despachos puede ser 00000
        linea += _num(c.get('punto_venta'), 5)
        # ─ Campo 4: Número de Comprobante (20) — o despacho si cbte=066
        if cod_cbte == '066':
            linea += _txt(c.get('despacho') or c.get('numero'), 16, upper=False) + '0000'
        else:
            linea += _num(c.get('numero'), 20)
        # ─ Campo 5: Despacho de Importación (16) - solo para cbte 066
        # (el layout NO lo incluye separado en compras; se usa el campo 4
        # con 16 caracteres + 4 ceros. Lo manejamos arriba.)
        # ─ Campo 5 real: Código de documento del vendedor (2)
        linea += _num(cod_doc, 2)
        # ─ Campo 6: Número de identificación del vendedor (20)
        linea += _num(c.get('prov_cuit'), 20)
        # ─ Campo 7: Apellido y nombre / Denominación del vendedor (30)
        linea += _txt(c.get('prov_nombre') or 'SIN NOMBRE', 30)
        # ─ Campo 8: Importe total de la operación (15)
        linea += _money(total)
        # ─ Campo 9: Conceptos que no integran el precio neto gravado (15)
        linea += _money(no_gravado)
        # ─ Campo 10: Importe de operaciones exentas (15)
        linea += _money(exento)
        # ─ Campo 11: Percepciones o pagos a cuenta de IVA (15)
        linea += _money(perc_iva)
        # ─ Campo 12: Percepciones o pagos a cuenta de impuestos nacionales (15)
        linea += _money(0)  # rara vez se usa en compras PyME
        # ─ Campo 13: Percepciones de Ingresos Brutos (15)
        linea += _money(perc_iibb)
        # ─ Campo 14: Percepciones de Impuestos Municipales (15)
        linea += _money(perc_muni)
        # ─ Campo 15: Impuestos internos (15)
        linea += _money(imp_internos)
        # ─ Campo 16: Código de Moneda (3)
        linea += 'PES'
        # ─ Campo 17: Tipo de Cambio (10)
        linea += '0001000000'
        # ─ Campo 18: Cantidad de alícuotas IVA (1)
        linea += str(int(c.get('cant_alicuotas') or 0))[:1]
        # ─ Campo 19: Código de operación (1)
        linea += (str(c.get('codigo_operacion') or ' ').strip() or ' ')[:1]
        # ─ Campo 20: Crédito Fiscal Computable (15)
        linea += _money(cred_fiscal_comp)
        # ─ Campo 21: Otros Tributos (15)
        linea += _money(otros_trib)
        # ─ Campo 22: CUIT Emisor/Corredor (11)  — solo liquidaciones
        cuit_ec = c.get('cuit_emisor_corredor') or '0'
        linea += _num(cuit_ec, 11)
        # ─ Campo 23: Denominación Emisor/Corredor (30)
        linea += _txt(c.get('denominacion_emisor') or '', 30)
        # ─ Campo 24: IVA Comisión (15)
        linea += _money(iva_comision)

        lineas.append(linea)
    return '\r\n'.join(lineas) + ('\r\n' if lineas else '')


def generar_compras_alicuotas(alicuotas):
    """
    Genera COMPRAS_ALICUOTAS.txt. Mismo formato que el de ventas.
    """
    # El formato de alícuotas de compras es idéntico al de ventas
    return generar_ventas_alicuotas(alicuotas)


# ─────────────────────────────────────────────────────────────────────────
# EMPAQUETADO EN ZIP
# ─────────────────────────────────────────────────────────────────────────

def armar_zip_citi(ventas_cbte, ventas_alic, compras_cbte, compras_alic,
                   cuit_informante='', periodo_aaaamm=''):
    """
    Devuelve un BytesIO con un ZIP que contiene los 4 archivos TXT
    + un README.txt con instrucciones.
    """
    cuit_clean = ''.join(c for c in (cuit_informante or '') if c.isdigit())
    sufijo = f"_{cuit_clean}_{periodo_aaaamm}" if cuit_clean and periodo_aaaamm else ''

    readme = f"""ARCHIVOS CITI - Régimen de Información de Compras y Ventas (RG 3685)

Generado por FactuFácil ({datetime.now().strftime('%d/%m/%Y %H:%M')})
CUIT informante: {cuit_informante or '(no especificado)'}
Período:        {periodo_aaaamm or '(no especificado)'}

CONTENIDO:
  - VENTAS_CBTE{sufijo}.txt       : Cabecera de comprobantes de ventas
  - VENTAS_ALICUOTAS{sufijo}.txt  : Alícuotas de IVA de ventas
  - COMPRAS_CBTE{sufijo}.txt      : Cabecera de comprobantes de compras
  - COMPRAS_ALICUOTAS{sufijo}.txt : Alícuotas de IVA de compras

CÓMO IMPORTAR EN EL APLICATIVO:
  1. Instalar S.I.Ap y el módulo "Régimen de Información de Compras y Ventas".
  2. Abrir el aplicativo y crear/seleccionar la DDJJ del período.
  3. Importar en ESTE ORDEN:
       a. Compras > Importación de Comprobantes -> COMPRAS_CBTE.txt
       b. Compras > Importación de Alícuotas     -> COMPRAS_ALICUOTAS.txt
       c. Ventas  > Importación de Comprobantes -> VENTAS_CBTE.txt
       d. Ventas  > Importación de Alícuotas     -> VENTAS_ALICUOTAS.txt
  4. Generar la presentación y presentarla por transferencia electrónica.

IMPORTANTE:
  - Los archivos se generan en ANSI (compatible MS-DOS) con salto 0D 0A (CRLF).
  - Si el aplicativo rechaza el archivo por "diseño de registro", verificar:
       * que el archivo sea ANSI (no UTF-8)
       * que no tenga líneas en blanco al final
       * que todos los renglones tengan el mismo ancho
  - Este archivo es una PROPUESTA. Antes de presentar al fisco,
    verificar con el contador que los datos coincidan con el libro IVA.

Cualquier duda técnica: pablogustavore@gmail.com
"""

    buf = BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as z:
        # Los TXT se guardan en codificación ANSI (latin-1) como pide ARCA
        z.writestr(f'VENTAS_CBTE{sufijo}.txt', (ventas_cbte or '').encode('latin-1', errors='replace'))
        z.writestr(f'VENTAS_ALICUOTAS{sufijo}.txt', (ventas_alic or '').encode('latin-1', errors='replace'))
        z.writestr(f'COMPRAS_CBTE{sufijo}.txt', (compras_cbte or '').encode('latin-1', errors='replace'))
        z.writestr(f'COMPRAS_ALICUOTAS{sufijo}.txt', (compras_alic or '').encode('latin-1', errors='replace'))
        z.writestr('LEEME.txt', readme.encode('utf-8'))
    buf.seek(0)
    return buf