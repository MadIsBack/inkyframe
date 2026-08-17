"""ICS/iCal-Parser mit Zeitzonenkonvertierung + Merge zweier Feeds.

Unterstuetzt:
- Zeilen-Folding (Fortsetzungszeilen mit Leerzeichen/Tab)
- DTSTART/DTEND Parsing (YYYYMMDDTHHMMSS[Z] und YYYYMMDD)
- Zeitzonen-Versatz: UTC `Z` wird korrekt in lokale Zeit konvertiert.
  Reine TZID-basierte (z.B. Europe/Berlin) Versaetze koennen unter
  MicroPython nicht zuverlaessig berechnet werden -> hier wird die
  im Feed angegebene Uhrzeit als lokal interpretiert (Doku in Context.md).
- Merge + Dedup zweier Feeds (Google + Nextcloud) anhand (start, summary).

Laeuft unter MicroPython und CPython (fuer Tests).
"""
import time as _time

# Lokaler Zeitzonenversatz (Sekunden) vs. UTC, wird zur Laufzeit ermittelt.
# Unter MicroPython ist die Zeit nach NTP typischerweise UTC; wir berechnen
# den Versatz aus time.mktime vs. gmtime. Falls nicht bestimmbar -> 0 (UTC).
_LOCAL_OFFSET = None


def _local_offset():
    """Liefert den lokalen Versatz zu UTC in Sekunden (memoisiert)."""
    global _LOCAL_OFFSET
    if _LOCAL_OFFSET is not None:
        return _LOCAL_OFFSET
    try:
        t = _time.time()
        local = _time.mktime(_time.localtime(t))
        gm = _time.mktime(_time.gmtime(t))
        _LOCAL_OFFSET = int(local - gm)
    except Exception:
        _LOCAL_OFFSET = 0
    return _LOCAL_OFFSET


def _unfold(lines):
    """ICS-Zeilen entfalten."""
    out = []
    for raw in lines:
        line = raw.rstrip("\r\n")
        if line[:1] in (" ", "\t"):
            if out:
                out[-1] += line[1:]
        else:
            out.append(line)
    return out


def _safe_mktime(tup):
    """mktime mit Fallback fuer extreme Jahre.

    mktime erwartet ein 9-Tupel (tm_isdst=-1 = Automatik). Bei nicht
    konvertierbaren Daten (z.B. sehr ferne Jahre) wird None geliefert,
    damit der Termin verworfen statt mit falscher Uhrzeit angezeigt wird.
    """
    y = tup[0]
    # Ferne Jahre: mktime nicht zuverlaessig -> verwerfen.
    if y < 1970 or y > 2100:
        return None
    full = (tup[0], tup[1], tup[2], tup[3], tup[4], tup[5], 0, 0, -1)
    try:
        return int(_time.mktime(full))
    except (OverflowError, ValueError, OSError, TypeError):
        return None


def _parse_dt(value, is_utc):
    """Parst einen Datumswert. Liefert lokale epoch-Sekunden."""
    if not value:
        return None
    value = value.strip()
    if is_utc is None:
        is_utc = value.endswith("Z")
    core = value.replace("Z", "")
    try:
        y = int(core[0:4]); mo = int(core[4:6]); d = int(core[6:8])
        if "T" in core:
            h = int(core[9:11]); mi = int(core[11:13]); s = int(core[13:15] or 0)
        else:
            h = mi = s = 0
    except (ValueError, IndexError):
        return None
    if is_utc:
        # UTC-Wert: _safe_mktime interpretiert das Tupel als lokal und liefert
        # somit (echte UTC-epoch + local_offset). Um die echte UTC-epoch zu
        # erhalten, ziehen wir den Versatz ab. localtime(UTC-epoch) zeigt dann
        # die korrekte lokale Uhrzeit.
        ts = _safe_mktime((y, mo, d, h, mi, s))
        if ts is None:
            return None
        return ts - _local_offset()
    # Lokaler Wert (inkl. TZID): direkt als lokal interpretieren.
    return _safe_mktime((y, mo, d, h, mi, s))


def _fmt_local(ts):
    """Formatiert epoch als 'HH:MM'."""
    if ts is None:
        return "?"
    t = _time.localtime(ts)
    return "{:02d}:{:02d}".format(t[3], t[4])


def _fmt_date(ts):
    """Formatiert epoch als 'TT.MM.'."""
    if ts is None:
        return "??.??."
    t = _time.localtime(ts)
    return "{:02d}.{:02d}.".format(t[2], t[1])


