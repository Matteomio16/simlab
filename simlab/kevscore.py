"""Score a Kev fine-tune against the soft targets it was trained to reproduce.

For every held-out record (Ohio, North Carolina, Texas) and question type: total variation distance between the model's
probabilities (at a chosen temperature; 1.0 = raw) and the real shares, weighted by the respondents behind each cell.
Baselines: the same cell pooled over the training states (no model at all) and, for the 2024 demographic cells, the
regression baseline of the fidelity test. Kev's own report scores hard labels, which is not what the engine needs.

    python -m simlab.kevscore ces-v2 [--temperature 1.0]
    python -m simlab.kevscore ces-v1 ces-v2 ces-v3a ces-v3b     # paired comparison on the cells all runs answer
    python -m simlab.kevscore --groups ces-v3b                  # the 28 voter groups against groups_base.json's d0
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.special import softmax

from .ces import DATA

HERE = Path(__file__).parent
RUNS = HERE.parent / "kev-finetune" / "runs"
HELD_OUT = ("Ohio", "North Carolina", "Texas")


def jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


V1 = {"vote0": "pres24", "vote1": "pres24", "vote2": "pres24", "turnout": "turnout24"}   # ces-v1 question ids


def qtype(qid: str) -> str:
    return V1.get(qid) or (qid.rsplit("_", 1)[0] if qid[-2:-1] == "_" else qid)


def kind(persona: str) -> str:
    return "party strata" if "Party identification" in persona else \
        "2020-vote cells" if "2020 presidential vote" in persona else "demographic cells"


def tvd(p: dict, t: dict) -> float:
    return 0.5 * sum(abs(p.get(k, 0.0) - t.get(k, 0.0)) for k in p.keys() | t.keys())


def cell_errors(run: str, data: str | None = None, temperature: float = 1.0) -> pd.DataFrame:
    """One row per held-out (cell, question type): respondents behind the target and the TVD of Kev, the pooled
    same-cell baseline and the regression baseline. ces-v1 has no sizes.json; its cells are ces-v2's."""
    folder = DATA / "kev" / (data or run)
    dev, rest = jsonl(folder / "development.jsonl"), jsonl(folder / "train.jsonl") + jsonl(folder / "calibration.jsonl")
    sizes = json.loads(next(f for f in (folder / "sizes.json", DATA / "kev" / "ces-v2" / "sizes.json")
                            if f.exists()).read_text())
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
        for qt, q in {qtype(qid): q for qid, q in r["questions"].items()}.items():
            w = sizes[r["state"]][qt]
            acc = pooled[(cell, qt)]
            for k, v in q["target"].items():
                acc[0][k] += w * v
            acc[1] += w

    rows = []
    for (i, qt), dists in pred.items():
        rec = dev[i]
        state, cell = rec["state"].split("\n", 1)
        target = next(q["target"] for qid, q in rec["questions"].items() if qtype(qid) == qt)
        p = {k: float(np.mean([d[k] for d in dists])) for k in dists[0]}
        base, reg = pooled.get((cell, qt)), regression.get((rec["state"], qt))
        rows.append({"question": qt, "records": kind(rec["state"]), "state": state.removeprefix("State: "),
                     "persona": rec["state"], "target": json.dumps(target, sort_keys=True),
                     "weight": sizes[rec["state"]][qt], "kev": tvd(p, target),
                     "pooled": tvd({k: v / base[1] for k, v in base[0].items()}, target) if base else np.nan,
                     "regression": tvd(reg, target) if reg else np.nan})
    return pd.DataFrame(rows)


def wmean(d: pd.DataFrame, col: str) -> float:
    ok = d[col].notna()
    return float(np.average(d[col][ok], weights=d.weight[ok])) if ok.any() else float("nan")


def score(run: str, data: str | None = None, temperature: float = 1.0) -> dict:
    report = {}
    print(f"{run} at temperature {temperature}: weighted TVD vs real shares on held-out states (lower is better)")
    print(f"{'question':10} {'records':18} {'state':15} {'cells':>5} {'kev':>6} {'pooled':>7} {'regression':>10}")
    for (qt, kd, state), d in cell_errors(run, data, temperature).groupby(["question", "records", "state"]):
        kev, pool, reg = wmean(d, "kev"), wmean(d, "pooled"), wmean(d, "regression")
        report[f"{qt}|{kd}|{state}"] = {"cells": len(d), "kev": kev, "pooled": pool, "regression": reg}
        print(f"{qt:10} {kd:18} {state:15} {len(d):5d} {kev:6.3f} {pool:7.3f} {reg:10.3f}")
    (RUNS / run / f"share_scores_T{temperature:g}.json").write_text(json.dumps(report, indent=1), encoding="utf-8")
    return report


