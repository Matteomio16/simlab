"""Closure post 1, "Our report card" (docs/results-2026.md §7; Matteo's yes to the series, 6 Nov). Every number comes
from docs/results-2026.md and is provisional: AK and MS uncalled, the House still counting, nothing certified.

    python -m simlab.publish.reportcard [--reel]

Framing (Matteo, 6 Nov): never "the polls beat us", never dunk on polls, no claim of race-level skill.
"""
from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from .final import ROOT, animate as _animate, big, save
from .frame import DISCLAIMER, LABEL, MARGIN, Slide, pt
from .launch import LIMIT
from .pollread import end
from . import racecards as rc
from .themes import LAB

DAY = date(2026, 11, 7)
SERIES = "Our report card"
SRC = "Provisional results (AP, networks, states; 6 Nov). Final scorecard after certification."
PARTY = {"D": LAB.dem, "R": LAB.rep, "I": LAB.ai}

# docs/results-2026.md §3: our final 3 Nov chance for the left candidate, our margin, the actual margin (left minus R)
RACES = [  # state, our chance for the left candidate, our margin, actual margin, left party
    ("Texas", 61, 1.3, 12.2, "D"), ("Ohio", 58, 1.0, 5.0, "D"), ("Maine", 63, 1.7, 6.9, "D"),
    ("Michigan", 83, 4.8, 7.1, "D"), ("Minnesota", 86, 5.4, 10.4, "D"), ("North Carolina", 95, 8.8, 20.0, "D"),
    ("New Hampshire", 94, 8.1, 14.0, "D"), ("Nebraska", 21, -4.6, -7.2, "I"), ("Florida", 13, -5.8, -2.9, "D"),
    ("Louisiana", 7, -9.6, -1.8, "D"), ("Iowa", 43, -0.9, 4.2, "D"), ("Kansas", 43, -0.9, 5.2, "D"),
    ("South Carolina", 17, -5.6, 4.5, "D"),
]


def winner(r):
    """(party that won, our chance in 100 for that winner, right call?)"""
    state, p, ours, actual, left = r
    won = left if actual > 0 else "R"
    chance = p if actual > 0 else 100 - p
    return won, chance, chance > 50


def mark(s: Slide, x: float, y: float, ok: bool, size: float = 26):
    """A drawn tick (purple) or cross (red): no glyphs, so it renders the same in every font."""
    c = LAB.ai if ok else LAB.rep
    kw = dict(color=c, lw=pt(5), solid_capstyle="round", zorder=4)
    if ok:
        s.ax.plot([x, x + size * 0.38, x + size], [y, y + size * 0.4, y - size * 0.45], **kw)
    else:
        h = size * 0.42
        s.ax.plot([x + 2, x + 2 * h], [y - h, y + h], **kw)
        s.ax.plot([x + 2, x + 2 * h], [y + h, y - h], **kw)


def cover(s: Slide):
    s.headline("Our report card: both chambers called right.", px=76)
    s.dek("Our final forecast on 3 November, and what voters decided.", px=32)
    y = big(s, [("59", "in 100: our chance Democrats win the Senate", LAB.dem),
                ("63", "in 100: our chance Democrats win the House", LAB.dem)], s.y + 20)
    for label, res in [("Senate", "Democrats at 54 seats, with Alaska and Mississippi still counting."),
                       ("House", "Democrats won the majority, with about 25 seats still counting.")]:
        mark(s, MARGIN + 4, y + 20, True, 30)
        s._put(MARGIN + 56, y + 20, label, "sans", 700, 32, LAB.ink, va="center")
        s.y = y + 2
        s.text(res, "sans", 500, 30, LAB.ink2, x=MARGIN + 210, width=s.width - 210, after=0.4)
        y = s.y + 24
    s.y = y
    return s


