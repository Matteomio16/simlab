import unittest

import numpy as np
from scipy.stats import multivariate_normal

from simlab import weekly


class LikelihoodTest(unittest.TestCase):
    def test_loglik_matches_the_joint_normal(self):
        t, y, v, q = np.array([0.0, 3.0]), np.array([1.0, 2.5]), np.array([4.0, 2.0]), 0.5
        prior = 1e6
        cov = np.array([[prior + v[0], prior], [prior, prior + 3 * q + v[1]]])
        direct = multivariate_normal(mean=[0, 0], cov=cov).logpdf(y)
        self.assertAlmostEqual(weekly.loglik(t, y, v, q)[0], direct, places=6)

    def test_innovations_are_standardised(self):
        t = np.arange(40.0)
        y = np.r_[np.zeros(39), 12.0]
        _, z = weekly.loglik(t, y, np.ones(40), 0.01)
        self.assertGreater(z[-1], 6)
        self.assertLess(np.abs(z[5:-1]).max(), 1e-6)

    def test_quadratic_recovered_from_six_points(self):
        A, b, c = np.array([[2.0, 0.5], [0.5, 1.0]]), np.array([1.0, -0.5]), 3.0
        f = lambda k: float(-0.5 * k @ A @ k + b @ k + c)
        A2, b2, c2 = weekly.quadratic(f)
        np.testing.assert_allclose(A2, A, atol=1e-9)
        np.testing.assert_allclose(b2, b, atol=1e-9)
        self.assertAlmostEqual(c2, c)


class PoolTest(unittest.TestCase):
    PRIOR = {"mean": [1.0, 1.0], "sd": [0.5, 0.5], "tau": [0.3, 0.3]}

    def test_no_data_returns_the_prior(self):
        post = weekly.pool({}, self.PRIOR)
        np.testing.assert_allclose(post["national"]["mean"], [1.0, 1.0])
        np.testing.assert_allclose(np.sqrt(np.diag(post["national"]["cov"])), [0.5, 0.5])

    def test_strong_data_moves_its_state_and_the_nation_less(self):
        info = 1e4
        units = {"OH": (np.diag([info, info]), np.array([0.2, 0.4]) * info, 0.0)}
        post = weekly.pool(units, self.PRIOR)
        np.testing.assert_allclose(post["units"]["OH"]["mean"], [0.2, 0.4], atol=0.01)
        nat = post["national"]["mean"]
        self.assertTrue(0.2 < nat[0] < 1.0 and 0.4 < nat[1] < 1.0)
        self.assertLess(np.sqrt(post["units"]["OH"]["cov"][0][0]), 0.02)

    def test_a_state_without_data_borrows_the_national_dial(self):
        units = {"OH": (np.diag([1e4, 1e4]), np.array([0.2, 0.4]) * 1e4, 0.0)}
        post = weekly.pool(units, self.PRIOR)
        other = weekly.state_dial(post, "TX", self.PRIOR)
        np.testing.assert_allclose(other["mean"], post["national"]["mean"])
        self.assertGreater(other["cov"][0][0], post["national"]["cov"][0][0])

    def test_marginal_likelihood_prefers_the_model_that_fits(self):
        good = {"OH": (np.diag([100.0, 100.0]), np.array([100.0, 100.0]), -1.0)}
        bad = {"OH": (np.diag([100.0, 100.0]), np.array([100.0, 100.0]), -50.0)}
        self.assertGreater(weekly.pool(good, self.PRIOR)["log_evidence"], weekly.pool(bad, self.PRIOR)["log_evidence"])


PARAMS = {"drift_daily_sd": {"national": 0.3, "race": 0.5}}
ELECTION = weekly.ELECTION


def story(first, full_s, h_age=None, h_after=None, full_t=0.0, scope="race", unit=0.0):
    return {"first_seen": first, "last_seen": first, "full_s_base": full_s, "full_t_base": full_t, "full_s_unit": unit,
            "age_half_life": h_age, "after_news_half_life": h_after, "scope": scope}


