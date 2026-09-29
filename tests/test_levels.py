import unittest
from datetime import date

import numpy as np
import pandas as pd

from simlab import levels
from simlab.polls import Race

COEF = {"r1": 1.0, "r2": 0.0, "inc": 5.0, "E": 1.0, "pr": 0.5, "const": 0.0}
E = {2018: 8.0, 2020: 3.0, 2022: -3.0, 2024: -2.0}


def pres_rows(year, votes):
    return [{"year": year, "state_po": st, "party_simplified": party, "candidatevotes": v, "writein": False}
            for st, (d, r) in votes.items() for party, v in (("DEMOCRAT", d), ("REPUBLICAN", r))]


PRES = pd.DataFrame(pres_rows(2016, {"OH": (46, 54), "NC": (48, 52), "NE": (40, 60)})
                    + pres_rows(2020, {"OH": (46, 54), "NC": (50, 50), "NE": (40, 60)})
                    + pres_rows(2024, {"OH": (45, 55), "NC": (49, 51), "NE": (39, 61)}))


def sen_rows(year, st, cands, stage="gen", special=False):
    return [{"year": year, "state_po": st, "stage": stage, "special": special, "candidate": c, "party_simplified": p,
             "candidatevotes": v, "writein": False} for c, p, v in cands]


SENATE = pd.DataFrame(sen_rows(2012, "OH", [("SHERROD BROWN", "DEMOCRAT", 51), ("JOSH MANDEL", "REPUBLICAN", 45)])
                      + sen_rows(2018, "OH", [("SHERROD BROWN", "DEMOCRAT", 53), ("JIM RENACCI", "REPUBLICAN", 47)])
                      + sen_rows(2024, "OH", [("SHERROD BROWN", "DEMOCRAT", 48), ("BERNIE MORENO", "REPUBLICAN", 52)])
                      + sen_rows(2024, "NE", [("DEB FISCHER", "REPUBLICAN", 53), ("DAN OSBORN", "OTHER", 47)]))
HOUSE = pd.DataFrame([{"year": 2024, "state_po": "AK", "district": 0, "stage": "GEN", "candidate": c, "party": p,
                       "candidatevotes": v, "writein": False}
                      for c, p, v in (("MARY PELTOLA", "DEMOCRAT", 48), ("NICK BEGICH", "REPUBLICAN", 52))])
EXTRA = [{"year": 2020, "state": "NC", "office": "governor", "left": "Roy Cooper", "left_votes": 52,
          "right": "Dan Forest", "right_votes": 48, "inc": 1}]


def race(state, right, left, incumbent="R", status="Incumbent renominated", special=False, left_party="D"):
    return Race(state, special, right, left, left_party, f"2026 race in {state}", incumbent, status)


class IncumbencyTest(unittest.TestCase):
    def test_running_incumbent_counts_fully_with_party_sign(self):
        self.assertEqual(levels.incumbency(race("ME", "Susan Collins", "Troy Jackson")), -1.0)
        self.assertEqual(levels.incumbency(race("GA", "Mike Collins", "Jon Ossoff", incumbent="D")), 1.0)
        self.assertEqual(levels.incumbency(race("AK", "Dan S. Sullivan", "Mary Peltola",
                                                status="Incumbent advanced to general")), -1.0)

    def test_appointed_incumbent_counts_half(self):
        self.assertEqual(levels.incumbency(race("OH", "Jon Husted", "Sherrod Brown",
                                                status="Interim appointee nominated", special=True)), -0.5)

    def test_open_seat_counts_zero(self):
        for status in ("Incumbent retiring", "Incumbent lost renomination in runoff",
                       "Interim appointee ineligible to run"):
            self.assertEqual(levels.incumbency(race("TX", "Ken Paxton", "James Talarico", status=status)), 0.0)


class LeanTest(unittest.TestCase):
    def test_relative_margin_is_state_minus_nation(self):
        rel = levels.relative_margins(PRES)
        self.assertAlmostEqual(rel[(2024, "OH")], -10 - 100 * (133 - 167) / 300)
        self.assertAlmostEqual(rel[(2020, "NC")], 0 - 100 * (136 - 164) / 300)


