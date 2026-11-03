"""Final maps (Matteo, 3 Nov): the whole Senate and House maps, every race coloured by its label (safe, likely, leans,
toss-up; racecards.verdict's thresholds), with the seat count on top if every race goes to the side our simulation
favors, toss-ups included.
python -m simlab.publish.finalmap --date 2026-11-03 --post 2026-11-03 [--reel]
"""
from __future__ import annotations

import argparse
import json
from datetime import date
from math import ceil, sqrt
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch

from . import text
from .frame import DISCLAIMER, LABEL, MARGIN, Slide
from .launch import LIMIT
from .pollread import end
from .racecards import TOSS_UP
from .specials import TILE, lum, mix
from .themes import LAB

ROOT = Path(__file__).resolve().parents[2]
SERIES = "Final forecast"
ALLOW = ()
ORDER = ["Safe D", "Likely D", "Leans D", "Toss-up", "Leans R", "Likely R", "Safe R"]
NAMES = {"AK": "Alaska", "IA": "Iowa", "KS": "Kansas", "OH": "Ohio", "TX": "Texas", "ME": "Maine", "MI": "Michigan",
         "NE": "Nebraska", "NC": "North Carolina", "MN": "Minnesota", "SC": "South Carolina", "FL": "Florida",
         "NH": "New Hampshire", "GA": "Georgia"}


def label(p: float) -> str:
    if TOSS_UP[0] <= p <= TOSS_UP[1]:
        return "Toss-up"
    q, side = max(p, 1 - p), "D" if p > 0.5 else "R"
    return f"Safe {side}" if q > 0.85 else f"Likely {side}" if q > 0.65 else f"Leans {side}"


def colour(cat: str, independent: bool = False) -> str:
    if cat == "Toss-up":
        return LAB.ai
    base = (LAB.ind if independent else LAB.dem) if cat.endswith("D") else LAB.rep
    return {"Safe": base, "Likely": mix(base, LAB.paper, 0.68), "Leans": mix(base, LAB.paper, 0.4)}[cat.split()[0]]


def seatbar(s: Slide, groups: list[tuple[int, str, bool]], total: int, line: int, top: float, h: float = 34) -> float:
    """Every seat in a row, grouped: (count, fill, outline only). A tick marks control."""
    x = MARGIN
    for n, col, hollow in groups:
        w = s.width * n / total
        s.ax.add_patch(plt.Rectangle((x, top), w, h, facecolor=LAB.paper if hollow else col, edgecolor=col,
                                     lw=1.5 if hollow else 0, zorder=3))
        x += w
    xl = MARGIN + s.width * line / total
    s.ax.plot([xl, xl], [top - 8, top + h + 8], color=LAB.ink, lw=2, zorder=4)
    return top + h


def legend(s: Slide, counts: dict, top: float) -> float:
    """Two rows: the Democratic side and toss-ups, then the Republican side."""
    for row, cats in enumerate((ORDER[:4], ORDER[4:])):
        x, y = MARGIN, top + row * 34
        for cat in cats:
            t = f"{cat.replace(' D', ' Dem').replace(' R', ' Rep')} {counts.get(cat, 0)}"
            s.ax.add_patch(plt.Rectangle((x, y + 3), 20, 20, color=colour(cat), lw=0, zorder=3))
            s._put(x + 28, y, t, "sans", 600, 20, LAB.ink, va="top")
            x += 28 + len(t) * 10.5 + 26
    return top + 70


def numbers(s: Slide, items: list[tuple[int, str, str]], top: float) -> float:
    w = s.width / len(items)
    for i, (n, who, col) in enumerate(items):
        s._put(MARGIN + i * w, top, str(n), "hero", 700, 84, col, va="top")
        s._put(MARGIN + i * w, top + 98, who, "sans", 700, 26, col, va="top")
    return top + 136


