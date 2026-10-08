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



def fake_base(day):
    from datetime import timedelta
    from simlab import levels
    gb = pd.DataFrame([{"pollster": f"P{i}", "start": day - timedelta(days=3 * i + 2), "end": day - timedelta(days=3 * i),
                        "population": "lv", "partisan": "", "dem": 48.0, "rep": 44.0, "n": 1000,
                        "margin": 100 * 4 / 92} for i in range(8)])
    s = pd.DataFrame({"state": ["OH"] * 4, "district": [1, 2, 3, 4], "new_map": [False] * 4,
                      "pres24": [-10.0, 0.0, 10.0, 60.0], "votes24": [3e5] * 4, "inc": [0] * 4,
                      "fixed": [None, None, None, "D"], "nominees": [{}] * 4}, index=["OH-1", "OH-2", "OH-3", "OH-4"])
    params, priors = levels.inputs()[:2]
    return {"day": day, "seats": s, "t": {"senate": pd.DataFrame(), "generic_ballot": gb, "entries": []},
            "params": params, "priors": priors, "polls": pd.DataFrame()}


class Build(unittest.TestCase):
    def test_story_paths(self):
        from datetime import date
        day = date(2026, 9, 29)
        base, lv = fake_base(day), {"national": {"E_hat": 2.0, "var": 16.0}}
        twin = house.build(base, lv)["races"]
        head = house.build(base, lv, {"US": [("2026-09-28", "2026-12-01", 2.0, None, None)],
                                      "OH-3": [("2026-09-28", "2026-12-01", -1.0, None, None)]})["races"]
        self.assertAlmostEqual(head["OH-1"]["margin"] - twin["OH-1"]["margin"], 2.0, places=2)
        self.assertEqual((head["OH-1"]["story_effect"], head["OH-1"]["story_effect_3nov"]), (2.0, 2.0))
        self.assertAlmostEqual(head["OH-3"]["margin"] - twin["OH-3"]["margin"], -1.0, places=2)
        self.assertEqual(head["OH-4"]["margin"], 100.0)
        self.assertEqual(head["OH-4"]["story_effect"], 0.0)
        self.assertEqual(twin["OH-1"]["sd"], house.SD_CLOSE if abs(twin["OH-1"]["fundamentals"]) < house.CLOSE else house.SD_SAFE)

    def test_news_across_the_close_line(self):
        """NY-21, 5-8 Oct: the headline's national vote moved its fundamentals across the close line (-15.2 to -14.9)
        but no single news part did, so its margin jumped 2.2 points off the sum of the parts and statsday dropped
        the House. The seat keeps the twin's prior width, and its margin moves linearly with the national vote."""
        from datetime import date, timedelta
        day = date(2026, 9, 29)
        base = fake_base(day)
        base["polls"] = pd.DataFrame([{"race_id": "OH-1", "pollster": "P", "start": day - timedelta(days=9),
                                       "end": day - timedelta(days=7), "population": "lv", "partisan": "",
                                       "left": 47.0, "right": 45.0, "n": 600, "margin": 100 * 2 / 92}])
        lv = lambda e: {"national": {"E_hat": e, "var": 16.0}}
        fund = lambda e: house.build(dict(base), lv(e))["races"]["OH-1"]["fundamentals"]
        e0 = (-house.CLOSE - 0.15 - fund(0.0)) / (fund(1.0) - fund(0.0))
        twin, part, head = (house.build(base, lv(e0 + x))["races"]["OH-1"] for x in (0.0, 0.15, 0.3))
        self.assertLess(twin["fundamentals"], -house.CLOSE)
        self.assertGreater(head["fundamentals"], -house.CLOSE)
        self.assertEqual(head["sd"], twin["sd"])
        self.assertAlmostEqual(head["margin"] - twin["margin"], 2 * (part["margin"] - twin["margin"]), places=9)


if __name__ == "__main__":
    unittest.main()
