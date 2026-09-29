"""Voter groups: the 28 party-ID x white/non-white x degree groups (engine-design §3.1, stats-groundwork §5.5).

    python -m simlab.groups --fit             writes simlab/pimu.json
    python -m simlab.groups --kev ANSWERS     writes simlab/kev_groups.json (Kev's margins, plus the nation's)

pi, the persuadable share, and mu, the mobilisable share, by state and group, from the CES pre- and post-election
waves of the 2018 and 2022 midterms (CES cumulative file), shrunk state -> census division -> nation. 2024 is kept as a
check.
"""
from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import brentq
from scipy.special import expit, logit

from .calib import DIVISION
from .statsdata import DATA

HERE = Path(__file__).parent
GROUPS = [a["id"] for a in json.loads((HERE / "archetypes.json").read_text(encoding="utf-8"))]
PID = {"strong democrat": "Strong Democrat", "not very strong democrat": "Not very strong Democrat",
       "lean democrat": "Lean Democrat", "independent": "Independent", "not sure": "Independent",
       "don't know": "Independent", "lean republican": "Lean Republican",
       "not very strong republican": "Not very strong Republican", "strong republican": "Strong Republican"}
CHOSE = {"[Democrat / Candidate 1]", "[Republican / Candidate 2]", "[Other / Candidate 3]", "[Other / Candidate 4]",
         "Other"}
UNDECIDED = {"Not Sure", "No One"}
FIRM = {"Yes, definitely", "I already voted (early or absentee)", "I plan to vote before Election Day"}
PSEUDO = 50
COLS = ["year", "st", "weight", "weight_post", "tookpost", "pid7", "race", "hispanic", "educ", "intent_sen",
        "voted_sen", "intent_turnout_self", "voted_turnout_self", "vv_turnout_gvm", "vv_regstatus"]
PIMU = HERE / "pimu.json"
KEV = HERE / "kev_groups.json"


def group_of(pid7, race, hispanic, educ) -> str | None:
    p = PID.get(str(pid7).lower())
    if p is None:
        return None
    white = race == "White" and hispanic != "Yes"
    degree = "Four-year college degree or more" if educ in ("4-Year", "Post-Grad") else "No four-year college degree"
    return f"{p} / {'white' if white else 'non-white'} / {degree}"


def persuadable(intent: pd.Series, voted: pd.Series) -> pd.Series:
    """1 if undecided before the election or the Senate vote differs from the intention; NaN outside the base, which
    is Senate voters who gave a pre-election preference or said they were unsure."""
    base = voted.isin(CHOSE) & (intent.isin(CHOSE) | intent.isin(UNDECIDED))
    return (intent.isin(UNDECIDED) | (intent != voted)).astype(float).where(base)


def mobilisable(intent: pd.Series, voted: pd.Series) -> pd.Series:
    """1 if the pre-election turnout intention was unsure ("probably", "undecided", no answer) or turned out wrong:
    intenders who didn't vote, non-intenders who did."""
    firm, no = intent.isin(FIRM), intent == "No"
    return ((~firm & ~no) | (firm & ~voted) | (no & voted)).astype(float)


def shrink(p: float, n: float, prior: float, k: float = PSEUDO) -> float:
    return (n * p + k * prior) / (n + k)


def _shares(d: pd.DataFrame, col: str, w: str, by: list[str]) -> pd.DataFrame:
    g = d.assign(_wy=d[col] * d[w]).groupby(by)
    return pd.DataFrame({"p": g._wy.sum() / g[w].sum(), "n": g.size()})


def shrunk(d: pd.DataFrame, col: str, w: str, by: str = "group", k: float = PSEUDO) -> tuple[pd.DataFrame, dict]:
    """Weighted share of `col` for each `by` within each state, shrunk toward the census division's, which is shrunk
    toward the nation's, each with `k` respondents' worth of prior. Returns (national shares, {state: {key: share}})."""
    d = d[d[col].notna() & d[w].notna()]
    d = d.assign(div=d.st.map(DIVISION))
    nat, div, st = (_shares(d, col, w, b) for b in ([by], ["div", by], ["st", by]))
    out = {s: {} for s in DIVISION}
    for g in nat.index:
        for s, dv in DIVISION.items():
            p_div = shrink(*(div.loc[(dv, g)] if (dv, g) in div.index else (0.0, 0.0)), nat.p[g], k)
            out[s][g] = float(shrink(*(st.loc[(s, g)] if (s, g) in st.index else (0.0, 0.0)), p_div, k))
    return nat, out


