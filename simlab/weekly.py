"""Weekly filter (stats-groundwork §5.7, engine-design §3.3): learns from the polls how much of the simulated news
effect is real.

Each state, and the nation, has two dials, for the switching and turnout parts of its story effects: 1 means the
polls confirm the simulated effect, 0 that they show none of it. The dials only scale known effect paths, so the
polls' likelihood is an exact quadratic in them: six Kalman runs per state recover it, and the states combine with a
national dial in closed form, so states with few polls borrow from it. The same evidence weighs a grid of fade
speeds and flags states whose polls keep surprising the forecast.

From 14 Oct (simulation only, docs/simulation-only.md) nothing here re-fits the forecast: the dials stay at the 12 Oct
update, and the Sunday weekly check (check) compares each race's weekly move with the polls' or the markets'. The
filter itself stays for the poll-filter rule, which is still run for scoring.

    python -m simlab.weekly --date YYYY-MM-DD --data <path to simlab-data>
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import numpy as np
from scipy.stats import chi2, norm

from . import moves
from .levels import ELECTION, effect, local_level

PRIOR_VAR = 1e6  # diffuse start, as levels.local_level
WEEKLY_FROM = date(2026, 10, 5)  # Mondays from here run the update inside the daily statistics step (Matteo, 29 Sep)
POINTS = [(0, 0), (1, 0), (2, 0), (0, 1), (0, 2), (1, 1)]


def loglik(t: np.ndarray, y: np.ndarray, v: np.ndarray, q: float) -> tuple[float, np.ndarray]:
    """Log-likelihood of a local-level series (a random walk with daily variance q, plus poll noise v; same-day polls
    pooled as in levels.local_level) and each poll day's standardised innovation."""
    day, w = np.floor(t), 1 / v
    ll, x, p, last, z = 0.0, 0.0, PRIOR_VAR, None, []
    for d in np.unique(day):
        if last is not None:
            p += q * (d - last)
        sel = day == d
        vo = 1 / np.sum(w[sel])
        f, nu = p + vo, np.sum(w[sel] * y[sel]) * vo - x
        ll -= 0.5 * (np.log(2 * np.pi * f) + nu * nu / f)
        z.append(nu / np.sqrt(f))
        k = p / f
        x, p, last = x + k * nu, (1 - k) * p, d
    return ll, np.array(z)


def quadratic(f) -> tuple[np.ndarray, np.ndarray, float]:
    """(A, b, c) of an exactly quadratic log-likelihood f(k) = -k'Ak/2 + b'k + c in two dials, from six points."""
    v = {pt: f(np.array(pt, dtype=float)) for pt in POINTS}
    c = v[(0, 0)]
    a1, a2 = 2 * (v[(1, 0)] - c) - (v[(2, 0)] - c), 2 * (v[(0, 1)] - c) - (v[(0, 2)] - c)
    b1, b2 = v[(1, 0)] - c + a1 / 2, v[(0, 1)] - c + a2 / 2
    a12 = -(v[(1, 1)] - c - b1 - b2 + a1 / 2 + a2 / 2)
    return np.array([[a1, a12], [a12, a2]]), np.array([b1, b2]), c


