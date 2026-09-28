"""Calibration of the statistics layer on past elections (docs/stats-groundwork.md §5.10). Fits the sizes the filter,
the blend and the Monte Carlo need, and writes them with their sources to simlab/stats_params.json.

Inputs (python -m simlab.statsdata download): 538's polls with results (raw_polls, 1998-2022 even years), 538's Senate
and generic-ballot poll lists (2018-2024), MIT president, Senate and House results. Margins are two-party, D minus R,
in points; a poll error is poll minus result, so + means the polls overstated the Democrat.

    python -m simlab.calib
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import minimize

from .statsdata import HIST, mit

OUT = Path(__file__).parent / "stats_params.json"
POP = {"lv": 0, "rv": 1, "v": 2, "a": 3}
SUFFIX = {"JR", "JR.", "SR", "SR.", "II", "III", "IV"}
DIVISIONS = {"New England": "CT ME MA NH RI VT", "Mid-Atlantic": "NJ NY PA", "East North Central": "IL IN MI OH WI",
             "West North Central": "IA KS MN MO NE ND SD", "South Atlantic": "DE DC FL GA MD NC SC VA WV",
             "East South Central": "AL KY MS TN", "West South Central": "AR LA OK TX",
             "Mountain": "AZ CO ID MT NV NM UT WY", "Pacific": "AK CA HI OR WA"}
DIVISION = {s: d for d, ss in DIVISIONS.items() for s in ss.split()}


def two_party(d, r):
    return 100 * (d - r) / (d + r)


def sampling_var(d, r, n):
    p = (d / (d + r)).clip(0.02, 0.98)
    return 1e4 * 4 * p * (1 - p) / (n * (d + r) / 100)


def raw_polls() -> pd.DataFrame:
    r = pd.read_csv(HIST / "538_raw_polls.csv", low_memory=False)
    r = r[(r.cycle % 2 == 0) & (r.cand1_party == "DEM") & (r.cand2_party == "REP")].copy()
    r["e"] = two_party(r.cand1_pct, r.cand2_pct) - two_party(r.cand1_actual, r.cand2_actual)
    r["m_actual"] = two_party(r.cand1_actual, r.cand2_actual)
    n = r.samplesize.fillna(r.samplesize.median()).clip(100, 20000)
    r["s2"] = sampling_var(r.cand1_pct, r.cand2_pct, n)
    return r


def decompose(x: pd.DataFrame) -> dict:
    """Method of moments: error = cycle (national) + race + poll (sampling + extra)."""
    k = x.groupby("race").e.transform("size")
    w = x[k >= 2]
    gw = w.groupby("race").e
    dev2 = (w.e - gw.transform("mean")) ** 2 * gw.transform("size") / (gw.transform("size") - 1)
    ns2 = max(dev2.mean() - w.s2.mean(), 0.0)
    races = x.groupby("race").agg(ebar=("e", "mean"), k=("e", "size"), s2=("s2", "mean"), cycle=("cycle", "first"))
    races["noise"] = (races.s2 + ns2) / races.k
    cyc = races.groupby("cycle").agg(b=("ebar", "mean"), R=("ebar", "size"))
    races = races.join(cyc, on="cycle")
    keep = races.R > 1
    u2 = max(((races.ebar - races.b)[keep] ** 2).sum() / ((races.R - 1) / races.R)[keep].sum()
             - races.noise[keep].mean(), 0.0)
    noise_c = races.groupby("cycle").noise.mean() / cyc.R + u2 / cyc.R
    b2 = max(cyc.b.var() - noise_c.mean(), 0.0) if len(cyc) > 2 else np.nan
    return {"polls": len(x), "races": len(races), "poll_extra_sd": np.sqrt(ns2), "sampling_sd": np.sqrt(x.s2.mean()),
            "race_sd": np.sqrt(u2), "cycle_sd": np.sqrt(b2), "cycle_rms": np.sqrt((cyc.b ** 2).mean()),
            "cycle_mean": cyc.b.mean(), "by_cycle": cyc.b}


def poll_errors(r: pd.DataFrame) -> dict:
    late = r[r.time_to_election <= 21]
    sen = late[late.type_simple == "Sen-G"]
    k = sen.groupby("race").size()
    close = sen.groupby("race").m_actual.first().abs()
    good = k[k >= 5].index.intersection(close[close < 15].index)
    out = {"senate_all": decompose(sen), "senate_well_polled_close": decompose(sen[sen.race.isin(good)]),
           "senate_modern_well_polled_close": decompose(sen[sen.race.isin(good) & (sen.cycle >= 2006)]),
           "senate_few_polls": decompose(sen[sen.race.isin(k[k < 5].index)])}
    early = r[(r.type_simple == "Sen-G") & (r.time_to_election > 21)]
    out["senate_well_polled_close_22_61_days"] = decompose(early[early.race.isin(good)])
    gb = late[late.type_simple == "House-G-US"].groupby("cycle").e.mean()
    out["generic_ballot"] = {"mean": gb.mean(), "rms": np.sqrt((gb ** 2).mean()), "sd": gb.std(), "by_cycle": gb}
    other = late[late.type_simple.isin(["Sen-G", "Gov-G", "House-G"])]
    nonp = other[other.partisan.isna()].groupby("race").e.mean()
    sp = other[other.partisan.isin(["DEM", "REP"])].join(nonp.rename("e_np"), on="race").dropna(subset=["e_np"])
    out["sponsor_shift"] = (sp.e - sp.e_np).groupby(sp.partisan).agg(["count", "mean", "median"])
    # regional and state shares of the race-level error (statewide races with 3+ polls, national miss removed)
    st = late[late.type_simple.isin(["Sen-G", "Gov-G", "Pres-G"]) & (late.location.str.len() == 2)]
    race = st.groupby(["cycle", "location", "type_simple"]).agg(e=("e", "mean"), k=("e", "size")).reset_index()
    race = race[race.k >= 3]
    race["e"] -= race.groupby("cycle").e.transform("mean")
    race["div"] = race.location.map(DIVISION)
    same_state = race.merge(race, on=["cycle", "location"]).query("type_simple_x < type_simple_y")
    same_div = race.merge(race, on=["cycle", "div"]).query("location_x < location_y")
    cov_s, cov_d = (same_state.e_x * same_state.e_y).mean(), (same_div.e_x * same_div.e_y).mean()
    tot = (race.e ** 2).mean()
    out["shares"] = {"race_level_sd": np.sqrt(tot), "regional_sd": np.sqrt(max(cov_d, 0)),
                     "state_sd": np.sqrt(max(cov_s - cov_d, 0)), "race_only_sd": np.sqrt(max(tot - cov_s, 0))}
    return out


def _kalman_nll(params, series):
    q, s2x = np.exp(params)
    ll = 0.0
    for t, y, s2 in series:
        x, P = y[0], s2[0] + s2x
        for i in range(1, len(y)):
            P += q * (t[i - 1] - t[i])
            S = P + s2[i] + s2x
            v = y[i] - x
            ll -= 0.5 * (np.log(2 * np.pi * S) + v * v / S)
            K = P / S
            x += K * v
            P *= 1 - K
    return -ll


def _drift_fit(df, key, window=120, min_polls=6):
    df = df[(df.t >= 0) & (df.t <= window)]
    series = []
    for _, g in df.groupby(key):
        if len(g) >= min_polls:
            g = g.sort_values("t", ascending=False)
            series.append((g.t.values.astype(float), g.y.values, g.s2.values))
    res = minimize(_kalman_nll, x0=np.log([0.1, 4.0]), args=(series,), method="Nelder-Mead",
                   options={"xatol": 1e-3, "fatol": 1e-3})
    q, s2x = np.exp(res.x)
    return {"series": len(series), "polls": int(sum(len(s[0]) for s in series)), "daily_sd": np.sqrt(q),
            "extra_poll_sd": np.sqrt(s2x)}


def _poll_frame(q, dem, rep):
    q = q.copy()
    for c in ("start_date", "end_date", "election_date"):
        q[c] = pd.to_datetime(q[c], format="%m/%d/%y")
    q["t"] = (q.election_date - (q.start_date + (q.end_date - q.start_date) / 2)).dt.days
    q["y"] = two_party(q[dem], q[rep])
    q["s2"] = sampling_var(q[dem], q[rep], q.sample_size.fillna(q.sample_size.median()).clip(100, 20000))
    return q


def drift() -> dict:
    """Random walk plus poll noise, fitted by maximum likelihood over each race's last 120 days (house effects not
    removed, so pollster-mix changes count as drift: an upper bound)."""
    d = pd.concat([pd.read_csv(HIST / f, low_memory=False)
                   for f in ("538_senate_polls_historical.csv", "538_senate_polls_2024.csv")])
    d = d[(d.stage == "general") & d.party.isin(["DEM", "REP"])]
    d = d[d.hypothetical.fillna(False).astype(str).str.lower() != "true"]
    q = d.pivot_table(index=["poll_id", "question_id", "race_id", "cycle", "population", "sample_size", "start_date",
                             "end_date", "election_date"], columns="party", values="pct", aggfunc="max").dropna().reset_index()
    q["pop"] = q.population.map(POP).fillna(4)
    sen = _poll_frame(q.sort_values(["poll_id", "pop"]).groupby("poll_id").head(1), "DEM", "REP")
    gb = pd.read_csv(HIST / "538_generic_ballot_polls_historical.csv", low_memory=False)
    gb["pop"] = gb.population.map(POP).fillna(4)
    gb = gb.sort_values(["poll_id", "pop"]).groupby("poll_id").head(1)
    gb["election_date"] = gb.cycle.map({2018: "11/6/18", 2020: "11/3/20", 2022: "11/8/22"})
    gb = _poll_frame(gb.dropna(subset=["election_date"]), "dem", "rep")
    return {"senate_2018_2024": _drift_fit(sen, "race_id"), "senate_midterms": _drift_fit(sen[sen.cycle.isin([2018, 2022])], "race_id"),
            "senate_2024": _drift_fit(sen[sen.cycle == 2024], "race_id"), "generic_ballot": _drift_fit(gb, "cycle")}


def _surname(name: str) -> str:
    name = name.split(",")[0] if "," in name else name
    toks = [t for t in re.sub(r"[\"'()]", " ", name).upper().split() if t not in SUFFIX]
    return toks[-1] if toks else ""


def senate_table() -> pd.DataFrame:
    """One row per Senate race with a Democrat and a Republican as the top two (decisive round; Louisiana's jungle
    races left out): margin, lean from the two previous presidential elections, national House vote, incumbency."""
    p = mit("president")
    p = p[p.party_simplified.isin(["DEMOCRAT", "REPUBLICAN"]) & ~p.writein.fillna(False).astype(bool)]
    pv = p.pivot_table(index=["year", "state_po"], columns="party_simplified", values="candidatevotes", aggfunc="sum")
    nat = pv.groupby("year").sum()
    rel = two_party(pv.DEMOCRAT, pv.REPUBLICAN) - two_party(nat.DEMOCRAT, nat.REPUBLICAN).reindex(
        pv.index.get_level_values(0)).values
    h = mit("house")
    h = h[(h.stage == "GEN") & h.party.isin(["DEMOCRAT", "REPUBLICAN"])]
    hv = h.pivot_table(index="year", columns="party", values="candidatevotes", aggfunc="sum")
    E = two_party(hv.DEMOCRAT, hv.REPUBLICAN)
    rp = pd.read_csv(HIST / "538_raw_polls.csv", low_memory=False)
    g = rp[rp.type_simple == "House-G-US"].drop_duplicates("cycle").set_index("cycle")
    E.update(two_party(g.cand1_actual, g.cand2_actual))
    s = mit("senate")
    s["stage"] = s.stage.str.lower()
    s = s[s.stage.isin(["gen", "runoff", "gen runoff"]) & ~s.writein.fillna(False).astype(bool) & (s.state_po != "LA")]
    s["rnd"] = (s.stage != "gen").astype(int)
    s = s[s.rnd == s.groupby(["year", "state_po", "special"]).rnd.transform("max")]
    rows = []
    for (y, st, sp), grp in s.groupby(["year", "state_po", "special"]):
        top2 = grp.nlargest(2, "candidatevotes")
        if set(top2.party_simplified) != {"DEMOCRAT", "REPUBLICAN"}:
            continue
        d, r = (top2[top2.party_simplified == x].iloc[0] for x in ("DEMOCRAT", "REPUBLICAN"))
        rows.append({"year": y, "st": st, "special": bool(sp), "D": d.candidate, "R": r.candidate,
                     "m": two_party(d.candidatevotes, r.candidatevotes)})
    t = pd.DataFrame(rows)
    t["wlast"] = np.where(t.m > 0, t.D.map(_surname), t.R.map(_surname))
    t["wsign"] = np.sign(t.m)

    def lean(y, st, i):
        prev = [py for py in range(y - 1, 1975, -1) if py % 4 == 0]
        return rel.get((prev[i], st), np.nan) if len(prev) > i else np.nan

    def incumbent(row):
        for sign, name in ((1, row.D), (-1, row.R)):
            w = t[(t.st == row.st) & (t.year < row.year) & (t.year >= row.year - 6) & (t.wsign == sign)
                  & (t.wlast == _surname(name))]
            if len(w):
                return sign
        return 0

    t["r1"] = [lean(y, st, 0) for y, st in zip(t.year, t.st)]
    t["r2"] = [lean(y, st, 1) for y, st in zip(t.year, t.st)]
    t["E"] = t.year.map(E)
    t["inc"] = [incumbent(row) for row in t.itertuples()]
    return t.dropna(subset=["r1", "r2", "E"]).reset_index(drop=True)


def _with_prior(D, allT, b):
    """Each incumbent's previous-win residual beyond lean, national vote and incumbency (the candidate effect)."""
    nr = allT.m - np.column_stack([allT.r1, allT.r2, allT.inc, allT.E, np.ones(len(allT))]) @ b
    allT = allT.assign(nr=nr)
    pr = []
    for row in D.itertuples():
        c = allT[(allT.st == row.st) & (allT.year < row.year) & (allT.year >= row.year - 6) & (np.sign(allT.m) == row.inc)]
        pr.append(c.sort_values("year").nr.iloc[-1] if row.inc and len(c) else 0.0)
    return D.assign(pr=pr)


