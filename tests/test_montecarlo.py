import unittest
from datetime import date

import numpy as np

from simlab import montecarlo as mc
from simlab.polls import Race

PARAMS = {"mc": {"regional_sd": 1.0, "state_sd": 2.0}}

PREDICTIONS = """== Predictions ==
{| class="wikitable sortable"
|-
! State
|-
! [[2026 United States Senate election in Alabama|Alabama]]
| {{Shading PVI|R|15}}
<!--Cook-->      | {{USRaceRating|Solid|R}}
<!--DDHQ-->      | {{USRaceRating|Safe|R}}
|-
! [[2026 United States Senate election in North Carolina|North Carolina]]
| {{Shading PVI|R|1}}
<!--Cook-->      | {{USRaceRating|Lean|D|flip}}
<!--DDHQ-->      | {{USRaceRating|Tossup}}
|-
! [[2026 United States Senate special election in Ohio|Ohio]]<br />{{small|(special)}}
| {{Shading PVI|R|5}}
<!--Cook-->      | {{USRaceRating|Tossup}}
|}

== Generic congressional ballot aggregate polls ==
"""


def kalshi_market(ticker, name, bid, ask):
    return {"ticker": ticker, "yes_sub_title": name, "yes_bid_dollars": bid, "yes_ask_dollars": ask, "status": "active"}


KALSHI = {
    "SENATENC": {"events": [
        {"event_ticker": "SENATENC-26", "markets": [
            kalshi_market("SENATENC-26-R", "Michael Whatley", "0.0640", "0.0670"),
            kalshi_market("SENATENC-26-D", "Roy Cooper", "0.9350", "0.9370")]},
        {"event_ticker": "SENATENC-28", "markets": [
            kalshi_market("SENATENC-28-D", "Democratic party", "0.5700", "0.6600")]}]},
    "SENATENE": {"events": [
        {"event_ticker": "SENATENE-26", "markets": [
            kalshi_market("SENATENE-26-R", "Pete Ricketts", "0.6900", "0.7000"),
            kalshi_market("SENATENE-26-D", "Cindy Burbank", "0.0000", "0.0050"),
            kalshi_market("SENATENE-26-DOSB", "Dan Osborn", "0.2900", "0.3000")]}]},
    "SENATEAK": {"events": [
        {"event_ticker": "SENATEAK-26", "markets": [
            kalshi_market("SENATEAK-26-R", "Republican party", "0.3000", "0.3100"),
            kalshi_market("SENATEAK-26-D", "Democratic party", "0.7000", "0.7100")]}]},
}


def poly_market(title, bid, ask, active=True):
    return {"groupItemTitle": title, "bestBid": bid, "bestAsk": ask, "active": active, "closed": False}


POLY = {
    "north-carolina-senate-election-winner": [{"markets": [
        poly_market("Roy Cooper (D)", 0.95, 0.96), poly_market("Michael Whatley (R)", 0.05, 0.06),
        poly_market("Person A", 0, 1, active=False)]}],
    "nebraska-senate-election-winner": [{"markets": [
        poly_market("Democrat", None, 0.002), poly_market("Pete Ricketts (R)", 0.69, 0.7),
        poly_market("Independent", 0.3, 0.31)]}],
    "alaska-senate-election-winner": [{"markets": [
        poly_market("Sen. Dan Sullivan", 0.28, 0.29), poly_market("Mary Peltola", 0.72, 0.73),
        poly_market("Ann Diener", None, 0.001)]}],
}

NC = Race("NC", False, "Michael Whatley", "Roy Cooper", "D", "2026 United States Senate election in North Carolina")
NE = Race("NE", False, "Pete Ricketts", "Dan Osborn", "I", "2026 United States Senate election in Nebraska")
AK = Race("AK", False, "Dan S. Sullivan", "Mary Peltola", "D", "2026 United States Senate election in Alaska")
OH = Race("OH", True, "Jon Husted", "Sherrod Brown", "D", "2026 United States Senate special election in Ohio")


