"""The NotAPoll canvas: every post image is drawn on a Slide, which always carries the label strip and the date.

Sizes are in pixels. Fonts (SIL Open Font License, unmodified files in fonts/): Newsreader for headlines, Libre
Franklin for text and numbers, IBM Plex Mono for labels. The two variable fonts are cut into the static weights
matplotlib needs on first use, into fonts/_static/ (not committed).
"""
from __future__ import annotations

import re
from datetime import date
from functools import cache
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
from matplotlib.font_manager import FontProperties
from matplotlib.text import Text
from PIL import Image, ImageFont

LABEL = "AI-simulated voters, not a poll"
SITE = "research.scaliastudio.dev/midterms"

PAPER = "#F5F3EE"
INK = "#111110"
INK2 = "#55534E"
MUTED = "#8A8781"
HAIRLINE = "#DEDBD2"
BASELINE = "#C4C1B7"
GRAPHITE = "#3B3A36"
DEM, REP, IND = "#2a78d6", "#e34948", "#eda100"
AI = "#4a3aa7"  # the simulation's own contribution; validated with DEM and REP on PAPER (all pairs)

DPI = 100
W, H = 1080, 1350
MARGIN = 72
STRIP = 96

FONTS = Path(__file__).parent / "fonts"
STATIC = FONTS / "_static"
VARIABLE = {"serif": "Newsreader[opsz,wght].ttf", "sans": "LibreFranklin[wght].ttf"}
MONO = {400: "IBMPlexMono-Regular.ttf", 500: "IBMPlexMono-Medium.ttf", 600: "IBMPlexMono-SemiBold.ttf"}


def pt(px: float) -> float:
    return px * 72 / DPI


@cache
def font_file(family: str, weight: int) -> Path:
    if family == "mono":
        return FONTS / MONO[weight]
    out = STATIC / f"{family}-{weight}.ttf"
    if not out.exists():
        axes = {"wght": weight} | ({"opsz": 72} if family == "serif" else {})
        STATIC.mkdir(exist_ok=True)
        tmp = out.with_suffix(".tmp")
        instancer.instantiateVariableFont(TTFont(FONTS / VARIABLE[family]), axes).save(tmp)
        tmp.replace(out)
    return out


def font(family: str, weight: int, px: float) -> FontProperties:
    return FontProperties(fname=font_file(family, weight), size=pt(px))


@cache
def _cmap(path: str) -> set[int]:
    return set(TTFont(path).getBestCmap())


@cache
def pil_font(family: str, weight: int, px: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(font_file(family, weight)), px)


def typeset(s: str) -> str:
    """Curly apostrophes and true minus signs."""
    return re.sub(r"(?<![\w.])-(?=\d)", "−", s.replace("'", "’"))


def wrap(s: str, family: str, weight: int, px: int, width: float) -> list[str]:
    """Greedy line breaks; a last line of one word takes a word from the line above when it fits."""
    f, lines = pil_font(family, weight, px), []
    for para in typeset(s).split("\n"):
        out, cur = [], ""
        for word in para.split():
            t = f"{cur} {word}".strip()
            if not cur or f.getlength(t) <= width:
                cur = t
            else:
                out.append(cur)
                cur = word
        out.append(cur)
        if len(out) > 1 and " " not in out[-1] and out[-2].count(" ") >= 2:
            head, moved = out[-2].rsplit(" ", 1)
            if f.getlength(f"{moved} {out[-1]}") <= width:
                out[-2:] = [head, f"{moved} {out[-1]}"]
        lines += out
    return lines


def fmt_day(d: date) -> str:
    return f"{d.day} {d.strftime('%b').upper()} {d.year}"


