"""The A10 checks (docs/rehearsal.md), run on GitHub Actions so the weekend needs nobody at a laptop.

    python -m simlab.rehearsal check-day --date D --data <data>      after each daily run (daily.yml)
    python -m simlab.rehearsal <drill> --date D --data <data> [--kev URL]   Sunday's drills (drills.yml)

Drills: again, kev-down, no-news, budget, weekly-filter. Each runs on the runner's copy of the data repo, which is
never pushed. Every check prints PASS or FAIL lines and exits non-zero on a FAIL, so the job fails and GitHub emails
Matteo. Logs print statuses and counts, never data.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

from .newsraces import PILOT


def _record(data: Path, day: str) -> dict:
    return json.loads((data / "derived" / day / "run.json").read_text(encoding="utf-8"))


def _step(rec: dict, name: str) -> dict:
    return next((s for s in rec["steps"] if s["name"] == name), {})


def _jsonl(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()] if path.exists() else []


def day_checks(rec: dict) -> list[tuple[str, bool, str]]:
    """The Saturday pass criteria for one day's run.json. A full-scale day (more than the pilot's races selected)
    gets the per-run cap and three hours."""
    news, react = _step(rec, "news").get("summary") or {}, _step(rec, "reactions").get("summary") or {}
    stats, kit = _step(rec, "statistics").get("summary") or {}, _step(rec, "post kit").get("summary") or {}
    selected = news.get("selected") or {}
    full = len(selected) > len(PILOT) + 1
    spend, limit = round(sum((rec.get("spend") or {}).values()), 3), 2.0 if full else 0.5
    minutes, max_minutes = round(rec.get("seconds", 0) / 60, 1), 180 if full else 45
    rows = react.get("rows") or 0
    mode = (rec.get("budget") or {}).get("mode", "full")
    return [
        ("steps", all(s["status"] == "ok" for s in rec["steps"]),
         ", ".join(f"{s['name']} {s['status']}" for s in rec["steps"])),
        ("news", news.get("articles", 0) > 200 and not news.get("label_errors"),
         f"{news.get('articles', 0)} articles, {news.get('stories', 0)} stories, "
         f"{news.get('label_errors', 0)} label errors"),
        ("every pilot race has a story", all(selected.get(r, 0) >= 1 for r in PILOT),
         ", ".join(f"{r} {selected.get(r, 0)}" for r in PILOT)),
        ("reactions", react.get("failed", 1) == 0 and react.get("parse_errors", 0) <= 0.01 * max(rows, 1),
         f"{rows} rows, {react.get('failed')} failed, {react.get('parse_errors')} parse errors"),
        ("statistics", all(stats.get(k, 1) == 0 for k in ("orphaned_events", "deselected_pairs", "ungrouped_races")),
         ", ".join(f"{k} {stats.get(k)}" for k in ("orphaned_events", "deselected_pairs", "ungrouped_races"))),
        ("post kit", kit.get("problems", 1) == 0, f"{kit.get('problems')} problems"),
        ("spend", spend < limit, f"${spend} (under ${limit})"),
        ("time", minutes < max_minutes, f"{minutes} min (under {max_minutes})"),
        ("budget mode", mode == "full", f"{mode} (the key had spent ${(rec.get('budget') or {}).get('key_spent_before')})"),
    ]


def _report(checks: list[tuple[str, bool, str]]) -> int:
    for name, ok, detail in checks:
        print(f"{'PASS' if ok else 'FAIL'} {name}: {detail}", flush=True)
    return 0 if all(ok for _, ok, _ in checks) else 1


def _daily(day: str, data: Path, kev: str = "", env: dict | None = None) -> int:
    return subprocess.run([sys.executable, "-m", "simlab.daily", "--date", day, "--data", str(data), "--kev", kev],
                          env={**os.environ, **(env or {})}).returncode


def again(day: str, data: Path, kev: str) -> list:
    """1. The same day again: the same stories, nothing asked again, no deselected pairs."""
    before = {e["event_id"] for e in _jsonl(data / "derived" / day / "events.jsonl")}
    _daily(day, data, kev)
    rec = _record(data, day)
    after = {e["event_id"] for e in _jsonl(data / "derived" / day / "events.jsonl")}
    rows = (_step(rec, "reactions").get("summary") or {}).get("rows")
    stats = _step(rec, "statistics").get("summary") or {}
    return [("steps", all(s["status"] == "ok" for s in rec["steps"]), ", ".join(s["status"] for s in rec["steps"])),
            ("same stories", before == after, f"{len(before & after)} of {len(before)} kept, {len(after - before)} new"),
            ("nothing asked again", rows == 0, f"{rows} new reaction rows"),
            ("no deselected pairs", stats.get("deselected_pairs") == 0, f"{stats.get('deselected_pairs')}")]


def kev_down(day: str, data: Path, kev: str) -> list:
    """2. Kev down: the reactions step asked again with a wrong address; GLM's rows complete, no Kev rows."""
    path = data / "derived" / day / "reactions.jsonl"
    glm = sum(r["model"] == "glm" for r in _jsonl(path))
    path.unlink(missing_ok=True)
    p = subprocess.run([sys.executable, "-m", "simlab.harness", "--date", day, "--out", str(data / "derived"),
                        "--kev", "https://kev-down.invalid"], capture_output=True, text=True)
    rows = _jsonl(path)
    return [("the step passes", p.returncode == 0, f"exit {p.returncode}"),
            ("logged", "kev: not asked today" in p.stderr, "kev: not asked today"),
            ("GLM complete", sum(r["model"] == "glm" for r in rows) == glm, f"{sum(r['model'] == 'glm' for r in rows)} of {glm} GLM rows"),
            ("no Kev rows", not any(r["model"] == "kev" for r in rows), f"{sum(r['model'] == 'kev' for r in rows)}")]


