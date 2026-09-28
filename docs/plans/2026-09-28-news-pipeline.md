# News Pipeline (A4) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn each day's news snapshots into `events.jsonl`. Each row is one story with its races, Jev labels, attention
and a neutral event card, ready for the reaction harness.

**Architecture:** A new module, `simlab/newsday.py`, made of small functions:
1. parse the snapshots
2. drop repeat sightings
3. cluster headlines into stories
4. carry stories over from earlier days
5. label them with Jev
6. score attention
7. select the stories that get reactions
8. write cards
9. write the files

Model calls are passed in (the Jev asker and the card writers), so the tests run offline with fakes. The test-bench
prototype `simlab/news.py` stays as it is. Only its `RACES` table and `_clean` are reused.

**Tech Stack:** Python 3.13, the standard library (`xml`, `gzip`, `json`, `unittest`), numpy, scikit-learn (installed),
`simlab.askers.DecisionAsker` (Jev), `simlab.core.Chat` (DeepSeek, with GLM as fallback).

**Spec:** `docs/engine-design.md` §4 (news pipeline) and §7 (the `events.jsonl` contract).

## Global Constraints

- Tests use `unittest`, as the other sessions do (no pytest; no new dependencies). Run them from `simlab/` with
  `.venv/Scripts/python.exe -m unittest tests.test_newsday -v`.
- Outputs go to `simlab-data/derived/YYYY-MM-DD/events.jsonl` and `news_private.jsonl`. Raw headlines, links and outlets
  appear only in `news_private.jsonl`.
- Every row carries `schema` (1), `date` and `run_id`. `first_seen` is a UTC ISO timestamp.
- Race ids for the pilot are `OH-S`, `NC`, `TX`, plus `US` for the national scope. Snapshot names map as
  `ohio→OH-S`, `north-carolina→NC`, `texas→TX`, `national→US`.
- Selection rules:
  - Jev labels news with outlet names removed.
  - The gate passes at p ≥ 0.5.
  - Stories of type `poll` get no reactions.
  - Top 5 per race by attention; top 3 national stories per race.
- Cards are 1–3 neutral sentences with no outlet names and no poll or survey wording.
- Model policy: Jev for labels, DeepSeek V4.1 Flash for cards (GLM as fallback). Never Claude or Gemini.
- Logs print counts only, never headlines, because the daily job runs in a public repository.
- Tag model calls `newsday:<step>`. The ledger's hard cap applies.

---

### Task 1: Read the day's news from the snapshots

**Files:**
- Create: `simlab/newsday.py`
- Test: `tests/test_newsday.py`

**Interfaces:**
- Produces:
  - `read_day(snap_root: Path, day: date) -> list[dict]`
  - article dicts `{race_id, title, url, outlet, domain, seen (UTC ISO), source}`
  - `parse_googlenews(raw: bytes, race_id: str) -> list[dict]`
  - `parse_gdelt(raw: bytes, race_id: str) -> list[dict]`
  - constants `SCHEMA`, `SNAP_RACES`, `PILOT`, `RACE_TEXT`

- [ ] **Step 1: Write the failing test**

