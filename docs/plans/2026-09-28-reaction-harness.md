# Reaction Harness (A5) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** For each day's selected events, ask every voter group how its support and turnout move, and write
`reactions.jsonl` for the Statistics session. The rows are GLM's; Kev's go in as shadow rows when a Kev endpoint is
given.

**Architecture:** A new module, `simlab/harness.py`, with four parts:
- **Personas per scope:** the 28 groups from `simlab/archetypes.json`, with their state set to the race's state, or
  removed for the national scope.
- **Questions per scope and wording:** support and turnout on the test bench's 5-point scales.
- **A skip set:** each event is asked once per race.
- **A parallel asking loop:** it writes expected values from −2 to 2.

The askers are passed in, so the tests use fakes.

**Tech Stack:** Python 3.13, `unittest`, `simlab.askers` (`LLMAsker` for GLM, `DecisionAsker` for Kev, `expected`),
`simlab.probes` (`REACTION_QUESTIONS`, `reaction_state`), `simlab.tests.EVENT_Q`.

**Spec:** `docs/engine-design.md` §3.2 (reactions), §3.4 (Kev shadow), §5 (harness), §7 (the `reactions.jsonl` contract).

## Global Constraints

- Tests use `unittest` with no new dependencies. Run them with `.venv/Scripts/python.exe -m unittest tests.test_harness -v`
  from `simlab/`.
- GLM follows the model recipes:
  - `LLMAsker("glm", n_orders=2)`, so every scale is asked both ways.
  - Turnout is asked in its own group, never alongside support.
  - The persona's state is set to the race's state.
- The news text the groups read is the event's `card`, never raw headlines. It uses the test bench's
  `reaction_state(persona, news)` layout, which was validated as is.
- Each (race, event, group, model) is asked once. Earlier days' rows are skipped (lookback 14 days).
- Row format: `{schema, date, run_id, race_id, event_id, group, model, shadow, wording, support, turnout, parse_error}`.
  `support` is positive toward the Democrat; `turnout` is positive for more likely to vote.
- Wording is `direct` (the default) or `reaction`, the reaction-aware variant from the backlash test. The default flips
  only if that test shows no loss of accuracy.
- Tag model calls `harness:<model>`. Logs print counts only.

---

### Task 1: Personas and questions per scope

**Files:**
- Create: `simlab/harness.py`
- Test: `tests/test_harness.py`

**Interfaces:**
- Produces:
  - `personas(race_id) -> list[dict]`, returning `{group, text}` for the 28 groups
  - `questions(race_id, wording) -> dict`, with keys `support` and `turnout`
  - constants `STATE_NAME` and `GROUPS = [["support"], ["turnout"]]`

- [ ] **Step 1: Write the failing test**

```python
import unittest

from simlab import harness


class Personas(unittest.TestCase):
    def test_race_personas_live_in_the_race_state(self):
        ps = harness.personas("TX")
        self.assertEqual(len(ps), 28)
        self.assertTrue(all(p["text"].startswith("State: Texas\n") for p in ps))
        self.assertEqual(len({p["group"] for p in ps}), 28)

    def test_national_personas_have_no_state(self):
        self.assertTrue(all("State:" not in p["text"] for p in harness.personas("US")))


class Questions(unittest.TestCase):
    def test_scopes_and_wordings(self):
        race, nat = harness.questions("OH-S", "direct"), harness.questions("US", "direct")
        self.assertIn("Senate race", race["support"]["instructions"])
        self.assertIn("parties", nat["support"]["instructions"])
        self.assertEqual(race["support"]["criteria"][4], "Moves strongly toward the Democratic candidate")
        react = harness.questions("OH-S", "reaction")
        self.assertIn("reacts to the news itself", react["support"]["instructions"])
        self.assertIn("reacts to the news itself", react["turnout"]["instructions"])
        self.assertEqual(react["turnout"]["criteria"], race["turnout"]["criteria"])
        self.assertEqual(harness.GROUPS, [["support"], ["turnout"]])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test and check it fails**

Run: `.venv/Scripts/python.exe -m unittest tests.test_harness -v`
Expected: `ImportError: cannot import name 'harness'`.

- [ ] **Step 3: Write the implementation**

```python
"""Voter-group reactions to the day's selected events -> derived/<date>/reactions.jsonl (engine-design §3.2, §5, §7).

    python -m simlab.harness [--date YYYY-MM-DD] [--wording direct|reaction] [--kev URL]

Each selected event is read by the 28 voter groups of every race it was selected for (personas in that race's state;
national scope: no state). GLM answers two 5-point questions, asked both ways and in separate prompts (turnout never
next to support): how the person's support and their likelihood of voting move. Rows hold expected values on -2..+2.
Kev, when an endpoint is given, answers the same questions as shadow rows (never applied). Each (race, event, group,
model) is asked once: earlier days' rows are skipped. Logs print counts only.
"""
from __future__ import annotations

