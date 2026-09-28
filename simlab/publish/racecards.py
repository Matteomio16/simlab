"""Race card layouts, for choosing one: python -m simlab.publish.racecards -> kits/racecards/<theme>/<layout>.jpg + boards.

Every card carries the same content: the chance in simulations, the toss-up verdict, the 7-day change, the margin range,
and the poll average, market and Cook beside our number. The numbers here are invented (EXAMPLE), not a forecast.
"""
from __future__ import annotations

from datetime import date

import matplotlib.pyplot as plt
import numpy as np

from .frame import MARGIN, Slide, Theme, pt, typeset
from .themes import LAB, RISO

DAY = date(2026, 10, 12)
RACE = {"state": "Ohio", "office": "Senate", "p": 0.58, "lo": -4.7, "mid": 0.9, "hi": 6.5, "poll": "D+1.5",
        "market": 0.55, "cook": "Toss-up", "change": "No meaningful change this week"}


def verdict(p: float) -> str:
    if 0.35 <= p <= 0.65:
        return "Toss-up"
    lean = "Democrat" if p > 0.5 else "Republican"
    return f"Likely {lean}" if max(p, 1 - p) >= 0.8 else f"Leans {lean}"


def margin_txt(x: float) -> str:
    return "Even" if abs(x) < 0.05 else f"{'D' if x > 0 else 'R'}+{abs(x):.1f}"


def draws(r: dict, n: int = 100) -> np.ndarray:
    """An invented sample of simulated margins matching the example's median and 10–90% range."""
    from scipy.stats import norm
    sd = (r["hi"] - r["lo"]) / 2.563
    return norm.ppf((np.arange(n) + 0.5) / n, r["mid"], sd)


def benchmarks(s: Slide, r: dict, px: int = 60):
    from . import charts
    charts.stats(s, [(f"{r['market']:.0%}", "market, Dem"), (r["poll"], "poll average"), (r["cook"], "Cook")],
                 px=px, rule=True)


def stamp(s: Slide, x: float, y: float, text: str, px: int = 96, rot: float = 8):
    t = s.t
    color = t.overprint or t.ink
    s.ax.text(x, y, typeset(text.upper()), rotation=rot, ha="center", va="center", color=color, zorder=5,
              fontproperties=s.font("hero", t.hero_weight, px), alpha=0.92,
              bbox=dict(boxstyle="square,pad=0.32", fc=t.highlight or "none", ec=color, lw=pt(7), alpha=0.92))


def split(t: Theme, r: dict = RACE) -> Slide:
    """The Split: one full-width bar cut where the simulations split, the toss-up zone marked above it."""
    s = Slide(DAY, "RACE CARD · EXAMPLE", t)
    s.headline(f"{r['state']} {r['office']}", px=104)
    s.dek(f"{verdict(r['p'])}. {r['change']}.", px=36)
    s.hero(MARGIN, s.y, f"{round(r['p'] * 10)} in 10", 180)
    s.y += 180 * 1.02
    s.text("simulations won by the Democrat", px=36, color=t.ink2, after=1.2)
    x0, w, h = MARGIN, s.width, 96
    cut = x0 + w * r["p"]
    y = s.y + 70
    lo, hi = x0 + w * 0.35, x0 + w * 0.65
    s.ax.plot([lo, lo, hi, hi], [y - 14, y - 36, y - 36, y - 14], color=t.ink2, lw=pt(2))
    s._put((lo + hi) / 2, y - 46, "TOSS-UP ZONE", "mono", 500, 22, t.ink2, ha="center", va="bottom")
    s.ax.add_patch(plt.Rectangle((x0, y), cut - x0 - 3, h, color=t.dem, lw=0, zorder=2))
    s.ax.add_patch(plt.Rectangle((cut + 3, y), x0 + w - cut - 3, h, color=t.rep, lw=0, zorder=2))
    s._put(x0 + 24, y + h / 2, f"D {r['p']:.0%}", "sans", 700, 40, "#FFFFFF", va="center", zorder=3)
    s._put(x0 + w - 24, y + h / 2, f"R {1 - r['p']:.0%}", "sans", 700, 40, "#FFFFFF", ha="right", va="center",
           zorder=3)
    s.y = y + h + 30
    s.text(f"Middle 80% of simulated margins: {margin_txt(r['lo'])} to {margin_txt(r['hi'])}", px=30,
           color=t.ink2, after=1.0)
    benchmarks(s, r)
    s.source("EXAMPLE: invented numbers, not a forecast. Layout: The Split.")
    return s


