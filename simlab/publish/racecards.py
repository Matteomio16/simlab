"""Race card layouts, for choosing one: python -m simlab.publish.racecards -> kits/racecards/<theme>/<layout>.jpg + boards.

Every card carries the same content: the chance in simulations, the toss-up verdict, the 7-day change, the margin range,
and the poll average, market and Cook beside our number. The numbers here are invented (EXAMPLE), not a forecast.
"""
from __future__ import annotations

from dataclasses import replace
from datetime import date

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch

from .frame import MARGIN, Slide, Theme, pt, typeset
from .themes import LAB, RISO

DAY = date(2026, 10, 12)
RACE = {"state": "Ohio", "usps": "OH", "code": "OH-SEN", "run": "a3f9c1e", "office": "Senate", "p": 0.58, "lo": -4.7, "mid": 0.9, "hi": 6.5, "poll": "D+1.5",
        "market": 0.55, "cook": "Toss-up", "change": "No meaningful change this week"}


LEFT = {"D": ("Democrat", "D"), "I": ("independent", "I")}  # the challenger to the Republican: races.json left_party


def who(r: dict) -> str:
    return LEFT[r.get("left_party", "D")][0]


def abbr(r: dict) -> str:
    return LEFT[r.get("left_party", "D")][1]


def verdict(p: float, left: str = "D") -> str:
    if 0.35 <= p <= 0.65:
        return "Toss-up"
    lean = LEFT[left][0].capitalize() if p > 0.5 else "Republican"
    return f"Likely {lean}" if max(p, 1 - p) >= 0.8 else f"Leans {lean}"


def verdict_color(t: Theme, p: float) -> str:
    return t.ai if 0.35 <= p <= 0.65 else t.dem if p > 0.65 else t.rep


def margin_txt(x: float, left: str = "D") -> str:
    return "Even" if abs(x) < 0.05 else f"{left if x > 0 else 'R'}+{abs(x):.1f}"


def span(r: dict) -> str:
    return f"{margin_txt(r['lo'], abbr(r))} to {margin_txt(r['hi'], abbr(r))}"


def pct_txt(x) -> str:
    return "n/a" if x is None else f"{x:.0%}"


def slide(t: Theme, r: dict) -> Slide:
    """The race's canvas; for an independent challenger the left side is drawn in the neutral independent colour."""
    if r.get("left_party", "D") == "I":
        t = replace(t, dem=t.ind)
    return Slide(r.get("day", DAY), r.get("kicker", "RACE CARD · EXAMPLE"), t, run=r["run"])


def source(s: Slide, r: dict, layout: str):
    s.source(r.get("source") or f"EXAMPLE: invented numbers, not a forecast. Layout: {layout}.")


def draws(r: dict, n: int = 100) -> np.ndarray:
    """n simulated margins (D positive): from the real draws when given (each side sampled evenly), else an invented
    sample with the example's 10–90% spread, centred so the Democrat wins round(p * n) of them."""
    q = (np.arange(n) + 0.5) / n
    if r.get("draws") is not None:  # exactly round(p * n) Democratic wins, so the dots match the headline number
        a = np.asarray(r["draws"], float)
        dem, rep, k = a[a > 0], a[a <= 0], round(r["p"] * n)
        if len(dem) and len(rep):
            pick = lambda x, m: np.quantile(x, (np.arange(m) + 0.5) / m) if m else np.array([])
            return np.concatenate([pick(dem, k), pick(rep, n - k)])
        return np.quantile(a, q)
    from scipy.stats import norm
    sd = (r["hi"] - r["lo"]) / 2.563
    return norm.ppf(q, sd * norm.ppf(min(max(r["p"], 0.005), 0.995)), sd)


def fit(s: Slide, txt: str, px: int, width: float, lines: int = 1, role: str = "serif", low: int = 56) -> int:
    """The largest size up to px at which txt fits in `lines` lines of `width`."""
    w = s.t.head_weight if role == "serif" else 400
    txt = txt.upper() if s.t.head_upper else txt
    while px > low:
        ls = s.wrap(txt, role, w, px, width)
        if len(ls) <= lines and max(s.pil(role, w, px).getlength(line) for line in ls) <= width:
            break
        px -= 4
    return px


def tag(s: Slide, r: dict, box: float = 190, box_h: float = 130) -> float:
    """The state of simulated voters at the top right; returns the width left for the headline."""
    from . import charts
    charts.state_voters(s, r["usps"], r["code"], r["p"], s.w - MARGIN - box, s.y + 4, box, box_h=box_h)
    return s.width - box - 40


