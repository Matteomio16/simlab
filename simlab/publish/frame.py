"""The NotAPoll canvas: every post image is drawn on a Slide, which always carries the label strip and the date.

Sizes are in pixels. A Theme sets colours, typefaces, texture and the signature elements; drawing code asks the slide
for roles ("serif" headline face, "sans" text face, "mono" label face) and theme colours, never raw values. Fonts are SIL
Open Font License files kept unmodified in fonts/; variable fonts are cut into the static instances matplotlib needs on
first use, into fonts/_static/ (not committed).
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field, replace
from datetime import date
from functools import cache
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
from matplotlib.font_manager import FontProperties
from matplotlib.text import Text
from PIL import Image, ImageFont

LABEL = "Social simulation, not a poll"
SITE = "notapoll.org"
# The fixed line that ends every caption (communication.md, 1 Oct). Wording still open with Matteo: option A for now.
DISCLAIMER = f"{LABEL}. How it works: {SITE}"  # Matteo, 28 Sep (relayed by the roadmap session): images show the domain
# The logo: H1, two hills, with the wordmark in Newsreader 560 (Matteo, 29 Sep; the kit is brand/final.py). The old
# ballot-box mark and the theme-face wordmark stay behind switches: NOTAPOLL_LOGO=grid, NOTAPOLL_WORDMARK=theme.
LOGO = os.environ.get("NOTAPOLL_LOGO", "hills")
WORDMARK = os.environ.get("NOTAPOLL_WORDMARK", "serif")
OVERLAP = {"light": "#7A4FC0", "dark": "#B98DD6"}  # the hills' overlap and ".org": on paper, on indigo or dark
HILLS = {"light": ("#2A78D6", "#E34948", "#7A4FC0"), "dark": ("#5B9BEA", "#F0605F", "#B98DD6")}  # the kit's own set
HILLS_W, HILLS_H = 104.8, 49.5  # the mark's native size in the logo kit

DPI = 100
W, H = 1080, 1350
MARGIN = 72
STRIP = 96

FONTS = Path(__file__).parent / "fonts"
STATIC = FONTS / "_static"
MONO = {400: "IBMPlexMono-Regular.ttf", 500: "IBMPlexMono-Medium.ttf", 600: "IBMPlexMono-SemiBold.ttf"}
FACES = {  # face -> (variable font file, fixed axes); "plexmono" is static
    "newsreader": ("Newsreader[opsz,wght].ttf", {"opsz": 72}),
    "franklin": ("LibreFranklin[wght].ttf", {}),
    "plexsans": ("IBMPlexSans[wdth,wght].ttf", {"wdth": 100}),
    "plexcond": ("IBMPlexSans[wdth,wght].ttf", {"wdth": 80}),
    "archivo": ("Archivo[wdth,wght].ttf", {"wdth": 100}),
    "archivocond": ("Archivo[wdth,wght].ttf", {"wdth": 68}),
    "schibsted": ("SchibstedGrotesk[wght].ttf", {}),
    "bricolage": ("BricolageGrotesque[opsz,wdth,wght].ttf", {"opsz": 96, "wdth": 100}),
    "bricolagetext": ("BricolageGrotesque[opsz,wdth,wght].ttf", {"opsz": 14, "wdth": 100}),
}


@dataclass(frozen=True)
class Theme:
    name: str
    paper: str = "#F5F3EE"
    ink: str = "#111110"
    ink2: str = "#55534E"
    muted: str = "#8A8781"
    hairline: str = "#DEDBD2"
    baseline: str = "#C4C1B7"
    strip_bg: str = "#111110"
    strip_fg: str = "#F5F3EE"
    accent: str = "#111110"
    dem: str = "#2a78d6"
    rep: str = "#e34948"
    ind: str = "#eda100"
    ai: str = "#4a3aa7"
    data: str = "#3B3A36"
    faces: dict = field(default_factory=lambda: {"serif": "newsreader", "sans": "franklin", "mono": "plexmono",
                                                 "hero": "franklin"})
    head_weight: int = 600
    hero_weight: int = 800
    head_upper: bool = False
    head_leading: float = 1.08
    texture: str | None = None  # "grid", "grain" or None
    header: str = "rule"  # "rule", "bar" (filled top bar) or "chip" (kicker in an accent box)
    highlight: str | None = None  # colour drawn behind hero numbers
    overprint: str | None = None  # second ink offset behind hero numbers (riso)
    tossup: str | None = None  # fill for the 35–65% toss-up zone; hairline when None
    swing_band: bool = False  # blue, purple, red band along the top of the label strip
    note: str = "#F6DD6E"  # post-it yellow for highlights: a note, a flag, "what changed" (communication.md)


BROADSHEET = Theme("broadsheet")


def pt(px: float) -> float:
    return px * 72 / DPI


def face_of(role: str, theme: Theme) -> str:
    return theme.faces.get(role) or theme.faces["sans"]


@cache
def face_file(face: str, weight: int) -> Path:
    if face == "plexmono":
        return FONTS / MONO[min(MONO, key=lambda w: abs(w - weight))]
    src, axes = FACES[face]
    out = STATIC / f"{face}-{weight}.ttf"
    if not out.exists():
        STATIC.mkdir(exist_ok=True)
        tmp = out.with_suffix(".tmp")
        instancer.instantiateVariableFont(TTFont(FONTS / src), axes | {"wght": weight}).save(tmp)
        tmp.replace(out)
    return out


def font_file(role: str, weight: int, theme: Theme = BROADSHEET) -> Path:
    return face_file(face_of(role, theme), weight)


def font(role: str, weight: int, px: float, theme: Theme = BROADSHEET) -> FontProperties:
    return FontProperties(fname=font_file(role, weight, theme), size=pt(px))


@cache
def _cmap(path: str) -> set[int]:
    return set(TTFont(path).getBestCmap())


@cache
def _pil(path: str, px: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, px)


def _ink(t: Text, bb):
    """The box around a text's glyphs (its line box minus unused ascender and descender room), in display pixels."""
    f = t.get_fontproperties().get_file()
    if not f or t.get_rotation() or len(t.get_text().splitlines()) > 1:
        return bb
    font = _pil(str(f), max(1, round(t.get_fontproperties().get_size_in_points() * DPI / 72)))
    _, top, _, bot = font.getbbox(t.get_text(), anchor="ls")  # y grows downward: top < 0 above the baseline
    base = bb.y0 + max(font.getbbox("lp", anchor="ls")[3], bot)  # display y grows upward
    return type(bb).from_extents(bb.x0, base - bot, bb.x1, base - top)


