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


QUERIES = {"mediacloud-ohio": CFG["OH-S"]["mediacloud"], "mediacloud-ga": CFG["GA"]["mediacloud"],
           "mediacloud-national": CFG["US"]["mediacloud"]}


class MediaCloud(unittest.TestCase):
    # its limits (FAQ, 30 Sep): 2 requests a minute, 4,000 a week
    def test_each_query_is_asked_once_in_order_31_seconds_apart(self):
        asked, run, sleeps = [], FakeRun(), []

        def get(url, params=None, headers=None, timeout=None):
            asked.append(params["q"])
            self.assertNotIn("sekrit", url + json.dumps(params))  # the key rides in a header only
            return reply(200)
        with mock.patch.object(snap.requests, "get", get), mock.patch.object(snap.time, "sleep", sleeps.append):
            snap.mediacloud(run, "sekrit", QUERIES, budget_s=600)
        self.assertEqual([n for n, _ in run.saved], list(QUERIES))
        self.assertEqual(asked, list(QUERIES.values()))
        self.assertEqual(sleeps, [31, 31])

    def test_a_rate_limit_waits_a_minute_then_skips_the_rest(self):
        run, sleeps = FakeRun(), []
        with mock.patch.object(snap.requests, "get", lambda *a, **k: reply(429)), \
                mock.patch.object(snap.time, "sleep", sleeps.append):
            snap.mediacloud(run, "key", QUERIES, budget_s=600)
        self.assertEqual(run.saved, [("mediacloud-ohio", 429)])
        self.assertEqual(run.errors, ["mediacloud-ga", "mediacloud-national"])
        self.assertEqual(sleeps, [60])

    def test_past_its_budget_every_query_is_recorded_as_skipped(self):
        run = FakeRun()
        with mock.patch.object(snap.requests, "get", lambda *a, **k: reply(200)):
            snap.mediacloud(run, "key", QUERIES, budget_s=0)
        self.assertEqual((len(run.saved), len(run.errors)), (0, 3))


DATES = ('<select name="RegistrationStatisticsSearchFilter.SelectedDate"><option value="09/19/2026">09/19/2026</option>'
         '<option value="09/26/2026">09/26/2026</option></select>')
RESULTS = ('<script>kendo.grid({"schema":{"model":{"fields":{"Total":{"type":"number"}}}},"data":{"Data":'
           '[{"CountyName":"ALAMANCE","Democrats":36631,"Republicans":38223,"Total":121242},'
           '{"CountyName":"ALEXANDER","Democrats":3555,"Republicans":12131,"Total":25820}],"Total":2}})</script>')


class VoterRegistration(unittest.TestCase):
    # Matteo, 29 Sep: registration totals only, never voter records
    def test_the_newest_reporting_date(self):
        self.assertEqual(snap.regstat_latest(DATES), "09/26/2026")
        self.assertIsNone(snap.regstat_latest("<select></select>"))

    def test_the_county_totals_embedded_in_the_results_page(self):
        rows = snap.regstat_rows(RESULTS)
        self.assertEqual([r["CountyName"] for r in rows], ["ALAMANCE", "ALEXANDER"])
        self.assertEqual(rows[0]["Democrats"], 36631)
        self.assertEqual(snap.regstat_rows("<html>nothing</html>"), [])

    def test_one_file_of_counts_for_the_newest_week(self):
        class Resp:
            def __init__(self, text):
                self.status_code, self.text = 200, text
        asked = []

        def get(url, params=None, *a, **k):
            asked.append(params)
            return Resp(DATES if "handler" in (params or {}) else RESULTS)
        run = FakeRun()
        with mock.patch.object(snap, "get", get):
            snap.voter_registration(run)
        self.assertEqual(run.saved, [("nc-regstat", 200)])
        self.assertEqual(asked[-1], {"date": "09/26/2026"})


if __name__ == "__main__":
    unittest.main()
