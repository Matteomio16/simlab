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
    def test_latest_run_before_the_news_cutoff_unless_named(self):
        with tempfile.TemporaryDirectory() as d:
            day = Path(d) / "snapshots" / "2026-09-28"
            for hhmm in ("0036", "0941", "0617"):
                (day / hhmm).mkdir(parents=True)
            (day.parent / "2026-09-29" / "0017").mkdir(parents=True)
            self.assertEqual(statsday.snapshot_for(Path(d), date(2026, 9, 28)).name, "0617")
            self.assertEqual(statsday.snapshot_for(Path(d), date(2026, 9, 28), "0036").name, "0036")
            self.assertEqual(statsday.snapshot_for(Path(d), date(2026, 9, 29)).name, "0017")

    def test_after_the_cutoff_only_when_nothing_came_before(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "snapshots" / "2026-09-28" / "0941").mkdir(parents=True)
            self.assertEqual(statsday.snapshot_for(Path(d), date(2026, 9, 28)).name, "0941")

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

    def test_iowa_and_maine_are_pilot_races_too(self):
        safe = {"cook": "Solid R", "market": 0.01}
        out = statsday.tiers({"IA": {}, "ME": {}}, {"IA": 0.01, "ME": 0.01}, {"IA": safe, "ME": safe}, [])
        self.assertEqual({r: out[r]["tier"] for r in out}, {"IA": "simulate", "ME": "simulate"})


class StoriesTest(unittest.TestCase):
    MV = {"date": "2026-10-01", "shadow": {},
          "US": {"events": {"n1": {"election_day": 0.1, "scope": "national"}}, "by_event_effect": {"n1": 0.5}},
          "OH-S": {"events": {"a": {"election_day": 0.2, "scope": "race"}, "n1": {"election_day": 0.3, "scope": "national"}},
                   "by_event_effect": {"a": 1.0, "n1": 0.6}},
          "IA": {"events": {"b": {"election_day": 0.05, "scope": "race"}}, "by_event_effect": {"b": 0.4}},
          "WY": {"events": {}, "by_event_effect": {}}}

    def test_each_races_stories_on_3_november_and_today(self):
        eday, now = statsday._stories(self.MV, "election_day"), statsday._stories(self.MV, "today")
        self.assertEqual(eday, {"OH-S": {"a": 0.2, "n1": 0.3}, "IA": {"b": 0.05, "n1": 0.1}, "WY": {"n1": 0.1}})
        self.assertEqual(now, {"OH-S": {"a": 1.0, "n1": 0.6}, "IA": {"b": 0.4, "n1": 0.5}, "WY": {"n1": 0.5}})


