# verificador_licencias_web.py - Verificador con interfaz web + tolerante a offline

"""
Sistema de verificación de licencias con interfaz web
En lugar de bloquear en consola, redirige a página de bloqueo

═══════════════════════════════════════════════════════════════════════════
TOLERANCIA A FALLOS DE RED (v2 - abr/2026)
═══════════════════════════════════════════════════════════════════════════
Si no hay internet pero hay un cache local de menos de 7 días,
el sistema arranca usando el último estado conocido.
Esto evita que el cliente NO PUEDA FACTURAR porque se le cayó internet.

Comportamiento:
- Internet OK: valida online y guarda cache.
- Sin internet + cache <7 días: arranca con cache (modo offline).
- Sin internet + cache >7 días: bloquea (pide conectarse).
- Sin internet + sin cache (1ra instalación): bloquea.
═══════════════════════════════════════════════════════════════════════════
"""

import requests
import json
import os
import time
from datetime import datetime, timedelta

# ============== CONFIGURACIÓN ==============
URL_LICENCIAS = "https://gist.githubusercontent.com/pablogre/77854e5d55d01018af8a4cab8ab5cc30/raw/licencias.json"

# Información de contacto para mensajes
CONTACTO_EMAIL = "pablogustavore@gmail.com"
CONTACTO_TELEFONO = "+54 9 336 4537093"
CONTACTO_WEB = "pablore.com.ar"

# Modo prueba: si es True, permite acceso aunque falle la verificación
MODO_PRUEBA = False

# Timeout de la petición HTTP (segundos)
TIMEOUT = 10

# ─── CACHE OFFLINE (NUEVO) ──────────────────────────────────────────────
# Archivo de cache local. Se crea junto al script en la misma carpeta.
CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'licencia_cache.json')

# Días de gracia: cuántos días puede arrancar sin internet usando el cache.
# Si el último contacto fue hace más de esto, exige conectarse.
DIAS_GRACIA_OFFLINE = 7
# ============================================


# ════════════════════════════════════════════════════════════════════════
# FUNCIONES DE CACHE
# ════════════════════════════════════════════════════════════════════════

def _guardar_cache(cuit, datos_cliente):
    """Guarda el último resultado válido en el archivo de cache local.
    Solo se llama cuando la verificación online fue EXITOSA."""
    try:
        cache = {
            'cuit': cuit,
            'razon_social': datos_cliente.get('razon_social', ''),
            'activo': datos_cliente.get('activo', False),
            'mora': datos_cliente.get('mora', False),
            'fecha_vencimiento': datos_cliente.get('fecha_vencimiento', ''),
            'observaciones': datos_cliente.get('observaciones', ''),
            'ultima_verificacion': datetime.now().isoformat(),
            'fuente': 'online'
        }
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ No se pudo guardar cache: {e}")


def _leer_cache(cuit):
    """Lee el cache local. Devuelve None si no existe, está corrupto, o
    es para un CUIT distinto al solicitado.
    
    Returns:
        dict con la info, o None si no hay cache utilizable.
    """
    if not os.path.exists(CACHE_FILE):
        return None
    
    try:
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            cache = json.load(f)
        
        # Verificar que el cache sea para el CUIT correcto
        if cache.get('cuit') != cuit:
            print(f"⚠️ Cache es para otro CUIT, ignorando")
            return None
        
        # Calcular antigüedad
        ultima = datetime.fromisoformat(cache['ultima_verificacion'])
        antiguedad = datetime.now() - ultima
        cache['dias_desde_verificacion'] = antiguedad.days
        cache['horas_desde_verificacion'] = int(antiguedad.total_seconds() / 3600)
        
        return cache
    except (json.JSONDecodeError, KeyError, ValueError, OSError) as e:
        print(f"⚠️ Cache corrupto o ilegible: {e}")
        return None


# ════════════════════════════════════════════════════════════════════════
# DESCARGA ONLINE
# ════════════════════════════════════════════════════════════════════════