def fit(df: pd.DataFrame, k: float = PSEUDO) -> dict:
    """pi and mu by state and group, shrunk state -> census division -> nation."""
    national, states = {}, {s: {} for s in DIVISION}
    for name, col, w in (("pi", "persuadable", "weight_post"), ("mu", "mobilisable", "weight")):
        nat, st = shrunk(df, col, w, k=k)
        for g in nat.index:
            national.setdefault(g, {}).update({name: round(float(nat.p[g]), 4), f"n_{name}": int(nat.n[g])})
            for s in DIVISION:
                states[s].setdefault(g, {})[name] = round(st[s][g], 4)
    return {"national": national, "states": states}


def tilt(df: pd.DataFrame, target: float) -> tuple[float, np.ndarray]:
    """Tilts the party mix within each demographic cell by exp(theta x position) until the groups' voters reproduce
    `target` (the 2024 presidential margin, -1..1); each cell keeps its population share. Columns: cell, pos, n, t24,
    m24."""
    cell, n0, pos = df.cell.values, df.n.values, df.pos.values
    total = pd.Series(n0).groupby(cell).transform("sum").values

    def tilted(theta):
        w = n0 * np.exp(theta * pos)
        return w * total / pd.Series(w).groupby(cell).transform("sum").values

    def gap(theta):
        v = tilted(theta) * df.t24.values
        return float(np.dot(v, df.m24.values) / v.sum()) - target

    theta = brentq(gap, -5, 5)
    return theta, tilted(theta)


def party_turnout(t_cell: float, n: np.ndarray, lor: np.ndarray) -> np.ndarray:
    """Turnout by party-ID level within one demographic cell: the cell's rate spread by the log odds ratios, shifted
    so the cell keeps its rate."""
    base = logit(np.clip(t_cell, 1e-4, 1 - 1e-4)) + lor
    c = brentq(lambda c: float(np.dot(n, expit(base + c)) / n.sum()) - t_cell, -10, 10)
    return expit(base + c)


def shift(d: np.ndarray, e: np.ndarray, target: float) -> np.ndarray:
    """Shifts every group's D share by the same amount on the logit scale until the voters' margin is `target`."""
    p = logit(np.clip((1 + d) / 2, 1e-4, 1 - 1e-4))
    c = brentq(lambda c: float(np.dot(e, 2 * expit(p + c) - 1) / e.sum()) - target, -20, 20)
    return 2 * expit(p + c) - 1


def race_groups(base: dict, pimu: dict, margin: float, kev: dict | None = None) -> dict:
    """A race's groups: population share n, turnout t, margin d shifted to the race's level (`margin`, points), and the
    persuadable and mobilisable shares. d starts from Kev's margin where `kev` has the group, else from the survey's d0."""
    gs, kev = list(base), kev or {}
    n, t = (np.array([base[g][k] for g in gs]) for k in ("n", "t"))
    d = shift(np.array([kev.get(g, base[g]["d0"]) for g in gs]), n * t, margin / 100)
    return {g: {"n": base[g]["n"], "t": base[g]["t"], "d": round(float(d[i]), 4), "pi": pimu[g]["pi"],
                "mu": pimu[g]["mu"]} for i, g in enumerate(gs)}


def build(levels: dict, base: dict, pimu: dict, day: str, run_id: str, kev: dict | None = None) -> dict:
    """groups.json (engine-design §7): every race's groups at its level, plus the nation's at the national level N. The
    pattern across groups comes from Kev (kev_groups.json) where it answered, else from the survey (Matteo, 29 Sep)."""
    kev = kev or {}
    out = {"date": day, "run_id": run_id, "schema": 1,
           "units": "n share of adult citizens; t midterm turnout; d D (or independent challenger) minus R among the "
                    "group's voters, -1..1; pi persuadable and mu mobilisable shares, 0..1",
           "d_source": f"Kev {kev['run']}: 2024 presidential vote by group (simlab/kev_groups.json); survey d0 where "
                       "Kev has no answer" if kev else
                       "survey d0: CES 2018/2022 Senate vote by group, House vote for US (simlab/groups_base.json)"}
    for rid, r in levels["races"].items():
        s = rid.split("-")[0]
        out[rid] = race_groups(base["states"][s], pimu["states"][s], r["margin"], kev.get("states", {}).get(s))
    out["US"] = race_groups(base["US"], pimu["national"], levels["national"]["N"], kev.get("US"))
    return out