import json
from pathlib import Path

from .probes import REACTION_QUESTIONS
from .tests import EVENT_Q

SCHEMA = 1
HERE = Path(__file__).parent
STATE_NAME = {"OH-S": "Ohio", "NC": "North Carolina", "TX": "Texas"}
GROUPS = [["support"], ["turnout"]]
REACTS = ("Think about how someone like them reacts to the news itself (for example anger, worry or enthusiasm that can "
          "rally them behind their side or put them off a {what}), not only about who the news helps on paper.")
REACTION_TEXT = {
    "race": "How does hearing this news change this person's preference in their state's Senate race, if at all? "
            + REACTS.format(what="candidate"),
    "US": "How does hearing this news change this person's support between the Democratic and Republican parties, if "
          "at all? " + REACTS.format(what="party"),
    "turnout": "How does hearing this news change this person's likelihood of voting in November, if at all? Think "
               "about how someone like them reacts to the news itself (for example whether it fires them up, alarms "
               "them or discourages them), not only about who the news helps on paper.",
}


def personas(race_id: str) -> list[dict]:
    """The 28 voter groups, living in the race's state (national scope: the state line removed)."""
    out = []
    for a in json.loads((HERE / "archetypes.json").read_text(encoding="utf-8")):
        lines = [l for l in a["text"].splitlines() if not l.startswith("State:")]
        if race_id in STATE_NAME:
            lines = [f"State: {STATE_NAME[race_id]}"] + lines
        out.append({"group": a["id"], "text": "\n".join(lines)})
    return out


def questions(race_id: str, wording: str = "direct") -> dict:
    support = dict(EVENT_Q) if race_id == "US" else dict(REACTION_QUESTIONS["support"])
    turnout = dict(REACTION_QUESTIONS["turnout"])
    if wording == "reaction":
        support["instructions"] = REACTION_TEXT["US" if race_id == "US" else "race"]
        turnout["instructions"] = REACTION_TEXT["turnout"]
    return {"support": support, "turnout": turnout}
```

- [ ] **Step 4: Run the test and check it passes**

Run: `.venv/Scripts/python.exe -m unittest tests.test_harness -v`
Expected: 3 tests OK.

- [ ] **Step 5: Commit**

```bash
git add simlab/harness.py tests/test_harness.py
git commit -m "harness: personas and questions per scope and wording"
```

### Task 2: Ask once per race, then react

**Files:**
- Modify: `simlab/harness.py`
- Test: `tests/test_harness.py`

**Interfaces:**
- Consumes: event rows from `events.jsonl` (`event_id`, `card`, `selected`). Askers with
  `ask_many(state, questions, tag[, groups])`. LLM askers have a `.chat` attribute and take `groups`; decision askers
  don't take it.
- Produces:
  - `asked_before(derived_root, day, lookback=14) -> set[tuple[race_id, event_id, group, model]]`
  - `react(events, askers: list[tuple[name, asker, shadow]], wording, skip) -> list[dict]`

- [ ] **Step 1: Write the failing test**

```python
import json
import tempfile
from datetime import date
from pathlib import Path


class FakeLLM:
    chat = None  # marks an LLM asker (takes `groups`)

    def __init__(self):
        self.calls = []

    def ask_many(self, state, questions, tag="", groups=None):
        self.calls.append((state, sorted(questions), groups))
        up = {"0": 0.0, "1": 0.0, "2": 0.5, "3": 0.5, "4": 0.0}
        return {q: up for q in questions}


class FakeDecision:
    def ask_many(self, state, questions, tag=""):
        return {q: {"0": 0.2, "1": 0.2, "2": 0.2, "3": 0.2, "4": 0.2} for q in questions}


EVENTS = [{"event_id": "OH-S-1", "card": "Trump will campaign for Jon Husted in Ohio.", "selected": {"OH-S": True}},
          {"event_id": "US-1", "card": "A national event happened.", "selected": {"OH-S": True, "US": True}},
          {"event_id": "TX-9", "card": "Not selected.", "selected": {}}]


