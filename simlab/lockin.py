"""Early votes lock in (Matteo, 26 Oct, via the Publishing approval thread): the 3 Nov forecast keeps the part of each
story's effect that the state's ballots saw when they were cast.

A story's 3 Nov contribution in state s is its full effect times

    G = sum over days d before 3 Nov of w(s, d) x held(d)  +  w(s, 3 Nov) x (L + (1 - L) x held(3 Nov))

where w(s, d) is the share of the state's ballots cast on day d (early in person, and mail by the day it came back),
held(d) the share of the story still felt that day, and L a small lasting share for Election Day voters. Past days
read held from that day's archived moves.json (its effect in force over its full effect: what the forecast had that
day, never recomputed); today and later days project it as now, coverage taken to end today. The switching and
turnout parts are treated alike, since G multiplies the whole story.

The ballot shares (early_shares.json, written by `python -m simlab.lockin --shares <EAVS csv>`):
- each state's share of 2022 ballots cast before Election Day: the EAC's 2022 Election Administration and Voting
  Survey, section F (UOCAVA, mail, early in person and all-mail ballots over all ballots);
- their timing: mail ballots follow the 2022 national pace of pre-Election-Day ballots (US Elections Project counts as
  reported then; CURVE), late returns arriving on Election Day; early in-person ballots follow the same pace but all
  before Election Day (the curve without its last day);
- North Carolina and Maine: 2026 ballots by the day they came back (our early-vote snapshots), the days left at the
  last week's pace, over the state's 2022 ballots.
"""
from __future__ import annotations

import argparse
import gzip
import io
import json
import sys
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

from . import levels, moves

HERE = Path(__file__).parent
SHARES = HERE / "early_shares.json"
ELECTION = levels.ELECTION
# cumulative share of a state's pre-Election-Day ballots cast by the end of the day k days before it (2022)
CURVE = [(42, 0.0), (35, 0.02), (28, 0.06), (21, 0.16), (9, 0.36), (6, 0.56), (1, 0.77), (0, 1.0)]
KEY = {"all": "full", "s": "full_s", "t": "full_t", "s_base": "full_s_base", "t_base": "full_t_base"}
COUNTED = ("nc", "me")
FROM, LASTING = None, 0.0  # off until Matteo's yes; then the first day and the chosen L
OFF = -1.0  # statsday.run(lasting=OFF): the 3 Nov view without lock-in (the shadow)


def cumulative(k: int, in_person: bool = False) -> float:
    """Share of the pre-Election-Day ballots cast by the end of the day k days before it; in person, all are cast by
    the day before."""
    ks, cs = zip(*CURVE)
    c = float(np.interp(-k, [-x for x in ks], cs))
    return min(c / cumulative(1), 1.0) if in_person and k >= 1 else (1.0 if in_person else c)


def eavs(csv: Path) -> dict:
    """{state: {"in_person": share of 2022 ballots cast early in person, "mail": by mail, "early": both, "ballots": all
    2022 ballots}} from the EAVS 2022 file (section F: F1a all, F1c UOCAVA, F1d mail, F1f early in person, F1g
    all-mail jurisdictions)."""
    d = pd.read_csv(csv, low_memory=False, encoding="latin-1")
    cols = ["F1a", "F1c", "F1d", "F1f", "F1g"]
    x = d[cols].apply(pd.to_numeric, errors="coerce")
    s = x.where(x >= 0).groupby(d.State_Abbr).sum()
    out = {}
    for st, r in s.iterrows():
        if r.F1a > 0:
            ip, mail = float(r.F1f / r.F1a), float(r[["F1c", "F1d", "F1g"]].sum() / r.F1a)
            out[st] = {"in_person": round(ip, 4), "mail": round(mail, 4), "early": round(ip + mail, 4),
                       "ballots": int(r.F1a)}
    for st, (ip, mail, why) in OVERRIDE.items():
        out[st] |= {"in_person": ip, "mail": mail, "early": round(ip + mail, 4), "note": why}
    return out


# states whose EAVS method fields are missing or filed elsewhere
OVERRIDE = {"MT": (0.0, 0.60, "EAVS leaves Montana's methods blank; about 280,000 absentee ballots were in by the day "
                              "before the 2022 election (KTVH, 7 Nov 2022) of 468,326 ballots"),
            "MS": (0.065, 0.0, "Mississippi files its absentee ballots, mostly cast in person at the clerk's office, under "
                               "EAVS F1h (other): (F1c + F1h) / F1a")}


def _latest(data: Path, st: str, name: str, today: date) -> Path | None:
    files = sorted(f for f in (data / "earlyvote" / st).glob(f"*/*/{name}") if f.parts[-3] <= today.isoformat())
    return files[-1] if files else None