def kev_national(states: dict, base: dict, votes: dict) -> dict:
    """The nation's Kev margin for each group: the states' margins weighted by the group's voters there, the state's
    2024 presidential votes times the group's share of its midterm voters (n t / sum n t)."""
    w, d = {}, {}
    for s, x in states.items():
        b = base["states"][s]
        tot = sum(v["n"] * v["t"] for v in b.values())
        for g, m in x.items():
            k = votes[s] * b[g]["n"] * b[g]["t"] / tot
            w[g], d[g] = w.get(g, 0.0) + k, d.get(g, 0.0) + k * m
    return {g: round(d[g] / w[g], 4) for g in w}


POS = {"Strong Democrat": 3, "Not very strong Democrat": 2, "Lean Democrat": 1, "Independent": 0,
       "Lean Republican": -1, "Not very strong Republican": -2, "Strong Republican": -3}
PID_OF = {g: g.split(" / ")[0] for g in GROUPS}
CELL_OF = {g: g.split(" / ", 1)[1] for g in GROUPS}
BASE = HERE / "groups_base.json"
BASE_COLS = ["year", "st", "weight", "vvweight_post", "pid7", "race", "hispanic", "educ", "vv_turnout_gvm",
             "voted_sen_party", "voted_rep_party", "voted_pres_24"]


def _cps(year: int, k: float = PSEUDO, pop: dict | None = None) -> tuple[dict, dict]:
    """CPS by demographic cell: population shares and turnout for each state and the nation. A state's cell rates are
    shrunk toward the national ones, then shifted on the logit scale to the state's official turnout, weighting the
    cells by `pop` if given (another year's population shares), else by this year's."""
    from . import cps
    from .polls import STATE_CODES
    abbr = {**STATE_CODES, "District of Columbia": "DC"}
    df = cps.respondents(year)
    df = df.assign(st=df.state.map(abbr), cell=np.where(df.race5 == "White", "white", "non-white") + " / " + df.degree,
                   wv=df.commonweight * df.voted)
    official = {abbr[k2]: v for k2, v in cps.official(year).items() if k2 in abbr}
    g = df.groupby("cell")
    shares, turnout = {"US": dict(g.weight_raw.sum() / df.weight_raw.sum())}, {"US": dict(g.wv.sum() / g.commonweight.sum())}
    for s, d in df.groupby("st"):
        g = d.groupby("cell")
        share = g.weight_raw.sum() / d.weight_raw.sum()
        prior = pd.Series(turnout["US"]).reindex(share.index)
        t = (g.size() * g.wv.sum() / g.commonweight.sum() + k * prior) / (g.size() + k)
        w = pd.Series(pop[s]).reindex(share.index) if pop else share
        c = brentq(lambda x: float(np.dot(w, expit(logit(t) + x))) - official[s], -5, 5)
        shares[s], turnout[s] = dict(share), dict(expit(logit(t) + c))
    return shares, turnout


def _ces() -> pd.DataFrame:
    df = pd.read_stata(DATA / "cumulative_2006-2025.dta", columns=BASE_COLS)
    df = df[df.year.isin([2018, 2022, 2023, 2024, 2025])].copy()
    for c in df.select_dtypes("category"):
        df[c] = df[c].astype(object)
    df["group"] = [group_of(*r) for r in zip(df.pid7, df.race, df.hispanic, df.educ)]
    df = df[df.group.notna()].copy()
    df["pid"], df["cell"] = df.group.map(PID_OF), df.group.map(CELL_OF)
    df["voted"] = (df.vv_turnout_gvm == "Voted").astype(float)
    two = lambda col, d, r: np.where(df[col] == d, 1.0, np.where(df[col] == r, 0.0, np.nan))
    df["dem_sen"] = np.where(df.voted == 1, two("voted_sen_party", "Democratic", "Republican"), np.nan)
    df["dem_rep"] = np.where(df.voted == 1, two("voted_rep_party", "Democratic", "Republican"), np.nan)
    df["harris"] = np.where(df.voted == 1, two("voted_pres_24", "Kamala Harris", "Donald Trump"), np.nan)
    return df


