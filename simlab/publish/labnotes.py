"""Lab notes, the making-of series (docs/content-plan.md §3): python -m simlab.publish.labnotes 1 2 3

Writes kits/labnotes/NN/: the slides (JPEG 1080x1350) and post.md with the Instagram caption, alt text, the thread for
X, Threads and Bluesky, and the rule checks. Drafts for Matteo's approval; nothing here posts anything.
Test-bench numbers come from runs/scorecard.jsonl; the outlet-name test was printed, not saved (CHANGELOG, 28 Sep).
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from PIL import Image

from ..core import RUNS
from ..scorecard import latest
from . import charts, text
from .frame import LABEL, Slide, Theme
from .themes import LAB

KITS = RUNS.parent / "kits" / "labnotes"
LIMITS = {"instagram": 2200, "thread": 280}
MODELS = {"jev": "Jev", "kev": "Kev (untuned)", "glm": "GLM", "mimo": "MiMo", "deepseek": "DeepSeek", "luna": "GPT-6 Luna"}


@dataclass
class Post:
    day: date
    title: str
    slides: list[tuple[Slide, str]]
    instagram: str
    thread: list[str]
    allow: tuple[str, ...] = ()


def closing(s: Slide):
    s.at_bottom(36 * 1.25 + 40)
    s.rule(s.t.ink, after=40)
    s.text("The forecast goes public on Monday 12 October.", px=36)


def ep01(theme: Theme = LAB) -> Post:
    s, day = latest(), date(2026, 10, 3)
    null_jev = min(s[("null", "jev")]["support_p_no_change"], s[("null", "jev")]["turnout_p_no_change"])
    null_kev = 1 - s[("null", "kev")]["support_p_no_change"]
    glm_dir = s[("events", "glm")]["sign_accuracy_nonnull"]
    k = "LAB NOTES 01"

    a = Slide(day, k, theme).headline("Before forecasting the midterms, we tested six models as synthetic voters.")
    a.dek("Can a synthetic voter react to the news the way real groups of people do? Four checks, the same questions for every "
          "model.")
    a.at_bottom(charts.stats_height(rule=True))
    charts.stats(a, [("6", "models"), ("4", "checks"), ("$1.52", "total cost")], rule=True)
    a.source("Test bench, 27–28 Sep 2026. Jev 1.13, Kev 4B, GLM-5.3 Flash, MiMo-V2.6 Flash, DeepSeek V4.1 Flash, "
             "GPT-6 Luna, through OpenRouter.")

    b = Slide(day, f"{k} · WHY TEST FIRST", theme).headline("In April, our first simulation called Hungary's winner, "
                                                     "and missed the size.")
    b.dek("TISZA's share of the vote")
    charts.hbars(b, [("Simulated", 36.7, theme.ai), ("Actual", 53.2, theme.data)], 60, lambda v: f"{v:.1f}%")
    b.y += 20
    b.text("Right direction, 16 points short. So this time every part is tested against real data before it goes "
           "into the forecast.", px=38, color=theme.ink2)
    b.source("Hungary, April 2026. Simulated: 45 simulated voters, run before the election. Actual: the official result.")

    c = Slide(day, f"{k} · THE CHECKS", theme).headline("Four checks, identical for every model.")
    c.y += 10
    for n, (t1, t2) in enumerate([
            ("Ignore noise.", "A football score or a new pumpkin spice croissant should change nobody's vote."),
            ("No built-in lean.", "Swap the parties in a story and the reaction should flip."),
            ("React to real events.", "19 events since 2012 with measured shifts in opinion."),
            ("Match real groups.", "How groups actually voted and turned out in 2024.")], 1):
        c.text(f"{n}  {t1}", "serif", 600, 50, after=0.2)
        c.text(t2, px=36, color=theme.ink2, after=0.9, x=132, width=c.width - 60)
    c.source("Checks: null test, mirror test, events test, fidelity test. Scored the same way for every model.")

    d = Slide(day, f"{k} · RESULTS", theme).headline("One job each, or none.")
    charts.rows(d, [
        ("Is this story relevant to the race?", "Jev", f"Said “no change” to {null_jev:.0%} of irrelevant news"),
        ("Which way does each group react?", "GLM-5.3 Flash",
         f"Right direction on {glm_dir * 13:.0f} of 13 real events that moved opinion"),
        ("Where does each race start?", "Plain statistics", "Smaller errors than every model at matching 2024 groups nationwide"),
        ("How big is a reaction?", "No model", "Sizes come from real past shifts, not from the models"),
    ])
    d.text("Kev, untuned, got no job. We trained our own (Lab notes 08).", px=30, color=theme.ink2)
    d.source("Scores: null, mirror, events and fidelity tests, 27–28 Sep 2026.")

    e = Slide(day, f"{k} · WHAT WE CHANGED", theme).headline("The simulation doesn't set the numbers. It moves them.", px=80)
    e.text("Statistics and real polls set where each race starts. The synthetic voters only simulate how the day's news "
           "shifts support and turnout, and a weekly check against new polls decides how much of that to keep.",
           px=40, color=theme.ink2, after=1.2)
    e.text("Next: how an outlet's name flipped a model's answer on 41% of stories.", "serif", 600, 48, after=1.2)
    closing(e)

    return Post(day, "Lab notes 01: we tested six models as synthetic voters", [
        (a, "Title slide: Before forecasting the midterms, we tested six models as synthetic voters. Six models, four checks, "
            "$1.52 total cost."),
        (b, "Bar chart of TISZA's vote share in Hungary, April 2026: simulated 36.7 percent, actual 53.2 percent. "
            "Right direction, 16 points short."),
        (c, "The four checks: ignore irrelevant news; no built-in party lean; react correctly to 19 real events; "
            "match how groups voted and turned out in 2024."),
        (d, "Results table. Relevance: Jev. Direction of reactions: GLM-5.3 Flash. Starting numbers: plain "
            "statistics. Size of reactions: no model."),
        (e, "So the simulation doesn't set the numbers, it moves them. Statistics and polls set the start; synthetic voters simulate "
            "how news shifts support and turnout."),
    ], f"""Before we forecast a single race, we tested six models as synthetic voters.

