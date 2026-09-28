"""State outlines for race cards, from the Census Bureau's 2024 cartographic boundary file (1:20m, public domain).

python -m simlab.publish.geo builds states.json from data/geo/cb_2024_us_state_20m.zip: one list of rings per state,
projected (longitude scaled by the cosine of the state's mean latitude), y pointing down, islands under 2% of the
state's largest ring dropped.
"""
from __future__ import annotations

import json
import math
import re
import zipfile
from functools import cache
from pathlib import Path

from ..core import RUNS

SRC = RUNS.parent / "data" / "geo" / "cb_2024_us_state_20m.zip"
OUT = Path(__file__).parent / "states.json"


def _area(ring):
    return abs(sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(ring, ring[1:] + ring[:1]))) / 2


def build() -> dict:
    z = zipfile.ZipFile(SRC)
    kml = z.read(next(n for n in z.namelist() if n.endswith(".kml"))).decode("utf-8")
    states = {}
    for pm in re.findall(r"<Placemark[^>]*>(.*?)</Placemark>", kml, re.S):
        usps = re.search(r'<SimpleData name="STUSPS">(\w+)</SimpleData>', pm).group(1)
        rings = [[tuple(map(float, p.split(",")[:2])) for p in c.split()]
                 for c in re.findall(r"<outerBoundaryIs>.*?<coordinates>(.*?)</coordinates>", pm, re.S)]
        lat = sum(y for r in rings for _, y in r) / sum(len(r) for r in rings)
        k = math.cos(math.radians(lat))
        rings = [[(x * k if x < 0 else (x - 360) * k, -y) for x, y in r] for r in rings]  # Alaska crosses 180°
        big = max(_area(r) for r in rings)
        states[usps] = [[[round(x, 4), round(y, 4)] for x, y in r] for r in rings if _area(r) >= 0.02 * big]
    OUT.write_text(json.dumps(states, separators=(",", ":")), encoding="utf-8")
    return states


@cache
def outline(usps: str) -> list[list[list[float]]]:
    return json.loads(OUT.read_text(encoding="utf-8"))[usps]


if __name__ == "__main__":
    s = build()
    print(f"{len(s)} states -> {OUT} ({OUT.stat().st_size // 1024} KB)")