def card(s: Slide, rows=RACES, step: float = 45):
    s.headline("30 of 33 Senate races called right.", px=68)
    s.dek("The closest, with the chance we gave the candidate who won.", px=28)
    top = s.y + 10
    xs, xc, xr = MARGIN + 60, MARGIN + 470, s.w - MARGIN
    for head, x, ha in [("RACE", xs, "left"), ("OUR CHANCE FOR THE WINNER", xc, "left"), ("RESULT", xr, "right")]:
        s._put(x, top, head, "mono", 600, 20, LAB.ink2, ha=ha, va="top")
    y = top + 52
    for r in rows:
        won, chance, ok = winner(r)
        mark(s, MARGIN + 4, y + 2, ok, 24)
        s._put(xs, y, r[0], "sans", 600, 30, LAB.ink, va="center")
        name = {"D": "Democrat", "R": "Republican", "I": "Independent"}[won]
        s._put(xc, y, f"{name} {chance} in 100", "sans", 700, 28, PARTY[won], va="center")
        s._put(xr, y, f"{won} +{abs(r[3]):.1f}", "mono", 600, 26, LAB.ink, ha="right", va="center")
        y += step
    s.y = y + 4
    s.text("The other 20 called races: all right.", "sans", 500, 26, LAB.ink2, after=0.3)
    s.text("Margins: share of the two main candidates' votes.", "sans", 400, 22, LAB.muted)
    return s


def wave(s: Slide):
    s.headline("Where we fell short: the size of the wave.", px=64)
    s.dek("NotAPoll v1's expected margin against the result, in points.", px=28)
    top, x0, x1 = s.y + 34, MARGIN + 250, s.w - MARGIN - 10
    lim = 22
    X = lambda v: x0 + (x1 - x0) * (v + lim) / (2 * lim)
    rows = sorted(RACES, key=lambda r: r[3])
    step = 38
    s.ax.plot([X(0), X(0)], [top - 10, top + step * len(rows)], color=LAB.baseline, lw=pt(2), zorder=1)
    s._put(X(0), top - 18, "even", "mono", 500, 20, LAB.ink2, ha="center", va="bottom")
    for i, r in enumerate(rows):
        y = top + 16 + i * step
        s._put(MARGIN, y, r[0], "sans", 600, 26, LAB.ink, va="center")
        s.ax.annotate("", (X(r[3]), y), (X(r[2]), y), arrowprops=dict(arrowstyle="-|>", color=LAB.ink2, lw=pt(2.5),
                      mutation_scale=pt(18), shrinkA=0, shrinkB=7), zorder=2)
        s.ax.scatter([X(r[2])], [y], s=pt(18) ** 2, color=LAB.ai, zorder=3)
        s.ax.scatter([X(r[3])], [y], s=pt(18) ** 2, facecolor=LAB.paper, edgecolor=LAB.ink, lw=pt(3), zorder=3)
    y = top + 16 + len(rows) * step
    s._put(X(-lim), y, "← Republican", "sans", 600, 22, LAB.rep, va="top")
    s._put(X(lim), y, "Democrat →", "sans", 600, 22, LAB.dem, ha="right", va="top")
    s.y = y + 44
    s.ax.scatter([MARGIN + 12], [s.y + 14], s=pt(18) ** 2, color=LAB.ai)
    s._put(MARGIN + 34, s.y + 14, "v1's expected margin", "sans", 500, 24, LAB.ink2, va="center")
    s.ax.scatter([MARGIN + 330], [s.y + 14], s=pt(18) ** 2, facecolor=LAB.paper, edgecolor=LAB.ink, lw=pt(3))
    s._put(MARGIN + 352, s.y + 14, "the result", "sans", 500, 24, LAB.ink2, va="center")
    s.y += 56
    s.text("On average, Democrats beat our margins by about 5 points, and by more in the House.", "sans", 600, 28,
           LAB.ink, after=0.5)
    return s


# Every Senate race in the final 3 Nov run: our chance for the left candidate, the left party (forecast.json); the
# winner from docs/results-2026.md §3 (the other 20 called races went to our favorite; AK and MS uncalled).
FINAL = {"AK": (48, "D"), "AL": (1, "D"), "AR": (0, "D"), "CO": (100, "D"), "DE": (100, "D"), "FL": (13, "D"),
         "GA": (97, "D"), "IA": (43, "D"), "ID": (0, "I"), "IL": (99, "D"), "KS": (43, "D"), "KY": (2, "D"),
         "LA": (7, "D"), "MA": (100, "D"), "ME": (63, "D"), "MI": (83, "D"), "MN": (86, "D"), "MS": (6, "D"),
         "MT": (1, "I"), "NC": (95, "D"), "NE": (21, "I"), "NH": (94, "D"), "NJ": (98, "D"), "NM": (99, "D"),
         "OH": (58, "D"), "OK": (0, "D"), "OR": (100, "D"), "RI": (100, "D"), "SC": (17, "D"), "SD": (1, "I"),
         "TN": (0, "D"), "TX": (61, "D"), "VA": (100, "D"), "WV": (0, "D"), "WY": (0, "D")}