def ladder(t: Theme, r: dict = RACE) -> Slide:
    """Where everyone stands: one 0–100% scale with our number, the market and Cook placed on it."""
    s = Slide(DAY, "RACE CARD · EXAMPLE", t)
    s.headline(f"{r['state']} {r['office']}", px=104)
    s.dek("Where everyone puts it: the Democrat's chance of winning.", px=36)
    x0, w = MARGIN + 44, s.width - 88
    X = lambda p: x0 + w * p
    y = s.y + 330
    s.ax.add_patch(plt.Rectangle((X(0.35), y - 250), X(0.65) - X(0.35), 470, color=t.hairline, lw=0, zorder=0,
                                 alpha=0.8))
    s._put(X(0.5), y - 260, "TOSS-UP", "mono", 600, 28, t.ink2, ha="center", va="bottom")
    s.ax.plot([X(0), X(1)], [y, y], color=t.ink, lw=pt(3), zorder=2, solid_capstyle="butt")
    for p in (0, 0.25, 0.5, 0.75, 1):
        s.ax.plot([X(p), X(p)], [y - 10, y + 10], color=t.ink, lw=pt(2), zorder=2)
        s._put(X(p), y + 20, f"{p:.0%}", "mono", 400, 26, t.ink2, ha="center", va="top")
    # our number above the line, large
    s.ax.plot([X(r["p"]), X(r["p"])], [y, y - 150], color=t.ai, lw=pt(3), zorder=3)
    s.ax.add_patch(plt.Circle((X(r["p"]), y), 26, color=t.ai, zorder=4))
    s._put(X(r["p"]) + 16, y - 236, f"{r['p']:.0%}", "hero", t.hero_weight, 110, t.ink, va="top", zorder=4)
    s._put(X(r["p"]) + 16, y - 118, "NotAPoll", "mono", 600, 30, t.ink, va="top", zorder=4)
    # market and Cook below the line
    s.ax.plot([X(r["market"]), X(r["market"])], [y, y + 110], color=t.data, lw=pt(2), zorder=3)
    s.ax.add_patch(plt.Circle((X(r["market"]), y), 17, color=t.paper, ec=t.data, lw=pt(3), zorder=4))
    s._put(X(r["market"]) - 14, y + 70, f"Market {r['market']:.0%}", "sans", 600, 36, t.ink, ha="right",
           va="top", zorder=4)
    s._put(X(0.5), y + 140, f"Cook: {r['cook']}", "sans", 600, 36, t.ink, ha="center", va="top", zorder=4)
    s.y = y + 230
    s.text(f"{verdict(r['p'])}. {r['change']}. Poll average {r['poll']}; middle 80% of simulated margins "
           f"{margin_txt(r['lo'])} to {margin_txt(r['hi'])}.", px=32, color=t.ink2)
    s.source("EXAMPLE: invented numbers, not a forecast. Layout: Where everyone stands.")
    return s


def futures(t: Theme, r: dict = RACE) -> Slide:
    """100 futures: a dot histogram of simulated margins, one dot per simulation, coloured by the winner."""
    s = Slide(DAY, "RACE CARD · EXAMPLE", t)
    s.headline(f"{r['state']} {r['office']}", px=88)
    d = draws(r)
    n_dem = int((d > 0).sum())
    s.hero(MARGIN, s.y, f"{n_dem} of 100", 124)
    s.y += 124 * 1.02
    s.text("simulated futures won by the Democrat", px=36, color=t.ink2, after=0.8)
    lim, size = 14, 28
    x0, w = MARGIN + 30, s.width - 60
    X = lambda m: x0 + w * (m + lim) / (2 * lim)
    bins = np.clip(np.round(d), -lim + 1, lim - 1).astype(int)
    base = s.y + 10 * (size + 2) + 10
    counts: dict[int, int] = {}
    for m, v in sorted(zip(bins, d), key=lambda z: (abs(z[0]), -z[1])):
        k = counts.get(m, 0)
        counts[m] = k + 1
        s.ax.add_patch(plt.Circle((X(m), base - size / 2 - k * (size + 2)), size / 2 - 1,
                                  color=t.dem if v > 0 else t.rep, lw=0, zorder=2))
    s.ax.plot([X(-lim), X(lim)], [base + 4, base + 4], color=t.baseline, lw=pt(2))
    s.ax.plot([X(0), X(0)], [base + 4, s.y - 10], color=t.ink, lw=pt(2), zorder=1)
    for m in (-10, -5, 0, 5, 10):
        s._put(X(m), base + 16, margin_txt(m), "mono", 400, 22, t.ink2, ha="center", va="top")
    s.y = base + 64
    s.text(f"{verdict(r['p'])}. Middle 80%: {margin_txt(r['lo'])} to {margin_txt(r['hi'])}. {r['change']}.",
           px=30, color=t.ink2, after=0.8)
    benchmarks(s, r, px=56)
    s.source("EXAMPLE: invented numbers, not a forecast. Layout: 100 futures.")
    return s


