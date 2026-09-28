"""Special editions for Sundays and special days: python -m simlab.publish.specials -> kits/specials/.

Five layouts, each with its own palette (themes.SPECIALS): The Ballot and The Main Event put a race's two candidates up
front, The Seismograph tells one race's week, The Chamber and The Map show the whole Senate. Names only, never faces.
Every race number still sits beside the poll average, the market and Cook. The numbers here are invented (EXAMPLE).
"""
from __future__ import annotations

from datetime import date

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Ellipse, FancyBboxPatch

from .frame import MARGIN, Slide, pt, typeset
from .racecards import DAY, RACE, benchmarks, chip, fit, margin_txt, pct_txt, strip, verdict
from .themes import BALLOT, CHAMBER, FIGHT, MAP, SEISMO

ELECTION = date(2026, 11, 3)
KICKER = "SUNDAY EDITION · EXAMPLE"
NC = RACE | {"state": "North Carolina", "usps": "NC", "code": "NC-SEN", "dem": "Roy Cooper", "rep": "Michael Whatley"}

# Senate seats not up in 2026 (EXAMPLE until Statistics supplies them): independents who caucus with Democrats count as D
HOLDOVER = {"D": 34, "R": 31}
UP = {"AL": .08, "AK": .30, "AR": .04, "CO": .86, "DE": .95, "FL": .22, "GA": .56, "ID": .02, "IL": .93, "IA": .33,
      "KS": .12, "KY": .10, "LA": .07, "ME": .51, "MA": .97, "MI": .62, "MN": .78, "MS": .09, "MT": .15, "NE": .38,
      "NH": .66, "NJ": .90, "NM": .88, "NC": .58, "OH": .44, "OK": .03, "OR": .92, "RI": .96, "SC": .11, "SD": .05,
      "TN": .06, "TX": .31, "VA": .84, "WV": .04, "WY": .02}
COOK = {"GA": "Toss-up", "ME": "Toss-up", "MI": "Toss-up", "NC": "Toss-up", "OH": "Toss-up", "NH": "Leans Democrat",
        "TX": "Likely Republican", "IA": "Likely Republican", "AK": "Leans Republican", "NE": "Likely Republican"}
TILES = """AK 0 0|ME 0 11|WI 1 6|VT 1 10|NH 1 11|WA 2 1|ID 2 2|MT 2 3|ND 2 4|MN 2 5|IL 2 6|MI 2 7|NY 2 9|MA 2 10|OR 3 1|NV 3 2
|WY 3 3|SD 3 4|IA 3 5|IN 3 6|OH 3 7|PA 3 8|NJ 3 9|CT 3 10|RI 3 11|CA 4 1|UT 4 2|CO 4 3|NE 4 4|MO 4 5|KY 4 6|WV 4 7
|VA 4 8|MD 4 9|DE 4 10|AZ 5 2|NM 5 3|KS 5 4|AR 5 5|TN 5 6|NC 5 7|SC 5 8|OK 6 4|LA 6 5|MS 6 6|AL 6 7|GA 6 8|HI 7 0
|TX 7 3|FL 7 8"""
TILE = {k: (int(r), int(c)) for k, r, c in (t.split() for t in TILES.replace("\n", "").split("|"))}
HISTORY = [.50, .51, .50, .52, .51, .55, .56, .55, .54, .49, .50, .53, .57, .58]
EVENTS = [(5, "The Democratic candidate released an ad on prices at the grocery store.", 3.1),
          (9, "The Republican candidate was endorsed by a popular former governor.", -4.6),
          (12, "A hurricane recovery bill passed with support from both candidates.", 2.2)]


def rating(p: float) -> str:
    return verdict(p).replace("Democrat", "D").replace("Republican", "R")


def mix(c: str, bg: str, a: float) -> str:
    f = lambda h: np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)])
    return "#" + "".join(f"{round(v):02X}" for v in f(c) * a + f(bg) * (1 - a))


def lum(c: str) -> float:
    return sum(int(c[i:i + 2], 16) * w for i, w in ((1, 0.2126), (3, 0.7152), (5, 0.0722))) / 255


