"""The NotAPoll.org logo, final: python -m brand.final -> brand/final/.

The mark is H1: a blue hill and a red hill, purple where they overlap (two electorates' opinion curves, side on).
One geometry source feeds both outputs: every shape is a list of flattened contours, written to SVG as paths and
rasterised with PIL (4x supersampled, even-odd fill), so the PNGs match the SVG masters exactly. Text is outlined
from Newsreader (SIL OFL) with its own kerning, so no SVG depends on an installed font.
"""
from __future__ import annotations

import math
from functools import lru_cache
from pathlib import Path

import numpy as np
from fontTools.pens.basePen import BasePen
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent
FONTS = ROOT.parent / "simlab" / "publish" / "fonts"
OUT = ROOT / "final"

LIGHT = {"bg": "#F5F3EE", "ink": "#111110", "blue": "#2A78D6", "red": "#E34948", "purple": "#7A4FC0",
         "muted": "#6B675F"}
DARK = {"bg": "#2A2152", "ink": "#F5F3EE", "blue": "#5B9BEA", "red": "#F0605F", "purple": "#B98DD6",
        "muted": "#B7B0D6"}
LABEL = "SOCIAL SIMULATION, NOT A POLL"
SERIF_WGHT = 560


# ---- type -----------------------------------------------------------------------------------------------------

class Flatten(BasePen):
    def __init__(self, glyphset, k, ox, oy, steps=16):
        super().__init__(glyphset)
        self.k, self.ox, self.oy, self.steps = k, ox, oy, steps
        self.contours, self.cur = [], []

    def _p(self, pt):
        return self.ox + pt[0] * self.k, self.oy - pt[1] * self.k

    def _moveTo(self, pt):
        self.cur = [self._p(pt)]

    def _lineTo(self, pt):
        self.cur.append(self._p(pt))

    def _curveToOne(self, p1, p2, p3):
        p0 = self._cur_font
        for i in range(1, self.steps + 1):
            t = i / self.steps
            u = 1 - t
            self.cur.append(self._p((u ** 3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t ** 3 * p3[0],
                                     u ** 3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t ** 3 * p3[1])))

    def _qCurveToOne(self, p1, p2):
        p0 = self._cur_font
        for i in range(1, self.steps + 1):
            t = i / self.steps
            u = 1 - t
            self.cur.append(self._p((u * u * p0[0] + 2 * u * t * p1[0] + t * t * p2[0],
                                     u * u * p0[1] + 2 * u * t * p1[1] + t * t * p2[1])))

    @property
    def _cur_font(self):
        return self._getCurrentPoint()

    def _closePath(self):
        if len(self.cur) > 2:
            self.contours.append(self.cur)
        self.cur = []

    _endPath = _closePath


class Face:
    def __init__(self, file: str, wght: int | None = None):
        f = TTFont(FONTS / file)
        if "fvar" in f:
            axes = {a.axisTag for a in f["fvar"].axes}
            f = instancer.instantiateVariableFont(f, {k: v for k, v in (("wght", wght), ("opsz", 72), ("wdth", 100))
                                                      if k in axes})
        self.f, self.gs, self.cmap = f, f.getGlyphSet(), f.getBestCmap()
        self.upm = f["head"].unitsPerEm
        self.cap = f["OS/2"].sCapHeight
        self._kern = self._pairs()

    def _pairs(self) -> dict:
        pairs: dict = {}
        if "GPOS" not in self.f:
            return pairs
        gpos = self.f["GPOS"].table
        idx = {i for fr in gpos.FeatureList.FeatureRecord if fr.FeatureTag == "kern" for i in fr.Feature.LookupListIndex}
        for i in sorted(idx):
            for st in gpos.LookupList.Lookup[i].SubTable:
                st = getattr(st, "ExtSubTable", st)
                if getattr(st, "Format", None) == 1 and hasattr(st, "PairSet"):
                    for first, ps in zip(st.Coverage.glyphs, st.PairSet):
                        for r in ps.PairValueRecord:
                            v = getattr(r.Value1, "XAdvance", 0) if r.Value1 else 0
                            pairs.setdefault((first, r.SecondGlyph), v)
                elif getattr(st, "Format", None) == 2:
                    c1, c2 = st.ClassDef1.classDefs, st.ClassDef2.classDefs
                    for first in st.Coverage.glyphs:
                        rec = st.Class1Record[c1.get(first, 0)]
                        pairs.setdefault(("__class2__", first), (rec, c2))
        return pairs

    def kern(self, a: str, b: str) -> float:
        if (a, b) in self._kern:
            return self._kern[(a, b)]
        cls = self._kern.get(("__class2__", a))
        if cls:
            rec, c2 = cls
            r = rec.Class2Record[c2.get(b, 0)]
            return getattr(r.Value1, "XAdvance", 0) or 0 if r.Value1 else 0
        return 0

    def layout(self, text: str, size: float, track: float = 0.0):
        k = size / self.upm
        out, x, prev = [], 0.0, None
        for ch in text:
            g = self.cmap[ord(ch)]
            if prev:
                x += self.kern(prev, g) * k
            out.append((ch, g, x))
            x += self.gs[g].width * k + track * size
            prev = g
        return out, x - track * size

    def shapes(self, text: str, size: float, x: float, baseline: float, colors, track: float = 0.0):
        """One shape per run of same-coloured characters; colors is one colour per character."""
        k = size / self.upm
        glyphs, _ = self.layout(text, size, track)
        runs: dict = {}
        for (ch, g, gx), c in zip(glyphs, colors):
            pen = Flatten(self.gs, k, x + gx, baseline)
            self.gs[g].draw(pen)
            runs.setdefault(c, []).extend(pen.contours)
        return [(cs, c) for c, cs in runs.items()]

    def width(self, text: str, size: float, track: float = 0.0) -> float:
        return self.layout(text, size, track)[1]


