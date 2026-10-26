"""The 3 Nov view without early votes locking in, run every day once lock-in is live, for scoring (Matteo, 26 Oct):
python -m simlab.fadeshadow --date YYYY-MM-DD --data <path>

Writes the simulation-only forecast with every story's effect expected to fade by 3 Nov (the rule before lockin.FROM)
to <data>/scoring/fade/<date>/. Before lockin.FROM it does nothing. It never fails the daily job: a failure is
reported in its one-line JSON summary and the exit code stays 0.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

from . import lockin, statsday
from .start import RULE

ROOT = "scoring/fade"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", type=date.fromisoformat, default=datetime.now(timezone.utc).date())
    ap.add_argument("--data", type=Path, default=Path(__file__).resolve().parents[2] / "simlab-data")
    ap.add_argument("--run-id", default="")
    a = ap.parse_args()
    if not lockin.FROM or a.date < lockin.FROM:
        print(json.dumps({"ok": True, "date": a.date.isoformat(), "skipped": "lock-in not live"}))
        return 0
    try:
        statsday.run(a.date, a.data, None, a.run_id or None, rule=RULE, out_root=ROOT, lasting=lockin.OFF)
        print(json.dumps({"ok": True, "date": a.date.isoformat(), "out": ROOT}))
    except Exception as e:
        print(json.dumps({"ok": False, "date": a.date.isoformat(), "error": f"{type(e).__name__}: {e}"[:200]}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
