"""
====================================================================
lector_factura.py (v3) - TODO EN UN ARCHIVO
====================================================================

Version mejorada despues de analizar una factura RIOSMA real.

Mejoras v3 sobre v2:
- Reconoce CANTIDADES CON COMA DECIMAL argentina (33,155 = 33.155)
- Distingue PERC. IVA (3%) de PERCEP. IIBB (separadas)
- Entiende la estructura de columnas de facturas con DTO. %
- Validacion incluye verificar que la suma de percepciones matchee

Uso:
    python lector_factura.py

Archivo esperado en Escritorio:
    factura_test.jpg / .jpeg / .png / .pdf
====================================================================
"""
import os
import sys
import json
import base64
import io
import subprocess
from anthropic import Anthropic
from PIL import Image


# ====================================================================
# CONFIGURACION
# ====================================================================
try:
    from config_cliente import ANTHROPIC_API_KEY
except ImportError:
    ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')

MODEL = "claude-sonnet-4-5-20250929"
MAX_IMAGE_SIZE_MB = 5


# ====================================================================
# PROMPT V3
# ====================================================================

PROMPT_EXTRACCION = """Sos un experto en extraccion de datos de facturas de proveedores argentinas.

Analiza la factura en la imagen y devuelve UN JSON estricto.

============ REGLAS CRITICAS ============

1) FORMATO DE NUMEROS EN ARGENTINA:
   - El separador de MILES es el PUNTO (.)
   - El separador DECIMAL es la COMA (,)
   - Ejemplo 1: "1.234,56" = mil doscientos treinta y cuatro con 56 centavos = 1234.56 JSON
   - Ejemplo 2: "33,155" = treinta y tres con 155 milesimos = 33.155 JSON (es un peso en kg!)
   - Ejemplo 3: "22.920" = veintidos mil novecientos veinte = 22920 JSON
   - ANTE LA DUDA: si ves un numero con coma decimal en columna "CANTIDAD" de un proveedor
     de alimentos/fiambres/carnes/frutas, SIEMPRE es kg con decimales. Ej: "33,155" = 33.155 kg.
   - NUNCA interpretes "33,155" como 33155.

2) NO INVENTES datos. Si un campo NO aparece, pon null.
   - NUNCA copies un valor de otro campo para rellenar.
   - Ej: si no hay vencimiento CAE, pon null (NO copies fecha emision).
   - Lee los numeros EXACTOS. No aproximes. Si no podes leer con claridad, pon null
     ANTES de inventar.

3) EXTRAE TODOS los items del detalle, sin omitir ninguno.

4) BONIFICACIONES/DESCUENTOS POR ITEM (muy comun en Argentina):
   Muchas facturas tienen columnas: CANTIDAD | P.UNITARIO | DTO% | P.FINAL | SUBTOTAL.
   - "porcentaje_bonificacion" = el % de la columna DTO% (ej: 13,00 = 13.0)
   - "precio_unitario" = el de la primera columna (ANTES del descuento)
   - "subtotal" = el IMPORTE FINAL de la ultima columna (ya con descuento aplicado)
   - La suma de todos los "subtotal" DEBE coincidir con "subtotal_sin_iva" del pie
     (tolerancia 1 peso).

5) ALICUOTA IVA por item:
   - Si la factura es "A" y muestra "IVA 21,00%" al pie, poné alicuota_iva=21 en TODOS.
   - Si muestra "IVA 10,5%", usá 10.5.
   - NO pongas null si en el pie esta claro que todo tiene la misma alicuota.

6) PERCEPCIONES — LAS MAS IMPORTANTES PARA ARGENTINA:
   Las facturas argentinas tienen un pie con varias columnas. Tipicamente:
     SUBTOTAL | FLETE | ABASTO | IVA | PER.IVA | PERCEP. IIBB | TOTAL
   
   Cada columna con "PER." o "PERCEP." es una percepcion DISTINTA:
   
   a) "PER. IVA" o "PERCEP. IVA" (ej: RG 3130): es Percepcion de IVA.
      Tipicamente tiene su % al lado (3,00% en el caso comun).
      Va en: {"descripcion": "Percepcion IVA", "importe": XXXX}
   
   b) "PERCEP. IIBB" o "PER. IIBB" o "Percepcion IIBB": es Percepcion de Ingresos Brutos.
      Puede decir la jurisdiccion (Bs.As., Santa Fe, CABA).
      Va en: {"descripcion": "Percepcion IIBB [jurisdiccion]", "importe": XXXX}
   
   c) "PER. GANANCIAS" o similar: es Percepcion de Ganancias.
   
   CADA UNA DE ESTAS ES UN ELEMENTO SEPARADO EN EL ARRAY "percepciones".
   NUNCA LAS SUMES JUNTAS. NUNCA CONFUNDAS UNA POR LA OTRA.
   
   DIFERENCIA CLAVE vs BONIFICACION:
   - BONIFICACION/DESCUENTO: REDUCEN el neto. Suelen estar POR ITEM como DTO%.
   - PERCEPCION: se SUMAN al total final. Estan siempre en el PIE de la factura.

7) VERIFICACION ARITMETICA (hacela mentalmente ANTES de responder):
   subtotal_sin_iva - bonificacion_total + iva_21 + iva_10_5 + SUMA(percepciones) = total
   Si no cuadra por mas de $1, RE-REVISA cada numero. Probablemente una percepcion
   esta mal identificada.

8) PUNTO DE VENTA Y NUMERO: sin ceros a la izquierda, como enteros.
   "00042-00656150" -> punto_venta: 42, numero_comprobante: 656150

9) "tipo" debe ser UNA LETRA: "A", "B", o "C". Lee el recuadro grande con la letra.

10) FECHAS: formato YYYY-MM-DD. La factura las trae como DD/MM/YYYY — convertilas.

11) CAE: es un numero largo de 14 digitos. Suele decir "C.A.E." o "CAE:" al pie.
    Leelo con MUCHO cuidado digito por digito. NO estimes.

============ ESQUEMA DE SALIDA ============

{
  "numero_factura": "00005-00018247",
  "punto_venta": 5,
  "numero_comprobante": 18247,
  "fecha_emision": "2026-04-15",
  "tipo": "A",
  "tipo_comprobante_desc": "Factura A",
  "proveedor_cuit": "30-68731043-4",
  "proveedor_razon_social": "DISTRIBUIDORA SAN MARTIN S.A.",
  "condicion_venta": "CONTADO",
  "remito_nro": "0900451893",
  "items": [
    {
      "codigo": "0101",
      "descripcion": "MILAN GRANDE 214",
      "cantidad": 33.155,
      "unidad_medida": "KG",
      "precio_unitario": 13016.88,
      "porcentaje_bonificacion": 13.0,
      "alicuota_iva": 21,
      "subtotal": 376764.66
    }
  ],
  "subtotales": {
    "subtotal_sin_iva": 3270714.24,
    "bonificacion_total": null,
    "iva_21": 686850.00,
    "iva_10_5": null,
    "iva_27": null,
    "exento": null
  },
  "percepciones": [
    {"descripcion": "Percepcion IVA RG 3130 (3%)", "importe": 98121.42},
    {"descripcion": "Percepcion IIBB Bs.As.", "importe": 163535.71}
  ],
  "total": 4219221.37,
  "cae": "86139158394464",
  "fecha_vto_cae": "2026-04-25"
}

RESPONDE SOLO EL JSON, sin marcadores de codigo ni texto adicional."""


