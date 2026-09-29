import unittest

import numpy as np
import pandas as pd

from simlab import house

SECTION = """
{{Infobox election
| election_name = 2026 Nebraska's 2nd congressional district election
| image1 = 
| nominee1 = Brinker Harding 
| party1 = Republican Party (United States)
| image2 = 
| nominee2 = '''[[Denise Powell]]'''<br/>''(Uncontested)''
| party2 = Democratic Party (United States)
| before_election = [[Don Bacon]]
}}
====Predictions====
| {{USRaceRating|Tossup}}
| {{USRaceRating|Lean|D|flip}}
| {{USRaceRating|Likely|R}}
"""


def seat(noms, before="", incumbent="Don Bacon", party="R", state="NE"):
    inp = {"races": {"NE-2": {"state": state, "district": 2, "new_map": False, "pres24": 4.0, "votes24": 400000,
                              "incumbent": incumbent, "incumbent_party": party}}}
    wiki = {"NE-2": {"nominees": noms, "before": before, "ratings": []}}
    return house.seats(inp, wiki).loc["NE-2"]


class Parse(unittest.TestCase):
    def test_district(self):
        d = house.district(SECTION)
        self.assertEqual(d["nominees"], {"R": ["Brinker Harding"], "D": ["Denise Powell"]})
        self.assertEqual(d["before"], "Don Bacon")
        self.assertEqual(d["ratings"], [0, 1, -2])

    def test_name_key(self):
        self.assertEqual(house.name_key("[[Nick Begich III]]"), house.name_key("Nick Begich"))


class Seats(unittest.TestCase):
    def test_incumbent_and_fixed(self):
        self.assertEqual((seat({"R": ["Don Bacon"], "D": ["Denise Powell"]}).inc, seat({"D": ["X Y"], "R": ["A B"]}).inc), (-1, 0))
        self.assertEqual(seat({"D": ["X Y"]}).fixed, "D")
        self.assertEqual(seat({"D": ["X Y"], "O": ["P Q"]}).fixed, "D")
        self.assertEqual(seat({"R": ["A B"]}).fixed, "R")
        self.assertIsNone(seat({"R": ["A B"], "O": ["P Q"]}).fixed)   # Alaska: an independent against a Republican
        unknown = seat({})
        self.assertEqual((unknown.inc, unknown.fixed, unknown.checked), (-1, None, False))


class Anchor(unittest.TestCase):
    def test_adds_up_to_national(self):
        s = pd.DataFrame({"pres24": [-20.0, 0.0, 15.0, 40.0], "inc": [-1, 0, 1, 1], "new_map": [False, True, False, False],
                          "votes24": [3e5, 3.5e5, 3e5, 2.5e5], "fixed": [None, None, None, "D"]})
        m, c = house.anchor(s, 3.0)
        w = s.votes24 * np.where(s.fixed.notna(), house.UNCONTESTED_TURNOUT, 1.0)
        self.assertAlmostEqual(float(np.dot(w, m) / w.sum()), 3.0, places=6)
        self.assertEqual(m.iloc[3], 100.0)



ACS = {**{f"B29002_{i:03d}E": v for i, v in enumerate([1000, 50, 50, 300, 200, 100, 200, 100], 1)},
       **{f"B05003H_{i:03d}E": 0 for i in range(1, 24)}, **{f"B15002_{i:03d}E": 0 for i in range(1, 36)},
       **{f"C15002H_{i:03d}E": 0 for i in range(1, 12)}}
ACS.update({"B05003H_009E": 300, "B05003H_011E": 10, "B05003H_020E": 300, "B05003H_022E": 10,
            "B15002_001E": 900, "B15002_015E": 150, "B15002_032E": 150,
            "C15002H_001E": 560, "C15002H_006E": 100, "C15002H_011E": 110})


class Groups(unittest.TestCase):
    def test_cells_add_up(self):
        c = house.cells(ACS)
        self.assertAlmostEqual(sum(c.values()), 1.0)
        self.assertAlmostEqual(c["white / Four-year college degree or more"] + c["white / No four-year college degree"], 0.62)
        self.assertAlmostEqual(c["white / Four-year college degree or more"] + c["non-white / Four-year college degree or more"], 0.3)

    def test_district_groups_reproduce_the_seat(self):
        from simlab.groups import BASE, PIMU
        import json
        base, pimu = (json.loads(f.read_text(encoding="utf-8")) for f in (BASE, PIMU))
        g = house.district_groups({"state": "OH", "pres24": -8.0, "acs": ACS}, -3.0, base, pimu, {})
        self.assertEqual(len(g), 28)
        n = sum(v["n"] for v in g.values())
        m = sum(v["n"] * v["t"] * v["d"] for v in g.values()) / sum(v["n"] * v["t"] for v in g.values())
        self.assertAlmostEqual(n, 1.0, places=3)
        self.assertAlmostEqual(100 * m, -3.0, places=2)



class Tiers(unittest.TestCase):
    def test_kept_seats_stay_and_the_rest_fill_up(self):
        idx = [f"XX-{i}" for i in range(1, 61)]
        s = pd.DataFrame({"fixed": [None] * 60, "ratings": [[]] * 60}, index=idx)
        p = pd.Series(np.linspace(0.5, 0.99, 60), index=idx)
        tier, why, _ = house.tiers(s, p, kept={"XX-60"})
        sim = set(tier[tier == "simulate"].index)
        self.assertEqual(len(sim), 40)
        self.assertIn("XX-60", sim)
        self.assertIn("kept from the last days", why["XX-60"])
        self.assertNotIn("XX-40", sim)


if __name__ == "__main__":
    unittest.main()
