import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

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
