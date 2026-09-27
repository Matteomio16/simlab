"""News-labelling set: election headlines from GDELT, grouped into stories, labelled by Jev and GLM.

    python -m simlab.news fetch [--weeks 4]     # GDELT headlines -> data/news/<date>/articles.jsonl
    python -m simlab.news build                 # stories (syndicated copies merged, similar titles clustered)
    python -m simlab.news label jev,glm         # model labels -> runs/news__<model>.jsonl

GDELT's DOC 2.0 API is free with no key (one request per 5 s) and returns headlines, not article text. Outlet lean
comes from AllSides ratings (CC BY-NC 4.0, 2019 community copy) and stays in data/news/, never in the public repo.
"""
from __future__ import annotations

import argparse
import json
import random
import re
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

import numpy as np
import requests
from sklearn.feature_extraction.text import TfidfVectorizer

from .askers import DecisionAsker, LLMAsker
from .ces import DATA
from .core import JEV, RUNS
from .probes import NEWS_QUESTIONS

NEWS = DATA / "news"
GDELT = "https://api.gdeltproject.org/api/v2/doc/doc"
UA = {"User-Agent": "simlab/0.1 (research; +https://scaliastudio.dev)"}
RACES = {
    "Ohio": ('("Sherrod Brown" OR "Jon Husted")',
             "Ohio U.S. Senate special election: Sherrod Brown (Democrat) vs Jon Husted (Republican)"),
    "North Carolina": ('("Roy Cooper" OR "Michael Whatley")',
                       "North Carolina U.S. Senate election: Roy Cooper (Democrat) vs Michael Whatley (Republican)"),
    "Texas": ('("James Talarico" OR "Ken Paxton")',
              "Texas U.S. Senate election: James Talarico (Democrat) vs Ken Paxton (Republican)"),
    "national": ('("midterm elections" OR "midterms" OR "Senate majority" OR "generic ballot")',
                 "The 2026 U.S. midterm elections nationally (Senate and House control)"),
}


def fetch(weeks: int = 4, gap: float = 12.0) -> None:
    """Up to 250 headlines per race per week (GDELT's cap), US English-language sources, newest first. Windows are
    anchored to midnight UTC and each is saved as its own file, so a re-run the same day only fetches what is
    missing. GDELT answers 429 when requests come faster than one per 5 s (and keeps doing so for a while after a
    burst), so requests are spaced by `gap` seconds and a 429 backs off 30 s, 60 s, 120 s."""
    day = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    out = NEWS / day.strftime("%Y-%m-%d")
    out.mkdir(parents=True, exist_ok=True)
    for race, (query, _) in RACES.items():
        for w in range(weeks):
            f = out / f"gdelt_{race.replace(' ', '_')}_w{w + 1}.json"
            if f.exists():
                continue
            end, start = day - timedelta(weeks=w), day - timedelta(weeks=w + 1)
            params = {"query": f"{query} sourcecountry:US sourcelang:english", "mode": "ArtList", "format": "json",
                      "maxrecords": 250, "sort": "DateDesc", "startdatetime": start.strftime("%Y%m%d%H%M%S"),
                      "enddatetime": end.strftime("%Y%m%d%H%M%S")}
            body = None
            for wait in (30, 60, 120, None):
                time.sleep(gap)
                try:
                    r = requests.get(GDELT, params=params, headers=UA, timeout=90)
                    if r.status_code == 200 and r.text.strip().startswith("{"):
                        body = r.json() if r.text.strip() != "{}" else {"articles": []}
                        break
                except (requests.ConnectionError, requests.Timeout):
                    pass
                if wait:
                    time.sleep(wait)
            if body is None:
                print(f"{race:15} week -{w + 1}: FAILED (rate-limited); re-run later to fill it")
                continue
            f.write_text(json.dumps(body), encoding="utf-8")
            print(f"{race:15} week -{w + 1}: {len(body.get('articles', [])):3} articles", flush=True)
    rows, seen = [], set()
    for f in sorted(out.glob("gdelt_*.json")):
        race = f.stem[6:].rsplit("_w", 1)[0].replace("_", " ")
        for a in json.loads(f.read_text(encoding="utf-8")).get("articles", []):
            if (race, a.get("url")) not in seen:
                seen.add((race, a.get("url")))
                rows.append(dict(race=race, **{k: a.get(k) for k in ("url", "title", "seendate", "domain")}))
    (out / "articles.jsonl").write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")
    missing = [f"{r} w{w + 1}" for r in RACES for w in range(weeks)
               if not (out / f"gdelt_{r.replace(' ', '_')}_w{w + 1}.json").exists()]
    print(f"{len(rows)} articles -> {out / 'articles.jsonl'}" + (f"; missing windows: {missing}" if missing else ""))


