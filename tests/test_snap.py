import json
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

from simlab import snap


CFG = json.loads((Path(snap.__file__).with_name("newsraces.json")).read_text(encoding="utf-8"))


class FakeRun:
    when = datetime(2026, 10, 12, 8, 0, tzinfo=timezone.utc)

    def __init__(self):
        self.saved, self.errors = [], []

    def save(self, source, name, url, fetch):
        self.saved.append((name, fetch()[0]))

    def error(self, source, name, url, message, fetched_at=None):
        self.errors.append(name)


def reply(status):
    class Resp:
        status_code, content = status, b'{"stories": []}'
    return Resp()


class MediaCloud(unittest.TestCase):
    def test_every_race_in_the_race_file_is_asked_once(self):
        queries, run = [], FakeRun()

        def get(url, params=None, headers=None, timeout=None):
            queries.append(params["q"])
            return reply(200)
        with mock.patch.object(snap.requests, "get", get), mock.patch.object(snap.time, "sleep", lambda s: None):
            snap.mediacloud(run, "key")
        names = [n for n, _ in run.saved]
        self.assertEqual(len(names), len(CFG))
        self.assertIn("mediacloud-ohio", names)
        self.assertIn("mediacloud-national", names)
        self.assertIn("mediacloud-ga", names)
        self.assertIn(CFG["GA"]["mediacloud"], queries)

    def test_a_rate_limit_backs_off_once_then_skips_the_rest(self):
        run, sleeps = FakeRun(), []
        with mock.patch.object(snap.requests, "get", lambda *a, **k: reply(429)), \
                mock.patch.object(snap.time, "sleep", sleeps.append):
            snap.mediacloud(run, "key")
        self.assertEqual(run.saved, [(run.saved[0][0], 429)])
        self.assertEqual(len(run.errors), len(CFG) - 1)
        self.assertEqual(sleeps.count(30), 1)

    def test_past_its_budget_every_race_is_recorded_as_skipped(self):
        run = FakeRun()
        with mock.patch.object(snap, "MEDIACLOUD_BUDGET_S", 0), \
                mock.patch.object(snap.requests, "get", lambda *a, **k: reply(200)):
            snap.mediacloud(run, "key")
        self.assertEqual((len(run.saved), len(run.errors)), (0, len(CFG)))


if __name__ == "__main__":
    unittest.main()
