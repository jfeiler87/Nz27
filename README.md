# NZ Campervan-Trip 2027

61 Tage Neuseeland im Britz Wanderer: **Fr 19.03.2027 Christchurch → Di 18.05.2027 Auckland**.
Südinsel im Uhrzeigersinn (Mt Cook zuerst, dann Otago-Küste, Catlins, Fiordland, Queenstown/Wanaka,
West Coast, Abel Tasman/Golden Bay, Kaikōura), Fähre am 25.04., Nordinsel bis Northland.

## Wo steht was?
- **[itinerary.md](itinerary.md)** — der Plan zum Lesen: Übersicht + Tag für Tag. Jeder Ort ist ein
  Google-Maps-Navigationslink (antippen → Navigation zum Parkplatz/zur Einfahrt startet).
- **[BUCHUNGS_TIMELINE.md](BUCHUNGS_TIMELINE.md)** — was wann gebucht/geklärt werden muss.
- **[TODO.md](TODO.md)** — offene Planungspunkte.
- **[LOGISTIK.md](LOGISTIK.md)** — Wetter, Ausrüstung, Apps, Camper-Betrieb.
- **[maps/](maps/README.md)** — KML (Google My Maps) und GPX (Organic Maps/OsmAnd) je Layer.
- **[recherche/](recherche/)** — Faktenchecks mit Quellen.
- **[BROSCHUERE.md](BROSCHUERE.md)** — Offline-Broschüre fürs Tablet bauen und Kommentare einarbeiten.

## Plan ändern
Nicht `itinerary.md` editieren, sondern `data/reise.yaml` (Tage) bzw. `data/orte_*.json` (Orte), dann:
```bash
python3 tools/build.py
```
Details für Agenten/Mitplanende: [AGENTS.md](AGENTS.md).
