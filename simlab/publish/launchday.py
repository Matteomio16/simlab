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
from datetime import date, timedelta
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


LAUNCH = date(2026, 10, 12)
MOVE = 0.03  # a smaller change in a race's chance since the last published day is "no change"
ASK = ["Which race are you watching this week?", "Which of these would you call differently?",
       "Which race do you think we're getting wrong?", "Where do you think the news is moving voters most?",
       "Which race should we look at more closely?", "What would change your mind about one of these races?",
       "Which race are you most unsure about?"]  # one per weekday, Monday first


def last_published(data: Path, day: date) -> tuple[date, dict] | None:
    """The previous published forecast (from the launch on), never the unpublished pilot days (review A14)."""
    d = day
    while (d := d - timedelta(days=1)) >= LAUNCH:
        p = data / "derived" / d.isoformat() / "forecast.json"
        if p.exists():
            return d, json.loads(p.read_text(encoding="utf-8"))
    return None


def change(p: float, prev: float | None, since: date | None) -> str:
    if prev is None:
        return "First public forecast"
    d = p - prev
    if abs(d) < MOVE:
        return f"No change since {since.day} {since:%b}"
    return f"{'Up' if d > 0 else 'Down'} {abs(d) * 100:.0f} since {since.day} {since:%b}"


def races(f: dict, day: date, kicker: str, source: str, prev: tuple[date, dict] | None = None) -> list[dict]:
    out = []
    since, pf = prev if prev else (None, {"races": {}})
    for rid, x in f["races"].items():
        if rid.startswith("US"):
            continue
        b = x.get("benchmarks") or {}
        m = race_meta(rid, {})
        m["left_party"] = x.get("left_party", m.get("left_party", "D"))
        before = (pf["races"].get(rid) or {}).get("p_dem_win")
        out.append(m | {"rid": rid, "run": None, "day": day,  # no run code on slides (Matteo, 12 Oct)
                        "kicker": kicker, "p": float(x["p_dem_win"]),
                        "prev": before, "today": (x.get("today") or {}).get("p_dem_win"),
                        "lo": x["margin"]["p10"], "mid": x["margin"]["p50"], "hi": x["margin"]["p90"],
                        "poll": poll_txt(b.get("poll_avg"), m["left_party"]), "market": b.get("market"),
                        "cook": COOK.get(b.get("cook"), b.get("cook")) or "n/a",
                        "change": change(float(x["p_dem_win"]), before, since), "benchmarks": b, "source": source})
    return out


def pick(rs: list[dict], n: int = 4) -> list[dict]:
    """The races a post shows: the closest races, and the biggest mover in the last slot only when it moved 3+ points
    since the last published day (13 Oct: a 1-point mover in a safe race had pushed out a closer one)."""
    close = sorted(rs, key=lambda r: abs(r["p"] - 0.5))
    moved = [r for r in close[n - 1:] if r["prev"] is not None and abs(r["p"] - r["prev"]) >= MOVE]
    last = max(moved, key=lambda r: abs(r["p"] - r["prev"])) if moved else close[n - 1]
    return close[:n - 1] + [last]


def daily_texts(day: date, sen: dict, psen: dict | None, since: date | None, feat: list[dict]) -> dict:
    """The everyday caption and posts (from 13 Oct): where the Senate stands, what moved since the last published
    day, the races to watch, a question that changes with the weekday; the Monday scoring line on Mondays only."""
    r_n, d_n = round(sen["p_r_50plus"] * 100), round(sen["p_d_caucus_51"] * 100)
    move = ""
    if psen and since:
        dr = r_n - round(psen["p_r_50plus"] * 100)
        move = (f" That's {'up' if dr > 0 else 'down'} {abs(dr)} for Republicans since {since.day} {since:%B}."
                if abs(dr) >= 3 else f" Little change since {since.day} {since:%B}.")
    tight = sorted(feat, key=lambda r: abs(r["p"] - 0.5))[0]
    moved = [r for r in feat if r["prev"] is not None and abs(r["p"] - r["prev"]) >= MOVE]
    big = max(moved, key=lambda r: abs(r["p"] - r["prev"])) if moved else None
    who, n = side(tight)
    ask = ASK[day.weekday()]
    lines = [f"Where the Senate stands, {day.day} {day:%B}: Republicans hold 50 or more seats in {r_n} of every 100 "
             f"simulated elections, Democrats reach 51 in {d_n}.{move}", ""]
    if big:
        bw, bn = side(big)
        lines += [f"Biggest move: {big['state']}, now {bw} {bn} in 100 ({big['change'].lower()}).", ""]
    lines += ["The races to watch today:",
              *[f"{line(r)}. Poll average {r['poll']}, {market(r)}, Cook {r['cook']}." for r in feat], ""]
    if day.weekday() == 0:
        lines += ["Every Monday we check our calls against the next week's polls, put the markets and Cook through the "
                  "same test, and publish the misses first.", ""]
    lines += [ask, "", "Every race, every day: notapoll.org", "", "#midterms2026 #Senate #elections", "", DISCLAIMER]
    x = (f"Senate, {day.day} {day:%b}: Republicans hold 50+ seats in {r_n} of 100 simulated elections, Democrats reach "
         f"51 in {d_n}. Closest race: {tight['state']}, {who} {n} in 100."
         + (f" Biggest move: {big['state']}." if big else "") + f" {LABEL}.")
    threads = (f"Where the Senate stands today: Republicans hold 50+ seats in {r_n} of every 100 simulated elections, "
               f"Democrats reach 51 in {d_n}. The tightest race is {tight['state']}, where {who} win {n} in 100."
               + (f" The biggest move is in {big['state']}." if big else "") + f" {ask}")
    threads = f"{threads} {DISCLAIMER}" if len(threads) + 1 + len(DISCLAIMER) <= LIMIT["threads"] else f"{threads} {LABEL}."
    bluesky = (f"Senate, {day.day} {day:%b}: Republicans 50+ in {r_n} of 100 simulated elections, Democrats 51 in "
               f"{d_n}. Closest: {tight['state']}. Every race: notapoll.org.")
    bluesky = f"{bluesky} {LABEL}." if len(bluesky) + len(LABEL) + 2 <= LIMIT["bluesky"] else bluesky
    return {"caption": "\n".join(lines), "x": x, "threads": threads, "bluesky": bluesky}


def side(r: dict) -> tuple[str, int]:
    """Who's ahead and their chance in 100, for the texts: ('Democrats', 59) or ('Republicans', 59)."""
    left = {"D": "Democrats", "I": "the independent", "O": r.get("state", "")}[r.get("left_party", "D")]
    n = round(r["p"] * 100)
    return (left, n) if n >= 50 else ("Republicans", 100 - n)


def line(r: dict) -> str:
    who, n = side(r)
    return f"{r['state']}: {who} win {n} of every 100 simulated elections (expected vote {rc.expected_vote(r)})"


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
    prev = None if day <= LAUNCH else last_published(data, day)
    rs = races(f, day, kicker, src, prev)
    feat = pick(rs)
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
    if day > LAUNCH:  # the everyday texts; the launch wording above is for 12 Oct only
        t = daily_texts(day, sen, prev[1]["senate"] if prev else None, prev[0] if prev else None, feat)
        caption, posts = t.pop("caption"), t
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
