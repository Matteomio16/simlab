"""CES 2024 (Cooperative Election Study) -> weighted demographic cells and personas.

Download: Harvard Dataverse doi:10.7910/DVN/X11EP6 (free, no registration).
Variable names are auto-detected from a list of candidates and printed, so a
renamed column fails loudly instead of silently.
"""
from __future__ import annotations

import io
import json
from pathlib import Path

import numpy as np
import pandas as pd
import requests
from scipy.optimize import brentq
from scipy.special import expit
from sklearn.linear_model import LogisticRegression

from .core import RUNS
from .personas import render

DATA = RUNS.parent / "data"
DATA.mkdir(exist_ok=True)
DOI = "doi:10.7910/DVN/X11EP6"
DV = "https://dataverse.harvard.edu/api"
UA = {"User-Agent": "simlab/0.1 (research; +https://scaliastudio.dev)"}  # Dataverse 403s the python-requests default

FIPS = {39: "Ohio", 37: "North Carolina", 48: "Texas"}


def download() -> Path:
    """The CSV (175 MB; the .dta is 947 MB) and the CES guide PDF (codebook). Returns the CSV path."""
    r = requests.get(f"{DV}/datasets/:persistentId/?persistentId={DOI}", headers=UA, timeout=60)
    r.raise_for_status()
    files = [f["dataFile"] for f in r.json()["data"]["latestVersion"]["files"]]
    csv = next(f for f in files if f["filename"].lower().endswith(".csv"))
    guide = next(f for f in files if f["filename"].lower().endswith(".pdf"))
    for f in (csv, guide):
        out = DATA / f["filename"]
        if out.exists():
            continue
        part = out.with_name(out.name + ".part")
        with requests.get(f"{DV}/access/datafile/{f['id']}", headers=UA, stream=True, timeout=600) as r:
            r.raise_for_status()
            with part.open("wb") as fh:
                for chunk in r.iter_content(1 << 20):
                    fh.write(chunk)
        if part.stat().st_size != f["filesize"]:
            raise IOError(f"{f['filename']}: got {part.stat().st_size} bytes, expected {f['filesize']}")
        part.replace(out)
    return DATA / csv["filename"]


# Code -> label, checked against CES_2024_GUIDE_vv.pdf by matching every category's count (27 Sep 2026).
# The guide's listing order is not the code order (e.g. race 8 = Middle Eastern, pid7 lists Strong R third).
GENDER = {1: "Man", 2: "Woman", 3: "Non-binary", 4: "Other"}
EDUC = {1: "No high school diploma", 2: "High school graduate", 3: "Some college", 4: "2-year degree",
        5: "4-year degree", 6: "Post-graduate degree"}
RACE = {1: "White", 2: "Black", 3: "Hispanic", 4: "Asian", 5: "Native American", 6: "Two or more races",
        7: "Other", 8: "Middle Eastern"}
PID7 = {1: "Strong Democrat", 2: "Not very strong Democrat", 3: "Lean Democrat", 4: "Independent",
        5: "Lean Republican", 6: "Not very strong Republican", 7: "Strong Republican", 8: "Not sure"}
IDEO5 = {1: "Very liberal", 2: "Liberal", 3: "Moderate", 4: "Conservative", 5: "Very conservative", 6: "Not sure"}
URBAN = {1: "City", 2: "Suburb", 3: "Town", 4: "Rural area", 5: "Other"}
RELIG = {1: "Protestant", 2: "Roman Catholic", 3: "Mormon", 4: "Eastern or Greek Orthodox", 5: "Jewish",
         6: "Muslim", 7: "Buddhist", 8: "Hindu", 9: "Atheist", 10: "Agnostic", 11: "Nothing in particular",
         12: "Something else"}
NEWSINT = {1: "Most of the time", 2: "Some of the time", 3: "Only now and then", 4: "Hardly at all"}
INCOME = dict(enumerate(["Less than $10,000", "$10,000 - $19,999", "$20,000 - $29,999", "$30,000 - $39,999",
                         "$40,000 - $49,999", "$50,000 - $59,999", "$60,000 - $69,999", "$70,000 - $79,999",
                         "$80,000 - $99,999", "$100,000 - $119,999", "$120,000 - $149,999",
                         "$150,000 - $199,999", "$200,000 - $249,999", "$250,000 - $349,999",
                         "$350,000 - $499,999", "$500,000 or more"], start=1))
VOTE20 = {1: "Joe Biden", 2: "Donald Trump", 3: "Jo Jorgensen", 4: "Howie Hawkins", 5: "Other", 6: "Did not vote"}
VOTE24 = {1: "harris", 2: "trump", 3: "other", 4: "other", 5: "other", 6: "other", 8: "other"}  # 9 = no pres vote
VOTE_OPTIONS = {"harris": "Kamala Harris, the Democratic candidate", "trump": "Donald Trump, the Republican candidate",
                "other": "Another candidate"}

