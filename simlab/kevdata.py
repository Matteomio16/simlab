"""CES cells -> Kev fine-tune records with soft targets; OH, NC and TX are never trained on.

ces-v1: each record is one demographic cell of one state (the same persona text as the fidelity test) with the cell's
weighted 2024 vote and turnout shares as soft targets (turnout shifted to the state's official 2024 rate, as in
`ces.build`). The questions are the exact fidelity-test questions, because a Kev fine-tune binds those strings. The
vote question appears in 3 option orders so the model learns order invariance.

ces-v2 adds, per state: the 28 party-ID x white/non-white x degree strata of the test archetypes and 2020-vote x
white/non-white x degree cells (2024 vote and turnout), and, from the CES cumulative file, 2018 and 2022 midterm turnout
(shifted per state to the official rate of that year) and the 2022 House vote, merged into the demographic-cell records.

ces-v3a/b test why ces-v2's vote shares got worse than ces-v1's: the same records as ces-v2 but with turnout from the
Census CPS (see cps.py; CES turnout tracks voter-file matching) on demographic cells only (v3a), or no turnout questions
at all (v3b).

    python -m simlab.kevdata            # data/kev/ces-v1/{train,calibration,development,all}.jsonl + manifest.json
    python -m simlab.kevdata v2         # data/kev/ces-v2/...
    python -m simlab.kevdata v3         # data/kev/ces-v3a/... and data/kev/ces-v3b/...
    python -m simlab.kevdata groups     # data/kev/groups: the 28 voter groups x 51 states, for Kev to answer
    python -m simlab.kevdata answers ces-v3b-groups   # that run's answers -> kev-finetune/runs/<run>/answers.json
"""
from __future__ import annotations

import hashlib
import json
import random
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import brentq
from scipy.special import expit

from . import cps, probes
from .ces import DATA, PID7, STATE_NAMES, VOTE_OPTIONS, _logit, cells, load, turnout_shift
from .personas import render

HELD_OUT = ("Ohio", "North Carolina", "Texas")
OUT = DATA / "kev" / "ces-v1"


def record(persona: str, vote: dict | None, turnout: dict | None, rng: random.Random, orders: int = 3) -> dict:
    qs = {}
    if vote:
        target = {k: round(vote.get(k, 0.0), 4) for k in VOTE_OPTIONS}
        opts = list(VOTE_OPTIONS.items())
        for i in range(orders):
            criteria = dict(opts if i == 0 else rng.sample(opts, len(opts)))
            qs[f"vote{i}"] = {**probes.vote_question(criteria), "label": max(target, key=target.get), "target": target}
    if turnout:
        qs["turnout"] = {**probes.TURNOUT_Q, "label": turnout["true"] >= 0.5, "target": turnout}
    return {"state": persona, "questions": qs}


def state_records(df, state: str, shift: float, min_n: int, rng: random.Random) -> list[dict]:
    vote = {c["persona"]: c["target"] for c in cells(df, "vote24", state, min_n=min_n)}
    turn = {c["persona"]: c["target"] for c in cells(df, "turnout", state, min_n=min_n, shift=shift)}
    return [record(p, vote.get(p), turn.get(p), rng) for p in sorted(vote.keys() | turn.keys())]


def build(min_n_train: int = 20, calibration: float = 0.15, seed: int = 0) -> None:
    csv = next(DATA.glob("CCES24_*.csv"))
    df = load(csv)
    df["state"] = df.inputstate.map(STATE_NAMES)
    shift = {s: turnout_shift(df, s) for s in STATE_NAMES.values()}
    rng = random.Random(seed)
    dev = [r for s in HELD_OUT for r in state_records(df, s, shift[s], 30, rng)]
    rest = [r for s in sorted(set(STATE_NAMES.values()) - set(HELD_OUT))
            for r in state_records(df, s, shift[s], min_n_train, rng)]
    rng.shuffle(rest)
    k = max(40, round(calibration * len(rest)))
    parts = {"calibration": rest[:k], "train": rest[k:], "development": dev}
    OUT.mkdir(parents=True, exist_ok=True)
    for name, recs in {**parts, "all": rest + dev}.items():
        (OUT / f"{name}.jsonl").write_text("\n".join(json.dumps(r) for r in recs) + "\n", encoding="utf-8")
    sha = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True,
                         cwd=Path(__file__).parent).stdout.strip()
    manifest = {"source": csv.name, "source_sha256": hashlib.sha256(csv.read_bytes()).hexdigest(),
                "simlab_git": sha, "seed": seed,
                "turnout_logit_shift_by_state": {s: round(v, 4) for s, v in sorted(shift.items())},
                "held_out": HELD_OUT, "min_n": {"train_and_calibration": min_n_train, "development": 30},
                "records": {n: len(r) for n, r in parts.items()},
                "questions": {n: sum(len(r["questions"]) for r in recs) for n, recs in parts.items()}}
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    print(json.dumps(manifest, indent=1))


