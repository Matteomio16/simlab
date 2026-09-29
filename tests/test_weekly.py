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


def story(first, full_s, h_age=None, h_after=None, full_t=0.0, scope="race"):
    return {"first_seen": first, "last_seen": first, "full_s_base": full_s, "full_t_base": full_t,
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


if __name__ == "__main__":
    unittest.main()
