"""NotAPoll.org logo candidates, drawn on one 100-unit canvas.

A mark is a list of shapes; each shape names a colour role, so one geometry renders on paper, on indigo, or in the
party twist. python -m brand.explore builds the comparison page from these.
"""
from __future__ import annotations

import math

PAPER, INK, INDIGO, LILAC, PURPLE = "#F5F3EE", "#111110", "#2A2152", "#B98DD6", "#4A3AA7"
BLUE, RED = "#2A78D6", "#E34948"

LIGHT = {"bg": PAPER, "fg": INK, "accent": PURPLE, "faint": "#D9D5CC", "blue": BLUE, "red": RED, "mix": "#7A4FC0",
         "blue_mix": "#4F60D0", "red_mix": "#B0439A", "band1": "#E6E0F2", "band2": "#C9BCE6"}
DARK = {"bg": INDIGO, "fg": PAPER, "accent": LILAC, "faint": "#4A4175", "blue": "#5B9BEA", "red": "#F0605F",
        "mix": "#B98DD6", "blue_mix": "#8A94E8", "red_mix": "#DE78B4", "band1": "#3B3270", "band2": "#57489A"}


def dot(x, y, r, role="fg"):
    return ("c", x, y, r, role)


def path(d, role="fg"):
    return ("p", d, role)


def ring(x, y, r, w, role="fg"):
    return ("r", x, y, r, w, role)


def halftone(inside, pitch, rmax, box=(0, 100), n=8):
    """Dots on a grid, each sized by how much of its cell the shape covers."""
    out = []
    lo, hi = box
    k = int((hi - lo) / pitch)
    for i in range(k):
        for j in range(k):
            x0, y0 = lo + i * pitch, lo + j * pitch
            hits = sum(inside(x0 + (a + .5) * pitch / n, y0 + (b + .5) * pitch / n) for a in range(n) for b in range(n))
            cov = hits / n / n
            if cov > .12:
                out.append([x0 + pitch / 2, y0 + pitch / 2, rmax * math.sqrt(cov)])
    return out


# ---- Direction A: the synthetic voter -------------------------------------------------------------------------

def _bust(x, y, head=(50, 30, 17), top=57, cx=50, rx=40, base=100):
    hx, hy, hr = head
    if (x - hx) ** 2 + (y - hy) ** 2 <= hr ** 2:
        return True
    if y < top or y > base:
        return False
    ry = base - top
    return ((x - cx) / rx) ** 2 + ((y - base) / ry) ** 2 <= 1


def voter_halftone():
    dots = halftone(lambda x, y: _bust(x, y, head=(50, 29.2, 17.5), top=58), 100 / 12, 4.3, box=(0, 100))
    shapes = [dot(x, y, r) for x, y, r in dots]
    heart = min(range(len(dots)), key=lambda i: (dots[i][0] - 50) ** 2 + (dots[i][1] - 75) ** 2)
    shapes[heart] = dot(*dots[heart][:2], dots[heart][2], "accent")
    return shapes


def voter_head(lean=0.0, lift=0.0, head_role="accent"):
    """A purple head on a body of 16 voters. lean and lift pose the character."""
    s = [dot(50 + lean, 26 - lift, 16, head_role)]
    for j, y in enumerate((58.5, 70, 81.5, 93)):
        for k in range(-4, 5):
            x = 50 + 12.5 * (k + (.5 if j % 2 else 0))
            if ((x - 50) / 47) ** 2 + ((y - 99) / 43) ** 2 <= 1:
                s.append(dot(x, y, 5.4))
    return s


def voter_nine():
    """The nine voters of today's avatar, regrouped into a person: one head, three, then five."""
    s = [dot(50, 24, 15, "accent")]
    for u in (-1, 0, 1):
        s.append(dot(50 + 16 * u, 58 + 3 * u * u, 7))
    for u in (-2, -1, 0, 1, 2):
        s.append(dot(50 + 16 * u, 80 + 2.2 * u * u, 7))
    return s


# ---- Direction B: the swing N ---------------------------------------------------------------------------------

def _n(left="fg", right="fg", diag="accent", faint=False):
    s = []
    for j in range(5):
        s.append(dot(10, 10 + 20 * j, 7.5, left))
        s.append(dot(90, 10 + 20 * j, 7.5, right))
    for k in (1, 2, 3):
        s.append(dot(10 + 20 * k, 10 + 20 * k, 7.5, diag))
    if faint:
        for i in (1, 2, 3):
            for j in range(5):
                if i != j:
                    s.append(dot(10 + 20 * i, 10 + 20 * j, 7.5, "faint"))
    return s


def n_mono():
    return _n()