# ====================================================================
# FUNCIONES DEL MOTOR
# ====================================================================

def _preparar_imagen(contenido, content_type):
    if content_type == 'application/pdf' or contenido[:4] == b'%PDF':
        try:
            from pdf2image import convert_from_bytes
            imagenes = convert_from_bytes(contenido, dpi=200, first_page=1, last_page=1)
            if not imagenes:
                raise ValueError("PDF sin paginas")
            buf = io.BytesIO()
            imagenes[0].save(buf, format='PNG', optimize=True)
            contenido = buf.getvalue()
            media_type = 'image/png'
        except ImportError:
            raise RuntimeError("pdf2image no instalado. pip install pdf2image")
        except Exception as e:
            if 'poppler' in str(e).lower():
                raise RuntimeError(
                    "Poppler no instalado o no encontrado en el PATH.\n"
                    "Bajar de https://github.com/oschwartz10612/poppler-windows/releases\n"
                    "Extraer en C:\\poppler y agregar C:\\poppler\\Library\\bin al PATH."
                )
            raise
    elif content_type in ('image/jpeg', 'image/jpg'):
        media_type = 'image/jpeg'
    elif content_type == 'image/png':
        media_type = 'image/png'
    elif content_type == 'image/webp':
        media_type = 'image/webp'
    else:
        if contenido[:3] == b'\xff\xd8\xff':
            media_type = 'image/jpeg'
        elif contenido[:8] == b'\x89PNG\r\n\x1a\n':
            media_type = 'image/png'
        else:
            raise ValueError("Formato no soportado: " + str(content_type))

    if len(contenido) > MAX_IMAGE_SIZE_MB * 1024 * 1024:
        img = Image.open(io.BytesIO(contenido))
        img.thumbnail((2000, 2000), Image.LANCZOS)
        buf = io.BytesIO()
        if media_type == 'image/png':
            img.save(buf, format='PNG', optimize=True)
        else:
            img.save(buf, format='JPEG', quality=85, optimize=True)
        contenido = buf.getvalue()

    return media_type, base64.b64encode(contenido).decode('utf-8')


