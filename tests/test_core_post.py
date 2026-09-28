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


if __name__ == "__main__":
    unittest.main()