def light_of(t) -> str:
    """The theme's lighter base (paper on light themes, ink on dark ones): "leans" tints move toward it."""
    return t.paper if lum(t.paper) > lum(t.ink) else t.ink


def rating_color(t, p: float) -> str:
    if 0.35 <= p <= 0.65:
        return t.ai
    c = t.dem if p > 0.5 else t.rep
    return c if max(p, 1 - p) >= 0.8 else mix(c, light_of(t), 0.55)


def surname(name: str) -> str:
    return name.split()[-1]


def days_left(day: date) -> int:
    return (ELECTION - day).days


def base(t, r: dict) -> Slide:
    return Slide(r.get("day", DAY), r.get("kicker", KICKER), t, run=r.get("run"))


def source(s: Slide, r: dict, layout: str):
    s.source(r.get("source") or f"EXAMPLE: invented numbers, not a forecast. Special edition: {layout}.")


def ballot(r: dict = NC, t=BALLOT) -> Slide:
    """The Ballot: a specimen ballot with both names, each oval marked as far as that candidate's share of simulated
    elections won. Nobody casts it; 40,000 simulated elections fill it in."""
    s = base(t, r)
    x0, x1 = MARGIN, s.w - MARGIN
    top = s.y + 4
    s.ax.add_patch(plt.Rectangle((x0, top), x1 - x0, 64, color=t.ink, lw=0, zorder=2))
    s._put(x0 + 24, top + 32, "SPECIMEN · SIMULATED BALLOT", "mono", 600, 24, t.paper, va="center", zorder=3)
    s._put(x1 - 24, top + 32, "COUNTED 40,000 TIMES", "mono", 400, 24, t.paper, ha="right", va="center", zorder=3)
    y = top + 96
    office = "United States Senator" + (" (special)" if "special" in r.get("office", "").lower() else "")
    s._put(x0 + 28, y, office.upper(), "sans", 800, 40, t.ink, va="top")
    s._put(x0 + 28, y + 52, f"{r['state']} · Vote for one", "sans", 400, 30, t.ink2, va="top")
    y += 118
    rows = [(r["dem"], "Independent" if r.get("left_party") == "I" else "Democratic", t.dem, r["p"]), (r["rep"], "Republican", t.rep, 1 - r["p"])]
    for name, party, col, share in rows:
        s.ax.plot([x0, x1], [y, y], color=t.ink, lw=pt(2))
        cy = y + 96
        ow, oh, ox = 116, 64, x0 + 28
        s.ax.add_patch(Ellipse((ox + ow / 2, cy), ow, oh, fill=False, ec=t.ink, lw=pt(4), zorder=3))
        clip = Ellipse((ox + ow / 2, cy), ow - 10, oh - 10, transform=s.ax.transData)
        for k in np.arange(-oh, ow * share, 7):  # pencil strokes, only as far as the share
            ln, = s.ax.plot([ox + k, ox + k + oh], [cy + oh / 2, cy - oh / 2], color=col, lw=pt(5), zorder=2,
                            solid_capstyle="round")
            ln.set_clip_path(clip)
        edge = ox + ow * share
        s.ax.add_patch(plt.Rectangle((edge, cy - oh / 2), ox + ow - edge + 2, oh, color=t.paper, lw=0, zorder=2))
        nx = ox + ow + 36
        s._put(nx, cy - 8, name.upper(), "sans", 800, 54, t.ink, va="bottom")
        s._put(nx, cy + 6, party, "sans", 400, 30, t.ink2, va="top")
        s._put(x1 - 28, cy - 22, f"{share * 100:.0f}", "hero", 800, 104, t.ink, ha="right", va="center")
        s._put(x1 - 28, cy + 46, "IN 100", "mono", 600, 22, t.ink2, ha="right", va="center")
        y += 192
    s.ax.plot([x0, x1], [y, y], color=t.ink, lw=pt(2))
    s.ax.add_patch(Ellipse((x0 + 28 + 58, y + 58), 116, 64, fill=False, ec=t.ink, lw=pt(4)))
    s._put(x0 + 180, y + 58, "Write-in", "sans", 400, 30, t.ink2, va="center")
    s.ax.plot([x0 + 310, x1 - 28], [y + 72, y + 72], color=t.baseline, lw=pt(2))
    y += 116
    s.ax.add_patch(plt.Rectangle((x0, top), x1 - x0, y - top, fill=False, ec=t.ink, lw=pt(4), zorder=4))
    chip(s, r, y + 36)
    s.y += 40
    benchmarks(s, r)
    source(s, r, "The Ballot")
    return s


