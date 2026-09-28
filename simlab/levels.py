"""Starting levels (docs/stats-groundwork.md §5.2-5.4, engine-design §3): each 2026 race's election-day margin from a
poll average relative to the national generic ballot, blended with fundamentals. This is also the stats-only forecast.
Margins are two-party, Democrat (or the independent challenger) minus Republican, in points.

    python -m simlab.levels [--snapshot DIR] [--out DIR] [--run-id ID]   # default out: simlab-data/derived/<date>/
"""
from __future__ import annotations

import argparse
import json
import os
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

from . import calib
from .calib import sampling_var, two_party
from .polls import Race, same_pollster, surname

ELECTION = date(2026, 11, 3)
SPONSOR_PRIOR_POLLS = 20


def incumbency(race: Race) -> float:
    """+1 for a Democratic senator running again, -1 for a Republican, half for an appointed senator, 0 for an open seat
    (stats-groundwork §5.3)."""
    sign = {"D": 1.0, "R": -1.0}.get(race.incumbent, 0.0)
    if race.status.startswith(("Incumbent renominated", "Incumbent advanced")):
        return sign
    if race.status.startswith("Interim appointee nominated"):
        return sign * 0.5
    return 0.0


def relative_margins(pres: pd.DataFrame) -> dict:
    """{(year, state): state two-party presidential margin minus the nation's} from MIT's president file."""
    p = pres[pres.party_simplified.isin(["DEMOCRAT", "REPUBLICAN"]) & ~pres.writein.fillna(False).astype(bool)]
    v = p.pivot_table(index=["year", "state_po"], columns="party_simplified", values="candidatevotes", aggfunc="sum")
    nat = v.groupby(level="year").sum()
    nat_m = two_party(nat.DEMOCRAT, nat.REPUBLICAN)
    rel = two_party(v.DEMOCRAT, v.REPUBLICAN) - nat_m.reindex(v.index.get_level_values("year")).values
    return rel.to_dict()


def _same_person(a: str, b: str) -> bool:
    return surname(a).lower() == surname(b).lower() and a.strip()[:1].lower() == b.strip()[:1].lower()


def _pairs(rows: pd.DataFrame, party_col: str) -> tuple[str, str, float] | None:
    reps = rows[rows[party_col] == "REPUBLICAN"]
    rest = rows[rows[party_col] != "REPUBLICAN"]
    if reps.empty or rest.empty:
        return None
    r, l = reps.loc[reps.candidatevotes.idxmax()], rest.loc[rest.candidatevotes.idxmax()]
    return l.candidate, r.candidate, float(two_party(l.candidatevotes, r.candidatevotes))


def statewide_races(senate: pd.DataFrame, house: pd.DataFrame, extra: list[dict]) -> pd.DataFrame:
    """Every statewide contest we can score a candidate on: Senate races (decisive round), at-large House seats and the
    extra governor and attorney-general races, with the top non-Republican as `left`. `inc` is +1 if the left candidate
    held the office (won it in the previous term), -1 if the right one did."""
    rows = []
    s = senate[~senate.writein.fillna(False).astype(bool)].assign(stage=lambda x: x.stage.str.lower())
    s = s[s.stage.isin(["gen", "runoff", "gen runoff"])].assign(rnd=lambda x: (x.stage != "gen").astype(int))
    s = s[s.rnd == s.groupby(["year", "state_po", "special"]).rnd.transform("max")]
    for (year, st, _), g in s.groupby(["year", "state_po", "special"]):
        if (pair := _pairs(g, "party_simplified")):
            rows.append({"year": year, "state": st, "office": "senate", "term": 6, **dict(zip(("left", "right", "margin"), pair))})
    h = house[(house.district == 0) & (house.stage == "GEN") & ~house.writein.fillna(False).astype(bool)]
    for (year, st), g in h.groupby(["year", "state_po"]):
        if (pair := _pairs(g, "party")):
            rows.append({"year": year, "state": st, "office": "house at-large", "term": 2,
                         **dict(zip(("left", "right", "margin"), pair))})
    t = pd.DataFrame(rows)
    t["winner"] = np.where(t.margin > 0, t.left, t.right)
    inc = []
    for r in t.itertuples():
        prev = t[(t.state == r.state) & (t.office == r.office) & (t.year < r.year) & (t.year >= r.year - r.term)]
        held = lambda name: any(_same_person(name, w) for w in prev.winner)
        inc.append(1 if held(r.left) else -1 if held(r.right) else 0)
    t["inc"] = inc
    ext = pd.DataFrame([{"year": e["year"], "state": e["state"], "office": e["office"], "term": 4, "left": e["left"],
                         "right": e["right"], "margin": float(two_party(e["left_votes"], e["right_votes"])),
                         "inc": e["inc"]} for e in extra])
    return pd.concat([t.drop(columns="winner"), ext], ignore_index=True)


