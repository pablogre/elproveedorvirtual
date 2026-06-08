#!/usr/bin/env python3
"""
Descarga todas las imágenes de una SPA (sitio que carga imágenes con JavaScript).
Renderiza la página con un navegador real, scrollea para disparar lazy-load
y baja todo lo que aparezca.

Instalación (una sola vez):
    pip install playwright requests
    python -m playwright install chromium

Uso:
    python scrape_spa.py

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
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/124.0 Safari/537.36"
}
EXTS = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".bmp", ".ico", ".avif")

os.makedirs(OUT, exist_ok=True)
urls = set()

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(user_agent=HEADERS["User-Agent"])

    # Capturar TODA imagen que el navegador pida por red (lo más confiable)
    def on_response(resp):
        ct = resp.headers.get("content-type", "")
        u = resp.url
        if ct.startswith("image/") or urlparse(u).path.lower().endswith(EXTS):
            urls.add(u)
    page.on("response", on_response)

    print(f"[*] Abriendo {URL}")
    page.goto(URL, wait_until="networkidle", timeout=60000)

    # Scroll para disparar lazy-load
    print("[*] Scrolleando para cargar imágenes diferidas...")
    for _ in range(15):
        page.mouse.wheel(0, 2000)
        time.sleep(0.6)
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    time.sleep(2)

    # Además, leer el DOM ya renderizado
    html = page.content()
    for img in re.findall(r'<img[^>]+>', html, re.I):
        for m in re.findall(r'(?:src|data-src|data-lazy-src|data-original)=["\'](.*?)["\']', img, re.I):
            urls.add(urljoin(URL, m))
        for ss in re.findall(r'srcset=["\'](.*?)["\']', img, re.I):
            for part in ss.split(","):
                u = part.strip().split(" ")[0]
                if u:
                    urls.add(urljoin(URL, u))
    for m in re.findall(r'url\(["\']?(.*?)["\']?\)', html):
        if re.search(r'\.(png|jpe?g|gif|webp|svg|bmp|ico|avif)', m, re.I):
            urls.add(urljoin(URL, m))

    browser.close()

# filtrar (sacar data: URIs y dejar solo imágenes)
urls = {u for u in urls if u.startswith("http")
        and urlparse(u).path.lower().endswith(EXTS)}

print(f"[*] {len(urls)} imágenes encontradas")

ok = 0
for i, u in enumerate(sorted(urls), 1):
    try:
        name = os.path.basename(urlparse(u).path) or f"img_{i}"
        dest = os.path.join(OUT, name)
        base, ext = os.path.splitext(dest)
        n = 1
        while os.path.exists(dest):
            dest = f"{base}_{n}{ext}"
            n += 1
        resp = requests.get(u, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        with open(dest, "wb") as f:
            f.write(resp.content)
        ok += 1
        print(f"  [{i}/{len(urls)}] OK  {name}")
    except Exception as e:
        print(f"  [{i}/{len(urls)}] ERROR {u} -> {e}")

print(f"\n[*] Listo: {ok}/{len(urls)} descargadas en ./{OUT}/")
