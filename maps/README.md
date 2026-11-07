# Karten-Dateien (maps/)

**Generiert** von `python3 tools/build.py` aus `data/reise.yaml` + `data/orte_*.json` — nicht von Hand editieren.

Je Layer eine Datei, jeweils als `.kml` (Google My Maps) und `.gpx` (Organic Maps / OsmAnd, offline):

| Datei | Inhalt |
|---|---|
| `nz_stellplaetze` | Hauptstellplatz je Nacht (Tag + Datum im Namen) |
| `nz_alternativen` | Ausweichplätze (Holiday Parks, Freiplätze) |
| `nz_attraktionen` | Programmpunkte (inkl. optionaler, „(opt.)“) |
| `nz_versorgung` | Tanken, Dump, Wäsche |
| `nz_fixpunkte` | Hotel, Britz-Stationen, Fähre, Hobbiton, Flughafen |
| `nz_route` | Fahrstrecke Übernachtung → Übernachtung (OSRM) |

Jeder Punkt liegt dort, wo man hinfährt (Parkplatz, Einfahrt, Ticketbüro), und enthält in der
Beschreibung den Google-Maps-Navigationslink.

## Google My Maps (Überblick)
maps.google.com → ☰ → „Gespeichert“ → „Karten“ → „Karte erstellen“ → je Layer „Importieren“ → `.kml` wählen.
Die Karte erscheint danach in der Google-Maps-App unter „Gespeichert → Karten“.

## Organic Maps / OsmAnd (offline)
`.gpx` aufs Handy kopieren → in der App öffnen/importieren → als Lesezeichen-/Track-Liste verfügbar.
NZ-Offlinekarte vorher herunterladen.