MISSED = {"IA", "KS", "SC"}
COUNTING = {"AK", "MS"}


def winner_of(k: str) -> str:
    p, left = FINAL[k]
    if k in MISSED:
        return left
    return left if p > 50 else "R"


def report(s: Slide):
    """The cover: a school report card, one row per subject."""
    from matplotlib.patches import FancyBboxPatch
    from .specials import mix
    s.headline("NotAPoll v1's report card", px=76)
    s.dek("The 2026 midterms: NotAPoll v1's final forecast on 3 November against what voters decided.", px=30)
    x0, w, top = MARGIN, s.width, s.y + 16
    h = 576
    s.ax.add_patch(FancyBboxPatch((x0 + 12, top + 12), w, h, boxstyle="round,pad=0,rounding_size=18",
                                  fc=LAB.accent, lw=0, zorder=1))
    s.ax.add_patch(FancyBboxPatch((x0, top), w, h, boxstyle="round,pad=0,rounding_size=18", fc="#FFFFFF",
                                  ec=LAB.hairline, lw=pt(2), zorder=2))
    s.ax.add_patch(FancyBboxPatch((x0, top), w, 86, boxstyle="round,pad=0,rounding_size=18", fc=LAB.strip_bg, lw=0,
                                  zorder=3))
    s.ax.add_patch(plt.Rectangle((x0, top + 50), w, 36, fc=LAB.strip_bg, lw=0, zorder=3))
    s._put(x0 + 34, top + 43, "REPORT CARD · NOTAPOLL V1", "sans", 700, 28, LAB.strip_fg, va="center", zorder=4)
    s._put(x0 + w - 34, top + 43, "2026 MIDTERMS", "mono", 600, 22, LAB.strip_fg, ha="right", va="center", zorder=4)
    cols = [("SUBJECT", x0 + 34, "left"), ("OUR CALL", x0 + 330, "left"), ("RESULT", x0 + 590, "left"),
            ("MARK", x0 + w - 34, "right")]
    y = top + 122
    for head, x, ha in cols:
        s._put(x, y, head, "mono", 600, 19, LAB.ink2, ha=ha, va="center", zorder=4)
    rows = [("Senate control", "Dem 59 in 100", "Dem, 54 seats", "tick"),
            ("House control", "Dem 63 in 100", "Dem majority", "tick"),
            ("Senate races", "33 called", "30 right", "30/33"),
            ("Size of the wave", "Too small", "5 pts bigger", "Needs work")]
    y += 36
    for subj, call, res, m in rows:
        s.ax.plot([x0 + 24, x0 + w - 24], [y, y], color=LAB.hairline, lw=pt(1.5), zorder=3)
        yc = y + 48
        s._put(x0 + 34, yc, subj, "sans", 700, 28, LAB.ink, va="center", zorder=4)
        s._put(x0 + 330, yc, call, "sans", 500, 26, LAB.ink2, va="center", zorder=4)
        s._put(x0 + 590, yc, res, "sans", 500, 26, LAB.ink2, va="center", zorder=4)
        if m == "tick":
            mark(s, x0 + w - 76, yc + 2, True, 40)
        elif m == "Needs work":
            s._put(x0 + w - 34, yc, m, "sans", 700, 26, LAB.rep, ha="right", va="center", zorder=4)
        else:
            s._put(x0 + w - 34, yc, m, "hero", 700, 40, LAB.ai, ha="right", va="center", zorder=4)
        y += 96
    s.y = top + h + 34
    rc.stamp(s, x0 + w - 150, top + h + 30, "Provisional", px=34, rot=-7, color=LAB.rep)
    s.note("Right direction, too timid on the size. That's v1.", width=640, px=30)


