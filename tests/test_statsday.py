import gzip
import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

import pandas as pd

from simlab import statsday
from simlab.polls import OVERVIEW_PAGE, Race, slug
from tests.test_montecarlo import KALSHI, POLY, PREDICTIONS

NC = Race("NC", False, "Michael Whatley", "Roy Cooper", "D", "2026 United States Senate election in North Carolina",
          "R", "Incumbent retiring")
OH = Race("OH", True, "Jon Husted", "Sherrod Brown", "D", "2026 United States Senate special election in Ohio", "R",
          "Interim appointee nominated")
AK = Race("AK", False, "Dan S. Sullivan", "Mary Peltola", "D", "2026 United States Senate election in Alaska", "R",
          "Incumbent advanced to general")


def put(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(gzip.compress(json.dumps(obj).encode()))


class SnapshotTest(unittest.TestCase):
    def test_latest_run_of_the_day_unless_named(self):
        with tempfile.TemporaryDirectory() as d:
            day = Path(d) / "snapshots" / "2026-09-28"
            for hhmm in ("0036", "0941", "0617"):
                (day / hhmm).mkdir(parents=True)
            (day.parent / "2026-09-29" / "0017").mkdir(parents=True)
            self.assertEqual(statsday.snapshot_for(Path(d), date(2026, 9, 28)).name, "0941")
            self.assertEqual(statsday.snapshot_for(Path(d), date(2026, 9, 28), "0036").name, "0036")

    def test_no_run_that_day(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(FileNotFoundError):
                statsday.snapshot_for(Path(d), date(2026, 9, 28))


class FilesTest(unittest.TestCase):
    def test_races_json(self):
        r = statsday.races_json([NC, OH, AK])
        self.assertEqual(list(r), ["NC", "OH-S", "AK"])
        self.assertEqual(r["OH-S"], {"state": "OH", "office": "senate", "district": None, "special": True, "rcv": False,
                                     "candidates": {"left": "Sherrod Brown", "right": "Jon Husted"},
                                     "left_party": "D", "incumbent_party": "R", "status": "Interim appointee nominated"})
        self.assertTrue(r["AK"]["rcv"])

    def test_poll_rows_put_the_generic_ballot_under_us(self):
        senate = pd.DataFrame({"race_id": ["NC"], "pollster": ["A"], "margin": [2.0]})
        gb = pd.DataFrame({"pollster": ["B"], "margin": [3.0]})
        out = statsday.poll_rows(senate, gb)
        self.assertEqual(out.race_id.tolist(), ["NC", "US"])
        self.assertEqual(out.margin.tolist(), [2.0, 3.0])


class FirstSeenTest(unittest.TestCase):
    TODAY = pd.DataFrame({"race_id": ["NC", "NC", "OH-S"], "pollster": ["A", "B", "C"],
                          "start": [date(2026, 9, 20), date(2026, 9, 21), date(2026, 9, 25)],
                          "end": [date(2026, 9, 22), date(2026, 9, 23), date(2026, 9, 27)],
                          "population": ["lv", "rv", "lv"]})

    def test_carried_from_the_last_day_and_stamped_when_new(self):
        prev = pd.DataFrame({"race_id": ["NC", "NC"], "pollster": ["A", "B"], "start": ["2026-09-20", "2026-09-21"],
                             "end": ["2026-09-22", "2026-09-23"], "population": ["lv", "rv"],
                             "first_seen": ["2026-09-27 09:17", "2026-09-28 09:17"]})
        out = statsday.first_seen(self.TODAY, prev, "2026-09-29 09:17")
        self.assertEqual(out.first_seen.tolist(), ["2026-09-27 09:17", "2026-09-28 09:17", "2026-09-29 09:17"])

    def test_first_day(self):
        self.assertEqual(set(statsday.first_seen(self.TODAY, None, "2026-09-28 09:41").first_seen), {"2026-09-28 09:41"})

    def test_previous_poll_file_is_the_latest_earlier_day(self):
        with tempfile.TemporaryDirectory() as d:
            for day, v in (("2026-09-26", "a"), ("2026-09-27", "b"), ("2026-09-29", "c")):
                (Path(d) / "derived" / day).mkdir(parents=True)
                pd.DataFrame({"x": [v]}).to_csv(Path(d) / "derived" / day / "polls.csv", index=False)
            (Path(d) / "derived" / "2026-09-28").mkdir()
            self.assertEqual(statsday.previous_polls(Path(d), date(2026, 9, 29)).x.tolist(), ["b"])
            self.assertIsNone(statsday.previous_polls(Path(d), date(2026, 9, 26)))


class TierTest(unittest.TestCase):
    def test_tier_rules(self):
        self.assertEqual(statsday.tier(0.5, "Solid R", 0.02)[0], "simulate")
        self.assertEqual(statsday.tier(0.95, "Lean R", 0.97)[0], "simulate")
        self.assertEqual(statsday.tier(0.95, "Solid D", 0.96)[0], "watch")
        self.assertEqual(statsday.tier(0.99, "Likely D", 0.99)[0], "watch")
        self.assertEqual(statsday.tier(0.99, "Solid D", 0.98), ("statistics", ["all three signals call it safe"]))

    def test_pilot_races_always_simulate_and_a_week_of_memory(self):
        races = {"OH-S": {}, "CO": {}, "WY": {}}
        stats = {"OH-S": 0.99, "CO": 0.99, "WY": 0.01}
        bench = {"OH-S": {"cook": "Solid D", "market": 0.99}, "CO": {"cook": "Solid D", "market": 0.99},
                 "WY": {"cook": "Solid R", "market": 0.01}}
        history = [{"CO": {"tier_raw": "watch"}}, {"WY": {"tier_raw": "statistics"}}]
        out = statsday.tiers(races, stats, bench, history)
        self.assertEqual((out["OH-S"]["tier"], out["OH-S"]["tier_reasons"]), ("simulate", ["pilot race"]))
        self.assertEqual((out["CO"]["tier_raw"], out["CO"]["tier"]), ("statistics", "watch"))
        self.assertEqual(out["WY"]["tier"], "statistics")


class BenchmarkTest(unittest.TestCase):
    def test_markets_and_cook_from_the_snapshot(self):
        with tempfile.TemporaryDirectory() as d:
            snap = Path(d)
            put(snap / "markets" / "kalshi.gz", KALSHI)
            put(snap / "markets" / "polymarket.gz", POLY)
            put(snap / "wikipedia" / f"{slug(OVERVIEW_PAGE)}.gz",
                {"revisions": [{"revid": 1, "slots": {"main": {"content": PREDICTIONS}}}]})
            b = statsday.benchmarks(snap, [NC, OH, AK])
        self.assertAlmostEqual(b["NC"]["market"], 0.9401, places=4)
        self.assertEqual(b["NC"]["cook"], "Lean D")
        self.assertEqual(set(b["NC"]["market_venues"]), {"kalshi", "polymarket"})
        self.assertEqual((b["OH-S"]["market"], b["OH-S"]["cook"]), (None, "Tossup"))
        self.assertEqual(b["AK"]["cook"], None)
        self.assertEqual(b["US-S"], {"market": None, "market_venues": {}})

    def test_missing_market_files(self):
        with tempfile.TemporaryDirectory() as d:
            snap = Path(d)
            put(snap / "wikipedia" / f"{slug(OVERVIEW_PAGE)}.gz",
                {"revisions": [{"revid": 1, "slots": {"main": {"content": PREDICTIONS}}}]})
            b = statsday.benchmarks(snap, [NC])
        self.assertEqual((b["NC"]["market"], b["NC"]["cook"]), (None, "Lean D"))


if __name__ == "__main__":
    unittest.main()
