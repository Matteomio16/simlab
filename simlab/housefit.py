"""Fits the House-seat forecast's swing-response and incumbency coefficients on MIT's House results, 1976-2024, and
writes them to simlab/house_params.json. Method: a Gelman-King style district regression m_t = a_year + b*m_{t-1} +
psi*I_t + c*I_{t-1} on consecutive-cycle district pairs with both years contested (a district races itself two years
later; redistricted pairs are skipped). a_year is the national-swing fixed effect the engine supplies separately, so
it is fit by demeaning each year's rows (equivalent to year dummies) rather than kept as a coefficient. I_t is +1/-1
when the previous winner is running again as the D/R candidate, 0 for an open seat; I_{t-1} is the same indicator one
cycle earlier, controlling for incumbency already baked into m_{t-1}. A second variant splits I_t by whether the
incumbent is defending for the first time. Leave-one-cycle-out residuals (refit without year y, then set that year's
national swing to the mean residual, as the forecast does with a known swing) give the district error to use when a
district is unpolled.

Data: data/results/1976-2024-house.tab. Candidates are matched across a district's fusion party lines by name within
a contest, and across cycles by a normalised last-name + first-initial key.

    python -m simlab.housefit
"""
from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

DATA = Path(__file__).parent.parent / "data" / "results" / "1976-2024-house.tab"
OUT = Path(__file__).parent / "house_params.json"

SUFFIX = {"JR", "SR", "II", "III", "IV"}
REDRAW_ALL = {1982, 1992, 2002, 2012, 2022}
REDRAW_STATES = {2004: {"TX"}, 2006: {"GA", "TX"}, 2016: {"FL", "NC", "VA"}, 2018: {"PA"}, 2020: {"NC"},
                 2024: {"AL", "GA", "LA", "NC", "NY"}}
IDX = ["year", "state_po", "district"]


def normalize(name: str) -> str:
    toks = [t for t in re.sub(r"[\"'(),.]", " ", str(name).upper()).split() if t not in SUFFIX]
    return f"{toks[-1]}_{toks[0][0]}" if toks else ""


def party_letter(p) -> str:
    if not isinstance(p, str):
        return "O"
    return "D" if "DEMOCRAT" in p else "R" if "REPUBLICAN" in p else "O"


def load_candidates() -> pd.DataFrame:
    """One row per candidate per district-year: votes summed across a candidate's party lines (fusion tickets) and
    modes (the file has only mode TOTAL, so this is a plain sum); party is the candidate's largest line."""
    df = pd.read_csv(DATA, low_memory=False)
    df = df[(df.stage == "GEN") & (df.special == False) & (df.runoff.fillna(False) != True)]
    df = df[~((df.state_po == "LA") & (df.year < 2008))]
    df = df.assign(pl=df.party.map(party_letter))
    g = df.groupby(IDX + ["candidate"])
    cand = g.candidatevotes.sum().rename("votes").reset_index()
    top = df.loc[g.candidatevotes.idxmax(), IDX + ["candidate", "pl"]]
    cand = cand.merge(top, on=IDX + ["candidate"])
    cand["key"] = cand.candidate.map(normalize)
    return cand


def contests(cand: pd.DataFrame) -> pd.DataFrame:
    """One row per district-year: the top D and R candidate (key, votes) and the outright winner (any party)."""
    def pick(letter):
        s = cand[cand.pl == letter]
        r = s.loc[s.groupby(IDX).votes.idxmax(), IDX + ["key", "votes"]]
        return r.set_index(IDX).rename(columns={"key": f"{letter.lower()}_key", "votes": f"{letter.lower()}_votes"})
    win = cand.loc[cand.groupby(IDX).votes.idxmax(), IDX + ["key", "pl"]]
    win = win.set_index(IDX).rename(columns={"key": "win_key", "pl": "win_pl"})
    out = win.join(pick("D"), how="left").join(pick("R"), how="left").reset_index()
    out[["d_votes", "r_votes"]] = out[["d_votes", "r_votes"]].fillna(0)
    # Louisiana's jungle primary can put two candidates of the same party on the same "GEN" line (they'd otherwise
    # meet in a December runoff); flag district-years where a second D or second R took a real share of the vote,
    # since the top-D-vs-top-R pair then understates that party's true vote and isn't a clean D-vs-R contest.
    frac = cand.votes / cand.groupby(IDX).votes.transform("sum")
    split = (cand[frac >= 0.15].groupby(IDX + ["pl"]).size() > 1).groupby(IDX).any()
    out = out.merge(split.rename("split").reset_index(), on=IDX, how="left")
    out["split"] = out.split.fillna(False)
    out["contested"] = out.d_key.notna() & out.r_key.notna() & ~out.split
    out["m"] = np.where(out.contested, 100 * (out.d_votes - out.r_votes) / (out.d_votes + out.r_votes), np.nan)
    return out


