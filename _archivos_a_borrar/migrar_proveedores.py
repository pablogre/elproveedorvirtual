"""
migrar_proveedores.py
Migra proveedores desde prov_cod.xls a la tabla `proveedor` de SCHIRO.
Ejecutar desde C:\\SCHIRO> python migrar_proveedores.py
"""

import xlrd
import pymysql
from datetime import datetime

# ─── CONFIGURACIÓN DE CONEXIÓN ───────────────────────────────
# Ajustá estos valores si son distintos en tu config_cliente.py
DB_HOST = 'localhost'
DB_USER = 'pos_user'
DB_PASS = 'pos_password'
DB_NAME = 'schiro'          # <── cambiá si la DB se llama distinto en SCHIRO

XLS_PATH = 'prov_cod.xls'   # debe estar en la misma carpeta
# ─────────────────────────────────────────────────────────────

TIPO_IVA = {
    'I': 'Responsable Inscripto',
    'i': 'Responsable Inscripto',
    'M': 'Monotributista',
    'm': 'Monotributista',
    'E': 'Exento',
    'e': 'Exento',
    'C': 'Consumidor Final',
    'c': 'Consumidor Final',
    'N': 'No Responsable',
    'n': 'No Responsable',
}

def limpiar(val):
    if val is None:
        return None
    s = str(val).strip()
    return s if s else None

def limpiar_cuit(val):
    """Devuelve el CUIT como string limpio o None"""
    s = limpiar(val)
    if not s:
        return None
    # Quitar espacios extra
    return s.strip()

def limpiar_numero(val):
    """Convierte float a int si es número, o devuelve el string"""
    if isinstance(val, float):
        return str(int(val))
    return limpiar(val)

def migrar():
    # Leer XLS
    wb = xlrd.open_workbook(XLS_PATH)
    sh = wb.sheet_by_index(0)

    proveedores = []
    for r in range(7, sh.nrows - 2):   # fila 7 hasta antes del pie de página
        row = [sh.cell_value(r, c) for c in range(sh.ncols)]
        nombre = limpiar(row[1])
        if not nombre:
            continue

        direccion_str = limpiar(row[3]) or ''
        localidad_str = limpiar(row[7]) or ''
        direccion_completa = ' - '.join(filter(None, [direccion_str, localidad_str])) or None

        tipo_iva_codigo = limpiar(row[10]) or ''
        condicion_iva   = TIPO_IVA.get(tipo_iva_codigo, 'Responsable Inscripto')

        prov = {
            'razon_social':  nombre,
            'cuit':          limpiar_cuit(row[11]),
            'condicion_iva': condicion_iva,
            'direccion':     direccion_completa,
            'telefono':      limpiar(row[9]),
            'email':         limpiar(row[12]),
            'saldo':         0.00,
            'activo':        1,
            'fecha_creacion': datetime.now(),
        }
        proveedores.append(prov)

    print(f"📋 Proveedores leídos del XLS: {len(proveedores)}")

    # Conectar a MySQL
    try:
        conn = pymysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASS, database=DB_NAME, charset='utf8mb4')
        cursor = conn.cursor()
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return

    # Insertar
    sql = """
        INSERT INTO proveedor
            (razon_social, cuit, condicion_iva, direccion, telefono, email, saldo, activo, fecha_creacion)
        VALUES
            (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    insertados  = 0
    duplicados  = 0
    errores     = 0

    for p in proveedores:
        # Verificar si ya existe por razón social para no duplicar
        cursor.execute("SELECT id FROM proveedor WHERE razon_social = %s", (p['razon_social'],))
        if cursor.fetchone():
            print(f"   ⚠️  Ya existe: {p['razon_social']} — omitido")
            duplicados += 1
            continue

        try:
            cursor.execute(sql, (
                p['razon_social'],
                p['cuit'],
                p['condicion_iva'],
                p['direccion'],
                p['telefono'],
                p['email'],
                p['saldo'],
                p['activo'],
                p['fecha_creacion'],
            ))
            insertados += 1
            print(f"   ✅ {p['razon_social']}")
        except Exception as e:
            print(f"   ❌ Error en {p['razon_social']}: {e}")
            errores += 1

    conn.commit()
    cursor.close()
    conn.close()

    print()
    print("=" * 50)
    print(f"✅ Insertados:  {insertados}")
    print(f"⚠️  Duplicados: {duplicados}")
    print(f"❌ Errores:     {errores}")
    print("=" * 50)


if __name__ == '__main__':
    migrar()