def synthetic(k_us, k_oh, h_true=None, noise=0.3, seed=0):
    """GB and Ohio polls from t = -80 to -30 with a national story at -60 and an Ohio story at -50. Ohio wasn't asked the
    national story, so its polls carry the nation's effect at the national dial."""
    from datetime import timedelta
    import pandas as pd
    rng = np.random.default_rng(seed)
    t = np.arange(-80.0, -29.0)
    m = {"US": {"events": {"n1": story(str(ELECTION + timedelta(days=-60)), 3.0, h_true, scope="national")}},
         "OH-S": {"events": {"o1": story(str(ELECTION + timedelta(days=-50)), 4.0, h_true)}}}
    shape = lambda t0: np.where(t >= t0, 1.0 if h_true is None else 0.5 ** (np.maximum(t - t0, 0) / h_true), 0.0)
    gb = 2.0 + k_us * 3.0 * shape(-60) + rng.normal(0, noise, len(t))
    oh = 2.0 - 1.0 + k_us * 3.0 * shape(-60) + k_oh * 4.0 * shape(-50) + rng.normal(0, noise, len(t))
    p = pd.DataFrame({"race": ["US"] * len(t) + ["OH-S"] * len(t), "t": np.r_[t, t], "adj": np.r_[gb, oh],
                      "v": noise ** 2})
    return p, m


def offset_synthetic(b_true, noise=0.3, seed=0):
    """Ohio polls from t = -80 to -30 around a flat nation: a story at -60 worth 4 points that the support offset
    doesn't touch, and one at -50 made only of the offset's effect (10 points per unit of offset)."""
    from datetime import timedelta
    import pandas as pd
    rng = np.random.default_rng(seed)
    t = np.arange(-80.0, -29.0)
    day = lambda k: str(ELECTION + timedelta(days=k))
    m = {"OH-S": {"events": {"a": story(day(-60), 4.0), "b": story(day(-50), 0.0, unit=10.0)}}}
    oh = 1.0 + 4.0 * (t >= -60) + b_true * 10.0 * (t >= -50) + rng.normal(0, noise, len(t))
    gb = 2.0 + rng.normal(0, noise, len(t))
    return pd.DataFrame({"race": ["US"] * len(t) + ["OH-S"] * len(t), "t": np.r_[t, t], "adj": np.r_[gb, oh],
                         "v": noise ** 2}), m


class AloneTest(unittest.TestCase):
    def test_a_unit_whose_polls_say_nothing_reports_no_dial_rather_than_noise(self):
        self.assertEqual(weekly._alone(np.zeros((2, 2)), np.zeros(2)), {"k": [None, None], "se": [None, None]})
        out = weekly._alone(np.diag([100.0, 1e-9]), np.array([80.0, 0.0]))
        self.assertEqual((out["k"][0], out["se"][0], out["k"][1]), (0.8, 0.1, None))


class OffsetTest(unittest.TestCase):
    PRIOR = {"mean": [1.0, 1.0], "sd": [0.5, 0.5], "tau": [0.3, 0.3]}

    def test_offset_grid_finds_the_true_support_offset(self):
        p, m = offset_synthetic(0.2)
        g = weekly.offset_grid(p, m, PARAMS, 30, self.PRIOR, [0.0, 0.1, 0.2, 0.3, 0.4], used=0.0, mean=0.2, sd=1.0)
        self.assertEqual(max(g["weights"], key=g["weights"].get), "0.2")
        self.assertAlmostEqual(g["offset"], 0.2, delta=0.05)
        self.assertFalse(g["flag"])

    def test_an_offset_pulled_below_zero_is_flagged(self):
        p, m = offset_synthetic(-0.2)
        g = weekly.offset_grid(p, m, PARAMS, 30, self.PRIOR, [-0.4, -0.2, 0.0, 0.2, 0.4], used=0.0, mean=0.0, sd=1.0)
        self.assertLess(g["offset"], 0)
        self.assertTrue(g["flag"])


