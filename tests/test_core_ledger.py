import tempfile
import unittest
from pathlib import Path
from unittest import mock

from simlab import core


class Ledger(unittest.TestCase):
    def test_a_broken_line_is_skipped(self):
        # 28 Sep: two processes appended at once on Windows and left a line holding only "}"; every paid call then
        # failed its budget check until the file was read tolerantly
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "spend.jsonl"
            path.write_text('{"ts": 1, "model": "m", "usd": 0.5, "tag": "a:x"}\n}\n'
                            '{"ts": 2, "model": "m", "usd": 0.25, "tag": "a:x"}\n', encoding="utf-8")
            with mock.patch.object(core.Ledger, "path", path), mock.patch.object(core.Ledger, "_total", None):
                self.assertEqual(core.Ledger.total(), 0.75)
                self.assertEqual(core.Ledger.spent("a:x"), 0.75)
                core.Ledger.check()


if __name__ == "__main__":
    unittest.main()
