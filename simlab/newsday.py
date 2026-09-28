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
import math
import re
import xml.etree.ElementTree as ET
from datetime import date, datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import urlparse

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

from .news import RACES, _clean
from .probes import NEWS_QUESTIONS

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


SIDES = {"democrats": "Democratic voters", "republicans": "Republican voters", "both": "Voters on both sides",
         "neither": "Neither side's voters"}
LABEL_QS = {
    "type": NEWS_QUESTIONS["type"],
    "helps_face": NEWS_QUESTIONS["helps"],
    "fires_up": {"type": "choice", "criteria": SIDES,
                 "instructions": "Whose voters might this news fire up, making them more motivated to vote?"},
    "puts_off": {"type": "choice", "criteria": SIDES,
                 "instructions": "Whose voters might this news put off, making them less keen on their candidate or "
                                 "less likely to vote?"},
    "salience": NEWS_QUESTIONS["salience"],
}
GATE_Q = {"relevant": NEWS_QUESTIONS["relevant"]}
LABEL_FIELDS = ("gate", "type", "helps_face", "fires_up", "puts_off", "salience")


def strip_outlets(title: str, names: list[str]) -> str:
    for n in sorted((n for n in names if len(n) >= 3), key=len, reverse=True):
        title = re.sub(rf"\b{re.escape(n)}\b", "", title, flags=re.I)
    return re.sub(r"\s{2,}", " ", title).strip(" -|:–—")


def story_text(story: dict, race_id: str) -> str:
    heads = [strip_outlets(t, story["outlet_names"]) for t in story["titles"][:5]]
    return f"RACE: {RACE_TEXT[race_id]}\nHEADLINES:\n" + "\n".join(f"- {h}" for h in heads if h)


def _top(p: dict) -> str:
    return max((k for k in p if not k.startswith("_")), key=p.get)


def _sides(p: dict) -> dict:
    return {"D": round(p.get("democrats", 0.0) + p.get("both", 0.0), 3),
            "R": round(p.get("republicans", 0.0) + p.get("both", 0.0), 3)}


def label(story: dict, asker) -> dict:
    """Jev's labels, asked with outlet names removed: the gate for each race the story could matter to, then the
    story's own labels (type, who it helps on its face, whose voters it fires up or puts off, salience)."""
    races = [story["race_id"]] if story["race_id"] != "US" else PILOT + ["US"]
    gate = {r: round(asker.ask_many(story_text(story, r), GATE_Q, "newsday:gate")["relevant"].get("true", 0.0), 3)
            for r in races}
    a = asker.ask_many(story_text(story, story["race_id"]), LABEL_QS, "newsday:labels")
    return {"gate": gate, "type": _top(a["type"]), "helps_face": _top(a["helps_face"]),
            "fires_up": _sides(a["fires_up"]), "puts_off": _sides(a["puts_off"]),
            "salience": round(sum(int(k) * v for k, v in a["salience"].items() if k.isdigit()), 3)}


CANDIDATE_PAGES = {"OH-S": ["Sherrod_Brown", "Jon_Husted"], "NC": ["Roy_Cooper", "Michael_Whatley"],
                   "TX": ["James_Talarico", "Ken_Paxton"]}


def load_pageviews(snap_root: Path, day: date) -> dict:
    """{article: {YYYYMMDD: views}} from the day's latest pageviews snapshot ({} if there is none)."""
    runs = sorted((snap_root / f"{day:%Y-%m-%d}").glob("*/pageviews/candidates.gz"))
    if not runs:
        return {}
    raw = json.loads(gzip.decompress(runs[-1].read_bytes()))
    return {a: {i["timestamp"][:8]: i["views"] for i in v["items"]} for a, v in raw.items() if "items" in v}


def spike_ratio(views: dict, race_id: str) -> float | None:
    """The latest day's views of the race's candidates over their median of the 7 days before (larger candidate)."""
    ratios = []
    for a in CANDIDATE_PAGES.get(race_id, []):
        series = views.get(a, {})
        days = sorted(series)
        if len(days) >= 4:
            med = float(np.median([series[d] for d in days[-8:-1]]))
            if med > 0:
                ratios.append(series[days[-1]] / med)
    return max(ratios) if ratios else None


def attention(story: dict, spike: float | None) -> dict:
    """a in [0, 1]: distinct outlets on a log scale (31 or more = 1), plus days in the news, boosted by up to 40% on a
    pageview spike. First version; weights to be checked against Matteo's spot-check answers (engine-design §9)."""
    n_o, n_d = len(story["outlets"]), len(story["days_seen"])
    base = math.log2(1 + n_o) / 5 + 0.05 * (min(n_d, 5) - 1)
    boost = 1 + 0.2 * min(max((spike or 1.0) - 1, 0.0), 2.0)
    return {"outlets": n_o, "articles": story["articles"], "days": n_d,
            "pageviews": None if spike is None else round(spike, 2), "a": round(min(1.0, base * boost), 3)}


def select(events: list[dict], per_race: int = 5, national: int = 3) -> None:
    """Mark, per race, the events that get reactions: past the gate (p >= 0.5), not about polls (polls enter through
    the filter), then the top by attention: `per_race` race stories and `national` national ones."""
    for e in events:
        e["selected"] = {}
    for r in PILOT + ["US"]:
        for scope, cap in (("race", per_race), ("national", national)):
            pool = [e for e in events if e["scope"] == scope and e["gate"].get(r, 0.0) >= 0.5 and e["type"] != "poll"]
            pool.sort(key=lambda e: (-e["attention"]["a"], -e["salience"], e["event_id"]))
            for e in pool[:cap]:
                e["selected"][r] = True
