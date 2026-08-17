# Context – InkyFrame Projekt

## Ziel
Auf einem **Pimoroni Inky Frame 7,3"** (Pico W / Pico 2 W Aboard) werden
**Wetterdaten** und **Termine** angezeigt. Das Projekt wird in **Python
(MicroPython)** geschrieben. Anweisungen und Fortschritte werden in dieser Datei
vermerkt und fortgeführt. Änderungen werden immer eingecheckt und gepusht.

## Hardware / Basis
- Pimoroni Inky Frame 7,3" (Auflösung 800x480, 7 native Farben + Dithering).
- Firmware: Pimoroni Inky-Frame MicroPython (`DISPLAY_INKY_FRAME_7` bzw.
  `DISPLAY_INKY_FRAME_SPECTRA_7`).
- Referenz-Repo: https://github.com/pimoroni/inky-frame

## Entwicklungsumgebung
- Auf dem Gerät läuft **MicroPython** (Pimoroni-Firmware). Die Lauf-Skripte
  (`main.py`, `lib/*.py`) werden per **Thonny** auf den Frame geladen.
- Für die API-Logik (Wetter/Kalender-Parsing) gibt es ein **Desktop-Skelett**
  (normales CPython), das ohne Hardware testbar ist. Module werden so geschrieben,
  dass sie sowohl unter MicroPython als auch (für Tests) unter CPython laufen
  (Standardbibliothek nur; `urequests`/`urllib`-Abstraktion).