def extraer_factura_proveedor(imagen_bytes, content_type='image/png', api_key=None):
    key = api_key or ANTHROPIC_API_KEY
    if not key:
        return {
            'success': False, 'data': None,
            'error': 'ANTHROPIC_API_KEY no configurada en config_cliente.py',
            'validaciones': {}, 'tokens_usados': {},
        }

    try:
        media_type, b64 = _preparar_imagen(imagen_bytes, content_type)
    except Exception as e:
        return {
            'success': False, 'data': None,
            'error': 'Error preparando imagen: ' + str(e),
            'validaciones': {}, 'tokens_usados': {},
        }

    client = Anthropic(api_key=key)
    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=4000,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image", "source": {"type": "base64",
                                                   "media_type": media_type, "data": b64}},
                    {"type": "text", "text": PROMPT_EXTRACCION},
                ],
            }],
        )
    except Exception as e:
        return {
            'success': False, 'data': None,
            'error': 'Error API Anthropic: ' + str(e),
            'validaciones': {}, 'tokens_usados': {},
        }

    texto = response.content[0].text.strip()
    if texto.startswith('```'):
        texto = texto.split('```')[1]
        if texto.startswith('json'):
            texto = texto[4:]
        texto = texto.strip()

    try:
        data = json.loads(texto)
    except json.JSONDecodeError as e:
        return {
            'success': False, 'data': None,
            'error': 'JSON invalido en respuesta: ' + str(e),
            'raw_response': texto[:500],
            'validaciones': {},
            'tokens_usados': {'input': response.usage.input_tokens,
                              'output': response.usage.output_tokens},
        }

    return {
        'success': True,
        'data': data,
        'error': None,
        'validaciones': validar_consistencia(data),
        'tokens_usados': {'input': response.usage.input_tokens,
                          'output': response.usage.output_tokens},
    }