def pool(units: dict, prior: dict) -> dict:
    """Posterior of the national dials and each unit's (state's, or "US") deviation from them: a hierarchical normal
    model solved exactly. `units` maps a unit to its log-likelihood quadratic (A, b, c) in its own two dials; the
    national dials have prior N(mean, sd^2) and each unit's deviation N(0, tau^2). Also returns the log evidence."""
    names = sorted(units)
    n = 2 + 2 * len(names)
    s0, tinv = np.diag(1 / np.array(prior["sd"], float) ** 2), np.diag(1 / np.array(prior["tau"], float) ** 2)
    lam0, mu0 = np.zeros((n, n)), np.zeros(n)
    lam0[:2, :2], mu0[:2] = s0, prior["mean"]
    for i in range(len(names)):
        lam0[2 + 2 * i:4 + 2 * i, 2 + 2 * i:4 + 2 * i] = tinv
    lam, eta, const = lam0.copy(), lam0 @ mu0, 0.0
    for i, u in enumerate(names):
        a, b, c = units[u]
        s = slice(2 + 2 * i, 4 + 2 * i)
        for r in (slice(0, 2), s):
            eta[r] += b
            for q in (slice(0, 2), s):
                lam[r, q] += a
        const += c
    cov = np.linalg.inv(lam)
    mean = cov @ eta
    log_ev = (const - mu0 @ lam0 @ mu0 / 2 + np.linalg.slogdet(lam0)[1] / 2 - np.linalg.slogdet(lam)[1] / 2
              + eta @ cov @ eta / 2)
    out = {"labels": ["national"] + names, "mean": mean.tolist(), "cov": cov.tolist(), "log_evidence": float(log_ev),
           "national": {"mean": mean[:2].tolist(), "cov": cov[:2, :2].tolist()}, "units": {}}
    for i, u in enumerate(names):
        s = slice(2 + 2 * i, 4 + 2 * i)
        c2 = cov[:2, :2] + cov[s, s] + cov[:2, s] + cov[s, :2]
        out["units"][u] = {"mean": (mean[:2] + mean[s]).tolist(), "cov": c2.tolist()}
    return out


def state_dial(post: dict, state: str, prior: dict) -> dict:
    """A state's dials: its own posterior if it had simulated stories and polls, else the national dials plus the
    prior spread of a state's deviation."""
    if state in post["units"]:
        return post["units"][state]
    nat = post["national"]
    return {"mean": nat["mean"], "cov": (np.array(nat["cov"]) + np.diag(np.array(prior["tau"], float) ** 2)).tolist()}


def _paths(m: dict, part: str, h_age: float | None = None, offset: float = 0.0, nation: bool = False) -> dict:
    """Each race's own effect paths at dial 1 for one part ("s" or "t"), and the nation's under "US", with the age
    half-life replaced by `h_age` if given, and the switching part's support offset moved by `offset` from the one
    moves.json was built with. With `nation`, the nation's stories each race takes instead (moves.nation_paths)."""
    get = moves.nation_paths if nation else (lambda mm, p: moves.paths(mm, p, with_nation=False))
    unit = get(m, "s_unit") if part == "s" and offset else {}
    return {r: [(f, l, x + offset * (unit[r][i][2] if unit else 0.0), h_age or ha, hf)
                for i, (f, l, x, ha, hf) in enumerate(items)]
            for r, items in get(m, f"{part}_base").items()}


def units(p, m: dict, params: dict, d: int, election=ELECTION, dials_us=(1.0, 1.0), h_age: float | None = None,
          offset: float = 0.0) -> dict:
    """Each unit's log-likelihood quadratic in its two dials: the nation's from the generic-ballot polls, each state's
    from its simulated races' polls relative to the national level (itself net of the national stories at
    `dials_us`). `p` is levels.poll_frame's table and `m` moves.json; `offset` as in _paths."""
    q_n, q_r = params["drift_daily_sd"]["national"] ** 2, params["drift_daily_sd"]["race"] ** 2
    ps, pt = _paths(m, "s", h_age, offset), _paths(m, "t", h_age)
    g = p[p.race == "US"]
    tg, yg, vg = g.t.values.astype(float), g.adj.values, g.v.values
    su, tu = effect(tg, ps.get("US", []), election), effect(tg, pt.get("US", []), election)
    out = {}
    if np.any(su) or np.any(tu):
        out["US"] = quadratic(lambda k: loglik(tg, yg - k[0] * su - k[1] * tu, vg, q_n)[0])
    grid, nx, npv = local_level(tg, yg - dials_us[0] * su - dials_us[1] * tu, vg, q_n, -d)
    ns, nt = _paths(m, "s", h_age, offset, nation=True), _paths(m, "t", h_age, nation=True)
    for race in sorted(r for r in ps if r != "US"):
        rp = p[p.race == race]
        t = rp.t.values.astype(float)
        s, u = effect(t, ps[race], election), effect(t, pt[race], election)
        if not len(rp) or not (np.any(s) or np.any(u)):
            continue
        y0, v = rp.adj.values - np.interp(t, grid, nx), rp.v.values + np.interp(t, grid, npv)
        if ns.get(race) or nt.get(race):  # the nation's stories it takes, at the national dials
            y0 = y0 - dials_us[0] * effect(t, ns.get(race, []), election) - dials_us[1] * effect(t, nt.get(race, []),
                                                                                                  election)
        a, b, c = quadratic(lambda k: loglik(t, y0 - k[0] * s - k[1] * u, v, q_r)[0])
        st = race.split("-")[0]
        out[st] = (out[st][0] + a, out[st][1] + b, out[st][2] + c) if st in out else (a, b, c)
    return out