FUND_COLS = ["r1", "r2", "inc", "E", "pr"]


def fundamentals(T: pd.DataFrame, lo=2012, hi=2024) -> dict:
    D = T[(T.year >= lo) & (T.year <= hi)].copy()
    X0 = np.column_stack([D.r1, D.r2, D.inc, D.E, np.ones(len(D))])
    b, *_ = np.linalg.lstsq(X0, D.m, rcond=None)
    for _ in range(3):
        D = _with_prior(D, T, b)
        X = np.column_stack([D[FUND_COLS].values, np.ones(len(D))])
        full, *_ = np.linalg.lstsq(X, D.m, rcond=None)
        b = full[[0, 1, 2, 3, 5]]
    oos = []
    for yr in sorted(D.year.unique()):
        tr, te = D[D.year != yr], D[D.year == yr]
        bt, *_ = np.linalg.lstsq(np.column_stack([tr[FUND_COLS].values, np.ones(len(tr))]), tr.m, rcond=None)
        oos.append(pd.DataFrame({"year": yr, "st": te.st, "m": te.m,
                                 "fund": np.column_stack([te[FUND_COLS].values, np.ones(len(te))]) @ bt}))
    oos = pd.concat(oos)
    err = oos.m - oos.fund
    close = oos.fund.abs() < 15
    return {"races": len(D), "coef": dict(zip(FUND_COLS + ["const"], full)), "oos": oos,
            "oos_rmse": np.sqrt((err ** 2).mean()), "oos_rmse_close": np.sqrt((err[close] ** 2).mean()),
            "oos_rmse_by_year": err.groupby(oos.year).apply(lambda e: np.sqrt((e ** 2).mean()))}