The question: can a synthetic voter react to news the way real groups of people do? Four checks, identical for every model:
1. Ignore irrelevant news
2. No built-in party lean
3. React correctly to 19 real events since 2012
4. Match how groups actually voted and turned out in 2024

No model was good at everything, so each got one job, or none. Jev is best at spotting news that doesn't matter. GLM gets the direction of reactions right. And plain statistics had smaller errors than every model at matching how groups voted nationwide, so the simulation never sets the starting numbers. It only simulates how the news moves them.

Why test first? In April, our first simulation called Hungary's winner but came up 16 points short on the size.

Total cost of these tests: $1.52. The forecast goes public on Monday 12 October.

{LABEL}.

#midterms2026 #elections #socialsimulation #dataviz""", [
        f"Before forecasting the 2026 midterms, we tested six models as synthetic voters: can they react to news like real "
        f"groups of people? Four checks, identical questions for every model. Here's what each one is good for. "
        f"{LABEL}.",
        f"Irrelevant news should change nothing. Jev said “no change” to {null_jev:.0%} of it. An untuned Kev reacted "
        f"to about 1 story in {1 / null_kev:.0f}.",
        f"Which way does a group react to real news? GLM-5.3 Flash got the direction right on {glm_dir * 13:.0f} of 13 "
        f"events that moved opinion.",
        "Where does each race start? Nationwide, plain statistics beat every model at matching how groups voted in 2024. "
        "So the simulation never sets the starting numbers; it only simulates how the news moves them.",
        "Total cost of the tests: $1.52. The forecast goes public on 12 October; the making-of runs daily until then.",
    ])


