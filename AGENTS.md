# AGENTS.md — NZ Campervan Trip 2027

> Leitfaden für KI-Agenten und Mitplanende in diesem Repo. Planungstexte sind **Deutsch**.

## Worum es geht
61 Tage Neuseeland im Campervan (2 Erwachsene), **19.03.2027 Abholung Christchurch → 18.05.2027 Rückgabe Auckland**.
Ziel: ein Plan, der unterwegs auf einem Android-Handy (Galaxy S7+) funktioniert — jeder Ort ist ein
antippbarer Navigationslink. Später soll daraus eine statische Webseite werden.

## Repo-Layout (Datenfluss)
```
data/orte_*.json   ──┐   (jeder Ort genau einmal: id, lat/lon = Anfahrtspunkt, ziel, quelle, konfidenz)
data/reise.yaml    ──┼─► tools/build.py ─► itinerary.md          (GENERIERT, nicht von Hand editieren)
data/route_cache.json┘                  └► maps/nz_*.kml|gpx    (GENERIERT, je Layer eine Datei)
```
- `data/reise.yaml` — **Quelle der Wahrheit** für Fixpunkte, Grundsätze und alle 61 Tage
  (Fahrt, Programm, Nacht + Alternativen, Versorgung, Hinweise, Buchungen). Orte nur per `id`.
- `data/orte_sued.json`, `data/orte_nord.json`, `data/orte_extra.json` — Ortsregister.
  Koordinate = **wo man hinfährt** (Parkplatz, Trailhead, Campingplatz-Einfahrt, Ticketbüro,
  Tour-Abfahrt) — nie Seemitte/Ortsmitte/Nationalpark-Zentroid. Jede Koordinate stammt aus einer
  Abfrage (OSM Nominatim/Overpass, DOC-Opendata, geokodierte Adresse) und hat `quelle` + `konfidenz`.
- `data/route_cache.json` — OSRM-Fahrstrecken (km, Minuten, Geometrie), damit Builds reproduzierbar sind.
- `tools/build.py` — Generator. `python3 tools/build.py` (online, füllt Cache) bzw. `--offline`.
  Bricht mit Exit 1 ab, wenn `reise.yaml` eine unbekannte Orts-id referenziert.
- `itinerary.md` — generierte Lesefassung (Übersicht + Tag für Tag).
- `maps/` — generierte KML (Google My Maps) + GPX (OsmAnd/Organic Maps); Anleitung in `maps/README.md`.
- `BUCHUNGS_TIMELINE.md` — was wann zu buchen/zu klären ist. `TODO.md` — offene Punkte.
- `LOGISTIK.md` — Wetter, Ausrüstung, Apps, Camper-Betrieb (Hintergrundwissen).
- `recherche/` — Faktenchecks mit Quellen (Stand + Konfidenz je Aussage).

## Feste Randbedingungen (nicht verletzen)
- **Fixpunkte** (gebucht): Flüge, Hotel Lylo Christchurch Airport 18./19.03., Britz-Abholung
  Christchurch 19.03. / Rückgabe Auckland-Mangere 18.05., Bluebridge Picton→Wellington **So 25.04. 13:00**,
  Hobbiton Evening Banquet **Mi 05.05. 15:30**. Details in `data/reise.yaml` → `fixpunkte`.
- **Kein Stewart Island.**
- **Britz-Straßenverbote:** Skippers Rd, **Crown Range / Cardrona Valley Rd**, Ball Hut Rd, Ninety Mile
  Beach, nördlich Colville, Mt Aspiring Rd hinter Treble Cone. **Schotter nur < 12 km** zu einem
  Campingplatz/einer großen Attraktion (sonst Sondergenehmigung; ohne sie erlischt der Versicherungsschutz).
- **Wandern:** max. ~15 km und ~400 Höhenmeter pro Tour (kein Tongariro Crossing, kein Roys Peak).
- **Übernachtung:** schönster *legaler* Platz zuerst (Freiplatz für Self-Contained / DOC), Kosten nur
  Tiebreaker. Alle 5–7 Nächte steht ein Holiday Park als Alternative drin (Wäsche, Strom, Dump).
  Freedom Camping nur mit grüner SC-Plakette; jeden Freiplatz vor Ort (Schild + CamperMate/Rankers) prüfen.
- **Interessen:** Landschaft > alles. Meeressäuger + Pinguine ja (wenn verlässlich), Vogelinseln nein.
  Herr-der-Ringe-Orte nur am Weg, Umweg nur für echte Highlights. Rundflüge statt langer Wanderungen.
- **Kalender:** Ostern 26.–29.03. (Karfreitag/Ostersonntag Läden zu), NZ-Schulferien 10.–26.04.,
  ANZAC Day So 25.04. (Läden bis 13 Uhr zu) + Mo 26.04. Feiertag.

## Konventionen
- Änderungen am Plan **nur** in `data/*`, dann `python3 tools/build.py`, generierte Dateien mitcommitten.
- Neuer Ort: Eintrag in `data/orte_extra.json` (oder Süd/Nord) mit Quelle und Konfidenz — Koordinate
  nie aus dem Gedächtnis. Mit `konfidenz: niedrig` markierte Orte erscheinen im Plan mit ⚠️.
- Fakten mit Quelle und Datum in `recherche/` ablegen; im Plan nur das Ergebnis.
- Arbeiten auf Feature-Branch, Commit-Messages `typ(scope): kurze deutsche Zusammenfassung`.