def levels(nc=2.0, poll=3.0):
    return {"national": {"var": 9.0},
            "races": {"NC": {"margin": nc, "sd": 5.0, "w_polls": 0.6, "poll_margin": poll},
                      "OH-S": {"margin": -1.0, "sd": 5.5, "w_polls": 0.5, "poll_margin": 0.5},
                      "NE": {"margin": -6.0, "sd": 7.0, "w_polls": 0.0, "poll_margin": None}}}


class StructureTest(unittest.TestCase):
    def test_state_from_race_id(self):
        self.assertEqual([mc.state_of(r) for r in ("NC", "OH-S", "TX-28", "AK-AL")], ["NC", "OH", "TX", "AK"])

    def test_shared_error_by_nation_division_and_state(self):
        c = mc.structure(["TX", "TX-28", "OK", "NC"], np.array([5.0, 6.0, 7.0, 8.0]), 9.0, 1.0, 2.0)
        np.testing.assert_allclose(np.diag(c), 1.0)
        self.assertAlmostEqual(c[0, 1], 14 / 30)
        self.assertAlmostEqual(c[0, 2], 10 / 35)
        self.assertAlmostEqual(c[0, 3], 9 / 40)
        self.assertAlmostEqual(c[2, 3], 9 / 56)


class FloorTest(unittest.TestCase):
    def test_lifts_low_pairs_and_keeps_the_rest(self):
        c = np.array([[1, 0.5, 0.18], [0.5, 1, 0.3], [0.18, 0.3, 1]])
        out, lifted = mc.floor(c, 0.25)
        self.assertEqual(lifted, 1)
        np.testing.assert_allclose(out, [[1, 0.5, 0.25], [0.5, 1, 0.3], [0.25, 0.3, 1]], atol=1e-9)

    def test_projects_to_a_valid_matrix_above_the_floor(self):
        c = np.array([[1, 0.99, 0.1], [0.99, 1, 0.99], [0.1, 0.99, 1]])
        out, lifted = mc.floor(c, 0.25)
        self.assertEqual(lifted, 1)
        np.testing.assert_allclose(np.diag(out), 1.0, atol=1e-9)
        np.testing.assert_allclose(out, out.T)
        self.assertGreaterEqual(np.linalg.eigvalsh(out).min(), -1e-9)
        self.assertGreaterEqual(out[~np.eye(3, dtype=bool)].min(), 0.25 - 1e-6)

    def test_untouched_when_all_pairs_clear_the_floor(self):
        c = np.array([[1, 0.4], [0.4, 1]])
        out, lifted = mc.floor(c, 0.25)
        self.assertEqual(lifted, 0)
        np.testing.assert_array_equal(out, c)


class DrawTest(unittest.TestCase):
    def setUp(self):
        self.mu, self.sd = np.array([1.0, -2.0]), np.array([4.0, 6.0])
        self.x = mc.draw(self.mu, self.sd, np.array([[1, 0.5], [0.5, 1]]), 40000, seed=7)

    def test_keeps_means_sds_and_correlation(self):
        self.assertEqual(self.x.shape, (40000, 2))
        np.testing.assert_allclose(self.x.mean(axis=0), self.mu, atol=0.15)
        np.testing.assert_allclose(self.x.std(axis=0), self.sd, rtol=0.03)
        self.assertAlmostEqual(np.corrcoef(self.x.T)[0, 1], 0.5, delta=0.02)

    def test_tails_fatter_than_normal(self):
        z = (self.x[:, 0] - self.mu[0]) / self.sd[0]
        self.assertGreater(np.mean(np.abs(z) > 3), 0.005)

    def test_one_shared_scale_per_draw(self):
        x = mc.draw(np.zeros(2), np.ones(2), np.eye(2), 40000, seed=3)
        self.assertGreater(np.corrcoef(np.abs(x.T))[0, 1], 0.06)

    def test_same_seed_same_draws(self):
        c = np.array([[1, 0.5], [0.5, 1]])
        np.testing.assert_array_equal(mc.draw(self.mu, self.sd, c, 500, seed=7), mc.draw(self.mu, self.sd, c, 500, seed=7))
        self.assertFalse(np.array_equal(mc.draw(self.mu, self.sd, c, 500, seed=7),
                                        mc.draw(self.mu, self.sd, c, 500, seed=8)))

    def test_seed_from_run_date(self):
        self.assertEqual(mc.seed_for(date(2026, 9, 28)), 20260928)