class Slide:
    """Top-to-bottom layout: a header (kicker, wordmark, rule), content placed at the cursor `y`, and a footer
    (source line, label strip with the date)."""

    def __init__(self, day: date, kicker: str, size: tuple[int, int] = (W, H)):
        self.w, self.h = size
        self.fig = plt.figure(figsize=(self.w / DPI, self.h / DPI), dpi=DPI)
        self.fig.patch.set_facecolor(PAPER)
        self.ax = self.fig.add_axes((0, 0, 1, 1))
        self.ax.set_xlim(0, self.w)
        self.ax.set_ylim(self.h, 0)
        self.ax.axis("off")
        self.width = self.w - 2 * MARGIN
        self.limit = self.h - STRIP - 110  # content ends above the two-line source zone
        self._put(MARGIN, 64, kicker, "mono", 500, 30, INK2, va="center")
        self._put(self.w - MARGIN, 64, "NotAPoll", "serif", 700, 40, INK, ha="right", va="center")
        self.ax.plot([MARGIN, self.w - MARGIN], [104, 104], color=INK, lw=pt(2), solid_capstyle="butt")
        self.ax.add_patch(plt.Rectangle((0, self.h - STRIP), self.w, STRIP, color=INK, lw=0))
        mid = self.h - STRIP / 2
        self._put(MARGIN, mid, LABEL.upper(), "mono", 600, 30, PAPER, va="center", gid="footer")
        self._put(self.w - MARGIN, mid, fmt_day(day), "mono", 400, 28, PAPER, ha="right", va="center", gid="footer")
        self.y = 160

    def _put(self, x, y, s, family, weight, px, color, **kw):
        return self.ax.text(x, y, typeset(s), fontproperties=font(family, weight, px), color=color, **kw)

    def at_bottom(self, height: float):
        """Moves the cursor down so a block of `height` ends at the bottom of the content area."""
        self.y = max(self.y, self.limit - height)
        return self

    def text(self, s: str, family: str = "sans", weight: int = 400, px: int = 40, color: str = INK,
             leading: float = 1.25, after: float = 0.6, width: float | None = None, x: float | None = None):
        step = px * leading
        for line in wrap(s, family, weight, px, width or self.width):
            self._put(MARGIN if x is None else x, self.y, line, family, weight, px, color, va="top")
            self.y += step
        self.y += px * after
        return self

    def headline(self, s: str, px: int = 88):
        return self.text(s, "serif", 600, px, INK, leading=1.08, after=0.45)

    def dek(self, s: str, px: int = 40):
        return self.text(s, "sans", 400, px, INK2, leading=1.3, after=0.9)

    def rule(self, color: str = HAIRLINE, after: float = 36):
        self.ax.plot([MARGIN, self.w - MARGIN], [self.y, self.y], color=color, lw=pt(1))
        self.y += after
        return self

    def chart(self, height: float, left: float = 0, right: float = 0):
        """An axes filling the content width at the cursor; `left` and `right` inset it (room for labels)."""
        x0, x1 = MARGIN + left, self.w - MARGIN - right
        ax = self.fig.add_axes((x0 / self.w, 1 - (self.y + height) / self.h, (x1 - x0) / self.w, height / self.h))
        ax.set_facecolor(PAPER)
        for side in ("top", "right", "left"):
            ax.spines[side].set_visible(False)
        ax.spines["bottom"].set_color(BASELINE)
        ax.spines["bottom"].set_linewidth(pt(1))
        ax.tick_params(length=0, pad=10, labelcolor=INK2)
        for lab in ax.get_xticklabels() + ax.get_yticklabels():
            lab.set_fontproperties(font("sans", 400, 28))
        self.y += height
        return ax

    def source(self, s: str):
        lines = wrap(s, "mono", 400, 22, self.width)
        if len(lines) > 2:
            raise ValueError(f"source line too long ({len(lines)} lines): {s!r}")
        for i, line in enumerate(reversed(lines)):
            self._put(MARGIN, self.h - STRIP - 28 - i * 30, line, "mono", 400, 22, MUTED, va="bottom", gid="footer")
        return self

    def layout_problems(self) -> list[str]:
        """Text outside the side margins, or content running into the source zone."""
        r, out = self.fig.canvas.get_renderer(), []
        for t in self.fig.findobj(Text):
            if not t.get_text().strip() or t.get_gid() == "footer" or not t.get_visible():
                continue
            bb = t.get_window_extent(r)
            if bb.x0 < MARGIN - 2 or bb.x1 > self.w - MARGIN + 2:
                out.append(f"outside the margins: {t.get_text()[:40]!r}")
            if self.h - bb.y0 > self.limit + 2:
                out.append(f"runs into the footer: {t.get_text()[:40]!r}")
        return out

    def missing_glyphs(self) -> list[str]:
        out = []
        for t in self.fig.findobj(Text):
            s, f = t.get_text(), t.get_fontproperties().get_file()
            if s.strip() and f:
                gone = sorted({c for c in s if not c.isspace() and ord(c) not in _cmap(str(f))})
                out += [f"{c!r} in {Path(f).name}: {s[:40]!r}" for c in gone]
        return out

    def save(self, path: Path) -> Path:
        path = Path(path)
        if gone := self.missing_glyphs():
            raise ValueError(f"{path}: missing glyphs: {gone}")
        if bad := self.layout_problems():
            raise ValueError(f"{path}: layout: {bad}")
        path.parent.mkdir(parents=True, exist_ok=True)
        self.fig.savefig(path, dpi=DPI, format="jpeg", facecolor=PAPER,
                         pil_kwargs={"quality": 92, "subsampling": 0, "optimize": True, "progressive": True})
        plt.close(self.fig)
        with Image.open(path) as im:
            if im.size != (self.w, self.h):
                raise ValueError(f"{path}: {im.size}, expected {(self.w, self.h)}")
        return path
