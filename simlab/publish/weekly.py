"""The weekly post (Mondays, from the Sunday check in docs/simulation-only.md): where we and the polls disagree most,
plus one slide per race whose week was flagged or cancelled.

    python -m simlab.publish.weekly --check FILE.json [--example]

The check file is the Sunday weekly check (Statistics), one row per race:
    {"week_ending": "2026-10-18", "races": [{"race": "IA", "state": "Iowa", "ours": -1.2, "polls": 0.8,
      "gap": 2.0, "flag": "" | "flag" | "severe" | "cancelled", "n_polls": 3, "basis": "polls" | "markets",
      "stories": ["..."], "what_we_did": "..."}]}
"ours" and "polls" are the week's change in margin (Democrat or independent minus Republican, points). --example
draws invented numbers stamped EXAMPLE, for review.
"""
from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

from . import charts, text
from .frame import DISCLAIMER, LABEL, Slide
from .themes import LAB

ROOT = Path(__file__).resolve().parents[2]
SERIES = "Weekly check"
FLAG_WORD = {"flag": "Flagged", "severe": "Investigated", "cancelled": "Week undone"}
EXAMPLE = {"week_ending": "2026-10-18", "races": [
    {"race": "IA", "state": "Iowa", "ours": -1.6, "polls": 1.9, "gap": 3.5, "flag": "flag", "n_polls": 3,
     "basis": "polls", "stories": ["Farm-state tariff story"], "what_we_did": "Checked: the story was on the right race; kept."},
    {"race": "OH-S", "state": "Ohio", "ours": 0.4, "polls": -1.1, "gap": 1.5, "flag": "", "n_polls": 4, "basis": "polls"},
    {"race": "TX", "state": "Texas", "ours": 0.9, "polls": 0.2, "gap": 0.7, "flag": "", "n_polls": 3, "basis": "polls"},
    {"race": "ME", "state": "Maine", "ours": -0.3, "polls": 0.6, "gap": 0.9, "flag": "", "n_polls": 2, "basis": "polls"},
    {"race": "AK", "state": "Alaska", "ours": 2.4, "polls": -0.4, "gap": 2.8, "flag": "", "n_polls": 1, "basis": "polls"},
]}


def pts(v: float) -> str:
    return "0" if abs(v) < 0.05 else f"{'+' if v > 0 else '−'}{abs(v):.1f}"


def build(check: dict, theme=LAB, example: bool = False) -> tuple[Path, list[str]]:
    week = date.fromisoformat(check["week_ending"])
    kicker = "EXAMPLE · INVENTED NUMBERS" if example else ""
    src = ("EXAMPLE: invented numbers, not a forecast." if example else
           "Change in margin over the week, Democrat (or independent) minus Republican. Poll average: polls published "
           "that week. Simulation: NotAPoll.")
    rows = sorted(check["races"], key=lambda r: -r["gap"])
    top = rows[:5]
    slides = []

    a = Slide(week, kicker, theme, series=SERIES)
    a.headline("Where we and the polls moved apart this week", px=64)
    a.dek("Each race's change over the week: our forecast against its poll average. Polls only check us; they "
          "don't move our numbers.", px=32)
    charts.legend_dots(a, [("Poll average", theme.data, False), ("Our forecast", theme.ai, True)])
    a.y += 6
    lim = max(4, max(max(abs(r["ours"]), abs(r["polls"])) for r in top) + 1)
    charts.dumbbell(a, [(r["state"] + (" *" if r["flag"] else ""), r["polls"], r["ours"]) for r in top], lim,
                    80 * len(top), "toward Republicans", "toward Democrats", pts, label_w=230)
    flagged = [r for r in rows if r["flag"]]
    a.text(("* " + ", ".join(f"{r['state']}: {FLAG_WORD[r['flag']].lower()}" for r in flagged)) if flagged else
           "No race moved more than 3 points apart from its polls.", px=30, color=theme.ink2)
    a.source(src)
    slides.append(a)

    for r in flagged:  # one slide per flagged, investigated or undone race
        b = Slide(week, kicker, theme, series=SERIES)
        way = ("further than the polls" if abs(r["ours"]) > abs(r["polls"]) and r["ours"] * r["polls"] >= 0 else
               "the other way from the polls" if r["ours"] * r["polls"] < 0 else "less than the polls")
        b.headline(f"{r['state']}: we moved {way} this week.", px=76)
        charts.stats(b, [(pts(r["ours"]), "our forecast's change"), (pts(r["polls"]),
                     "poll average's change" if r.get("basis", "polls") == "polls" else "markets' change")], px=110,
                     rule=True)
        if r.get("stories"):
            b.text("What moved us", "sans", 600, 30, theme.ink2, after=0.4)
            b.text("; ".join(r["stories"]) + ".", "serif", 600, 36, after=0.8)
        b.text("What we did", "sans", 600, 30, theme.ink2, after=0.4)
        b.text(r.get("what_we_did") or "Still under review.", "serif", 600, 36, after=0.8)
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
    lines = [f"Every Sunday we check our forecast against the polls. Since 12 October polls no longer move our numbers: "
             f"only the news does, through the voter personas. So each week we look at where the two moved apart.", "",
             f"The biggest gap this week: {big['state']}, where our forecast moved {pts(big['ours'])} points and the poll "
             f"average {pts(big['polls'])}."]
    for r in flagged:
        lines += ["", f"{r['state']} ({FLAG_WORD[r['flag']].lower()}): {r.get('what_we_did') or 'still under review.'}"]
    lines += ["", "Which race do you think we're reading wrong?", "", "#midterms2026 #elections", "", DISCLAIMER]
    caption = "\n".join(lines)
    x = (f"Weekly check: the biggest gap between our forecast and the polls this week was {big['state']} "
         f"(us {pts(big['ours'])}, polls {pts(big['polls'])}). Polls only check us now; the news moves our numbers. "
         f"{LABEL}.")
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