@lru_cache
def serif() -> Face:
    return Face("Newsreader[opsz,wght].ttf", SERIF_WGHT)


@lru_cache
def mono() -> Face:
    return Face("IBMPlexMono-Medium.ttf")


# ---- the mark -------------------------------------------------------------------------------------------------

EPS = .5
NATIVE_W, NATIVE_H = 104.8, 49.5


def _hill(x, cx):
    return 50 * np.exp(-(x - cx) ** 2 / (2 * 13 * 13))


def mark(x: float, baseline: float, height: float, pal, n: int = 400):
    """H1 with its baseline at `baseline` and left edge at x, scaled to `height`."""
    k = height / NATIVE_H
    u = np.linspace(-2.4, 102.4, n)
    f1, f2 = np.maximum(_hill(u, 37) - EPS, 0), np.maximum(_hill(u, 63) - EPS, 0)
    px = x + (u + 2.4) * k

    def area(f):
        m = f > 0
        xs, ys = px[m], baseline - f[m] * k
        return [[(xs[0], baseline)] + list(zip(xs, ys)) + [(xs[-1], baseline)]]
    return [(area(f1), pal["blue"]), (area(f2), pal["red"]), (area(np.minimum(f1, f2)), pal["purple"])]


def mark_w(height: float) -> float:
    return NATIVE_W * height / NATIVE_H


def circle(cx, cy, r, n=360):
    return [[(cx + r * math.cos(2 * math.pi * i / n), cy + r * math.sin(2 * math.pi * i / n)) for i in range(n)]]


def rect(x, y, w, h):
    return [[(x, y), (x + w, y), (x + w, y + h), (x, y + h)]]


def rounded(x, y, w, h, r, n=24):
    pts = []
    for cx, cy, a0 in ((x + w - r, y + r, -90), (x + w - r, y + h - r, 0), (x + r, y + h - r, 90), (x + r, y + r, 180)):
        pts += [(cx + r * math.cos(math.radians(a0 + 90 * i / n)), cy + r * math.sin(math.radians(a0 + 90 * i / n)))
                for i in range(n + 1)]
    return [pts]


# ---- lockups --------------------------------------------------------------------------------------------------

def wordmark(x, baseline, size, pal, track=-0.005, face=None):
    text = "NotAPoll.org"
    return (face or serif()).shapes(text, size, x, baseline, [pal["ink"]] * 8 + [pal["purple"]] * 4, track)


def lockup_horizontal(x, baseline, size, pal, face=None, track=-0.005):
    """The hills stand on the wordmark's baseline, as tall as a capital and a bit: one ground for both."""
    face = face or serif()
    cap = face.cap * size / face.upm
    h = cap * 1.18
    gap = cap * .42
    return mark(x, baseline, h, pal) + wordmark(x + mark_w(h) + gap, baseline, size, pal, track, face)


def lockup_horizontal_size(size):
    cap = serif().cap * size / serif().upm
    h = cap * 1.18
    return mark_w(h) + cap * .42 + serif().width("NotAPoll.org", size, -0.005), cap, h


