"""Census CPS November Voting and Registration Supplement -> citizen respondents with self-reported turnout, reweighted
per state to that year's official turnout. Source of the turnout targets; CES stays the source for vote choice.

Why not CES: its validated turnout counts respondents who weren't matched to a voter file as non-voters, so a cell's
turnout mostly tracks its match rate (2024: correlation 0.995 across cells). The CPS asks everyone. Following Hur and
Achen (2013, Public Opinion Quarterly), respondents who didn't answer the vote question (don't know, refused, no
response) are dropped rather than counted as non-voters (the Census convention, which lowers turnout in groups with
high supplement non-response); then in each state voters' weights are multiplied by T/R and non-voters' by
(1-T)/(1-R), where T is the official VEP turnout (turnout{year}.json) and R the weighted self-reported rate, so every
state matches its official turnout and keeps its total weight.

Files in data/cps/ (www2.census.gov/programs-surveys/cps/datasets/<year>/supp/): nov24pub.csv, nov22pub.csv and the
fixed-width nov18/nov18pub.dat (positions from cpsnov18.pdf). These supplements have no weight of their own; the
techdocs say to use the basic weight PWSSWGT (4 implied decimals). Checked 27 Sep 2026: 2018 vote-question counts equal
the techdoc's, and the Census-convention national rates reproduce the published 53.4% (2018), 52.2% (2022), 65.3% (2024).

    python -m simlab.cps
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from .ces import DATA, GENDER, STATE_NAMES

CPS = DATA / "cps"
YEARS = (2018, 2022, 2024)
LAYOUT_2018 = {"GESTFIPS": (92, 94), "PRTAGE": (121, 123), "PESEX": (128, 130), "PEEDUCA": (136, 138),
               "PTDTRACE": (138, 140), "PEHSPNON": (156, 158), "PRPERTYP": (160, 162), "PRCITSHP": (171, 173),
               "PWSSWGT": (612, 622), "PES1": (1000, 1002)}


def official(year: int) -> dict[str, float]:
    return json.loads((Path(__file__).parent / f"turnout{year}.json").read_text())["vep_turnout"]


def raw(year: int) -> pd.DataFrame:
    if year == 2018:
        return pd.read_fwf(CPS / "nov18" / "nov18pub.dat", colspecs=list(LAYOUT_2018.values()),
                           names=list(LAYOUT_2018), header=None)
    return pd.read_csv(CPS / f"nov{year % 100}pub.csv", usecols=list(LAYOUT_2018))


def respondents(year: int) -> pd.DataFrame:
    """Adult civilian citizens who answered the vote question, with ces.load's cell fields and labels. weight_raw is
    PWSSWGT in persons; commonweight is the turnout-corrected weight."""
    d = raw(year)
    d = d[(d.PRPERTYP == 2) & (d.PRTAGE >= 18) & d.PRCITSHP.between(1, 4) & d.PES1.isin([1, 2])]
    df = pd.DataFrame({"year": year, "inputstate": d.GESTFIPS, "state": d.GESTFIPS.map(STATE_NAMES), "age": d.PRTAGE,
                       "gender4": d.PESEX, "gender": d.PESEX.map(GENDER)})
    df["age4"] = pd.cut(df.age, [17, 29, 44, 64, 200], labels=["18-29", "30-44", "45-64", "65+"]).astype(str)
    df["age2"] = np.where(df.age < 45, "18-44", "45+")
    df["race5"] = np.where(d.PEHSPNON == 1, "Hispanic",
                           d.PTDTRACE.map({1: "White", 2: "Black", 4: "Asian"}).fillna("Other"))
    df["race4"] = df.race5.replace({"Asian": "Other"})
    df["degree"] = np.where(d.PEEDUCA >= 43, "Four-year college degree or more", "No four-year college degree")
    df["cit1"] = 1
    df["voted"] = d.PES1 == 1
    df["turnout"] = np.where(df.voted, "true", "false")
    df["weight_raw"] = d.PWSSWGT / 1e4
    r = (df.weight_raw * df.voted).groupby(df.state).sum() / df.weight_raw.groupby(df.state).sum()
    t = pd.Series(official(year)).reindex(r.index)
    df["commonweight"] = df.weight_raw * np.where(df.voted, df.state.map(t / r), df.state.map((1 - t) / (1 - r)))
    return df.reset_index(drop=True)


def rate(d: pd.DataFrame, w: str = "commonweight") -> float:
    return float(np.average(d.voted, weights=d[w]))


def summary() -> None:
    for year in YEARS:
        df = respondents(year)
        states = df.groupby("state")[["voted", "weight_raw"]].apply(rate, "weight_raw")
        print(f"{year}: {len(df)} respondents; self-reported {rate(df, 'weight_raw'):.3f}, corrected {rate(df):.3f} "
              f"(official {official(year)['United States']:.3f}); state self-reports {states.min():.3f}-{states.max():.3f}")
        for c in ("age4", "race5", "degree"):
            by = df.groupby(c)[["voted", "commonweight"]].apply(rate)
            print(f"  {c}: " + ", ".join(f"{k} {v:.3f}" for k, v in by.items()))


if __name__ == "__main__":
    summary()