def blend_weight(oos: pd.DataFrame, r: pd.DataFrame) -> dict:
    """Election-day weight on the poll average that minimises error, national misses removed, for Senate races with 5+
    polls in the last 21 days whose poll average is within 15."""
    s = r[(r.type_simple == "Sen-G") & (r.time_to_election <= 21)]
    avg = s.assign(mp=s.e + s.m_actual).groupby(["cycle", "location"]).agg(poll=("mp", "mean"), k=("mp", "size"))
    M = oos.merge(avg.reset_index(), left_on=["year", "st"], right_on=["cycle", "location"])
    M = M[(M.k >= 5) & (M.poll.abs() < 15)]
    ep = (M.poll - M.m) - (M.poll - M.m).groupby(M.year).transform("mean")
    ef = (M.fund - M.m) - (M.fund - M.m).groupby(M.year).transform("mean")
    w = ((ef - ep) * ef).sum() / ((ef - ep) ** 2).sum()
    blend = w * M.poll + (1 - w) * M.fund
    return {"races": len(M), "weight": w, "corr": np.corrcoef(ep, ef)[0, 1], "rmse_polls": np.sqrt(((M.poll - M.m) ** 2).mean()),
            "rmse_fund": np.sqrt(((M.fund - M.m) ** 2).mean()), "rmse_blend": np.sqrt(((blend - M.m) ** 2).mean())}


