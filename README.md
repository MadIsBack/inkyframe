# InkyFrame – Wetter, Kalender & Shelly-Dashboard

Dashboard auf einem [Pimoroni Inky Frame 7,3"](https://shop.pimoroni.com/products/inky-frame-7-3)
(Pico W / Pico 2 W Aboard), geschrieben in **MicroPython**.

## Funktionen
- **Wetter:** Open-Meteo (kein API-Key) – aktueller Wert + 3h-Slots für
  heute und morgen (Temperatur, WMO-Code als deutscher Text, Regenwahrscheinlichkeit).
- **Kalender:** zwei ICS-Feeds (Google + Nextcloud) parallel, gemergt + dedup;
  nächste 7 Tage Termine; Geburtstage der nächsten 30 Tage (RRULE FREQ=YEARLY).
  Zeitzonenkonvertierung (UTC `Z` / TZID).
- **Shelly EM3:** zwei Module auslesen (Autodetection Gen1 REST + Gen2/Pro 3EM
  RPC), Differenz berechnen, Verlauf als Liniendiagramm (Historie in `state.json`).
- **Dashboard-Layout:** Wetter links, 7-Tage-Kalender Mitte, Geburtstage rechts,
  Shelly-Chart unten. Farb-Akzente pro Bereich.

## Setup

### 1. Firmware
Aktuelle `-with-examples`-Firmware von
https://github.com/pimoroni/inky-frame/releases/latest als `.uf2` flashen
(BOOTSEL + Reset, Datei auf `RP2350`-Laufwerk ziehen).

### 2. Dateien übertragen (Thonny)
```
main.py
secrets.py          # selbst anlegen (siehe unten / secrets.example.py)
lib/network.py
lib/weather.py
lib/calendar_ics.py
lib/shelly.py
lib/state.py
lib/display.py
```

### 3. secrets.py anlegen
Kopiere `secrets.example.py` → `secrets.py` (wird NICHT committen) und trage:
```python
WIFI_SSID = "..."
WIFI_PASSWORD = "..."
LATITUDE = 52.52
LONGITUDE = 13.405
ICS_URL_GOOGLE = "https://calendar.google.com/calendar/ical/.../basic.ics"
ICS_URL_NEXTCLOUD = "https://cloud.example.org/remote.php/dav/public-calendars/<id>/?export"
SHELLY_EM3_IP_A = "192.168.1.10"
SHELLY_EM3_IP_B = "192.168.1.11"
SHELLY_EM3_TOKEN = ""   # nur bei aktiviertem Auth-Schutz
UPDATE_INTERVAL_MINUTES = 5
```

### 4. Starten
`main.py` läuft automatisch: WLAN → Zeit sync → alle Quellen → zeichnen → sleep.

## Shelly-Hinweise
- **Autodetection:** zuerst Gen2 (`/rpc/EM.GetStatus?id=0` → `total_act_power`),
  bei Fehlschlag Gen1 (`/status` → `emeters[].power` / `total_power`).
- Vorzeichen: positiv = Bezug, negativ = Einspeisung.
- Differenz = Leistung A − Leistung B.

## Struktur
```
main.py              Einstieg: Wifi → Daten → zeichnen → sleep
secrets.py           Konfiguration (gitignored)
lib/network.py       WiFi, RTC, sleep_for
lib/weather.py       Open-Meteo, 3h-Slots heute+morgen
lib/calendar_ics.py  ICS-Parser + Zeitzonen + Merge + Geburtstage
lib/shelly.py        Zwei EM3, Autodetection Gen1/Gen2, Differenz
lib/state.py         Historie der Shelly-Differenz (state.json)
lib/display.py       PicoGraphics-Dashboard 7.3"
Context.md           Anweisungen & Fortschritt
```

## Entwicklung / Tests
Logik-Module sind auch unter normalem CPython testbar:
```bash
python3 -c "import lib.weather as w; print(w.describe(61))"
python3 -m py_compile lib/*.py main.py
```
