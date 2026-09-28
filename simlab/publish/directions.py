"""Renders every creative direction on the same four posts, for Matteo to compare:
python -m simlab.publish.directions -> kits/directions/<theme>/ and kits/directions/board-<n>.jpg

The daily card and the video frame use invented example numbers, stamped EXAMPLE; they are not a forecast.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path

import matplotlib.pyplot as plt
from PIL import Image, ImageDraw, ImageFont

from . import charts
from .frame import Slide, Theme, face_file
from .labnotes import KITS, ep01, ep03
from .themes import DIRECTIONS

OUT = KITS.parent / "directions"
DAY = date(2026, 10, 12)


def daily_card(t: Theme) -> Slide:
    s = Slide(DAY, "DAILY FORECAST · EXAMPLE", t)
    s.headline("Example race: still a toss-up.", px=80)
    charts.stats(s, [("6 in 10", "simulations won by the Democrat")], px=150)
    s.text("Toss-up: anything from 35% to 65%. No meaningful change this week.", px=32, color=t.ink2, after=1.0)
    s.text("Simulated margin, middle 80% of outcomes", "sans", 600, 30, after=0.3)
    charts.margin_range(s, -4.2, 1.6, 7.4)
    charts.stats(s, [("58%", "NotAPoll"), ("D+1.5", "poll average"), ("55%", "market"), ("Toss-up", "Cook")], px=64,
                 rule=True)
    s.source("EXAMPLE DATA, NOT A FORECAST. Shows the daily card; real numbers start 12 Oct.")
    return s


def every_future(t: Theme) -> Slide:
    s = Slide(DAY, "EVERY FUTURE · EXAMPLE", t, size=(1080, 1920))
    s.headline("100 simulated elections.", px=84)
    s.dek("One dot per simulation, coloured by who wins.", px=36)
    charts.dot_grid(s, 58, size=40, gap=12)
    charts.stats(s, [("58", "won by the Democrat"), ("42", "won by the Republican")], px=100)
    s.source("EXAMPLE DATA, NOT A FORECAST. Frame from the 9:16 video.")
    return s


def render(t: Theme) -> list[Path]:
    d = OUT / t.name.lower().replace(" ", "-")
    a, c = ep01(t), ep03(t)
    picks = [a.slides[0][0], c.slides[2][0], daily_card(t), every_future(t)]
    for post in (a, c):
        for sl, _ in post.slides:
            if sl not in picks:
                plt.close(sl.fig)
    return [sl.save(d / f"{i}.jpg") for i, sl in enumerate(picks, 1)]


def board(t: Theme, paths: list[Path], n: int) -> Path:
    """The four posts at reduced size with the palette and typefaces written above them."""
    ims = [Image.open(p) for p in paths]
    h = 760
    thumbs = [im.resize((round(im.width * h / im.height), h), Image.LANCZOS) for im in ims]
    gap, head = 28, 230
    W = sum(im.width for im in thumbs) + gap * (len(thumbs) + 1)
    sheet = Image.new("RGB", (W, head + h + gap), "#E4E1DA")
    dr = ImageDraw.Draw(sheet)
    title = ImageFont.truetype(str(face_file("newsreader", 700)), 64)
    small = ImageFont.truetype(str(face_file("plexmono", 500)), 26)
    dr.text((gap, 30), f"{n}. {t.name}", font=title, fill="#141414")
    faces = sorted({t.faces[r] for r in ("serif", "sans", "mono")}, key=list(t.faces.values()).index)
    dr.text((gap, 118), "Type: " + " / ".join(faces), font=small, fill="#3A3833")
    x = gap
    for name, col in [("paper", t.paper), ("ink", t.ink), ("Dem", t.dem), ("Rep", t.rep), ("AI", t.ai),
                      ("strip", t.strip_bg)]:
        dr.rectangle((x, 166, x + 44, 210), fill=col, outline="#141414")
        dr.text((x + 54, 172), f"{name} {col}", font=small, fill="#3A3833")
        x += 54 + small.getlength(f"{name} {col}") + 36
    x = gap
    for im in thumbs:
        sheet.paste(im, (x, head))
        x += im.width + gap
    out = OUT / f"board-{n}.jpg"
    sheet.save(out, quality=90)
    return out


if __name__ == "__main__":
    for n, theme in enumerate(DIRECTIONS, 1):
        print(board(theme, render(theme), n))
