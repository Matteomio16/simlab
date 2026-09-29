"""The races the news pipeline follows: each race's description (for Jev and the cards) and its news queries, built
from Statistics' races.json. The Senate races and the nation are in simlab/newsraces.json, committed because the
snapshot job reads the queries and checks out only this repo. Rebuild it when candidates change:

    python -m simlab.newsraces --races ../simlab-data/derived/YYYY-MM-DD/races.json

The simulated House seats change with the daily tiers, so house() builds them from the latest races.json when the news
job and the news step run: each seat with its description, and one group per state that carries the news query
(GDELT answers only a few queries a run; Matteo, 29 Sep).
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

CONFIG = Path(__file__).with_name("newsraces.json")
PILOT = ["OH-S", "NC", "TX", "IA", "ME"]  # the private pilot, 5-11 Oct (Matteo, 29 Sep); every race from 12 Oct
FULL_RUN = "2026-10-12"  # every race from here on; the pilot races before
PARTY = {"D": "Democrat", "I": "independent", "O": "other party", "R": "Republican"}
CONTEXT = {"senate": "(Senate OR election OR campaign)", "house": "(Congress OR House OR election OR campaign)"}
SUFFIXES = {"Jr.", "Jr", "Sr.", "Sr", "II", "III", "IV"}
HOUSE_ID = re.compile(r"[A-Z]{2}-(\d+|AL)")  # TX-28, AK-AL (OH-S is a Senate special)


def is_house(race_id: str) -> bool:
    return bool(HOUSE_ID.fullmatch(race_id))


def names(full: str) -> list[str]:
    """How the news writes a name: middle initials and suffixes dropped ("Dan S. Sullivan" -> "Dan Sullivan", "Nick
    Begich III" -> "Nick Begich"); a longer name also as first and last word ("Shelley Moore Capito" -> "Shelley
    Capito")."""
    words = [w for w in full.split() if not re.fullmatch(r"[A-Z]\.", w) and w.rstrip(",") not in SUFFIXES]
    return [" ".join(words)] + ([f"{words[0]} {words[-1]}"] if len(words) > 2 else [])


def ordinal(n: int) -> str:
    return f"{n}{'th' if 10 <= n % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')}"


def sides(race: dict) -> list[tuple[str, str]]:
    """(candidate, party) pairs: a Senate row has one nominee a side ({left, right}), a House row lists them by party."""
    c = race["candidates"]
    if "left" in c:
        return [(c["left"], race["left_party"]), (c["right"], "R")]
    return [(n, p) for p in ("D", "I", "O", "R") for n in c.get(p) or []]


def query(people: list[str]) -> str:
    return "(" + " OR ".join(f'"{n}"' for c in people for n in names(c)) + ")" if people else ""


def seat(race: dict) -> str:
    return f"{ordinal(race['district'])} congressional district" if race["district"] else "at-large congressional district"


def describe(race: dict) -> dict:
    from .polls import STATE_NAMES
    state, pairs = STATE_NAMES[race["state"]], sides(race)
    who = " vs ".join(f"{n} ({PARTY[p]})" for n, p in pairs)
    if race["office"] == "house":
        text = f"{state}'s {seat(race)}" + (f": {who}" if who else "")
    else:
        text = f"{state} U.S. Senate {'special ' if race['special'] else ''}election: {who}"
    q = query([n for n, _ in pairs])
    return {"state": race["state"], "state_name": state, "office": race["office"], "district": race["district"],
            "text": text, "query": q, "mediacloud": f"{q} AND {CONTEXT[race['office']]}" if q else ""}


def house(races: dict) -> dict:
    """The simulated House seats in races.json ({seat: its description and `group`}) and one group per state
    ("OH-H": the seats, their text, one query with every seat's candidates). A seat without listed candidates is kept
    for national stories but adds nothing to the query; a state whose seats list none gets no group."""
    from .polls import STATE_NAMES
    out, by_state = {}, {}
    rows = [(rid, r) for rid, r in races.items()
            if isinstance(r, dict) and r.get("office") == "house" and r.get("tier") == "simulate"]
    for rid, r in sorted(rows, key=lambda x: (x[1]["state"], x[1]["district"] or 0)):
        out[rid] = {**describe(r), "group": f"{r['state']}-H"}
        by_state.setdefault(r["state"], []).append(rid)
    for st, seats in by_state.items():
        q = query([n for s in seats for n, _ in sides(races[s])])
        if q:
            text = f"{STATE_NAMES[st]}'s U.S. House races: " + "; ".join(
                f"{seat(races[s])}: " + " vs ".join(f"{n} ({PARTY[p]})" for n, p in sides(races[s])) for s in seats)
            out[f"{st}-H"] = {"state": st, "state_name": STATE_NAMES[st], "office": "house group", "district": None,
                              "seats": seats, "text": text, "query": q, "mediacloud": f"{q} AND {CONTEXT['house']}"}
    return out


def build(races: dict) -> dict:
    """{race_id: describe(race)} for every Senate race in races.json, plus the nation as "US"."""
    from .news import RACES
    out = {rid: describe(r) for rid, r in sorted(races.items()) if isinstance(r, dict) and r.get("office") != "house"}
    q, text = RACES["national"]
    out["US"] = {"state": None, "state_name": None, "office": "national", "district": None, "text": text, "query": q,
                 "mediacloud": q}
    return out


def load(path: Path = CONFIG) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--races", type=Path, required=True)
    cfg = build(json.loads(ap.parse_args().races.read_text(encoding="utf-8")))
    CONFIG.write_bytes((json.dumps(cfg, indent=1, ensure_ascii=False) + "\n").encode("utf-8"))
    print(f"{len(cfg)} races -> {CONFIG.name}")
