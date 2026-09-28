"""Chart pieces drawn on a Slide, in its theme: stat tiles, rows, bars, dumbbells, range bars, dot grids.
Marks carry colour; text stays in ink."""
from __future__ import annotations

import matplotlib.pyplot as plt

from .frame import MARGIN, Slide, pt, typeset


def stats(s: Slide, items: list[tuple[str, str]], px: int = 120, rule: bool = False):
    """A row of big numbers with a label under each; the numbers shrink together until each fits its column."""
    t = s.t
    if rule:
        s.rule(t.ink, after=40)
    col = s.width / len(items)
    while px > 40 and max(s.pil("hero", t.hero_weight, px).getlength(typeset(v)) for v, _ in items) > col - 40:
        px -= 4
    for i, (value, label) in enumerate(items):
        x = MARGIN + i * col
        s.hero(x, s.y, value, px)
        s._put(x, s.y + px * 1.05, label, "sans", 400, 34, t.ink2, va="top")
    s.y += px * 1.05 + 34 * 1.3 + 40
    return s


def stats_height(px: int = 120, rule: bool = False) -> float:
    return px * 1.05 + 34 * 1.3 + (40 if rule else 0)


def rows(s: Slide, items: list[tuple[str, str, str]], label_w: float = 380):
    """Hairline-separated rows: a question on the left, the answer and its evidence on the right."""
    t = s.t
    x2 = MARGIN + label_w + 32
    w2 = s.width - label_w - 32
    for question, answer, evidence in items:
        s.rule(t.hairline, after=22)
        top = s.y
        q = s.wrap(question, "sans", 600, 32, label_w)
        for i, line in enumerate(q):
            s._put(MARGIN, top + i * 40, line, "sans", 600, 32, t.ink2, va="top")
        s._put(x2, top, answer.upper() if t.head_upper else answer, "serif", t.head_weight, 44, t.ink, va="top")
        ev = s.wrap(evidence, "sans", 400, 30, w2)
        for i, line in enumerate(ev):
            s._put(x2, top + 58 + i * 38, line, "sans", 400, 30, t.ink2, va="top")
        s.y = max(top + len(q) * 40, top + 58 + len(ev) * 38) + 22
    s.rule(t.hairline, after=30)
    return s


def hbars(s: Slide, items: list[tuple[str, float, str]], xmax: float, fmt, height: float | None = None,
          label_w: float = 300, title: str | None = None):
    """Horizontal bars from one baseline; category names on the left, values at the tips."""
    t = s.t
    if title:
        s.text(title, "sans", 600, 32, t.ink, after=0.5)
    height = height or 92 * len(items)
    ax = s.chart(height, left=label_w, right=180)
    ax.set_xlim(0, xmax)
    ax.set_ylim(len(items) - 0.5, -0.5)
    ax.set_yticks([])
    ax.set_xticks([])
    ax.spines["bottom"].set_visible(False)
    ax.axvline(0, color=t.baseline, lw=pt(2))
    thick = 36 / (height / len(items))
    for i, (name, v, color) in enumerate(items):
        ax.barh(i, v, height=thick, color=color, lw=0)
        ax.text(v, i, typeset(f"  {fmt(v)}"), va="center", ha="left", color=t.ink, fontproperties=s.font("sans", 600, 36))
        ax.text(-xmax * 0.03, i, typeset(name), va="center", ha="right", color=t.ink,
                fontproperties=s.font("sans", 400, 32))
    s.y += 24
    return ax


def dumbbell(s: Slide, items: list[tuple[str, float, float]], lim: float, height: float, left_label: str,
             right_label: str, fmt, label_w: float = 250):
    """One row per item: hollow dot = before, filled dot = after, joined by a line; zero line in the middle."""
    t = s.t
    ax = s.chart(height, left=label_w, right=48)
    ax.set_xlim(-lim, lim)
    ax.set_ylim(len(items) - 0.5, -0.5)
    ax.set_yticks([])
    ticks = [-lim, -lim / 2, 0, lim / 2, lim]
    ax.set_xticks(ticks, [typeset(fmt(x)) for x in ticks])
    for lab in ax.get_xticklabels():
        lab.set_fontproperties(s.font("sans", 400, 28))
    ax.axvline(0, color=t.baseline, lw=pt(2), zorder=1)
    for x in ticks:
        if x:
            ax.axvline(x, color=t.hairline, lw=pt(1), zorder=0)
    for i, (name, before, after) in enumerate(items):
        ax.plot([before, after], [i, i], color=t.data, lw=pt(3), zorder=2, solid_capstyle="round")
        ax.scatter([before], [i], s=pt(26) ** 2, facecolor=t.paper, edgecolor=t.data, linewidth=pt(3), zorder=3)
        ax.scatter([after], [i], s=pt(26) ** 2, facecolor=t.ai, edgecolor=t.paper, linewidth=pt(3), zorder=4)
        ax.text(-lim * 1.04, i, typeset(name), va="center", ha="right", color=t.ink,
                fontproperties=s.font("sans", 400, 32))
    s.y += 56
    x0, x1 = MARGIN + label_w, s.w - MARGIN
    arrow = s.pil("mono", 400, 28).getlength("← ")
    s._put(x0, s.y, "← ", "mono", 400, 28, t.ink2, va="top")
    s._put(x0 + arrow, s.y, left_label, "sans", 400, 28, t.ink2, va="top")
    s._put(x1, s.y, " →", "mono", 400, 28, t.ink2, ha="right", va="top")
    s._put(x1 - arrow, s.y, right_label, "sans", 400, 28, t.ink2, ha="right", va="top")
    s.y += 60
    return ax


