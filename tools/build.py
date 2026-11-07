#!/usr/bin/env python3
"""Erzeugt itinerary.md + maps/*.kml|gpx aus data/reise.yaml und data/orte_*.json.

Aufruf (aus dem Repo-Root):   python3 tools/build.py            # mit OSRM (Route/km)
                              python3 tools/build.py --offline  # nur Cache benutzen

- Jeder Ort steht genau einmal in data/orte_*.json (id, lat, lon, ziel, konfidenz ...).
- data/reise.yaml referenziert Orte nur über ihre id.
- Links sind Google-Maps-Navigationslinks (dir/?api=1&destination=lat,lon) -> Tippen = Navi startet.
- Fahrstrecken (km/h) kommen von OSRM (router.project-osrm.org) und werden in
  data/route_cache.json gecacht, damit der Build reproduzierbar und offline-fähig ist.
"""
import datetime as dt
import glob
import json
import os
import sys
import urllib.request

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
MAPS = os.path.join(ROOT, "maps")
CACHE_FILE = os.path.join(DATA, "route_cache.json")
OFFLINE = "--offline" in sys.argv

WOCHENTAG = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
NACHT_TYP = {"frei": "🆓 Freiplatz", "doc": "🏕 DOC", "hp": "🏠 Holiday Park",
             "hotel": "🏨 Hotel", "faehre": "⛴ Fähre", "camp": "🏕 Campground"}
VERS_TYP = {"tanken": "⛽ Tanken", "dump": "🚻 Dump", "waesche": "🧺 Wäsche",
            "wasser": "💧 Wasser", "einkauf": "🛒 Einkauf"}


# ---------------------------------------------------------------- Daten laden
def load_orte():
    orte = {}
    for fn in sorted(glob.glob(os.path.join(DATA, "orte_*.json"))):
        for o in json.load(open(fn, encoding="utf-8")):
            if o["id"] in orte:
                print(f"WARN doppelte Orts-id {o['id']} ({fn})", file=sys.stderr)
            o["_datei"] = os.path.basename(fn)
            orte[o["id"]] = o
    return orte


ORTE = load_orte()
REISE = yaml.safe_load(open(os.path.join(DATA, "reise.yaml"), encoding="utf-8"))
FEHLEND = set()


def ort(oid):
    o = ORTE.get(oid)
    if o is None:
        FEHLEND.add(oid)
    return o


def nav(oid):
    o = ort(oid)
    if not o:
        return None
    return f"https://www.google.com/maps/dir/?api=1&destination={o['lat']:.6f},{o['lon']:.6f}&travelmode=driving"


def link(oid, label=None):
    o = ort(oid)
    label = label or (o["name"] if o else oid)
    u = nav(oid)
    if not u:
        return f"{label} ⚠️(Koordinate fehlt)"
    warn = " ⚠️" if o.get("konfidenz") == "niedrig" else ""
    return f"[{label}]({u}){warn}"


# ---------------------------------------------------------------- Routing
try:
    CACHE = json.load(open(CACHE_FILE, encoding="utf-8"))
except (OSError, ValueError):
    CACHE = {}


def route(a, b):
    """Liefert dict(km, min, geom[(lat,lon)]) zwischen zwei Orts-ids oder None."""
    oa, ob = ort(a), ort(b)
    if not oa or not ob or a == b:
        return None
    key = f"{oa['lat']:.5f},{oa['lon']:.5f}|{ob['lat']:.5f},{ob['lon']:.5f}"
    if key in CACHE:
        return CACHE[key]
    if OFFLINE:
        return None
    url = ("https://router.project-osrm.org/route/v1/driving/"
           f"{oa['lon']},{oa['lat']};{ob['lon']},{ob['lat']}?overview=simplified&geometries=geojson")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "nz27-trip-planner/1.0"})
        d = json.load(urllib.request.urlopen(req, timeout=20))
        if d.get("code") != "Ok":
            return None
        r = d["routes"][0]
        res = {"km": round(r["distance"] / 1000), "min": round(r["duration"] / 60),
               "geom": [[round(lat, 5), round(lon, 5)] for lon, lat in r["geometry"]["coordinates"]]}
    except Exception as e:  # noqa: BLE001
        print(f"WARN OSRM {a}->{b}: {e}", file=sys.stderr)
        return None
    CACHE[key] = res
    return res


