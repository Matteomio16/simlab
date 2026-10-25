"""One race from the Senate (Matteo, 25 Oct: a new format to test): two of our simulated elections where every race is
called but one, the last race decided by a tenth of a point each way, then how often control comes down to one race.
Read from draws.json (every 40th of the 40,000 simulated elections: draw k is election 40k + 1).
python -m simlab.publish.onerace --date 2026-10-24 --post 2026-10-26 --race AK [--reel]
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
SERIES = "One race left"
ALLOW = ()
NAMES = {"AK": "Alaska", "OH-S": "Ohio", "IA": "Iowa", "ME": "Maine", "MI": "Michigan", "KS": "Kansas",
         "MN": "Minnesota", "TX": "Texas", "NC": "North Carolina", "SC": "South Carolina", "NH": "New Hampshire"}
GREY = "#D6D9E2"


def tipping(draws: dict, lefts: dict) -> list[tuple]:
    """(margin, k, side, race) for each sampled election that is one race from flipping, no new independent seated."""
    sen, races = draws["seats"]["senate"], draws["races"]
    out = []
    for k in range(len(sen["R"])):
        r, i = sen["R"][k], sen["I"][k]
        if i != 2 or r not in (49, 50):  # King and Sanders are the only independents; R 50 holds with the VP
            continue
        m = {x: v[k] for x, v in races.items()}
        won = ({x: -v for x, v in m.items() if v < 0} if r == 50
               else {x: v for x, v in m.items() if v > 0 and lefts[x] == "D"})
        x = min(won, key=won.get)
        out.append((won[x], k, "R" if r == 50 else "D", x))
    return out


def seats(s: Slide, top: float, d: int, r: int, open_: int, cell: float = 74) -> float:
    """100 seats, Democrats (and the two independents who caucus with them) blue, Republicans red, open purple."""
    x0 = MARGIN + (s.width - 10 * cell) / 2 + cell / 2
    cols = [LAB.dem] * d + [LAB.ai] * open_ + [LAB.rep] * r
    for i, c in enumerate(cols):
        row, col = divmod(i, 10)
        s.ax.add_patch(plt.Circle((x0 + col * cell, top + row * cell + cell / 2), cell * 0.36, color=c, lw=0, zorder=3))
    return top + 10 * cell


def build(data_day: str, post_day: str, race: str, data: Path, reel: bool = False) -> tuple[Path, list[str]]:
    draws = json.loads((data / "derived" / data_day / "draws.json").read_text(encoding="utf-8"))
    f = json.loads((data / "derived" / data_day / "forecast.json").read_text(encoding="utf-8"))
    meta_r = json.loads((data / "derived" / data_day / "races.json").read_text(encoding="utf-8"))
    lefts = {x: f["races"][x].get("left_party", "D") for x in draws["races"]}
    rows = tipping(draws, lefts)
    n = len(draws["seats"]["senate"]["R"])
    close = [t for t in rows if t[0] < 1]
    per100 = round(100 * len(close) / n)
    top = Counter(t[3] for t in close).most_common(6)
    if top[0][0] != race:
        raise SystemExit(f"{race} isn't the most frequent deciding race ({top[0][0]} is)")
    pair = {side: min((t for t in rows if t[3] == race and t[2] == side), key=lambda t: t[0]) for side in ("D", "R")}
    cand = (meta_r.get(race) or meta_r["races"][race])["candidates"]
    dem, rep = cand["left"].split()[-1], cand["right"].split()[-1]
    state = NAMES[race]
    no = {side: f"{40 * t[1] + 1:,}" for side, t in pair.items()}
    tenth = "a tenth of a point" if max(t[0] for t in pair.values()) <= 0.1 else "less than half a point"
    d = date.fromisoformat(post_day)
    src = (f"Our simulation, {date.fromisoformat(data_day).day} Oct: a sample of 1,000 of its 40,000 simulated "
           f"elections. Independents King and Sanders count with Democrats; with 50–50 the Vice President decides.")

    a = Slide(d, "", LAB, series=SERIES)
    a.headline(f"Election night, simulated. Every race is called but one: {state}.", px=64)
    a.dek(f"Democrats 50, Republicans 49. Whoever wins {state} controls the Senate.", px=32)
    y = seats(a, a.y + 6, 50, 49, 1, cell=52) + 18
    a._put(MARGIN, y, "Democrats 50", "sans", 600, 30, LAB.dem, va="top")
    a._put(a.w / 2, y, state, "sans", 700, 30, LAB.ai, ha="center", va="top")
    a._put(a.w - MARGIN, y, "Republicans 49", "sans", 600, 30, LAB.rep, ha="right", va="top")
    a.source(src)

    b = Slide(d, "", LAB, series=SERIES)
    b.headline("Two of our simulated elections. Same 50–49, opposite Senates.", px=60)
    b.y += 10
    for side, who, result, col in (("D", dem, "Democrats hold the Senate, 51–49.", LAB.dem),
                                   ("R", rep, "50–50, and the Vice President's vote gives Republicans the Senate.",
                                    LAB.rep)):
        b.text(f"Election No. {no[side]}", "mono", 600, 26, LAB.ink2, after=0.3)
        b.text(f"{who} wins {state} by {tenth}.", "serif", 700, 44, col, after=0.35)
        b.text(result, "sans", 400, 32, LAB.ink, after=1.0)
    b.note(f"In {state}, a tenth of a point is a few hundred votes.", width=900, px=30)
    b.source(src)

    c = Slide(d, "", LAB, series=SERIES)
    c.headline(f"It isn't rare: {per100} in 100.", px=80)
    c.dek(f"In {per100} of every 100 of our simulated elections, control of the Senate came down to a single race "
          f"decided by less than a point. The races that decided it most often:", px=30)
    biggest = top[0][1]
    for name, k in top:
        c._put(MARGIN, c.y, NAMES.get(name, name), "sans", 600, 34, LAB.ink, va="top")
        x0, w = MARGIN + 290, c.width - 290 - 70
        c.ax.add_patch(plt.Rectangle((x0, c.y + 6), w * k / biggest, 34, color=LAB.ai if name == race else GREY,
                                     lw=0, zorder=2))
        c._put(c.w - MARGIN, c.y, f"{k}", "mono", 600, 32, LAB.ink, ha="right", va="top")
        c.y += 62
    c._put(c.w - MARGIN, c.y + 4, f"times in {n:,} simulated elections", "mono", 500, 22, LAB.ink2, ha="right", va="top")
    c.y += 60
    c.note("Every race: notapoll.org", width=520, px=30)
    c.source(src)

    caption = (
        f"Election night, simulated. In one of our 40,000 simulated elections, No. {no['D']}, every Senate race is "
        f"called but one. Democrats have 50 seats, Republicans 49. Whoever wins {state} controls the Senate. "
        f"{dem} wins it by {tenth}.\n\n"
        f"In another, No. {no['R']}, the night reaches the same 50–49 with only {state} left, and ends the other way: "
        f"{rep} wins it by {tenth}, the Senate is 50–50, and the Vice President's vote gives Republicans control.\n\n"
        f"It isn't a fluke. In {per100} of every 100 of our simulated elections, control of the Senate comes down to "
        f"a single race decided by less than a point, and {state} is the race that decides it most often.\n\n"
        f"These are simulations, not predictions: each one is a possible election night, played out from voter "
        f"personas reacting to the news.\n\n"
        f"Which race do you think decides the Senate?\n\n"
        f"#midterms2026 #Senate #{state}Senate #elections\n\n{DISCLAIMER}")
    x = (f"Simulated election No. {no['D']}: every Senate race called but one. Democrats 50, Republicans 49. "
         f"{state} decides, and {dem} wins it by {tenth}. In No. {no['R']}, {rep} does. {LABEL}.")
    threads = (f"In {per100} of every 100 of our simulated elections, the Senate comes down to one race decided by "
               f"less than a point. Most often it's {state}. In election No. {no['D']}, {dem} wins it by {tenth} and "
               f"Democrats hold the Senate; in No. {no['R']}, {rep} wins it by the same and Republicans do. Which "
               f"race do you think decides it?")
    short = (f"In {per100} of every 100 of our simulated elections, the Senate comes down to one race decided by less "
             f"than a point. Most often: {state}.")
    posts = {"x": x, "threads": end(threads, LIMIT["threads"]), "bluesky": end(short, LIMIT["bluesky"])}

    out = ROOT / "kits" / "daily" / f"{d.day:02d}-one-race"
    out.mkdir(parents=True, exist_ok=True)
    problems = []
    for i, s in enumerate((a, b, c), 1):
        problems += [f"slide {i}: {p}" for p in s.layout_problems() + s.missing_glyphs() + text.slide_problems(s, ALLOW)]
        s.save(out / f"slide-{i}.jpg")
    alts = [f"100 Senate seats as dots: 50 blue for Democrats, 49 red for Republicans and one purple, {state}, still "
            f"to be called.",
            f"Two simulated elections: in No. {no['D']} {dem} wins {state} by {tenth} and Democrats hold the Senate "
            f"51–49; in No. {no['R']} {rep} wins by the same and Republicans hold it 50–50 with the Vice President.",
            f"In {per100} of every 100 simulated elections, Senate control came down to one race decided by less than "
            f"a point. Most often: " + ", ".join(f"{NAMES.get(k, k)} {v} times in {n:,}" for k, v in top) + "."]
    (out / "caption.txt").write_text(caption, encoding="utf-8")
    (out / "alt-text.txt").write_text("".join(f"slide-{i}.jpg: {t}\n" for i, t in enumerate(alts, 1)), encoding="utf-8")
    meta = {"threads_topic": "2026 Midterms", "instagram_first_comment": "Which race do you think decides the Senate?"}
    lines = ["# Single posts (X and Threads through Buffer; Bluesky by hand)", ""]
    for key in ("x", "threads", "bluesky"):
        lines += [f"## {'X' if key == 'x' else key.capitalize()} ({len(posts[key])} of {LIMIT[key]} characters; "
                  f"attach slide-1 to slide-3)", "", posts[key], ""]
        problems += [f"{key}: {len(posts[key])} characters" for _ in [0] if len(posts[key]) > LIMIT[key]]
    (out / "single-post.md").write_text("\n".join(lines), encoding="utf-8")
    for name, t in [("caption", caption), *posts.items()]:
        problems += [f"{name}: {p}" for p in text.check(t, caption=True, allow=ALLOW)]
    if reel:
        animate(out, d, state, dem, rep, no, tenth, per100, src)
        meta["reel"] = True
    (out / "meta.json").write_text(json.dumps(meta, indent=1, ensure_ascii=False), encoding="utf-8")
    (out / "checks.txt").write_text("\n".join(problems) or "all rules pass", encoding="utf-8")
    return out, problems


def animate(out: Path, d: date, state: str, dem: str, rep: str, no: dict, tenth: str, per100: int, src: str):
    """9:16 Reel: the seats fill in, the last one pulses, then the two endings and how often it happens."""
    import imageio_ffmpeg
    from PIL import Image
    w, h, fps = 1080, 1920, 30
    cards = []

    def card(head: str, sub: str, d_: int, r_: int, open_: int, accent: str | None = None):
        s = Slide(d, "", LAB, size=(w, h), series=SERIES)
        s.headline(head, px=66)
        s.dek(sub, px=32)
        seats(s, s.y + 10, d_, r_, open_, cell=64)
        s.source(src)
        if bad := s.layout_problems() + s.missing_glyphs():
            raise ValueError(f"reel layout: {bad}")
        s.fig.canvas.draw()
        img = np.asarray(s.fig.canvas.buffer_rgba())[:, :, :3].copy()
        plt.close(s.fig)
        return img

    cards.append((card(f"Election night, simulated. One race left: {state}.", "Democrats 50, Republicans 49.",
                       50, 49, 1), 3.5))
    cards.append((card(f"Election No. {no['D']}: {dem} wins by {tenth}.", "Democrats hold the Senate, 51–49.",
                       51, 49, 0), 3.0))
    cards.append((card(f"Election No. {no['R']}: {rep} wins by {tenth}.",
                       "50–50: the Vice President's vote gives Republicans the Senate.", 50, 50, 0), 3.0))
    cards.append((card(f"In {per100} of every 100 simulated elections, one race this close decides the Senate.",
                       f"Most often: {state}. Every race: notapoll.org", 50, 49, 1), 3.5))
    writer = imageio_ffmpeg.write_frames(str(out / "reel.mp4"), (w, h), fps=fps, codec="libx264", quality=8,
                                         macro_block_size=8, pix_fmt_in="rgb24", pix_fmt_out="yuv420p",
                                         output_params=["-movflags", "+faststart"])
    writer.send(None)
    for img, secs in cards:
        for _ in range(int(secs * fps)):
            writer.send(np.ascontiguousarray(img))
    writer.close()
    Image.fromarray(cards[0][0]).save(out / "reel-cover.jpg", quality=92, subsampling=0)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True)
    ap.add_argument("--post", required=True)
    ap.add_argument("--race", default="AK")
    ap.add_argument("--data", type=Path, default=ROOT.parent / "simlab-data")
    ap.add_argument("--reel", action="store_true")
    a = ap.parse_args()
    out, problems = build(a.date, a.post, a.race, a.data, a.reel)
    print(out, "; ".join(problems) or "all rules pass")


if __name__ == "__main__":
    main()