def n_party():
    """Voters change colour as they cross: blue, then purple, then red."""
    s = _n("blue", "red", "mix")
    s[-3] = dot(30, 30, 7.5, "blue_mix")
    s[-1] = dot(70, 70, 7.5, "red_mix")
    return s


def n_wave():
    """The swing is the biggest thing on the grid: the crossing voters swell."""
    s = []
    for j in range(5):
        s += [dot(10, 10 + 20 * j, 5.5), dot(90, 10 + 20 * j, 5.5)]
    for k in (1, 2, 3):
        s.append(dot(10 + 20 * k, 10 + 20 * k, 9.5 if k == 2 else 8, "accent"))
    return s


def n_flow():
    """The diagonal leaves the grid: seven voters in a continuous crossing, faint grid behind."""
    s = [dot(10 + 20 * i, 10 + 20 * j, 3, "faint") for i in (1, 2, 3) for j in range(5)]
    for j in range(5):
        s += [dot(10, 10 + 20 * j, 7.5), dot(90, 10 + 20 * j, 7.5)]
    for k in range(1, 6):
        t = k / 6
        s.append(dot(10 + 80 * t, 10 + 80 * t, 6, "accent"))
    return s


def n_crossing():
    """One voter mid-crossing with a fading trail: the swing voter as a single moving dot."""
    s = []
    for j in range(5):
        s += [dot(10, 10 + 20 * j, 7.5), dot(90, 10 + 20 * j, 7.5)]
    for k, r in ((1, 2.2), (2, 3.4), (3, 4.8), (4, 6.2)):
        t = k / 7
        s.append(dot(10 + 80 * t, 10 + 80 * t, r, "accent"))
    s.append(dot(10 + 80 * 5.3 / 7, 10 + 80 * 5.3 / 7, 8.5, "accent"))
    return s


# ---- Direction C: the broken pie ------------------------------------------------------------------------------

def _pt(cx, cy, r, deg):
    t = math.radians(deg - 90)
    return cx + r * math.cos(t), cy + r * math.sin(t)


def _sector(cx, cy, r, a0, a1):
    x0, y0 = _pt(cx, cy, r, a0)
    x1, y1 = _pt(cx, cy, r, a1)
    big = 1 if (a1 - a0) % 360 > 180 else 0
    return f"M{cx},{cy} L{x0:.2f},{y0:.2f} A{r},{r} 0 {big} 1 {x1:.2f},{y1:.2f} Z"


def _wedge_dots(cx, cy, r, a0, a1, pitch, rmax, burst, role):
    def inside(x, y):
        d = math.hypot(x - cx, y - cy)
        a = (math.degrees(math.atan2(y - cy, x - cx)) + 90) % 360
        return 3 < d <= r and a0 <= a <= a1
    s = []
    for x, y, rr in halftone(inside, pitch, rmax, box=(0, 100)):
        d = math.hypot(x - cx, y - cy)
        k = 1 + burst * (d / r) ** 2
        s.append(dot(cx + (x - cx) * k, cy + (y - cy) * k, rr, role))
    return s


def pie_burst():
    cx = cy = 52
    return [path(_sector(cx, cy, 38, 60, 360))] + _wedge_dots(cx, cy, 38, 2, 58, 8.5, 3.9, .35, "accent")


def pie_ring():
    cx = cy = 52
    return [("arc", cx, cy, 30, 16, 60, 360, "fg")] + _wedge_dots(cx, cy, 38, 2, 58, 8.5, 3.9, .35, "accent")


def pie_party():
    cx = cy = 52
    return [path(_sector(cx, cy, 38, 60, 214), "red"), path(_sector(cx, cy, 38, 214, 360), "blue")] + \
        _wedge_dots(cx, cy, 38, 2, 58, 8.5, 3.9, .35, "mix")


def pie_dotted():
    """The whole pie is voters; one slice pulled out."""
    cx = cy = 52

    def body(x, y):
        a = (math.degrees(math.atan2(y - cy, x - cx)) + 90) % 360
        return math.hypot(x - cx, y - cy) <= 38 and not (0 <= a <= 60)
    s = [dot(x, y, r) for x, y, r in halftone(body, 8.5, 3.9)]
    ox, oy = _pt(0, 0, 7, 30)
    for x, y, r in halftone(lambda x, y: math.hypot(x - cx, y - cy) <= 38 and
                            0 <= (math.degrees(math.atan2(y - cy, x - cx)) + 90) % 360 <= 60, 8.5, 3.9):
        s.append(dot(x + ox, y + oy, r, "accent"))
    return s


# ---- Direction D: the overlap ---------------------------------------------------------------------------------

LENS = "M50,26.93 A26,26 0 0 1 50,73.07 A26,26 0 0 1 50,26.93 Z"


def overlap_party():
    return [ring(38, 50, 26, 5.5, "blue"), ring(62, 50, 26, 5.5, "red"), path(LENS, "mix")]