def dauer(minuten):
    h, m = divmod(minuten, 60)
    return f"{h}:{m:02d} h"


# ---------------------------------------------------------------- Tage aufbereiten
START = dt.date.fromisoformat(str(REISE["meta"]["start"]))
TAGE = REISE["tage"]
for i, t in enumerate(TAGE):
    t["_datum"] = START + dt.timedelta(days=t["tag"] - 1)
    t["_wt"] = WOCHENTAG[t["_datum"].weekday()]
    prev = TAGE[i - 1]["nacht"]["ort"] if i > 0 and TAGE[i - 1].get("nacht") else REISE["meta"].get("startort")
    t["_von"] = t.get("start_ort") or prev
    ziel = t["nacht"]["ort"] if t.get("nacht") else t.get("end_ort")
    t["_route"] = None
    if not t.get("faehre") and t["_von"] and ziel:
        pts = [t["_von"], *t.get("via", []), ziel]
        legs = [route(a, b) for a, b in zip(pts, pts[1:])]
        if all(legs):
            t["_route"] = {"km": sum(x["km"] for x in legs), "min": sum(x["min"] for x in legs),
                           "geom": [g for x in legs for g in x["geom"]]}


def ddmm(d):
    return d.strftime("%d.%m.")


# ---------------------------------------------------------------- itinerary.md
def md():
    m = REISE["meta"]
    out = [f"# {m['titel']}", "",
           "> **Generiert** aus `data/reise.yaml` + `data/orte_*.json` mit `python3 tools/build.py`.",
           "> Nicht von Hand editieren – Änderungen in den Daten machen und neu bauen.", "",
           "**Zeitraum:** 19.03.–18.05.2027 · 61 Tage · Abholung Christchurch, Rückgabe Auckland  ",
           "**Links:** Jeder Ortsname ist ein Google-Maps-**Navigationslink** zum Parkplatz/zur Zufahrt (antippen → Navi startet).  ",
           "**km/Fahrzeit:** Direktstrecke Übernachtung→Übernachtung laut OSRM, ohne Abstecher. ⚠️ = Koordinate unsicher.", ""]

    out += ["## Fixpunkte (gebucht)", ""]
    for f in REISE["fixpunkte"]:
        out.append(f"- **{f['datum']}** – {f['was']}" + (f" · {link(f['ort'])}" if f.get("ort") else ""))
    out.append("")

    out += ["## Grundsätze", ""] + [f"- {g}" for g in REISE["grundsaetze"]] + [""]

    out += ["## Übersicht", "", "| Tag | Datum | Etappe | km / Fahrt | Nacht |", "|---|---|---|---|---|"]
    for t in TAGE:
        r = t["_route"]
        km = f"{r['km']} km / {dauer(r['min'])}" if r else ("Fähre" if t.get("faehre") else "–")
        n = t.get("nacht")
        nacht = (ort(n["ort"])["name"] if n and ort(n["ort"]) else (n["ort"] if n else "–"))
        out.append(f"| {t['tag']} | {t['_wt']} {ddmm(t['_datum'])} | {t['titel']} | {km} | {nacht} |")
    out.append("")

    out += ["## Tag für Tag", ""]
    insel = None
    for t in TAGE:
        if t.get("insel") != insel:
            insel = t.get("insel")
            out += [f"### {'Südinsel' if insel == 'sued' else 'Nordinsel'}", ""]
        r = t["_route"]
        kopf = f"#### Tag {t['tag']} · {t['_wt']} {ddmm(t['_datum'])} — {t['titel']}"
        out.append(kopf)
        out.append("")
        if r:
            out.append(f"**Fahrt:** {r['km']} km · {dauer(r['min'])} reine Fahrzeit"
                       + (f" · {t['fahrt']}" if t.get("fahrt") else ""))
        elif t.get("fahrt"):
            out.append(f"**Fahrt:** {t['fahrt']}")
        out.append("")
        if t.get("programm"):
            out.append("**Programm:**")
            for p in t["programm"]:
                opt = " *(optional)*" if p.get("optional") else ""
                lbl = link(p["ort"]) if p.get("ort") else ""
                txt = p.get("text", "")
                out.append(f"- {lbl}{opt}{' – ' if lbl and txt else ''}{txt}")
            out.append("")
        n = t.get("nacht")
        if n:
            out.append(f"**Nacht:** {NACHT_TYP.get(n['typ'], n['typ'])} {link(n['ort'])}"
                       + (f" – {n['hinweis']}" if n.get("hinweis") else ""))
            for a in n.get("alternativen", []):
                out.append(f"  - Alternative: {NACHT_TYP.get(a['typ'], a['typ'])} {link(a['ort'])}"
                           + (f" – {a['hinweis']}" if a.get("hinweis") else ""))
            out.append("")
        if t.get("versorgung"):
            v = " · ".join(f"{VERS_TYP.get(x['typ'], x['typ'])}: {link(x['ort']) if x.get('ort') else x.get('text', '')}"
                           for x in t["versorgung"])
            out += [f"**Versorgung:** {v}", ""]
        for h in t.get("hinweise", []):
            out.append(f"> ⚠️ {h}")
        if t.get("hinweise"):
            out.append("")
        if t.get("buchung"):
            out += [f"**Buchung:** {'; '.join(t['buchung'])}", ""]

    tot = sum(t["_route"]["km"] for t in TAGE if t["_route"])
    out += ["---", f"*Gesamtstrecke (nur Übernachtung→Übernachtung): ~{tot} km.*", ""]
    return "\n".join(out)