def expected_margin(year: int, state: str, inc: float, rel: dict, E: dict, coef: dict) -> float | None:
    """The fundamentals formula of stats-groundwork §5.3 for a past or present race, without the candidate term."""
    prev = [y for y in range(year - 1, year - 13, -1) if y % 4 == 0][:2]
    total = coef["const"] + coef["inc"] * inc + coef["E"] * E.get(year, np.nan)
    for c, y in zip(("r1", "r2"), prev):
        if coef[c]:
            total += coef[c] * rel.get((y, state), np.nan)
    return None if np.isnan(total) else float(total)


def overperformance(name: str, side: str, state: str, table: pd.DataFrame, rel: dict, E: dict, coef: dict,
                    since: int = 2014, until: int = 2024) -> float | None:
    """The candidate's last statewide result on the same side (left or right) within [since, until], minus what the
    fundamentals expected: + means better for the Democratic side."""
    rows = table[(table.state == state) & table.year.between(since, until)]
    rows = rows.loc[np.array([_same_person(name, n) for n in rows[side]], dtype=bool)].sort_values("year")
    for r in rows[::-1].itertuples():
        exp = expected_margin(r.year, state, r.inc, rel, E, coef)
        if exp is not None:
            return r.margin - exp
    return None


def candidate_effect(race: Race, table: pd.DataFrame, rel: dict, E: dict, coef: dict) -> tuple[float, dict]:
    """D10: the fitted share of each nominee's own last statewide over-performance, summed."""
    detail = {"left": overperformance(race.left, "left", race.state, table, rel, E, coef),
              "right": overperformance(race.right, "right", race.state, table, rel, E, coef)}
    return coef["pr"] * sum(v for v in detail.values() if v is not None), detail


def local_level(t: np.ndarray, y: np.ndarray, v: np.ndarray, q: float, end: float, smooth: bool = True):
    """Random walk plus noise on a daily grid from the first observation to `end` (days), diffuse start; observations
    on the same day are pooled by inverse variance. Returns grid, means and variances (smoothed by default)."""
    grid = np.arange(np.floor(t.min()), np.floor(end) + 1)
    day = np.floor(t)
    w = 1 / v
    obs = {d: (np.sum(w[day == d] * y[day == d]) / np.sum(w[day == d]), 1 / np.sum(w[day == d])) for d in np.unique(day)}
    xf, pf, xp, pp = (np.zeros(len(grid)) for _ in range(4))
    x, p = 0.0, 1e6
    for i, d in enumerate(grid):
        if i:
            p += q
        xp[i], pp[i] = x, p
        if d in obs:
            yo, vo = obs[d]
            k = p / (p + vo)
            x, p = x + k * (yo - x), (1 - k) * p
        xf[i], pf[i] = x, p
    if not smooth:
        return grid, xf, pf
    xs, ps = xf.copy(), pf.copy()
    for i in range(len(grid) - 2, -1, -1):
        c = pf[i] / pp[i + 1]
        xs[i] = xf[i] + c * (xs[i + 1] - xp[i + 1])
        ps[i] = pf[i] + c * c * (ps[i + 1] - pp[i + 1])
    return grid, xs, ps


def blend(r_poll: float | None, v_poll: float | None, f: float, sd_f: float) -> tuple[float, float, float]:
    """Inverse-variance blend of the poll-based and fundamentals estimates: (mean, variance, weight on polls)."""
    if r_poll is None:
        return f, sd_f ** 2, 0.0
    w = sd_f ** 2 / (sd_f ** 2 + v_poll)
    return w * r_poll + (1 - w) * f, 1 / (1 / v_poll + 1 / sd_f ** 2), w


def lv_gap(entries: list[dict]) -> float:
    """Median likely-minus-registered generic-ballot margin over polls VoteHub lists both ways, capped at +-2 (Field
    Guide); 0 with fewer than five pairs (stats-groundwork §2.3)."""
    by = {}
    for e in entries:
        if e.get("poll_type") != "generic-ballot" or e.get("population") not in ("lv", "rv"):
            continue
        a = {x["choice"]: x["pct"] for x in e["answers"]}
        if "Dem" in a and "Rep" in a:
            by.setdefault((e["pollster"], e["start_date"], e["end_date"]), {})[e["population"]] = two_party(a["Dem"], a["Rep"])
    diffs = [v["lv"] - v["rv"] for v in by.values() if len(v) == 2]
    return float(np.clip(np.median(diffs), -2, 2)) if len(diffs) >= 5 else 0.0