HE_FILES = ["538_senate_polls_historical.csv", "538_senate_polls_2024.csv", "538_house_polls_historical.csv",
            "538_house_polls_2024.csv", "538_governor_polls_historical.csv", "538_governor_polls_2024.csv"]
HE_OUT = Path(__file__).parent / "house_effect_priors.json"
ALIASES = {"Public Policy Polling": "PPP", "Saint Anselm": "St. Anselm", "Saint Anselm College": "St. Anselm",
           "Siena College/The New York Times Upshot": "Siena/NYT", "The New York Times/Siena College": "Siena/NYT",
           "Rasmussen Reports": "Rasmussen", "Marist College": "Marist", "Monmouth University": "Monmouth"}


def he_polls(window: int = 150) -> pd.DataFrame:
    """General-election polls 2018-2024 (Senate, House, governor, generic ballot), one question per poll and race
    (likely voters first), within `window` days of the election."""
    d = pd.concat([pd.read_csv(HIST / f, low_memory=False) for f in HE_FILES])
    d = d[(d.stage == "general") & d.party.isin(["DEM", "REP"])]
    d = d[d.hypothetical.fillna(False).astype(str).str.lower() != "true"].assign(partisan=lambda x: x.partisan.fillna(""))
    idx = ["poll_id", "question_id", "race_id", "cycle", "office_type", "pollster", "population", "sample_size",
           "start_date", "end_date", "election_date", "partisan"]
    q = d.pivot_table(index=idx, columns="party", values="pct", aggfunc="max").dropna().reset_index()
    q["pop"] = q.population.map(POP).fillna(4)
    q = q.sort_values(["poll_id", "race_id", "pop"]).groupby(["poll_id", "race_id"]).head(1)
    gb = pd.read_csv(HIST / "538_generic_ballot_polls_historical.csv", low_memory=False)
    gb["pop"] = gb.population.map(POP).fillna(4)
    gb = gb.sort_values(["poll_id", "pop"]).groupby("poll_id").head(1)
    gb = gb.assign(race_id="GB" + gb.cycle.astype(str), office_type="generic", DEM=gb.dem, REP=gb.rep,
                   partisan=gb.partisan.fillna(""), election_date=gb.cycle.map({2018: "11/6/18", 2020: "11/3/20", 2022: "11/8/22"}))
    q = pd.concat([q, gb[q.columns.intersection(gb.columns)]], ignore_index=True).dropna(subset=["election_date"])
    for c in ("start_date", "end_date", "election_date"):
        q[c] = pd.to_datetime(q[c], format="%m/%d/%y")
    q["t"] = (q.election_date - (q.start_date + (q.end_date - q.start_date) / 2)).dt.days
    q = q[(q.t >= 0) & (q.t <= window)].copy()
    q["y"] = two_party(q.DEM, q.REP)
    q["s2"] = sampling_var(q.DEM, q.REP, q.sample_size.fillna(q.sample_size.median()).clip(100, 20000))
    q["race"] = q.race_id.astype(str) + "_" + q.cycle.astype(str)
    return q.reset_index(drop=True)