def build_panel(c: pd.DataFrame) -> pd.DataFrame:
    """Adds m_{t-1}, I_t, I_{t-1}, the first-termer flag and valid_pair (whether year-2 to year is on the same lines,
    for the b/psi/c fit) to each district-year.

    Incumbency is a property of the person, not the district: I_t asks whether the district's top D or R candidate
    won ANY general in the same state two years earlier (matched by name key), wherever they won it, so it still
    works across a redistricting boundary (flagged incumbent_moved when the district number changed). I_{t-1} asks
    the same question of whoever ran in that same district two years earlier, one cycle further back."""
    ndist = c.groupby(["year", "state_po"]).district.nunique().to_dict()
    swin: dict[tuple[int, str], dict[str, int]] = {}
    for r in c.itertuples():
        swin.setdefault((r.year, r.state_po), {})[r.win_key] = r.district
    dr = {(r.year, r.state_po, r.district): (r.d_key, r.r_key) for r in c.itertuples()}

    def valid_pair(st, y):
        if y in REDRAW_ALL or st in REDRAW_STATES.get(y, set()):
            return False
        n1, n0 = ndist.get((y, st)), ndist.get((y - 2, st))
        return n1 is not None and n0 is not None and n1 == n0

    def inc(y, st, d):
        """(sign, moved) from state-wide winners two years before y, or None if that year has no data at all."""
        prev = swin.get((y - 2, st))
        if prev is None:
            return None
        dk, rk = dr.get((y, st, d), (None, None))
        d_in, r_in = dk in prev, rk in prev
        if d_in and r_in:
            return 0, False  # member vs member after redistricting: no net incumbency edge
        if d_in:
            return 1, prev[dk] != d
        if r_in:
            return -1, prev[rk] != d
        return 0, False

    prev_m = c[IDX + ["m"]].assign(year=lambda x: x.year + 2).rename(columns={"m": "m_lag"})
    p = c.merge(prev_m, on=IDX, how="left")
    p["valid_pair"] = [valid_pair(st, y) for y, st in zip(p.year, p.state_po)]
    it = [inc(y, st, d) for y, st, d in zip(p.year, p.state_po, p.district)]
    p["I_t"] = [x[0] if x else np.nan for x in it]
    p["incumbent_moved"] = [x[1] if x else np.nan for x in it]
    il = [inc(y - 2, st, d) for y, st, d in zip(p.year, p.state_po, p.district)]
    p["I_lag"] = [x[0] if x else np.nan for x in il]
    p["first_termer"] = np.where(p.I_lag.isna(), np.nan, p.I_lag == 0)
    return p


def fe_fit(d: pd.DataFrame, x_cols: list[str], y_col: str = "m"):
    """Year fixed-effect OLS by within-year demeaning (equivalent to year dummies); returns coefficients and the
    per-year effect (the national swing each year's rows imply)."""
    dm = d.groupby("year")[[y_col] + x_cols].transform(lambda s: s - s.mean())
    b, *_ = np.linalg.lstsq(dm[x_cols].values, dm[y_col].values, rcond=None)
    means = d.groupby("year")[[y_col] + x_cols].mean()
    a = means[y_col] - means[x_cols].values @ b
    return b, a


def loyo(d: pd.DataFrame, x_cols: list[str], years: list[int]) -> pd.DataFrame:
    """Leave-one-cycle-out: refit b/psi/c without year y, set that year's swing to the mean residual, collect
    residuals and the fitted psi for each left-out year."""
    rows, psis = [], {}
    for y in years:
        train = d[(d.year != y) & d.year.isin(years)]
        b, _ = fe_fit(train, x_cols)
        test = d[d.year == y].copy()
        pred = test[x_cols].values @ b
        a_y = (test.m - pred).mean()
        test["resid"] = test.m - pred - a_y
        test["fitted"] = a_y + pred
        rows.append(test)
        psis[y] = b[x_cols.index("I_t")] if "I_t" in x_cols else np.nan
    return pd.concat(rows), psis


