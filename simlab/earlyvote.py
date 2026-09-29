"""Early-vote files, saved each time the publisher updates them (roadmap A12). The files are overwritten in place, so
an update that is never fetched is gone.

Each check asks for the file's Last-Modified header (or, where there is none, compares the content's hash) and saves
only what changed since the last save. A new version goes to <out>/<state>/YYYY-MM-DD/HHMM/<name>.<ext>.gz (the
publisher's timestamp where given, UTC; gzip with a fixed header) with a manifest.json giving the URL, both times, the
raw size and the raw SHA-256. Files with one row per voter are counted in memory and only the counts are written
(Matteo, 29 Sep: no raw voter files in simlab-data); the hash still identifies the exact file. Nothing raw is printed:
the job runs in a public repo whose logs are public.

- nc: NCSBE's absentee file (one row per ballot, by mail and, from 15 Oct, one-stop early voting) counted by county,
  congressional district, party, race, ethnicity, gender, age band, request type, delivery, return status, return
  date and same-day registration; and NCSBE's own county counts of requests, kept as published.
- me: the Secretary of State's absentee voter file (one row per ballot request with the voter's record number, no
  names; its name changes with each update, so the voter-data page is read for the current link), counted by town,
  congressional district, party, ballot type, request, issue and return methods, dates and return status.
- ia: the Secretary of State's daily absentee PDFs by county and by congressional district, kept as published (links
  read from the statistics page; only files uploaded from September 2026, which excludes the primary's).
- tx: the Secretary of State's early-vote system (Civix): its election list, which shows when the general
  election's early-voting days start (~19 Oct); the turnout files join once the first day exists to test on.

Ohio is not here: the Secretary of State's site blocks scripts and publishes no file (skipped for the pilot, Matteo, 29 Sep).

    python -m simlab.earlyvote --out ../simlab-data/earlyvote [--state me]
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import re
import subprocess
import tempfile
import zipfile
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import urljoin

import pandas as pd
import requests

UA = {"User-Agent": "simlab/0.1 (research; +https://scaliastudio.dev)"}
ENABLED = ("nc", "ia", "tx", "me")  # a state joins only after Matteo's OK: small aggregates yes, voter-level files by name
NCSBE = "https://s3.amazonaws.com/dl.ncsbe.gov/ENRS/2026_11_03/"
NC_BY = ["county_desc", "cong_dist_desc", "voter_party_code", "race", "ethnicity", "gender", "age_band",
         "ballot_req_type", "ballot_req_delivery_type", "ballot_rtn_status", "ballot_rtn_dt", "sdr"]
AGE_BANDS = ([17, 29, 44, 64, 200], ["18-29", "30-44", "45-64", "65+"])
MAINE_PAGE = "https://www.maine.gov/sos/elections-voting/voter-data"
MAINE_FILE = re.compile(r'href="([^"]*inline-files/11-3-26[^"]*AB%20Voter%20File[^"]*\.txt)"', re.I)
# www.maine.gov/sos/elections-voting/absenteelayout: 27 fields in this order
# the file's own header (29 Sep 2026: 23 pipe-separated fields, no names), mapped to the names kept
MAINE_COLUMNS = {"RES MUNICIPALITY": "municipality", "CG": "cong_dist", "P": "party", "Ballot Type": "ballot_type",
                 "Req Type": "request_method", "Req Date": "requested", "Issued Type": "issue_method",
                 "Issued Date": "issued", "Rec Type": "return_method", "Rec Date": "received",
                 "Status": "return_status"}
MAINE_BY = ["municipality", "cong_dist", "party", "ballot_type", "request_method", "requested", "issue_method",
            "issued", "return_method", "received", "return_status"]
IOWA_PAGE = "https://sos.iowa.gov/iowans/election-results-statistics"
IOWA_FILE = re.compile(r'href="([^"]*/sites/default/files/(\d{4}-\d{2})/ABS%20(Counties|Congressional)%202026\.pdf)"')
TX_ELECTIONS = "https://goelect.txelections.civixapps.com/api-ivis-system/api/v1/getFile?type=EVR_ELECTION"


def nc_counts(path: Path) -> tuple[bytes, int]:
    """NCSBE's one-row-per-ballot file -> counts by NC_BY. Names, addresses and voter ids never leave this function."""
    cols = [c for c in NC_BY if c != "age_band"] + ["age"]
    parts, voters = [], 0
    with zipfile.ZipFile(path) as z, z.open(z.namelist()[0]) as f:
        for c in pd.read_csv(f, dtype=str, encoding="latin-1", usecols=cols, chunksize=500_000, keep_default_na=False):
            c = c.apply(lambda s: s.str.strip())
            c["age_band"] = pd.cut(pd.to_numeric(c.pop("age"), errors="coerce"), AGE_BANDS[0], labels=AGE_BANDS[1]).astype(str)
            c["ballot_rtn_dt"] = pd.to_datetime(c.ballot_rtn_dt, format="%m/%d/%Y", errors="coerce").dt.strftime("%Y-%m-%d")
            parts.append(c.fillna("").groupby(NC_BY).size())
            voters += len(c)
    counts = pd.concat(parts).groupby(level=list(range(len(NC_BY)))).sum().rename("n").reset_index()
    return counts.to_csv(index=False).encode(), voters


