import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

from simlab import newsnap

NOW = datetime(2026, 10, 12, 12, 0, tzinfo=timezone.utc)


def manifest(root: Path, day: str, hhmm: str, names: list[str], errors: list[str] = ()) -> None:
    run = root / day / hhmm
    run.mkdir(parents=True, exist_ok=True)
    files = [{"source": "news", "name": n, "file": f"news/{n}.gz"} for n in names]
    files += [{"source": "news", "name": n, "error": "HTTP 429"} for n in errors]
    (run / "manifest.json").write_text(json.dumps({"files": files}), encoding="utf-8")


class Due(unittest.TestCase):
    def test_last_saved_reads_successes_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest(root, "2026-10-11", "2300", ["gdelt-ohio"])
            manifest(root, "2026-10-12", "0900", ["gdelt-texas"], errors=["gdelt-ohio"])
            last = newsnap.last_saved(root, NOW)
        self.assertEqual(last, {"gdelt-ohio": datetime(2026, 10, 11, 23, 0, tzinfo=timezone.utc),
                                "gdelt-texas": datetime(2026, 10, 12, 9, 0, tzinfo=timezone.utc)})

    def test_most_overdue_first_and_the_simulated_races_before_the_rest(self):
        last = {"gdelt-ohio": datetime(2026, 10, 12, 1, 0, tzinfo=timezone.utc),
                "gdelt-texas": datetime(2026, 10, 12, 9, 0, tzinfo=timezone.utc),
                "gdelt-al": datetime(2026, 10, 11, 1, 0, tzinfo=timezone.utc)}
        order = newsnap.due(["ohio", "texas", "al", "ga", "national"], last, NOW, first={"ohio", "national", "ga"})
        # texas was saved 3 hours ago: not due; never-saved queries count as the most overdue
        self.assertEqual(order, ["national", "ga", "ohio", "al"])

    def test_until_the_full_run_the_pilot_races_come_before_the_other_contested_races(self):
        slugs, first = ["ak", "ar", "ohio", "texas", "national", "al"], newsnap.PILOT | {"ak", "ar"}
        pilot_week = datetime(2026, 10, 5, 12, 0, tzinfo=timezone.utc)
        self.assertEqual(newsnap.due(slugs, {}, pilot_week, first), ["national", "ohio", "texas", "ak", "ar", "al"])
        self.assertEqual(newsnap.due(slugs, {}, NOW, first), ["national", "ak", "ar", "ohio", "texas", "al"])


class Gdelt(unittest.TestCase):
    def test_a_refused_query_is_retried_until_the_budget_ends_and_the_rest_wait_for_the_next_run(self):
        replies = iter([429, 429, 200])

        class Resp:
            def __init__(self, status):
                self.status_code, self.content = status, b'{"articles": []}'

        class Run:
            saved, errors = [], []

            def save(self, source, name, url, fetch):
                self.saved.append((name, fetch()[0]))

            def error(self, source, name, url, message, fetched_at=None):
                self.errors.append(name)
        clock = [0.0]  # time moves only when the code sleeps: 6 s, then 30 s and 60 s of back-off, then ohio is saved

        def sleep(s):
            clock[0] += s
        with mock.patch.object(newsnap.snap.requests, "get", lambda *a, **k: Resp(next(replies))), \
                mock.patch.object(newsnap.time, "sleep", sleep), \
                mock.patch.object(newsnap.time, "monotonic", lambda: clock[0]):
            run = Run()
            newsnap.gdelt(run, {"ohio": '("Sherrod Brown")', "texas": '("Ken Paxton")'}, ["ohio", "texas"], budget_s=100)
        self.assertEqual(run.saved, [("gdelt-ohio", 200)])
        self.assertEqual(run.errors, ["gdelt-texas"])


class Pilot(unittest.TestCase):
    def test_the_pilot_races_and_the_nation_are_asked_first(self):
        self.assertEqual(newsnap.PILOT, {"ohio", "north-carolina", "texas", "ia", "me", "national"})
        self.assertEqual(newsnap.first_races(None), newsnap.PILOT)


class Queries(unittest.TestCase):
    def test_every_race_and_the_nation_with_the_pilot_file_names(self):
        qs = newsnap.queries()
        self.assertIn("ohio", qs)
        self.assertIn("national", qs)
        self.assertIn("ga", qs)
        self.assertEqual(qs["ohio"], '("Sherrod Brown" OR "Jon Husted")')


class House(unittest.TestCase):
    RACES = {"date": "2026-10-11", "GA": {"state": "GA", "tier": "watch"},
             "OH-9": {"state": "OH", "office": "house", "district": 9, "tier": "simulate",
                      "candidates": {"D": ["Marcy Kaptur"], "R": ["Derek Merrin"]}}}

    def test_one_query_per_state_for_the_simulated_seats(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "races.json"
            p.write_text(json.dumps(self.RACES), encoding="utf-8")
            qs, first = newsnap.queries(p), newsnap.first_races(p)
        self.assertEqual(qs["oh-h"], '("Marcy Kaptur" OR "Derek Merrin")')
        self.assertNotIn("oh-9", qs)
        self.assertIn("ohio", qs)
        self.assertTrue({"oh-h", "ga"} <= first)

    def test_a_states_house_seats_are_asked_every_12_hours(self):
        seven_hours_ago = datetime(2026, 10, 12, 5, 0, tzinfo=timezone.utc)
        last = {"gdelt-oh-h": seven_hours_ago, "gdelt-ga": seven_hours_ago}
        self.assertEqual(newsnap.due(["oh-h", "ga"], last, NOW), ["ga"])


if __name__ == "__main__":
    unittest.main()
