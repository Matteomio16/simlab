"""Wider fidelity test (Field Guide: ~15 CES items), Jev and GLM only, all of a persona's questions in one request.

14 items from the CES 2024 file already downloaded. Two persona types: demographic cells (national + OH/NC/TX, as in
the first fidelity test) and agent-style cells (national demographics + party identification, the fields the
engine's agents carry). The regression baseline is fitted on the same fields, cross-fitted by state.

    python -m simlab.fidelity2 build                 # -> simlab/cells2.json
    python -m simlab.fidelity2 run jev,glm [--limit N]   # -> runs/fidelity2__<model>.jsonl, docs/fidelity2.md
"""
from __future__ import annotations

import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import pandas as pd
from scipy.special import expit
from sklearn.linear_model import LogisticRegression

from . import probes
from .askers import DecisionAsker, LLMAsker
from .ces import CELL_FIELDS, DATA, FIPS, VOTE_OPTIONS, _logit, load, turnout_shift
from .core import JEV, RUNS, Ledger
from .personas import render

HERE = RUNS.parent / "simlab"
DOCS = RUNS.parent / "docs"

APPROVE = {"strongly_approve": "Strongly approve", "somewhat_approve": "Somewhat approve",
           "somewhat_disapprove": "Somewhat disapprove", "strongly_disapprove": "Strongly disapprove",
           "not_sure": "Not sure"}
ECONOMY = {"much_better": "Gotten much better", "somewhat_better": "Gotten somewhat better",
           "same": "Stayed about the same", "somewhat_worse": "Gotten somewhat worse", "much_worse": "Gotten much worse",
           "not_sure": "Not sure"}
PRICES = {"up_a_lot": "Increased a lot", "up_somewhat": "Increased somewhat", "same": "Stayed about the same",
          "down_somewhat": "Decreased somewhat", "down_a_lot": "Decreased a lot"}
PARTIES = {"dem": "The Democratic candidate", "rep": "The Republican candidate", "other": "Another candidate"}
PARTY5 = {1: "Democrat", 2: "Democrat", 3: "Independent who leans Democratic", 4: "Independent",
          5: "Independent who leans Republican", 6: "Republican", 7: "Republican", 8: "Independent"}


def _choice(text: str, opts: dict) -> dict:
    return {"type": "choice", "instructions": text, "criteria": opts}


def _noul(text: str) -> dict:
    return {"type": "noul", "instructions": text}


# name: question, label column, population ('voters' validated, 'citizens', 'all'), headline labels for the bias check.
# vote24 and turnout keep the first fidelity test's exact wording (a Kev fine-tune binds these strings).
ITEMS = {
    "vote24": (probes.vote_question(VOTE_OPTIONS), "vote24", "voters", ("harris",)),
    "turnout": (probes.TURNOUT_Q, "turnout", "citizens", ("true",)),
    "senate24": (_choice("How did this person vote in their state's 2024 U.S. Senate race?", PARTIES),
                 "i_senate24", "voters", ("dem",)),
    "house24": (_choice("How did this person vote in the 2024 election for the U.S. House of Representatives?",
                        PARTIES), "i_house24", "voters", ("dem",)),
    "biden_approval": (_choice("In fall 2024, did this person approve or disapprove of the way Joe Biden was handling "
                               "his job as president?", APPROVE), "i_biden", "all",
                       ("strongly_approve", "somewhat_approve")),
    "congress_approval": (_choice("In fall 2024, did this person approve or disapprove of the way the U.S. Congress "
                                  "was doing its job?", APPROVE), "i_congress", "all",
                          ("strongly_approve", "somewhat_approve")),
    "scotus_approval": (_choice("In fall 2024, did this person approve or disapprove of the way the U.S. Supreme "
                                "Court was doing its job?", APPROVE), "i_scotus", "all",
                        ("strongly_approve", "somewhat_approve")),
    "economy": (_choice("In fall 2024, did this person think the nation's economy had gotten better or worse over the "
                        "past year?", ECONOMY), "i_economy", "all", ("much_better", "somewhat_better")),
    "prices": (_choice("In fall 2024, did this person say the prices of everyday goods and services had gone up or "
                       "down over the past year?", PRICES), "i_prices", "all", ("up_a_lot",)),
    "legal_status": (_noul("In fall 2024, did this person support granting legal status to undocumented immigrants "
                           "who have held jobs and paid taxes for at least 3 years and have no felony convictions?"),
                     "i_legal", "all", ("true",)),
    "border_wall": (_noul("In fall 2024, did this person support building a wall between the U.S. and Mexico?"),
                    "i_wall", "all", ("true",)),
    "abortion_choice": (_noul("In fall 2024, did this person support always allowing a woman to obtain an abortion "
                              "as a matter of choice?"), "i_abortion_choice", "all", ("true",)),
    "abortion_ban": (_noul("In fall 2024, did this person support making abortion illegal in all circumstances?"),
                     "i_abortion_ban", "all", ("true",)),
    "assault_ban": (_noul("In fall 2024, did this person support banning assault rifles?"), "i_assault", "all",
                    ("true",)),
}
OPINION_COLS = {"i_biden": ("CC24_312a", APPROVE), "i_congress": ("CC24_312b", APPROVE),
                "i_scotus": ("CC24_312c", APPROVE), "i_economy": ("CC24_301", ECONOMY), "i_prices": ("CC24_303", PRICES),
                "i_legal": ("CC24_323a", None), "i_wall": ("CC24_323c", None), "i_abortion_choice": ("CC24_324a", None),
                "i_abortion_ban": ("CC24_324c", None), "i_assault": ("CC24_321a", None)}
