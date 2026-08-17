"""Wetter-Modul: Open-Meteo, 3-Stunden-Zyklus, heute + morgen.

Kein API-Key noetig (https://open-meteo.com). Holt hourly-Daten fuer
den aktuellen und den naechsten Tag, aggregiert auf 3h-Slots.

Laeuft unter MicroPython (urequests) und CPython (urllib, fuer Tests).
"""
import time as _time

WMO_CODES = {
    0: ("Klar", "clear"),
    1: ("Ueberw. klar", "mainly-clear"),
    2: ("Teilw. bewoelkt", "partly-cloudy"),
    3: ("Bewoelkt", "overcast"),
    45: ("Nebel", "fog"),
    48: ("Reifnebel", "fog"),
    51: ("Nieselregen", "drizzle"),
    53: ("Nieselregen", "drizzle"),
    55: ("Nieselregen", "drizzle"),
    56: ("Gefr. Niesel", "drizzle"),
    57: ("Gefr. Niesel", "drizzle"),
    61: ("Regen", "rain"),
    63: ("Regen", "rain"),
    65: ("Starker Regen", "rain"),
    66: ("Gefr. Regen", "rain"),
    67: ("Gefr. Regen", "rain"),
    71: ("Schnee", "snow"),
    73: ("Schnee", "snow"),
    75: ("Starker Schnee", "snow"),
    77: ("Schneegruessel", "snow"),
    80: ("Regenschauer", "rain"),
    81: ("Regenschauer", "rain"),
    82: ("Starke Schauer", "rain"),
    85: ("Schneeschauer", "snow"),
    86: ("Schneeschauer", "snow"),
    95: ("Gewitter", "thunderstorm"),
    96: ("Gewitter+Hagel", "thunderstorm"),
    99: ("Gewitter+Hagel", "thunderstorm"),
}


def describe(code):
    """(deutscher Text, kategorie) fuer einen WMO-Code."""
    return WMO_CODES.get(code, ("Unbekannt", "unknown"))


def _http_get_json(url, timeout=10):
    import json
    try:
        import urequests
        r = urequests.get(url, timeout=timeout)
        data = r.json()
        r.close()
        return data
    except ImportError:
        from urllib.request import urlopen
        with urlopen(url, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))


def _slot_of(iso_time):
    """Aus ISO-Zeit 'YYYY-MM-DDTHH:00' den 3h-Slot-Stunde (0,3,6,9,...) holen."""
    try:
        hour = int(iso_time[11:13])
    except (ValueError, IndexError):
        return 0
    return (hour // 3) * 3


def _local_offset():
    """Lokaler UTC-Versatz in Sekunden."""
    try:
        t = _time.time()
        local = _time.mktime(_time.localtime(t))
        gm = _time.mktime(_time.gmtime(t))
        return int(local - gm)
    except Exception:
        return 0


def _today_str(now_ts=None):
    now = now_ts if now_ts is not None else _time.time()
    t = _time.localtime(now)
    return "{:04d}-{:02d}-{:02d}".format(t[0], t[1], t[2])


def fetch(latitude, longitude, now_ts=None):
    """Holt Wetter: aktueller Wert + 3h-Slots fuer heute und morgen.

    Liefert dict:
      current_temp, current_code, current_text,
      today: [ {hour, temp, code, text, pop} ]   # 3h-Slots heute
      tomorrow: [ {hour, temp, code, text, pop} ]# 3h-Slots morgen
      today_max, today_min, tomorrow_max, tomorrow_min
    """
    url = (
        "https://api.open-meteo.com/v1/forecast?"
        "latitude={lat}&longitude={lon}"
        "&current=temperature_2m,weather_code,wind_speed_10m"
        "&hourly=temperature_2m,weather_code,precipitation_probability"
        "&daily=temperature_2m_max,temperature_2m_min,weather_code"
        "&timezone=auto"
        "&forecast_days=2"
    ).format(lat=latitude, lon=longitude)
    print("wetter: request")
    j = _http_get_json(url)

    cur = j.get("current", {})
    hourly = j.get("hourly", {})
    daily = j.get("daily", {})

    code = cur.get("weather_code")
    text, _ = describe(code) if code is not None else ("Unbekannt", "unknown")

    # Stundenwerte in 3h-Slots pro Tag gruppieren.
    times = hourly.get("time", [])
    temps = hourly.get("temperature_2m", [])
    codes = hourly.get("weather_code", [])
    pops = hourly.get("precipitation_probability", [])

    today_str = _today_str(now_ts)
    slots_by_day = {"today": [], "tomorrow": []}
    for i, t in enumerate(times):
        if i >= len(temps) or i >= len(codes):
            break
        day = "today" if (t and t[:10] == today_str) else "tomorrow"
        if day not in slots_by_day:
            continue
        slot = _slot_of(t)
        # pro Slot den mittleren Wert nehmen (vereinfacht: letzten des Slots)
        c_text, _ = describe(codes[i])
        slots_by_day[day].append({
            "hour": slot,
            "temp": temps[i],
            "code": codes[i],
            "text": c_text,
            "pop": pops[i] if i < len(pops) else None,
        })

    # auf unique 3h-Slots reduzieren (ersten Eintrag je Slot behalten)
    for d in slots_by_day:
        seen = set()
        reduced = []
        for s in slots_by_day[d]:
            if s["hour"] in seen:
                continue
            seen.add(s["hour"])
            reduced.append(s)
        slots_by_day[d] = sorted(reduced, key=lambda x: x["hour"])

    dmax = daily.get("temperature_2m_max", [])
    dmin = daily.get("temperature_2m_min", [])
    dcodes = daily.get("weather_code", [])

    return {
        "current_temp": cur.get("temperature_2m"),
        "current_code": code,
        "current_text": text,
        "current_wind": cur.get("wind_speed_10m"),
        "today": slots_by_day["today"],
        "tomorrow": slots_by_day["tomorrow"],
        "today_max": dmax[0] if dmax else None,
        "today_min": dmin[0] if dmin else None,
        "today_code": dcodes[0] if dcodes else None,
        "tomorrow_max": dmax[1] if len(dmax) > 1 else None,
        "tomorrow_min": dmin[1] if len(dmin) > 1 else None,
        "tomorrow_code": dcodes[1] if len(dcodes) > 1 else None,
    }