@cache
def cap_height(path: str) -> float:
    """Capital height as a share of the font size."""
    f = TTFont(path)
    return f["OS/2"].sCapHeight / f["head"].unitsPerEm


def tone(t: "Theme") -> str:
    """ "light" or "dark", from the paper colour."""
    r, g, b = (int(t.paper[i:i + 2], 16) for i in (1, 3, 5))
    return "dark" if 0.2126 * r + 0.7152 * g + 0.0722 * b < 128 else "light"


def hills(ax, x: float, baseline: float, height: float, colors, zorder: int = 3):
    """The H1 mark (logo kit): a blue hill and a red hill, purple where they overlap, standing on `baseline` (y down)."""
    k = height / HILLS_H
    u = np.linspace(-2.4, 102.4, 400)
    hill = lambda c: np.maximum(50 * np.exp(-(u - c) ** 2 / (2 * 13 * 13)) - 0.5, 0)
    f1, f2 = hill(37), hill(63)
    px = x + (u + 2.4) * k
    for f, col in ((f1, colors[0]), (f2, colors[1]), (np.minimum(f1, f2), colors[2])):
        m = f > 0
        ax.fill(np.r_[px[m][0], px[m], px[m][-1]], np.r_[baseline, baseline - f[m] * k, baseline], color=col, lw=0,
                zorder=zorder)


def pil_font(role: str, weight: int, px: int, theme: Theme = BROADSHEET) -> ImageFont.FreeTypeFont:
    return _pil(str(font_file(role, weight, theme)), int(px))


def typeset(s: str) -> str:
    """Curly apostrophes and true minus signs."""
    return re.sub(r"(?<![\w.])-(?=\d)", "−", s.replace("'", "’"))


