"""The four checks for any model (Jev, Kev, our fine-tuned Kev, GLM, MiMo, DeepSeek, Luna).

1. fidelity  - reproduce real survey distributions (CES 2024 cells)
2. null      - politically irrelevant news should produce "no change"
3. mirror    - swapping the party of the actor should flip the reaction
4. events    - reaction direction and size vs measured shifts after real events

Each returns a metrics dict and writes per-item rows to runs/<test>__<model>.jsonl.
"""
from __future__ import annotations

import json
import math
import random
from pathlib import Path

import numpy as np
from scipy.stats import pearsonr, spearmanr

from . import probes
from .askers import batch, expected
from .core import RUNS

EVENTS = json.loads((Path(__file__).parent / "events.json").read_text())


def _save(name: str, model: str, rows: list[dict]):
    p = RUNS / f"{name}__{model}.jsonl"
    p.write_text("\n".join(json.dumps(r) for r in rows))


# ------------------------------------------------------------------ 1. fidelity
def fidelity(asker, cells: list[dict], question: dict, target_key: str) -> dict:
    """cells: [{persona: str, n: int, target: {option: share}}]. question: System One choice/noul."""
    items = [(c["persona"], question) for c in cells]
    preds = batch(asker, items, tag="fidelity")
    rows, tvds, ws = [], [], []
    for c, p in zip(cells, preds):
        t = c["target"]
        keys = set(t) | {k for k in p if not k.startswith("_")}
        tvd = 0.5 * sum(abs(p.get(k, 0) - t.get(k, 0)) for k in keys)
        tvds.append(tvd)
        ws.append(c["n"])
        rows.append({"persona": c["persona"], "n": c["n"], "target": t, "pred": p, "tvd": tvd})
    _save(f"fidelity_{target_key}", asker.name, rows)
    first = next(iter(cells[0]["target"]))
    x = [r["pred"].get(first, 0) for r in rows]
    y = [r["target"].get(first, 0) for r in rows]
    # Brier-style score treating each cell's true shares as the outcome distribution
    return {"test": f"fidelity_{target_key}", "model": asker.name, "cells": len(cells),
            "tvd_weighted": float(np.average(tvds, weights=ws)),
            f"corr_{first}": float(pearsonr(x, y)[0]) if len(set(x)) > 1 else float("nan"),
            "mean_abs_err_" + first: float(np.average(np.abs(np.array(x) - np.array(y)), weights=ws))}


# ------------------------------------------------------------------ 2. null
def null_test(asker, personas: list[str], news: list[str] | None = None) -> dict:
    news = news or probes.NULL_NEWS
    items, meta = [], []
    for p in personas:
        for n in news:
            st = probes.reaction_state(p, n)
            for qk in ("support", "turnout"):
                items.append((st, probes.REACTION_QUESTIONS[qk]))
                meta.append((p, n, qk))
    preds = batch(asker, items, tag="null")
    rows = [{"persona": m[0], "news": m[1], "q": m[2], "pred": pr} for m, pr in zip(meta, preds)]
    _save("null", asker.name, rows)
    out = {"test": "null", "model": asker.name, "n": len(rows)}
    for qk in ("support", "turnout"):
        rs = [r for r in rows if r["q"] == qk]
        p_none = [r["pred"].get("2", 0) for r in rs]
        e = [abs(expected(r["pred"])) for r in rs]
        out[f"{qk}_p_no_change"] = float(np.mean(p_none))
        out[f"{qk}_mean_abs_shift"] = float(np.mean(e))
        out[f"{qk}_argmax_not_nochange"] = float(np.mean([max(r["pred"], key=lambda k: r["pred"][k] if not k.startswith("_") else -1) != "2" for r in rs]))
    return out