def _parse_feed(text):
    """Parst alle VEVENTs aus einem ICS-Text. Liefert Liste von dicts."""
    lines = _unfold(text.split("\n"))
    events = []
    cur = None
    # Tracken, ob ein DTSTART explizit UTC (Z) ist vs. mit TZID (lokal).
    cur_dt_utc = None
    for line in lines:
        if line == "BEGIN:VEVENT":
            cur = {}
            cur_dt_utc = None
        elif line == "END:VEVENT":
            if cur is not None and cur.get("start_ts") is not None:
                cur["start_str"] = _fmt_local(cur["start_ts"])
                cur["date_str"] = _fmt_date(cur["start_ts"])
                events.append(cur)
            else:
                # start_ts nicht konvertierbar -> dt_raw fuer Geburtstage behalten
                if cur is not None and cur.get("dt_raw"):
                    cur["start_str"] = "??"
                    cur["date_str"] = "??"
                    events.append(cur)
            cur = None
        elif cur is not None and ":" in line:
            key, _, value = line.partition(":")
            params = key.split(";")
            base_key = params[0].lower()
            # TZID-Parameter erkennen (z.B. DTSTART;TZID=Europe/Berlin:...)
            tzid = None
            for p in params[1:]:
                if p.upper().startswith("TZID="):
                    tzid = p.split("=", 1)[1]
            if base_key == "summary":
                cur["summary"] = value
            elif base_key == "location":
                cur["location"] = value
            elif base_key == "dtstart":
                is_utc = value.endswith("Z")
                if tzid and not is_utc:
                    is_utc = False
                cur["dt_raw"] = value
                cur["start_ts"] = _parse_dt(value, is_utc)
            elif base_key == "dtend":
                is_utc = value.endswith("Z")
                if tzid and not is_utc:
                    is_utc = False
                cur["end_ts"] = _parse_dt(value, is_utc)
            # RRULE: wiederkehrende Termine (rudimentaer fuer Geburtstage)
            elif base_key == "rrule":
                cur["rrule"] = value
    events.sort(key=lambda e: e["start_ts"])
    return events


def _http_get_text(url):
    """Liefert Rohtext eines ICS-Feeds."""
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


def _dedup(events):
    """Entfernt Duplikate anhand (start_ts, summary)."""
    seen = set()
    out = []
    for e in events:
        key = (e.get("start_ts"), e.get("summary"))
        if key in seen:
            continue
        seen.add(key)
        out.append(e)
    return out


def parse(text):
    """Oeffentliche API: parst einen einzelnen ICS-Text."""
    return _parse_feed(text)


def fetch_and_merge(urls, now_ts=None):
    """Holt mehrere ICS-Feeds, merged + dedup, liefert sortierte Liste."""
    if isinstance(urls, str):
        urls = [urls]
    all_events = []
    for url in urls:
        if not url:
            continue
        try:
            text = _http_get_text(url)
            all_events.extend(_parse_feed(text))
        except Exception as e:
            print("calendar_ics: feed {}: {}".format(url, e))
    events = _dedup(all_events)
    now = now_ts if now_ts is not None else _time.time()
    # nur zukuenftige (oder aktuell laufende) Termine
    upcoming = [e for e in events if (e.get("end_ts") or e["start_ts"]) >= now]
    return upcoming


def filter_next_days(events, days, now_ts=None):
    """Liefert Termine in den naechsten `days` Tagen ab jetzt."""
    now = now_ts if now_ts is not None else _time.time()
    horizon = now + days * 86400
    return [e for e in events if e["start_ts"] <= horizon]


def filter_birthdays(events, days, now_ts=None):
    """Filtert Geburtstage (wiederkehrende, RRULE FREQ=YEARLY) der naechsten
    `days` Tage. Berechnet das naechste jaehrliche Vorkommen ab heute.

    Heuristik: ein Event gilt als Geburtstag, wenn RRULE FREQ=YEARLY enthaelt
    oder die SUMMARY ein Geburtsjahr-Format hat / 'geburtstag' enthaelt.
    """
    now = now_ts if now_ts is not None else _time.time()
    horizon = now + days * 86400
    today = _time.localtime(now)
    results = []
    for e in events:
        rrule = (e.get("rrule") or "").upper()
        is_yearly = "FREQ=YEARLY" in rrule or "GEBURTSTAG" in (e.get("summary") or "").upper()
        if not is_yearly:
            continue
        # Monat/Tag aus dem Original-Datum (start_ts kann bei alten Jahren -1 sein).
        mo = d = 1; h = mi = s = 0
        raw = e.get("dt_raw") or ""
        core = raw.replace("Z", "")
        try:
            mo = int(core[4:6]); d = int(core[6:8])
            if "T" in core:
                h = int(core[9:11]); mi = int(core[11:13])
        except (ValueError, IndexError):
            continue
        # Naechstes Vorkommen: Monat/Tag im aktuellen oder naechsten Jahr.
        for year_off in (0, 1):
            y = today[0] + year_off
            ts = _safe_mktime((y, mo, d, h, mi, s))
            if ts is None:
                continue
            if now <= ts <= horizon:
                c = dict(e)
                c["next_ts"] = ts
                c["date_str"] = _fmt_date(ts)
                results.append(c)
                break
    results.sort(key=lambda x: x.get("next_ts", 0))
    return results