class RecordTest(unittest.TestCase):
    def setUp(self):
        self.table = levels.statewide_races(SENATE, HOUSE, EXTRA)
        self.rel = levels.relative_margins(PRES)

    def test_statewide_table_has_left_right_margin_and_incumbency(self):
        oh24 = self.table[(self.table.year == 2024) & (self.table.state == "OH")].iloc[0]
        self.assertEqual((oh24.left, oh24.right, oh24.inc), ("SHERROD BROWN", "BERNIE MORENO", 1))
        self.assertAlmostEqual(oh24.margin, -4.0)
        ne = self.table[self.table.state == "NE"].iloc[0]
        self.assertEqual((ne.left, ne.right), ("DAN OSBORN", "DEB FISCHER"))
        self.assertEqual(set(self.table.office), {"senate", "house at-large", "governor"})

    def test_overperformance_is_last_race_residual_on_the_candidates_side(self):
        # 2024 Ohio: expected = 1.0*rel(2020, OH) + 5*inc(+1) + 1.0*E(2024) = rel20 + 5 - 2
        expected = self.rel[(2020, "OH")] + 5 - 2
        got = levels.overperformance("Sherrod Brown", "left", "OH", self.table, self.rel, E, COEF)
        self.assertAlmostEqual(got, -4.0 - expected)

    def test_record_outside_twelve_years_is_ignored(self):
        old = self.table[self.table.year != 2024].copy()
        old = old[~((old.state == "OH") & (old.year == 2018))]
        self.assertIsNone(levels.overperformance("Sherrod Brown", "left", "OH", old, self.rel, E, COEF))

    def test_candidate_effect_sums_both_nominees_times_share(self):
        brown = levels.overperformance("Sherrod Brown", "left", "OH", self.table, self.rel, E, COEF)
        effect, detail = levels.candidate_effect(race("OH", "Jon Husted", "Sherrod Brown", special=True),
                                                 self.table, self.rel, E, COEF)
        self.assertAlmostEqual(effect, 0.5 * brown)
        self.assertIsNone(detail["right"])

    def test_governor_record_from_extra_table(self):
        got = levels.overperformance("Roy Cooper", "left", "NC", self.table, self.rel, E, COEF)
        expected = self.rel[(2016, "NC")] + 5 + 3
        self.assertAlmostEqual(got, 100 * 4 / 100 - expected)


class FilterTest(unittest.TestCase):
    def test_local_level_settles_on_steady_polls(self):
        t = np.array([-60.0, -50, -40, -30, -20, -10])
        grid, mean, var = levels.local_level(t, np.full(6, 5.0), np.full(6, 4.0), q=0.25, end=-5)
        self.assertEqual(grid[-1], -5)
        self.assertAlmostEqual(mean[-1], 5.0, places=6)
        self.assertLess(var[-1], 4.0)

    def test_blend_weights_by_inverse_variance(self):
        m, v, w = levels.blend(4.0, 9.0, 0.0, 6.0)
        self.assertAlmostEqual(w, 0.8)
        self.assertAlmostEqual(m, 3.2)
        self.assertAlmostEqual(v, 7.2)

    def test_blend_without_polls_is_fundamentals(self):
        self.assertEqual(levels.blend(None, None, -3.0, 6.0), (-3.0, 36.0, 0.0))


def gb_entry(i, pollster, pop, dem, rep, day):
    return {"id": f"g{i}{pop}", "poll_type": "generic-ballot", "subject": "2026", "pollster": pollster,
            "population": pop, "sample_size": 1000, "start_date": day, "end_date": day, "created_at": day,
            "answers": [{"choice": "Dem", "pct": dem}, {"choice": "Rep", "pct": rep}], "sponsors": [],
            "partisan": None, "internal": False, "url": ""}


PARAMS = {"poll_extra_sd": {"value": 2.0}, "race_poll_bias_sd": {"value": 3.5, "few_polls": 5.9},
          "national_poll_bias_sd": {"value": 3.0}, "generic_ballot_bias": {"mean": 2.8},
          "drift_daily_sd": {"race": 0.5, "national": 0.3}, "fundamentals": {"coef": COEF, "sd": 7.5}}


def poll_frame(margins, start_day, pollsters, race_id=None):
    rows = []
    for i, m in enumerate(margins):
        d = date.fromordinal(start_day.toordinal() + 5 * i)
        left = 50 + m / 2
        row = {"pollster": pollsters[i % len(pollsters)], "start": d, "end": d, "mid": d, "population": "lv",
               "n": 1000, "partisan": ""}
        if race_id:
            row.update(race_id=race_id, left=left, right=100 - left, margin=m)
        else:
            row.update(dem=left, rep=100 - left, margin=m)
        rows.append(row)
    return pd.DataFrame(rows)


