"""Who can still move (Matteo, 25 Oct: a new format to test): 100 figures for a state's adult citizens, the ones whose
vote is still open lit in purple, then who they are. Shares from groups.json (n, pi, mu; docs/engine-design.md 3.1).
python -m simlab.publish.persuadable --race TX --date 2026-10-24 --post 2026-10-25 [--reel]
"""
from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch

from . import text
from .frame import DISCLAIMER, LABEL, MARGIN, Slide
from .launch import LIMIT
from .pollread import end
from .themes import LAB

ROOT = Path(__file__).resolve().parents[2]
SERIES = "Who can still move"
ALLOW = ("survey",)
STATES = {"TX": ("Texas", "Texans"), "AK": ("Alaska", "Alaskans"), "OH-S": ("Ohio", "Ohioans"),
          "ME": ("Maine", "Mainers"), "IA": ("Iowa", "Iowans")}
GREY = "#D6D9E2"
SOURCE = ("Still open: undecided, or voting against their stated plan, among people like them in the 2018 and 2022 "
          "midterms (Cooperative Election Study).")


def shares(groups: dict) -> dict:
    n = sum(x["n"] for x in groups.values())
    out = {"pi": sum(x["n"] * x["pi"] for x in groups.values()) / n,
           "mu": sum(x["n"] * x["mu"] for x in groups.values()) / n}
    for key, test in (("independent", lambda k: k.split(" / ")[0] == "Independent"),
                      ("no_degree", lambda k: k.endswith("No four-year college degree")),
                      ("of_color", lambda k: k.split(" / ")[1] == "non-white")):
        out[key] = sum(x["n"] * x["pi"] for k, x in groups.items() if test(k)) / n
    return out


def figure(ax, cx: float, cy: float, h: float, color: str, z: float = 3):
    """A person: a round head over rounded shoulders, `h` tall, centred on (cx, cy)."""
    r = h * 0.2
    ax.add_patch(plt.Circle((cx, cy - h * 0.28), r, color=color, lw=0, zorder=z))
    w = h * 0.62
    ax.add_patch(FancyBboxPatch((cx - w / 2, cy - h * 0.02), w, h * 0.5, boxstyle=f"round,pad=0,rounding_size={h * 0.24}",
                                color=color, lw=0, zorder=z))


def lit(k: int, seed: int = 7) -> list[int]:
    """Which of the 100 places are purple: scattered, the same every time."""
    return sorted(np.random.default_rng(seed).choice(100, size=k, replace=False).tolist())


def grid(s: Slide, k: int, top: float, cell: float, on: list[int] | None = None) -> float:
    x0 = MARGIN + (s.width - 10 * cell) / 2 + cell / 2
    on = lit(k) if on is None else on
    for i in range(100):
        r, c = divmod(i, 10)
        figure(s.ax, x0 + c * cell, top + r * cell + cell / 2, cell * 0.78, LAB.ai if i in on else GREY)
    return top + 10 * cell


