import unittest
from datetime import datetime, timedelta, timezone

from simlab import snap


class GdeltOrder(unittest.TestCase):
    def test_each_run_starts_one_query_later(self):
        # GDELT tends to answer the first query of a run and rate-limit the rest (28-29 Sep): no race is always last
        t = datetime(2026, 9, 29, 0, 17, tzinfo=timezone.utc)
        firsts = [snap.gdelt_order(t + timedelta(hours=3 * k))[0] for k in range(len(snap.NEWS))]
        self.assertEqual(sorted(firsts), sorted(snap.NEWS))
        self.assertEqual(sorted(snap.gdelt_order(t)), sorted(snap.NEWS))


if __name__ == "__main__":
    unittest.main()