# ------------------------------------------------------------------------------------------------------------ ces-v2
OUT_V2 = DATA / "kev" / "ces-v2"
OUT_V3A, OUT_V3B = DATA / "kev" / "ces-v3a", DATA / "kev" / "ces-v3b"
OUT_GROUPS = DATA / "kev" / "groups"
CUMULATIVE = DATA / "cumulative_2006-2025.dta"
MIDTERMS = (2018, 2022)
TURNOUT = {y: json.loads((Path(__file__).parent / f"turnout{y}.json").read_text())["vep_turnout"] for y in MIDTERMS}
CELL = ["age2", "gender", "race4", "degree"]
PARTY = {**PID7, 8: PID7[4]}  # "Not sure" joins the independents, as in the test archetypes
VOTE20 = {1: "Joe Biden", 2: "Donald Trump", 3: "Another candidate", 4: "Another candidate", 5: "Another candidate",
          6: "Did not vote"}


def shares(d: pd.DataFrame, by: list[str], target: str, weight: str, min_n: int, shift: float | None = None) -> dict:
    """(respondents, weighted shares of `target`) per cell of `by` with at least `min_n` respondents; `shift`
    logit-shifts 'true'."""
    out = {}
    for key, g in d.groupby(by):
        if len(g) < min_n:
            continue
        s = (g.groupby(target)[weight].sum() / g[weight].sum()).to_dict()
        if shift is not None:
            t = float(expit(_logit(s.get("true", 0.0)) + shift))
            s = {"true": t, "false": 1 - t}
        out[key] = (len(g), {str(k): round(float(v), 4) for k, v in s.items()})
    return out


def logit_shift(d: pd.DataFrame, weight: str, rate: float) -> float:
    """One logit shift for every demographic cell that lifts validated turnout to the official rate (as ces.turnout_shift)."""
    g = d.groupby(CELL)
    p = g.apply(lambda x: np.average(x.voted, weights=x[weight]), include_groups=False)
    w = g[weight].sum()
    return brentq(lambda k: np.average(expit(_logit(p) + k), weights=w) - rate, -5, 5)


def midterms() -> pd.DataFrame:
    """Citizens in the CES cumulative file for the midterm years, with the same cell fields as the 2024 cells."""
    cols = ["year", "weight", "vvweight_post", "state", "gender", "age", "race", "hispanic", "educ", "citizen",
            "vv_turnout_gvm", "voted_rep_party"]
    d = pd.read_stata(CUMULATIVE, columns=cols, convert_categoricals=True)
    d = d[d.year.isin(MIDTERMS) & d.gender.isin(["Male", "Female"]) & (d.citizen == "Citizen")].copy()
    d["gender"] = d.gender.astype(str).map({"Male": "Man", "Female": "Woman"})
    d["age2"] = np.where(d.age < 45, "18-44", "45+")
    hispanic = (d.hispanic == "Yes") | (d.race == "Hispanic")
    d["race4"] = np.where(hispanic, "Hispanic", d.race.astype(str).map({"White": "White", "Black": "Black"}).fillna("Other"))
    d["degree"] = np.where(d.educ.isin(["4-Year", "Post-Grad"]), "Four-year college degree or more",
                           "No four-year college degree")
    d["state"] = d.state.astype(str)
    d["voted"] = d.vv_turnout_gvm == "Voted"
    d["turnout"] = np.where(d.voted, "true", "false")
    party = d.voted_rep_party.astype(str).map({"Democratic": "democrat", "Republican": "republican"}).fillna("other")
    d["house22"] = party.where(d.voted & d.voted_rep_party.notna() & (d.year == 2022))
    return d


def question(template: dict, target: dict) -> dict:
    keys = list(template["criteria"]) if template["type"] == "choice" else ["true", "false"]
    t = {k: round(target.get(k, 0.0), 4) for k in keys}
    label = max(t, key=t.get) if template["type"] == "choice" else t["true"] >= 0.5
    return {**template, "label": label, "target": t}


def add_choice(qs: dict, name: str, make, options: dict, target: dict, rng: random.Random, orders: int = 3):
    opts = list(options.items())
    for i in range(orders):
        qs[f"{name}_{i}"] = question(make(dict(opts if i == 0 else rng.sample(opts, len(opts)))), target)


