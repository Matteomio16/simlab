"""Statistics step of the daily job: python -m simlab.statsday --date YYYY-MM-DD --data <path to simlab-data>

Reads the day's latest snapshot run (or --snapshot HHMM) and writes to derived/<date>/: polls.csv, races.json,
levels.json, groups.json, forecast.json and draws.json (engine-design §7). Moves and the filter join as they are built;
until then the headline and the stats-only twin run on the same levels. Exits 1 on failure; the last stdout line
is a one-line JSON summary, which holds no forecast numbers.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import subprocess
import sys
import traceback
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

from . import groups, levels, montecarlo, moves, polls
from .polls import OVERVIEW_PAGE, Race, slug

RCV = {"AK", "ME"}
SCHEMA = 1


def snapshot_for(data: Path, day: date, hhmm: str | None = None) -> Path:
    runs = sorted(p for p in (data / "snapshots" / day.isoformat()).glob("*") if p.is_dir())
    if hhmm:
        runs = [p for p in runs if p.name == hhmm]
    if not runs:
        raise FileNotFoundError(f"no snapshot run for {day}" + (f" at {hhmm}" if hhmm else ""))
    return runs[-1]


def races_json(race_list: list[Race]) -> dict:
    return {r.race_id: {"state": r.state, "office": "senate", "district": None, "special": r.special,
                        "rcv": r.state in RCV, "candidates": {"left": r.left, "right": r.right},
                        "left_party": r.left_party, "incumbent_party": r.incumbent, "status": r.status}
            for r in race_list}


def poll_rows(senate: pd.DataFrame, gb: pd.DataFrame) -> pd.DataFrame:
    return pd.concat([senate, gb.assign(race_id="US")], ignore_index=True)


FIRST_SEEN_KEY = ["race_id", "pollster", "start", "end", "population"]


def first_seen(today: pd.DataFrame, prev: pd.DataFrame | None, stamp: str) -> pd.DataFrame:
    """Each poll row's first snapshot: carried from the last day's polls.csv, else this run's snapshot time."""
    key = lambda df: df[FIRST_SEEN_KEY].astype(str).agg("|".join, axis=1)
    seen = dict(zip(key(prev), prev.first_seen)) if prev is not None and "first_seen" in prev else {}
    return today.assign(first_seen=[seen.get(k, stamp) for k in key(today)])


def previous_polls(data: Path, day: date) -> pd.DataFrame | None:
    files = sorted(p for p in (data / "derived").glob("*/polls.csv") if p.parent.name < day.isoformat())
    return pd.read_csv(files[-1], low_memory=False) if files else None


PILOT = {"OH-S", "NC", "TX"}
TIER_RANK = {"statistics": 0, "watch": 1, "simulate": 2}


def tier(p_stats: float | None, cook: str | None, market: float | None) -> tuple[str, list[str]]:
    """Where the simulation runs (Matteo, 28 Sep): "simulate" (full), "watch" (the biggest stories only) or
    "statistics" (statistics and national news). A race runs on statistics alone only when all three signals call it
    safe, since a race that flips unsimulated would count against the simulation."""
    close = lambda p, lo: p is not None and lo <= p <= 1 - lo
    word = (cook or "").split(" ")[0]
    reasons = ([f"stats-only {p_stats:.0%}"] if close(p_stats, 0.10) else []) +               ([f"Cook {cook}"] if word in ("Tossup", "Tilt", "Lean") else []) +               ([f"market {market:.0%}"] if close(market, 0.10) else [])
    if reasons:
        return "simulate", reasons
    reasons = ([f"stats-only {p_stats:.0%}"] if close(p_stats, 0.03) else []) +               ([f"Cook {cook}"] if word == "Likely" else []) + ([f"market {market:.0%}"] if close(market, 0.05) else [])
    return ("watch", reasons) if reasons else ("statistics", ["all three signals call it safe"])


def tiers(races: dict, stats: dict, bench: dict, history: list[dict]) -> dict:
    """races.json rows with today's tier: pilot races always simulate; otherwise the most competitive tier of today
    and the last days in `history` (earlier races.json files), so a race doesn't drop out after one quiet day."""
    out = {}
    for rid, row in races.items():
        raw, why = tier(stats.get(rid), bench.get(rid, {}).get("cook"), bench.get(rid, {}).get("market"))
        past = [h[rid]["tier_raw"] for h in history if rid in h and "tier_raw" in h.get(rid, {})]
        best = max([raw, *past], key=TIER_RANK.get)
        if rid in PILOT:
            best, why = "simulate", ["pilot race"]
        elif best != raw:
            why = why + [f"kept from the last {len(history)} days"]
        out[rid] = row | {"tier": best, "tier_raw": raw, "tier_reasons": why}
    return out


def _read(path: Path):
    return json.loads(gzip.decompress(path.read_bytes())) if path.exists() else {}


def benchmarks(snap: Path, race_list: list[Race]) -> dict:
    """Market prices and Cook ratings as of the snapshot: shown beside the forecast, never used in it."""
    kalshi, poly = _read(snap / "markets" / "kalshi.gz"), _read(snap / "markets" / "polymarket.gz")
    overview = _read(snap / "wikipedia" / f"{slug(OVERVIEW_PAGE)}.gz")
    ratings = montecarlo.cook(overview["revisions"][0]["slots"]["main"]["content"]) if overview else {}
    out = {}
    for r in race_list:
        p, venues = montecarlo.market(kalshi, poly, r)
        out[r.race_id] = {"market": p, "market_venues": venues, "cook": ratings.get(r.race_id)}
    p, venues = montecarlo.control_market(kalshi, poly, "senate")
    out["US-S"] = {"market": p, "market_venues": venues}
    return out


