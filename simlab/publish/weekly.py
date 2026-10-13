"""The weekly post (Mondays, from the Sunday check in docs/simulation-only.md): where we and the polls disagree most,
plus one slide per race whose week was flagged or cancelled.

    python -m simlab.publish.weekly --check FILE.json [--example]

The check file is simlab-data/derived/<Sunday>/weekly_check.json (Statistics), one row per race, largest gap first:
    {"week_ending": "2026-10-18", "races": [{"race": "IA", "state": "Iowa", "ours": -1.2, "polls": 0.8,
      "markets": 0.5, "gap": 2.0, "flag": "" | "flag" | "severe" | "cancel" | "cancelled", "n_polls": 3,
      "basis": "polls" | "markets" | null, "stories": [{...}], "what_we_did": "...", "moved_by": "...",
      "left": "Turek", "left_party": "D", "right": "Hinson"}]}
"stories" are unreviewed model cards and never appear on the post; "moved_by" is our reviewed public wording, added by
hand. Rows without a poll average or market (basis null) are left out. A "cancel" row is a candidate waiting for
Matteo's yes and is worded as investigated.
"ours" (our expected vote) and "polls" (the poll average) are the week's change in margin, Democrat or independent
minus Republican, in points. "left"/"right" are the candidates' surnames, so every change is named by whom it moved
toward. Vote only on this post, never chances (review, 13 Oct). --example draws invented numbers stamped EXAMPLE.
"""
from __future__ import annotations

import argparse
import json
from datetime import date, timedelta
from pathlib import Path

from . import charts, text
from .frame import DISCLAIMER, LABEL, Slide
from .themes import LAB

ROOT = Path(__file__).resolve().parents[2]
SERIES = "Weekly check"
FLAG_WORD = {"flag": "Flagged", "severe": "Investigated", "cancel": "Investigated", "cancelled": "Week undone"}
EXAMPLE = {"week_ending": "2026-10-18", "races": [
    {"race": "IA", "state": "Iowa", "ours": -1.6, "polls": 1.9, "gap": 3.5, "flag": "flag", "n_polls": 3,
     "basis": "polls", "moved_by": "Farm-state tariff story", "left": "Turek", "right": "Hinson",
     "what_we_did": "we checked that the story was matched to the right race and kept it."},
    {"race": "OH-S", "state": "Ohio", "ours": 0.4, "polls": -1.1, "gap": 1.5, "flag": "", "n_polls": 4, "basis": "polls",
     "left": "Brown", "right": "Husted"},
    {"race": "TX", "state": "Texas", "ours": 0.9, "polls": 0.2, "gap": 0.7, "flag": "", "n_polls": 3, "basis": "polls",
     "left": "Talarico", "right": "Paxton"},
    {"race": "ME", "state": "Maine", "ours": -0.3, "polls": 0.6, "gap": 0.9, "flag": "", "n_polls": 2, "basis": "polls",
     "left": "Jackson", "right": "Collins"},
    {"race": "AK", "state": "Alaska", "ours": 2.4, "polls": -0.4, "gap": 2.8, "flag": "", "n_polls": 1, "basis": "polls",
     "left": "Peltola", "right": "Sullivan"},
]}


def pts(v: float) -> str:
    return "0" if abs(v) < 0.05 else f"{'+' if v > 0 else '−'}{abs(v):.1f}"


def side(r: dict, v: float) -> str:
    """Whom a change moved toward: "Hinson (R)", or the party when the check file has no names."""
    if not r.get("left"):
        return "Democrats" if v > 0 else "Republicans"
    return f"{r['left']} ({r.get('left_party', 'D')})" if v > 0 else f"{r['right']} (R)"


def toward(r: dict, v: float) -> str:
    """A change named by candidate, never by sign (review, 13 Oct): "1.6 points toward Hinson (R)"."""
    return "no change" if abs(v) < 0.05 else f"{abs(v):.1f} points toward {side(r, v)}"


LAUNCH = date(2026, 10, 12)


def bench(r: dict) -> float:
    """The week's benchmark change: the poll average, or the markets when the week brought no new polls."""
    return r["polls"] if r.get("basis") == "polls" else r["markets"]


def bench_name(r: dict) -> str:
    return "poll average" if r.get("basis") == "polls" else "markets"


