# -*- coding: utf-8 -*-
"""
exportador_libro_iva.py — Generador de archivos TXT del Libro IVA Digital (RG 4597)

Genera los archivos de ancho fijo que se importan desde el Portal IVA de AFIP/ARCA:
    - LIBRO_IVA_DIGITAL_VENTAS_CBTE.txt       (un registro por comprobante)
    - LIBRO_IVA_DIGITAL_VENTAS_ALICUOTAS.txt  (un registro por alícuota)

Especificación: https://www.afip.gob.ar/iva/documentos/Libro-IVA-Digital-Especificaciones.pdf
                (revisión 30/07/2025)

Reglas clave del formato:
    * Encoding ANSI / Windows-1252 (NO UTF-8)
    * Fin de línea CRLF
    * Importes: 15 dígitos = 13 enteros + 2 decimales, sin coma ni punto
    * Importes negativos: signo '-' en la 1ª posición de los enteros
    * Textos: blancos a la derecha (padding)
    * Numéricos: ceros a la izquierda (padding)
    * No se pueden mezclar períodos (meses) en un mismo archivo
"""

from io import BytesIO, StringIO
from decimal import Decimal
from datetime import date, datetime
import unicodedata
import zipfile


# ═══════════════════════════════════════════════════════════════════
# TABLAS DE MAPEO (RG 4597 - Tablas del Sistema)
# ═══════════════════════════════════════════════════════════════════

# Tipo de comprobante: formato CITI/AFIP 2 dígitos → Libro IVA 3 dígitos
TIPOS_CBTE_MAP = {
    '01': '001',  # Factura A
    '02': '002',  # Nota de Débito A
    '03': '003',  # Nota de Crédito A
    '06': '006',  # Factura B
    '07': '007',  # Nota de Débito B
    '08': '008',  # Nota de Crédito B
    '11': '011',  # Factura C
    '12': '012',  # Nota de Débito C
    '13': '013',  # Nota de Crédito C
}

# En COMPRAS, los tipos vienen guardados como 'A', 'B', 'C' (string).
# Si alguna vez se carga una NC de proveedor, se puede usar 'NA', 'NB', 'NC'.
TIPOS_CBTE_COMPRAS_LETRA_MAP = {
    'A':  '001', 'B':  '006', 'C':  '011',
    'NA': '003', 'NB': '008', 'NC': '013',
    'NDA':'002', 'NDB':'007', 'NDC':'012',
}

# Tipo de documento: lo que tenemos guardado → código AFIP 2 dígitos
TIPOS_DOC_MAP = {
    'CUIT': '80',
    'CUIL': '86',
    'CDI':  '87',
    'LE':   '89',
    'LC':   '90',
    'CI':   '91',
    'PAS':  '94',
    'DNI':  '96',
    '':     '99',  # Sin identificar / Venta Global Diaria
}

# Alícuota de IVA: porcentaje → código AFIP 4 dígitos
ALICUOTAS_MAP = {
    0:    '0003',
    2.5:  '0009',
    5:    '0008',
    10.5: '0004',
    21:   '0005',
    27:   '0006',
}

# Comprobantes clase C (Monotributo) que NO discriminan IVA
# → cantidad de alícuotas = 0, no se genera registro en archivo ALICUOTAS
TIPOS_CLASE_C = {'11', '12', '13'}


# ═══════════════════════════════════════════════════════════════════
# HELPERS DE FORMATEO
# ═══════════════════════════════════════════════════════════════════

def _texto(valor, longitud):
    """Texto a `longitud` caracteres, padding con blancos a la derecha.
    Elimina tildes y caracteres no mapeables a Windows-1252."""
    if valor is None:
        valor = ''
    s = str(valor)
    # Quitar tildes (NFD + eliminar combining marks)
    s = unicodedata.normalize('NFKD', s)
    s = ''.join(c for c in s if not unicodedata.combining(c))
    # Caracteres no representables → espacio
    s = s.encode('cp1252', errors='replace').decode('cp1252').replace('?', ' ')
    # Quitar saltos/tabs que romperían la línea
    s = s.replace('\r', ' ').replace('\n', ' ').replace('\t', ' ')
    s = s.upper()
    return s[:longitud].ljust(longitud, ' ')


