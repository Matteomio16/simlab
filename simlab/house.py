"""House seats (roadmap A11): all 435 districts on the 2026 lines, in the levels.json race shape (engine-design §7,
stats-groundwork §5.9).

Fundamentals (fitted on 2022 and 2024, `python -m simlab.house fit`):
    margin = c + 0.973 × lean + 4.45 × incumbent
- lean: the district's 2024 presidential two-party margin (The Downballot, on the 2026 lines) minus the nation's.
- incumbent: +1 when the Democratic nominee is a sitting member (anywhere in the state), -1 for the Republican, 0 for
  an open seat or member against member; × 0.7 on a map redrawn for 2026 (Field Guide rule, untested here).
- c: set each day so the 435 seats add up to the day's national House vote (levels.json `national.E_hat`), weighting
  contested seats by their 2024 presidential votes and uncontested ones, fixed at ±100, by 0.71 of theirs (2024's
  ratio). On 2024's contested seats this anchoring leaves no bias (+0.03).
- sd: 5.5 within 15 points, 9 beyond (Matteo, 29 Sep): predicting 2022 from 2024 and back, given the national vote,
  close seats missed by 4.9 and 4.6; safe seats by about 10.
Nominees, sitting members, uncontested seats and ratings come from the day's Wikipedia House pages. Where a district
has no section yet, its nominees are unknown: it counts as contested with the CSV's incumbent assumed to run
(`checked: false`). Ratings pick the simulated seats (with the fundamentals) and never enter the numbers.

Inputs: <data>/house/inputs.json (built once by `python -m simlab.house inputs` from the Engine's data/house/, which
is gitignored; kept private in simlab-data).

    python -m simlab.house inputs          # data/house/*.csv -> ../simlab-data/house/inputs.json
    python -m simlab.house fit             # refits b and psi on 2022 and 2024 (MIT House file + The Downballot)
    python -m simlab.house run --date 2026-09-29 --data ../simlab-data
"""
from __future__ import annotations

import argparse
import gzip
import json
import re
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import brentq
from scipy.stats import norm

from .calib import DIVISION
from .polls import STATE_CODES
from .snap import AT_LARGE, slug

HERE = Path(__file__).parent
LOCAL = HERE.parent / "data" / "house"
B_LEAN, PSI, REDRAWN_PSI, UNCONTESTED_TURNOUT = 0.973, 4.45, 0.7, 0.71
SD_CLOSE, SD_SAFE, CLOSE = 5.5, 9.0, 15.0
NATIONAL_PRES24 = -1.68   # Harris minus Trump, two-party, summed over the 435 districts
N_SIMULATE = 40
RATING = {"safe": 3, "solid": 3, "likely": 2, "lean": 1, "tilt": 0.5, "tossup": 0, "toss-up": 0}


def inputs(out: Path) -> dict:
    """The Engine's district files -> one private JSON the daily job can read."""
    d = pd.read_csv(LOCAL / "districts_2026.csv")
    acs = pd.read_csv(LOCAL / "acs2024_cd119.csv").set_index("race_id")
    races = {}
    for r in d.itertuples():
        a = acs.loc[r.race_id].to_dict() if r.race_id in acs.index else {}
        races[r.race_id] = {"state": r.state, "district": int(r.district), "new_map": bool(r.new_map_2026),
                            "incumbent": r.incumbent, "incumbent_party": r.incumbent_party,
                            "pres24": round(100 * (r.harris_2024 - r.trump_2024) / (r.harris_2024 + r.trump_2024), 3),
                            "votes24": int(r.total_2024),
                            "pres20": None if pd.isna(r.margin_2020) else float(r.margin_2020),
                            "acs": {k: (None if pd.isna(v) else float(v)) for k, v in a.items() if k not in ("state", "district")}}
    doc = {"source": "The Downballot, 2024 presidential results on the 2026 lines (9 Jul 2026; attribute if published); "
                     "Census ACS 2024 5-year (acs2024_cd119.csv: in the 10 redrawn states these are the old lines)",
           "national_pres24": NATIONAL_PRES24, "races": races}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, indent=1), encoding="utf-8")
    print(f"{out}: {len(races)} districts")
    return doc