def lockup_stacked(cx, top, size, pal):
    cap = serif().cap * size / serif().upm
    ww = serif().width("NotAPoll.org", size, -0.005)
    h = cap * 1.9
    base = top + h
    return mark(cx - mark_w(h) / 2, base, h, pal) + wordmark(cx - ww / 2, base + cap * .55 + cap, size, pal)


# ---- output ---------------------------------------------------------------------------------------------------

def svg(shapes, w, h, bg=None) -> str:
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:g} {h:g}" width="{w:g}" height="{h:g}">']
    if bg:
        parts.append(f'<rect width="{w:g}" height="{h:g}" fill="{bg}"/>')
    for contours, color in shapes:
        d = " ".join("M" + " L".join(f"{px:.2f},{py:.2f}" for px, py in c) + " Z" for c in contours)
        parts.append(f'<path d="{d}" fill="{color}"/>')
    parts.append("</svg>")
    return "".join(parts)


def _signed(c) -> float:
    a = np.asarray(c)
    return float(np.dot(a[:, 0], np.roll(a[:, 1], -1)) - np.dot(a[:, 1], np.roll(a[:, 0], -1)))


def raster(shapes, w, h, bg=None, ss=4) -> Image.Image:
    """Nonzero fill: variable fonts keep overlapping contours, which an even-odd fill would punch holes into."""
    W, H = int(w * ss), int(h * ss)
    img = Image.new("RGBA", (W, H), bg or (0, 0, 0, 0))
    for contours, color in shapes:
        wind = np.zeros((H, W), np.int8)
        for c in contours:
            pts = np.asarray(c) * ss
            x0, y0 = np.maximum(np.floor(pts.min(0)).astype(int) - 1, 0)
            x1, y1 = np.minimum(np.ceil(pts.max(0)).astype(int) + 2, (W, H))
            if x1 <= x0 or y1 <= y0:
                continue
            one = Image.new("L", (int(x1 - x0), int(y1 - y0)), 0)
            ImageDraw.Draw(one).polygon([(px - x0, py - y0) for px, py in pts], fill=1)
            wind[y0:y1, x0:x1] += np.asarray(one, np.int8) * (1 if _signed(c) > 0 else -1)
        mask = Image.fromarray(((wind != 0) * 255).astype(np.uint8))
        img.paste(Image.new("RGBA", (W, H), color), (0, 0), mask)
    return img.resize((int(w), int(h)), Image.LANCZOS)


def bounds(shapes):
    pts = np.array([p for cs, _ in shapes for c in cs for p in c])
    return pts.min(0), pts.max(0)


def fit(shapes, w, h, pad):
    """Translate and scale shapes to sit centred in a w x h canvas with pad on every side."""
    (x0, y0), (x1, y1) = bounds(shapes)
    k = min((w - 2 * pad) / (x1 - x0), (h - 2 * pad) / (y1 - y0))
    ox, oy = (w - (x1 - x0) * k) / 2 - x0 * k, (h - (y1 - y0) * k) / 2 - y0 * k
    return [([[(ox + px * k, oy + py * k) for px, py in c] for c in cs], col) for cs, col in shapes]


# ---- compositions ---------------------------------------------------------------------------------------------

def avatar(pal, size=1080, share=.78, lift=.06):
    """The mark centred for the circle crop: `share` of the width, nudged up because the hills' weight sits low."""
    h = size * share * NATIVE_H / NATIVE_W
    base = size / 2 + h / 2 - lift * h
    return mark((size - mark_w(h)) / 2, base, h, pal)


def avatar_bleed(pal, size=1080, share=.56):
    """The hills rising from the bottom of the circle, cropped like a landscape; share = hill height / size."""
    h = size * share
    w = mark_w(h)
    return mark((size - w) / 2, size + h * .02, h, pal)


def avatar_big(pal, size=1080):
    """The whole mark, as large as the circle allows: tails run into the edge, base on the lower third."""
    w = size * .96
    h = w * NATIVE_H / NATIVE_W
    return mark((size - w) / 2, size * .72, h, pal)


AVATARS = {  # option -> (composition, note); each is drawn on indigo and on paper
    "D": (lambda p: avatar_bleed(p, share=.72), "Landscape crop, hills 30% bigger: the purple overlap fills the lower middle"),
    "D+": (lambda p: avatar_bleed(p, share=.86), "Landscape crop, bigger still: the peaks near the top of the circle"),
    "E": (avatar_big, "The whole mark, as wide as the circle, standing on the lower third"),
}


