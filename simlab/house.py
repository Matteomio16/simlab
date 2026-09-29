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

Polls: each district's general-election polls (Wikipedia's district tables and VoteHub's us-representative entries,
merged as for the Senate) are corrected with the day's likely-voter gap, pollster leans and sponsor shift and blended
with the fundamentals exactly as a Senate race is (levels.build, stats-only). `sd` excludes the national part, which
the Monte Carlo adds. On 29 Sep: 192 polls in 84 seats, running 5.7 points more Democratic than the fundamentals on
average (2.8 of it is the generic ballot's bias, which the Senate carries too).

Voter groups (house_groups.json, the simulated seats): the district's citizen adults by white/non-white x degree
(ACS; the old lines in the 10 redrawn states), split by the state's party mix within each cell and tilted to the
district's 2024 presidential margin; Kev's group margins shifted to the seat's level; turnout and pi/mu the state's.

Inputs: <data>/house/inputs.json (built once by `python -m simlab.house inputs` from the Engine's data/house/, which
is gitignored; kept private in simlab-data).

    python -m simlab.house inputs          # data/house/*.csv -> ../simlab-data/house/inputs.json
    python -m simlab.house fit             # refits b and psi on 2022 and 2024 (MIT House file + The Downballot)
    python -m simlab.house run --date 2026-09-29 --data ../simlab-data   # writes to <data>/derived/<date>/
"""
from __future__ import annotations

import argparse
import gzip
import json
import re
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import brentq
from scipy.stats import norm

from . import levels
from .calib import DIVISION
from .groups import BASE, CELL_OF, GROUPS, KEV, PID_OF, PIMU, POS, race_groups, tilt
from .polls import STATE_CODES, VERSION_COLUMNS, Race, merge, wiki_polls
from .polls import _answer as answer, _vh_meta as vh_meta, build as build_polls
from .snap import AT_LARGE, slug

HERE = Path(__file__).parent
LOCAL = HERE.parent / "data" / "house"
B_LEAN, PSI, REDRAWN_PSI, UNCONTESTED_TURNOUT = 0.973, 4.45, 0.7, 0.71
SD_CLOSE, SD_SAFE, CLOSE = 5.5, 9.0, 15.0
NATIONAL_PRES24 = -1.68   # Harris minus Trump, two-party, summed over the 435 districts
N_SIMULATE, KEEP_DAYS = 40, 6
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
                            "acs": {k: (None if pd.isna(v) else float(v)) for k, v in a.items()
                                    if k not in ("state", "district")}}
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
    return {"nominees": noms, "before": _clean(box.get("before_election", "")), "ratings": ratings, "text": sec}


def wikipedia(snap: Path) -> dict:
    """{race_id: district()} from the snapshot's House pages; California's districts live on two sub-pages."""
    read = lambda title: (json.loads(gzip.decompress(f.read_bytes()))["revisions"][0]["slots"]["main"]["content"]
                          if (f := snap / "wikipedia" / f"{slug(title)}.gz").exists() else "")
    out = {}
    for name, st in STATE_CODES.items():
        if name in AT_LARGE:
            t = read(f"2026 United States House of Representatives election in {name}")
            if t:
                out[f"{st}-AL"] = district(t) | {"level": 2}
            continue
        pages = ([f"2026 United States House of Representatives elections in California (districts {r})"
                  for r in ("1–26", "27–52")] if st == "CA" else
                 [f"2026 United States House of Representatives elections in {name}"])
        for t in map(read, pages):
            secs = re.split(r"\n==\s*District (\d+)\s*==", t)
            for k in range(1, len(secs), 2):
                out[f"{st}-{int(secs[k])}"] = district(secs[k + 1]) | {"level": 3}
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
    c = brentq(total, -100, 100)
    return fixed.fillna(base + c), c


def tiers(s: pd.DataFrame, p: pd.Series, kept: set | None = None) -> tuple[pd.Series, pd.Series, pd.Series]:
    """The ~40 simulated seats: consensus Toss-up, Tilt or Lean, then the closest by win chance, up to N_SIMULATE;
    seats simulated on any of the last days (`kept`) stay in, as Senate races do, so a seat doesn't drop out after one
    quiet day (the list can then run a little over 40). 'watch' for the next ones (win chance 3-97% or consensus
    Likely); the rest statistics."""
    consensus = s.ratings.map(lambda r: float(np.median(r)) if r else np.nan).astype(float)
    score = pd.Series(np.minimum(np.abs(p - 0.5) / 0.4, consensus.abs().fillna(9)), index=s.index)
    order = score[s.fixed.isna()].sort_values()
    kept = {r for r in kept or () if r in order.index}
    simulate = kept | set(order.drop(list(kept)).index[:max(0, N_SIMULATE - len(kept))])
    tier, why = {}, {}
    for rid in s.index:
        reasons = ([f"stats-only {p[rid]:.0%}"] if 0.03 <= p[rid] <= 0.97 else []) + (
            [f"ratings {consensus[rid]:+.1f}"] if pd.notna(consensus[rid]) and abs(consensus[rid]) <= 2 else [])
        if s.fixed[rid] in ("D", "R"):
            tier[rid], why[rid] = "statistics", [f"uncontested ({s.fixed[rid]})"]
        elif rid in simulate:
            tier[rid], why[rid] = "simulate", (reasons or ["closest remaining"]) + (
                ["kept from the last days"] if rid in kept and rid not in set(order.index[:N_SIMULATE]) else [])
        else:
            tier[rid], why[rid] = ("watch", reasons) if reasons else ("statistics", ["safe by fundamentals and ratings"])
    return pd.Series(tier), pd.Series(why), consensus


# --- district polls, the blend and the simulated seats' voter groups ------------------------------------------------

def pair(s: pd.DataFrame, rid: str) -> Race | None:
    """The seat's matchup as a polls.Race: the Republican nominee against the Democrat (or the independent)."""
    noms = s.nominees[rid]
    left = (noms.get("D") or noms.get("O") or [None])[0]
    if s.fixed[rid] in ("D", "R") or not noms.get("R") or not left:
        return None
    return Race(s.state[rid], False, noms["R"][0], left, "D" if noms.get("D") else "O", "")


def district_polls(s: pd.DataFrame, wiki: dict, entries: list[dict]) -> pd.DataFrame:
    """Every seat's general-election polls, Wikipedia's district tables and VoteHub's us-representative entries
    (subject "2026 ME-02"), merged as for the Senate (polls.merge)."""
    at_large = {STATE_CODES[n] for n in AT_LARGE}
    frames, vh = [], []
    for rid in s.index:
        race, w = pair(s, rid), wiki.get(rid)
        if race and w:
            frames.append(wiki_polls(w["text"], race, w["level"]).assign(race_id=rid))
    for e in entries:
        m = re.fullmatch(r"2026 ([A-Z]{2})-(\d+)", e.get("subject") or "")
        if e.get("poll_type") != "us-representative" or not m:
            continue
        rid = f"{m.group(1)}-AL" if m.group(1) in at_large else f"{m.group(1)}-{int(m.group(2))}"
        race = pair(s, rid) if rid in s.index else None
        left, right = (answer(e["answers"], race.left), answer(e["answers"], race.right)) if race else (None, None)
        if left is None or right is None or (left == right == 50 and len(e["answers"]) == 2):
            continue
        rest = sum(a["pct"] for a in e["answers"]) - left - right
        vh.append({"race_id": rid, **vh_meta(e), "left": left, "right": right, "other": rest if rest > 0 else np.nan,
                   "undecided": np.nan})
    wiki_df = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=VERSION_COLUMNS + ["race_id"])
    return merge(wiki_df, pd.DataFrame(vh))