def house_effects(q: pd.DataFrame, tau: float = 3.0, ns2: float = 4.0, bw: float = 7.0, rounds: int = 6,
                  prior: pd.Series | None = None):
    """Each poll against a consensus of the other pollsters' polls in the same race (Gaussian time weights, SD `bw`
    days); a pollster's effect is its shrunken mean residual (prior N(prior mean, tau^2), mean 0 unless `prior` gives
    one), centred on the average pollster; sponsored polls get a shift pooled by sponsor party on top. Alternates
    `rounds` times."""
    m = (prior if prior is not None else pd.Series(dtype=float)).reindex(q.pollster.unique()).fillna(0.0)
    h = m.copy()
    sp = {"DEM": 0.0, "REP": 0.0}
    for _ in range(rounds):
        adj = q.y - q.pollster.map(h) - q.partisan.map(sp).fillna(0.0)
        cons, cvar = np.full(len(q), np.nan), np.full(len(q), np.nan)
        for _, g in q.groupby("race"):
            ix, t, a = g.index.values, g.t.values, adj[g.index].values
            w0, pol = 1.0 / (g.s2.values + ns2), g.pollster.values
            for j, i in enumerate(ix):
                k = np.exp(-0.5 * ((t - t[j]) / bw) ** 2) * w0 * (pol != pol[j])
                if (k > 1e-3 * w0.max()).sum() >= 2:
                    cons[i], cvar[i] = (k * a).sum() / k.sum(), 1.0 / k.sum()
        ok = ~np.isnan(cons)
        res, w = (q.y - cons)[ok], 1.0 / (q.s2[ok] + ns2 + cvar[ok])
        num = ((res - q.partisan[ok].map(sp).fillna(0.0)) * w).groupby(q.pollster[ok]).sum()
        den = w.groupby(q.pollster[ok]).sum()
        h = ((num + m.reindex(num.index) / tau ** 2) / (den + 1 / tau ** 2)).reindex(h.index).fillna(m)
        h -= np.average(h[den.index], weights=den)
        r2 = res - q.pollster[ok].map(h)
        sp = {p: float(np.average(r2[q.partisan[ok] == p], weights=w[q.partisan[ok] == p])) for p in ("DEM", "REP")}
    tab = pd.DataFrame({"mean": h, "se": 1 / np.sqrt(den + 1 / tau ** 2), "n": q[ok].groupby("pollster").size()})
    return tab.dropna(subset=["n"]).sort_values("n", ascending=False), sp


