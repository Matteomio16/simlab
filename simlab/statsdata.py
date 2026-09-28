"""Statistics inputs: past results, 538 poll archives and district results for the starting levels, the filter and
the House map. Downloaded with Matteo's OK (28 Sep 2026) into data/results/ and data/history/ (gitignored); every file's
URL, size, SHA-256 and fetch time go to data/stats_downloads.json.

- MIT Election Data + Science Lab on Harvard Dataverse (CC0): president by state 1976-2024 (doi:10.7910/DVN/42MVDX),
  Senate by state 1976-2024 (doi:10.7910/DVN/PEJ5QU), House by district 1976-2024 (doi:10.7910/DVN/IG0UN2).
- FiveThirtyEight (CC BY 4.0; repos frozen since March 2025): pollster-ratings raw polls with results and ratings
  (github.com/fivethirtyeight/data), Senate forecasts with outcomes (checking-our-work-data), and the Senate, House
  and governor poll lists through the Internet Archive: the "historical" files hold 2018-2022, the current-cycle
  files 2024 (copies from late Nov / early Dec 2024, after the election).
- The Downballot: 2024 and 2020 presidential results by congressional district, on the lines used in 2024 and on the
  2026 lines (cite and link; don't republish whole sheets).

    python -m simlab.statsdata download
    python -m simlab.statsdata check
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone

import pandas as pd
import requests

from .ces import DATA
from .history import UA, _save

RESULTS = DATA / "results"
HIST = DATA / "history"
LEDGER = DATA / "stats_downloads.json"
DV = "https://dataverse.harvard.edu/api"
GH = "https://raw.githubusercontent.com/fivethirtyeight"
WB = "https://web.archive.org/web"
FTE = "https://projects.fivethirtyeight.com/polls/data"
SHEET = "https://docs.google.com/spreadsheets/d"
DB_2024_LINES = "1ng1i_Dm_RMDnEvauH44pgE6JCUsapcuu8F2pCfeLWFo"
DB_2026_LINES = "1eZfaFI-c-PFOoKx1-zZA2MP0_dxRq_LVK0re3BOQqy0"
DB_TABS = {"percentages": 620838163, "vote_totals": 1491069057, "info": 1793797417}
MIT = {"doi:10.7910/DVN/42MVDX": "1976-2024-president.csv", "doi:10.7910/DVN/PEJ5QU": "1976-2024-senate-state.tab",
       "doi:10.7910/DVN/IG0UN2": "1976-2024-house.tab"}
FILES = {  # local path: (URL, licence, expected bytes or None)
    HIST / "538_raw_polls.csv": (f"{GH}/data/master/pollster-ratings/raw_polls.csv", "CC BY 4.0", 4961378),
    HIST / "538_pollster_ratings_combined.csv": (f"{GH}/data/master/pollster-ratings/pollster-ratings-combined.csv",
                                                 "CC BY 4.0", 40046),
    HIST / "538_pollster_ratings_README.md": (f"{GH}/data/master/pollster-ratings/README.md", "CC BY 4.0", 8311),
    HIST / "538_pollster_ratings_2023.csv": (f"{GH}/data/master/pollster-ratings/2023/pollster-ratings.csv",
                                             "CC BY 4.0", 95044),
    HIST / "538_cow_us_senate_elections.csv": (f"{GH}/checking-our-work-data/master/us_senate_elections.csv",
                                               "CC BY 4.0", 7981949),
    HIST / "538_senate_polls_historical.csv": (f"{WB}/20241203065148id_/{FTE}/senate_polls_historical.csv",
                                               "CC BY 4.0", 2963974),
    HIST / "538_house_polls_historical.csv": (f"{WB}/20241203120317id_/{FTE}/house_polls_historical.csv",
                                              "CC BY 4.0", None),
    HIST / "538_governor_polls_historical.csv": (f"{WB}/20241203175703id_/{FTE}/governor_polls_historical.csv",
                                                 "CC BY 4.0", 2490600),
    HIST / "538_senate_polls_2024.csv": (f"{WB}/20241203183703id_/{FTE}/senate_polls.csv", "CC BY 4.0", 1497307),
    HIST / "538_house_polls_2024.csv": (f"{WB}/20241126021208id_/{FTE}/house_polls.csv", "CC BY 4.0", 373366),
    HIST / "538_governor_polls_2024.csv": (f"{WB}/20241202052158id_/{FTE}/governor_polls.csv", "CC BY 4.0", 457589),
    **{RESULTS / f"downballot_pres_by_cd_{lines}_{tab}.csv":
       (f"{SHEET}/{sid}/export?format=csv&gid={gid}", "The Downballot: cite and link, don't republish whole sheets", None)
       for lines, sid in (("2024lines", DB_2024_LINES), ("2026lines", DB_2026_LINES)) for tab, gid in DB_TABS.items()},
}


def _mit_files() -> dict:
    out = {}
    for doi, name in MIT.items():
        r = requests.get(f"{DV}/datasets/:persistentId/", params={"persistentId": doi}, headers=UA, timeout=60)
        r.raise_for_status()
        for f in r.json()["data"]["latestVersion"]["files"]:
            d = f["dataFile"]
            if d["filename"] == name or d["filename"].startswith("codebook"):
                out[RESULTS / d["filename"].replace("–", "-")] = (f"{DV}/access/datafile/{d['id']}", "CC0",
                                                                      d["filesize"])
    return out


def download() -> None:
    """Skips files already in the ledger. The MIT House file sits behind a Dataverse guestbook form (name, email),
    which this script doesn't fill in: download it by hand from the dataset page into data/results/."""
    RESULTS.mkdir(parents=True, exist_ok=True)
    ledger = json.loads(LEDGER.read_text()) if LEDGER.exists() else {}
    for path, (url, licence, size) in {**_mit_files(), **FILES}.items():
        key = str(path.relative_to(DATA)).replace("\\", "/")
        if path.exists() and key in ledger:
            continue
        try:
            got = _save(url, path)
        except requests.HTTPError as e:
            if not path.exists():
                print(f"{key}: skipped (HTTP {e.response.status_code}); download it by hand into {path.parent}")
                continue
            got, url, size = path.stat().st_size, f"{url} (downloaded by hand)", None
        if size and got != size:
            raise IOError(f"{key}: got {got} bytes, expected {size}")
        ledger[key] = {"url": url, "licence": licence, "bytes": got,
                       "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                       "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
        LEDGER.write_text(json.dumps(ledger, indent=1))
        print(f"{key}: {got / 1e3:.0f} KB")
    print(f"{len(ledger)} files, {sum(v['bytes'] for v in ledger.values()) / 1e6:.1f} MB -> {LEDGER}")


def check() -> None:
    """What each file covers, so a truncated or changed download shows up at once."""
    pres = pd.read_csv(RESULTS / MIT["doi:10.7910/DVN/42MVDX"])
    print(f"president: {pres.year.min()}-{pres.year.max()}, 2024 states {pres[pres.year == 2024].state_po.nunique()}")
    sen = pd.read_csv(RESULTS / MIT["doi:10.7910/DVN/PEJ5QU"], sep="\t")
    print(f"senate: {sen.year.min()}-{sen.year.max()}, 2024 races "
          f"{sen[sen.year == 2024].groupby(['state_po', 'special']).ngroups}, columns {list(sen.columns)}")
    if (RESULTS / MIT["doi:10.7910/DVN/IG0UN2"]).exists():
        house = pd.read_csv(RESULTS / MIT["doi:10.7910/DVN/IG0UN2"], sep="\t", low_memory=False)
        print(f"house: {house.year.min()}-{house.year.max()}, 2024 districts "
              f"{house[house.year == 2024].groupby(['state_po', 'district']).ngroups}")
    else:
        print("house: missing (guestbook download by hand)")
    raw = pd.read_csv(HIST / "538_raw_polls.csv", low_memory=False)
    print(f"538 raw polls: {len(raw)} rows, cycles {raw.cycle.min()}-{raw.cycle.max()}, "
          f"types {raw.type_simple.value_counts().to_dict()}")
    for kind in ("senate", "house", "governor"):
        for part in ("historical", "2024"):
            d = pd.read_csv(HIST / f"538_{kind}_polls_{part}.csv", low_memory=False)
            print(f"538 {kind} polls ({part}): {d.poll_id.nunique()} polls, cycles {sorted(d.cycle.unique().tolist())}")
    cow = pd.read_csv(HIST / "538_cow_us_senate_elections.csv", low_memory=False)
    print(f"538 Senate forecasts: years {sorted(cow.year.unique())}, {len(cow)} rows")
    for lines in ("2024lines", "2026lines"):
        d = pd.read_csv(RESULTS / f"downballot_pres_by_cd_{lines}_percentages.csv", header=None)
        districts = d[0].astype(str).str.match(r"^[A-Z]{2}-(\d\d|AL)$")
        print(f"downballot {lines}: {districts.sum()} districts")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["download", "check"])
    {"download": download, "check": check}[ap.parse_args().cmd]()