```python
import gzip
import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

from simlab import newsday

RSS = """<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel>
<item><title>Brown and Husted clash over tariffs - Cleveland.com</title><link>https://news.google.com/a1</link>
<pubDate>Mon, 28 Sep 2026 08:00:00 GMT</pubDate><source url="https://www.cleveland.com">Cleveland.com</source></item>
<item><title>Crypto PAC to spend $30M against Sherrod Brown - Politico</title><link>https://news.google.com/a2</link>
<pubDate>Mon, 28 Sep 2026 07:00:00 GMT</pubDate><source url="https://www.politico.com">Politico</source></item>
</channel></rss>"""
GDELT = {"articles": [{"url": "https://example.com/x", "title": "Talarico , Paxton trade attacks",
                       "seendate": "20260928T090000Z", "domain": "example.com"}]}


def snapshot(root: Path, day: str, hhmm: str, files: dict) -> None:
    run = root / day / hhmm
    entries = []
    for name, body in files.items():
        path = run / "news" / f"{name}.gz"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(gzip.compress(body, mtime=0))
        entries.append({"source": "news", "name": name, "file": f"news/{name}.gz"})
    entries.append({"source": "news", "name": "gdelt-ohio", "error": "HTTP 429"})
    (run / "manifest.json").write_text(json.dumps({"files": entries}), encoding="utf-8")


class ReadDay(unittest.TestCase):
    def test_parses_both_sources_dedupes_and_cleans(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            snapshot(root, "2026-09-28", "0036", {"googlenews-ohio": RSS.encode()})
            snapshot(root, "2026-09-28", "0341", {"googlenews-ohio": RSS.encode(),
                                                   "gdelt-texas": json.dumps(GDELT).encode()})
            arts = newsday.read_day(root, date(2026, 9, 28))
        self.assertEqual([a["race_id"] for a in arts], ["OH-S", "OH-S", "TX"])
        oh = {a["title"]: a for a in arts if a["race_id"] == "OH-S"}
        self.assertEqual(oh["Brown and Husted clash over tariffs"]["domain"], "cleveland.com")
        self.assertEqual(oh["Brown and Husted clash over tariffs"]["seen"], "2026-09-28T08:00:00+00:00")
        tx = [a for a in arts if a["race_id"] == "TX"][0]
        self.assertEqual(tx["title"], "Talarico, Paxton trade attacks")
        self.assertEqual(tx["source"], "gdelt")

    def test_bad_gdelt_json_is_skipped(self):
        self.assertEqual(newsday.parse_gdelt(b'{"articles": [ {bad', "TX"), [])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test and check it fails**

Run: `.venv/Scripts/python.exe -m unittest tests.test_newsday -v`
Expected: ERROR, `ImportError: cannot import name 'newsday'`.

- [ ] **Step 3: Write the minimal implementation**

```python
"""The day's news for the engine: snapshots -> stories -> Jev labels -> attention -> neutral cards -> events.jsonl.

    python -m simlab.newsday [--date YYYY-MM-DD] [--snap ../simlab-data/snapshots] [--out ../simlab-data/derived]

Reads only saved snapshots, so any day can be re-run. Writes derived/<date>/events.jsonl for the reaction harness and
news_private.jsonl with the raw headlines, links and outlets (never published). Logs print counts, never headlines: the
daily job runs in a public repo. Contract: docs/engine-design.md §4 and §7.
"""
from __future__ import annotations

import gzip
import json
import xml.etree.ElementTree as ET
from datetime import date, datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import urlparse

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
```

- [ ] **Step 4: Run the test and check it passes**

Run: `.venv/Scripts/python.exe -m unittest tests.test_newsday -v`
Expected: 2 tests OK.

- [ ] **Step 5: Commit**

```bash
git add simlab/newsday.py tests/test_newsday.py
git commit -m "newsday: read the day's news from the snapshots"
```

### Task 2: Stories, and stories that continue from earlier days

**Files:**
- Modify: `simlab/newsday.py` (add below `read_day`)
- Test: `tests/test_newsday.py` (add the classes before `if __name__`)

**Interfaces:**
- Consumes: article dicts from Task 1.
- Produces:
  - `cluster_titles(titles, firsts, sim=0.55, days=3.0) -> list[list[int]]`
  - `make_stories(articles, sim=0.55, days=3.0) -> list[dict]`, returning stories
    `{race_id, title, titles, outlets, outlet_names, articles, first_seen, last_seen, days_seen, urls}`
  - `event_id(race_id, first_seen, title) -> str`
  - `carry_over(stories, known, sim=0.5) -> list[dict]`, which adds `event_id` and `known` (the earlier event row, or
    None)

- [ ] **Step 1: Write the failing test**

```python
def art(race, title, seen, domain="a.com", outlet="A"):
    return {"race_id": race, "title": title, "url": f"https://{domain}/{title[:24]}", "outlet": outlet,
            "domain": domain, "seen": seen, "source": "gdelt"}


