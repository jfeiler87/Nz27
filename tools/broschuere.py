#!/usr/bin/env python3
"""Baut die Broschüre als EINE selbständige HTML-Datei: broschuere/nz27-broschuere.html

Aufruf aus dem Repo-Root:  python3 tools/broschuere.py
- Liest data/reise.yaml, data/orte_*.json, data/route_cache.json, optional data/ablauf.yaml,
  data/vorschlaege.yaml, data/bilder_*.json.
- Lädt Bilder (einmalig) nach .cache/img/, verkleinert sie und bettet sie als WebP ein.
- Lädt einmalig eine NZ-Küstenlinie (Natural Earth 1:10m) nach .cache/ für die Offline-Karten.
Ausgabe und Cache sind per .gitignore vom (öffentlichen) Repo ausgenommen.
"""
import base64
import datetime as dt
import glob
import hashlib
import html
import io
import json
import math
import os
import sys
import urllib.request

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
CACHE = os.path.join(ROOT, ".cache")
OUT = os.path.join(ROOT, "broschuere", "nz27-broschuere.html")
UA = {"User-Agent": "nz27-trip-planner/1.0 (private)"}
WT = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
NACHT = {"frei": "Freiplatz", "doc": "DOC-Platz", "hp": "Holiday Park", "camp": "Campingplatz", "hotel": "Hotel"}
VERS = {"tanken": "⛽ Tanken", "dump": "🚻 Dump", "waesche": "🧺 Wäsche", "wasser": "💧 Wasser", "einkauf": "🛒 Einkauf"}


def load_yaml(name, default):
    p = os.path.join(DATA, name)
    return yaml.safe_load(open(p, encoding="utf-8")) if os.path.exists(p) else default


ORTE = {}
for fn in sorted(glob.glob(os.path.join(DATA, "orte_*.json"))):
    for o in json.load(open(fn, encoding="utf-8")):
        ORTE[o["id"]] = o
REISE = load_yaml("reise.yaml", {})
ABLAUF = load_yaml("ablauf.yaml", {}) or {}
VORSCHLAEGE = load_yaml("vorschlaege.yaml", []) or []
ROUTES = json.load(open(os.path.join(DATA, "route_cache.json"), encoding="utf-8"))
BILDER = {}
for fn in glob.glob(os.path.join(DATA, "bilder_*.json")):
    BILDER.update(json.load(open(fn, encoding="utf-8")))
START = dt.date.fromisoformat(str(REISE["meta"]["start"]))


def nav(oid):
    o = ORTE[oid]
    return f"https://www.google.com/maps/dir/?api=1&destination={o['lat']:.6f},{o['lon']:.6f}&travelmode=driving"


# ------------------------------------------------------------------ Sonne (NOAA-Näherung)
def sonne(lat, lon, datum):
    """Sonnenauf-/untergang in NZ-Ortszeit (NZDT bis 04.04.2027, danach NZST)."""
    n = datum.timetuple().tm_yday
    g = 2 * math.pi / 365 * (n - 1)
    eqt = 229.18 * (0.000075 + 0.001868 * math.cos(g) - 0.032077 * math.sin(g)
                    - 0.014615 * math.cos(2 * g) - 0.040849 * math.sin(2 * g))
    decl = (0.006918 - 0.399912 * math.cos(g) + 0.070257 * math.sin(g) - 0.006758 * math.cos(2 * g)
            + 0.000907 * math.sin(2 * g) - 0.002697 * math.cos(3 * g) + 0.00148 * math.sin(3 * g))
    la = math.radians(lat)
    cos_ha = math.cos(math.radians(90.833)) / (math.cos(la) * math.cos(decl)) - math.tan(la) * math.tan(decl)
    ha = math.degrees(math.acos(max(-1, min(1, cos_ha))))
    tz = 13 if datum < dt.date(2027, 4, 4) else 12
    auf = 720 - 4 * (lon + ha) - eqt + tz * 60
    unter = 720 - 4 * (lon - ha) - eqt + tz * 60
    f = lambda m: f"{int(m // 60):02d}:{int(m % 60):02d}"  # noqa: E731
    return f(auf), f(unter)


# ------------------------------------------------------------------ Bilder
def bild_data_uri(url):
    os.makedirs(os.path.join(CACHE, "img"), exist_ok=True)
    fn = os.path.join(CACHE, "img", hashlib.sha1(url.encode()).hexdigest()[:16] + ".webp")
    if not os.path.exists(fn):
        try:
            from PIL import Image
            raw = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30).read()
            im = Image.open(io.BytesIO(raw)).convert("RGB")
            im.thumbnail((820, 820))
            im.save(fn, "WEBP", quality=55, method=6)
        except Exception as e:  # noqa: BLE001
            print(f"WARN Bild {url[:80]}: {e}", file=sys.stderr)
            open(fn + ".fail", "w").close()
            return None
    if not os.path.exists(fn):
        return None
    return "data:image/webp;base64," + base64.b64encode(open(fn, "rb").read()).decode()


def bilder_fuer(oid, maxn=2):
    out = []
    for b in BILDER.get(oid, [])[:maxn]:
        if os.path.exists(os.path.join(CACHE, "img", hashlib.sha1(b["url"].encode()).hexdigest()[:16] + ".webp.fail")):
            continue
        uri = bild_data_uri(b["url"])
        if uri:
            out.append({"src": uri, "credit": b.get("credit", ""), "motiv": b.get("motiv", ""), "seite": b.get("seite", "")})
    return out