def fetch_rss(weeks: int = 4, gap: float = 3.0) -> None:
    """Google News RSS search, one query per race per week (~100 headlines each, the feed's cap), same output as
    fetch(). Used because GDELT kept rate-limiting this IP (27 Sep 2026). Titles end in ' - Outlet'; the <source>
    element gives the outlet's site, which the AllSides mapping needs."""
    import xml.etree.ElementTree as ET
    from email.utils import parsedate_to_datetime
    from urllib.parse import urlparse
    day = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    out = NEWS / day.strftime("%Y-%m-%d")
    out.mkdir(parents=True, exist_ok=True)
    rows, seen = [], set()
    for race, (query, _) in RACES.items():
        for w in range(weeks):
            end, start = day - timedelta(weeks=w) + timedelta(days=1), day - timedelta(weeks=w + 1)
            q = f"{query} after:{start:%Y-%m-%d} before:{end:%Y-%m-%d}"
            r = requests.get("https://news.google.com/rss/search", headers=UA, timeout=60,
                             params={"q": q, "hl": "en-US", "gl": "US", "ceid": "US:en"})
            time.sleep(gap)
            items = ET.fromstring(r.content).iter("item") if r.status_code == 200 else []
            n = 0
            for it in items:
                title, src = it.findtext("title") or "", it.find("source")
                key = (race, title)
                if key in seen:
                    continue
                seen.add(key)
                n += 1
                rows.append({"race": race, "url": it.findtext("link"), "title": title,
                             "seendate": parsedate_to_datetime(it.findtext("pubDate")).strftime("%Y%m%dT%H%M%SZ"),
                             "domain": urlparse(src.get("url", "")).netloc.removeprefix("www.") if src is not None
                             else "", "outlet": src.text if src is not None else ""})
            print(f"{race:15} week -{w + 1}: {n:3} headlines (HTTP {r.status_code})", flush=True)
    (out / "articles.jsonl").write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")
    print(f"{len(rows)} headlines -> {out / 'articles.jsonl'}")


CANDIDATES = {"Ohio": ("brown", "husted"), "North Carolina": ("cooper", "whatley"), "Texas": ("talarico", "paxton"),
              "national": ()}


def _clean(title: str) -> str:
    """Drop a trailing ' - Outlet' tag and undo GDELT's spacing around hyphens and punctuation."""
    t = re.sub(r"\s+[|–—-]\s+[^|–—-]{2,40}$", "", title or "")
    t = re.sub(r"(\w) - (\w)", r"\1-\2", t)
    t = re.sub(r"\s+([,.:;!?%])", r"\1", t)
    return re.sub(r"\s+", " ", t).strip()


def latest() -> "Path":
    return sorted(p for p in NEWS.iterdir() if p.is_dir())[-1]


