"""Backtest of the statistics-only chain (docs/stats-groundwork.md §5.1-5.4) on the 2018-2024 Senate races, scored
against the results and, for 2018-2022, against 538's own forecasts (lite, classic, deluxe) made on the same dates
(538's scoring file has no 2024).

No peeking: a poll counts only once 538 had logged it (created_at) by the forecast date; pollster house effects use
the tested cycle's polls known by then, with priors from earlier cycles only; the fundamentals, the generic-ballot
correction and the error sizes are refitted without the tested cycle. Left out: Georgia 2020 (both seats went to
January runoffs), specials with the same two candidates as that year's regular race (California 2022 and 2024), and
races without a Democrat and a Republican as the top two (Louisiana, independents, same-party runoffs).

    python -m simlab.backtest
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import t as student_t

from . import calib
from .statsdata import HIST, mit

CYCLES = (2018, 2020, 2022, 2024)
DAYS = (35, 14, 1)
ELECTION = {2018: "2018-11-06", 2020: "2020-11-03", 2022: "2022-11-08", 2024: "2024-11-05"}
REGULAR_CLASS = {2018: "Class I", 2020: "Class II", 2022: "Class III", 2024: "Class I"}
NS2, NU = 2.0 ** 2, 8
OUT = calib.Path(__file__).parents[1] / "runs" / "backtest_senate_2018_2024.csv"


def _states() -> dict:
    s = mit("senate")
    return dict(zip(s.state.str.title(), s.state_po))


def senate_polls() -> pd.DataFrame:
    """One row per poll and race (versions within a population averaged, likely voters first), nominee pairs only."""
    d = pd.concat([pd.read_csv(HIST / f, low_memory=False)
                   for f in ("538_senate_polls_historical.csv", "538_senate_polls_2024.csv")])
    d = d[(d.stage == "general") & d.party.isin(["DEM", "REP"])].copy()
    d["st"] = d.state.map(_states())
    d["special"] = d.seat_name != d.cycle.map(REGULAR_CLASS)
    d = d.assign(partisan=d.partisan.fillna(""), population=d.population.fillna("v"), sample_size=d.sample_size.fillna(-1),
                 created_at=d.created_at.fillna(""))
    idx = ["poll_id", "question_id", "cycle", "st", "special", "pollster", "population", "sample_size", "start_date",
           "end_date", "created_at", "partisan"]
    top = d.sort_values("pct", ascending=False).groupby(idx + ["party"]).head(1)
    q = top.pivot_table(index=idx, columns="party", values=["pct", "candidate_name"], aggfunc="first").dropna()
    q.columns = [f"{a}_{b}" for a, b in q.columns]
    q = q.reset_index()
    q["sample_size"] = q.sample_size.where(q.sample_size > 0)
    q["dlast"], q["rlast"] = q.candidate_name_DEM.map(calib._surname), q.candidate_name_REP.map(calib._surname)
    q["y"] = calib.two_party(q.pct_DEM.astype(float), q.pct_REP.astype(float))
    q["s2"] = calib.sampling_var(q.pct_DEM.astype(float), q.pct_REP.astype(float),
                                 q.sample_size.fillna(q.sample_size.median()).clip(100, 20000))
    return _dates(q)


def nominee_polls(q: pd.DataFrame, T: pd.DataFrame) -> pd.DataFrame:
    """Keep only questions about the actual Democratic and Republican nominees of each race."""
    noms = T.assign(dlast=T.D.map(calib._surname), rlast=T.R.map(calib._surname), cycle=T.year)
    noms["race"] = noms.st + np.where(noms.special, "-S", "") + "_" + noms.cycle.astype(str)
    return q.merge(noms[["race", "dlast", "rlast"]], on=["race", "dlast", "rlast"])


def gb_polls() -> pd.DataFrame:
    g = pd.concat([pd.read_csv(HIST / f, low_memory=False)
                   for f in ("538_generic_ballot_polls_historical.csv", "538_generic_ballot_polls_2024.csv")])
    g = g.assign(partisan=g.partisan.fillna(""), st="US", special=False, dlast="", rlast="",
                 y=calib.two_party(g.dem, g.rep),
                 s2=calib.sampling_var(g.dem, g.rep, g.sample_size.fillna(g.sample_size.median()).clip(100, 20000)))
    return _dates(g)


def _dates(q: pd.DataFrame) -> pd.DataFrame:
    for c in ("start_date", "end_date"):
        q[c] = pd.to_datetime(q[c], format="%m/%d/%y")
    q["created"] = pd.to_datetime(q.created_at, format="%m/%d/%y %H:%M", errors="coerce").fillna(
        q.end_date + pd.Timedelta(days=2))
    q["mid"] = q.start_date + (q.end_date - q.start_date) / 2
    q["race"] = q.st + np.where(q.special, "-S", "") + "_" + q.cycle.astype(str)
    q["pop"] = q.population.map(calib.POP).fillna(4)
    return q


KEYS = ["poll_id", "race", "dlast", "rlast"]


def one_per_poll(q: pd.DataFrame) -> pd.DataFrame:
    """Best population per poll and matchup, versions within it averaged (D7)."""
    q = q[q["pop"] == q.groupby(KEYS)["pop"].transform("min")]
    agg = {c: "first" for c in q.columns if c not in KEYS + ["y", "s2", "question_id"]}
    return q.groupby(KEYS, as_index=False).agg({**agg, "y": "mean", "s2": "mean"})


def flooding(p: pd.DataFrame) -> np.ndarray:
    """How many polls the same pollster has in the same race within 7 days either side (each counts 1/k)."""
    k = np.ones(len(p))
    for _, g in p.groupby(["race", "pollster"]):
        t = g.t.values
        k[p.index.get_indexer(g.index)] = (np.abs(t[:, None] - t[None, :]) <= 7).sum(axis=1)
    return k


def lv_gap(q: pd.DataFrame) -> float:
    """Median likely-minus-registered margin over polls released both ways, capped at +-2 (Field Guide)."""
    p = q[q.population.isin(["lv", "rv"])].groupby(["poll_id", "race", "population"]).y.mean().unstack()
    diff = (p.lv - p.rv).dropna() if {"lv", "rv"} <= set(p.columns) else pd.Series(dtype=float)
    return float(np.clip(diff.median(), -2, 2)) if len(diff) >= 5 else 0.0


def kalman_grid(t: np.ndarray, y: np.ndarray, v: np.ndarray, q: float, end: float, smooth: bool):
    """Local level on a daily grid from the first observation to `end` (days); returns grid, means, variances
    (smoothed if asked), with a diffuse start."""
    grid = np.arange(np.floor(t.min()), np.floor(end) + 1)
    obs = pd.DataFrame({"d": np.floor(t), "y": y, "w": 1 / v}).groupby("d").apply(
        lambda g: pd.Series({"y": np.average(g.y, weights=g.w), "v": 1 / g.w.sum()}), include_groups=False)
    xf, pf, xp, pp = (np.zeros(len(grid)) for _ in range(4))
    x, p = 0.0, 1e6
    for i, day in enumerate(grid):
        if i:
            p += q
        xp[i], pp[i] = x, p
        if day in obs.index:
            k = p / (p + obs.v[day])
            x, p = x + k * (obs.y[day] - x), (1 - k) * p
        xf[i], pf[i] = x, p
    if not smooth:
        return grid, xf, pf
    xs, ps = xf.copy(), pf.copy()
    for i in range(len(grid) - 2, -1, -1):
        c = pf[i] / pp[i + 1]
        xs[i] = xf[i] + c * (xs[i + 1] - xp[i + 1])
        ps[i] = pf[i] + c * c * (ps[i + 1] - pp[i + 1])
    return grid, xs, ps


def params_without(cycle: int, raw: pd.DataFrame, S1: pd.DataFrame, G1: pd.DataFrame) -> dict:
    """Error sizes and generic-ballot bias refitted without the tested cycle (S1, G1: one row per poll)."""
    pe = calib.poll_errors(raw[raw.cycle != cycle])
    days = lambda q: (pd.to_datetime(q.cycle.map(ELECTION)) - q.mid).dt.days
    s = S1[S1.cycle != cycle].assign(t=days)
    g = G1[G1.cycle != cycle].assign(t=days)
    return {"sbN": pe["senate_well_polled_close"]["cycle_sd"], "sbS": pe["senate_well_polled_close"]["race_sd"],
            "sbS_few": pe["senate_few_polls"]["race_sd"], "gb_bias": pe["generic_ballot"]["by_cycle"].mean(),
            "qR": calib._drift_fit(s, "race")["daily_sd"] ** 2,
            "qN": calib._drift_fit(g, "race", window=365)["daily_sd"] ** 2}


def fundamentals_without(cycle: int, T: pd.DataFrame):
    """The §5.10 fundamentals model fitted on 2012-2024 without the tested cycle; returns a predictor taking E."""
    D = T[(T.year >= 2012) & (T.year <= 2024) & (T.year != cycle)].copy()
    b, *_ = np.linalg.lstsq(np.column_stack([D.r1, D.r2, D.inc, D.E, np.ones(len(D))]), D.m, rcond=None)
    for _ in range(3):
        D = calib._with_prior(D, T, b)
        X = np.column_stack([D[calib.FUND_COLS].values, np.ones(len(D))])
        full, *_ = np.linalg.lstsq(X, D.m, rcond=None)
        b = full[[0, 1, 2, 3, 5]]
    Y = pd.get_dummies(D.year.astype(str), dtype=float).values
    Xy = np.column_stack([D.r1, D.r2, D.inc, D.pr, Y])
    by, *_ = np.linalg.lstsq(Xy, D.m, rcond=None)
    sd = np.sqrt(((D.m - Xy @ by) ** 2).sum() / (len(D) - Xy.shape[1]))
    test = calib._with_prior(T[T.year == cycle].copy(), T, b)

    def predict(E):
        return test.assign(fund=np.column_stack([test.r1, test.r2, test.inc, np.full(len(test), E), test.pr,
                                                 np.ones(len(test))]) @ full)
    return predict, sd, full[3]


def run_cycle(cycle, sen, gb, S1, G1, raw, T, prior):
    P = params_without(cycle, raw, S1, G1)
    predict, sdF, eco = fundamentals_without(cycle, T)
    eday = pd.Timestamp(ELECTION[cycle])
    races = T[T.year == cycle]
    regular = set(zip(races.st[~races.special], races.D[~races.special], races.R[~races.special]))
    same_pair = races.special & np.array([(s, d, r) in regular for s, d, r in zip(races.st, races.D, races.R)])
    races = races[~((cycle == 2020) & (races.st == "GA")) & ~same_pair]
    out = []
    for d in DAYS:
        F = eday - pd.Timedelta(days=d) + pd.Timedelta(hours=23, minutes=59)
        known = lambda q: q[(q.cycle == cycle) & (q.created <= F) & (q.mid <= F)]
        gap = lv_gap(pd.concat([known(sen), known(gb)]))
        polls = pd.concat([known(S1), known(G1)], ignore_index=True)
        polls["t"] = (polls.mid - eday).dt.days.astype(float)
        he, sp = calib.house_effects(polls, prior=prior)
        polls["adj"] = (polls.y + np.where(polls.population.isin(["rv", "a", "v"]), gap, 0.0)
                        - polls.pollster.map(he["mean"]).fillna(0.0) - polls.partisan.map(sp).fillna(0.0))
        polls["v"] = ((polls.s2 + NS2) * np.where(polls.partisan.isin(["DEM", "REP"]), 2.0, 1.0)) * flooding(polls)
        gp = polls[polls.st == "US"]
        grid, nx, npv = kalman_grid(gp.t.values, gp.adj.values, gp.v.values, P["qN"], -d, smooth=True)
        n_now, pn_now = nx[-1], npv[-1]
        E_hat = n_now - P["gb_bias"]
        fund = predict(E_hat)
        var_N = pn_now + P["qN"] * d + P["sbN"] ** 2
        for row in races.itertuples():
            f = fund[(fund.st == row.st) & (fund.year == row.year) & (fund.m == row.m)].fund.iloc[0]
            F_rel = f - n_now
            rp = polls[polls.race == row.st + ("-S" if row.special else "") + f"_{cycle}"]
            if len(rp):
                nt = np.interp(rp.t.values, grid, nx)
                nv = np.interp(rp.t.values, grid, npv)
                _, rx, rv = kalman_grid(rp.t.values, rp.adj.values - nt, rp.v.values + nv, P["qR"], -d, smooth=False)
                recent = (rp.t >= -d - 30).sum()
                sbS = P["sbS"] if recent >= 5 else P["sbS_few"]
                V = rv[-1] + P["qR"] * d + sbS ** 2
                w = sdF ** 2 / (sdF ** 2 + V)
                r_hat, var_R = w * rx[-1] + (1 - w) * F_rel, 1 / (1 / V + 1 / sdF ** 2)
                poll_mu, poll_var = n_now + rx[-1], var_N + V
            else:
                w, r_hat, var_R = 0.0, F_rel, sdF ** 2
                poll_mu, poll_var = np.nan, np.nan
            mu, var = n_now + r_hat, var_N + var_R
            pwin = lambda m, v: float(student_t.cdf(m / np.sqrt(v * (NU - 2) / NU), NU))
            out.append({"cycle": cycle, "days": d, "st": row.st, "special": bool(row.special), "result": row.m,
                        "polls": len(rp), "w_polls": w, "mu": mu, "sd": np.sqrt(var), "p": pwin(mu, var),
                        "mu_polls": poll_mu, "p_polls": pwin(poll_mu, poll_var) if len(rp) else pwin(f, eco ** 2 * var_N + sdF ** 2),
                        "mu_fund": f, "p_fund": pwin(f, eco ** 2 * var_N + sdF ** 2)})
    return pd.DataFrame(out)


def add_538(bt: pd.DataFrame) -> pd.DataFrame:
    c = pd.read_csv(HIST / "538_cow_us_senate_elections.csv", low_memory=False)
    c = c[(c.party == "D") & c.year.isin(CYCLES)]
    c["special"] = c.special.astype(str).str.lower() == "true"
    c["days"] = (pd.to_datetime(c.election_date) - pd.to_datetime(c.forecast_date)).dt.days
    c = c[c.days.isin(DAYS)]
    wide = c.pivot_table(index=["year", "state", "special", "days"], columns="forecast_type",
                         values=["probwin", "projected_voteshare"], aggfunc="first")
    wide.columns = [f"{'p' if a == 'probwin' else 'share'}_538{b}" for a, b in wide.columns]
    wide = wide.reset_index().rename(columns={"year": "cycle", "state": "st"})
    return bt.merge(wide, on=["cycle", "st", "special", "days"], how="left")


OURS = {"ours": "p", "polls only": "p_polls", "fundamentals only": "p_fund"}
WITH_538 = {**OURS, "538 lite": "p_538lite", "538 classic": "p_538classic", "538 deluxe": "p_538deluxe"}


def score(bt: pd.DataFrame, models: dict) -> pd.DataFrame:
    """Brier, log loss and wrong calls per forecast date, for all races and for competitive ones (a model in the
    comparison gave 10-90%)."""
    y = (bt.result > 0).astype(float)
    close = pd.concat([bt[c].between(0.1, 0.9) for c in ("p", "p_538classic") if c in models.values()], axis=1).any(axis=1)
    rows = []
    for d in DAYS:
        for sub, mask in (("all", bt.days == d), ("competitive", (bt.days == d) & close)):
            m = mask & bt[list(models.values())].notna().all(axis=1)
            for name, col in models.items():
                p = bt.loc[m, col].clip(0.01, 0.99)
                o = y[m]
                rows.append({"days": d, "races": sub, "n": int(m.sum()), "model": name,
                             "brier": ((p - o) ** 2).mean(),
                             "log_loss": -(o * np.log(p) + (1 - o) * np.log(1 - p)).mean(),
                             "wrong": int(((p > 0.5) != (o > 0.5)).sum())})
    return pd.DataFrame(rows)


def main() -> None:
    sen, gb, raw, T = senate_polls(), gb_polls(), calib.raw_polls(), calib.senate_table()
    S1, G1 = nominee_polls(one_per_poll(sen), T), one_per_poll(gb)
    print(f"polls: Senate {len(S1)} (nominee pairs, one per poll), generic ballot {len(G1)}", flush=True)
    allq = pd.concat([S1, G1], ignore_index=True)
    allq["t"] = (allq.mid - pd.to_datetime(allq.cycle.map(ELECTION))).dt.days.astype(float)
    frames = []
    for cyc in CYCLES:
        earlier = allq[allq.cycle < cyc].reset_index(drop=True)
        prior = calib.house_effects(earlier)[0]["mean"] if len(earlier) else None
        frames.append(run_cycle(cyc, sen, gb, S1, G1, raw, T, prior))
        print(f"{cyc}: done", flush=True)
    bt = add_538(pd.concat(frames, ignore_index=True))
    OUT.parent.mkdir(exist_ok=True)
    bt.to_csv(OUT, index=False)
    pd.set_option("display.width", 200)
    for label, sub, models in (("2018-2022, against 538", bt[bt.cycle < 2024], WITH_538),
                               ("2024 (no 538 file)", bt[bt.cycle == 2024], OURS),
                               ("2018-2024, our chain and its parts", bt, OURS)):
        sc = score(sub, models)
        print(f"\n######## {label}")
        for d in DAYS:
            print(f"== {d} days before the election ==")
            print(sc[sc.days == d].pivot_table(index="model", columns="races", values=["brier", "wrong", "n"])
                  .round(3).to_string())
    last = bt[bt.days == 1]
    err = lambda a: (a - last.result)
    tab = pd.DataFrame({"ours_bias": err(last.mu), "ours_mae": err(last.mu).abs(),
                        "polls_mae": err(last.mu_polls.fillna(last.mu_fund)).abs(), "fund_mae": err(last.mu_fund).abs(),
                        "538d_mae": err(2 * last.share_538deluxe - 100).abs()}).groupby(last.cycle).mean()
    print("\nelection-eve margin error by cycle:\n" + tab.round(2).to_string())
    bins = pd.cut(bt.p, [0, 0.1, 0.3, 0.5, 0.7, 0.9, 1.0])
    print("\ncalibration, all cycles and dates:", bt.groupby(bins, observed=True).apply(
        lambda g: f"n={len(g)} predicted {g.p.mean():.2f} actual {(g.result > 0).mean():.2f}", include_groups=False).to_dict())
    print(f"-> {OUT}")


if __name__ == "__main__":
    main()