def build_v2(min_n: int = 20, calibration: float = 0.15, seed: int = 0, turnout: str = "ces") -> None:
    """turnout='ces' builds ces-v2. turnout='cps' builds ces-v3: turnout targets from the Census CPS
    (cps.respondents) on demographic cells only, since the CPS has no party ID or 2020 vote, written twice with the
    same records, option orders and split: ces-v3a with the turnout questions, ces-v3b without them (vote only)."""
    csv = next(DATA.glob("CCES24_*.csv"))
    df = load(csv)
    df["state"] = df.inputstate.map(STATE_NAMES)
    df["party_id"] = df.pid7.map(PARTY)
    df["race2"] = np.where(df.race5 == "White", "White", "Non-white")
    df["vote_2020"] = df.presvote20post.map(VOTE20)
    voters = df[df.vote24.notna() & df.vvweight_post.notna()]
    citizens = df[df.cit1 == 1]
    mid = midterms()
    census = {y: cps.respondents(y) for y in cps.YEARS} if turnout == "cps" else {}
    rng = random.Random(seed)
    records, shifts, sizes = {}, defaultdict(dict), defaultdict(dict)
    for s in STATE_NAMES.values():
        n_dev = 30 if s in HELD_OUT else min_n   # held-out demographic cells = the fidelity-test cells
        qs = defaultdict(dict)
        for c in cells(df, "vote24", s, min_n=n_dev):
            add_choice(qs[c["persona"]], "pres24", probes.vote_question, VOTE_OPTIONS, c["target"], rng)
            sizes[c["persona"]]["pres24"] = c["n"]
        if census:
            turnout24 = cells(census[2024], "turnout", s, min_n=n_dev)
        else:
            shifts[2024][s] = turnout_shift(df, s)
            turnout24 = cells(df, "turnout", s, min_n=n_dev, shift=shifts[2024][s])
        for c in turnout24:
            qs[c["persona"]]["turnout24"] = question(probes.turnout_question(2024), c["target"])
            sizes[c["persona"]]["turnout24"] = c["n"]
        for field in ("party_id", "vote_2020"):
            by = [field, "race2", "degree"]
            persona = lambda k: render({"state": s, "race": k[1], "education": k[2], field: k[0]})
            for k, (n, t) in shares(voters[voters.state == s], by, "vote24", "vvweight_post", min_n).items():
                add_choice(qs[persona(k)], "pres24", probes.vote_question, VOTE_OPTIONS, t, rng)
                sizes[persona(k)]["pres24"] = n
            if census:
                continue
            for k, (n, t) in shares(citizens[citizens.state == s], by, "turnout", "commonweight", min_n,
                                    shifts[2024][s]).items():
                qs[persona(k)]["turnout24"] = question(probes.turnout_question(2024), t)
                sizes[persona(k)]["turnout24"] = n
        persona = lambda k: render({"state": s, "age": k[0], "gender": k[1], "race": k[2], "education": k[3]})
        for y in MIDTERMS:
            for c in cells(census[y], "turnout", s, min_n=min_n) if census else []:
                qs[c["persona"]][f"turnout{y % 100}"] = question(probes.turnout_question(y), c["target"])
                sizes[c["persona"]][f"turnout{y % 100}"] = c["n"]
            d = mid[(mid.year == y) & (mid.state == s)]
            if len(d) < 200:
                continue
            if not census:
                shifts[y][s] = logit_shift(d, "weight", TURNOUT[y][s])
                for k, (n, t) in shares(d, CELL, "turnout", "weight", min_n, shifts[y][s]).items():
                    qs[persona(k)][f"turnout{y % 100}"] = question(probes.turnout_question(y), t)
                    sizes[persona(k)][f"turnout{y % 100}"] = n
            if y == 2022:
                v = d[d.house22.notna() & d.vvweight_post.notna()]
                for k, (n, t) in shares(v, CELL, "house22", "vvweight_post", min_n).items():
                    add_choice(qs[persona(k)], "house22", lambda o: probes.house_vote_question(2022, o),
                               probes.HOUSE_OPTIONS, t, rng)
                    sizes[persona(k)]["house22"] = n
        records[s] = [{"state": p, "questions": q} for p, q in sorted(qs.items())]
    dev = [r for s in HELD_OUT for r in records[s]]
    rest = [r for s in sorted(set(STATE_NAMES.values()) - set(HELD_OUT)) for r in records[s]]
    rng.shuffle(rest)
    k = max(40, round(calibration * len(rest)))
    parts = {"calibration": rest[:k], "train": rest[k:], "development": dev}
    sha = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True,
                         cwd=Path(__file__).parent).stdout.strip()
    sources = [csv, CUMULATIVE, *([cps.CPS / "nov24pub.csv", cps.CPS / "nov22pub.csv", cps.CPS / "nov18" / "nov18pub.dat"]
                                  if census else [])]
    manifest = {"sources": {f.name: hashlib.sha256(f.read_bytes()).hexdigest() for f in sources},
                "simlab_git": sha, "seed": seed, "held_out": HELD_OUT, "turnout": turnout,
                "min_n": {"all": min_n, "held-out 2024 demographic cells": 30},
                "turnout_logit_shift": {y: {s: round(v, 4) for s, v in sorted(m.items())} for y, m in shifts.items()}}
    if not census:
        write(OUT_V2, parts, manifest, sizes)
        return
    write(OUT_V3A, parts, manifest, sizes)
    vote_only = lambda recs: [v for v in ({"state": r["state"], "questions": {q: x for q, x in r["questions"].items()
                                                                            if not q.startswith("turnout")}}
                                          for r in recs) if v["questions"]]
    write(OUT_V3B, {n: vote_only(r) for n, r in parts.items()}, manifest, sizes)


