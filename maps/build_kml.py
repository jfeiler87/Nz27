import re, json, urllib.request, urllib.parse, time, os

PATH = "/home/hermes/nz_trip_2027/itinerary.md"
OUTDIR = "/home/hermes/nz_trip_2027/maps"

text = open(PATH, encoding="utf-8").read()

def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def parse_coord(url):
    if not url: return None
    m = re.search(r'@(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)', url)
    if m: return (float(m.group(1)), float(m.group(2)))
    m = re.search(r'query=(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)', url)
    if m: return (float(m.group(1)), float(m.group(2)))
    return None

# ---------- geocoding ----------
def geocode(q):
    url = "https://nominatim.openstreetmap.org/search?format=json&limit=1&countrycodes=nz&q=" + urllib.parse.quote(q)
    req = urllib.request.Request(url, headers={"User-Agent": "nz-trip-planner/1.0"})
    try:
        data = json.load(urllib.request.urlopen(req, timeout=15))
        if data:
            return (float(data[0]["lat"]), float(data[0]["lon"]))
    except Exception:
        pass
    return None

# ---------- parse sections ----------
headers = list(re.finditer(r'^### Tag (\d+) · ([0-9.]+) — (.+)$', text, re.M))
stops = []
for i, m in enumerate(headers):
    day = int(m.group(1)); date = m.group(2); title = m.group(3).strip()
    start = m.end()
    end = headers[i+1].start() if i+1 < len(headers) else len(text)
    sec = text[start:end]
    sm = re.search(r'\*\*🏕 Stellplatz:\*\*\s*(.+)', sec)
    sline = sm.group(1) if sm else ""
    lm = re.search(r'\(https://www\.google\.com/maps/[^\)]+\)', sline)
    url = lm.group(0)[1:-1] if lm else None
    name = re.split(r'[·\[]', sline)[0].strip()
    coord = parse_coord(url)
    am = re.search(r'🎯 Attraktionen:\*\*(.*?)(?=\*\*[⚠🛠]|###|\Z)', sec, re.S)
    attractions = []
    if am:
        for b in re.finditer(r'^- \*\*(.+?)\*\*(.*?)(?=\n- |\Z)', am.group(1), re.S | re.M):
            an = b.group(1).strip()
            rest = b.group(2)
            rm = re.search(r'Rating (\d+)/10', rest)
            rating = rm.group(1) if rm else None
            alm = re.search(r'\(https://www\.google\.com/maps/[^\)]+\)', rest)
            aurl = alm.group(0)[1:-1] if alm else None
            acoord = parse_coord(aurl) if aurl else None
            attractions.append({"name": an, "rating": rating, "coord": acoord, "url": aurl})
    vm = re.search(r'🛠 Versorgung in der Nähe:\*\*\s*(.+)', sec)
    supply = []
    if vm:
        typemap = {"🧺": "Wäsche", "🚻": "Sanidump", "💧": "Frischwasser", "⛽": "Tanken"}
        for p in re.split(r'\s\u00b7\s', vm.group(1)):
            p = p.strip()
            if not p:
                continue
            emoji = p[0] if p[0] in typemap else None
            supply.append({"type": typemap.get(emoji, "Versorgung"), "text": p})
    stops.append({"day": day, "date": date, "title": title, "name": name,
                  "url": url, "coord": coord, "attractions": attractions, "supply": supply})

for s in stops:
    if not s["coord"]:
        c = geocode(f"{s['name']}, {s['title']}, New Zealand") or geocode(f"{s['title']}, New Zealand")
        s["coord"] = c
        time.sleep(1.1)
for s in stops:
    if not s["coord"] and s["day"] == 61:
        s["coord"] = (-36.8485, 174.7633)

# ---------- KML helpers ----------
def pm_point(name, desc, lat, lon, style=None):
    s = f'      <Placemark>\n        <name>{esc(name)}</name>\n'
    if style: s += f'        <styleUrl>#{style}</styleUrl>\n'
    s += f'        <description>{esc(desc)}</description>\n'
    s += f'        <Point><coordinates>{lon:.6f},{lat:.6f},0</coordinates></Point>\n      </Placemark>'
    return s

def pm_line(name, coords, style=None):
    c = " ".join(f"{lon:.6f},{lat:.6f},0" for lat, lon in coords)
    s = f'      <Placemark>\n        <name>{esc(name)}</name>\n'
    if style: s += f'        <styleUrl>#{style}</styleUrl>\n'
    s += '        <LineString><tessellate>1</tessellate><coordinates>' + c + '</coordinates></LineString>\n      </Placemark>'
    return s

def style_def(sid, color, line=False, width=3):
    if line:
        return f'    <Style id="{sid}"><LineStyle><color>{color}</color><width>{width}</width></LineStyle></Style>'
    return f'    <Style id="{sid}"><IconStyle><color>{color}</color><scale>1.0</scale></IconStyle></Style>'

