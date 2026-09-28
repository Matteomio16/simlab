"""Per-group GLM answers on the 46 events2 events, for the Statistics session's size calibration (engine-design §3.2):
runs/events2_groups__glm.jsonl, one row per event x voter group with the measured shift, the group's weight and GLM's
expected support move (-2..+2, toward D). Rebuilt with the exact calls of events2.predict, so every answer comes from
the response cache (no spend).

    python -m simlab.groupcalib
"""
from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from .askers import LLMAsker, expected
from .core import RUNS
from .probes import reaction_state
from .tests import EVENT_Q

HERE = Path(__file__).parent


def export(model: str = "glm") -> Path:
    arch = json.loads((HERE / "archetypes.json").read_text(encoding="utf-8"))
    events = [e for e in json.loads((HERE / "events2.json").read_text(encoding="utf-8")) if e["shift_toward_D"] is not None]
    asker = LLMAsker(model, n_orders=2, name=model)
    items = [(e, p) for e in events for p in arch]
    with ThreadPoolExecutor(16) as ex:
        answers = list(ex.map(lambda it: asker.ask_many(
            reaction_state(it[1]["text_events"], f"({it[0]['date']}) {it[0]['description']}"), {"q": EVENT_Q},
            f"events2:{model}")["q"], items))
    out = RUNS / f"events2_groups__{model}.jsonl"
    out.write_text("\n".join(json.dumps({
        "event_id": e["id"], "date": e["date"], "event_type": e["event_type"], "measured_shift_toward_D": e["shift_toward_D"],
        "z": e.get("z"), "group": p["id"], "party": p["party"], "weight": p["weight"], "wording": "direct",
        "support": round(expected(a), 4), "parse_error": bool(a.get("_parse_error"))})
        for (e, p), a in zip(items, answers)) + "\n", encoding="utf-8")
    return out


if __name__ == "__main__":
    print(export())