def cluster_bootstrap_coef(fit: pd.DataFrame, x_cols: list[str], years: list[int], n: int = 500, seed: int = 0):
    """Cluster bootstrap by election year: resample years with replacement, refit, n times. Returns the coefficient
    draws (rows = draws, columns = x_cols)."""
    rng = np.random.default_rng(seed)
    groups = {y: fit[fit.year == y] for y in years}
    draws = []
    for _ in range(n):
        samp = rng.choice(years, size=len(years), replace=True)
        boot = pd.concat([groups[y] for y in samp], ignore_index=True)
        b, _ = fe_fit(boot, x_cols)
        draws.append(b)
    return np.array(draws)


def cluster_bootstrap_sd(res: pd.DataFrame, years: list[int], n: int = 500, seed: int = 1) -> np.ndarray:
    """Cluster bootstrap by election year of a residual-SD statistic: resample years' residuals with replacement,
    pool and take the SD, n times."""
    rng = np.random.default_rng(seed)
    groups = {y: res.resid[res.year == y].values for y in years}
    draws = []
    for _ in range(n):
        samp = rng.choice(years, size=len(years), replace=True)
        pooled = np.concatenate([groups[y] for y in samp])
        draws.append(pooled.std(ddof=1))
    return np.array(draws)


def ci90(x: np.ndarray) -> list[float]:
    return [round(float(v), 3) for v in np.percentile(x, [5, 95])]


