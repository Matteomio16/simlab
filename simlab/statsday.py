"""Statistics step of the daily job: python -m simlab.statsday --date YYYY-MM-DD --data <path to simlab-data>

Reads the day's latest snapshot run before 09:30 UTC (or --snapshot HHMM) and writes to derived/<date>/: polls.csv, races.json,
levels.json, groups.json, forecast.json and draws.json (engine-design §7). From 14 Oct the headline follows the
simulation-only rule (docs/simulation-only.md): the frozen 12 Oct start plus the moves since (simlab.start), with the
stats-only twin on the day's polls as "polls alone", and a weekly check on Sundays (weekly_check.json). Earlier days,
or --rule poll-filter (with --out-root, to score it beside the published one), run the poll filter. Exits 1 on
failure; the last stdout line is a one-line JSON summary, which holds no forecast numbers.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import subprocess
import sys
import traceback
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

from . import groups, levels, montecarlo, moves, polls, weekly
from . import lockin
from . import start as frozen
from .polls import OVERVIEW_PAGE, Race, slug, surname

RCV = {"AK", "ME"}
SCHEMA = 1


CUTOFF = "0930"  # UTC, as simlab.newsday.CUTOFF: runs that start before it belong to that day's job


def snapshot_for(data: Path, day: date, hhmm: str | None = None) -> Path:
    """The run named `hhmm`, else the day's latest run that started before the news cutoff, so a re-run later in the
    day reads the same polls as the day's job (the latest run of the day if none came before)."""
    runs = sorted(p for p in (data / "snapshots" / day.isoformat()).glob("*") if p.is_dir())
    if hhmm:
        runs = [p for p in runs if p.name == hhmm]
    if not runs:
        raise FileNotFoundError(f"no snapshot run for {day}" + (f" at {hhmm}" if hhmm else ""))
    return ([p for p in runs if p.name < CUTOFF] or runs)[-1] if not hhmm else runs[-1]


def races_json(race_list: list[Race]) -> dict:
    return {r.race_id: {"state": r.state, "office": "senate", "district": None, "special": r.special,
                        "rcv": r.state in RCV, "candidates": {"left": r.left, "right": r.right},
                        "left_party": r.left_party, "incumbent_party": r.incumbent, "status": r.status}
            for r in race_list}


def poll_rows(senate: pd.DataFrame, gb: pd.DataFrame) -> pd.DataFrame:
    return pd.concat([senate, gb.assign(race_id="US")], ignore_index=True)


FIRST_SEEN_KEY = ["race_id", "pollster", "start", "end", "population"]


def first_seen(today: pd.DataFrame, prev: pd.DataFrame | None, stamp: str) -> pd.DataFrame:
    """Each poll row's first snapshot: carried from the last day's polls.csv, else this run's snapshot time."""
    key = lambda df: df[FIRST_SEEN_KEY].astype(str).agg("|".join, axis=1)
    seen = dict(zip(key(prev), prev.first_seen)) if prev is not None and "first_seen" in prev else {}
    return today.assign(first_seen=[seen.get(k, stamp) for k in key(today)])


def previous_polls(data: Path, day: date) -> pd.DataFrame | None:
    files = sorted(p for p in (data / "derived").glob("*/polls.csv") if p.parent.name < day.isoformat())
    return pd.read_csv(files[-1], low_memory=False) if files else None


PILOT = {"OH-S", "NC", "TX", "IA", "ME"}
TIER_RANK = {"statistics": 0, "watch": 1, "simulate": 2}


def tier(p_stats: float | None, cook: str | None, market: float | None) -> tuple[str, list[str]]:
    """Where the simulation runs (Matteo, 28 Sep): "simulate" (full), "watch" (the biggest stories only) or
    "statistics" (statistics and national news). A race runs on statistics alone only when all three signals call it
    safe, since a race that flips unsimulated would count against the simulation."""
    close = lambda p, lo: p is not None and lo <= p <= 1 - lo
    word = (cook or "").split(" ")[0]
    reasons = ([f"stats-only {p_stats:.0%}"] if close(p_stats, 0.10) else []) +               ([f"Cook {cook}"] if word in ("Tossup", "Tilt", "Lean") else []) +               ([f"market {market:.0%}"] if close(market, 0.10) else [])
    if reasons:
        return "simulate", reasons
    reasons = ([f"stats-only {p_stats:.0%}"] if close(p_stats, 0.03) else []) +               ([f"Cook {cook}"] if word == "Likely" else []) + ([f"market {market:.0%}"] if close(market, 0.05) else [])
    return ("watch", reasons) if reasons else ("statistics", ["all three signals call it safe"])


