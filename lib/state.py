"""Persistenz-Helfer: Historie der Shelly-Differenz in state.json puffern.

Speichert eine Liste von Werten (z.B. letzter 24h im Minutentakt) auf dem
Geraet. Schema:
  {"shelly_history": [{"t": <epoch>, "v": <float>}], "shelly_last": <float>}

Laeuft unter MicroPython und CPython (fuer Tests).
"""
import json
import os
import time as _time

STATE_FILE = "state.json"
# Maximal gespeicherte Stichproben (aelteste werden verworfen).
MAX_HISTORY = 288  # z.B. 24h bei 5-Minuten-Takt


def _load():
    try:
        with open(STATE_FILE, "r") as f:
            return json.loads(f.read())
    except (OSError, ValueError):
        return {}


def _save(data):
    with open(STATE_FILE, "w") as f:
        f.write(json.dumps(data))
        f.flush()


def append_shelly_sample(value, now_ts=None, max_history=MAX_HISTORY):
    """Haengt einen Shelly-Differenz-Wert an die Historie an."""
    if value is None:
        return
    data = _load()
    hist = data.get("shelly_history", [])
    ts = now_ts if now_ts is not None else _time.time()
    hist.append({"t": ts, "v": float(value)})
    if len(hist) > max_history:
        hist = hist[-max_history:]
    data["shelly_history"] = hist
    data["shelly_last"] = float(value)
    _save(data)


def get_shelly_history():
    """Liefert die gespeicherte Historie als Liste von dicts."""
    return _load().get("shelly_history", [])


def get_shelly_last():
    """Liefert den zuletzt gespeicherten Wert (float) oder None."""
    return _load().get("shelly_last")


def clear():
    """Loescht die State-Datei (fuer Tests)."""
    try:
        os.remove(STATE_FILE)
    except OSError:
        pass
