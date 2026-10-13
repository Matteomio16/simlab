"""The frozen start (docs/simulation-only.md, Matteo 13 Oct): polls set each race's level once, at the 12 Oct launch;
after that only the simulation moves it.

    python -m simlab.start --data <path to simlab-data>     # writes <data>/start/2026-10-12.json once

The start is 12 Oct's statistical level as the launch forecast had it (kind "filter"): the poll average and
fundamentals of the 09:08 snapshot, with each poll taken less the story effects in force on its dates, for every
election day from 12 Oct to 3 Nov, so the "if the election were today" view has its own start too. A day's headline is
that level plus every story's effect expected on election day, so on 12 Oct it is the launch forecast and after that
only the stories move it ("moves since 12 Oct" = the stories' expected effect now less on 12 Oct). A race without news
doesn't move. It is recomputed once from that snapshot and 12 Oct's moves.json, with the sponsor-footnote fix
(polls.sponsor) and Alaska's House pairing (house.challenger), and then never changes.

Kind "polls" (an alternative, for comparison) starts from the stats-only level instead and takes each story's effect
in force on 12 Oct as already in the polls, so stories seen before 12 Oct count only by how much they fade after it.
"""
from __future__ import annotations

import argparse
import json
import subprocess
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import numpy as np

from . import levels

START = date(2026, 10, 12)
SNAPSHOT = "0908"
FROM = date(2026, 10, 14)  # the first daily run under the rule; earlier days keep the poll filter (both are scored)
RULE, OLD_RULE = "simulation-only", "poll-filter"
CANCELLED = Path(__file__).parent / "cancelled_weeks.json"
SENATE_KEYS = ("margin", "sd", "w_polls", "poll_margin", "fundamentals", "n_polls")
HOUSE_KEYS = SENATE_KEYS + ("fixed", "state", "region")


def path(data: Path) -> Path:
    return data / "start" / f"{START.isoformat()}.json"


def rule_for(day: date) -> str:
    return RULE if day >= FROM else OLD_RULE


def _slim(lv: dict, keys: tuple, kind: str, twin: dict | None = None) -> dict:
    """One election day's start levels; for kind "filter" the margin is the statistical level (the headline less its
    story effect on election day, kept as story_3nov), with the stats-only margin as poll_level."""
    r6 = lambda v: round(v, 6) if isinstance(v, float) else v
    races = {}
    for r, x in lv["races"].items():
        races[r] = {k: r6(x.get(k)) for k in keys}
        if kind == "filter" and not x.get("fixed"):
            races[r] |= {"margin": r6(x["margin"] - x["story_effect_3nov"]), "story_3nov": r6(x["story_effect_3nov"]),
                         "poll_level": r6(twin["races"][r]["margin"])}
    out = {"kind": kind, "days_to_election": lv["days_to_election"], "races": races}
    if "national" in lv:
        out["national"] = {k: r6(v) for k, v in lv["national"].items()}
    return out


def freeze(data: Path, kind: str = "filter") -> dict:
    """The start file: 12 Oct's levels (kind "filter": the launch forecast's statistical level, with 12 Oct's
    moves.json; "polls": the stats-only level), Senate and House, for each election day from 12 Oct to 3 Nov."""
    from . import house, moves, polls
    snap = data / "snapshots" / START.isoformat() / SNAPSHOT
    run_id = json.loads((data / "derived" / START.isoformat() / "levels.json").read_text(encoding="utf-8"))["run_id"]
    t, inp = polls.build(snap), levels.inputs()
    lv = levels.compute(t, START, run_id, inp=inp)
    hb = house.prepare(START, data, lv, snap=snap, run_id=run_id)
    p12 = moves.paths(json.loads((data / "derived" / START.isoformat() / "moves.json").read_text(encoding="utf-8"))) \
        if kind == "filter" else None
    sha = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True,
                         cwd=Path(__file__).parent).stdout.strip()
    out = {"start": START.isoformat(), "kind": kind, "snapshot": t["snapshot"], "run_id": run_id, "code": sha,
           "made": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "units": "two-party margin, D (or independent challenger) minus R, points; keyed by election day",
           "senate": {}, "house": {}}
    for k in range((levels.ELECTION - START).days + 1):
        e = START + timedelta(days=k)
        s = levels.compute(t, START, run_id, inp=inp, election=e)
        h = house.build(hb, s, election=e)
        if p12 is None:
            out["senate"][e.isoformat()] = _slim(s, SENATE_KEYS, kind)
            out["house"][e.isoformat()] = _slim(h, HOUSE_KEYS, kind)
            continue
        f = levels.compute(t, START, run_id, moves=p12, inp=inp, election=e)
        out["senate"][e.isoformat()] = _slim(f, SENATE_KEYS, kind, s)
        out["house"][e.isoformat()] = _slim(house.build(hb, f, p12, election=e), HOUSE_KEYS, kind, h)
    return out


