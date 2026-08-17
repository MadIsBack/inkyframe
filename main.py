"""Haupt-Skript fuer den Inky Frame 7.3".

Ablauf:
  1. VSYS-HOLD + WiFi verbinden
  2. Zeit syncen (RTC)
  3. Wetter (Open-Meteo) + Termine (ICS) holen
  4. Display zeichnen + updaten
  5. Schlafen legen (RTC-Timer)
"""
import gc
import lib.network as net
import lib.weather as weather
import lib.calendar_ics as cal
import lib.display as display

UPDATE_INTERVAL_MINUTES = 30  # Fallback, falls secrets leer


def _load_secrets():
    try:
        from secrets import (
            WIFI_SSID, WIFI_PASSWORD,
            LATITUDE, LONGITUDE, ICS_URL, UPDATE_INTERVAL_MINUTES,
        )
        return {
            "ssid": WIFI_SSID, "psk": WIFI_PASSWORD,
            "lat": LATITUDE, "lon": LONGITUDE, "ics": ICS_URL,
            "interval": UPDATE_INTERVAL_MINUTES,
        }
    except ImportError:
        print("secrets.py fehlt / unvollstaendig")
        return {"ssid": "", "psk": "", "lat": None, "lon": None, "ics": "",
                "interval": UPDATE_INTERVAL_MINUTES}


def run():
    cfg = _load_secrets()

    # 1. WLAN
    if cfg["ssid"] and cfg["psk"]:
        if not net.network_connect(cfg["ssid"], cfg["psk"]):
            print("WLAN-Verbindung fehlgeschlagen")
    else:
        print("Keine WLAN-Daten in secrets.py")

    # 2. Zeit
    try:
        net.sync_time()
    except Exception as e:
        print("Zeit-Sync fehlgeschlagen:", e)

    # 3. Daten holen (RAM-intensiv -> vor Graphics-Instanz)
    weather_data = None
    events = []
    try:
        if cfg["lat"] is not None and cfg["lon"] is not None:
            weather_data = weather.fetch(cfg["lat"], cfg["lon"])
        gc.collect()
    except Exception as e:
        print("Wetter-Fehler:", e)

    try:
        if cfg["ics"]:
            events = cal.fetch_upcoming(cfg["ics"], max_items=4)
        gc.collect()
    except Exception as e:
        print("Kalender-Fehler:", e)

    # 4. Zeichnen
    try:
        display.render(weather_data, events)
    except Exception as e:
        print("Display-Fehler:", e)

    # 5. Schlafen
    gc.collect()
    try:
        net.sleep_for(cfg["interval"])
    except Exception as e:
        print("Sleep-Fehler:", e)


run()
