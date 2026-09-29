"""The races the news pipeline follows: each race's description (for Jev and the cards) and its news queries, built
from Statistics' races.json. The output, simlab/newsraces.json, is committed because the snapshot job reads the
queries and checks out only this repo. Rebuild it when candidates change or House seats are added:

    python -m simlab.newsraces --races ../simlab-data/derived/YYYY-MM-DD/races.json
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

CONFIG = Path(__file__).with_name("newsraces.json")
PILOT = ["OH-S", "NC", "TX", "IA", "ME"]  # the private pilot, 5-11 Oct (Matteo, 29 Sep); every race from 12 Oct
FULL_RUN = "2026-10-12"  # every race from here on; the pilot races before
PARTY = {"D": "Democrat", "I": "independent", "R": "Republican"}
CONTEXT = {"senate": "(Senate OR election OR campaign)", "house": "(Congress OR House OR election OR campaign)"}


def names(full: str) -> list[str]:
    """How the news writes a name: middle initials dropped ("Dan S. Sullivan" -> "Dan Sullivan"); a longer name also
    as first and last word ("Shelley Moore Capito" -> "Shelley Capito")."""
    words = [w for w in full.split() if not re.fullmatch(r"[A-Z]\.", w)]
    return [" ".join(words)] + ([f"{words[0]} {words[-1]}"] if len(words) > 2 else [])


def ordinal(n: int) -> str:
    return f"{n}{'th' if 10 <= n % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')}"


def describe(race: dict) -> dict:
    from .polls import STATE_NAMES
    state = STATE_NAMES[race["state"]]
    left, right = race["candidates"]["left"], race["candidates"]["right"]
    who = f"{left} ({PARTY[race['left_party']]}) vs {right} (Republican)"
    if race["office"] == "house":
        seat = f"{ordinal(race['district'])} congressional district" if race["district"] else "at-large congressional district"
        text = f"{state}'s {seat}: {who}"
    else:
        text = f"{state} U.S. Senate {'special ' if race['special'] else ''}election: {who}"
    query = "(" + " OR ".join(f'"{n}"' for c in (left, right) for n in names(c)) + ")"
    return {"state": race["state"], "state_name": state, "office": race["office"], "district": race["district"],
            "text": text, "query": query, "mediacloud": f"{query} AND {CONTEXT[race['office']]}"}


def build(races: dict) -> dict:
    """{race_id: describe(race)} for every race in races.json, plus the nation as "US"."""
    from .news import RACES
    out = {rid: describe(r) for rid, r in sorted(races.items()) if isinstance(r, dict)}
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
