#!/usr/bin/env python3
#!/usr/bin/env python3
"""
1) Baja las imagenes del catalogo nombrandolas con su descripcion,
   CORTANDO el nombre justo despues del codigo:
       "ALF BON O BON TRIPLE NEGROx60g (cod 735 ).jpeg"
   (sin precio ni "Pedir"/"Sin stock")
2) Extrae el codigo del articulo del patron "(cod NNN)"
3) Genera:
     - mapeo.csv               -> para que revises codigo <-> archivo
     - updates_imagen_url.sql  -> UPDATEs listos para correr en DBeaver

OJO: borra/vacia la carpeta productos_img antes de re-correr,
     asi no te quedan las imagenes viejas con el nombre sucio.

Uso:
    python scrape_y_sql.py
"""

import os
import re
import csv
import time
import requests
from collections import Counter
from urllib.parse import urljoin, urlparse
from playwright.sync_api import sync_playwright

# ==================== CONFIG ====================
URL          = "https://blending.com.ar/elproveedorvirtual"
OUT_IMG      = "productos_img"
RUTA_WEB     = "/static/productos_img/"
TABLA        = "producto"
CAMPO_CODIGO = "codigo"          # <-- cambiar si tu campo se llama distinto
CAMPO_IMAGEN = "imagen_url"
# ===============================================

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
EXTS = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".avif")

# regex del codigo: (cod 735) (cod. 736) (cod:735) (COD 735 )
RE_COD = re.compile(r'\(\s*cod\.?\:?\s*(\d+)\s*\)', re.IGNORECASE)

os.makedirs(OUT_IMG, exist_ok=True)


def sanitizar(nombre):
    """Quita SOLO los caracteres ilegales de Windows. Mantiene ( ) espacios . , etc."""
    t = nombre.replace("\n", " ").replace("\r", " ")
    t = re.sub(r'[\\/:*?"<>|]+', ' ', t)
    t = re.sub(r'\s+', ' ', t).strip()
    t = t.rstrip(". ")
    return t[:150]


JS = r"""
() => {
  const out = [];
  document.querySelectorAll('img').forEach(img => {
    const src = img.currentSrc || img.src ||
                img.getAttribute('data-src') ||
                img.getAttribute('data-lazy-src') || '';
    if (!src) return;
    let cardText = '';
    let el = img.parentElement;
    for (let i = 0; i < 4 && el; i++) {
      const txt = (el.innerText || '').trim();
      if (txt && txt.length < 200) { cardText = txt; break; }
      el = el.parentElement;
    }
    out.push({
      src: src,
      alt: img.alt || '',
      title: img.title || '',
      aria: img.getAttribute('aria-label') || '',
      cardText: cardText
    });
  });
  return out;
}
"""

print(f"[*] Abriendo {URL}")
items = []
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(user_agent=UA)
    page.goto(URL, wait_until="networkidle", timeout=60000)

    print("[*] Scrolleando para cargar imagenes diferidas...")
    for _ in range(20):
        page.mouse.wheel(0, 2000)
        time.sleep(0.5)
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    time.sleep(2)

    items = page.evaluate(JS)
    browser.close()

filas = []          # (codigo, descripcion_cortada, url)
sin_codigo = 0
vistos_url = set()

for it in items:
    u = urljoin(URL, it["src"])
    if not u.startswith("http") or not urlparse(u).path.lower().endswith(EXTS):
        continue
    if u in vistos_url:
        continue

    candidatos = [it["alt"], it["title"], it["aria"], it["cardText"]]
    desc = None
    cod = None
    for c in candidatos:
        if not c:
            continue
        m = RE_COD.search(c)
        if m:
            desc = c[:m.end()]      # <<<<<< CORTA justo despues de "(cod NNN)"
            cod = m.group(1)
            break
    if not cod:
        sin_codigo += 1
        continue

    vistos_url.add(u)
    filas.append((cod, desc, u))

print(f"[*] {len(filas)} imagenes de producto con codigo | {sin_codigo} sin codigo (descartadas)")

# aviso de codigos duplicados (mismo cod en dos productos de la web)
dups = [c for c, n in Counter(c for c, _, _ in filas).items() if n > 1]
if dups:
    print(f"[!] OJO codigos repetidos en la web (revisar manualmente): {sorted(dups)}")

mapeo = []
usados = {}
errores = []
for i, (cod, desc, u) in enumerate(sorted(filas, key=lambda x: int(x[0])), 1):
    ext = os.path.splitext(urlparse(u).path)[1].lower() or ".jpg"
    base = sanitizar(desc)
    name = base + ext
    if name in usados:
        usados[name] += 1
        name = f"{base}_{usados[name]}{ext}"
    else:
        usados[name] = 0
    dest = os.path.join(OUT_IMG, name)
    try:
        r = requests.get(u, headers={"User-Agent": UA}, timeout=30)
        r.raise_for_status()
        with open(dest, "wb") as f:
            f.write(r.content)
        mapeo.append((cod, name, RUTA_WEB + name, u))
        print(f"  [{i}/{len(filas)}] cod {cod:>5}  OK  {name}")
    except Exception as e:
        errores.append((cod, u, str(e)))
        print(f"  [{i}/{len(filas)}] cod {cod:>5}  ERROR {u} -> {e}")

with open("mapeo.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f, delimiter=";")
    w.writerow(["codigo", "archivo", "imagen_url", "url_origen"])
    w.writerows(mapeo)

with open("updates_imagen_url.sql", "w", encoding="utf-8") as f:
    f.write("-- Generado automaticamente. Revisar mapeo.csv antes de ejecutar.\n")
    f.write("-- 1) BACKUP recomendado antes de correr:\n")
    f.write(f"--    CREATE TABLE {TABLA}_backup_img AS SELECT * FROM {TABLA};\n")
    f.write("-- 2) Ejecutar como SCRIPT COMPLETO (Alt+Shift+X en DBeaver), no de a una.\n")
    f.write("-- 3) Verificar el COUNT del final y recien ahi descomentar COMMIT.\n\n")
    f.write("START TRANSACTION;\n\n")
    for cod, name, imagen_url, _ in mapeo:
        path_sql = imagen_url.replace("'", "''")
        f.write(f"UPDATE {TABLA} SET {CAMPO_IMAGEN} = '{path_sql}' "
                f"WHERE {CAMPO_CODIGO} = {cod};\n")
    f.write("\n-- Cuantas filas quedaron con imagen asignada:\n")
    f.write(f"SELECT COUNT(*) AS actualizados FROM {TABLA} "
            f"WHERE {CAMPO_IMAGEN} LIKE '{RUTA_WEB}%';\n\n")
    f.write("-- Si todo OK:\n-- COMMIT;\n-- Si algo salio mal:\n-- ROLLBACK;\n")

print(f"\n[*] Listo:")
print(f"    - {len(mapeo)} imagenes en ./{OUT_IMG}/")
print(f"    - mapeo.csv")
print(f"    - updates_imagen_url.sql")
if errores:
    print(f"    - {len(errores)} con error de descarga (404 en origen): "
          f"{[c for c, _, _ in errores]}")