class Stories(unittest.TestCase):
    def test_similar_headlines_cluster_and_outlets_count(self):
        arts = [art("OH-S", "Crypto super PAC to spend $30 million against Sherrod Brown", "2026-09-28T07:00:00+00:00",
                    "politico.com", "Politico"),
                art("OH-S", "Crypto super PAC will spend $30 million against Sherrod Brown in Ohio",
                    "2026-09-28T08:00:00+00:00", "axios.com", "Axios"),
                art("OH-S", "Husted visits Dayton factory", "2026-09-28T09:00:00+00:00")]
        stories = newsday.make_stories(arts)
        self.assertEqual(len(stories), 2)
        pac = [s for s in stories if "PAC" in s["title"]][0]
        self.assertEqual(pac["outlets"], ["axios.com", "politico.com"])
        self.assertEqual(pac["first_seen"], "2026-09-28T07:00:00+00:00")

    def test_carry_over_keeps_id_and_first_seen(self):
        s = newsday.make_stories([art("OH-S", "Crypto super PAC to spend $30 million against Sherrod Brown",
                                      "2026-09-29T07:00:00+00:00")])
        known = [{"event_id": "OH-S-20260928-abcdef12", "race_id": "OH-S", "first_seen": "2026-09-28T07:00:00+00:00",
                  "days_seen": ["2026-09-28"], "titles": ["Crypto super PAC to spend $30 million against Sherrod Brown"]}]
        out = newsday.carry_over(s, known)
        self.assertEqual(out[0]["event_id"], "OH-S-20260928-abcdef12")
        self.assertEqual(out[0]["first_seen"], "2026-09-28T07:00:00+00:00")
        self.assertEqual(out[0]["days_seen"], ["2026-09-28", "2026-09-29"])

    def test_new_story_gets_deterministic_id(self):
        s = newsday.carry_over(newsday.make_stories([art("TX", "Paxton sues county", "2026-09-28T10:00:00+00:00")]), [])
        self.assertEqual(s[0]["event_id"], newsday.event_id("TX", "2026-09-28T10:00:00+00:00", "Paxton sues county"))
        self.assertTrue(s[0]["event_id"].startswith("TX-20260928-"))
        self.assertIsNone(s[0]["known"])
```

- [ ] **Step 2: Run the test and check it fails**

Run: `.venv/Scripts/python.exe -m unittest tests.test_newsday -v`
Expected: `AttributeError: module 'simlab.newsday' has no attribute 'make_stories'`.

- [ ] **Step 3: Write the implementation**

Add `import hashlib`, `import numpy as np` and `from sklearn.feature_extraction.text import TfidfVectorizer` to the
imports, then:

```python
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
```

- [ ] **Step 4: Run the tests and check they pass**

Run: `.venv/Scripts/python.exe -m unittest tests.test_newsday -v`
Expected: 5 tests OK.

- [ ] **Step 5: Commit**

```bash
git add simlab/newsday.py tests/test_newsday.py
git commit -m "newsday: stories and carry-over across days"
```

### Task 3: Jev labels, with outlet names removed

**Files:**
- Modify: `simlab/newsday.py`
- Test: `tests/test_newsday.py`

**Interfaces:**
- Consumes: stories from Task 2. Any asker with
  `ask_many(state: str, questions: dict, tag: str) -> {qid: {option: p}}`.
- Produces:
  - `label(story, asker) -> {gate: {race_id: p}, type, helps_face, fires_up: {D, R}, puts_off: {D, R}, salience}`
  - `strip_outlets(title, names) -> str`
  - `story_text(story, race_id) -> str`
  - `LABEL_FIELDS`

- [ ] **Step 1: Write the failing test**

```python
class FakeAsker:
    def __init__(self):
        self.states = []

    def ask_many(self, state, questions, tag=""):
        self.states.append(state)
        out = {}
        for qid, q in questions.items():
            if qid == "relevant":
                out[qid] = {"true": 0.8, "false": 0.2}
            elif qid == "salience":
                out[qid] = {"0": 0.0, "1": 0.5, "2": 0.5, "3": 0.0, "4": 0.0}
            elif qid in ("fires_up", "puts_off"):
                out[qid] = {"democrats": 0.6, "republicans": 0.1, "both": 0.2, "neither": 0.1}
            else:
                keys = list(q["criteria"])
                out[qid] = {k: (0.7 if i == 0 else 0.3 / (len(keys) - 1)) for i, k in enumerate(keys)}
        return out


class Labels(unittest.TestCase):
    def story(self, race="OH-S"):
        return {"race_id": race, "title": "Fox News: Brown leads in new ad war",
                "titles": ["Fox News: Brown leads in new ad war"], "outlet_names": ["Fox News"],
                "outlets": ["foxnews.com"]}

    def test_maps_answers_and_hides_outlets(self):
        fake = FakeAsker()
        lab = newsday.label(self.story(), fake)
        self.assertEqual(lab["gate"], {"OH-S": 0.8})
        self.assertEqual(lab["type"], "scandal")
        self.assertEqual(lab["helps_face"], "democrat")
        self.assertEqual(lab["fires_up"], {"D": 0.8, "R": 0.3})
        self.assertAlmostEqual(lab["salience"], 1.5)
        self.assertTrue(all("Fox News" not in s for s in fake.states))
        self.assertIn("- Brown leads in new ad war", fake.states[0])

    def test_national_story_gets_a_gate_per_race(self):
        lab = newsday.label(self.story("US"), FakeAsker())
        self.assertEqual(sorted(lab["gate"]), ["NC", "OH-S", "TX", "US"])
