"""Daily post kit: python -m simlab.publish.kit --date YYYY-MM-DD --data <path to simlab-data>

Reads derived/<date>/forecast.json and draws.json (docs/engine-design.md §7) and writes derived/<date>/post-kit/: the
slides, a contact sheet, the Instagram caption, alt text, the thread for X, Threads and Bluesky, note.md (checks first)
and manifest.json. Exits 1 if the kit can't be built; the last stdout line is always a one-line JSON summary, which the
daily job copies into run.json. Nothing here posts or publishes; before 12 Oct every slide says PILOT · INTERNAL.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path

from . import racecards, text
from .frame import LABEL
from .geo import state_name
from .labnotes import contact_sheet
from .themes import LAB

LAYOUTS = ("4-stamp", "2-ladder", "3-futures")  # provisional until Matteo picks
MEANINGFUL = 0.03  # a smaller 7-day move in the win chance is "no meaningful change"
MOVER_MIN = 0.5  # margin points on 3 Nov; smaller story effects stay in note.md, out of public captions
LAUNCH = date(2026, 10, 12)
LIMITS = {"instagram": 2200, "thread": 280}
PILOT = ("OH-S", "NC", "TX")
FEATURED = 4  # races per daily post from the launch: the closest races plus the biggest mover
COOK = {"Tossup": "Toss-up", "Toss Up": "Toss-up"}


def race_meta(rid: str, races: dict) -> dict:
    """Race ids per engine-design §7: NC (Senate), OH-S (special Senate), TX-28 (House), AK-AL (at-large)."""
    usps, _, rest = rid.partition("-")
    m = {"usps": usps, "office": "Senate", "special": rest == "S", "code": f"{usps}-SEN"}
    if rest and rest != "S":
        m |= {"office": "House", "code": rid, "special": False}
    info = races.get(rid, {})
    m["office"] = info.get("office", m["office"]).title() if isinstance(info.get("office"), str) else m["office"]
    m["special"] = bool(info.get("special", m["special"]))
    m["state"] = state_name(usps)
    if m["office"] == "House":
        m["state"] = f"{m['state']} {rest if rest != 'AL' else 'at-large'}"
    if m["special"]:
        m["office"] = "Senate special"
    m["left_party"] = info.get("left_party", "D")
    m["candidates"] = info.get("candidates") or {}
    return m


def featured(rs: list[dict], day: date, only: list[str] | None = None) -> list[dict]:
    """The races a day's post shows: the pilot's three before the launch; from the launch, the closest races and
    the biggest 7-day mover, at most FEATURED."""
    if only:
        return [r for r in rs if r["rid"] in only]
    if day < LAUNCH:
        return [r for r in rs if r["rid"] in PILOT] or rs[:FEATURED]
    close = sorted(rs, key=lambda r: abs(r["p"] - 0.5))[:FEATURED - 1]
    moved = sorted((r for r in rs if r not in close), key=lambda r: -abs(r["p"] - (r["prev"] or r["p"])))
    return close + moved[:1]


def poll_txt(x, left: str = "D") -> str:
    if x is None:
        return "n/a"
    return x if isinstance(x, str) else racecards.margin_txt(float(x), left)


def change_txt(p: float, prev: float | None) -> str:
    if prev is None:
        return "First week"
    d = p - prev
    if abs(d) < MEANINGFUL:
        return "No meaningful change this week"
    return f"{'Up' if d > 0 else 'Down'} {abs(d) * 100:.0f} points this week"


def race_draws(draws: dict | None, rid: str):
    """Accepts {"races": {rid: [margins]}} or {"draws": [{rid: margin, ...}, ...]}."""
    if not draws:
        return None
    if isinstance(draws.get("races"), dict) and rid in draws["races"]:
        return draws["races"][rid]
    if isinstance(draws.get("draws"), list):
        return [row[rid] for row in draws["draws"] if rid in row] or None
    return None


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build(day: date, data: Path, theme=LAB, only: list[str] | None = None) -> dict:
    d = data / "derived" / day.isoformat()
    f = load(d / "forecast.json")
    if f is None:
        raise FileNotFoundError(f"no forecast.json in {d}")
    draws = load(d / "draws.json")
    prev = load(data / "derived" / (day - timedelta(days=7)).isoformat() / "forecast.json") or {"races": {}}
    races = load(d / "races.json") or load(data / "races.json") or {}
    run = str(f.get("run_id", "unknown")).rsplit("-", 1)[-1][:7]  # "2026-09-28-bf145e8" -> "bf145e8"
    pilot = day < LAUNCH
    kicker = "PILOT · INTERNAL, NOT FOR POSTING" if pilot else "DAILY FORECAST"
    out = d / "post-kit"
    (out / "slides").mkdir(parents=True, exist_ok=True)
    for old in (out / "slides").glob("*.jpg"):
        old.unlink()

    rs, problems, alts, paths = [], [], {}, []
    for rid, x in f["races"].items():
        if rid.startswith("US"):
            continue
        b = x.get("benchmarks") or {}
        m = race_meta(rid, races)
        m["left_party"] = x.get("left_party", m["left_party"])
        before = (prev["races"].get(rid) or {}).get("p_dem_win")
        rs.append(m | {"rid": rid, "run": run, "day": day, "kicker": kicker, "p": float(x["p_dem_win"]), "prev": before,
                       "lo": x["margin"]["p10"], "mid": x["margin"]["p50"], "hi": x["margin"]["p90"],
                       "poll": poll_txt(b.get("poll_avg"), m["left_party"]), "market": b.get("market"),
                       "cook": COOK.get(b.get("cook"), b.get("cook")) or "n/a",
                       "change": change_txt(float(x["p_dem_win"]), before),
                       "draws": race_draws(draws, rid), "movers": x.get("movers") or [], "benchmarks": b,
                       "source": f"NotAPoll run {run}: 40,000 simulated elections. Poll average, market and Cook as of "
                                 "the run."})
    if not rs:
        raise ValueError("forecast.json has no races")
    everyone, rs = rs, featured(rs, day, only)
    for r in rs:
        m, b = r, r["benchmarks"]
        for key, what in (("poll_avg", "poll average"), ("market", "market price"), ("cook", "Cook rating")):
            if b.get(key) is None:
                problems.append(f"{m['code']}: no {what}")
        for mv in r["movers"]:
            problems += [f"{m['code']} event card: {p}" for p in text.check(mv.get("card", ""), caption=False)]
        for name in LAYOUTS:
            n = len(paths) + 1
            p = racecards.LAYOUTS[name](theme, r).save(out / "slides" / f"{n:02d}-{m['code']}-{name[2:]}.jpg")
            paths.append(p)
            alts[p.name] = (f"{r['state']} {r['office']}: {racecards.verdict(r['p'], r['left_party'])}. The "
                            f"{racecards.who(r)} wins "
                            f"{r['p']:.0%} of simulated elections; poll average {r['poll']}, market "
                            f"{racecards.pct_txt(r['market'])}, Cook {r['cook']}. {r['change']}.")
    contact_sheet(paths, out / "contact.jpg", scale=0.3)

    lines = [f"Where the races stand, {day:%d %B}: {len(rs)} of our {len(everyone)} races, 40,000 simulated "
             "elections each.", ""]
    for r in rs:
        lines.append(f"{r['state']} {r['office']}: {racecards.verdict(r['p'], r['left_party'])}. "
                     f"The {racecards.who(r)} wins "
                     f"{round(r['p'] * 10)} in 10 simulated elections. Poll average {r['poll']}, market "
                     f"{racecards.pct_txt(r['market'])}, Cook {r['cook']}. {r['change']}.")
        top = [mv for mv in sorted(r["movers"], key=lambda mv: -abs(mv.get("delta", 0)))
               if abs(mv.get("delta", 0)) >= MOVER_MIN][:1]
        if top:
            lines.append(f"What moved it: {top[0]['card']}")
        lines.append("")
    lines += ["How to read it: synthetic voters react to each day's news, and each simulated election plays the race "
              "out once. Anything from 35% to 65% is a toss-up.", "", f"{LABEL}.", "",
              "#midterms2026 #elections #socialsimulation"]
    caption = "\n".join(lines)
    thread = [f"Where the races stand today, in 40,000 simulated elections each. {LABEL}."]
    thread += [f"{r['state']} {r['office']}: {racecards.verdict(r['p'], r['left_party'])}, the {racecards.who(r)} "
               f"wins {round(r['p'] * 10)} "
               f"in 10. Poll average {r['poll']}, market {racecards.pct_txt(r['market'])}, Cook {r['cook']}. "
               f"{r['change']}." for r in rs]

    problems += [f"Instagram caption: {p}" for p in text.check(caption)]
    if len(caption) > LIMITS["instagram"]:
        problems.append(f"Instagram caption: {len(caption)} characters")
    problems += [f"Thread post 1: {p}" for p in text.check(thread[0])]
    for i, t in enumerate(thread, 1):
        problems += [f"Thread post {i}: {p}" for p in text.check(t, caption=False)]
        if len(t) > LIMITS["thread"]:
            problems.append(f"Thread post {i}: {len(t)} characters (limit {LIMITS['thread']})")
    notes = sorted({n for t in [caption, *thread, *alts.values()] for n in text.style(t)})

    (out / "caption_instagram.txt").write_text(caption, encoding="utf-8")
    (out / "alt_text.json").write_text(json.dumps(alts, indent=1, ensure_ascii=False), encoding="utf-8")
    (out / "thread.txt").write_text("\n\n".join(thread), encoding="utf-8")
    note = [f"# Post kit {day:%a %d %b %Y}" + (" (pilot: internal, not for posting)" if pilot else ""), "",
            "## Checks", ""] + ([f"- {p}" for p in problems] or ["- All rules pass."]) + [""]
    note += ["## Style notes", ""] + ([f"- {n}" for n in notes] or ["- None."]) + [""]
    note += ["## What changed and why", ""]
    for r in everyone:
        so = f["races"][r["rid"]].get("stats_only", {}).get("p_dem_win")
        gap = "" if so is None else f"; statistics alone: {so:.0%}"
        note.append(f"- **{r['state']} {r['office']}**: {r['p']:.0%}{gap}. {r['change']}.")
        x = f["races"][r["rid"]]
        tier = (races.get(r["rid"]) or {}).get("tier")
        nw = x.get("news") or {}
        if abs(nw.get("effect", 0)) >= 0.005:  # races the news hasn't touched get no line
            note.append(f"  - News: {nw.get('effect', 0):+.2f} pts on the 3 Nov margin ({nw.get('switching', 0):+.2f} "
                        f"switching, {nw.get('turnout', 0):+.2f} turnout). Win chance "
                        f"{nw.get('if_weaker', {}).get('p_dem_win', r['p']):.0%} if news matters less, "
                        f"{nw.get('if_stronger', {}).get('p_dem_win', r['p']):.0%} if more."
                        + (f" Tier: {tier}." if tier else ""))
        note += [f"  - {mv['card']} (effect on the 3 Nov margin {mv.get('delta', 0):+.2f} pts"
                 + ("" if abs(mv.get("delta", 0)) >= MOVER_MIN else "; too small for captions") + ")"
                 for mv in r["movers"]]
    (out / "note.md").write_text("\n".join(note) + "\n", encoding="utf-8")

    try:
        commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=Path(__file__).parent,
                                capture_output=True, text=True).stdout.strip()
    except OSError:
        commit = ""
    files = sorted(p for p in out.rglob("*") if p.is_file() and p.name != "manifest.json")
    manifest = {"date": day.isoformat(), "run_id": f.get("run_id"), "code_commit": commit, "theme": theme.name,
                "layouts": list(LAYOUTS),
                "inputs": {n: sha(d / n) for n in ("forecast.json", "draws.json") if (d / n).exists()},
                "outputs": {str(p.relative_to(out)).replace("\\", "/"): sha(p) for p in files}}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    return {"ok": True, "date": day.isoformat(), "races": len(everyone), "featured": [r["rid"] for r in rs],
            "slides": len(paths), "problems": len(problems),
            "approvable": not problems, "out": str(out)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--date", required=True, type=date.fromisoformat)
    ap.add_argument("--data", type=Path, default=Path(__file__).resolve().parents[3] / "simlab-data")
    ap.add_argument("--races", help="comma-separated race ids to feature instead of the automatic pick")
    a = ap.parse_args(argv)
    try:
        summary = build(a.date, a.data, only=a.races.split(",") if a.races else None)
        code = 0
    except Exception as e:  # the daily job needs one summary line and a non-zero exit, whatever went wrong
        summary, code = {"ok": False, "date": a.date.isoformat(), "error": f"{type(e).__name__}: {e}"}, 1
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print(json.dumps(summary, ensure_ascii=False))
    return code


if __name__ == "__main__":
    sys.exit(main())
