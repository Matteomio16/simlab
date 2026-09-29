"""Wordmark font side by side for Matteo: python -m brand.fontcheck -> brand/final/font-compare.png.

A: the kit's Newsreader 560. B: IBM Plex Sans 700, what the Lab Notebook slides set today (themes.LAB, frame.wordmark).
Each row shows the lockup on paper and indigo and the slide header at its real size (1080-wide slide).
"""
from __future__ import annotations

from .final import DARK, LIGHT, OUT, Face, lockup_horizontal, mono, raster, rect, serif

SLIDE = {"bg": "#F7F7F2", "ink": "#1C2A4A", "blue": "#2F6DB5", "red": "#D1432F", "purple": "#6D2E8C"}
W, ROW = 1760, 330


def row(y, face, track, label):
    s = mono().shapes(label, 20, 60, y + 44, ["#6B675F"] * len(label), .04)
    s += [(rect(40, y + 70, 820, 200), LIGHT["bg"])] + lockup_horizontal(80, y + 205, 84, LIGHT, face, track)
    s += [(rect(900, y + 70, 820, 200), DARK["bg"])] + lockup_horizontal(940, y + 205, 84, DARK, face, track)
    return s


def header(y, face, track, label):
    """The top of a 1080-wide slide at 1:1: kicker left, lockup right, rule under."""
    s = mono().shapes(label, 20, 60, y + 44, ["#6B675F"] * len(label), .04)
    s += [(rect(40, y + 70, 1080, 150), SLIDE["bg"])]
    s += mono().shapes("LAB NOTES 01", 30, 40 + 72, y + 70 + 76, [SLIDE["ink"]] * 12, .04)
    size = 40
    cap = face.cap * size / face.upm
    from .final import mark_w
    ww = mark_w(cap * 1.18) + cap * .42 + face.width("NotAPoll.org", size, track)
    s += lockup_horizontal(40 + 1080 - 72 - ww, y + 70 + 76, size, SLIDE, face, track)
    s += [(rect(40 + 72, y + 70 + 108, 1080 - 144, 2), SLIDE["ink"])]
    return s


def build():
    plex = Face("IBMPlexSans[wdth,wght].ttf", 700)
    shapes = row(0, serif(), -0.005, "A. NEWSREADER 560 (THE KIT)")
    shapes += row(ROW, plex, 0.0, "B. IBM PLEX SANS 700 (THE SLIDES TODAY)")
    shapes += header(2 * ROW, serif(), -0.005, "A ON A LAB NOTES SLIDE, ACTUAL SIZE")
    shapes += header(2 * ROW + 250, plex, 0.0, "B ON A LAB NOTES SLIDE, ACTUAL SIZE")
    h = 2 * ROW + 500
    raster(shapes, W, h, "#FFFFFF").convert("RGB").save(OUT / "font-compare.png", optimize=True)
    return OUT / "font-compare.png"


if __name__ == "__main__":
    print(build())