def kml_doc(name, desc, pms, styles):
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<kml xmlns="http://www.opengis.net/kml/2.2">\n  <Document>\n'
            f'    <name>{esc(name)}</name>\n    <description>{esc(desc)}</description>\n'
            + "\n".join(styles) + "\n" + "\n".join(pms) + "\n  </Document>\n</kml>")

def dayrange(days):
    return f"{days[0]}-{days[-1]}" if len(days) > 1 else str(days[0])

# ---------- GPX helpers ----------
GPX_HEAD = ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<gpx version="1.1" creator="nz-trip-planner" '
            'xmlns="http://www.topografix.com/GPX/1/1" '
            'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
            'xsi:schemaLocation="http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd">')

def gpx_wpt_file(name, desc, wpts):
    out = [GPX_HEAD, f'  <metadata><name>{esc(name)}</name></metadata>']
    for label, d, lat, lon in wpts:
        out.append(f'  <wpt lat="{lat:.6f}" lon="{lon:.6f}">')
        out.append(f'    <name>{esc(label)}</name>')
        out.append(f'    <desc>{esc(d)}</desc>')
        out.append('  </wpt>')
    out.append('</gpx>')
    return "\n".join(out)

def gpx_track_file(name, desc, legs):
    out = [GPX_HEAD, f'  <metadata><name>{esc(name)}</name></metadata>', '  <trk>']
    out.append(f'    <name>{esc(name)}</name>')
    out.append(f'    <desc>{esc(desc)}</desc>')
    out.append('    <trkseg>')
    for leg in legs:
        for lat, lon in leg:
            out.append(f'      <trkpt lat="{lat:.6f}" lon="{lon:.6f}"></trkpt>')
    out.append('    </trkseg>')
    out.append('  </trk>')
    out.append('</gpx>')
    return "\n".join(out)

# ---------- 1) Stellplätze ----------
STELL = "ff0000ff"
stell_pins = []
prev = None
for s in stops:
    if not s["coord"]:
        continue
    if prev and prev["coord"] == s["coord"]:
        prev["days"].append(s["day"])
    else:
        prev = {"days": [s["day"]], "date": s["date"], "title": s["title"],
                "name": s["name"], "coord": s["coord"], "url": s["url"]}
        stell_pins.append(prev)

stell_wpts = []
stell_pms = []
for p in stell_pins:
    nm = f"T{dayrange(p['days'])} - {p['title']}"
    desc = f"Tag {dayrange(p['days'])} ({p['date']}) - {p['title']}"
    if p["name"]:
        desc += f" | Stellplatz: {p['name']}"
    link = ""
    if p["url"]:
        link = f"<br/>{p['url']}"
        desc += f"\n{p['url']}"
    stell_wpts.append((nm, desc, p["coord"][0], p["coord"][1]))
    stell_pms.append(pm_point(nm, f"Tag {dayrange(p['days'])} ({p['date']}) - {p['title']}" + (f" | Stellplatz: {p['name']}" if p['name'] else "") + link, p["coord"][0], p["coord"][1], "st"))
stell_kml = kml_doc("NZ27 Stellplätze", "Uebernachtungs-Stellplaetze je Tag.", stell_pms, [style_def("st", STELL)])
stell_gpx = gpx_wpt_file("NZ27 Stellplätze", "Uebernachtungs-Stellplaetze je Tag.", stell_wpts)

# ---------- 2) Attraktionen ----------
ATTR = "ff00ff00"
attr_list = []
attr_pms = []
attr_missing = 0
for s in stops:
    region = re.split(r'[→(]', s["title"])[0].strip()
    for a in s["attractions"]:
        lat, lon = (a["coord"] if a["coord"] else (None, None))
        if lat is None:
            c = geocode(f"{a['name']}, {region}, New Zealand")
            if c:
                lat, lon = c
            else:
                attr_missing += 1
                continue
            time.sleep(1.1)
        nm = f"{a['name']} (T{s['day']})"
        desc = f"Tag {s['day']} ({s['date']}) - {s['title']}"
        if a["rating"]:
            desc += f" | Rating {a['rating']}/10"
        link = ""
        if a["url"]:
            link = f"<br/>{a['url']}"
            desc += f"\n{a['url']}"
        attr_list.append((nm, desc, lat, lon))
        attr_pms.append(pm_point(nm, f"Tag {s['day']} ({s['date']}) - {s['title']}" + (f" | Rating {a['rating']}/10" if a['rating'] else "") + link, lat, lon, "at"))
attr_kml = kml_doc("NZ27 Attraktionen", "Sehenswuerdigkeiten laut itinerary (mit Rating).", attr_pms, [style_def("at", ATTR)])
attr_gpx = gpx_wpt_file("NZ27 Attraktionen", "Sehenswuerdigkeiten laut itinerary (mit Rating).", attr_list)