class UnitsTest(unittest.TestCase):
    def test_dials_learned_from_polls_recover_the_truth(self):
        p, m = synthetic(0.5, 1.5)
        u = weekly.units(p, m, PARAMS, 30, dials_us=(0.5, 1.0))
        k_us = np.linalg.lstsq(u["US"][0], u["US"][1], rcond=None)[0]
        k_oh = np.linalg.lstsq(u["OH"][0], u["OH"][1], rcond=None)[0]
        self.assertAlmostEqual(k_us[0], 0.5, delta=0.1)
        self.assertAlmostEqual(k_oh[0], 1.5, delta=0.1)
        self.assertLess(abs(u["OH"][0][1, 1]), 1e-9)

    def test_fade_speed_grid_prefers_the_true_speed(self):
        p, m = synthetic(1.0, 1.0, h_true=2.75)
        prior = {"mean": [1.0, 1.0], "sd": [0.5, 0.5], "tau": [0.3, 0.3]}
        grid = weekly.fade_grid(p, m, PARAMS, 30, prior, [2.75, 5.5, 11.0])
        self.assertEqual(max(grid["weights"], key=grid["weights"].get), "2.75")

    def test_surprise_monitor_flags_a_state_whose_polls_are_off(self):
        p, m = synthetic(1.0, 1.0)
        p.loc[(p.race == "OH-S") & (p.t > -37), "adj"] += 6.0
        flags = weekly.surprises(p, m, PARAMS, 30, {"US": (1.0, 1.0), "OH": (1.0, 1.0)})
        self.assertTrue(flags["OH-S"]["flag"])
        self.assertFalse(flags["US"]["flag"])
        self.assertGreater(flags["OH-S"]["mean_z"], 0)


def race(p50, poll, stats=None, effect=0.0, movers=()):
    return {"margin": {"p10": p50 - 6, "p50": p50, "p90": p50 + 6},
            "stats_only": {"margin": {"p50": p50 if stats is None else stats}}, "benchmarks": {"poll_avg": poll},
            "news": {"effect": effect}, "movers": list(movers)}


def polls_table(counts: dict, stamp="2026-10-15 09:07", old=2):
    import pandas as pd
    rows = [(r, f"P{i}", stamp) for r, n in counts.items() for i in range(n)]
    rows += [(r, f"Old{i}", "2026-09-29 09:07") for r in counts for i in range(old)]
    return pd.DataFrame(rows, columns=["race_id", "pollster", "first_seen"])