# ---------------------------------------------------------------- KML / GPX
def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


GPX_HEAD = ('<?xml version="1.0" encoding="UTF-8"?>\n<gpx version="1.1" creator="nz27" '
            'xmlns="http://www.topografix.com/GPX/1/1">')


def kml(name, pins, lines=(), color="ff0000ff"):
    o = ['<?xml version="1.0" encoding="UTF-8"?>', '<kml xmlns="http://www.opengis.net/kml/2.2"><Document>',
         f"<name>{esc(name)}</name>",
         f'<Style id="p"><IconStyle><color>{color}</color></IconStyle></Style>',
         f'<Style id="l"><LineStyle><color>{color}</color><width>3</width></LineStyle></Style>']
    for nm, desc, lat, lon in pins:
        o.append(f"<Placemark><name>{esc(nm)}</name><styleUrl>#p</styleUrl><description>{esc(desc)}</description>"
                 f"<Point><coordinates>{lon:.6f},{lat:.6f},0</coordinates></Point></Placemark>")
    for nm, pts in lines:
        c = " ".join(f"{lon:.5f},{lat:.5f},0" for lat, lon in pts)
        o.append(f"<Placemark><name>{esc(nm)}</name><styleUrl>#l</styleUrl>"
                 f"<LineString><tessellate>1</tessellate><coordinates>{c}</coordinates></LineString></Placemark>")
    o.append("</Document></kml>")
    return "\n".join(o)


def gpx(name, pins, lines=()):
    o = [GPX_HEAD, f"<metadata><name>{esc(name)}</name></metadata>"]
    for nm, desc, lat, lon in pins:
        o.append(f'<wpt lat="{lat:.6f}" lon="{lon:.6f}"><name>{esc(nm)}</name><desc>{esc(desc)}</desc></wpt>')
    for nm, pts in lines:
        o.append(f"<trk><name>{esc(nm)}</name><trkseg>")
        o += [f'<trkpt lat="{lat:.5f}" lon="{lon:.5f}"/>' for lat, lon in pts]
        o.append("</trkseg></trk>")
    o.append("</gpx>")
    return "\n".join(o)


