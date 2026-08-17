"""Wetter-Modul: Open-Meteo Abfrage + WMO-Code-Mapping.

Kein API-Key noetig, siehe https://open-meteo.com.

Laeuft unter MicroPython (urequests) und CPython (urllib, fuer Tests).
"""
WMO_CODES = {
    0: ("Klar", "clear"),
    1: ("Ueberwiegend klar", "mainly-clear"),
    2: ("Teilweise bewoelkt", "partly-cloudy"),
    3: ("Bewoelkt", "overcast"),
    45: ("Nebel", "fog"),
    48: ("Reifnebel", "fog"),
    51: ("Nieselregen", "drizzle"),
    53: ("Nieselregen", "drizzle"),
    55: ("Nieselregen", "drizzle"),
    56: ("Gefrierender Nieselregen", "drizzle"),
    57: ("Gefrierender Nieselregen", "drizzle"),
    61: ("Regen", "rain"),
    63: ("Regen", "rain"),
    65: ("Starker Regen", "rain"),
    66: ("Gefrierender Regen", "rain"),
    67: ("Gefrierender Regen", "rain"),
    71: ("Schnee", "snow"),
    73: ("Schnee", "snow"),
    75: ("Starker Schneefall", "snow"),
    77: ("Schneegruessel", "snow"),
    80: ("Regenschauer", "rain"),
    81: ("Regenschauer", "rain"),
    82: ("Starke Regenschauer", "rain"),
    85: ("Schneeschauer", "snow"),
    86: ("Schneeschauer", "snow"),
    95: ("Gewitter", "thunderstorm"),
    96: ("Gewitter mit Hagel", "thunderstorm"),
    99: ("Gewitter mit Hagel", "thunderstorm"),
}


def describe(code):
    """Gibt (deutscher Text, kategorie) fuer einen WMO-Code zurueck."""
    return WMO_CODES.get(code, ("Unbekannt", "unknown"))


def _http_get(url):
    """Plattformabhaengiger HTTP-GET, liefert geparstes JSON (dict)."""
    import json
    try:
        import urequests
        r = urequests.get(url)
        data = r.json()
        r.close()
        return data
    except ImportError:
        from urllib.request import urlopen
        with urlopen(url) as resp:
            return json.loads(resp.read().decode("utf-8"))


def fetch(latitude, longitude):
    """Holt aktuelle Wetterdaten + Kurznachmittag-Vorschau von Open-Meteo.

    Liefert ein Dict:
      current_temp, current_code, current_text, current_wind,
      today_max, today_min, today_code, today_text,
      hourly: Liste von dicts {time, temp, code}
    """
    url = (
        "https://api.open-meteo.com/v1/forecast?"
        "latitude={lat}&longitude={lon}"
        "&current=temperature_2m,weather_code,wind_speed_10m"
        "&daily=weather_code,temperature_2m_max,temperature_2m_min"
        "&timezone=auto"
        "&forecast_days=1"
    ).format(lat=latitude, lon=longitude)
    print("wetter: request", url)
    j = _http_get(url)
    cur = j.get("current", {})
    day = j.get("daily", {})
    code = cur.get("weather_code")
    text, _cat = describe(code) if code is not None else ("Unbekannt", "unknown")
    day_code = day.get("weather_code", [None])
    day_code = day_code[0] if day_code else None
    day_text, _ = describe(day_code) if day_code is not None else ("Unbekannt", "unknown")
    return {
        "current_temp": cur.get("temperature_2m"),
        "current_code": code,
        "current_text": text,
        "current_wind": cur.get("wind_speed_10m"),
        "today_max": day.get("temperature_2m_max", [None])[0] if day.get("temperature_2m_max") else None,
        "today_min": day.get("temperature_2m_min", [None])[0] if day.get("temperature_2m_min") else None,
        "today_code": day_code,
        "today_text": day_text,
    }
