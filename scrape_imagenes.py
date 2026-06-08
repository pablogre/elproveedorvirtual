#!/usr/bin/env python3
"""
Descarga todas las imágenes de https://blending.com.ar/elproveedorvirtual
Uso:
    pip install requests beautifulsoup4
    python scrape_imagenes.py
Las imágenes quedan en la carpeta ./imagenes_proveedorvirtual/
"""

import os
import re
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

URL = "https://blending.com.ar/elproveedorvirtual"
OUT = "imagenes_proveedorvirtual"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/124.0 Safari/537.36"
}

os.makedirs(OUT, exist_ok=True)

print(f"[*] Descargando {URL}")
r = requests.get(URL, headers=HEADERS, timeout=30)
r.raise_for_status()
soup = BeautifulSoup(r.text, "html.parser")

urls = set()

# <img src> y lazy-load (data-src, data-lazy-src, srcset)
for img in soup.find_all("img"):
    for attr in ("src", "data-src", "data-lazy-src", "data-original"):
        v = img.get(attr)
        if v:
            urls.add(urljoin(URL, v))
    srcset = img.get("srcset") or img.get("data-srcset")
    if srcset:
        for part in srcset.split(","):
            u = part.strip().split(" ")[0]
            if u:
                urls.add(urljoin(URL, u))

# imágenes de fondo en style="background-image:url(...)"
for el in soup.find_all(style=True):
    for m in re.findall(r'url\(["\']?(.*?)["\']?\)', el["style"]):
        urls.add(urljoin(URL, m))

# url(...) dentro de <style> y CSS embebido
for m in re.findall(r'url\(["\']?(.*?)["\']?\)', r.text):
    if re.search(r'\.(png|jpe?g|gif|webp|svg|bmp|ico|avif)', m, re.I):
        urls.add(urljoin(URL, m))

# filtrar solo imágenes
exts = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".bmp", ".ico", ".avif")
urls = {u for u in urls if urlparse(u).path.lower().endswith(exts)}

print(f"[*] {len(urls)} imágenes encontradas")

ok = 0
for i, u in enumerate(sorted(urls), 1):
    try:
        name = os.path.basename(urlparse(u).path) or f"img_{i}"
        dest = os.path.join(OUT, name)
        # evitar pisar nombres repetidos
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
