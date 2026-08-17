"""Shelly EM3-Auslesung: zwei Module, aktuelle Leistung, Differenz.

Unterstuetzt Gen1 (REST /status, Feld emeters[].power / total_power) und
Gen2/Gen3 Pro 3EM (RPC /rpc/EM.GetStatus, Feld total_act_power) via
Autodetection: es wird versucht, beide Endpunkte zu lesen.

Vorzeichen-Konvention (Shelly-Standard):
  positiver Wert = Leistungsaufnahme (Bezug)
  negativer Wert = Einspeisung (Lieferung)

Laeuft unter MicroPython (urequests) und CPython (urllib, fuer Tests).
"""

# Maximale Anzahl Versuche pro Shelly-Modul
MAX_ATTEMPTS = 2
# Timeout je Request (Sekunden) - auf dem Geraet kurz halten
REQUEST_TIMEOUT = 8


def _http_get_json(url, timeout=REQUEST_TIMEOUT):
    """HTTP-GET, liefert geparstes JSON (dict). Plattformabhaengig."""
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


def _gen2_power(base_url, token=""):
    """Gen2/Pro 3EM: /rpc/EM.GetStatus?id=0 -> total_act_power (W)."""
    url = base_url.rstrip("/") + "/rpc/EM.GetStatus?id=0"
    if token:
        url += "&auth=" + token
    j = _http_get_json(url)
    # RPC-Antwort: {"result": {"total_act_power": ..., ...}}
    result = j.get("result", j)
    power = result.get("total_act_power")
    if power is None:
        # Fallback: Summe der Phasen
        a = result.get("a_act_power") or 0.0
        b = result.get("b_act_power") or 0.0
        c = result.get("c_act_power") or 0.0
        power = a + b + c
    return float(power)


def _gen1_power(base_url):
    """Gen1 3EM: /status -> emeters[].power (Summe) oder total_power."""
    url = base_url.rstrip("/") + "/status"
    j = _http_get_json(url)
    if "total_power" in j and j["total_power"] is not None:
        return float(j["total_power"])
    emeters = j.get("emeters", [])
    total = 0.0
    for em in emeters:
        p = em.get("power")
        if p is not None:
            total += float(p)
    return total


def read_power(base_url, token=""):
    """Liest die aktuelle Gesamtwirkleistung eines Shelly-Moduls (Watt).

    Versucht zuerst Gen2 (RPC), dann Gen1 (REST). Liefert float oder None.
    """
    last_err = None
    # Gen2 zuerst versuchen (Pro 3EM ist aktueller)
    try:
        return _gen2_power(base_url, token)
    except Exception as e:
        last_err = e
    try:
        return _gen1_power(base_url)
    except Exception as e:
        print("shelly {}: gen2+gen1 fehlgeschlagen (gen2: {}, gen1: {})".format(
            base_url, last_err, e))
        return None


def fetch(ip_a, ip_b, token=""):
    """Liest zwei Shelly-Module und berechnet die Differenz.

    Liefert dict:
      power_a, power_b, diff (A - B), ok (bool), error (str|None)
    """
    pa = read_power("http://" + ip_a, token) if ip_a else None
    pb = read_power("http://" + ip_b, token) if ip_b else None
    diff = None
    ok = False
    error = None
    if pa is not None and pb is not None:
        diff = pa - pb
        ok = True
    elif pa is None and pb is None:
        error = "beide Module nicht erreichbar"
    elif pa is None:
        error = "Modul A nicht erreichbar"
    else:
        error = "Modul B nicht erreichbar"
    return {"power_a": pa, "power_b": pb, "diff": diff, "ok": ok, "error": error}
