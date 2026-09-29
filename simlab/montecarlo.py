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
HOUSE_MAJORITY = 218
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


def draw(mu: np.ndarray, sd: np.ndarray, c: np.ndarray, n: int, seed: int, df: int = DF,
         first: int | None = None) -> np.ndarray:
    """Multivariate Student-t: one shared scale per draw, so an extreme year is extreme everywhere. The scale is set so
    each race keeps its SD; only the tails fatten. With `first`, the races after the first `first` (House seats) are
    drawn given those (the Senate's), which keep the random numbers of a draw of them alone."""
    rng = np.random.default_rng(seed)
    k = len(mu) if first is None else first
    z = rng.standard_normal((n, k))
    s = np.sqrt((df - 2) / rng.chisquare(df, n))
    low = np.linalg.cholesky(c[:k, :k])
    y = z @ low.T
    if k < len(mu):
        b = np.linalg.solve(low, c[:k, k:]).T
        w, v = np.linalg.eigh(c[k:, k:] - b @ b.T)
        own = np.random.default_rng([seed, 2]).standard_normal((n, len(mu) - k))
        y = np.hstack([y, z @ b.T + own @ (v * np.sqrt(np.maximum(w, 0.0))).T])
    return mu + s[:, None] * y * sd


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


def house_seats(x: np.ndarray, left: list[str], fixed: dict) -> dict:
    """Seats per draw: uncontested seats plus contested seats won. The left candidate is a Democrat or, where none
    runs, another challenger (O)."""
    won, left = x > 0, np.array(left)
    return {"D": fixed.get("D", 0) + (won & (left == "D")).sum(axis=1), "O": (won & (left == "O")).sum(axis=1),
            "R": fixed.get("R", 0) + (~won).sum(axis=1)}


def house_summary(seats: dict, majority: int = HOUSE_MAJORITY) -> dict:
    return {"p_d_majority": round(float(np.mean(seats["D"] >= majority)), 4),
            "p_r_majority": round(float(np.mean(seats["R"] >= majority)), 4), "majority": majority,
            "seats": {k: _dist(v) for k, v in seats.items()}}