def build(sim: float = 0.55, days: float = 3.0) -> None:
    """Stories = headlines about the same event. Identical titles (syndicated copies) merge first; then titles whose
    TF-IDF cosine is >= `sim` within `days` of each other join the same story (union-find). Salience proxy = number
    of distinct outlets carrying the story."""
    d = latest()
    arts = [json.loads(l) for l in (d / "articles.jsonl").read_text(encoding="utf-8").splitlines()]
    stories = []
    for race in RACES:
        items: dict = {}
        for a in arts:
            if a["race"] != race or not a.get("title"):
                continue
            t = _clean(a["title"])
            it = items.setdefault(t.lower(), {"title": t, "domains": set(), "n": 0, "seen": []})
            it["domains"].add(a["domain"]); it["n"] += 1; it["seen"].append(a["seendate"])
        keys = list(items)
        if not keys:
            continue
        X = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), min_df=1).fit_transform(keys)
        S = (X @ X.T).toarray()
        when = np.array([datetime.strptime(min(items[k]["seen"]), "%Y%m%dT%H%M%SZ").timestamp() for k in keys])
        parent = list(range(len(keys)))

        def find(i):
            while parent[i] != i:
                parent[i] = parent[parent[i]]
                i = parent[i]
            return i
        for i, j in zip(*np.where(np.triu(S, 1) >= sim)):
            if abs(when[i] - when[j]) <= days * 86400:
                parent[find(i)] = find(j)
        groups: dict = {}
        for i, k in enumerate(keys):
            groups.setdefault(find(i), []).append(items[k])
        for n, g in enumerate(sorted(groups.values(), key=lambda g: -len(set().union(*(x["domains"] for x in g))))):
            rep = max(g, key=lambda x: len(x["domains"]))
            doms = set().union(*(x["domains"] for x in g))
            seen = sorted(s for x in g for s in x["seen"])
            stories.append({"story_id": f"{race[:2].upper()}{n:04d}", "race": race, "title": rep["title"],
                            "titles": [x["title"] for x in sorted(g, key=lambda x: -len(x["domains"]))][:12],
                            "domains": sorted(doms), "n_outlets": len(doms), "n_articles": sum(x["n"] for x in g),
                            "first_seen": seen[0], "last_seen": seen[-1],
                            "names_candidate": any(c in rep["title"].lower() for c in CANDIDATES[race])})
    (d / "stories.jsonl").write_text("\n".join(json.dumps(s) for s in stories), encoding="utf-8")
    for race in RACES:
        rs = [s for s in stories if s["race"] == race]
        print(f"{race:15} {len(rs):5} stories, {sum(s['n_outlets'] >= 3 for s in rs):4} with 3+ outlets, "
              f"{sum(s['names_candidate'] for s in rs):4} naming a candidate")


def label_state(s: dict) -> str:
    return f"RACE: {RACES[s['race']][1]}\nHEADLINE: {s['title']}"