def counts(data: Path, today: date) -> dict:
    """{state: {date: ballots}}: 2026 ballots accepted by the day they came back, from the latest early-vote snapshot
    on or before `today` (North Carolina, Maine)."""
    read = lambda f: pd.read_csv(io.BytesIO(gzip.decompress(f.read_bytes())), dtype=str, keep_default_na=False)
    out = {}
    if (f := _latest(data, "nc", "absentee.csv.gz", today)) is not None:
        d = read(f)
        d = d[d.ballot_rtn_status.str.startswith("ACCEPTED") & (d.ballot_rtn_dt != "")]
        out["NC"] = d.assign(n=d.n.astype(int)).groupby("ballot_rtn_dt").n.sum().to_dict()
    if (f := _latest(data, "me", "absentee.csv.gz", today)) is not None:
        d = read(f)
        d = d[d.return_status.isin(["ACT", "ACU", "ACH"]) & (d.received != "")]
        out["ME"] = d.assign(n=d.n.astype(int)).groupby("received").n.sum().to_dict()
    return {s: {k: int(v) for k, v in c.items() if k < today.isoformat()} for s, c in out.items()}


def weights(state: str, today: date, shares: dict, counted: dict | None = None, election: date = ELECTION) -> dict:
    """{day: share of the state's ballots cast that day}, the Election Day share under `election`; days sum to 1. With
    `counted` ({date: ballots}), the past days are the 2026 counts and the days left before Election Day continue the
    last week's pace (the early share kept between the 2022 one and 0.95)."""
    sh = shares.get(state) or shares["US"]
    total = sh["ballots"]
    ip, mail = sh.get("in_person", 0.0), sh.get("mail", sh["early"])
    days = [election - timedelta(days=k) for k in range(CURVE[0][0], 0, -1)]
    step = lambda k, person: cumulative(k, person) - cumulative(k + 1, person)
    w = {d: ip * step((election - d).days, True) + mail * step((election - d).days, False) for d in days}
    if counted:
        past = {date.fromisoformat(k): v / total for k, v in counted.items()}
        left = [d for d in days if d >= today]
        recent = [past.get(today - timedelta(days=k), 0.0) for k in range(1, 8)]
        pace = sum(recent) / 7
        done = sum(past.values())
        future = min(pace * len(left), max(0.95 - done, 0.0))
        w = {d: v for d, v in past.items() if d < today} | {d: future / len(left) for d in left}
    w[election] = max(1.0 - sum(w.values()), 0.0)
    return w


def archive(derived: Path, today: date, start: date = date(2026, 9, 1)) -> dict:
    """{day: {event_id: share held that day}} from every archived moves.json before `today`: a story's effect in force
    that day over its full effect, from any block that has it."""
    out = {}
    for f in sorted(derived.glob("*/moves.json")):
        day = f.parent.name
        if not (start.isoformat() <= day < today.isoformat()):
            continue
        m, held = json.loads(f.read_text(encoding="utf-8")), {}
        for r, x in m.items():
            if r == "shadow" or not isinstance(x, dict) or not x.get("events"):
                continue
            eff = x.get("by_event_effect", {})
            for e, v in x["events"].items():
                if e not in held and v.get("full") and e in eff:
                    held[e] = eff[e] / v["full"]
        out[date.fromisoformat(day)] = held
    return out


def factors(m: dict, w: dict, held: dict, today: date, lasting: float, election: date = ELECTION) -> dict:
    """{event_id: G} for one state's ballot shares `w`, every story in moves.json `m`. Lasting topics (no after-news
    fading: economy, national) already last; the lasting share L isn't stacked on them."""
    events = {}
    for r, x in m.items():
        if r != "shadow" and isinstance(x, dict) and x.get("events"):
            for e, v in x["events"].items():
                events.setdefault(e, v)
    days = sorted(w)
    future = [d for d in days if d >= today]
    t = np.array([(d - election).days for d in future], dtype=float)
    stop = float((today - election).days)
    out = {}
    for e, v in events.items():
        g = sum(w[d] * held.get(d, {}).get(e, 0.0) for d in days if d < today)
        item = [(v["first_seen"], v["last_seen"], 1.0, v["age_half_life"], v["after_news_half_life"])]
        h = levels.effect(t, item, election, stop=stop)
        g += float(sum(w[d] * h[i] for i, d in enumerate(future) if d < election))
        keep = lasting if v["after_news_half_life"] is not None else 0.0
        g += w[election] * (keep + (1 - keep) * float(h[-1]))
        out[e] = g
    return out


def specific(m: dict, groups: dict, offset: float, turnout: float, c_t: float, dials: dict | None = None) -> dict:
    """{(block, event_id): (own switching, own turnout, at dial 1; dials k_s, k_t)}: the part of each story's effect
    that is its own (Engine's lean check, 26 Oct): switching net of GLM's support offset (`offset` times the effect of
    one unit of support, full_s_unit), turnout net of the average turnout answer (`turnout` times the effect of one
    unit of turnout answer for every group, from the block's voter groups). The rest is the same push every story
    gives; under the story-specific variant it keeps fading as before. The dials are the block's unit's (its state,
    or the nation's for "US")."""
    dials = dials or {}
    dial = lambda b: dials.get(b.split("-")[0], dials.get("default", {}))
    out = {}
    for b, x in m.items():
        if b == "shadow" or not isinstance(x, dict) or not x.get("events") or b not in groups:
            continue
        g = {k: v for k, v in groups[b].items() if isinstance(v, dict) and "mu" in v}
        for e, v in x["events"].items():
            unit_t = 100 * moves.race_move(g, {}, {k: gv["mu"] * c_t / 2 * v["a"] for k, gv in g.items()})
            out[(b, e)] = (v["full_s_base"] - offset * v["full_s_unit"], v["full_t_base"] - turnout * unit_t,
                           dial(b).get("k_s", 1.0), dial(b).get("k_t", 1.0))
    return out