class React(unittest.TestCase):
    def test_rows_per_race_event_group_with_separate_turnout(self):
        glm = FakeLLM()
        rows = harness.react(EVENTS, [("glm", glm, False)], "direct", skip=set())
        self.assertEqual(len(rows), 3 * 28)
        self.assertEqual({(r["race_id"], r["event_id"]) for r in rows},
                         {("OH-S", "OH-S-1"), ("OH-S", "US-1"), ("US", "US-1")})
        self.assertTrue(all(c[2] == [["support"], ["turnout"]] for c in glm.calls))
        self.assertTrue(all("NEWS THIS PERSON SAW TODAY\n" in c[0] for c in glm.calls))
        r = rows[0]
        self.assertAlmostEqual(r["support"], 0.5)
        self.assertEqual((r["model"], r["shadow"], r["wording"], r["parse_error"]), ("glm", False, "direct", False))

    def test_skip_and_shadow(self):
        skip = {("OH-S", "OH-S-1", g["group"], "glm") for g in harness.personas("OH-S")}
        rows = harness.react(EVENTS[:1], [("glm", FakeLLM(), False), ("kev", FakeDecision(), True)], "direct", skip)
        self.assertEqual({(r["model"], r["shadow"]) for r in rows}, {("kev", True)})
        self.assertEqual(len(rows), 28)

    def test_asked_before_reads_earlier_days(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp) / "2026-09-27"
            d.mkdir()
            (d / "reactions.jsonl").write_text(json.dumps({"race_id": "OH-S", "event_id": "OH-S-1", "group": "g",
                                                           "model": "glm"}) + "\n", encoding="utf-8")
            self.assertEqual(harness.asked_before(Path(tmp), date(2026, 9, 28)), {("OH-S", "OH-S-1", "g", "glm")})
```

- [ ] **Step 2: Run the test and check it fails**

Run: `.venv/Scripts/python.exe -m unittest tests.test_harness -v`
Expected: `AttributeError: module 'simlab.harness' has no attribute 'react'`.

- [ ] **Step 3: Write the implementation**

Add `from concurrent.futures import ThreadPoolExecutor`, `from datetime import date, timedelta`,
`from .askers import expected` and `from .probes import reaction_state` to the imports, then:

```python
def asked_before(derived_root: Path, day: date, lookback: int = 14) -> set:
    """(race_id, event_id, group, model) already asked in the previous `lookback` days."""
    seen = set()
    for k in range(1, lookback + 1):
        p = derived_root / f"{day - timedelta(days=k):%Y-%m-%d}" / "reactions.jsonl"
        if p.exists():
            for line in p.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    r = json.loads(line)
                    seen.add((r["race_id"], r["event_id"], r["group"], r["model"]))
    return seen


def react(events: list[dict], askers: list[tuple], wording: str, skip: set) -> list[dict]:
    """Every (race, selected event, voter group, model) not asked before: expected support and turnout moves."""
    tasks = [(r, e, p, name, asker, shadow)
             for e in events for r in sorted(e.get("selected") or {})
             for p in personas(r) for name, asker, shadow in askers
             if (r, e["event_id"], p["group"], name) not in skip]

    def one(t):
        r, e, p, name, asker, shadow = t
        kw = {"groups": GROUPS} if hasattr(asker, "chat") else {}
        a = asker.ask_many(reaction_state(p["text"], e["card"]), questions(r, wording), f"harness:{name}", **kw)
        return {"schema": SCHEMA, "race_id": r, "event_id": e["event_id"], "group": p["group"], "model": name,
                "shadow": shadow, "wording": wording, "support": round(expected(a["support"]), 4),
                "turnout": round(expected(a["turnout"]), 4),
                "parse_error": bool(a["support"].get("_parse_error") or a["turnout"].get("_parse_error"))}
    with ThreadPoolExecutor(16) as ex:
        return list(ex.map(one, tasks))
