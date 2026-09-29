"""Every future: a 9:16 video (1080x1920, 30 fps, H.264, no sound) in which a race's 100 simulated elections land one
by one as dots until the count reads the race's chance. python -m simlab.publish.reel -> kits/reels/<code>.mp4 and a
cover image; the daily kit calls reel() with --reel. Music, if any, is added in the Instagram app when posting by hand.
"""
from __future__ import annotations

import sys
from pathlib import Path

import imageio_ffmpeg
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

from . import racecards as rc
from .frame import MARGIN, Slide, pt
from .themes import LAB

W, H, FPS = 1080, 1920, 30
START, FALL, SECONDS = 1.0, 0.45, 16.0  # first drop, fall time per dot, total length
OUT = Path(__file__).resolve().parents[2] / "kits" / "reels"


def schedule(n: int = 100, first: float = 0.22, last: float = 0.035) -> np.ndarray:
    """Drop times: slow at first so the eye learns what a dot means, then faster (a geometric speed-up)."""
    gaps = first * (last / first) ** (np.arange(n) / (n - 1))
    return START + np.concatenate([[0], np.cumsum(gaps[:-1])])


def build(r: dict, t=LAB):
    """The canvas with its static parts drawn, plus what each frame needs."""
    s = Slide(r.get("day", rc.DAY), r.get("kicker", "EVERY FUTURE · EXAMPLE"), rc.replace(t, dem=t.ind)
              if r.get("left_party", "D") == "I" else t, size=(W, H), run=r["run"])
    t = s.t
    y0 = s.y
    hw = rc.tag(s, r, box_h=110)
    rc.title(s, r, hw)
    s.y = max(s.y, y0 + 4 + 110 + 60) + 26  # a fixed band for the outline, so every state gets the same layout
    count = s._put(MARGIN, s.y, "0", "hero", t.hero_weight, 150, t.ink, va="top")
    s.y += 150 * 1.12
    label = s._put(MARGIN, s.y, "", "sans", 400, 34, t.ink2, va="top")
    s.y += 34 * 1.4 + 20
    s._put(MARGIN, s.y, "EACH DOT: ONE SIMULATED ELECTION ON 3 NOV", "mono", 500, 24, t.ai, va="top")
    s.y += 44
    top = s.y
    dots, radius, base = rc.pile(s, r, rc.draws(r), top, 250)
    s.y = base + 64
    order = np.random.default_rng(sum(map(ord, r["code"]))).permutation(len(dots))
    return s, count, label, [dots[i] for i in order], radius, top + radius


def reveal(s: Slide, r: dict):
    """The closing card: the verdict label, the 3 Nov and today numbers, and the benchmarks."""
    rc.chip(s, r, s.y)
    s.y += 22
    if r.get("today") is not None:
        s._put(MARGIN, s.y, f"If the election were today: {r['today'] * 100:.0f} in 100", "sans", 600, 32, s.t.ink,
               va="top")
        s.y += 32 * 1.3 + 8
    s._put(MARGIN, s.y, f"Poll average {r['poll']} · Market {rc.pct_txt(r['market'])} · Cook {r['cook']}", "mono",
           500, 26, s.t.ink2, va="top")
    s.y += 40
    s.source(r.get("source") or "EXAMPLE: invented numbers, not a forecast. Every future.")


def reel(r: dict, out: Path, t=LAB) -> dict:
    """Renders the video and its cover; refuses if the closing frame breaks the layout rules."""
    s, count, label, dots, radius, top = build(r, t)  # dots fall from the top of the chart, never across text
    who = rc.who(r)
    drops = schedule(len(dots))
    sc = s.ax.scatter([], [], s=pt(2 * radius) ** 2, lw=0, zorder=2)
    revealed = False
    out.parent.mkdir(parents=True, exist_ok=True)
    writer = imageio_ffmpeg.write_frames(str(out), (W, H), fps=FPS, codec="libx264", quality=8, macro_block_size=8,
                                         pix_fmt_in="rgb24", pix_fmt_out="yuv420p",
                                         output_params=["-movflags", "+faststart"])
    writer.send(None)
    last = None
    for f in range(int(SECONDS * FPS)):
        now = f / FPS
        xy, cols, landed, dem = [], [], 0, 0
        for (x, y, col), t0 in zip(dots, drops):
            if now < t0:
                break
            u = min((now - t0) / FALL, 1)
            xy.append((x, top + (y - top) * u * u))  # falls like a dropped ball, landing at u = 1
            cols.append(col)
            if u >= 1:
                landed += 1
                dem += col == s.t.dem
        sc.set_offsets(np.array(xy) if xy else np.empty((0, 2)))
        sc.set_color(cols)
        count.set_text(str(dem))
        label.set_text(f"of {landed} simulated elections won by the {who}" if landed else "")
        if not revealed and now >= drops[-1] + FALL + 0.5:
            reveal(s, r)
            revealed = True
            if bad := s.layout_problems() + s.missing_glyphs():
                writer.close()
                out.unlink(missing_ok=True)
                raise ValueError(f"{out}: {bad}")
        s.fig.canvas.draw()
        last = np.asarray(s.fig.canvas.buffer_rgba())[:, :, :3]
        writer.send(np.ascontiguousarray(last))
    writer.close()
    cover = out.with_name(out.stem + "-cover.jpg")
    Image.fromarray(last).save(cover, quality=92, subsampling=0)
    plt.close(s.fig)
    return {"video": out, "cover": cover, "seconds": SECONDS, "dem_wins": dem}


if __name__ == "__main__":
    demo = rc.RACE | {"state": "North Carolina", "usps": "NC", "code": "NC-SEN", "today": 0.61}
    for arg in sys.argv[1:] or ["NC"]:
        r = demo if arg == "NC" else demo | {"state": "Texas", "usps": "TX", "code": "TX-SEN", "p": 0.24,
                                               "market": 0.2, "cook": "Likely R", "poll": "R+6.5", "today": 0.22}
        print(reel(r, OUT / f"{r['code']}.mp4"))