def fade_grid(p, m: dict, params: dict, d: int, prior: dict, grid: list[float], election=ELECTION,
              center: float = 5.5, spread: float = 0.5) -> dict:
    """Weighs the age half-lives in `grid` by the polls' evidence with each (the dials integrated over their prior),
    times a lognormal prior around `center`; returns the weights and their geometric mean."""
    logw = {h: pool(units(p, m, params, d, election, h_age=h), prior)["log_evidence"]
            - 0.5 * (np.log(h / center) / spread) ** 2 for h in grid}
    top = max(logw.values())
    w = {h: np.exp(v - top) for h, v in logw.items()}
    tot = sum(w.values())
    return {"grid": [round(h, 3) for h in grid], "weights": {f"{h:g}": round(float(w[h] / tot), 4) for h in grid},
            "half_life": round(float(np.exp(sum(w[h] / tot * np.log(h) for h in grid))), 2),
            "prior": {"center": center, "spread_log": spread}}


def offset_grid(p, m: dict, params: dict, d: int, prior: dict, grid: list[float], used: float, election=ELECTION,
                h_age: float | None = None, mean: float = 0.08, sd: float = 0.065) -> dict:
    """Weighs GLM's support offsets in `grid` by the polls' evidence with each (the dials integrated over their prior;
    moves.json was built with `used`), times a normal prior; returns the weights, their mean and a flag when the
    polls pull the offset below zero, against the benchmark's sign (Matteo decides then)."""
    logw = {b: pool(units(p, m, params, d, election, h_age=h_age, offset=b - used), prior)["log_evidence"]
            - 0.5 * ((b - mean) / sd) ** 2 for b in grid}
    top = max(logw.values())
    w = {b: np.exp(v - top) for b, v in logw.items()}
    tot = sum(w.values())
    est = float(sum(w[b] / tot * b for b in grid))
    return {"grid": [round(b, 4) for b in grid], "weights": {f"{b:g}": round(float(w[b] / tot), 4) for b in grid},
            "offset": round(est, 4), "prior": {"mean": mean, "sd": sd}, "flag": est < 0}


def _flag(t: np.ndarray, z: np.ndarray, d: int, days: int, alpha: float) -> dict:
    zz = z[np.unique(np.floor(t)) > -d - days]
    stat = float(np.sum(zz ** 2))
    pv = float(chi2.sf(stat, len(zz))) if len(zz) else 1.0
    return {"n": int(len(zz)), "chi2": round(stat, 2), "p": round(pv, 4),
            "mean_z": round(float(zz.mean()), 2) if len(zz) else 0.0, "flag": bool(len(zz) and pv < alpha)}


