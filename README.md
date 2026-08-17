# InkyFrame – Wetter & Termine

Anzeige von **Wetterdaten** und **Terminen** auf einem
[Pimoroni Inky Frame 7,3"](https://shop.pimoroni.com/products/inky-frame-7-3)
(Pico W / Pico 2 W Aboard). Geschrieben in **MicroPython**.

## Funktionen
- **Wetter:** Open-Meteo (kein API-Key nötig) – aktuelle Temperatur, Beschreibung
  (WMO-Code-Mapping auf Deutsch), Wind, Tages-Max/Min.
- **Termine:** öffentlicher ICS/iCal-Feed (Nextcloud, Google Calendar, …) –
  die nächsten Termine ab jetzt.
- **Layout:** Wetter links, Termine rechts, Header mit Datum/Uhrzeit.
- **Stromsparen:** Aktualisierung per RTC-Timer (Batteriebetrieb) bzw.
  `time.sleep` (USB-Betrieb).

## Setup

### 1. Firmware auf den Inky Frame
Lade die aktuelle `-with-examples`-Firmware von
https://github.com/pimoroni/inky-frame/releases/latest als `.uf2` herunter
und flashe sie (BOOTSEL + Reset, Datei auf `RP2350`-Laufwerk ziehen).
Details: [Pimoroni README](https://github.com/pimoroni/inky-frame).

### 2. Dateien übertragen
Lege diese Dateien per [Thonny](https://thonny.org) auf den Frame:

```
main.py
secrets.py        # selbst anlegen (siehe unten)
lib/network.py
lib/weather.py
lib/calendar_ics.py
lib/display.py
```

### 3. secrets.py anlegen
Erstelle lokal eine `secrets.py` (nicht committen!) mit deinen Werten:

```python
WIFI_SSID = "DEIN_WLAN"
WIFI_PASSWORD = "DEIN_PASSWORT"

# Standort für Open-Meteo (Breitengrad, Längengrad)
LATITUDE = 52.52
LONGITUDE = 13.405

# Öffentliche .ics-URL deines Kalenders
ICS_URL = "https://.../calendar.ics"

UPDATE_INTERVAL_MINUTES = 30
```

### 4. Starten
`main.py` läuft automatisch (oder via Thonny "Run"). Beim ersten Lauf:
WLAN verbinden → Zeit via NTP syncen → Wetter + Termine holen → anzeigen →
schlafen bis zum nächsten Intervall.

## Struktur
```
main.py              Einstieg: Wifi → Daten → zeichnen → sleep
secrets.py           Konfiguration (gitignored)
lib/network.py       WiFi, RTC, sleep_for
lib/weather.py       Open-Meteo + WMO-Code-Mapping
lib/calendar_ics.py  Minimaler ICS-Parser
lib/display.py       PicoGraphics-Layout für 7.3"
Context.md           Anweisungen & Fortschritt
```

## Hinweise / bekannte Einschränkungen
- **Zeitzonen:** Der ICS-Parser ignoriert aktuell den Zeitzonenversatz
  (UTC `Z` und `TZID`). Termine werden in der im Feed angegebenen Uhrzeit
  gezeigt. Für eine korrekte Konvertierung ist ein späterer Ausbau vorgesehen.
- **Layout:** Erstes rudimentäres Layout; wird nach erstem Lauf auf dem Gerät
  verfeinert.
- **Display-Variante:** `lib/display.py` nutzt `DISPLAY_INKY_FRAME_7`
  (bzw. `DISPLAY_INKY_FRAME` als Fallback). Für die Spectra-Variante
  `DISPLAY_INKY_FRAME_SPECTRA_7` anpassen.

## Entwicklung / Tests
Die Logik-Module (`weather.py`, `calendar_ics.py`) sind so geschrieben, dass
sie auch unter normalem CPython (für lokale Tests ohne Hardware) laufen:

```bash
python3 -c "import lib.weather as w; print(w.describe(61))"
```