class WeeklyTest(unittest.TestCase):
    MP = {"dials": {}, "age_half_life_days": 5.5,
          "dial_prior": {"mean": [1.0, 1.0], "sd": [0.44, 0.71], "tau": [0.3, 0.5]}}

    def test_latest_weekly_update_on_or_before_the_day(self):
        with tempfile.TemporaryDirectory() as d:
            for day in ("2026-10-12", "2026-10-19"):
                (Path(d) / "derived" / day).mkdir(parents=True)
                (Path(d) / "derived" / day / "filter_weekly.json").write_text(json.dumps({"date": day}))
            self.assertEqual(statsday.latest_weekly(Path(d), date(2026, 10, 15))["date"], "2026-10-12")
            self.assertIsNone(statsday.latest_weekly(Path(d), date(2026, 10, 11)))

    def test_before_the_first_update_the_dials_follow_the_prior(self):
        mp = statsday.apply_weekly(self.MP, None)
        self.assertEqual((mp["dial_posterior"]["labels"], mp["dial_posterior"]["mean"]), (["national"], [1.0, 1.0]))
        self.assertAlmostEqual(mp["dial_posterior"]["cov"][0][0], 0.44 ** 2)
        self.assertEqual(mp["dials"], {})

    def test_a_weekly_update_sets_the_dials_and_the_fade_speed(self):
        wk = {"date": "2026-10-12", "dials": {"OH": {"k_s": 0.6, "k_t": 1.1}, "default": {"k_s": 0.9, "k_t": 1.0}},
              "fade": {"half_life": 4.2},
              "posterior": {"labels": ["national", "OH"], "mean": [0.9, 1.0, -0.3, 0.1], "cov": [[0.1] * 4] * 4}}
        mp = statsday.apply_weekly(self.MP, wk)
        self.assertEqual((mp["dials"]["OH"]["k_s"], mp["age_half_life_days"], mp["dial_posterior"]["labels"]),
                         (0.6, 4.2, ["national", "OH"]))
        self.assertEqual(statsday.apply_weekly(self.MP | {"support_offset": 0.08}, wk | {"offset": {"offset": 0.05}})
                         ["support_offset"], 0.05)

    @staticmethod
    def nc(p50, poll):
        return {"margin": {"p50": p50}, "stats_only": {"margin": {"p50": p50}}, "benchmarks": {"poll_avg": poll}}

    @staticmethod
    def day(d: str, forecast: dict, senate: list[str] | None = None, seen=None, house_levels=None,
            house_polls: dict | None = None) -> Path:
        """derived/<d> with forecast.json, polls.csv (NC polls by `senate` pollsters, first seen `seen`) and, given
        them, house_levels.json and house_polls.csv ({seat: [pollsters]})."""
        out = Path(d)
        out.mkdir(parents=True, exist_ok=True)
        (out / "forecast.json").write_text(json.dumps(forecast))
        senate = senate or []
        pd.DataFrame({"race_id": ["NC"] * len(senate), "pollster": senate,
                      "first_seen": seen or ["2026-10-01 09:07"] * len(senate)}).to_csv(out / "polls.csv", index=False)
        if house_levels is not None:
            (out / "house_levels.json").write_text(json.dumps({"races": house_levels}))
        if house_polls is not None:
            rows = [{"race_id": r, "pollster": p, "start": "2026-10-01", "end": "2026-10-03", "population": "lv"}
                    for r, ps in house_polls.items() for p in ps]
            pd.DataFrame(rows, columns=statsday.FIRST_SEEN_KEY).to_csv(out / "house_polls.csv", index=False)
        return out

    def test_trend_check_against_the_forecast_a_week_earlier(self):
        with tempfile.TemporaryDirectory() as d:
            der = Path(d) / "derived"
            self.day(der / "2026-10-12", {"date": "2026-10-12", "snapshot": "2026-10-12 09:07",
                                          "races": {"NC": self.nc(5.0, 6.0)}, "house": None})
            now = {"races": {"NC": self.nc(1.0, 9.0)}, "house": None}
            out = self.day(der / "2026-10-19", now, list("ABCD"), ["2026-10-12 09:07"] + ["2026-10-16 09:07"] * 3)
            res = statsday.week_trend(Path(d), date(2026, 10, 19), now, out)
            self.assertEqual((res["since"], res["new_polls"], res["analyse"]), ("2026-10-12", {"NC": 3}, ["NC"]))
            self.assertEqual((res["far_from_polls"], res["house"]), ({}, {"note": "no House forecast to compare"}))
            later = self.day(der / "2026-10-20", now, list("ABC"))
            self.assertIn("no forecast", statsday.week_trend(Path(d), date(2026, 10, 20), now, later)["note"])

    def test_house_trend_from_last_mondays_house_poll_table(self):
        seat = lambda p50: {"margin": {"p50": p50}}
        with tempfile.TemporaryDirectory() as d:
            der = Path(d) / "derived"
            self.day(der / "2026-10-12", {"date": "2026-10-12", "snapshot": "2026-10-12 09:07", "races": {},
                                          "house": {"races": {"AK-AL": seat(-11.0)}}},
                     house_levels={"AK-AL": {"margin": -11.5, "poll_margin": -12.0}}, house_polls={"AK-AL": ["A", "B"]})
            now = {"races": {}, "house": {"races": {"AK-AL": seat(-16.0), "NY-21": seat(-30.0)}}}
            out = self.day(der / "2026-10-19", now,
                           house_levels={"AK-AL": {"margin": -14.0, "poll_margin": -9.0},
                                         "NY-21": {"margin": -29.0, "poll_margin": -5.0}},
                           house_polls={"AK-AL": list("ABCDE"), "NY-21": list("XYZ")})
            res = statsday.week_trend(Path(d), date(2026, 10, 19), now, out)
            h = res["house"]
            self.assertEqual((h["new_polls"], h["flagged"], h["analyse"]), ({"AK-AL": 3, "NY-21": 3}, [], ["AK-AL"]))
            r = h["races"]["AK-AL"]  # ours -5 against the polls' +3
            self.assertEqual((r["office"], r["gap"], r["stats_only_change"]), ("house", 8.0, -2.5))
            self.assertEqual((r["news_change"], r["movers"]), (None, []))  # no per-seat news in forecast.json
            self.assertEqual(h["races"]["NY-21"]["level"], "no poll average a week ago")
            self.assertEqual(sorted(res["far_from_polls"]), ["NY-21"])  # 25 points from its 3 polls
            self.assertEqual(statsday.trend_summary(res), {"flagged": [], "analyse": ["AK-AL"],
                                                           "far_from_polls": ["NY-21"]})

    def test_a_broken_trend_check_never_stops_the_forecast(self):
        with tempfile.TemporaryDirectory() as d:
            der = Path(d) / "derived"
            (der / "2026-10-12").mkdir(parents=True)
            (der / "2026-10-12" / "forecast.json").write_text("{}")
            out = self.day(der / "2026-10-19", {"races": {}}, ["A"], ["2026-10-16 09:07"])
            res = statsday.week_trend(Path(d), date(2026, 10, 19), {"races": {}}, out)
            self.assertTrue(res["error"].startswith("KeyError"))
            self.assertEqual(statsday.trend_summary(res), {"error": res["error"]})


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