def surprises(p, m: dict, params: dict, d: int, dials: dict, election=ELECTION, days: int = 7, alpha: float = 0.01,
              h_age: float | None = None, offset: float = 0.0) -> dict:
    """The innovation monitor: each series' standardised surprises over the last `days` days, with the story effects
    at `dials` ({unit: (k_s, k_t)}), their chi-squared p-value, and a flag below `alpha`. A state that keeps
    getting flagged goes to the weekly auditor, which explains and never changes numbers."""
    q_n, q_r = params["drift_daily_sd"]["national"] ** 2, params["drift_daily_sd"]["race"] ** 2
    ps, pt = _paths(m, "s", h_age, offset), _paths(m, "t", h_age)
    ku = dials.get("US", (1.0, 1.0))
    g = p[p.race == "US"]
    tg = g.t.values.astype(float)
    yg = g.adj.values - ku[0] * effect(tg, ps.get("US", []), election) - ku[1] * effect(tg, pt.get("US", []), election)
    out = {"US": _flag(tg, loglik(tg, yg, g.v.values, q_n)[1], d, days, alpha)}
    grid, nx, npv = local_level(tg, yg, g.v.values, q_n, -d)
    ns, nt = _paths(m, "s", h_age, offset, nation=True), _paths(m, "t", h_age, nation=True)
    for race in sorted(set(p.race) - {"US"}):
        rp = p[p.race == race]
        t = rp.t.values.astype(float)
        # a race without stories of its own takes all the nation's, one with stories those it takes
        nat = [effect(t, x.get("US", []) if race not in ps else n.get(race, []), election)
               for x, n in ((ps, ns), (pt, nt))]
        own = [effect(t, x[race], election) for x in (ps, pt)] if race in ps else [0.0, 0.0]
        k = dials.get(race.split("-")[0], ku)
        y = (rp.adj.values - k[0] * own[0] - k[1] * own[1] - (ku[0] * nat[0] + ku[1] * nat[1])
             - np.interp(t, grid, nx))
        out[race] = _flag(t, loglik(t, y, rp.v.values + np.interp(t, grid, npv), q_r)[1], d, days, alpha)
    return out


TREND = {"min_new_polls": 3, "flag_over": 4.0, "analyse_over": 6.0, "far_over": 15.0, "far_min_polls": 3,
         "rollback": "none: only what the analysis finds wrong is fixed, as a logged change with both versions scored"}


def trend(now: dict, before: dict | None, polls, rules: dict = TREND) -> dict:
    """The weekly trend check (Matteo, 11 Oct): in each state with `min_new_polls` or more polls first seen since the
    forecast a week earlier (`before`; one row per poll in `polls`, polls.csv), the week's change in our 3 Nov margin
    (p50) against the change in the poll average beside it in forecast.json. Moves in opposite directions more than
    `flag_over` points apart are flagged, more than `analyse_over` analysed for a bug, a bad story summary or a story
    on the wrong race. It only reports: nothing is rolled back."""
    out = {"since": before and before.get("date"), "since_snapshot": before and before.get("snapshot"), "rules": rules,
           "new_polls": {}, "races": {}, "flagged": [], "analyse": []}
    if before is None:
        return out | {"note": "no forecast a week ago: nothing to compare"}
    new = polls[(polls.race_id != "US") & (polls.first_seen.astype(str) > str(before["snapshot"]))]
    out["new_polls"] = {r: int(n) for r, n in sorted(new.race_id.value_counts().items())}
    for r, n in out["new_polls"].items():
        if n < rules["min_new_polls"] or r not in now["races"]:
            continue
        a, b = before["races"].get(r, {}), now["races"][r]
        pa, pb = (x.get("benchmarks", {}).get("poll_avg") for x in (a, b))
        if pa is None or pb is None:
            out["races"][r] = {"new_polls": n, "level": f"no poll average {'a week ago' if pa is None else 'today'}"}
            continue
        fa, fb = a["margin"]["p50"], b["margin"]["p50"]
        df, dp = round(fb - fa, 2), round(pb - pa, 2)
        gap, opposite = round(abs(df - dp), 2), df * dp < 0
        level = ("ok" if not opposite or gap <= rules["flag_over"] else
                 "flag" if gap <= rules["analyse_over"] else "analyse")
        news = lambda x: (x.get("news") or {}).get("effect", 0.0)
        row = {"office": b.get("office", "senate"), "new_polls": n, "forecast": {"before": fa, "now": fb, "change": df},
               "poll_avg": {"before": pa, "now": pb, "change": dp},
               "stats_only_change": round(b["stats_only"]["margin"]["p50"] - a["stats_only"]["margin"]["p50"], 2),
               "news_change": round(news(b) - news(a), 2) if "news" in a or "news" in b else None,
               "opposite": opposite, "gap": gap, "level": level}
        if level != "ok":
            row["movers"] = b.get("movers", [])
            out["flagged" if level == "flag" else "analyse"].append(r)
        out["races"][r] = row
    return out


