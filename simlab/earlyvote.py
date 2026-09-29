"""Early-vote files, saved each time the publisher updates them (roadmap A12). The files are overwritten in place, so
an update that is never fetched is gone.

Each check asks for the file's Last-Modified header and fetches only what changed since the last save. A new version
goes to <out>/<state>/YYYY-MM-DD/HHMM/<name>.csv.gz (the publisher's timestamp, UTC; gzip with a fixed header) with a
manifest.json giving the URL, both times, the raw size and the raw SHA-256. Files with one row per voter are counted
in memory and only the counts are written (Matteo, 29 Sep: no raw voter files in simlab-data); the hash still
identifies the exact file. Nothing raw is printed: the job runs in a public repo whose logs are public.

- nc: NCSBE's absentee file (one row per ballot, by mail and, from 15 Oct, one-stop early voting) counted by county,
  congressional district, party, race, ethnicity, gender, age band, request type, delivery, return status, return
  date and same-day registration; and NCSBE's own county counts of requests, kept as published.

    python -m simlab.earlyvote --out ../simlab-data/earlyvote
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import subprocess
import tempfile
import zipfile
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

import pandas as pd
import requests

UA = {"User-Agent": "simlab/0.1 (research; +https://scaliastudio.dev)"}
NCSBE = "https://s3.amazonaws.com/dl.ncsbe.gov/ENRS/2026_11_03/"
NC_BY = ["county_desc", "cong_dist_desc", "voter_party_code", "race", "ethnicity", "gender", "age_band",
         "ballot_req_type", "ballot_req_delivery_type", "ballot_rtn_status", "ballot_rtn_dt", "sdr"]
AGE_BANDS = ([17, 29, 44, 64, 200], ["18-29", "30-44", "45-64", "65+"])


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


SOURCES = {"nc": {"absentee": (NCSBE + "absentee_20261103.zip", nc_counts),
                  "counts_county": (NCSBE + "absentee_counts_county_20261103.csv", None)}}


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


def check(out: Path, state: str) -> list[dict]:
    """Saves every file of `state` whose Last-Modified differs from the last one saved; returns manifest entries."""
    latest_path = out / state / "latest.json"
    latest = json.loads(latest_path.read_text(encoding="utf-8")) if latest_path.exists() else {}
    entries = []
    for name, (url, count) in SOURCES[state].items():
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        try:
            head = requests.head(url, headers=UA, timeout=30)
            if head.status_code != 200:
                raise RuntimeError(f"HTTP {head.status_code}")
            modified = head.headers.get("Last-Modified", "")
            if modified and latest.get(name) == modified:
                print(f"{state}/{name}: unchanged", flush=True)
                continue
            when = parsedate_to_datetime(modified) if modified else datetime.now(timezone.utc)
            with tempfile.TemporaryDirectory() as tmp:
                raw = Path(tmp) / "raw"
                size, sha = fetch(url, raw)
                body, rows = count(raw) if count else (raw.read_bytes(), None)
            folder = out / state / f"{when:%Y-%m-%d}" / f"{when:%H%M}"
            folder.mkdir(parents=True, exist_ok=True)
            gz = gzip.compress(body, mtime=0)
            (folder / f"{name}.csv.gz").write_bytes(gz)
            entries.append({"state": state, "name": name, "url": url, "last_modified": modified, "fetched_at": now,
                            "raw_bytes": size, "raw_sha256": sha, "file": f"{folder.relative_to(out).as_posix()}/{name}.csv.gz",
                            "kept": "counts only (raw file has one row per voter)" if count else "as published",
                            **({"voters": rows} if count else {})})
            latest[name] = modified
            print(f"{state}/{name}: {size / 1e6:.1f} MB raw -> {len(gz) / 1e6:.1f} MB kept (gzip)", flush=True)
        except Exception as e:
            entries.append({"state": state, "name": name, "url": url, "fetched_at": now,
                            "error": f"{type(e).__name__}: {e}"[:300]})
            print(f"{state}/{name}: {type(e).__name__}", flush=True)
    for e in entries:
        if "file" in e:
            m = out / Path(e["file"]).parent / "manifest.json"
            old = json.loads(m.read_text(encoding="utf-8")) if m.exists() else {"files": []}
            sha = os.environ.get("GITHUB_SHA") or subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True,
                                                                 text=True, cwd=Path(__file__).parent).stdout.strip()
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
    ap.add_argument("--state", action="append", choices=sorted(SOURCES))
    a = ap.parse_args()
    for state in a.state or sorted(SOURCES):
        check(a.out, state)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