def senate(f: dict, meta: dict, d: date, src: str, reel: bool) -> tuple[Path, list[str]]:
    sen, up = f["senate"], {}
    for r, x in f["races"].items():
        up[r.split("-")[0]] = (x["p_dem_win"], x.get("left_party", "D"))
    nu = sen["not_up"]
    won = {"D": 0, "R": 0, "I": 0}
    counts = {}
    for p, left in up.values():
        won[left if p > 0.5 else "R"] += 1
        counts[label(p)] = counts.get(label(p), 0) + 1
    dem, rep, ind = nu["D"] + nu["I"] + won["D"], nu["R"] + won["R"], won["I"]
    tos = sorted((k for k, (p, _) in up.items() if label(p) == "Toss-up"), key=lambda k: up[k][0])

    a = Slide(d, "", LAB, series=SERIES)
    a.headline("Our final Senate map", px=64)
    items = [(dem, "Democrats", LAB.dem), (rep, "Republicans", LAB.rep)] + ([(ind, "Independents", LAB.ind)] if ind else [])
    a.y = numbers(a, items, a.y + 4)
    groups = [(nu["D"] + nu["I"], LAB.dem, True)]
    for cat in ORDER:
        sides = [(p, l) for p, l in up.values() if label(p) == cat]
        if cat == "Toss-up":
            groups += [(sum(1 for p, _ in sides if p > 0.5), LAB.ai, False)]
            groups += [(sum(1 for p, _ in sides if p <= 0.5), mix(LAB.ai, LAB.rep, 0.6), False)]
        else:
            groups.append((len(sides), colour(cat), False))
    groups.append((nu["R"], LAB.rep, True))
    a.y = seatbar(a, groups, 100, 50, a.y + 6) + 14
    a.text("Every race given to the side ahead in our simulated elections, toss-ups included; outlined: seats not "
           "up this year. On each state, the favorite's chance in 100.", "sans", 500, 22, LAB.ink2, after=0.4)
    size, gap = 58, 6
    x0 = MARGIN + (a.width - 12 * (size + gap) + gap) / 2
    top = a.y + 4
    tiles = []
    for k, (row, c) in sorted(TILE.items(), key=lambda kv: -max(up.get(kv[0], (1, ""))[0],
                                                                  1 - up.get(kv[0], (1, ""))[0])):
        x, y = x0 + c * (size + gap), top + row * (size + gap)
        n0, t0 = len(a.ax.patches), len(a.ax.texts)
        if k in up:
            p, left = up[k]
            col = colour(label(p), left == "I" and p > 0.5)
            a.ax.add_patch(FancyBboxPatch((x, y), size, size, boxstyle="round,pad=0,rounding_size=6", color=col, lw=0,
                                          zorder=2))
            fg = "#FFFFFF" if lum(col) < 0.6 else LAB.ink
            a._put(x + size / 2, y + 21, k, "sans", 700, 22, fg, ha="center", va="center", zorder=4)
            a._put(x + size / 2, y + 42, f"{round(100 * max(p, 1 - p))}", "mono", 500, 17, fg, ha="center",
                   va="center", zorder=4)
        else:
            a.ax.add_patch(FancyBboxPatch((x, y), size, size, boxstyle="round,pad=0,rounding_size=6", fill=False,
                                          ec=LAB.baseline, lw=1.2, zorder=2))
            a._put(x + size / 2, y + size / 2, k, "sans", 400, 18, LAB.muted, ha="center", va="center", zorder=4)
        tiles.append(a.ax.patches[n0:] + a.ax.texts[t0:])
    a.y = top + 8 * (size + gap) + 8
    a.y = legend(a, counts, a.y)
    a.source(src)

    tos_names = ", ".join(NAMES.get(k, k) for k in tos)
    cnt = lambda c: counts.get(c, 0)
    caption = (
        f"Our final Senate map. Give every race to the side ahead in our simulated elections, toss-ups included, and "
        f"the Senate comes out Democrats {dem}, Republicans {rep}" + (f", independents {ind}" if ind else "")
        + " (King and Sanders count with Democrats).\n\n"
        f"Safe Democratic {cnt('Safe D')}, likely {cnt('Likely D')}, leaning {cnt('Leans D')}. Toss-ups "
        f"{cnt('Toss-up')}" + (f": {tos_names}" if tos else "") + f". Leaning Republican {cnt('Leans R')}, likely "
        f"{cnt('Likely R')}, safe {cnt('Safe R')}.\n\n"
        f"That's one map. Across all our simulated elections, Democrats hold the Senate in "
        f"{round(100 * sen['p_d_caucus_51'])} of every 100, so some of these colours will flip. Tonight we start "
        f"finding out which. Once the official results are in, we'll score every race, hits and misses.\n\n"
        f"Which state do you think we have wrong?\n\n#midterms2026 #ElectionDay #Senate #elections\n\n{DISCLAIMER}")
    x = (f"Our final Senate map, every race to the side we favor: Democrats {dem}, Republicans {rep}. Toss-ups: "
         f"{tos_names or 'none'}. Once official results are in, we score every race. {LABEL}.")
    threads = (f"Our final Senate map. Give every race to the side ahead in our simulated elections and it's "
               f"Democrats {dem}, Republicans {rep}. The toss-ups: {tos_names or 'none'}. That's one map; across all of "
               f"them Democrats hold the Senate in {round(100 * sen['p_d_caucus_51'])} of 100. Which state do you think "
               f"we have wrong?")
    alt = (f"A tile map of the 50 states. The 35 Senate races are coloured from safe Democratic to safe Republican, "
           f"toss-ups in purple" + (f" ({tos_names})" if tos else "") + f". Giving every race to its favorite: "
           f"Democrats {dem}, Republicans {rep}.")
    return save(ROOT / "kits" / "daily" / f"{d.day:02d}-final-senate-map", a, caption, x, threads, alt, reel, tiles,
                "Which state do you think we have wrong?", src, lambda s: draw_senate_reel(s, up, items, groups))