def far_from_polls(races: dict, polls: dict, rules: dict = TREND) -> dict:
    """The level check (Matteo, 12 Oct): races (forecast.json rows, house_view's for House seats) with `far_min_polls`
    or more polls in the table (`polls`: race id -> rows) whose 3 Nov margin sits more than `far_over` points from
    their poll average. Reports only."""
    out = {}
    for r, x in sorted(races.items()):
        pa = x.get("benchmarks", {}).get("poll_avg")
        if pa is None or polls.get(r, 0) < rules["far_min_polls"]:
            continue
        if (gap := round(abs(x["margin"]["p50"] - pa), 2)) > rules["far_over"]:
            out[r] = {"office": x.get("office", "senate"), "forecast": x["margin"]["p50"], "poll_avg": pa, "gap": gap,
                      "polls": int(polls[r])}
    return out


def house_view(forecast: dict | None, levels: dict | None) -> dict:
    """House seats in forecast.json's race shape for trend() and far_from_polls(): the 3 Nov margin from forecast.json's
    House block, the stats-only margin and poll average from house_levels.json (the stats-only twin)."""
    if not (forecast or {}).get("house") or not levels:
        return {}
    r2 = lambda v: None if v is None else round(v, 2)
    lv = levels["races"]
    return {r: {"office": "house", "margin": x["margin"], "stats_only": {"margin": {"p50": r2(lv[r]["margin"])}},
                "benchmarks": {"poll_avg": r2(lv[r]["poll_margin"])}}
            for r, x in forecast["house"]["races"].items() if r in lv}


CHECK = {"flag_over": 3.0, "severe_over": 5.0, "cancel_over": 6.5, "min_new_polls": 1, "min_polls_severe": 3,
         "gap": "|our 3 Nov margin's change over the week - the poll average's change|, points, any direction",
         "no_polls": "the markets' implied margin instead (win chance as a margin on our spread), flag only",
         "cancel": "only with Matteo's yes (cancelled_weeks.json): the race drops that week's stories"}


def implied(p: float, x: dict) -> float:
    """A market's win chance for the left candidate as a margin: its normal quantile times our forecast's spread."""
    s = (x["margin"]["p90"] - x["margin"]["p10"]) / (2 * norm.ppf(0.9))
    return float(norm.ppf(min(max(p, 0.01), 0.99)) * s)


def _level(gap: float | None, basis: str | None, n: int, rules: dict) -> str:
    """"", "flag", "severe" or "cancel"; severe and cancel need polls, `min_polls_severe` of them new that week."""
    if gap is None:
        return ""
    strong = basis == "polls" and n >= rules["min_polls_severe"]
    if strong and gap > rules["cancel_over"]:
        return "cancel"
    if strong and gap > rules["severe_over"]:
        return "severe"
    return "flag" if gap > rules["flag_over"] else ""


