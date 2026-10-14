import unittest

from simlab.rulecompare import table


def forecast(races: dict, senate: float, house: float) -> dict:
    return {"races": {r: {"p_dem_win": p, "margin": {"p50": m}} for r, (p, m) in races.items()},
            "senate": {"p_r_50plus": senate}, "house": {"p_d_majority": house}}


class TableTest(unittest.TestCase):
    def test_both_rules_side_by_side_largest_gap_first(self):
        new = forecast({"NC": (0.94, 8.0), "LA": (0.06, -9.9)}, 0.419, 0.607)
        old = forecast({"NC": (0.94, 8.1), "LA": (0.09, -8.5)}, 0.411, 0.623)
        lines = table(new, old).splitlines()
        self.assertEqual(lines[2], "| LA | 6.0, -9.90 | 9.0, -8.50 | -1.40 |")
        self.assertEqual(lines[3], "| NC | 94.0, +8.00 | 94.0, +8.10 | -0.10 |")
        self.assertEqual(lines[-2], "Republicans hold 50+: 41.9 (simulation only) against 41.1 (poll filter) in 100.")
        self.assertEqual(lines[-1], "Democratic House majority: 60.7 against 62.3 in 100.")


if __name__ == "__main__":
    unittest.main()