def tiers(races: dict, stats: dict, bench: dict, history: list[dict]) -> dict:
    """races.json rows with today's tier: pilot races always simulate; otherwise the most competitive tier of today
    and the last days in `history` (earlier races.json files), so a race doesn't drop out after one quiet day."""
    out = {}
    for rid, row in races.items():
        raw, why = tier(stats.get(rid), bench.get(rid, {}).get("cook"), bench.get(rid, {}).get("market"))
        past = [h[rid]["tier_raw"] for h in history if rid in h and "tier_raw" in h.get(rid, {})]
        best = max([raw, *past], key=TIER_RANK.get)
        if rid in PILOT:
            best, why = "simulate", ["pilot race"]
        elif best != raw:
            why = why + [f"kept from the last {len(history)} days"]
        out[rid] = row | {"tier": best, "tier_raw": raw, "tier_reasons": why}
    return out


def _read(path: Path):
    return json.loads(gzip.decompress(path.read_bytes())) if path.exists() else {}


def benchmarks(snap: Path, race_list: list[Race]) -> dict:
    """Market prices and Cook ratings as of the snapshot: shown beside the forecast, never used in it."""
    kalshi, poly = _read(snap / "markets" / "kalshi.gz"), _read(snap / "markets" / "polymarket.gz")
    overview = _read(snap / "wikipedia" / f"{slug(OVERVIEW_PAGE)}.gz")
    ratings = montecarlo.cook(overview["revisions"][0]["slots"]["main"]["content"]) if overview else {}
    out = {}
    for r in race_list:
        p, venues = montecarlo.market(kalshi, poly, r)
        out[r.race_id] = {"market": p, "market_venues": venues, "cook": ratings.get(r.race_id)}
    for key, chamber in (("US-S", "senate"), ("US-H", "house")):
        p, venues = montecarlo.control_market(kalshi, poly, chamber)
        out[key] = {"market": p, "market_venues": venues}
    return out


def latest_weekly(data: Path, day: date, roots: tuple = ("derived",)) -> dict | None:
    """The latest weekly filter update (<root>/<date>/filter_weekly.json) on or before `day`."""
    files = sorted((f for root in roots for f in (data / root).glob("*/filter_weekly.json")
                    if f.parent.name <= day.isoformat()), key=lambda f: f.parent.name)
    return json.loads(files[-1].read_text(encoding="utf-8")) if files else None


def apply_weekly(mp: dict, wk: dict | None) -> dict:
    """move_params with the weekly update's dials, fade speed and dial posterior; before the first update, the dials'
    posterior is their prior (national dials only, each state's deviation drawn from tau in the Monte Carlo)."""
    prior = mp["dial_prior"]
    post = wk["posterior"] if wk else {"labels": ["national"], "mean": list(prior["mean"]),
                                       "cov": [[prior["sd"][0] ** 2, 0.0], [0.0, prior["sd"][1] ** 2]]}
    out = mp | {"dial_posterior": post}
    if wk:
        out |= {"dials": wk["dials"], "age_half_life_days": wk["fade"]["half_life"], "weekly_update": wk["date"]}
        if wk.get("offset"):
            out["support_offset"] = wk["offset"]["offset"]
    return out


def _stories(mv: dict, when: str, drop: dict | None = None, lock: dict | None = None) -> dict:
    """{race_id: {story: effect}}: each story's effect on each race at its dials, on 3 Nov ("election_day") or today,
    for the story-strength draws. A race without its own stories takes the nation's, and a race with stories adds the
    nation's it takes (moves.nation_paths' rule). The effects leave out the offset that polls read net of the news
    give them, so the draws err on the wide side. A race's cancelled weeks (`drop`, start.cancelled) are left out.
    With `lock` (lockin.prepare), a story's 3 Nov effect is its full effect times its state's lock-in factor."""
    us, takes = mv.get("US", {}), moves.takes_nation(mv)
    value = (lambda x, e, v: v["election_day"]) if when == "election_day" else (
        lambda x, e, v: x.get("by_event_effect", {}).get(e, 0.0))
    out = {}
    for r, x in mv.items():
        if r in ("US", "shadow") or not isinstance(x, dict) or "events" not in x:
            continue
        src = [(x, e, v) for e, v in x["events"].items()]
        taken = set(x.get("nation_unasked", ())) if src and r not in takes else None
        src += [(us, e, v) for e, v in us.get("events", {}).items() if taken is None or e in taken]
        if (drop or {}).get(r):
            src = [s for s in src if frozen.kept([(s[2]["first_seen"],)], drop[r])]
        if lock and when == "election_day":
            g = lock["factors"][r.split("-")[0]]
            out[r] = {e: round(float(v["full"] * g.get(e, 0.0)), 4) for xx, e, v in src}
            continue
        out[r] = {e: round(float(value(xx, e, v)), 4) for xx, e, v in src}
    return out