def wrap(s: str, role: str, weight: int, px: int, width: float, theme: Theme = BROADSHEET) -> list[str]:
    """Greedy line breaks; a last line of one word takes a word from the line above when it fits."""
    f, lines = pil_font(role, weight, px, theme), []
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
    """Top-to-bottom layout: a header (kicker, wordmark), content placed at the cursor `y`, and a footer (source line,
    label strip with the date). `size` can be (1080, 1920) for video frames and stories."""

    def __init__(self, day: date, kicker: str, theme: Theme = BROADSHEET, size: tuple[int, int] = (W, H),
                 run: str | None = None):
        self.t, (self.w, self.h) = theme, size
        t = theme
        self.fig = plt.figure(figsize=(self.w / DPI, self.h / DPI), dpi=DPI)
        self.fig.patch.set_facecolor(t.paper)
        self.ax = self.fig.add_axes((0, 0, 1, 1))
        self.ax.set_xlim(0, self.w)
        self.ax.set_ylim(self.h, 0)
        self.ax.axis("off")
        self.width = self.w - 2 * MARGIN
        tall = self.h > 1600  # 9:16: keep clear of the Reels/Stories interface at the top and bottom
        self.top, self.foot = (220, self.h - 340) if tall else (0, self.h)
        self.limit = self.foot - STRIP - 110
        self._texture()
        T = self.top
        if t.header == "bar":
            self.ax.add_patch(plt.Rectangle((0, T), self.w, 128, color=t.ink, lw=0, zorder=1))
            self._put(MARGIN, T + 64, kicker, "mono", 500, 30, t.paper, va="center", zorder=2)
            self.wordmark(T + 64, 800, t.paper, t.paper)
            self.y = T + 184
        else:
            if t.header == "chip":
                wk = self.pil("mono", 600, 28).getlength(typeset(kicker))
                self.ax.add_patch(plt.Rectangle((MARGIN - 12, T + 42), wk + 24, 46, color=t.accent, lw=0, zorder=1))
                self._put(MARGIN, T + 65, kicker, "mono", 600, 28, t.strip_fg if t.strip_bg == t.accent else t.paper,
                          va="center", zorder=2)
            else:
                self._put(MARGIN, T + 64, kicker, "mono", 500, 30, t.ink2, va="center")
            self.wordmark(T + 64, 800 if t.head_upper else 700, t.ink, t.ai)
            self.ax.plot([MARGIN, self.w - MARGIN], [T + 110, T + 110], color=t.ink, lw=pt(2), solid_capstyle="butt")
            self.y = T + 164
        if run:
            self._put(self.w - MARGIN, self.y - 22, f"RUN {run} · 40,000 SIMULATED ELECTIONS", "mono", 500, 20, t.ink2,
                      ha="right", va="center")
            self.y += 14
        self.ax.add_patch(plt.Rectangle((0, self.foot - STRIP), self.w, STRIP, color=t.strip_bg, lw=0, zorder=1))
        if t.swing_band:
            for i, c in enumerate((t.dem, t.ai, t.rep)):
                self.ax.add_patch(plt.Rectangle((self.w * i / 3, self.foot - STRIP - 10), self.w / 3, 10, color=c,
                                                lw=0, zorder=1))
        mid = self.foot - STRIP / 2
        self._put(MARGIN, mid, LABEL.upper(), "mono", 600, 30, t.strip_fg, va="center", gid="footer", zorder=2)
        self._put(self.w - MARGIN, mid, fmt_day(day), "mono", 400, 28, t.strip_fg, ha="right", va="center",
                  gid="footer", zorder=2)

    def _texture(self):
        t = self.t
        if t.texture == "grid":
            for x in np.arange(0, self.w + 1, 36):
                self.ax.plot([x, x], [0, self.h], color=t.hairline, lw=pt(1), zorder=0)
            for y in np.arange(0, self.h + 1, 36):
                self.ax.plot([0, self.w], [y, y], color=t.hairline, lw=pt(1), zorder=0)
        elif t.texture == "grain":
            rng = np.random.default_rng(7)
            n = self.w * self.h // 90
            self.ax.scatter(rng.uniform(0, self.w, n), rng.uniform(0, self.h, n), s=pt(1.6) ** 2, color=t.ink,
                            alpha=0.06, lw=0, zorder=0)

    def font(self, role: str, weight: int, px: float) -> FontProperties:
        return font(role, weight, px, self.t)

    def pil(self, role: str, weight: int, px: float) -> ImageFont.FreeTypeFont:
        return pil_font(role, weight, px, self.t)

    def wrap(self, s: str, role: str, weight: int, px: int, width: float) -> list[str]:
        return wrap(s, role, weight, px, width, self.t)

    def _put(self, x, y, s, role, weight, px, color, **kw):
        return self.ax.text(x, y, typeset(s), fontproperties=self.font(role, weight, px), color=color, **kw)

    def at_bottom(self, height: float):
        """Moves the cursor down so a block of `height` ends at the bottom of the content area."""
        self.y = max(self.y, self.limit - height)
        return self

    def text(self, s: str, role: str = "sans", weight: int = 400, px: int = 40, color: str | None = None,
             leading: float = 1.25, after: float = 0.6, width: float | None = None, x: float | None = None):
        color = color or self.t.ink
        step = px * leading
        for line in self.wrap(s, role, weight, px, width or self.width):
            self._put(MARGIN if x is None else x, self.y, line, role, weight, px, color, va="top")
            self.y += step
        self.y += px * after
        return self

    def headline(self, s: str, px: int = 88, width: float | None = None):
        t = self.t
        return self.text(s.upper() if t.head_upper else s, "serif", t.head_weight, px, t.ink,
                         leading=t.head_leading, after=0.45, width=width)

    def dek(self, s: str, px: int = 40, width: float | None = None):
        return self.text(s, "sans", 400, px, self.t.ink2, leading=1.3, after=0.9, width=width)

    def wordmark(self, y: float, weight: int, color: str, tld: str):
        """Logomark and "NotAPoll.org" at the top right; the ".org" in the simulation colour doubles as the address."""
        px = 42 if WORDMARK == "serif" else 40
        if WORDMARK == "serif":
            fp, f = FontProperties(fname=face_file("newsreader", 560), size=pt(px)), _pil(str(face_file("newsreader", 560)), px)
        else:
            fp, f = self.font("serif", weight, px), self.pil("serif", weight, px)
        base = y + 14  # the text sits on one baseline; the hills stand on it too
        purple = OVERLAP[tone(self.t)] if LOGO == "hills" else tld
        self.ax.text(self.w - MARGIN, base, ".org", fontproperties=fp, color=purple, ha="right", va="baseline", zorder=2)
        right = self.w - MARGIN - f.getlength(".org")
        self.ax.text(right, base, "NotAPoll", fontproperties=fp, color=color, ha="right", va="baseline", zorder=2)
        left = right - f.getlength("NotAPoll")
        if LOGO == "hills":  # the kit's rule: hills 1.18 x cap height, 0.42 x cap height from the N
            cap = cap_height(fp.get_file()) * px
            h = 1.18 * cap
            hills(self.ax, left - 0.42 * cap - HILLS_W * h / HILLS_H, base, h, (self.t.dem, self.t.rep, purple))
        else:
            self.logomark(left - 58, y - 22, 44, color)

    def note(self, text: str, x: float | None = None, y: float | None = None, width: float = 520, px: int = 32,
             rot: float = -1.5):
        """A post-it: yellow paper with a soft shadow, slightly turned, for "what changed" or a flag."""
        x = MARGIN if x is None else x
        y = self.y if y is None else y
        lines = self.wrap(text, "sans", 600, px, width - 56)
        h = len(lines) * px * 1.3 + 52
        from matplotlib.transforms import Affine2D
        turn = Affine2D().rotate_deg_around(x + width / 2, y + h / 2, rot) + self.ax.transData
        self.ax.add_patch(plt.Rectangle((x + 6, y + 8), width, h, color="#00000018", lw=0, zorder=4, transform=turn))
        self.ax.add_patch(plt.Rectangle((x, y), width, h, color=self.t.note, lw=0, zorder=5, transform=turn))
        for i, line in enumerate(lines):
            self.ax.text(x + 28, y + 26 + i * px * 1.3, typeset(line), fontproperties=self.font("sans", 600, px),
                         color=self.t.ink, va="top", zorder=6, transform=turn)
        self.y = y + h + 24
        return self

    def logomark(self, x: float, y: float, size: float, color: str):
        """The NotAPoll mark: a ballot box holding a 3x3 grid of simulated voters instead of a tick."""
        self.ax.add_patch(plt.Rectangle((x, y), size, size, fill=False, ec=color, lw=pt(size / 14), zorder=3))
        step, r = size / 4, size * 0.085
        for i in range(3):
            for j in range(3):
                c = self.t.ai if (i, j) == (1, 1) else color
                self.ax.add_patch(plt.Circle((x + step * (j + 1), y + step * (i + 1)), r, color=c, lw=0, zorder=3))

    def rule(self, color: str | None = None, after: float = 36):
        self.ax.plot([MARGIN, self.w - MARGIN], [self.y, self.y], color=color or self.t.hairline, lw=pt(1))
        self.y += after
        return self

    def hero(self, x: float, y: float, value: str, px: int, **kw):
        """A big number, with the theme's highlighter or second-ink offset behind it."""
        t = self.t
        if t.highlight:
            wv = self.pil("hero", t.hero_weight, px).getlength(typeset(value))
            self.ax.add_patch(plt.Rectangle((x - 8, y + px * 0.45), wv + 16, px * 0.55, color=t.highlight, lw=0,
                                            zorder=1))
        if t.overprint:
            self._put(x + px * 0.05, y + px * 0.05, value, "hero", t.hero_weight, px, t.overprint, va="top", zorder=1,
                      alpha=0.9)
        return self._put(x, y, value, "hero", t.hero_weight, px, t.ink, va="top", zorder=2, **kw)

    def chart(self, height: float, left: float = 0, right: float = 0):
        """An axes filling the content width at the cursor; `left` and `right` inset it (room for labels)."""
        t = self.t
        x0, x1 = MARGIN + left, self.w - MARGIN - right
        ax = self.fig.add_axes((x0 / self.w, 1 - (self.y + height) / self.h, (x1 - x0) / self.w, height / self.h))
        ax.patch.set_alpha(0)
        for side in ("top", "right", "left"):
            ax.spines[side].set_visible(False)
        ax.spines["bottom"].set_color(t.baseline)
        ax.spines["bottom"].set_linewidth(pt(1))
        ax.tick_params(length=0, pad=10, labelcolor=t.ink2)
        for lab in ax.get_xticklabels() + ax.get_yticklabels():
            lab.set_fontproperties(self.font("sans", 400, 28))
        self.y += height
        return ax

    def source(self, s: str):
        lines = self.wrap(s, "mono", 400, 22, self.width)
        if len(lines) > 2:
            raise ValueError(f"source line too long ({len(lines)} lines): {s!r}")
        for i, line in enumerate(reversed(lines)):
            self._put(MARGIN, self.foot - STRIP - 28 - i * 30, line, "mono", 400, 22, self.t.muted, va="bottom",
                      gid="footer")
        return self

    def layout_problems(self) -> list[str]:
        """Text outside the side margins, or content running into the source zone."""
        r, out, boxes = self.fig.canvas.get_renderer(), [], []
        for t in self.fig.findobj(Text):
            if not t.get_text().strip() or not t.get_visible():
                continue
            bb = t.get_window_extent(r)
            ib = _ink(t, bb)
            for other, ob in boxes:  # glyphs of one text touching the glyphs of another
                if min(ib.x1, ob.x1) - max(ib.x0, ob.x0) > 2 and min(ib.y1, ob.y1) - max(ib.y0, ob.y0) > 2:
                    out.append(f"overlaps: {t.get_text()[:30]!r} and {other[:30]!r}")
            boxes.append((t.get_text(), ib))
            if t.get_gid() == "footer":
                continue
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
        self.fig.savefig(path, dpi=DPI, format="jpeg", facecolor=self.t.paper,
                         pil_kwargs={"quality": 92, "subsampling": 0, "optimize": True, "progressive": True})
        plt.close(self.fig)
        with Image.open(path) as im:
            if im.size != (self.w, self.h):
                raise ValueError(f"{path}: {im.size}, expected {(self.w, self.h)}")
        return path


# Colour names kept for code that predates themes.
PAPER, INK, INK2, MUTED = BROADSHEET.paper, BROADSHEET.ink, BROADSHEET.ink2, BROADSHEET.muted
HAIRLINE, BASELINE, GRAPHITE = BROADSHEET.hairline, BROADSHEET.baseline, BROADSHEET.data
DEM, REP, IND, AI = BROADSHEET.dem, BROADSHEET.rep, BROADSHEET.ind, BROADSHEET.ai
