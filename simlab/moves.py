"""Moves: voter-group reactions to the day's stories -> each race's move (engine-design §3.2, stats-groundwork §5.5).

    python -m simlab.moves --fit      fits c_s on the events2 calibration and writes simlab/move_params.json

For every story that reached a race, GLM's group reactions (support and turnout, -2..+2) become group changes, capped
at the persuadable and mobilisable shares, then a race move. A story counts once, from the day it was first seen, and
fades with its half-life. Kev's shadow rows get the same arithmetic under "shadow" and never move the forecast.
"""
from __future__ import annotations

import argparse
import json
from datetime import date, datetime, timedelta
from pathlib import Path

import numpy as np
from scipy.optimize import minimize_scalar

HERE = Path(__file__).parent
PARAMS = HERE / "move_params.json"
LOOKBACK = 60
SCHEMA = 1
UNITS = "delta_margin and by_event in points of two-party margin (D or independent challenger minus R); " \
        "delta_turnout in percentage points; by_group dd in points of the group's margin, dt in turnout points"


def group_change(r_s: float, r_t: float, pi: float, mu: float, a: float, c_s: float, c_t: float,
                 k_s: float = 1.0, k_t: float = 1.0) -> tuple[float, float]:
    """(change in the group's D-minus-R margin, change in its turnout), both as fractions."""
    return (2 * pi * float(np.clip(c_s * k_s * r_s / 2, -1, 1)) * a,
            mu * float(np.clip(c_t * k_t * r_t / 2, -1, 1)) * a)


def race_move(groups: dict, dd: dict, dt: dict) -> float:
    """Switching plus the turnout mix: sum e_g dd_g + sum e_g (dt_g / t_g)(d_g - m), e_g = n_g t_g / sum n t."""
    e = {g: v["n"] * v["t"] for g, v in groups.items()}
    tot = sum(e.values())
    m = sum(e[g] * groups[g]["d"] for g in groups) / tot
    return sum(e[g] / tot * (dd.get(g, 0.0) + dt.get(g, 0.0) / groups[g]["t"] * (groups[g]["d"] - m))
               for g in groups)


def decay(days: float, half_life: float) -> float:
    return 0.0 if days < 0 else 0.5 ** (days / half_life)


def fit_cs(rows: list[dict], pimu: dict) -> dict:
    """c_s from real events with measured national shifts (points toward D): each event's predicted shift is the
    §3.2 switching term over the national groups (attention 1), fitted by weighted least squares with the measured
    shift's standard error (|shift / z|, at least 0.1)."""
    ev = {}
    for r in rows:
        ev.setdefault(r["event_id"], []).append(r)
    ids = sorted(ev)
    shift = np.array([ev[e][0]["measured_shift_toward_D"] for e in ids])
    se = np.array([max(abs(ev[e][0]["measured_shift_toward_D"] / ev[e][0]["z"]) if ev[e][0]["z"] else 1.0, 0.1)
                   for e in ids])

    def predict(c):
        out = []
        for e in ids:
            w = np.array([r["weight"] for r in ev[e]])
            dd = np.array([group_change(r["support"], 0.0, pimu[r["group"]]["pi"], 0.0, 1.0, c, 0.0)[0] for r in ev[e]])
            out.append(100 * float(np.dot(w, dd) / w.sum()))
        return np.array(out)

    c = minimize_scalar(lambda c: float(np.sum(((shift - predict(c)) / se) ** 2)), bounds=(0, 5), method="bounded",
                        options={"xatol": 1e-6}).x
    p = predict(c)
    return {"c_s": round(float(c), 4), "events": len(ids), "rmse": round(float(np.sqrt(np.mean((shift - p) ** 2))), 3),
            "corr": round(float(np.corrcoef(shift, p)[0, 1]), 3)}


def _jsonl(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()] if path.exists() else []


def _history(day: date, derived: Path) -> tuple[dict, dict]:
    """Reactions asked in the last LOOKBACK days, earliest answer per (model, race, event, group), with the day asked;
    and the latest record of every event up to `day`."""
    reactions, events = {}, {}
    for k in range(LOOKBACK, -1, -1):
        d = day - timedelta(days=k)
        folder = derived / d.isoformat()
        for r in _jsonl(folder / "reactions.jsonl"):
            if not r.get("parse_error"):
                reactions.setdefault((r["model"], bool(r.get("shadow")), r["race_id"], r["event_id"], r["group"]),
                                     (r, d))
        for e in _jsonl(folder / "events.jsonl"):
            events[e["event_id"]] = e
    return reactions, events