def _levels(t: dict, day: date, run_id: str, mv: dict, inp: tuple, mp: dict, election: date = levels.ELECTION,
            hb: dict | None = None, start: tuple | None = None, drop: dict | None = None, lock: dict | None = None
            ) -> tuple[dict, dict, dict, dict | None]:
    """Stats-only and headline levels for one election day, and each race's story effect at dial 1 split four ways:
    switching and turnout, from its own stories (its state's dials) and from the nation's (the national dials). The
    headline is linear in the effects, so the parts times the dials must add up to it. With the House base `hb`
    (house.prepare), the seats get the same by house.build: {"twin", "levels"}, their parts joining `news`; a failure
    there returns {"error"} and leaves the Senate alone. With `start` (the frozen start's Senate and House levels for
    this election day, start.at), the headline is the start plus the moves since 12 Oct (start.headline, without the
    cancelled weeks in `drop`) and the parts are measured from the start; the stats-only twin still reads the day's
    polls. With `lock` (lockin.prepare, the 3 Nov view only) each story counts its full effect times its state's
    lock-in factor (early votes lock in, Matteo 26 Oct) instead of what is expected to remain on 3 Nov."""
    twin = levels.compute(t, day, run_id, inp=inp, election=election)
    zero = start[0] if start else twin
    run = (lambda p: frozen.headline(start[0], p, day, election, drop)) if start else (
        lambda p: levels.compute(t, day, run_id, moves=p, inp=inp, election=election))
    lock = lock if lock and start and election != day else None
    if lock:
        ps = lock["paths"]
        head = run(ps["all"])
        specs = {name: ps[name] for name in ("own_s", "own_t", "us_s", "us_t")}
        own = {k: {r: x for r, x in ps[f"own_{k}"].items() if r != "US" and (x or ps[f"own_{'t' if k == 's' else 's'}"][r])}
               for k in "st"}
    else:
        head = run(moves.paths(mv))
        own = {k: {r: x for r, x in moves.paths(mv, f"{k}_base", with_nation=False).items() if r != "US"} for k in "st"}
        nation = {k: moves.paths(mv, f"{k}_base").get("US", []) for k in "st"}
        taken = {k: moves.nation_paths(mv, f"{k}_base") for k in "st"}
        specs = {f"own_{k}": own[k] | {"US": []} for k in "st"} | {
            f"us_{k}": {"US": nation[k]} | {r: taken[k].get(r, []) for r in own[k]} for k in "st"}
    full = {name: run(p) for name, p in specs.items()}
    runs = {name: f["races"] for name, f in full.items()}
    part = lambda name: {r: runs[name][r]["margin"] - zero["races"][r]["margin"] for r in zero["races"]}
    news = {"switching": part("own_s"), "turnout": part("own_t"), "switching_us": part("us_s"),
            "turnout_us": part("us_t"), "unit": {r: r.split("-")[0] for r in own["s"]},
            "posterior": mp["dial_posterior"], "tau": mp["dial_prior"]["tau"],
            "stories": _stories(mv, "today" if election == day else "election_day", drop, lock),
            "story_sd": mp.get("story_sd", 0.0)}
    dials = mp.get("dials", {})
    k = lambda unit, x: dials.get(unit, dials.get("default", {})).get(f"k_{x}", 1.0)
    margins = lambda lv: {r: x["margin"] for r, x in lv["races"].items() if not x.get("fixed")}
    miss = lambda hd, tw: max(((abs(hd[r] - tw[r]
                                    - sum(k(news["unit"].get(r), x) * news[name][r]
                                          for x, name in (("s", "switching"), ("t", "turnout")))
                                    - sum(k("US", x) * news[name][r]
                                          for x, name in (("s", "switching_us"), ("t", "turnout_us")))), r) for r in tw),
                              default=(0.0, None))
    if (gap := miss(margins(head), margins(zero)))[0] > 1e-3:  # parts are rounded to 4 decimals: a clipped or broken dial
        raise ValueError(f"story effects don't add up across their parts (gap {gap[0]:.2e} at {gap[1]})")
    house = None
    if hb:
        try:  # the House (Kev session, house.build) must not stop the Senate forecast
            from .house import build as house_build
            h_twin = house_build(hb, twin, election=election)
            if start and not start[1]:
                raise ValueError("the start file has no House levels")
            hz = start[1] if start else h_twin
            hrun = (lambda p, lv: frozen.headline(hz, p, day, election, drop)) if start else (
                lambda p, lv: house_build(hb, lv, p, election))
            h = {"twin": h_twin, "levels": hrun(lock["paths"]["all"] if lock else moves.paths(mv), head)}
            hp, htw = {name: margins(hrun(p, full[name])) for name, p in specs.items()}, margins(hz)
            for key, name in (("switching", "own_s"), ("turnout", "own_t"), ("switching_us", "us_s"), ("turnout_us", "us_t")):
                news[key] |= {r: hp[name][r] - htw[r] for r in htw}
            if (gap := miss(margins(h["levels"]), htw))[0] > 1e-3:
                raise ValueError(f"House story effects don't add up across their parts (gap {gap[0]:.2e} at {gap[1]})")
            house = h
        except Exception as e:
            house = {"error": f"{type(e).__name__}: {e}"[:120]}
    return twin, head, news, house