def build(base: dict, levels_json: dict, paths: dict | None = None, election: date = levels.ELECTION) -> dict:
    """house_levels.json for one set of story paths, by levels.build's rules (paths None: the stats-only twin).
    `paths` is moves.paths' {race_id or "US": [(first_seen, last_seen, full, age half-life, after half-life)]}; a seat
    without its own stories takes the nation's. Each district poll is taken less the effects in force on its date,
    relative to the national path; margin = n_now + r_t + the story effect left on election day; poll_margin adds
    today's. The fundamentals are anchored to this call's `levels_json` national E_hat. Cheap (no parsing): statsday
    calls it for the twin, the headline, the news parts and the "if the election were today" view (election=day).
    `sd` excludes the national variance, which the Monte Carlo adds."""
    s, hp, t, day, params = base["seats"], base["polls"], base["t"], base["day"], base["params"]
    paths = paths or {}
    path = lambda r: paths.get(r, paths.get("US", []))
    d = (election - day).days
    q_n, q_r = params["drift_daily_sd"]["national"] ** 2, params["drift_daily_sd"]["race"] ** 2
    now = lambda r: float(levels.effect(np.array([-d], dtype=float), path(r), election)[0])
    eday = lambda r: float(levels.effect(np.array([0.0]), path(r), election, stop=-d)[0])
    frames = base.setdefault("frames", {})
    if election not in frames:
        frames[election] = levels.poll_frame(t["senate"], t["generic_ballot"], params, base["priors"], day, election,
                                             t["entries"])
    pf, gap, he, sp = frames[election]
    g = pf[pf.race == "US"]
    gt = g.t.values.astype(float)
    grid, nx, npv = levels.local_level(gt, g.adj.values - levels.effect(gt, path("US"), election), g.v.values, q_n, -d)
    n_now = float(nx[-1])
    rows = levels._poll_rows(hp, pd.DataFrame(), election) if len(hp) else pd.DataFrame(columns=["race", "t"])
    rows = rows[rows.t <= -d].reset_index(drop=True)
    if len(rows):
        rows["adj"] = (rows.y + np.where(rows.population == "lv", 0.0, gap) - rows.pollster.map(he["mean"]).fillna(0.0)
                       - rows.partisan.map(sp).fillna(0.0))
        rows["v"] = ((rows.s2 + params["poll_extra_sd"]["value"] ** 2)
                     * np.where(rows.partisan.isin(["DEM", "REP"]), 2.0, 1.0) * levels._flooding(rows))
    E = levels_json["national"]["E_hat"]
    fund, c = anchor(s, E)
    tier = base.get("tier", {})
    races = {}
    for rid in s.index:
        sd_f = SD_CLOSE if abs(fund[rid]) < CLOSE else SD_SAFE
        row = {"margin": round(float(fund[rid]), 3), "sd": sd_f, "w_polls": 0.0, "poll_margin": None,
               "story_effect": 0.0, "story_effect_3nov": 0.0, "fundamentals": round(float(fund[rid]), 3),
               "n_polls": 0, "last_poll": None}
        if s.fixed[rid] not in ("D", "R"):
            rp = rows[rows.race == rid]
            r_poll = v_poll = poll_margin = None
            if len(rp):
                tt = rp.t.values.astype(float)
                adj = rp.adj.values - levels.effect(tt, path(rid), election)
                _, rx, rv = levels.local_level(tt, adj - np.interp(tt, grid, nx), rp.v.values + np.interp(tt, grid, npv),
                                               q_r, -d, smooth=False)
                recent = int((tt >= -d - 30).sum())
                sb = params["race_poll_bias_sd"]["value"] if recent >= 5 else params["race_poll_bias_sd"]["few_polls"]
                r_poll, v_poll = float(rx[-1]), float(rv[-1] + q_r * d + sb ** 2)
                poll_margin = n_now + r_poll + now(rid)
            r_t, var_r, w = levels.blend(r_poll, v_poll, float(fund[rid]) - n_now, sd_f)
            row.update(margin=round(n_now + r_t + eday(rid), 3), sd=round(float(np.sqrt(var_r)), 3), w_polls=round(w, 3),
                       poll_margin=None if poll_margin is None else round(poll_margin, 3),
                       story_effect=round(now(rid), 3), story_effect_3nov=round(eday(rid), 3), n_polls=int(len(rp)),
                       last_poll=str(max(rp.mid)) if len(rp) else None)
        races[rid] = row | {"fixed": s.fixed[rid] if s.fixed[rid] in ("D", "R") else None, "tier": tier.get(rid),
                            "state": s.state[rid],
                            "region": DIVISION[s.state[rid]],
                            "components": {"lean": round(B_LEAN * (s.pres24[rid] - NATIONAL_PRES24), 3),
                                           "incumbency": round(PSI * s.inc[rid] * (REDRAWN_PSI if s.new_map[rid] else 1), 3),
                                           "anchor": round(c, 3), "national_house_vote": E}}
    national = {k: levels_json[k] for k in ("date", "schema", "days_to_election", "national") if k in levels_json}
    return national | {"office": "house", "units": levels_json.get("units"), "anchor_c": round(c, 3),
                       "params": {"b_lean": B_LEAN, "psi": PSI, "redrawn_psi": REDRAWN_PSI, "sd_close": SD_CLOSE,
                                  "sd_safe": SD_SAFE, "uncontested_turnout": UNCONTESTED_TURNOUT}, "races": races}


