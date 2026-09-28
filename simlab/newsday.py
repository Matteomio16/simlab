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
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

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


def parse_gdelt(raw: bytes, race_id: str) -> list[dict]:
    try:
        arts = json.loads(raw).get("articles", [])
    except ValueError:  # GDELT sometimes returns malformed JSON
        return []
    return [{"race_id": race_id, "title": a.get("title") or "", "url": a.get("url") or "",
             "outlet": a.get("domain") or "", "domain": a.get("domain") or "",
             "seen": _iso(datetime.strptime(a["seendate"], "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)),
             "source": "gdelt"} for a in arts if a.get("seendate")]


# Google News is not a source: its feed's terms allow only personal news readers (Matteo, 28 Sep); files saved before
# that decision are ignored.
PARSERS = {"gdelt": parse_gdelt}


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
                if len(a["title"].split()) >= 4 and (key not in best or a["seen"] < best[key]["seen"]):
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
            for e in [e for e in candidates(events, r, top=len(events)) if e["scope"] == scope][:cap]:
                e["selected"][r] = True


CARD_SYSTEM = (
    "You write short, neutral summaries of news events for a research simulation of voters. Use only the headlines "
    "given. In 1 to 3 plain sentences, say what happened and who was involved. Do not name any news outlet or website. "
    "Do not use the words poll, polls, polling, pollster, survey or surveys. No opinions and no predictions. "
    "If the headlines do not describe a specific news event (for example a news round-up, a TV listing, a schedule, "
    'or nothing beyond the race itself), reply {"card": "", "event": false}. '
    'Otherwise reply with JSON only: {"card": "...", "event": true}')
FORBIDDEN = re.compile(r"\b(poll|polls|polling|pollsters?|surveys?)\b", re.I)


def card_ok(card: str, outlet_names: list[str]) -> bool:
    low = card.lower()
    return (0 < len(card) <= 450 and not FORBIDDEN.search(card)
            and not any(n.lower() in low for n in outlet_names if len(n) >= 3))


def write_card(story: dict, chats: list) -> str:
    """1-3 neutral sentences from the first model that follows the rules (two tries each); '' if none does, or at once
    if the model says the headlines aren't a specific event (round-ups, listings)."""
    user = story_text(story, story["race_id"])
    for chat in chats:
        for note in ("", "\nYour previous answer broke a rule. Follow every rule exactly."):
            try:
                text = chat.complete([{"role": "system", "content": CARD_SYSTEM},
                                      {"role": "user", "content": user + note}], tag="newsday:card", max_tokens=200)
                reply = json.loads(text[text.index("{"): text.rindex("}") + 1])
                if reply.get("event") is False:
                    return ""
                card = str(reply.get("card", "")).strip()
            except (ValueError, RuntimeError, AttributeError):
                card = ""
            if card_ok(card, story["outlet_names"]):
                return card
    return ""


POOL = 10
SAME_SYSTEM = (
    "You check whether two news headlines report the same specific event: the same action by the same people at about "
    "the same time, such as two reports of one rally, one ad or one lawsuit. Headlines about the same topic or the same "
    'candidate but about different events are different. Reply with JSON only: {"same": true} or {"same": false}.')


def candidates(events: list[dict], race_id: str, top: int = POOL) -> list[dict]:
    """The race's best candidates for reactions: usable, past the gate (p >= 0.5), not about polls (polls enter
    through the filter), ranked by attention, then salience."""
    return sorted((e for e in events if e.get("usable", True) and e["gate"].get(race_id, 0.0) >= 0.5
                   and e["type"] != "poll"), key=lambda e: (-e["attention"]["a"], -e["salience"], e["event_id"]))[:top]


def same_event(a: tuple[str, str], b: tuple[str, str], chats: list) -> bool:
    """(headline, date) pairs; False unless a model says they are the same specific event."""
    user = f"A ({a[1][:10]}): {a[0]}\nB ({b[1][:10]}): {b[0]}"
    for chat in chats:
        try:
            text = chat.complete([{"role": "system", "content": SAME_SYSTEM}, {"role": "user", "content": user}],
                                 tag="newsday:same", max_tokens=20)
            return json.loads(text[text.index("{"): text.rindex("}") + 1]).get("same") is True
        except (ValueError, RuntimeError, AttributeError):
            continue
    return False


def merge_same_events(events: list[dict], stories: dict, chats: list, top: int = POOL) -> None:
    """Per race, each top candidate is checked against the better-covered candidates already kept; a story that
    reports the same event in other words loses its gate for that race and `same_as` names the kept story."""
    def head(e):
        s = stories[e["event_id"]]
        return strip_outlets(s["titles"][0], s["outlet_names"]), e["first_seen"]
    for r in PILOT + ["US"]:
        kept: list = []
        for e in candidates(events, r, top):
            dup = next((k for k in kept if same_event(head(k), head(e), chats)), None)
            if dup:
                e["gate"][r] = 0.0
                e.setdefault("same_as", {})[r] = dup["event_id"]
            else:
                kept.append(e)


def dedupe_scopes(events: list[dict], stories: dict, sim: float = 0.55) -> None:
    """A national story that repeats a race's own story (similar headlines) doesn't count again for that race: its gate
    there drops to 0 and `covered_by` names the race story."""
    for nat in (e for e in events if e["scope"] == "national"):
        for r in PILOT:
            local = [e for e in events if e["scope"] == "race" and e["races"] == [r]]
            if not local:
                continue
            docs = [" ".join(stories[nat["event_id"]]["titles"])] + [" ".join(stories[e["event_id"]]["titles"])
                                                                   for e in local]
            try:
                X = TfidfVectorizer(stop_words="english", ngram_range=(1, 2)).fit_transform(docs)
            except ValueError:
                continue
            sims = (X[0] @ X[1:].T).toarray()[0]
            j = int(np.argmax(sims))
            if sims[j] >= sim:
                nat["gate"][r] = 0.0
                nat.setdefault("covered_by", {})[r] = local[j]["event_id"]


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
    fresh = [s for s in stories if s["known"] is None or s["known"].get("label_error")]

    def safe_label(s):
        try:
            return label(s, asker)
        except Exception:  # failed after its retries: no labels today, asked again tomorrow
            return {"gate": {}, "type": "other", "helps_face": "unclear", "fires_up": {"D": 0.0, "R": 0.0},
                    "puts_off": {"D": 0.0, "R": 0.0}, "salience": 0.0, "label_error": True}
    with ThreadPoolExecutor(16) as ex:
        fresh_labels = dict(zip([s["event_id"] for s in fresh], ex.map(safe_label, fresh)))
    events, private, new = [], [], 0
    for s in stories:
        k = s.pop("known")
        new += k is None
        labels = fresh_labels.get(s["event_id"]) or {f: k[f] for f in LABEL_FIELDS}
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
    by_id = {s["event_id"]: s for s in stories}
    dedupe_scopes(events, by_id)
    pool = {e["event_id"]: e for r in PILOT + ["US"] for scope in ("race", "national")
            for e in [c for c in candidates(events, r, top=len(events)) if c["scope"] == scope][:POOL]}
    todo = [e for e in pool.values() if not e["card"]]
    with ThreadPoolExecutor(8) as ex:
        for e, card in zip(todo, ex.map(lambda e: write_card(by_id[e["event_id"]], chats), todo)):
            e["card"] = card
    for e in events:
        e["usable"] = bool(e["card"])  # only stories with a card can be selected (the pool is the top 10 per race)
    merge_same_events(events, by_id, chats)
    select(events)
    written, failed = sum(bool(e["card"]) for e in todo), sum(not e["card"] for e in todo)
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
