# verificador_licencias_web.py - VERSION CON CACHE OFFLINE (mayo/2026)
#
# Consulta el panel.factufacil.ar con tolerancia a fallos de red:
#   - Si el panel responde -> guarda cache local y devuelve el estado.
#   - Si el panel NO responde y hay cache <7 dias -> usa el cache (modo offline).
#   - Si el panel NO responde y el cache supera 7 dias -> bloquea (offline_expirado).
#   - Si el panel NO responde y NO hay cache -> bloquea (primera instalacion sin internet).

import requests
import json
import os
from datetime import datetime

# ============== CONFIGURACION ==============
URL_API_LICENCIA = "https://panel.factufacil.ar/api/licencia"
API_TOKEN = "tk_mZXaUn2L6mFbTt-rTZfM5d7sZvWsOlPuFW-GzidyUH0"

CONTACTO_EMAIL = "pablogustavore@gmail.com"
CONTACTO_TELEFONO = "+54 9 336 4537093"
CONTACTO_WEB = "pablore.com.ar"

TIMEOUT = 10                        # segundos para consulta HTTP
DIAS_GRACIA_OFFLINE = 7             # dias sin validar antes de bloquear
CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'licencia_cache.json')
# ============================================


# ════════════════════════════════════════════════════════════════════════
# CACHE LOCAL (archivo JSON junto al script)
# ════════════════════════════════════════════════════════════════════════

def _guardar_cache(cuit, datos):
    """Guarda el ultimo estado validado en disco. Solo se llama cuando la
    consulta online fue exitosa."""
    try:
        cache = {
            'cuit': cuit,
            'razon_social': datos.get('razon_social', ''),
            'activo': datos.get('activo', False),
            'mora': datos.get('mora', False),
            'fecha_vencimiento': datos.get('fecha_vencimiento', ''),
            'observaciones': datos.get('observaciones', ''),
            'ultima_verificacion': datetime.now().isoformat(),
        }
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"WARN: No se pudo guardar cache: {e}")


def _leer_cache(cuit):
    """Lee el cache. Devuelve None si no existe, esta corrupto, o es para
    otro CUIT. Si es valido, devuelve el dict con dias_desde_verificacion."""
    if not os.path.exists(CACHE_FILE):
        return None
    try:
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            cache = json.load(f)
        if cache.get('cuit') != cuit:
            return None
        ultima = datetime.fromisoformat(cache['ultima_verificacion'])
        antiguedad = datetime.now() - ultima
        cache['dias_desde_verificacion'] = antiguedad.days
        return cache
    except Exception as e:
        print(f"WARN: Cache corrupto: {e}")
        return None


# ════════════════════════════════════════════════════════════════════════
# HELPERS
# ════════════════════════════════════════════════════════════════════════

def _resultado_base():
    """Estructura comun del resultado."""
    return {
        'valida': False,
        'activo': False,
        'mora': False,
        'razon_social': '',
        'fecha_vencimiento': '',
        'observaciones': '',
        'mensaje': '',
        'tipo_bloqueo': 'error',
        'modo_offline': False,
        'dias_desde_verificacion': 0,
        'contacto': {
            'email': CONTACTO_EMAIL,
            'telefono': CONTACTO_TELEFONO,
            'web': CONTACTO_WEB,
        }
    }


def _aplicar_estado(resultado, datos, modo_offline=False, dias=0):
    """Llena el resultado con los datos del cliente y calcula tipo_bloqueo."""
    resultado['activo'] = bool(datos.get('activo', False))
    resultado['mora'] = bool(datos.get('mora', False))
    resultado['razon_social'] = datos.get('razon_social', '')
    resultado['fecha_vencimiento'] = datos.get('fecha_vencimiento', '')
    resultado['observaciones'] = datos.get('observaciones', '')
    resultado['modo_offline'] = modo_offline
    resultado['dias_desde_verificacion'] = dias

    if not resultado['activo']:
        resultado['valida'] = False
        resultado['tipo_bloqueo'] = 'bloqueado'
        resultado['mensaje'] = "El sistema se encuentra desactivado."
    elif resultado['mora']:
        resultado['valida'] = True
        resultado['tipo_bloqueo'] = 'mora'
        if modo_offline:
            resultado['mensaje'] = (f"Su período de mantenimiento está vencido. "
                                    f"Modo offline (hace {dias} día(s) sin validar).")
        else:
            resultado['mensaje'] = "Su período de mantenimiento se encuentra vencido."
    else:
        resultado['valida'] = True
        resultado['tipo_bloqueo'] = 'sin_bloqueo'
        if modo_offline:
            resultado['mensaje'] = (f"Licencia válida (modo offline, "
                                    f"hace {dias} día(s) sin validar).")
        else:
            resultado['mensaje'] = "Licencia válida"

    return resultado