class TrendTest(unittest.TestCase):
    """The weekly trend check (Matteo, 11 Oct; roadmap A15)."""
    BEFORE = {"date": "2026-10-12", "snapshot": "2026-10-12 09:07"}

    def check(self, before: dict, now: dict, counts: dict, **kw):
        return weekly.trend({"date": "2026-10-19", "snapshot": "2026-10-19 09:07", "races": now},
                            self.BEFORE | {"races": before}, polls_table(counts), **kw)

    def test_opposite_moves_over_4_are_flagged_and_over_6_analysed(self):
        before = {"NC": race(5.0, 6.0), "TX": race(-2.0, -1.0), "OH-S": race(1.0, 0.0), "IA": race(0.0, 0.0)}
        now = {"NC": race(3.0, 9.0), "TX": race(1.0, -2.0), "OH-S": race(-2.0, 2.5), "IA": race(-1.0, 3.0)}
        out = self.check(before, now, {"NC": 3, "TX": 4, "OH-S": 3, "IA": 3})
        r = out["races"]
        self.assertEqual((r["NC"]["gap"], r["NC"]["level"]), (5.0, "flag"))  # -2 against +3
        self.assertEqual((r["TX"]["gap"], r["TX"]["level"]), (4.0, "ok"))  # +3 against -1: not over 4
        self.assertEqual((r["OH-S"]["gap"], r["OH-S"]["level"]), (5.5, "flag"))
        self.assertEqual(r["IA"]["level"], "ok")  # -1 against +3: a gap of 4
        self.assertEqual((out["flagged"], out["analyse"]), (["NC", "OH-S"], []))
        now["NC"] = race(1.5, 9.0)
        out = self.check(before, now, {"NC": 3})
        self.assertEqual((out["races"]["NC"]["gap"], out["races"]["NC"]["level"]), (6.5, "analyse"))
        self.assertEqual((out["flagged"], out["analyse"]), ([], ["NC"]))

    def test_same_direction_is_never_flagged_however_far_apart(self):
        out = self.check({"NC": race(5.0, 5.0)}, {"NC": race(5.5, 15.0)}, {"NC": 5})
        self.assertFalse(out["races"]["NC"]["opposite"])
        self.assertEqual((out["races"]["NC"]["gap"], out["races"]["NC"]["level"]), (9.5, "ok"))
        out = self.check({"NC": race(5.0, 5.0)}, {"NC": race(5.0, 15.0)}, {"NC": 5})  # our margin didn't move
        self.assertEqual(out["races"]["NC"]["level"], "ok")

    def test_only_states_with_3_new_polls_since_last_monday(self):
        before = {"NC": race(5.0, 6.0), "TX": race(-2.0, -1.0)}
        now = {"NC": race(0.0, 12.0), "TX": race(4.0, -5.0)}
        out = self.check(before, now, {"NC": 2, "TX": 3})
        self.assertEqual(sorted(out["races"]), ["TX"])
        self.assertEqual(out["new_polls"], {"NC": 2, "TX": 3})
        self.assertEqual(out["races"]["TX"]["new_polls"], 3)

    def test_polls_seen_by_last_mondays_run_are_not_new(self):
        p = polls_table({"NC": 3}, stamp="2026-10-12 09:07")  # in last Monday's average already
        out = weekly.trend({"date": "2026-10-19", "snapshot": "2026-10-19 09:07", "races": {"NC": race(0.0, 12.0)}},
                           self.BEFORE | {"races": {"NC": race(5.0, 6.0)}}, p)
        self.assertEqual((out["races"], out["new_polls"]), ({}, {}))

    def test_the_generic_ballot_is_not_a_state(self):
        p = polls_table({"US": 5, "NC": 3})
        out = weekly.trend({"date": "2026-10-19", "races": {"NC": race(0.0, 12.0)}},
                           self.BEFORE | {"races": {"NC": race(5.0, 6.0)}}, p)
        self.assertEqual(sorted(out["races"]), ["NC"])
        self.assertNotIn("US", out["new_polls"])

    def test_flagged_rows_carry_what_the_analysis_starts_from(self):
        mv = [{"event_id": "NC-1", "card": "A story.", "delta": -3.1}]
        before = {"NC": race(5.0, 6.0, stats=5.2, effect=0.4)}
        now = {"NC": race(1.0, 9.0, stats=7.0, effect=-3.2, movers=mv)}
        r = self.check(before, now, {"NC": 3})["races"]["NC"]
        self.assertEqual(r["forecast"], {"before": 5.0, "now": 1.0, "change": -4.0})
        self.assertEqual(r["poll_avg"], {"before": 6.0, "now": 9.0, "change": 3.0})
        self.assertEqual(r["stats_only_change"], 1.8)  # the statistics moved with the polls
        self.assertEqual(r["news_change"], -3.6)  # the stories moved it the other way
        self.assertEqual(r["movers"], mv)
        ok = self.check(before, {"NC": race(6.0, 9.0, movers=mv)}, {"NC": 3})["races"]["NC"]
        self.assertNotIn("movers", ok)

    def test_no_forecast_a_week_ago(self):
        out = weekly.trend({"date": "2026-10-19", "races": {"NC": race(0.0, 12.0)}}, None, polls_table({"NC": 3}))
        self.assertEqual((out["races"], out["flagged"], out["analyse"]), ({}, [], []))
        self.assertIn("no forecast", out["note"])

    def test_a_race_without_a_poll_average_a_week_ago_is_skipped(self):
        out = self.check({"NC": race(5.0, None)}, {"NC": race(0.0, 12.0)}, {"NC": 3})
        self.assertEqual(out["races"]["NC"]["level"], "no poll average a week ago")
        self.assertEqual(out["flagged"], [])

    def test_the_rules_are_written_with_the_result(self):
        out = self.check({}, {}, {})
        self.assertEqual(out["rules"], {"min_new_polls": 3, "flag_over": 4.0, "analyse_over": 6.0,
                                        "far_over": 15.0, "far_min_polls": 3,
                                        "rollback": "none: only what the analysis finds wrong is fixed, as a logged "
                                                    "change with both versions scored"})
        self.assertEqual((out["since"], out["since_snapshot"]), ("2026-10-12", "2026-10-12 09:07"))


