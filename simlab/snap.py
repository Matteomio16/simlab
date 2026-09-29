"""Snapshots of live data every 3 hours: raw, immutable, hashed. The forecast reads them, and after the election the
blind track may use nothing else, so a missed run can't be recovered for sources that overwrite themselves (news
feeds, markets, poll lists that get edited, early-vote files).

Each run writes <out>/YYYY-MM-DD/HHMM/<source>/<name>.gz (gzip with a fixed header, so an unchanged file is
byte-identical and git stores it once) and <out>/YYYY-MM-DD/HHMM/manifest.json: per file the URL, UTC fetch time,
HTTP status, raw size and SHA-256 of the raw content, or the error. Sources, all free and keyless:
- polls: VoteHub API, every poll (CC BY 4.0).
- wikipedia: the 35 Senate race pages, the 50 states' House election pages (candidates, district polls), the Senate
  and House overview pages (ratings, generic ballot) and the approval polling page; raw wikitext with revision ids
  (CC BY-SA).
- markets, benchmark only (never assimilated): PredictIt (all markets), Kalshi and Polymarket (Senate and House
  control, every Senate race).
- news: GDELT headlines for each pilot race and the national midterms (news.RACES queries), the last 24 hours each run
  so a later run fills a failed query's gap. GDELT allows one request per 5 s and often rate-limits shared IPs, so each
  query retries with longer waits and the query order rotates each run. Google News is not used: its
  feed's terms allow only personal news readers (Matteo, 28 Sep). Media Cloud, for every race in newsraces.json,
  joins once its key exists.
- pageviews: daily Wikipedia views of the pilot candidates' articles, last 10 days.
Sources that need keys (FEC, FRED, EIA) and early-vote aggregates join once their keys and files exist. Nothing raw
is printed: the job runs in a public repo whose logs are public.

    python -m simlab.snap --out ../simlab-data/snapshots
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import re
import subprocess
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

UA = {"User-Agent": "simlab/0.1 (research; +https://scaliastudio.dev)"}
REGULAR = {"AL": "Alabama", "AK": "Alaska", "AR": "Arkansas", "CO": "Colorado", "DE": "Delaware", "GA": "Georgia",
           "ID": "Idaho", "IL": "Illinois", "IA": "Iowa", "KS": "Kansas", "KY": "Kentucky", "LA": "Louisiana",
           "ME": "Maine", "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi",
           "MT": "Montana", "NE": "Nebraska", "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico",
           "NC": "North Carolina", "OK": "Oklahoma", "OR": "Oregon", "RI": "Rhode Island", "SC": "South Carolina",
           "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "VA": "Virginia", "WV": "West Virginia",
           "WY": "Wyoming"}
SPECIAL = {"OH": "Ohio", "FL": "Florida"}
AT_LARGE = ["Alaska", "Delaware", "North Dakota", "South Dakota", "Vermont", "Wyoming"]
MULTI_DISTRICT = ["Alabama", "Arizona", "Arkansas", "California", "Colorado", "Connecticut", "Florida", "Georgia",
                  "Hawaii", "Idaho", "Illinois", "Indiana", "Iowa", "Kansas", "Kentucky", "Louisiana", "Maine",
                  "Maryland", "Massachusetts", "Michigan", "Minnesota", "Mississippi", "Missouri", "Montana",
                  "Nebraska", "Nevada", "New Hampshire", "New Jersey", "New Mexico", "New York", "North Carolina",
                  "Ohio", "Oklahoma", "Oregon", "Pennsylvania", "Rhode Island", "South Carolina", "Tennessee", "Texas",
                  "Utah", "Virginia", "Washington", "West Virginia", "Wisconsin"]
WIKI_API = "https://en.wikipedia.org/w/api.php"
WIKI_PAGES = ["2026 United States Senate elections", "2026 United States House of Representatives elections",
              "Opinion polling on the second Trump presidency",
              *(f"2026 United States Senate election in {s}" for s in REGULAR.values()),
              *(f"2026 United States Senate special election in {s}" for s in SPECIAL.values()),
              *(f"2026 United States House of Representatives elections in {s}" for s in MULTI_DISTRICT),
              *(f"2026 United States House of Representatives election in {s}" for s in AT_LARGE)]
KALSHI = "https://api.elections.kalshi.com/trade-api/v2/events"
KALSHI_SERIES = ["CONTROLS", "CONTROLH", *(f"SENATE{c}" for c in REGULAR), *(f"SENATE{c}S" for c in SPECIAL)]
GAMMA = "https://gamma-api.polymarket.com/events"
POLYMARKET_SLUGS = ["which-party-will-win-the-senate-in-2026", "which-party-will-win-the-house-in-2026",
                    "balance-of-power-2026-midterms", "alabama-senate-election-winner-154",
                    *(f"{s.lower().replace(' ', '-')}-senate-election-winner"
                      for s in sorted({*REGULAR.values(), *SPECIAL.values()} - {"Alabama"}))]
NEWS = {"ohio": '("Sherrod Brown" OR "Jon Husted")', "north-carolina": '("Roy Cooper" OR "Michael Whatley")',
        "texas": '("James Talarico" OR "Ken Paxton")',
        "national": '("midterm elections" OR "midterms" OR "Senate majority" OR "generic ballot")'}
GDELT = "https://api.gdeltproject.org/api/v2/doc/doc"
GDELT_BUDGET_S = 480
PAGEVIEWS = "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/user"
CANDIDATES = ["Sherrod_Brown", "Jon_Husted", "Roy_Cooper", "Michael_Whatley", "James_Talarico", "Ken_Paxton"]


def get(url: str, params: dict | None = None, tries: int = 3, wait: float = 5.0,
        deadline: float | None = None) -> requests.Response:
    """GET with retries on connection errors, 429 and 5xx; returns the last response or raises the last error. No
    request or retry runs past `deadline` (a time.monotonic() value)."""
    for i in range(tries):
        left = None if deadline is None else deadline - time.monotonic()
        try:
            last = requests.get(url, params=params, headers=UA, timeout=90 if left is None else max(5.0, min(90.0, left)))
            if last.status_code < 500 and last.status_code != 429:
                return last
        except requests.RequestException as e:
            last = e
        pause = wait * (i + 1)
        if i == tries - 1 or (deadline is not None and time.monotonic() + pause >= deadline):
            break
        time.sleep(pause)
    if isinstance(last, Exception):
        raise last
    return last


def one(url: str, params: dict | None = None, tries: int = 3, wait: float = 5.0, deadline: float | None = None):
    def fetch():
        r = get(url, params, tries, wait, deadline)
        return r.status_code, r.content
    return fetch


def combined(parts: dict[str, tuple[str, dict]], pause: float = 0.2):
    """Several small responses stored as one JSON object {key: response JSON}; a failed part keeps its HTTP status."""
    def fetch():
        out = {}
        for key, (url, params) in parts.items():
            r = get(url, params)
            out[key] = r.json() if r.status_code == 200 else {"_http_status": r.status_code}
            time.sleep(pause)
        ok = any("_http_status" not in v for v in out.values())
        return (200 if ok else 502), json.dumps(out, sort_keys=True).encode()
    return fetch


MEDIACLOUD = "https://search.mediacloud.org/api/search/story-list"
MC_US_NATIONAL = 34412234  # Media Cloud's "United States - National" collection


def _key(name: str) -> str:
    """A key from the environment (GitHub secret), else from the Sim Research .env; never printed."""
    if os.environ.get(name):
        return os.environ[name]
    env = Path(__file__).resolve().parents[2] / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8-sig").splitlines():
            k, _, v = line.partition("=")
            if k.strip() == name:
                return v.strip().strip('"').strip("'")
    return ""


NEWS_RACES = Path(__file__).with_name("newsraces.json")  # every race's queries (simlab/newsraces.py builds it)
LEGACY = {"OH-S": "ohio", "NC": "north-carolina", "TX": "texas", "US": "national"}  # file names from the pilot
MEDIACLOUD_BUDGET_S = 300


def mediacloud(run: "Run", key: str) -> None:
    """The last day's stories for every race in newsraces.json and the nation, from Media Cloud's US national
    collection. Bounded: a 429 or 5xx is retried once after 30 s, a second 429 skips the remaining races, and so does
    the end of the 5-minute budget; each skipped race is recorded. The key rides in a header, so it never reaches the
    URL, the manifest or the logs."""
    end, stop, limited = run.when.date(), time.monotonic() + MEDIACLOUD_BUDGET_S, False
    for rid, race in json.loads(NEWS_RACES.read_text(encoding="utf-8")).items():
        name = f"mediacloud-{LEGACY.get(rid, rid.lower())}"
        if limited or time.monotonic() >= stop:
            run.error("news", name, MEDIACLOUD, "skipped: Media Cloud rate-limited" if limited else
                      f"skipped: Media Cloud's {MEDIACLOUD_BUDGET_S // 60}-minute budget is used up")
            continue
        params = {"q": race["mediacloud"], "start": f"{end - timedelta(days=1)}", "end": f"{end}",
                  "platform": "onlinenews-mediacloud", "cs": MC_US_NATIONAL, "page_size": 1000}

        def fetch(params=params):
            nonlocal limited
            for i in range(2):
                r = requests.get(MEDIACLOUD, params=params, headers={**UA, "Authorization": f"Token {key}"},
                                 timeout=max(5.0, min(90.0, stop - time.monotonic())))
                if r.status_code < 500 and r.status_code != 429:
                    break
                if i == 0:
                    time.sleep(30)
            limited = r.status_code == 429
            return r.status_code, r.content
        run.save("news", name, MEDIACLOUD, fetch)
        time.sleep(1)


def gdelt_order(when: datetime) -> list[str]:
    """The GDELT queries, starting one later each 3-hour slot: GDELT tends to answer a run's first query and
    rate-limit the rest, so no race should always come last."""
    names, k = list(NEWS), int(when.timestamp() // (3 * 3600))
    return names[k % len(names):] + names[:k % len(names)]


def slug(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")


class Run:
    def __init__(self, out: Path, when: datetime):
        self.when, self.dir, self.files = when, out / f"{when:%Y-%m-%d}" / f"{when:%H%M}", []

    def save(self, source: str, name: str, url: str, fetch) -> None:
        """fetch() -> (HTTP status, raw bytes). Anything but a 200 is recorded as an error, with no file."""
        fetched_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
        try:
            status, body = fetch()
        except Exception as e:
            return self.error(source, name, url, f"{type(e).__name__}: {e}", fetched_at)
        if status != 200:
            return self.error(source, name, url, f"HTTP {status}", fetched_at)
        path = self.dir / source / f"{name}.gz"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(gzip.compress(body, mtime=0))
        self.files.append({"source": source, "name": name, "url": url, "fetched_at": fetched_at, "status": status,
                           "file": f"{source}/{name}.gz", "bytes": len(body),
                           "sha256": hashlib.sha256(body).hexdigest()})
        print(f"{source}/{name}: {len(body) / 1e3:.0f} KB", flush=True)

    def error(self, source: str, name: str, url: str, message: str, fetched_at: str | None = None) -> None:
        self.files.append({"source": source, "name": name, "url": url, "error": message[:300],
                           "fetched_at": fetched_at or datetime.now(timezone.utc).isoformat(timespec="seconds")})
        print(f"{source}/{name}: {message[:120]}", flush=True)

    def close(self) -> dict:
        sha = os.environ.get("GITHUB_SHA") or subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True,
                                                             text=True, cwd=Path(__file__).parent).stdout.strip()
        manifest = {"started": self.when.isoformat(timespec="seconds"),
                    "finished": datetime.now(timezone.utc).isoformat(timespec="seconds"), "simlab_git": sha,
                    "files": self.files}
        self.dir.mkdir(parents=True, exist_ok=True)
        (self.dir / "manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
        return manifest


def wikipedia(run: Run) -> None:
    for i in range(0, len(WIKI_PAGES), 10):
        batch = WIKI_PAGES[i:i + 10]
        try:
            r = get(WIKI_API, {"action": "query", "prop": "revisions", "rvprop": "ids|timestamp|content",
                               "rvslots": "main", "format": "json", "formatversion": 2, "titles": "|".join(batch)})
            r.raise_for_status()
            pages, error = {p["title"]: p for p in r.json()["query"]["pages"]}, ""
        except Exception as e:
            pages, error = {}, f"{type(e).__name__}: {e}"
        for title in batch:
            url, p = f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}", pages.get(title)
            if p is None or p.get("missing"):
                run.error("wikipedia", slug(title), url, error or ("page missing" if p else "not in the response"))
            else:
                run.save("wikipedia", slug(title), url, lambda p=p: (200, json.dumps(p, sort_keys=True).encode()))
        time.sleep(1)


def snapshot(out: Path) -> dict:
    run = Run(out, datetime.now(timezone.utc))
    run.save("polls", "votehub", "https://api.votehub.com/polls", one("https://api.votehub.com/polls"))
    wikipedia(run)
    run.save("markets", "predictit", "https://www.predictit.org/api/marketdata/all/",
             one("https://www.predictit.org/api/marketdata/all/"))
    run.save("markets", "kalshi", KALSHI, combined(
        {t: (KALSHI, {"series_ticker": t, "status": "open", "with_nested_markets": "true"}) for t in KALSHI_SERIES}))
    run.save("markets", "polymarket", GAMMA, combined({s: (GAMMA, {"slug": s}) for s in POLYMARKET_SLUGS}))
    if key := _key("MEDIACLOUD_API_KEY"):
        mediacloud(run, key)
    end = run.when.date()
    run.save("pageviews", "candidates", PAGEVIEWS, combined(
        {a: (f"{PAGEVIEWS}/{a}/daily/{end - timedelta(days=10):%Y%m%d}/{end:%Y%m%d}", {}) for a in CANDIDATES}))
    stop = time.monotonic() + GDELT_BUDGET_S   # last, and bounded: a rate-limited GDELT must not cost the whole run
    for race in gdelt_order(run.when):
        if time.monotonic() + 6 >= stop:
            run.error("news", f"gdelt-{race}", GDELT, f"skipped: GDELT's {GDELT_BUDGET_S // 60}-minute budget is used up")
            continue
        time.sleep(6)
        run.save("news", f"gdelt-{race}", GDELT, one(GDELT, {
            "query": f"{NEWS[race]} sourcecountry:US sourcelang:english", "mode": "ArtList", "format": "json",
            "maxrecords": 250, "sort": "DateDesc", "timespan": "24h"}, tries=5, wait=20.0, deadline=stop))
    m = run.close()
    print(f"{sum('file' in f for f in m['files'])} of {len(m['files'])} files saved to {run.dir}")
    return m


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=Path(__file__).parents[2] / "simlab-data" / "snapshots")
    snapshot(ap.parse_args().out)