def load(data: Path) -> dict:
    return json.loads(path(data).read_text(encoding="utf-8"))


def at(start: dict, election: date, tier: dict | None = None) -> tuple[dict, dict | None]:
    """The start's Senate and House levels for one election day; House seats carry today's `tier`."""
    key = election.isoformat()
    if key not in start["senate"]:
        raise KeyError(f"the start file has no levels for election day {key}")
    h = start["house"].get(key)
    if h and tier is not None:
        h = h | {"races": {r: x | {"tier": tier.get(r)} for r, x in h["races"].items()}}
    return start["senate"][key], h


def cancelled(file: Path = CANCELLED) -> dict:
    """{race_id: [(after, until)]}: the weeks Matteo cancelled (cancelled_weeks.json), whose stories that race drops:
    those first seen after the Sunday before `until` and up to `until`."""
    if not file.exists():
        return {}
    out = {}
    for w in json.loads(file.read_text(encoding="utf-8")).get("weeks", []):
        until = date.fromisoformat(w["week_ending"])
        out.setdefault(w["race"], []).append(((until - timedelta(days=7)).isoformat(), until.isoformat()))
    return out


def kept(items: list, windows) -> list:
    """Path items (first_seen first) outside the dropped windows."""
    day = lambda s: str(s)[:10]
    return [x for x in items if not any(a < day(x[0]) <= b for a, b in windows)] if windows else items


def headline(base: dict, paths: dict, day: date, election: date = levels.ELECTION, drop: dict | None = None) -> dict:
    """The headline levels on `day` for one election day: the start (`base`, at() for that election day) plus the
    story effects, from moves.paths' items {race_id or "US": [(first_seen, last_seen, full effect, age half-life,
    after-news half-life)]}; a race without its own stories takes the nation's. Kind "filter": every story's effect
    expected on election day (coverage taken to end today, as levels.build); kind "polls": that less its effect in
    force on 12 Oct. Linear in the effects, so the news parts add up as before. `drop` (cancelled()) removes a race's
    cancelled weeks."""
    d = (election - day).days
    then = float((START - election).days)
    races = {}
    for r, x in base["races"].items():
        if x.get("fixed"):
            races[r] = dict(x)
            continue
        items = kept(paths.get(r, paths.get("US", [])), (drop or {}).get(r))
        eday = float(levels.effect(np.array([0.0]), items, election, stop=-d)[0])
        now = float(levels.effect(np.array([-d], dtype=float), items, election)[0])
        if base.get("kind") == "polls":
            add = move = eday - float(levels.effect(np.array([then]), items, election)[0])
            first = x["margin"]
        else:
            add, move, first = eday, eday - x["story_3nov"], x["margin"] + x["story_3nov"]
        races[r] = x | {"margin": x["margin"] + add, "story_effect": now, "story_effect_3nov": eday,
                        "moves_since_start": move, "start_margin": first}
    return base | {"date": day.isoformat(), "days_to_election": d, "rule": RULE, "start": START.isoformat(),
                   "races": races}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, default=Path(__file__).resolve().parents[2] / "simlab-data")
    ap.add_argument("--force", action="store_true", help="rewrite an existing start file")
    ap.add_argument("--kind", choices=["filter", "polls"], default="filter")
    a = ap.parse_args()
    f = path(a.data)
    if f.exists() and not a.force:
        print(f"{f} exists; the start is frozen (use --force only with Matteo's yes)")
        return 1
    out = freeze(a.data, a.kind)
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(out, separators=(",", ":")), encoding="utf-8")
    print(json.dumps({"ok": True, "file": str(f), "senate": len(out["senate"]), "snapshot": out["snapshot"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