def _lor(d: pd.DataFrame) -> dict:
    """Each group's log odds ratio of validated turnout against its demographic cell (national)."""
    pg, pc = _shares(d, "voted", "weight", ["group"]).p, _shares(d, "voted", "weight", ["cell"]).p
    return {g: float(logit(pg[g]) - logit(pc[CELL_OF[g]])) for g in pg.index}


def _pres(year: int = 2024) -> pd.DataFrame:
    from .statsdata import mit
    p = mit("president")
    p = p[(p.year == year) & p.party_simplified.isin(["DEMOCRAT", "REPUBLICAN"]) & ~p.writein.fillna(False).astype(bool)]
    return p.pivot_table(index="state_po", columns="party_simplified", values="candidatevotes", aggfunc="sum")


def _pres_margins(year: int = 2024) -> dict:
    v = _pres(year)
    out = ((v.DEMOCRAT - v.REPUBLICAN) / (v.DEMOCRAT + v.REPUBLICAN)).to_dict()
    t = v.sum()
    return out | {"US": float((t.DEMOCRAT - t.REPUBLICAN) / (t.DEMOCRAT + t.REPUBLICAN))}


def fit_base(k: float = PSEUDO) -> dict:
    """n, t and d0 for the 28 groups in every state and the nation (stats-groundwork §5.5)."""
    ces = _ces()
    pop24, t24 = _cps(2024, k)
    _, t22 = _cps(2022, k, pop24)
    recent, mid = ces[ces.year >= 2022], ces[ces.year.isin([2018, 2022])]
    mix = {s: {} for s in [*DIVISION, "US"]}
    for pid in POS:
        nat, st = shrunk(recent.assign(ind=(recent.pid == pid).astype(float)), "ind", "weight", by="cell", k=k)
        for s in DIVISION:
            mix[s] |= {f"{pid} / {c}": v for c, v in st[s].items()}
        mix["US"] |= {f"{pid} / {c}": float(v) for c, v in nat.p.items()}
    lor22, lor24 = _lor(mid), _lor(ces[ces.year == 2024])
    m24_nat, m24 = shrunk(ces[ces.year == 2024], "harris", "vvweight_post", k=k)
    d0_nat, d0 = shrunk(mid, "dem_sen", "vvweight_post", k=k)
    house = _shares(mid[mid.dem_rep.notna()], "dem_rep", "vvweight_post", ["group"]).p
    m24["US"], d0["US"] = dict(m24_nat.p), dict(house)
    target = _pres_margins()
    out, thetas = {}, {}
    for s in [*DIVISION, "US"]:
        df = pd.DataFrame({"cell": [CELL_OF[g] for g in GROUPS], "pos": [POS[PID_OF[g]] for g in GROUPS]}, index=GROUPS)
        df["n"] = [pop24[s][CELL_OF[g]] * mix[s][g] for g in GROUPS]
        df["t24"] = np.nan
        for c, idx in df.groupby("cell").groups.items():
            df.loc[idx, "t24"] = party_turnout(t24[s][c], df.n[idx].values, np.array([lor24[g] for g in idx]))
        df["m24"] = [2 * m24[s][g] - 1 for g in GROUPS]
        thetas[s], df["n"] = tilt(df, target[s])
        for c, idx in df.groupby("cell").groups.items():
            df.loc[idx, "t"] = party_turnout(t22[s][c], df.n[idx].values, np.array([lor22[g] for g in idx]))
        out[s] = {g: {"n": round(float(df.n[g]), 5), "t": round(float(df.t[g]), 4), "d0": round(2 * d0[s][g] - 1, 4)}
                  for g in GROUPS}
    return {"states": {s: out[s] for s in DIVISION}, "US": out["US"], "theta": {s: round(v, 3) for s, v in thetas.items()}}