def week_trend(data: Path, day: date, forecast: dict, out: Path) -> dict:
    """The weekly trend check (weekly.trend) against the forecast 7 days earlier, for the Senate and, under "house",
    the House seats (a House poll is new when last week's house_polls.csv lacks it), with the level check
    (weekly.far_from_polls). `out` is the day's folder. It only reports, so it never stops the forecast."""
    try:
        before = data / "derived" / (day - timedelta(days=7)).isoformat()
        read = lambda f: json.loads(f.read_text(encoding="utf-8")) if f.exists() else None
        table = lambda f: pd.read_csv(f, low_memory=False) if f.exists() else None
        polls, hp, prev = table(out / "polls.csv"), table(out / "house_polls.csv"), read(before / "forecast.json")
        house = weekly.house_view(forecast, read(out / "house_levels.json"))
        counts = polls[polls.race_id != "US"].race_id.value_counts().to_dict() | (
            hp.race_id.value_counts().to_dict() if hp is not None else {})
        res = weekly.trend(forecast, prev, polls) | {"far_from_polls": weekly.far_from_polls(forecast["races"] | house,
                                                                                               counts)}
        if prev is None:
            return res
        house0, hp0 = weekly.house_view(prev, read(before / "house_levels.json")), table(before / "house_polls.csv")
        if not (house and house0 and hp is not None and hp0 is not None):
            return res | {"house": {"note": "no House forecast to compare"}}
        key = lambda df: df[FIRST_SEEN_KEY].astype(str).agg("|".join, axis=1)
        hp = hp.assign(first_seen=key(hp).isin(set(key(hp0))).map({True: prev["snapshot"], False: day.isoformat()}))
        h = weekly.trend({"races": house}, {"date": prev["date"], "snapshot": prev["snapshot"], "races": house0}, hp)
        return res | {"house": {k: h[k] for k in ("new_polls", "races", "flagged", "analyse")}}
    except Exception as e:
        return {"error": f"{type(e).__name__}: {e}"[:120]}


def trend_summary(res: dict) -> dict:
    """The weekly trend check's line in run.json: flagged and analysed races, Senate and House, and those far from
    their polls."""
    if "error" in res:
        return {"error": res["error"]}
    h = res.get("house", {})
    return {"flagged": res["flagged"] + h.get("flagged", []), "analyse": res["analyse"] + h.get("analyse", []),
            "far_from_polls": sorted(res["far_from_polls"])} | ({"note": res["note"]} if "note" in res else {})