def house(f: dict, hr: dict, d: date, src: str, reel: bool) -> tuple[Path, list[str]]:
    h = f["house"]
    seats, counts = {}, {}
    dem = rep = 0
    for k, v in hr.items():
        if k == "date":
            continue
        st = k.split("-")[0]
        x = h["races"].get(k)
        if x is None:  # uncontested, or both candidates from one party
            parties = [p for p, names in v["candidates"].items() if names]
            p = 1.0 if parties and parties[0] != "R" else 0.0
        else:
            p = x["p_dem_win"]
        cat = label(p)
        counts[cat] = counts.get(cat, 0) + 1
        dem, rep = dem + (p > 0.5), rep + (p <= 0.5)
        seats.setdefault(st, []).append(p)
    line = h.get("majority", 218)
    mid = int(h["seats"]["D"]["p50"])

    a = Slide(d, "", LAB, series=SERIES)
    a.headline("Our final House map", px=64)
    a.y = numbers(a, [(dem, "Democrats", LAB.dem), (rep, "Republicans", LAB.rep)], a.y + 4)
    groups = [(counts.get(c, 0), colour(c), False) for c in ORDER]
    a.y = seatbar(a, groups, 435, line, a.y + 6) + 14
    a.text(f"Every seat given to the side ahead in our simulated elections, toss-ups included; {line} for control. "
           f"Each square is one district.", "sans", 500, 22, LAB.ink2, after=0.5)
    size, gap = 62, 5
    x0 = MARGIN + (a.width - 12 * (size + gap) + gap) / 2
    top = a.y + 4
    tiles = []
    for k, (row, c) in TILE.items():
        x, y = x0 + c * (size + gap), top + row * (size + gap)
        n0, t0 = len(a.ax.patches), len(a.ax.texts)
        a.ax.add_patch(FancyBboxPatch((x, y), size, size, boxstyle="round,pad=0,rounding_size=5", color="#ECEAF2", lw=0,
                                      zorder=2))
        a._put(x + 5, y + 3, k, "mono", 600, 14, LAB.ink2, va="top", zorder=4)
        ps = sorted(seats.get(k, []), reverse=True)
        n = len(ps)
        cols = max(1, ceil(sqrt(n)))
        cell = min(22.0, (size - 10) / cols, (size - 24) / ceil(n / cols)) if n else 0
        for i, p in enumerate(ps):
            r_, c_ = divmod(i, cols)
            a.ax.add_patch(plt.Rectangle((x + 5 + c_ * cell, y + 21 + r_ * cell), cell * 0.82, cell * 0.82,
                                         color=colour(label(p)), lw=0, zorder=3))
        tiles.append(a.ax.patches[n0:] + a.ax.texts[t0:])
    a.y = top + 8 * (size + gap) + 8
    a.y = legend(a, counts, a.y)
    a.source(src)

    cnt = lambda c: counts.get(c, 0)
    caption = (
        f"Our final House map. Give every seat to the side ahead in our simulated elections, toss-ups included, and "
        f"the House comes out Democrats {dem}, Republicans {rep}, with {line} needed for control.\n\n"
        f"Safe Democratic {cnt('Safe D')}, likely {cnt('Likely D')}, leaning {cnt('Leans D')}. Toss-ups "
        f"{cnt('Toss-up')}. Leaning Republican {cnt('Leans R')}, likely {cnt('Likely R')}, safe {cnt('Safe R')}.\n\n"
        f"That's one map. Toss-ups split both ways in our simulated elections, so the middle result is {mid} "
        f"Democratic seats, and Democrats win the House in {round(100 * h['p_d_majority'])} of every 100. Tonight we "
        f"start finding out which colours hold. Once the official results are in, we'll score every seat, hits and "
        f"misses.\n\n"
        f"Which seat do you think we have wrong?\n\n#midterms2026 #ElectionDay #House #elections\n\n{DISCLAIMER}")
    x = (f"Our final House map, every seat to the side we favor: Democrats {dem}, Republicans {rep}, {line} for "
         f"control. {cnt('Toss-up')} toss-ups. Once official results are in, we score every seat. {LABEL}.")
    threads = (f"Our final House map. Give every seat to the side ahead in our simulated elections and it's Democrats "
               f"{dem}, Republicans {rep}, with {line} needed. {cnt('Toss-up')} seats are toss-ups, and across all our "
               f"simulated elections Democrats win the House in {round(100 * h['p_d_majority'])} of 100. Which seat "
               f"do you think we have wrong?")
    alt = (f"A tile map of the 50 states, each filled with one small square per House district, coloured from safe "
           f"Democratic to safe Republican, toss-ups in purple. Giving every seat to its favorite: Democrats {dem}, "
           f"Republicans {rep}; {line} for control.")
    return save(ROOT / "kits" / "daily" / f"{d.day:02d}-final-house-map", a, caption, x, threads, alt, reel, tiles,
                "Which seat do you think we have wrong?", src, None)