def check(now: dict, before: dict, new_polls: dict, stories: dict, cancelled: set = frozenset(),
          rules: dict = CHECK) -> dict:
    """The weekly check (Matteo, 13 Oct): per race (forecast.json rows, house_view's for House seats, now and a week
    before), our 3 Nov margin's change against the poll average's change when the week brought new polls
    (`new_polls`: race -> count), else against the markets' implied margin (flag only). Gap above `flag_over` is a
    flag, above `severe_over` severe, above `cancel_over` a week to cancel with Matteo's yes (both need
    `min_polls_severe` new polls, else it stays a flag); a race in `cancelled`
    (cancelled with his yes) says so. Rows carry the stories behind our move (`stories`, week_stories: a race's own,
    or the nation's for a flagged race without its own), largest gap first. It only reports."""
    rows = []
    for r, b in now.items():
        a = before.get(r)
        if not a:
            continue
        ours = round(b["margin"]["p50"] - a["margin"]["p50"], 2)
        n = int(new_polls.get(r, 0))
        pa, pb = (x.get("benchmarks", {}).get("poll_avg") for x in (a, b))
        ma, mb = (x.get("benchmarks", {}).get("market") for x in (a, b))
        polls = round(pb - pa, 2) if pa is not None and pb is not None else None
        markets = round(implied(mb, b) - implied(ma, a), 2) if ma is not None and mb is not None else None
        basis = "polls" if n >= rules["min_new_polls"] and polls is not None else "markets" if markets is not None             else None
        gap = round(abs(ours - (polls if basis == "polls" else markets)), 2) if basis else None
        flag = "cancelled" if r in cancelled else _level(gap, basis, n, rules)
        own = stories.get(r)
        rows.append({"race": r, "state": r.split("-")[0], "office": b.get("office", "senate"), "ours": ours,
                     "polls": polls, "markets": markets, "gap": gap, "flag": flag, "n_polls": n, "basis": basis,
                     "margin": b["margin"]["p50"], "margin_before": a["margin"]["p50"],
                     "stories": own if own is not None else (stories.get("US", []) if flag else []),
                     "what_we_did": ""})
    rows.sort(key=lambda x: (x["gap"] is None, -(x["gap"] or 0.0), x["race"]))
    pick = lambda f: [x["race"] for x in rows if x["flag"] == f]
    return {"rules": rules, "races": rows, "flagged": pick("flag"), "severe": pick("severe"), "cancel": pick("cancel"),
            "cancelled": pick("cancelled"), "no_check": [x["race"] for x in rows if x["basis"] is None]}


def week_stories(m: dict, since, top: int = 5) -> dict:
    """{race_id or "US": the stories first seen after `since` with the largest expected effect on its 3 Nov margin}
    from moves.json's main block: event id, summary card, first seen and effect in points."""
    out = {}
    for r, x in m.items():
        if r == "shadow" or not isinstance(x, dict) or not x.get("events"):
            continue
        new = [(e, v) for e, v in x["events"].items() if v["first_seen"] > str(since)]
        new.sort(key=lambda kv: -abs(kv[1]["election_day"]))
        out[r] = [{"event_id": e, "card": v.get("card", ""), "first_seen": v["first_seen"],
                   "delta": round(v["election_day"], 2)} for e, v in new[:top]]
    return out


def check_summary(res: dict) -> dict:
    """The weekly check's line in run.json."""
    return {k: res.get(k, []) for k in ("flagged", "severe", "cancel", "cancelled")} | {
        "far_from_polls": sorted(res.get("far_from_polls", {}))} | ({"note": res["note"]} if "note" in res else {})


def _alone(a: np.ndarray, b: np.ndarray, most: float = 5.0) -> dict:
    """What a unit's polls say about its two dials on their own: the estimate and its standard error, or None for a dial
    the polls don't pin down yet (no information, or a standard error above `most`)."""
    cov = np.linalg.pinv(a)
    k, var = cov @ b, np.diag(cov)
    ok = [v > 0 and np.sqrt(v) <= most for v in var]
    return {"k": [round(float(k[i]), 3) if ok[i] else None for i in range(2)],
            "se": [round(float(np.sqrt(var[i])), 3) if ok[i] else None for i in range(2)]}