def load(years: tuple[int, ...]) -> pd.DataFrame:
    """CES cumulative respondents for `years`, with group and the persuadable and mobilisable flags. mu uses validated
    turnout among respondents matched to an active registration (validated turnout is only reliable where the match
    is); mobilisable_self uses self-reported turnout from the post-election wave, as a check."""
    df = pd.read_stata(DATA / "cumulative_2006-2025.dta", columns=COLS)
    df = df[df.year.isin(years)].copy()
    for c in df.select_dtypes("category"):
        df[c] = df[c].astype(object)
    df["group"] = [group_of(*r) for r in zip(df.pid7, df.race, df.hispanic, df.educ)]
    post = df.tookpost == "Took Post-Election Survey"
    df["persuadable"] = persuadable(df.intent_sen.where(post), df.voted_sen.where(post))
    df["mobilisable"] = mobilisable(df.intent_turnout_self, df.vv_turnout_gvm == "Voted").where(
        df.vv_regstatus == "Active")
    df["mobilisable_self"] = mobilisable(df.intent_turnout_self, df.voted_turnout_self == "Yes").where(
        post & df.voted_turnout_self.notna())
    return df[df.group.notna()]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fit", action="store_true", help="fit pi and mu and write simlab/pimu.json")
    ap.add_argument("--kev", metavar="ANSWERS", help="Kev's margins by state and group ({run, states: {st: {group: "
                    "d}}}): add the nation's and write simlab/kev_groups.json")
    a = ap.parse_args()
    if a.kev:
        kev = json.loads(Path(a.kev).read_text(encoding="utf-8"))
        base = json.loads(BASE.read_text(encoding="utf-8"))
        missing = [f"{s} {g}" for s in base["states"] for g in GROUPS if g not in kev["states"].get(s, {})]
        v = _pres()
        kev["US"] = kev_national(kev["states"], base, (v.DEMOCRAT + v.REPUBLICAN).to_dict())
        kev["US_method"] = "the states' margins weighted by 2024 presidential votes x the group's share of midterm voters"
        KEV.write_text(json.dumps(kev, indent=1), encoding="utf-8")
        print(f"Kev groups: {len(kev['states'])} states; {len(missing)} state-group pairs without an answer use the "
              f"survey's d0{': ' + ', '.join(missing[:10]) if missing else ''} -> {KEV}")
        return
    if not a.fit:
        ap.error("nothing to do (use --fit or --kev)")
    mid = load((2018, 2022))
    out = fit(mid)
    check = load((2024,))
    check["weight_post"] = check.weight_post.fillna(check.weight)  # the cumulative file has no 2024 post weight
    nat = lambda d, col, w: _shares(d[d[col].notna() & d[w].notna()], col, w, ["group"]).p.round(4).to_dict()
    doc = {"fitted": f"{date.today()}, python -m simlab.groups --fit",
           "source": "CES cumulative 2006-2025, 2018 and 2022 midterms (pre- and post-election waves)",
           "variables": {
               "pi": "Senate voters (voted_sen a candidate, post wave) who were unsure before (intent_sen 'Not Sure' "
                     "or 'No One') or whose vote differs from intent_sen; weight_post",
               "mu": "respondents matched to an active registration (vv_regstatus): intent_turnout_self 'Probably', "
                     "'Undecided' or missing, or firm intenders without a validated vote (vv_turnout_gvm), or "
                     "'No' with one; weight"},
           "shrinkage": {"pseudo_count": PSEUDO, "levels": "state -> census division -> nation"},
           "checks": {"pi_2024": nat(check, "persuadable", "weight_post"), "mu_2024": nat(check, "mobilisable", "weight"),
                      "mu_self_report": nat(mid, "mobilisable_self", "weight_post")},
           **out}
    PIMU.write_text(json.dumps(doc, indent=1), encoding="utf-8")
    print(f"pi/mu: {len(out['national'])} groups, {len(out['states'])} states -> {PIMU}")
    base = fit_base()
    doc = {"fitted": f"{date.today()}, python -m simlab.groups --fit",
           "method": "stats-groundwork §5.5. n: CPS 2024 citizen adults by white/non-white x degree, times the CES "
                     "2022-25 party mix within cell (shrunk state -> division -> nation), tilted by exp(theta x party "
                     "position) to the state's 2024 two-party presidential margin; t: CPS 2022 turnout by cell "
                     "(official-corrected), spread by party with CES 2018/2022 validated-turnout odds ratios; d0: CES "
                     "2018/2022 validated voters' two-party Senate vote (House vote for US), shrunk the same way",
           "shrinkage": {"pseudo_count": PSEUDO}, **base}
    BASE.write_text(json.dumps(doc, indent=1), encoding="utf-8")
    print(f"groups base: {len(base['states'])} states + US -> {BASE}")


if __name__ == "__main__":
    main()