def write(out: Path, parts: dict, manifest: dict, sizes: dict) -> None:
    out.mkdir(parents=True, exist_ok=True)
    for name, recs in {**parts, "all": parts["calibration"] + parts["train"] + parts["development"]}.items():
        (out / f"{name}.jsonl").write_text("\n".join(json.dumps(r) for r in recs) + "\n", encoding="utf-8")
    count = lambda recs: dict(sorted(pd.Series([q.rsplit("_", 1)[0] for r in recs for q in r["questions"]]).value_counts()
                                     .to_dict().items()))
    manifest = {**manifest, "records": {n: len(r) for n, r in parts.items()},
                "questions": {n: count(r) for n, r in parts.items()}}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    (out / "sizes.json").write_text(json.dumps(sizes), encoding="utf-8")   # respondents behind each target, for scoring
    print(out.name, json.dumps({k: manifest[k] for k in ("records", "questions")}, indent=1))


def build_groups(seed: int = 0) -> None:
    """The engine's 28 voter groups in every state of groups_base.json as persona records (the ces-v2/v3 party-ID
    strata text) with the pres24 question in 3 option orders, for a fine-tune to answer. Targets are placeholders."""
    from .groups import BASE
    from .statsdata import mit
    upper = {v.upper(): v for v in STATE_NAMES.values()}
    p = mit("president")
    name = {po: upper[s] for po, s in zip(p.state_po, p.state)}
    rng, recs = random.Random(seed), []
    for st, groups in sorted(json.loads(BASE.read_text(encoding="utf-8"))["states"].items()):
        for g in groups:
            pid, race, educ = g.split(" / ")
            qs = {}
            add_choice(qs, "pres24", probes.vote_question, VOTE_OPTIONS, dict.fromkeys(VOTE_OPTIONS, 1 / 3), rng)
            recs.append({"state": render({"state": name[st], "race": race.capitalize(), "education": educ,
                                          "party_id": pid}), "questions": qs, "_key": [st, g]})
    OUT_GROUPS.mkdir(parents=True, exist_ok=True)
    (OUT_GROUPS / "keys.json").write_text(json.dumps([r.pop("_key") for r in recs]), encoding="utf-8")
    (OUT_GROUPS / "development.jsonl").write_text("\n".join(json.dumps(r) for r in recs) + "\n", encoding="utf-8")
    print(f"{OUT_GROUPS}: {len(recs)} records")


def group_answers(run: str, data: Path = None) -> dict:
    """A run's answers on build_groups' records as {run, question, temperature, held_out, states: {state: {group: d}}},
    d = (harris - trump) / (harris + trump) averaged over the option orders at temperature 1.0, written next to the
    run's reports as answers.json (the input of `python -m simlab.groups --kev`)."""
    from scipy.special import softmax
    runs = Path(__file__).parent.parent / "kev-finetune" / "runs" / run
    keys = json.loads(((data or OUT_GROUPS) / "keys.json").read_text(encoding="utf-8"))
    d = defaultdict(list)
    for r in json.loads((runs / "development" / "rows.json").read_text(encoding="utf-8")):
        p = dict(zip(r["keys"], softmax(np.array(r["logits"]))))
        d[tuple(keys[int(r["id"].split("/")[1])])].append((p["harris"] - p["trump"]) / (p["harris"] + p["trump"]))
    out = {"run": run, "question": "pres24", "temperature": 1.0, "held_out": list(HELD_OUT), "states": {}}
    for (st, g), v in sorted(d.items()):
        assert len(v) == 3, (st, g, len(v))
        out["states"].setdefault(st, {})[g] = round(float(np.mean(v)), 4)
    (runs / "answers.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(f"{runs / 'answers.json'}: {sum(map(len, out['states'].values()))} groups in {len(out['states'])} states")
    return out


if __name__ == "__main__":
    if sys.argv[1:2] == ["answers"]:
        group_answers(sys.argv[2])
    else:
        {"v2": build_v2, "v3": lambda: build_v2(turnout="cps"), "groups": build_groups}.get(
            sys.argv[1] if sys.argv[1:] else "", build)()
