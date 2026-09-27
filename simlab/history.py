"""Poll history for the real-events set (events2): where public opinion actually moved after events.

Downloaded with Matteo's OK (27 Sep 2026) into data/history/ (gitignored):
- VoteHub API (CC BY 4.0, no key): approval polls (Trump's second term, Congress, Supreme Court, from Nov 2018) and
  generic-ballot polls (Dec 2024 on).
- FiveThirtyEight archives through the Internet Archive (538 closed in March 2025): Trump first-term and Biden approval
  averages, and the poll lists behind them; generic-ballot poll lists and the 2017-19 generic-ballot average.
- Democracy Fund + UCLA Nationscape (CC0, Harvard Dataverse doi:10.7910/DVN/CQFP3Z): weekly cross-sections, July 2019
  to January 2021, ~6,250 interviews a week, for group-level shifts (party, age, race). Main weekly waves only (the
  "parallel" extra samples are skipped), as Dataverse tab files, plus the variables list and one wave's codebook.

    python -m simlab.history download
"""
from __future__ import annotations

import argparse
import json

import requests

from .ces import DATA

HIST = DATA / "history"
UA = {"User-Agent": "simlab/0.1 (research; +https://scaliastudio.dev)"}
DV = "https://dataverse.harvard.edu/api"
NATIONSCAPE = "doi:10.7910/DVN/CQFP3Z"
FTE = "https://projects.fivethirtyeight.com"
WAYBACK = {  # local name: (snapshot timestamp, original URL); "id_" asks the archive for the raw file
    "538_trump1_approval_topline.csv": ("20210414020514", f"{FTE}/trump-approval-data/approval_topline.csv"),
    "538_trump1_approval_polllist.csv": ("20210414015923", f"{FTE}/trump-approval-data/approval_polllist.csv"),
    "538_biden_approval_topline.csv": ("20250306182158", f"{FTE}/biden-approval-data/approval_topline.csv"),
    "538_president_approval_polls.csv": ("20250306062820", f"{FTE}/polls/data/president_approval_polls.csv"),
    "538_generic_ballot_polls.csv": ("20250306165516", f"{FTE}/polls/data/generic_ballot_polls.csv"),
    "538_generic_ballot_polls_historical.csv": ("20241203041935",
                                                f"{FTE}/polls/data/generic_ballot_polls_historical.csv"),
    "538_generic_topline_2017_19.csv": ("20190524202349", f"{FTE}/generic-ballot-data/generic_topline.csv"),
}


def _save(url: str, path, **kw) -> int:
    part = path.with_name(path.name + ".part")
    with requests.get(url, headers=UA, stream=True, timeout=300, **kw) as r:
        r.raise_for_status()
        with part.open("wb") as fh:
            for chunk in r.iter_content(1 << 20):
                fh.write(chunk)
    part.replace(path)
    return path.stat().st_size


def download() -> None:
    HIST.mkdir(parents=True, exist_ok=True)
    for kind in ("approval", "generic-ballot"):
        polls = requests.get("https://api.votehub.com/polls", params={"poll_type": kind}, headers=UA, timeout=120).json()
        (HIST / f"votehub_{kind}.json").write_text(json.dumps(polls), encoding="utf-8")
        print(f"votehub {kind}: {len(polls)} polls")
    for name, (ts, url) in WAYBACK.items():
        p = HIST / name
        if not p.exists():
            print(f"{name}: {_save(f'https://web.archive.org/web/{ts}id_/{url}', p) / 1e3:.0f} KB")
    ns = HIST / "nationscape"
    ns.mkdir(exist_ok=True)
    files = requests.get(f"{DV}/datasets/:persistentId/?persistentId={NATIONSCAPE}", headers=UA,
                         timeout=60).json()["data"]["latestVersion"]["files"]
    wanted = [f for f in files if (f["dataFile"]["filename"].endswith(".tab")
                                   and "parallel" not in (f.get("directoryLabel") or ""))
              or f["dataFile"]["filename"] in ("Nationscape-Variables-2021Dec.csv", "codebook_ns20200702.pdf")]
    total = 0
    for f in wanted:
        d = f["dataFile"]
        p = ns / d["filename"]
        if not p.exists():
            total += _save(f"{DV}/access/datafile/{d['id']}", p)
    print(f"nationscape: {len(wanted)} files, {total / 1e6:.0f} MB downloaded -> {ns}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["download"])
    ap.parse_args()
    download()
