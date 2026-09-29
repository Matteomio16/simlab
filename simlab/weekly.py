"""Weekly filter (stats-groundwork §5.7, engine-design §3.3): learns from the polls how much of the simulated news
effect is real.

Each state, and the nation, has two dials, for the switching and turnout parts of its story effects: 1 means the
polls confirm the simulated effect, 0 that they show none of it. The dials only scale known effect paths, so the
polls' likelihood is an exact quadratic in them: six Kalman runs per state recover it, and the states combine with a
national dial in closed form, so states with few polls borrow from it. The same evidence weighs a grid of fade
speeds and flags states whose polls keep surprising the forecast.

    python -m simlab.weekly --date YYYY-MM-DD --data <path to simlab-data>
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import numpy as np
from scipy.stats import chi2

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


def _paths(m: dict, part: str, h_age: float | None = None) -> dict:
    """Each race's own effect paths at dial 1 for one part ("s" or "t"), and the nation's under "US", with the age
    half-life replaced by `h_age` if given."""
    return {r: [(f, l, x, h_age or ha, hf) for f, l, x, ha, hf in items]
            for r, items in moves.paths(m, f"{part}_base", with_nation=False).items()}


def units(p, m: dict, params: dict, d: int, election=ELECTION, dials_us=(1.0, 1.0), h_age: float | None = None) -> dict:
    """Each unit's log-likelihood quadratic in its two dials: the nation's from the generic-ballot polls, each state's
    from its simulated races' polls relative to the national level (itself net of the national stories at
    `dials_us`). `p` is levels.poll_frame's table and `m` moves.json."""
    q_n, q_r = params["drift_daily_sd"]["national"] ** 2, params["drift_daily_sd"]["race"] ** 2
    ps, pt = _paths(m, "s", h_age), _paths(m, "t", h_age)
    g = p[p.race == "US"]
    tg, yg, vg = g.t.values.astype(float), g.adj.values, g.v.values
    su, tu = effect(tg, ps.get("US", []), election), effect(tg, pt.get("US", []), election)
    out = {}
    if np.any(su) or np.any(tu):
        out["US"] = quadratic(lambda k: loglik(tg, yg - k[0] * su - k[1] * tu, vg, q_n)[0])
    grid, nx, npv = local_level(tg, yg - dials_us[0] * su - dials_us[1] * tu, vg, q_n, -d)
    takes = moves.takes_nation(m)
    for race in sorted(r for r in ps if r != "US"):
        rp = p[p.race == race]
        t = rp.t.values.astype(float)
        s, u = effect(t, ps[race], election), effect(t, pt[race], election)
        if not len(rp) or not (np.any(s) or np.any(u)):
            continue
        y0, v = rp.adj.values - np.interp(t, grid, nx), rp.v.values + np.interp(t, grid, npv)
        if race in takes:
            y0 = y0 - dials_us[0] * effect(t, ps.get("US", []), election) - dials_us[1] * effect(t, pt.get("US", []),
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


def _flag(t: np.ndarray, z: np.ndarray, d: int, days: int, alpha: float) -> dict:
    zz = z[np.unique(np.floor(t)) > -d - days]
    stat = float(np.sum(zz ** 2))
    pv = float(chi2.sf(stat, len(zz))) if len(zz) else 1.0
    return {"n": int(len(zz)), "chi2": round(stat, 2), "p": round(pv, 4),
            "mean_z": round(float(zz.mean()), 2) if len(zz) else 0.0, "flag": bool(len(zz) and pv < alpha)}


def surprises(p, m: dict, params: dict, d: int, dials: dict, election=ELECTION, days: int = 7, alpha: float = 0.01,
              h_age: float | None = None) -> dict:
    """The innovation monitor: each series' standardised surprises over the last `days` days, with the story effects
    at `dials` ({unit: (k_s, k_t)}), their chi-squared p-value, and a flag below `alpha`. A state that keeps
    getting flagged goes to the weekly auditor, which explains and never changes numbers."""
    q_n, q_r = params["drift_daily_sd"]["national"] ** 2, params["drift_daily_sd"]["race"] ** 2
    ps, pt = _paths(m, "s", h_age), _paths(m, "t", h_age)
    ku = dials.get("US", (1.0, 1.0))
    g = p[p.race == "US"]
    tg = g.t.values.astype(float)
    yg = g.adj.values - ku[0] * effect(tg, ps.get("US", []), election) - ku[1] * effect(tg, pt.get("US", []), election)
    out = {"US": _flag(tg, loglik(tg, yg, g.v.values, q_n)[1], d, days, alpha)}
    grid, nx, npv = local_level(tg, yg, g.v.values, q_n, -d)
    takes = moves.takes_nation(m)
    for race in sorted(set(p.race) - {"US"}):
        rp = p[p.race == race]
        t = rp.t.values.astype(float)
        nat = [effect(t, x.get("US", []), election) for x in (ps, pt)]
        own = [effect(t, x[race], election) for x in (ps, pt)] if race in ps else [0.0, 0.0]
        k = dials.get(race.split("-")[0], ku)
        with_nat = race not in ps or race in takes
        y = (rp.adj.values - k[0] * own[0] - k[1] * own[1] - (ku[0] * nat[0] + ku[1] * nat[1]) * with_nat
             - np.interp(t, grid, nx))
        out[race] = _flag(t, loglik(t, y, rp.v.values + np.interp(t, grid, npv), q_r)[1], d, days, alpha)
    return out


def _dial(x: dict) -> dict:
    return {"k_s": round(float(x["mean"][0]), 4), "k_t": round(float(x["mean"][1]), 4),
            "sd_s": round(float(np.sqrt(x["cov"][0][0])), 4), "sd_t": round(float(np.sqrt(x["cov"][1][1])), 4)}


def run(day: date, t: dict, m: dict, mp: dict, election=ELECTION) -> dict:
    """The week's update from every poll up to `day` (t: polls.build of the day's snapshot) and the day's moves.json
    (m), with the priors in move_params (mp): the fade speed, then the national dials, then each state's, then the
    surprise monitor. "polls_alone" is what each unit's polls say on their own, before pooling."""
    from .levels import inputs, poll_frame
    params, priors, *_ = inputs()
    p = poll_frame(t["senate"], t["generic_ballot"], params, priors, day, election, t["entries"])[0]
    d, prior, center = (election - day).days, mp["dial_prior"], mp["age_half_life_prior"]
    fade = fade_grid(p, m, params, d, prior, [round(center * 2 ** e, 2) for e in (-1, -0.5, 0, 0.5, 1)], election,
                     center)
    h = fade["half_life"]
    us = tuple(state_dial(pool(units(p, m, params, d, election, h_age=h), prior), "US", prior)["mean"])
    u = units(p, m, params, d, election, dials_us=us, h_age=h)
    post = pool(u, prior)
    alone = {}
    for name, (a, b, _) in u.items():
        cov = np.linalg.pinv(a)
        alone[name] = {"k": [round(float(v), 3) for v in cov @ b],
                       "se": [round(float(np.sqrt(max(v, 0))), 3) if v > 0 else None for v in np.diag(cov)]}
    means = {name: tuple(x["mean"]) for name, x in post["units"].items()}
    return {"polls": {"n": int(len(p)), "first": str(p.mid.min()), "last": str(p.mid.max())}, "prior": prior,
            "fade": fade, "posterior": {k: post[k] for k in ("labels", "mean", "cov", "log_evidence")},
            "dials": {name: _dial(x) for name, x in post["units"].items()} | {"default": _dial(post["national"])},
            "polls_alone": alone,
            "surprises": surprises(p, m, params, d, means | {"US": means.get("US", us)}, election, h_age=h)}


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