def map_priors(names, priors: dict) -> pd.Series:
    """Each 2026 pollster's historical lean (simlab/house_effect_priors.json): by alias, exact name, then name match;
    pollsters without a track record are left out (prior 0)."""
    known, aliases, out = priors.get("pollsters", {}), priors.get("aliases", {}), {}
    for name in names:
        key = aliases.get(name, name)
        if key not in known:
            hits = [k for k in known if same_pollster(name, k)]
            key = max(hits, key=lambda k: known[k].get("n", 0)) if hits else None
        if key is not None:
            out[name] = known[key]["mean"]
    return pd.Series(out, dtype=float)


def _flooding(p: pd.DataFrame) -> np.ndarray:
    """Polls by the same pollster in the same race within 7 days either side; each counts 1/k (Field Guide)."""
    k = np.ones(len(p))
    for _, g in p.groupby(["race", "pollster"]):
        t = g.t.values
        k[p.index.get_indexer(g.index)] = (np.abs(t[:, None] - t[None, :]) <= 7).sum(axis=1)
    return k


def _poll_rows(senate: pd.DataFrame, gb: pd.DataFrame, election: date) -> pd.DataFrame:
    def mid(df):
        return df["mid"] if "mid" in df else [s + (e - s) / 2 for s, e in zip(df.start, df.end)]
    rows = []
    if len(gb):
        rows.append(pd.DataFrame({"race": "US", "pollster": gb.pollster, "mid": mid(gb), "population": gb.population,
                                  "partisan": gb.partisan.fillna(""), "y": gb.margin,
                                  "s2": sampling_var(gb.dem, gb.rep, gb.n.fillna(gb.n.median()).clip(100, 20000))}))
    if len(senate):
        rows.append(pd.DataFrame({"race": senate.race_id, "pollster": senate.pollster, "mid": mid(senate),
                                  "population": senate.population, "partisan": senate.partisan.fillna(""),
                                  "y": senate.margin, "s2": sampling_var(senate.left, senate.right,
                                                                         senate.n.fillna(senate.n.median()).clip(100, 20000))}))
    p = pd.concat(rows, ignore_index=True)
    p["t"] = [(pd.Timestamp(m) - pd.Timestamp(election)).days for m in p.mid]
    return p


def effect(t: np.ndarray, items: list, election: date = ELECTION) -> np.ndarray:
    """Total story effect on days `t` (relative to election day) from (first_seen date, full effect, half-life)."""
    out = np.zeros(len(t))
    for first, full, h in items:
        t0 = (date.fromisoformat(first) - election).days
        out += np.where(t >= t0, full * 0.5 ** ((t - t0) / h), 0.0)
    return out