def fit() -> dict:
    """b and psi on the 2022 and 2024 contested seats whose lines match the 2026 ones, and each year predicted from
    the other (given its national House vote)."""
    from . import housefit as hf
    p = hf.build_panel(hf.contests(hf.load_candidates()))
    p = p[p.year.isin([2022, 2024]) & p.contested & p.m.notna()]
    d = pd.read_csv(LOCAL / "districts_2026.csv")
    d["pres24"] = 100 * (d.harris_2024 - d.trump_2024) / (d.harris_2024 + d.trump_2024)
    redrawn_2024 = {"AL", "GA", "LA", "NC", "NY"}
    parts = []
    for y, col, nat in ((2024, "pres24", NATIONAL_PRES24), (2022, "margin_2020", 4.46)):
        dd = d[~d.new_map_2026 & (d.margin_2020.notna() | (y == 2024)) & (~d.state.isin(redrawn_2024) | (y == 2024))]
        j = dd.merge(p[p.year == y], left_on=["state", "district"], right_on=["state_po", "district"])
        parts.append(j.assign(year=y, lean=j[col] - nat))
    j = pd.concat(parts)
    house = {y: 100 * (g.d_votes.sum() - g.r_votes.sum()) / (g.d_votes.sum() + g.r_votes.sum()) for y, g in
             p.groupby("year")}
    j["y"] = j.m - j.year.map(house)
    ols = lambda t: np.linalg.lstsq(np.c_[t.lean, t.I_t], t.y, rcond=None)[0]
    out = {"b_lean_psi": ols(j).round(3).tolist(), "n": j.groupby("year").size().to_dict(), "cross": {}}
    for y in (2022, 2024):
        t = j[j.year == y]
        pred = np.c_[t.lean, t.I_t] @ ols(j[j.year != y])
        r = t.y - pred
        r -= r.mean()
        out["cross"][y] = {"sd": round(r.std(), 2), "sd_close": round(r[np.abs(pred + house[y]) < CLOSE].std(), 2)}
    print(json.dumps(out, indent=1))
    return out


# --- Wikipedia ---------------------------------------------------------------------------------------------------------

def _clean(v: str) -> str:
    v = re.sub(r"<!--.*?-->|<ref[^>]*/>|<ref.*?</ref>|\{\{[^{}]*\}\}", "", v, flags=re.S)
    v = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]", r"\1", v)
    v = re.sub(r"<br\s*/?>.*", "", v, flags=re.S).replace("'''", "").replace("''", "")
    return re.sub(r"\s+", " ", v).strip()


def _infobox(sec: str) -> dict:
    i = sec.find("{{Infobox election")
    if i < 0:
        return {}
    depth, j = 0, i
    while j < len(sec):
        if sec.startswith("{{", j):
            depth, j = depth + 1, j + 2
        elif sec.startswith("}}", j):
            depth, j = depth - 1, j + 2
            if depth == 0:
                break
        else:
            j += 1
    return {k.strip(): v for k, v in re.findall(r"^[ \t]*\|[ \t]*([\w ]+?)[ \t]*=[ \t]*(.*)$", sec[i:j], re.M)}


def name_key(name: str) -> str:
    toks = [t for t in re.sub(r"[^a-z ]", " ", _clean(name).lower().replace("jr.", "")).split() if len(t) > 1 or t == name]
    toks = [t for t in toks if t not in ("jr", "sr", "ii", "iii", "iv")]
    return f"{toks[-1]}_{toks[0][0]}" if toks else ""


def district(sec: str) -> dict:
    """Nominees (D, R, others), the member before the election and the ratings of one district section."""
    box, noms = _infobox(sec), {}
    for k, v in box.items():
        m = re.fullmatch(r"(?:nominee|candidate)(\d+)", k)
        if m and _clean(v):
            party = box.get(f"party{m.group(1)}", "")
            letter = "D" if "Democratic" in party else "R" if "Republican" in party else "O"
            noms.setdefault(letter, []).append(_clean(v))
    ratings = []
    for r in re.findall(r"\{\{USRaceRating\|([^}]*)\}\}", sec):
        parts = [p.strip().lower() for p in r.split("|") if p.strip().lower() not in ("flip", "")]
        if parts and parts[0] in RATING:
            side = next((p for p in parts[1:] if p in ("d", "r")), None)
            ratings.append(RATING[parts[0]] * (1 if side == "d" else -1 if side == "r" else 0))
    return {"nominees": noms, "before": _clean(box.get("before_election", "")), "ratings": ratings}


