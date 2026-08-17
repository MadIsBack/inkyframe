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