```

- [ ] **Step 2: Run the test and check it fails**

Run: `.venv/Scripts/python.exe -m unittest tests.test_newsday -v`
Expected: `AttributeError: module 'simlab.newsday' has no attribute 'label'`.

- [ ] **Step 3: Write the implementation**

Add `import re` and `from .probes import NEWS_QUESTIONS` to the imports, then:

```python
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
```

- [ ] **Step 4: Run the tests and check they pass**

Run: `.venv/Scripts/python.exe -m unittest tests.test_newsday -v`
Expected: 7 tests OK.

- [ ] **Step 5: Commit**

```bash
git add simlab/newsday.py tests/test_newsday.py
git commit -m "newsday: Jev labels incl. whose voters a story fires up or puts off"
```

### Task 4: Attention and which stories get reactions

**Files:**
- Modify: `simlab/newsday.py`
- Test: `tests/test_newsday.py`

**Interfaces:**
- Consumes: stories (with `outlets`, `days_seen`, `articles`) and event rows (with `scope`, `gate`, `type`,
  `salience`, `attention.a`, `event_id`).
- Produces:
  - `load_pageviews(snap_root, day) -> {article: {YYYYMMDD: views}}`
  - `spike_ratio(views, race_id) -> float | None`
  - `attention(story, spike) -> {outlets, articles, days, pageviews, a}`
  - `select(events, per_race=5, national=3) -> None`, which sets `event["selected"] = {race_id: True}`

- [ ] **Step 1: Write the failing test**

```python
def cov(n, d=1):
    return {"outlets": [f"o{i}.com" for i in range(n)], "days_seen": [f"2026-09-{28 - i}" for i in range(d)],
            "articles": n}


class Attention(unittest.TestCase):
    def test_more_outlets_more_attention_capped(self):
        a1, a7, a40 = (newsday.attention(cov(n), None)["a"] for n in (1, 7, 40))
        self.assertLess(a1, a7)
        self.assertEqual(a40, 1.0)
        self.assertGreater(newsday.attention(cov(1), 3.0)["a"], a1)
        self.assertGreater(newsday.attention(cov(1, 3), None)["a"], a1)

    def test_spike_ratio(self):
        views = {"Sherrod_Brown": {f"202609{d:02d}": 100 for d in range(18, 27)} | {"20260927": 300}}
        self.assertAlmostEqual(newsday.spike_ratio(views, "OH-S"), 3.0)
        self.assertIsNone(newsday.spike_ratio({}, "OH-S"))


class Select(unittest.TestCase):
    def ev(self, eid, scope, gate, a, typ="policy"):
        return {"event_id": eid, "scope": scope, "gate": gate, "type": typ, "salience": 1.0, "attention": {"a": a}}

    def test_gate_poll_rule_and_caps(self):
        evs = [self.ev(f"OH-S-{i}", "race", {"OH-S": 0.9}, a=i / 10) for i in range(7)]
        evs += [self.ev("OH-S-poll", "race", {"OH-S": 0.9}, a=1.0, typ="poll"),
                self.ev("OH-S-weak", "race", {"OH-S": 0.3}, a=1.0),
                self.ev("US-1", "national", {"OH-S": 0.9, "NC": 0.2, "TX": 0.9, "US": 0.9}, a=0.5)]
        newsday.select(evs)
        chosen = sorted(e["event_id"] for e in evs if e["selected"].get("OH-S") and e["scope"] == "race")
        self.assertEqual(chosen, ["OH-S-2", "OH-S-3", "OH-S-4", "OH-S-5", "OH-S-6"])
        self.assertEqual(evs[-1]["selected"], {"OH-S": True, "TX": True, "US": True})
