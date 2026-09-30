"""News snapshots every 15 minutes (.github/workflows/news.yml): GDELT and Media Cloud for every race in
simlab/newsraces.json, the simulated House seats (one query per state) and the nation, and the RSS feeds of state
outlets whose licences allow reuse. Writes <out>/YYYY-MM-DD/HHMM/ in snap.py's format (news/<name>.gz plus
manifest.json), which simlab.newsday reads next to the main snapshots.

GDELT refuses an address for several minutes after one success (28-29 Sep, from GitHub and from home alike), so each
run asks only the most overdue queries within a short budget, retrying a refused query with growing pauses. A query
saved in the last 6 hours isn't asked again, and one that failed is asked by the next run; every query covers 24 hours,
so a later success fills the gap. Media Cloud (from 30 Sep, when its key is set) runs alongside at its own limits: 2
requests a minute and 4,000 a week, so the contested races, the House groups and the nation every 3 hours and the rest
every 12, about 340 requests a day. Nothing raw is printed.

    python -m simlab.newsnap --out ../simlab-data/news [--budget 540] [--races <races.json>]
"""
from __future__ import annotations

import argparse
import json
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

from . import newsraces, snap

# Only nonpartisan outlets whose feeds answer a declared bot and whose licences allow reuse (29 Sep). The States
# Newsroom sites (CC BY-NC-ND) refuse bots with 403, so they aren't here; no Iowa outlet qualified (GDELT carries
# 250+ Iowa articles a week).
RSS_FEEDS = {"signal-ohio": ("OH", "Signal Ohio", "https://signalohio.org/feed/"),
             "signal-cleveland": ("OH", "Signal Cleveland", "https://signalcleveland.org/feed/"),
             "texas-tribune": ("TX", "The Texas Tribune", "https://www.texastribune.org/feeds/main/"),
             "carolina-public-press": ("NC", "Carolina Public Press", "https://carolinapublicpress.org/feed/"),  # CC BY-ND
             "maine-monitor": ("ME", "The Maine Monitor", "https://themainemonitor.org/feed/")}  # free to republish
PILOT = {snap.LEGACY.get(r, r.lower()) for r in newsraces.PILOT} | {"national"}
EVERY_H = 6
EVERY_H_HOUSE = 12  # a state's House seats get a few articles a day, and each answer covers 24 hours
MC_EVERY_H, MC_EVERY_H_REST = 3, 12  # Media Cloud: the contested races, the House groups and the nation; the rest


def every_h(slug: str) -> float:
    return EVERY_H_HOUSE if slug.endswith("-h") else EVERY_H


def queries(races_json: Path | None = None, field: str = "query") -> dict[str, str]:
    """{file slug: GDELT query (field="mediacloud": Media Cloud's)} for every race in newsraces.json and the nation
    (pilot races keep their old names), plus one per state for the simulated House seats in the latest races.json
    ("oh-h")."""
    races = json.loads(snap.NEWS_RACES.read_text(encoding="utf-8"))
    if races_json and races_json.exists():
        races |= {g: c for g, c in newsraces.house(json.loads(races_json.read_text(encoding="utf-8"))).items()
                  if c.get("seats")}
    return {snap.LEGACY.get(rid, rid.lower()): c[field] for rid, c in races.items()}


def last_saved(root: Path, now: datetime, back: int = 2) -> dict[str, datetime]:
    """{file name: start of the newest run that saved it}, from the manifests of the last `back` days."""
    out: dict = {}
    for k in range(back, -1, -1):
        d = (now - timedelta(days=k)).date()
        for m in sorted((root / f"{d}").glob("*/manifest.json")):
            try:
                when = datetime.strptime(f"{d}{m.parent.name}", "%Y-%m-%d%H%M").replace(tzinfo=timezone.utc)
            except ValueError:
                continue
            for f in json.loads(m.read_text(encoding="utf-8"))["files"]:
                if "file" in f:
                    out[f["name"]] = max(out.get(f["name"], when), when)
    return out


