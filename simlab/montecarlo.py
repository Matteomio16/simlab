"""Monte Carlo: correlated simulated elections from the day's levels (stats-groundwork §5.8, engine-design §3.3 and §7).

Each race's election-day margin is its level plus national, census-division, state and race-only errors, drawn as a
multivariate Student-t. `build` returns forecast.json and draws.json; `python -m simlab.statsday` writes them.
"""
from __future__ import annotations

import re
from datetime import date

import numpy as np

from .calib import DIVISION
from .polls import STATE_CODES, STATE_NAMES, Race, _section, slug, surname

N_DRAWS, EVERY, DF, FLOOR = 40_000, 40, 8, 0.25
NOT_UP = {"R": 31, "D": 32, "I": 2}  # seats not up in 2026 (overview page, 28 Sep); I = King and Sanders
SCHEMA = 1
UNITS = "two-party margin, D (or independent challenger) minus R, points"


def state_of(race_id: str) -> str:
    return race_id.split("-")[0]


def structure(ids: list[str], sd: np.ndarray, national_var: float, regional_sd: float, state_sd: float) -> np.ndarray:
    """Correlations implied by errors shared nationally, by census division and by state; the race-only error takes
    the rest of each race's variance (at least 1, so the matrix stays invertible)."""
    st = np.array([state_of(r) for r in ids])
    div = np.array([DIVISION[s] for s in st])
    cov = national_var + regional_sd ** 2 * (div[:, None] == div[None, :]) + state_sd ** 2 * (st[:, None] == st[None, :])
    shared = national_var + regional_sd ** 2 + state_sd ** 2
    np.fill_diagonal(cov, shared + np.maximum(sd ** 2 - shared, 1.0))
    d = np.sqrt(np.diag(cov))
    return cov / d[:, None] / d[None, :]


def floor(c: np.ndarray, lo: float = FLOOR, iters: int = 500) -> tuple[np.ndarray, int]:
    """Lifts correlations below `lo`; if that breaks validity, alternates with eigenvalue clipping until both hold.
    Returns the matrix and the number of pairs lifted."""
    off = ~np.eye(len(c), dtype=bool)
    lifted = int((c[off] < lo).sum()) // 2
    if not lifted:
        return c, 0
    x = c.copy()
    for _ in range(iters):
        x[off] = np.maximum(x[off], lo)
        w, v = np.linalg.eigh(x)
        if w.min() >= -1e-12:
            break
        x = (v * np.maximum(w, 1e-8)) @ v.T
        d = np.sqrt(np.diag(x))
        x = x / d[:, None] / d[None, :]
    return x, lifted


def draw(mu: np.ndarray, sd: np.ndarray, c: np.ndarray, n: int, seed: int, df: int = DF) -> np.ndarray:
    """Multivariate Student-t: one shared scale per draw, so an extreme year is extreme everywhere. The scale is set so
    each race keeps its SD; only the tails fatten."""
    rng = np.random.default_rng(seed)
    z = rng.standard_normal((n, len(mu)))
    s = np.sqrt((df - 2) / rng.chisquare(df, n))
    return mu + s[:, None] * (z @ np.linalg.cholesky(c).T) * sd


def seed_for(day: date) -> int:
    return int(day.strftime("%Y%m%d"))


def race_summary(x: np.ndarray) -> dict:
    p10, p50, p90 = np.percentile(x, [10, 50, 90])
    return {"p_dem_win": round(float(np.mean(x > 0)), 4),
            "margin": {"p10": round(float(p10), 2), "p50": round(float(p50), 2), "p90": round(float(p90), 2)}}


def senate_seats(x: np.ndarray, left: list[str], not_up: dict) -> dict:
    """Seats per draw: those not up plus races won. The challenger wins a race when the margin is above 0."""
    won, left = x > 0, np.array(left)
    return {"R": not_up["R"] + (~won).sum(axis=1), "D": not_up["D"] + (won & (left == "D")).sum(axis=1),
            "I": not_up["I"] + (won & (left == "I")).sum(axis=1)}