ELECTION_DAY = {1998: "1998-11-03", 2000: "2000-11-07", 2002: "2002-11-05", 2004: "2004-11-02", 2006: "2006-11-07",
                2008: "2008-11-04", 2010: "2010-11-02", 2012: "2012-11-06", 2014: "2014-11-04", 2016: "2016-11-08",
                2018: "2018-11-06", 2020: "2020-11-03", 2022: "2022-11-08"}
PRESIDENT = {1998: ("clinton", 1), 2000: ("clinton", 1), 2002: ("gwbush", -1), 2004: ("gwbush", -1),
             2006: ("gwbush", -1), 2008: ("gwbush", -1), 2010: ("obama", 1), 2012: ("obama", 1), 2014: ("obama", 1),
             2016: ("obama", 1), 2018: ("trump1", -1), 2020: ("trump1", -1), 2022: ("biden", 1)}


def approval_test(r: pd.DataFrame) -> dict:
    """D4: does net approval add to the final generic-ballot average in predicting the national House vote? Each cycle
    1998-2022 is predicted from the others. Net approval is Gallup's last reading before election day (American
    Presidency Project), signed toward the president's party; 2022 uses 538's Biden average, because the Gallup sheet
    stops in January 2022."""
    late = r[(r.type_simple == "House-G-US") & (r.time_to_election <= 21)]
    rows = []
    for cyc, g in late.groupby("cycle"):
        name, sign = PRESIDENT[cyc]
        day = pd.Timestamp(ELECTION_DAY[cyc])
        a = pd.read_csv(HIST / f"app_gallup_approval_{name}.csv")
        a["end"] = pd.to_datetime(a["End Date"], format="mixed")
        a = a[a.end < day]
        if len(a):
            net = float((a.Approving - a.Disapproving).iloc[a.end.argmax()])
        else:
            b = pd.read_csv(HIST / "538_biden_approval_topline.csv")
            b = b[(b.subgroup == "All polls") & (pd.to_datetime(b.end_date) < day)]
            b = b.loc[pd.to_datetime(b.end_date).idxmax()]
            net = float(b.approve_estimate - b.disapprove_estimate)
        rows.append({"cycle": cyc, "gb": g.e.mean() + g.m_actual.iloc[0], "E": g.m_actual.iloc[0],
                     "appr": sign * net, "midterm": cyc % 4 == 2})
    d = pd.DataFrame(rows)

    def loyo(cols, subset):
        errs = []
        for c in d.cycle[subset]:
            tr = d[d.cycle != c]
            X = np.column_stack([tr[k] for k in cols] + [np.ones(len(tr))])
            b, *_ = np.linalg.lstsq(X, tr.E, rcond=None)
            te = d[d.cycle == c]
            errs.append(float(te.E.iloc[0] - np.r_[[te[k].iloc[0] for k in cols], 1.0] @ b))
        return np.sqrt(np.mean(np.square(errs)))

    out = {"table": d}
    for lab, subset in (("all", d.cycle == d.cycle), ("midterms", d.midterm)):
        out[lab] = {"gb_only": loyo(["gb"], subset), "gb_plus_approval": loyo(["gb", "appr"], subset),
                    "approval_only": loyo(["appr"], subset)}
    out["passes"] = out["midterms"]["gb_plus_approval"] < out["midterms"]["gb_only"] and \
        out["all"]["gb_plus_approval"] < out["all"]["gb_only"]
    return out


