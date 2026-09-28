"""Chart pieces drawn on a Slide: stat tiles, job rows, horizontal bars, dumbbells. Marks carry colour; text stays in ink."""
from __future__ import annotations

from .frame import (BASELINE, GRAPHITE, HAIRLINE, INK, INK2, MARGIN, PAPER, Slide, font, pil_font, pt, typeset,
                    wrap)


def stats(s: Slide, items: list[tuple[str, str]], px: int = 120, rule: bool = False):
    """A row of big numbers with a label under each; the numbers shrink together until each fits its column."""
    if rule:
        s.rule(INK, after=40)
    col = s.width / len(items)
    while px > 40 and max(pil_font("sans", 800, px).getlength(typeset(v)) for v, _ in items) > col - 32:
        px -= 4
    for i, (value, label) in enumerate(items):
        x = MARGIN + i * col
        s._put(x, s.y, value, "sans", 800, px, INK, va="top")
        s._put(x, s.y + px * 1.05, label, "sans", 400, 34, INK2, va="top")
    s.y += px * 1.05 + 34 * 1.3 + 40
    return s


def stats_height(px: int = 120, rule: bool = False) -> float:
    return px * 1.05 + 34 * 1.3 + (40 if rule else 0)


def rows(s: Slide, items: list[tuple[str, str, str]], label_w: float = 380):
    """Hairline-separated rows: a question on the left, the answer and its evidence on the right."""
    x2 = MARGIN + label_w + 32
    w2 = s.width - label_w - 32
    for question, answer, evidence in items:
        s.rule(HAIRLINE, after=22)
        top = s.y
        q = wrap(question, "sans", 600, 32, label_w)
        for i, line in enumerate(q):
            s._put(MARGIN, top + i * 40, line, "sans", 600, 32, INK2, va="top")
        s._put(x2, top, answer, "serif", 600, 44, INK, va="top")
        ev = wrap(evidence, "sans", 400, 30, w2)
        for i, line in enumerate(ev):
            s._put(x2, top + 58 + i * 38, line, "sans", 400, 30, INK2, va="top")
        s.y = max(top + len(q) * 40, top + 58 + len(ev) * 38) + 22
    s.rule(HAIRLINE, after=30)
    return s


def hbars(s: Slide, items: list[tuple[str, float, str]], xmax: float, fmt, height: float | None = None,
          label_w: float = 300, title: str | None = None):
    """Horizontal bars from one baseline; category names on the left, values at the tips."""
    if title:
        s.text(title, "sans", 600, 32, INK, after=0.5)
    height = height or 92 * len(items)
    ax = s.chart(height, left=label_w, right=180)
    ax.set_xlim(0, xmax)
    ax.set_ylim(len(items) - 0.5, -0.5)
    ax.set_yticks([])
    ax.set_xticks([])
    ax.spines["bottom"].set_visible(False)
    ax.axvline(0, color=BASELINE, lw=pt(2))
    thick = 36 / (height / len(items))
    for i, (name, v, color) in enumerate(items):
        ax.barh(i, v, height=thick, color=color, lw=0)
        ax.text(v, i, typeset(f"  {fmt(v)}"), va="center", ha="left", color=INK, fontproperties=font("sans", 600, 36))
        ax.text(-xmax * 0.03, i, typeset(name), va="center", ha="right", color=INK,
                fontproperties=font("sans", 400, 32))
    s.y += 24
    return ax


def dumbbell(s: Slide, items: list[tuple[str, float, float]], lim: float, height: float, left_label: str,
             right_label: str, fmt, label_w: float = 250):
    """One row per item: hollow dot = before, filled dot = after, joined by a line; zero line in the middle."""
    ax = s.chart(height, left=label_w, right=48)
    ax.set_xlim(-lim, lim)
    ax.set_ylim(len(items) - 0.5, -0.5)
    ax.set_yticks([])
    ticks = [-lim, -lim / 2, 0, lim / 2, lim]
    ax.set_xticks(ticks, [typeset(fmt(t)) for t in ticks])
    for lab in ax.get_xticklabels():
        lab.set_fontproperties(font("sans", 400, 28))
    ax.axvline(0, color=BASELINE, lw=pt(2), zorder=1)
    for x in ticks:
        if x:
            ax.axvline(x, color=HAIRLINE, lw=pt(1), zorder=0)
    for i, (name, before, after) in enumerate(items):
        ax.plot([before, after], [i, i], color=GRAPHITE, lw=pt(3), zorder=2, solid_capstyle="round")
        ax.scatter([before], [i], s=pt(26) ** 2, facecolor=PAPER, edgecolor=GRAPHITE, linewidth=pt(3), zorder=3)
        ax.scatter([after], [i], s=pt(26) ** 2, facecolor=INK, edgecolor=PAPER, linewidth=pt(3), zorder=4)
        ax.text(-lim * 1.04, i, typeset(name), va="center", ha="right", color=INK,
                fontproperties=font("sans", 400, 32))
    s.y += 56
    x0, x1 = MARGIN + label_w, s.w - MARGIN
    arrow = pil_font("mono", 400, 28).getlength("← ")
    s._put(x0, s.y, "← ", "mono", 400, 28, INK2, va="top")
    s._put(x0 + arrow, s.y, left_label, "sans", 400, 28, INK2, va="top")
    s._put(x1, s.y, " →", "mono", 400, 28, INK2, ha="right", va="top")
    s._put(x1 - arrow, s.y, right_label, "sans", 400, 28, INK2, ha="right", va="top")
    s.y += 60
    return ax


def legend_dots(s: Slide, items: list[tuple[str, bool]]):
    """Hollow/filled dot keys in one line."""
    x = MARGIN
    for label, filled in items:
        s.ax.scatter([x + 13], [s.y + 16], s=pt(26) ** 2, facecolor=INK if filled else PAPER,
                     edgecolor=INK if filled else GRAPHITE, linewidth=pt(3), zorder=4)
        s._put(x + 40, s.y + 16, label, "sans", 400, 30, INK2, va="center")
        x += 40 + pil_font("sans", 400, 30).getlength(label) + 48
    s.y += 56
    return s