def banner(pal, w, h, tagline="Democracy, rehearsed."):
    """Headers: the hills stand on the bottom edge at the right; tagline and label top left, clear of the avatar."""
    s = h / 500
    hh = h * .72
    shapes = mark(w - mark_w(hh) - 40 * s, h + 1, hh, pal)
    shapes += serif().shapes(tagline, 64 * s, 80 * s, 160 * s, [pal["ink"]] * len(tagline), -0.01)
    for i, line in enumerate(("The 2026 US midterms,", "simulated every day by synthetic voters.")):
        shapes += serif().shapes(line, 27 * s, 82 * s, (214 + 36 * i) * s, [pal["muted"]] * len(line))
    shapes += mono().shapes(LABEL, 17 * s, 82 * s, 88 * s, [pal["purple"]] * len(LABEL), .06)
    return shapes


def favicon(pal, size=64):
    """A rounded tile with the hills standing on its bottom edge: at 16 px the colour still reads."""
    h = size * .5
    w = mark_w(h)
    return [(rounded(0, 0, size, size, size * .22), pal["bg"])] + mark((size - w) / 2, size * .8, h, pal)


def build() -> list[Path]:
    OUT.mkdir(exist_ok=True)
    written = []

    def save(name, shapes, w, h, bg=None, png=True, jpg=False):
        (OUT / f"{name}.svg").write_text(svg(shapes, w, h, bg), encoding="utf-8")
        written.append(OUT / f"{name}.svg")
        if png or jpg:
            im = raster(shapes, w, h, bg)
            if png:
                im.save(OUT / f"{name}.png")
                written.append(OUT / f"{name}.png")
            if jpg:
                im.convert("RGB").save(OUT / f"{name}.jpg", quality=92)
                written.append(OUT / f"{name}.jpg")

    for tag, pal in (("light", LIGHT), ("dark", DARK)):
        m = fit(mark(0, 0, 100, pal), 400, 200, 8)
        save(f"mark-{tag}", m, 400, 200)
        ww, cap, _ = lockup_horizontal_size(100)
        save(f"lockup-{tag}", fit(lockup_horizontal(0, 0, 100, pal), ww + 80, cap * 1.5 + 80, 40), ww + 80,
             cap * 1.5 + 80)
        st = lockup_stacked(0, 0, 100, pal)
        (x0, y0), (x1, y1) = bounds(st)
        save(f"lockup-stacked-{tag}", fit(st, x1 - x0 + 80, y1 - y0 + 80, 40), x1 - x0 + 80, y1 - y0 + 80)
    mono_pal = {**LIGHT, "blue": LIGHT["ink"], "red": LIGHT["ink"]}
    save("mark-mono", fit(mark(0, 0, 100, mono_pal), 400, 200, 8), 400, 200)

    save("avatar", avatar_bleed(LIGHT, share=.72), 1080, 1080, LIGHT["bg"], png=True, jpg=True)  # Matteo, 29 Sep: D white
    save("avatar-crop-indigo", avatar_bleed(DARK), 1080, 1080, DARK["bg"])
    (OUT / "avatar-options").mkdir(exist_ok=True)
    for key, (fn, _) in AVATARS.items():
        for tag, pal in (("indigo", DARK), ("white", LIGHT)):
            (OUT / "avatar-options" / f"{key}-{tag}.svg").write_text(svg(fn(pal), 1080, 1080, pal["bg"]), encoding="utf-8")
    save("avatar-centred", avatar(DARK), 1080, 1080, DARK["bg"])
    save("avatar-centred-paper", avatar(LIGHT), 1080, 1080, LIGHT["bg"])
    save("avatar-paper", avatar_bleed(LIGHT), 1080, 1080, LIGHT["bg"])
    save("header-x", banner(LIGHT, 1500, 500), 1500, 500, LIGHT["bg"], jpg=True)
    save("header-x-dark", banner(DARK, 1500, 500), 1500, 500, DARK["bg"])
    save("banner-bluesky", banner(LIGHT, 3000, 1000), 3000, 1000, LIGHT["bg"], jpg=True)

    fav = favicon(DARK)
    (OUT / "favicon.svg").write_text(svg(fav, 64, 64), encoding="utf-8")
    written.append(OUT / "favicon.svg")
    big = raster(fav, 64, 64, ss=8)
    for n in (16, 32, 48, 180):
        raster(favicon(DARK, n), n, n, ss=8).save(OUT / f"favicon-{n}.png")
        written.append(OUT / f"favicon-{n}.png")
    big.save(OUT / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)])
    written.append(OUT / "favicon.ico")
    return written


if __name__ == "__main__":
    for p in build():
        print(p.relative_to(ROOT.parent))