def candidates(races: dict, house_races: dict | None = None) -> dict:
    """{race_id: {"left": surname, "left_party", "right": surname}} for the weekly check's rows, Senate (races_json)
    and House (house.prepare's races)."""
    out = {r: {"left": surname(x["candidates"]["left"]), "left_party": x["left_party"],
               "right": surname(x["candidates"]["right"])} for r, x in races.items()}
    for r, x in (house_races or {}).items():
        c, lp = x["candidates"], x["left_party"]
        out[r] = {"left": surname((c.get(lp) or [""])[0]), "left_party": lp, "right": surname((c.get("R") or [""])[0])}
    return out


def weekly_check_files(data: Path, day: date, forecast: dict, out: Path, mv: dict, root: str = "derived",
                       names: dict | None = None) -> dict:
    """The Sunday weekly check (weekly.check, docs/simulation-only.md) against the forecast a week earlier (or the
    rule's first day, start.FROM, if later), for the Senate and the House seats: the week's new polls (Senate: first
    seen after that forecast's snapshot; House: not in that day's house_polls.csv), the stories behind our moves
    (weekly.week_stories) and Matteo's cancelled weeks, with the level check (weekly.far_from_polls); rows carry the
    candidates' surnames (`names`, candidates()). Reports only."""
    since = max(day - timedelta(days=7), frozen.FROM)
    before = data / root / since.isoformat()
    read = lambda f: json.loads(f.read_text(encoding="utf-8")) if f.exists() else None
    table = lambda f: pd.read_csv(f, low_memory=False) if f.exists() else None
    pl, hp = table(out / "polls.csv"), table(out / "house_polls.csv")
    now = forecast["races"] | weekly.house_view(forecast, read(out / "house_levels.json"))
    counts = pl[pl.race_id != "US"].race_id.value_counts().to_dict() | (
        hp.race_id.value_counts().to_dict() if hp is not None else {})
    far = weekly.far_from_polls(now, counts)
    prev = read(before / "forecast.json") if since < day else None
    if prev is None:
        return {"week_ending": day.isoformat(), "since": since.isoformat(), "rules": weekly.CHECK, "races": [],
                "note": "no forecast under this rule a week ago: nothing to compare", "far_from_polls": far}
    then = prev["races"] | weekly.house_view(prev, read(before / "house_levels.json"))
    new = pl[(pl.race_id != "US") & (pl.first_seen.astype(str) > str(prev["snapshot"]))].race_id.value_counts()
    new = new.to_dict()
    hp0 = table(before / "house_polls.csv")
    if hp is not None and hp0 is not None:
        key = lambda df: df[FIRST_SEEN_KEY].astype(str).agg("|".join, axis=1)
        new |= hp[~key(hp).isin(set(key(hp0)))].race_id.value_counts().to_dict()
    weeks = {(w["race"], w["week_ending"]) for w in (read(frozen.CANCELLED) or {}).get("weeks", [])}
    res = weekly.check(now, then, new, weekly.week_stories(mv, since), {r for r, w in weeks if w == day.isoformat()})
    res["races"] = [x | (names or {}).get(x["race"], {}) for x in res["races"]]
    return {"week_ending": day.isoformat(), "since": since.isoformat(), "since_snapshot": prev["snapshot"]} | res | {
        "far_from_polls": far}


def _git_sha() -> str:
    return subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True,
                          cwd=Path(__file__).parent).stdout.strip()


def _write(path: Path, obj, compact: bool = False) -> str:
    text = json.dumps(obj, separators=(",", ":")) if compact else json.dumps(obj, indent=1, default=str)
    path.write_text(text, encoding="utf-8")
    return hashlib.sha256(text.encode()).hexdigest()