def compare(runs: list[str], temperature: float = 1.0, draws: int = 2000, seed: int = 0) -> None:
    """Runs on the held-out cells they all answer with the same target, OH/NC/TX pooled: weighted TVD per run, and
    each run minus the first with a 95% interval from resampling cells (dev-set noise only; a second training seed
    would add run noise)."""
    frames = {r: cell_errors(r).set_index(["question", "records", "persona"]) for r in runs}
    common = frames[runs[0]].index
    for f in frames.values():
        common = common.intersection(f.index)
    common = common[[len({frames[r].loc[i, "target"] for r in runs}) == 1 for i in common]]   # same target in every run
    rng = np.random.default_rng(seed)
    print(f"weighted TVD on shared held-out cells at temperature {temperature}; delta = run - {runs[0]} [95% interval]")
    for (qt, kd), idx in pd.DataFrame(index=common).groupby(level=[0, 1]):
        first = frames[runs[0]].loc[idx.index]
        w = first.weight.to_numpy()
        boot = rng.choice(len(w), (draws, len(w)))
        line = [f"{qt} {kd} ({len(w)} cells): pooled {wmean(first, 'pooled'):.3f}"]
        for r in runs:
            e = frames[r].loc[idx.index, "kev"].to_numpy()
            line.append(f"{r} {np.average(e, weights=w):.3f}")
            if r != runs[0]:
                diff = e - first.kev.to_numpy()
                lo, hi = np.percentile([np.average(diff[b], weights=w[b]) for b in boot], [2.5, 97.5])
                line[-1] += f" ({np.average(diff, weights=w):+.3f} [{lo:+.3f}, {hi:+.3f}])"
        print("; ".join(line))


def groups(run: str, draws: int = 2000, seed: int = 0) -> dict:
    """Kev's 2024 margin for the engine's voter groups (party ID x white/non-white x degree) in the held-out states
    against Statistics' d0 (groups_base.json), both scored on CES validated voters. 'shifted' moves both to the
    state's true level with groups.shift, as the engine does, so only the pattern across groups is compared."""
    from .groups import BASE, shift
    code = {"Ohio": "OH", "North Carolina": "NC", "Texas": "TX"}
    base = json.loads(BASE.read_text(encoding="utf-8"))["states"]
    dev = jsonl(DATA / "kev" / run / "development.jsonl")
    kev, truth = defaultdict(list), {}
    for r in json.loads((RUNS / run / "development" / "rows.json").read_text(encoding="utf-8")):
        rec = dev[int(r["id"].split("/")[1])]
        f = dict(line.split(": ", 1) for line in rec["state"].split("\n"))
        if not r["question"].startswith("pres24") or "Party identification" not in f:
            continue
        key = (code[f["State"]], f"{f['Party identification']} / {f['Race/ethnicity'].lower()} / {f['Education']}")
        p = dict(zip(r["keys"], softmax(np.array(r["logits"]))))
        t = rec["questions"][r["question"]]["target"]
        kev[key].append((p["harris"] - p["trump"]) / (p["harris"] + p["trump"]))
        truth[key] = (t["harris"] - t["trump"]) / (t["harris"] + t["trump"])
    keys = sorted(truth)
    y = np.array([truth[k] for k in keys])
    w = np.array([base[s][g]["n"] * base[s][g]["t"] for s, g in keys])
    st = np.array([s for s, _ in keys])
    raw = {"kev": np.array([np.mean(kev[k]) for k in keys]), "stats": np.array([base[s][g]["d0"] for s, g in keys])}
    shifted = {m: v.copy() for m, v in raw.items()}
    for m, v in shifted.items():
        for s in code.values():
            i = st == s
            v[i] = shift(raw[m][i], w[i], float(np.dot(w[i], y[i]) / w[i].sum()))
    rng = np.random.default_rng(seed)
    boot = [rng.integers(0, len(y), len(y)) for _ in range(draws)]
    out = {"run": run, "groups": len(keys)}
    for label, v in (("raw", raw), ("shifted", shifted)):
        e = {m: np.abs(x - y) * 100 for m, x in v.items()}
        diff = [np.average(e["kev"][b], weights=w[b]) - np.average(e["stats"][b], weights=w[b]) for b in boot]
        out[label] = {"kev": np.average(e["kev"], weights=w), "stats": np.average(e["stats"], weights=w),
                      "kev_minus_stats_95": list(np.percentile(diff, [2.5, 97.5])),
                      "by_state": {s: {m: np.average(e[m][st == s], weights=w[st == s]) for m in e} for s in code.values()}}
    out = json.loads(json.dumps(out, default=float), parse_float=lambda x: round(float(x), 2))
    print(json.dumps(out, indent=1))
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("runs", nargs="+", help="one run to score, or several to compare (the first is the reference)")
    ap.add_argument("--data", default=None, help="training data folder under data/kev (default: the run name)")
    ap.add_argument("--temperature", type=float, default=1.0)
    ap.add_argument("--groups", action="store_true", help="score the engine's voter groups against groups_base.json")
    a = ap.parse_args()
    if a.groups:
        [groups(r) for r in a.runs]
    else:
        score(a.runs[0], a.data, a.temperature) if len(a.runs) == 1 else compare(a.runs, a.temperature)