def main_event(r: dict = NC, t=FIGHT) -> Slide:
    """The Main Event: the race as a fight card. Both surnames as tall as the page allows, the score in simulated
    elections won, the undercard of benchmarks, and the count of days left."""
    s = base(t, r)
    cx = s.w / 2
    s._put(cx, s.y + 8, f"{r['state'].upper()} · U.S. SENATE", "mono", 600, 28, t.ink2, ha="center", va="top")
    y = s.y + 70
    for name, col, i in ((surname(r["dem"]), t.dem, 0), (surname(r["rep"]), t.rep, 1)):
        px = 200
        while s.pil("hero", 800, px).getlength(name.upper()) > s.width:
            px -= 6
        s._put(cx, y, name, "hero", 800, px, col, ha="center", va="top")
        y += px * 0.86
        if i == 0:
            y += 24
            s.ax.plot([MARGIN, cx - 70], [y + 38, y + 38], color=t.baseline, lw=pt(2))
            s.ax.plot([cx + 70, s.w - MARGIN], [y + 38, y + 38], color=t.baseline, lw=pt(2))
            s.ax.add_patch(plt.Circle((cx, y + 38), 48, color=t.ai, zorder=3))
            s._put(cx, y + 40, "VS", "hero", 800, 50, t.ink, ha="center", va="center", zorder=4)
            y += 100
    y += 20
    d, rp = round(r["p"] * 100), 100 - round(r["p"] * 100)
    s._put(cx - 40, y, f"{d}", "hero", 800, 170, t.dem, ha="right", va="top")
    s._put(cx, y + 10, "–", "hero", 800, 150, t.ink2, ha="center", va="top")
    s._put(cx + 40, y, f"{rp}", "hero", 800, 170, t.rep, ha="left", va="top")
    s._put(cx, y + 190, "SIMULATED ELECTIONS WON, OUT OF 100", "mono", 600, 24, t.ink, ha="center", va="top")
    s._put(cx, y + 226, f"{verdict(r['p'])} · {r['change']}", "sans", 400, 28, t.ink2, ha="center", va="top")
    y += 282
    s.ax.plot([MARGIN, s.w - MARGIN], [y, y], color=t.baseline, lw=pt(2))
    col = s.width / 4
    cells = (("POLL AVG", r["poll"]), ("MARKET", pct_txt(r["market"])), ("COOK", r["cook"]),
             ("DAYS LEFT", str(days_left(r.get("day", DAY)))))
    vpx = 44
    while vpx > 26 and max(s.pil("hero", 800, vpx).getlength(typeset(v)) for _, v in cells) > col - 20:
        vpx -= 2
    for i, (label, value) in enumerate(cells):
        x = MARGIN + col * (i + 0.5)
        s._put(x, y + 22, label, "mono", 500, 20, t.ink2, ha="center", va="top")
        s._put(x, y + 52, value, "hero", 800, vpx, t.ink, ha="center", va="top")
        if i:
            s.ax.plot([MARGIN + col * i] * 2, [y + 18, y + 104], color=t.baseline, lw=pt(1))
    s.y = y + 120
    source(s, r, "The Main Event")
    return s


