"""Wetter-Icons, als PicoGraphics-Primitive gezeichnet.

Jede draw_*-Funktion zeichnet ein Icon zentriert in ein Quadrat der
Groesse `size` an Position (x, y). Die Stiftfarbe wird von `graphics`
selbst gesetzt (Aufrufer kann Farbe waehlen).

WMO-Kategorie -> Icon-Funktion:
  clear / mainly-clear   -> Sonne
  partly-cloudy          -> Sonne+Wolke
  overcast / fog         -> Wolke
  drizzle / rain         -> Wolke+Regentropfen
  snow                   -> Wolke+Schneeflocken
  thunderstorm           -> Wolke+Blitz

Laeuft unter MicroPython (PicoGraphics) und CPython (fuer Tests mit Mock).
"""


def _icon_for_category(cat):
    """Mappt WMO-Kategorie auf Zeichenfunktion."""
    return {
        "clear": draw_sun,
        "mainly-clear": draw_sun,
        "partly-cloudy": draw_partly_cloudy,
        "overcast": draw_cloud,
        "fog": draw_cloud,
        "drizzle": draw_rain,
        "rain": draw_rain,
        "snow": draw_snow,
        "thunderstorm": draw_thunderstorm,
    }.get(cat, draw_cloud)


def draw_by_category(graphics, cat, x, y, size):
    """Zeichnet das Icon fuer `cat` an (x, y) mit Groesse `size`."""
    fn = _icon_for_category(cat)
    fn(graphics, x, y, size)


def draw_sun(graphics, x, y, size):
    """Sonne: Kreis + Strahlen."""
    import math
    cx = x + size // 2
    cy = y + size // 2
    r = max(1, size // 4)
    graphics.circle(cx, cy, r)
    # 8 Strahlen
    for i in range(8):
        a = i * math.pi / 4
        inner = r + 2
        outer = r + size // 3
        x1 = int(cx + math.cos(a) * inner)
        y1 = int(cy + math.sin(a) * inner)
        x2 = int(cx + math.cos(a) * outer)
        y2 = int(cy + math.sin(a) * outer)
        graphics.line(x1, y1, x2, y2)


def _cloud_shape(graphics, x, y, size):
    """Wolke aus ueberlappenden Kreisen + Unterseite."""
    w = size
    cx = x + w // 2
    cy = y + w // 2
    r = max(1, w // 4)
    # Drei Kreise fuer die Wolkform
    graphics.circle(cx - r, cy, r)
    graphics.circle(cx + r, cy, r)
    graphics.circle(cx, cy - r // 2, r + 1)
    # Unterseite als Linie
    graphics.line(cx - 2 * r, cy + r // 2, cx + 2 * r, cy + r // 2)


def draw_cloud(graphics, x, y, size):
    _cloud_shape(graphics, x, y, size)


def draw_partly_cloudy(graphics, x, y, size):
    # Sonne oben links, Wolke unten rechts
    draw_sun(graphics, x, y, size * 2 // 3)
    _cloud_shape(graphics, x + size // 3, y + size // 3, size * 2 // 3)


def draw_rain(graphics, x, y, size):
    _cloud_shape(graphics, x, y, size)
    # Tropfen unter der Wolke
    cx = x + size // 2
    base_y = y + size // 2 + size // 4
    r = max(1, size // 4)
    for dx in (-r, 0, r):
        graphics.line(cx + dx, base_y, cx + dx, base_y + size // 4)


def draw_snow(graphics, x, y, size):
    _cloud_shape(graphics, x, y, size)
    # Sternchen unter der Wolke
    cx = x + size // 2
    base_y = y + size // 2 + size // 4
    r = max(1, size // 6)
    for dx in (-size // 3, 0, size // 3):
        graphics.line(cx + dx - r, base_y, cx + dx + r, base_y)
        graphics.line(cx + dx, base_y - r, cx + dx, base_y + r)


def draw_thunderstorm(graphics, x, y, size):
    _cloud_shape(graphics, x, y, size)
    # Blitz unter der Wolke
    cx = x + size // 2
    base_y = y + size // 2
    h = size // 3
    # Zickzack
    graphics.line(cx, base_y, cx - h // 2, base_y + h)
    graphics.line(cx - h // 2, base_y + h, cx, base_y + h)
    graphics.line(cx, base_y + h, cx + h // 2, base_y + 2 * h)
    graphics.line(cx, base_y + h + h // 2, cx, base_y + 2 * h)


def draw_fog(graphics, x, y, size):
    _cloud_shape(graphics, x, y, size * 2 // 3)
    # Nebellinien darunter
    cx = x + size // 2
    base_y = y + size // 2 + size // 5
    for off in (0, size // 5):
        graphics.line(cx - size // 3, base_y + off, cx + size // 3, base_y + off)
