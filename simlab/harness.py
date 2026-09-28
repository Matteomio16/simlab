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
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from pathlib import Path

from .askers import expected
from .probes import REACTION_QUESTIONS, reaction_state
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