def build(race: str, data_day: str, post_day: str, data: Path, reel: bool = False) -> tuple[Path, list[str]]:
    groups = json.loads((data / "derived" / data_day / "groups.json").read_text(encoding="utf-8"))[race]
    sh = shares(groups)
    state, people = STATES[race]
    k, mob = round(sh["pi"] * 100), round(sh["mu"] * 100)
    ind, nod, col = (round(sh[x] * 100) for x in ("independent", "no_degree", "of_color"))
    d = date.fromisoformat(post_day)
    src = SOURCE.format(state=state)
    head = f"100 {people}. Only {k} could still change their vote."

    a = Slide(d, "", LAB, series=SERIES)
    a.headline(head, px=68)
    a.dek(f"Each figure is 1 in 100 adult citizens of {state}. In purple, those whose vote is still open.", px=30)
    a.y = grid(a, k, a.y + 4, 62) + 24
    a._put(MARGIN, a.y, f"{k} could still change who they vote for", "sans", 600, 28, LAB.ai, va="top")
    a._put(a.w - MARGIN, a.y, f"{100 - k} are set", "sans", 600, 28, LAB.ink2, ha="right", va="top")
    a.source(src)

    b = Slide(d, "", LAB, series=SERIES)
    b.headline(f"Who the {k} are", px=80)
    b.y += 10
    for n, label in ((ind, "are independents"), (nod, "have no four-year college degree"),
                     (col, f"are {people} of color")):
        b._put(MARGIN, b.y, f"{n} of {k}", "hero", 700, 46, LAB.ai, va="top")
        b._put(MARGIN + 190, b.y + 10, label, "sans", 600, 32, LAB.ink, va="top")
        b.y += 70
        cell = min(66, b.width / k)
        for i in range(k):
            figure(b.ax, MARGIN + cell / 2 + i * cell, b.y + cell / 2, cell * 0.8, LAB.ai if i < n else GREY)
        b.y += cell + 34
    b.y += 6
    b.text(f"And {mob} in 100 could still decide whether to vote at all.", "serif", 600, 34, after=0.7)
    b.note("These are the people our voter personas stand in for: every day, the simulation asks how the news moves "
           "them.", width=900, px=30)
    b.source(src)

    caption = (
        f"Who decides the {state} Senate race? By our estimate, about {k} in every 100 adult {people} could still "
        f"change who they vote for: undecided, or likely to switch before voting, judging by how people like them "
        f"behaved in the last two midterms. The other {100 - k} have, for the most part, made up their minds.\n\n"
        f"Who are the {k}? {ind.__str__().capitalize()} are independents. {nod} have no four-year college degree. "
        f"{col} are {people} of color. And {mob} in 100 could still decide whether to vote at all.\n\n"
        f"These are the people our social simulation is built around. Every day, voter personas built from real "
        f"survey answers stand in for groups like them and react to the news, and only the share of each group that "
        f"can still move, moves.\n\n"
        f"{people}: do you know anyone who still hasn't decided?\n\n"
        f"#midterms2026 #{state} #{state}Senate #elections\n\n{DISCLAIMER}")
    x = (f"100 {people}. By our estimate only {k} could still change their vote in the Senate race; {ind} of them are "
         f"independents and {nod} have no four-year degree. Everyone else has mostly decided. {LABEL}.")
    threads = (f"Who actually decides the {state} Senate race? By our estimate, about {k} in every 100 adult {people} "
               f"could still change their vote, judging by how people like them behaved in past midterms. {ind} of "
               f"the {k} are independents; {nod} have no four-year degree. {people}: do you know anyone who still "
               f"hasn't decided?")
    short = (f"100 {people}: by our estimate only {k} could still change their Senate vote. {ind} of them are "
             f"independents, {nod} have no four-year degree.")
    posts = {"x": x, "threads": end(threads, LIMIT["threads"]), "bluesky": end(short, LIMIT["bluesky"])}

    out = ROOT / "kits" / "daily" / f"{d.day:02d}-who-can-move"
    out.mkdir(parents=True, exist_ok=True)
    problems = []
    for i, s in enumerate((a, b), 1):
        problems += [f"slide {i}: {p}" for p in s.layout_problems() + s.missing_glyphs() + text.slide_problems(s, ALLOW)]
        s.save(out / f"slide-{i}.jpg")
    alt1 = (f"A grid of 100 small figures standing for {state}'s adult citizens. {k} are purple, scattered through the "
            f"grid: those who could still change who they vote for. The other {100 - k} are grey.")
    alt2 = (f"Who the {k} are: {ind} are independents, {nod} have no four-year college degree, {col} are {people} of "
            f"color. And {mob} in 100 could still decide whether to vote at all.")
    (out / "caption.txt").write_text(caption, encoding="utf-8")
    (out / "alt-text.txt").write_text(f"slide-1.jpg: {alt1}\nslide-2.jpg: {alt2}\n", encoding="utf-8")
    meta = {"threads_topic": "2026 Midterms",
            "instagram_first_comment": f"{people}: do you know anyone who still hasn't decided?"}
    lines = ["# Single posts (X and Threads through Buffer; Bluesky by hand)", ""]
    for key in ("x", "threads", "bluesky"):
        lines += [f"## {'X' if key == 'x' else key.capitalize()} ({len(posts[key])} of {LIMIT[key]} characters; "
                  f"attach slide-1 to slide-2)", "", posts[key], ""]
        problems += [f"{key}: {len(posts[key])} characters" for _ in [0] if len(posts[key]) > LIMIT[key]]
    (out / "single-post.md").write_text("\n".join(lines), encoding="utf-8")
    for name, t in [("caption", caption), *posts.items()]:
        problems += [f"{name}: {p}" for p in text.check(t, caption=True, allow=ALLOW)]
    if reel:
        animate(out, d, head, state, k, src)
        meta["reel"] = True
    (out / "meta.json").write_text(json.dumps(meta, indent=1, ensure_ascii=False), encoding="utf-8")
    (out / "checks.txt").write_text("\n".join(problems) or "all rules pass", encoding="utf-8")
    return out, problems


