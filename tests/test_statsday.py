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