def main() -> None:
    r = raw_polls()
    pe = poll_errors(r)
    print("Poll errors, two-party margin, polls in the last 21 days (538 raw polls, 1998-2022):")
    for k in ("senate_all", "senate_well_polled_close", "senate_modern_well_polled_close", "senate_few_polls",
              "senate_well_polled_close_22_61_days"):
        v = pe[k]
        print(f"  {k:38} polls {v['polls']:5} races {v['races']:4} | extra poll sd {v['poll_extra_sd']:.2f} (sampling "
              f"{v['sampling_sd']:.2f}) | race sd {v['race_sd']:.2f} | national sd {v['cycle_sd']:.2f} (rms {v['cycle_rms']:.2f})")
    g = pe["generic_ballot"]
    print(f"  generic ballot: mean error {g['mean']:+.2f}, rms {g['rms']:.2f}, sd {g['sd']:.2f}; by cycle "
          + ", ".join(f"{c} {v:+.1f}" for c, v in g["by_cycle"].items()))
    print("  sponsored polls vs nonpartisan in the same race:",
          {k: round(v, 2) for k, v in pe["sponsor_shift"]["mean"].items()}, "(mean margin shift)")
    print("  shares of race-level error:", {k: round(v, 2) for k, v in pe["shares"].items()})
    dr = drift()
    print("Drift (random walk + poll noise, last 120 days, 538 poll lists):")
    for k, v in dr.items():
        print(f"  {k:18} series {v['series']:3} polls {v['polls']:5} | daily sd {v['daily_sd']:.3f} (35 days "
              f"{v['daily_sd'] * np.sqrt(35):.2f}) | extra poll sd {v['extra_poll_sd']:.2f}")
    T = senate_table()
    fu = fundamentals(T)
    c = fu["coef"]
    print(f"Fundamentals, Senate 2012-2024 ({fu['races']} races, D v R, Louisiana out): lean latest {c['r1']:.2f}, previous "
          f"{c['r2']:.2f}, incumbency {c['inc']:+.2f}, national House vote {c['E']:.2f}, prior over-performance {c['pr']:.2f}, "
          f"const {c['const']:+.2f} | leave-one-year-out rmse {fu['oos_rmse']:.2f}, predicted within 15 {fu['oos_rmse_close']:.2f}")
    print("  by year:", {int(k): round(v, 1) for k, v in fu["oos_rmse_by_year"].items()})
    fu06 = fundamentals(T, 2006, 2022)
    bw = blend_weight(fu06["oos"], r)
    print(f"Blend check, 2006-2022, well-polled close races ({bw['races']}): best poll weight {bw['weight']:.2f}, error "
          f"correlation {bw['corr']:.2f}, rmse polls {bw['rmse_polls']:.2f} / fundamentals {bw['rmse_fund']:.2f} / blend {bw['rmse_blend']:.2f}")
    ap = approval_test(r)
    print("Approval test (national House vote from the final generic ballot, each cycle predicted from the others):")
    print(ap["table"].round(1).to_string(index=False))
    for k in ("all", "midterms"):
        print(f"  {k:9} rmse: generic ballot only {ap[k]['gb_only']:.2f} | plus approval {ap[k]['gb_plus_approval']:.2f} | "
              f"approval only {ap[k]['approval_only']:.2f}")
    print(f"  approval passes: {ap['passes']}")
    hq = he_polls()
    he, he_sp = house_effects(hq)
    print(f"House effects 2018-2024 ({len(hq)} polls, {hq.race.nunique()} races, {len(he)} pollsters; + leans D), "
          f"sponsor shift on top of pollster effects {({k: round(v, 2) for k, v in he_sp.items()})}:")
    big = he[he.n >= 20]
    print("  most R-leaning:", ", ".join(f"{p} {v:+.1f}" for p, v in big["mean"].nsmallest(8).items()))
    print("  most D-leaning:", ", ".join(f"{p} {v:+.1f}" for p, v in big["mean"].nlargest(8).items()))
    HE_OUT.write_text(json.dumps({
        "fitted": "2026-09-28, python -m simlab.calib (538 poll lists 2018-2024, general elections, last 150 days)",
        "units": "two-party margin, D minus R, relative to the average pollster; prior N(0, 3^2) for pollsters not listed",
        "sponsor_shift": {k: round(v, 2) for k, v in he_sp.items()}, "aliases": ALIASES,
        "pollsters": {p: {"mean": round(r["mean"], 2), "se": round(r.se, 2), "n": int(r.n)} for p, r in he.iterrows()}},
        indent=1))
    print(f"-> {HE_OUT}")
    s, sh = pe["senate_well_polled_close"], pe["shares"]
    params = {
        "fitted": "2026-09-28, python -m simlab.calib",
        "poll_extra_sd": {"value": 2.0, "fit": [round(pe["senate_modern_well_polled_close"]["poll_extra_sd"], 2),
                                                 round(pe["senate_all"]["poll_extra_sd"], 2)], "note": "extra poll noise beyond sampling; range from well-polled close races (2006-22) to all Senate races"},
        "race_poll_bias_sd": {"value": 3.5, "fit": round(s["race_sd"], 2), "few_polls": round(pe["senate_few_polls"]["race_sd"], 2),
                              "note": "error shared by a race's polls in the last 3 weeks, national part removed"},
        "national_poll_bias_sd": {"value": 3.0, "fit": [round(s["cycle_sd"], 2), round(pe["senate_all"]["cycle_rms"], 2)],
                                  "note": "Senate polls' shared miss per cycle"},
        "generic_ballot_bias": {"mean": round(g["mean"], 2), "sd": round(g["sd"], 2), "note": "final generic-ballot average minus national House vote, 1998-2022; + = overstated D"},
        "sponsor_shift": {"raw": {k: round(v, 2) for k, v in pe["sponsor_shift"]["mean"].items()},
                          "with_pollster_effects": {k: round(v, 2) for k, v in he_sp.items()},
                          "note": "raw = against nonpartisan polls of the same race (1998-2022); the second is on top of pollster house effects (2018-24), the one to use with house effects"},
        "drift_daily_sd": {"race": 0.5, "national": 0.3, "fit": {k: round(v["daily_sd"], 3) for k, v in dr.items()}},
        "fundamentals": {"coef": {k: round(v, 3) for k, v in c.items()}, "sd": 7.5,
                         "oos_rmse": round(fu["oos_rmse"], 2), "oos_rmse_close": round(fu["oos_rmse_close"], 2),
                         "note": "margin = r1*lean_latest + r2*lean_previous + inc*incumbent(+1 D/-1 R) + E*national House vote + pr*prior over-performance + const"},
        "blend": {"best_poll_weight": round(bw["weight"], 2), "races": bw["races"]},
        "approval_test": {"passes": bool(ap["passes"]),
                          **{k: {m: round(v, 2) for m, v in ap[k].items()} for k in ("all", "midterms")}},
        "mc": {"regional_sd": round(sh["regional_sd"], 2), "state_sd": round(sh["state_sd"], 2),
               "race_only_sd": round(sh["race_only_sd"], 2), "regions": "census divisions"},
    }
    OUT.write_text(json.dumps(params, indent=1))
    print(f"-> {OUT}")


if __name__ == "__main__":
    main()
