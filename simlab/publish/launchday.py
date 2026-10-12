"""The launch post (Mon 12 Oct, 14:00 Paris) and, from then, the template for the daily forecast post:
python -m simlab.publish.launchday --date 2026-10-12 --data ../simlab-data [--preview]

Reads derived/<date>/forecast.json (docs/engine-design.md §7) and writes kits/daily/<DD>-forecast/: slide 1 The
Chamber (Senate control as a split, as on the race cards), then the closest races and the biggest mover on race
cards, caption.txt, alt-text.txt, single-post.md (X, Threads, Bluesky) and meta.json for buffer.py. --preview stamps
every slide as a preview (for review on pilot numbers; never posted).
"""
from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

from . import racecards as rc
from . import specials, text
from .frame import DISCLAIMER, LABEL, SITE
from .kit import COOK, featured, poll_txt, race_meta
from .launch import LIMIT
from .themes import LAB

ROOT = Path(__file__).resolve().parents[2]
SERIES = "Daily forecast"
ALLOW = ("poll", "polls")


def races(f: dict, day: date, kicker: str, source: str) -> list[dict]:
    run = str(f.get("run_id", "unknown")).rsplit("-", 1)[-1][:7]
    out = []
    for rid, x in f["races"].items():
        if rid.startswith("US"):
            continue
        b = x.get("benchmarks") or {}
        m = race_meta(rid, {})
        m["left_party"] = x.get("left_party", m.get("left_party", "D"))
        out.append(m | {"rid": rid, "run": None, "day": day,  # no run code on slides (Matteo, 12 Oct)
                        "kicker": kicker, "p": float(x["p_dem_win"]),
                        "prev": None, "today": (x.get("today") or {}).get("p_dem_win"),
                        "lo": x["margin"]["p10"], "mid": x["margin"]["p50"], "hi": x["margin"]["p90"],
                        "poll": poll_txt(b.get("poll_avg"), m["left_party"]), "market": b.get("market"),
                        "cook": COOK.get(b.get("cook"), b.get("cook")) or "n/a", "change": "First public forecast",
                        "benchmarks": b, "source": source})
    return out


def side(r: dict) -> tuple[str, int]:
    """Who's ahead and their chance in 100, for the texts: ('Democrats', 59) or ('Republicans', 59)."""
    left = {"D": "Democrats", "I": "the independent", "O": r.get("state", "")}[r.get("left_party", "D")]
    n = round(r["p"] * 100)
    return (left, n) if n >= 50 else ("Republicans", 100 - n)


def line(r: dict) -> str:
    who, n = side(r)
    return f"{r['state']}: {who} win {n} of every 100 simulated elections"


def market(r: dict) -> str:
    """The market price, named by side, since our headline may name the other party: "markets: Democrats 73%"."""
    if r.get("market") is None:
        return "no market price"
    left = {"D": "Democrats", "I": "the independent", "O": r.get("state", "")}[r.get("left_party", "D")]
    return f"markets: {left} {round(r['market'] * 100)}%"


