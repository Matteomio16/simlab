import json
import unittest
from datetime import date, timedelta

import numpy as np

from simlab import levels, lockin, moves

ED = levels.ELECTION
SHARES = {"TX": {"in_person": 0.6, "mail": 0.1, "early": 0.7, "ballots": 1000},
          "US": {"in_person": 0.2, "mail": 0.3, "early": 0.5, "ballots": 1000}}


def ev(first, last, full, kind="national", lasting=True):
    return {"first_seen": first, "last_seen": last, "scope": kind, "age_half_life": 5.5,
            "after_news_half_life": None if lasting else 1, "full": full, "full_s": 0.8 * full, "full_t": 0.2 * full,
            "full_s_base": 0.8 * full, "full_t_base": 0.2 * full, "card": "c", "election_day": 0.0}


MOVES = {"US": {"events": {"n1": ev("2026-10-20", "2026-10-24", 1.0)}, "by_event_effect": {"n1": 0.8}},
         "TX": {"events": {"t1": ev("2026-10-22", "2026-10-22", -2.0, "state", False)},
                "by_event_effect": {"t1": -1.0}},
         "IA": {"events": {"i1": ev("2026-10-21", "2026-10-21", 0.5, "state"), "n1": ev("2026-10-20", "2026-10-24", 1.2)},
                "nation_unasked": [], "by_event_effect": {}}, "shadow": {}}


class WeightsTest(unittest.TestCase):
    def test_curve_rises_and_in_person_is_all_cast_before_election_day(self):
        c = [lockin.cumulative(k) for k in range(42, -1, -1)]
        self.assertEqual(c, sorted(c))
        self.assertEqual((lockin.cumulative(0), lockin.cumulative(1, True), lockin.cumulative(0, True)), (1.0, 1.0, 1.0))

    def test_shares_add_up_and_late_mail_counts_on_election_day(self):
        w = lockin.weights("TX", date(2026, 10, 25), SHARES)
        self.assertAlmostEqual(sum(w.values()), 1.0)
        self.assertAlmostEqual(w[ED], 0.3 + 0.1 * (1 - lockin.cumulative(1)))
        self.assertEqual(lockin.weights("XX", date(2026, 10, 25), SHARES), lockin.weights("US", date(2026, 10, 25), SHARES))

    def test_counted_states_use_the_ballots_back_and_last_weeks_pace(self):
        today = date(2026, 10, 25)
        counted = {(today - timedelta(days=k)).isoformat(): 20 for k in range(1, 11)}
        w = lockin.weights("TX", today, SHARES, counted)
        self.assertAlmostEqual(w[today - timedelta(days=3)], 0.02)
        self.assertAlmostEqual(w[today], 0.02)  # 20 a day of 1000 ballots, the days left at that pace
        self.assertAlmostEqual(sum(w.values()), 1.0)
        self.assertAlmostEqual(w[ED], 1 - 0.2 - 0.02 * 9)


class FactorTest(unittest.TestCase):
    def test_past_days_read_the_archive_and_election_day_voters_keep_l(self):
        today = date(2026, 10, 25)
        w = {date(2026, 10, 23): 0.4, today: 0.0, ED: 0.6}
        held = {date(2026, 10, 23): {"n1": 0.5}}
        g0 = lockin.factors(MOVES, w, held, today, 0.0)
        self.assertAlmostEqual(g0["n1"], 0.4 * 0.5 + 0.6 * float(levels.effect(
            np.array([0.0]), [("2026-10-20", "2026-10-24", 1.0, 5.5, None)], ED, stop=float((today - ED).days))[0]))
        self.assertAlmostEqual(g0["t1"], 0.0, places=3)  # not in the archive, and all but gone by 3 Nov
        g = lockin.factors(MOVES, w, held, today, 0.1)
        self.assertAlmostEqual(g["t1"] - g0["t1"], 0.06, places=4)
        self.assertAlmostEqual(g["n1"], g0["n1"])  # a lasting topic already lasts: no L on top


class PathsTest(unittest.TestCase):
    def test_same_stories_as_moves_paths_scaled_by_the_factor(self):
        ps = lockin.path_sets(MOVES, {"TX": {"n1": 1.0, "t1": 1.0}, "IA": {"n1": 1.0, "i1": 1.0},
                                      "AL": {"n1": 1.0}}, ["TX", "IA", "AL"])
        ref = moves.paths(MOVES)
        for r in ("TX", "IA"):
            self.assertAlmostEqual(sum(x[2] for x in ps["all"][r]), sum(x[2] for x in ref[r]))
        self.assertEqual([x[2] for x in ps["all"]["AL"]], [x[2] for x in ref["US"]])  # the nation's, explicitly
        self.assertEqual((ps["all"]["US"], ps["own_s"]["AL"], ps["us_s"]["AL"][0][2]), ([], [], 0.8))
        self.assertEqual(ps["us_s"]["TX"][0][2], 0.8)  # TX has no national story of its own: it takes the nation's
        self.assertEqual(ps["us_s"]["IA"], [])  # IA was asked about n1 itself
        half = lockin.path_sets(MOVES, {"TX": {"n1": 0.5, "t1": 0.5}}, ["TX"])["all"]["TX"]
        self.assertEqual(sorted(x[2] for x in half), [-1.0, 0.5])
        self.assertTrue(all(x[3] is None and x[4] is None for x in half))  # no further fading

    def test_story_specific_variant_locks_only_the_storys_own_share(self):
        split = {("TX", "t1"): (-0.8, -0.1, 1.0, 1.0)}
        ps = lockin.path_sets(MOVES, {"TX": {"t1": 0.4, "n1": 1.0}}, ["TX"], split)["all"]["TX"]
        t1 = [x for x in ps if x[0] == "2026-10-22"]
        self.assertAlmostEqual(t1[0][2], -0.9 * 0.4)  # its own part, locked in at G
        self.assertAlmostEqual(t1[1][2], -2.0 + 0.9)  # the rest, fading as before
        self.assertEqual((t1[0][3], t1[1][3], t1[1][4]), (None, 5.5, 1))
        v = MOVES["TX"]["events"]["t1"] | {"a": 1.0, "full_s_unit": 0.4}
        groups = {"TX": {"g": {"n": 1.0, "t": 0.5, "d": 0.2, "pi": 0.1, "mu": 0.2}}}
        own = lockin.specific({"TX": {"events": {"t1": v}}}, groups, 0.08, 0.2, 0.2, {"TX": {"k_s": 0.8}})
        os_, ot, ks, kt = own[("TX", "t1")]
        self.assertAlmostEqual(os_, -1.6 - 0.08 * 0.4)
        self.assertAlmostEqual(ot, -0.4)  # one group: turnout changes nobody's share of the vote
        self.assertEqual((ks, kt), (0.8, 1.0))

    def test_the_shares_file_names_its_sources(self):
        f = json.loads(lockin.SHARES.read_text(encoding="utf-8"))
        self.assertIn("EAVS", f["source"])
        self.assertTrue(all(0 <= x["early"] <= 1 for x in f["states"].values()))
        self.assertEqual((f["states"]["MT"]["mail"], f["states"]["MS"]["in_person"]), (0.6, 0.065))


if __name__ == "__main__":
    unittest.main()
