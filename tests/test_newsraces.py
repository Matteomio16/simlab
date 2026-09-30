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

    def test_the_pilot_is_one_list_of_five_races_in_the_race_file(self):
        # Matteo, 29 Sep: the private pilot (5-11 Oct) is Ohio, North Carolina, Texas, Iowa and Maine
        self.assertEqual(newsraces.PILOT, ["OH-S", "NC", "TX", "IA", "ME"])
        self.assertTrue(set(newsraces.PILOT) <= set(newsraces.load()))

    def test_the_committed_file_covers_the_pilot(self):
        cfg = newsraces.load()
        for rid, name in (("OH-S", "Ohio"), ("NC", "North Carolina"), ("TX", "Texas")):
            self.assertEqual(cfg[rid]["text"], RACES[name][1])


def seat(state, district, tier="simulate", **candidates):
    return {"state": state, "office": "house", "district": district, "special": False, "rcv": False, "tier": tier,
            "candidates": candidates, "left_party": "O" if "O" in candidates else "D"}


HOUSE = {"date": "2026-10-12", "OH-S": OH,
         "OH-9": seat("OH", 9, D=["Marcy Kaptur"], R=["Derek Merrin"]),
         "OH-1": seat("OH", 1, D=["Greg Landsman"], R=["Eric Conroy"]),
         "OH-2": seat("OH", 2, "watch", D=["Ann Lee"], R=["Bo Ray"]),
         "AK-AL": seat("AK", 0, O=["Bill Hill"], R=["Nick Begich III"]),
         "CA-22": seat("CA", 22)}


class House(unittest.TestCase):
    # Matteo, 29 Sep: one news query per state for the simulated House seats
    def test_simulated_seats_and_one_group_per_state(self):
        h = newsraces.house(HOUSE)
        self.assertEqual(sorted(h), ["AK-AL", "AK-H", "CA-22", "OH-1", "OH-9", "OH-H"])
        self.assertEqual(h["OH-H"]["seats"], ["OH-1", "OH-9"])
        self.assertEqual(h["OH-H"]["query"], '("Greg Landsman" OR "Eric Conroy" OR "Marcy Kaptur" OR "Derek Merrin")')
        self.assertEqual((h["OH-9"]["group"], h["OH-9"]["text"]),
                         ("OH-H", "Ohio's 9th congressional district: Marcy Kaptur (Democrat) vs Derek Merrin (Republican)"))
        self.assertEqual(h["AK-AL"]["text"],
                         "Alaska's at-large congressional district: Bill Hill (other party) vs Nick Begich III (Republican)")
        self.assertEqual(h["AK-H"]["query"], '("Bill Hill" OR "Nick Begich")')

    def test_a_seat_without_listed_candidates_gets_no_query(self):
        h = newsraces.house(HOUSE)
        self.assertEqual((h["CA-22"]["query"], h["CA-22"]["text"]), ("", "California's 22nd congressional district"))
        self.assertNotIn("CA-H", h)

    def test_the_committed_file_stays_senate_only(self):
        self.assertEqual(sorted(newsraces.build(HOUSE)), ["OH-S", "US"])

    def test_the_state_names_match_the_statistics_ones(self):
        from simlab.polls import STATE_NAMES
        self.assertEqual({c: STATE_NAMES[c] for c in newsraces.STATE_NAMES if c in STATE_NAMES}, newsraces.STATE_NAMES)

    def test_house_ids_and_name_suffixes(self):
        self.assertEqual([newsraces.is_house(r) for r in ("TX-28", "AK-AL", "OH-S", "NC", "US", "OH-H")],
                         [True, True, False, False, False, False])
        self.assertEqual(newsraces.names("Nick Begich III"), ["Nick Begich"])
        self.assertEqual(newsraces.names("Robert F. Kennedy Jr."), ["Robert Kennedy"])


if __name__ == "__main__":
    unittest.main()