def _num(valor, longitud):
    """Número entero a `longitud` caracteres, padding con ceros a la izquierda.
    Si viene como string con formato (ej '30-70829641-0'), extrae solo los dígitos."""
    if valor is None or valor == '':
        return '0'.zfill(longitud)
    if isinstance(valor, str):
        digitos = ''.join(c for c in valor if c.isdigit())
        valor = digitos if digitos else '0'
    s = str(int(valor))
    return s.zfill(longitud)[-longitud:]


def _importe(valor, longitud=15):
    """Importe con formato: 13 enteros + 2 decimales, sin separador.
    Ej: 1234.56 → '000000000123456'. Negativo: '-' en la 1ª posición.
    Por defecto: 15 dígitos totales."""
    if valor is None or valor == '':
        valor = 0
    # Redondear a 2 decimales usando Decimal (evita errores de float)
    d = Decimal(str(valor)).quantize(Decimal('0.01'))
    negativo = d < 0
    d = abs(d)
    centavos = int((d * 100).to_integral_value())  # total en centavos
    s = str(centavos).zfill(longitud)
    if negativo:
        # El signo '-' reemplaza al primer dígito de los enteros (posición 1)
        # Longitud total se mantiene.
        s = '-' + s[1:]
    return s[-longitud:]


def _fecha(valor):
    """Fecha AAAAMMDD (8 dígitos)."""
    if valor is None or valor == '':
        return '00000000'
    if isinstance(valor, datetime):
        valor = valor.date()
    if isinstance(valor, date):
        return valor.strftime('%Y%m%d')
    # Si viene como string, intentar parsear
    try:
        return datetime.strptime(str(valor), '%Y-%m-%d').strftime('%Y%m%d')
    except Exception:
        return '00000000'


def _tipo_doc(valor):
    """Normaliza tipo de documento a código AFIP 2 dígitos."""
    if valor is None:
        valor = ''
    v = str(valor).strip().upper()
    return TIPOS_DOC_MAP.get(v, '99')


def _tipo_cbte(valor):
    """Normaliza tipo de comprobante a 3 dígitos.
    Acepta: 3 dígitos ('001'), 2 dígitos ('01'), letras ('A','B','C','NA','NB','NC')."""
    if valor is None:
        return '000'
    s = str(valor).strip().upper()
    # Si viene ya en 3 dígitos, lo dejamos
    if len(s) == 3 and s.isdigit():
        return s
    # Si es letra (formato compras)
    if s in TIPOS_CBTE_COMPRAS_LETRA_MAP:
        return TIPOS_CBTE_COMPRAS_LETRA_MAP[s]
    # Si viene en 2 dígitos numérico, mapear
    s2 = s.zfill(2)
    return TIPOS_CBTE_MAP.get(s2, s.zfill(3))


def _cod_alicuota(porcentaje):
    """Porcentaje de IVA → código AFIP 4 dígitos."""
    try:
        p = float(porcentaje or 0)
    except Exception:
        p = 0
    # Buscar la alícuota más cercana (tolerancia para float)
    for alic, cod in ALICUOTAS_MAP.items():
        if abs(p - alic) < 0.01:
            return cod
    # Por defecto, si no coincide, consideramos 21%
    return '0005'


def _nro_puro(numero):
    """Extrae los dígitos del número de comprobante (maneja '0009-00000123')."""
    if not numero:
        return '0'
    s = str(numero)
    if '-' in s:
        s = s.split('-')[-1]
    return ''.join(c for c in s if c.isdigit()) or '0'


# ═══════════════════════════════════════════════════════════════════
# GENERADOR: ARCHIVO DE COMPROBANTES (VENTAS_CBTE)
# ═══════════════════════════════════════════════════════════════════

