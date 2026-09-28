import gzip
import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

from simlab import newsday

RSS = """<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel>
<item><title>Brown and Husted clash over tariffs - Cleveland.com</title><link>https://news.google.com/a1</link>
<pubDate>Mon, 28 Sep 2026 08:00:00 GMT</pubDate><source url="https://www.cleveland.com">Cleveland.com</source></item>
<item><title>Crypto PAC to spend $30M against Sherrod Brown - Politico</title><link>https://news.google.com/a2</link>
<pubDate>Mon, 28 Sep 2026 07:00:00 GMT</pubDate><source url="https://www.politico.com">Politico</source></item>
</channel></rss>"""
GDELT = {"articles": [{"url": "https://example.com/x", "title": "Talarico , Paxton trade attacks",
                       "seendate": "20260928T090000Z", "domain": "example.com"}]}


def snapshot(root: Path, day: str, hhmm: str, files: dict) -> None:
    run = root / day / hhmm
    entries = []
    for name, body in files.items():
        path = run / "news" / f"{name}.gz"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(gzip.compress(body, mtime=0))
        entries.append({"source": "news", "name": name, "file": f"news/{name}.gz"})
    entries.append({"source": "news", "name": "gdelt-ohio", "error": "HTTP 429"})
    (run / "manifest.json").write_text(json.dumps({"files": entries}), encoding="utf-8")


class ReadDay(unittest.TestCase):
    def test_parses_both_sources_dedupes_and_cleans(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            snapshot(root, "2026-09-28", "0036", {"googlenews-ohio": RSS.encode()})
            snapshot(root, "2026-09-28", "0341", {"googlenews-ohio": RSS.encode(),
                                                   "gdelt-texas": json.dumps(GDELT).encode()})
            arts = newsday.read_day(root, date(2026, 9, 28))
        self.assertEqual([a["race_id"] for a in arts], ["OH-S", "OH-S", "TX"])
        oh = {a["title"]: a for a in arts if a["race_id"] == "OH-S"}
        self.assertEqual(oh["Brown and Husted clash over tariffs"]["domain"], "cleveland.com")
        self.assertEqual(oh["Brown and Husted clash over tariffs"]["seen"], "2026-09-28T08:00:00+00:00")
        tx = [a for a in arts if a["race_id"] == "TX"][0]
        self.assertEqual(tx["title"], "Talarico, Paxton trade attacks")
        self.assertEqual(tx["source"], "gdelt")

    def test_bad_gdelt_json_is_skipped(self):
        self.assertEqual(newsday.parse_gdelt(b'{"articles": [ {bad', "TX"), [])


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


if __name__ == "__main__":
    unittest.main()