def chamber(t=CHAMBER, up: dict = UP, holdover: dict = HOLDOVER, p_r: float = 0.64, market: float | None = 0.71,
            day: date = DAY, run: str = "a3f9c1e", kicker: str = KICKER, src: str | None = None) -> Slide:
    """The Chamber: all 100 seats in a half circle. Seats not up this year are pale; the 35 races are coloured by how
    the simulations lean, toss-ups in purple. The line marks 50 seats, which is control for Republicans."""
    s = Slide(day, kicker, t, run=run)
    s.headline("Who holds the Senate?", px=80)
    s.dek("All 100 seats; the 35 on the ballot by how the simulations lean.", px=32)
    order = sorted(up, key=lambda k: -up[k])
    seats = ([(t.dem, False, None)] * holdover["D"] + [(t.ai if 0.35 <= up[k] <= 0.65 else t.dem if up[k] > 0.5 else t.rep, True, k) for k in order]
             + [(t.rep, False, None)] * holdover["R"])
    cx, cy, R = s.w / 2, s.y + 470, 420
    rows, pos = 6, []
    radii = np.linspace(R * 0.42, R, rows)
    counts = np.round(100 * radii / radii.sum()).astype(int)
    counts[-1] += 100 - counts.sum()
    for rad, n in zip(radii, counts):
        for a in np.linspace(np.pi, 0, n):
            pos.append((a, rad))
    pos.sort(key=lambda p: (-p[0], p[1]))
    dot = 40
    for (a, rad), (col, live, k) in zip(pos, seats):
        x, y = cx + rad * np.cos(a), cy - rad * np.sin(a)
        if live:
            s.ax.add_patch(plt.Circle((x, y), dot / 2, color=col, lw=0, zorder=3))
        else:
            s.ax.add_patch(plt.Circle((x, y), dot / 2, color=mix(col, t.paper, 0.25), lw=0, zorder=3))
    s.ax.plot([cx, cx], [cy - R - 34, cy - 130], color=t.ink, lw=pt(3), zorder=4, dashes=(3, 2))
    s._put(cx, cy - R - 42, "50", "mono", 600, 26, t.ink, ha="center", va="bottom")
    tos = sum(1 for p in up.values() if 0.35 <= p <= 0.65)
    s._put(cx, cy - 118, f"{p_r * 100:.0f}", "hero", 600, 120, t.ink, ha="center", va="top")
    s._put(cx, cy + 36, "in 100: Republicans hold 50+", "sans", 500, 30, t.ink2, ha="center", va="top")
    s.y = cy + 96
    items = [("D favoured", [t.dem]), ("Toss-up", [t.ai]), ("R favoured", [t.rep]),
             ("Not up this year", [mix(t.dem, t.paper, 0.25), mix(t.rep, t.paper, 0.25)])]
    x = MARGIN
    for label, cols in items:
        for j, col in enumerate(cols):
            s.ax.add_patch(plt.Circle((x + 12 + j * 20, s.y + 17), 12, color=col, lw=0))
        x += 20 * (len(cols) - 1)
        s._put(x + 34, s.y + 17, label, "sans", 400, 26, t.ink2, va="center")
        x += 34 + s.pil("sans", 400, 26).getlength(label) + 36
    s.y += 64
    strip(s, [("Market, R control", pct_txt(market)), ("Toss-ups", str(tos)),
              ("Not up", f"D {holdover['D']} · R {holdover['R']}")])
    s.source(src or "EXAMPLE: invented numbers, not a forecast. Independents who caucus with Democrats count as D. "
                    "Special edition: The Chamber.")
    return s


