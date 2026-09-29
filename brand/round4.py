"""Round 4: C3 (voter pie) and D3 (dotted overlap) developed, plus three directions in new visual languages:
logic notation (E), forecast lines (F) and contour maps (G). Same 100-unit canvas and colour roles as brand.marks.
"""
from __future__ import annotations

import math
from functools import lru_cache
from pathlib import Path

import contourpy
import numpy as np
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

from .marks import _pt, dot, path, ring

FONTS = Path(__file__).resolve().parents[1] / "simlab" / "publish" / "fonts"


def stroke(d, w, role="fg"):
    return ("s", d, w, role)


def poly(pts, closed=False) -> str:
    d = "M" + " L".join(f"{x:.2f},{y:.2f}" for x, y in pts)
    return d + (" Z" if closed else "")


def hexfill(inside, pitch, r, role):
    out, dy = [], pitch * math.sqrt(3) / 2
    for j in range(-2, int(100 / dy) + 3):
        for i in range(-2, int(100 / pitch) + 3):
            x, y = i * pitch + (pitch / 2 if j % 2 else 0), j * dy
            if inside(x, y):
                out.append(dot(x, y, r, role(x, y) if callable(role) else role))
    return out


# ---- C3 developed: the voter pie ------------------------------------------------------------------------------

def polar_pie(role, cx=50, cy=50, pitch=9.2, rings=4, r=3.9, cut=(20, 80), pull=9.0, burst=0.0, inner=1):
    """Dots on concentric rings; the slice between cut angles (clockwise from 12) is pulled out along its bisector."""
    s = []
    mid = (cut[0] + cut[1]) / 2
    ox, oy = _pt(0, 0, pull, mid)
    for k in range(inner, rings + 1):
        rad = pitch * k
        m = max(1, round(2 * math.pi * rad / pitch))
        for j in range(m):
            a = (j + .5) * 360 / m
            x, y = _pt(cx, cy, rad, a)
            if cut[0] <= a <= cut[1]:
                f = 1 + burst * (k / rings) ** 2
                bx, by = _pt(0, 0, pull + burst * 9 * (k / rings) ** 2, mid)
                s.append(dot(x + bx + (x - cx) * (f - 1) * .25, y + by + (y - cy) * (f - 1) * .25, r, "accent"))
            else:
                s.append(dot(x, y, r, role(a)))
    return s


def pie_ink():
    return polar_pie(lambda a: "fg")


def pie_party():
    return polar_pie(lambda a: "blue" if a > 220 else "red")


def pie_coming_apart():
    return polar_pie(lambda a: "fg", burst=1.0, pull=5)


def pie_donut():
    return polar_pie(lambda a: "fg", inner=3, rings=5, pitch=7.6, r=3, pull=6)


# ---- D3 developed: the dotted overlap -------------------------------------------------------------------------

L, R_, RAD = 37.0, 63.0, 27.0


def _in(x, y, cx, rad=RAD):
    return (x - cx) ** 2 + (y - 50) ** 2 <= rad ** 2


def ring_dots(cx, n, role, size=lambda x, y: 3.4, other=None):
    s = []
    for k in range(n):
        t = 2 * math.pi * (k + .5) / n
        x, y = cx + RAD * math.cos(t), 50 + RAD * math.sin(t)
        if other is not None and _in(x, y, other, RAD - 1):
            continue
        s.append(dot(x, y, size(x, y), role))
    return s


def lens_dots(role="mix", pitch=6.2, r=2.5):
    return hexfill(lambda x, y: _in(x, y, L, RAD - 4) and _in(x, y, R_, RAD - 4), pitch, r, role)


def overlap_refined():
    return ring_dots(L, 20, "blue", other=R_) + ring_dots(R_, 20, "red", other=L) + lens_dots()


def overlap_ink():
    return ring_dots(L, 20, "fg", other=R_) + ring_dots(R_, 20, "fg", other=L) + lens_dots("accent")


def overlap_pull():
    def size(x, y):
        return 2.2 + 3.0 * max(0.0, 1 - math.hypot(x - 50, y - 50) / 34) ** 1.2
    return (ring_dots(L, 24, "blue", size, other=R_) + ring_dots(R_, 24, "red", size, other=L)
            + lens_dots(pitch=5.6, r=2.4))


def overlap_fields():
    def role(x, y):
        a, b = _in(x, y, L), _in(x, y, R_)
        return "mix" if a and b else "blue" if a else "red"
    return hexfill(lambda x, y: _in(x, y, L, RAD + .5) or _in(x, y, R_, RAD + .5), 6.4, 2.5, role)