def cells(acs: dict) -> dict:
    """Citizen adults by white (non-Hispanic) / non-white x four-year degree, as shares: CVAP and its degree share
    (B29002), white citizen adults (B05003H), white degree share among 25+ (C15002H) scaled to 18+ by the district's
    CVAP-to-25+ degree ratio (B15002)."""
    e = lambda t, *k: sum(acs[f"{t}_{i:03d}E"] for i in k)
    total, deg = e("B29002", 1), e("B29002", 7, 8) / e("B29002", 1)
    white = e("B05003H", 9, 11, 20, 22)
    deg25 = e("B15002", 15, 16, 17, 18, 32, 33, 34, 35) / e("B15002", 1)
    wd = white * min(1.0, e("C15002H", 6, 11) / e("C15002H", 1) * deg / deg25)
    nd = max(0.0, total * deg - wd)
    return {"white / Four-year college degree or more": wd / total,
            "white / No four-year college degree": (white - wd) / total,
            "non-white / Four-year college degree or more": nd / total,
            "non-white / No four-year college degree": max(0.0, total - white - nd) / total}


def district_groups(r: dict, margin: float, base: dict, pimu: dict, kev: dict) -> dict:
    """A district's 28 groups (groups.race_groups): the ACS cell shares split by the state's party mix within each
    cell, tilted (groups.tilt) until the groups reproduce the district's 2024 presidential margin, with Kev's group
    margins (the survey's where Kev has none); turnout and d0 are the state's."""
    b = base["states"][r["state"]]
    share = cells(r["acs"])
    df = pd.DataFrame({"cell": [CELL_OF[g] for g in GROUPS], "pos": [POS[PID_OF[g]] for g in GROUPS]}, index=GROUPS)
    tot = {c: sum(b[g]["n"] for g in GROUPS if CELL_OF[g] == c) for c in share}
    df["n"] = [share[CELL_OF[g]] * b[g]["n"] / tot[CELL_OF[g]] for g in GROUPS]
    df["t24"] = [b[g]["t"] for g in GROUPS]
    df["m24"] = [kev.get(g, b[g]["d0"]) for g in GROUPS]
    _, n = tilt(df, r["pres24"] / 100)
    dist = {g: {"n": round(float(n[i]), 5), "t": b[g]["t"], "d0": b[g]["d0"]} for i, g in enumerate(GROUPS)}
    return race_groups(dist, pimu["states"][r["state"]], margin, kev)


