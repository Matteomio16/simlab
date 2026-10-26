import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

from simlab import harness, moves, rerun


class FakeLLM:
    chat = None

    def __init__(self):
        self.calls = []

    def ask_many(self, state, questions, tag="", groups=None):
        self.calls.append(state)
        return {q: {"0": 0.0, "1": 0.0, "2": 0.0, "3": 1.0, "4": 0.0} for q in questions}


GROUPS = [p["group"] for p in harness.personas("OH-S")]


def write(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")


class Rerun(unittest.TestCase):
    # 26 Oct: 20-23 Oct were answered by a host that reasoned at length; Matteo's yes to ask them again
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        events = [{"event_id": "E1", "card": "Something happened in Ohio.", "selected": {"OH-S": True}},
                  {"event_id": "E0", "card": "An older story.", "selected": {"OH-S": True}}]
        orig = [{"race_id": "OH-S", "event_id": "E1", "group": g, "model": m, "shadow": m == "kev", "wording": "direct",
                 "support": -1.0, "turnout": 1.5, "parse_error": g == GROUPS[1], "date": "2026-10-20",
                 "run_id": "2026-10-20-abc"} for g in GROUPS for m in ("glm", "kev")]
        orig += [{"race_id": "OH-S", "event_id": "E0", "group": g, "model": "glm", "shadow": False, "wording": "direct",
                  "support": 0.0, "turnout": 0.0, "parse_error": False, "date": "2026-10-19"} for g in GROUPS]
        write(self.root / "2026-10-20" / "events.jsonl", events)
        write(self.root / "2026-10-20" / "reactions.jsonl", orig)

    def tearDown(self):
        self.tmp.cleanup()

    def test_the_days_readable_glm_rows_are_asked_again_into_todays_file(self):
        llm = FakeLLM()
        s = rerun.rerun_day(date(2026, 10, 20), self.root, llm, date(2026, 10, 26))
        rows = [json.loads(l) for l in (self.root / "2026-10-26" / "reactions.jsonl").read_text().splitlines()]
        self.assertEqual((s["originals"], s["asked"], len(llm.calls)), (27, 27, 27 * 1))
        self.assertEqual({r["event_id"] for r in rows}, {"E1"})  # not the story first asked on another day
        self.assertNotIn(GROUPS[1], {r["group"] for r in rows})  # its unreadable answer was asked again later anyway
        r = rows[0]
        self.assertEqual({k: r[k] for k in ("model", "shadow", "wording", "rerun", "first_asked", "replaces", "date")},
                         {"model": "glm", "shadow": False, "wording": "direct", "rerun": rerun.TAG,
                          "first_asked": "2026-10-20", "replaces": "2026-10-20-abc", "date": "2026-10-26"})
        self.assertAlmostEqual(r["support"], 1.0)
        before = (self.root / "2026-10-20" / "reactions.jsonl").read_text()
        rerun.rerun_day(date(2026, 10, 20), self.root, llm, date(2026, 10, 26))
        self.assertEqual(len(llm.calls), 27)  # resumes: nothing asked twice
        self.assertEqual((self.root / "2026-10-20" / "reactions.jsonl").read_text(), before)

    def test_moves_takes_the_rerun_row_and_keeps_the_day_first_asked(self):
        rerun.rerun_day(date(2026, 10, 20), self.root, FakeLLM(), date(2026, 10, 26))
        write(self.root / "2026-10-26" / "events.jsonl", [{"event_id": "E1", "card": "x", "selected": {}}])
        reactions, _, dropped, _ = moves._history(date(2026, 10, 26), self.root)
        row, first = reactions[("glm", False, "OH-S", "E1", GROUPS[0])]
        self.assertEqual((row["support"], first, dropped), (1.0, date(2026, 10, 20), set()))
        self.assertEqual(reactions[("kev", True, "OH-S", "E1", GROUPS[0])][0]["support"], -1.0)


if __name__ == "__main__":
    unittest.main()