def seismograph(r: dict = NC, t=SEISMO, history: list | None = None, events: list = EVENTS) -> Slide:
    """The Seismograph: two weeks of one race drawn as a trace on chart paper. Each tremor is numbered and tied to the
    neutral event card that caused it."""
    s = base(t, r)
    if history is None:  # the example trace, moved so it ends on today's number
        history = [min(max(p - HISTORY[-1] + r["p"], 0.01), 0.99) for p in HISTORY]
    txt = f"What moved {r['state']}"
    s.headline(txt, px=fit(s, txt, 72, s.width, low=48))
    x0, x1 = MARGIN, s.w - MARGIN
    top, h = s.y + 6, 360
    lo_p, hi_p = max(0, min(history) - 0.08), min(1, max(history) + 0.08)
    lo_p, hi_p = min(lo_p, 0.62), max(hi_p, 0.38)  # always show at least the edge of the toss-up zone
    if hi_p - lo_p < 0.3:
        mid = (hi_p + lo_p) / 2
        lo_p, hi_p = max(0, mid - 0.15), min(1, mid + 0.15)
    Y = lambda p: top + h - (p - lo_p) / (hi_p - lo_p) * h
    cx0 = x0 + 78  # left column holds the scale labels
    X = lambda i: cx0 + 20 + (x1 - cx0 - 170) * i / (len(history) - 1)
    for gx in np.arange(cx0, x1 + 1, 18):
        s.ax.plot([gx, gx], [top, top + h], color=t.hairline, lw=pt(1.4 if (gx - cx0) % 90 == 0 else 0.7), zorder=0)
    for gy in np.arange(top, top + h + 1, 18):
        s.ax.plot([cx0, x1], [gy, gy], color=t.hairline, lw=pt(1.4 if (gy - top) % 90 == 0 else 0.7), zorder=0)
    band = Y(min(0.65, hi_p)), Y(max(0.35, lo_p))
    if band[1] > band[0]:
        s.ax.add_patch(plt.Rectangle((cx0, band[0]), x1 - cx0, band[1] - band[0], color=t.tossup, alpha=0.8, lw=0,
                                     zorder=0))
    if lo_p < 0.5 < hi_p:
        s.ax.plot([cx0, x1], [Y(0.5)] * 2, color=t.baseline, lw=pt(1.5), zorder=1)
    for p, col in ((0.65, t.ai), (0.5, t.ink2), (0.35, t.ai), (lo_p, t.ink2), (hi_p, t.ink2)):
        if lo_p <= p <= hi_p and (p in (0.35, 0.5, 0.65) or min(abs(p - q) for q in (0.35, 0.5, 0.65)) > 0.06):
            s._put(cx0 - 12, Y(p), f"{p:.0%}", "mono", 500, 20, col, ha="right", va="center")
    xs = np.array([X(i) for i in range(len(history))])
    ys = np.array([Y(p) for p in history])
    fine = np.linspace(0, len(history) - 1, 400)
    jitter = 4 * np.sin(fine * 23) * np.sin(fine * 3.1)
    s.ax.plot(np.interp(fine, range(len(history)), xs), np.interp(fine, range(len(history)), ys) + jitter,
              color=t.ink, lw=pt(3), zorder=3, solid_joinstyle="round")
    ex, ey = xs[-1], ys[-1]
    s.ax.add_patch(plt.Polygon([[ex + 4, ey], [ex + 40, ey - 14], [ex + 40, ey + 14]], color=t.ai, zorder=4))
    s._put(ex + 48, ey, f"{history[-1]:.0%}", "hero", 700, 40, t.ink, va="center", zorder=4)
    for n, (i, _, delta) in enumerate(events, 1):
        up = delta > 0
        mx, my = X(i), Y(history[i]) + (-40 if up else 40)
        if not top + 20 <= my <= top + h - 20:  # no room on its own side: mark it on the other
            my = Y(history[i]) + (40 if up else -40)
        s.ax.add_patch(plt.Circle((mx, my), 18, color=t.dem if up else t.rep, zorder=5))
        s._put(mx, my + 1, str(n), "mono", 600, 22, "#FFFFFF", ha="center", va="center", zorder=6)
    first = date.fromordinal(r.get("day", DAY).toordinal() - len(history) + 1)
    s._put(X(0), top + h + 12, first.strftime("%d %b").upper(), "mono", 400, 20, t.ink2, ha="left", va="top")
    s._put(x1, top + h + 12, "TODAY", "mono", 600, 20, t.ink2, ha="right", va="top")
    s._put((X(0) + x1) / 2, top + h + 12, "SHADED: TOSS-UP", "mono", 500, 20, t.ai, ha="center", va="top")
    s.y = top + h + 64
    s._put(s.w - MARGIN, s.y, "MARGIN MOVE", "mono", 500, 20, t.ink2, ha="right", va="top")
    s.y += 34
    for n, (i, card, delta) in enumerate(events, 1):
        up = delta > 0
        s.ax.add_patch(plt.Circle((MARGIN + 18, s.y + 20), 18, color=t.dem if up else t.rep))
        s._put(MARGIN + 18, s.y + 21, str(n), "mono", 600, 22, "#FFFFFF", ha="center", va="center")
        lines = s.wrap(card, "sans", 400, 28, s.width - 210)
        for k, line in enumerate(lines):
            s._put(MARGIN + 56, s.y + 4 + k * 36, line, "sans", 400, 28, t.ink, va="top")
        s._put(s.w - MARGIN, s.y + 4, f"{abs(delta):.1f} {'D' if up else 'R'}", "mono", 600, 26, t.ink, ha="right",
               va="top")
        s.y += max(len(lines), 1) * 36 + 18
    s.y += 8
    benchmarks(s, r)
    source(s, r, "The Seismograph")
    return s