def build(day: date, data: Path, preview: bool = False, theme=LAB) -> tuple[Path, list[str]]:
    f = json.loads((data / "derived" / day.isoformat() / "forecast.json").read_text(encoding="utf-8"))
    run = str(f.get("run_id", "unknown")).rsplit("-", 1)[-1][:7]
    kicker = "PREVIEW · NOT FOR POSTING" if preview else ""
    src = (f"Preview on pilot numbers ({day:%d %b}), not a public forecast." if preview else
           "40,000 simulated elections per race. Poll average, market and Cook as of this morning.")
    rs = races(f, day, kicker, src)
    feat = featured(rs, max(day, date(2026, 10, 12)))
    sen = f["senate"]
    up = {r["usps"]: r["p"] for r in rs}
    ind = {r["usps"] for r in rs if r["left_party"] in ("I", "O")}
    hold = sen.get("not_up", {"D": 32, "R": 31, "I": 2})
    cover = specials.chamber(theme, up, {"D": hold.get("D", 0) + hold.get("I", 0), "R": hold.get("R", 0)},
                             sen["p_r_50plus"], (sen.get("benchmarks") or {}).get("market"), day, None, kicker,
                             src + " Independents who caucus with Democrats count as D.", p_d=sen["p_d_caucus_51"],
                             ind=ind, series=SERIES, p_ind=sen.get("p_independents_decide"))
    slides = [cover] + [rc.stamped(theme, r) for r in feat]

    out = ROOT / "kits" / "daily" / (f"preview-{day:%d}-forecast" if preview else f"{day:%d}-forecast")
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob("slide-*.jpg"):
        old.unlink()
    problems = []
    for i, s in enumerate(slides, 1):
        problems += [f"slide {i}: {x}" for x in s.layout_problems() + s.missing_glyphs() + text.slide_problems(s, ALLOW)]
        s.save(out / f"slide-{i}.jpg")

    r_n, d_n = round(sen["p_r_50plus"] * 100), round(sen["p_d_caucus_51"] * 100)
    mkt = (sen.get("benchmarks") or {}).get("market")
    close = sorted(feat, key=lambda r: abs(r["p"] - 0.5))
    tight = close[0]
    mkt_txt = (f" The prediction markets give Republicans {round(mkt * 100)}% for control." if mkt is not None else "")
    caption = "\n".join([
        "Our 2026 midterm forecast is live. Every morning from today, voter personas built from real survey answers "
        "react to the day's news, every Senate race is played out 40,000 times, and we publish where things stand.",
        "",
        f"The Senate is close. Republicans hold 50 or more seats in {r_n} of every 100 simulated elections, and "
        f"Democrats reach 51 in {d_n}.{mkt_txt}",
        "",
        "The races to watch today:",
        *[f"{line(r)}. Poll average {r['poll']}, {market(r)}, Cook {r['cook']}." for r in feat],
        "",
        "Our number always sits beside the poll average, the prediction markets and Cook. From 19 October, every "
        "Monday, we'll check our calls against the next week's polls, put the markets and Cook through the same test, "
        "and publish the misses first.",
        "",
        "Which race are you watching most?",
        "",
        "Every race, every day: notapoll.org",
        "",
        "#midterms2026 #Senate #elections",
        "",
        DISCLAIMER])
    who, n = side(tight)
    x = (f"Our 2026 midterm forecast is live. Senate: Republicans hold 50+ seats in {r_n} of 100 simulated elections, "
         f"Democrats reach 51 in {d_n}. Closest race today: {tight['state']}, {who} {n} in 100. {LABEL}.")
    threads = (f"Our 2026 midterm forecast goes live today. The Senate is close: Republicans hold 50+ seats in {r_n} "
               f"of every 100 simulated elections, Democrats reach 51 in {d_n}. The tightest race right now is "
               f"{tight['state']}, where {who} win {n} in 100. Every number sits beside the polls, the markets and "
               f"Cook. Which race are you watching?")
    threads = f"{threads} {DISCLAIMER}" if len(threads) + 1 + len(DISCLAIMER) <= LIMIT["threads"] else f"{threads} {LABEL}."
    bluesky = (f"Our 2026 midterm forecast is live. Senate: Republicans hold 50+ in {r_n} of 100 simulated elections, "
               f"Democrats reach 51 in {d_n}. Closest: {tight['state']}. Every race: notapoll.org.")
    bluesky = f"{bluesky} {LABEL}." if len(bluesky) + len(LABEL) + 2 <= LIMIT["bluesky"] else bluesky
    posts = {"x": x, "threads": threads, "bluesky": bluesky}
    alts = [f"The Chamber: all 100 Senate seats in a half circle, the 35 on the ballot coloured by how the simulations "
            f"lean. Republicans hold 50 or more seats in {r_n} of 100 simulations, Democrats reach 51 in {d_n}."]
    alts += [f"Race card, {r['state']} {r['office']}: {rc.verdict(r['p'], rc.lean(r))}. {line(r)} on 3 Nov. Poll "
             f"average {r['poll']}, market {rc.pct_txt(r['market'])}, Cook {r['cook']}." for r in feat]
    (out / "caption.txt").write_text(caption, encoding="utf-8")
    (out / "alt-text.txt").write_text("".join(f"slide-{i}.jpg: {a}\n" for i, a in enumerate(alts, 1)), encoding="utf-8")
    lines = ["# Single posts (X and Threads through Buffer; Bluesky by hand)", ""]
    for k in ("x", "threads", "bluesky"):
        t = posts[k]
        size = len(t) + (t.count(SITE) * 18 if k == "x" else 0)
        lines += [f"## {'X' if k == 'x' else k.capitalize()} ({size} of {LIMIT[k]} characters; attach slide-1 to "
                  f"slide-{min(len(slides), 4)})", "", t, ""]
        problems += [f"{k}: {size} characters" for _ in [0] if size > LIMIT[k]]
    (out / "single-post.md").write_text("\n".join(lines), encoding="utf-8")
    (out / "meta.json").write_text(json.dumps({"threads_topic": "2026 Midterms"}, indent=1), encoding="utf-8")
    for name, t in [("caption", caption), *posts.items()]:
        problems += [f"{name}: {q}" for q in text.check(t, caption=True, allow=ALLOW)]
    (out / "checks.txt").write_text("\n".join(problems) or "all rules pass", encoding="utf-8")
    return out, problems


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True)
    ap.add_argument("--data", type=Path, default=ROOT.parent / "simlab-data")
    ap.add_argument("--preview", action="store_true")
    a = ap.parse_args()
    out, problems = build(date.fromisoformat(a.date), a.data, a.preview)
    print(out, "; ".join(problems) or "all rules pass")


if __name__ == "__main__":
    main()