def title(s: Slide, r: dict, width: float, px: int = 64):
    """The race name at one size on every card (smaller only when a long name needs it)."""
    txt = f"{r['state']} {r['office']}"
    s.headline(txt, px=min(px, fit(s, txt, px, width, low=44)), width=width)


def chip(s: Slide, r: dict, y: float | None = None, change: bool = True) -> float:
    """The verdict as a filled label (purple for a toss-up, blue or red otherwise), then the 7-day change."""
    t = s.t
    y = s.y if y is None else y
    label = verdict(r["p"], abbr(r)).upper()
    w = s.pil("mono", 600, 26).getlength(label) + 36
    s.ax.add_patch(FancyBboxPatch((MARGIN, y), w, 48, boxstyle="round,pad=0,rounding_size=6",
                                  color=verdict_color(t, r["p"]), lw=0, zorder=2))
    s._put(MARGIN + 18, y + 25, label, "mono", 600, 26, "#FFFFFF", va="center", zorder=3)
    if change:
        s._put(MARGIN + w + 20, y + 25, r["change"], "sans", 400, 30, t.ink2, va="center")
    s.y = y + 48
    return s.y


def strip(s: Slide, items: list[tuple[str, str]]):
    """Labelled numbers in a row under a rule; the values share one size, the largest that fits every column."""
    t = s.t
    s.rule(t.ink, after=20)
    col = s.width / len(items)
    px = 44
    while px > 26 and max(s.pil("sans", 700, px).getlength(typeset(v)) for _, v in items) > col - 28:
        px -= 2
    for i, (label, value) in enumerate(items):
        s._put(MARGIN + i * col, s.y, label.upper(), "mono", 500, 22, t.ink2, va="top")
        s._put(MARGIN + i * col, s.y + 36, value, "sans", 700, px, t.ink, va="top")
    s.y += 36 + 44 * 1.25


def benchmarks(s: Slide, r: dict, px: int = 60):
    strip(s, [("Poll average", r["poll"]), (f"Market, {abbr(r)}", pct_txt(r["market"])), ("Cook", r["cook"])])


def stamp(s: Slide, x: float, y: float, text: str, px: int = 96, rot: float = 8, color: str | None = None):
    t = s.t
    color = color or t.overprint or t.ink
    s.ax.text(x, y, typeset(text.upper()), rotation=rot, ha="center", va="center", color=color, zorder=5,
              fontproperties=s.font("hero", t.hero_weight, px), alpha=0.92,
              bbox=dict(boxstyle="square,pad=0.32", fc=t.highlight or "none", ec=color, lw=pt(7), alpha=0.92))


def split(t: Theme, r: dict = RACE) -> Slide:
    """The Split: one full-width bar cut where the simulations split, the toss-up zone marked above it."""
    s = slide(t, r)
    hw = tag(s, r)
    title = f"{r['state']} {r['office']}"
    s.headline(title, px=fit(s, title, 104, hw), width=hw)
    s.dek(f"{verdict(r['p'])}. {r['change']}.", px=36, width=hw)
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
    source(s, r, "The Split")
    return s


def ladder(t: Theme, r: dict = RACE) -> Slide:
    """Where everyone stands: one 0–100% scale with our number above it and the market below it."""
    s = slide(t, r)
    t = s.t
    hw = tag(s, r)
    title(s, r, hw)
    chip(s, r, s.y + 4)
    y0 = max(s.y, s.tag_bottom) + 56
    s._put(MARGIN, y0, f"THE {who(r).upper()}’S CHANCE OF WINNING", "mono", 500, 24, t.ink2, va="top")
    x0, w = MARGIN + 20, s.width - 40
    X = lambda p: x0 + w * p
    y = y0 + 330
    s.ax.add_patch(plt.Rectangle((X(0.35), y - 34), X(0.65) - X(0.35), 68, color=t.tossup or t.hairline, lw=0,
                                 zorder=1))
    s.ax.add_patch(FancyBboxPatch((X(0), y - 5), w, 10, boxstyle="round,pad=0,rounding_size=5", color=t.baseline,
                                  lw=0, zorder=2))
    near = lambda a, b: b is not None and abs(a - b) < 0.05
    for p, col in ((0, t.ink2), (0.35, t.ai), (0.65, t.ai), (1, t.ink2)):
        if not near(p, r["market"]):
            s._put(X(p), y + 48, f"{p:.0%}", "mono", 500, 22, col, va="top",
                   ha={0: "left", 1: "right"}.get(p, "center"))
    if not near(0.5, r["market"]):
        s._put(X(0.5), y + 48, "TOSS-UP", "mono", 600, 22, t.ai, ha="center", va="top")

    def label(x: float, lines: list[tuple[str, str, int, int, str]], top: float):
        wmax = max(s.pil(role, wt, px).getlength(typeset(txt)) for txt, role, wt, px, _ in lines)
        cx = min(max(x, MARGIN + wmax / 2), s.w - MARGIN - wmax / 2)
        for txt, role, wt, px, col in lines:
            s._put(cx, top, txt, role, wt, px, col, ha="center", va="top", zorder=4)
            top += px * 1.12

    ours = X(r["p"])
    label(ours, [("SIMULATION", "mono", 600, 24, t.ai), (f"{r['p']:.0%}", "hero", t.hero_weight, 140, t.ink)], y0 + 70)
    s.ax.plot([ours, ours], [y0 + 250, y - 22], color=t.ai, lw=pt(3), zorder=3)
    s.ax.add_patch(plt.Circle((ours, y), 22, color=t.ai, ec=t.paper, lw=pt(4), zorder=5))
    if r["market"] is not None:
        mx = X(r["market"])
        s.ax.plot([mx, mx], [y + 16, y + 92], color=t.ink, lw=pt(2), zorder=3)
        s.ax.add_patch(plt.Circle((mx, y), 15, color=t.paper, ec=t.ink, lw=pt(3), zorder=4))
        label(mx, [("MARKET", "mono", 500, 22, t.ink2), (f"{r['market']:.0%}", "sans", 700, 48, t.ink)], y + 100)
    else:
        s._put(MARGIN, y + 100, "No market price for this race", "sans", 400, 28, t.ink2, va="top")
    s.y = y + 230
    strip(s, [("Poll average", r["poll"]), ("Cook", r["cook"]),
              ("Range (80%)", span(r))])
    source(s, r, "Where everyone stands")
    return s


