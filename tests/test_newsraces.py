import unittest

from simlab import newsraces
from simlab.news import RACES

OH = {"state": "OH", "office": "senate", "district": None, "special": True, "rcv": False,
      "candidates": {"left": "Sherrod Brown", "right": "Jon Husted"}, "left_party": "D", "tier": "simulate"}


class Describe(unittest.TestCase):
    def test_a_pilot_race_keeps_the_text_and_query_in_use(self):
        c = newsraces.describe(OH)
        self.assertEqual((c["query"], c["text"]), RACES["Ohio"])

    def test_names_drop_middle_initials_and_add_first_and_last(self):
        self.assertEqual(newsraces.names("Dan S. Sullivan"), ["Dan Sullivan"])
        self.assertEqual(newsraces.names("Shelley Moore Capito"), ["Shelley Moore Capito", "Shelley Capito"])

    def test_an_independent_and_a_house_seat(self):
        ne = {**OH, "state": "NE", "special": False, "left_party": "I",
              "candidates": {"left": "Dan Osborn", "right": "Pete Ricketts"}}
        self.assertEqual(newsraces.describe(ne)["text"],
                         "Nebraska U.S. Senate election: Dan Osborn (independent) vs Pete Ricketts (Republican)")
        tx28 = {**OH, "state": "TX", "office": "house", "district": 28, "special": False,
                "candidates": {"left": "Ann Lee", "right": "Bo Ray"}}
        c = newsraces.describe(tx28)
        self.assertEqual(c["text"], "Texas's 28th congressional district: Ann Lee (Democrat) vs Bo Ray (Republican)")
        self.assertTrue(c["mediacloud"].endswith("AND (Congress OR House OR election OR campaign)"))

    def test_build_skips_metadata_and_adds_the_nation(self):
        cfg = newsraces.build({"date": "2026-09-29", "schema": 1, "OH-S": OH})
        self.assertEqual(sorted(cfg), ["OH-S", "US"])
        self.assertEqual(cfg["US"]["text"], RACES["national"][1])

    def test_the_committed_file_covers_the_pilot(self):
        cfg = newsraces.load()
        for rid, name in (("OH-S", "Ohio"), ("NC", "North Carolina"), ("TX", "Texas")):
            self.assertEqual(cfg[rid]["text"], RACES[name][1])


if __name__ == "__main__":
    unittest.main()
