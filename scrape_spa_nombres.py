#!/usr/bin/env python3
"""
Descarga las imágenes de la SPA nombrándolas con su DESCRIPCIÓN
(alt / title / texto del contenedor que las rodea) en vez del nombre del archivo.

Instalación (una sola vez):
    pip install playwright requests
    python -m playwright install chromium

Uso:
    python scrape_spa_nombres.py

Las imágenes quedan en ./imagenes_proveedorvirtual/
"""

import os
import re
import time
import requests
from urllib.parse import urljoin, urlparse
from playwright.sync_api import sync_playwright

URL = "https://blending.com.ar/elproveedorvirtual"
OUT = "imagenes_proveedorvirtual"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
EXTS = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".avif")

os.makedirs(OUT, exist_ok=True)


def sanitizar(texto, fallback):
    """Convierte una descripción en un nombre de archivo válido para Windows."""
    if not texto:
        return fallback
    t = texto.strip()
    # sacar caracteres prohibidos en Windows  \ / : * ? " < > |
    t = re.sub(r'[\\/:*?"<>|]+', ' ', t)
    t = re.sub(r'\s+', ' ', t).strip()
    t = t[:80].strip()  # cortar largo
    return t or fallback


# JS que recorre cada <img> visible y devuelve su src + la mejor descripción
JS = r"""
() => {
  const out = [];
  document.querySelectorAll('img').forEach(img => {
    const src = img.currentSrc || img.src ||
                img.getAttribute('data-src') ||
                img.getAttribute('data-lazy-src') || '';
    if (!src) return;

    // 1) alt  2) title  3) aria-label
    let desc = img.alt || img.title || img.getAttribute('aria-label') || '';

    // 4) si no hay, subir por los padres buscando texto (la "card")
    if (!desc.trim()) {
      let el = img.parentElement;
      for (let i = 0; i < 4 && el; i++) {
        const txt = (el.innerText || '').trim();
        if (txt && txt.length > 1 && txt.length < 120) { desc = txt; break; }
        el = el.parentElement;
      }
    }
    out.push({ src, desc: (desc || '').split('\n')[0].trim() });
  });
  return out;
}
"""

items = []
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(user_agent=UA)
    print(f"[*] Abriendo {URL}")
    page.goto(URL, wait_until="networkidle", timeout=60000)

    print("[*] Scrolleando para cargar imágenes diferidas...")
    for _ in range(15):
        page.mouse.wheel(0, 2000)
        time.sleep(0.6)
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    time.sleep(2)

    items = page.evaluate(JS)
    browser.close()

# normalizar URLs y filtrar a imágenes reales (descartar data: URIs)
vistos = set()
limpios = []
for it in items:
    u = urljoin(URL, it["src"])
    if not u.startswith("http"):
        continue
    if not urlparse(u).path.lower().endswith(EXTS):
        continue
    if u in vistos:
        continue
    vistos.add(u)
    limpios.append({"url": u, "desc": it["desc"]})

print(f"[*] {len(limpios)} imágenes encontradas")

ok = 0
usados = {}
for i, it in enumerate(limpios, 1):
    u = it["url"]
    ext = os.path.splitext(urlparse(u).path)[1].lower() or ".jpg"
    base = sanitizar(it["desc"], f"imagen_{i}")

    # evitar nombres repetidos
    name = base + ext
    if name in usados:
        usados[name] += 1
        name = f"{base}_{usados[name]}{ext}"
    else:
        usados[name] = 0
    dest = os.path.join(OUT, name)

    try:
        resp = requests.get(u, headers={"User-Agent": UA}, timeout=30)
        resp.raise_for_status()
        with open(dest, "wb") as f:
            f.write(resp.content)
        ok += 1
        print(f"  [{i}/{len(limpios)}] OK  {name}")
    except Exception as e:
        print(f"  [{i}/{len(limpios)}] ERROR {u} -> {e}")

print(f"\n[*] Listo: {ok}/{len(limpios)} descargadas en ./{OUT}/")
