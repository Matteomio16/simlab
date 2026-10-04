import unittest

from simlab import rehearsal


def record(**over):
    news = {"articles": 1200, "stories": 600, "label_errors": 0,
            "selected": {"OH-S": 3, "NC": 6, "TX": 6, "IA": 4, "ME": 7, "US": 3}}
    rec = {"seconds": 500, "spend": {"newsday": 0.03, "harness": 0.1}, "budget": {"mode": "full", "key_spent_before": 2.2},
           "steps": [{"name": "news", "status": "ok", "summary": news},
                     {"name": "reactions", "status": "ok", "summary": {"rows": 1596, "failed": 0, "parse_errors": 6}},
                     {"name": "statistics", "status": "ok",
                      "summary": {"orphaned_events": 0, "deselected_pairs": 0, "ungrouped_races": 0}},
                     {"name": "post kit", "status": "ok", "summary": {"problems": 0}}]}
    for k, v in over.items():
        if k in news:
            news[k] = v
        else:
            rec[k] = v
    return rec


def failed(rec):
    return [name for name, ok, _ in rehearsal.day_checks(rec) if not ok]


class DayChecks(unittest.TestCase):
    # the Saturday pass criteria (docs/rehearsal.md), checked after every daily run so a miss emails Matteo
    def test_a_good_pilot_day_passes(self):
        self.assertEqual(failed(record()), [])

    def test_missing_news_and_a_pilot_race_without_a_story_fail(self):
        rec = record(label_errors=40, selected={"OH-S": 0, "NC": 6, "TX": 6, "IA": 4, "ME": 7, "US": 3})
        self.assertEqual(failed(rec), ["news", "every pilot race has a story"])

    def test_the_budget_safeguard_kicking_in_is_reported(self):
        self.assertEqual(failed(record(budget={"mode": "economy", "key_spent_before": 17.2})), ["budget mode"])

    def test_a_full_scale_day_gets_the_per_run_cap_and_three_hours(self):
        many = {f"R{i}": 2 for i in range(60)} | {"OH-S": 3, "NC": 6, "TX": 6, "IA": 4, "ME": 7, "US": 3}
        self.assertEqual(failed(record(selected=many, spend={"harness": 1.2}, seconds=5000)), [])
        self.assertEqual(failed(record(spend={"harness": 1.2})), ["spend"])


class SameDayAgain(unittest.TestCase):
    # 4 Oct: the replay asked again the day's one unreadable answer, by design, and the drill called it a failure
    def replay(self, appended):
        import json
        import tempfile
        from pathlib import Path
        from unittest import mock
        row = lambda g, err=False: {"race_id": "TX", "event_id": "E", "group": g, "model": "glm", "parse_error": err}
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp) / "derived" / "2026-10-04"
            d.mkdir(parents=True)
            (d / "events.jsonl").write_text(json.dumps({"event_id": "E"}) + "\n", encoding="utf-8")
            (d / "reactions.jsonl").write_text(json.dumps(row("a")) + "\n" + json.dumps(row("b", True)) + "\n",
                                               encoding="utf-8")
            (d / "run.json").write_text(json.dumps(record()), encoding="utf-8")

            def daily(day, data, kev="", env=None):
                with (d / "reactions.jsonl").open("a", encoding="utf-8") as f:
                    f.writelines(json.dumps(row(g)) + "\n" for g in appended)
            with mock.patch.object(rehearsal, "_daily", daily):
                return {name: ok for name, ok, _ in rehearsal.again("2026-10-04", Path(tmp), "")}

    def test_an_unreadable_answer_asked_again_passes(self):
        self.assertTrue(self.replay(["b"])["nothing asked again"])

    def test_a_readable_answer_asked_again_fails(self):
        self.assertFalse(self.replay(["a"])["nothing asked again"])


if __name__ == "__main__":
    unittest.main()