COLS = ["inputstate", "birthyr", "gender4", "race", "hispanic", "educ", "faminc_new", "pid7", "ideo5", "religpew",
        "urbancity", "newsint", "presvote20post", "CC24_410", "TS_g2024", "cit1", "commonweight", "vvweight_post"]
VEP_TURNOUT_2024 = 0.639  # UF Election Lab (McDonald): 2024 turnout, share of the voting-eligible population


def load(path: Path | None = None) -> pd.DataFrame:
    """Respondent table with derived fields. voted = validated 2024 general vote (TS_g2024 1-6; unmatched
    respondents count as non-voters, the guide's specification 1)."""
    df = pd.read_csv(path or next(DATA.glob("CCES24_*.csv")), usecols=COLS, low_memory=False)
    age = 2024 - df.birthyr
    df["age4"] = pd.cut(age, [17, 29, 44, 64, 200], labels=["18-29", "30-44", "45-64", "65+"]).astype(str)
    df["age2"] = np.where(age < 45, "18-44", "45+")
    df["gender"] = df.gender4.map(GENDER)
    df["race5"] = np.where(df.hispanic == 1, "Hispanic",
                           df.race.map({1: "White", 2: "Black", 3: "Hispanic", 4: "Asian"}).fillna("Other"))
    df["race4"] = df.race5.replace({"Asian": "Other"})
    df["degree"] = np.where(df.educ >= 5, "Four-year college degree or more", "No four-year college degree")
    df["state"] = df.inputstate.map(FIPS)
    df["voted"] = df.TS_g2024.between(1, 6)
    df["turnout"] = np.where(df.voted, "true", "false")
    df["vote24"] = df.CC24_410.map(VOTE24).where(df.voted)
    return df


CELL_FIELDS = {"age4": "age", "age2": "age", "gender": "gender", "race5": "race", "race4": "race",
               "degree": "education"}


def _logit(p):
    p = np.clip(p, 0.005, 0.995)
    return np.log(p / (1 - p))


def turnout_shift(df: pd.DataFrame) -> float:
    """Logit shift that lifts CES validated turnout (citizens, commonweight) to the official 2024 rate.
    About a third of respondents weren't matched to a voter file and count as non-voters, so the raw rate
    (~55%) understates turnout; one shift for every cell keeps each cell's relative position."""
    g = df[df.cit1 == 1].groupby(["age4", "gender4", "race5", "degree"])
    p = g.apply(lambda x: np.average(x.voted, weights=x.commonweight))
    w = g.commonweight.sum()
    return brentq(lambda c: np.average(expit(_logit(p) + c), weights=w) - VEP_TURNOUT_2024, -5, 5)


def crossfit(d: pd.DataFrame, y: str, w: str, folds: int = 5, seed: int = 0) -> pd.DataFrame:
    """Plain regression baseline (Field Guide): weighted logistic regression on age, gender, race and degree, main
    effects only, cross-fitted over folds of states, so every respondent is predicted by a model that never saw
    their state. Returns one probability column per outcome."""
    states = np.sort(d.inputstate.unique())
    np.random.default_rng(seed).shuffle(states)
    fold = d.inputstate.map({s: i % folds for i, s in enumerate(states)})
    X = pd.get_dummies(d[["age4", "gender4", "race5", "degree"]].astype(str), dtype=float)
    out = pd.DataFrame(0.0, index=d.index, columns=sorted(d[y].unique()))
    for k in range(folds):
        te = fold == k
        m = LogisticRegression(max_iter=2000).fit(X[~te], d[y][~te], sample_weight=d[w][~te])
        out.loc[te, list(m.classes_)] = m.predict_proba(X[te])
    return out


def cells(df: pd.DataFrame, target: str, state: str | None = None, min_n: int | None = None,
          shift: float = 0.0, pred: pd.DataFrame | None = None) -> list[dict]:
    """Weighted target shares per demographic cell (persona = the cell's fields only; targets never enter it).
    target 'vote24': validated voters, vvweight_post. 'turnout': citizens, commonweight, logit-shifted by `shift`.
    National cells: age4 x gender x race5 x degree; state cells are coarser: age2 x gender x race4 x degree.
    `pred` (respondent-level baseline probabilities) adds each cell's weighted-mean baseline prediction."""
    by = ["age2", "gender", "race4", "degree"] if state else ["age4", "gender", "race5", "degree"]
    d = df[df.gender.isin(["Man", "Woman"])]
    if state:
        d = d[d.state == state]
    if target == "vote24":
        d, w = d[d.vote24.notna() & d.vvweight_post.notna()], "vvweight_post"
    else:
        d, w = d[d.cit1 == 1], "commonweight"
    out = []
    for key, g in d.groupby(by):
        if len(g) < (min_n or (30 if state else 50)):
            continue
        shares = (g.groupby(target)[w].sum() / g[w].sum()).to_dict()
        if target == "turnout":
            raw = shares.get("true", 0.0)
            shares = {"true": float(expit(_logit(raw) + shift)), "false": float(1 - expit(_logit(raw) + shift)),
                      "raw_true": raw}
        fields = {CELL_FIELDS[b]: v for b, v in zip(by, key)}
        cell = {"persona": render({"state": state, **fields}), "n": len(g), "scope": state or "national",
                "target": {k: round(float(v), 4) for k, v in shares.items() if k != "raw_true"},
                **({"raw_true": round(float(shares["raw_true"]), 4)} if target == "turnout" else {})}
        if pred is not None:
            b = dict(zip(pred.columns, np.average(pred.loc[g.index], axis=0, weights=g[w])))
            if target == "turnout":
                b = {"true": float(expit(_logit(b["true"]) + shift))}
                b["false"] = 1 - b["true"]
            cell["baseline"] = {k: round(float(v), 4) for k, v in b.items()}
        out.append(cell)
    return out


