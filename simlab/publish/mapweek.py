"""The map post (Matteo, 25 Oct: one established format plus one new one): every Senate race as a tile, Cook's
toss-ups ringed, then Cook's toss-ups one by one with our chance and our expected vote, so the reader sees that a race
can be close in votes and still lean in simulated wins.
python -m simlab.publish.mapweek --date 2026-10-24 --post 2026-10-25 --data ../simlab-data
"""
from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

from . import racecards as rc
from . import specials, text
from .frame import DISCLAIMER, LABEL, MARGIN, Slide
from .launch import LIMIT, X_LINK
from .pollread import end
from .themes import LAB

ROOT = Path(__file__).resolve().parents[2]
SERIES = "The Senate map"
ALLOW = ("poll", "polls")
COOK = {"Tossup": "Toss-up", "Lean D": "Leans Democrat", "Likely D": "Likely Democrat", "Solid D": "Safe Democrat",
        "Lean R": "Leans Republican", "Likely R": "Likely Republican", "Solid R": "Safe Republican"}
NAMES = {"AK": "Alaska", "IA": "Iowa", "KS": "Kansas", "ME": "Maine", "MI": "Michigan", "OH": "Ohio", "TX": "Texas",
         "GA": "Georgia", "NC": "North Carolina", "NH": "New Hampshire", "MN": "Minnesota", "NE": "Nebraska"}


def vote(m: float, left: str) -> str:
    lead = round(50 + abs(m) / 2)
    return "50–50" if lead == 50 else f"{left if m > 0 else 'R'} {lead}–{100 - lead}"


