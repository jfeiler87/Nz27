# Karten-Dateien (maps/)

Zwei Formate, jeweils als **eigener Layer** importierbar:
- **KML** → Google My Maps (Planung / Überblick am Desktop)
- **GPX** → OsmAnd / Maps.me (Offline-Navigation auf dem Handy)

Jede Kategorie liegt als eigene Datei vor (→ einzeln schaltbar).

## Dateien (je Kategorie `.kml` + `.gpx`)
- `nz_stellplaetze.{kml,gpx}` — Übernachtungs-Stellplätze je Tag (Freiplatz / DOC /
  Holiday Park), beschriftet mit Tag + Ziel + Original-Link.
- `nz_attraktionen.{kml,gpx}` — Sehenswürdigkeiten aus dem itinerary, mit Rating,
  nach Tag beschriftet.
- `nz_versorgung.{kml,gpx}` — Versorgung: Wäsche (🧺), Sanidump (🚻), Frischwasser (💧),
  Tanken (⛽). Orte teils nur stadteben (Geocoding), daher ungefähr.
- `nz_faehre.{kml,gpx}` — Cook-Strait-Fähre Picton ↔ Wellington (Camper mitbuchen!).
- `nz_route.{kml,gpx}` — Routen-Etappen (KML: Linien; GPX: Track / `<trkpt>`).

## Import KML → Google My Maps (pro Layer eine Datei)
Für **jede** Datei einzeln:
1. https://maps.google.com → Menü (☰) → „Meine Orte" → „Karten".
2. „Karte erstellen" (oder bestehende öffnen).
3. Ebene „Importieren" → Datei auswählen / hochladen, z. B. `nz_stellplaetze.kml`.
4. Layer benennen (z. B. „Stellplätze"); für die anderen 4 Dateien wiederholen.

## Import GPX → OsmAnd / Maps.me (Offline)
- **OsmAnd:** Menü → Meine Plätze → Tracks / Wegpunkte → GPX importieren (oder Datei
  im Dateimanager öffnen). Pro Datei ein Track bzw. eine Wegpunkt-Gruppe; Farbe und
  Einblenden konfigurierbar.
- **Maps.me:** GPX-Datei öffnen → „Auf Karte anzeigen". Wegpunkte erscheinen als POIs,
  Tracks als Linie.
- Tipp: vor Abflug alle 5 GPX aufs Handy kopieren und die Offline-Kartenpakete
  (NZ Südinsel + Nordinsel) in der App laden.

## Neu generieren (nach Itinerar-Änderungen)
Im Repo-Root ausführen:

    python3 maps/build_kml.py

Erzeugt alle 10 Dateien (5× KML + 5× GPX) aus `itinerary.md` – extrahiert Koordinaten
aus den `[Karte]`-Links, geocodiert fehlende Stopps / Attraktionen via Nominatim und
zeichnet Routen via OSRM.

## Hinweise
- My Maps / GPX-Tracks dienen Planung & Offline-Überblick, keine Garantie für
  befahrbare Wege (Baustellen / Sperrungen vor Ort prüfen).
- GPX-Track folgt OSRM-Straßen-Routing; im Gelände (z. B. DOC-Schotterstraßen) kann
  abweichen.
- Versorgungs-Pins sind best-effort (manche nur stadtgenau); tagesaktuelle
  Freiplatz-Regeln in Rankers / CamperMate prüfen.
- Der Generator braucht Internet (Nominatim / OSRM). Fehlt die Verbindung, werden
  fehlende Punkte übersprungen bzw. Routen als gerade Linien gezeichnet.
