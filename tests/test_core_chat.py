import tempfile
import unittest
from pathlib import Path
from unittest import mock

from simlab import core


def reply(text):
    return {"choices": [{"message": {"content": text}}], "usage": {"cost": 0.0}}


class Complete(unittest.TestCase):
    # 1 Oct: GLM's hosts count its compulsory reasoning against max_tokens, and the fallback host sometimes returns
    # nothing but reasoning; 7% of the day's GLM reaction rows were unreadable
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = core.Cache(Path(self.tmp.name) / "c.sqlite")
        self.cache = mock.patch.object(core, "CACHE", self.db)
        self.cache.start()

    def tearDown(self):
        self.cache.stop()
        self.db.db.close()
        self.tmp.cleanup()

    def test_a_reasoning_model_gets_room_for_its_reasoning(self):
        sent = []
        with mock.patch.object(core, "_post", lambda url, payload, headers: sent.append(payload) or reply('{"a": 1}')), \
                mock.patch.object(core.Ledger, "add", lambda *a: None), mock.patch.object(core.Ledger, "check", lambda: None):
            core.Chat("z/glm", ["H"], reasoning={"effort": "minimal"}).complete([], max_tokens=70)
            core.Chat("z/other", ["H"]).complete([], max_tokens=70)
        self.assertEqual([p["max_tokens"] for p in sent], [70 + core.REASONING_ROOM, 70])

    def test_an_empty_reply_is_asked_again_and_never_cached(self):
        replies = iter(["", "  ", '{"q1": [1, 2]}'])
        chat = core.Chat("z/glm", ["H"], reasoning={"effort": "minimal"})
        with mock.patch.object(core, "_post", lambda *a: reply(next(replies))), \
                mock.patch.object(core.Ledger, "add", lambda *a: None), mock.patch.object(core.Ledger, "check", lambda: None):
            self.assertEqual(chat.complete([{"role": "user", "content": "x"}]), '{"q1": [1, 2]}')
            self.assertEqual(chat.complete([{"role": "user", "content": "x"}]), '{"q1": [1, 2]}')  # from the cache

    def test_three_empty_replies_give_an_empty_answer_that_is_asked_again_next_time(self):
        calls = []
        chat = core.Chat("z/glm", ["H"], reasoning={"effort": "minimal"})
        with mock.patch.object(core, "_post", lambda *a: calls.append(1) or reply("")), \
                mock.patch.object(core.Ledger, "add", lambda *a: None), mock.patch.object(core.Ledger, "check", lambda: None):
            self.assertEqual(chat.complete([]), "")
            chat.complete([])
        self.assertEqual(len(calls), 6)


if __name__ == "__main__":
    unittest.main()
