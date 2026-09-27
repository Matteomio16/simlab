"""Run the test bench: python -m simlab.run <null|mirror|events|fidelity|all> [--models ...] [--limit N]

Personas and cells come from simlab/archetypes.json and simlab/cells.json (rebuild: python -m simlab.ces).
Models run in parallel; single-order variants (jev1, glm1, ...) run after the rest so their calls come from
the cache. Results are printed and appended to runs/scorecard.jsonl with the spend each test caused.
"""
from __future__ import annotations

import argparse
import json
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from . import probes, tests
from .askers import make
from .ces import VOTE_OPTIONS
from .core import BUDGET_USD, LLMS, RUNS, Ledger

HERE = Path(__file__).parent
TESTS = ("null", "mirror", "events", "fidelity")


class Baseline:
    """The regression baseline (ces.crossfit) as an asker: returns each cell's precomputed prediction.
    Fidelity only, no API calls."""
    name = "regression"

    def __init__(self, cells: dict):
        self.pred = {(c["persona"], t): c["baseline"] for t, v in cells.items() for cs in v.values() for c in cs}

    def ask(self, state: str, question: dict, tag: str = "") -> dict:
        return self.pred[(state, "vote24" if question["type"] == "choice" else "turnout")]


def run_model(name: str, which: list[str], arch: list[dict], cells: dict) -> list[dict]:
    asker = Baseline(cells) if name == "regression" else make(name)
    texts = [p["text"] for p in arch]
    out = []
    for t in which:
        if name == "regression" and t != "fidelity":
            continue
        t0 = time.time()
        try:
            if t == "null":
                res = [tests.null_test(asker, texts)]
            elif t == "mirror":
                res = [tests.mirror_test(asker, texts)]
            elif t == "events":
                res = [tests.events_test(asker, [dict(p, text=p["text_events"]) for p in arch])]
            else:
                vq = probes.vote_question(VOTE_OPTIONS)
                res = [tests.fidelity(asker, cs, vq, f"vote24_{s}") for s, cs in cells["vote24"].items()]
                res += [tests.fidelity(asker, cs, probes.TURNOUT_Q, f"turnout_{s}") for s, cs in cells["turnout"].items()]
        except Exception as e:
            res = [{"test": t, "model": name, "error": f"{type(e).__name__}: {e}"[:300]}]
        usd = Ledger.spent(f"{t}:{name}", t0)
        for r in res:
            r.update(seconds=round(time.time() - t0), usd_test=round(usd, 5))
        out += res
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("test", choices=[*TESTS, "all"])
    ap.add_argument("--models", default="jev,kev,glm,mimo,deepseek,luna")
    ap.add_argument("--limit", type=int, default=0, help="first N personas / cells per scope only (quick check)")
    a = ap.parse_args()
    which = list(TESTS) if a.test == "all" else [a.test]
    arch = json.loads((HERE / "archetypes.json").read_text())
    cells = json.loads((HERE / "cells.json").read_text())
    if a.limit:
        arch = arch[:a.limit]
        cells = {t: {s: c[:a.limit] for s, c in v.items()} for t, v in cells.items()}
    names = a.models.split(",")
    single = [n for n in names if n.endswith("1") and n[:-1] in ("jev", "kev", *LLMS)]
    start, spent0, rows = time.time(), Ledger.total(), []
    for group in ([n for n in names if n not in single], single):
        if group:
            with ThreadPoolExecutor(len(group)) as ex:
                for res in ex.map(lambda n: run_model(n, which, arch, cells), group):
                    rows += res
    with (RUNS / "scorecard.jsonl").open("a") as f:
        for r in rows:
            f.write(json.dumps({"ts": start, "limit": a.limit, **r}) + "\n")
    for r in rows:
        vals = "  ".join(f"{k}={v:.3f}" if isinstance(v, float) else f"{k}={v}"
                         for k, v in r.items() if k not in ("test", "model"))
        print(f"{r['test']:24} {r['model']:9} {vals}")
    print(f"\nspent this run ${Ledger.total() - spent0:.4f}; ledger total ${Ledger.total():.4f} (cap ${BUDGET_USD:.2f})")


if __name__ == "__main__":
    main()
