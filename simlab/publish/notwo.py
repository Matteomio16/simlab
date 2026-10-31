"""No two alike (Matteo, 30 Oct: final-days special): a wall of our simulated elections, one row each, showing who wins
the closest Senate races, then how few times even the most common combination came up.
Read from draws.json (every 40th of the 40,000 simulated elections: draw k is election 40k + 1).
python -m simlab.publish.notwo --date 2026-10-30 --post 2026-10-30 [--reel]
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import date
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from . import text
from .frame import DISCLAIMER, LABEL, MARGIN, Slide
from .launch import LIMIT
from .pollread import end
from .themes import LAB

ROOT = Path(__file__).resolve().parents[2]
SERIES = "No two alike"
ALLOW = ()
CODE = {"OH-S": "OH", "FL-S": "FL"}
NAMES = {"MN": "Minnesota", "MI": "Michigan", "ME": "Maine", "TX": "Texas", "OH-S": "Ohio", "AK": "Alaska",
         "IA": "Iowa", "KS": "Kansas", "NE": "Nebraska", "SC": "South Carolina", "FL-S": "Florida",
         "NC": "North Carolina", "NH": "New Hampshire", "GA": "Georgia"}


def control(s: dict, k: int) -> tuple[str, str]:
    """(label, side) for simulated election k: King and Sanders count with Democrats; 50-50 goes to the Vice President."""
    r, d = s["R"][k], s["D"][k] + 2
    if r >= 50:
        return f"Rep {r}", "R"
    if d >= 51:
        return f"Dem {d}", "D"
    return "Ind. decide", "I"


def strip(s: Slide, y: float, x0: float, cell: float, wins: list[str]) -> list:
    """One simulated election: a square per race, coloured by who wins it."""
    col = {"D": LAB.dem, "R": LAB.rep, "I": LAB.ai}
    out = []
    for i, w in enumerate(wins):
        n0 = len(s.ax.patches)
        s.ax.add_patch(plt.Rectangle((x0 + i * cell, y), cell * 0.84, cell * 0.84, color=col[w], lw=0, zorder=3))
        out += s.ax.patches[n0:]
    return out


def winners(draws: dict, races: list[str], lefts: dict, k: int) -> list[str]:
    return [("I" if lefts[r] == "I" else "D") if draws["races"][r][k] > 0 else "R" for r in races]


def wall(s: Slide, draws: dict, races: list[str], lefts: dict, ks: list[int], top: float, cell: float) -> tuple[float, list]:
    """Rows of simulated elections under a header of state codes; returns the bottom and each row's artists."""
    x0 = MARGIN + 190
    for i, r in enumerate(races):
        s._put(x0 + i * cell + cell * 0.42, top, CODE.get(r, r), "mono", 600, 20, LAB.ink2, ha="center", va="top")
    y, rows = top + 38, []
    for k in ks:
        label, side = control(draws["seats"]["senate"], k)
        parts = [s._put(MARGIN, y + cell * 0.42, f"No. {40 * k + 1:,}", "mono", 500, 22, LAB.ink2, va="center")]
        parts += strip(s, y, x0, cell, winners(draws, races, lefts, k))
        parts.append(s._put(s.w - MARGIN, y + cell * 0.42, label, "sans", 700, 26,
                            {"D": LAB.dem, "R": LAB.rep, "I": LAB.ai}[side], ha="right", va="center"))
        rows.append(parts)
        y += cell
    return y, rows


