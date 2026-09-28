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


class BaseTest(unittest.TestCase):
    def test_tilt_matches_the_target_and_keeps_each_cells_total(self):
        df = pd.DataFrame({"cell": ["a", "a", "b", "b"], "pos": [1, -1, 1, -1], "n": 0.25, "t24": 1.0,
                           "m24": [1.0, -1.0, 1.0, -1.0]})
        theta, n = groups.tilt(df, 0.2)
        self.assertAlmostEqual(theta, np.arctanh(0.2), places=6)
        np.testing.assert_allclose(n, [0.3, 0.2, 0.3, 0.2], atol=1e-9)

    def test_party_turnout_keeps_the_cell_rate(self):
        t = groups.party_turnout(0.5, np.array([0.5, 0.5]), np.array([0.5, -0.5]))
        np.testing.assert_allclose(t, [1 / (1 + np.exp(-0.5)), 1 / (1 + np.exp(0.5))], atol=1e-9)
        t = groups.party_turnout(0.4, np.array([0.2, 0.8]), np.array([1.0, 0.0]))
        self.assertAlmostEqual(float(np.dot([0.2, 0.8], t)), 0.4, places=9)
        self.assertGreater(t[0], t[1])

    def test_shift_on_the_logit_scale(self):
        e = np.array([0.5, 0.5])
        np.testing.assert_allclose(groups.shift(np.array([0.5, -0.5]), e, 0.0), [0.5, -0.5], atol=1e-9)
        d = groups.shift(np.array([0.5, -0.5]), e, 0.2)
        self.assertAlmostEqual(float(np.dot(e, d)), 0.2, places=9)
        self.assertTrue(d[0] > 0.5 and d[1] > -0.5)

    def test_race_groups(self):
        base = {A: {"n": 0.6, "t": 0.5, "d0": 0.4}, groups.GROUPS[1]: {"n": 0.4, "t": 0.25, "d0": -0.6}}
        pimu = {A: {"pi": 0.1, "mu": 0.2}, groups.GROUPS[1]: {"pi": 0.3, "mu": 0.4}}
        out = groups.race_groups(base, pimu, 10.0)
        e = np.array([0.6 * 0.5, 0.4 * 0.25]) / (0.6 * 0.5 + 0.4 * 0.25)
        self.assertAlmostEqual(float(np.dot(e, [out[A]["d"], out[groups.GROUPS[1]]["d"]])), 0.1, places=4)
        self.assertEqual({k: out[A][k] for k in ("n", "t", "pi", "mu")}, {"n": 0.6, "t": 0.5, "pi": 0.1, "mu": 0.2})

    def test_groups_json_for_every_race_and_the_nation(self):
        b = {A: {"n": 1.0, "t": 0.5, "d0": 0.0}}
        base = {"states": {"OH": b, "NC": b}, "US": b}
        pimu = {"states": {"OH": {A: {"pi": 0.1, "mu": 0.2}}, "NC": {A: {"pi": 0.3, "mu": 0.4}}},
                "national": {A: {"pi": 0.5, "mu": 0.6, "n_pi": 9, "n_mu": 9}}}
        levels = {"national": {"N": 4.0}, "races": {"OH-S": {"margin": 2.0}, "NC": {"margin": -6.0}}}
        out = groups.build(levels, base, pimu, "2026-10-02", "run-1")
        self.assertEqual((out["date"], out["run_id"], out["schema"]), ("2026-10-02", "run-1", 1))
        self.assertIn("units", out)
        self.assertAlmostEqual(out["OH-S"][A]["d"], 0.02, places=4)
        self.assertEqual((out["NC"][A]["pi"], out["NC"][A]["d"]), (0.3, -0.06))
        self.assertEqual((out["US"][A]["pi"], out["US"][A]["d"]), (0.5, 0.04))


if __name__ == "__main__":
    unittest.main()
