"""Build docs/app/ (Slipway Web, for Android Chrome and desktop Chrome/Edge) from tools/web/.

Output is one self-contained index.html plus PWA files. The Felucca libraries in tools/web/felucca
are GPL-3.0; the output is therefore GPL-3.0 too (LICENSE-GPL-3.0.txt, NOTICE.txt).
"""
import base64, io, json, pathlib, re
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
WEB = ROOT / "tools" / "web"
OUT = ROOT / "docs" / "app"
OUT.mkdir(parents=True, exist_ok=True)

def lib(name):
    src = (WEB / "felucca" / name).read_text(encoding="utf-8")
    return re.sub(r"^export\s+", "", src, flags=re.M)

logo = Image.open(ROOT / "slipway" / "slipway.png").convert("RGBA")
def png(size):
    b = io.BytesIO(); logo.resize((size, size), Image.LANCZOS).save(b, "PNG", optimize=True); return b.getvalue()
(OUT / "icon-192.png").write_bytes(png(192))
(OUT / "icon-512.png").write_bytes(png(512))
logo_uri = "data:image/png;base64," + base64.b64encode(png(96)).decode()

html = (WEB / "template.html").read_text(encoding="utf-8")
html = html.replace("/*LIB*/", lib("fm1ota.js") + "\n" + lib("fm1pkg.js")).replace("__LOGO__", logo_uri)
(OUT / "index.html").write_text(html, encoding="utf-8")

(OUT / "manifest.webmanifest").write_text(json.dumps({
    "name": "Slipway", "short_name": "Slipway", "description": "Firmware loader for the M-VAVE FM-1",
    "start_url": "./", "scope": "./", "display": "standalone", "background_color": "#151213", "theme_color": "#151213",
    "icons": [{"src": "icon-192.png", "sizes": "192x192", "type": "image/png"},
              {"src": "icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any maskable"}]}, indent=2))

(OUT / "sw.js").write_text("""// cache the app shell so it opens offline (firmware files are never cached here)
const C = "slipway-web-1";
self.addEventListener("install", (e) => { e.waitUntil(caches.open(C).then((c) => c.addAll(["./", "index.html", "manifest.webmanifest", "icon-192.png"]))); self.skipWaiting(); });
self.addEventListener("activate", (e) => { e.waitUntil(caches.keys().then((ks) => Promise.all(ks.filter((k) => k !== C).map((k) => caches.delete(k))))); self.clients.claim(); });
self.addEventListener("fetch", (e) => { if (e.request.method !== "GET") return;
  e.respondWith(fetch(e.request).then((r) => { const cp = r.clone(); caches.open(C).then((c) => c.put(e.request, cp)); return r; }).catch(() => caches.match(e.request))); });
""")

(OUT / "NOTICE.txt").write_text("""Slipway Web
Copyright (c) 2026 Discodave-Glitch. Licensed GPL-3.0 (see LICENSE-GPL-3.0.txt).

Includes fm1ota.js and fm1pkg.js from Felucca's web installer:
Copyright (C) 2026 Leo Kuroshita (@kurogedelic), Hugelton Instruments, GPL-3.0-only.
https://github.com/hugelton/Felucca

The rest of Slipway (the desktop app) is MIT and lives outside docs/app/.
""")
print("built", OUT, len(html) // 1024, "KB")