def wikipedia(snap: Path) -> dict:
    """{race_id: district()} from the snapshot's House pages; California's districts live on two sub-pages."""
    read = lambda title: (json.loads(gzip.decompress(f.read_bytes()))["revisions"][0]["slots"]["main"]["content"]
                          if (f := snap / "wikipedia" / f"{slug(title)}.gz").exists() else "")
    out = {}
    for name, st in STATE_CODES.items():
        if name in AT_LARGE:
            t = read(f"2026 United States House of Representatives election in {name}")
            if t:
                out[f"{st}-AL"] = district(t)
            continue
        pages = ([f"2026 United States House of Representatives elections in California (districts {r})"
                  for r in ("1–26", "27–52")] if st == "CA" else
                 [f"2026 United States House of Representatives elections in {name}"])
        for t in map(read, pages):
            secs = re.split(r"\n==\s*District (\d+)\s*==", t)
            for k in range(1, len(secs), 2):
                out[f"{st}-{int(secs[k])}"] = district(secs[k + 1])
    return out


# --- the day's seats ---------------------------------------------------------------------------------------------------

def seats(inp: dict, wiki: dict) -> pd.DataFrame:
    rows = []
    members = {}
    for rid, r in inp["races"].items():
        members.setdefault(r["state"], set()).add(name_key(r["incumbent"]))
    for rid, w in wiki.items():
        if w["before"] and rid in inp["races"]:
            members[inp["races"][rid]["state"]].add(name_key(w["before"]))
    for rid, r in inp["races"].items():
        w = wiki.get(rid)
        noms = w["nominees"] if w else {}
        d_in = any(name_key(n) in members[r["state"]] for n in noms.get("D", []))
        r_in = any(name_key(n) in members[r["state"]] for n in noms.get("R", []))
        if w and noms:
            inc = 0 if d_in == r_in else (1 if d_in else -1)
            fixed = "D" if not noms.get("R") else "R" if not (noms.get("D") or noms.get("O")) else None
        else:
            inc, fixed = {"D": 1, "R": -1}.get(r["incumbent_party"], 0), None
        rows.append({"race_id": rid, **{k: r[k] for k in ("state", "district", "new_map", "pres24", "votes24")},
                     "incumbent": r["incumbent"], "incumbent_party": r["incumbent_party"], "inc": inc, "fixed": fixed,
                     "checked": bool(w and noms), "nominees": noms, "ratings": w["ratings"] if w else []})
    s = pd.DataFrame(rows).set_index("race_id")
    s["fixed"] = s.fixed.astype(object).where(s.fixed.isin(["D", "R"]), None)
    return s


def anchor(s: pd.DataFrame, national: float) -> tuple[pd.Series, float]:
    """Margins with c set so the seats' votes add up to `national`."""
    base = B_LEAN * (s.pres24 - NATIONAL_PRES24) + PSI * s.inc * np.where(s.new_map, REDRAWN_PSI, 1.0)
    fixed = s.fixed.map({"D": 100.0, "R": -100.0})
    w = s.votes24 * np.where(fixed.notna(), UNCONTESTED_TURNOUT, 1.0)
    total = lambda c: float(np.dot(w, fixed.fillna(np.clip(base + c, -100, 100))) / w.sum()) - national
    c = brentq(total, -60, 60)
    return fixed.fillna(base + c), c


def tiers(s: pd.DataFrame, p: pd.Series) -> tuple[pd.Series, pd.Series]:
    """The ~40 simulated seats: consensus Toss-up, Tilt or Lean, then the closest by win chance, up to N_SIMULATE;
    'watch' for the next ones (win chance 3-97% or consensus Likely); the rest statistics."""
    consensus = s.ratings.map(lambda r: float(np.median(r)) if r else None)
    score = pd.Series(np.minimum(np.abs(p - 0.5) / 0.4, consensus.abs().fillna(9)), index=s.index)
    order = score[s.fixed.isna()].sort_values()
    simulate = set(order.index[:N_SIMULATE])
    tier, why = {}, {}
    for rid in s.index:
        reasons = ([f"stats-only {p[rid]:.0%}"] if 0.03 <= p[rid] <= 0.97 else []) + (
            [f"ratings {consensus[rid]:+.1f}"] if pd.notna(consensus[rid]) and abs(consensus[rid]) <= 2 else [])
        if s.fixed[rid] is not None:
            tier[rid], why[rid] = "statistics", [f"uncontested ({s.fixed[rid]})"]
        elif rid in simulate:
            tier[rid], why[rid] = "simulate", reasons or ["closest remaining"]
        else:
            tier[rid], why[rid] = ("watch", reasons) if reasons else ("statistics", ["safe by fundamentals and ratings"])
    return pd.Series(tier), pd.Series(why), consensus