```

- [ ] **Step 2: Run the test and check it fails**

Run: `.venv/Scripts/python.exe -m unittest tests.test_newsday -v`
Expected: `AttributeError: module 'simlab.newsday' has no attribute 'attention'`.

- [ ] **Step 3: Write the implementation**

Add `import math` to the imports, then:

```python
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
```

- [ ] **Step 4: Run the tests and check they pass**

Run: `.venv/Scripts/python.exe -m unittest tests.test_newsday -v`
Expected: 10 tests OK.

- [ ] **Step 5: Commit**

```bash
git add simlab/newsday.py tests/test_newsday.py
git commit -m "newsday: attention from coverage and pageviews; selection rules"
```

### Task 5: Neutral event cards

**Files:**
- Modify: `simlab/newsday.py`
- Test: `tests/test_newsday.py`

**Interfaces:**
- Consumes: a story (`race_id`, `titles`, `outlet_names`). Chat objects with
  `complete(messages, tag, max_tokens, json_mode) -> str`.
- Produces:
  - `write_card(story, chats: list) -> str`, which returns `''` when no model follows the rules
  - `card_ok(card, outlet_names) -> bool`

- [ ] **Step 1: Write the failing test**

```python
class FakeChat:
    def __init__(self, replies):
        self.replies, self.calls = list(replies), 0

    def complete(self, messages, tag="", max_tokens=300, json_mode=True):
        self.calls += 1
        return self.replies.pop(0) if self.replies else '{"card": ""}'


GOOD = "A crypto industry group plans to spend $30 million opposing Sherrod Brown."


class Cards(unittest.TestCase):
    story = {"race_id": "OH-S", "titles": ["Crypto PAC to spend $30M against Brown"], "outlet_names": ["Politico"]}

    def test_rule_breaking_card_retries_then_falls_back(self):
        bad = FakeChat(['{"card": "Politico reports a crypto PAC will spend $30M."}',
                        '{"card": "A new poll shows Brown ahead."}'])
        good = FakeChat(['{"card": "%s"}' % GOOD])
        self.assertEqual(newsday.write_card(self.story, [bad, good]), GOOD)
        self.assertEqual(bad.calls, 2)

    def test_no_valid_card_gives_empty(self):
        self.assertEqual(newsday.write_card(self.story, [FakeChat(["not json", "{}"])]), "")
```

- [ ] **Step 2: Run the test and check it fails**

Run: `.venv/Scripts/python.exe -m unittest tests.test_newsday -v`
Expected: `AttributeError: module 'simlab.newsday' has no attribute 'write_card'`.

- [ ] **Step 3: Write the implementation**

```python
CARD_SYSTEM = (
    "You write short, neutral summaries of news events for a research simulation of voters. Use only the headlines "
    "given. In 1 to 3 plain sentences, say what happened and who was involved. Do not name any news outlet or website. "
    "Do not use the words poll, polls, polling, pollster, survey or surveys. No opinions and no predictions. "
    'Reply with JSON only: {"card": "..."}')
FORBIDDEN = re.compile(r"\b(poll|polls|polling|pollsters?|surveys?)\b", re.I)


def card_ok(card: str, outlet_names: list[str]) -> bool:
    low = card.lower()
    return (0 < len(card) <= 450 and not FORBIDDEN.search(card)
            and not any(n.lower() in low for n in outlet_names if len(n) >= 3))


def write_card(story: dict, chats: list) -> str:
    """1-3 neutral sentences from the first model that follows the rules (two tries each); '' if none does."""
    user = story_text(story, story["race_id"])
    for chat in chats:
        for note in ("", "\nYour previous answer broke a rule. Follow every rule exactly."):
            try:
                text = chat.complete([{"role": "system", "content": CARD_SYSTEM},
                                      {"role": "user", "content": user + note}], tag="newsday:card", max_tokens=200)
                card = str(json.loads(text[text.index("{"): text.rindex("}") + 1]).get("card", "")).strip()
            except (ValueError, RuntimeError):
                card = ""
            if card_ok(card, story["outlet_names"]):
                return card
    return ""
```

- [ ] **Step 4: Run the tests and check they pass**

Run: `.venv/Scripts/python.exe -m unittest tests.test_newsday -v`
Expected: 12 tests OK.

- [ ] **Step 5: Commit**

```bash
git add simlab/newsday.py tests/test_newsday.py
git commit -m "newsday: neutral event cards with rule checks and fallback model"
```

### Task 6: The day's run, the files and the command line

**Files:**
- Modify: `simlab/newsday.py`
- Test: `tests/test_newsday.py`

**Interfaces:**
- Consumes: everything above.
- Produces:
  - `run(day, snap_root, derived_root, run_id, asker, chats) -> summary dict`, which writes
    `derived/<day>/events.jsonl` (the contract row per event, plus `selected`) and `news_private.jsonl`
  - `load_known(derived_root, day, lookback=7) -> list[dict]`
  - `_jsonl(path) -> list[dict]`
  - CLI `python -m simlab.newsday`

- [ ] **Step 1: Write the failing test**

```python
REQUIRED = ["schema", "date", "run_id", "event_id", "first_seen", "last_seen", "scope", "races", "gate", "type",
            "helps_face", "fires_up", "puts_off", "salience", "attention", "card", "selected"]


