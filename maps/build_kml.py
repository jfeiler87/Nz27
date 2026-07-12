import re, json, urllib.request, urllib.parse, time, os, sys

PATH = "/home/hermes/nz_trip_2027/itinerary.md"
text = open(PATH, encoding="utf-8").read()

def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

# ---- parse sections ----
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
    stops.append({"day": day, "date": date, "title": title, "name": name, "url": url, "coord": None})

def parse_coord(url):
    if not url: return None
    m = re.search(r'@(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)', url)
    if m: return (float(m.group(1)), float(m.group(2)))  # lat, lon
    m = re.search(r'query=(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)', url)
    if m: return (float(m.group(1)), float(m.group(2)))
    return None

for s in stops:
    s["coord"] = parse_coord(s["url"])

# ---- geocode missing ----
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

missing = [s for s in stops if not s["coord"]]
for s in missing:
    q = f"{s['name']}, {s['title']}, New Zealand"
    c = geocode(q)
    if not c:
        c = geocode(f"{s['title']}, New Zealand")
    s["coord"] = c
    time.sleep(1.1)

# Fallback for return day without campsite -> Auckland
for s in stops:
    if not s["coord"] and s["day"] == 61:
        s["coord"] = (-36.8485, 174.7633)

print(f"Tage gesamt: {len(stops)} | mit Koordinate: {sum(1 for s in stops if s['coord'])} | ohne: {[s['day'] for s in stops if not s['coord']]}", flush=True)

# ---- merge consecutive identical coords into one pin ----
pins = []
for s in stops:
    if not s["coord"]:
        continue
    if pins and pins[-1]["coord"] == s["coord"]:
        pins[-1]["days"].append(s["day"])
    else:
        pins.append({"days": [s["day"]], "date": s["date"], "title": s["title"],
                     "name": s["name"], "coord": s["coord"], "url": s["url"]})

# ---- route legs (real roads via OSRM, fallback straight) ----
def osrm(lat1, lon1, lat2, lon2):
    url = f"http://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=full&geometries=geojson"
    try:
        data = json.load(urllib.request.urlopen(url, timeout=15))
        if data.get("code") == "Ok":
            return data["routes"][0]["geometry"]["coordinates"]  # [lon,lat]
    except Exception:
        pass
    return None

legs = []
ordered = [s for s in stops if s["coord"]]
for i in range(len(ordered)-1):
    a, b = ordered[i]["coord"], ordered[i+1]["coord"]
    g = osrm(a[0], a[1], b[0], b[1])
    if g:
        legs.append((ordered[i]["day"], ordered[i+1]["day"], g))
    else:
        legs.append((ordered[i]["day"], ordered[i+1]["day"], [[a[1], a[0]], [b[1], b[0]]]))
    time.sleep(0.1)

# ---- build KML ----
def coord_str(latlon):
    return f"{latlon[1]:.6f},{latlon[0]:.6f},0"

def dayrange(days):
    return f"{days[0]}-{days[-1]}" if len(days) > 1 else str(days[0])

kml = []
kml.append('<?xml version="1.0" encoding="UTF-8"?>')
kml.append('<kml xmlns="http://www.opengis.net/kml/2.2">')
kml.append('  <Document>')
kml.append('    <name>NZ Campervan Route 2027 (19.03-18.05)</name>')
kml.append('    <description>Stopps + Routenueberblick aus itinerary.md. Import in Google My Maps: Meine Orte - Karten - Karte erstellen - Importieren.</description>')
kml.append('    <Style id="pin"><IconStyle><color>ff0000ff</color><scale>1.0</scale></IconStyle></Style>')
kml.append('    <Style id="route"><LineStyle><color>ffff0000</color><width>3</width></LineStyle></Style>')
kml.append('    <Folder><name>Stopps (Pins)</name>')
for p in pins:
    nm = esc(f"T{dayrange(p['days'])} - {p['title']}")
    desc = esc(f"Tag {dayrange(p['days'])} ({p['date']}) - {p['title']}")
    if p["url"]:
        desc += "<br/>" + esc(p["url"])
    kml.append('      <Placemark>')
    kml.append(f'        <name>{nm}</name>')
    kml.append(f'        <description>{desc}</description>')
    kml.append('        <styleUrl>#pin</styleUrl>')
    kml.append('        <Point><coordinates>' + coord_str(p["coord"]) + '</coordinates></Point>')
    kml.append('      </Placemark>')
kml.append('    </Folder>')
kml.append('    <Folder><name>Route (Etappen)</name>')
for d1, d2, g in legs:
    coords = " ".join(f"{lon:.6f},{lat:.6f},0" for lon, lat in g)
    kml.append('      <Placemark>')
    kml.append(f'        <name>{esc(f"T{d1}-T{d2}")}</name>')
    kml.append('        <styleUrl>#route</styleUrl>')
    kml.append('        <LineString><tessellate>1</tessellate><coordinates>' + coords + '</coordinates></LineString>')
    kml.append('      </Placemark>')
kml.append('    </Folder>')
kml.append('  </Document>')
kml.append('</kml>')
kml_text = "\n".join(kml)

out = "/home/hermes/nz_trip_2027/maps/nz_route.kml"
os.makedirs(os.path.dirname(out), exist_ok=True)
open(out, "w", encoding="utf-8").write(kml_text)
print(f"KML geschrieben: {out} | Pins: {len(pins)} | Legs: {len(legs)} | Groesse: {len(kml_text)} Zeichen", flush=True)