def _dial(x: dict) -> dict:
    return {"k_s": round(float(x["mean"][0]), 4), "k_t": round(float(x["mean"][1]), 4),
            "sd_s": round(float(np.sqrt(x["cov"][0][0])), 4), "sd_t": round(float(np.sqrt(x["cov"][1][1])), 4)}


def run(day: date, t: dict, m: dict, mp: dict, election=ELECTION) -> dict:
    """The week's update from every poll up to `day` (t: polls.build of the day's snapshot) and the day's moves.json
    (m), with the priors in move_params (mp): the fade speed, then GLM's support offset, then the national dials, then
    each state's, then the surprise monitor. "polls_alone" is what each unit's polls say on their own, before
    pooling."""
    from .levels import inputs, poll_frame
    params, priors, *_ = inputs()
    p = poll_frame(t["senate"], t["generic_ballot"], params, priors, day, election, t["entries"])[0]
    d, prior, center = (election - day).days, mp["dial_prior"], mp["age_half_life_prior"]
    fade = fade_grid(p, m, params, d, prior, [round(center * 2 ** e, 2) for e in (-1, -0.5, 0, 0.5, 1)], election,
                     center)
    h, used, bp = fade["half_life"], mp.get("support_offset", 0.0), mp.get("support_offset_prior")
    lean = offset_grid(p, m, params, d, prior, [bp["mean"] + bp["sd"] * e for e in (-2, -1, 0, 1, 2)], used, election,
                       h, bp["mean"], bp["sd"]) if bp else None
    off = lean["offset"] - used if lean else 0.0
    us = tuple(state_dial(pool(units(p, m, params, d, election, h_age=h, offset=off), prior), "US", prior)["mean"])
    u = units(p, m, params, d, election, dials_us=us, h_age=h, offset=off)
    post = pool(u, prior)
    alone = {name: _alone(a, b) for name, (a, b, _) in u.items()}
    means = {name: tuple(x["mean"]) for name, x in post["units"].items()}
    return {"polls": {"n": int(len(p)), "first": str(p.mid.min()), "last": str(p.mid.max())}, "prior": prior,
            "fade": fade, "offset": lean, "posterior": {k: post[k] for k in ("labels", "mean", "cov", "log_evidence")},
            "dials": {name: _dial(x) for name, x in post["units"].items()} | {"default": _dial(post["national"])},
            "polls_alone": alone,
            "surprises": surprises(p, m, params, d, means | {"US": means.get("US", us)}, election, h_age=h, offset=off)}


def main() -> int:
    """Runs the update for a day whose statistics step has already written moves.json."""
    from . import polls, statsday
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", type=date.fromisoformat, default=datetime.now(timezone.utc).date())
    ap.add_argument("--data", type=Path, default=Path(__file__).resolve().parents[2] / "simlab-data")
    a = ap.parse_args()
    out = a.data / "derived" / a.date.isoformat()
    m = json.loads((out / "moves.json").read_text(encoding="utf-8"))
    mp = json.loads(moves.PARAMS.read_text(encoding="utf-8"))
    wk = {"date": a.date.isoformat(), "run_id": m["run_id"], "schema": 1} | run(
        a.date, polls.build(statsday.snapshot_for(a.data, a.date)), m, mp)
    (out / "filter_weekly.json").write_text(json.dumps(wk, indent=1), encoding="utf-8")
    print(json.dumps({"ok": True, "date": a.date.isoformat(), "units": sorted(wk["posterior"]["labels"][1:]),
                      "half_life": wk["fade"]["half_life"], "flags": sorted(r for r, x in wk["surprises"].items()
                                                                            if x["flag"])}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
