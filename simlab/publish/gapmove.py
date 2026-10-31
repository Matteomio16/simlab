"""More can move than the gap (Matteo, 30 Oct: final-days special, after the people grid): in the closest Senate races,
how many could still change their vote (groups.json pi, as in persuadable.py) against the gap in our expected vote.
python -m simlab.publish.gapmove --date 2026-10-31 --post 2026-11-01 [--reel]
"""
from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from . import text
from .frame import DISCLAIMER, LABEL, MARGIN, Slide
from .launch import LIMIT
from .persuadable import GREY, SOURCE, shares
from .pollread import end
from .themes import LAB

ROOT = Path(__file__).resolve().parents[2]
SERIES = "Who can still move"
ALLOW = ("survey",)
NAMES = {"AK": ("Alaska", "Alaskans"), "IA": ("Iowa", "Iowans"), "KS": ("Kansas", "Kansans"),
         "OH-S": ("Ohio", "Ohioans"), "TX": ("Texas", "Texans"), "ME": ("Maine", "Mainers"),
         "MI": ("Michigan", "Michiganders"), "NE": ("Nebraska", "Nebraskans"), "NC": ("North Carolina", "North Carolinians")}
SCALE = 25.0


def rows_for(f: dict, groups: dict, meta: dict, n: int = 6) -> list[dict]:
    """The n closest Senate races by our expected vote: who leads, by how much, and how many could still move."""
    out = []
    for r, x in sorted(f["races"].items(), key=lambda kv: abs(kv[1]["margin"]["p50"])):
        if r not in NAMES or r not in groups or not 0.2 < x["p_dem_win"] < 0.8:
            continue
        c = (meta.get(r) or meta["races"][r])["candidates"]
        m = x["margin"]["p50"]
        out.append({"race": r, "state": NAMES[r][0], "people": NAMES[r][1], "gap": abs(m),
                    "leader": (c["left"] if m > 0 else c["right"]).split()[-1], "pi": round(100 * shares(groups[r])["pi"])})
    return out[:n]


def bars(s: Slide, rows: list[dict], top: float, step: float = 108) -> tuple[float, list]:
    """Per race: the state and who leads, a purple bar for those who could still move, a dark sliver for the gap."""
    x0 = MARGIN + 250
    w = s.w - MARGIN - x0 - 150
    arts, y = [], top
    for r in rows:
        parts = [s._put(MARGIN, y, r["state"], "sans", 700, 34, LAB.ink, va="top"),
                 s._put(MARGIN, y + 46, f"{r['leader']} +{r['gap']:.1f}", "mono", 500, 22, LAB.ink2, va="top")]
        n0 = len(s.ax.patches)
        s.ax.add_patch(plt.Rectangle((x0, y + 4), w * r["pi"] / SCALE, 30, color=LAB.ai, lw=0, zorder=3))
        s.ax.add_patch(plt.Rectangle((x0, y + 50), max(3.0, w * r["gap"] / SCALE), 18, color=LAB.ink, lw=0, zorder=3))
        parts += s.ax.patches[n0:]
        parts.append(s._put(x0 + w * r["pi"] / SCALE + 12, y + 2, f"{r['pi']} could move", "sans", 700, 26, LAB.ai,
                            va="top"))
        parts.append(s._put(x0 + max(3.0, w * r["gap"] / SCALE) + 12, y + 44, f"gap {r['gap']:.1f}", "mono", 600, 22,
                            LAB.ink, va="top"))
        arts.append(parts)
        y += step
    return y, arts