def _race(race: str, rows: dict, events: dict, groups: dict, params: dict, day: date) -> dict:
    """One race's moves from its reactions {event_id: {group: (row, day asked)}}."""
    state = race.split("-")[0]
    dial = params.get("dials", {}).get(state, {})
    hl = params["half_life_days"]
    by_event, by_effect, info, by_group = {}, {}, {}, {g: {"dd": 0.0, "dt": 0.0} for g in groups}
    delta = delta_base = delta_t = 0.0
    for eid, answers in sorted(rows.items()):
        e = events.get(eid)
        if e is None:
            continue
        first = datetime.fromisoformat(e["first_seen"]).date()
        asked = min(d for _, d in answers.values())
        tau, h, a = (day - first).days, hl.get(e.get("type"), hl["default"]), float(e.get("attention", {}).get("a", 0.0))
        known = 1.0 if asked < day else 0.0
        step = decay(tau, h) - known * decay(tau - 1, h)
        full = {}
        for base, (ks, kt) in (("dials", (dial.get("k_s", 1.0), dial.get("k_t", 1.0))), ("base", (1.0, 1.0))):
            ch = {g: group_change(r["support"], r["turnout"], groups[g]["pi"], groups[g]["mu"], a, params["c_s"],
                                  params["c_t"], ks, kt) for g, (r, _) in answers.items() if g in groups}
            dd, dt = {g: c[0] for g, c in ch.items()}, {g: c[1] for g, c in ch.items()}
            full[base] = (100 * race_move(groups, dd, dt), 100 * sum(groups[g]["n"] * dt[g] for g in dt), dd, dt)
        m, turnout, dd, dt = full["dials"]
        by_event[eid] = round(m * step, 4)
        by_effect[eid] = round(m * decay(tau, h), 4)
        delta += m * step
        delta_base += full["base"][0] * step
        delta_t += turnout * step
        for g in dd:
            by_group[g]["dd"] += 100 * dd[g] * decay(tau, h)
            by_group[g]["dt"] += 100 * dt[g] * decay(tau, h)
        fs, ft = round(100 * race_move(groups, dd, {}), 4), round(100 * race_move(groups, {}, dt), 4)
        info[eid] = {"first_seen": first.isoformat(), "half_life": h, "a": a, "full": round(fs + ft, 4), "full_s": fs,
                     "full_t": ft, "full_base": round(full["base"][0], 4), "card": e.get("card", "")}
    return {"delta_margin": round(delta, 4), "delta_margin_base": round(delta_base, 4),
            "delta_turnout": round(delta_t, 4),
            "by_group": {g: {k: round(v, 4) for k, v in x.items()} for g, x in by_group.items()},
            "by_event": by_event, "by_event_effect": by_effect, "events": info}


def build(day: date, derived: Path, groups: dict, params: dict, run_id: str) -> dict:
    """moves.json (engine-design §7) for every race in groups.json (and US), GLM's rows in the main block and shadow
    rows (Kev) under "shadow"."""
    reactions, events = _history(day, derived)
    races = [k for k in groups if isinstance(groups[k], dict) and k not in ("units",)]
    out = {"date": day.isoformat(), "run_id": run_id, "schema": SCHEMA, "units": UNITS,
           "params": {k: params[k] for k in ("c_s", "c_t")}, "shadow": {}}
    for shadow in (False, True):
        by_race = {}
        for (model, sh, race, eid, g), v in reactions.items():
            if sh == shadow:
                by_race.setdefault(race, {}).setdefault(eid, {})[g] = v
        dest = out["shadow"] if shadow else out
        for race in races:
            if shadow and race not in by_race:
                continue
            dest[race] = _race(race, by_race.get(race, {}), events, groups[race], params, day)
    return out


def paths(m: dict, part: str = "all") -> dict:
    """{race_id or "US": [(first_seen, full effect, half-life)]} from moves.json's main block, for levels.build: the
    whole effect, or only its switching ("s") or turnout ("t") part."""
    key = {"all": "full", "s": "full_s", "t": "full_t"}[part]
    return {r: [(v["first_seen"], v[key], v["half_life"]) for v in x["events"].values()]
            for r, x in m.items() if r != "shadow" and isinstance(x, dict) and "events" in x}


def movers(m: dict, top: int = 5, least: float = 0.01) -> dict:
    """forecast.json movers: each race's stories with the largest effect so far (points), largest first."""
    out = {}
    for r, x in m.items():
        if r in ("US", "shadow") or not isinstance(x, dict) or "by_event_effect" not in x:
            continue
        ranked = sorted(x["by_event_effect"].items(), key=lambda kv: -abs(kv[1]))[:top]
        out[r] = [{"event_id": e, "card": x["events"][e]["card"], "delta": round(v, 2)} for e, v in ranked
                  if abs(v) >= least]
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fit", action="store_true", help="fit c_s on runs/events2_groups__glm.jsonl")
    a = ap.parse_args()
    if not a.fit:
        ap.error("nothing to do (use --fit)")
    from .core import RUNS
    rows = [r for r in _jsonl(RUNS / "events2_groups__glm.jsonl") if not r.get("parse_error")]
    pimu = json.loads((HERE / "pimu.json").read_text(encoding="utf-8"))["national"]
    fit = fit_cs(rows, pimu)
    params = json.loads(PARAMS.read_text(encoding="utf-8")) if PARAMS.exists() else {}
    params |= {"c_s": fit["c_s"], "fit": fit | {"on": "runs/events2_groups__glm.jsonl (GLM, direct wording)",
                                                 "fitted": date.today().isoformat()}}
    PARAMS.write_text(json.dumps(params, indent=1), encoding="utf-8")
    print(json.dumps(fit))


if __name__ == "__main__":
    main()
