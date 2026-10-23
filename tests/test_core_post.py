import unittest
from unittest import mock

import requests

from simlab import core


class FakeResponse:
    status_code = 200

    def json(self):
        return {"choices": [{"message": {"content": "{}"}}]}


class Post(unittest.TestCase):
    def test_connection_dropped_mid_reply_is_retried(self):
        calls = []

        def post(*a, **k):
            calls.append(1)
            if len(calls) == 1:
                raise requests.exceptions.ChunkedEncodingError("Connection broken")
            return FakeResponse()
        with mock.patch.object(core.requests, "post", post), mock.patch.object(core.time, "sleep", lambda s: None):
            out = core._post("https://example.invalid", {}, {})
        self.assertEqual(len(calls), 2)
        self.assertIn("choices", out)

    def test_attempts_are_recorded_and_backoff_is_capped_at_30_seconds(self):
        class Busy(FakeResponse):
            status_code, text = 429, "rate limited"
        seq, sleeps = iter([Busy()] * 6 + [requests.Timeout()]), []

        def post(*a, **k):
            r = next(seq, FakeResponse())
            if isinstance(r, Exception):
                raise r
            return r
        info = {}
        with mock.patch.object(core.requests, "post", post), mock.patch.object(core.time, "sleep", sleeps.append), \
                mock.patch.object(core.random, "random", lambda: 0.0):
            core._post("https://example.invalid", {}, {}, info=info)
        self.assertEqual(info["attempts"], [429] * 6 + ["timeout", 200])
        self.assertEqual(sleeps, [1, 2, 4, 8, 16, 30, 30])
        self.assertIn("seconds", info)


if __name__ == "__main__":
    unittest.main()
