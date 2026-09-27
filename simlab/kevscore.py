"""Score a Kev fine-tune against the soft targets it was trained to reproduce.

For every held-out record (Ohio, North Carolina, Texas) and question type: total variation distance between the model's
probabilities (at a chosen temperature; 1.0 = raw) and the real shares, weighted by the respondents behind each cell.
Baselines: the same cell pooled over the training states (no model at all) and, for the 2024 demographic cells, the
regression baseline of the fidelity test. Kev's own report scores hard labels, which is not what the engine needs.

    python -m simlab.kevscore ces-v2 [--temperature 1.0]
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.special import softmax

from .ces import DATA

HERE = Path(__file__).parent
RUNS = HERE.parent / "kev-finetune" / "runs"
HELD_OUT = ("Ohio", "North Carolina", "Texas")


def jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def qtype(qid: str) -> str:
    return qid.rsplit("_", 1)[0] if qid[-2:-1] == "_" else qid


def kind(persona: str) -> str:
    return "party strata" if "Party identification" in persona else \
        "2020-vote cells" if "2020 presidential vote" in persona else "demographic cells"


def tvd(p: dict, t: dict) -> float:
    return 0.5 * sum(abs(p.get(k, 0.0) - t.get(k, 0.0)) for k in p.keys() | t.keys())


def score(run: str, data: str | None = None, temperature: float = 1.0) -> dict:
    folder = DATA / "kev" / (data or run)
    dev, rest = jsonl(folder / "development.jsonl"), jsonl(folder / "train.jsonl") + jsonl(folder / "calibration.jsonl")
    sizes = json.loads((folder / "sizes.json").read_text())
    fidelity = json.loads((HERE / "cells.json").read_text())
    regression = {(c["persona"], "pres24" if t == "vote24" else "turnout24"): c["baseline"]
                  for t in ("vote24", "turnout") for s in HELD_OUT for c in fidelity[t][s]}

    pred = defaultdict(list)   # (record, question type) -> one distribution per option order
    for r in json.loads((RUNS / run / "development" / "rows.json").read_text(encoding="utf-8")):
        p = softmax(np.array(r["logits"]) / temperature)
        pred[(int(r["id"].split("/")[1]), qtype(r["question"]))].append(dict(zip(r["keys"], p)))

    pooled = defaultdict(lambda: [defaultdict(float), 0.0])   # cell without its state line -> summed shares, weight
    for r in rest:
        cell = r["state"].split("\n", 1)[1]
        for qid, q in r["questions"].items():
            if qid.endswith("_1") or qid.endswith("_2"):
                continue
            w = sizes[r["state"]][qtype(qid)]
            acc = pooled[(cell, qtype(qid))]
            for k, v in q["target"].items():
                acc[0][k] += w * v
            acc[1] += w

    out = defaultdict(lambda: defaultdict(list))
    for (i, qt), dists in pred.items():
        rec = dev[i]
        state, cell = rec["state"].split("\n", 1)
        state = state.removeprefix("State: ")
        target = next(q["target"] for qid, q in rec["questions"].items() if qtype(qid) == qt)
        p = {k: float(np.mean([d[k] for d in dists])) for k in dists[0]}
        w = sizes[rec["state"]][qt]
        row = out[(qt, kind(rec["state"]))][state]
        base = pooled.get((cell, qt))
        pooled_p = {k: v / base[1] for k, v in base[0].items()} if base else None
        reg = regression.get((rec["state"], qt))
        row.append((w, tvd(p, target), tvd(pooled_p, target) if pooled_p else np.nan, tvd(reg, target) if reg else np.nan))

    report = {}
    print(f"{run} at temperature {temperature}: weighted TVD vs real shares on held-out states (lower is better)")
    print(f"{'question':10} {'records':18} {'state':15} {'cells':>5} {'kev':>6} {'pooled':>7} {'regression':>10}")
    for (qt, kd), states in sorted(out.items()):
        for state in HELD_OUT:
            rows = np.array(states.get(state, []), dtype=float)
            if not len(rows):
                continue
            avg = lambda col: float(np.average(rows[~np.isnan(rows[:, col]), col], weights=rows[~np.isnan(rows[:, col]), 0])) \
                if (~np.isnan(rows[:, col])).any() else float("nan")
            kev, pool, reg = avg(1), avg(2), avg(3)
            report[f"{qt}|{kd}|{state}"] = {"cells": len(rows), "kev": kev, "pooled": pool, "regression": reg}
            print(f"{qt:10} {kd:18} {state:15} {len(rows):5d} {kev:6.3f} {pool:7.3f} {reg:10.3f}")
    (RUNS / run / f"share_scores_T{temperature:g}.json").write_text(json.dumps(report, indent=1), encoding="utf-8")
    return report


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("run")
    ap.add_argument("--data", default=None, help="training data folder under data/kev (default: the run name)")
    ap.add_argument("--temperature", type=float, default=1.0)
    a = ap.parse_args()
    score(a.run, a.data, a.temperature)
