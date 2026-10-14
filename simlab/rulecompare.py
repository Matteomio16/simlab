"""The day's forecast under both rules, side by side, for the Publishing approval thread (Matteo, 14 Oct: shown for
the first three days of simulation only; he decides which number is posted).

    python -m simlab.rulecompare --date YYYY-MM-DD [--data <path to simlab-data>]

Reads derived/<date>/forecast.json (simulation only, published) and scoring/poll-filter/<date>/forecast.json (the old
poll filter) and prints a markdown table: each Senate race's 3 Nov chance and expected margin under both rules,
largest margin gap first, then the Senate and House control numbers.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

from .pollfilter import ROOT


def table(new: dict, old: dict) -> str:
    """Markdown: race, chance and margin under each rule, and the margin difference (new minus old)."""
    m = lambda f, r: f["races"][r]["margin"]["p50"]
    p = lambda f, r: f["races"][r]["p_dem_win"] * 100
    races = sorted(new["races"], key=lambda r: (-abs(m(new, r) - m(old, r)), r))
    lines = ["| Race | Simulation only: chance, margin | Poll filter: chance, margin | Difference |", "|---|---|---|---|"]
    lines += [f"| {r} | {p(new, r):.1f}, {m(new, r):+.2f} | {p(old, r):.1f}, {m(old, r):+.2f} | "
              f"{m(new, r) - m(old, r):+.2f} |" for r in races]
    s = lambda f: f["senate"]["p_r_50plus"] * 100
    h = lambda f: f["house"]["p_d_majority"] * 100 if f.get("house") else float("nan")
    lines += ["", f"Republicans hold 50+: {s(new):.1f} (simulation only) against {s(old):.1f} (poll filter) in 100.",
              f"Democratic House majority: {h(new):.1f} against {h(old):.1f} in 100."]
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", type=date.fromisoformat, default=datetime.now(timezone.utc).date())
    ap.add_argument("--data", type=Path, default=Path(__file__).resolve().parents[2] / "simlab-data")
    a = ap.parse_args()
    read = lambda f: json.loads(f.read_text(encoding="utf-8"))
    d = a.date.isoformat()
    print(table(read(a.data / "derived" / d / "forecast.json"), read(a.data / ROOT / d / "forecast.json")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