def sample(stories: list[dict], per_race: int = 120, seed: int = 0) -> list[dict]:
    """Per race: the most-covered stories plus a random draw of the rest, so labels span big and small news."""
    rng, out = random.Random(seed), []
    for race in RACES:
        rs = sorted((s for s in stories if s["race"] == race), key=lambda s: -s["n_outlets"])
        top, rest = rs[:per_race // 2], rs[per_race // 2:]
        out += top + rng.sample(rest, min(len(rest), per_race - len(top)))
    return out


def label(models: list[str], per_race: int = 120) -> None:
    d = latest()
    stories = sample([json.loads(l) for l in (d / "stories.jsonl").read_text(encoding="utf-8").splitlines()], per_race)
    askers = {"jev": DecisionAsker(JEV, n_orders=2, name="jev"), "glm": LLMAsker("glm", n_orders=2, name="glm")}
    for m in models:
        with ThreadPoolExecutor(16) as ex:
            preds = list(ex.map(lambda s: askers[m].ask_many(label_state(s), NEWS_QUESTIONS, f"news:{m}"), stories))
        rows = [{"story_id": s["story_id"], "race": s["race"], "title": s["title"], "n_outlets": s["n_outlets"],
                 "names_candidate": s["names_candidate"], "pred": p} for s, p in zip(stories, preds)]
        (RUNS / f"news__{m}.jsonl").write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")
        print(f"{m}: labelled {len(rows)} stories")


SOURCES = {"right": "Fox News", "left": "MSNBC"}  # AllSides (2019): Fox News online "right", MSNBC "left"


def _lean(p: dict) -> float:
    return p.get("democrat", 0.0) - p.get("republican", 0.0)


def _top(p: dict) -> str:
    return max((k for k in p if not k.startswith("_")), key=p.get)


def framing(models: list[str], n: int = 80, seed: int = 0) -> dict:
    """Same headline, three attributions (none / a right-leaning outlet / a left-leaning outlet). The event is identical,
    so "which side does this help" should not move with the outlet name; the gap is a source-attribution bias."""
    d = latest()
    stories = [json.loads(l) for l in (d / "stories.jsonl").read_text(encoding="utf-8").splitlines()]
    rng = random.Random(seed)
    picked = [s for race in RACES for s in rng.sample([x for x in stories if x["race"] == race and
                                                       (x["names_candidate"] or race == "national")], n // len(RACES))]
    qs = {k: NEWS_QUESTIONS[k] for k in ("helps", "salience")}
    askers = {"jev": DecisionAsker(JEV, n_orders=2, name="jev"), "glm": LLMAsker("glm", n_orders=2, name="glm")}
    out = {}
    for m in models:
        def one(s):
            return {v: askers[m].ask_many(label_state(s) + (f"\nSOURCE: {src}" if src else ""), qs, f"framing:{m}")
                    for v, src in (("none", None), *SOURCES.items())}
        with ThreadPoolExecutor(16) as ex:
            res = list(ex.map(one, picked))
        gap = np.array([_lean(r["left"]["helps"]) - _lean(r["right"]["helps"]) for r in res])
        flips = np.mean([_top(r["left"]["helps"]) != _top(r["right"]["helps"]) for r in res])
        out[m] = {"stories": len(res), "mean_gap": float(gap.mean()), "mean_abs_gap": float(np.abs(gap).mean()),
                  "top_label_flips": float(flips)}
        print(f"{m}: P(helps D) - P(helps R) is {gap.mean():+.3f} higher when the same headline is attributed to "
              f"{SOURCES['left']} than to {SOURCES['right']} (avg |gap| {np.abs(gap).mean():.3f}); the top label "
              f"changes on {flips:.0%} of {len(res)} stories")
    return out


def report() -> None:
    """Jev vs GLM on the labelled stories: agreement, salience vs real coverage, relevance vs naming a candidate."""
    rows = {m: {r["story_id"]: r for r in map(json.loads, (RUNS / f"news__{m}.jsonl").read_text(encoding="utf-8")
                                              .splitlines())} for m in ("jev", "glm")}
    ids = [i for i in rows["jev"] if i in rows["glm"]]
    J, G = [rows["jev"][i] for i in ids], [rows["glm"][i] for i in ids]
    sal = lambda r: sum(int(k) * v for k, v in r["pred"]["salience"].items() if k.isdigit())
    outlets = np.log1p([r["n_outlets"] for r in J])
    cand = np.array([r["names_candidate"] for r in J])
    lines = [f"stories {len(ids)}",
             f"same top event type: {np.mean([_top(a['pred']['type']) == _top(b['pred']['type']) for a, b in zip(J, G)]):.0%}",
             f"same top 'helps' label: {np.mean([_top(a['pred']['helps']) == _top(b['pred']['helps']) for a, b in zip(J, G)]):.0%}",
             f"correlation of 'helps' lean (P(D) - P(R)) between models: "
             f"{np.corrcoef([_lean(a['pred']['helps']) for a in J], [_lean(b['pred']['helps']) for b in G])[0, 1]:.2f}"]
    for m, R in (("jev", J), ("glm", G)):
        s = np.array([sal(r) for r in R])
        rel = np.array([r["pred"]["relevant"].get("true", 0) for r in R])
        lines.append(f"{m}: salience vs log(outlets) corr {np.corrcoef(s, outlets)[0, 1]:.2f}; P(relevant) "
                     f"{rel[cand].mean():.2f} when a candidate is named vs {rel[~cand].mean():.2f} otherwise; "
                     f"top types {Counter(_top(r['pred']['type']) for r in R).most_common(4)}; "
                     f"'helps' {Counter(_top(r['pred']['helps']) for r in R).most_common(4)}")
    print("\n".join(lines))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["fetch", "rss", "build", "label", "report", "framing"])
    ap.add_argument("models", nargs="?", default="jev,glm")
    ap.add_argument("--weeks", type=int, default=4)
    ap.add_argument("--per-race", type=int, default=120)
    a = ap.parse_args()
    if a.cmd == "fetch":
        fetch(a.weeks)
    elif a.cmd == "rss":
        fetch_rss(a.weeks)
    elif a.cmd == "build":
        build()
    elif a.cmd == "label":
        label(a.models.split(","), a.per_race)
    elif a.cmd == "report":
        report()
    else:
        framing(a.models.split(","))