def build(data_day: str, post_day: str, data: Path, reel: bool = False) -> tuple[Path, list[str]]:
    draws = json.loads((data / "derived" / data_day / "draws.json").read_text(encoding="utf-8"))
    f = json.loads((data / "derived" / data_day / "forecast.json").read_text(encoding="utf-8"))
    races = sorted((r for r, x in f["races"].items() if 0.1 < x["p_dem_win"] < 0.9 and r in draws["races"]),
                   key=lambda r: -f["races"][r]["p_dem_win"])
    lefts = {r: f["races"][r].get("left_party", "D") for r in races}
    n = len(draws["seats"]["senate"]["R"])
    maps = Counter(tuple(winners(draws, races, lefts, k)) for k in range(n))
    distinct, (common, most) = len(maps), maps.most_common(1)[0]
    top3 = maps.most_common(3)
    sweeps = [m for m, _ in top3 if m.count("R") >= len(races) - 1 or m.count("R") <= 1]
    side = {"Republican" if m.count("R") >= len(races) - 1 else "Democratic" for m in sweeps}
    count = ["", "One", "Two", "All three"][len(sweeps)]
    core = (f"{'is a' if len(sweeps) == 1 else 'are'} {side.pop() + ' ' if len(side) == 1 else ''}"
            f"{'sweep' if len(sweeps) == 1 else 'sweeps'}, or close to it: when the close races break, they tend to "
            f"break together.")
    together = f"{count} of the three {core}" if sweeps else ""
    together_caption = f"{count} of the three most common combinations {core}" if sweeps else ""
    sen = f["senate"]
    pd_, pr, pi = (round(100 * sen[x]) for x in ("p_d_caucus_51", "p_r_50plus", "p_independents_decide"))
    names = ", ".join(NAMES.get(r, r) for r in races[:-1]) + " and " + NAMES.get(races[-1], races[-1])
    d = date.fromisoformat(post_day)
    src = (f"Our simulation, {date.fromisoformat(data_day).day} Oct: a sample of 1,000 of its 40,000 simulated "
           f"elections. King and Sanders count with Democrats; with 50–50 the Vice President decides.")
    head = f"1,000 of our simulated elections. {distinct} different results in the {len(races)} closest races."

    a = Slide(d, "", LAB, series=SERIES)
    a.headline(head, px=58)
    a.dek("Each row is one simulated election. Blue: the Democrat wins; red: the Republican; purple: an independent.",
          px=28)
    a.y, _ = wall(a, draws, races, lefts, list(range(12)), a.y + 8, 50)
    a.source(src)

    b = Slide(d, "", LAB, series=SERIES)
    b.headline(f"Even the most common result came up only {most} times in 1,000.", px=60)
    b.dek(f"The three combinations of the {len(races)} closest races we saw most often:", px=28)
    x0, cell = MARGIN + 190, 50
    for i, r in enumerate(races):
        b._put(x0 + i * cell + cell * 0.42, b.y + 4, CODE.get(r, r), "mono", 600, 20, LAB.ink2, ha="center", va="top")
    b.y += 42
    for m, c in top3:
        strip(b, b.y, x0, cell, list(m))
        b._put(MARGIN, b.y + cell * 0.42, f"{c} times", "mono", 600, 24, LAB.ink, va="center")
        b.y += cell + 8
    b.y += 16
    if together:
        b.text(together, "sans", 600, 30, LAB.ink2, after=0.8)
    b.text(f"Democrats hold the Senate in {pd_} of every 100 of our simulated elections, Republicans in {pr}"
           + (f", and in {pi} the new independents hold the balance." if pi else "."), "serif", 600, 36, after=0.6)
    b.note("Hundreds of routes to the same chance. On Tuesday, only one of them happens.", width=900, px=30)
    b.source(src)

    caption = (
        f"We played out the Senate 40,000 times. In a sample of 1,000 of those simulated elections, the "
        f"{len(races)} closest races came out {distinct} different ways, and even the most common combination came up "
        f"only {most} times.\n\n"
        f"Each row on the first slide is one simulated election: who wins {names}. Democrats hold the Senate in "
        f"{pd_} of every 100, Republicans in {pr}" + (f", and in {pi} the new independents hold the balance" if pi
                                                      else "") + ".\n\n"
        + (f"{together_caption}\n\n" if together_caption else "") +
        f"That's why one number can't tell you what election night will look like: the same chance arrives by "
        f"hundreds of routes. On Tuesday, only one of them happens.\n\n"
        f"Which combination are you expecting?\n\n"
        f"#midterms2026 #Senate #elections\n\n{DISCLAIMER}")
    x = (f"We played out the Senate 40,000 times. In 1,000 of those simulated elections the {len(races)} closest races "
         f"came out {distinct} different ways; the most common only {most} times. Democrats hold it in {pd_} of 100. "
         f"{LABEL}.")
    threads = (f"In 1,000 of our simulated elections, the {len(races)} closest Senate races came out {distinct} "
               f"different ways, and even the most common combination came up only {most} times. Democrats hold the "
               f"Senate in {pd_} of every 100, but by hundreds of different routes. On Tuesday only one happens. Which "
               f"one are you expecting?")
    posts = {"x": x, "threads": end(threads, LIMIT["threads"])}

    out = ROOT / "kits" / "daily" / f"{d.day:02d}-no-two-alike"
    out.mkdir(parents=True, exist_ok=True)
    problems = []
    for i, s in enumerate((a, b), 1):
        problems += [f"slide {i}: {p}" for p in s.layout_problems() + s.missing_glyphs() + text.slide_problems(s, ALLOW)]
        s.save(out / f"slide-{i}.jpg")
    alts = [f"Twelve of our simulated elections, one per row: for each, a square per race ({names}), blue where the "
            f"Democrat wins, red where the Republican wins, purple where an independent wins, and who holds the "
            f"Senate. No two rows are the same.",
            f"The three most common combinations of the {len(races)} closest races, which came up {top3[0][1]}, "
            f"{top3[1][1]} and {top3[2][1]} times in 1,000 simulated elections. Democrats hold the Senate in {pd_} of "
            f"every 100, Republicans in {pr}."]
    (out / "caption.txt").write_text(caption, encoding="utf-8")
    (out / "alt-text.txt").write_text("".join(f"slide-{i}.jpg: {t}\n" for i, t in enumerate(alts, 1)), encoding="utf-8")
    meta = {"threads_topic": "2026 Midterms", "instagram_first_comment": "Which combination are you expecting?"}
    lines = ["# Single posts (X and Threads through Buffer)", ""]
    for key in ("x", "threads"):
        lines += [f"## {'X' if key == 'x' else key.capitalize()} ({len(posts[key])} of {LIMIT[key]} characters; "
                  f"attach slide-1 to slide-2)", "", posts[key], ""]
        problems += [f"{key}: {len(posts[key])} characters" for _ in [0] if len(posts[key]) > LIMIT[key]]
    (out / "single-post.md").write_text("\n".join(lines), encoding="utf-8")
    for name, t in [("caption", caption), *posts.items()]:
        problems += [f"{name}: {p}" for p in text.check(t, caption=True, allow=ALLOW)]
    if reel:
        animate(out, d, draws, races, lefts, distinct, most, src)
        meta["reel"] = True
    (out / "meta.json").write_text(json.dumps(meta, indent=1, ensure_ascii=False), encoding="utf-8")
    (out / "checks.txt").write_text("\n".join(problems) or "all rules pass", encoding="utf-8")
    return out, problems