class Run(unittest.TestCase):
    def test_writes_events_and_private_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            snap, derived = Path(tmp) / "snap", Path(tmp) / "derived"
            snapshot(snap, "2026-09-28", "0036", {"googlenews-ohio": RSS.encode()})
            summary = newsday.run(date(2026, 9, 28), snap, derived, "test-run", FakeAsker(),
                                  [FakeChat(['{"card": "%s"}' % GOOD] * 5)])
            events = newsday._jsonl(derived / "2026-09-28" / "events.jsonl")
            private = newsday._jsonl(derived / "2026-09-28" / "news_private.jsonl")
        self.assertEqual(summary["stories"], 2)
        for e in events:
            self.assertEqual(set(REQUIRED) - set(e), set())
            self.assertNotIn("titles", e)
        self.assertEqual({p["event_id"] for p in private}, {e["event_id"] for e in events})
        self.assertTrue(all(e["card"] for e in events if e["selected"]))

    def test_second_day_reuses_labels_and_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            snap, derived = Path(tmp) / "snap", Path(tmp) / "derived"
            snapshot(snap, "2026-09-28", "0036", {"googlenews-ohio": RSS.encode()})
            snapshot(snap, "2026-09-29", "0036", {"googlenews-ohio": RSS.replace("28 Sep", "29 Sep").encode()})
            chat = FakeChat(['{"card": "%s"}' % GOOD] * 10)
            newsday.run(date(2026, 9, 28), snap, derived, "d1", FakeAsker(), [chat])
            asker2 = FakeAsker()
            newsday.run(date(2026, 9, 29), snap, derived, "d2", asker2, [chat])
            day1 = {e["event_id"] for e in newsday._jsonl(derived / "2026-09-28" / "events.jsonl")}
            day2 = newsday._jsonl(derived / "2026-09-29" / "events.jsonl")
        self.assertEqual({e["event_id"] for e in day2}, day1)
        self.assertEqual(asker2.states, [])
        self.assertTrue(all(e["first_seen"].startswith("2026-09-28") for e in day2))