# ---- E: logic notation, "not P" -------------------------------------------------------------------------------

@lru_cache
def _font(name: str, wght: int | None = None):
    f = TTFont(FONTS / name)
    if "fvar" in f:
        f = instancer.instantiateVariableFont(f, {"wght": wght, "opsz": 72})
    return f


def type_parts(text, name, wght, box, roles, track=0.0):
    """Outline text, scaled to fit box=(x0, y0, x1, y1) by its ink bounds; one path per glyph, coloured by roles."""
    f = _font(name, wght)
    gs, cmap = f.getGlyphSet(), f.getBestCmap()
    upm = f["head"].unitsPerEm
    xs, x = [], 0.0
    for ch in text:
        g = cmap[ord(ch)]
        xs.append((g, x))
        x += gs[g].width + track * upm
    bp = BoundsPen(gs)
    for g, gx in xs:
        gs[g].draw(TransformPen(bp, (1, 0, 0, 1, gx, 0)))
    bx0, by0, bx1, by1 = bp.bounds
    x0, y0, x1, y1 = box
    k = min((x1 - x0) / (bx1 - bx0), (y1 - y0) / (by1 - by0))
    ox = x0 + ((x1 - x0) - (bx1 - bx0) * k) / 2 - bx0 * k
    oy = y0 + ((y1 - y0) - (by1 - by0) * k) / 2 + by1 * k
    out = []
    for (g, gx), role in zip(xs, roles):
        sp = SVGPathPen(gs)
        gs[g].draw(TransformPen(sp, (k, 0, 0, -k, ox + gx * k, oy)))
        out.append(path(sp.getCommands(), role))
    return out


NOT = "M16,33 H84 V69 H69 V48 H16 Z"


def not_p():
    s = type_parts("P", "Newsreader[opsz,wght].ttf", 600, (55, 18, 90, 82), ["fg"])
    return [path("M10,37 H47 V64 H35.5 V48.5 H10 Z", "accent")] + s


def not_sign():
    return [path(NOT, "accent")]


def p_bar():
    return [path("M28,10 H72 V20 H28 Z", "accent")] + type_parts("P", "Newsreader[opsz,wght].ttf", 600,
                                                               (26, 28, 74, 92), ["fg"])


# ---- F: forecast lines ----------------------------------------------------------------------------------------

def _futures(n=13, seed=7, spread=36.0):
    rng = np.random.default_rng(seed)
    t = np.linspace(0, 1, 70)
    out = []
    for i in range(n):
        end = (i - (n - 1) / 2) / ((n - 1) / 2)
        ph = rng.uniform(0, 2 * np.pi, 2)
        wig = 1.6 * t * (np.sin(2 * np.pi * .9 * t + ph[0]) + .5 * np.sin(2 * np.pi * 1.9 * t + ph[1]))
        y = 50 + spread * end * t ** 1.5 + wig
        out.append((end, np.column_stack([12 + 76 * t, y])))
    return out


