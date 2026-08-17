"""Minimaler ICS/iCal-Parser ohne externe Abhaengigkeiten.

Parst VEVENTs aus einem .ics-Stream und liefert kommende Termine.
Laeuft unter MicroPython und CPython (fuer Tests).
"""
import time as _time


def _unfold(lines):
    """ICS-Zeilen entfalten: Fortsetzungszeilen (Beginn mit Leerzeichen/Tab)
    an die vorherige Zeile anhaengen."""
    out = []
    for raw in lines:
        # CR entfernen, MicroPython-Dateien oft mit \r\n
        line = raw.rstrip("\r\n")
        if line[:1] in (" ", "\t"):
            if out:
                out[-1] += line[1:]
        else:
            out.append(line)
    return out


def _safe_mktime(y, mo, d, h, mi, s):
    """mktime mit Fallback fuer Jahre ausserhalb des Plattformbereichs."""
    try:
        return _time.mktime((y, mo, d, h, mi, s, 0, 0))
    except (OverflowError, ValueError, OSError, TypeError):
        # Approximation: 365.25 Tage/Jahr ab 2000 (nur fuer grobes Sortieren
        # bei sehr weit entfernten Terminen).
        if y < 2000:
            return -1
        return int(((y - 2000) * 365.25 + (mo - 1) * 30.44 + d) * 86400) + h * 3600 + mi * 60 + s


def _parse_dt(value):
    """Parst YYYYMMDDTHHMMSSZ bzw. YYYYMMDD. Liefert epoch-Sekunden (lokal).

    mktime kann bei sehr weit entfernten Jahren fehlschlagen -> robust
    via try/except, dann None (Termin wird verworfen).
    """
    if not value:
        return None
    value = value.strip()
    if "T" in value:
        core = value.replace("Z", "")
        try:
            y = int(core[0:4]); mo = int(core[4:6]); d = int(core[6:8])
            h = int(core[9:11]); mi = int(core[11:13]); s = int(core[13:15] or 0)
            return _safe_mktime(y, mo, d, h, mi, s)
        except (ValueError, IndexError):
            return None
    try:
        y = int(value[0:4]); mo = int(value[4:6]); d = int(value[6:8])
        return _safe_mktime(y, mo, d, 0, 0, 0)
    except (ValueError, IndexError):
        return None


def _fmt_local(ts):
    """Formatiert epoch-Sekunden als 'HH:MM'."""
    if ts is None:
        return "?"
    t = _time.localtime(ts)
    return "{:02d}:{:02d}".format(t[3], t[4])


def parse(text):
    """Parst alle VEVENTs aus `text`. Liefert Liste von dicts:
       {summary, start_ts, end_ts, start_str, location}."""
    lines = _unfold(text.split("\n"))
    events = []
    cur = None
    for line in lines:
        if line == "BEGIN:VEVENT":
            cur = {}
        elif line == "END:VEVENT":
            if cur is not None and cur.get("start_ts") is not None:
                cur["start_str"] = _fmt_local(cur["start_ts"])
                events.append(cur)
            cur = None
        elif cur is not None and ":" in line:
            key, _, value = line.partition(":")
            key = key.split(";", 1)[0].lower()  # Parameter wie DTSTART;TZID=... weg
            if key == "summary":
                cur["summary"] = value
            elif key == "location":
                cur["location"] = value
            elif key == "dtstart":
                cur["start_ts"] = _parse_dt(value)
            elif key == "dtend":
                cur["end_ts"] = _parse_dt(value)

    events.sort(key=lambda e: e["start_ts"])
    return events


def _http_get_text(url):
    """Liefert Rohtext eines ICS-Feeds (MicroPython urequests / CPython urllib)."""
    try:
        import urequests
        r = urequests.get(url)
        text = r.read().decode("utf-8")
        r.close()
        return text
    except ImportError:
        from urllib.request import urlopen
        with urlopen(url) as resp:
            return resp.read().decode("utf-8")


def fetch_upcoming(url, max_items=4, now_ts=None):
    """Holt den ICS-Feed und liefert die naechsten Termine ab jetzt."""
    text = _http_get_text(url)
    events = parse(text)
    now = now_ts if now_ts is not None else _time.time()
    upcoming = [e for e in events if (e.get("end_ts") or e["start_ts"]) >= now]
    return upcoming[:max_items]