```

- [ ] **Step 2: Run the test and check it fails**

Run: `.venv/Scripts/python.exe -m unittest tests.test_newsday -v`
Expected: `AttributeError: module 'simlab.newsday' has no attribute 'run'`.

- [ ] **Step 3: Write the implementation**

Change the datetime import to `from datetime import date, datetime, timedelta, timezone`, then:

```python
def _jsonl(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def load_known(derived_root: Path, day: date, lookback: int = 7) -> list[dict]:
    """Events from the previous `lookback` days (the newest copy of each) with their headlines, for carry_over."""
    out: dict = {}
    for k in range(1, lookback + 1):
        d = derived_root / f"{day - timedelta(days=k):%Y-%m-%d}"
        if not ((d / "events.jsonl").exists() and (d / "news_private.jsonl").exists()):
            continue
        priv = {r["event_id"]: r for r in _jsonl(d / "news_private.jsonl")}
        for e in _jsonl(d / "events.jsonl"):
            p = priv.get(e["event_id"])
            if p and e["event_id"] not in out:
                out[e["event_id"]] = {**e, "race_id": p["race_id"], "titles": p["titles"], "days_seen": p["days_seen"]}
    return list(out.values())


def run(day: date, snap_root: Path, derived_root: Path, run_id: str, asker, chats: list) -> dict:
    """One day: read, cluster, carry over, label new stories, score attention, select, write cards, write files."""
    arts = read_day(snap_root, day)
    stories = carry_over(make_stories(arts), load_known(derived_root, day))
    views = load_pageviews(snap_root, day)
    events, private, new = [], [], 0
    for s in stories:
        k = s.pop("known")
        new += k is None
        labels = {f: k[f] for f in LABEL_FIELDS} if k else label(s, asker)
        national = s["race_id"] == "US"
        events.append({"schema": SCHEMA, "date": f"{day}", "run_id": run_id, "event_id": s["event_id"],
                       "first_seen": s["first_seen"], "last_seen": s["last_seen"],
                       "scope": "national" if national else "race",
                       "races": PILOT + ["US"] if national else [s["race_id"]], **labels,
                       "attention": attention(s, spike_ratio(views, s["race_id"])),
                       "card": (k or {}).get("card", "")})
        private.append({"schema": SCHEMA, "date": f"{day}", "event_id": s["event_id"], "race_id": s["race_id"],
                        "titles": s["titles"], "outlet_names": s["outlet_names"], "outlets": s["outlets"],
                        "urls": s["urls"], "days_seen": s["days_seen"]})
    select(events)
    by_id, written, failed = {s["event_id"]: s for s in stories}, 0, 0
    for e in events:
        if e["selected"] and not e["card"]:
            e["card"] = write_card(by_id[e["event_id"]], chats)
            written += bool(e["card"])
            if not e["card"]:
                e["selected"], failed = {}, failed + 1
    out = derived_root / f"{day:%Y-%m-%d}"
    out.mkdir(parents=True, exist_ok=True)
    for name, rows in (("events.jsonl", events), ("news_private.jsonl", private)):
        (out / name).write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8")
    return {"articles": len(arts), "stories": len(events), "new": new, "carried": len(events) - new,
            "selected": {r: sum(bool(e["selected"].get(r)) for e in events) for r in PILOT + ["US"]},
            "cards_written": written, "cards_failed": failed}


def main() -> None:
    import argparse
    from .askers import DecisionAsker
    from .core import HOSTS, JEV, LLMS, REASONING, Chat
    data = Path(__file__).resolve().parents[2] / "simlab-data"
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", type=date.fromisoformat, default=datetime.now(timezone.utc).date())
    ap.add_argument("--snap", type=Path, default=data / "snapshots")
    ap.add_argument("--out", type=Path, default=data / "derived")
    ap.add_argument("--run-id", default="")
    a = ap.parse_args()
    chats = [Chat(LLMS["deepseek"], HOSTS["deepseek"]), Chat(LLMS["glm"], HOSTS["glm"], reasoning=REASONING["glm"])]
    print(json.dumps(run(a.date, a.snap, a.out, a.run_id or f"{a.date}-manual",
                         DecisionAsker(JEV, n_orders=2, name="jev"), chats)))


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run the tests and check they pass**

Run: `.venv/Scripts/python.exe -m unittest tests.test_newsday -v`
Expected: 14 tests OK.

- [ ] **Step 5: Commit**

```bash
git add simlab/newsday.py tests/test_newsday.py
git commit -m "newsday: day run, events and private files, command line"
```

### Task 7: First real run on today's snapshots, docs, hand-off

**Files:**
- Modify: `docs/CHANGELOG.md`
- Output (private, not committed here): `simlab-data/derived/2026-09-28/events.jsonl`, `news_private.jsonl`

- [ ] **Step 1: Run on today's snapshots**

Run: `.venv/Scripts/python.exe -m simlab.newsday --date 2026-09-28`
Expected: a JSON summary with stories > 0 and cards_failed = 0 or small. Expected spend under $0.10. Check it with
`.venv/Scripts/python.exe -c "from simlab.core import Ledger; print(Ledger.spent('newsday'))"`.

- [ ] **Step 2: Inspect the output**
  - Read 10 selected events.
  - Every card is neutral, with no outlet names and no poll or survey wording.
  - Gates look sensible: national stories that don't concern a race have a low gate for it.
  - Attention ranks the big stories first.
  - Note anything off in the changelog entry.

- [ ] **Step 3: Changelog and hand-off**
  - Add a dated entry: what `newsday` does, the first run's counts and spend, and anything that needs tuning.
  - Commit with `git add docs/CHANGELOG.md` and `git commit -m "newsday: first run on the 28 Sep snapshots"`.
  - Tell the Statistics and Content & site sessions where `events.jsonl` is.

## Out of scope (later plans)

- Scaling the news queries in `snap.py` to all 35 Senate races and the ~40 House seats (by 12 Oct).
- Media Cloud as a source, if Matteo approves it and adds the key. It needs a `parse_mediacloud` parser registered in
  `PARSERS`.
- Tuning the attention weights against Matteo's spot-check answers (engine-design §9).