class SummaryTest(unittest.TestCase):
    def test_race_summary(self):
        s = mc.race_summary(np.array([-1.0, 0.5, 2.0, 3.0]))
        self.assertEqual(s["p_dem_win"], 0.75)
        self.assertAlmostEqual(s["margin"]["p10"], -0.55)
        self.assertAlmostEqual(s["margin"]["p50"], 1.25)
        self.assertAlmostEqual(s["margin"]["p90"], 2.7)

    def test_senate_seats_and_control(self):
        x = np.array([[1.0, 1.0, 1.0], [-1.0, -1.0, 1.0], [-1.0, -1.0, -1.0]])
        seats = mc.senate_seats(x, ["D", "D", "I"], {"R": 48, "D": 47, "I": 2})
        np.testing.assert_array_equal(seats["R"], [48, 50, 51])
        np.testing.assert_array_equal(seats["D"], [49, 47, 47])
        np.testing.assert_array_equal(seats["I"], [3, 3, 2])
        s = mc.senate_summary(seats, {"R": 48, "D": 47, "I": 2})
        self.assertAlmostEqual(s["p_r_50plus"], 2 / 3, places=4)
        self.assertAlmostEqual(s["p_d_caucus_51"], 1 / 3, places=4)


class BenchmarkTest(unittest.TestCase):
    def test_cook_ratings_from_the_predictions_table(self):
        self.assertEqual(mc.cook(PREDICTIONS), {"AL": "Solid R", "NC": "Lean D", "OH-S": "Tossup"})

    def test_market_averages_venues_on_the_challenger_side(self):
        p, venues = mc.market(KALSHI, POLY, NC)
        self.assertAlmostEqual(venues["kalshi"], 0.936 / 1.0015, places=4)
        self.assertAlmostEqual(venues["polymarket"], 0.955 / 1.01, places=4)
        self.assertAlmostEqual(p, (0.936 / 1.0015 + 0.955 / 1.01) / 2, places=4)

    def test_market_finds_independents_and_party_level_markets(self):
        p, venues = mc.market(KALSHI, POLY, NE)
        self.assertAlmostEqual(venues["kalshi"], 0.295 / 0.9925, places=4)
        self.assertAlmostEqual(venues["polymarket"], 0.305 / 1.001, places=4)
        p, venues = mc.market(KALSHI, POLY, AK)
        self.assertAlmostEqual(venues["kalshi"], 0.705 / 1.01, places=4)
        self.assertAlmostEqual(venues["polymarket"], 0.725 / 1.0105, places=4)

    def test_no_market(self):
        self.assertEqual(mc.market(KALSHI, POLY, OH), (None, {}))

    def test_senate_control_market(self):
        k = {"CONTROLS": {"events": [
            {"event_ticker": "CONTROLS-2026", "markets": [
                kalshi_market("CONTROLS-2026-D", "Democratic Party", "0.6100", "0.6200"),
                kalshi_market("CONTROLS-2026-R", "Republican Party", "0.3800", "0.3900")]},
            {"event_ticker": "CONTROLS-2028", "markets": [
                kalshi_market("CONTROLS-2028-R", "Republican party", "0.4300", "0.4900")]}]}}
        p = {"which-party-will-win-the-senate-in-2026": [{"markets": [
            poly_market("Democratic Party", 0.62, 0.63), poly_market("Republican Party", 0.37, 0.38)]}]}
        r, venues = mc.control_market(k, p, "senate")
        self.assertEqual(venues, {"kalshi": 0.385, "polymarket": 0.375})
        self.assertAlmostEqual(r, 0.38, places=4)


