import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def example_inputs(data: Path, day: str = "2026-10-05"):
    """Invented numbers in the engine-design §7 shapes (EXAMPLE, not a forecast)."""
    rng = np.random.default_rng(0)
    races = {"OH-S": (0.44, -1.2, 0.41, "Toss-up"), "NC": (0.58, 1.5, 0.55, "Toss-up"),
             "TX": (0.31, -3.8, None, "Lean R")}
    f = {"date": day, "run_id": "c0ffee1234", "schema": 1, "races": {}, "senate": {"p_r_50plus": 0.46, "seats": {}},
         "house": {"p_d_majority": 0.71, "seats": {}}}
    d = {"date": day, "run_id": "c0ffee1234", "schema": 1, "races": {}}
    for rid, (p, poll, market, cook) in races.items():
        mid = 5.5 * (p - 0.5) * 2
        f["races"][rid] = {"p_dem_win": p, "margin": {"p10": mid - 6, "p50": mid, "p90": mid + 6},
                           "stats_only": {"p_dem_win": p - 0.02, "margin": {"p50": mid - 0.3}},
                           "benchmarks": {"poll_avg": poll, "market": market, "cook": cook},
                           "movers": [{"event_id": "e1", "card": "The candidate announced a plan on prices.",
                                       "delta": 0.4}]}
        d["races"][rid] = (rng.normal(mid, 4.7, 1000)).round(2).tolist()
    out = data / "derived" / day
    out.mkdir(parents=True)
    (out / "forecast.json").write_text(json.dumps(f))
    (out / "draws.json").write_text(json.dumps(d))
    prev = data / "derived" / "2026-09-28"
    prev.mkdir(parents=True)
    f2 = json.loads(json.dumps(f))
    f2["races"]["NC"]["p_dem_win"] = 0.50
    (prev / "forecast.json").write_text(json.dumps(f2))


class KitTest(unittest.TestCase):
    def run_kit(self, data: Path, day: str):
        return subprocess.run([sys.executable, "-m", "simlab.publish.kit", "--date", day, "--data", str(data)],
                              cwd=ROOT, capture_output=True, text=True, encoding="utf-8")

    def test_builds_kit_and_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            data = Path(tmp)
            example_inputs(data)
            r = self.run_kit(data, "2026-10-05")
            self.assertEqual(r.returncode, 0, r.stderr[-2000:])
            summary = json.loads(r.stdout.strip().splitlines()[-1])
            self.assertTrue(summary["ok"])
            self.assertEqual(summary["races"], 3)
            kit = data / "derived" / "2026-10-05" / "post-kit"
            self.assertEqual(len(list((kit / "slides").glob("*.jpg"))), summary["slides"])
            for f in ("caption_instagram.txt", "alt_text.json", "thread.txt", "note.md", "manifest.json",
                      "contact.jpg"):
                self.assertTrue((kit / f).exists(), f)
            note = (kit / "note.md").read_text(encoding="utf-8")
            self.assertIn("TX-SEN: no market price", note)  # missing benchmark is reported, not hidden
            caption = (kit / "caption_instagram.txt").read_text(encoding="utf-8")
            self.assertIn("A live experiment in social simulation", caption)
            self.assertIn("Up 8 points this week", caption)  # NC moved 0.50 -> 0.58
            self.assertIn("No meaningful change", caption)

    def test_missing_forecast_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = self.run_kit(Path(tmp), "2026-10-05")
            self.assertNotEqual(r.returncode, 0)
            self.assertFalse(json.loads(r.stdout.strip().splitlines()[-1])["ok"])


if __name__ == "__main__":
    unittest.main()