def pin(oid, label, extra=""):
    o = ort(oid)
    if not o:
        return None
    desc = f"{o.get('ziel', '')} {extra}\n{nav(oid)}".strip()
    return (label, desc, o["lat"], o["lon"])


def maps():
    layers = {"stellplaetze": [], "alternativen": [], "attraktionen": [], "versorgung": [], "fixpunkte": []}
    seen = set()

    def add(layer, p, key):
        if p and key not in seen:
            seen.add(key)
            layers[layer].append(p)

    for f in REISE["fixpunkte"]:
        if f.get("ort"):
            add("fixpunkte", pin(f["ort"], f"{f['datum']} {f['was']}"), ("fix", f["ort"]))
    for t in TAGE:
        tg = f"T{t['tag']} {ddmm(t['_datum'])}"
        n = t.get("nacht")
        if n:
            add("stellplaetze", pin(n["ort"], f"{tg} {ort(n['ort'])['name'] if ort(n['ort']) else n['ort']}"),
                ("n", n["ort"], t["tag"]))
            for a in n.get("alternativen", []):
                add("alternativen", pin(a["ort"], f"{tg} Alt: {ort(a['ort'])['name'] if ort(a['ort']) else a['ort']}"),
                    ("a", a["ort"]))
        for p in t.get("programm", []):
            if p.get("ort"):
                o = ort(p["ort"])
                add("attraktionen", pin(p["ort"], f"{tg} {o['name'] if o else p['ort']}" + (" (opt.)" if p.get("optional") else "")),
                    ("p", p["ort"]))
        for v in t.get("versorgung", []):
            if v.get("ort"):
                o = ort(v["ort"])
                add("versorgung", pin(v["ort"], f"{VERS_TYP.get(v['typ'], v['typ'])}: {o['name'] if o else v['ort']}"),
                    ("v", v["ort"]))
    lines = [(f"T{t['tag']} {t['titel']}", t["_route"]["geom"]) for t in TAGE if t["_route"]]
    farben = {"stellplaetze": "ff0000ff", "alternativen": "ff7f7fff", "attraktionen": "ff00b000",
              "versorgung": "ffff8000", "fixpunkte": "ff00d7ff"}
    for f in glob.glob(os.path.join(MAPS, "nz_*.kml")) + glob.glob(os.path.join(MAPS, "nz_*.gpx")):
        os.remove(f)
    for k, pins in layers.items():
        open(os.path.join(MAPS, f"nz_{k}.kml"), "w", encoding="utf-8").write(kml(f"NZ27 {k}", pins, color=farben[k]))
        open(os.path.join(MAPS, f"nz_{k}.gpx"), "w", encoding="utf-8").write(gpx(f"NZ27 {k}", pins))
    open(os.path.join(MAPS, "nz_route.kml"), "w", encoding="utf-8").write(kml("NZ27 Route", [], lines, "ff800080"))
    open(os.path.join(MAPS, "nz_route.gpx"), "w", encoding="utf-8").write(gpx("NZ27 Route", [], lines))
    return {k: len(v) for k, v in layers.items()}


# ---------------------------------------------------------------- main
if __name__ == "__main__":
    text = md()
    open(os.path.join(ROOT, "itinerary.md"), "w", encoding="utf-8").write(text)
    stats = maps()
    json.dump(CACHE, open(CACHE_FILE, "w", encoding="utf-8"), indent=0)
    json.dump({t["tag"]: t["_route"] for t in TAGE if t["_route"]},
              open(os.path.join(DATA, "tage_routen.json"), "w", encoding="utf-8"))
    niedrig = sorted({oid for oid, o in ORTE.items() if o.get("konfidenz") == "niedrig"})
    print("Layer:", stats)
    print(f"Orte gesamt: {len(ORTE)} · unsicher: {len(niedrig)}")
    if FEHLEND:
        print("FEHLENDE Orts-ids:", ", ".join(sorted(FEHLEND)))
        sys.exit(1)
