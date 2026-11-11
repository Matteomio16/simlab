"""The closing series (Matteo, 8-11 Nov): eight posts from docs/results-2026.md, one a day at 16:00 Paris, each with a Reel.
The model is called "NotAPoll v1" wherever we show results or how we compare (Matteo, 11 Nov): a first version, with a
better one to come. Every number is from docs/results-2026.md, the final 3 Nov run and docs/hypotheses.md, and every
result is provisional.

    python -m simlab.publish.closing [--only NAME] [--start 2026-11-11] [--reel]

Framing (Matteo, 6 Nov): never "the polls beat us", never dunk on polls, no claim of race-level skill.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, replace
from datetime import date, timedelta
from pathlib import Path
from typing import Callable

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch, Polygon

from . import reportcard as rcard
from .final import ROOT, save
from .frame import DISCLAIMER, LABEL, MARGIN, Slide, pt
from .launch import LIMIT
from .pollread import end
from .specials import TILE
from .themes import BALLOT, CHAMBER, LAB, SEISMO

AS_OF = "11 Nov"
SRC = f"Provisional results (AP, networks, states; {AS_OF}). Final scorecard after certification."
strip = dict(strip_bg=LAB.strip_bg, strip_fg=LAB.strip_fg)
T_SEIS, T_CHAM, T_BALL = (replace(t, **strip) for t in (SEISMO, CHAMBER, BALLOT))
T_LILAC = replace(LAB, paper="#EDE6F8", texture=None, hairline="#D8CBEF")
LILAC = "#E6DAF3"
CODE = {"Texas": "TX", "Ohio": "OH", "Maine": "ME", "Michigan": "MI", "Minnesota": "MN", "North Carolina": "NC",
        "New Hampshire": "NH", "Nebraska": "NE", "Florida": "FL", "Louisiana": "LA", "Iowa": "IA", "Kansas": "KS",
        "South Carolina": "SC"}


def lean_arrow(s, cx, cy, shift, k=5.3, lw=4.0, z=5):
    """The Times' convention: an arrow leans left and is blue for a move toward Democrats, right and red toward
    Republicans; its length is the size of the move."""
    L = abs(shift) * k
    th = np.radians(32)
    dx, dy = L * np.sin(th), L * np.cos(th)
    sg = -1 if shift > 0 else 1
    base, tip = (cx - sg * dx / 2, cy + dy / 2), (cx + sg * dx / 2, cy - dy / 2)
    col = LAB.dem if shift > 0 else LAB.rep
    s.ax.annotate("", xy=tip, xytext=base, zorder=z, arrowprops=dict(
        arrowstyle="-|>,head_length=0.55,head_width=0.3", color=col, lw=pt(lw), shrinkA=0, shrinkB=0,
        mutation_scale=pt(min(20, max(7, L * 0.42)))))


def numbered(s, lines, size=40):
    for n, line in enumerate(lines, 1):
        top = s.y
        s._put(MARGIN, top - 6, str(n), "hero", s.t.hero_weight, 64, s.t.ai, va="top")
        s.text(line, "serif", 600, size, x=MARGIN + 76, width=s.width - 76, after=0.7)


# ---- 2 How we compare -------------------------------------------------------------------------------------------
def tape(s):
    t = s.t
    s.headline("How NotAPoll v1 compares.", px=74)
    s.dek("The 33 called Senate races, scored four ways.", px=32)
    x0, lw_ = MARGIN, 250
    cw = (s.width - lw_) / 4
    top = s.y + 30
    s.ax.add_patch(plt.Rectangle((x0 + lw_ + cw * 2 + 6, top - 10), cw - 12, 560, fc="#EFE7F8", lw=0, zorder=1))
    for i, h in enumerate(["MARKETS", "POLLS ALONE", "NOTAPOLL V1", "COOK"]):
        cx, mine = x0 + lw_ + cw * (i + .5), i == 2
        s.ax.add_patch(FancyBboxPatch((cx - cw / 2 + 6, top), cw - 12, 54, boxstyle="round,pad=0,rounding_size=27",
                                      fc=t.ai if mine else "#FFFFFF", ec=t.ai, lw=pt(2.5), zorder=3))
        s._put(cx, top + 27, h, "mono", 700, 17, "#FFFFFF" if mine else t.ink, ha="center", va="center", zorder=4)
    rows = [("Calls right", "", ["32/33", "30/33", "30/33", "27/33"], 0, ["", "", "", "+ 5 toss-ups"]),
            ("Confidence score", "lower is better", ["0.039", "0.052", "0.060", "0.068"], 0, [""] * 4),
            ("Average miss", "points of margin", ["–", "6.1", "6.3", "–"], 1, [""] * 4)]
    for r, (lab, sub, vals, best, extra) in enumerate(rows):
        y = top + 120 + r * 160
        s._put(x0, y, lab, "sans", 700, 28, t.ink, va="center")
        if sub:
            s._put(x0, y + 34, sub, "sans", 400, 21, t.ink2, va="center")
        s.ax.plot([x0, x0 + s.width], [y + 70, y + 70], color=t.hairline, lw=pt(1.5), zorder=2)
        for i, v in enumerate(vals):
            cx = x0 + lw_ + cw * (i + .5)
            if i == best:
                s.ax.add_patch(FancyBboxPatch((cx - cw / 2 + 12, y - 36), cw - 24, 72,
                                              boxstyle="round,pad=0,rounding_size=14", fc=LILAC, lw=0, zorder=2))
            s._put(cx, y, v, "hero", 700, 46, t.ink if v != "–" else t.muted, ha="center", va="center", zorder=4)
            if extra[i]:
                s._put(cx, y + 44, extra[i], "sans", 500, 19, t.ink2, ha="center", va="center", zorder=4)
    s.y = top + 120 + 3 * 160 - 40
    s.note("v1 finished level with polls alone on the calls, slightly behind on confidence. Both missed the size of "
           "the wave.", width=900, px=28)


FIELD = [("Silver Bulletin", 80), ("FiftyPlusOne", 79), ("Race to the WH", 78), ("Split Ticket", 77),
         ("Polymarket", 77), ("Kalshi", 77), ("DDHQ", 64), ("NotAPoll v1", 59), ("The Economist", 53)]


def field(s):
    t = s.t
    s.headline("All nine had Democrats ahead. Only one was less sure than us.", px=58)
    s.dek("Each forecast's final chance of a Democratic Senate, in 100. Democrats won it.", px=28)
    xl, xr = MARGIN + 290, s.w - MARGIN - 70
    X = lambda v: xl + (xr - xl) * (v - 50) / 50
    top, step = s.y + 70, 60
    for v, lab in [(50, "coin flip"), (75, "75"), (100, "certain")]:
        s.ax.plot([X(v), X(v)], [top - 14, top + step * len(FIELD) - 18], color=t.hairline if v != 50 else t.baseline,
                  lw=pt(2), zorder=1)
        s._put(X(v), top - 24, lab, "mono", 500, 19, t.ink2, ha="center" if v == 75 else "right" if v == 100 else
               "center", va="bottom")
    for i, (name, v) in enumerate(FIELD):
        y, me = top + i * step + 14, name == "NotAPoll v1"
        s._put(MARGIN, y, name, "sans", 700 if me else 500, 28, t.ai if me else t.ink, va="center")
        s.ax.plot([X(50), X(v)], [y, y], color=t.ai if me else t.baseline, lw=pt(4 if me else 3), zorder=2)
        s.ax.scatter([X(v)], [y], s=pt(26 if me else 20) ** 2, color=t.ai if me else t.data, zorder=3)
        s._put(X(v) + 24, y, str(v), "mono", 700, 24, t.ai if me else t.ink, va="center")
    s.y = top + step * len(FIELD) + 10
    s.text("Seven were at 64 or higher. v1 said 59.", "sans", 600, 28, t.ink, after=0.4)


def bias(s):
    t = s.t
    s.headline("All three leaned the same way.", px=78)
    s.dek("How far each underrated Democrats on the Senate margins, on average, in points.", px=28)
    k = 150
    y = s.y + 50
    for lab, v, col in [("Raw poll average (27 races with polls)", 3.6, t.ink2), ("Polls alone, our own twin", 4.9, t.ink2),
                        ("NotAPoll v1", 5.2, t.ai)]:
        s._put(MARGIN, y, lab, "sans", 600 if col == t.ai else 500, 26, t.ai if col == t.ai else t.ink2, va="top")
        y += 40
        s.ax.add_patch(FancyBboxPatch((MARGIN, y), v * k, 46, boxstyle="round,pad=0,rounding_size=6", fc=col, lw=0,
                                      zorder=3))
        s._put(MARGIN + v * k + 18, y + 23, f"{v}", "hero", 700, 40, col, va="center")
        y += 46 + 44
    s.y = y + 6
    s.text("Average miss on the margin: 5.9 points for the raw poll average, 6.1 for polls alone, 6.3 for v1.", "sans",
           500, 27, t.ink2, after=0.5)
    s.note("We all missed the same wave.", width=620, px=30)


# ---- 3 The wave -------------------------------------------------------------------------------------------------
def arrows(s, size=62):
    t = s.t
    s.headline("Almost every arrow points the same way.", px=64)
    s.dek("How far each result moved from NotAPoll v1's forecast margin, 13 closest Senate races.", px=25)
    shift = {CODE[n]: act - ours for n, p, ours, act, left in rcard.RACES}
    gap = 6
    x0 = MARGIN + (s.width - (12 * (size + gap) - gap)) / 2
    top = s.y + 24
    for k, (row, c) in TILE.items():
        x, y = x0 + c * (size + gap), top + row * (size + gap)
        has = k in shift
        s.ax.add_patch(FancyBboxPatch((x, y), size, size, boxstyle="round,pad=0,rounding_size=8",
                                      fc="#FFFFFF" if has else "none", ec=t.baseline if has else t.hairline,
                                      lw=pt(1.8 if has else 1.2), zorder=2))
        s._put(x + 7, y + size - 5, k, "mono", 600 if has else 400, 16, t.ink2 if has else t.muted, va="bottom",
               zorder=4)
        if has:
            lean_arrow(s, x + size / 2, y + size / 2 - 2, shift[k], k=size / 62 * 5.3)
    y = top + 8 * (size + gap) + 4
    lean_arrow(s, MARGIN + 30, y + 26, 5)
    s._put(MARGIN + 66, y + 26, "5 points, toward Democrats", "sans", 500, 22, t.ink2, va="center")
    lean_arrow(s, MARGIN + 470, y + 26, -5)
    s._put(MARGIN + 506, y + 26, "toward Republicans", "sans", 500, 22, t.ink2, va="center")
    s.y = y + 64
    s.text("12 of 13 moved toward Democrats. Only Nebraska went the other way.", "sans", 700, 26, t.ink, after=0.3)


def damp(s):
    t = s.t
    s.headline("Why v1 stayed close to where it started.", px=70)
    s.dek("Three design choices, each reasonable, that damped everything.", px=28)
    s.y += 16
    numbered(s, ["Stories fade fast: a half-life of 5.5 days, so a week-old story keeps about 40% of its effect.",
                 "Only voters who can still move count: the persuadable share for vote choice, the mobilisable share "
                 "for turnout.",
                 "The size we gave each reaction was set from past events, about 0.21 on our scale. No wave was in that history."],
             size=40)
    s.note("Together, they damped everything.", width=640, px=32)


# ---- 4 Texas ----------------------------------------------------------------------------------------------------
TX_OURS = [59.0, 59.1, 59.0, 58.7, 59.3, 59.8, 59.0, 60.8, 61.2, 62.5, 65.7, 63.8, 61.8, 62.6, 62.5, 61.4, 62.5, 62.9,
           60.5, 64.5, 64.8, 64.7, 60.8]
TX_MKT = [x * 100 for x in (0.63, 0.6432, 0.63, 0.6278, 0.62, 0.6169, 0.6184, 0.62, 0.6169, 0.64, 0.675, 0.6633, 0.635,
                            0.64, 0.645, 0.66, 0.665, 0.6858, 0.7035, 0.71, 0.6966, 0.745, 0.74)]


def texas(s):
    t = s.t
    s.headline("Texas: Talarico was ahead in all 23 of v1's runs. He won by 12.", px=54)
    s.dek("NotAPoll v1's chance for Talarico each morning, in 100, and the prediction markets'.", px=26)
    xl, xr = MARGIN + 60, s.w - MARGIN - 190
    yt, yb = s.y + 60, s.y + 60 + 440
    X = lambda i: xl + (xr - xl) * i / 22
    Y = lambda v: yb - (yb - yt) * (v - 45) / 35
    for v in (50, 60, 70, 80):
        s.ax.plot([xl, s.w - MARGIN], [Y(v), Y(v)], color=t.baseline if v == 50 else t.hairline,
                  lw=pt(2 if v == 50 else 1.4), zorder=1)
        s._put(MARGIN, Y(v), str(v), "mono", 500, 20, t.ink2, va="center")
    s._put(xl + 6, Y(50) + 10, "coin flip. Cook called Texas a toss-up.", "sans", 500, 20, t.ink2, va="top")
    for i, lab in [(0, "12 Oct"), (8, "20 Oct"), (16, "28 Oct"), (22, "3 Nov")]:
        s._put(X(i), yb + 22, lab, "mono", 500, 20, t.ink2, ha="center" if 0 < i < 22 else "left" if i == 0 else
               "right", va="top")
    for series, col, lw in ((TX_MKT, t.muted, 3.4), (TX_OURS, t.ai, 5)):  # segments, so the Reel draws the line
        for i in range(22):
            s.ax.plot([X(i), X(i + 1)], [Y(series[i]), Y(series[i + 1])], color=col, lw=pt(lw), zorder=4,
                      solid_capstyle="round")
    s.ax.scatter([X(22)], [Y(TX_OURS[-1])], s=pt(20) ** 2, color=t.ai, zorder=5)
    s.ax.scatter([X(22)], [Y(TX_MKT[-1])], s=pt(16) ** 2, color=t.muted, zorder=5)
    s._put(X(22) + 22, Y(TX_OURS[-1]), "v1 61", "sans", 700, 26, t.ai, va="center")
    s._put(X(22) + 22, Y(TX_MKT[-1]), "Markets 74", "sans", 700, 26, t.ink2, va="center")
    s.y = yb + 70
    s.note("Result: Talarico by 12.2 points. v1's expected margin: 1.3.", width=900, px=30)


def texas_four(s):
    t = s.t
    s.headline("Four forecasts. One 12-point win.", px=70)
    s.dek("The chance in 100 each gave Talarico on 3 November.", px=28)
    xl, xr = MARGIN, s.w - MARGIN
    X = lambda v: xl + (xr - xl) * v / 100
    top = s.y + 70
    for v, lab in [(0, "0"), (50, "coin flip"), (100, "100")]:
        s.ax.plot([X(v), X(v)], [top - 10, top + 4 * 118 - 36], color=t.baseline if v == 50 else t.hairline, lw=pt(2),
                  zorder=1)
        s._put(X(v), top - 18, lab, "mono", 500, 19, t.ink2, ha="left" if v == 0 else "right" if v == 100 else "center",
               va="bottom")
    rows = [("Cook Political Report", 50, "toss-up", t.baseline), ("NotAPoll v1", 61, "61", t.ai),
            ("Polls alone", 65, "65", t.ink2), ("Prediction markets", 74, "74", t.ink2)]
    for i, (lab, v, txt, col) in enumerate(rows):
        y = top + 20 + i * 118
        s._put(MARGIN, y, lab, "sans", 700 if col == t.ai else 500, 26, t.ai if col == t.ai else t.ink, va="center")
        s.ax.add_patch(FancyBboxPatch((xl, y + 24), X(v) - xl, 42, boxstyle="round,pad=0,rounding_size=6", fc=col, lw=0,
                                      zorder=3))
        s._put(X(v) + 14, y + 45, txt, "hero", 700, 34, col if col != t.baseline else t.ink2, va="center")
    s.y = top + 4 * 118 + 6
    s.note("He won by 12.2 points.", width=520, px=32)


# ---- 5 The voter personas ---------------------------------------------------------------------------------------
def personas(s):
    t = s.t
    s.headline("Right way. A tenth of the distance.", px=80)
    s.dek("How the voter personas read the 2026 Senate races.", px=30)
    s._put(MARGIN, s.y + 10, "WHICH WAY THEY PUSHED, 32 RACES", "mono", 600, 19, t.ink2, va="top")
    top = s.y + 52
    for i in range(32):
        row, col = divmod(i, 8)
        lean_arrow(s, MARGIN + (col + .5) * s.width / 8, top + row * 58 + 30, 8.4 if i < 29 else -8.4)
    y = top + 4 * 58 + 2
    s._put(MARGIN, y, "29 of 32 toward Democrats. Three the other way.", "sans", 600, 27, t.ink, va="top")
    y += 52
    s._put(MARGIN, y, "HOW FAR, IN THE 10 CLOSEST RACES", "mono", 600, 19, t.ink2, va="top")
    k = 150
    for lab, v, col in [("What the personas moved a race", 0.4, t.ai),
                        ("How far results beat our polls-alone number", 4.5, t.dem)]:
        y += 38
        s._put(MARGIN, y, lab, "sans", 500, 24, t.ink2, va="top")
        y += 32
        s.ax.add_patch(FancyBboxPatch((MARGIN, y), v * k, 38, boxstyle="round,pad=0,rounding_size=6", fc=col, lw=0,
                                      zorder=3))
        s._put(MARGIN + v * k + 16, y + 19, f"{v} points", "hero", 700, 34, col, va="center")
        y += 38
    s.y = y + 20
    s.note("A feel for the national mood. Not for which races.", width=760, px=30)


def personas_text(s):
    s.headline("They sensed the mood. Not the map.", px=74)
    s.y += 16
    numbered(s, ["In 29 of 32 Senate races, the news effect pointed toward the Democrat or independent challenger.",
                 "The results beat the polls toward that same side in 28 of 32.",
                 "But the races the personas pushed hardest were not the races that moved most: no link at all."],
             size=40)
    s.note("A national tilt, not race-by-race skill.", width=640, px=32)


# ---- 6 The receipts ---------------------------------------------------------------------------------------------
def receipt(s):
    t = s.t
    s.headline("The receipts.", px=92)
    s.dek("What we said about seven races, and how they came out.", px=30)
    x0, x1 = MARGIN + 90, s.w - MARGIN - 90
    top = s.y + 20
    bot = top + 752
    amp, nz = 11, 28

    def zig(y, up):
        xs = np.linspace(x0, x1, nz + 1)
        return [(x, y + (amp if (k % 2) == up else 0)) for k, x in enumerate(xs)]

    for off, col in ((9, "#CBB9E8"), (0, "#FFFFFF")):
        pts_ = [(px + off, py + off) for px, py in zig(top, 1)] + [(px + off, py + off) for px, py in zig(bot, 0)][::-1]
        s.ax.add_patch(Polygon(pts_, closed=True, fc=col, lw=0, zorder=2 if off else 3))
    cx, y = (x0 + x1) / 2, top + 44
    s._put(cx, y, "NOTAPOLL V1", "mono", 700, 36, t.ink, ha="center", va="center", zorder=5)
    s._put(cx, y + 40, f"RESULTS AS OF {AS_OF.upper()} 2026", "mono", 500, 19, t.ink2, ha="center", va="center",
           zorder=5)
    s._put(cx, y + 66, "PROVISIONAL", "mono", 700, 19, t.rep, ha="center", va="center", zorder=5)

    def rule(yy):
        s.ax.plot([x0 + 26, x1 - 26], [yy, yy], color=t.ink2, lw=pt(1.6), linestyle=(0, (4, 3)), zorder=5)

    y += 90
    rule(y)
    y += 26
    s._put(x0 + 30, y, "RACE", "mono", 600, 17, t.ink2, va="center", zorder=5)
    s._put(x0 + 250, y, "WE SAID", "mono", 600, 17, t.ink2, va="center", zorder=5)
    s._put(x1 - 80, y, "RESULT", "mono", 600, 17, t.ink2, ha="right", va="center", zorder=5)
    rows = [("Texas", "Talarico +3", "D +12.2", True), ("Ohio", "Brown +3", "D +5.0", True),
            ("Michigan", "El-Sayed +4", "D +7.1", True), ("N. Carolina", "Cooper +9", "D +20.0", True),
            ("Maine", "Jackson +2", "D +6.9", True), ("Kansas", "Marshall +2", "D +5.2", False),
            ("Iowa", "Hinson +1", "D +4.2", False)]
    y += 10
    for race, said, res, ok in rows:
        y += 40
        s._put(x0 + 30, y, race, "mono", 600, 22, t.ink, va="center", zorder=5)
        s._put(x0 + 250, y, said, "mono", 500, 22, t.ink2, va="center", zorder=5)
        s._put(x1 - 80, y, res, "mono", 700, 22, t.dem, ha="right", va="center", zorder=5)
        rcard.mark(s, x1 - 62, y + 1, ok, 20)
    y += 32
    rule(y)
    for lab, val in [("DIRECTION RIGHT", "5 / 7"), ("DEMOCRATS DID BETTER", "7 / 7")]:
        y += 38
        s._put(x0 + 30, y, lab, "mono", 700, 21, t.ink, va="center", zorder=5)
        s._put(x1 - 30, y, val, "mono", 700, 24, t.ai, ha="right", va="center", zorder=5)
    y += 26
    rule(y)
    y += 24
    for line in ["Alaska: still counting. Texas and Ohio were posted", "several times (+2 to +3; +3). Hypotheses as posted;",
                 "results: share of the two main candidates' votes."]:
        s._put(x0 + 30, y, line, "mono", 400, 16, t.ink2, va="center", zorder=5)
        y += 22
    rng = np.random.default_rng(3)
    bx = x0 + 70
    for _ in range(46):
        w = rng.choice([2, 2, 3, 5])
        s.ax.add_patch(plt.Rectangle((bx, y + 6), w, 36, fc=t.ink, lw=0, zorder=5))
        bx += w + rng.choice([2, 3, 4])
        if bx > x1 - 70:
            break
    s.y = bot + 30


# ---- 7 What a v2 would change -----------------------------------------------------------------------------------
def faders(s):
    t = s.t
    s.headline("What a v2 would change.", px=84)
    s.dek("Five dials we'd turn after reading the results.", px=30)
    sw = s.width / 5
    top, h = s.y + 40, 380
    items = [("How far news moves a race", .30, .74), ("How long a story lasts", .34, .70),
             ("Turnout reactions, tuned on their own", .26, .64), ("Room for a national swing", .38, .72),
             ("The starting correction, re-checked", .72, .34)]
    for i, (lab, a, b) in enumerate(items):
        cx = MARGIN + sw * (i + .5)
        s.ax.add_patch(FancyBboxPatch((cx - 6, top), 12, h, boxstyle="round,pad=0,rounding_size=6", fc=LILAC, lw=0,
                                      zorder=2))
        for tk in range(9):
            s.ax.plot([cx - 24, cx - 12], [top + h * tk / 8] * 2, color=t.baseline, lw=pt(1.4), zorder=2)
        ya, yb_ = top + h * (1 - a), top + h * (1 - b)
        s.ax.annotate("", xy=(cx + 44, yb_ + (16 if b > a else -16)), xytext=(cx + 44, ya + (-16 if b > a else 16)),
                      arrowprops=dict(arrowstyle="-|>,head_length=0.5,head_width=0.3", color=t.ai, lw=pt(3.2),
                                      shrinkA=0, shrinkB=0, mutation_scale=pt(18)), zorder=4)
        s.ax.add_patch(FancyBboxPatch((cx - 36, ya - 17), 72, 34, boxstyle="round,pad=0,rounding_size=8", fc=t.paper,
                                      ec=t.ink2, lw=pt(2.2), linestyle=(0, (3, 2)), zorder=5))
        s.ax.add_patch(FancyBboxPatch((cx - 36, yb_ - 17), 72, 34, boxstyle="round,pad=0,rounding_size=8", fc=t.ai,
                                      lw=0, zorder=6))
        s.ax.plot([cx - 20, cx + 20], [yb_] * 2, color="#FFFFFF", lw=pt(2.2), zorder=7)
        for j, line in enumerate(s.wrap(lab, "sans", 700, 21, sw - 18)):
            s._put(cx, top + h + 34 + j * 28, line, "sans", 700, 21, t.ink, ha="center", va="top")
    s.y = top + h + 140
    s.text("Dashed: today. Solid: next time. Plus more local news and state-specific personas, to find which races "
           "move.", "sans", 500, 24, t.ink2, after=0.3)


def how_we_know(s):
    s.headline("How we'd know v2 is better.", px=76)
    s.y += 16
    numbered(s, ["Race by race: do the races the personas push hardest move the most? Today that link is zero.",
                 "A blind test: no 2026 polls, so the news alone has to find the wave.",
                 "The same scorecard, the same rules, in public: hits, misses and every number."], size=40)
    s.note("v1 is our first version, not our last.", width=640, px=32)


# ---- 8 By the numbers -------------------------------------------------------------------------------------------
def numbers(s):
    t = s.t
    s.headline("NotAPoll v1, by the numbers.", px=72)
    bw, bh, g = (s.width - 20) / 2, 196, 18
    blocks = [("23", "daily forecasts, 12 Oct to 3 Nov", t.ai, "#FFFFFF"), ("45,000", "news articles read", t.dem, "#FFFFFF"),
              ("135,000", "reactions from voter personas", "#F6DD6E", t.ink),
              ("35 + 435", "Senate races and House seats", "#CDB8E3", t.ink),
              ("$18", "in model costs for the daily runs", t.rep, "#FFFFFF"), ("128", "posts, hits and misses", "#FFFFFF", t.ink)]
    top = s.y + 6
    for i, (num, lab, fc, fg) in enumerate(blocks):
        r, c = divmod(i, 2)
        x, y = MARGIN + c * (bw + g), top + r * (bh + g)
        s.ax.add_patch(FancyBboxPatch((x, y), bw, bh, boxstyle="round,pad=0,rounding_size=22", fc=fc,
                                      ec=t.hairline if fc == "#FFFFFF" else "none", lw=pt(2), zorder=3))
        s._put(x + 30, y + 30, num, "hero", 700, 80, fg, va="top", zorder=4)
        for j, line in enumerate(s.wrap(lab, "sans", 600, 25, bw - 60)):
            s._put(x + 30, y + 132 + j * 30, line, "sans", 600, 25, fg, va="top", zorder=4)
    s.y = top + 3 * (bh + g) + 2
    s.note("Thank you for following along.", width=700, px=30)


# ---- the posts --------------------------------------------------------------------------------------------------
# ---- the second slot (20:30 Paris, early afternoon in the US): lighter posts ------------------------------------
def card_row(s, y, h, title, body, n=None):
    t = s.t
    s.ax.add_patch(FancyBboxPatch((MARGIN, y), s.width, h, boxstyle="round,pad=0,rounding_size=18", fc="#FFFFFF",
                                  ec=t.hairline, lw=pt(2), zorder=2))
    x = MARGIN + 28
    if n is not None:
        s.ax.add_patch(plt.Circle((MARGIN + 58, y + h / 2), 30, fc=t.ai, lw=0, zorder=3))
        s._put(MARGIN + 58, y + h / 2, str(n), "hero", 700, 34, "#FFFFFF", ha="center", va="center", zorder=4)
        x = MARGIN + 112
    s._put(x, y + 24, title, "sans", 700, 30, t.ink, va="top", zorder=4)
    for j, line in enumerate(s.wrap(body, "sans", 400, 25, s.width - (x - MARGIN) - 28)):
        s._put(x, y + 70 + j * 32, line, "sans", 400, 25, t.ink2, va="top", zorder=4)


def how_it_worked(s):
    s.headline("How NotAPoll v1 worked.", px=80)
    s.dek("Four steps, from the starting line to the final forecast.", px=30)
    y = s.y + 14
    for n, (title, body) in enumerate([
            ("12 Oct: the starting line", "Each race started from its polls and the state's voting record."),
            ("Every day: the news", "Voter personas, built from real survey answers, reacted to the day's stories."),
            ("Every race: 40,000 simulated elections", "Each draws its own swings. A candidate's chance is how often "
                                                       "they win."),
            ("Every Sunday: the check", "The polls and the markets checked us. They never moved our numbers.")], 1):
        card_row(s, y, 158, title, body, n)
        y += 178
    s.y = y


def what_next(s):
    t = s.t
    s.headline("The count isn't over.", px=88)
    s.dek("What happens next, as of 11 November.", px=30)
    x = MARGIN + 36
    top = s.y + 36
    items = [("Mississippi", "Still counting its last ballots."),
             ("Alaska", "Runs its ranked-choice count in the coming days."),
             ("After certification", "Our final scorecard: every race scored against the official results, misses "
                                     "first.")]
    step = 200
    s.ax.plot([x, x], [top + 16, top + step * 2 + 16], color=t.baseline, lw=pt(3), zorder=1)
    for i, (title, body) in enumerate(items):
        y = top + i * step
        s.ax.add_patch(plt.Circle((x, y + 16), 17, fc=t.ai if i == 2 else t.paper, ec=t.ai, lw=pt(3.5), zorder=3,
                                  linestyle="-" if i == 2 else (0, (3, 2))))
        s._put(x + 50, y, title, "sans", 700, 34, t.ink, va="top")
        for j, line in enumerate(s.wrap(body, "sans", 400, 27, s.width - 100)):
            s._put(x + 50, y + 52 + j * 34, line, "sans", 400, 27, t.ink2, va="top")
    s.y = top + 3 * step - 10
    s.note("Until then, every number is provisional.", width=640, px=30)


def chips(s, items, h=128, gap=26, px=54):
    t = s.t
    y = s.y + 30
    for letter, txt in items:
        s.ax.add_patch(FancyBboxPatch((MARGIN, y), s.width, h, boxstyle="round,pad=0,rounding_size=22", fc="#FFFFFF",
                                      ec=t.ai, lw=pt(3), zorder=2))
        s.ax.add_patch(plt.Circle((MARGIN + 70, y + h / 2), 38, fc=t.ai, lw=0, zorder=3))
        s._put(MARGIN + 70, y + h / 2, letter, "hero", 700, 44, "#FFFFFF", ha="center", va="center", zorder=4)
        s._put(MARGIN + 140, y + h / 2, txt, "hero", 700, px, t.ink, va="center", zorder=4)
        y += h + gap
    s.y = y


def guess_q(s):
    s.headline("Guess the margin.", px=96)
    s.dek("North Carolina Senate. NotAPoll v1 said Cooper by 8.8 points. Where did it land?", px=30)
    chips(s, [("A", "Cooper by 9"), ("B", "Cooper by 14"), ("C", "Cooper by 20")])
    s.note("Swipe for the answer.", width=520, px=32)


def guess_a(s):
    t = s.t
    s.headline("Cooper by 20.0.", px=96)
    s.dek("The result, in points. NotAPoll v1 had said 8.8.", px=30)
    y = s.y + 30
    s._put(MARGIN, y, "8.8", "hero", 700, 170, t.muted, va="top")
    s._put(MARGIN + 380, y + 50, "→", "hero", 700, 110, t.ai, va="top")
    s._put(MARGIN + 520, y, "20.0", "hero", 700, 170, t.ai, va="top")
    s._put(MARGIN, y + 190, "v1's expected margin", "sans", 600, 26, t.ink2, va="top")
    s._put(MARGIN + 520, y + 190, "the result", "sans", 600, 26, t.ink2, va="top")
    s.y = y + 250
    s.text("The biggest gap between v1 and a result in the 13 closest Senate races: 11.2 points.", "sans", 600, 30,
           t.ink, after=0.6)
    s.note("A safe call, right. A margin far bigger than v1 expected.", width=860, px=30)


def sc_chances(s):
    t = s.t
    s.headline("South Carolina: the real miss.", px=66)
    s.dek("The chance in 100 each gave the Democrat.", px=28)
    xl, xr = MARGIN, s.w - MARGIN
    X = lambda v: xl + (xr - xl) * v / 100
    top = s.y + 70
    for v, lab in [(0, "0"), (50, "coin flip"), (100, "100")]:
        s.ax.plot([X(v), X(v)], [top - 10, top + 3 * 118 - 36], color=t.baseline if v == 50 else t.hairline, lw=pt(2),
                  zorder=1)
        s._put(X(v), top - 18, lab, "mono", 500, 19, t.ink2, ha="left" if v == 0 else "right" if v == 100 else "center",
               va="bottom")
    for i, (lab, v, col) in enumerate([("NotAPoll v1", 17, t.ai), ("Polls alone", 25, t.ink2),
                                       ("Prediction markets", 32, t.ink2)]):
        y = top + 20 + i * 118
        s._put(MARGIN, y, lab, "sans", 700 if col == t.ai else 500, 26, t.ai if col == t.ai else t.ink, va="center")
        s.ax.add_patch(FancyBboxPatch((xl, y + 24), X(v) - xl, 42, boxstyle="round,pad=0,rounding_size=6", fc=col, lw=0,
                                      zorder=3))
        s._put(X(v) + 14, y + 45, str(v), "hero", 700, 34, col, va="center")
    s.y = top + 3 * 118 + 6
    s.text("All three had the Republican ahead.", "sans", 600, 28, t.ink, after=0.5)
    s.note("The Democrat won by 4.5 points.", width=620, px=32)


def sc_margin(s):
    t = s.t
    s.headline("A 10-point miss.", px=96)
    s.dek("NotAPoll v1's expected margin in South Carolina, against the result.", px=28)
    xl, xr = MARGIN + 50, s.w - MARGIN - 50
    X = lambda v: xl + (xr - xl) * (v + 12) / 24
    y = s.y + 190
    s.ax.plot([X(-12), X(12)], [y, y], color=t.baseline, lw=pt(3), zorder=1)
    for v in (-10, -5, 0, 5, 10):
        s.ax.plot([X(v), X(v)], [y - 10, y + 10], color=t.baseline, lw=pt(2), zorder=1)
        s._put(X(v), y + 24, str(abs(v)), "mono", 500, 20, t.ink2, ha="center", va="top")
    s._put(X(-12), y + 62, "← Republican", "sans", 600, 24, t.rep, va="top")
    s._put(X(12), y + 62, "Democrat →", "sans", 600, 24, t.dem, ha="right", va="top")
    s.ax.annotate("", xy=(X(4.5) - 22, y), xytext=(X(-5.6) + 22, y), zorder=3, arrowprops=dict(
        arrowstyle="-|>,head_length=0.5,head_width=0.3", color=t.ink2, lw=pt(3.5), shrinkA=0, shrinkB=0,
        mutation_scale=pt(20)))
    s.ax.scatter([X(-5.6)], [y], s=pt(28) ** 2, color=t.ai, zorder=4)
    s.ax.scatter([X(4.5)], [y], s=pt(28) ** 2, facecolor=t.paper, edgecolor=t.ink, lw=pt(3.5), zorder=4)
    s._put(X(-5.6), y - 44, "v1: Republican by 5.6", "sans", 700, 25, t.ai, ha="center", va="bottom")
    s._put(X(4.5), y - 44, "Result: Democrat by 4.5", "sans", 700, 25, t.ink, ha="center", va="bottom")
    s.y = y + 140
    s.text("After 12 October the polls moved toward the Democrat. v1's start stayed frozen, and its news moves were too "
           "small to follow. The same happened in Maine, Kansas and Texas.", "sans", 500, 29, t.ink, after=0.6)


def ask_card(s):
    s.headline("If v2 could get one thing right.", px=74)
    s.dek("Which would you pick?", px=32)
    chips(s, [("A", "Which races move most"), ("B", "The size of the wave"), ("C", "Turnout, on its own")], px=46)
    s.note("A, B or C? Tell us in the comments.", width=700, px=32)



@dataclass
class Post:
    name: str
    theme: object
    series: str
    slides: list            # [(draw, source line)]
    reel: Callable | None   # draws the 9:16 cover (None: no Reel)
    caption: str
    x: str
    threads: str
    alts: list
    first_comment: str


def tags(extra: str = "") -> str:
    return f"#midterms2026 #elections{extra}\n\n{DISCLAIMER}"


def post_list() -> list[Post]:
    P = []
    P.append(Post(
        "report-card", LAB, "Our report card",
        [(rcard.report, SRC), (rcard.map_slide, SRC), (rcard.wave, SRC)],
        lambda s: (s.headline("30 of 33 Senate races called right.", px=72), rcard.results_map(s, s.y + 60, 72, 8, 24)),
        "NotAPoll v1's report card. These are provisional results (as of 11 November); the final scorecard comes after "
        "certification.\n\n"
        "Both chambers right. NotAPoll v1 gave Democrats the Senate in 59 of every 100 simulated elections, and they're "
        "at 54 seats, with Alaska and Mississippi still counting. It gave them the House in 63 of 100, and Democrats "
        "won the majority, with more than 250 seats.\n\n"
        "30 of the 33 called Senate races right. That includes Texas, where v1 had Talarico favoured while Cook called "
        "it a toss-up, and Ohio, Maine, Michigan, Minnesota, North Carolina and New Hampshire, plus the Republican "
        "holds in Nebraska, Florida and Louisiana.\n\n"
        "Three misses. Iowa and Kansas we had close, Democrats winning 43 in 100 in each, and both went the other way. "
        "South Carolina was the real miss: 17 in 100 for the Democrat. Two races are still too close to call: Alaska, "
        "and Mississippi, where v1 gave the Republican 94 in 100. If Mississippi flips, it will be v1's biggest miss.\n\n"
        "Where v1 fell short: the size of the wave. On average, Democrats beat our margins by about 5 points in the "
        "Senate, and by more in the House.\n\n"
        "That's v1, our first version. Next: how it compares with the markets, other forecasters and its own "
        "polls-alone twin, and what a v2 would change.\n\n"
        f"Which call surprised you most?\n\n{tags()}",
        f"NotAPoll v1's report card (provisional): both chambers right, 30 of 33 Senate races; missed Iowa, Kansas, "
        f"South Carolina. v1 underestimated the wave: Democrats beat our margins by about 5 points on average. Final "
        f"scorecard after certification. {LABEL}.",
        "NotAPoll v1's report card (provisional): both chambers called right, and 30 of 33 Senate races, Texas "
        "included, where v1 had Talarico favoured while Cook said toss-up. Misses: Iowa, Kansas, South Carolina. And "
        "v1 underestimated the wave: on average, Democrats beat our margins by about 5 points. Which call surprised "
        "you most?",
        ["NotAPoll v1's report card, drawn as a school report: Senate control, called Democrats 59 in 100, result "
         "Democrats at 54 seats, ticked; House control, 63 in 100, Democratic majority, ticked; Senate races, 30 of 33 "
         "right; size of the wave, needs work. Provisional results.",
         "30 of 33 Senate races called right. A tile map of the 35 Senate races, each coloured by who won, with the "
         "chance NotAPoll v1 gave the winner: " + "; ".join(f"{r[0]} {rcard.winner(r)[1]}" for r in rcard.RACES)
         + ". Iowa, Kansas and South Carolina carry a cross: v1 called them the other way. Alaska and Mississippi: "
         "still counting.",
         "Where v1 fell short: its expected margin against the result in 13 Senate races, with arrows; most results "
         "landed to the Democratic side of v1's number. Democrats beat its margins by about 5 points."],
        "Which call surprised you most?"))

    P.append(Post(
        "compare", T_SEIS, "How we compare",
        [(tape, "Scored on the 33 called Senate races. Polls alone: our own twin, with the voter personas off. "
                "Provisional results."),
         (field, "Final forecasts, 1 to 3 Nov. Markets are Polymarket and Kalshi prices; The Economist's figure is via "
                 "Vote-Scope, 2 Nov. Provisional results."),
         (bias, "Raw poll average: the 27 races with polls. Bias: how far Democrats were underrated, on average. "
                "Provisional results.")],
        tape,
        "How NotAPoll v1 compares, now the results are in (provisional until certification).\n\n"
        "We scored four forecasters on the 33 Senate races called so far: the prediction markets, a polls-alone "
        "version of our own model (the same model with the voter personas switched off), NotAPoll v1, and the Cook "
        "Political Report.\n\n"
        "Calls: the markets got 32 of 33 right, polls alone and v1 30 of 33, Cook 27 of 33 with 5 toss-ups. "
        "Confidence score, lower is better: markets 0.039, polls alone 0.052, v1 0.060, Cook 0.068. Average miss on "
        "the margin: polls alone 6.1 points, v1 6.3.\n\n"
        "So v1 finished level with polls alone on the calls, and slightly behind on confidence. Most of that gap "
        "comes from four races: South Carolina, Maine, Kansas and Texas. And we all leaned the same way: the raw poll "
        "average underrated Democrats by 3.6 points, polls alone by 4.9, v1 by 5.2.\n\n"
        "Next to other forecasters, v1 was less sure that Democrats would win the Senate: 59 in 100, against 77 to 80 "
        "at the markets and four others. Only the Economist was lower, at around 53 to 56. Democrats won it.\n\n"
        "This is v1, our first version. The full scorecard comes after certification, and v2 starts from it.\n\n"
        f"Which number surprised you?\n\n{tags()}",
        f"How NotAPoll v1 compares (provisional): level with its polls-alone twin on the calls, 30 of 33 each, and "
        f"slightly behind on the confidence score. Markets did best. All of us underrated Democrats. Full scorecard "
        f"after certification. {LABEL}.",
        "How NotAPoll v1 compares, provisional: on the 33 called Senate races it got 30 right, level with its own "
        "polls-alone twin and behind the markets (32). Slightly behind on confidence, and we all underrated "
        "Democrats. The full scorecard comes after certification. Which number surprised you?",
        ["A comparison table for the 33 called Senate races. Calls right: markets 32 of 33, polls alone 30, "
         "NotAPoll v1 30, Cook 27 plus 5 toss-ups. Confidence score, lower is better: 0.039, 0.052, 0.060, 0.068. "
         "Average miss: polls alone 6.1 points, v1 6.3.",
         "Final chance of a Democratic Senate, in 100: Silver Bulletin 80, FiftyPlusOne 79, Race to the WH 78, Split "
         "Ticket 77, Polymarket 77, Kalshi 77, DDHQ 64, NotAPoll v1 59, The Economist 53. Democrats won the Senate.",
         "Three bars for how far each underrated Democrats on Senate margins, on average: raw poll average 3.6 points, "
         "polls alone 4.9, NotAPoll v1 5.2. Average miss: 5.9, 6.1 and 6.3 points."],
        "Which number surprised you?"))

    P.append(Post(
        "wave", LAB, "The wave",
        [(arrows, "Result minus NotAPoll v1's expected margin (share of the two main candidates' votes). Provisional "
                  "results."),
         (damp, "From our review of the results. Half-life: a story loses half its effect every 5.5 days.")],
        lambda s: arrows(s, 70),
        "The wave, race by race. NotAPoll v1's expected margin against the result in the 13 closest Senate races: 12 "
        "of 13 moved toward Democrats, the biggest in North Carolina (11.2 points), Texas (10.9) and South Carolina "
        "(10.1). Only Nebraska went the other way, 2.6 points toward the Republican.\n\n"
        "Why was v1 so cautious? Three design choices kept its moves small: news stories fade with a half-life of "
        "5.5 days; only the persuadable and mobilisable share of each group counts; and the size of a reaction was "
        "set from past events, which held no wave. Together they damped everything.\n\n"
        "A v2 would test all three. Provisional results; the final scorecard comes after certification.\n\n"
        f"Where did the wave surprise you?\n\n{tags()}",
        f"The wave, race by race (provisional): 12 of the 13 closest Senate races moved toward Democrats against "
        f"NotAPoll v1's forecast, North Carolina by 11 points, Texas by 11, South Carolina by 10. Only Nebraska went "
        f"the other way. {LABEL}.",
        "The wave, race by race: 12 of the 13 closest Senate races came in more Democratic than NotAPoll v1 "
        "forecast, the most in North Carolina (11 points), Texas (11) and South Carolina (10). Only Nebraska moved the "
        "other way. v1 was built to move cautiously; a v2 would test that. Where did the wave surprise you?",
        ["A tile map of the 50 states. In 13 close Senate races an arrow shows how far the result moved from "
         "NotAPoll v1's expected margin: blue arrows lean left, toward Democrats, red toward Republicans. Twelve "
         "arrows are blue; the biggest are North Carolina, Texas and South Carolina. Only Nebraska is red.",
         "Why v1 stayed close to where it started: stories fade with a half-life of 5.5 days; only voters who can "
         "still move count; the size given each reaction was set from past events, about 0.21 on our scale. Together they damped "
         "everything."],
        "Where did the wave surprise you?"))

    P.append(Post(
        "texas", T_CHAM, "Texas",
        [(texas, SRC), (texas_four, SRC)],
        texas,
        "Texas, in 23 runs. NotAPoll v1 had Talarico ahead in every one of its 23 daily forecasts, between 59 and 66 "
        "in 100. The prediction markets climbed from 63 to 74 over the same weeks. Cook called it a toss-up.\n\n"
        "Talarico won by 12.2 points (provisional). v1's expected margin was 1.3. The right call, but a far smaller "
        "margin than the voters delivered.\n\n"
        "On 3 November: Cook a toss-up, v1 61 in 100, polls alone 65, the markets 74. Margins are the share of the "
        "two main candidates' votes. The final scorecard comes after certification.\n\n"
        f"Which race did you watch most?\n\n{tags(' #Texas')}",
        f"Texas in 23 runs: NotAPoll v1 had Talarico ahead every day (59 to 66 in 100); markets rose from 63 to 74; "
        f"Cook said toss-up. He won by 12.2 points (provisional); v1 expected 1.3. Right call, far too small a "
        f"margin. {LABEL}.",
        "Texas in 23 runs: NotAPoll v1 had Talarico ahead every single day, between 59 and 66 in 100. The markets "
        "rose from 63 to 74, and Cook said toss-up. He won by 12.2 points (provisional); v1's expected margin was "
        "1.3. Right call, far too small a margin. Which race did you watch most?",
        ["A line chart of 23 daily forecasts for Texas, 12 October to 3 November. NotAPoll v1's chance for Talarico "
         "stays between 59 and 66 in 100, ending at 61; the prediction markets' price climbs from 63 to 74. Result: "
         "Talarico won by 12.2 points; v1's expected margin was 1.3.",
         "Four forecasts of Talarico's chance on 3 November: Cook, a toss-up; NotAPoll v1, 61 in 100; polls alone, 65; "
         "prediction markets, 74. He won by 12.2 points."],
        "Which race did you watch most?"))

    P.append(Post(
        "personas", LAB, "Voter personas",
        [(personas, "Ten closest Senate races; direction across 32. " + SRC), (personas_text, SRC)],
        personas,
        "What the voter personas sensed. In NotAPoll v1, voter personas built from real survey answers react to the "
        "news every day, and those reactions were the only thing that moved our numbers after 12 October.\n\n"
        "They leaned the right way: in 29 of 32 Senate races the news pushed toward the Democrat or independent "
        "challenger, and the results beat the polls toward the same side in 28 of 32.\n\n"
        "But they moved about a tenth of the distance. In the ten closest races the personas moved a result by 0.4 "
        "points on average; the results beat our polls-alone number by 4.5.\n\n"
        "And they didn't know where it would land: the races the personas pushed hardest were not the ones that moved "
        "most. v1 sensed the national mood, not the map. That's what a v2 has to fix.\n\n"
        f"Provisional results. Would you rather have the mood or the map?\n\n{tags()}",
        f"What the voter personas sensed (provisional): in 29 of 32 Senate races NotAPoll v1's news effect pointed "
        f"toward Democrats, the right way. But it moved the closest races 0.4 points; the results beat polls alone by "
        f"4.5. The mood, not the map. {LABEL}.",
        "What the voter personas sensed: in 29 of 32 Senate races the news pushed toward the Democrat, the right way. "
        "But they moved the closest races about 0.4 points, a tenth of how far the results beat polls alone (4.5), "
        "and they didn't know which races. The mood, not the map. Would you rather have the mood or the map?",
        ["A grid of 32 arrows, one per Senate race: 29 blue arrows lean left, toward Democrats; 3 red arrows lean "
         "right. Below, two bars to scale: the personas moved a race 0.4 points; the results beat our polls-alone "
         "number by 4.5.",
         "They sensed the mood, not the map: in 29 of 32 races the news effect pointed toward Democrats; the results "
         "beat the polls the same way in 28 of 32; but the races pushed hardest were not the races that moved most."],
        "Would you rather have the mood or the map?"))

    P.append(Post(
        "receipts", T_LILAC, "The receipts",
        [(receipt, SRC)],
        receipt,
        "The receipts. Every Reading the polls post ended with a hypothesis, our best guess of the real margin. Seven "
        "can be scored now, against the provisional results.\n\n"
        "Texas, in four posts: Talarico +2 to +3. He won by 12.2. Ohio: Brown +3, he won by 5.0. Michigan: El-Sayed +4, "
        "he won by 7.1. North Carolina: Cooper +9, he won by 20.0. Maine: Jackson +2, he won by 6.9. Kansas: Marshall "
        "+2, but Hamilton won by 5.2. Iowa: Hinson +1, but Turek won by 4.2.\n\n"
        "Direction right in 5 of 7. In all seven, the Democrat did better than we said.\n\n"
        "We had promised to check each one against the next three polls. This is the simpler check: the result. "
        "Alaska is still counting, and South Dakota isn't scored here yet. Hypotheses are margins as we posted them; "
        "results are shares of the two main candidates' votes.\n\n"
        f"Which receipt surprised you?\n\n{tags()}",
        f"The receipts: what we said about seven races in Reading the polls, against the provisional results. "
        f"Direction right in 5 of 7, and in all seven the Democrat did better than we said. Texas: we said +3, "
        f"Talarico won by 12.2. {LABEL}.",
        "The receipts: what we said about seven races in Reading the polls, against the provisional results. "
        "Direction right in 5 of 7, and in all seven the Democrat did better than we said. Texas: we said Talarico "
        "+3, he won by 12.2. Which receipt surprised you?",
        ["A shop receipt headed NotAPoll v1, results as of 11 November, provisional. Seven rows, what we said and the "
         "result: Texas Talarico +3, D +12.2, right; Ohio Brown +3, D +5.0, right; Michigan El-Sayed +4, D +7.1, "
         "right; North Carolina Cooper +9, D +20.0, right; Maine Jackson +2, D +6.9, right; Kansas Marshall +2, D "
         "+5.2, wrong; Iowa Hinson +1, D +4.2, wrong. Direction right 5 of 7; Democrats did better 7 of 7."],
        "Which receipt surprised you?"))

    P.append(Post(
        "v2", T_BALL, "What v2 changes",
        [(faders, "Illustration: arrows show the direction of each change, not its size. From our review of the "
                  "results."),
         (how_we_know, "From our review of the results.")],
        faders,
        "What a v2 would change. We went back through the results and found five dials to turn on NotAPoll v1:\n\n"
        "1. How far news moves a race: v1's moves were about a tenth of what the voters did.\n"
        "2. How long a story lasts: v1's stories fade in days, but a wave builds for weeks.\n"
        "3. Turnout: the wave ran on enthusiasm and turnout, so those reactions need their own calibration.\n"
        "4. Room for a national swing: our 80% ranges held 75% of the results, and every miss went the same way.\n"
        "5. The starting correction: re-check the 2.8-point adjustment we make to the generic ballot, and let "
        "early-vote data move the start.\n\n"
        "And one thing no dial fixes: telling which races move most. More local news and state-specific voter "
        "personas are the first thing we'd try, and we'd score it race by race.\n\n"
        f"v1 is our first version, not our last. Provisional results. What should v2 get right first?\n\n{tags()}",
        f"What a v2 would change: turn up how far news moves a race and how long it lasts, tune turnout on its own, "
        f"allow a wider national swing, re-check the starting correction. NotAPoll v1 is our first version, not our "
        f"last. {LABEL}.",
        "What a v2 would change: turn up how far news moves a race and how long it lasts, tune turnout on its own, "
        "allow a wider national swing, and re-check the starting correction. Then see whether it can tell which races "
        "move. v1 is our first version, not our last. What should v2 get right first?",
        ["Five vertical sliders, like a mixing desk. Four move up, from a dashed position today to a solid one next "
         "time: how far news moves a race, how long a story lasts, turnout reactions tuned on their own, room for a "
         "national swing. One moves down: the starting correction, re-checked. An illustration of direction, not size.",
         "How we would know v2 is better: race by race, do the races the personas push hardest move the most; a blind "
         "test with no 2026 polls; the same scorecard and rules, in public. v1 is our first version, not our last."],
        "What should v2 get right first?"))

    P.append(Post(
        "numbers", T_LILAC, "By the numbers",
        [(numbers, "The public runs, 12 Oct to 3 Nov. Counts from our own records.")],
        numbers,
        "NotAPoll v1, by the numbers. From 12 October to 3 November: 23 daily forecasts of all 35 Senate races and 435 "
        "House seats; about 45,000 news articles read; about 135,000 reactions from voter personas built from real "
        "survey answers; 128 posts, hits and misses included. The daily runs cost about $18 in model fees.\n\n"
        "Thank you for following along, and for every comment. The final scorecard comes after certification. Then, "
        f"v2.\n\nWhat would you like us to score next?\n\n{tags()}",
        f"NotAPoll v1 by the numbers: 23 daily forecasts, about 45,000 news articles read, about 135,000 reactions "
        f"from voter personas, 128 posts, about $18 in model costs for the daily runs. Thank you for following along. Final scorecard "
        f"after certification. {LABEL}.",
        "NotAPoll v1, by the numbers: 23 daily forecasts of 35 Senate races and 435 House seats, about 45,000 news "
        "articles read, about 135,000 reactions from voter personas, 128 posts, and about $18 in model costs for the daily runs. "
        "Thank you for following along. What would you like us to score next?",
        ["Six colour blocks of numbers for NotAPoll v1: 23 daily forecasts, 12 October to 3 November; 45,000 news "
         "articles read; 135,000 reactions from voter personas; 35 Senate races plus 435 House seats; about $18 in "
         "model costs for the daily runs; 128 posts, hits and misses. Thank you for following along."],
        "What would you like us to score next?"))
    return P


def second_list() -> list[Post]:
    P = []
    P.append(Post(
        "how-v1-worked", LAB, "How v1 worked", [(how_it_worked, "How NotAPoll v1 worked. Method: notapoll.org/methods")],
        how_it_worked,
        "How NotAPoll v1 worked, in four steps.\n\n"
        "1. On 12 October, each race started from its polls and the state's voting record.\n"
        "2. Every day after that, voter personas, built from real survey answers, reacted to the day's news.\n"
        "3. Every race was then played out 40,000 times, and a candidate's chance is how often they win.\n"
        "4. Every Sunday, the polls and the markets checked us. They never moved our numbers.\n\n"
        "That was the experiment: could a social simulation, rather than a poll, get close to a real election? This "
        "week we're sharing how it went, hits and misses.\n\n"
        f"What would you like us to explain next?\n\n{tags()}",
        f"How NotAPoll v1 worked: polls and voting records set each race's start on 12 Oct; then voter personas "
        f"reacted to the news every day, 40,000 simulated elections per race, and polls only checked us on Sundays. "
        f"{LABEL}.",
        "How NotAPoll v1 worked, in four steps: a starting line from polls and voting records on 12 October; voter "
        "personas reacting to the news every day; 40,000 simulated elections per race; and a check against the polls "
        "and markets every Sunday. What would you like us to explain next?",
        ["Four numbered steps for how NotAPoll v1 worked. One: 12 October, the starting line, from each race's polls and "
         "the state's voting record. Two: every day, the news, with voter personas built from real survey answers "
         "reacting. Three: every race played out 40,000 times. Four: every Sunday, a check against the polls and "
         "markets, which never moved our numbers."],
        "What would you like us to explain next?"))

    P.append(Post(
        "what-next", T_SEIS, "What's next", [(what_next, "Status from news reports, as of 11 Nov; it can change.")],
        what_next,
        "The count isn't over. As of 11 November, two Senate races are still unsettled: Mississippi is still counting "
        "its last ballots, and Alaska runs its ranked-choice count in the coming days.\n\n"
        "After certification we publish our final scorecard: every race scored against the official results, misses "
        "first.\n\n"
        f"Until then, every number we've shown is provisional. Which race are you watching?\n\n{tags()}",
        f"The count isn't over (11 Nov): Mississippi is still counting its last ballots, and Alaska runs its "
        f"ranked-choice count in the coming days. Then our final scorecard, misses first. {LABEL}.",
        "The count isn't over: as of 11 November, Mississippi is still counting its last ballots, and Alaska runs its "
        "ranked-choice count in the coming days. After certification, our final scorecard, misses first. Which race "
        "are you watching?",
        ["A timeline of three steps. Mississippi: still counting its last ballots. Alaska: runs its ranked-choice count "
         "in the coming days. After certification: our final scorecard, every race scored against the official "
         "results, misses first."],
        "Which race are you watching?"))

    P.append(Post(
        "guess-margin", T_LILAC, "Guess the margin",
        [(guess_q, "Margins: share of the two main candidates' votes. Provisional results."),
         (guess_a, "Result as of 11 Nov (AP, networks, states). Margins: share of the two main candidates' votes.")],
        None,
        "Guess the margin. North Carolina Senate: NotAPoll v1 said Cooper by 8.8 points. Where did it land?\n\n"
        "A. Cooper by 9\nB. Cooper by 14\nC. Cooper by 20\n\n"
        "Pick one in the comments, then swipe for the answer. Provisional results; the final scorecard comes after "
        f"certification.\n\nA, B or C?\n\n{tags(' #NorthCarolina')}",
        f"Guess the margin: North Carolina Senate. NotAPoll v1 said Cooper by 8.8. Was it A) 9, B) 14 or C) 20? Swipe "
        f"for the answer. {LABEL}.",
        "Guess the margin: North Carolina Senate. NotAPoll v1 said Cooper by 8.8 points. Was the result A) Cooper by "
        "9, B) by 14 or C) by 20? Swipe for the answer. A, B or C?",
        ["Guess the margin. North Carolina Senate, NotAPoll v1 said Cooper by 8.8 points. Three options: A, Cooper by "
         "9; B, Cooper by 14; C, Cooper by 20. Swipe for the answer.",
         "The answer: Cooper by 20.0. NotAPoll v1 had said 8.8: the biggest gap between v1 and a result in the 13 "
         "closest Senate races, 11.2 points."],
        "A, B or C? Pick before you swipe."))

    P.append(Post(
        "south-carolina", T_CHAM, "South Carolina",
        [(sc_chances, SRC), (sc_margin, SRC)],
        sc_chances,
        "South Carolina was NotAPoll v1's real miss. v1 gave the Democrat 17 in 100; polls alone gave 25 and the "
        "prediction markets 32. All three had the Republican ahead. The Democrat won by 4.5 points (provisional).\n\n"
        "In margin terms, v1 expected the Republican by 5.6, so it missed by 10.1 points.\n\n"
        "Why? In South Carolina, as in Maine, Kansas and Texas, the polls moved toward the Democrat after 12 October. "
        "v1's starting line stayed frozen, and its news moves were too small to follow. That's one of the things a v2 "
        "would test.\n\n"
        f"Margins are the share of the two main candidates' votes. Did you expect South Carolina?\n\n"
        f"{tags(' #SouthCarolina')}",
        f"South Carolina was NotAPoll v1's real miss: 17 in 100 for the Democrat (polls alone 25, markets 32), all "
        f"three with the Republican ahead. The Democrat won by 4.5 points (provisional); v1 expected the Republican by "
        f"5.6. {LABEL}.",
        "South Carolina was NotAPoll v1's real miss: 17 in 100 for the Democrat, with polls alone at 25 and the markets "
        "at 32, all three with the Republican ahead. The Democrat won by 4.5 points (provisional), a 10-point miss on "
        "the margin. Did you expect South Carolina?",
        ["Three bars for the chance in 100 each gave the South Carolina Democrat: NotAPoll v1 17, polls alone 25, "
         "prediction markets 32. All three had the Republican ahead. The Democrat won by 4.5 points.",
         "A number line from Republican to Democrat: NotAPoll v1 expected the Republican by 5.6; the result was the "
         "Democrat by 4.5, a 10-point miss. The polls moved toward the Democrat after 12 October while v1's start "
         "stayed frozen; the same in Maine, Kansas and Texas."],
        "Did you expect South Carolina?"))

    P.append(Post(
        "what-v2-first", T_BALL, "Your v2 pick", [(ask_card, "From our review of the results. Provisional results.")],
        ask_card,
        "If a v2 could get one thing right, which would you pick?\n\n"
        "A. Which races move most\nB. The size of the wave\nC. Turnout, on its own\n\n"
        "These are the three things our review of NotAPoll v1's results kept pointing to. Tell us in the comments: A, B "
        f"or C?\n\n{tags()}",
        f"If a v2 could get one thing right, which would you pick? A) Which races move most, B) the size of the wave, "
        f"C) turnout, on its own. A, B or C? {LABEL}.",
        "If a v2 of NotAPoll could get one thing right, which would you pick? A) Which races move most, B) the size of "
        "the wave, C) turnout, on its own. A, B or C?",
        ["If a v2 could get one thing right, which would you pick? Three options: A, which races move most; B, the "
         "size of the wave; C, turnout, on its own."],
        "A, B or C?"))
    return P



def animate(out: Path, d: date, theme, series: str, src: str, draw):
    """9:16 Reel: the slide's marks appear one after another, then hold; the cover is the last frame."""
    import imageio_ffmpeg
    from PIL import Image
    w, h, fps = 1080, 1920, 30
    s = Slide(d, "", theme, size=(w, h), series=series)
    n_text, n_patch = len(s.ax.texts), len(s.ax.patches)
    draw(s)
    s.source(src)
    if bad := s.layout_problems() + s.missing_glyphs():
        raise ValueError(f"reel layout: {bad}")
    marks = s.ax.texts[n_text:] + s.ax.patches[n_patch:] + s.ax.lines[:]
    marks = [m for m in marks if m.get_visible()]
    t0, t1, t_end = 0.6, 3.6, 7.0
    writer = imageio_ffmpeg.write_frames(str(out / "reel.mp4"), (w, h), fps=fps, codec="libx264", quality=8,
                                         macro_block_size=8, pix_fmt_in="rgb24", pix_fmt_out="yuv420p",
                                         output_params=["-movflags", "+faststart"])
    writer.send(None)
    frame = None
    for fr in range(int(t_end * fps)):
        now = fr / fps
        shown = int(len(marks) * min(1.0, max(0.0, (now - t0) / (t1 - t0))))
        for i, m in enumerate(marks):
            m.set_visible(i < shown)
        s.fig.canvas.draw()
        frame = np.asarray(s.fig.canvas.buffer_rgba())[:, :, :3]
        writer.send(np.ascontiguousarray(frame))
    writer.close()
    Image.fromarray(frame).save(out / "reel-cover.jpg", quality=92, subsampling=0)
    plt.close(s.fig)