def build(check: dict, theme=LAB, example: bool = False) -> tuple[Path, list[str]]:
    ending = date.fromisoformat(check["week_ending"])
    since = date.fromisoformat(check.get("since") or str(ending - timedelta(days=7)))
    if not example and ((ending - since).days < 7 or (ending - LAUNCH).days < 7):  # a full week first (review, 13 Oct)
        raise SystemExit(f"the check for {since} to {ending} is under a full week; the first post waits a week")
    week = ending + timedelta(days=1)  # posted on Monday, the morning after the Sunday check
    span = f"week to {ending.day} {ending:%b}"
    kicker = "EXAMPLE · INVENTED NUMBERS" if example else ""
    src = ("EXAMPLE: invented numbers, not a forecast." if example else
           "Change in margin over the week, Democrat (or independent) minus Republican. Poll average: polls published "
           "that week. Simulation: NotAPoll.")
    rows = sorted((r for r in check["races"] if r.get("basis") and r.get("gap") is not None), key=lambda r: -r["gap"])
    top = rows[:5]
    slides = []

    a = Slide(week, kicker, theme, series=SERIES)
    a.headline("Where we and the polls moved apart this week", px=64)
    a.dek(f"Each race's change in points of margin, {span}: our expected vote against its poll average. Polls "
          "only check us; they don't move our numbers.", px=32)
    charts.legend_dots(a, [("Poll average", theme.data, False), ("Our expected vote", theme.ai, True)])
    a.y += 6
    lim = max(4, max(max(abs(r["ours"]), abs(bench(r))) for r in top) + 1)
    charts.dumbbell(a, [(r["state"] + (" †" if r.get("basis") == "markets" else "") + (" *" if r["flag"] else ""),
                         bench(r), r["ours"]) for r in top], lim,
                    80 * len(top), "toward Republicans", "toward Democrats",
                    lambda v: f"{abs(v):g}", label_w=230)
    flagged = [r for r in rows if r["flag"]]
    a.text(("* " + ", ".join(f"{r['state']}: {FLAG_WORD[r['flag']].lower()}" for r in flagged)) if flagged else
           "No race moved more than 3 points apart from its polls.", px=30, color=theme.ink2)
    if any(r.get("basis") == "markets" for r in top):
        a.text("† no new polls this week: markets instead", px=30, color=theme.ink2)
    a.source(src)
    slides.append(a)

    for r in flagged:  # one slide per flagged, investigated or undone race
        b = Slide(week, kicker, theme, series=SERIES)
        o, q, them = r["ours"], bench(r), "the polls" if r.get("basis") == "polls" else "the markets"
        way = (f"further than {them}" if abs(o) > abs(q) and o * q >= 0 else
               f"the other way from {them}" if o * q < 0 else f"less than {them}")
        b.headline(f"{r['state']}: we moved {way} this week.", px=76)
        name = bench_name(r)
        b.text(f"Our expected vote: {toward(r, r['ours'])}", "serif", 600, 44, after=0.3)
        b.text(f"{name[0].upper() + name[1:]}: {toward(r, bench(r))}", "serif", 600, 44, theme.data, after=0.3)
        b.text(f"Change in margin, {span}.", px=28, color=theme.ink2, after=0.8)
        if r.get("moved_by"):
            b.text("What moved us", "sans", 600, 30, theme.ink2, after=0.4)
            b.text(r["moved_by"].rstrip(".") + ".", "serif", 600, 36, after=0.8)
        b.text("What we did", "sans", 600, 30, theme.ink2, after=0.4)
        did = r.get("what_we_did") or "still under review."
        b.text(did[0].upper() + did[1:], "serif", 600, 36, after=0.8)
        b.source(src)
        slides.append(b)

    out = ROOT / "kits" / "daily" / (f"example-weekly" if example else f"{week:%d}-weekly")
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob("slide-*.jpg"):
        old.unlink()
    problems = []
    for i, s in enumerate(slides, 1):
        problems += [f"slide {i}: {x}" for x in s.layout_problems() + s.missing_glyphs()
                     + text.slide_problems(s, ("poll", "polls"))]
        s.save(out / f"slide-{i}.jpg")

    big = top[0]
    lines = [f"Every Sunday we check our expected vote against the polls. Since 12 October polls no longer move our numbers: "
             f"only the news does, through the voter personas. So each week we look at where the two moved apart.", "",
             f"The biggest gap in the {span}: {big['state']}, where our expected vote moved "
             f"{toward(big, big['ours'])} and the {bench_name(big)} {toward(big, bench(big))}."]
    done = {"flag": "was flagged", "severe": "was investigated", "cancel": "was investigated",
            "cancelled": "had its week undone"}
    for r in flagged:
        lines += ["", f"{r['state']} {done[r['flag']]}; {r.get('what_we_did') or 'it is still under review.'}"]
    lines += ["", "Which race do you think we're reading wrong?", "", "#midterms2026 #elections", "", DISCLAIMER]
    caption = "\n".join(lines)
    x = (f"Weekly check, {span}: the biggest gap between our expected vote and the polls was {big['state']} (ours "
         f"moved {toward(big, big['ours'])}, the {bench_name(big)} {toward(big, bench(big))}). Polls only check us now; the news moves our "
         f"numbers. {LABEL}.")
    (out / "caption.txt").write_text(caption, encoding="utf-8")
    (out / "single-post.md").write_text(f"# Single posts\n\n## X ({len(x)} of 280 characters)\n\n{x}\n", encoding="utf-8")
    problems += [f"caption: {q}" for q in text.check(caption, caption=True, allow=("poll", "polls"))]
    problems += [f"x: {q}" for q in text.check(x, caption=True, allow=("poll", "polls"))]
    (out / "checks.txt").write_text("\n".join(problems) or "all rules pass", encoding="utf-8")
    return out, problems


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", type=Path)
    ap.add_argument("--example", action="store_true")
    a = ap.parse_args()
    check = EXAMPLE if a.example else json.loads(a.check.read_text(encoding="utf-8"))
    out, problems = build(check, example=a.example)
    print(out, "; ".join(problems) or "all rules pass")


if __name__ == "__main__":
    main()