def prepare(day: date, data: Path, levels_json: dict, snap: Path | None = None, run_id: str | None = None) -> dict:
    """The once-a-day part: seats and nominees (Wikipedia), district polls, the stats-only twin (build with no
    paths, on the twin's `levels_json`), tiers from it and the simulated seats' voter groups at its margins."""
    from .statsday import snapshot_for
    inp = json.loads((data / "house" / "inputs.json").read_text(encoding="utf-8"))
    snap = snap or snapshot_for(data, day)
    wiki = wikipedia(snap)
    s = seats(inp, wiki)
    t = build_polls(snap)
    params, priors = levels.inputs()[:2]
    base = {"day": day, "run_id": run_id, "inp": inp, "seats": s, "t": t, "params": params, "priors": priors,
            "polls": district_polls(s, wiki, t["entries"])}
    twin = build(base, levels_json)
    margin = pd.Series({rid: r["margin"] for rid, r in twin["races"].items()})
    sd = pd.Series({rid: r["sd"] for rid, r in twin["races"].items()})
    p = pd.Series(norm.cdf(margin / np.sqrt(sd ** 2 + levels_json["national"]["var"])), index=s.index).where(
        s.fixed.isna(), s.fixed.map({"D": 1.0, "R": 0.0}))
    past = [data / "derived" / (day - timedelta(days=k)).isoformat() / "house_races.json" for k in range(1, KEEP_DAYS + 1)]
    kept = {rid for f in past if f.exists() for rid, x in json.loads(f.read_text(encoding="utf-8")).items()
            if isinstance(x, dict) and x.get("tier") == "simulate"}
    tier, why, consensus = tiers(s, p, kept)
    base["tier"] = tier.to_dict()
    for rid, r in twin["races"].items():
        r["tier"] = tier[rid]
    left = lambda rid: "D" if s.nominees[rid].get("D") or not s.checked[rid] else "O"
    base["races"] = {rid: {"state": s.state[rid], "office": "house", "district": int(s.district[rid]),
                           "special": False, "rcv": s.state[rid] in ("ME", "AK"), "candidates": s.nominees[rid],
                           "left_party": left(rid), "incumbent": s.incumbent[rid],
                           "incumbent_party": s.incumbent_party[rid],
                           "incumbent_running": {1: "D", -1: "R"}.get(int(s.inc[rid])),
                           "status": "uncontested" if s.fixed[rid] in ("D", "R") else "contested",
                           "checked": bool(s.checked[rid]), "new_map": bool(s.new_map[rid]),
                           "p_dem_stats": round(float(p[rid]), 4),
                           "ratings_consensus": None if pd.isna(consensus[rid]) else round(float(consensus[rid]), 2),
                           "tier": tier[rid], "tier_reasons": why[rid]} for rid in s.index}
    gbase, pimu = (json.loads(f.read_text(encoding="utf-8")) for f in (BASE, PIMU))
    kev = json.loads(KEV.read_text(encoding="utf-8")) if KEV.exists() else {}
    base["groups"] = {"date": day.isoformat(), "run_id": run_id, "schema": 1,
                      "units": "as groups.json; n from the district's ACS citizen adults (old lines in the 10 redrawn "
                               "states)",
                      **{rid: district_groups(inp["races"][rid], float(margin[rid]), gbase, pimu,
                                              kev.get("states", {}).get(s.state[rid], {}))
                         for rid in s.index if tier[rid] == "simulate"}}
    base["twin"] = twin
    return base