class SimulationOnlyTest(unittest.TestCase):
    """The simulation-only rule's daily pieces (Matteo, 13 Oct)."""

    def test_dials_frozen_at_12_october_and_the_old_rules_own_updates(self):
        with tempfile.TemporaryDirectory() as d:
            for root, day in (("derived", "2026-10-12"), ("derived", "2026-10-19"), ("old", "2026-10-26")):
                (Path(d) / root / day).mkdir(parents=True)
                (Path(d) / root / day / "filter_weekly.json").write_text(json.dumps({"date": day}))
            self.assertEqual(statsday.latest_weekly(Path(d), date(2026, 10, 12))["date"], "2026-10-12")
            self.assertEqual(statsday.latest_weekly(Path(d), date(2026, 10, 30), ("derived", "old"))["date"],
                             "2026-10-26")

    def test_candidate_surnames_for_the_weekly_rows(self):
        names = statsday.candidates(statsday.races_json([NC]), {"AK-AL": {"candidates": {"R": ["Nick Begich"],
                                                                                         "D": ["Eric Hafner"],
                                                                                         "O": ["Bill Hill"]},
                                                                          "left_party": "O"}})
        self.assertEqual(names, {"NC": {"left": "Cooper", "left_party": "D", "right": "Whatley"},
                                 "AK-AL": {"left": "Hill", "left_party": "O", "right": "Begich"}})

    def test_sunday_check_against_the_rules_first_week(self):
        nc = lambda p50, poll: {"margin": {"p10": p50 - 6, "p50": p50, "p90": p50 + 6},
                                "benchmarks": {"poll_avg": poll, "market": None}}
        seat = lambda p50: {"margin": {"p10": p50 - 6, "p50": p50, "p90": p50 + 6}}
        with tempfile.TemporaryDirectory() as d:
            der = Path(d) / "derived"
            WeeklyTest.day(der / "2026-10-14", {"date": "2026-10-14", "snapshot": "2026-10-14 09:07",
                                                "races": {"NC": nc(5.0, 6.0)}, "house": {"races": {"AK-AL": seat(-12)}}},
                           house_levels={"AK-AL": {"margin": -12.0, "poll_margin": -12.0}},
                           house_polls={"AK-AL": ["A"]})
            now = {"races": {"NC": nc(1.0, 9.0)}, "house": {"races": {"AK-AL": seat(-12)}}}
            out = WeeklyTest.day(der / "2026-10-18", now, list("ABCD"), ["2026-10-14 09:07"] + ["2026-10-16 09:07"] * 3,
                                 house_levels={"AK-AL": {"margin": -12.0, "poll_margin": -5.0}},
                                 house_polls={"AK-AL": ["A", "B"]})
            mv = {"NC": {"events": {"e1": {"first_seen": "2026-10-15", "election_day": -0.4, "card": "x"}}}}
            names = {"NC": {"left": "Cooper", "left_party": "D", "right": "Whatley"}}
            res = statsday.weekly_check_files(Path(d), date(2026, 10, 18), now, out, mv, names=names)
            r = {x["race"]: x for x in res["races"]}
            self.assertEqual((res["since"], r["NC"]["n_polls"], r["NC"]["gap"], r["NC"]["flag"]),
                             ("2026-10-14", 3, 7.0, "cancel"))  # ours -4 against the polls' +3, 3 new polls
            self.assertEqual((r["NC"]["left"], r["NC"]["stories"][0]["event_id"]), ("Cooper", "e1"))
            self.assertEqual((r["AK-AL"]["n_polls"], r["AK-AL"]["gap"], r["AK-AL"]["flag"]), (1, 7.0, "flag"))
            first = statsday.weekly_check_files(Path(d), date(2026, 10, 14), now, out, mv)
            self.assertIn("nothing to compare", first["note"])



if __name__ == "__main__":
    unittest.main()