def generar_ventas_cbte(rows):
    """
    Genera el contenido del archivo LIBRO_IVA_DIGITAL_VENTAS_CBTE.txt

    rows: lista de dicts con estas claves (todas requeridas salvo
          donde se indique; faltantes → 0/vacío):
        fecha                    : date/datetime
        tipo_comprobante         : str ('01', '03', '06', '08', '11', '13')
        punto_venta              : int/str
        numero                   : str (número completo, ej '0009-00000123')
        cliente_doc_tipo         : str ('CUIT', 'DNI', '', ...)
        cliente_doc_numero       : str (solo dígitos)
        cliente_nombre           : str
        total                    : Decimal/float (importe total)
        neto_gravado             : Decimal/float (suma de netos gravados)
        iva                      : Decimal/float (suma de IVA)
        cant_alicuotas           : int (0 para tipo C, 1+ para A/B)
        exento                   : Decimal/float (opcional, default 0)
        no_gravado               : Decimal/float (opcional, default 0)
        otros_tributos           : Decimal/float (opcional, default 0)

    Retorna: str con una línea por comprobante, fin de línea CRLF.
    """
    out = StringIO()
    for r in rows:
        tipo = _tipo_cbte(r.get('tipo_comprobante'))
        nro  = _nro_puro(r.get('numero'))
        es_clase_c = r.get('tipo_comprobante', '') in ('11', '12', '13') or tipo in ('011', '012', '013')

        # --- Campos según RG 4597 (VENTAS_CBTE) ---
        linea = (
            # 1. Fecha (8)
            _fecha(r.get('fecha'))
            # 2. Tipo de comprobante (3)
            + tipo
            # 3. Punto de venta (5)
            + _num(r.get('punto_venta'), 5)
            # 4. Número de comprobante (20)
            + _num(nro, 20)
            # 5. Número de comprobante hasta (20) — igual al campo 4 (sin agrupamiento)
            + _num(nro, 20)
            # 6. Código de documento comprador (2)
            + _tipo_doc(r.get('cliente_doc_tipo'))
            # 7. Número de identificación comprador (20)
            + _num(r.get('cliente_doc_numero') or 0, 20)
            # 8. Apellido y nombre comprador (30)
            + _texto(r.get('cliente_nombre') or 'CONSUMIDOR FINAL', 30)
            # 9. Importe total operación (15)
            + _importe(r.get('total'))
            # 10. Importe total conceptos que no integran el precio neto gravado (15)
            + _importe(r.get('no_gravado', 0))
            # 11. Percepción a no categorizados (15)
            + _importe(0)
            # 12. Importe operaciones exentas (15)
            + _importe(r.get('exento', 0))
            # 13. Percepciones o pagos a cuenta de impuestos nacionales (15)
            + _importe(0)
            # 14. Percepciones de ingresos brutos (15)
            + _importe(0)
            # 15. Percepciones de impuestos municipales (15)
            + _importe(0)
            # 16. Impuestos internos (15)
            + _importe(0)
            # 17. Código de moneda (3)
            + 'PES'
            # 18. Tipo de cambio (10) = 4 enteros + 6 decimales → '0001000000'
            + '0001000000'
            # 19. Cantidad de alícuotas de IVA (1)
            + ('0' if es_clase_c else _num(r.get('cant_alicuotas', 1), 1))
            # 20. Código de operación (1) = ' ' (blanco) para operaciones comunes
            + ' '
            # 21. Otros tributos (15)
            + _importe(r.get('otros_tributos', 0))
            # 22. Fecha de vencimiento/pago (8) = ceros (solo obligatorio servicios públicos)
            + '00000000'
        )
        out.write(linea + '\r\n')
    return out.getvalue()


# ═══════════════════════════════════════════════════════════════════
# GENERADOR: ARCHIVO DE ALÍCUOTAS (VENTAS_ALICUOTAS)
# ═══════════════════════════════════════════════════════════════════

def generar_ventas_alicuotas(rows):
    """
    Genera el contenido del archivo LIBRO_IVA_DIGITAL_VENTAS_ALICUOTAS.txt

    rows: lista de dicts con:
        tipo_comprobante : str
        punto_venta      : int/str
        numero           : str
        neto_gravado     : Decimal/float
        porcentaje_iva   : float (ej: 21, 10.5)
        iva_liquidado    : Decimal/float

    IMPORTANTE: el orden de las alícuotas debe respetar el orden
    del archivo VENTAS_CBTE (por comprobante). Las alícuotas de un
    mismo comprobante van juntas.

    Comprobantes clase C (11/12/13) NO deben aparecer en este archivo.
    """
    out = StringIO()
    for r in rows:
        tipo = r.get('tipo_comprobante', '')
        # Saltear clase C (no discriminan IVA)
        if tipo in ('11', '12', '13') or _tipo_cbte(tipo) in ('011', '012', '013'):
            continue

        nro = _nro_puro(r.get('numero'))
        linea = (
            # 1. Tipo de comprobante (3)
            _tipo_cbte(tipo)
            # 2. Punto de venta (5)
            + _num(r.get('punto_venta'), 5)
            # 3. Número de comprobante (20)
            + _num(nro, 20)
            # 4. Importe neto gravado (15)
            + _importe(r.get('neto_gravado'))
            # 5. Alícuota de IVA (4)
            + _cod_alicuota(r.get('porcentaje_iva'))
            # 6. Impuesto liquidado (15)
            + _importe(r.get('iva_liquidado'))
        )
        out.write(linea + '\r\n')
    return out.getvalue()