def results_map(s: Slide, top: float, size: float = 66, gap: float = 7, label_px: int = 22) -> tuple[float, list]:
    """Every Senate race coloured by who won; on each tile the chance we gave the winner. Misses carry a cross."""
    from matplotlib.patches import FancyBboxPatch
    from .specials import TILE
    x0 = MARGIN + (s.width - 12 * (size + gap) + gap) / 2
    tiles = []
    order = sorted(TILE, key=lambda k: (k not in FINAL, k in MISSED or k in COUNTING, TILE[k]))
    for k in order:
        row, c = TILE[k]
        x, y = x0 + c * (size + gap), top + row * (size + gap)
        n0, t0, l0 = len(s.ax.patches), len(s.ax.texts), len(s.ax.lines)
        box = dict(boxstyle="round,pad=0,rounding_size=8", zorder=2)
        if k in COUNTING:
            s.ax.add_patch(FancyBboxPatch((x, y), size, size, fc=LAB.paper, ec=LAB.ink2, lw=pt(2.5),
                                          linestyle=(0, (3, 2)), **box))
            s._put(x + size / 2, y + size * 0.38, k, "sans", 700, label_px, LAB.ink, ha="center", va="center", zorder=4)
            s._put(x + size / 2, y + size * 0.7, "count", "mono", 500, label_px - 7, LAB.ink2, ha="center",
                   va="center", zorder=4)
        elif k in FINAL:
            p, left = FINAL[k]
            won = winner_of(k)
            chance = p if won == left else 100 - p
            col = LAB.dem if won in ("D", "I") else LAB.rep
            s.ax.add_patch(FancyBboxPatch((x, y), size, size, fc=col, lw=0, **box))
            s._put(x + size / 2, y + size * 0.36, k, "sans", 700, label_px, "#FFFFFF", ha="center", va="center",
                   zorder=4)
            s._put(x + size / 2, y + size * 0.68, str(chance), "mono", 600, label_px - 5, "#FFFFFF", ha="center",
                   va="center", zorder=4)
            if k in MISSED:
                cx, cy = x + size - 6, y + 6
                s.ax.add_patch(plt.Circle((cx, cy), size * 0.24, fc="#FFFFFF", ec=LAB.rep, lw=pt(3), zorder=5))
                hh = size * 0.11
                for a, b in (((cx - hh, cy - hh), (cx + hh, cy + hh)), ((cx - hh, cy + hh), (cx + hh, cy - hh))):
                    s.ax.plot([a[0], b[0]], [a[1], b[1]], color=LAB.rep, lw=pt(4), solid_capstyle="round", zorder=6)
        else:
            s.ax.add_patch(FancyBboxPatch((x, y), size, size, fill=False, ec=LAB.hairline, lw=pt(1.5), **box))
            s._put(x + size / 2, y + size / 2, k, "sans", 400, label_px - 4, LAB.muted, ha="center", va="center",
                   zorder=4)
        tiles.append(s.ax.patches[n0:] + s.ax.texts[t0:] + s.ax.lines[l0:])
    return top + 8 * (size + gap), tiles


def map_slide(s: Slide, size: float = 66):
    s.headline("30 of 33 Senate races called right.", px=68)
    s.dek("Who won each state, and the chance in 100 NotAPoll v1 gave the winner.", px=28)
    s.y, _ = results_map(s, s.y + 20, size)
    s.y += 8
    x = MARGIN
    for col, lab, hollow in [(LAB.dem, "Democrat won", False), (LAB.rep, "Republican won", False),
                             (LAB.ink2, "still counting", True)]:
        s.ax.add_patch(plt.Rectangle((x, s.y + 4), 22, 22, fc=LAB.paper if hollow else col, ec=col,
                                     lw=pt(2) if hollow else 0, zorder=3))
        s._put(x + 32, s.y + 15, lab, "sans", 600, 22, LAB.ink, va="center")
        x += 32 + len(lab) * 11.5 + 34
    s.y += 50
    s.text("Missed: Iowa and Kansas, near coin flips at 43 in 100, and South Carolina, where we gave the Democrat 17.",
           "sans", 600, 26, LAB.ink, after=0.3)


