"""The daily job: the day's steps in order, then derived/<date>/run.json (engine-design §6).

    python -m simlab.daily [--date YYYY-MM-DD] [--data ../simlab-data] [--wording direct|reaction] [--kev URL]
                           [--scope pilot|all]   (default: the pilot races until 11 Oct, every race from 12 Oct)

Each step is a command-line module whose last stdout line is a one-line JSON summary. A step whose module isn't built
yet is skipped and logged; a failed step stops the steps after it (their inputs would be missing) and the job exits
non-zero, so the missed-run alert fires. Logs print step names, statuses and summaries, never data.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from .core import HOSTS, JEV, LLMS, RUNS

SCHEMA = 1
FULL_RUN = "2026-10-12"  # every race from here on; the pilot races (OH, NC, TX) before
# (name, module, arguments, steps whose outputs it reads)
STEPS = [
    ("news", "simlab.newsday",
     lambda d, data, o: ["--date", d, "--snap", str(data / "snapshots"), "--out", str(data / "derived"),
                         "--scope", o.get("scope", "pilot")], []),
    ("reactions", "simlab.harness",
     lambda d, data, o: ["--date", d, "--out", str(data / "derived"), "--wording", o["wording"]]
     + (["--kev", o["kev"]] if o["kev"] else []), ["news"]),
    ("statistics", "simlab.statsday", lambda d, data, o: ["--date", d, "--data", str(data)], ["reactions"]),
    ("post kit", "simlab.publish.kit", lambda d, data, o: ["--date", d, "--data", str(data)], ["statistics"]),
]


def scope_for(day: str, override: str | None) -> str:
    """The pilot races until the full run starts, every race from then; --scope overrides."""
    return override or ("all" if day >= FULL_RUN else "pilot")


def _exists(module: str) -> bool:
    try:
        return importlib.util.find_spec(module) is not None
    except ModuleNotFoundError:
        return False


def _subprocess(module: str, args: list[str]) -> tuple[int, str, str]:
    p = subprocess.run([sys.executable, "-m", module, *args], capture_output=True, text=True, timeout=4 * 3600)
    return p.returncode, p.stdout, p.stderr


def _summary(stdout: str):
    lines = [l for l in stdout.splitlines() if l.strip()]
    try:
        return json.loads(lines[-1]) if lines else None
    except ValueError:
        return None


def run_steps(day: str, data: Path, opts: dict, runner=_subprocess, exists=_exists) -> list[dict]:
    out, stopped = [], False
    for name, module, args, needs in STEPS:
        step = {"name": name, "module": module}
        if stopped:
            out.append({**step, "status": "not run"})
            continue
        if not exists(module):
            out.append({**step, "status": "skipped", "reason": "not built yet"})
            continue
        missing = [n for n in needs if not any(s["name"] == n and s["status"] == "ok" for s in out)]
        if missing:
            out.append({**step, "status": "skipped", "reason": "needs " + ", ".join(missing)})
            continue
        t0 = time.time()
        code, stdout, stderr = runner(module, args(day, data, opts))
        step |= {"seconds": round(time.time() - t0, 1), "summary": _summary(stdout)}
        if code == 0:
            out.append({**step, "status": "ok"})
        else:
            out.append({**step, "status": "failed", "error": "\n".join(stderr.strip().splitlines()[-5:])})
            stopped = True
    return out


def _git_sha() -> str:
    return subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True,
                          cwd=Path(__file__).parent).stdout.strip()


def _spend(started: float, finished: float) -> dict:
    path = RUNS / "spend.jsonl"
    out: dict = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                e = json.loads(line)
            except ValueError:  # a line another process is still writing
                continue
            if started <= e["ts"] <= finished:
                k = e["tag"].split(":")[0]
                out[k] = out.get(k, 0.0) + e["usd"]
    return {k: round(v, 4) for k, v in out.items()}


def record(day: str, data: Path, run_id: str, steps: list[dict], started: float, finished: float) -> dict:
    """run.json: code version, models, the snapshot runs the day read (manifest hashes), steps, spend."""
    snaps = sorted((data / "snapshots" / day).glob("*/manifest.json"))
    rec = {"schema": SCHEMA, "date": day, "run_id": run_id, "git_sha": _git_sha(),
           "started": datetime.fromtimestamp(started, timezone.utc).isoformat(timespec="seconds"),
           "seconds": round(finished - started, 1),
           "models": {"glm": [LLMS["glm"], HOSTS["glm"]], "jev": JEV, "deepseek": [LLMS["deepseek"], HOSTS["deepseek"]]},
           "snapshots": [{"run": m.parent.name, "manifest_sha256": hashlib.sha256(m.read_bytes()).hexdigest()}
                         for m in snaps],
           "steps": steps, "spend": _spend(started, finished)}
    out = data / "derived" / day
    out.mkdir(parents=True, exist_ok=True)
    (out / "run.json").write_text(json.dumps(rec, indent=1), encoding="utf-8")
    return rec


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=datetime.now(timezone.utc).date().isoformat())
    ap.add_argument("--data", type=Path, default=Path(__file__).resolve().parents[2] / "simlab-data")
    ap.add_argument("--wording", choices=["direct", "reaction"], default="direct")
    ap.add_argument("--kev", default="")
    ap.add_argument("--run-id", default="")
    ap.add_argument("--scope", choices=["pilot", "all"], default=None)
    a = ap.parse_args()
    started = time.time()
    steps = run_steps(a.date, a.data, {"wording": a.wording, "kev": a.kev, "scope": scope_for(a.date, a.scope)})
    for s in steps:
        print(f"{s['name']}: {s['status']}" + (f" in {s['seconds']}s" if "seconds" in s else ""), flush=True)
    rec = record(a.date, a.data, a.run_id or f"{a.date}-{_git_sha()[:7]}", steps, started, time.time())
    print(json.dumps({"steps": {s["name"]: s["status"] for s in steps}, "spend": rec["spend"]}))
    return 1 if any(s["status"] == "failed" for s in steps) else 0


if __name__ == "__main__":
    sys.exit(main())
