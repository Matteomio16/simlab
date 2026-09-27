"""CES 2024 cells -> Kev fine-tune records with soft targets; OH, NC and TX are never trained on.

Each record is one demographic cell of one state (the same persona text as the fidelity test) with the cell's weighted
2024 vote and turnout shares as soft targets (turnout shifted to the state's official 2024 rate, as in `ces.build`).
The questions are the exact fidelity-test questions, because a Kev
fine-tune binds those strings. The vote question appears in 3 option orders so the model learns order invariance.

    python -m simlab.kevdata            # writes data/kev/ces-v1/{train,calibration,development,all}.jsonl + manifest.json
"""
from __future__ import annotations

import hashlib
import json
import random
import subprocess
from pathlib import Path

from . import probes
from .ces import DATA, VOTE_OPTIONS, cells, load, turnout_shift

STATES = {1: "Alabama", 2: "Alaska", 4: "Arizona", 5: "Arkansas", 6: "California", 8: "Colorado", 9: "Connecticut",
          10: "Delaware", 11: "District of Columbia", 12: "Florida", 13: "Georgia", 15: "Hawaii", 16: "Idaho",
          17: "Illinois", 18: "Indiana", 19: "Iowa", 20: "Kansas", 21: "Kentucky", 22: "Louisiana", 23: "Maine",
          24: "Maryland", 25: "Massachusetts", 26: "Michigan", 27: "Minnesota", 28: "Mississippi", 29: "Missouri",
          30: "Montana", 31: "Nebraska", 32: "Nevada", 33: "New Hampshire", 34: "New Jersey", 35: "New Mexico",
          36: "New York", 37: "North Carolina", 38: "North Dakota", 39: "Ohio", 40: "Oklahoma", 41: "Oregon",
          42: "Pennsylvania", 44: "Rhode Island", 45: "South Carolina", 46: "South Dakota", 47: "Tennessee",
          48: "Texas", 49: "Utah", 50: "Vermont", 51: "Virginia", 53: "Washington", 54: "West Virginia",
          55: "Wisconsin", 56: "Wyoming"}
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
    df["state"] = df.inputstate.map(STATES)
    shift = {s: turnout_shift(df, s) for s in STATES.values()}
    rng = random.Random(seed)
    dev = [r for s in HELD_OUT for r in state_records(df, s, shift[s], 30, rng)]
    rest = [r for s in sorted(set(STATES.values()) - set(HELD_OUT))
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


if __name__ == "__main__":
    build()