def _dist(v: np.ndarray) -> dict:
    k, c = np.unique(v, return_counts=True)
    p10, p50, p90 = np.percentile(v, [10, 50, 90])
    return {"mean": round(float(v.mean()), 2), "p10": float(p10), "p50": float(p50), "p90": float(p90),
            "dist": {str(int(a)): round(b / len(v), 4) for a, b in zip(k, c)}}


def senate_summary(seats: dict, not_up: dict) -> dict:
    """Control (D3): Republicans hold 50+ (the Vice President breaks ties); the second line counts only the
    independents not up (King, Sanders) as caucusing with Democrats. New independents are shown on their own."""
    return {"p_r_50plus": round(float(np.mean(seats["R"] >= 50)), 4),
            "p_d_caucus_51": round(float(np.mean(seats["D"] + not_up["I"] >= 51)), 4),
            "seats": {k: _dist(v) for k, v in seats.items()}, "not_up": dict(not_up)}


def cook(overview: str) -> dict:
    """Cook Political Report ratings from the overview page's predictions table: a benchmark, never an input (D2)."""
    span = _section(overview, "Predictions", 2)
    out = {}
    for row in re.split(r"\n\|-", overview[span[0]:span[1]] if span else ""):
        m = re.search(r"^!\s*\[\[2026 United States Senate (special )?election in ([^|\]]+)\|", row, re.M)
        r = re.search(r"<!--\s*Cook\s*-->\s*\|\s*\{\{USRaceRating\|([^}]*)\}\}", row)
        if m and r and m.group(2).strip() in STATE_CODES:
            parts = [p for p in r.group(1).split("|") if p.lower() != "flip"]
            out[STATE_CODES[m.group(2).strip()] + ("-S" if m.group(1) else "")] = " ".join(parts[:2])
    return out


def _mid(bid, ask) -> float:
    return (float(bid or 0.0) + float(ask or 0.0)) / 2


def _share(titles: list[str], tags: list[str], mids: list[float], name: str, fallback) -> float | None:
    """Price of the market whose title names `name` (else whose tag passes `fallback`), over all the event's markets."""
    hit = [i for i, t in enumerate(titles) if name in t.lower()] or [i for i, g in enumerate(tags) if fallback(g)]
    return round(mids[hit[0]] / sum(mids), 4) if hit and sum(mids) > 0 else None


def _kalshi(k: dict, key: str, year: str, name: str, fallback) -> float | None:
    ev = [e for e in k.get(key, {}).get("events", []) if str(e.get("event_ticker", "")).endswith(year)]
    ms = [m for m in ev[0].get("markets", []) if m.get("status") == "active"] if ev else []
    return _share([m.get("yes_sub_title", "") for m in ms], [m["ticker"].rsplit("-", 1)[-1] for m in ms],
                  [_mid(m.get("yes_bid_dollars"), m.get("yes_ask_dollars")) for m in ms], name, fallback)


def _poly(p: dict, prefix: str, name: str, fallback) -> float | None:
    key = next((k for k in p if k.startswith(prefix)), None)
    ms = [m for m in p[key][0].get("markets", []) if m.get("active") and not m.get("closed")] if key and p[key] else []
    titles = [m.get("groupItemTitle", "").strip() for m in ms]
    return _share(titles, titles, [_mid(m.get("bestBid"), m.get("bestAsk")) for m in ms], name, fallback)


def _average(venues: dict) -> tuple[float | None, dict]:
    venues = {k: v for k, v in venues.items() if v is not None}
    return (round(float(np.mean(list(venues.values()))), 4) if venues else None), venues