def stamped(t: Theme, r: dict = RACE) -> Slide:
    """The Stamp: the state as a masthead, the verdict stamped across it, a ledger of every number."""
    r = r | {"state": "North Carolina"}
    s = Slide(DAY, "RACE CARD · EXAMPLE", t)
    s._put(MARGIN, s.y, "SENATE", "mono", 600, 30, t.ink2, va="top")
    s.y += 50
    s.text(r["state"], "serif", t.head_weight, 136, t.ink, leading=0.98, after=0.2)
    stamp(s, s.w - MARGIN - 200, s.y + 40, verdict(r["p"]), px=76, rot=-6)
    s.y += 120
    rows = [("Simulations won", f"D {r['p'] * 100:.0f}  ·  R {(1 - r['p']) * 100:.0f}"),
            ("Middle 80% of margins", f"{margin_txt(r['lo'])} to {margin_txt(r['hi'])}"),
            ("Poll average", r["poll"]), ("Market (Dem)", f"{r['market']:.0%}"), ("Cook", r["cook"]),
            ("This week", "No meaningful change")]
    for label, value in rows:
        s.rule(t.hairline, after=14)
        s._put(MARGIN, s.y, label, "sans", 400, 34, t.ink2, va="top")
        s._put(s.w - MARGIN, s.y, value, "mono", 600, 34, t.ink, ha="right", va="top")
        s.y += 34 * 1.3 + 12
    s.rule(t.hairline)
    s.source("EXAMPLE: invented numbers, not a forecast. Layout: The Stamp.")
    return s


def tape(t: Theme, r: dict = RACE) -> Slide:
    """Tale of the tape: Democrat and Republican side by side, the same rows for both, the verdict in the middle."""
    s = Slide(DAY, "RACE CARD · EXAMPLE", t)
    s.headline(f"{r['state']} {r['office']}", px=104)
    mid = s.w / 2
    colw = s.width / 2 - 20
    top = s.y + 10
    for x, name, col in ((MARGIN, "DEMOCRAT", t.dem), (mid + 20, "REPUBLICAN", t.rep)):
        s.ax.add_patch(plt.Rectangle((x, top), colw, 14, color=col, lw=0))
        s._put(x, top + 34, name, "mono", 600, 28, t.ink, va="top")
    y = top + 90
    for x, v in ((MARGIN, r["p"]), (mid + 20, 1 - r["p"])):
        s.hero(x, y, f"{v * 100:.0f}", 200)
    s._put(mid, y + 210, "OF 100 SIMULATIONS WON", "mono", 500, 24, t.ink2, ha="center", va="top")
    s.ax.plot([mid, mid], [top, y + 190], color=t.hairline, lw=pt(2))
    s.y = y + 270
    rows = [("Market", f"{r['market']:.0%}", f"{1 - r['market']:.0%}"),
            ("Poll average", r["poll"].replace("D", "") + " lead" if r["poll"].startswith("D") else "", ""),
            ("Best 1-in-10 outcome", margin_txt(r["hi"]), margin_txt(r["lo"]))]
    for label, a, b in rows:
        s.rule(t.hairline, after=16)
        s._put(MARGIN, s.y, a, "sans", 700, 38, t.ink, va="top")
        s._put(mid, s.y + 4, label, "mono", 500, 24, t.ink2, ha="center", va="top")
        s._put(s.w - MARGIN, s.y, b, "sans", 700, 38, t.ink, ha="right", va="top")
        s.y += 38 * 1.3 + 16
    s.rule(t.hairline, after=40)
    stamp(s, mid, s.y + 50, f"{r['cook']} · Cook agrees" if r["cook"] == verdict(r["p"]) else verdict(r["p"]),
          px=52, rot=0)
    s.y += 110
    s.source("EXAMPLE: invented numbers, not a forecast. Layout: Tale of the tape.")
    return s


LAYOUTS = {"1-split": split, "2-ladder": ladder, "3-futures": futures, "4-stamp": stamped, "5-tape": tape}


if __name__ == "__main__":
    from .directions import OUT as DIR_OUT
    from .labnotes import contact_sheet
    out = DIR_OUT.parent / "racecards"
    for theme in (RISO, LAB):
        d = out / theme.name.lower().replace(" ", "-")
        paths = [fn(theme).save(d / f"{name}.jpg") for name, fn in LAYOUTS.items()]
        print(contact_sheet(paths, out / f"board-{theme.name.lower().replace(' ', '-')}.jpg", scale=0.45))
