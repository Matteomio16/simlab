import json
import tempfile
import unittest
from pathlib import Path

import numpy as np

from simlab import scoring


def race(p, m, cook="Tossup", market=0.5, poll=1.0, left="D"):
    return {"p_dem_win": p, "margin": {"p50": m}, "left_party": left,
            "stats_only": {"p_dem_win": 0.5, "margin": {"p50": 0.0}},
            "benchmarks": {"poll_avg": poll, "market": market, "cook": cook}}


class ScoringTest(unittest.TestCase):
    def test_cook_ratings_as_the_left_candidates_chance(self):
        self.assertEqual((scoring.cook_chance("Lean D", "D"), scoring.cook_chance("Likely R", "I"),
                          scoring.cook_chance("Tossup", "D"), scoring.cook_chance(None, "D")), (0.73, 1 - 0.88, 0.5, None))

    def test_crps_of_a_point_forecast_is_its_absolute_error(self):
        self.assertAlmostEqual(scoring.crps([2.0] * 10, 5.0), 3.0)
        self.assertLess(scoring.crps(list(np.linspace(-1, 1, 101)), 0.0), scoring.crps([1.0] * 101, 0.0))

    def test_measures_and_toss_ups_call_nothing(self):
        rows = [{"p": 0.8, "won": True, "margin": 3.0, "actual": 1.0}, {"p": 0.5, "won": False, "margin": 0.0,
                                                                         "actual": -2.0}]
        m = scoring.measures(rows)
        self.assertEqual((m["n"], m["wrong"], m["margin_mae"]), (2, 0, 2.0))
        self.assertAlmostEqual(m["brier"], (0.04 + 0.25) / 2)
        self.assertEqual(scoring.measures([{"p": None, "won": False, "margin": 1.0, "actual": -1.0}]),
                         {"n": 1, "wrong": 1, "margin_mae": 2.0})

    def test_every_version_on_a_scoring_date(self):
        with tempfile.TemporaryDirectory() as d:
            data = Path(d)
            fc = {"races": {"TX": race(0.7, 2.0, "Lean D", 0.6, 1.5), "NE": race(0.2, -4.0, "Likely R", 0.1, -2.0, "I")},
                  "senate": {"p_r_50plus": 0.4, "benchmarks": {"market": 0.3}}, "house": None}
            for root in ("derived", "scoring/fade"):
                (data / root / "2026-11-03").mkdir(parents=True)
                (data / root / "2026-11-03" / "forecast.json").write_text(json.dumps(fc))
            res = {"senate": {"TX": {"margin": 1.0, "left_won": True}, "NE": {"margin": 2.0, "left_won": True}},
                   "control": {"senate_r_50plus": False}}
            s = scoring.score(data, res, ["2026-11-03"])["2026-11-03"]
        self.assertEqual(sorted(s), ["Cook", "fade", "markets", "poll average", "polls alone", "published"])
        self.assertEqual((s["published"]["senate"]["wrong"], s["poll average"]["senate"]["wrong"]), (1, 1))
        self.assertAlmostEqual(s["published"]["senate_control"], 0.16)
        self.assertAlmostEqual(s["markets"]["senate_control"], 0.09)
        self.assertIn("| 2026-11-03 | published |", scoring.table({"2026-11-03": s}))


if __name__ == "__main__":
    unittest.main()
