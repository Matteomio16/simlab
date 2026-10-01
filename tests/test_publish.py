import tempfile
import unittest
from datetime import date
from pathlib import Path

from PIL import Image

from simlab.publish import frame, text


class FrameTest(unittest.TestCase):
    def test_slide_is_exact_jpeg_with_label_and_date(self):
        s = frame.Slide(date(2026, 10, 3), "LAB NOTES 01")
        s.headline("A headline long enough to wrap onto a second line of the slide")
        drawn = [t.get_text() for t in s.ax.texts]
        self.assertIn(frame.LABEL.upper(), drawn)
        self.assertIn("3 OCT 2026", drawn)
        with tempfile.TemporaryDirectory() as d:
            p = s.save(Path(d) / "s.jpg")
            with Image.open(p) as im:
                self.assertEqual(im.format, "JPEG")
                self.assertEqual(im.size, (1080, 1350))

    def test_wrap_respects_width(self):
        lines = frame.wrap("word " * 60, "sans", 400, 40, 600)
        self.assertGreater(len(lines), 1)
        f = frame.pil_font("sans", 400, 40)
        self.assertTrue(all(f.getlength(l) <= 600 for l in lines))

    def test_missing_glyph_blocks_save(self):
        s = frame.Slide(date(2026, 10, 3), "LAB NOTES 01")
        s.text("leans Democratic →")
        self.assertTrue(s.missing_glyphs())
        with tempfile.TemporaryDirectory() as d, self.assertRaises(ValueError):
            s.save(Path(d) / "s.jpg")

    def test_overflow_blocks_save(self):
        s = frame.Slide(date(2026, 10, 3), "LAB NOTES 01")
        s._put(frame.W - 100, 400, "$1.52 wide text", "sans", 800, 120, frame.INK, va="top")
        s.y = s.limit - 20
        s.text("This paragraph starts too low and runs into the footer.")
        problems = " ".join(s.layout_problems())
        self.assertIn("outside the margins", problems)
        self.assertIn("runs into the footer", problems)

    def test_typeset(self):
        self.assertEqual(frame.typeset("GLM's lean -44%, GLM-5.3"), "GLM’s lean −44%, GLM-5.3")

    def test_cursor_moves_down(self):
        s = frame.Slide(date(2026, 10, 3), "LAB NOTES 01")
        y0 = s.y
        s.headline("Short")
        self.assertGreater(s.y, y0)


class TextCheckTest(unittest.TestCase):
    def test_clean_caption_passes(self):
        self.assertEqual(text.check(f"Ohio moved a little. {frame.LABEL}. Poll average beside ours."), [])

    def test_missing_label(self):
        self.assertIn("missing the label", " ".join(text.check("Ohio moved a little.")))

    def test_banned_words(self):
        msgs = " ".join(text.check(f"Our poll shows it. Voters say yes. A survey. 40% of voters. {frame.LABEL}"))
        for w in ("poll", "voters say", "survey", "% of voters"):
            self.assertIn(w, msgs)

    def test_allowed_poll_phrases(self):
        self.assertEqual(text.check(f"{frame.LABEL}. The poll average and polls close at 7. Not a poll."), [])

    def test_style_notes_flag_ai_wording(self):
        notes = " ".join(text.style("Our AI voters and bots, an LLM, 500 respondents"))
        for w in ("AI", "LLM", "respondents"):
            self.assertIn(w, notes)
        self.assertEqual(text.style("Voter personas in a social simulation"), [])
        self.assertTrue(text.check("Synthetic voters react.", caption=False))
        for s in ("our bots", "AI agents", "an AI-powered forecast", "a game-changer", "Matteo built it",
                  "Hungary's election"):
            self.assertTrue(text.check(s, caption=False), s)

    def test_allow_list_for_real_surveys(self):
        self.assertEqual(text.check(f"The survey's own data. {frame.LABEL}", allow=("survey",)), [])

    def test_overlapping_text_blocks_save(self):
        s = frame.Slide(date(2026, 10, 12), "TEST")
        s.text("Overlap", px=60)
        s.y -= 70
        s.text("Overlap", px=60)
        self.assertTrue(any("overlaps" in p for p in s.layout_problems()))

    def test_stacked_lines_do_not_count_as_overlap(self):
        s = frame.Slide(date(2026, 10, 12), "TEST")
        s.headline("A headline long enough to wrap onto a second line, and a third one too.", px=88)
        self.assertEqual(s.layout_problems(), [])

    def test_reel_schedule_and_closing_frame(self):
        from simlab.publish import racecards as rc, reel
        times = reel.schedule()
        self.assertEqual(len(times), 100)
        self.assertTrue((times[1:] > times[:-1]).all())
        self.assertLess(times[-1] + reel.FALL + 1, reel.SECONDS)  # the closing card stays up for a while
        for usps, name in (("TX", "Texas"), ("NH", "New Hampshire")):
            r = rc.RACE | {"state": name, "usps": usps, "code": f"{usps}-SEN", "today": 0.6, "office": "Senate special"}
            s, *_ = reel.build(r)
            reel.reveal(s, r)
            self.assertEqual(s.layout_problems(), [], name)

    def test_never_betting(self):
        for s in ("the betting markets", "bettors", "a bet", "gamblers", "wagers"):
            self.assertTrue(text.check(s, caption=False, allow=("betting",)), s)  # allow can't lift it
        self.assertEqual(text.check("prediction markets and markets", caption=False), [])

    def test_opponent_wording(self):
        from simlab.publish import racecards as rc
        from simlab.publish.themes import LAB
        base = rc.RACE | {"state": "Texas 28", "usps": "TX", "code": "TX-28", "office": "House", "p": 0.7}
        self.assertEqual(rc.who(base, cap=True), "The Democrat")
        o = base | {"left_party": "O", "candidates": {"left": "Jane Smith", "right": "Tom Roe"}}
        self.assertEqual(rc.who(o), "Smith")
        self.assertEqual(rc.verdict(o["p"], rc.lean(o)), "Leans Smith")
        self.assertEqual(rc.who(base | {"left_party": "O"}), "the other candidate")
        self.assertEqual(rc.verdict(0.9, rc.lean(base | {"left_party": "O"})), "Likely Other candidate")
        for r in (o, base | {"left_party": "O"}, base | {"left_party": "I"}):
            for name in ("4-stamp", "2-ladder", "3-futures"):
                self.assertEqual(rc.LAYOUTS[name](LAB, r).layout_problems(), [], (name, r.get("candidates")))

    def test_special_editions_render(self):
        from simlab.publish import specials
        with tempfile.TemporaryDirectory() as tmp:
            for name, fn in specials.LAYOUTS.items():
                self.assertTrue(fn().save(Path(tmp) / f"{name}.jpg").exists(), name)


if __name__ == "__main__":
    unittest.main()