# ═══════════════════════════════════════════════════════════════════
# ARMADO DEL ZIP
# ═══════════════════════════════════════════════════════════════════

LEEME_VENTAS = """LIBRO IVA DIGITAL - VENTAS (RG 4597)
=======================================

Archivos incluidos:
  * LIBRO_IVA_DIGITAL_VENTAS_CBTE.txt       (uno por comprobante)
  * LIBRO_IVA_DIGITAL_VENTAS_ALICUOTAS.txt  (uno por alicuota)

Cómo presentar al fisco:
  1. Ingresar al Portal IVA de AFIP/ARCA con clave fiscal
     (Servicio: "Portal IVA")
  2. Seleccionar el periodo fiscal correspondiente
  3. En el Libro de Ventas, elegir "Importacion de datos"
  4. Subir LIBRO_IVA_DIGITAL_VENTAS_CBTE.txt como "Cabecera"
  5. Subir LIBRO_IVA_DIGITAL_VENTAS_ALICUOTAS.txt como "Alicuotas"
  6. Validar y confirmar el período.

Especificacion oficial:
  https://www.afip.gob.ar/iva/documentos/Libro-IVA-Digital-Especificaciones.pdf

IMPORTANTE:
  - Los archivos estan en codificacion Windows-1252 (ANSI).
  - Fin de linea: CRLF.
  - No mezclar periodos (meses) en un mismo archivo.

Generado por FactuFacil - https://FactuFacil.ar
"""


def armar_zip_libro_iva(ventas_cbte_txt, ventas_alic_txt,
                        cuit_informante='', periodo_aaaamm=''):
    """
    Arma un ZIP con los dos archivos TXT + un README.

    ventas_cbte_txt: str, contenido del archivo de comprobantes
    ventas_alic_txt: str, contenido del archivo de alícuotas
    cuit_informante: str (solo para nombre interno del README)
    periodo_aaaamm:  str (solo para nombre interno del README)

    Retorna: BytesIO con el ZIP listo para send_file.
    """
    buf = BytesIO()
    # Los archivos TXT se codifican en Windows-1252 (ANSI), NO UTF-8
    cbte_bytes = ventas_cbte_txt.encode('cp1252', errors='replace')
    alic_bytes = ventas_alic_txt.encode('cp1252', errors='replace')

    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('LIBRO_IVA_DIGITAL_VENTAS_CBTE.txt',      cbte_bytes)
        zf.writestr('LIBRO_IVA_DIGITAL_VENTAS_ALICUOTAS.txt', alic_bytes)
        zf.writestr('LEEME.txt', LEEME_VENTAS.encode('cp1252', errors='replace'))

    buf.seek(0)
    return buf


# ═══════════════════════════════════════════════════════════════════
# GENERADOR: ARCHIVO DE COMPROBANTES DE COMPRAS (COMPRAS_CBTE)
# ═══════════════════════════════════════════════════════════════════

# En COMPRAS, los tipos B y C NO discriminan IVA (a diferencia de ventas,
# donde B sí se discrimina en el libro). Por eso acá "clase C" incluye
# también la clase B.
def _compras_no_discrimina_iva(tipo_3):
    """True si el comprobante recibido NO discrimina IVA (tipos B o C)."""
    return tipo_3 in ('006', '007', '008', '011', '012', '013')


