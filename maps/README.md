# Karten-Dateien (maps/)

## nz_route.kml
Google-My-Maps-importierbare Route der gesamten Reise (19.03.–18.05.2027):
alle Stopps als Pins (nach Tag beschriftet, mit Original-Google-Maps-Link) plus
Routen-Etappen als Linien (echte Straßen via OSRM; Fähre Picton→Wellington als
gerade Linie über die Cook Strait).

## Import in Google My Maps
1. https://maps.google.com öffnen → Menü (☰) → „Meine Orte" → „Karten".
2. „Karte erstellen" (oder bestehende Karte öffnen).
3. Ebene „Importieren" → Datei `nz_route.kml` auswählen / hochladen.
4. Fertig: Pins + Route erscheinen. Pin anklicken → Tag, Ziel, Original-Link.

## Neu generieren (nach Itinerar-Änderungen)
Im Repo-Root ausführen:

    python3 maps/build_kml.py

Der Generator liest `itinerary.md`, extrahiert Koordinaten aus den `[Karte]`-Links,
geocodiert fehlende Stopps via Nominatim und zeichnet Routen via OSRM.

## Hinweise
- My Maps ist für Planung / Überblick gedacht, kein Live-Turn-by-Turn-Navi.
  Zum Fahren einfach den entsprechenden Pin antippen.
- Die Etappe Picton→Wellington ist die Cook-Strait-Fähre (gerade Linie).
- Freie / legale Stellplätze tagesaktuell in Rankers / CamperMate prüfen
  (Bylaws ändern sich laufend).
- Der Generator braucht Internet (Nominatim / OSRM). Fehlt die Verbindung,
  werden fehlende Stopps übersprungen bzw. Routen als gerade Linien gezeichnet.