def descargar_licencias():
    """
    Descarga el archivo de licencias desde el servidor.
    
    Usa 2 técnicas anti-cache para garantizar que SIEMPRE se obtenga
    la versión más reciente del Gist (sino GitHub puede servir la versión
    cacheada hasta 5 minutos):
      1. Query param con timestamp (cache busting): GitHub ve cada request
         como una URL distinta y no puede cachear.
      2. Headers HTTP anti-cache: instruye a proxies y al CDN a no servir
         versiones cacheadas.
    
    Returns:
        dict: Contenido del JSON o None si hay error
    """
    try:
        # Técnica 1: cache busting con timestamp (cambia en cada request)
        url_con_busting = f"{URL_LICENCIAS}?_={int(time.time())}"
        
        # Técnica 2: headers anti-cache
        headers = {
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache',
            'Expires': '0'
        }
        
        response = requests.get(url_con_busting, headers=headers, timeout=TIMEOUT, verify=True)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Error al descargar licencias: HTTP {response.status_code}")
            return None
            
    except requests.exceptions.Timeout:
        print(f"❌ Timeout al conectar con el servidor (>{TIMEOUT}s)")
        return None
    except requests.exceptions.ConnectionError:
        print("❌ Error de conexión con el servidor")
        return None
    except json.JSONDecodeError:
        print("❌ Error al procesar el archivo de licencias")
        return None
    except Exception as e:
        print(f"❌ Error inesperado: {str(e)}")
        return None


# ════════════════════════════════════════════════════════════════════════
# VERIFICACIÓN PRINCIPAL
# ════════════════════════════════════════════════════════════════════════

def verificar_licencia(cuit):
    """
    Verifica el estado de la licencia para un CUIT.
    
    Estrategia:
      1. Intenta online → si funciona, valida y actualiza cache.
      2. Si falla online → recurre al cache:
         - Si hay cache <7 días: arranca con el cache (modo offline).
         - Si hay cache >7 días: bloquea, pide conectar.
         - Si no hay cache: bloquea, necesita internet sí o sí.
    
    Args:
        cuit (str): CUIT del cliente a verificar
        
    Returns:
        dict: {
            'valida': bool,
            'activo': bool,
            'mora': bool,
            'razon_social': str,
            'mensaje': str,
            'tipo_bloqueo': str,  # 'sin_bloqueo', 'mora', 'bloqueado', 'error', 'no_encontrada', 'offline_expirado'
            'modo_offline': bool, # NUEVO: True si está usando el cache local
            'dias_desde_verificacion': int  # NUEVO: solo si modo_offline
        }
    """
    resultado = {
        'valida': False,
        'activo': False,
        'mora': False,
        'razon_social': '',
        'mensaje': '',
        'tipo_bloqueo': 'error',
        'modo_offline': False,
        'contacto': {
            'email': CONTACTO_EMAIL,
            'telefono': CONTACTO_TELEFONO,
            'web': CONTACTO_WEB
        }
    }
    
    print(f"🔐 Verificando licencia para CUIT: {cuit}")
    print(f"📡 Verificando licencias...")
    
    # ─── PASO 1: Intentar verificación ONLINE ───
    licencias = descargar_licencias()
    
    if licencias is not None:
        # ✅ Internet OK → verificar normalmente y actualizar cache
        return _verificar_online(cuit, licencias, resultado)
    
    # ─── PASO 2: Falló online → intentar OFFLINE con cache ───
    print("📴 Sin conexión con servidor de licencias, evaluando modo offline...")
    
    if MODO_PRUEBA:
        print("⚠️ MODO PRUEBA: Permitiendo acceso sin verificación")
        resultado['valida'] = True
        resultado['activo'] = True
        resultado['tipo_bloqueo'] = 'sin_bloqueo'
        resultado['mensaje'] = "Modo prueba - Sin verificación"
        return resultado
    
    return _verificar_offline(cuit, resultado)


def _verificar_online(cuit, licencias, resultado):
    """Verificación normal con datos descargados online.
    Si la licencia es válida, actualiza el cache."""
    
    # Buscar el CUIT en las licencias
    if cuit not in licencias.get('clientes', {}):
        resultado['tipo_bloqueo'] = 'no_encontrada'
        resultado['mensaje'] = f"No se encontró una licencia válida para este sistema (CUIT: {cuit})."
        return resultado
    
    # Obtener datos del cliente
    cliente = licencias['clientes'][cuit]
    resultado['razon_social'] = cliente.get('razon_social', 'Sin nombre')
    resultado['activo'] = cliente.get('activo', False)
    resultado['mora'] = cliente.get('mora', False)
    resultado['fecha_vencimiento'] = cliente.get('fecha_vencimiento', '')
    resultado['observaciones'] = cliente.get('observaciones', '')
    
    # Verificar si está activo
    if not resultado['activo']:
        resultado['valida'] = False
        resultado['tipo_bloqueo'] = 'bloqueado'
        resultado['mensaje'] = "El sistema se encuentra desactivado."
        # NO guardamos cache de licencia bloqueada (no queremos permitir offline si está bloqueada online)
        return resultado
    
    # Verificar mora
    if resultado['mora']:
        resultado['valida'] = True  # Puede usar el sistema pero con advertencia
        resultado['tipo_bloqueo'] = 'mora'
        resultado['mensaje'] = "Su período de mantenimiento del sistema se encuentra vencido."
        # Guardamos cache de mora (puede operar offline en estado mora)
        _guardar_cache(cuit, cliente)
        return resultado
    
    # Todo OK
    resultado['valida'] = True
    resultado['activo'] = True
    resultado['tipo_bloqueo'] = 'sin_bloqueo'
    resultado['mensaje'] = "Licencia válida"
    
    # Guardamos cache de licencia válida
    _guardar_cache(cuit, cliente)
    
    print(f"✅ Licencia válida (online): {resultado['razon_social']}")
    
    return resultado