# Senate: codes 1-3 = candidates, 5 = other (6 didn't vote in the race, 8 not sure). House: 1-5, 10 = other.
RACES = {"i_senate24": ("CC24_411", "SenCand", 3, 5), "i_house24": ("CC24_412", "HouseCand", 5, 10)}


def frame() -> pd.DataFrame:
    df = load()
    extra = [c for c, _ in OPINION_COLS.values()] + [c for c, *_ in RACES.values()]
    extra += [f"{p}{k}Party_post" for _, p, n, _ in RACES.values() for k in range(1, n + 1)]
    df = df.join(pd.read_csv(next(DATA.glob("CCES24_*.csv")), usecols=extra, low_memory=False))
    for col, (src, labels) in OPINION_COLS.items():
        df[col] = df[src].map(dict(zip(range(1, len(labels) + 1), labels)) if labels else {1: "true", 2: "false"})
    for col, (src, prefix, n, other) in RACES.items():
        out = pd.Series(np.nan, index=df.index, dtype=object)
        for k in range(1, n + 1):
            m = df[src] == k
            out[m] = df.loc[m, f"{prefix}{k}Party_post"].map({"Democratic": "dem", "Republican": "rep"}).fillna("other")
        out[df[src] == other] = "other"
        df[col] = out.where(df.voted)
    df["party5"] = df.pid7.map(PARTY5)
    return df


def population(df: pd.DataFrame, item: str) -> tuple[pd.DataFrame, str]:
    _, col, pop, _ = ITEMS[item]
    if pop == "voters":
        return df[df.voted & df[col].notna() & df.vvweight_post.notna()], "vvweight_post"
    if pop == "citizens":
        return df[df.cit1 == 1], "commonweight"
    return df[df[col].notna()], "commonweight"


def crossfit(d: pd.DataFrame, y: str, w: str, features: list[str], folds: int = 5, seed: int = 0) -> pd.DataFrame:
    """Same baseline as ces.crossfit (weighted logistic regression, cross-fitted over folds of states) with a
    feature list, so agent-style cells can include party identification."""
    states = np.sort(d.inputstate.unique())
    np.random.default_rng(seed).shuffle(states)
    fold = d.inputstate.map({s: i % folds for i, s in enumerate(states)})
    X = pd.get_dummies(d[features].astype(str), dtype=float)
    out = pd.DataFrame(0.0, index=d.index, columns=sorted(d[y].unique()))
    for k in range(folds):
        te = fold == k
        m = LogisticRegression(max_iter=2000).fit(X[~te], d[y][~te], sample_weight=d[w][~te])
        out.loc[te, list(m.classes_)] = m.predict_proba(X[te])
    return out