class BuildTest(unittest.TestCase):
    def build(self, twin=None, movers=None):
        return mc.build(levels(), twin or levels(), {"NC": "D", "OH-S": "D", "NE": "I"}, PARAMS, date(2026, 9, 28),
                        "run-1", benchmarks={"NC": {"market": 0.9, "cook": "Lean D"}, "US-S": {"market": 0.38}},
                        not_up={"R": 48, "D": 47, "I": 2}, n=4000, movers=movers)

    def test_forecast_and_draws_follow_the_contract(self):
        f, d = self.build()
        self.assertEqual((f["date"], f["run_id"], f["schema"], f["house"]), ("2026-09-28", "run-1", 1, None))
        nc = f["races"]["NC"]
        self.assertTrue(0.6 < nc["p_dem_win"] < 0.75)
        self.assertLess(nc["margin"]["p10"], nc["margin"]["p50"])
        self.assertLess(nc["margin"]["p50"], nc["margin"]["p90"])
        self.assertEqual(nc["stats_only"], {"p_dem_win": nc["p_dem_win"], "margin": nc["margin"]})
        self.assertEqual(nc["benchmarks"], {"poll_avg": 3.0, "market": 0.9, "cook": "Lean D"})
        self.assertEqual(f["races"]["NE"]["benchmarks"], {"poll_avg": None, "market": None, "cook": None})
        self.assertEqual((nc["movers"], f["races"]["NE"]["left_party"]), ([], "I"))
        self.assertIn("p_r_50plus", f["senate"])
        self.assertEqual(f["senate"]["benchmarks"], {"market": 0.38})
        self.assertEqual(len(d["races"]["NC"]), 100)
        self.assertEqual(len(d["seats"]["senate"]["R"]), 100)
        self.assertEqual(len(d["stats_only"]["races"]["NC"]), 100)

    def test_rerun_is_identical(self):
        self.assertEqual(self.build(), self.build())

    def test_poll_average_benchmark_comes_from_the_stats_only_twin(self):
        f, _ = self.build(twin=levels(poll=1.0))
        self.assertEqual(f["races"]["NC"]["benchmarks"]["poll_avg"], 1.0)

    def test_movers_passed_through(self):
        mv = {"NC": [{"event_id": "e1", "card": "A story", "delta": 0.4}]}
        f, _ = self.build(movers=mv)
        self.assertEqual((f["races"]["NC"]["movers"], f["races"]["NE"]["movers"]), (mv["NC"], []))

    def test_news_size_uncertainty_and_the_sensitivity_map(self):
        news = {"switching": {"NC": 2.0}, "turnout": {"NC": 1.0}, "sigma": {"s": 0.5, "t": 0.75}}
        run = lambda: mc.build(levels(nc=5.0), levels(nc=2.0), {"NC": "D", "OH-S": "D", "NE": "I"}, PARAMS,
                               date(2026, 9, 28), "run-1", not_up={"R": 48, "D": 47, "I": 2}, n=20000, news=news)
        f, d = run()
        nc, oh = f["races"]["NC"], f["races"]["OH-S"]
        spread = lambda m: m["p90"] - m["p10"]
        self.assertGreater(spread(nc["margin"]), spread(nc["stats_only"]["margin"]) + 0.2)
        self.assertAlmostEqual(nc["margin"]["p50"], 5.0, delta=0.4)
        self.assertEqual((oh["p_dem_win"], oh["margin"]), (oh["stats_only"]["p_dem_win"], oh["stats_only"]["margin"]))
        s = nc["news"]
        self.assertEqual((s["effect"], s["switching"], s["turnout"]), (3.0, 2.0, 1.0))
        self.assertLess(s["if_weaker"]["p_dem_win"], nc["p_dem_win"])
        self.assertGreater(s["if_stronger"]["p_dem_win"], nc["p_dem_win"])
        self.assertAlmostEqual(s["if_weaker"]["multipliers"]["s"], float(np.exp(-1.2816 * 0.5 - 0.5 ** 2 / 2)), places=3)
        self.assertIn("if_stronger", f["senate"]["news"])
        self.assertEqual(f["news_prior"], {"sigma": {"s": 0.5, "t": 0.75}})
        self.assertEqual(run(), (f, d))

    def test_stats_only_twin_uses_its_own_levels(self):
        f, _ = self.build(twin=levels(nc=-2.0))
        nc = f["races"]["NC"]
        self.assertLess(nc["stats_only"]["p_dem_win"], nc["p_dem_win"])


if __name__ == "__main__":
    unittest.main()