def _fields(r) -> dict:
    return {"state": FIPS.get(r.inputstate), "age": r.age4, "gender": GENDER.get(r.gender4),
            "race": RACE.get(r.race) if r.race5 == "Other" else r.race5, "education": EDUC.get(r.educ),
            "income": INCOME.get(r.faminc_new), "religion": RELIG.get(r.religpew), "area": URBAN.get(r.urbancity),
            "party_id": PID7.get(r.pid7), "ideology": IDEO5.get(r.ideo5), "vote_2020": VOTE20.get(r.presvote20post),
            "interest": NEWSINT.get(r.newsint)}


def archetypes(df: pd.DataFrame, draws: int = 3000, seed: int = 0) -> list[dict]:
    """28 strata (7-point party ID x white/non-white x degree) weighted by national adult share. Each stratum is
    represented by one real OH/NC/TX respondent (every persona lives in a state with a 2026 Senate race), drawn
    with probability proportional to survey weight; of `draws` candidate sets, the one whose weighted gender, age,
    race and ideology mix is closest to the national mix is kept. text_events drops the year-specific 2020 vote."""
    d = df.assign(pid=df.pid7.replace({8: 4}), white=df.race5 == "White")
    total = d.commonweight.sum()
    strata = [(k, g.commonweight.sum() / total, g[g.inputstate.isin(list(FIPS))])
              for k, g in d.groupby(["pid", "white", "degree"])]
    w = np.array([s[1] for s in strata])
    target = {t: d.groupby(t).commonweight.sum() / total for t in ("gender4", "age4", "race5", "ideo5")}
    rng = np.random.default_rng(seed)
    best, best_gap = None, np.inf
    for _ in range(draws):
        picks = [pool.iloc[rng.choice(len(pool), p=pool.commonweight / pool.commonweight.sum())]
                 for _, _, pool in strata]
        gap = sum(0.5 * sum(abs(w[[p[t] == v for p in picks]].sum() - share) for v, share in target[t].items())
                  for t in target)
        if gap < best_gap:
            best, best_gap = picks, gap
    print(f"archetype draw: gap {best_gap:.3f} (sum of gender, age, race, ideology TVDs) after {draws} draws")
    out = []
    for ((pid, white, deg), wt, _), r in zip(strata, best):
        f = _fields(r)
        out.append({"id": f"{PID7[pid]} / {'white' if white else 'non-white'} / {deg}",
                    "party": "D" if pid in (1, 2) else "R" if pid in (6, 7) else "I",
                    "weight": round(float(wt), 5), "text": render(f), "text_events": render(f, drop=("vote_2020",))})
    return out


def build() -> None:
    """Write simlab/archetypes.json and simlab/cells.json from the downloaded CES file."""
    df = load(download())
    here = Path(__file__).parent
    arch = archetypes(df)
    (here / "archetypes.json").write_text(json.dumps(arch, indent=1))
    shift = turnout_shift(df)
    preds = {"vote24": crossfit(df[df.vote24.notna() & df.vvweight_post.notna()], "vote24", "vvweight_post"),
             "turnout": crossfit(df[df.cit1 == 1], "turnout", "commonweight")}
    out = {t: {s or "national": cells(df, t, s, shift=shift, pred=preds[t]) for s in (None, *FIPS.values())}
           for t in ("vote24", "turnout")}
    (here / "cells.json").write_text(json.dumps(out, indent=1))
    c = df[df.cit1 == 1]
    print(f"respondents {len(df)}, citizens' validated turnout {np.average(c.voted, weights=c.commonweight):.3f}, "
          f"logit shift to {VEP_TURNOUT_2024}: {shift:+.3f}")
    v = df[df.vote24.notna() & df.vvweight_post.notna()]
    print("weighted 2024 vote (validated voters):",
          (v.groupby("vote24").vvweight_post.sum() / v.vvweight_post.sum()).round(3).to_dict())
    print(f"archetypes: {len(arch)}, weights sum {sum(a['weight'] for a in arch):.3f}, "
          f"party {pd.Series([a['party'] for a in arch]).value_counts().to_dict()}")
    for t, scopes in out.items():
        print(t, {s: (len(c), sum(x['n'] for x in c)) for s, c in scopes.items()})


if __name__ == "__main__":
    build()
