"""The old rule, run every day for scoring (Matteo, 13 Oct): python -m simlab.pollfilter --date YYYY-MM-DD --data <path>

The poll-filter forecast (daily poll correction, Monday re-fit) on the same inputs as the published one, written to
<data>/scoring/poll-filter/<date>/, so both versions are scored without re-runs. It never fails the daily job: a
failure is reported in its one-line JSON summary and the exit code stays 0.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

from . import statsday
from .start import OLD_RULE

ROOT = "scoring/poll-filter"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", type=date.fromisoformat, default=datetime.now(timezone.utc).date())
    ap.add_argument("--data", type=Path, default=Path(__file__).resolve().parents[2] / "simlab-data")
    ap.add_argument("--run-id", default="")
    a = ap.parse_args()
    try:
        s = statsday.run(a.date, a.data, None, a.run_id or None, rule=OLD_RULE, out_root=ROOT)
        print(json.dumps({"ok": True, "date": a.date.isoformat(), "rule": OLD_RULE, "out": ROOT,
                          "weekly_update": s.get("weekly_update")}))
    except Exception as e:
        print(json.dumps({"ok": False, "date": a.date.isoformat(), "rule": OLD_RULE,
                          "error": f"{type(e).__name__}: {e}"[:200]}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