def _git_sha() -> str:
    return subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True,
                          cwd=Path(__file__).parent).stdout.strip()


def _write(path: Path, obj, compact: bool = False) -> str:
    text = json.dumps(obj, separators=(",", ":")) if compact else json.dumps(obj, indent=1, default=str)
    path.write_text(text, encoding="utf-8")
    return hashlib.sha256(text.encode()).hexdigest()


def run(day: date, data: Path, hhmm: str | None = None, run_id: str | None = None) -> dict:
    snap = snapshot_for(data, day, hhmm)
    run_id = run_id or f"{day}-{_git_sha()[:7]}"
    meta = {"date": day.isoformat(), "run_id": run_id, "schema": SCHEMA}
    out = data / "derived" / day.isoformat()
    out.mkdir(parents=True, exist_ok=True)
    t = polls.build(snap)
    first_seen(poll_rows(t["senate"], t["generic_ballot"]), previous_polls(data, day),
               t["snapshot"]).to_csv(out / "polls.csv", index=False)
    races = races_json(t["race_list"])
    inp = levels.inputs()
    lv = levels.compute(t, day, run_id, inp=inp)
    sha = {"levels.json": _write(out / "levels.json", lv)}
    base, pimu = (json.loads(f.read_text(encoding="utf-8")) for f in (groups.BASE, groups.PIMU))
    grp = groups.build(lv, base, pimu, day.isoformat(), run_id)
    _write(out / "groups.json", grp)
    mp = json.loads(moves.PARAMS.read_text(encoding="utf-8"))
    _write(out / "params.json", meta | mp | {"fitted_on": mp["fit"]["on"]})
    mv = moves.build(day, data / "derived", grp, mp, run_id)
    sha["moves.json"] = _write(out / "moves.json", mv)
    head = levels.compute(t, day, run_id, moves=moves.paths(mv), inp=inp)
    sha["filter_state.json"] = _write(out / "filter_state.json", head | {"moves": "moves.json, main block (GLM)",
                                                                          "dials": mp["dials"]})
    part = {k: levels.compute(t, day, run_id, moves=moves.paths(mv, k), inp=inp)["races"] for k in ("s", "t")}
    news = {name: {r: part[k][r]["margin"] - lv["races"][r]["margin"] for r in lv["races"]}
            for name, k in (("switching", "s"), ("turnout", "t"))}
    gap = max(abs(head["races"][r]["margin"] - lv["races"][r]["margin"] - news["switching"][r] - news["turnout"][r])
              for r in lv["races"])
    if gap > 1e-6:
        raise ValueError(f"story effects don't add up across their parts (gap {gap:.2e})")
    news["sigma"] = {k[-1]: mp["uncertainty"][k]["sigma_log"] for k in ("c_s", "c_t")}
    params = json.loads((Path(levels.__file__).parent / "stats_params.json").read_text())
    bench = benchmarks(snap, t["race_list"])
    forecast, draws = montecarlo.build(head, lv, {k: v["left_party"] for k, v in races.items()}, params, day, run_id,
                                       benchmarks=bench, movers=moves.movers(mv), news=news)
    forecast |= {"snapshot": t["snapshot"], "inputs": sha}
    history = [json.loads(f.read_text(encoding="utf-8")) for k in range(1, 7)
               if (f := data / "derived" / (day - timedelta(days=k)).isoformat() / "races.json").exists()]
    stats = {r: x["stats_only"]["p_dem_win"] for r, x in forecast["races"].items()}
    races = tiers(races, stats, bench, history)
    _write(out / "races.json", meta | races)
    _write(out / "forecast.json", forecast)
    _write(out / "draws.json", draws, compact=True)
    return {"ok": True, "date": day.isoformat(), "run_id": run_id, "snapshot": t["snapshot"], "races": len(races),
            "with_polls": sum(r["n_polls"] > 0 for r in lv["races"].values()), "draws": forecast["draws"],
            "floor_lifted_pairs": forecast["floor_lifted_pairs"],
            "tiers": {k: sum(r["tier"] == k for r in races.values()) for k in TIER_RANK},
            "stories": sum(len(x["events"]) for k, x in mv.items() if k != "shadow" and isinstance(x, dict) and "events" in x),
            "files": ["polls.csv", "races.json", "levels.json", "groups.json", "params.json", "moves.json",
                      "filter_state.json", "forecast.json", "draws.json"]}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", type=date.fromisoformat, default=datetime.now(timezone.utc).date())
    ap.add_argument("--data", type=Path, default=Path(__file__).resolve().parents[2] / "simlab-data")
    ap.add_argument("--snapshot", default=None, help="snapshot run HHMM (default: the day's latest)")
    ap.add_argument("--run-id", default="")
    a = ap.parse_args()
    try:
        summary = run(a.date, a.data, a.snapshot, a.run_id or None)
    except Exception as e:
        traceback.print_exc()
        print(json.dumps({"ok": False, "date": a.date.isoformat(), "error": f"{type(e).__name__}: {e}"}))
        return 1
    print(json.dumps(summary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