def draw_senate_reel(s: Slide, up: dict, items: list, groups: list):
    s.headline("Our final Senate map", px=64)
    s.y = numbers(s, items, s.y + 4)
    s.y = seatbar(s, groups, 100, 50, s.y + 6) + 20


def save(out: Path, a: Slide, caption: str, x: str, threads: str, alt: str, reel: bool, tiles: list, question: str,
         src: str, _draw) -> tuple[Path, list[str]]:
    out.mkdir(parents=True, exist_ok=True)
    problems = [f"slide 1: {p}" for p in a.layout_problems() + a.missing_glyphs() + text.slide_problems(a, ALLOW)]
    posts = {"x": x, "threads": end(threads, LIMIT["threads"])}
    meta = {"threads_topic": "2026 Midterms", "instagram_first_comment": question}
    if reel:
        animate(out, a, tiles)
        meta["reel"] = True
    a.save(out / "slide-1.jpg")
    (out / "caption.txt").write_text(caption, encoding="utf-8")
    (out / "alt-text.txt").write_text(f"slide-1.jpg: {alt}\n", encoding="utf-8")
    md = ["# Single posts (X and Threads through Buffer)", ""]
    for key in ("x", "threads"):
        md += [f"## {'X' if key == 'x' else key.capitalize()} ({len(posts[key])} of {LIMIT[key]} characters; attach "
               f"slide-1)", "", posts[key], ""]
        problems += [f"{key}: {len(posts[key])} characters" for _ in [0] if len(posts[key]) > LIMIT[key]]
    (out / "single-post.md").write_text("\n".join(md), encoding="utf-8")
    for name, t in [("caption", caption), *posts.items()]:
        problems += [f"{name}: {p}" for p in text.check(t, caption=True, allow=ALLOW)]
    (out / "meta.json").write_text(json.dumps(meta, indent=1, ensure_ascii=False), encoding="utf-8")
    (out / "checks.txt").write_text("\n".join(problems) or "all rules pass", encoding="utf-8")
    return out, problems


def animate(out: Path, a: Slide, tiles: list):
    """A 4:5 Reel of the slide itself: the states fill in one after another, most certain first; the cover is the
    finished map."""
    import imageio_ffmpeg
    from PIL import Image
    fig = a.fig
    w, h = (int(v) for v in fig.canvas.get_width_height())
    fps, t0, t1, t_end = 30, 0.8, 4.8, 8.0
    writer = imageio_ffmpeg.write_frames(str(out / "reel.mp4"), (w, h), fps=fps, codec="libx264", quality=8,
                                         macro_block_size=8, pix_fmt_in="rgb24", pix_fmt_out="yuv420p",
                                         output_params=["-movflags", "+faststart"])
    writer.send(None)
    frame = None
    for fr in range(int(t_end * fps)):
        now = fr / fps
        shown = int(len(tiles) * min(1.0, max(0.0, (now - t0) / (t1 - t0))))
        for i, parts in enumerate(tiles):
            for p in parts:
                p.set_visible(i < shown)
        fig.canvas.draw()
        frame = np.asarray(fig.canvas.buffer_rgba())[:, :, :3]
        writer.send(np.ascontiguousarray(frame))
    writer.close()
    for parts in tiles:
        for p in parts:
            p.set_visible(True)
    Image.fromarray(frame).save(out / "reel-cover.jpg", quality=92, subsampling=0)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True, help="the forecast day to read")
    ap.add_argument("--post", required=True, help="the day it goes out")
    ap.add_argument("--data", type=Path, default=ROOT.parent / "simlab-data")
    ap.add_argument("--reel", action="store_true")
    a = ap.parse_args()
    day = a.data / "derived" / a.date
    f = json.loads((day / "forecast.json").read_text(encoding="utf-8"))
    meta = json.loads((day / "races.json").read_text(encoding="utf-8"))
    hr = json.loads((day / "house_races.json").read_text(encoding="utf-8"))
    run = date.fromisoformat(a.date)
    src = f"Our simulation, {run.day} {run:%b} {run.year}. Toss-up 45–55 in 100, leans to 65, likely to 85, safe above."
    post = date.fromisoformat(a.post)
    for out, problems in (senate(f, meta, post, src, a.reel), house(f, hr, post, src, a.reel)):
        print(out, "; ".join(problems) or "all rules pass")


if __name__ == "__main__":
    main()