def run(day: date, data: Path, levels: dict, snap: Path | None = None) -> dict:
    """house_levels.json and house_races.json for `day` (house_groups.json joins with the simulated seats' groups)."""
    from .statsday import snapshot_for
    inp = json.loads((data / "house" / "inputs.json").read_text(encoding="utf-8"))
    snap = snap or snapshot_for(data, day)
    s = seats(inp, wikipedia(snap))
    E = levels["national"]["E_hat"]
    margin, c = anchor(s, E)
    sd = pd.Series(np.where(margin.abs() < CLOSE, SD_CLOSE, SD_SAFE), index=s.index)
    p = pd.Series(norm.cdf(margin / np.sqrt(sd ** 2 + levels["national"]["var"])), index=s.index).where(
        s.fixed.isna(), s.fixed.map({"D": 1.0, "R": 0.0}))
    tier, why, consensus = tiers(s, p)
    base = {k: levels[k] for k in ("date", "schema", "days_to_election", "national") if k in levels}
    races = {rid: {"margin": round(float(margin[rid]), 3), "sd": float(sd[rid]), "w_polls": 0.0, "poll_margin": None,
                   "story_effect": 0.0, "story_effect_3nov": 0.0, "fundamentals": round(float(margin[rid]), 3),
                   "n_polls": 0, "last_poll": None, "fixed": s.fixed[rid], "tier": tier[rid], "state": s.state[rid],
                   "region": DIVISION[s.state[rid]],
                   "components": {"lean": round(B_LEAN * (s.pres24[rid] - NATIONAL_PRES24), 3),
                                  "incumbency": round(PSI * s.inc[rid] * (REDRAWN_PSI if s.new_map[rid] else 1), 3),
                                  "anchor": round(c, 3), "national_house_vote": E}}
             for rid in s.index}
    lv = base | {"office": "house", "units": levels.get("units"), "anchor_c": round(c, 3),
                 "params": {"b_lean": B_LEAN, "psi": PSI, "redrawn_psi": REDRAWN_PSI, "sd_close": SD_CLOSE,
                            "sd_safe": SD_SAFE, "uncontested_turnout": UNCONTESTED_TURNOUT}, "races": races}
    left = lambda rid: "D" if s.nominees[rid].get("D") or not s.checked[rid] else "O"
    meta = {rid: {"state": s.state[rid], "office": "house", "district": int(s.district[rid]), "special": False,
                  "rcv": s.state[rid] in ("ME", "AK"), "candidates": s.nominees[rid], "left_party": left(rid),
                  "incumbent": s.incumbent[rid], "incumbent_party": s.incumbent_party[rid],
                  "incumbent_running": {1: "D", -1: "R"}.get(int(s.inc[rid])), "status": "uncontested" if s.fixed[rid] is not None else "contested",
                  "checked": bool(s.checked[rid]), "new_map": bool(s.new_map[rid]), "p_dem_stats": round(float(p[rid]), 4),
                  "ratings_consensus": None if pd.isna(consensus[rid]) else round(float(consensus[rid]), 2),
                  "tier": tier[rid], "tier_reasons": why[rid]} for rid in s.index}
    out = data / "derived" / day.isoformat()
    out.mkdir(parents=True, exist_ok=True)
    (out / "house_levels.json").write_text(json.dumps(lv, indent=1), encoding="utf-8")
    (out / "house_races.json").write_text(json.dumps({"date": day.isoformat(), **meta}, indent=1), encoding="utf-8")
    seats_d = int((p > 0.5).sum())
    return {"seats": len(s), "checked": int(s.checked.sum()), "uncontested": int(s.fixed.notna().sum()),
            "anchor_c": round(c, 2), "expected_d_seats": round(float(p.sum()), 1), "d_favoured": seats_d,
            "tiers": tier.value_counts().to_dict()}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=["inputs", "fit", "run"])
    ap.add_argument("--date", type=date.fromisoformat)
    ap.add_argument("--data", type=Path, default=HERE.parent.parent / "simlab-data")
    a = ap.parse_args()
    if a.what == "inputs":
        inputs(a.data / "house" / "inputs.json")
    elif a.what == "fit":
        fit()
    else:
        levels = json.loads((a.data / "derived" / a.date.isoformat() / "levels.json").read_text(encoding="utf-8"))
        print(json.dumps(run(a.date, a.data, levels), indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