def build() -> dict:
    df = frame()
    shifts = {s: turnout_shift(df, s) for s in (None, *FIPS.values())}
    demo_f, agent_f = ["age4", "gender4", "race5", "degree"], ["age4", "gender4", "race5", "degree", "party5"]
    preds = {}
    for item in ITEMS:
        d, w = population(df, item)
        preds[item] = {"demographic": crossfit(d, ITEMS[item][1], w, demo_f),
                       "agent": crossfit(d, ITEMS[item][1], w, agent_f)}
    layouts = [("demographic", "national", ["age4", "gender", "race5", "degree"], 50)]
    layouts += [("demographic", s, ["age2", "gender", "race4", "degree"], 30) for s in FIPS.values()]
    layouts += [("agent", "national", ["age2", "gender", "race4", "degree", "party5"], 50)]
    cells = []
    for kind, scope, by, min_n in layouts:
        d0 = df[df.gender.isin(["Man", "Woman"])]
        if scope != "national":
            d0 = d0[d0.state == scope]
        for key, g in d0.groupby(by):
            fields = {CELL_FIELDS.get(b, "party_id"): v for b, v in zip(by, key)}
            cell = {"kind": kind, "scope": scope, "persona": render({"state": None if scope == "national" else scope,
                                                                     **fields}),
                    "targets": {}, "baseline": {}, "n": {}}
            for item, (_, col, _, _) in ITEMS.items():
                d, w = population(g, item)
                if len(d) < min_n:
                    continue
                shares = (d.groupby(col)[w].sum() / d[w].sum()).to_dict()
                base = dict(zip(preds[item][kind].columns,
                                np.average(preds[item][kind].loc[d.index], axis=0, weights=d[w])))
                if item == "turnout":
                    k = shifts[None if scope == "national" else scope]
                    shares = {"true": float(expit(_logit(shares.get("true", 0.0)) + k))}
                    base = {"true": float(expit(_logit(base["true"]) + k))}
                    shares["false"], base["false"] = 1 - shares["true"], 1 - base["true"]
                cell["targets"][item] = {k2: round(float(v), 4) for k2, v in shares.items()}
                cell["baseline"][item] = {k2: round(float(v), 4) for k2, v in base.items()}
                cell["n"][item] = len(d)
            if cell["targets"]:
                cells.append(cell)
    out = {"items": {k: v[0] for k, v in ITEMS.items()}, "cells": cells}
    (HERE / "cells2.json").write_text(json.dumps(out, indent=1))
    by_kind = pd.Series([(c["kind"], c["scope"]) for c in cells]).value_counts()
    print(f"{len(cells)} cells, {sum(len(c['targets']) for c in cells)} cell-item targets\n{by_kind.to_string()}")
    return out


def _key(p: dict, labels: tuple) -> float:
    return sum(p.get(k, 0.0) for k in labels)


def metrics(rows: list[dict]) -> dict:
    """Per (kind, scope, item): weighted TVD, correlation and bias of the headline share."""
    out = {}
    df = pd.DataFrame(rows)
    for (kind, scope, item), g in df.groupby(["kind", "scope", "item"]):
        labels = ITEMS[item][3]
        tvd = [0.5 * sum(abs(p.get(k, 0) - t.get(k, 0)) for k in set(t) | {k for k in p if not k.startswith("_")})
               for p, t in zip(g.pred, g.target)]
        x, y = np.array([_key(p, labels) for p in g.pred]), np.array([_key(t, labels) for t in g.target])
        out[(kind, scope, item)] = {
            "cells": len(g), "tvd": float(np.average(tvd, weights=g.n)),
            "corr": float(np.corrcoef(x, y)[0, 1]) if len(g) > 2 and x.std() > 0 and y.std() > 0 else float("nan"),
            "bias": float(np.average(x - y, weights=g.n))}
    return out


def run(models: list[str], limit: int = 0) -> None:
    data = json.loads((HERE / "cells2.json").read_text())
    cells = data["cells"][:limit] if limit else data["cells"]
    askers = {"jev": DecisionAsker(JEV, n_orders=2, name="jev"), "glm": LLMAsker("glm", n_orders=2, name="glm")}
    votes = [i for i, v in ITEMS.items() if v[2] == "voters"]
    groups = {"glm": [[i for i in ITEMS if i not in votes], votes]}  # Jev answers each question in isolation
    results = {}
    for m in models:
        spent0 = Ledger.total()
        a = askers[m]
        kw = {"groups": groups[m]} if m in groups else {}
        with ThreadPoolExecutor(16) as ex:
            preds = list(ex.map(lambda c: a.ask_many(c["persona"], {i: data["items"][i] for i in c["targets"]},
                                                     f"fidelity2:{m}", **kw), cells))
        rows = [{"kind": c["kind"], "scope": c["scope"], "persona": c["persona"], "item": i, "n": c["n"][i],
                 "target": c["targets"][i], "pred": p[i]} for c, p in zip(cells, preds) for i in c["targets"]]
        if not limit:
            (RUNS / f"fidelity2__{m}.jsonl").write_text("\n".join(json.dumps(r) for r in rows))
        results[m] = (rows, Ledger.total() - spent0)
    base_rows = [{"kind": c["kind"], "scope": c["scope"], "persona": c["persona"], "item": i, "n": c["n"][i],
                  "target": c["targets"][i], "pred": c["baseline"][i]} for c in cells for i in c["targets"]]
    results["regression"] = (base_rows, 0.0)
    report(results, write=not limit)