def generar_compras_cbte(rows):
    """
    Genera el contenido del archivo LIBRO_IVA_DIGITAL_COMPRAS_CBTE.txt

    rows: lista de dicts con estas claves:
        fecha                    : date/datetime (fecha del comprobante)
        tipo_comprobante         : str ('A','B','C','NA','NB','NC' o códigos numéricos)
        punto_venta              : int/str
        numero                   : str
        prov_doc_numero          : str (CUIT del proveedor, solo dígitos)
        prov_nombre              : str (razón social)
        total                    : Decimal/float (importe total)
        neto_gravado             : Decimal/float (suma neto gravado 21 + 10.5)
        iva                      : Decimal/float (suma IVA 21 + 10.5)
        neto_no_gravado          : Decimal/float (opcional, default 0)
        exento                   : Decimal/float (opcional, default 0)
        percepcion_iva           : Decimal/float (opcional, default 0)
        percepcion_otros_nac     : Decimal/float (opcional, default 0) — ej: Ganancias
        percepcion_iibb          : Decimal/float (opcional, default 0)
        percepcion_municipal     : Decimal/float (opcional, default 0)
        impuestos_internos       : Decimal/float (opcional, default 0)
        otros_tributos           : Decimal/float (opcional, default 0)
        credito_fiscal_computable: Decimal/float (opcional, default = iva)
        cant_alicuotas           : int (0 para B/C, 1+ para A)

    Retorna: str con una línea por comprobante, fin de línea CRLF.
    """
    out = StringIO()
    for r in rows:
        tipo = _tipo_cbte(r.get('tipo_comprobante'))
        nro  = _nro_puro(r.get('numero'))
        no_discrim = _compras_no_discrimina_iva(tipo)

        if no_discrim:
            cant_alic = 0
        else:
            cant_alic = r.get('cant_alicuotas', 1) or 1

        # Crédito fiscal computable: si no se pasa, asumir = IVA (sin prorrateo)
        cf_computable = r.get('credito_fiscal_computable')
        if cf_computable is None:
            cf_computable = 0 if no_discrim else r.get('iva', 0)

        # --- Campos según RG 4597 (COMPRAS_CBTE) ---
        linea = (
            # 1. Fecha de comprobante (8)
            _fecha(r.get('fecha'))
            # 2. Tipo de comprobante (3)
            + tipo
            # 3. Punto de venta (5)
            + _num(r.get('punto_venta'), 5)
            # 4. Número de comprobante (20)
            + _num(nro, 20)
            # 5. Despacho de importación (16) — ceros para compras normales
            + ('0' * 16)
            # 6. Código de documento del vendedor (2) — siempre CUIT (80)
            + '80'
            # 7. Número de identificación del vendedor (20)
            + _num(r.get('prov_doc_numero') or 0, 20)
            # 8. Apellido y nombre o denominación del vendedor (30)
            + _texto(r.get('prov_nombre') or 'SIN NOMBRE', 30)
            # 9. Importe total de la operación (15)
            + _importe(r.get('total'))
            # 10. Importe total conceptos que no integran el precio neto gravado (15)
            + _importe(r.get('neto_no_gravado', 0))
            # 11. Importe operaciones exentas (15)
            + _importe(r.get('exento', 0))
            # 12. Percepciones o pagos a cuenta del IVA (15)
            + _importe(r.get('percepcion_iva', 0))
            # 13. Percepciones o pagos a cuenta de otros impuestos nacionales (15)
            + _importe(r.get('percepcion_otros_nac', 0))
            # 14. Percepciones de ingresos brutos (15)
            + _importe(r.get('percepcion_iibb', 0))
            # 15. Percepciones de impuestos municipales (15)
            + _importe(r.get('percepcion_municipal', 0))
            # 16. Impuestos internos (15)
            + _importe(r.get('impuestos_internos', 0))
            # 17. Código de moneda (3)
            + 'PES'
            # 18. Tipo de cambio (10)
            + '0001000000'
            # 19. Cantidad alícuotas IVA (1) — 0 para B/C
            + _num(cant_alic, 1)
            # 20. Código de operación (1) — blanco para operación común
            + ' '
            # 21. Crédito fiscal computable (15)
            + _importe(cf_computable)
            # 22. Otros tributos (15)
            + _importe(r.get('otros_tributos', 0))
            # 23. CUIT Emisor/Corredor (11) — ceros salvo granos/liq. compra
            + ('0' * 11)
            # 24. Denominación Emisor/Corredor (30) — blancos
            + (' ' * 30)
            # 25. IVA Comisión (15) — ceros
            + _importe(0)
            # 26. Reintegro Dto 1043/2016 / Devol IVA Turistas (15) — ceros
            + _importe(0)
        )
        out.write(linea + '\r\n')
    return out.getvalue()