def market(kalshi: dict, poly: dict, race: Race) -> tuple[float | None, dict]:
    """The challenger's win price on Kalshi and Polymarket: bid-ask midpoints, normalised over the race's candidates,
    then averaged over the venues. A benchmark only: prediction markets never enter the numbers."""
    name, side = surname(race.left).lower(), race.left_party
    label = {"D": ("(D)", "Democrat"), "I": ("(I)", "Independent")}[side]
    return _average({
        "kalshi": _kalshi(kalshi, f"SENATE{race.state}{'S' if race.special else ''}", "-26", name,
                          lambda g: g == "D" if side == "D" else g.startswith("I")),
        "polymarket": _poly(poly, f"{slug(STATE_NAMES[race.state])}-senate-election-winner", name,
                            lambda g: g.endswith(label[0]) or g == label[1])})


def control_market(kalshi: dict, poly: dict, chamber: str = "senate") -> tuple[float | None, dict]:
    """Republican control price for a chamber, the market benchmark for p_r_50plus."""
    return _average({
        "kalshi": _kalshi(kalshi, {"senate": "CONTROLS", "house": "CONTROLH"}[chamber], "-2026", "republican",
                          lambda g: g == "R"),
        "polymarket": _poly(poly, f"which-party-will-win-the-{chamber}-in-2026", "republican", lambda g: False)})


def _simulate(lv: dict, ids: list[str], params: dict, n: int, seed: int, df: int, lo: float) -> tuple[np.ndarray, int]:
    mu = np.array([lv["races"][r]["margin"] for r in ids])
    sd = np.array([lv["races"][r]["sd"] for r in ids])
    c = structure(ids, sd, lv["national"]["var"], params["mc"]["regional_sd"], params["mc"]["state_sd"])
    c, lifted = floor(c, lo)
    return draw(mu, sd, c, n, seed, df), lifted


def build(head: dict, twin: dict, left: dict, params: dict, day: date, run_id: str, benchmarks: dict | None = None,
          not_up: dict = NOT_UP, n: int = N_DRAWS, every: int = EVERY, df: int = DF, lo: float = FLOOR,
          movers: dict | None = None) -> tuple[dict, dict]:
    """forecast.json and draws.json from the headline levels and the stats-only twin's, on the same random numbers.
    The poll-average benchmark is the twin's, which has no story effects in it."""
    ids, seed, bm, movers = sorted(head["races"]), seed_for(day), benchmarks or {}, movers or {}
    x, lifted = _simulate(head, ids, params, n, seed, df, lo)
    xt, _ = _simulate(twin, ids, params, n, seed, df, lo)
    parties = [left[r] for r in ids]
    seats, seats_t = senate_seats(x, parties, not_up), senate_seats(xt, parties, not_up)
    races = {}
    for i, r in enumerate(ids):
        lv, b = head["races"][r], bm.get(r, {})
        poll = twin["races"][r].get("poll_margin")
        races[r] = {**race_summary(x[:, i]), "stats_only": race_summary(xt[:, i]), "left_party": left[r],
                    "w_polls": round(float(lv.get("w_polls", 0.0)), 3),
                    "benchmarks": {"poll_avg": None if poll is None else round(float(poll), 2),
                                   "market": b.get("market"), "cook": b.get("cook")},
                    "movers": movers.get(r, [])}
    twin_senate = senate_summary(seats_t, not_up)
    senate = senate_summary(seats, not_up) | {"stats_only": {k: v for k, v in twin_senate.items() if k.startswith("p_")},
                                              "benchmarks": {"market": bm.get("US-S", {}).get("market")}}
    meta = {"date": str(day), "run_id": run_id, "schema": SCHEMA, "units": UNITS, "seed": seed}
    forecast = meta | {"draws": n, "df": df, "corr_floor": lo, "floor_lifted_pairs": lifted, "races": races,
                       "senate": senate, "house": None}
    keep = slice(None, None, every)
    sample = lambda xx, ss: {"races": {r: np.round(xx[keep, i], 1).tolist() for i, r in enumerate(ids)},
                             "seats": {"senate": {k: v[keep].tolist() for k, v in ss.items()}}}
    draws = meta | {"every": every} | sample(x, seats) | {"stats_only": sample(xt, seats_t)}
    return forecast, draws