def build(race_list: list[Race], senate: pd.DataFrame, gb: pd.DataFrame, params: dict, priors: dict, rel: dict,
          E: dict, statewide: pd.DataFrame, today: date, election: date = ELECTION, entries: list[dict] | None = None,
          lv_gap_value: float | None = None, moves: dict | None = None) -> dict:
    """Starting levels for every race on `today` (stats-groundwork §5.2-5.4). With `moves` ({race_id or "US":
    [(first_seen, full effect, half-life)]}) this is the daily filter (§5.6): each poll is compared with the latent
    less the story effects in force on its date, and today's effects are added back, so a story moves the level only
    as far as the polls since it haven't already shown it. Without, it is the stats-only twin."""
    moves = moves or {}
    d = (election - today).days
    coef, sd_f = params["fundamentals"]["coef"], params["fundamentals"]["sd"]
    q_n, q_r = params["drift_daily_sd"]["national"] ** 2, params["drift_daily_sd"]["race"] ** 2
    ns2 = params["poll_extra_sd"]["value"] ** 2
    gap = lv_gap_value if lv_gap_value is not None else lv_gap(entries or [])
    p = _poll_rows(senate, gb, election)
    p = p[p.t <= -d].reset_index(drop=True)
    he, sp = calib.house_effects(p, prior=map_priors(p.pollster.unique(), priors))
    n_sp = p.partisan.value_counts()
    sp = {k: (n_sp.get(k, 0) * sp[k] + SPONSOR_PRIOR_POLLS * priors.get("sponsor_shift", {}).get(k, 0.0))
          / (n_sp.get(k, 0) + SPONSOR_PRIOR_POLLS) for k in ("DEM", "REP")}
    p["adj"] = (p.y + np.where(p.population == "lv", 0.0, gap) - p.pollster.map(he["mean"]).fillna(0.0)
                - p.partisan.map(sp).fillna(0.0))
    p["v"] = (p.s2 + ns2) * np.where(p.partisan.isin(["DEM", "REP"]), 2.0, 1.0) * _flooding(p)
    for r in set(p.race) & set(moves):
        sel = (p.race == r).values
        p.loc[sel, "adj"] -= effect(p.t.values[sel].astype(float), moves[r], election)
    now = lambda r: float(effect(np.array([-d], dtype=float), moves.get(r, []), election)[0])
    g = p[p.race == "US"]
    grid, nx, npv = local_level(g.t.values.astype(float), g.adj.values, g.v.values, q_n, -d)
    n_now, pn_now = float(nx[-1]) + now("US"), float(npv[-1])
    e_hat = n_now - params["generic_ballot_bias"]["mean"]
    var_n = pn_now + q_n * d + params["national_poll_bias_sd"]["value"] ** 2
    races = {}
    for race in race_list:
        rp = p[p.race == race.race_id]
        inc = incumbency(race)
        cand, detail = candidate_effect(race, statewide, rel, E, coef)
        lean = coef["r1"] * rel.get((2024, race.state), np.nan) + coef["r2"] * rel.get((2020, race.state), np.nan)
        fund = lean + coef["inc"] * inc + coef["E"] * e_hat + cand + coef["const"]
        r_poll, v_poll, poll_margin = None, None, None
        if len(rp):
            t = rp.t.values.astype(float)
            _, rx, rv = local_level(t, rp.adj.values - np.interp(t, grid, nx), rp.v.values + np.interp(t, grid, npv),
                                    q_r, -d, smooth=False)
            recent = int((t >= -d - 30).sum())
            sb = params["race_poll_bias_sd"]["value"] if recent >= 5 else params["race_poll_bias_sd"]["few_polls"]
            r_poll, v_poll = float(rx[-1]) + now(race.race_id) - now("US"), float(rv[-1] + q_r * d + sb ** 2)
            poll_margin = n_now + r_poll
        r_t, var_r, w = blend(r_poll, v_poll, fund - n_now, sd_f)
        races[race.race_id] = {
            "margin": n_now + r_t, "sd": float(np.sqrt(var_n + var_r)), "w_polls": w, "poll_margin": poll_margin,
            "fundamentals": fund, "n_polls": int(len(rp)),
            "last_poll": str(max(rp.mid)) if len(rp) else None,
            "components": {"lean": lean, "incumbency": inc, "candidate": cand, "candidate_detail": detail,
                           "national_house_vote": e_hat}}
    return {"date": str(today), "schema": 1, "units": "two-party margin, D (or independent challenger) minus R, points",
            "days_to_election": d,
            "national": {"N": n_now, "var": var_n, "E_hat": e_hat, "n_polls": int(len(g))},
            "lv_gap": gap, "sponsor_shift": sp, "house_effects": he["mean"].round(3).to_dict(), "races": races}


def inputs() -> tuple:
    """The fixed inputs: fitted parameters, pollster priors, state leans, national House vote, candidate records."""
    from .statsdata import mit
    here = Path(__file__).parent
    params = json.loads((here / "stats_params.json").read_text())
    priors = json.loads((here / "house_effect_priors.json").read_text())
    extra = json.loads((here / "statewide_extra.json").read_text())["races"]
    return (params, priors, relative_margins(mit("president")), calib.national_house_vote().to_dict(),
            statewide_races(mit("senate"), mit("house"), extra))


def compute(t: dict, today: date, run_id: str, moves: dict | None = None, inp: tuple | None = None) -> dict:
    """levels.json for one snapshot's poll tables (polls.build); with `moves`, the headline filter state."""
    params, priors, rel, E, statewide = inp or inputs()
    out = build(t["race_list"], t["senate"], t["generic_ballot"], params, priors, rel, E, statewide, today,
                entries=t["entries"], moves=moves)
    out.update(run_id=run_id, snapshot=t["snapshot"])
    return out


def main() -> None:
    from . import polls
    ap = argparse.ArgumentParser()
    ap.add_argument("--snapshot", type=Path, default=None)
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--run-id", default=os.environ.get("RUN_ID"))
    args = ap.parse_args()
    snap = args.snapshot or polls.latest_snapshot()
    today = date.fromisoformat(snap.parent.name)
    t = polls.build(snap)
    out = compute(t, today, args.run_id or f"{today}-local")
    dest = args.out or polls.SNAPSHOTS.parent / "derived" / str(today)
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "levels.json").write_text(json.dumps(out, indent=1, default=str))
    r = out["races"]
    print(f"levels {today} ({t['snapshot']}): {len(r)} races, national from {out['national']['n_polls']} generic-ballot "
          f"polls, LV gap {out['lv_gap']:+.2f}, {sum(v['n_polls'] > 0 for v in r.values())} races with polls -> {dest}")


if __name__ == "__main__":
    main()