def due(slugs: list[str], last: dict, now: datetime, first: set = frozenset(), source: str = "gdelt",
        every=every_h) -> list[str]:
    """The queries not saved in the last `every(slug)` hours (GDELT: 6, a state's House seats 12): those in `first`
    (the races that simulate or watch, and the nation) before the rest, the nation first among equals (it reaches every
    race), and the longest unsaved (never saved counts as longest) first. Until the full run the pilot races and the
    nation come before all others: they are the only races the daily job simulates, and GDELT answers only a few
    queries a run."""
    never = datetime.min.replace(tzinfo=timezone.utc)
    late = [s for s in slugs if now - last.get(f"{source}-{s}", never) >= timedelta(hours=every(s))]
    top = PILOT if f"{now:%Y-%m-%d}" < newsraces.FULL_RUN else first
    return sorted(late, key=lambda s: (s not in top, s not in first, last.get(f"{source}-{s}", never), s != "national",
                                       s))


def gdelt(run, qs: dict, order: list[str], budget_s: float) -> None:
    """Ask the queries in `order` until the budget ends. A refused query is retried with pauses of 30, 60, 90 s...
    rather than skipped (the refusal is for the address, not the query); queries left at the end are recorded as
    skipped, for the next run."""
    stop = time.monotonic() + budget_s
    for slug in order:
        if time.monotonic() + 6 >= stop:
            run.error("news", f"gdelt-{slug}", snap.GDELT, "skipped: this run's budget is used up")
            continue
        time.sleep(6)  # GDELT asks for at most one request every 5 s
        run.save("news", f"gdelt-{slug}", snap.GDELT, snap.one(snap.GDELT, {
            "query": f"{qs[slug]} sourcecountry:US sourcelang:english", "mode": "ArtList", "format": "json",
            "maxrecords": 250, "sort": "DateDesc", "timespan": "24h"}, tries=12, wait=30.0, deadline=stop))


def rss(run) -> None:
    for name, (_, _, url) in RSS_FEEDS.items():
        run.save("news", f"rss-{name}", url, snap.one(url))


def first_races(races_json: Path | None) -> set[str]:
    """File slugs asked first: the pilot races and the nation, plus every race that simulates or watches in races.json
    (a House seat through its state's group)."""
    out = set(PILOT)
    if races_json and races_json.exists():
        for rid, r in json.loads(races_json.read_text(encoding="utf-8")).items():
            if isinstance(r, dict) and r.get("tier") in ("simulate", "watch"):
                out.add(f"{r['state'].lower()}-h" if r.get("office") == "house" else snap.LEGACY.get(rid, rid.lower()))
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=Path(__file__).parents[2] / "simlab-data" / "news")
    ap.add_argument("--budget", type=float, default=540.0, help="seconds for GDELT and Media Cloud in this run")
    ap.add_argument("--races", type=Path, default=None, help="the latest races.json, to ask its contested races first")
    a = ap.parse_args()
    now = datetime.now(timezone.utc)
    run = snap.Run(a.out, now)
    rss(run)
    last, first = last_saved(a.out, now), first_races(a.races)
    mc, morder = None, []
    if key := snap._key("MEDIACLOUD_API_KEY"):
        mq = queries(a.races, "mediacloud")
        morder = due(list(mq), last, now, first, "mediacloud", lambda s: MC_EVERY_H if s in first else MC_EVERY_H_REST)
        mc = threading.Thread(target=snap.mediacloud,
                              args=(run, key, {f"mediacloud-{s}": mq[s] for s in morder}, a.budget))
        mc.start()
    qs = queries(a.races)
    # with Media Cloud on, the races on statistics alone (no reactions) leave GDELT to the contested ones
    order = [s for s in due(list(qs), last, now, first) if s in first or not key]
    gdelt(run, qs, order, a.budget)
    if mc:
        mc.join()
    m = run.close()
    saved = sum("file" in f for f in m["files"])
    print(f"{saved} of {len(m['files'])} files saved; {len(order)} GDELT and {len(morder)} Media Cloud queries were due")


if __name__ == "__main__":
    main()