def senate_summary(seats: dict, not_up: dict) -> dict:
    """Control (D3): Republicans hold 50+ (the Vice President breaks ties); the second line counts only the
    independents not up (King, Sanders) as caucusing with Democrats. New independents are shown on their own
    (Matteo, 28 Sep); in the remaining elections they hold the balance."""
    r, d = seats["R"] >= 50, seats["D"] + not_up["I"] >= 51
    return {"p_r_50plus": round(float(np.mean(r)), 4), "p_d_caucus_51": round(float(np.mean(d)), 4),
            "p_independents_decide": round(float(np.mean(~r & ~d)), 4),
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


def _simulate(lv: dict, ids: list[str], params: dict, n: int, seed: int, df: int, lo: float,
              seats: list[str] = (), house: dict | None = None) -> tuple[np.ndarray, int]:
    """The races' draws, then the House seats' given them. A seat's sd leaves out the national error (house.py), so it
    is added here. The floor applies among the Senate races: lifting the House's many low pairs breaks the matrix."""
    nv, seats = lv["national"]["var"], list(seats)
    mu = np.array([lv["races"][r]["margin"] for r in ids] + [house["races"][r]["margin"] for r in seats])
    sd = np.array([lv["races"][r]["sd"] for r in ids] + [np.hypot(house["races"][r]["sd"], np.sqrt(nv)) for r in seats])
    c = structure(ids + seats, sd, nv, params["mc"]["regional_sd"], params["mc"]["state_sd"])
    c[:len(ids), :len(ids)], lifted = floor(c[:len(ids), :len(ids)], lo)
    return draw(mu, sd, c, n, seed, df, first=len(ids)), lifted


def story_noise(stories: dict, ids: list[str], sd: float, n: int, seed: int) -> np.ndarray:
    """Each story's strength drawn once per simulated election (sd relative to its effect) and applied to its effect in
    every race it touches ({race: {story: effect}}): a national story's draw is shared by all its races, a race
    story's is its own race's (Matteo, 29 Sep)."""
    ev = sorted({e for r in ids for e in stories.get(r, {})})
    if not ev or not sd:
        return np.zeros((n, len(ids)))
    effects = np.array([[stories.get(r, {}).get(e, 0.0) for r in ids] for e in ev])
    return (np.random.default_rng([seed, 3]).standard_normal((n, len(ev))) * sd) @ effects


def _dials(news: dict, units: list[str], n: int, seed: int) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Per race, the dials' posterior mean and a draw per simulated election: the national dials plus the unit's
    deviation, drawn jointly from the weekly filter's posterior; a unit it hasn't seen gets its deviation from the
    prior spread tau. Returns (mean per race, draws [n, race, part], national mean, national sd)."""
    post, tau = news["posterior"], np.array(news["tau"], float)
    mean, cov = np.array(post["mean"], float), np.array(post["cov"], float)
    rng = np.random.default_rng(seed)
    theta = rng.multivariate_normal(mean, cov, n)
    extra = {u: rng.standard_normal((n, 2)) * tau for u in sorted(set(units) - set(post["labels"][1:]))}
    col = {u: 2 + 2 * i for i, u in enumerate(post["labels"][1:])}
    dev = lambda u: theta[:, col[u]:col[u] + 2] if u in col else extra[u]
    dev_mean = lambda u: mean[col[u]:col[u] + 2] if u in col else np.zeros(2)
    k_hat = np.array([mean[:2] + dev_mean(u) for u in units])
    k_draw = np.stack([theta[:, :2] + dev(u) for u in units], axis=1)
    return k_hat, k_draw, mean[:2], np.sqrt(np.diag(cov)[:2])


def build(head: dict, twin: dict, left: dict, params: dict, day: date, run_id: str, benchmarks: dict | None = None,
          not_up: dict = NOT_UP, n: int = N_DRAWS, every: int = EVERY, df: int = DF, lo: float = FLOOR,
          movers: dict | None = None, news: dict | None = None, house: dict | None = None) -> tuple[dict, dict]:
    """forecast.json and draws.json from the headline levels and the stats-only twin's, on the same random numbers.
    The poll-average benchmark is the twin's, which has no story effects in it.

    `news` holds each race's story effect at dial 1, split into its switching and turnout parts: from its own
    stories ({"switching": {race_id: points}, "turnout": {...}}), whose dials are its unit's ("unit": {race_id:
    state}), and from the nation's ("switching_us", "turnout_us"), whose dials are the nation's; and
    the weekly filter's posterior of the dials ("posterior": {labels, mean, cov}, "tau"). Every simulated election
    draws its own dials, so the forecast is not tied to the fitted sizes and races with strong simulated reactions get
    wider, story-driven tails. Each race also reports its win chance with the national dials at their 10th and 90th
    percentiles. With "stories" ({race_id: {story: effect}}) and "story_sd", each story's strength is also drawn per
    election (story_noise): the news uncertainty has three layers, the overall scale (national dial), each state's
    sensitivity (its deviation) and each story's strength.

    `house` ({"levels": house_levels.json, "left": {seat: "D" or "O"}}) adds the House: its contested seats are drawn
    with the Senate's national, regional and state errors, and the seat totals give the majority (218). The seats take
    no news yet, so the headline and the twin share their levels."""
    ids, seed, bm, movers = sorted(head["races"]), seed_for(day), benchmarks or {}, movers or {}
    hv = house["levels"]["races"] if house else {}
    hid = sorted(r for r, v in hv.items() if not v.get("fixed"))
    x, lifted = _simulate(head, ids, params, n, seed, df, lo, hid, house and house["levels"])
    xt, _ = _simulate(twin, ids, params, n, seed, df, lo, hid, house and house["levels"])
    (x, xh), (xt, xth) = np.hsplit(x, [len(ids)]), np.hsplit(xt, [len(ids)])
    parties = [left[r] for r in ids]
    if news:
        x = x + story_noise(news.get("stories", {}), ids, news.get("story_sd", 0.0), n, seed)
        part = lambda k: np.array([news.get(k, {}).get(r, 0.0) for r in ids])
        ds, dt, us, ut = part("switching"), part("turnout"), part("switching_us"), part("turnout_us")
        k_hat, k_draw, nat, nat_sd = _dials(news, [news["unit"].get(r, "US") for r in ids] + ["US"], n, seed + 1)
        own_hat, own, us_hat, usd = k_hat[:-1], k_draw[:, :-1], k_hat[-1], k_draw[:, -1]
        at = {q: {"s": float(nat[0] + z * nat_sd[0]), "t": float(nat[1] + z * nat_sd[1])}
              for q, z in (("if_weaker", -1.2816), ("if_stronger", 1.2816))}
        fixed = {q: x + (m["s"] - nat[0]) * (ds + us) + (m["t"] - nat[1]) * (dt + ut) for q, m in at.items()}
        x = (x + (own[:, :, 0] - own_hat[:, 0]) * ds + (own[:, :, 1] - own_hat[:, 1]) * dt
             + np.outer(usd[:, 0] - us_hat[0], us) + np.outer(usd[:, 1] - us_hat[1], ut))
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
        if news:
            hs, ht = own_hat[i, 0] * ds[i] + us_hat[0] * us[i], own_hat[i, 1] * dt[i] + us_hat[1] * ut[i]
            races[r]["news"] = {"effect": round(float(hs + ht), 3), "switching": round(float(hs), 3),
                                "turnout": round(float(ht), 3)} | {
                q: {"multipliers": {k: round(v, 3) for k, v in m.items()},
                    "p_dem_win": round(float(np.mean(fixed[q][:, i] > 0)), 4)} for q, m in at.items()}
    twin_senate = senate_summary(seats_t, not_up)
    senate = senate_summary(seats, not_up) | {"stats_only": {k: v for k, v in twin_senate.items() if k.startswith("p_")},
                                              "benchmarks": {"market": bm.get("US-S", {}).get("market")}}
    if news:
        senate["news"] = {q: senate_summary(senate_seats(fixed[q], parties, not_up), not_up)["p_r_50plus"] for q in at}
    house_out = hseats = hseats_t = None
    if house:
        fixed_seats = {}
        for v in hv.values():
            if v.get("fixed"):
                fixed_seats[v["fixed"]] = fixed_seats.get(v["fixed"], 0) + 1
        hl = [house["left"].get(r, "D") for r in hid]
        hseats, hseats_t = house_seats(xh, hl, fixed_seats), house_seats(xth, hl, fixed_seats)
        house_out = house_summary(hseats) | {
            "stats_only": {k: v for k, v in house_summary(hseats_t).items() if k.startswith("p_")},
            "benchmarks": {"market": bm.get("US-H", {}).get("market")}, "contested": len(hid), "fixed": fixed_seats,
            "races": {r: race_summary(xh[:, i]) | {"tier": hv[r].get("tier")} for i, r in enumerate(hid)}}
    meta = {"date": str(day), "run_id": run_id, "schema": SCHEMA, "units": UNITS, "seed": seed}
    forecast = meta | {"draws": n, "df": df, "corr_floor": lo, "floor_lifted_pairs": lifted, "races": races,
                       "senate": senate, "house": house_out} | (
        {"news_dials": {"national": {"mean": [round(v, 4) for v in nat], "sd": [round(v, 4) for v in nat_sd]},
                        "tau": news["tau"]}} if news else {})
    keep = slice(None, None, every)
    sim = [i for i, r in enumerate(hid) if hv[r].get("tier") == "simulate"]

    def sample(xx, ss, xxh, hs):
        out = {"races": {r: np.round(xx[keep, i], 1).tolist() for i, r in enumerate(ids)},
               "seats": {"senate": {k: v[keep].tolist() for k, v in ss.items()}}}
        if hs:
            out["seats"]["house"] = {k: v[keep].tolist() for k, v in hs.items()}
            out["house_races"] = {hid[i]: np.round(xxh[keep, i], 1).tolist() for i in sim}
        return out

    draws = meta | {"every": every} | sample(x, seats, xh, hseats) | {"stats_only": sample(xt, seats_t, xth, hseats_t)}
    return forecast, draws


def attach_today(forecast: dict, today: dict, movers: dict | None = None) -> dict:
    """Adds the "if the election were today" view (a build with election day set to today: no drift, stories at
    today's strength) beside each race's and the Senate's 3 Nov numbers (Matteo, 29 Sep), with the stories that moved
    today's margin most."""
    for r, x in forecast["races"].items():
        t = today["races"][r]
        x["today"] = {"p_dem_win": t["p_dem_win"], "margin": t["margin"], "stats_only": t["stats_only"],
                      "movers": (movers or {}).get(r, [])}
    keys = ("p_r_50plus", "p_d_caucus_51", "p_independents_decide")
    forecast["senate"]["today"] = {k: today["senate"][k] for k in keys} | {"stats_only": today["senate"]["stats_only"]}
    if forecast.get("house") and today.get("house"):
        forecast["house"]["today"] = {k: today["house"][k] for k in ("p_d_majority", "p_r_majority")} | {
            "stats_only": today["house"]["stats_only"]}
    return forecast