def build(post: Post, d: date, reel: bool = True) -> tuple[Path, list[str]]:
    out = ROOT / "kits" / "daily" / f"{d.day:02d}-{post.name}"
    slides = []
    for draw, src in post.slides:
        s = Slide(d, "", post.theme, series=post.series)
        draw(s)
        s.source(src)
        slides.append(s)
    meta = {"threads_topic": "2026 Midterms", "instagram_first_comment": post.first_comment}
    try:
        problems = save(out, slides, post.caption, {"x": post.x, "threads": end(post.threads, LIMIT["threads"])},
                        post.alts, meta)
    except ValueError as e:
        return out, [str(e).split("layout:")[-1][:600]]
    if not reel and (out / "reel.mp4").exists():  # a static rebuild keeps the Reel flag
        meta["reel"] = True
        (out / "meta.json").write_text(json.dumps(meta, indent=1, ensure_ascii=False), encoding="utf-8")
    if reel and post.reel is not None:
        try:
            animate(out, d, post.theme, post.series, post.slides[0][1], post.reel)
            meta["reel"] = True
            (out / "meta.json").write_text(json.dumps(meta, indent=1, ensure_ascii=False), encoding="utf-8")
        except ValueError as e:
            problems.append(str(e)[:600])
    (out / "checks.txt").write_text("\n".join(problems) or "all rules pass", encoding="utf-8")
    return out, problems


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only")
    ap.add_argument("--set", choices=["main", "second"], default="main")
    ap.add_argument("--start", default="2026-11-11")
    ap.add_argument("--reel", action="store_true")
    a = ap.parse_args()
    start = date.fromisoformat(a.start)
    for i, post in enumerate(post_list() if a.set == "main" else second_list()):
        if a.only and post.name != a.only:
            continue
        out, problems = build(post, start + timedelta(days=i), a.reel)
        print(f"{start + timedelta(days=i):%a %d %b}", post.name, out.name, "; ".join(problems) or "all rules pass")


if __name__ == "__main__":
    main()