def build(data_day: str, post_day: str, data: Path) -> tuple[Path, list[str]]:
    f = json.loads((data / "derived" / data_day / "forecast.json").read_text(encoding="utf-8"))
    races = f["races"]
    up = {k.removesuffix("-S"): x["p_dem_win"] for k, x in races.items()}
    cook = {k.removesuffix("-S"): COOK.get((x.get("benchmarks") or {}).get("cook"), "") for k, x in races.items()}
    tossups = sorted((k for k, c in cook.items() if c == "Toss-up"), key=lambda k: abs(up[k] - 0.5))
    ours = [k for k in up if rc.TOSS_UP[0] <= up[k] <= rc.TOSS_UP[1]]
    if len(ours) != 1 or len(tossups) < 3:
        raise SystemExit(f"the story needs one toss-up of ours and several of Cook's: ours {ours}, Cook {tossups}")
    us = NAMES[ours[0]]
    d, nd = date.fromisoformat(post_day), date.fromisoformat(data_day)
    n_cook = {3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight"}[len(tossups)]
    head = f"Cook calls {n_cook} Senate races toss-ups. Our simulation calls one."
    a = specials.tile_map(LAB, up, {k: "Toss-up" for k in tossups}, d, kicker="", series=SERIES, head=head, size=64,
                          run=str(f.get("run_id", "")).rsplit("-", 1)[-1][:7],
                          dek="Each square: the Democrat's wins in 100 simulated elections.",
                          ring=f"Ringed: Cook's toss-ups. Only {us} stays between 45 and 55 in ours.",
                          src=f"Simulation: {nd.day} Oct; in Nebraska, South Dakota and Montana, the independent's wins. "
                              f"Ratings: Cook Political Report.")

    b = Slide(d, "", LAB, series=SERIES)
    b.headline("Close in votes. Not always in wins.", px=72)
    b.text(f"Cook's {n_cook} toss-ups, in our simulation", "sans", 600, 30, LAB.ink2, after=0.8)
    rows = []
    for k in tossups:
        x = races[k if k in races else f"{k}-S"]
        p, left = x["p_dem_win"], {"D": "D", "I": "I"}.get(x.get("left_party", "D"), "D")
        chance = f"{left if p >= 0.5 else 'R'} {round(max(p, 1 - p) * 100)} in 100"
        rows.append((NAMES.get(k, k), vote(x["margin"]["p50"], left), chance))
    b._put(b.w - MARGIN - 300, b.y, "EXPECTED VOTE", "mono", 500, 22, LAB.ink2, ha="right", va="top")
    b._put(b.w - MARGIN, b.y, "WINS", "mono", 500, 22, LAB.ink2, ha="right", va="top")
    b.y += 40
    for name, v, c in rows:
        b.rule(LAB.hairline, after=14)
        b._put(MARGIN, b.y, name, "sans", 600, 36, LAB.ink, va="top")
        b._put(b.w - MARGIN - 300, b.y, v, "mono", 600, 34, LAB.ink, ha="right", va="top")
        b._put(b.w - MARGIN, b.y, c, "mono", 600, 34, LAB.ai if c.split()[1] in ("50", "51", "52", "53", "54", "55")
               else LAB.ink, ha="right", va="top")
        b.y += 36 * 1.3 + 8
    b.rule(LAB.hairline, after=30)
    widest = max(rows, key=lambda r: int(r[1].split()[-1].split("–")[0]) if "–" in r[1] else 50)[1]
    b.note(f"All {n_cook} are close in votes: none wider than {widest.split()[-1]}. But a small, steady edge decides "
           f"most simulated elections, so only {us} is a coin flip.", width=900, px=30)
    b.source(f"Simulation: {nd.day} Oct. Ratings: Cook Political Report. Expected vote: the middle result of 40,000 "
             f"simulated elections.")

    rest = [NAMES.get(k, k) for k in tossups if k != ours[0]]
    names = ", ".join(rest[:-1]) + " and " + rest[-1]
    n_rest = {2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven"}[len(rest)]
    caption = (
        f"Cook Political Report rates {n_cook} Senate races as toss-ups. In our social simulation, only {us} stays "
        f"that close: between 45 and 55 of every 100 simulated elections.\n\n"
        f"That isn't a disagreement about how close these races are. In votes, all {n_cook} are tight: our expected "
        f"vote is no wider than {widest.split()[-1]} in any of them. The difference is what we count. Cook rates how "
        f"competitive a race is; we play each one out 40,000 times and count who wins. A small edge that holds up "
        f"across most simulated elections turns a near-even vote into something like 60 in 100.\n\n"
        f"So {names} lean one way in our simulation without being safe for anyone.\n\n"
        f"Which of Cook's toss-ups would you call a coin flip?\n\n"
        f"#midterms2026 #Senate #elections\n\n{DISCLAIMER}")
    x_text = (f"Cook calls {n_cook} Senate races toss-ups. Our simulation calls one: {us}. In votes all {n_cook} are "
              f"close, none wider than {widest.split()[-1]}. In 40,000 simulated elections, a small edge wins most of "
              f"them. {LABEL}.")
    threads = (f"Cook rates {n_cook} Senate races as toss-ups. In our simulation only {us} is a coin flip. The other "
               f"{n_rest} are close in votes too, none wider than {widest.split()[-1]}, but a small, steady "
               f"edge wins most of the 40,000 simulated elections. Which of Cook's toss-ups would you call a coin "
               f"flip?")
    short = (f"Cook: {n_cook} Senate toss-ups. Our simulation: one, {us}. All {n_cook} are close in votes (none wider "
             f"than {widest.split()[-1]}), but a small edge wins most simulated elections.")
    posts = {"x": x_text, "threads": end(threads, LIMIT["threads"]), "bluesky": end(short, LIMIT["bluesky"])}

    out = ROOT / "kits" / "daily" / f"{d.day:02d}-map"
    out.mkdir(parents=True, exist_ok=True)
    problems = []
    for i, s in enumerate((a, b), 1):
        problems += [f"slide {i}: {x}" for x in s.layout_problems() + s.missing_glyphs() + text.slide_problems(s, ALLOW)]
        s.save(out / f"slide-{i}.jpg")
    alt1 = (f"Tile map of the 35 Senate races, each square coloured by how often the Democrat (or independent) wins in "
            f"our simulated elections. Cook's {n_cook} toss-ups are ringed; only {us} sits between 45 and 55.")
    alt2 = f"Cook's {n_cook} toss-ups with our expected vote and chance of winning: " + "; ".join(
        f"{n}: expected vote {v}, wins {c}" for n, v, c in rows) + "."
    (out / "caption.txt").write_text(caption, encoding="utf-8")
    (out / "alt-text.txt").write_text(f"slide-1.jpg: {alt1}\nslide-2.jpg: {alt2}\n", encoding="utf-8")
    (out / "meta.json").write_text(json.dumps({"threads_topic": "2026 Midterms",
                                               "instagram_first_comment": "Which of Cook's toss-ups would you call a "
                                                                          "coin flip?"}, indent=1), encoding="utf-8")
    lines = ["# Single posts (X and Threads through Buffer; Bluesky by hand)", ""]
    for k in ("x", "threads", "bluesky"):
        lines += [f"## {'X' if k == 'x' else k.capitalize()} ({len(posts[k])} of {LIMIT[k]} characters; attach "
                  f"slide-1 to slide-2)", "", posts[k], ""]
        problems += [f"{k}: {len(posts[k])} characters" for _ in [0] if len(posts[k]) > LIMIT[k]]
    (out / "single-post.md").write_text("\n".join(lines), encoding="utf-8")
    for name, s in [("caption", caption), *posts.items()]:
        problems += [f"{name}: {x}" for x in text.check(s, caption=True, allow=ALLOW)]
    (out / "checks.txt").write_text("\n".join(problems) or "all rules pass", encoding="utf-8")
    return out, problems


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True, help="the forecast day to read")
    ap.add_argument("--post", required=True, help="the day it goes out")
    ap.add_argument("--data", type=Path, default=ROOT.parent / "simlab-data")
    a = ap.parse_args()
    out, problems = build(a.date, a.post, a.data)
    print(out, "; ".join(problems) or "all rules pass")


if __name__ == "__main__":
    main()