def animate(out: Path, d: date, head: str, state: str, k: int, src: str):
    """9:16 Reel: 100 grey figures appear, then the open ones light up purple one by one; the cover is the last frame."""
    import imageio_ffmpeg
    from PIL import Image
    w, h, fps = 1080, 1920, 30
    s = Slide(d, "", LAB, size=(w, h), series=SERIES)
    s.headline(head, px=72)
    s.dek(f"Each figure is 1 in 100 adult citizens of {state}.", px=30)
    top, cell = s.y + 10, 62
    x0 = MARGIN + (s.width - 10 * cell) / 2 + cell / 2
    on = lit(k)
    figs = []
    for i in range(100):
        r, c = divmod(i, 10)
        n0 = len(s.ax.patches)
        figure(s.ax, x0 + c * cell, top + r * cell + cell / 2, cell * 0.78, GREY)
        figs.append(s.ax.patches[n0:])
    y = top + 10 * cell + 30
    note = s._put(MARGIN, y, f"In purple: the {k} whose vote is still open.", "sans", 600, 34, LAB.ai, va="top")
    s.source(src)
    if bad := s.layout_problems() + s.missing_glyphs():
        raise ValueError(f"reel layout: {bad}")
    t_show, t_lit, t_end = 1.5, 2.2, 2.2 + 0.35 * k + 2.5
    writer = imageio_ffmpeg.write_frames(str(out / "reel.mp4"), (w, h), fps=fps, codec="libx264", quality=8,
                                         macro_block_size=8, pix_fmt_in="rgb24", pix_fmt_out="yuv420p",
                                         output_params=["-movflags", "+faststart"])
    writer.send(None)
    frame = None
    for f in range(int(t_end * fps)):
        now = f / fps
        for i, parts in enumerate(figs):
            for p in parts:
                p.set_visible(now >= t_show * i / 100)
                lit_at = t_lit + 0.35 * on.index(i) if i in on else None
                p.set_color(LAB.ai if lit_at is not None and now >= lit_at else GREY)
        note.set_visible(now >= t_lit + 0.35 * k)
        s.fig.canvas.draw()
        frame = np.asarray(s.fig.canvas.buffer_rgba())[:, :, :3]
        writer.send(np.ascontiguousarray(frame))
    writer.close()
    Image.fromarray(frame).save(out / "reel-cover.jpg", quality=92, subsampling=0)
    plt.close(s.fig)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--race", default="TX")
    ap.add_argument("--date", required=True, help="the forecast day to read")
    ap.add_argument("--post", required=True, help="the day it goes out")
    ap.add_argument("--data", type=Path, default=ROOT.parent / "simlab-data")
    ap.add_argument("--reel", action="store_true")
    a = ap.parse_args()
    out, problems = build(a.race, a.date, a.post, a.data, a.reel)
    print(out, "; ".join(problems) or "all rules pass")


if __name__ == "__main__":
    main()
