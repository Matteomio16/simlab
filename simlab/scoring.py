"""How we did (CLAUDE.md §5 evaluation; Matteo's plan for 4 Nov): every version of the forecast against the results.

    python -m simlab.scoring --data <path to simlab-data> [--dates 2026-10-12,2026-10-19,2026-10-26,2026-11-03]

Reads the results from <data>/results/2026.json (filled in by hand from the official counts and called races):

    {"senate": {race_id: {"margin": left minus right, two-party points, "left_won": true/false}},
     "house": {seat: {"margin": ..., "left_won": ...}},
     "control": {"senate_r_50plus": true/false, "house_d_majority": true/false}}

and writes <data>/results/scores.json and a markdown table to stdout. Versions, each on every scoring date it has:
- "published": derived/<date>/forecast.json and draws.json, what went out;
- "fade": scoring/fade/<date>/ (the 3 Nov rule before early votes locked in, from 31 Oct);
- "poll filter": scoring/poll-filter/<date>/ (the rule before simulation only, from 14 Oct; derived/ before);
- "polls alone": the stats-only twin inside the published forecast (stats_only);
- "markets": each race's market price (benchmarks.market) and the chambers' Republican control price;
- "Cook": Cook's rating as a chance, by COOK below (fixed before the results).
Measures, per race over the Senate (and the House for the versions that have it): Brier score and log loss of the
left candidate's chance (Democrat or independent), wrong calls, the mean absolute error of the median margin (with
"poll average" as a margin-only baseline), and CRPS from the 1,000 kept draws where a version has them.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

DATES = ["2026-10-12", "2026-10-19", "2026-10-26", "2026-11-03"]
# a rating as the left candidate's chance (fixed 31 Oct, before any result; Solid ~ 98 in 100)
COOK = {"Solid": 0.98, "Likely": 0.88, "Lean": 0.73, "Tilt": 0.6, "Tossup": 0.5}
CLIP = 0.005  # chances are kept within [0.5%, 99.5%] for the log loss


def cook_chance(rating: str | None, left_party: str) -> float | None:
    """'Lean R' -> the left candidate's chance (Democrat or independent): a rating for R counts against it."""
    if not rating:
        return None
    word, _, side = rating.partition(" ")
    if word not in COOK:
        return None
    return COOK[word] if side != "R" else 1 - COOK[word]


def crps(draws: list[float], y: float) -> float:
    """CRPS of an ensemble: mean |x - y| - half the mean |x - x'| (exact for the sample)."""
    x = np.sort(np.asarray(draws, dtype=float))
    n = len(x)
    pair = 2 * np.sum(x * (2 * np.arange(1, n + 1) - n - 1)) / (n * n)
    return float(np.mean(np.abs(x - y)) - 0.5 * pair)


def measures(rows: list[dict]) -> dict:
    """rows: {p (left's chance), won, margin (median), actual, draws?} -> Brier, log loss, wrong calls, margin error,
    CRPS (over the rows with draws). A row without a chance (p None: the poll average) counts for calls and margin
    error only."""
    o = np.array([1.0 if r["won"] else 0.0 for r in rows])
    if rows[0].get("p") is None:
        call = np.array([r["margin"] > 0 for r in rows])
        return {"n": len(rows), "wrong": int(np.sum(call != (o > 0.5))),
                "margin_mae": round(float(np.mean([abs(r["margin"] - r["actual"]) for r in rows])), 3)}
    p = np.clip(np.array([r["p"] for r in rows], dtype=float), CLIP, 1 - CLIP)
    out = {"n": len(rows), "brier": round(float(np.mean((p - o) ** 2)), 4),
           "log_loss": round(float(-np.mean(o * np.log(p) + (1 - o) * np.log(1 - p))), 4),
           "wrong": int(np.sum((p != 0.5) & ((p > 0.5) != (o > 0.5))))}  # a toss-up (0.5) calls nothing
    m = [abs(r["margin"] - r["actual"]) for r in rows if r.get("margin") is not None]
    if m:
        out["margin_mae"] = round(float(np.mean(m)), 3)
    c = [crps(r["draws"], r["actual"]) for r in rows if r.get("draws")]
    if c:
        out["crps"] = round(float(np.mean(c)), 3)
    return out


def _read(path: Path):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def versions(data: Path, date: str) -> dict:
    """{name: (forecast, draws)} for every version that exists on `date`."""
    folder = lambda root: data / root / date
    out = {"published": (_read(folder("derived") / "forecast.json"), _read(folder("derived") / "draws.json"))}
    for name, root in (("fade", "scoring/fade"), ("poll filter", "scoring/poll-filter")):
        f = _read(folder(root) / "forecast.json")
        if f is not None:
            out[name] = (f, _read(folder(root) / "draws.json"))
    if "poll filter" not in out and date < "2026-10-14":
        out["poll filter"] = out["published"]
    return {k: v for k, v in out.items() if v[0] is not None}


