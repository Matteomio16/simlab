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
