import json
import tempfile
import unittest
from pathlib import Path

from simlab import daily


def fake_runner(results):
    calls = []

    def run(module, args):
        calls.append((module, args))
        return results.get(module, (0, '{"ok": true}\n', ""))
    run.calls = calls
    return run


class Steps(unittest.TestCase):
    def test_missing_modules_are_skipped_and_a_failure_stops_the_rest(self):
        runner = fake_runner({"simlab.harness": (1, "", "Traceback ...\nRuntimeError: giving up")})
        built = {"simlab.newsday", "simlab.harness", "simlab.publish.kit"}
        steps = daily.run_steps("2026-10-05", Path("/data"), {"wording": "direct", "kev": ""}, runner,
                                exists=lambda m: m in built)
        self.assertEqual([(s["name"], s["status"]) for s in steps],
                         [("news", "ok"), ("reactions", "failed"), ("statistics", "not run"), ("post kit", "not run")])
        self.assertEqual(steps[0]["summary"], {"ok": True})
        self.assertIn("giving up", steps[1]["error"])
        self.assertEqual([c[0] for c in runner.calls], ["simlab.newsday", "simlab.harness"])

    def test_unbuilt_step_is_skipped_and_so_are_steps_that_need_it(self):
        runner = fake_runner({})
        steps = daily.run_steps("2026-10-05", Path("/data"), {"wording": "reaction", "kev": "https://kev"}, runner,
                                exists=lambda m: m != "simlab.statsday")
        self.assertEqual([s["status"] for s in steps], ["ok", "ok", "skipped", "skipped"])
        self.assertEqual(steps[3]["reason"], "needs statistics")
        harness_args = [c[1] for c in runner.calls if c[0] == "simlab.harness"][0]
        self.assertEqual(harness_args[-4:], ["--wording", "reaction", "--kev", "https://kev"])
        self.assertNotIn("simlab.publish.kit", [c[0] for c in runner.calls])


class Record(unittest.TestCase):
    def test_run_record_names_inputs_models_and_steps(self):
        with tempfile.TemporaryDirectory() as tmp:
            data = Path(tmp)
            run_dir = data / "snapshots" / "2026-10-05" / "0917"
            run_dir.mkdir(parents=True)
            (run_dir / "manifest.json").write_text('{"files": []}', encoding="utf-8")
            steps = [{"name": "news", "status": "ok"}]
            rec = daily.record("2026-10-05", data, "run-1", steps, started=100.0, finished=160.0)
            saved = json.loads((data / "derived" / "2026-10-05" / "run.json").read_text(encoding="utf-8"))
        self.assertEqual(saved, rec)
        self.assertEqual(rec["snapshots"][0]["run"], "0917")
        self.assertEqual(len(rec["snapshots"][0]["manifest_sha256"]), 64)
        self.assertIn("glm", rec["models"])
        self.assertEqual(rec["steps"], steps)
        self.assertEqual(rec["seconds"], 60.0)


if __name__ == "__main__":
    unittest.main()