def main() -> None:
    cand = load_candidates()
    c = contests(cand)
    p = build_panel(c)

    win_1996 = (p.year >= 1996) & (p.year <= 2024)
    elig = p[win_1996].copy()
    # the b/psi/c fit keeps exactly the same pairs as before: same lines (valid_pair) and both years contested.
    elig["eligible_pair"] = elig.valid_pair & elig.m_lag.notna()
    n_uncontested = int((elig.eligible_pair & ~elig.contested).sum())
    n_split = int((elig.eligible_pair & elig.split).sum())
    fit = elig[elig.eligible_pair & elig.contested].copy()
    n_lag_unknown = int(fit.I_lag.isna().sum())  # only possible right at the start of the source data (pre-1980)
    fit["I_lag"] = fit.I_lag.fillna(0)
    n_moved = int(fit.incumbent_moved.fillna(False).astype(bool).sum())

    ft = fit.first_termer.fillna(False).astype(bool)
    fit["I_first"] = np.where(ft, fit.I_t, 0)
    fit["I_senior"] = np.where(~ft & (fit.I_t != 0), fit.I_t, 0)
    n_first = int((fit.first_termer == True).sum())
    n_senior = int(((fit.I_t != 0) & (fit.first_termer == False)).sum())
    n_unknown = int(((fit.I_t != 0) & fit.first_termer.isna()).sum())

    main_x, split_x = ["m_lag", "I_t", "I_lag"], ["m_lag", "I_first", "I_senior", "I_lag"]
    b, _ = fe_fit(fit, main_x)
    bf, _ = fe_fit(fit, split_x)
    fit10, fit14 = fit[fit.year >= 2010], fit[fit.year >= 2014]
    b10, _ = fe_fit(fit10, main_x)
    b14, _ = fe_fit(fit14, main_x)
    bf14, _ = fe_fit(fit14, split_x)

    years = sorted(y for y in fit.year.unique())
    res, psi_by_year = loyo(fit, main_x, years)

    def sd(mask):
        return float(res.resid[mask].std(ddof=1))

    def sd_breakdown(year_mask):
        open_m, inc_m = (res.I_t == 0) & year_mask, (res.I_t != 0) & year_mask
        return {"all": sd(year_mask), "close_lt15": sd((res.fitted.abs() < 15) & year_mask),
                "open": sd(open_m), "incumbent": sd(inc_m)}

    sds = sd_breakdown(res.resid.notna())
    sds_2014 = sd_breakdown(res.year >= 2014)
    sd_by_year = {int(y): round(float(g.resid.std(ddof=1)), 2) for y, g in res.groupby("year")}

    boot_main = cluster_bootstrap_coef(fit, main_x, years)
    boot_split = cluster_bootstrap_coef(fit, split_x, years)
    boot_sd14 = cluster_bootstrap_sd(res, [y for y in years if y >= 2014])
    ci = {"psi": ci90(boot_main[:, 1]), "psi_first": ci90(boot_split[:, 1]), "psi_senior": ci90(boot_split[:, 2]),
          "sd_2014_2024": ci90(boot_sd14)}

    print(f"Candidates {len(cand)}, district-years {len(c)}, contested {int(c.contested.sum())}")
    print(f"Fit panel 1996-2024: {len(fit)} pairs, {n_uncontested} uncontested/non-D-vs-R skipped "
          f"(of which {n_split} same-party vote-splits, mostly LA jungle races), "
          f"first-termers {n_first}, senior incumbents {n_senior}, unknown seniority {n_unknown} "
          f"(I_lag unresolvable {n_lag_unknown}), incumbent ran in a different district number {n_moved}")
    print(f"b {b[0]:.3f} psi {b[1]:.3f} c {b[2]:.3f} | 2010-2024: b {b10[0]:.3f} psi {b10[1]:.3f} c {b10[2]:.3f} "
          f"| 2014-2024: b {b14[0]:.3f} psi {b14[1]:.3f} c {b14[2]:.3f}")
    print(f"psi_first {bf[1]:.3f} psi_senior {bf[2]:.3f} (c {bf[3]:.3f}) | 2014-2024: "
          f"psi_first {bf14[1]:.3f} psi_senior {bf14[2]:.3f}")
    print("SD (district error when unpolled), all years:", {k: round(v, 2) for k, v in sds.items()})
    print("SD, 2014-2024 only:", {k: round(v, 2) for k, v in sds_2014.items()})
    print("SD by left-out year:", sd_by_year)
    print("90% cluster-bootstrap-by-year intervals (500 draws):", ci)

    params = {
        "fitted": f"{date.today().isoformat()}, python -m simlab.housefit",
        "source": "data/results/1976-2024-house.tab (MIT Election Lab)",
        "method": "Gelman-King district regression m_t = a_year + b*m_t-1 + psi*I_t + c*I_t-1 on consecutive House "
                  "elections in the same district with both years contested by a D and an R; a_year (the national "
                  "swing) is fit by demeaning within year rather than as a coefficient, since the forecast supplies "
                  "it separately. Incumbency is a property of the person: I_t is +1/-1 when the district's D/R "
                  "candidate won ANY general in the same state two years earlier (matched by normalised name), "
                  "wherever in the state they won it (incumbent_moved flags a changed district number), 0 for an "
                  "open seat or a member-vs-member race after redistricting; I_t-1 is the same check for whoever ran "
                  "in that district one cycle earlier. A second fit splits I_t into first-term and senior "
                  "incumbents. The b/psi/c fit itself still only uses consecutive-cycle pairs on the same district "
                  "lines: redistricted pairs (decennial years for all states, listed mid-decade redraws, or a "
                  "change in the state's district count) are skipped, as is Louisiana's jungle primary before 2008 "
                  "and any district-year where a second candidate of the same party took 15%+ of the vote (a jungle "
                  "race not really D-vs-R). The district error is from leave-one-election-cycle-out residuals: "
                  "refit without year y, set that year's swing to the mean residual (as the forecast does once it "
                  "knows the swing), collect residuals. 90% intervals are a cluster bootstrap by election year (500 "
                  "resamples of years, with replacement, refit each time).",
        "n_pairs": len(fit), "n_uncontested_skipped": n_uncontested, "n_same_party_split_skipped": n_split,
        "n_incumbent_moved_district": n_moved, "years": "1996-2024",
        "b": round(float(b[0]), 3), "psi": round(float(b[1]), 3), "c": round(float(b[2]), 3),
        "psi_first": round(float(bf[1]), 3), "psi_senior": round(float(bf[2]), 3),
        "n_first_termers": n_first, "n_senior_incumbents": n_senior, "n_unknown_seniority": n_unknown,
        "b_2010_2024": round(float(b10[0]), 3), "psi_2010_2024": round(float(b10[1]), 3),
        "c_2010_2024": round(float(b10[2]), 3),
        "b_2014_2024": round(float(b14[0]), 3), "psi_2014_2024": round(float(b14[1]), 3),
        "c_2014_2024": round(float(b14[2]), 3),
        "psi_first_2014_2024": round(float(bf14[1]), 3), "psi_senior_2014_2024": round(float(bf14[2]), 3),
        "per_year_psi": {int(y): round(float(v), 3) for y, v in psi_by_year.items()},
        "sd": {k: round(v, 2) for k, v in sds.items()}, "sd_2014_2024": {k: round(v, 2) for k, v in sds_2014.items()},
        "sd_by_year": sd_by_year,
        "ci90_bootstrap_by_year": ci,
    }
    OUT.write_text(json.dumps(params, indent=1))
    print(f"-> {OUT}")


if __name__ == "__main__":
    main()