def animate(out: Path, d: date, draws: dict, races: list[str], lefts: dict, distinct: int, most: int, src: str):
    """9:16 Reel: simulated elections arrive one row at a time, then the count; the cover is the last frame."""
    import imageio_ffmpeg
    from PIL import Image
    w, h, fps = 1080, 1920, 30
    s = Slide(d, "", LAB, size=(w, h), series=SERIES)
    s.headline(f"1,000 simulated elections. {distinct} different results.", px=66)
    s.dek(f"Each row: who wins the {len(races)} closest Senate races. Blue Democrat, red Republican, purple independent.",
          px=28)
    y, rows = wall(s, draws, races, lefts, list(range(11)), s.y + 8, 50)
    note = s._put(MARGIN, y + 26, f"The most common came up only {most} times in 1,000.", "sans", 700, 34, LAB.ai,
                  va="top")
    s.source(src)
    if bad := s.layout_problems() + s.missing_glyphs():
        raise ValueError(f"reel layout: {bad}")
    step, t_end = 0.4, 1.0 + 0.4 * len(rows) + 3.0
    writer = imageio_ffmpeg.write_frames(str(out / "reel.mp4"), (w, h), fps=fps, codec="libx264", quality=8,
                                         macro_block_size=8, pix_fmt_in="rgb24", pix_fmt_out="yuv420p",
                                         output_params=["-movflags", "+faststart"])
    writer.send(None)
    frame = None
    for fr in range(int(t_end * fps)):
        now = fr / fps
        for i, parts in enumerate(rows):
            for p in parts:
                p.set_visible(now >= 1.0 + step * i)
        note.set_visible(now >= 1.0 + step * len(rows))
        s.fig.canvas.draw()
        frame = np.asarray(s.fig.canvas.buffer_rgba())[:, :, :3]
        writer.send(np.ascontiguousarray(frame))
    writer.close()
    Image.fromarray(frame).save(out / "reel-cover.jpg", quality=92, subsampling=0)
    plt.close(s.fig)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True, help="the forecast day to read")
    ap.add_argument("--post", required=True, help="the day it goes out")
    ap.add_argument("--data", type=Path, default=ROOT.parent / "simlab-data")
    ap.add_argument("--reel", action="store_true")
    a = ap.parse_args()
    out, problems = build(a.date, a.post, a.data, a.reel)
    print(out, "; ".join(problems) or "all rules pass")


if __name__ == "__main__":
    main()