def overlap_mono():
    return [ring(38, 50, 26, 5.5), ring(62, 50, 26, 5.5), path(LENS, "accent")]


def overlap_dots():
    s = []
    for cx, role in ((38, "blue"), (62, "red")):
        for k in range(18):
            t = 2 * math.pi * k / 18
            x, y = cx + 26 * math.cos(t), 50 + 26 * math.sin(t)
            if abs(x - 50) < 1e-6 or (math.hypot(x - 38, y - 50) < 25 and math.hypot(x - 62, y - 50) < 25):
                continue
            s.append(dot(x, y, 3.6, role))

    def lens(x, y):
        return math.hypot(x - 38, y - 50) <= 26 and math.hypot(x - 62, y - 50) <= 26
    s += [dot(x, y, r, "mix") for x, y, r in halftone(lens, 6.5, 2.9)]
    return s


def overlap_voter():
    """Two party rings; in the overlap, a synthetic voter."""
    return [ring(38, 50, 26, 5.5, "blue"), ring(62, 50, 26, 5.5, "red"), dot(50, 42, 6.5, "mix"),
            path("M40.5,64 A9.5,9.5 0 0 1 59.5,64 Z", "mix")]


MARKS = {
    "A1": ("Halftone voter", "A person drawn as a halftone of voter dots; one purple voter at the heart.", voter_halftone),
    "A2": ("Nota", "A purple head on a body of voters. The head can lean, rise or sink when the news moves them.",
           voter_head),
    "A3": ("Nine", "Today's nine voters regrouped into a person: one head, three, then five.", voter_nine),
    "B1": ("Swing N", "The N is 13 voters; the diagonal is the three crossing from one column to the other.", n_mono),
    "B2": ("Swing N, party", "A blue column and a red column; the voters crossing change colour on the way.", n_party),
    "B3": ("Crossing N", "One voter mid-crossing, with its trail behind it.", n_crossing),
    "B4": ("Wave N", "The crossing voters swell: the swing is the biggest thing on the grid.", n_wave),
    "C1": ("Broken pie", "A poll's pie chart whose missing slice bursts into individual voters.", pie_burst),
    "C2": ("Broken ring", "The same on a donut chart, lighter at small sizes.", pie_ring),
    "C3": ("Voter pie", "The whole pie is voters, one slice pulled out.", pie_dotted),
    "D1": ("Purple overlap", "A blue ring and a red ring; where they overlap is purple, the brand colour.", overlap_party),
    "D2": ("Overlap, ink", "The same without party colours.", overlap_mono),
    "D3": ("Dotted overlap", "The rings and the overlap are made of voters.", overlap_dots),
}


def _arc(cx, cy, r, a0, a1):
    x0, y0 = _pt(cx, cy, r, a0)
    x1, y1 = _pt(cx, cy, r, a1)
    big = 1 if (a1 - a0) % 360 > 180 else 0
    return f"M{x0:.2f},{y0:.2f} A{r},{r} 0 {big} 1 {x1:.2f},{y1:.2f}"


def body(shapes, pal) -> str:
    out = []
    for s in shapes:
        kind, role = s[0], s[-1]
        c = pal[role]
        if kind == "c":
            out.append(f'<circle cx="{s[1]:.2f}" cy="{s[2]:.2f}" r="{s[3]:.2f}" fill="{c}"/>')
        elif kind == "p":
            out.append(f'<path d="{s[1]}" fill="{c}"/>')
        elif kind == "r":
            out.append(f'<circle cx="{s[1]}" cy="{s[2]}" r="{s[3]}" fill="none" stroke="{c}" stroke-width="{s[4]}"/>')
        elif kind == "s":
            out.append(f'<path d="{s[1]}" fill="none" stroke="{c}" stroke-width="{s[2]}" stroke-linecap="round" '
                       f'stroke-linejoin="round"/>')
        elif kind == "arc":
            out.append(f'<path d="{_arc(s[1], s[2], s[3], s[5], s[6])}" fill="none" stroke="{c}" '
                       f'stroke-width="{s[4]}"/>')
    return "".join(out)


def svg(shapes, pal, pad=0.0, bg=False, circle=False, size=None) -> str:
    """pad: margin around the 100-unit mark as a share of the canvas."""
    lo, span = -100 * pad, 100 * (1 + 2 * pad)
    wh = f' width="{size}" height="{size}"' if size else ""
    back = ""
    if bg:
        back = (f'<circle cx="50" cy="50" r="{span / 2}" fill="{pal["bg"]}"/>' if circle
                else f'<rect x="{lo}" y="{lo}" width="{span}" height="{span}" fill="{pal["bg"]}"/>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{lo} {lo} {span} {span}"{wh}>'
            f'{back}{body(shapes, pal)}</svg>')
