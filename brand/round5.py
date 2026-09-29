"""Round 5: G2's two hills made into real hills (H), D3.4's two electorates refined, the polar and party pies kept.

The hills are two opinion distributions seen side on: a blue electorate and a red one, purple where they overlap.
"""
from __future__ import annotations

import math

import numpy as np

from . import marks as m
from . import round4 as r4
from .marks import clip, dot, path, ring
from .round4 import hexfill, poly, stroke

X = np.linspace(2, 98, 97)


def hill(cx, sd, h, x=X):
    return h * np.exp(-(x - cx) ** 2 / (2 * sd * sd))


def area(f, base, x=X) -> str:
    return poly([(x[0], base)] + list(zip(x, base - f)) + [(x[-1], base)], True)


def ridge(f, base, x=X) -> str:
    return poly(list(zip(x, base - f)))


def two(f1, f2, base, x=X):
    return [path(area(f1, base, x), "blue"), path(area(f2, base, x), "red"),
            path(area(np.minimum(f1, f2), base, x), "mix")]


def hills_two():
    return two(hill(37, 13, 50), hill(63, 13, 50), 77)


def hills_three():
    base = 78
    front = hill(50, 10.5, 30)
    return [path(area(hill(29, 11, 52), base), "blue"), path(area(hill(71, 11, 52), base), "red"),
            stroke(ridge(front, base), 4, "bg"), path(area(front, base), "mix")]


def hills_voters():
    """A dot plot: each dot a voter, stacked into two hills; purple where the two electorates mix."""
    pitch, r, base = 6.6, 2.75, 83
    s = []
    for i in range(14):
        x = 7.1 + pitch * i
        a, b = hill(35, 12, 58, x), hill(65, 12, 58, x)
        n = int(round((a + b) / pitch))
        p = a / (a + b)
        role = "blue" if p > .7 else "red" if p < .3 else "mix"
        s += [dot(x, base - pitch * (k + .5), r, role) for k in range(n)]
    return s


def hills_ridges():
    """Earlier states of the electorate as outlined ridges behind today's coloured hills."""
    s = []
    for k, (a, b, sd) in enumerate(((44, 56, 14), (41, 59, 13.5), (38, 62, 13))):
        base = 60 + 8 * k
        f = np.maximum(hill(a, sd, 34), hill(b, sd, 34))
        s += [path(area(f, base), "bg"), stroke(ridge(f, base), 2.2, "fg")]
    f1, f2 = hill(35, 12.5, 40), hill(65, 12.5, 40)
    base = 88
    s += [path(area(np.maximum(f1, f2), base), "bg")] + two(f1, f2, base)
    return s


def hills_landscape():
    x = np.linspace(-10, 110, 121)
    f1, f2 = hill(30, 17, 62, x), hill(71, 17, 58, x)
    return [clip(50, 50, 46, two(f1, f2, 102, x)), ring(50, 50, 46, 3)]


# ---- two electorates, refined ---------------------------------------------------------------------------------

L, R_, RAD = 33.0, 67.0, 26.0


def _in(x, y, cx):
    return (x - cx) ** 2 + (y - 50) ** 2 <= RAD ** 2


def _region(x, y):
    a, b = _in(x, y, L), _in(x, y, R_)
    if a and b:
        return "mix"
    if a or b:
        return "blue" if a else "red"
    return "blue" if math.hypot(x - L, y - 50) - RAD < math.hypot(x - R_, y - 50) - RAD else "red"


def _union(x, y):
    return _in(x, y, L) or _in(x, y, R_)


def halftone_hex(inside, pitch, rmax, role, n=6):
    out, dy = [], pitch * math.sqrt(3) / 2
    for j in range(-1, int(100 / dy) + 2):
        for i in range(-1, int(100 / pitch) + 2):
            x, y = i * pitch + (pitch / 2 if j % 2 else 0), j * dy
            hits = sum(inside(x + (a + .5 - n / 2) * pitch / n, y + (b + .5 - n / 2) * dy / n)
                       for a in range(n) for b in range(n))
            cov = hits / n / n
            if cov > .15:
                out.append(dot(x, y, rmax * math.sqrt(cov), role(x, y)))
    return out


def electorates_halftone():
    return halftone_hex(_union, 6.4, 2.8, _region)


def electorates_lens():
    out = []
    for sh in halftone_hex(_union, 6.4, 2.8, _region):
        _, x, y, rr, role = sh
        out.append(dot(x, y, rr * (1.12 if role == "mix" else .78), role))
    return out


def electorates_ink():
    return halftone_hex(_union, 6.4, 2.8, lambda x, y: "accent" if _region(x, y) == "mix" else "fg")


NEW = {
    "H1": ("Two hills", "A blue hill and a red hill, purple where they overlap. Side on, they're the two electorates' "
           "opinion curves: the shape every polarisation chart draws.", hills_two),
    "H2": ("Three hills", "Blue and red ranges behind, a purple hill in front: the voters in the middle, standing "
           "out.", hills_three),
    "H3": ("Voter hills", "The hills built from voters, one dot each, stacked like a dot plot. Where the two "
           "electorates mix, the voters turn purple.", hills_voters),
    "H4": ("Ridges", "Today's coloured hills in front of the earlier ridges: the electorate's shape over time, "
           "the thing the simulation moves.", hills_ridges),
    "H5": ("Landscape", "The hills seen through a round window, rising past its edge, like a landscape.",
           hills_landscape),
    "D3.5": ("Two electorates, round edges", "D3.4 with the circles further apart and the edge voters sized to "
             "the curve, so it reads as two round electorates instead of a honeycomb pill.", electorates_halftone),
    "D3.6": ("Two electorates, middle first", "The purple voters grow and the rest shrink: the overlap reads first.",
             electorates_lens),
    "D3.7": ("Two electorates, ink", "Ink voters, purple overlap, no party colours.", electorates_ink),
}


def roster():
    old = {**{k: v for k, v in m.MARKS.items()}, **{k: v for k, v in r4.MARKS.items() if v[2]}}
    out = {k: old[k] for k in ("G2",)}
    out.update({k: v for k, v in NEW.items() if k.startswith("H")})
    out.update({k: old[k] for k in ("D3", "D3.4")})
    out.update({k: v for k, v in NEW.items() if k.startswith("D")})
    out.update({k: old[k] for k in ("C3.1", "C3.2")})
    return out


DIRECTIONS = {
    "H": ("The hills", "From G2, without the contour lines around it: real hills, side on. Two hills are the two "
          "electorates' opinion curves; purple is where they overlap. G2 is first for reference.",
          ["G2", "H1", "H2", "H3", "H4", "H5"]),
    "D": ("Two electorates", "D3 and D3.4 as they were, then D3.4 refined three ways.",
          ["D3", "D3.4", "D3.5", "D3.6", "D3.7"]),
    "C": ("Voter pie", "The two you liked, unchanged, so they sit beside the others in the line-up.",
          ["C3.1", "C3.2"]),
}