## Datenquellen (Start-Entscheidung)
- **Wetter:** Open-Meteo (https://open-meteo.com) – **kein API-Key nötig**,
  frei nutzbar, liefert aktuelle Werte + Forecast mit Wettercodes (WMO).
- **Termine:** ICS/iCal-Feed (öffentliche Kalender-URL, z.B. Nextcloud/Google
  Calendar `.ics`). URL wird in `secrets.py` hinterlegt. Es wird ein
  eigener kleiner ICS-Parser ohne externe Abhängigkeit geschrieben.
- Beide Entscheidungen sind leicht austauschbar (OpenWeatherMap, CalDAV etc.),
  da die Datenquellen hinter Module gekapselt sind.

## Pimoroni-Patterns (übernommen aus Referenz-Repo)
- `HOLD_VSYS_EN_PIN = 2` als Output setzen, damit das Gerät am Strom nicht
  schlafen geht.
- I2C für RTC: `PimoroniI2C(4, 5, 100000)`, `PCF85063A(i2c)`.
- WiFi-Connect via `network.WLAN` mit pulsierender Network-LED (Pin 7),
  Warn-LED Pin 6.
- Farben als Konstanten aus `inky_frame`: BLACK/WHITE/GREEN/BLUE/RED/YELLOW/ORANGE.
- Update-Intervall per RTC-Timer, dann `hold_vsys_en_pin.init(Pin.IN)` und
  `time.sleep()` (für USB-Betrieb) bzw. Power-Off (für Batterie).
- PicoGraphics-Instanz erst **nach** RAM-intensiven HTTPS-Requests anlegen
  (Pattern aus `carbon_intensity.py`).

## Projektstruktur
```
main.py              # Einstieg: Wifi -> Daten holen -> zeichnen -> sleep
secrets.py           # WIFI_SSID, WIFI_PASSWORD, LOCATION, ICS_URL (NICHT committen! -> .gitignore)
lib/
  weather.py         # Open-Meteo Abfrage + WMO-Code-Mapping zu Text/Icon
  calendar_ics.py    # Minimaler ICS-Parser + Termin-Auswahl (heute/nächste)
  display.py         # PicoGraphics-Setup + Layout (Wetter + Termine)
  network.py         # WiFi-Connect, RTC-Sync, sleep_for-Helper
context.md           # Diese Datei
README.md            # Setup-Anleitung
```

## Fortschritt
- [x] Repo pimoroni/inky-frame gelesen, Patterns verstanden.
- [x] Context.md angelegt.
- [x] Projektstruktur + Module angelegt (main.py, lib/, secrets-Template).
- [x] Wetter-Modul (Open-Meteo, WMO-Mapping) + CPython-Test.
- [x] Kalender-Modul (eigener ICS-Parser) + CPython-Test.
- [x] Display/Layout-Modul (PicoGraphics, 7.3").
- [x] main.py verdrahtet (Wifi -> Zeit -> Daten -> zeichnen -> sleep).
- [x] README + Setup-Anleitung.
- [x] Commit & Push (erster Stand).

## Bekannte Einschraenkungen (Folge-Aufgaben)
- ICS-Parser ignoriert Zeitzonenversatz (UTC `Z` / TZID) -> spaeter ausbauen.
- Layout ist rudimentaer -> nach erstem Lauf auf dem Geraet verfeinern.
- Spectra-Variante (`DISPLAY_INKY_FRAME_SPECTRA_7`) als Option in display.py.
- Icons fuer Wettercodes folgen (aktuell nur Text).

## Offene Punkte / nächste Entscheidungen
- Konkrete ICS-URL und Breitengrad/Längengrad für den Standort (in `secrets.py`).
- Farb-Schema / Layout-Vorlieben (folgt nach erstem Lauf auf dem Gerät).
- Battery-Betrieb vs. USB-Steckbetrieb (beeinflusst Sleep-Logik; aktuell beides unterstützt).

---

# Anforderungen (vollstaendig, fuer spaetere Sitzungen)

> Die bisherigen Module (`lib/weather.py`, `lib/calendar_ics.py`, `lib/display.py`,
> `lib/network.py`, `main.py`) dienen nur der **Veranschaulichung / als Startpunkt**.
> Sie werden im Laufe der weiteren Sitzungen durch die echte Implementierung der
> hier dokumentierten Anforderungen ersetzt/erweitert. Diese Sektion enthaelt die
> verbindliche Aufgabenliste fuer kommende Sitzungen.

## 1. WLAN-Anbindung
- Verbindung des Inky Frame mit dem lokalen WLAN-Netzwerk (Credentials in
  `secrets.py`: `WIFI_SSID`, `WIFI_PASSWORD`).
- Robuster Connect mit Retry/Timeout, Network-LED-Feedback (Pimoroni-Pattern).

## 2. Wetter
- Quelle: Open-Meteo (kein API-Key), Standort via `LATITUDE`/`LONGITUDE` in
  `secrets.py`.
- **Zeitraum:** aktueller Tag + naechster Tag.
- **Aufloesung:** 3-Stunden-Zyklus (stündliche/hourly Forecast, aggregiert auf
  3h-Schritte) fuer beide Tage.
- Darzustellende Werte je 3h-Slot: Temperatur, Wettercode (WMO) -> Text/Icon,
  ggf. Niederschlag/Wind.
- Mapping WMO-Code -> deutscher Text + Icon (Icons als nachgezeichnete
  PicoGraphics-Symbole, siehe Anzeige).

## 3. Kalender
- **Zwei Quellen parallel:**
  - **Google Calendar** (oeffentliche ICS-URL bzw. "Secret address in iCal format").
  - **Nextcloud** (oeffentlicher CalDAV-Export: `.../remote.php/dav/public-calendars/<id>/?export`).
- Beide URLs in `secrets.py` hinterlegen (z.B. `ICS_URL_GOOGLE`, `ICS_URL_NEXTCLOUD`).
- Eigener ICS-Parser (keine externe Abhaengigkeit), beide Feeds mergen + dedup.
- **Zeitzonenversatz (UTC `Z` / TZID)** korrekt konvertieren (bekannte
  Einschraenkung im Start-Code -> MUSS ausgebaut werden).

## 4. Shelly EM3 (zwei Module)
- **Zwei Shelly 3EM-Messgeraete** auslesen (aktuelle Leistung).
- Auslesen vermutlich via Shelly REST-API (HTTP GET, JSON) im lokalen Netz:
  `http://<shelly-ip>/status` bzw. Gen2-Devices `/rpc/EM.GetStatus`.
- IPs / Endpoints in `secrets.py` (`SHELLY_EM3_IP_A`, `SHELLY_EM3_IP_B`).
- **Verrechnung:** Differenz der aktuellen Leistungen beider Module berechnen
  (Leistung_A - Leistung_B; Vorzeichen/Bezug+Lieferung klaeren).
- **Chart:** die Differenz als Verlauf anzeigen (Liniendiagramm in PicoGraphics).
- => fuer den Verlauf muessen Historien-Werte gepuffert werden. Optionen:
  - Zwischenspeicher in `state.json` auf dem Geraet, oder
  - Shelly liefert selbst Verlaufsdaten (Pruefen: `/rpc/EM.GetStatus` /
    `/emeter/0` Historie); bevorzugt wenn verfuegbar.
- Klaren: Anzeige aktueller Wert + Trend, oder Zeitreihe? -> offene Frage.

## 5. Anzeige (Layout, attraktiv)
- **Anzeige-Flaeche 800x480**, 7 Farben + Dithering.
- Ziel: eine **ansprechende Dashboard-Optik** (klare Typo, Farb-Akzente,
  Trennlinien, ggf. Hintergrund-Dither).
- **Elemente gleichzeitig auf dem Screen:**
  1. **Wetter** (aktueller Tag + naechster Tag, 3h-Zyklus, mit Icons).
  2. **Naechste 7 Tage aus dem Kalender** (Termine der kommenden 7 Tage).
  3. **Geburtstage der naechsten 30 Tage**.
  4. (zusatzlich) **Shelly-Differenz-Chart** (siehe 4).
- Layout-Vorschlag fuer naechste Sitzung: 2-3 Spalten/Regionen, Header mit
  Datum+Uhrzeit; Skizze vorab als ASCII oder direkte PicoGraphics-Implementierung.
- Farb-Akzente: Wetter=BLUE, Kalender=RED, Geburtstage=GREEN/ORANGE, Chart=YELLOW.

## 6. Daten/Geheimnisse
- Alle geraete-/konto-spezifischen Werte in `secrets.py` (gitignored):
  - WLAN, Lat/Lon, `ICS_URL_GOOGLE`, `ICS_URL_NEXTCLOUD`,
    `SHELLY_EM3_IP_A`, `SHELLY_EM3_IP_B`.
- `secrets.example.py` als Vorlage pflegen.

## 7. Ablauf / Update-Intervall
- Zyklischer Ablauf: WLAN -> Zeit sync -> alle Datenquellen holen ->
  zeichnen -> sleep -> wiederholen.
- Update-Intervall in `secrets.py` (`UPDATE_INTERVAL_MINUTES`).
- Shelly-Differenz-Chart evtl. hoeherfrequent als Wetter/Kalender -> ggf.
  untersch. Intervalle pruefen (zwei Schlaf-Zyklen?).

## Offene Fragen (vor Implementierung zu klaeren)
1. Shelly-Differenz: Bezug vs. Lieferung? Was genau soll der Chart zeigen
   (aktueller Wert, Trend, Zeitreihe ueber welchen Zeitraum)?
2. Shelly-Historie: Geraet liefert selbst Verlauf, oder puffern wir selbst?
3. Shelly-Generation (Gen1 REST vs. Gen2 RPC) der beiden Module?
4. Layout-Prioritaet/Skizze abnehmen, bevor implementiert wird.
5. Geburtstage: eigene Kalenderquelle oder aus den ICS-Feeds filtern (nach
   wiederkehrenden Ereignissen / SUMMARY-Pattern)?
