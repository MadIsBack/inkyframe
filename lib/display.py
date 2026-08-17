"""Dashboard-Layout fuer Inky Frame 7.3" (800x480).

Regionen:
  Header:   Datum + Uhrzeit (volle Breite, oben)
  Links:    Wetter (heute + morgen, 3h-Slots)
  Mitte:     Kalender naechste 7 Tage
  Rechts:   Geburtstage naechste 30 Tage
  Unten:    Shelly-Differenz-Chart (Verlauf)

Farben: Wetter=BLUE, Kalender=RED, Geburtstage=GREEN/ORANGE, Chart=YELLOW.
"""
from inky_frame import BLACK, WHITE, GREEN, BLUE, RED, YELLOW, ORANGE

# Spalten-X-Grenzen
COL_WX = 0
COL_MX = 270
COL_RX = 540
HEADER_H = 44
CHART_H = 90


def make_graphics():
    try:
        from picographics import DISPLAY_INKY_FRAME_7 as DISPLAY
    except ImportError:
        from picographics import DISPLAY_INKY_FRAME as DISPLAY
    from picographics import PicoGraphics
    return PicoGraphics(DISPLAY)


def _init(graphics):
    graphics.set_font("bitmap8")
    width, height = graphics.get_bounds()
    graphics.set_pen(WHITE)
    graphics.clear()
    return width, height


def _header(graphics, width):
    graphics.set_pen(BLACK)
    graphics.rectangle(0, 0, width, HEADER_H)
    graphics.set_pen(WHITE)
    import time
    t = time.localtime()
    stamp = "{:02d}.{:02d}.{:04d}  {:02d}:{:02d}".format(t[2], t[1], t[0], t[3], t[4])
    graphics.text("InkyFrame Dashboard", 12, 14, width, 3)
    graphics.text(stamp, width - 250, 14, width, 3)


def _draw_weather(graphics, weather):
    x = COL_WX
    y = HEADER_H + 10
    graphics.set_pen(BLUE)
    graphics.text("Wetter", x + 10, y, 250, 3)
    y += 26
    if not weather:
        graphics.set_pen(RED)
        graphics.text("nicht verfuegbar", x + 10, y, 240, 2)
        return

    # Aktuell gross
    temp = weather.get("current_temp")
    if temp is not None:
        graphics.set_pen(BLACK)
        graphics.text("{:.1f}C".format(temp), x + 10, y, 250, 4)
    graphics.set_pen(BLUE)
    graphics.text(weather.get("current_text", ""), x + 110, y + 8, 140, 2)
    wind = weather.get("current_wind")
    if wind is not None:
        graphics.text("Wind {:.0f}km/h".format(wind), x + 110, y + 26, 140, 2)
    y += 56

    # 3h-Slots heute
    graphics.set_pen(BLACK)
    graphics.text("Heute", x + 10, y, 250, 2)
    y += 18
    _draw_slots(graphics, weather.get("today", []), x + 10, y, 250)
    y += 70

    # 3h-Slots morgen
    graphics.set_pen(BLACK)
    graphics.text("Morgen", x + 10, y, 250, 2)
    y += 18
    _draw_slots(graphics, weather.get("tomorrow", []), x + 10, y, 250)


def _draw_slots(graphics, slots, x, y, w):
    if not slots:
        graphics.set_pen(RED)
        graphics.text("-", x, y, w, 2)
        return
    cols = min(len(slots), 8)
    cell_w = (w - 4) // max(cols, 1)
    for i, s in enumerate(slots[:cols]):
        cx = x + i * cell_w
        graphics.set_pen(BLACK)
        graphics.text("{:02d}".format(s["hour"]), cx, y, cell_w, 2)
        graphics.set_pen(BLUE)
        if s.get("temp") is not None:
            graphics.text("{:.0f}".format(s["temp"]), cx, y + 16, cell_w, 2)
        # Regenwahrscheinlichkeit
        pop = s.get("pop")
        if pop is not None and pop > 0:
            graphics.set_pen(GREEN)
            graphics.text("{}%".format(pop), cx, y + 32, cell_w, 1)