def spaghetti():
    s = []
    lines = _futures()
    for end, pts in lines:
        if abs(end) > 1e-9:
            s.append(stroke(poly(pts), 2.0))
    s.append(stroke(poly(lines[len(lines) // 2][1]), 4.6, "accent"))
    s.append(dot(12, 50, 5, "fg"))
    return s


def spaghetti_party():
    s = []
    for end, pts in _futures(13, 3):
        role = "blue" if end < -.2 else "red" if end > .2 else "mix"
        s.append(stroke(poly(pts), 3.0 if role == "mix" else 2.0, role))
    return s + [dot(12, 50, 5, "fg")]


def cone():
    t = np.linspace(0, 1, 60)
    x = 12 + 76 * t
    c = 50 - 7 * np.sin(np.pi * t) * t
    s = []
    for a, role in ((38, "band1"), (19, "band2")):
        w = a * t ** 1.3
        s.append(path(poly(list(zip(x, c - w)) + list(zip(x[::-1], (c + w)[::-1])), True), role))
    s.append(stroke(poly(np.column_stack([x, c])), 4.4, "accent"))
    return s + [dot(12, 50, 5, "fg")]


# ---- G: contour maps ------------------------------------------------------------------------------------------

def _grid(n=241):
    xs = np.linspace(0, 100, n)
    return np.meshgrid(xs, xs)


def _g(X, Y, cx, cy, s):
    return np.exp(-((X - cx) ** 2 + (Y - cy) ** 2) / (2 * s * s))


def _lines(X, Y, Z, level, mask=None):
    gen = contourpy.contour_generator(X, Y, np.ma.array(Z, mask=mask) if mask is not None else Z)
    return gen.lines(level)


def _d(seg) -> str:
    closed = np.allclose(seg[0], seg[-1])
    return poly(seg[:-1] if closed else seg, closed)


def contours():
    X, Y = _grid()
    Z = _g(X, Y, 48, 52, 19) + .45 * _g(X, Y, 60, 40, 11) + .3 * _g(X, Y, 36, 64, 10) \
        + .05 * np.sin(X / 6.5) * np.cos(Y / 7.5)
    top = Z.max()
    levels = [top * f for f in (.14, .3, .46, .62, .78)]
    s = [stroke(_d(seg), 2.5) for lv in levels for seg in _lines(X, Y, Z, lv)]
    s += [path(_d(seg), "accent") for seg in _lines(X, Y, Z, top * .9)]
    return s


def contours_party():
    X, Y = _grid()
    Z = _g(X, Y, 33, 53, 13) + _g(X, Y, 67, 47, 13)
    s = []
    for lv in (.18, .36, .54, .72, .86, .97):
        for seg in _lines(X, Y, Z, lv):
            mx = seg[:, 0].mean()
            role = "blue" if mx < 44 else "red" if mx > 56 else "fg"
            s.append(stroke(_d(seg), 2.5, role))
    s.append(path("M50,43.5 C54,47 54,53 50,56.5 C46,53 46,47 50,43.5 Z", "mix"))
    return s


def contours_lens():
    X, Y = _grid()
    Z = _g(X, Y, 62, 40, 26) + .35 * _g(X, Y, 40, 66, 12) + .04 * np.sin(X / 5.5 + Y / 9)
    mask = (X - 50) ** 2 + (Y - 50) ** 2 > 44 ** 2
    top = Z.max()
    s = [ring(50, 50, 45.5, 2.5)]
    s += [stroke(_d(seg), 2.3) for f in (.2, .35, .5, .65, .8) for seg in _lines(X, Y, Z, top * f, mask)]
    s += [path(_d(seg), "accent") for seg in _lines(X, Y, Z, top * .92, mask)]
    return s


MARKS = {
    "C3": ("Voter pie, round 3", "Where it started: square-grid dots, one slice pulled out.", None),
    "C3.1": ("Polar voter pie", "The voters sit on the pie's own rings, so the circle is exact; the purple slice is pulled out.", pie_ink),
    "C3.2": ("Party voter pie", "Blue and red voters make the pie; the slice pulled out is purple, the voters who can still move.", pie_party),
    "C3.3": ("Coming apart", "The pulled slice loosens as it leaves: a poll's block breaking into individual voters.", pie_coming_apart),
    "C3.4": ("Voter donut", "The same idea as a donut chart: lighter, and it survives 16 px better.", pie_donut),
    "D3": ("Dotted overlap, round 3", "Where it started.", None),
    "D3.1": ("Overlap, refined", "Twenty voters to a ring, evenly spaced; the overlap packed with purple voters.", overlap_refined),
    "D3.2": ("Overlap, ink", "The same without party colours: ink rings, a purple middle.", overlap_ink),
    "D3.3": ("Pulled to the middle", "Voters grow as they near the overlap: the middle is where the election is decided.", overlap_pull),
    "D3.4": ("Two electorates", "Each circle filled with its voters; purple where they share ground.", overlap_fields),
    "E1": ("Not P", "The name in logic notation: the negation sign, then P. \"Not a poll\" as a lab would write it.", not_p),
    "E2": ("The sign", "The negation sign alone, heavy and square. The wordmark carries the rest.", not_sign),
    "E3": ("P-bar", "The other way logicians write not-P: a bar over the letter, the bar in purple.", p_bar),
    "F1": ("Spaghetti", "A hurricane-style spaghetti plot: one starting point, many simulated futures, the likeliest in purple.", spaghetti),
    "F2": ("Spaghetti, party", "The futures that end blue, red, or in the purple toss-up band.", spaghetti_party),
    "F3": ("The cone", "The forecast cone of uncertainty, as on a hurricane map: two bands and the central path.", cone),
    "G1": ("Opinion map", "The electorate as a landscape: contour lines of opinion, the summit in purple.", contours),
    "G2": ("Two hills", "A blue hill and a red hill; the swing voters live in the saddle between them.", contours_party),
    "G3": ("Through the lens", "The landscape seen through a round lens, like a map under a loupe.", contours_lens),
}