def _verificar_offline(cuit, resultado):
    """Falló la verificación online. Intentamos con el cache local.
    Si el cache es viejo (>7 días) o no existe, bloqueamos."""
    
    cache = _leer_cache(cuit)
    
    if cache is None:
        # No hay cache: primera instalación o cache borrado
        resultado['tipo_bloqueo'] = 'error'
        resultado['mensaje'] = (
            "No se pudo verificar la licencia del sistema. "
            "Verifique su conexión a internet e intente nuevamente."
        )
        return resultado
    
    dias = cache['dias_desde_verificacion']
    horas = cache['horas_desde_verificacion']
    
    if dias > DIAS_GRACIA_OFFLINE:
        # Cache muy viejo: hay que conectarse a internet sí o sí
        resultado['tipo_bloqueo'] = 'offline_expirado'
        resultado['mensaje'] = (
            f"Hace {dias} días que no se valida la licencia. "
            f"Conecte el sistema a internet para continuar usándolo."
        )
        resultado['dias_desde_verificacion'] = dias
        return resultado
    
    # Cache válido (menos de 7 días) → arrancar con el cache
    resultado['razon_social'] = cache.get('razon_social', '')
    resultado['activo'] = cache.get('activo', False)
    resultado['mora'] = cache.get('mora', False)
    resultado['fecha_vencimiento'] = cache.get('fecha_vencimiento', '')
    resultado['observaciones'] = cache.get('observaciones', '')
    resultado['modo_offline'] = True
    resultado['dias_desde_verificacion'] = dias
    
    if not resultado['activo']:
        # Esto no debería pasar porque NO guardamos cache de bloqueadas, pero por las dudas
        resultado['valida'] = False
        resultado['tipo_bloqueo'] = 'bloqueado'
        resultado['mensaje'] = "El sistema se encuentra desactivado."
        return resultado
    
    # Determinar mensaje según mora
    if horas < 24:
        tiempo_str = f"hace {horas} horas"
    else:
        tiempo_str = f"hace {dias} día(s)"
    
    if resultado['mora']:
        resultado['valida'] = True
        resultado['tipo_bloqueo'] = 'mora'
        resultado['mensaje'] = (
            f"Su período de mantenimiento se encuentra vencido. "
            f"Modo offline (última verificación: {tiempo_str})."
        )
    else:
        resultado['valida'] = True
        resultado['tipo_bloqueo'] = 'sin_bloqueo'
        resultado['mensaje'] = f"Licencia válida (modo offline, última verificación: {tiempo_str})"
    
    print(f"📴 Modo offline: licencia desde cache ({dias} días). {resultado['razon_social']}")
    
    return resultado


# Test del módulo
if __name__ == '__main__':
    import sys
    
    print("="*60)
    print("  VERIFICADOR DE LICENCIAS - TEST")
    print("="*60)
    
    # CUIT de prueba
    cuit_test = "27333429433"
    
    if len(sys.argv) > 1:
        cuit_test = sys.argv[1]
    
    resultado = verificar_licencia(cuit_test)
    
    print("\n" + "="*60)
    print("RESULTADO:")
    print("="*60)
    print(f"Válida: {resultado['valida']}")
    print(f"Activo: {resultado['activo']}")
    print(f"Mora: {resultado['mora']}")
    print(f"Tipo Bloqueo: {resultado['tipo_bloqueo']}")
    print(f"Modo Offline: {resultado.get('modo_offline', False)}")
    if resultado.get('modo_offline'):
        print(f"Días desde verificación: {resultado.get('dias_desde_verificacion', '?')}")
    print(f"Razón Social: {resultado['razon_social']}")
    print(f"Mensaje: {resultado['mensaje']}")
    print("="*60)