# ------------------------------------------------------------------ Küstenlinie
def kueste():
    fn = os.path.join(CACHE, "nz_land.json")
    if not os.path.exists(fn):
        os.makedirs(CACHE, exist_ok=True)
        url = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_10m_land.geojson"
        try:
            gj = json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120))
        except Exception as e:  # noqa: BLE001
            print(f"WARN Küstenlinie: {e}", file=sys.stderr)
            return []
        polys = []
        for f in gj["features"]:
            g = f["geometry"]
            rings = g["coordinates"] if g["type"] == "Polygon" else [r for p in g["coordinates"] for r in p]
            for r in rings:
                if all(165 < x < 179.5 and -48 < y < -34 for x, y in r[:: max(1, len(r) // 20)]):
                    if len(r) > 30:
                        polys.append([[round(y, 3), round(x, 3)] for x, y in r[::3]])
        json.dump(polys, open(fn, "w"))
    return json.load(open(fn))


# ------------------------------------------------------------------ Daten zusammenstellen
def route_fuer(a, b):
    if a not in ORTE or b not in ORTE or a == b:
        return None
    oa, ob = ORTE[a], ORTE[b]
    return ROUTES.get(f"{oa['lat']:.5f},{oa['lon']:.5f}|{ob['lat']:.5f},{ob['lon']:.5f}")


def ortinfo(oid):
    o = ORTE.get(oid)
    if not o:
        return {"id": oid, "name": oid, "fehlt": True}
    return {"id": oid, "name": o["name"], "ziel": o.get("ziel", ""), "hinweis": o.get("hinweis", ""),
            "unsicher": o.get("konfidenz") == "niedrig", "nav": nav(oid), "lat": o["lat"], "lon": o["lon"],
            "bilder": bilder_fuer(oid)}


tage = []
prev = REISE["meta"].get("startort")
for t in REISE["tage"]:
    d = START + dt.timedelta(days=t["tag"] - 1)
    von = t.get("start_ort") or prev
    n = t.get("nacht")
    ziel = n["ort"] if n else t.get("end_ort")
    r = None if t.get("faehre") else route_fuer(von, ziel)
    sp = ORTE.get(ziel) or ORTE.get(von)
    auf, unter = sonne(sp["lat"], sp["lon"], d) if sp else ("", "")
    tage.append({
        "tag": t["tag"], "datum": f"{WT[d.weekday()]} {d:%d.%m.}", "iso": d.isoformat(), "titel": t["titel"],
        "insel": t.get("insel"), "fahrt": t.get("fahrt", ""), "km": r["km"] if r else None,
        "min": r["min"] if r else None, "geom": r["geom"] if r else [],
        "sonne": [auf, unter], "hinweise": t.get("hinweise", []), "buchung": t.get("buchung", []),
        "programm": [{"text": p.get("text", ""), "optional": bool(p.get("optional")),
                      "ort": ortinfo(p["ort"]) if p.get("ort") else None} for p in t.get("programm", [])],
        "nacht": None if not n else {"typ": NACHT.get(n["typ"], n["typ"]), "hinweis": n.get("hinweis", ""),
                                     "ort": ortinfo(n["ort"]),
                                     "alternativen": [{"typ": NACHT.get(a["typ"], a["typ"]), "hinweis": a.get("hinweis", ""),
                                                       "ort": ortinfo(a["ort"])} for a in n.get("alternativen", [])]},
        "versorgung": [{"typ": VERS.get(v["typ"], v["typ"]), "text": v.get("text", ""),
                        "ort": ortinfo(v["ort"]) if v.get("ort") else None} for v in t.get("versorgung", [])],
        "ablauf": (ABLAUF.get(t["tag"]) or {}),
        "vorschlaege": [{"id": f"v{t['tag']}-{v['ort']}", "titel": v["titel"], "text": v.get("text", ""),
                         "aufwand": v.get("aufwand", ""), "quelle": v.get("quelle", ""), "ort": ortinfo(v["ort"])}
                        for v in VORSCHLAEGE if v.get("tag") == t["tag"]],
    })
    prev = ziel or prev

DATEN = {
    "titel": REISE["meta"]["titel"], "gebaut": dt.datetime.now().strftime("%d.%m.%Y %H:%M"),
    "fixpunkte": [{"datum": f["datum"], "was": f["was"], "ort": ortinfo(f["ort"]) if f.get("ort") else None}
                  for f in REISE["fixpunkte"]],
    "grundsaetze": REISE.get("grundsaetze", []), "tage": tage, "kueste": kueste(),
}

# ------------------------------------------------------------------ HTML
TEMPLATE = open(os.path.join(ROOT, "tools", "broschuere_vorlage.html"), encoding="utf-8").read()
html_out = TEMPLATE.replace("/*__DATEN__*/null", json.dumps(DATEN, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/"))
html_out = html_out.replace("__TITEL__", html.escape(DATEN["titel"]))
os.makedirs(os.path.dirname(OUT), exist_ok=True)
open(OUT, "w", encoding="utf-8").write(html_out)
nb = sum(len(p["ort"]["bilder"]) for t in tage for p in t["programm"] if p["ort"] and "bilder" in p["ort"])
print(f"{OUT}: {os.path.getsize(OUT) / 1e6:.1f} MB · {len(tage)} Tage · {nb} Programm-Bilder · "
      f"{sum(len(t['vorschlaege']) for t in tage)} Vorschläge · {sum(1 for t in tage if t['ablauf'])} Tage mit Ablauf")