# ------------------------------------------------------------------ 3. mirror
def mirror_test(asker, personas: list[str]) -> dict:
    items, meta = [], []
    for p in personas:
        for i in range(len(probes.MIRROR_TEMPLATES)):
            d_news, r_news = probes.mirror_pair(i)
            for side, news in (("D", d_news), ("R", r_news)):
                items.append((probes.reaction_state(p, news), probes.REACTION_QUESTIONS["support"]))
                meta.append((p, i, side))
    preds = batch(asker, items, tag="mirror")
    by = {}
    for m, pr in zip(meta, preds):
        by.setdefault((m[0], m[1]), {})[m[2]] = expected(pr)
    ed = np.array([v["D"] for v in by.values()])
    er = np.array([v["R"] for v in by.values()])
    moved = (np.abs(ed) > 0.1) | (np.abs(er) > 0.1)
    sign_ok = np.mean(np.sign(ed[moved]) == -np.sign(er[moved])) if moved.any() else float("nan")
    rows = [{"persona": k[0], "template": k[1], "E_D": v["D"], "E_R": v["R"]} for k, v in by.items()]
    _save("mirror", asker.name, rows)
    return {"test": "mirror", "model": asker.name, "pairs": len(rows),
            "flip_corr": float(pearsonr(ed, -er)[0]) if ed.std() > 0 and er.std() > 0 else float("nan"),
            "sign_flip_rate": float(sign_ok),
            "mean_asymmetry": float(np.mean(ed + er)),  # >0 = leans pro-D, <0 = leans pro-R
            "mean_abs_reaction": float(np.mean(np.abs(np.r_[ed, er])))}


# ------------------------------------------------------------------ 4. events
EVENT_Q = {"type": "score",
           "instructions": "After this news, how does this person's support between the Democratic and Republican parties change, if at all?",
           "criteria": ["Moves strongly toward the Republicans", "Moves slightly toward the Republicans", "No change",
                        "Moves slightly toward the Democrats", "Moves strongly toward the Democrats"]}


def events_test(asker, personas: list[dict]) -> dict:
    """personas: [{text, weight, party: 'D'|'R'|'I'}] - a weighted sample of the electorate.
    Personas are described as of the event date (no year-specific facts), news from EVENTS."""
    items, meta = [], []
    for ev in EVENTS:
        news = f"({ev['date']}) {ev['description']}"
        for p in personas:
            items.append((probes.reaction_state(p["text"], news), EVENT_Q))
            meta.append((ev["id"], p))
    preds = batch(asker, items, tag="events")
    agg: dict = {}
    for (eid, p), pr in zip(meta, preds):
        a = agg.setdefault(eid, {"all": [0.0, 0.0], "D": [0.0, 0.0], "R": [0.0, 0.0], "I": [0.0, 0.0]})
        e = expected(pr)
        for g in ("all", p["party"]):
            a[g][0] += e * p["weight"]
            a[g][1] += p["weight"]
    rows = []
    for ev in EVENTS:
        a = agg[ev["id"]]
        pred = {g: (v[0] / v[1] if v[1] else None) for g, v in a.items()}
        rows.append({"id": ev["id"], "measured": ev["shift_toward_D"], "measured_party": ev["party"],
                     "weight": ev["weight"], "pred": pred})
    _save("events", asker.name, rows)
    x = np.array([r["pred"]["all"] for r in rows])
    y = np.array([r["measured"] for r in rows], float)
    w = np.array([r["weight"] for r in rows])
    k = float(np.sum(w * x * y) / np.sum(w * x * x)) if np.sum(x * x) > 0 else float("nan")  # points per unit
    nonnull = np.abs(y) >= 2
    party_pairs = [(r["pred"][g], r["measured_party"][g]) for r in rows if r["measured_party"]
                   for g in "DRI" if r["measured_party"].get(g) is not None and r["pred"][g] is not None]
    return {"test": "events", "model": asker.name, "events": len(rows),
            "spearman": float(spearmanr(x, y)[0]),
            "sign_accuracy_nonnull": float(np.mean(np.sign(x[nonnull]) == np.sign(y[nonnull]))),
            "null_events_mean_abs_pred": float(np.mean(np.abs(x[~nonnull]))),
            "scale_points_per_unit": k,
            "rmse_after_scaling": float(np.sqrt(np.average((k * x - y) ** 2, weights=w))),
            "party_corr": float(pearsonr(*zip(*party_pairs))[0]) if len(party_pairs) > 3 else float("nan")}