def ep02(theme: Theme = LAB) -> Post:
    day, k = date(2026, 10, 4), "LAB NOTES 02"
    gap = {"GLM": 0.30, "Jev": 0.15}
    flips = {"GLM": 0.41, "Jev": 0.15}

    a = Slide(day, k, theme)
    a.y += 20
    a.text(f"{flips['GLM']:.0%}", "sans", 800, 300, leading=1.0, after=0.15)
    a.headline("of headlines got a different answer when we swapped “Fox News” for “MSNBC.”", px=76)
    a.dek("Same story, same words. We asked a model which party the news helps; only the outlet's name changed.")
    a.source("80 real headlines about 2026 Senate races, September 2026. Model: GLM-5.3 Flash.")

    b = Slide(day, f"{k} · THE TEST", theme).headline("One story, three versions.")
    b.y += 10
    for label, body in [("No outlet", "The headline on its own."), ("“Fox News”", "The same headline, credited to Fox."),
                        ("“MSNBC”", "The same headline, credited to MSNBC.")]:
        b.text(label, "serif", 600, 50, after=0.15)
        b.text(body, px=36, color=theme.ink2, after=0.9)
    b.text("The event is identical, so which party it helps shouldn't move. We asked two models, 80 headlines each.",
           px=38, after=0.5)
    b.source("Headlines: Google News, September 2026. Question: which party does this news help?")

    c = Slide(day, f"{k} · RESULTS", theme).headline("Both models moved. One moved a lot.", px=80)
    charts.hbars(c, [(m, 100 * v, theme.data) for m, v in gap.items()], 50, lambda v: f"+{v:.0f} points",
                 title="Shift toward “helps Democrats” when the outlet is MSNBC instead of Fox")
    c.y += 20
    charts.hbars(c, [(m, 100 * v, theme.data) for m, v in flips.items()], 50, lambda v: f"{v:.0f}%",
                 title="Headlines where the top answer flipped")
    c.source("Shift: change in P(helps Democrats) minus P(helps Republicans), scale −100 to +100. 80 headlines.")

    d = Slide(day, f"{k} · WHAT WE CHANGED", theme).headline("So no model ever sees an outlet's name.")
    d.text("Before any model reads the news, we remove the outlet and rewrite each story as a short, neutral event "
           "card. Real readers do weigh the source; the simulation has to judge the event itself.",
           px=40, color=theme.ink2, after=1.2)
    d.text("Next: ask it backwards and most of the lean disappears.", "serif", 600, 48, after=1.2)
    closing(d)

    return Post(day, "Lab notes 02: the outlet name changed the answer", [
        (a, "41 percent of headlines got a different answer when we swapped Fox News for MSNBC. Same story; only the "
            "outlet's name changed."),
        (b, "The test: each headline asked three ways, with no outlet, credited to Fox News, and credited to MSNBC."),
        (c, "Bar charts. Shift toward helps Democrats when the outlet is MSNBC instead of Fox: GLM plus 30 points, Jev "
            "plus 15. Top answer flipped: GLM 41 percent, Jev 15 percent."),
        (d, "So no model ever sees an outlet's name: stories become short neutral event cards first."),
    ], f"""Same headline, two outlets. The model changed its answer.

We took 80 real headlines about 2026 Senate races and asked two models which party each story helps. Three versions of every headline: no outlet, credited to Fox News, credited to MSNBC. Same words every time.

Credited to MSNBC instead of Fox, GLM's lean toward "helps Democrats" rose by 30 points, and its top answer flipped on 41% of headlines. Jev moved half as much.

The models read the outlet as a clue about the story. Real readers do that too, but a simulation has to judge the event itself. So no model in our forecast ever sees an outlet's name: every story becomes a short, neutral event card first.

Lab notes 02 of the making-of. The forecast goes public on Monday 12 October.

{LABEL}.

#midterms2026 #elections #socialsimulation #media""", [
        f"Same headline, two outlets: we credited it to Fox News, then to MSNBC. The model's top answer on which party it "
        f"helps flipped on 41% of 80 headlines. {LABEL}.",
        "Credited to MSNBC instead of Fox, GLM's lean toward “helps Democrats” rose by 30 points. Jev moved half as "
        "much.",
        "Real readers weigh the source too, but a simulation has to judge the event itself. So no model in our "
        "forecast ever sees an outlet's name: every story becomes a short, neutral event card first.",
    ])


