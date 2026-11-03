"""Final forecast (Matteo, 3 Nov: Election Day): one post for the Senate and one for the House, from the 3 Nov morning
run, each ending on how and when we'll check it against the official results.
python -m simlab.publish.final --date 2026-11-03 --post 2026-11-03 [--reel]
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
from .pollread import end
from .themes import LAB

ROOT = Path(__file__).resolve().parents[2]
SERIES = "Final forecast"
ALLOW = ("poll", "polls")
NAMES = {"AK": "Alaska", "IA": "Iowa", "KS": "Kansas", "OH-S": "Ohio", "TX": "Texas", "ME": "Maine", "MI": "Michigan",
         "NE": "Nebraska", "NC": "North Carolina", "MN": "Minnesota", "SC": "South Carolina", "FL-S": "Florida",
         "NH": "New Hampshire", "GA": "Georgia", "MS": "Mississippi", "LA": "Louisiana"}
PARTY = {"D": LAB.dem, "R": LAB.rep, "I": LAB.ai}


def split(m: float) -> str:
    """Expected vote as a two-way split, leader first: margin 1.8 -> '51–49'."""
    lead = round(50 + abs(m) / 2)
    return f"{lead}–{100 - lead}"


def lead(m: float, left: str, right: str, digits: int = 1) -> str:
    return "Tied" if abs(m) < 0.05 else f"{left if m > 0 else right} +{abs(m):.{digits}f}"


def surname(name: str) -> str:
    parts = [p for p in name.replace(",", "").split() if p not in ("Jr.", "Sr.", "II", "III", "IV")]
    return parts[-1]


def senate_rows(f: dict, meta: dict) -> list[dict]:
    out = []
    for r, x in f["races"].items():
        if r not in NAMES or not 0.1 < x["p_dem_win"] < 0.9:
            continue
        c = (meta.get(r) or meta["races"][r])["candidates"]
        left, right, m, p = surname(c["left"]), surname(c["right"]), x["margin"]["p50"], x["p_dem_win"]
        out.append({"state": NAMES[r], "m": m, "p": p, "who": left if p >= 0.5 else right,
                    "side": x.get("left_party", "D") if p >= 0.5 else "R", "chance": round(100 * max(p, 1 - p)),
                    "poll": (x.get("benchmarks") or {}).get("poll_avg"), "left": left, "right": right})
    return sorted(out, key=lambda r: abs(r["p"] - 0.5))


def house_rows(f: dict, hr: dict, n: int = 10) -> list[dict]:
    out = []
    for r, x in f["house"]["races"].items():
        if x.get("tier") != "simulate" or r not in hr:
            continue
        c = hr[r]["candidates"]
        left = surname((c.get("D") or c.get("I") or ["?"])[0])
        right = surname((c.get("R") or ["?"])[0])
        p, m = x["p_dem_win"], x["margin"]["p50"]
        out.append({"seat": r, "m": m, "p": p, "who": left if p >= 0.5 else right, "side": "D" if p >= 0.5 else "R",
                    "chance": round(100 * max(p, 1 - p))})
    return sorted(out, key=lambda r: abs(r["p"] - 0.5))[:n]


def table(s: Slide, rows: list[dict], cols: list[tuple[str, float, str]], key: str, top: float, step: float = 56):
    """Rows of the closest races: name, who wins in 100 (party colour), expected vote, and a poll average if given."""
    for head, x, ha in cols:
        s._put(x, top, head, "mono", 600, 20, LAB.ink2, ha=ha, va="top")
    y = top + 40
    for r in rows:
        s._put(cols[0][1], y, r[key], "sans", 600, 30, LAB.ink, va="top")
        s._put(cols[1][1], y, f"{r['who']} {r['chance']}", "sans", 700, 30, PARTY[r["side"]], va="top")
        s._put(cols[2][1], y, split(r["m"]), "mono", 600, 28, LAB.ink, va="top")
        if len(cols) > 3:
            s._put(cols[3][1], y, "–" if r["poll"] is None else lead(r["poll"], r["left"], r["right"]), "mono", 500,
                   26, LAB.ink2, ha="right", va="top")
        y += step
    return y


def big(s: Slide, items: list[tuple[str, str, str]], top: float) -> float:
    """Big numbers side by side: (number, label, colour)."""
    w = s.width / len(items)
    for i, (num, label, col) in enumerate(items):
        x = MARGIN + i * w
        s._put(x, top, num, "hero", 700, 120, col, va="top")
        for j, line in enumerate(s.wrap(label, "sans", 600, 26, w - 24)):
            s._put(x, top + 150 + j * 34, line, "sans", 600, 26, LAB.ink, va="top")
    return top + 150 + 2 * 34 + 20


def bar(s: Slide, parts: list[tuple[float, str]], top: float, h: float = 44) -> float:
    x = MARGIN
    for share, col in parts:
        s.ax.add_patch(plt.Rectangle((x, top), s.width * share, h, color=col, lw=0, zorder=3))
        x += s.width * share
    return top + h


def histogram(s: Slide, dist: dict, top: float, h: float, lo: int, hi: int, line: int, mid: int) -> float:
    """Democratic seats across the simulated elections: blue at or above the majority line, red below."""
    seats = list(range(lo, hi + 1))
    vals = [dist.get(str(k), 0.0) for k in seats]
    peak = max(vals)
    w = s.width / len(seats)
    base = top + h
    for i, (k, v) in enumerate(zip(seats, vals)):
        bh = h * v / peak
        s.ax.add_patch(plt.Rectangle((MARGIN + i * w, base - bh), w * 0.86, bh,
                                     color=LAB.dem if k >= line else LAB.rep, lw=0, zorder=3))
    xl = MARGIN + (line - lo) * w - w * 0.07
    s.ax.plot([xl, xl], [top - 40, base + 6], color=LAB.ink, lw=2, zorder=4)
    s._put(xl + 8, top - 44, f"{line} for control", "mono", 600, 22, LAB.ink, va="top")
    for k, ha in ((lo, "left"), (mid, "center"), (hi, "right")):
        x = MARGIN if ha == "left" else s.w - MARGIN if ha == "right" else MARGIN + (k - lo) * w + w * 0.43
        s._put(x, base + 12, str(k), "mono", 500, 22, LAB.ink2, ha=ha, va="top")
    return base + 48


def closing(s: Slide, chamber: str, simulated: str):
    s.headline("Now we find out.", px=88)
    s.y += 6
    s.text(f"Since 12 October, polls haven't moved these numbers. Only the news has: every day, voter personas built "
           f"from real survey answers reacted to the day's stories{simulated}. Polls only checked us.", "serif", 500,
           32, after=0.7)
    s.text("That was the experiment: how close can a social simulation get to a real election?", "serif", 700, 34,
           after=0.7)
    s.text(f"Once the official results are in, we'll score every {chamber} race against them, next to the poll "
           f"average, prediction markets and Cook, and publish all of it, hits and misses. Some states take days to "
           f"count; we'll wait for them.", "serif", 500, 32, after=0.8)
    s.note("We can't wait to see how this holds.", width=760, px=32)


def save(out: Path, slides: list[Slide], caption: str, posts: dict, alts: list[str], meta: dict) -> list[str]:
    out.mkdir(parents=True, exist_ok=True)
    problems = []
    for i, s in enumerate(slides, 1):
        problems += [f"slide {i}: {p}" for p in s.layout_problems() + s.missing_glyphs() + text.slide_problems(s, ALLOW)]
        s.save(out / f"slide-{i}.jpg")
    (out / "caption.txt").write_text(caption, encoding="utf-8")
    (out / "alt-text.txt").write_text("".join(f"slide-{i}.jpg: {t}\n" for i, t in enumerate(alts, 1)), encoding="utf-8")
    md = ["# Single posts (X and Threads through Buffer)", ""]
    for key in ("x", "threads"):
        md += [f"## {'X' if key == 'x' else key.capitalize()} ({len(posts[key])} of {LIMIT[key]} characters; attach "
               f"slide-1 to slide-{len(slides)})", "", posts[key], ""]
        problems += [f"{key}: {len(posts[key])} characters" for _ in [0] if len(posts[key]) > LIMIT[key]]
    (out / "single-post.md").write_text("\n".join(md), encoding="utf-8")
    for name, t in [("caption", caption), *posts.items()]:
        problems += [f"{name}: {p}" for p in text.check(t, caption=True, allow=ALLOW)]
    (out / "meta.json").write_text(json.dumps(meta, indent=1, ensure_ascii=False), encoding="utf-8")
    return problems


def senate(f: dict, meta: dict, d: date, when: str, src: str, reel: bool, start: dict) -> tuple[Path, list[str]]:
    sen = f["senate"]
    pd_, pr, pi = (round(100 * sen[x]) for x in ("p_d_caucus_51", "p_r_50plus", "p_independents_decide"))
    mk = (sen.get("benchmarks") or {}).get("market")
    rows = senate_rows(f, meta)

    a = Slide(d, "", LAB, series=SERIES)
    a.headline("Our final Senate forecast.", px=84)
    a.dek(f"40,000 simulated elections, run on {when} with the last day of news.", px=30)
    items = [(str(pd_), "in 100: Democrats hold the Senate", LAB.dem), (str(pr), "Republicans hold 50 or more", LAB.rep)]
    if pi:
        items.append((str(pi), "the new independents decide", LAB.ai))
    a.y = big(a, items, a.y + 10)
    a.y = bar(a, [(sen["p_d_caucus_51"], LAB.dem), (sen["p_independents_decide"], LAB.ai), (sen["p_r_50plus"], LAB.rep)],
              a.y) + 30
    if mk is not None:
        a.text(f"Prediction markets this morning: Republicans {round(100 * mk)} in 100.", "sans", 600, 28, LAB.ink2,
               after=0.4)
    a.text(f"When we started, on 12 October: Republicans {round(100 * start['senate']['p_r_50plus'])} in 100.", "sans",
           600, 28, LAB.ink2)
    a.source(src)

    b = Slide(d, "", LAB, series=SERIES)
    b.headline("The races that decide it", px=72)
    b.dek("Who wins in 100 of our simulated elections, our expected vote, and the poll average.", px=28)
    table(b, rows, [("RACE", MARGIN, "left"), ("WINS, IN 100", MARGIN + 290, "left"), ("EXPECTED", MARGIN + 590, "left"),
                    ("POLL AVERAGE", b.w - MARGIN, "right")], "state", b.y + 10)
    b.source(src)

    c = Slide(d, "", LAB, series=SERIES)
    closing(c, "Senate", "")
    c.source(src)

    lines = "\n".join(f"{r['state']}: {r['who']} {r['chance']} in 100, expected vote {split(r['m'])}, poll average "
                      f"{'n/a' if r['poll'] is None else lead(r['poll'], r['left'], r['right']).replace('Tied', 'tied')}"
                      for r in rows)
    caption = (
        f"Our final Senate forecast, from this morning's run: Democrats hold the Senate in {pd_} of every 100 simulated "
        f"elections, Republicans in {pr}" + (f", and in {pi} the new independents decide" if pi else "") + "."
        + (f" Prediction markets give Republicans {round(100 * mk)} in 100." if mk is not None else "") + "\n\n"
        f"The races that decide it (who wins in 100 simulated elections, our expected vote, the poll average):\n"
        f"{lines}\n\n"
        f"Since 12 October, polls haven't moved these numbers. Only the news has: every day, voter personas built from "
        f"real survey answers reacted to the day's stories, and polls only checked us. That was the experiment.\n\n"
        f"Once the official results are in, we'll score every race against them, next to the poll average, prediction "
        f"markets and Cook, and publish all of it, hits and misses. Some states take days to count, so we'll wait for "
        f"them. We can't wait to see how this holds.\n\n"
        f"What's your call for the Senate?\n\n"
        f"#midterms2026 #ElectionDay #Senate #elections\n\n{DISCLAIMER}")
    x = (f"Our final Senate forecast: Democrats hold it in {pd_} of 100 simulated elections, Republicans in {pr}. For "
         f"three weeks only the news moved our numbers. Once official results are in, we score every race, hits and "
         f"misses. {LABEL}.")
    threads = (f"Our final Senate forecast: Democrats hold the Senate in {pd_} of every 100 of our simulated elections, "
               f"Republicans in {pr}. Closest: {rows[0]['state']}, {rows[1]['state']} and {rows[2]['state']}. Since 12 "
               f"October only the news has moved our numbers; polls only checked us. Once the official results are "
               f"in, we'll score every race, hits and misses. We can't wait to see how close a social simulation gets. "
               f"What's your call?")
    posts = {"x": x, "threads": end(threads, LIMIT["threads"])}
    alts = [f"Our final Senate forecast: Democrats hold the Senate in {pd_} of 100 simulated elections, Republicans in "
            f"{pr}" + (f", the new independents decide in {pi}" if pi else "") + ".",
            "The closest Senate races, each with who wins in 100 simulated elections, our expected vote and the poll "
            "average: " + "; ".join(f"{r['state']} {r['who']} {r['chance']}" for r in rows) + ".",
            "Now we find out: since 12 October only the news moved our numbers; once official results are in we'll "
            "score every race against them, next to the poll average, prediction markets and Cook."]
    meta_out = {"threads_topic": "2026 Midterms", "instagram_first_comment": "What's your call for the Senate?"}
    out = ROOT / "kits" / "daily" / f"{d.day:02d}-final-senate"
    problems = save(out, [a, b, c], caption, posts, alts, meta_out)
    if reel:
        parts = [(sen["p_d_caucus_51"], LAB.dem), (sen["p_independents_decide"], LAB.ai), (sen["p_r_50plus"], LAB.rep)]
        animate(out, d, src, lambda s: (s.headline("Our final Senate forecast.", px=84),
                                        bar(s, parts, big(s, items, s.y + 30))))
        meta_out["reel"] = True
        (out / "meta.json").write_text(json.dumps(meta_out, indent=1, ensure_ascii=False), encoding="utf-8")
    (out / "checks.txt").write_text("\n".join(problems) or "all rules pass", encoding="utf-8")
    return out, problems


def house(f: dict, hr: dict, d: date, when: str, src: str, reel: bool, start: dict) -> tuple[Path, list[str]]:
    h = f["house"]
    seats = h["seats"]["D"]
    pd_, pr = round(100 * h["p_d_majority"]), round(100 * h["p_r_majority"])
    mid, lo, hi = int(seats["p50"]), int(seats["p10"]), int(seats["p90"])
    mk = (h.get("benchmarks") or {}).get("market")
    mk = None if mk is None else 1 - mk  # stored as the Republicans' chance of a majority
    line = h.get("majority", 218)
    rows = house_rows(f, hr)
    sim = sum(1 for x in h["races"].values() if x.get("tier") == "simulate")

    a = Slide(d, "", LAB, series=SERIES)
    a.headline("Our final House forecast.", px=84)
    a.dek(f"40,000 simulated elections, run on {when} with the last day of news.", px=30)
    a.y = big(a, [(str(pd_), "in 100: Democrats win the House", LAB.dem),
                  (str(pr), "Republicans keep it", LAB.rep)], a.y + 10)
    a.y = histogram(a, seats["dist"], a.y + 30, 170, lo - 15, hi + 15, line, mid)
    a.text(f"Middle result: {mid} Democratic seats; 8 in 10 of our simulated elections fall between {lo} and {hi}.",
           "sans", 600, 26, LAB.ink2, after=0.4)
    if mk is not None:
        a.text(f"Prediction markets this morning: Democrats {round(100 * mk)} in 100. When we started, on 12 "
               f"October, we had Democrats at {round(100 * start['house']['p_d_majority'])}.", "sans", 600, 26,
               LAB.ink2)
    a.source(src)

    b = Slide(d, "", LAB, series=SERIES)
    b.headline("The closest seats", px=72)
    b.dek(f"Of the {sim} House races we simulate every day: who wins in 100 of our simulated elections, and our "
          f"expected vote.", px=28)
    table(b, rows, [("SEAT", MARGIN, "left"), ("WINS, IN 100", MARGIN + 290, "left"), ("EXPECTED", MARGIN + 620, "left")],
          "seat", b.y + 10)
    b.source(src)

    c = Slide(d, "", LAB, series=SERIES)
    closing(c, "House", f" in the {sim} closest seats, and statistics covered the rest")
    c.source(src)

    lines = "\n".join(f"{r['seat']}: {r['who']} {r['chance']} in 100, expected vote {split(r['m'])}" for r in rows[:6])
    caption = (
        f"Our final House forecast, from this morning's run: Democrats win the House in {pd_} of every 100 simulated "
        f"elections, Republicans keep it in {pr}. The middle result is {mid} Democratic seats, with {line} needed for "
        f"control; 8 in 10 of our simulated elections fall between {lo} and {hi}."
        + (f" Prediction markets give Democrats {round(100 * mk)} in 100, a lot more than we do." if mk is not None
           else "") + "\n\n"
        f"The closest seats we simulate (who wins in 100, our expected vote):\n{lines}\n\n"
        f"Since 12 October, polls haven't moved these numbers. In the {sim} closest seats, voter personas built from "
        f"real survey answers reacted to each day's news; statistics covered the rest. That was the experiment.\n\n"
        f"Once the official results are in, we'll score every race against them, next to the poll average, prediction "
        f"markets and Cook, and publish all of it, hits and misses. We can't wait to see how this holds.\n\n"
        f"Who do you think wins the House?\n\n"
        f"#midterms2026 #ElectionDay #House #elections\n\n{DISCLAIMER}")
    x = (f"Our final House forecast: Democrats win it in {pd_} of 100 simulated elections; middle result {mid} seats. "
         + (f"Prediction markets say {round(100 * mk)}. " if mk is not None else "")
         + f"Once official results are in, we score every race, hits and misses. {LABEL}.")
    threads = (f"Our final House forecast: Democrats win the House in {pd_} of every 100 of our simulated elections, "
               f"with {mid} seats in the middle result and {line} needed. "
               + (f"Prediction markets give Democrats {round(100 * mk)} in 100, much more than we do. " if mk is not None
                  else "")
               + "Once the official results are in, we'll score every race and see who read it better. Who do you "
                 "think wins the House?")
    posts = {"x": x, "threads": end(threads, LIMIT["threads"])}
    alts = [f"Our final House forecast: Democrats win in {pd_} of 100 simulated elections, Republicans keep it in {pr}. "
            f"A histogram of Democratic seats, blue at {line} and above, red below; middle result {mid}, 8 in 10 between "
            f"{lo} and {hi}.",
            "The closest House seats we simulate, with who wins in 100 simulated elections and our expected vote: "
            + "; ".join(f"{r['seat']} {r['who']} {r['chance']}" for r in rows) + ".",
            "Now we find out: since 12 October only the news moved our numbers; once official results are in we'll "
            "score every race against them, next to the poll average, prediction markets and Cook."]
    meta_out = {"threads_topic": "2026 Midterms", "instagram_first_comment": "Who do you think wins the House?"}
    out = ROOT / "kits" / "daily" / f"{d.day:02d}-final-house"
    problems = save(out, [a, b, c], caption, posts, alts, meta_out)
    if reel:
        animate(out, d, src, lambda s: (s.headline("Our final House forecast.", px=84),
                                        histogram(s, seats["dist"], big(s, [(str(pd_), "in 100: Democrats win the House",
                                                                             LAB.dem), (str(pr), "Republicans keep it",
                                                                                        LAB.rep)], s.y + 30) + 30,
                                                  170, lo - 15, hi + 15, line, mid)))
        meta_out["reel"] = True
        (out / "meta.json").write_text(json.dumps(meta_out, indent=1, ensure_ascii=False), encoding="utf-8")
    (out / "checks.txt").write_text("\n".join(problems) or "all rules pass", encoding="utf-8")
    return out, problems


def animate(out: Path, d: date, src: str, draw):
    """9:16 Reel: the slide's marks appear one after another, then hold; the cover is the last frame."""
    import imageio_ffmpeg
    from PIL import Image
    w, h, fps = 1080, 1920, 30
    s = Slide(d, "", LAB, size=(w, h), series=SERIES)
    n_text, n_patch = len(s.ax.texts), len(s.ax.patches)
    draw(s)
    s.source(src)
    if bad := s.layout_problems() + s.missing_glyphs():
        raise ValueError(f"reel layout: {bad}")
    marks = s.ax.texts[n_text:] + s.ax.patches[n_patch:] + s.ax.lines[:]
    marks = [m for m in marks if m.get_visible()]
    t0, t1, t_end = 0.6, 3.6, 7.0
    writer = imageio_ffmpeg.write_frames(str(out / "reel.mp4"), (w, h), fps=fps, codec="libx264", quality=8,
                                         macro_block_size=8, pix_fmt_in="rgb24", pix_fmt_out="yuv420p",
                                         output_params=["-movflags", "+faststart"])
    writer.send(None)
    frame = None
    for fr in range(int(t_end * fps)):
        now = fr / fps
        shown = int(len(marks) * min(1.0, max(0.0, (now - t0) / (t1 - t0))))
        for i, m in enumerate(marks):
            m.set_visible(i < shown)
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
    day = a.data / "derived" / a.date
    f = json.loads((day / "forecast.json").read_text(encoding="utf-8"))
    meta = json.loads((day / "races.json").read_text(encoding="utf-8"))
    hr = json.loads((day / "house_races.json").read_text(encoding="utf-8"))
    run = date.fromisoformat(a.date)
    when = f"the morning of {run.day} {run:%B}"
    start = json.loads((a.data / "derived" / "2026-10-12" / "forecast.json").read_text(encoding="utf-8"))
    src = f"Our simulation, {run.day} {run:%b} {run.year}: 40,000 simulated elections."
    for out, problems in (senate(f, meta, date.fromisoformat(a.post), when,
                                 src + " Poll average: VoteHub (CC BY 4.0), Wikipedia (CC BY-SA 4.0).", a.reel, start),
                          house(f, hr, date.fromisoformat(a.post), when, src, a.reel, start)):
        print(out, "; ".join(problems) or "all rules pass")


if __name__ == "__main__":
    main()