# ---------- 3) Versorgung ----------
VERS = "ffff0000"
vers_list = []
vers_pms = []
cnt = 0
for s in stops:
    for item in s["supply"]:
        place = None
        im = re.search(r'\bin\s+([A-Za-zÄÖÜäöü][A-Za-zÄÖÜäöü\s\-]+?)(?:\(|$|,)', item["text"])
        if im:
            c = geocode(im.group(1).strip() + ", New Zealand")
            if c:
                place = c
        if not place:
            if s["coord"]:
                place = (s["coord"][0] + cnt * 0.00035, s["coord"][1])
            else:
                place = geocode(s["title"].split("(")[0].strip() + ", New Zealand")
            if not place:
                continue
        cnt += 1
        nm = f"{item['type']} (T{s['day']})"
        desc = f"Tag {s['day']} ({s['date']}) - {item['type']}\n{item['text']}"
        vers_list.append((nm, desc, place[0], place[1]))
        vers_pms.append(pm_point(nm, f"Tag {s['day']} ({s['date']}) - {item['type']}<br/>{item['text']}", place[0], place[1], "ve"))
vers_kml = kml_doc("NZ27 Versorgung", "Versorgung: Wäsche/Sanidump/Wasser/Tanken.", vers_pms, [style_def("ve", VERS)])
vers_gpx = gpx_wpt_file("NZ27 Versorgung", "Versorgung: Wäsche/Sanidump/Wasser/Tanken.", vers_list)

# ---------- 4) Fähre ----------
FERR = "ff00a5ff"
ferr_list = []
ferr_pms = []
for i, s in enumerate(stops):
    if "Fähre" in s["title"]:
        w = s["coord"] or geocode("Wellington Interislander Terminal, New Zealand")
        p = stops[i-1]["coord"] if i > 0 and stops[i-1]["coord"] else geocode("Picton, New Zealand")
        if w:
            ferr_list.append(("Interislander Fähre Wellington (Ankunft)", f"Tag {s['day']} ({s['date']}) - {s['title']}", w[0], w[1]))
            ferr_pms.append(pm_point("Interislander Fähre Wellington (Ankunft)", f"Tag {s['day']} ({s['date']}) - {s['title']}", w[0], w[1], "fe"))
        if p:
            ferr_list.append(("Interislander Fähre Picton (Abfahrt)", "Cook Strait Fähre, Camper mitbuchten!", p[0], p[1]))
            ferr_pms.append(pm_point("Interislander Fähre Picton (Abfahrt)", "Cook Strait Fähre, Camper mitbuchten!", p[0], p[1], "fe"))
        time.sleep(1.1)
ferr_kml = kml_doc("NZ27 Fähre", "Cook-Strait-Fähre Picton <-> Wellington.", ferr_pms, [style_def("fe", FERR)])
ferr_gpx = gpx_wpt_file("NZ27 Fähre", "Cook-Strait-Fähre Picton <-> Wellington.", ferr_list)

# ---------- 5) Route ----------
ROUTE = "ff800080"
def osrm(lat1, lon1, lat2, lon2):
    url = f"http://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=simplified&geometries=geojson"
    try:
        data = json.load(urllib.request.urlopen(url, timeout=15))
        if data.get("code") == "Ok":
            return data["routes"][0]["geometry"]["coordinates"]
    except Exception:
        pass
    return None

route_pms = []
route_legs = []
ordered = [s for s in stops if s["coord"]]
for i in range(len(ordered)-1):
    a, b = ordered[i]["coord"], ordered[i+1]["coord"]
    g = osrm(a[0], a[1], b[0], b[1])
    leg = [(lat, lon) for lon, lat in g] if g else [a, b]
    route_legs.append(leg)
    route_pms.append(pm_line(f"T{ordered[i]['day']}-T{ordered[i+1]['day']}", leg, "rt"))
    time.sleep(0.1)
route_kml = kml_doc("NZ27 Route", "Routen-Etappen (echte Straßen via OSRM; Fähre = gerade Linie).", route_pms, [style_def("rt", ROUTE, line=True, width=3)])
route_gpx = gpx_track_file("NZ27 Route", "Routen-Etappen (echte Straßen via OSRM; Fähre = gerade Linie).", route_legs)

# ---------- write files ----------
os.makedirs(OUTDIR, exist_ok=True)
files = {
    "nz_stellplaetze.kml": stell_kml, "nz_stellplaetze.gpx": stell_gpx,
    "nz_attraktionen.kml": attr_kml, "nz_attraktionen.gpx": attr_gpx,
    "nz_versorgung.kml": vers_kml, "nz_versorgung.gpx": vers_gpx,
    "nz_faehre.kml": ferr_kml, "nz_faehre.gpx": ferr_gpx,
    "nz_route.kml": route_kml, "nz_route.gpx": route_gpx,
}
for fn, doc in files.items():
    open(os.path.join(OUTDIR, fn), "w", encoding="utf-8").write(doc)
    print(f"  {fn}: {len(doc)} Zeichen", flush=True)

print(f"Stellplatz: {len(stell_pins)} | Attraktionen: {len(attr_list)} (fehlend: {attr_missing}) | Versorgung: {len(vers_list)} | Fähre: {len(ferr_list)} | Route-Legs: {len(route_legs)}", flush=True)
