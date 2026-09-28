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


if __name__ == "__main__":
    unittest.main()