class FarFromPollsTest(unittest.TestCase):
    """The level check (Matteo, 12 Oct): a 3 Nov margin more than 15 points from the poll average, 3+ polls."""
    def test_races_far_from_their_poll_average(self):
        races = {"NC": race(1.0, 17.0), "TX": race(0.0, 20.0), "OH-S": race(0.0, -15.0),
                 "AK-AL": race(-35.56, -73.58) | {"office": "house"}, "IA": race(0.0, None)}
        out = weekly.far_from_polls(races, {"NC": 3, "TX": 2, "OH-S": 9, "AK-AL": 6, "IA": 5})
        self.assertEqual(sorted(out), ["AK-AL", "NC"])  # TX: 2 polls; OH-S: 15, not over; IA: no average
        self.assertEqual(out["NC"], {"office": "senate", "forecast": 1.0, "poll_avg": 17.0, "gap": 16.0, "polls": 3})
        self.assertEqual((out["AK-AL"]["office"], out["AK-AL"]["gap"]), ("house", 38.02))


class HouseViewTest(unittest.TestCase):
    def test_house_seats_in_the_forecasts_race_shape(self):
        f = {"house": {"races": {"AK-AL": {"p_dem_win": 0.02, "margin": {"p10": -18.7, "p50": -11.89, "p90": -5.0}},
                                 "NY-21": {"p_dem_win": 0.1, "margin": {"p50": -9.3}}}}}
        lv = {"races": {"AK-AL": {"margin": -12.4441, "poll_margin": -12.6238}}}
        v = weekly.house_view(f, lv)
        self.assertEqual(v, {"AK-AL": {"office": "house", "margin": {"p10": -18.7, "p50": -11.89, "p90": -5.0},
                                       "stats_only": {"margin": {"p50": -12.44}}, "benchmarks": {"poll_avg": -12.62}}})
        lv["races"]["AK-AL"]["poll_margin"] = None
        self.assertIsNone(weekly.house_view(f, lv)["AK-AL"]["benchmarks"]["poll_avg"])
        self.assertEqual((weekly.house_view({"house": None}, lv), weekly.house_view(f, None)), ({}, {}))

def row(p50: float, poll: float | None = None, market: float | None = None, spread: float = 12.8155) -> dict:
    """A forecast.json race row; the default spread makes the market's implied margin 5 times its normal quantile."""
    return {"margin": {"p10": p50 - spread / 2, "p50": p50, "p90": p50 + spread / 2},
            "benchmarks": {"poll_avg": poll, "market": market}}