def no_news(day: str, data: Path, kev: str) -> list:
    """3. No new news: the day replayed with every news file gone (the news job's folder, and any news a snapshot run
    saved before 30 Sep); statistics and the kit run on the polls."""
    shutil.rmtree(data / "news", ignore_errors=True)
    for m in (data / "snapshots").glob("*/*/manifest.json"):
        j = json.loads(m.read_text(encoding="utf-8"))
        m.write_text(json.dumps({**j, "files": [f for f in j["files"] if f.get("source") != "news"]}), encoding="utf-8")
    shutil.rmtree(data / "derived" / day, ignore_errors=True)
    _daily(day, data, kev)
    rec = _record(data, day)
    selected = (_step(rec, "news").get("summary") or {}).get("selected") or {}
    return [("steps", all(s["status"] in ("ok", "skipped") for s in rec["steps"]) and _step(rec, "statistics").get("status") == "ok"
             and _step(rec, "post kit").get("status") == "ok", ", ".join(f"{s['name']} {s['status']}" for s in rec["steps"])),
            ("nothing selected", sum(selected.values()) == 0, f"{sum(selected.values())} selected")]


def budget(day: str, data: Path, kev: str) -> list:
    """4. The per-run cap at $0.01: labels fail softly, the job still ends, and the summary shows the missing news.
    It empties the answer cache so the calls are real, so it runs only on a GitHub runner."""
    if os.environ.get("GITHUB_ACTIONS") != "true":
        return [("on a GitHub runner", False, "this drill empties the answer cache; run it from drills.yml")]
    shutil.rmtree(data / "derived" / day, ignore_errors=True)
    (Path(__file__).resolve().parents[1] / "runs" / "cache.sqlite").unlink(missing_ok=True)
    _daily(day, data, kev, {"SIMLAB_BUDGET_USD": "0.01"})
    rec = _record(data, day)
    news = _step(rec, "news").get("summary") or {}
    return [("the day ends", _step(rec, "statistics").get("status") == "ok",
             ", ".join(f"{s['name']} {s['status']}" for s in rec["steps"])),
            ("missing news shows", news.get("label_errors", 0) > 0, f"{news.get('label_errors')} label errors")]


def weekly_filter(day: str, data: Path, kev: str) -> list:
    """5. The weekly filter forced once (Statistics): it writes filter_weekly.json within 5 minutes."""
    t = time.time()
    p = subprocess.run([sys.executable, "-m", "simlab.statsday", "--date", day, "--data", str(data), "--weekly"])
    seconds = round(time.time() - t)
    out = data / "derived" / day / "filter_weekly.json"
    return [("the step passes", p.returncode == 0, f"exit {p.returncode}"),
            ("written", out.exists(), str(out.name)),
            ("under 5 minutes", seconds < 300, f"{seconds} s")]


DRILLS = {"again": again, "kev-down": kev_down, "no-news": no_news, "budget": budget, "weekly-filter": weekly_filter}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=["check-day", *DRILLS])
    ap.add_argument("--date", required=True)
    ap.add_argument("--data", type=Path, required=True)
    ap.add_argument("--kev", default="")
    a = ap.parse_args()
    if a.what == "check-day":
        return _report(day_checks(_record(a.data, a.date)))
    return _report(DRILLS[a.what](a.date, a.data, a.kev))


if __name__ == "__main__":
    sys.exit(main())
