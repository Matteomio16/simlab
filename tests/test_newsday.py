import gzip
import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

from simlab import newsday

def gdelt(*arts) -> str:
    return json.dumps({"articles": [{"url": f"https://{d}/{t[:24]}", "title": t, "seendate": s, "domain": d}
                                    for t, s, d in arts]})


OHIO = gdelt(("Brown and Husted clash over tariffs", "20260928T080000Z", "cleveland.com"),
             ("Crypto PAC to spend $30M against Sherrod Brown", "20260928T070000Z", "politico.com"))
TEXAS = gdelt(("Talarico , Paxton trade attacks", "20260928T090000Z", "example.com"))


def snapshot(root: Path, day: str, hhmm: str, files: dict) -> None:
    run = root / day / hhmm
    entries = []
    for name, body in files.items():
        path = run / "news" / f"{name}.gz"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(gzip.compress(body.encode(), mtime=0))
        entries.append({"source": "news", "name": name, "file": f"news/{name}.gz"})
    entries.append({"source": "news", "name": "gdelt-north-carolina", "error": "HTTP 429"})
    (run / "manifest.json").write_text(json.dumps({"files": entries}), encoding="utf-8")


class ReadDay(unittest.TestCase):
    def test_parses_dedupes_and_cleans(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            snapshot(root, "2026-09-28", "0036", {"gdelt-ohio": OHIO})
            snapshot(root, "2026-09-28", "0341", {"gdelt-ohio": OHIO, "gdelt-texas": TEXAS})
            arts = newsday.read_day(root, date(2026, 9, 28))
        self.assertEqual([a["race_id"] for a in arts], ["OH-S", "OH-S", "TX"])
        oh = {a["title"]: a for a in arts if a["race_id"] == "OH-S"}
        self.assertEqual(oh["Brown and Husted clash over tariffs"]["domain"], "cleveland.com")
        self.assertEqual(oh["Brown and Husted clash over tariffs"]["seen"], "2026-09-28T08:00:00+00:00")
        tx = [a for a in arts if a["race_id"] == "TX"][0]
        self.assertEqual(tx["title"], "Talarico, Paxton trade attacks")
        self.assertEqual(tx["source"], "gdelt")

    def test_google_news_files_are_ignored(self):
        with tempfile.TemporaryDirectory() as tmp:
            snapshot(Path(tmp), "2026-09-28", "0036", {"googlenews-ohio": "<rss><channel></channel></rss>"})
            self.assertEqual(newsday.read_day(Path(tmp), date(2026, 9, 28)), [])

    def test_mediacloud_stories(self):
        raw = json.dumps({"stories": [
            {"id": "1", "title": "Brown and Husted clash over tariffs", "url": "https://cleveland.com/a",
             "media_name": "cleveland.com", "media_url": "cleveland.com", "publish_date": "2026-09-28",
             "indexed_date": "2026-09-28T08:15:00", "language": "en"},
            {"id": "2", "title": "No date here at all", "url": "https://x.com/b", "media_name": "x.com"}]})
        arts = newsday.parse_mediacloud(raw.encode(), "OH-S")
        self.assertEqual(len(arts), 1)
        self.assertEqual((arts[0]["source"], arts[0]["domain"], arts[0]["seen"]),
                         ("mediacloud", "cleveland.com", "2026-09-28T08:15:00+00:00"))

    def test_bad_gdelt_json_is_skipped(self):
        self.assertEqual(newsday.parse_gdelt(b'{"articles": [ {bad', "TX"), [])

    def test_headlines_under_four_words_are_dropped(self):
        stub = OHIO.replace("Brown and Husted clash over tariffs", "GOP-ABC News")
        with tempfile.TemporaryDirectory() as tmp:
            snapshot(Path(tmp), "2026-09-28", "0036", {"gdelt-ohio": stub})
            arts = newsday.read_day(Path(tmp), date(2026, 9, 28))
        self.assertEqual([a["title"] for a in arts], ["Crypto PAC to spend $30M against Sherrod Brown"])


def art(race, title, seen, domain="a.com", outlet="A"):
    return {"race_id": race, "title": title, "url": f"https://{domain}/{title[:24]}", "outlet": outlet,
            "domain": domain, "seen": seen, "source": "gdelt"}


class Stories(unittest.TestCase):
    def test_similar_headlines_cluster_and_outlets_count(self):
        arts = [art("OH-S", "Crypto super PAC to spend $30 million against Sherrod Brown", "2026-09-28T07:00:00+00:00",
                    "politico.com", "Politico"),
                art("OH-S", "Crypto super PAC will spend $30 million against Sherrod Brown in Ohio",
                    "2026-09-28T08:00:00+00:00", "axios.com", "Axios"),
                art("OH-S", "Husted visits Dayton factory", "2026-09-28T09:00:00+00:00")]
        stories = newsday.make_stories(arts)
        self.assertEqual(len(stories), 2)
        pac = [s for s in stories if "PAC" in s["title"]][0]
        self.assertEqual(pac["outlets"], ["axios.com", "politico.com"])
        self.assertEqual(pac["first_seen"], "2026-09-28T07:00:00+00:00")

    def test_carry_over_keeps_id_and_first_seen(self):
        s = newsday.make_stories([art("OH-S", "Crypto super PAC to spend $30 million against Sherrod Brown",
                                      "2026-09-29T07:00:00+00:00")])
        known = [{"event_id": "OH-S-20260928-abcdef12", "race_id": "OH-S", "first_seen": "2026-09-28T07:00:00+00:00",
                  "days_seen": ["2026-09-28"], "titles": ["Crypto super PAC to spend $30 million against Sherrod Brown"]}]
        out = newsday.carry_over(s, known)
        self.assertEqual(out[0]["event_id"], "OH-S-20260928-abcdef12")
        self.assertEqual(out[0]["first_seen"], "2026-09-28T07:00:00+00:00")
        self.assertEqual(out[0]["days_seen"], ["2026-09-28", "2026-09-29"])

    def test_new_story_gets_deterministic_id(self):
        s = newsday.carry_over(newsday.make_stories([art("TX", "Paxton sues county", "2026-09-28T10:00:00+00:00")]), [])
        self.assertEqual(s[0]["event_id"], newsday.event_id("TX", "2026-09-28T10:00:00+00:00", "Paxton sues county"))
        self.assertTrue(s[0]["event_id"].startswith("TX-20260928-"))
        self.assertIsNone(s[0]["known"])


class FakeAsker:
    def __init__(self):
        self.states = []

    def ask_many(self, state, questions, tag=""):
        self.states.append(state)
        out = {}
        for qid, q in questions.items():
            if qid == "relevant":
                out[qid] = {"true": 0.8, "false": 0.2}
            elif qid == "salience":
                out[qid] = {"0": 0.0, "1": 0.5, "2": 0.5, "3": 0.0, "4": 0.0}
            elif qid in ("fires_up", "puts_off"):
                out[qid] = {"democrats": 0.6, "republicans": 0.1, "both": 0.2, "neither": 0.1}
            else:
                keys = list(q["criteria"])
                out[qid] = {k: (0.7 if i == 0 else 0.3 / (len(keys) - 1)) for i, k in enumerate(keys)}
        return out


class Labels(unittest.TestCase):
    def story(self, race="OH-S"):
        return {"race_id": race, "title": "Fox News: Brown leads in new ad war",
                "titles": ["Fox News: Brown leads in new ad war"], "outlet_names": ["Fox News"],
                "outlets": ["foxnews.com"]}

    def test_maps_answers_and_hides_outlets(self):
        fake = FakeAsker()
        lab = newsday.label(self.story(), fake)
        self.assertEqual(lab["gate"], {"OH-S": 0.8})
        self.assertEqual(lab["type"], "scandal")
        self.assertEqual(lab["helps_face"], "democrat")
        self.assertEqual(lab["fires_up"], {"D": 0.8, "R": 0.3})
        self.assertAlmostEqual(lab["salience"], 1.5)
        self.assertTrue(all("Fox News" not in s for s in fake.states))
        self.assertIn("- Brown leads in new ad war", fake.states[0])

    def test_national_story_gets_a_gate_per_race(self):
        lab = newsday.label(self.story("US"), FakeAsker())
        self.assertEqual(sorted(lab["gate"]), ["NC", "OH-S", "TX", "US"])


def cov(n, d=1):
    return {"outlets": [f"o{i}.com" for i in range(n)], "days_seen": [f"2026-09-{28 - i}" for i in range(d)],
            "articles": n}


class Attention(unittest.TestCase):
    def test_more_outlets_more_attention_capped(self):
        a1, a7, a40 = (newsday.attention(cov(n), None)["a"] for n in (1, 7, 40))
        self.assertLess(a1, a7)
        self.assertEqual(a40, 1.0)
        self.assertGreater(newsday.attention(cov(1), 3.0)["a"], a1)
        self.assertGreater(newsday.attention(cov(1, 3), None)["a"], a1)

    def test_spike_ratio(self):
        views = {"Sherrod_Brown": {f"202609{d:02d}": 100 for d in range(18, 27)} | {"20260927": 300}}
        self.assertAlmostEqual(newsday.spike_ratio(views, "OH-S"), 3.0)
        self.assertIsNone(newsday.spike_ratio({}, "OH-S"))


class Select(unittest.TestCase):
    def ev(self, eid, scope, gate, a, typ="policy"):
        return {"event_id": eid, "scope": scope, "gate": gate, "type": typ, "salience": 1.0, "attention": {"a": a}}

    def test_gate_poll_rule_and_caps(self):
        evs = [self.ev(f"OH-S-{i}", "race", {"OH-S": 0.9}, a=i / 10) for i in range(7)]
        evs += [self.ev("OH-S-poll", "race", {"OH-S": 0.9}, a=1.0, typ="poll"),
                self.ev("OH-S-weak", "race", {"OH-S": 0.3}, a=1.0),
                self.ev("US-1", "national", {"OH-S": 0.9, "NC": 0.2, "TX": 0.9, "US": 0.9}, a=0.5)]
        newsday.select(evs)
        chosen = sorted(e["event_id"] for e in evs if e["selected"].get("OH-S") and e["scope"] == "race")
        self.assertEqual(chosen, ["OH-S-2", "OH-S-3", "OH-S-4", "OH-S-5", "OH-S-6"])
        self.assertEqual(evs[-1]["selected"], {"OH-S": True, "TX": True, "US": True})


class FakeChat:
    def __init__(self, replies):
        self.replies, self.calls = list(replies), 0

    def complete(self, messages, tag="", max_tokens=300, json_mode=True):
        self.calls += 1
        return self.replies.pop(0) if self.replies else '{"card": ""}'


GOOD = "A crypto industry group plans to spend $30 million opposing Sherrod Brown."


class Cards(unittest.TestCase):
    story = {"race_id": "OH-S", "titles": ["Crypto PAC to spend $30M against Brown"], "outlet_names": ["Politico"]}

    def test_rule_breaking_card_retries_then_falls_back(self):
        bad = FakeChat(['{"card": "Politico reports a crypto PAC will spend $30M."}',
                        '{"card": "A new poll shows Brown ahead."}'])
        good = FakeChat(['{"card": "%s"}' % GOOD])
        self.assertEqual(newsday.write_card(self.story, [bad, good]), GOOD)
        self.assertEqual(bad.calls, 2)

    def test_no_valid_card_gives_empty(self):
        self.assertEqual(newsday.write_card(self.story, [FakeChat(["not json", "{}"])]), "")

    def test_headlines_that_are_not_an_event_get_no_card(self):
        chat = FakeChat(['{"card": "", "event": false}', '{"card": "%s", "event": true}' % GOOD])
        self.assertEqual(newsday.write_card(self.story, [chat]), "")
        self.assertEqual(chat.calls, 1)


class Scopes(unittest.TestCase):
    def test_national_copy_of_a_race_story_does_not_count_twice_for_that_race(self):
        race = {"event_id": "OH-S-1", "scope": "race", "races": ["OH-S"], "gate": {"OH-S": 0.9}}
        nat = {"event_id": "US-1", "scope": "national", "races": ["OH-S", "NC", "TX", "US"],
               "gate": {"OH-S": 0.9, "NC": 0.8, "TX": 0.2, "US": 0.9}}
        stories = {"OH-S-1": {"race_id": "OH-S", "titles": ["Trump to travel to Ohio to stump for Sen. Jon Husted"]},
                   "US-1": {"race_id": "US", "titles": ["Trump to travel to Ohio to stump for Jon Husted"]}}
        newsday.dedupe_scopes([race, nat], stories)
        self.assertEqual(nat["gate"], {"OH-S": 0.0, "NC": 0.8, "TX": 0.2, "US": 0.9})
        self.assertEqual(nat["covered_by"], {"OH-S": "OH-S-1"})
        self.assertEqual(race["gate"], {"OH-S": 0.9})

    def test_same_event_in_other_words_counts_once(self):
        def ev(eid, a):
            return {"event_id": eid, "scope": "race", "races": ["OH-S"], "gate": {"OH-S": 0.9}, "type": "other",
                    "salience": 1.0, "attention": {"a": a}, "first_seen": "2026-09-28T07:00:00+00:00"}
        evs = [ev("OH-S-1", 0.8), ev("OH-S-2", 0.2), ev("OH-S-3", 0.5)]
        stories = {"OH-S-1": {"titles": ["Trump to travel to Ohio to stump for Sen. Jon Husted"], "outlet_names": []},
                   "OH-S-2": {"titles": ["President Donald Trump to visit Ohio as campaign season heats up"],
                              "outlet_names": []},
                   "OH-S-3": {"titles": ["Brown visits Mahoning Valley"], "outlet_names": []}}
        # pairs are checked in attention order against stories already kept: OH-S-3 vs OH-S-1, then OH-S-2 vs OH-S-1
        chat = FakeChat(['{"same": false}', '{"same": true}'])
        newsday.merge_same_events(evs, stories, [chat])
        self.assertEqual(evs[1]["gate"]["OH-S"], 0.0)
        self.assertEqual(evs[1]["same_as"], {"OH-S": "OH-S-1"})
        self.assertEqual(evs[0]["gate"]["OH-S"], 0.9)
        self.assertEqual(evs[2]["gate"]["OH-S"], 0.9)
        self.assertEqual(chat.calls, 2)

    def test_stories_without_a_usable_card_are_never_selected(self):
        evs = [{"event_id": "OH-S-1", "scope": "race", "gate": {"OH-S": 0.9}, "type": "other", "salience": 1.0,
                "attention": {"a": 0.9}, "usable": False},
               {"event_id": "OH-S-2", "scope": "race", "gate": {"OH-S": 0.9}, "type": "other", "salience": 1.0,
                "attention": {"a": 0.1}}]
        newsday.select(evs)
        self.assertEqual([e["selected"] for e in evs], [{}, {"OH-S": True}])


REQUIRED = ["schema", "date", "run_id", "event_id", "first_seen", "last_seen", "scope", "races", "gate", "type",
            "helps_face", "fires_up", "puts_off", "salience", "attention", "card", "selected"]


class Run(unittest.TestCase):
    def test_writes_events_and_private_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            snap, derived = Path(tmp) / "snap", Path(tmp) / "derived"
            snapshot(snap, "2026-09-28", "0036", {"gdelt-ohio": OHIO})
            summary = newsday.run(date(2026, 9, 28), snap, derived, "test-run", FakeAsker(),
                                  [FakeChat(['{"card": "%s"}' % GOOD] * 5)])
            events = newsday._jsonl(derived / "2026-09-28" / "events.jsonl")
            private = newsday._jsonl(derived / "2026-09-28" / "news_private.jsonl")
        self.assertEqual(summary["stories"], 2)
        for e in events:
            self.assertEqual(set(REQUIRED) - set(e), set())
            self.assertNotIn("titles", e)
        self.assertEqual({p["event_id"] for p in private}, {e["event_id"] for e in events})
        self.assertTrue(all(e["card"] for e in events if e["selected"]))

    def test_a_failing_label_call_skips_that_story_and_is_retried_next_day(self):
        class Flaky(FakeAsker):
            fail = True

            def ask_many(self, state, questions, tag=""):
                if self.fail and "tariffs" in state:
                    raise RuntimeError("giving up")
                return super().ask_many(state, questions, tag)
        with tempfile.TemporaryDirectory() as tmp:
            snap, derived = Path(tmp) / "snap", Path(tmp) / "derived"
            snapshot(snap, "2026-09-28", "0036", {"gdelt-ohio": OHIO})
            snapshot(snap, "2026-09-29", "0036", {"gdelt-ohio": OHIO.replace("20260928", "20260929")})
            chat = FakeChat(['{"card": "%s"}' % GOOD] * 10)
            newsday.run(date(2026, 9, 28), snap, derived, "d1", Flaky(), [chat])
            day1 = {e["event_id"]: e for e in newsday._jsonl(derived / "2026-09-28" / "events.jsonl")}
            ok = Flaky()
            ok.fail = False
            newsday.run(date(2026, 9, 29), snap, derived, "d2", ok, [chat])
            day2 = {e["event_id"]: e for e in newsday._jsonl(derived / "2026-09-29" / "events.jsonl")}
        failed = [e for e in day1.values() if e.get("label_error")]
        self.assertEqual(len(failed), 1)
        self.assertEqual((failed[0]["gate"], failed[0]["selected"]), ({}, {}))
        self.assertFalse(day2[failed[0]["event_id"]].get("label_error"))
        self.assertTrue(any("tariffs" in s for s in ok.states))

    def test_second_day_reuses_labels_and_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            snap, derived = Path(tmp) / "snap", Path(tmp) / "derived"
            snapshot(snap, "2026-09-28", "0036", {"gdelt-ohio": OHIO})
            snapshot(snap, "2026-09-29", "0036", {"gdelt-ohio": OHIO.replace("20260928", "20260929")})
            chat = FakeChat(['{"card": "%s"}' % GOOD] * 10)
            newsday.run(date(2026, 9, 28), snap, derived, "d1", FakeAsker(), [chat])
            asker2 = FakeAsker()
            newsday.run(date(2026, 9, 29), snap, derived, "d2", asker2, [chat])
            day1 = {e["event_id"] for e in newsday._jsonl(derived / "2026-09-28" / "events.jsonl")}
            day2 = newsday._jsonl(derived / "2026-09-29" / "events.jsonl")
        self.assertEqual({e["event_id"] for e in day2}, day1)
        self.assertEqual(asker2.states, [])
        self.assertTrue(all(e["first_seen"].startswith("2026-09-28") for e in day2))


if __name__ == "__main__":
    unittest.main()
