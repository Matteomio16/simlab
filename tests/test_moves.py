import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

from simlab import moves
from simlab.groups import GROUPS

A, B = GROUPS[0], GROUPS[-1]


class FormulaTest(unittest.TestCase):
    def test_group_change(self):
        dd, dt = moves.group_change(r_s=1.0, r_t=-1.0, pi=0.1, mu=0.2, a=0.5, c_s=0.5, c_t=0.5)
        self.assertAlmostEqual(dd, 2 * 0.1 * 0.25 * 0.5)
        self.assertAlmostEqual(dt, 0.2 * -0.25 * 0.5)

    def test_group_change_is_capped_at_the_movable_share(self):
        dd, dt = moves.group_change(r_s=2.0, r_t=2.0, pi=0.1, mu=0.2, a=1.0, c_s=10, c_t=10)
        self.assertAlmostEqual(dd, 0.2)
        self.assertAlmostEqual(dt, 0.2)

    def test_race_move_switching_plus_turnout_mix(self):
        g = {A: {"n": 0.5, "t": 0.5, "d": 0.8}, B: {"n": 0.5, "t": 0.5, "d": -0.8}}
        self.assertAlmostEqual(moves.race_move(g, {A: 0.1, B: 0.1}, {A: 0.0, B: 0.0}), 0.1)
        self.assertAlmostEqual(moves.race_move(g, {A: 0.0, B: 0.0}, {A: 0.05, B: 0.0}), 0.5 * (0.05 / 0.5) * 0.8)

    def test_decay(self):
        self.assertEqual(moves.decay(0, 10), 1.0)
        self.assertAlmostEqual(moves.decay(10, 10), 0.5)
        self.assertEqual(moves.decay(-1, 10), 0.0)


class FitTest(unittest.TestCase):
    def test_recovers_a_known_size(self):
        pimu = {A: {"pi": 0.1}, B: {"pi": 0.3}}
        rows, rng = [], np.random.default_rng(0)
        for e in range(30):
            r = rng.uniform(-2, 2, 2)
            shift = 100 * (0.5 * 2 * 0.1 * 0.4 * r[0] / 2 + 0.5 * 2 * 0.3 * 0.4 * r[1] / 2)
            rows += [{"event_id": str(e), "group": g, "weight": 0.5, "support": float(x), "measured_shift_toward_D": shift,
                      "z": 2.0} for g, x in zip((A, B), r)]
        self.assertAlmostEqual(moves.fit_cs(rows, pimu)["c_s"], 0.4, places=2)


def write_day(root: Path, day: str, events: list[dict], reactions: list[dict]) -> None:
    d = root / day
    d.mkdir(parents=True, exist_ok=True)
    (d / "events.jsonl").write_text("".join(json.dumps(e) + "\n" for e in events), encoding="utf-8")
    (d / "reactions.jsonl").write_text("".join(json.dumps(r) + "\n" for r in reactions), encoding="utf-8")


def event(eid, first, a, races=("OH-S",)):
    return {"event_id": eid, "first_seen": first, "type": "policy", "scope": "race", "races": list(races),
            "attention": {"a": a}, "card": f"card {eid}"}


def reaction(eid, group, s, t, race="OH-S", model="glm", shadow=False):
    return {"race_id": race, "event_id": eid, "group": group, "model": model, "shadow": shadow, "support": s,
            "turnout": t, "parse_error": False}