def ep03(theme: Theme = LAB) -> Post:
    s, day, k = latest(), date(2026, 10, 5), "LAB NOTES 03"
    lean = lambda m: s[("mirror", m)]["mean_asymmetry"] / s[("mirror", m)]["mean_abs_reaction"]
    order = ["glm", "deepseek", "mimo", "luna", "jev", "kev"]
    items = [(MODELS[m], 100 * lean(m + "1"), 100 * lean(m)) for m in order]
    pct = lambda v: f"{v:+.0f}%" if v else "0"

    a = Slide(day, k, theme).headline("Ask it backwards, and most of the model's lean disappears.")
    a.dek("Some models favour whichever answer comes first. Our answer scale listed the Republican side first.")
    glm = items[0]
    a.at_bottom(charts.stats_height(150, rule=True) + 40 + 80)
    charts.stats(a, [(pct(glm[1]), "GLM, asked one way"), (pct(glm[2]), "asked both ways")], px=150, rule=True)
    a.text("Leftover lean toward Republicans, as a share of the model's typical reaction.", px=30, color=theme.ink2)
    a.source("Mirror test: 16 news stories, each with the parties swapped, 28 simulated voter types. Sep 2026.")

    b = Slide(day, f"{k} · THE TEST", theme).headline("The mirror test.")
    b.text("Each news story is shown twice, with the parties swapped. A fair model's reactions mirror each other "
           "exactly. Whatever is left over is a built-in lean.", px=40, color=theme.ink2, after=1.0)
    b.text("Then we asked every question in both orders: the answer scale as written, and reversed.", px=40,
           color=theme.ink2, after=1.0)
    b.text("If the lean flips with the order, it comes from the order, not from politics.", "serif", 600, 50)
    b.source("Scale: strongly toward the Republican to strongly toward the Democrat, five steps.")

    c = Slide(day, f"{k} · RESULTS", theme).headline("Averaging both orders cancels most of it.", px=80)
    charts.legend_dots(c, [("Asked one way", theme.data, False), ("Both ways, averaged", theme.ai, True)])
    c.y += 10
    charts.dumbbell(c, items, 80, 500, "leans Republican", "leans Democratic", pct)
    c.text("Kev, untuned, got worse. It failed other checks too.", px=30, color=theme.ink2)
    c.source("Lean = average of the two mirrored reactions, as a share of the model's typical reaction size.")

    d = Slide(day, f"{k} · WHAT WE CHANGED", theme).headline("So every question is asked both ways.")
    d.text("It doubles the cost of each answer, still a few cents per thousand. A fixed correction instead of "
           "asking twice removed only about two-thirds of GLM's lean, because the lean grows with the size of "
           "the reaction.", px=40, color=theme.ink2, after=1.2)
    d.text("Next: the models know which way voters move, not how far.", "serif", 600, 48, after=1.2)
    closing(d)

    names = ", ".join(f"{n} {pct(b1)} → {pct(b2)}" for n, b1, b2 in items[:3])
    return Post(day, "Lab notes 03: ask it backwards", [
        (a, f"Ask it backwards and most of the model's lean disappears. GLM asked one way: {pct(glm[1])}; asked both "
            f"ways: {pct(glm[2])}."),
        (b, "The mirror test: each story shown twice with the parties swapped, and every question asked in both "
            "orders."),
        (c, f"Dot chart of each model's leftover lean, one way versus both ways averaged: {names}; the rest near zero "
            "except untuned Kev, which got worse."),
        (d, "So every question is asked both ways. A fixed correction removed only about two-thirds of the lean."),
    ], f"""Ask it backwards, and most of the model's lean disappears.

Some models favour whichever answer comes first. Our answer scale listed the Republican side first, so a model with that habit looks like it leans Republican.

The mirror test: 16 news stories, each shown twice with the parties swapped. A fair model's reactions mirror each other; whatever is left over is a built-in lean. Then we asked every question in both orders.

Asked one way, GLM's leftover lean was {pct(glm[1])} of its typical reaction. Asked both ways and averaged: {pct(glm[2])}. DeepSeek went from {pct(items[1][1])} to {pct(items[1][2])}, MiMo from {pct(items[2][1])} to {pct(items[2][2])}.

So every question in our forecast is asked both ways. It doubles the cost of each answer, still a few cents per thousand.

Lab notes 03 of the making-of. The forecast goes public on Monday 12 October.

{LABEL}.

#midterms2026 #elections #socialsimulation #dataviz""", [
        f"Ask it backwards and most of the model's lean disappears. Asked one way, GLM's leftover lean was "
        f"{pct(glm[1])} of its typical reaction. Asked both ways and averaged: {pct(glm[2])}. {LABEL}.",
        "Why: some models favour whichever answer comes first, and our scale listed the Republican side first. Swap "
        "the order and the lean flips with it.",
        f"DeepSeek went from {pct(items[1][1])} to {pct(items[1][2])}, MiMo from {pct(items[2][1])} to "
        f"{pct(items[2][2])}. So every question in our forecast is asked both ways.",
    ])


