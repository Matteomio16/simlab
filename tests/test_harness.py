import json
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest import mock

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
        rows, _ = harness.react(EVENTS, [("glm", glm, False)], "direct", skip=set())
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
        rows, _ = harness.react(EVENTS[:1], [("glm", FakeLLM(), False), ("kev", FakeDecision(), True)], "direct", skip)
        self.assertEqual({(r["model"], r["shadow"]) for r in rows}, {("kev", True)})
        self.assertEqual(len(rows), 28)

    def test_a_model_that_keeps_failing_is_dropped_for_the_day_and_the_others_carry_on(self):
        # a Kev outage must not stall GLM for hours: each failed call has already used up its retries
        class Down:
            calls = 0

            def ask_many(self, state, questions, tag=""):
                Down.calls += 1
                raise RuntimeError("giving up after 8 tries")
        with mock.patch.object(harness, "THREADS", 1):
            rows, failed = harness.react(EVENTS[:1], [("glm", FakeLLM(), False), ("kev", Down(), True)], "direct",
                                         skip=set())
        self.assertEqual(Down.calls, harness.MAX_FAILS)
        self.assertEqual((len(rows), failed), (28, 28))
        self.assertEqual({r["model"] for r in rows}, {"glm"})

    def test_a_failing_call_does_not_sink_the_run(self):
        class Flaky(FakeLLM):
            def ask_many(self, state, questions, tag="", groups=None):
                if "Strong Democrat" in state:
                    raise RuntimeError("giving up on https://openrouter.ai after 8 tries")
                return super().ask_many(state, questions, tag, groups)
        rows, failed = harness.react(EVENTS[:1], [("glm", Flaky(), False)], "direct", skip=set())
        self.assertEqual((len(rows), failed), (24, 4))

    def test_asked_before_reads_earlier_days(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp) / "2026-09-27"
            d.mkdir()
            (d / "reactions.jsonl").write_text(json.dumps({"race_id": "OH-S", "event_id": "OH-S-1", "group": "g",
                                                           "model": "glm"}) + "\n", encoding="utf-8")
            self.assertEqual(harness.asked_before(Path(tmp), date(2026, 9, 28)), {("OH-S", "OH-S-1", "g", "glm")})


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


class Scale(unittest.TestCase):
    def test_every_race_lives_in_its_state(self):
        self.assertTrue(harness.personas("GA")[0]["text"].startswith("State: Georgia\n"))

    def test_a_house_race_is_asked_as_a_house_race(self):
        with mock.patch.dict(harness.CONFIG, {"TX-28": {"office": "house", "state_name": "Texas"}}):
            for wording in ("direct", "reaction"):
                text = harness.questions("TX-28", wording)["support"]["instructions"]
                self.assertIn("their district's U.S. House race", text)
                self.assertNotIn("Senate", text)


if __name__ == "__main__":
    unittest.main()