def build(reel: bool = False) -> tuple[Path, list[str]]:
    a, b, c = (Slide(DAY, "", LAB, series=SERIES) for _ in range(3))
    report(a)
    map_slide(b)
    wave(c)
    for s in (a, b, c):
        s.source(SRC)

    caption = (
        "Our report card, three days after the election. These are provisional results; the final scorecard comes "
        "after certification.\n\n"
        "Both chambers right. We gave Democrats the Senate in 59 of every 100 simulated elections, and they're at 54 "
        "seats, with Alaska and Mississippi still counting. We gave them the House in 63 of 100, and Democrats won the majority, with about 25 seats still counting.\n\n"
        "30 of the 33 called Senate races right. That includes Texas, where we had Talarico favoured while Cook "
        "called it a toss-up, and Ohio, Maine, Michigan, Minnesota, North Carolina and New Hampshire, plus the "
        "Republican holds in Nebraska, Florida and Louisiana.\n\n"
        "Three misses. Iowa and Kansas we had close, Democrats winning 43 in 100 in each, and both went the other "
        "way. South Carolina was the real miss: we gave the Democrat 17 in 100.\n\n"
        "Where we fell short: the size of the wave. On average, Democrats beat our margins by about 5 points in the "
        "Senate, and by more in the House.\n\n"
        "Next: how we compare with the markets, the forecasters and "
        "our own polls-alone twin.\n\n"
        "Which call surprised you most?\n\n"
        f"#midterms2026 #elections\n\n{DISCLAIMER}")
    x = ("Our report card (provisional): both chambers right, 30 of 33 called Senate races; missed Iowa, Kansas "
         "and South Carolina. We underestimated the wave: on average Democrats beat our margins by about 5 points. "
         f"Final scorecard after certification. {LABEL}.")
    threads = ("Our report card, provisional until certification: we called both chambers right, and 30 of 33 "
               "called Senate races, Texas included, where we had Talarico favoured while Cook said toss-up. We "
               "missed Iowa and Kansas, both near coin flips, and South Carolina. And we underestimated the size of "
               "the wave: on average, Democrats beat our margins by about 5 points. Which call surprised you most?")
    posts = {"x": x, "threads": end(threads, LIMIT["threads"])}
    alts = ["Our report card, drawn as a school report: Senate control, our call Democrats 59 in 100, result Democrats at 54 seats, ticked; House control, 63 in 100, Democratic majority, ticked; Senate races, 30 of 33 right; size of the wave, needs work. Both chambers called right: we gave Democrats the Senate in 59 of 100 simulated "
            "elections and they are at 54 seats; the House in 63 of 100 and they won the majority, with about 25 seats still counting. "
            "Provisional results.",
            "30 of 33 Senate races called right. A tile map of the 35 Senate races, each coloured by who won, with "
            "the chance we gave the winner: " + "; ".join(f"{r[0]} {winner(r)[1]}" for r in RACES) + ". Iowa, "
            "Kansas and South Carolina carry a cross: we called them the other way. Alaska and Mississippi: still "
            "counting.",
            "Where we fell short: our expected margin against the result in 13 Senate races, with arrows; most "
            "results landed to the Democratic side of our number. Democrats beat our margins by about 5 points."]
    meta = {"threads_topic": "2026 Midterms", "instagram_first_comment": "Which call surprised you most?"}
    out = ROOT / "kits" / "daily" / f"{DAY.day:02d}-report-card"
    problems = save(out, [a, b, c], caption, posts, alts, meta)
    if reel:
        import simlab.publish.final as fin
        fin.SERIES = SERIES  # the Reel's strip names this series
        _animate(out, DAY, SRC, lambda s: (s.headline("30 of 33 Senate races called right.", px=72),
                                           results_map(s, s.y + 60, 72, 8, 24)))
        meta["reel"] = True
        (out / "meta.json").write_text(json.dumps(meta, indent=1, ensure_ascii=False), encoding="utf-8")
    (out / "checks.txt").write_text("\n".join(problems) or "all rules pass", encoding="utf-8")
    return out, problems


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reel", action="store_true")
    out, problems = build(ap.parse_args().reel)
    print(out, "; ".join(problems) or "all rules pass")


if __name__ == "__main__":
    main()