def run(day: date, data: Path, hhmm: str | None = None, run_id: str | None = None, weekly_update: bool = False,
        rule: str | None = None, out_root: str | None = None, weekly_check: bool = False,
        lasting: float | None = None) -> dict:
    """The day's statistics step under `rule` (start.rule_for(day) by default), written to <out_root>/<date>/
    ("derived" by default; the inputs always come from derived/). Under the simulation-only rule the dials stay at
    the 12 Oct update and nothing is re-fitted from polls; the weekly check runs on Sundays (or `weekly_check`).
    `weekly_update` forces the poll filter's Monday re-fit. Under the simulation-only rule, from lockin.FROM or with
    `lasting` (the Election Day voters' lasting share L), the 3 Nov view lets early votes lock in (lockin);
    lasting=lockin.OFF keeps it off."""
    snap = snapshot_for(data, day, hhmm)
    run_id = run_id or f"{day}-{_git_sha()[:7]}"
    rule = rule or frozen.rule_for(day)
    sim = rule == frozen.RULE
    meta = {"date": day.isoformat(), "run_id": run_id, "schema": SCHEMA}
    out = data / (out_root or "derived") / day.isoformat()
    out.mkdir(parents=True, exist_ok=True)
    t = polls.build(snap)
    first_seen(poll_rows(t["senate"], t["generic_ballot"]), previous_polls(data, day),
               t["snapshot"]).to_csv(out / "polls.csv", index=False)
    races = races_json(t["race_list"])
    inp = levels.inputs()
    lv = levels.compute(t, day, run_id, inp=inp)
    sha = {"levels.json": _write(out / "levels.json", lv)}
    hb, house_note = None, None
    if (data / "house" / "inputs.json").exists():
        try:  # the House (Kev session, house.py) must not stop the Senate forecast
            from . import house as hs
            hb = hs.prepare(day, data, lv, run_id=run_id)
            hs.write(hb, hb["twin"], out)
            house_note = {k: v for k, v in hs.summary(hb).items() if k in ("seats", "uncontested", "tiers")}
        except Exception as e:
            hb, house_note = None, {"error": f"{type(e).__name__}: {e}"[:120]}
    base, pimu = (json.loads(f.read_text(encoding="utf-8")) for f in (groups.BASE, groups.PIMU))
    kev = json.loads(groups.KEV.read_text(encoding="utf-8")) if groups.KEV.exists() else None
    grp = groups.build(lv, base, pimu, day.isoformat(), run_id, kev) | (
        {r: g for r, g in hb["groups"].items() if isinstance(g, dict)} if hb else {})
    _write(out / "groups.json", grp)
    roots = ("derived",) + ((out_root,) if out_root and not sim else ())
    mp = apply_weekly(json.loads(moves.PARAMS.read_text(encoding="utf-8")),
                      latest_weekly(data, min(day, frozen.START) if sim else day, roots))
    mv = moves.build(day, data / "derived", grp, mp, run_id)
    wk = None
    if not sim and (weekly_update or (day.weekday() == 0 and day >= weekly.WEEKLY_FROM)):
        wk = meta | weekly.run(day, t, mv, mp)
        sha["filter_weekly.json"] = _write(out / "filter_weekly.json", wk)
        mp = apply_weekly(mp, wk)
        mv = moves.build(day, data / "derived", grp, mp, run_id)
    _write(out / "params.json", meta | mp | {"fitted_on": mp["fit"]["on"]})
    sha["moves.json"] = _write(out / "moves.json", mv)
    fz, drop = (frozen.load(data), frozen.cancelled()) if sim else (None, None)
    at = lambda e: frozen.at(fz, e, hb["tier"] if hb else None) if fz else None
    if sim and lasting is None and lockin.FROM and day >= lockin.FROM:
        lasting = lockin.LASTING
    lk = lockin.prepare(data, day, mv, [r.race_id for r in t["race_list"]] + list(hb["races"] if hb else []),
                        lasting) if sim and lasting is not None and lasting >= 0 else None
    lv, head, news, house = _levels(t, day, run_id, mv, inp, mp, hb=hb, start=at(levels.ELECTION), drop=drop,
                                    lock=lk)
    sha["filter_state.json"] = _write(out / "filter_state.json", head | {"moves": "moves.json, main block (GLM)",
                                                                          "dials": mp["dials"], "rule": rule})
    params = json.loads((Path(levels.__file__).parent / "stats_params.json").read_text())
    bench, left = benchmarks(snap, t["race_list"]), {k: v["left_party"] for k, v in races.items()}
    now_twin, now_head, now_news, now_house = _levels(t, day, run_id, mv, inp, mp, election=day, hb=hb,
                                                      start=at(day), drop=drop)
    left_h = {r: x["left_party"] for r, x in hb["races"].items()} if hb else {}
    for h in (house, now_house):
        if h and "error" in h:
            house_note = h
    house, now_house = ((h | {"left": left_h}) if h and "error" not in h else None for h in (house, now_house))
    forecast, draws = montecarlo.build(head, lv, left, params, day, run_id, benchmarks=bench, movers=moves.movers(mv),
                                       news=news, house=house)
    forecast = montecarlo.attach_today(forecast, montecarlo.build(now_head, now_twin, left, params, day, run_id,
                                                                  news=now_news, house=now_house)[0],
                                       movers=moves.movers(mv, when="today"))
    if wk:  # the weekly trend check reads the new forecast and only reports
        wk["trend"] = week_trend(data, day, forecast, out)
        sha["filter_weekly.json"] = _write(out / "filter_weekly.json", wk)
    check = None
    if sim and (weekly_check or day.weekday() == 6):  # Sunday, after the day's forecast; it only reports
        check = meta | weekly_check_files(data, day, forecast, out, mv, out_root or "derived",
                                          candidates(races, hb["races"] if hb else None))
        sha["weekly_check.json"] = _write(out / "weekly_check.json", check)
    forecast["rule"] = rule
    if lk:
        forecast["lock_in"] = {"lasting": lk["lasting"], "counted": lk["counted"],
                               "cast_before_election_day": {st: round(1 - w[levels.ELECTION], 4)
                                                            for st, w in sorted(lk["weights"].items())},
                               "cast_by_today": {st: round(sum(v for d, v in w.items() if d < day), 4)
                                                 for st, w in sorted(lk["weights"].items())}}
    forecast |= {"snapshot": t["snapshot"], "inputs": sha}
    history = [json.loads(f.read_text(encoding="utf-8")) for k in range(1, 7)
               if (f := data / "derived" / (day - timedelta(days=k)).isoformat() / "races.json").exists()]
    stats = {r: x["stats_only"]["p_dem_win"] for r, x in forecast["races"].items()}
    races = tiers(races, stats, bench, history)
    _write(out / "races.json", meta | races | (hb["races"] if hb else {}))
    _write(out / "forecast.json", forecast)
    _write(out / "draws.json", draws, compact=True)
    return {"ok": True, "date": day.isoformat(), "run_id": run_id, "snapshot": t["snapshot"], "races": len(races),
            "with_polls": sum(r["n_polls"] > 0 for r in lv["races"].values()), "draws": forecast["draws"],
            "floor_lifted_pairs": forecast["floor_lifted_pairs"],
            "tiers": {k: sum(r["tier"] == k for r in races.values()) for k in TIER_RANK},
            "orphaned_events": len(mv["orphaned_events"]), "deselected_pairs": len(mv["deselected_pairs"]),
            "ungrouped_races": len(mv["ungrouped_races"]), "weekly_update": mp.get("weekly_update"),
            "trend": trend_summary(wk["trend"]) if wk else None, "rule": rule,
            "lock_in": lk and {"lasting": lk["lasting"], "counted": lk["counted"]},
            "weekly_check": weekly.check_summary(check) if check else None,
            "stories": sum(len(x["events"]) for k, x in mv.items() if k != "shadow" and isinstance(x, dict) and "events" in x),
            "house": house_note,
            "files": ["polls.csv", "races.json", "levels.json", "groups.json", "params.json", "moves.json",
                      "filter_state.json", "forecast.json", "draws.json"] + (
                ["house_levels.json", "house_races.json", "house_groups.json", "house_polls.csv"] if hb else []) + (
                ["weekly_check.json"] if check else [])}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", type=date.fromisoformat, default=datetime.now(timezone.utc).date())
    ap.add_argument("--data", type=Path, default=Path(__file__).resolve().parents[2] / "simlab-data")
    ap.add_argument("--snapshot", default=None, help="snapshot run HHMM (default: the day's latest)")
    ap.add_argument("--run-id", default="")
    ap.add_argument("--weekly", action="store_true", help="poll filter only: run its weekly update today (Mondays anyway)")
    ap.add_argument("--rule", choices=[frozen.RULE, frozen.OLD_RULE], default=None,
                    help="default: simulation-only from 14 Oct, the poll filter before")
    ap.add_argument("--out-root", default=None, help="write to <data>/<out-root>/<date>/ instead of derived/")
    ap.add_argument("--weekly-check", action="store_true", help="run the Sunday weekly check today")
    ap.add_argument("--lasting", type=float, default=None,
                    help="let early votes lock in on 3 Nov with this lasting share for Election Day voters")
    a = ap.parse_args()
    try:
        summary = run(a.date, a.data, a.snapshot, a.run_id or None, a.weekly, a.rule, a.out_root, a.weekly_check,
                      a.lasting)
    except Exception as e:
        traceback.print_exc()
        print(json.dumps({"ok": False, "date": a.date.isoformat(), "error": f"{type(e).__name__}: {e}"}))
        return 1
    print(json.dumps(summary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
