import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

from simlab import start

# one story first seen 10 Oct, still in the news; one first seen 14 Oct, out of the news after 15 Oct
OLD = ("2026-10-10", "2026-10-13", 2.0, 5.5, 1.0)
NEW = ("2026-10-14", "2026-10-15", -1.0, 5.5, 1.0)
DAY = date(2026, 10, 16)


def base(kind: str = "filter") -> dict:
    races = {"NC": {"margin": 5.0, "sd": 5.5, "story_3nov": 0.3, "poll_level": 6.0},
             "TX": {"margin": -1.0, "sd": 5.5, "story_3nov": 0.0, "poll_level": -1.0},
             "VT-AL": {"margin": 30.0, "sd": 9.0, "fixed": "D"}}
    if kind == "polls":
        races = {r: {k: v for k, v in x.items() if k not in ("story_3nov", "poll_level")} for r, x in races.items()}
    return {"kind": kind, "days_to_election": 22, "national": {"var": 9.0}, "races": races}


class HeadlineTest(unittest.TestCase):
    def test_start_plus_every_storys_effect_left_on_election_day(self):
        h = start.headline(base(), {"NC": [OLD, NEW]}, DAY)
        nc = h["races"]["NC"]
        self.assertAlmostEqual(nc["margin"], 5.0 + nc["story_effect_3nov"])
        self.assertAlmostEqual(nc["moves_since_start"], nc["story_effect_3nov"] - 0.3)
        self.assertAlmostEqual(nc["start_margin"], 5.3)
        self.assertEqual((h["rule"], h["start"], h["date"], h["days_to_election"]),
                         ("simulation-only", "2026-10-12", "2026-10-16", 18))

    def test_a_race_without_news_does_not_move(self):
        h = start.headline(base(), {"NC": [OLD]}, DAY)
        self.assertEqual(h["races"]["TX"]["margin"], -1.0)
        self.assertEqual(h["races"]["VT-AL"], base()["races"]["VT-AL"])

    def test_a_race_without_its_own_stories_takes_the_nations(self):
        lasting = NEW[:4] + (None,)
        h = start.headline(base(), {"US": [lasting]}, DAY)
        self.assertLess(h["races"]["TX"]["margin"], -1.05)
        self.assertAlmostEqual(h["races"]["TX"]["margin"] + 1.0, h["races"]["NC"]["margin"] - 5.0)

    def test_linear_in_the_stories_so_the_news_parts_add_up(self):
        m = lambda p: start.headline(base(), p, DAY)["races"]["NC"]["margin"] - 5.0
        self.assertAlmostEqual(m({"NC": [OLD, NEW]}), m({"NC": [OLD]}) + m({"NC": [NEW]}))

    def test_today_view_uses_the_effect_in_force_today(self):
        far = start.headline(base(), {"NC": [NEW]}, DAY)["races"]["NC"]
        now = start.headline(base(), {"NC": [NEW]}, DAY, election=DAY)["races"]["NC"]
        self.assertAlmostEqual(now["story_effect_3nov"], now["story_effect"])
        self.assertLess(abs(far["story_effect_3nov"]), abs(now["story_effect"]))

    def test_polls_kind_counts_only_the_change_since_12_october(self):
        h = start.headline(base("polls"), {"NC": [OLD]}, DAY)["races"]["NC"]
        self.assertLess(h["moves_since_start"], 0.0)  # the 10 Oct story fades after 12 Oct
        self.assertAlmostEqual(h["margin"], 5.0 + h["moves_since_start"])
        self.assertAlmostEqual(start.headline(base("polls"), {"NC": [NEW]}, DAY)["races"]["NC"]["moves_since_start"],
                               start.headline(base(), {"NC": [NEW]}, DAY)["races"]["NC"]["story_effect_3nov"])

    def test_a_cancelled_week_drops_that_races_stories_of_the_week(self):
        drop = {"NC": [("2026-10-11", "2026-10-18")]}
        lasting = NEW[:4] + (None,)
        h = start.headline(base(), {"NC": [OLD, lasting], "US": [lasting]}, DAY, drop=drop)["races"]
        self.assertAlmostEqual(h["NC"]["margin"], start.headline(base(), {"NC": [OLD]}, DAY)["races"]["NC"]["margin"])
        self.assertLess(h["TX"]["margin"], -1.05)  # other races keep the week


class FileTest(unittest.TestCase):
    def test_rule_by_date(self):
        self.assertEqual((start.rule_for(date(2026, 10, 13)), start.rule_for(date(2026, 10, 14))),
                         ("poll-filter", "simulation-only"))

    def test_levels_for_an_election_day_with_todays_house_tiers(self):
        f = {"senate": {"2026-11-03": base()}, "house": {"2026-11-03": base()}}
        s, h = start.at(f, date(2026, 11, 3), {"NC": "simulate"})
        self.assertEqual((s["races"]["NC"]["margin"], h["races"]["NC"]["tier"], h["races"]["TX"]["tier"]),
                         (5.0, "simulate", None))
        with self.assertRaises(KeyError):
            start.at(f, date(2026, 10, 20))

    def test_cancelled_weeks_from_matteos_file(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "cancelled.json"
            self.assertEqual(start.cancelled(f), {})
            f.write_text(json.dumps({"weeks": [{"race": "TX", "week_ending": "2026-10-18", "approved": "x"}]}))
            self.assertEqual(start.cancelled(f), {"TX": [("2026-10-11", "2026-10-18")]})
        self.assertEqual(json.loads(start.CANCELLED.read_text(encoding="utf-8"))["weeks"], [])

    def test_kept_drops_stories_first_seen_inside_the_window_only(self):
        items = [("2026-10-11", 0), ("2026-10-12T08:00", 1), ("2026-10-18", 2), ("2026-10-19", 3)]
        self.assertEqual([x[1] for x in start.kept(items, [("2026-10-11", "2026-10-18")])], [0, 3])
        self.assertEqual(start.kept(items, None), items)


if __name__ == "__main__":
    unittest.main()
