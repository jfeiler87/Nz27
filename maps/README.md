# Karten-Dateien (maps/)

Jede KML-Datei wird in Google My Maps als **eigener Layer** importiert – so kannst
du Stellplätze, Attraktionen, Versorgung usw. unabhängig voneinander ein- und
ausblenden.

## Dateien
- `nz_stellplaetze.kml` — Übernachtungs-Stellplätze je Tag (Freiplatz / DOC /
  Holiday Park), beschriftet mit Tag + Ziel + Original-Google-Maps-Link.
- `nz_attraktionen.kml` — Sehenswürdigkeiten aus dem itinerary, mit Rating,
  nach Tag beschriftet.
- `nz_versorgung.kml` — Versorgung: Wäsche (🧺), Sanidump (🚻), Frischwasser (💧),
  Tanken (⛽). Orte teils nur stadteben (Geocoding), daher ungefähr.
- `nz_faehre.kml` — Cook-Strait-Fähre Picton ↔ Wellington (Camper mitbuchen!).
- `nz_route.kml` — Routen-Etappen als Linien (echte Straßen via OSRM;
  Fähre = gerade Linie über die Cook Strait).

## Import in Google My Maps (pro Layer eine Datei)
Für **jede** Datei einzeln:
1. https://maps.google.com → Menü (☰) → „Meine Orte" → „Karten".
2. „Karte erstellen" (oder bestehende Karte öffnen).
3. Ebene „Importieren" → Datei auswählen / hochladen, z. B. `nz_stellplaetze.kml`.
4. Layer sinnvoll benennen (z. B. „Stellplätze").
   Wiederholen für die anderen 4 Dateien.
→ Pro Kategorie ein eigener, einzeln schaltbarer Layer.

## Neu generieren (nach Itinerar-Änderungen)
Im Repo-Root ausführen:

    python3 maps/build_kml.py

Der Generator liest `itinerary.md`, extrahiert Koordinaten aus den `[Karte]`-Links,
geocodiert fehlende Stopps / Attraktionen via Nominatim und zeichnet Routen via OSRM.

## Hinweise
- My Maps ist für Planung / Überblick gedacht, kein Live-Turn-by-Turn-Navi.
  Zum Fahren einfach den entsprechenden Pin antippen.
- Pin-Farben werden in My Maps oft auf Standard gesetzt – du kannst pro Layer
  manuell einfärben.
- Versorgungs-Pins sind best-effort (manche nur stadtgenau); tagesaktuelle
  Freiplatz-Regeln in Rankers / CamperMate prüfen.
- Der Generator braucht Internet (Nominatim / OSRM). Fehlt die Verbindung,
  werden fehlende Punkte übersprungen bzw. Routen als gerade Linien gezeichnet.