def me_counts(path: Path) -> tuple[bytes, int]:
    """Maine's one-row-per-ballot file -> counts by MAINE_BY, read by the file's header (pipe-separated). Only the
    MAINE_COLUMNS fields are read; voter numbers never leave this function."""
    d = pd.read_csv(path, sep="|", dtype=str, encoding="latin-1", keep_default_na=False,
                    usecols=lambda c: c.strip() in MAINE_COLUMNS)
    d = d.rename(columns=lambda c: MAINE_COLUMNS[c.strip()])[MAINE_BY].apply(lambda s: s.str.strip())
    for c in ("requested", "issued", "received"):
        d[c] = pd.to_datetime(d[c], format="%m/%d/%Y", errors="coerce").dt.strftime("%Y-%m-%d").fillna("")
    counts = d.groupby(MAINE_BY).size().rename("n").reset_index()
    return counts.to_csv(index=False).encode(), len(d)


def links(page: str, pattern: re.Pattern) -> list[re.Match]:
    r = requests.get(page, headers=UA, timeout=60)
    r.raise_for_status()
    return list(pattern.finditer(r.text))


def maine() -> list[tuple]:
    found = links(MAINE_PAGE, MAINE_FILE)
    if not found:
        raise RuntimeError("no 11-3-26 absentee voter file linked on the voter-data page")
    return [("absentee", urljoin(MAINE_PAGE, found[0].group(1)), me_counts, "csv")]


def iowa() -> list[tuple]:
    newest = {}
    for m in links(IOWA_PAGE, IOWA_FILE):
        if m.group(2) >= "2026-09" and m.group(2) >= newest.get(m.group(3), ("",))[0]:
            newest[m.group(3)] = (m.group(2), urljoin(IOWA_PAGE, m.group(1)))
    return [(f"absentee_{kind.lower()}", url, None, "pdf") for kind, (_, url) in sorted(newest.items())]


SOURCES = {
    "nc": lambda: [("absentee", NCSBE + "absentee_20261103.zip", nc_counts, "csv"),
                   ("counts_county", NCSBE + "absentee_counts_county_20261103.csv", None, "csv")],
    "me": maine,
    "ia": iowa,
    "tx": lambda: [("elections", TX_ELECTIONS, None, "json")],
}


def fetch(url: str, into: Path) -> tuple[int, str]:
    """Streams url to a file; returns (bytes, SHA-256)."""
    h, n = hashlib.sha256(), 0
    with requests.get(url, headers=UA, stream=True, timeout=120) as r, into.open("wb") as f:
        r.raise_for_status()
        for chunk in r.iter_content(1 << 20):
            h.update(chunk)
            f.write(chunk)
            n += len(chunk)
    return n, h.hexdigest()


