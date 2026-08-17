"""Haupt-Skript fuer den Inky Frame 7.3".

Zyklischer Ablauf:
  1. WLAN verbinden + Zeit syncen
  2. Wetter (heute+morgen, 3h-Slots) holen
  3. Kalender (Google + Nextcloud) mergen -> 7 Tage Termine + 30T Geburtstage
  4. Shelly EM3: zwei Module lesen, Differenz + Historie (state.json)
  5. Dashboard zeichnen + updaten
  6. Schlafen legen

Shelly-Daten werden oefter aktualisiert: das Display wird bei jedem Wake
neu gezeichnet, aber Wetter/Kalender nur, wenn ihr Intervall abgelaufen ist
(getrennte Zaehler via state.json).
"""
import gc
import lib.network as net
import lib.weather as weather
import lib.calendar_ics as cal
import lib.shelly as shelly
import lib.state as state
import lib.display as display

# Intervalle (Minuten)
SHELLY_INTERVAL_MIN = 5     # Shelly alle 5 Min
FULL_INTERVAL_MIN = 30      # Wetter+Kalender+Vollzeichnung alle 30 Min


def _load_secrets():
    try:
        from secrets import (
            WIFI_SSID, WIFI_PASSWORD,
            LATITUDE, LONGITUDE,
            ICS_URL_GOOGLE, ICS_URL_NEXTCLOUD,
            SHELLY_EM3_IP_A, SHELLY_EM3_IP_B, SHELLY_EM3_TOKEN,
            UPDATE_INTERVAL_MINUTES,
        )
        return {
            "ssid": WIFI_SSID, "psk": WIFI_PASSWORD,
            "lat": LATITUDE, "lon": LONGITUDE,
            "ics_google": ICS_URL_GOOGLE, "ics_next": ICS_URL_NEXTCLOUD,
            "shelly_a": SHELLY_EM3_IP_A, "shelly_b": SHELLY_EM3_IP_B,
            "shelly_token": getattr(__import__("secrets"), "SHELLY_EM3_TOKEN", ""),
            "interval": UPDATE_INTERVAL_MINUTES,
        }
    except ImportError:
        print("secrets.py fehlt / unvollstaendig")
        return {"ssid": "", "psk": "", "lat": None, "lon": None,
                "ics_google": "", "ics_next": "", "shelly_a": "", "shelly_b": "",
                "shelly_token": "", "interval": FULL_INTERVAL_MIN}


def _fetch_weather(cfg):
    if cfg["lat"] is None or cfg["lon"] is None:
        return None
    try:
        return weather.fetch(cfg["lat"], cfg["lon"])
    except Exception as e:
        print("Wetter-Fehler:", e)
        return None


def _fetch_calendar(cfg):
    urls = [u for u in (cfg["ics_google"], cfg["ics_next"]) if u]
    if not urls:
        return [], []
    try:
        events = cal.fetch_and_merge(urls)
        next7 = cal.filter_next_days(events, 7)
        birthdays = cal.filter_birthdays(events, 30)
        return next7, birthdays
    except Exception as e:
        print("Kalender-Fehler:", e)
        return [], []


def _fetch_shelly(cfg):
    if not cfg["shelly_a"] or not cfg["shelly_b"]:
        return None
    try:
        return shelly.fetch(cfg["shelly_a"], cfg["shelly_b"], cfg["shelly_token"])
    except Exception as e:
        print("Shelly-Fehler:", e)
        return None


def run():
    cfg = _load_secrets()

    # 1. WLAN + Zeit
    if cfg["ssid"] and cfg["psk"]:
        if not net.network_connect(cfg["ssid"], cfg["psk"]):
            print("WLAN-Verbindung fehlgeschlagen")
    try:
        net.sync_time()
    except Exception as e:
        print("Zeit-Sync fehlgeschlagen:", e)

    # 2-4. Daten holen (vor Graphics-Instanz wegen RAM)
    weather_data = _fetch_weather(cfg)
    gc.collect()
    next7, birthdays = _fetch_calendar(cfg)
    gc.collect()
    shelly_res = _fetch_shelly(cfg)
    gc.collect()

    # Shelly-Historie pflegen
    if shelly_res and shelly_res.get("diff") is not None:
        state.append_shelly_sample(shelly_res["diff"])
    shelly_history = state.get_shelly_history()
    shelly_current = shelly_res["diff"] if (shelly_res and shelly_res.get("ok")) else None

    # 5. Zeichnen
    try:
        display.render(weather_data, next7, birthdays, shelly_history, shelly_current)
    except Exception as e:
        print("Display-Fehler:", e)

    # 6. Schlafen
    gc.collect()
    try:
        net.sleep_for(cfg.get("interval") or SHELLY_INTERVAL_MIN)
    except Exception as e:
        print("Sleep-Fehler:", e)


run()