EPISODES = {1: ep01, 2: ep02, 3: ep03}


def contact_sheet(paths: list[Path], out: Path, scale: float = 0.4, gap: int = 16) -> Path:
    """All slides of a post side by side at reduced size, for review on a phone."""
    ims = [Image.open(p) for p in paths]
    w, h = int(ims[0].width * scale), int(ims[0].height * scale)
    sheet = Image.new("RGB", (len(ims) * (w + gap) + gap, h + 2 * gap), "#D9D6CE")
    for i, im in enumerate(ims):
        sheet.paste(im.resize((w, h), Image.LANCZOS), (gap + i * (w + gap), gap))
    sheet.save(out, quality=90)
    return out


def write(n: int, theme: Theme = LAB) -> Path:
    post = EPISODES[n](theme)
    out = KITS / f"{n:02d}"
    lines = [f"# {post.title}", "", f"Draft for Matteo's approval. Planned date: {post.day:%a %d %b %Y}.", ""]
    problems = []
    paths = [sl.save(out / f"slide-{i}.jpg") for i, (sl, _) in enumerate(post.slides, 1)]
    contact_sheet(paths, out / "contact.jpg")
    problems += [f"Instagram caption: {p}" for p in text.check(post.instagram, allow=post.allow)]
    if len(post.instagram) > LIMITS["instagram"]:
        problems.append(f"Instagram caption: {len(post.instagram)} characters (limit {LIMITS['instagram']})")
    problems += [f"Thread post 1: {p}" for p in text.check(post.thread[0], allow=post.allow)]
    for i, t in enumerate(post.thread, 1):
        problems += [f"Thread post {i}: {p}" for p in text.check(t, caption=False, allow=post.allow)]
        if len(t) > LIMITS["thread"]:
            problems.append(f"Thread post {i}: {len(t)} characters (limit {LIMITS['thread']})")
    lines += ["## Checks", ""] + ([f"- {p}" for p in problems] or ["- All rules pass."]) + [""]
    notes = sorted({n for t in [post.instagram, *post.thread] + [a for _, a in post.slides] for n in text.style(t)})
    lines += ["## Style notes", ""] + ([f"- {n}" for n in notes] or ["- None."]) + [""]
    lines += ["## Slides and alt text", ""] + [f"{i}. `slide-{i}.jpg`: {alt}" for i, (_, alt) in
                                             enumerate(post.slides, 1)] + [""]
    lines += ["## Instagram caption", "", post.instagram, ""]
    lines += ["## Thread for X, Threads and Bluesky", ""]
    lines += [f"{i}/ ({len(t)} characters) {t}" for i, t in enumerate(post.thread, 1)] + [""]
    (out / "post.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"{out}: {len(post.slides)} slides; " + ("; ".join(problems) if problems else "all rules pass"))
    return out


if __name__ == "__main__":
    for arg in sys.argv[1:] or ["1", "2", "3"]:
        write(int(arg))