def _intentar_offline(cuit):
    """La consulta online falló. Intentar con cache local."""
    print("Online fallido, intentando modo offline...")
    cache = _leer_cache(cuit)
    resultado = _resultado_base()

    if cache is None:
        # No hay cache (primera instalacion sin internet, o cache borrado)
        resultado['tipo_bloqueo'] = 'error'
        resultado['mensaje'] = ("No se pudo verificar la licencia. "
                                "Verifique su conexión a internet.")
        return resultado

    dias = cache.get('dias_desde_verificacion', 999)

    if dias >= DIAS_GRACIA_OFFLINE:
        # Cache muy viejo: bloquear pidiendo conectarse
        resultado['tipo_bloqueo'] = 'offline_expirado'
        resultado['dias_desde_verificacion'] = dias
        resultado['mensaje'] = (
            f"Hace {dias} días que no se valida la licencia. "
            f"Conecte el sistema a internet para continuar usándolo."
        )
        return resultado

    # Cache valido: usar el ultimo estado conocido
    print(f"Modo offline: cache de {dias} dia(s)")
    return _aplicar_estado(resultado, cache, modo_offline=True, dias=dias)


# ════════════════════════════════════════════════════════════════════════
# FUNCION PRINCIPAL
# ════════════════════════════════════════════════════════════════════════

def verificar_licencia(cuit):
    """Verifica el estado de la licencia.

    Returns:
        dict: {
            'valida': bool,
            'activo': bool,
            'mora': bool,
            'razon_social': str,
            'fecha_vencimiento': str,
            'observaciones': str,
            'mensaje': str,
            'tipo_bloqueo': 'sin_bloqueo' | 'mora' | 'bloqueado' |
                            'no_encontrada' | 'error' | 'offline_expirado',
            'modo_offline': bool,
            'dias_desde_verificacion': int,
            'contacto': {'email', 'telefono', 'web'}
        }
    """
    print(f"Verificando licencia CUIT {cuit} en panel...")
    resultado = _resultado_base()

    try:
        url = f"{URL_API_LICENCIA}/{cuit}"
        headers = {'X-API-Token': API_TOKEN}
        response = requests.get(url, headers=headers, timeout=TIMEOUT)

        if response.status_code == 401:
            resultado['mensaje'] = ("Error de autenticación con el servidor de licencias. "
                                    "Contacte con soporte.")
            print("Error 401: token invalido")
            return resultado

        if response.status_code == 404:
            resultado['tipo_bloqueo'] = 'no_encontrada'
            resultado['mensaje'] = f"No se encontró una licencia para el CUIT {cuit}."
            print(f"Error 404: CUIT {cuit} no registrado")
            return resultado

        if response.status_code != 200:
            # Error del server (5xx) -> intentar con cache
            print(f"HTTP {response.status_code}, intentando cache local")
            return _intentar_offline(cuit)

        # Online OK -> guardar cache y devolver estado fresco
        datos = response.json()
        _guardar_cache(cuit, datos)
        return _aplicar_estado(resultado, datos, modo_offline=False)

    except requests.exceptions.Timeout:
        print(f"Timeout >{TIMEOUT}s")
        return _intentar_offline(cuit)
    except requests.exceptions.ConnectionError:
        print("Sin conexion al panel")
        return _intentar_offline(cuit)
    except Exception as e:
        print(f"Error inesperado: {e}")
        return _intentar_offline(cuit)


# ════════════════════════════════════════════════════════════════════════
# Test del modulo
# ════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    import sys
    cuit_test = sys.argv[1] if len(sys.argv) > 1 else "20203852100"
    r = verificar_licencia(cuit_test)
    print("\n" + "=" * 50)
    print(f"valida: {r['valida']}")
    print(f"activo: {r['activo']}")
    print(f"mora: {r['mora']}")
    print(f"tipo_bloqueo: {r['tipo_bloqueo']}")
    print(f"modo_offline: {r['modo_offline']}")
    print(f"dias_desde_verificacion: {r['dias_desde_verificacion']}")
    print(f"razon_social: {r['razon_social']}")
    print(f"fecha_vencimiento: {r['fecha_vencimiento']}")
    print(f"mensaje: {r['mensaje']}")
    print("=" * 50)