# ═══════════════════════════════════════════════════════════════════
# GENERADOR: ARCHIVO DE ALÍCUOTAS DE COMPRAS (COMPRAS_ALICUOTAS)
# ═══════════════════════════════════════════════════════════════════

def generar_compras_alicuotas(rows):
    """
    Genera el contenido del archivo LIBRO_IVA_DIGITAL_COMPRAS_ALICUOTAS.txt

    Comprobantes clase B y C (que no discriminan IVA) NO aparecen acá.

    rows: lista de dicts con:
        tipo_comprobante   : str
        punto_venta        : int/str
        numero             : str
        prov_doc_numero    : str (CUIT del proveedor)
        neto_gravado       : Decimal/float
        porcentaje_iva     : float (21, 10.5, etc.)
        iva_liquidado      : Decimal/float
    """
    out = StringIO()
    for r in rows:
        tipo = _tipo_cbte(r.get('tipo_comprobante'))
        # Saltear B y C (no discriminan IVA en compras recibidas)
        if _compras_no_discrimina_iva(tipo):
            continue

        nro = _nro_puro(r.get('numero'))
        linea = (
            # 1. Tipo de comprobante (3)
            tipo
            # 2. Punto de venta (5)
            + _num(r.get('punto_venta'), 5)
            # 3. Número de comprobante (20)
            + _num(nro, 20)
            # 4. Código de documento del vendedor (2) — siempre CUIT
            + '80'
            # 5. Número de identificación del vendedor (20)
            + _num(r.get('prov_doc_numero') or 0, 20)
            # 6. Importe neto gravado (15)
            + _importe(r.get('neto_gravado'))
            # 7. Alícuota de IVA (4)
            + _cod_alicuota(r.get('porcentaje_iva'))
            # 8. Impuesto liquidado (15)
            + _importe(r.get('iva_liquidado'))
        )
        out.write(linea + '\r\n')
    return out.getvalue()


LEEME_COMPRAS = """LIBRO IVA DIGITAL - COMPRAS (RG 4597)
=========================================

Archivos incluidos:
  * LIBRO_IVA_DIGITAL_COMPRAS_CBTE.txt       (uno por comprobante)
  * LIBRO_IVA_DIGITAL_COMPRAS_ALICUOTAS.txt  (uno por alicuota)
    (NO incluye comprobantes tipo B o C, que no discriminan IVA)

Cómo presentar al fisco:
  1. Ingresar al Portal IVA de AFIP/ARCA con clave fiscal
     (Servicio: "Portal IVA")
  2. Seleccionar el periodo fiscal correspondiente
  3. En el Libro de Compras, elegir "Importacion de datos"
  4. Subir LIBRO_IVA_DIGITAL_COMPRAS_CBTE.txt como "Cabecera"
  5. Subir LIBRO_IVA_DIGITAL_COMPRAS_ALICUOTAS.txt como "Alicuotas"
  6. Validar y confirmar el período.

Especificacion oficial:
  https://www.afip.gob.ar/iva/documentos/Libro-IVA-Digital-Especificaciones.pdf

IMPORTANTE:
  - Los archivos estan en codificacion Windows-1252 (ANSI).
  - Fin de linea: CRLF.
  - No mezclar periodos (meses) en un mismo archivo.
  - El credito fiscal computable se informa SIN prorrateo
    (igual al impuesto liquidado).

Generado por FactuFacil - https://FactuFacil.ar
"""


def armar_zip_libro_iva_compras(compras_cbte_txt, compras_alic_txt,
                                cuit_informante='', periodo_aaaamm=''):
    """
    Arma un ZIP con los dos archivos TXT de COMPRAS + README.
    Retorna: BytesIO con el ZIP listo para send_file.
    """
    buf = BytesIO()
    cbte_bytes = compras_cbte_txt.encode('cp1252', errors='replace')
    alic_bytes = compras_alic_txt.encode('cp1252', errors='replace')

    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('LIBRO_IVA_DIGITAL_COMPRAS_CBTE.txt',      cbte_bytes)
        zf.writestr('LIBRO_IVA_DIGITAL_COMPRAS_ALICUOTAS.txt', alic_bytes)
        zf.writestr('LEEME.txt', LEEME_COMPRAS.encode('cp1252', errors='replace'))

    buf.seek(0)
    return buf