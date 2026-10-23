import json
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
        self.log = mock.patch.object(core.CallLog, "path", Path(self.tmp.name) / "calls.jsonl")
        self.log.start()

    def tearDown(self):
        self.log.stop()
        self.cache.stop()
        self.db.db.close()
        self.tmp.cleanup()

    def test_a_reasoning_model_gets_room_for_its_reasoning(self):
        sent = []
        with mock.patch.object(core, "_post", lambda url, payload, headers, **k: sent.append(payload) or reply('{"a": 1}')), \
                mock.patch.object(core.Ledger, "add", lambda *a: None), mock.patch.object(core.Ledger, "check", lambda: None):
            core.Chat("z/glm", ["H"], reasoning={"effort": "minimal"}).complete([], max_tokens=70)
            core.Chat("z/other", ["H"]).complete([], max_tokens=70)
        self.assertEqual([p["max_tokens"] for p in sent], [70 + core.REASONING_ROOM, 70])

    def test_an_empty_reply_is_asked_again_and_never_cached(self):
        replies = iter(["", "  ", '{"q1": [1, 2]}'])
        chat = core.Chat("z/glm", ["H"], reasoning={"effort": "minimal"})
        with mock.patch.object(core, "_post", lambda *a, **k: reply(next(replies))), \
                mock.patch.object(core.Ledger, "add", lambda *a: None), mock.patch.object(core.Ledger, "check", lambda: None):
            self.assertEqual(chat.complete([{"role": "user", "content": "x"}]), '{"q1": [1, 2]}')
            self.assertEqual(chat.complete([{"role": "user", "content": "x"}]), '{"q1": [1, 2]}')  # from the cache

    def test_three_empty_replies_give_an_empty_answer_that_is_asked_again_next_time(self):
        calls = []
        chat = core.Chat("z/glm", ["H"], reasoning={"effort": "minimal"})
        with mock.patch.object(core, "_post", lambda *a, **k: calls.append(1) or reply("")), \
                mock.patch.object(core.Ledger, "add", lambda *a: None), mock.patch.object(core.Ledger, "check", lambda: None):
            self.assertEqual(chat.complete([]), "")
            chat.complete([])
        self.assertEqual(len(calls), 6)

    def test_every_call_is_logged_with_its_host_tokens_and_attempts_and_a_cache_hit_as_a_hit(self):
        def post(url, payload, headers, **k):
            k["info"].update(attempts=[429, 200], seconds=1.5)
            self.assertEqual(k["timeout"], core.CHAT_TIMEOUT_S)
            return {"choices": [{"message": {"content": '{"q1": [1]}'}}], "provider": "InferenceNet",
                    "usage": {"prompt_tokens": 270, "completion_tokens": 36, "cost": 4.7e-05,
                              "completion_tokens_details": {"reasoning_tokens": 16}}}
        chat = core.Chat("z/glm", ["H"], reasoning={"effort": "minimal"})
        with mock.patch.object(core, "_post", post), mock.patch.object(core.Ledger, "add", lambda *a: None), \
                mock.patch.object(core.Ledger, "check", lambda: None):
            chat.complete([{"role": "user", "content": "x"}], tag="harness:glm")
            chat.complete([{"role": "user", "content": "x"}], tag="harness:glm")
        first, hit = [json.loads(l) for l in core.CallLog.path.read_text().splitlines()]
        self.assertEqual({k: first[k] for k in ("model", "tag", "cached", "provider", "in", "out", "reasoning", "usd",
                                                 "attempts", "seconds")},
                         {"model": "z/glm", "tag": "harness:glm", "cached": False, "provider": "InferenceNet", "in": 270,
                          "out": 36, "reasoning": 16, "usd": 4.7e-05, "attempts": [429, 200], "seconds": 1.5})
        self.assertEqual((hit["cached"], "provider" in hit), (True, False))
        self.assertNotIn("x", json.dumps(first) + json.dumps(hit))  # no prompt text in the log


class GlmHosts(unittest.TestCase):
    # 20 Oct: OpenInference reasoned at length (7 s, billed at max_tokens, turnout answers 0.2 higher)
    def test_glm_asks_inferencenet_then_sail_then_deepinfra_and_never_openinference(self):
        hosts = ["InferenceNet", "Sail Research", "DeepInfra"]
        self.assertEqual(core.HOSTS["glm"], hosts)
        sent = []
        with mock.patch.object(core, "_post", lambda url, payload, headers, **k: sent.append(payload) or reply("{}")), \
                mock.patch.object(core.CACHE, "get", lambda k: None), mock.patch.object(core.CACHE, "put", lambda *a: None), \
                mock.patch.object(core.CallLog, "add", lambda *a, **k: None), \
                mock.patch.object(core.Ledger, "add", lambda *a: None), mock.patch.object(core.Ledger, "check", lambda: None):
            core.Chat(core.LLMS["glm"], core.HOSTS["glm"], reasoning=core.REASONING["glm"]).complete([])
        self.assertEqual(sent[0]["provider"], {"order": hosts, "only": hosts})


if __name__ == "__main__":
    unittest.main()