class BuildTest(unittest.TestCase):
    def setUp(self):
        self.groups = {"OH-S": {A: {"n": 0.5, "t": 0.5, "d": 0.8, "pi": 0.1, "mu": 0.2},
                                B: {"n": 0.5, "t": 0.5, "d": -0.8, "pi": 0.1, "mu": 0.2}},
                       "US": {A: {"n": 0.5, "t": 0.5, "d": 0.8, "pi": 0.1, "mu": 0.2},
                              B: {"n": 0.5, "t": 0.5, "d": -0.8, "pi": 0.1, "mu": 0.2}}}
        self.params = {"c_s": 0.5, "c_t": 0.0, "dials": {}, "half_life_days": {"default": 10}}

    def build(self, root, day):
        return moves.build(date.fromisoformat(day), root, self.groups, self.params, "run-1")

    def test_an_event_counts_once_from_first_seen_and_fades(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            write_day(root, "2026-10-01", [event("e1", "2026-10-01T08:00:00+00:00", 1.0)],
                      [reaction("e1", A, 2.0, 0.0), reaction("e1", B, 2.0, 0.0)])
            write_day(root, "2026-10-11", [event("e1", "2026-10-01T08:00:00+00:00", 1.0)], [])
            first, later = self.build(root, "2026-10-01"), self.build(root, "2026-10-11")
        full = 100 * 2 * 0.1 * 0.5
        self.assertAlmostEqual(first["OH-S"]["by_event_effect"]["e1"], full, places=6)
        self.assertAlmostEqual(first["OH-S"]["delta_margin"], full, places=6)
        self.assertAlmostEqual(later["OH-S"]["by_event_effect"]["e1"], full / 2, places=6)
        self.assertAlmostEqual(later["OH-S"]["by_event"]["e1"], full * (0.5 - 0.5 ** 0.9), places=4)
        self.assertEqual(later["OH-S"]["events"]["e1"]["first_seen"], "2026-10-01")

    def test_rows_for_pairs_the_days_news_no_longer_selects_are_dropped(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            e1 = event("e1", "2026-10-01T08:00:00+00:00", 1.0) | {"selected": {"OH-S": True}}
            write_day(root, "2026-10-01", [e1], [reaction("e1", A, 1.0, 0.0), reaction("e1", A, 1.0, 0.0, race="NC")])
            m = self.build(root, "2026-10-01")
        self.assertEqual(m["deselected_pairs"], ["NC e1"])
        self.assertIn("e1", m["OH-S"]["events"])

    def test_reactions_to_stories_missing_from_the_news_file_are_flagged(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            write_day(root, "2026-10-01", [event("e1", "2026-10-01T08:00:00+00:00", 1.0)],
                      [reaction("e1", A, 1.0, 0.0), reaction("gone", A, 1.0, 0.0), reaction("gone", B, 1.0, 0.0)])
            m = self.build(root, "2026-10-01")
        self.assertEqual(m["orphaned_events"], ["gone"])
        self.assertEqual(list(m["OH-S"]["events"]), ["e1"])

    def test_contract_fields_and_shadow_rows_kept_apart(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            write_day(root, "2026-10-01", [event("e1", "2026-10-01T08:00:00+00:00", 0.5)],
                      [reaction("e1", A, 1.0, 1.0), reaction("e1", B, -1.0, 0.0),
                       reaction("e1", A, -2.0, 0.0, model="kev", shadow=True)])
            m = self.build(root, "2026-10-01")
        self.assertEqual((m["date"], m["run_id"], m["schema"]), ("2026-10-01", "run-1", 1))
        oh = m["OH-S"]
        self.assertEqual(set(oh) >= {"delta_margin", "delta_margin_base", "delta_turnout", "by_group", "by_event",
                                     "by_event_effect"}, True)
        self.assertEqual(oh["delta_margin"], oh["delta_margin_base"])
        self.assertAlmostEqual(oh["by_group"][A]["dd"], 100 * 2 * 0.1 * 0.25 * 0.5, places=6)
        self.assertLess(m["shadow"]["OH-S"]["delta_margin"], 0)
        self.assertEqual(m["US"]["delta_margin"], 0.0)


class CoverageTest(unittest.TestCase):
    GROUPS = {"OH-S": {A: {"n": 0.5, "t": 0.5, "d": 0.8, "pi": 0.1, "mu": 0.2},
                       B: {"n": 0.5, "t": 0.5, "d": -0.8, "pi": 0.1, "mu": 0.2}}}

    def run_days(self, etype):
        params = {"c_s": 0.5, "c_t": 0.0, "dials": {}, "half_life_days": {"default": 1}, "age_half_life_days": 5.5,
                  "lasting_types": ["economy"]}
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            e = event("e1", "2026-10-01T08:00:00+00:00", 1.0) | {"type": etype}
            write_day(root, "2026-10-01", [e], [reaction("e1", A, 2.0, 0.0), reaction("e1", B, 2.0, 0.0)])
            write_day(root, "2026-10-05", [e | {"last_seen": "2026-10-05T09:00:00+00:00"}], [])
            return {day: moves.build(date.fromisoformat(day), root, self.GROUPS, params, "run-1")["OH-S"]
                    for day in ("2026-10-05", "2026-10-06", "2026-10-08")}

    def test_a_one_off_story_fades_with_age_and_drops_once_out_of_the_news(self):
        m, full = self.run_days("endorsement"), 10.0
        self.assertAlmostEqual(m["2026-10-05"]["by_event_effect"]["e1"], full * 0.5 ** (4 / 5.5), places=4)
        self.assertAlmostEqual(m["2026-10-06"]["by_event_effect"]["e1"], full * 0.5 ** (5 / 5.5) / 2, places=4)
        self.assertAlmostEqual(m["2026-10-08"]["by_event_effect"]["e1"], full * 0.5 ** (7 / 5.5) / 8, places=4)
        self.assertEqual(m["2026-10-05"]["events"]["e1"]["last_seen"], "2026-10-05")

    def test_lasting_topics_keep_fading_at_the_age_rate_after_the_news_moves_on(self):
        oneoff, lasting = self.run_days("endorsement"), self.run_days("economy")
        self.assertAlmostEqual(lasting["2026-10-05"]["by_event_effect"]["e1"], 10 * 0.5 ** (4 / 5.5), places=4)
        self.assertAlmostEqual(lasting["2026-10-08"]["by_event_effect"]["e1"], 10 * 0.5 ** (7 / 5.5), places=4)
        self.assertAlmostEqual(lasting["2026-10-05"]["events"]["e1"]["election_day"], 10 * 0.5 ** (33 / 5.5), places=4)
        self.assertIsNone(lasting["2026-10-05"]["events"]["e1"]["after_news_half_life"])
        self.assertLess(oneoff["2026-10-05"]["events"]["e1"]["election_day"], 1e-6)


class PartsTest(unittest.TestCase):
    def test_switching_and_turnout_parts_add_up(self):
        groups = {"OH-S": {A: {"n": 0.5, "t": 0.5, "d": 0.8, "pi": 0.1, "mu": 0.2},
                           B: {"n": 0.5, "t": 0.5, "d": -0.8, "pi": 0.1, "mu": 0.2}}}
        params = {"c_s": 0.5, "c_t": 0.5, "dials": {}, "half_life_days": {"default": 10}}
        with tempfile.TemporaryDirectory() as d:
            write_day(Path(d), "2026-10-01", [event("e1", "2026-10-01T08:00:00+00:00", 1.0)],
                      [reaction("e1", A, 1.0, 1.0), reaction("e1", B, 0.0, 0.0)])
            m = moves.build(date(2026, 10, 1), Path(d), groups, params, "run-1")
        e = m["OH-S"]["events"]["e1"]
        self.assertAlmostEqual(e["full_s"], 100 * 0.5 * 2 * 0.1 * 0.25, places=4)
        self.assertAlmostEqual(e["full_t"], 100 * 0.5 * (0.2 * 0.25 / 0.5) * 0.8, places=4)
        self.assertAlmostEqual(e["full"], e["full_s"] + e["full_t"], places=4)
        self.assertEqual(moves.paths(m, "s"), {"OH-S": [("2026-10-01", "2026-10-01", e["full_s"], None, 10)]})
        self.assertEqual(moves.paths(m, "t"), {"OH-S": [("2026-10-01", "2026-10-01", e["full_t"], None, 10)]})


class LastingTest(unittest.TestCase):
    def series(self, step):
        days = pd.date_range("2020-01-01", "2021-12-31")
        out = pd.Series(0.0, index=days)
        events = [pd.Timestamp(d) for d in ("2020-03-01", "2020-07-01", "2020-11-01", "2021-03-01", "2021-07-01")]
        for d in events:
            age = (days - d).days.values
            out += np.where(age >= 0, step(np.maximum(age, 0)), 0.0)
        return [(out, d, 1) for d in events]

    def test_a_permanent_shift_lasts(self):
        share, n = moves.lasting_share(self.series(lambda age: 2.0 + 0 * age))
        self.assertEqual(n, 5)
        self.assertAlmostEqual(share["+33..42"], 1.0, places=2)

    def test_a_fading_shift_does_not(self):
        share, _ = moves.lasting_share(self.series(lambda age: 2.0 * 0.5 ** (age / 10)))
        self.assertLess(share["+33..42"], 0.3)


class DialTest(unittest.TestCase):
    def test_parts_at_dial_one_kept_beside_the_dialled_ones(self):
        groups = {"OH-S": {A: {"n": 0.5, "t": 0.5, "d": 0.8, "pi": 0.1, "mu": 0.2},
                           B: {"n": 0.5, "t": 0.5, "d": -0.8, "pi": 0.1, "mu": 0.2}}}
        params = {"c_s": 0.5, "c_t": 0.5, "dials": {"OH": {"k_s": 2.0, "k_t": 0.5}}, "half_life_days": {"default": 10}}
        with tempfile.TemporaryDirectory() as d:
            write_day(Path(d), "2026-10-01", [event("e1", "2026-10-01T08:00:00+00:00", 1.0)],
                      [reaction("e1", A, 1.0, 1.0), reaction("e1", B, 0.0, 0.0)])
            m = moves.build(date(2026, 10, 1), Path(d), groups, params, "run-1")
        e = m["OH-S"]["events"]["e1"]
        self.assertAlmostEqual(e["full_s"], 2.0 * e["full_s_base"], places=4)
        self.assertAlmostEqual(e["full_t"], 0.5 * e["full_t_base"], places=4)
        self.assertEqual(moves.paths(m, "s_base")["OH-S"][0][2], e["full_s_base"])

    def test_a_state_without_its_own_dial_takes_the_national_one(self):
        groups = {"OH-S": {A: {"n": 0.5, "t": 0.5, "d": 0.8, "pi": 0.1, "mu": 0.2},
                           B: {"n": 0.5, "t": 0.5, "d": -0.8, "pi": 0.1, "mu": 0.2}}}
        params = {"c_s": 0.5, "c_t": 0.5, "dials": {"default": {"k_s": 0.5, "k_t": 1.0}},
                  "half_life_days": {"default": 10}}
        with tempfile.TemporaryDirectory() as d:
            write_day(Path(d), "2026-10-01", [event("e1", "2026-10-01T08:00:00+00:00", 1.0)],
                      [reaction("e1", A, 1.0, 0.0), reaction("e1", B, 0.0, 0.0)])
            e = moves.build(date(2026, 10, 1), Path(d), groups, params, "run-1")["OH-S"]["events"]["e1"]
        self.assertAlmostEqual(e["full_s"], 0.5 * e["full_s_base"], places=4)


class NationTest(unittest.TestCase):
    ev = lambda self, scope, full: {"first_seen": "2026-10-12", "last_seen": "2026-10-12", "scope": scope,
                                    "age_half_life": 5.5, "after_news_half_life": 1, "full": full, "full_s": full,
                                    "full_t": 0.0, "full_s_base": full, "full_t_base": 0.0, "election_day": 0.0,
                                    "card": ""}
    def m(self):
        return {"US": {"events": {"n1": self.ev("national", 1.0)}},
                "GA": {"events": {"g1": self.ev("race", 2.0)}},
                "OH-S": {"events": {"o1": self.ev("race", 3.0), "n1": self.ev("national", 4.0)}}}

    def test_a_watch_race_keeps_the_nations_national_stories(self):
        p = moves.paths(self.m())
        self.assertEqual(sorted(x[2] for x in p["GA"]), [1.0, 2.0])
        self.assertEqual(sorted(x[2] for x in p["OH-S"]), [3.0, 4.0])
        self.assertEqual(moves.takes_nation(self.m()), {"GA"})

    def test_own_stories_only(self):
        p = moves.paths(self.m(), with_nation=False)
        self.assertEqual(([x[2] for x in p["GA"]], sorted(x[2] for x in p["OH-S"])), ([2.0], [3.0, 4.0]))


class ReadTest(unittest.TestCase):
    ev = lambda first, last, full, eday, card: {"first_seen": first, "last_seen": last, "age_half_life": 5.5,
                                                "after_news_half_life": 1, "full": full, "full_s": full, "full_t": 0.0,
                                                "election_day": eday, "card": card}
    M = {"date": "2026-10-11", "params": {"c_s": 0.2, "c_t": 0.2}, "shadow": {"OH-S": {"events": {}}},
         "OH-S": {"events": {"e1": ev("2026-10-01", "2026-10-03", 2.0, 0.2, "c1"),
                             "e2": ev("2026-10-05", "2026-10-05", -0.5, -0.9, "c2"),
                             "e3": ev("2026-10-05", "2026-10-05", 0.001, 0.0004, "c3")},
                  "by_event_effect": {"e1": 1.0, "e2": -0.33, "e3": 0.0006}},
         "US": {"events": {}, "by_event_effect": {}}}

    def test_effect_paths_for_the_filter(self):
        self.assertEqual(moves.paths(self.M), {"OH-S": [("2026-10-01", "2026-10-03", 2.0, 5.5, 1),
                                                        ("2026-10-05", "2026-10-05", -0.5, 5.5, 1),
                                                        ("2026-10-05", "2026-10-05", 0.001, 5.5, 1)]})

    def test_movers_for_the_today_view_rank_by_todays_effect(self):
        self.assertEqual(moves.movers(self.M, when="today"), {"OH-S": [{"event_id": "e1", "card": "c1", "delta": 1.0},
                                                                       {"event_id": "e2", "card": "c2", "delta": -0.33}]})

    def test_races_without_stories_are_left_out_so_they_take_the_nations(self):
        self.assertNotIn("US", moves.paths(self.M))

    def test_movers_are_the_stories_effect_on_election_day(self):
        self.assertEqual(moves.movers(self.M), {"OH-S": [{"event_id": "e2", "card": "c2", "delta": -0.9},
                                                         {"event_id": "e1", "card": "c1", "delta": 0.2}]})


if __name__ == "__main__":
    unittest.main()