def legend_dots(s: Slide, items: list[tuple[str, str, bool]]):
    """Dot keys in one line: (label, colour, filled)."""
    t, x = s.t, MARGIN
    for label, color, filled in items:
        s.ax.scatter([x + 13], [s.y + 16], s=pt(26) ** 2, facecolor=color if filled else t.paper,
                     edgecolor=color, linewidth=pt(3), zorder=4)
        s._put(x + 40, s.y + 16, label, "sans", 400, 30, t.ink2, va="center")
        x += 40 + s.pil("sans", 400, 30).getlength(typeset(label)) + 48
    s.y += 56
    return s


def margin_range(s: Slide, lo: float, mid: float, hi: float, lim: float = 15, height: float = 150):
    """The 10–90% range of the simulated margin (D positive), zero line in the middle, median marked."""
    t = s.t
    ax = s.chart(height, left=44, right=44)
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-1, 1)
    ax.set_yticks([])
    ticks = [-lim, -lim / 2, 0, lim / 2, lim]
    ax.set_xticks(ticks, [("R+" if x < 0 else "D+" if x > 0 else "") + (f"{abs(x):.0f}" if x else "Even")
                          for x in ticks])
    for lab in ax.get_xticklabels():
        lab.set_fontproperties(s.font("sans", 400, 28))
    ax.barh(0, min(hi, 0) - lo, left=lo, height=0.7, color=t.rep, alpha=0.9, lw=0)
    ax.barh(0, hi - max(lo, 0), left=max(lo, 0), height=0.7, color=t.dem, alpha=0.9, lw=0)
    ax.axvline(0, color=t.ink, lw=pt(2))
    ax.plot([mid, mid], [-0.62, 0.62], color=t.paper, lw=pt(6), solid_capstyle="butt")
    ax.plot([mid, mid], [-0.62, 0.62], color=t.ink, lw=pt(3), solid_capstyle="butt")
    s.y += 60
    return ax


def dot_grid(s: Slide, n_dem: int, n: int = 100, cols: int = 10, size: float = 64, gap: float = 20):
    """One dot per simulated election, coloured by the winner (Democratic wins first)."""
    t = s.t
    rows_ = -(-n // cols)
    width = cols * size + (cols - 1) * gap
    x0 = MARGIN + (s.width - width) / 2
    for k in range(n):
        r, c = divmod(k, cols)
        s.ax.add_patch(plt.Circle((x0 + c * (size + gap) + size / 2, s.y + r * (size + gap) + size / 2), size / 2,
                                  color=t.dem if k < n_dem else t.rep, lw=0, zorder=2))
    s.y += rows_ * (size + gap) + 20
    return s


def state_voters(s: Slide, usps: str, code: str, p_dem: float, x: float, y: float, box: float, n: int = 420,
                 box_h: float | None = None):
    """The race's state drawn as a field of simulated voters: dots inside the state outline, exactly p_dem of them
    blue, scattered at random (seeded by the state), with the race code under it."""
    import numpy as np
    from matplotlib.path import Path as MPath

    from .geo import outline
    t = s.t
    rings = [np.array(r) for r in outline(usps)]
    pts = np.vstack(rings)
    (x0, y0), (x1, y1) = pts.min(0), pts.max(0)
    bw, bh = box, box_h or box
    k = min(bw / (x1 - x0), bh / (y1 - y0))
    ox, oy = x + (bw - (x1 - x0) * k) / 2, y + (bh - (y1 - y0) * k) / 2
    rings = [np.column_stack([ox + (r[:, 0] - x0) * k, oy + (r[:, 1] - y0) * k]) for r in rings]
    area = sum(abs(np.dot(r[:, 0], np.roll(r[:, 1], 1)) - np.dot(r[:, 1], np.roll(r[:, 0], 1))) / 2 for r in rings)
    step = (area / n) ** 0.5
    gx, gy = np.meshgrid(np.arange(x, x + bw, step) + step / 2, np.arange(y, y + bh, step) + step / 2)
    grid = np.column_stack([gx.ravel(), gy.ravel()])
    inside = np.zeros(len(grid), bool)
    for r in rings:
        inside |= MPath(r).contains_points(grid)
    dots = grid[inside]
    rng = np.random.default_rng(sum(map(ord, usps)))
    blue = np.zeros(len(dots), bool)
    blue[rng.permutation(len(dots))[:round(p_dem * len(dots))]] = True
    s.ax.scatter(dots[:, 0], dots[:, 1], s=pt(step * 0.72) ** 2, c=np.where(blue, t.dem, t.rep), lw=0, zorder=3)
    for r in rings:
        s.ax.fill(r[:, 0], r[:, 1], fill=False, ec=t.ink, lw=pt(2), zorder=2)
    bottom = oy + (y1 - y0) * k
    s._put(x + bw / 2, bottom + 18, code, "mono", 600, 26, t.ink, ha="center", va="top")
    s.tag_bottom = bottom + 60
    return len(dots)