def write(base: dict, house_levels: dict, out: Path) -> None:
    """house_levels.json (the given build), house_races.json, house_groups.json and house_polls.csv into `out`."""
    out.mkdir(parents=True, exist_ok=True)
    (out / "house_levels.json").write_text(json.dumps(house_levels, indent=1), encoding="utf-8")
    (out / "house_races.json").write_text(json.dumps({"date": base["day"].isoformat(), **base["races"]}, indent=1),
                                          encoding="utf-8")
    (out / "house_groups.json").write_text(json.dumps(base["groups"], indent=1), encoding="utf-8")
    base["polls"].to_csv(out / "house_polls.csv", index=False)


def summary(base: dict) -> dict:
    s, r = base["seats"], base["races"]
    return {"seats": len(s), "checked": int(s.checked.sum()), "uncontested": int(s.fixed.notna().sum()),
            "with_polls": sum(x["n_polls"] > 0 for x in base["twin"]["races"].values()), "polls": int(len(base["polls"])),
            "anchor_c": base["twin"]["anchor_c"], "expected_d_seats": round(sum(x["p_dem_stats"] for x in r.values()), 1),
            "d_favoured": sum(x["p_dem_stats"] > 0.5 for x in r.values()),
            "tiers": pd.Series({k: x["tier"] for k, x in r.items()}).value_counts().to_dict(),
            "groups": len(base["groups"]) - 4}


def run(day: date, data: Path, levels_json: dict, snap: Path | None = None, run_id: str | None = None) -> dict:
    """prepare, then write the stats-only twin into <data>/derived/<day>/; returns a summary."""
    base = prepare(day, data, levels_json, snap, run_id)
    write(base, base["twin"], data / "derived" / day.isoformat())
    return summary(base)


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
        lv = json.loads((a.data / "derived" / a.date.isoformat() / "levels.json").read_text(encoding="utf-8"))
        print(json.dumps(run(a.date, a.data, lv), indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
