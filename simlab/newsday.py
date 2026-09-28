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