def senate_rows(fc: dict, draws: dict | None, results: dict) -> dict:
    """{version name: rows} for the Senate races of one forecast: the version itself, polls alone, markets, Cook,
    and the poll average (margin only)."""
    out = {"self": [], "polls alone": [], "markets": [], "Cook": [], "poll average": []}
    for r, x in fc["races"].items():
        res = results.get(r)
        if res is None:
            continue
        base = {"won": res["left_won"], "actual": res["margin"]}
        out["self"].append(base | {"p": x["p_dem_win"], "margin": x["margin"]["p50"],
                                   "draws": (draws or {}).get("races", {}).get(r)})
        so = x["stats_only"]
        out["polls alone"].append(base | {"p": so["p_dem_win"], "margin": so["margin"]["p50"],
                                          "draws": (draws or {}).get("stats_only", {}).get("races", {}).get(r)})
        b = x.get("benchmarks", {})
        if b.get("market") is not None:
            out["markets"].append(base | {"p": b["market"]})
        if (c := cook_chance(b.get("cook"), x.get("left_party", "D"))) is not None:
            out["Cook"].append(base | {"p": c})
        if b.get("poll_avg") is not None:
            out["poll average"].append(base | {"p": None, "margin": b["poll_avg"]})
    return out


def score(data: Path, results: dict, dates: list[str] = DATES) -> dict:
    """Every version on every scoring date: Senate races, House seats (versions with a House) and chamber control."""
    out = {}
    for d in dates:
        day = {}
        for name, (fc, dr) in versions(data, d).items():
            rows = senate_rows(fc, dr, results.get("senate", {}))
            day[name] = {"senate": measures(rows["self"])} if rows["self"] else {}
            if name == "published":
                for base in ("polls alone", "markets", "Cook", "poll average"):
                    if rows[base]:
                        day[base] = {"senate": measures(rows[base])}
            hr = [{"p": x["p_dem_win"], "won": results["house"][s]["left_won"], "margin": x["margin"]["p50"],
                   "actual": results["house"][s]["margin"],
                   "draws": (dr or {}).get("house_races", {}).get(s)}
                  for s, x in ((fc.get("house") or {}).get("races") or {}).items() if s in results.get("house", {})]
            if hr:
                day[name]["house"] = measures(hr)
            ctl = results.get("control", {})
            if "senate_r_50plus" in ctl:
                day[name]["senate_control"] = round((fc["senate"]["p_r_50plus"] - float(ctl["senate_r_50plus"])) ** 2, 4)
                if name == "published" and fc["senate"].get("benchmarks", {}).get("market") is not None:
                    day.setdefault("markets", {})["senate_control"] = round(
                        (fc["senate"]["benchmarks"]["market"] - float(ctl["senate_r_50plus"])) ** 2, 4)
            if "house_d_majority" in ctl and fc.get("house"):
                day[name]["house_control"] = round((fc["house"]["p_d_majority"] - float(ctl["house_d_majority"])) ** 2, 4)
                if name == "published" and fc["house"].get("benchmarks", {}).get("market") is not None:
                    day.setdefault("markets", {})["house_control"] = round(
                        (1 - fc["house"]["benchmarks"]["market"] - float(ctl["house_d_majority"])) ** 2, 4)
        out[d] = day
    return out


def table(scores: dict) -> str:
    lines = ["| Date | Version | Senate Brier | Log loss | Wrong calls | Margin error | CRPS | House Brier | "
             "Senate control | House control |", "|---|---|---|---|---|---|---|---|---|---|"]
    def get(x, key, sub=None):
        v = x.get(key, {}).get(sub) if sub else x.get(key)
        return "" if v is None else v
    for d, day in scores.items():
        for name, x in day.items():
            lines.append(f"| {d} | {name} | {get(x, 'senate', 'brier')} | {get(x, 'senate', 'log_loss')} | "
                         f"{get(x, 'senate', 'wrong')} | {get(x, 'senate', 'margin_mae')} | {get(x, 'senate', 'crps')} | "
                         f"{get(x, 'house', 'brier')} | {get(x, 'senate_control')} | {get(x, 'house_control')} |")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, default=Path(__file__).resolve().parents[2] / "simlab-data")
    ap.add_argument("--dates", default=",".join(DATES))
    a = ap.parse_args()
    results = _read(a.data / "results" / "2026.json")
    if results is None:
        print(f"no results yet: fill in {a.data / 'results' / '2026.json'} (format in this module's docstring)")
        return 1
    s = score(a.data, results, a.dates.split(","))
    (a.data / "results" / "scores.json").write_text(json.dumps(s, indent=1), encoding="utf-8")
    print(table(s))
    return 0


if __name__ == "__main__":
    sys.exit(main())
