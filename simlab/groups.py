"""Voter groups: the 28 party-ID x white/non-white x degree groups (engine-design §3.1, stats-groundwork §5.5).

    python -m simlab.groups --fit     writes simlab/pimu.json

pi, the persuadable share, and mu, the mobilisable share, by state and group, from the CES pre- and post-election
waves of the 2018 and 2022 midterms (CES cumulative file), shrunk state -> census division -> nation. 2024 is kept as a
check.
"""
from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

from .calib import DIVISION
from .statsdata import DATA

HERE = Path(__file__).parent
GROUPS = [a["id"] for a in json.loads((HERE / "archetypes.json").read_text(encoding="utf-8"))]
PID = {"strong democrat": "Strong Democrat", "not very strong democrat": "Not very strong Democrat",
       "lean democrat": "Lean Democrat", "independent": "Independent", "not sure": "Independent",
       "don't know": "Independent", "lean republican": "Lean Republican",
       "not very strong republican": "Not very strong Republican", "strong republican": "Strong Republican"}
CHOSE = {"[Democrat / Candidate 1]", "[Republican / Candidate 2]", "[Other / Candidate 3]", "[Other / Candidate 4]",
         "Other"}
UNDECIDED = {"Not Sure", "No One"}
FIRM = {"Yes, definitely", "I already voted (early or absentee)", "I plan to vote before Election Day"}
PSEUDO = 50
COLS = ["year", "st", "weight", "weight_post", "tookpost", "pid7", "race", "hispanic", "educ", "intent_sen",
        "voted_sen", "intent_turnout_self", "voted_turnout_self", "vv_turnout_gvm", "vv_regstatus"]
PIMU = HERE / "pimu.json"


def group_of(pid7, race, hispanic, educ) -> str | None:
    p = PID.get(str(pid7).lower())
    if p is None:
        return None
    white = race == "White" and hispanic != "Yes"
    degree = "Four-year college degree or more" if educ in ("4-Year", "Post-Grad") else "No four-year college degree"
    return f"{p} / {'white' if white else 'non-white'} / {degree}"


def persuadable(intent: pd.Series, voted: pd.Series) -> pd.Series:
    """1 if undecided before the election or the Senate vote differs from the intention; NaN outside the base, which
    is Senate voters who gave a pre-election preference or said they were unsure."""
    base = voted.isin(CHOSE) & (intent.isin(CHOSE) | intent.isin(UNDECIDED))
    return (intent.isin(UNDECIDED) | (intent != voted)).astype(float).where(base)


def mobilisable(intent: pd.Series, voted: pd.Series) -> pd.Series:
    """1 if the pre-election turnout intention was unsure ("probably", "undecided", no answer) or turned out wrong:
    intenders who didn't vote, non-intenders who did."""
    firm, no = intent.isin(FIRM), intent == "No"
    return ((~firm & ~no) | (firm & ~voted) | (no & voted)).astype(float)


def shrink(p: float, n: float, prior: float, k: float = PSEUDO) -> float:
    return (n * p + k * prior) / (n + k)


def _shares(d: pd.DataFrame, col: str, w: str, by: list[str]) -> pd.DataFrame:
    g = d.assign(_wy=d[col] * d[w]).groupby(by)
    return pd.DataFrame({"p": g._wy.sum() / g[w].sum(), "n": g.size()})


def fit(df: pd.DataFrame, k: float = PSEUDO) -> dict:
    """pi and mu by state and group: weighted shares, each shrunk toward its census division, which is shrunk toward
    the nation, with `k` respondents' worth of prior."""
    df = df.assign(div=df.st.map(DIVISION))
    national, states = {}, {s: {} for s in DIVISION}
    for name, col, w in (("pi", "persuadable", "weight_post"), ("mu", "mobilisable", "weight")):
        d = df[df[col].notna() & df[w].notna()]
        nat = _shares(d, col, w, ["group"])
        div = _shares(d, col, w, ["div", "group"])
        st = _shares(d, col, w, ["st", "group"])
        for g in nat.index:
            national.setdefault(g, {})[name] = round(float(nat.p[g]), 4)
            national[g][f"n_{name}"] = int(nat.n[g])
            for s, dv in DIVISION.items():
                pd_ = shrink(*div.loc[(dv, g)] if (dv, g) in div.index else (0.0, 0.0), nat.p[g], k)
                ps = shrink(*st.loc[(s, g)] if (s, g) in st.index else (0.0, 0.0), pd_, k)
                states[s].setdefault(g, {})[name] = round(float(ps), 4)
    return {"national": national, "states": states}


def load(years: tuple[int, ...]) -> pd.DataFrame:
    """CES cumulative respondents for `years`, with group and the persuadable and mobilisable flags. mu uses validated
    turnout among respondents matched to an active registration (validated turnout is only reliable where the match
    is); mobilisable_self uses self-reported turnout from the post-election wave, as a check."""
    df = pd.read_stata(DATA / "cumulative_2006-2025.dta", columns=COLS)
    df = df[df.year.isin(years)].copy()
    for c in df.select_dtypes("category"):
        df[c] = df[c].astype(object)
    df["group"] = [group_of(*r) for r in zip(df.pid7, df.race, df.hispanic, df.educ)]
    post = df.tookpost == "Took Post-Election Survey"
    df["persuadable"] = persuadable(df.intent_sen.where(post), df.voted_sen.where(post))
    df["mobilisable"] = mobilisable(df.intent_turnout_self, df.vv_turnout_gvm == "Voted").where(
        df.vv_regstatus == "Active")
    df["mobilisable_self"] = mobilisable(df.intent_turnout_self, df.voted_turnout_self == "Yes").where(
        post & df.voted_turnout_self.notna())
    return df[df.group.notna()]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fit", action="store_true", help="fit pi and mu and write simlab/pimu.json")
    a = ap.parse_args()
    if not a.fit:
        ap.error("nothing to do (use --fit)")
    mid = load((2018, 2022))
    out = fit(mid)
    check = load((2024,))
    check["weight_post"] = check.weight_post.fillna(check.weight)  # the cumulative file has no 2024 post weight
    nat = lambda d, col, w: _shares(d[d[col].notna() & d[w].notna()], col, w, ["group"]).p.round(4).to_dict()
    doc = {"fitted": f"{date.today()}, python -m simlab.groups --fit",
           "source": "CES cumulative 2006-2025, 2018 and 2022 midterms (pre- and post-election waves)",
           "variables": {
               "pi": "Senate voters (voted_sen a candidate, post wave) who were unsure before (intent_sen 'Not Sure' "
                     "or 'No One') or whose vote differs from intent_sen; weight_post",
               "mu": "respondents matched to an active registration (vv_regstatus): intent_turnout_self 'Probably', "
                     "'Undecided' or missing, or firm intenders without a validated vote (vv_turnout_gvm), or "
                     "'No' with one; weight"},
           "shrinkage": {"pseudo_count": PSEUDO, "levels": "state -> census division -> nation"},
           "checks": {"pi_2024": nat(check, "persuadable", "weight_post"), "mu_2024": nat(check, "mobilisable", "weight"),
                      "mu_self_report": nat(mid, "mobilisable_self", "weight_post")},
           **out}
    PIMU.write_text(json.dumps(doc, indent=1), encoding="utf-8")
    print(f"pi/mu: {len(out['national'])} groups, {len(out['states'])} states -> {PIMU}")


if __name__ == "__main__":
    main()