def last_modified(url: str) -> str:
    try:
        head = requests.head(url, headers=UA, timeout=30, allow_redirects=True)
        return head.headers.get("Last-Modified", "") if head.status_code == 200 else ""
    except requests.RequestException:
        return ""


def check(out: Path, state: str) -> list[dict]:
    """Saves every file of `state` that changed since the last save (same Last-Modified, or where there is none the
    same SHA-256, means unchanged); returns manifest entries."""
    latest_path = out / state / "latest.json"
    latest = json.loads(latest_path.read_text(encoding="utf-8")) if latest_path.exists() else {}
    latest = {k: v if isinstance(v, dict) else {"modified": v} for k, v in latest.items()}
    entries, now = [], lambda: datetime.now(timezone.utc).isoformat(timespec="seconds")
    try:
        files = SOURCES[state]()
    except Exception as e:
        files = []
        entries.append({"state": state, "name": "links", "fetched_at": now(), "error": f"{type(e).__name__}: {e}"[:300]})
        print(f"{state}/links: {type(e).__name__}", flush=True)
    if not files and not entries:
        print(f"{state}: nothing published yet", flush=True)
    for name, url, count, ext in files:
        fetched_at, prev = now(), latest.get(name, {})
        try:
            modified = last_modified(url)
            if modified and prev.get("modified") == modified and prev.get("url", url) == url:
                print(f"{state}/{name}: unchanged", flush=True)
                continue
            with tempfile.TemporaryDirectory() as tmp:
                raw = Path(tmp) / "raw"
                size, sha = fetch(url, raw)
                if sha == prev.get("sha256"):
                    print(f"{state}/{name}: unchanged", flush=True)
                    continue
                body, rows = count(raw) if count else (raw.read_bytes(), None)
            when = parsedate_to_datetime(modified) if modified else datetime.now(timezone.utc)
            folder = out / state / f"{when:%Y-%m-%d}" / f"{when:%H%M}"
            folder.mkdir(parents=True, exist_ok=True)
            gz = gzip.compress(body, mtime=0)
            (folder / f"{name}.{ext}.gz").write_bytes(gz)
            entries.append({"state": state, "name": name, "url": url, "last_modified": modified,
                            "fetched_at": fetched_at, "raw_bytes": size, "raw_sha256": sha,
                            "file": f"{folder.relative_to(out).as_posix()}/{name}.{ext}.gz",
                            "kept": "counts only (raw file has one row per voter)" if count else "as published",
                            **({"voters": rows} if count else {})})
            latest[name] = {"modified": modified, "sha256": sha, "url": url}
            print(f"{state}/{name}: {size / 1e6:.1f} MB raw -> {len(gz) / 1e6:.1f} MB kept (gzip)", flush=True)
        except Exception as e:
            entries.append({"state": state, "name": name, "url": url, "fetched_at": fetched_at,
                            "error": f"{type(e).__name__}: {e}"[:300]})
            print(f"{state}/{name}: {type(e).__name__}", flush=True)
    sha = os.environ.get("GITHUB_SHA") or subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True,
                                                         cwd=Path(__file__).parent).stdout.strip()
    for e in entries:
        if "file" in e:
            m = out / Path(e["file"]).parent / "manifest.json"
            old = json.loads(m.read_text(encoding="utf-8")) if m.exists() else {"files": []}
            m.write_text(json.dumps({"simlab_git": sha, "files": old["files"] + [e]}, indent=1), encoding="utf-8")
    if any("file" in e for e in entries):
        latest_path.write_text(json.dumps(latest, indent=1), encoding="utf-8")
    errors = [e for e in entries if "error" in e]
    if errors:
        log = out / state / "errors.jsonl"
        log.parent.mkdir(parents=True, exist_ok=True)
        with log.open("a", encoding="utf-8") as f:
            f.writelines(json.dumps(e) + "\n" for e in errors)
    return entries


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--state", action="append", choices=sorted(SOURCES), help="default: the enabled states")
    a = ap.parse_args()
    for state in a.state or ENABLED:
        check(a.out, state)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