def path_sets(m: dict, fac: dict, races: list[str], split: dict | None = None) -> dict:
    """moves.paths' items for the 3 Nov view with each story's full effect times its state's G (fac: {state: {event:
    G}}) and no further fading, per race and part: "all" (own and taken national stories, or the nation's for a race
    without its own), "own_s"/"own_t" and "us_s"/"us_t" at dial 1, as statsday._levels builds its news parts. Every
    race is listed, with "US" empty, so no race falls back to the nation's unscaled items. Mirrors moves._split.
    With `split` (specific()), only each story's own share locks in; the rest is a second item that fades as now."""
    blocks = {r: x for r, x in m.items() if r != "shadow" and isinstance(x, dict) and x.get("events")}
    us, extra = m.get("US", {}).get("events", {}), moves.takes_nation(m)
    def items(b, e, v, key, g):
        if split is None:
            return [(v["first_seen"], v["last_seen"], v[key] * g, None, None)]
        if (b, e) not in split:
            return [(v["first_seen"], v["last_seen"], v[key] * g, None, None)]
        os_, ot, ks, kt = split[(b, e)]
        own = ks * os_ + kt * ot if key == "full" else (os_ if "_s" in key else ot)
        return [(v["first_seen"], v["last_seen"], own * g, None, None),
                (v["first_seen"], v["last_seen"], v[key] - own, v["age_half_life"], v["after_news_half_life"])]
    out = {name: {"US": []} for name in ("all", "own_s", "own_t", "us_s", "us_t")}
    for r in races:
        f = fac[r.split("-")[0]]
        own_x = blocks.get(r) if r != "US" else None
        take = (set(us) if r in extra else set(own_x.get("nation_unasked", ()))) if own_x else set(us)
        for name, key in (("all", "all"), ("s", "s_base"), ("t", "t_base")):
            k = KEY[key]
            own = [i for e, v in own_x["events"].items() for i in items(r, e, v, k, f.get(e, 0.0))] if own_x else []
            nat = [i for e, v in us.items() if e in take for i in items("US", e, v, k, f.get(e, 0.0))]
            if name == "all":
                out["all"][r] = own + nat
            else:
                out[f"own_{name}"][r], out[f"us_{name}"][r] = own, nat
    return out


def prepare(data: Path, today: date, m: dict, races: list[str], lasting: float, shares: dict | None = None,
            own_only: dict | None = None) -> dict:
    """Everything the 3 Nov view needs on `today`: each state's ballot shares, G per story and the path sets. With
    `own_only` ({"offset", "turnout", "c_t", "groups"}), the story-specific variant (specific())."""
    shares = shares or json.loads(SHARES.read_text(encoding="utf-8"))["states"]
    counted, held = counts(data, today), archive(data / "derived", today)
    states = sorted({r.split("-")[0] for r in races})
    w = {s: weights(s, today, shares, counted.get(s)) for s in states}
    fac = {s: factors(m, w[s], held, today, lasting) for s in states}
    split = specific(m, own_only["groups"], own_only["offset"], own_only["turnout"], own_only["c_t"],
                     own_only.get("dials")) if own_only else None
    return {"lasting": lasting, "weights": w, "factors": fac, "paths": path_sets(m, fac, races, split),
            "counted": sorted(counted), "split": split}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--shares", type=Path, help="the EAVS 2022 CSV: write simlab/early_shares.json")
    a = ap.parse_args()
    if a.shares:
        st = eavs(a.shares)
        tot = sum(x["ballots"] for x in st.values())
        st["US"] = {k: round(sum(x[k] * x["ballots"] for x in st.values()) / tot, 4) for k in ("in_person", "mail", "early")}
        st["US"]["ballots"] = tot
        SHARES.write_text(json.dumps({
            "source": "EAC 2022 Election Administration and Voting Survey (EAVS), public release V1.0 CSV "
                      "(eac.gov, 2022_EAVS_for_Public_Release_nolabel_V1_CSV.zip), section F: in_person = F1f early in "
                      "person / F1a all ballots, mail = (F1c UOCAVA + F1d mail + F1g all-mail jurisdictions) / F1a; US = "
                      "ballot-weighted", "timing": "lockin.CURVE: 2022 national pace of pre-Election-Day ballots "
                      "(US Elections Project counts as reported: about 9.3M three weeks out, 20.4M on 30 Oct, 32M on "
                      "2 Nov, 44M on 7 Nov, of about 57M)", "states": st}, indent=1), encoding="utf-8")
        print(json.dumps({"ok": True, "states": len(st)}))
        return 0
    ap.error("nothing to do")
    return 1


if __name__ == "__main__":
    sys.exit(main())
