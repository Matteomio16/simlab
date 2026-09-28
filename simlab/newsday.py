"""The day's news for the engine: snapshots -> stories -> Jev labels -> attention -> neutral cards -> events.jsonl.

    python -m simlab.newsday [--date YYYY-MM-DD] [--snap ../simlab-data/snapshots] [--out ../simlab-data/derived]

Reads only saved snapshots, so any day can be re-run. Writes derived/<date>/events.jsonl for the reaction harness and
news_private.jsonl with the raw headlines, links and outlets (never published). Logs print counts, never headlines: the
daily job runs in a public repo. Contract: docs/engine-design.md §4 and §7.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import xml.etree.ElementTree as ET
from datetime import date, datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import urlparse

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

from .news import RACES, _clean

SCHEMA = 1
SNAP_RACES = {"ohio": "OH-S", "north-carolina": "NC", "texas": "TX", "national": "US"}
PILOT = ["OH-S", "NC", "TX"]
RACE_TEXT = {"OH-S": RACES["Ohio"][1], "NC": RACES["North Carolina"][1], "TX": RACES["Texas"][1],
             "US": RACES["national"][1]}


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat(timespec="seconds")


def parse_googlenews(raw: bytes, race_id: str) -> list[dict]:
    out = []
    for it in ET.fromstring(raw).iter("item"):
        src, when = it.find("source"), it.findtext("pubDate")
        if not when:
            continue
        out.append({"race_id": race_id, "title": it.findtext("title") or "", "url": it.findtext("link") or "",
                    "outlet": (src.text or "").strip() if src is not None else "",
                    "domain": urlparse(src.get("url", "")).netloc.removeprefix("www.") if src is not None else "",
                    "seen": _iso(parsedate_to_datetime(when)), "source": "googlenews"})
    return out


def parse_gdelt(raw: bytes, race_id: str) -> list[dict]:
    try:
        arts = json.loads(raw).get("articles", [])
    except ValueError:  # GDELT sometimes returns malformed JSON
        return []
    return [{"race_id": race_id, "title": a.get("title") or "", "url": a.get("url") or "",
             "outlet": a.get("domain") or "", "domain": a.get("domain") or "",
             "seen": _iso(datetime.strptime(a["seendate"], "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)),
             "source": "gdelt"} for a in arts if a.get("seendate")]


PARSERS = {"googlenews": parse_googlenews, "gdelt": parse_gdelt}


def read_day(snap_root: Path, day: date) -> list[dict]:
    """Every news article in the day's snapshot runs, once per race (earliest sighting kept), titles cleaned."""
    best: dict = {}
    for manifest in sorted((snap_root / f"{day:%Y-%m-%d}").glob("*/manifest.json")):
        for f in json.loads(manifest.read_text(encoding="utf-8"))["files"]:
            kind, _, slug = f.get("name", "").partition("-")
            if f.get("source") != "news" or "file" not in f or kind not in PARSERS or slug not in SNAP_RACES:
                continue
            for a in PARSERS[kind](gzip.decompress((manifest.parent / f["file"]).read_bytes()), SNAP_RACES[slug]):
                a["title"] = _clean(a["title"])
                key = (a["race_id"], a["url"] or f"{a['title'].lower()}|{a['domain']}")
                if a["title"] and (key not in best or a["seen"] < best[key]["seen"]):
                    best[key] = a
    return sorted(best.values(), key=lambda a: (a["race_id"], a["seen"]))


def cluster_titles(titles: list[str], firsts: list[str], sim: float = 0.55, days: float = 3.0) -> list[list[int]]:
    """Groups of similar headlines (TF-IDF cosine >= sim, first seen within `days`), joined transitively."""
    n = len(titles)
    parent = list(range(n))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    if n > 1:
        try:
            X = TfidfVectorizer(stop_words="english", ngram_range=(1, 2)).fit_transform(titles)
        except ValueError:  # headlines made only of stop words
            X = None
        if X is not None:
            S = (X @ X.T).toarray()
            when = [datetime.fromisoformat(f).timestamp() for f in firsts]
            for i, j in zip(*np.where(np.triu(S, 1) >= sim)):
                if abs(when[i] - when[j]) <= days * 86400:
                    parent[find(i)] = find(j)
    groups: dict = {}
    for i in range(n):
        groups.setdefault(find(i), []).append(i)
    return list(groups.values())


def make_stories(articles: list[dict], sim: float = 0.55, days: float = 3.0) -> list[dict]:
    """Per race: identical headlines (syndicated copies) merge, then similar ones cluster into one story."""
    stories = []
    for race_id in sorted({a["race_id"] for a in articles}):
        by_title: dict = {}
        for a in articles:
            if a["race_id"] == race_id:
                by_title.setdefault(a["title"].lower(), []).append(a)
        keys = list(by_title)
        firsts = [min(a["seen"] for a in by_title[k]) for k in keys]
        for grp in cluster_titles(keys, firsts, sim, days):
            members = [a for i in grp for a in by_title[keys[i]]]
            rep = max(grp, key=lambda i: (len({a["domain"] or a["outlet"] for a in by_title[keys[i]]}), -i))
            count: dict = {}
            for a in members:
                count[a["title"]] = count.get(a["title"], 0) + 1
            stories.append({
                "race_id": race_id, "title": by_title[keys[rep]][0]["title"],
                "titles": sorted(count, key=lambda t: (-count[t], t))[:12],
                "outlets": sorted({a["domain"] or a["outlet"] for a in members} - {""}),
                "outlet_names": sorted({a["outlet"] for a in members} - {""}),
                "articles": len(members), "first_seen": min(a["seen"] for a in members),
                "last_seen": max(a["seen"] for a in members),
                "days_seen": sorted({a["seen"][:10] for a in members}),
                "urls": sorted({a["url"] for a in members} - {""})[:20]})
    return stories


def event_id(race_id: str, first_seen: str, title: str) -> str:
    return f"{race_id}-{first_seen[:10].replace('-', '')}-{hashlib.sha1(title.lower().encode()).hexdigest()[:8]}"


def carry_over(stories: list[dict], known: list[dict], sim: float = 0.5) -> list[dict]:
    """A story that continues a known event (same race, similar headlines) keeps its id, first sighting and labels;
    each known event is claimed at most once, by the best-covered story."""
    used: set = set()
    for s in sorted(stories, key=lambda s: -s["articles"]):
        s["known"] = None
        cands = [k for k in known if k["race_id"] == s["race_id"] and k["event_id"] not in used]
        if cands:
            try:
                X = TfidfVectorizer(stop_words="english", ngram_range=(1, 2)).fit_transform(
                    [" ".join(s["titles"])] + [" ".join(k["titles"]) for k in cands])
                sims = (X[0] @ X[1:].T).toarray()[0]
                j = int(np.argmax(sims))
                if sims[j] >= sim:
                    s["known"] = cands[j]
            except ValueError:
                pass
        if s["known"]:
            k = s["known"]
            used.add(k["event_id"])
            s["event_id"], s["first_seen"] = k["event_id"], min(k["first_seen"], s["first_seen"])
            s["days_seen"] = sorted(set(k["days_seen"]) | set(s["days_seen"]))
        else:
            s["event_id"] = event_id(s["race_id"], s["first_seen"], s["title"])
    return stories