def _draw_calendar(graphics, events):
    x = COL_MX
    y = HEADER_H + 10
    graphics.set_pen(RED)
    graphics.text("Termine (7T)", x, y, 250, 3)
    y += 26
    if not events:
        graphics.set_pen(BLACK)
        graphics.text("keine Termine", x, y, 250, 2)
        return
    graphics.set_pen(BLUE)
    graphics.line(x - 8, HEADER_H + 4, x - 8, 460)
    for ev in events[:9]:
        if y > 440:
            break
        graphics.set_pen(RED)
        graphics.text(ev.get("date_str", "?"), x, y, 60, 2)
        graphics.set_pen(BLACK)
        graphics.text(ev.get("start_str", "?"), x + 60, y, 50, 2)
        graphics.text(ev.get("summary", "(ohne)")[:22], x, y + 16, 250, 2)
        y += 40


def _draw_birthdays(graphics, birthdays):
    x = COL_RX
    y = HEADER_H + 10
    graphics.set_pen(ORANGE)
    graphics.text("Geburtstage (30T)", x, y, 250, 3)
    y += 26
    graphics.set_pen(BLUE)
    graphics.line(x - 8, HEADER_H + 4, x - 8, 460)
    if not birthdays:
        graphics.set_pen(BLACK)
        graphics.text("keine Geburtstage", x, y, 250, 2)
        return
    for b in birthdays[:9]:
        if y > 440:
            break
        graphics.set_pen(GREEN)
        graphics.text(b.get("date_str", "?"), x, y, 60, 2)
        graphics.set_pen(ORANGE)
        graphics.text(b.get("summary", "")[:24], x + 60, y, 250, 2)
        y += 22


def _draw_chart(graphics, width, height, history):
    y0 = height - CHART_H
    graphics.set_pen(BLACK)
    graphics.line(0, y0, width, y0)
    graphics.set_pen(YELLOW)
    graphics.text("Shelly Differenz (W)", 10, y0 + 4, width, 2)
    if not history or len(history) < 2:
        graphics.set_pen(RED)
        graphics.text("keine Historie", 200, y0 + 4, width, 2)
        return
    vals = [h["v"] for h in history]
    vmin = min(vals)
    vmax = max(vals)
    span = (vmax - vmin) or 1.0
    n = len(vals)
    plot_x0 = 10
    plot_x1 = width - 10
    plot_y0 = y0 + 22
    plot_y1 = height - 6
    plot_h = plot_y1 - plot_y0
    plot_w = plot_x1 - plot_x0
    # Nulllinie, falls im Bereich
    if vmin <= 0 <= vmax:
        zy = plot_y1 - int((0 - vmin) / span * plot_h)
        graphics.set_pen(BLACK)
        graphics.line(plot_x0, zy, plot_x1, zy)
    # Linie
    prev = None
    for i, v in enumerate(vals):
        px = plot_x0 + int(i * plot_w / (n - 1))
        py = plot_y1 - int((v - vmin) / span * plot_h)
        if prev is not None:
            graphics.set_pen(BLUE)
            graphics.line(prev[0], prev[1], px, py)
        prev = (px, py)
    # aktueller Wert rechts
    graphics.set_pen(BLACK)
    graphics.text("{:.0f} W".format(vals[-1]), width - 80, y0 + 4, 80, 2)


def render(weather, events, birthdays, shelly_history=None, shelly_current=None):
    """Baut das komplette Dashboard auf und aktualisiert das Display."""
    graphics = make_graphics()
    width, height = _init(graphics)
    _header(graphics, width)
    _draw_weather(graphics, weather)
    _draw_calendar(graphics, events)
    _draw_birthdays(graphics, birthdays)
    _draw_chart(graphics, width, height, shelly_history or [])
    if shelly_current is not None:
        graphics.set_pen(BLACK)
        graphics.text("akt: {:.0f}W".format(shelly_current), width // 2 - 40,
                      height - CHART_H + 4, 120, 2)
    graphics.update()