```

- [ ] **Step 4: Run the tests and check they pass**

Run: `.venv/Scripts/python.exe -m unittest tests.test_harness -v`
Expected: 6 tests OK.

- [ ] **Step 5: Commit**

```bash
git add simlab/harness.py tests/test_harness.py
git commit -m "harness: ask each race x event x group once; separate turnout; Kev shadow rows"
```

### Task 3: The day's run and command line

**Files:**
- Modify: `simlab/harness.py`
- Test: `tests/test_harness.py`

**Interfaces:**
- Produces:
  - `run(day, derived_root, run_id, askers, wording="direct") -> summary`, which appends the day's rows to
    `derived/<day>/reactions.jsonl` (rows get `date` and `run_id`)
  - CLI `python -m simlab.harness`

- [ ] **Step 1: Write the failing test**

```python
class Run(unittest.TestCase):
    def test_run_writes_rows_and_second_run_asks_nothing_new(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            d = root / "2026-09-28"
            d.mkdir()
            (d / "events.jsonl").write_text("\n".join(json.dumps(e) for e in EVENTS) + "\n", encoding="utf-8")
            s1 = harness.run(date(2026, 9, 28), root, "r1", [("glm", FakeLLM(), False)])
            s2 = harness.run(date(2026, 9, 28), root, "r2", [("glm", FakeLLM(), False)])
            rows = [json.loads(l) for l in (d / "reactions.jsonl").read_text(encoding="utf-8").splitlines()]
        self.assertEqual((s1["rows"], s2["rows"]), (84, 0))
        self.assertEqual(len(rows), 84)
        self.assertTrue(all(r["date"] == "2026-09-28" and r["run_id"] == "r1" for r in rows))
```

- [ ] **Step 2: Run the test and check it fails**

Run: `.venv/Scripts/python.exe -m unittest tests.test_harness -v`
Expected: `AttributeError: module 'simlab.harness' has no attribute 'run'`.

- [ ] **Step 3: Write the implementation**

```python
def run(day: date, derived_root: Path, run_id: str, askers: list[tuple], wording: str = "direct") -> dict:
    """React to the day's selected events; rows asked earlier today or in the last 14 days are not asked again."""
    d = derived_root / f"{day:%Y-%m-%d}"
    events = [json.loads(l) for l in (d / "events.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    out = d / "reactions.jsonl"
    skip = asked_before(derived_root, day)
    if out.exists():
        skip |= {(r["race_id"], r["event_id"], r["group"], r["model"])
                 for r in map(json.loads, out.read_text(encoding="utf-8").splitlines()) if r}
    rows = [{**r, "date": f"{day}", "run_id": run_id} for r in react(events, askers, wording, skip)]
    with out.open("a", encoding="utf-8") as f:
        f.writelines(json.dumps(r) + "\n" for r in rows)
    return {"rows": len(rows), "parse_errors": sum(r["parse_error"] for r in rows),
            "by_model": {m: sum(r["model"] == m for r in rows) for m in {r["model"] for r in rows}}}


def main() -> None:
    import argparse
    from datetime import datetime, timezone
    from .askers import DecisionAsker, LLMAsker
    data = Path(__file__).resolve().parents[2] / "simlab-data"
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", type=date.fromisoformat, default=datetime.now(timezone.utc).date())
    ap.add_argument("--out", type=Path, default=data / "derived")
    ap.add_argument("--wording", choices=["direct", "reaction"], default="direct")
    ap.add_argument("--kev", default="", help="Kev endpoint URL (Modal); its rows are shadow rows")
    ap.add_argument("--run-id", default="")
    a = ap.parse_args()
    askers = [("glm", LLMAsker("glm", n_orders=2, name="glm"), False)]
    if a.kev:
        askers.append(("kev", DecisionAsker("kev-latest", endpoint=a.kev.rstrip("/") + "/v1/systemone",
                                            n_orders=2, name="kev"), True))
    print(json.dumps(run(a.date, a.out, a.run_id or f"{a.date}-manual", askers, a.wording)))


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run the tests and check they pass**

Run: `.venv/Scripts/python.exe -m unittest tests.test_harness -v`
Expected: 7 tests OK.

- [ ] **Step 5: Commit**

```bash
git add simlab/harness.py tests/test_harness.py
git commit -m "harness: day run, append-only reactions file, command line"
```

### Task 4: First real run, and the calibration file for Statistics

- [ ] **Step 1:** Run `.venv/Scripts/python.exe -m simlab.harness --date 2026-09-28`. There are about 27 (race, event)
  pairs × 28 groups × 2 questions × 2 orders, roughly 3,000 GLM prompts. Expected spend is under $0.10; check
  `harness:glm` in `runs/spend.jsonl`.
- [ ] **Step 2: Inspect the output.**
  - Parse errors are about 0.
  - Strong partisans' support barely moves; turnout moves more than support.
  - A Trump rally for Husted fires up Republicans' turnout. Do Democrats' turnout answers show backlash?
  - Irrelevant-looking events stay near 0.
- [ ] **Step 3:** Write `runs/events2_groups__glm.jsonl` for the Statistics session's `c_s` fit. For every events2
  event and group, give the per-group support expected value in each wording that was run. These come from the cache,
  so they cost nothing.
- [ ] **Step 4:** Add a changelog entry, commit, and tell Statistics where `reactions.jsonl` and the calibration file
  are.