def build(data_day: str, post_day: str, data: Path, reel: bool = False) -> tuple[Path, list[str]]:
    day = data / "derived" / data_day
    f = json.loads((day / "forecast.json").read_text(encoding="utf-8"))
    groups = json.loads((day / "groups.json").read_text(encoding="utf-8"))
    meta = json.loads((day / "races.json").read_text(encoding="utf-8"))
    rows = rows_for(f, groups, meta)
    first = rows[0]
    d = date.fromisoformat(post_day)
    when = f"{date.fromisoformat(data_day).day} Oct"
    src = (f"Purple: per 100 adult citizens, whose vote is still open (Cooperative Election Study, 2018 and 2022). "
           f"Dark: the gap in our expected vote, in points, {when}.")
    lo, hi = min(r["gap"] for r in rows), max(r["gap"] for r in rows)
    head = (f"{first['state']} is {first['gap']:.1f} points apart. {first['pi']} in 100 {first['people']} could still "
            f"change their vote.")

    a = Slide(d, "", LAB, series=SERIES)
    a.headline(head, px=58)
    a.dek(f"The {len(rows)} closest Senate races: who could still change their vote, against the gap between the "
          f"candidates.", px=28)
    a.y, _ = bars(a, rows, a.y + 14)
    a.source(src)

    b = Slide(d, "", LAB, series=SERIES)
    b.headline("Who could still change their vote?", px=72)
    b.y += 6
    b.text("People who, in the 2018 and 2022 midterms, were undecided before the election or voted against the plan "
           "they had given, among those like them: same party, race and education.", "serif", 500, 34, after=0.8)
    b.text("Most of them won't switch. But in every one of these races, a small share of them would be enough.",
           "serif", 700, 34, after=0.8)
    most = max(rows, key=lambda r: r["pi"])
    ind = round(100 * shares(groups[most["race"]])["independent"])
    b.text(f"{most['state']} has the most: {most['pi']} in 100, and {ind} of them are independents.", "serif", 500, 34,
           after=0.8)
    b.note("They are the people our voter personas stand in for: every day, the simulation asks how the news moves "
           "them.", width=900, px=30)
    b.source(src)

    lines = "\n".join(f"{r['state']}: {r['leader']} ahead by {r['gap']:.1f}; {r['pi']} in 100 could still change their "
                      f"vote." for r in rows)
    caption = (
        f"The {len(rows)} closest Senate races, by our expected vote, are {lo:.1f} to {hi:.1f} points apart. In every "
        f"one, far more people could still change their vote.\n\n{lines}\n\n"
        f"\"Could still change\" means undecided, or likely to vote against their stated plan, judging by how people "
        f"like them behaved in the 2018 and 2022 midterms. Most of them won't switch. In races this close, a small "
        f"share of them would be enough.\n\n"
        f"Which race do you think moves before Tuesday?\n\n"
        f"#midterms2026 #Senate #elections\n\n{DISCLAIMER}")
    x = (f"{first['state']} is {first['gap']:.1f} points apart, and {first['pi']} in 100 {first['people']} could still "
         f"change their vote. In all of the {len(rows)} closest Senate races, far more people could still move than "
         f"separate the candidates. {LABEL}.")
    threads = (f"The {len(rows)} closest Senate races are {lo:.1f} to {hi:.1f} points apart in our expected vote. In "
               f"each, far more people could still change their vote: {first['pi']} in 100 in {first['state']}, "
               f"{rows[1]['pi']} in {rows[1]['state']}, {rows[2]['pi']} in {rows[2]['state']}. Most won't switch, but a "
               f"small share would be enough. Which race moves before Tuesday?")
    posts = {"x": x, "threads": end(threads, LIMIT["threads"])}

    out = ROOT / "kits" / "daily" / f"{d.day:02d}-more-than-the-gap"
    out.mkdir(parents=True, exist_ok=True)
    problems = []
    for i, s in enumerate((a, b), 1):
        problems += [f"slide {i}: {p}" for p in s.layout_problems() + s.missing_glyphs() + text.slide_problems(s, ALLOW)]
        s.save(out / f"slide-{i}.jpg")
    alts = [f"For the {len(rows)} closest Senate races, a purple bar for how many in 100 adult citizens could still "
            f"change their vote and a thin dark bar for the gap in our expected vote: "
            + "; ".join(f"{r['state']} {r['pi']} against {r['gap']:.1f}" for r in rows) + ".",
            "Who could still change their vote: people who were undecided or voted against their stated plan in the "
            "2018 and 2022 midterms, among those like them. Most won't switch, but a small share would be enough."]
    (out / "caption.txt").write_text(caption, encoding="utf-8")
    (out / "alt-text.txt").write_text("".join(f"slide-{i}.jpg: {t}\n" for i, t in enumerate(alts, 1)), encoding="utf-8")
    meta_out = {"threads_topic": "2026 Midterms", "instagram_first_comment": "Which race do you think moves before Tuesday?"}
    md = ["# Single posts (X and Threads through Buffer)", ""]
    for key in ("x", "threads"):
        md += [f"## {'X' if key == 'x' else key.capitalize()} ({len(posts[key])} of {LIMIT[key]} characters; attach "
               f"slide-1 to slide-2)", "", posts[key], ""]
        problems += [f"{key}: {len(posts[key])} characters" for _ in [0] if len(posts[key]) > LIMIT[key]]
    (out / "single-post.md").write_text("\n".join(md), encoding="utf-8")
    for name, t in [("caption", caption), *posts.items()]:
        problems += [f"{name}: {p}" for p in text.check(t, caption=True, allow=ALLOW)]
    if reel:
        animate(out, d, head, rows, src)
        meta_out["reel"] = True
    (out / "meta.json").write_text(json.dumps(meta_out, indent=1, ensure_ascii=False), encoding="utf-8")
    (out / "checks.txt").write_text("\n".join(problems) or "all rules pass", encoding="utf-8")
    return out, problems


def animate(out: Path, d: date, head: str, rows: list[dict], src: str):
    """9:16 Reel: one race at a time; the cover is the last frame."""
    import imageio_ffmpeg
    from PIL import Image
    w, h, fps = 1080, 1920, 30
    s = Slide(d, "", LAB, size=(w, h), series=SERIES)
    s.headline(head, px=58)
    _, arts = bars(s, rows, s.y + 20)
    s.source(src)
    if bad := s.layout_problems() + s.missing_glyphs():
        raise ValueError(f"reel layout: {bad}")
    t0, step = 1.2, 1.0
    t_end = t0 + step * len(arts) + 2.5
    writer = imageio_ffmpeg.write_frames(str(out / "reel.mp4"), (w, h), fps=fps, codec="libx264", quality=8,
                                         macro_block_size=8, pix_fmt_in="rgb24", pix_fmt_out="yuv420p",
                                         output_params=["-movflags", "+faststart"])
    writer.send(None)
    frame = None
    for fr in range(int(t_end * fps)):
        now = fr / fps
        for i, parts in enumerate(arts):
            for p in parts:
                p.set_visible(now >= t0 + step * i)
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