def validar_consistencia(data, tolerancia=1.0):
    avisos = []
    try:
        suma_items = sum(float(i.get('subtotal', 0)) for i in data.get('items', []))
        subtotal_decl = float(data.get('subtotales', {}).get('subtotal_sin_iva') or 0)
        if subtotal_decl and abs(suma_items - subtotal_decl) > tolerancia:
            avisos.append(
                "Suma de items (" + format(suma_items, ',.2f') + ") no coincide con subtotal declarado (" +
                format(subtotal_decl, ',.2f') + "). Diferencia: $" +
                format(abs(suma_items - subtotal_decl), ',.2f')
            )

        st = data.get('subtotales', {}) or {}
        neto = float(st.get('subtotal_sin_iva') or 0) - float(st.get('bonificacion_total') or 0)
        iva_total = sum([float(st.get('iva_21') or 0),
                         float(st.get('iva_10_5') or 0),
                         float(st.get('iva_27') or 0)])
        perc_total = sum(float(p.get('importe') or 0) for p in data.get('percepciones', []))
        total_calculado = neto + iva_total + perc_total
        total_declarado = float(data.get('total') or 0)
        if total_declarado and abs(total_calculado - total_declarado) > tolerancia:
            avisos.append(
                "Total declarado (" + format(total_declarado, ',.2f') + ") no cuadra con neto + IVA + percepciones (" +
                format(total_calculado, ',.2f') + "). Diferencia: $" +
                format(abs(total_calculado - total_declarado), ',.2f')
            )

        if not data.get('items'):
            avisos.append("No se detectaron items en la factura")

        items_sin_iva = sum(1 for i in data.get('items', []) if i.get('alicuota_iva') is None)
        if items_sin_iva:
            avisos.append(
                str(items_sin_iva) + " de " + str(len(data.get('items', []))) +
                " items no tienen alicuota_iva detectada."
            )

        # NUEVO en v3: revisar cantidades que parezcan enteros gigantes (posible error de decimal)
        for idx, it in enumerate(data.get('items', []), 1):
            cant = it.get('cantidad')
            if cant and cant > 1000 and cant == int(cant):
                avisos.append(
                    "Item #" + str(idx) + " (" + str(it.get('descripcion', ''))[:30] +
                    ") tiene cantidad=" + str(cant) +
                    " (posible error: puede ser " + str(cant/1000) + " kg)"
                )

    except (TypeError, ValueError, KeyError) as e:
        avisos.append("Error validando: " + str(e))

    return {'ok': len(avisos) == 0, 'avisos': avisos}


def estimar_costo_usd(tokens_usados):
    inp = tokens_usados.get('input', 0)
    out = tokens_usados.get('output', 0)
    return (inp * 3 + out * 15) / 1_000_000


def encontrar_factura():
    home = os.path.expanduser("~")
    posibles_bases = [
        os.path.join(home, "Desktop"),
        os.path.join(home, "OneDrive", "Desktop"),
        os.path.join(home, "OneDrive", "Escritorio"),
        os.path.join(home, "Escritorio"),
        os.path.join(home, "Documents"),
        os.path.join(home, "OneDrive", "Documents"),
        os.path.join(home, "Documentos"),
    ]

    if os.name == "nt":
        try:
            result = subprocess.run(
                ["powershell", "-Command", '[Environment]::GetFolderPath("Desktop")'],
                capture_output=True, text=True, timeout=5
            )
            ruta_real = result.stdout.strip()
            if ruta_real and ruta_real not in posibles_bases:
                posibles_bases.insert(0, ruta_real)
        except Exception:
            pass

    nombres = ["factura_test.pdf", "factura_test.PDF",
               "factura_test.jpg", "factura_test.jpeg",
               "factura_test.JPG", "factura_test.JPEG",
               "factura_test.png", "factura_test.PNG"]

    for base in posibles_bases:
        if not os.path.isdir(base):
            continue
        for nombre in nombres:
            ruta = os.path.join(base, nombre)
            if os.path.exists(ruta):
                return ruta
    return None


# ====================================================================
# TEST PRINCIPAL
# ====================================================================

