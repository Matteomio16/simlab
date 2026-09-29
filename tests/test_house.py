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


if __name__ == "__main__":
    unittest.main()