def futures(t: Theme, r: dict = RACE) -> Slide:
    """100 futures: a dot histogram of simulated margins, one dot per simulation, coloured by the winner."""
    s = slide(t, r)
    t = s.t
    hw = tag(s, r)
    title(s, r, hw)
    chip(s, r, s.y + 4)
    s.y = max(s.y, s.tag_bottom) + 40
    d = draws(r)
    n_dem = int((d > 0).sum())
    s.hero(MARGIN, s.y, f"{n_dem} of 100", 110)
    s.y += 110 * 1.05
    s.text(f"simulated elections won by the {who(r)}", px=32, color=t.ink2, after=0.6)
    # the axis covers the simulated margins plus Even, so lopsided races keep readable dots
    lo_m = min(-7, int(np.floor(d.min())) - 1)
    hi_m = max(7, int(np.ceil(d.max())) + 1)
    if hi_m - lo_m < 28:
        pad = (28 - (hi_m - lo_m)) / 2
        lo_m, hi_m = int(np.floor(lo_m - pad)), int(np.ceil(hi_m + pad))
    x0, w = MARGIN + 30, s.width - 60
    X = lambda m: x0 + w * (m - lo_m) / (hi_m - lo_m)
    # one-point columns either side of the Even line, so no column mixes the two parties
    bins = np.where(d > 0, np.ceil(d), np.minimum(-1, -np.ceil(-d))).astype(int)
    rows = max(np.bincount(bins - lo_m).max(), 10)
    size = min(28, 300 / rows - 2, w / (hi_m - lo_m) - 2)  # tall or wide spreads get smaller dots, same chart size
    base = s.y + 300 + 16
    counts: dict[int, int] = {}
    for m, v in sorted(zip(bins, d), key=lambda z: (abs(z[0]), -z[1])):
        k = counts.get(m, 0)
        counts[m] = k + 1
        s.ax.add_patch(plt.Circle((X(m - 0.5 if m > 0 else m + 0.5), base - size / 2 - k * (size + 2)), size / 2 - 1,
                                  color=t.dem if v > 0 else t.rep, lw=0, zorder=2))
    s.ax.plot([X(lo_m), X(hi_m)], [base + 4, base + 4], color=t.baseline, lw=pt(2))
    s.ax.plot([X(0), X(0)], [base + 4, s.y + 4], color=t.ink, lw=pt(2), zorder=3, dashes=(3, 2))
    step = 5 if hi_m - lo_m <= 32 else 10
    for m in range(-(-lo_m // step) * step, hi_m, step):
        s._put(X(m), base + 16, "Even" if m == 0 else f"{abbr(r) if m > 0 else 'R'}+{abs(m)}", "mono", 400, 22,
               t.ink2, ha="center", va="top")
    s.y = base + 76
    benchmarks(s, r)
    source(s, r, "100 futures")
    return s


def stamped(t: Theme, r: dict = RACE) -> Slide:
    """The Stamp: the state as a masthead, its simulated voters, the verdict stamped beside the number, a ledger."""
    s = slide(t, r)
    t = s.t
    s._put(MARGIN, s.y, r["office"].upper(), "mono", 600, 28, t.ink2, va="top")
    s.y += 46
    s.text(r["state"], "serif", t.head_weight, fit(s, r["state"], 136, s.width, lines=1, low=84), t.ink, leading=0.98,
           after=0.35)
    from . import charts
    top = s.y
    charts.state_voters(s, r["usps"], r["code"], r["p"], MARGIN, top, 480, n=520, box_h=230)
    rx, rw = MARGIN + 540, s.width - 540
    num = f"{r['p'] * 100:.0f}"
    s._put(rx, top - 10, num, "hero", t.hero_weight, 150, t.ink, va="top")
    s._put(rx + s.pil("hero", t.hero_weight, 150).getlength(num) + 18, top + 16, "ON 3 NOV", "mono", 600, 24, t.ai,
           va="top")
    s._put(rx, top + 150, "of 100 simulations", "sans", 400, 30, t.ink2, va="top")
    s._put(rx, top + 188, f"won by the {who(r)}", "sans", 400, 30, t.ink2, va="top")
    label = verdict(r["p"], abbr(r)).upper()
    spx = 48
    while spx > 26 and s.pil("hero", t.hero_weight, spx).getlength(label) + spx * 1.4 > rw - 20:
        spx -= 2
    sw = s.pil("hero", t.hero_weight, spx).getlength(label) + spx * 0.64
    stamp(s, rx + sw / 2 + 6, top + 290, label, px=spx, rot=-5, color=None if t.overprint else verdict_color(t, r["p"]))
    s.y = max(top + 350, s.tag_bottom + 20)
    rows = [("Range of margins (80%)", span(r)),
            ("Poll average", r["poll"]), (f"Market, {abbr(r)}", pct_txt(r["market"])), ("Cook", r["cook"]),
            ("This week", r["change"].replace(" this week", ""))]
    if r.get("today") is not None:  # the election held today: no time left for opinion to drift
        rows.insert(0, ("If the election were today", f"{r['today'] * 100:.0f} in 100"))
    gap = 12 if len(rows) <= 5 else 4
    for name, value in rows:
        s.rule(t.hairline, after=14)
        s._put(MARGIN, s.y, name, "sans", 400, 32, t.ink2, va="top")
        s._put(s.w - MARGIN, s.y, value, "mono", 600, 32, t.ink, ha="right", va="top")
        s.y += 32 * 1.3 + gap
    s.rule(t.hairline)
    source(s, r, "The Stamp")
    return s


def tape(t: Theme, r: dict = RACE) -> Slide:
    """Tale of the tape: Democrat and Republican side by side, the same rows for both, the verdict in the middle."""
    s = slide(t, r)
    hw = tag(s, r)
    title = f"{r['state']} {r['office']}"
    s.headline(title, px=fit(s, title, 104, hw), width=hw)
    mid = s.w / 2
    colw = s.width / 2 - 20
    top = max(s.y + 10, s.tag_bottom)
    for x, name, col in ((MARGIN, "DEMOCRAT", t.dem), (mid + 20, "REPUBLICAN", t.rep)):
        s.ax.add_patch(plt.Rectangle((x, top), colw, 14, color=col, lw=0))
        s._put(x, top + 34, name, "mono", 600, 28, t.ink, va="top")
    y = top + 90
    for x, v in ((MARGIN, r["p"]), (mid + 20, 1 - r["p"])):
        s.hero(x, y, f"{v * 100:.0f}", 170)
    s._put(mid, y + 180, "OF 100 SIMULATIONS WON", "mono", 500, 24, t.ink2, ha="center", va="top")
    s.ax.plot([mid, mid], [top, y + 160], color=t.hairline, lw=pt(2))
    s.y = y + 232
    rows = [("Market", pct_txt(r["market"]), pct_txt(None if r["market"] is None else 1 - r["market"])),
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
    source(s, r, "Tale of the tape")
    return s


LAYOUTS = {"1-split": split, "2-ladder": ladder, "3-futures": futures, "4-stamp": stamped, "5-tape": tape}
DEMO = {"4-stamp": RACE | {"state": "North Carolina", "usps": "NC", "code": "NC-SEN"}}


if __name__ == "__main__":
    from .directions import OUT as DIR_OUT
    from .labnotes import contact_sheet
    out = DIR_OUT.parent / "racecards"
    for theme in (RISO, LAB):
        d = out / theme.name.lower().replace(" ", "-")
        paths = [fn(theme, DEMO.get(name, RACE)).save(d / f"{name}.jpg") for name, fn in LAYOUTS.items()]
        print(contact_sheet(paths, out / f"board-{theme.name.lower().replace(' ', '-')}.jpg", scale=0.45))