class CheckTest(unittest.TestCase):
    """The Sunday weekly check (Matteo, 13 Oct, docs/simulation-only.md)."""

    def test_gap_in_any_direction_with_flag_severe_and_cancel(self):
        before = {r: row(0.0, 0.0) for r in ("NC", "TX", "OH-S", "IA", "ME")}
        now = {"NC": row(-2.0, 2.0), "TX": row(5.5, 0.5), "OH-S": row(0.5, 5.0), "IA": row(1.0, 4.0),
               "ME": row(0.0, 7.0)}
        out = weekly.check(now, before, {r: 3 for r in now}, {})
        r = {x["race"]: x for x in out["races"]}
        self.assertEqual((r["NC"]["gap"], r["NC"]["flag"]), (4.0, "flag"))  # opposite moves
        self.assertEqual((r["TX"]["gap"], r["TX"]["flag"]), (5.0, "flag"))  # over-move: 5 is not above 5
        self.assertEqual((r["OH-S"]["gap"], r["OH-S"]["flag"]), (4.5, "flag"))  # under-move
        self.assertEqual((r["IA"]["gap"], r["IA"]["flag"]), (3.0, ""))  # 3 is not above 3
        self.assertEqual((r["ME"]["gap"], r["ME"]["flag"]), (7.0, "cancel"))
        now["TX"] = row(5.6, 0.5)
        self.assertEqual(weekly.check(now, before, {r: 3 for r in now}, {})["severe"], ["TX"])
        self.assertEqual([x["race"] for x in out["races"]][:2], ["ME", "TX"])  # largest gap first
        self.assertEqual((out["flagged"], out["cancel"]), (["TX", "OH-S", "NC"], ["ME"]))

    def test_one_or_two_new_polls_can_only_flag(self):
        out = weekly.check({"ME": row(0.0, 9.0)}, {"ME": row(0.0, 0.0)}, {"ME": 2}, {})
        self.assertEqual((out["races"][0]["gap"], out["races"][0]["flag"]), (9.0, "flag"))

    def test_no_new_polls_compares_with_the_markets_and_only_flags(self):
        out = weekly.check({"NC": row(0.0, 1.0, 0.9)}, {"NC": row(0.0, 1.0, 0.5)}, {}, {})
        x = out["races"][0]
        self.assertEqual((x["basis"], x["polls"], x["n_polls"], x["flag"]), ("markets", 0.0, 0, "flag"))
        self.assertAlmostEqual(x["markets"], 6.41, places=2)  # 5 x the normal quantile of 0.9
        self.assertAlmostEqual(weekly.implied(0.5, row(3.0)), 0.0)

    def test_no_polls_and_no_market_is_not_checked(self):
        out = weekly.check({"PA-7": row(1.0)}, {"PA-7": row(0.0)}, {}, {})
        self.assertEqual((out["races"][0]["basis"], out["races"][0]["gap"], out["no_check"]), (None, None, ["PA-7"]))

    def test_rows_carry_the_stories_and_a_cancelled_week(self):
        stories = {"NC": [{"event_id": "e1"}], "US": [{"event_id": "n1"}]}
        before, now = {r: row(0.0, 0.0) for r in ("NC", "TX", "IA")}, {"NC": row(-2.0, 2.0), "TX": row(4.0, 0.0),
                                                                        "IA": row(0.0, 0.0)}
        out = weekly.check(now, before, {r: 3 for r in now}, stories, cancelled={"TX"})
        r = {x["race"]: x for x in out["races"]}
        self.assertEqual((r["NC"]["stories"], r["TX"]["stories"], r["IA"]["stories"]),
                         ([{"event_id": "e1"}], [{"event_id": "n1"}], []))  # the nation's only when flagged
        self.assertEqual((r["TX"]["flag"], out["cancelled"], r["TX"]["what_we_did"]), ("cancelled", ["TX"], ""))
        self.assertEqual(weekly.check_summary(out | {"far_from_polls": {"AK": {}}}),
                         {"flagged": ["NC"], "severe": [], "cancel": [], "cancelled": ["TX"], "far_from_polls": ["AK"]})

    def test_week_stories_are_the_weeks_largest(self):
        ev = lambda first, eff: {"first_seen": first, "election_day": eff, "card": "c"}
        m = {"NC": {"events": {"a": ev("2026-10-10", 3.0), "b": ev("2026-10-13", -0.2), "c": ev("2026-10-15", 0.5)}},
             "shadow": {"NC": {"events": {"z": ev("2026-10-15", 9.0)}}}, "date": "2026-10-18"}
        out = weekly.week_stories(m, "2026-10-11")
        self.assertEqual([x["event_id"] for x in out["NC"]], ["c", "b"])
        self.assertEqual(out["NC"][0], {"event_id": "c", "card": "c", "first_seen": "2026-10-15", "delta": 0.5})



if __name__ == "__main__":
    unittest.main()
