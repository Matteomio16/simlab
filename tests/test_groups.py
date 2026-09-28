import unittest

import numpy as np
import pandas as pd

from simlab import groups

A = groups.GROUPS[0]


class GroupTest(unittest.TestCase):
    def test_28_groups_from_the_archetypes(self):
        self.assertEqual(len(groups.GROUPS), 28)

    def test_group_of_cumulative_labels(self):
        self.assertEqual(groups.group_of("Strong Democrat", "White", "No", "4-Year"),
                         "Strong Democrat / white / Four-year college degree or more")
        self.assertEqual(groups.group_of("Not Very Strong Republican", "Black", "No", "High School Graduate"),
                         "Not very strong Republican / non-white / No four-year college degree")
        self.assertEqual(groups.group_of("Not Sure", "White", "Yes", "Post-Grad"),
                         "Independent / non-white / Four-year college degree or more")
        self.assertIsNone(groups.group_of(np.nan, "White", "No", "4-Year"))


class FlagTest(unittest.TestCase):
    def test_persuadable(self):
        intent = pd.Series(["[Democrat / Candidate 1]", "Not Sure", "[Republican / Candidate 2]", "No One",
                            "[Democrat / Candidate 1]", np.nan])
        voted = pd.Series(["[Democrat / Candidate 1]", "[Republican / Candidate 2]", "[Democrat / Candidate 1]",
                           "[Democrat / Candidate 1]", "I Did Not Vote In This Race", "[Democrat / Candidate 1]"])
        out = groups.persuadable(intent, voted)
        self.assertEqual(out[:4].tolist(), [0.0, 1.0, 1.0, 1.0])
        self.assertTrue(out[4:].isna().all())

    def test_mobilisable(self):
        intent = pd.Series(["Yes, definitely", "Probably", "Undecided", "Yes, definitely", "No", "No",
                            "I already voted (early or absentee)", np.nan])
        voted = pd.Series([True, True, False, False, False, True, True, True])
        self.assertEqual(groups.mobilisable(intent, voted).tolist(), [0.0, 1.0, 1.0, 1.0, 0.0, 1.0, 0.0, 1.0])


class FitTest(unittest.TestCase):
    def test_shrink(self):
        self.assertAlmostEqual(groups.shrink(0.4, 10, 0.1, 50), 0.15)

    def test_state_then_division_then_nation(self):
        df = pd.DataFrame({"st": ["OH"] * 10 + ["NC"] * 90, "group": A, "persuadable": [1.0] * 10 + [0.0] * 90,
                           "mobilisable": 0.5, "weight": 1.0, "weight_post": 1.0})
        out = groups.fit(df, k=50)
        self.assertAlmostEqual(out["national"][A]["pi"], 0.1)
        self.assertAlmostEqual(out["states"]["OH"][A]["pi"], (10 + 50 * 0.25) / 60, places=4)
        self.assertAlmostEqual(out["states"]["NC"][A]["pi"], 50 * (5 / 140) / 140, places=4)
        self.assertAlmostEqual(out["states"]["TX"][A]["pi"], 0.1, places=4)
        self.assertAlmostEqual(out["states"]["TX"][A]["mu"], 0.5, places=4)
        self.assertEqual(len(out["states"]), 51)


if __name__ == "__main__":
    unittest.main()