class FrozenInputsTest(unittest.TestCase):
    def test_round_trip(self):
        import json
        rel = {(2024, "OH"): -10.0, (2020, "OH"): -8.0}
        E = {2022: -2.8, 2018: 8.6}
        sw = pd.DataFrame([{"year": 2018, "state": "OH", "office": "senate", "term": 6, "left": "SHERROD BROWN",
                            "right": "JIM RENACCI", "margin": 6.8, "inc": 1}])
        r2, e2, sw2 = levels.unpack(json.loads(json.dumps(levels.pack(rel, E, sw))))
        self.assertEqual((r2, e2), (rel, E))
        pd.testing.assert_frame_equal(sw2, sw, check_dtype=False)


class AssemblyTest(unittest.TestCase):
    def test_lv_gap_from_polls_released_both_ways(self):
        entries = []
        for i, diff in enumerate([1, 2, 0, 1, 3]):
            entries += [gb_entry(i, f"P{i}", "rv", 45, 45, "2026-09-01"), gb_entry(i, f"P{i}", "lv", 45 + diff / 2, 45 - diff / 2, "2026-09-01")]
        self.assertAlmostEqual(levels.lv_gap(entries), 100 * 1 / 90)
        self.assertEqual(levels.lv_gap(entries[:4]), 0.0)

    def test_pollster_priors_by_alias_and_by_name(self):
        priors = {"aliases": {"Rasmussen Reports": "Rasmussen"},
                  "pollsters": {"Rasmussen": {"mean": -5.1}, "Emerson": {"mean": -1.5}}}
        got = levels.map_priors(["Rasmussen Reports", "Emerson College", "Quantus Insights"], priors)
        self.assertEqual(got.to_dict(), {"Rasmussen Reports": -5.1, "Emerson College": -1.5})

    def test_levels_unpolled_race_is_fundamentals_and_polled_race_sits_between(self):
        today = date(2026, 9, 28)
        oh = race("OH", "Jon Husted", "Sherrod Brown", status="Interim appointee nominated", special=True)
        nc = race("NC", "Michael Whatley", "Roy Cooper", status="Incumbent retiring")
        gb = poll_frame([4.0] * 12, date(2026, 7, 30), ["A", "B", "C"])
        senate = poll_frame([2.0] * 8, date(2026, 8, 20), ["A", "B", "D"], race_id="OH-S")
        rel = {(2024, "OH"): -10.0, (2020, "OH"): -8.0, (2024, "NC"): -2.0, (2020, "NC"): -1.0}
        empty = pd.DataFrame(columns=["year", "state", "office", "left", "right", "margin", "inc"])
        out = levels.build([oh, nc], senate, gb, PARAMS, {"pollsters": {}, "aliases": {}}, rel, E, empty, today,
                           lv_gap_value=0.0)
        n = out["national"]["N"]
        self.assertAlmostEqual(n, 4.0, places=3)
        ncr = out["races"]["NC"]
        expected_nc = -2.0 + 5.0 * 0 + 1.0 * (n - 2.8)
        self.assertEqual(ncr["w_polls"], 0.0)
        self.assertAlmostEqual(ncr["margin"], expected_nc, places=6)
        ohr = out["races"]["OH-S"]
        self.assertAlmostEqual(ohr["poll_margin"], 2.0, places=3)
        self.assertTrue(0 < ohr["w_polls"] < 1)
        lo, hi = sorted([2.0, ohr["fundamentals"]])
        self.assertTrue(lo < ohr["margin"] < hi)
        self.assertGreater(ohr["sd"], 3.0)

    def headline(self, moves):
        today = date(2026, 9, 28)
        oh = race("OH", "Jon Husted", "Sherrod Brown", status="Interim appointee nominated", special=True)
        nc = race("NC", "Michael Whatley", "Roy Cooper", status="Incumbent retiring")
        gb = poll_frame([4.0] * 12, date(2026, 7, 30), ["A", "B", "C"])
        senate = poll_frame([2.0] * 8, date(2026, 8, 20), ["A", "B", "D"], race_id="OH-S")
        rel = {(2024, "OH"): -10.0, (2020, "OH"): -8.0, (2024, "NC"): -2.0, (2020, "NC"): -1.0}
        empty = pd.DataFrame(columns=["year", "state", "office", "left", "right", "margin", "inc"])
        args = ([oh, nc], senate, gb, PARAMS, {"pollsters": {}, "aliases": {}}, rel, E, empty, today)
        return levels.build(*args, lv_gap_value=0.0), levels.build(*args, lv_gap_value=0.0, moves=moves)

    def test_story_effects_the_polls_already_show_change_nothing(self):
        twin, head = self.headline({"US": [("2026-07-01", "2026-09-28", 3.0, None, 1e9)],
                                    "OH-S": [("2026-07-01", "2026-09-28", 3.0, None, 1e9)]})
        self.assertAlmostEqual(head["national"]["N"], twin["national"]["N"], places=3)
        self.assertAlmostEqual(head["races"]["OH-S"]["margin"], twin["races"]["OH-S"]["margin"], places=3)

    def test_story_after_the_last_poll_moves_the_level(self):
        twin, head = self.headline({"US": [("2026-09-28", "2026-09-28", 2.0, None, 1e9)],
                                    "OH-S": [("2026-09-28", "2026-09-28", 3.0, None, 1e9)]})
        self.assertAlmostEqual(head["national"]["N"] - twin["national"]["N"], 2.0, places=3)
        self.assertAlmostEqual(head["races"]["OH-S"]["margin"] - twin["races"]["OH-S"]["margin"], 3.0, places=3)
        self.assertAlmostEqual(head["races"]["NC"]["margin"] - twin["races"]["NC"]["margin"], 2.0, places=3)

    def test_race_story_moves_a_race_without_polls_in_full(self):
        twin, head = self.headline({"NC": [("2026-09-28", "2026-09-28", 1.5, None, 1e9)]})
        self.assertEqual(twin["races"]["NC"]["n_polls"], 0)
        self.assertAlmostEqual(head["races"]["NC"]["margin"] - twin["races"]["NC"]["margin"], 1.5, places=3)
        self.assertAlmostEqual(head["races"]["OH-S"]["margin"], twin["races"]["OH-S"]["margin"], places=3)
        self.assertEqual(head["races"]["NC"]["story_effect"], 1.5)

    def test_one_day_story_counts_today_but_not_on_election_day(self):
        twin, head = self.headline({"NC": [("2026-09-28", "2026-09-28", 1.5, None, 1.0)]})
        nc = head["races"]["NC"]
        self.assertEqual(nc["story_effect"], 1.5)
        self.assertLess(nc["story_effect_3nov"], 1e-6)
        self.assertAlmostEqual(nc["margin"], twin["races"]["NC"]["margin"], places=6)

    def test_if_the_election_were_today(self):
        today = date(2026, 9, 28)
        nc = race("NC", "Michael Whatley", "Roy Cooper", status="Incumbent retiring")
        gb = poll_frame([4.0] * 12, date(2026, 7, 30), ["A", "B", "C"])
        empty = pd.DataFrame(columns=["year", "state", "office", "left", "right", "margin", "inc"])
        rel = {(2024, "NC"): -2.0, (2020, "NC"): -1.0}
        args = ([nc], poll_frame([], today, [], race_id="NC"), gb, PARAMS, {"pollsters": {}, "aliases": {}}, rel, E,
                empty, today)
        moves = {"NC": [("2026-09-28", "2026-09-28", 1.5, None, 1.0)]}
        now_twin = levels.build(*args, election=today, lv_gap_value=0.0)
        now_head = levels.build(*args, election=today, lv_gap_value=0.0, moves=moves)
        self.assertEqual(now_head["days_to_election"], 0)
        self.assertAlmostEqual(now_head["races"]["NC"]["margin"] - now_twin["races"]["NC"]["margin"], 1.5, places=6)
        later = levels.build(*args, lv_gap_value=0.0)
        self.assertLess(now_twin["races"]["NC"]["sd"], later["races"]["NC"]["sd"])

    def test_every_story_fades_with_age_even_while_in_the_news(self):
        twin, head = self.headline({"NC": [("2026-09-21", "2026-09-28", 2.0, 5.5, 1.0)]})
        self.assertAlmostEqual(head["races"]["NC"]["story_effect"], 2.0 * 0.5 ** (7 / 5.5), places=9)
        self.assertLess(head["races"]["NC"]["story_effect_3nov"], 1e-6)

    def test_polls_while_a_story_was_in_the_news_are_compared_net_of_it(self):
        twin, head = self.headline({"US": [("2026-07-01", "2026-09-27", 3.0, None, 1.0)],
                                    "OH-S": [("2026-07-01", "2026-09-27", 3.0, None, 1.0)]})
        self.assertAlmostEqual(head["national"]["N"] - twin["national"]["N"], -1.5, places=3)
        self.assertAlmostEqual(head["races"]["NC"]["story_effect_3nov"], 3.0 * 0.5 ** 37, places=9)


if __name__ == "__main__":
    unittest.main()
