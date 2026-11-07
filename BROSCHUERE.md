# Broschüre (Offline-HTML fürs Tablet)

Eine **einzige, selbständige HTML-Datei** zum Durchblättern des Plans auf dem Galaxy Tab S7+ – ohne Internet.
Erzeugt aus denselben Daten wie `itinerary.md`.

```bash
python3 tools/broschuere.py      # → broschuere/nz27-broschuere.html (~25 MB)
```

## Warum eine Datei?
Android öffnet lokale HTML-Dateien aus dem Dateimanager als `content://`-URI; Nachbardateien (Bilder, JS)
sind dann nicht erreichbar. Deshalb ist alles eingebettet: Daten als JSON, Bilder als WebP-Data-URIs,
Küstenlinie als SVG-Pfad. Aufs Tablet kopieren (USB/Google Drive) → in Chrome oder Samsung Internet öffnen.

## Nicht im Repo
`broschuere/` und `.cache/` stehen in `.gitignore`: Das Repo ist öffentlich, die eingebetteten Bilder
(auch nicht frei lizenzierte) sind nur für privaten Gebrauch. Ins Repo kommen nur Generator + Daten;
Bild-URLs stehen in `data/bilder_*.json`, die Bilder werden beim Build nach `.cache/img/` geladen
(max. 820 px, WebP q55) und wiederverwendet. Fehlgeschlagene Downloads hinterlassen `*.fail` (zum Neuversuch löschen).

## Dateien
| Datei | Rolle |
|---|---|
| `tools/broschuere.py` | Generator: liest Daten, lädt/komprimiert Bilder, berechnet Sonnenauf-/untergang (NOAA-Näherung, NZDT bis 04.04.2027), baut JSON und setzt es in die Vorlage |
| `tools/broschuere_vorlage.html` | HTML/CSS/JS-Vorlage; Platzhalter `/*__DATEN__*/null` und `__TITEL__` |
| `data/reise.yaml` | Tage, Programm, Nacht, Versorgung, Hinweise, Buchungen (Quelle der Wahrheit) |
| `data/orte_*.json` | Ortsregister (Koordinate = Anfahrtspunkt) |
| `data/ablauf.yaml` | pro Tag: `intro` (Teaser), `text` (Fließtext neben der Karte), `schritte` [{zeit, text}] |
| `data/beschreibungen.yaml` | pro Orts-id ein ausformulierter Beschreibungstext |
| `data/vorschlaege.yaml` + `data/orte_vorschlaege.json` | Vorschläge (noch nicht im Plan) je Tag |
| `data/bilder_*.json` | {id: [{url, seite, credit, motiv}]} – Bildquellen pro Ort |
| `data/route_cache.json` | OSRM-Geometrie/km/Fahrzeit je Etappe (von `tools/build.py` gefüllt) |

Kein Eintrag in `ablauf.yaml`/`beschreibungen.yaml` → der Abschnitt wird einfach weggelassen.

## Aufbau der Seite
- **Start:** Fixpunkte, Grundsätze, Übersichtskarte, Kommentar „gesamt“.
- **Tag N:** Kopf (Datum, km/Fahrzeit, 🌅/🌇), Fließtext + Karte des Streckenabschnitts (Start/Ziel),
  „So könnte der Tag laufen“, Programm, Übernachtung (+ Alternativen), Versorgung, Hinweise, Buchen,
  Vorschläge (mit 👍/🤔/👎), Kommentar.
- **Navigationslinks:** Hauptbutton „Route ab …“ = Google-Maps-Route mit `origin` = Startpunkt des Tages
  (Übernachtungsplatz der Vornacht, also der Startpunkt der Karte); daneben „📍 ab Standort“ ohne `origin`
  (für echtes Losfahren vom aktuellen Standort).
- **Navigation in der Seite** über eigene Click-Handler (`go()`), nicht über `hashchange` – das ist in
  manchen Android-/Vorschau-Kontexten unzuverlässig.

## Kommentare
- Gespeichert in `localStorage` (Key `nz27-notizen-v1`: `{seiten:{id:{text,ts}}, votes:{vorschlagId: ja|vielleicht|nein}}`).
  Seiten-ids: `gesamt`, `tag-N`, Vorschläge `v<tag>-<ortId>`.
- Seite „Kommentare & Export“: **Download als Markdown** (`nz27-kommentare-YYYY-MM-DD.md`), Kopieren,
  **Import** (liest den JSON-Block am Ende eines Exports; vorhandene Kommentare haben Vorrang).
- Vor dem Austausch der HTML-Datei immer exportieren – je nach Browser hängt der Speicher am Dateipfad.

## Kommentar-Export einarbeiten (für Claude)
Der Export ist nach Tagen sortiert (`## Tag N · Datum · Titel`), Vorschläge mit Wertung und Orts-id.
Vorgehen: Änderungen in `data/reise.yaml` (👍-Vorschläge als Programmpunkt übernehmen, Ort aus
`orte_vorschlaege.json` ggf. nach `orte_extra_*.json` verschieben, Eintrag aus `vorschlaege.yaml` entfernen),
dann `python3 tools/build.py` und `python3 tools/broschuere.py`, committen (ohne `broschuere/`).

## Bekannte Grenzen
- Gezeiten 2027 nicht eingetragen (nur Hinweise „Gezeitentabelle prüfen“).
- Einige Bilder zeigen nur die Umgebung (Bildunterschrift „(Umgebung)“); 5 Orte ohne Bild.
- Orte mit `konfidenz: niedrig` erscheinen mit „⚠ Ort unsicher“.