def main():
    print("=" * 70)
    print(" TEST DEL LECTOR DE FACTURAS DE PROVEEDOR (v3)")
    print("=" * 70)

    ruta_factura = encontrar_factura()
    if not ruta_factura:
        print("\nERROR: No se encontro factura_test en el Escritorio.")
        print("Coloca la factura con nombre: factura_test.pdf (o .jpg/.png)")
        sys.exit(1)

    print("\n[1/3] Archivo encontrado:")
    print("      " + ruta_factura)
    print("      Tamano: {:.1f} KB".format(os.path.getsize(ruta_factura) / 1024))

    print("\n[2/3] Verificando API key...")
    if not ANTHROPIC_API_KEY or ANTHROPIC_API_KEY.startswith("PEGA") or len(ANTHROPIC_API_KEY) < 50:
        print("      ERROR: ANTHROPIC_API_KEY no configurada")
        sys.exit(1)
    print("      OK (empieza con: " + ANTHROPIC_API_KEY[:15] + "...)")

    print("\n[3/3] Procesando factura con Claude Vision... (10-30 seg)")
    with open(ruta_factura, "rb") as f:
        imagen_bytes = f.read()

    ext = os.path.splitext(ruta_factura)[1].lower()
    if ext == ".pdf":
        content_type = "application/pdf"
    elif ext == ".png":
        content_type = "image/png"
    else:
        content_type = "image/jpeg"

    resultado = extraer_factura_proveedor(imagen_bytes, content_type)

    print("\n" + "=" * 70)
    if resultado["success"]:
        print(" EXTRACCION EXITOSA")
        print("=" * 70)
        data = resultado["data"]

        print("\nDATOS EXTRAIDOS:")
        print("-" * 70)
        print("  Proveedor:       " + str(data.get("proveedor_razon_social", "?")))
        print("  CUIT:            " + str(data.get("proveedor_cuit", "?")))
        print("  Numero:          " + str(data.get("numero_factura", "?")))
        print("  Fecha:           " + str(data.get("fecha_emision", "?")))
        print("  Tipo:            " + str(data.get("tipo_comprobante_desc", "?")))
        print("  Subtotal:        $ " + format(data.get("subtotales", {}).get("subtotal_sin_iva") or 0, ',.2f'))
        print("  IVA 21%:         $ " + format(data.get("subtotales", {}).get("iva_21") or 0, ',.2f'))

        # Mostrar percepciones separadas
        percepciones = data.get("percepciones", []) or []
        if percepciones:
            print("  PERCEPCIONES:")
            for p in percepciones:
                print("    - " + str(p.get("descripcion", "?")) + ": $ " +
                      format(p.get("importe") or 0, ',.2f'))
        else:
            print("  PERCEPCIONES:   ninguna detectada")

        print("  Total:           $ " + format(data.get("total") or 0, ',.2f'))
        print("  CAE:             " + str(data.get("cae", "?")))
        print("  Items:           " + str(len(data.get("items", []))) + " detectados")

        print("\nITEMS DETECTADOS:")
        print("-" * 70)
        for i, it in enumerate(data.get("items", []), 1):
            desc = (it.get("descripcion") or "")[:38]
            print("  " + str(i) + ". " + desc +
                  " | Cant: " + str(it.get("cantidad")) +
                  " | P.U: $" + str(it.get("precio_unitario")) +
                  " | Dto: " + str(it.get("porcentaje_bonificacion")) + "%" +
                  " | Sub: $" + str(it.get("subtotal")))

        print("\nVALIDACIONES AUTOMATICAS:")
        print("-" * 70)
        val = resultado["validaciones"]
        if val["ok"]:
            print("  OK - Todos los numeros cuadran correctamente")
        else:
            print("  Se detectaron inconsistencias:")
            for aviso in val["avisos"]:
                print("    - " + aviso)

        print("\nCOSTO:")
        print("-" * 70)
        costo = estimar_costo_usd(resultado["tokens_usados"])
        print("  Tokens input/output: " + str(resultado["tokens_usados"].get("input")) +
              " / " + str(resultado["tokens_usados"].get("output")))
        print("  Costo aprox: US$ " + "{:.6f}".format(costo))

        print("\n" + "=" * 70)
        print(" JSON COMPLETO")
        print("=" * 70)
        print(json.dumps(data, indent=2, ensure_ascii=False, default=str))
    else:
        print(" ERROR EN LA EXTRACCION")
        print("=" * 70)
        print("\nError: " + str(resultado["error"]))
        if "raw_response" in resultado:
            print("\nRespuesta cruda:")
            print(resultado["raw_response"])


if __name__ == "__main__":
    main()