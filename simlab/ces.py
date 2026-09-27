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

from .core import RUNS
from .personas import render

DATA = RUNS.parent / "data"
DATA.mkdir(exist_ok=True)
DOI = "doi:10.7910/DVN/X11EP6"
DV = "https://dataverse.harvard.edu/api"

FIPS = {39: "Ohio", 37: "North Carolina", 48: "Texas"}


def download() -> Path:
    meta = requests.get(f"{DV}/datasets/:persistentId/?persistentId={DOI}", timeout=60).json()
    files = meta["data"]["latestVersion"]["files"]
    tabular = [f for f in files if f["dataFile"].get("filename", "").lower().endswith((".csv", ".tab", ".dta"))]
    for f in files:
        print(f["dataFile"]["filename"], f["dataFile"].get("filesize"))
    big = max(tabular, key=lambda f: f["dataFile"].get("filesize", 0))
    fid, name = big["dataFile"]["id"], big["dataFile"]["filename"]
    out = DATA / name
    if not out.exists():
        with requests.get(f"{DV}/access/datafile/{fid}?format=original", stream=True, timeout=600) as r:
            r.raise_for_status()
            with out.open("wb") as fh:
                for chunk in r.iter_content(1 << 20):
                    fh.write(chunk)
    return out


def load(path: Path) -> pd.DataFrame:
    if path.suffix == ".dta":
        return pd.read_stata(path, convert_categoricals=True)
    sep = "\t" if path.suffix == ".tab" else ","
    return pd.read_csv(path, sep=sep, low_memory=False)


CANDIDATES = {
    "state": ["inputstate", "inputstate_post"],
    "birthyr": ["birthyr"],
    "gender": ["gender4", "gender"],
    "race": ["race"],
    "hispanic": ["hispanic"],
    "educ": ["educ"],
    "income": ["faminc_new"],
    "pid7": ["pid7"],
    "ideo5": ["ideo5"],
    "religion": ["religpew"],
    "urban": ["urbancity"],
    "vote20": ["presvote20post"],
    "vote24": ["CC24_410", "presvote24post", "CC24_410a"],
    "voted_validated": ["TS_g2024", "vv_turnout_gvm", "CL_2024gvm"],
    "weight": ["commonpostweight", "vvweight_post", "commonweight"],
}


def detect(df: pd.DataFrame) -> dict:
    found = {}
    for k, cands in CANDIDATES.items():
        for c in cands:
            if c in df.columns:
                found[k] = c
                break
    print("column map:", json.dumps(found, indent=1))
    return found
