"""Re-asks a day's GLM reaction rows on today's hosts (Matteo's yes, 26 Oct).

    python -m simlab.rerun --days 2026-10-20 2026-10-21 2026-10-22 2026-10-23 [--data ../simlab-data]

20-23 Oct were answered by a host that reasoned at length (turnout answers about 0.18 too high; CHANGELOG 20-23 Oct).
Every readable GLM row a day's run wrote is asked again with that day's card, personas, question and wording; Kev's
shadow rows are left alone and the earlier days' files are never rewritten. The new rows go into today's
reactions.jsonl in the usual shape plus `rerun` (why), `first_asked` (the original's day) and `replaces` (its run_id);
moves._history lets a row with `rerun` replace the earliest answer and keep the day first asked (Statistics, 26 Oct).
Rows already re-asked are not asked again, so an interrupted run resumes.
"""
from __future__ import annotations

import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

from . import harness

TAG = "glm-hosts-2026-10-26"


def _jsonl(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()] if path.exists() else []


def rerun_day(day: date, derived: Path, asker, asked: date, tag: str = TAG) -> dict:
    d, out = derived / f"{day}", derived / f"{asked}" / "reactions.jsonl"
    events = _jsonl(d / "events.jsonl")
    orig = {(r["race_id"], r["event_id"], r["group"]): r for r in _jsonl(d / "reactions.jsonl")
            if r["model"] == "glm" and r.get("date") == f"{day}" and not r.get("parse_error")}
    done = {(r["race_id"], r["event_id"], r["group"]) for r in _jsonl(out)
            if r.get("rerun") == tag and r["model"] == "glm" and not r.get("parse_error")}
    possible = {(r, e["event_id"], p["group"]) for e in events for r in sorted(e.get("selected") or {})
                for p in harness.personas(r)}
    by_wording: dict = {}
    for k, r in orig.items():
        if k not in done:
            by_wording.setdefault(r.get("wording", "direct"), set()).add(k)
    rows, failed = [], 0
    for wording, keys in by_wording.items():
        new, f = harness.react(events, [("glm", asker, False)], wording, {(*k, "glm") for k in possible - keys})
        rows += new
        failed += f
    rows = [r | {"date": f"{asked}", "run_id": f"rerun-{asked}", "rerun": tag, "first_asked": f"{day}",
                 "replaces": orig[(r["race_id"], r["event_id"], r["group"])].get("run_id")} for r in rows]
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("a", encoding="utf-8") as f:
        f.writelines(json.dumps(r) + "\n" for r in rows)
    return {"day": f"{day}", "originals": len(orig), "asked": len(rows), "failed": failed,
            "parse_errors": sum(r["parse_error"] for r in rows), "already_done": len(done & set(orig)),
            "not_in_events": len(set(orig) - possible)}


def main() -> None:
    import argparse
    from .askers import LLMAsker
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", nargs="+", type=date.fromisoformat, required=True)
    ap.add_argument("--data", type=Path, default=Path(__file__).resolve().parents[2] / "simlab-data")
    a = ap.parse_args()
    asked = datetime.now(timezone.utc).date()
    asker = LLMAsker("glm", n_orders=2, name="glm")
    for day in a.days:
        print(json.dumps(rerun_day(day, a.data / "derived", asker, asked)), flush=True)


if __name__ == "__main__":
    sys.exit(main())