def report(results: dict, write: bool = True) -> None:
    ms = {m: metrics(rows) for m, (rows, _) in results.items()}
    keys = sorted(next(iter(ms.values())))
    names = list(results)
    lines = ["# Wider fidelity test (14 CES 2024 items, Jev and GLM)", "",
             "Generated by `python -m simlab.fidelity2 run`. TVD = weighted total variation distance between predicted "
             "and real answer shares per cell (lower is better); bias = average predicted minus real headline share "
             "(approval = strongly + somewhat approve; support items = support; votes = Democratic share). Both models "
             "are asked every question in two option orders, all of a persona's questions at once.", "",
             "## Cost", "", "| model | spent | cells |", "|---|---|---|"]
    lines += [f"| {m} | ${usd:.4f} | {len({r['persona'] + r['scope'] for r in rows})} |"
              for m, (rows, usd) in results.items() if m != "regression"]
    for kind in ("demographic", "agent"):
        ks = [k for k in keys if k[0] == kind]
        lines += ["", f"## {'Demographics only' if kind == 'demographic' else 'Agent-style personas (with party ID)'}",
                  "", "| scope | item | cells | " + " | ".join(f"TVD {m}" for m in names) + " | "
                  + " | ".join(f"bias {m}" for m in names if m != "regression") + " |",
                  "|" + "---|" * (3 + len(names) + len(names) - 1)]
        for k in ks:
            lines.append(f"| {k[1]} | {k[2]} | {ms[names[0]][k]['cells']} | "
                         + " | ".join(f"{ms[m][k]['tvd']:.3f}" for m in names) + " | "
                         + " | ".join(f"{100 * ms[m][k]['bias']:+.0f}" for m in names if m != "regression") + " |")
        avg = {m: np.mean([ms[m][k]["tvd"] for k in ks]) for m in names}
        lines.append(f"| **all** | **average** | | " + " | ".join(f"**{avg[m]:.3f}**" for m in names) + " | |")
    if {"jev", "glm"} <= set(results):
        lines += ["", "## Do Jev and GLM make different mistakes?", "",
                  "Correlation of their errors on the headline share across cells (low = averaging them helps), and the "
                  "TVD of their average.", "", "| kind | item | error correlation | TVD jev | TVD glm | TVD average |",
                  "|---|---|---|---|---|---|"]
        rj = {(r["kind"], r["scope"], r["persona"], r["item"]): r for r in results["jev"][0]}
        rg = {(r["kind"], r["scope"], r["persona"], r["item"]): r for r in results["glm"][0]}
        for kind in ("demographic", "agent"):
            for item in ITEMS:
                ks = [k for k in rj if k[0] == kind and k[3] == item and k in rg]
                if len(ks) < 5:
                    continue
                lab = ITEMS[item][3]
                ej = np.array([_key(rj[k]["pred"], lab) - _key(rj[k]["target"], lab) for k in ks])
                eg = np.array([_key(rg[k]["pred"], lab) - _key(rg[k]["target"], lab) for k in ks])
                w = np.array([rj[k]["n"] for k in ks])

                def tv(p, t):
                    return 0.5 * sum(abs(p.get(x, 0) - t.get(x, 0)) for x in set(t) | {x for x in p if x[0] != "_"})
                avg = [{x: (rj[k]["pred"].get(x, 0) + rg[k]["pred"].get(x, 0)) / 2
                        for x in set(rj[k]["pred"]) | set(rg[k]["pred"])} for k in ks]
                lines.append(f"| {kind} | {item} | {np.corrcoef(ej, eg)[0, 1]:+.2f} | "
                             f"{np.average([tv(rj[k]['pred'], rj[k]['target']) for k in ks], weights=w):.3f} | "
                             f"{np.average([tv(rg[k]['pred'], rg[k]['target']) for k in ks], weights=w):.3f} | "
                             f"{np.average([tv(a, rj[k]['target']) for a, k in zip(avg, ks)], weights=w):.3f} |")
    md = "\n".join(lines)
    if write:
        (DOCS / "fidelity2.md").write_text(md, encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print(md)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["build", "run"])
    ap.add_argument("models", nargs="?", default="jev,glm")
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()
    build() if a.cmd == "build" else run(a.models.split(","), a.limit)