def tile_map(t=MAP, up: dict = UP, cook: dict = COOK, day: date = DAY, run: str = "a3f9c1e", kicker: str = KICKER,
             src: str | None = None) -> Slide:
    """The Map: one square per state. The 35 races are coloured by how the simulations lean; a ring marks each race
    where Cook's rating differs from ours."""
    s = Slide(day, kicker, t, run=run)
    tos = sum(1 for p in up.values() if 0.35 <= p <= 0.65)
    s.headline(f"35 races. {tos} toss-ups.", px=88)
    s.dek("The Democrat's chance in each state's simulated elections.", px=34)
    size, gap = 72, 6
    x0 = MARGIN + (s.width - 12 * (size + gap) + gap) / 2
    top = s.y + 6
    for k, (row, c) in TILE.items():
        x, y = x0 + c * (size + gap), top + row * (size + gap)
        if k in up:
            p = up[k]
            s.ax.add_patch(FancyBboxPatch((x, y), size, size, boxstyle="round,pad=0,rounding_size=6",
                                          color=rating_color(t, p), lw=0, zorder=2))
            if k in cook and cook[k] != verdict(p):
                s.ax.add_patch(FancyBboxPatch((x - 5, y - 5), size + 10, size + 10, fill=False, ec=t.ink, lw=pt(3.5),
                                              boxstyle="round,pad=0,rounding_size=9", zorder=3))
            fg = "#FFFFFF" if lum(rating_color(t, p)) < 0.6 else "#141414"
            s._put(x + size / 2, y + 28, k, "sans", 700, 26, fg, ha="center", va="center", zorder=4)
            s._put(x + size / 2, y + 54, f"{p * 100:.0f}", "mono", 500, 20, fg, ha="center", va="center", zorder=4)
        else:
            s.ax.add_patch(FancyBboxPatch((x, y), size, size, boxstyle="round,pad=0,rounding_size=6", fill=False,
                                          ec=t.baseline, lw=pt(1.5), zorder=2))
            s._put(x + size / 2, y + size / 2, k, "sans", 400, 20, t.muted, ha="center", va="center", zorder=4)
    s.y = top + 8 * (size + gap) + 20
    items = [("Likely D", t.dem), ("Leans D", rating_color(t, 0.7)), ("Toss-up", t.ai),
             ("Leans R", rating_color(t, 0.3)), ("Likely R", t.rep)]
    x = MARGIN
    for label, col in items:
        s.ax.add_patch(plt.Rectangle((x, s.y + 4), 26, 26, color=col, lw=0))
        s._put(x + 36, s.y + 17, label, "sans", 400, 24, t.ink2, va="center")
        x += 36 + s.pil("sans", 400, 24).getlength(label) + 34
    s.y += 56
    diff = sorted(k for k in up if k in cook and cook[k] != verdict(up[k]))
    s.ax.add_patch(FancyBboxPatch((MARGIN + 2, s.y + 2), 24, 24, fill=False, ec=t.ink, lw=pt(3),
                                  boxstyle="round,pad=0,rounding_size=5"))
    s.text(f"Ringed: Cook rates it differently ({', '.join(diff) or 'none'}).", px=24, color=t.ink2,
           x=MARGIN + 40, width=s.width - 40, after=0.4)
    s.source(src or "EXAMPLE: invented numbers, not a forecast. Special edition: The Map.")
    return s


LAYOUTS = {"1-ballot": ballot, "2-main-event": main_event, "3-chamber": chamber, "4-seismograph": seismograph,
           "5-map": tile_map}


if __name__ == "__main__":
    from .directions import OUT as DIR_OUT
    from .labnotes import contact_sheet
    out = DIR_OUT.parent / "specials"
    paths = [fn().save(out / f"{name}.jpg") for name, fn in LAYOUTS.items()]
    print(contact_sheet(paths, out / "board.jpg", scale=0.4))
