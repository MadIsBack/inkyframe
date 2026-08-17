"""Display/Layout-Modul fuer den Inky Frame 7.3" (800x480).

Baut die PicoGraphics-Instanz auf und zeichnet Wetter + Termine.
Die Graphics-Instanz wird bewusst spaet erzeugt (RAM-Pattern).
"""
from inky_frame import BLACK, WHITE, GREEN, BLUE, RED, YELLOW, ORANGE


def make_graphics():
    """Erzeugt die PicoGraphics-Instanz fuer 7.3\"."""
    # 7.3" Standard; fuer Spectra: DISPLAY_INKY_FRAME_SPECTRA_7
    try:
        from picographics import DISPLAY_INKY_FRAME_7 as DISPLAY
    except ImportError:
        from picographics import DISPLAY_INKY_FRAME as DISPLAY
    from picographics import PicoGraphics
    graphics = PicoGraphics(DISPLAY)
    return graphics


def _init(graphics):
    graphics.set_font("bitmap8")
    width, height = graphics.get_bounds()
    graphics.set_pen(WHITE)
    graphics.clear()
    return width, height


def _header(graphics, width):
    graphics.set_pen(BLACK)
    graphics.rectangle(0, 0, width, 50)
    graphics.set_pen(WHITE)
    graphics.text("Wetter & Termine", 16, 16, width, 3)
    # Datum/Uhrzeit rechts im Header
    import time
    t = time.localtime()
    stamp = "{:02d}.{:02d}.{:04d}  {:02d}:{:02d}".format(t[2], t[1], t[0], t[3], t[4])
    graphics.text(stamp, width - 300, 16, width, 2)


def _draw_weather(graphics, width, height, weather):
    if not weather:
        graphics.set_pen(RED)
        graphics.text("Wetter nicht verfuegbar", 16, 70, width, 2)
        return
    y = 70
    graphics.set_pen(BLACK)
    graphics.text("Wetter", 16, y, width, 2)
    y += 28
    temp = weather.get("current_temp")
    if temp is not None:
        graphics.set_pen(BLUE)
        graphics.text("{:.1f} C".format(temp), 16, y, width, 6)
    y += 70
    graphics.set_pen(BLACK)
    graphics.text(weather.get("current_text", "?"), 16, y, width, 2)
    y += 30
    wind = weather.get("current_wind")
    if wind is not None:
        graphics.text("Wind: {:.0f} km/h".format(wind), 16, y, width, 2)
    # Tageswerte
    y += 30
    hi = weather.get("today_max"); lo = weather.get("today_min")
    if hi is not None and lo is not None:
        graphics.set_pen(RED)
        graphics.text("Max {:.0f}".format(hi), 16, y, width, 2)
        graphics.set_pen(GREEN)
        graphics.text("Min {:.0f}".format(lo), 140, y, width, 2)
    y += 30
    graphics.set_pen(ORANGE)
    graphics.text(weather.get("today_text", ""), 16, y, width, 2)


def _draw_events(graphics, width, height, events):
    # Termine in der rechten Haelfte
    x = width // 2
    y = 70
    graphics.set_pen(BLACK)
    graphics.text("Termine", x, y, width, 2)
    y += 30
    if not events:
        graphics.set_pen(BLACK)
        graphics.text("Keine Termine", x, y, width, 2)
        return
    graphics.set_pen(BLUE)
    graphics.line(x - 10, 60, x - 10, height - 20)
    for ev in events:
        if y > height - 40:
            break
        graphics.set_pen(RED)
        graphics.text(ev.get("start_str", "?"), x, y, width, 3)
        y += 26
        graphics.set_pen(BLACK)
        graphics.text(ev.get("summary", "(ohne Titel)"), x, y, width - x, 2)
        y += 22
        if ev.get("location"):
            graphics.set_pen(GREEN)
            graphics.text(ev["location"], x, y, width - x, 2)
            y += 20
        y += 10


def render(weather, events):
    """Haupt-Einstieg: baut Graphics auf, zeichnet alles, updated das Display."""
    graphics = make_graphics()
    width, height = _init(graphics)
    _header(graphics, width)
    _draw_weather(graphics, width, height, weather)
    _draw_events(graphics, width, height, events)
    graphics.update()
