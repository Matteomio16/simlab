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


def ep01(theme: Theme = LAB) -> Post:
    s, day = latest(), date(2026, 10, 3)
    null_jev = min(s[("null", "jev")]["support_p_no_change"], s[("null", "jev")]["turnout_p_no_change"])
    null_kev = 1 - s[("null", "kev")]["support_p_no_change"]
    glm_dir = s[("events", "glm")]["sign_accuracy_nonnull"]
    k = "LAB NOTES 01"

    a = Slide(day, k, theme).headline("In April we simulated Hungary’s election. We called the winner and missed "
                                      "by 16 points.", px=80)
    a.dek("TISZA’s share of the vote")
    charts.hbars(a, [("Our simulation", 36.7, theme.ai), ("The result", 53.2, theme.data)], 60,
                 lambda v: f"{v:.1f}%")
    a.y += 30
    a.text("So this time nothing goes into the forecast until it has been tested against what really happened.",
           "serif", 600, 44)
    a.source("Hungary, April 2026. Simulation: 45 simulated voters, run before the vote. Result: the official "
             "count.")

    b = Slide(day, f"{k} · THE TESTS", theme).headline("Six models, four questions.", px=84)
    b.y += 10
    for n, (t1, t2) in enumerate([
            ("Does a football score move a Senate race?", "It shouldn’t. 20 stories that matter to nobody’s vote."),
            ("If the parties swap, does the reaction swap?", "16 stories, each told twice with the parties reversed."),
            ("Does it move the way people really moved?", "19 events since 2012 whose effect on opinion was measured."),
            ("Does it know how groups voted in 2024?", "Checked against the real vote, group by group.")], 1):
        b.text(f"{n}  {t1}", "serif", 600, 44, after=0.2, width=b.width)
        b.text(t2, px=34, color=theme.ink2, after=0.8, x=132, width=b.width - 60)
    b.source("Jev 1.13, Kev 4B, GLM-5.3 Flash, MiMo-V2.6 Flash, DeepSeek V4.1 Flash, GPT-6 Luna. 27–28 Sep 2026. "
             "Total cost: $1.52.")

    c = Slide(day, f"{k} · WHAT WE FOUND", theme).headline("Each model was good at one thing. None at everything.",
                                                           px=76)
    charts.rows(c, [
        ("Ignore news that doesn’t matter", "Jev", f"“No change” to {null_jev:.0%} of it"),
        ("Which way a group moves", "GLM-5.3 Flash", f"Right direction on {glm_dir * 13:.0f} of 13 events"),
        ("How far it moves", "None", "GLM’s sizes barely track reality (correlation 0.26)"),
        ("How groups voted", "Plain statistics", "Beat every off-the-shelf model"),
    ])
    c.source("Scores: null, mirror, events and fidelity tests, 27–28 Sep 2026.")

    d = Slide(day, f"{k} · THE BLIND SPOT", theme).headline("They all got the same things wrong.", px=84)
    d.text("Every model under-reacted to real shocks: COVID, January 6, the fall of Kabul. And every one over-reacted "
           "to media spectacles: the Access Hollywood tape, the debates.", px=40, color=theme.ink2, after=1.0)
    d.text("Averaging them doesn’t cancel the error. So reaction sizes come from shifts that were actually measured, "
           "never from a model.", "serif", 600, 44)
    d.source("19 real events, 2012–2026. Errors correlate +0.88 to +0.97 between models.")

    e = Slide(day, f"{k} · WHAT IT MEANS", theme).headline("Statistics decide where each race starts. The simulation "
                                                           "only moves it.", px=76)
    e.text("The starting point of every race comes from past results, the economy and the poll average. Each voter "
           "group’s starting split comes from Kev, a model we trained on real survey answers. Synthetic voters then "
           "react to each day’s news, and every week the latest poll average decides how much of that to keep.",
           px=36, color=theme.ink2, after=1.0)
    e.text("Tomorrow: one model changed its answer on 41% of headlines when we swapped “Fox News” for “MSNBC”.",
           "serif", 600, 42)
    e.source("Forecasts go public on Monday 12 October.")

    return Post(day, "Lab notes 01: we missed Hungary by 16 points, so we tested everything", [
        (a, "In April we simulated Hungary's election: we called the winner and missed by 16 points. Bar chart of "
            "TISZA's share: our simulation 36.7 percent, the result 53.2 percent."),
        (b, "Six models, four questions: does irrelevant news move a race; does the reaction swap when the parties "
            "swap; does it move the way people really moved on 19 measured events; does it know how groups voted in "
            "2024."),
        (c, f"What we found. Ignoring irrelevant news: Jev, no change to {null_jev:.0%}. Direction of a reaction: "
            f"GLM, right on {glm_dir * 13:.0f} of 13 events. Size of a reaction: no model. How groups voted: plain "
            "statistics."),
        (d, "Every model under-reacted to real shocks like COVID and January 6 and over-reacted to media spectacles "
            "like the debates, so reaction sizes come from measured shifts, never from a model."),
        (e, "Statistics decide where each race starts; the simulation only moves it, and the weekly poll average "
            "decides how much movement to keep."),
    ], f"""In April we simulated Hungary's election. We called the winner and missed the size by 16 points.

So before the midterms we put six models through four questions. Does a football score move a Senate race? (It shouldn't.) If you swap the parties in a story, does the reaction swap? Does the model move the way people actually moved on 19 events since 2012? Does it know how groups voted in 2024?

Each model was good at one thing and none at everything. Jev ignores news that doesn't matter ({null_jev:.0%} of the time). GLM gets the direction of a reaction right ({glm_dir * 13:.0f} of 13 real events). Nobody gets the size right.

And they all fail the same way: too calm about real shocks like COVID and January 6, too excited about media spectacles like debates. Averaging them doesn't fix that. So in our forecast, statistics decide where each race starts, reaction sizes come from shifts that were actually measured, and the synthetic voters only decide which way the news pushes each group.

The whole test bench cost $1.52. We'll keep publishing what fails as well as what works.

{LABEL}.

#midterms2026 #elections #socialsimulation #dataviz""", [
        f"In April we simulated Hungary's election. We called the winner and missed the size by 16 points. So before "
        f"the midterms we tested six models on four questions. What we found, in five posts. {LABEL}.",
        f"Ignoring news that doesn't matter: Jev said “no change” {null_jev:.0%} of the time. An untuned Kev reacted to "
        f"about 1 story in {1 / null_kev:.0f}.",
        f"Which way a group moves: GLM-5.3 Flash was right on {glm_dir * 13:.0f} of 13 real events. How far: no model. "
        "GLM's sizes barely track reality (0.26).",
        "Every model under-reacted to real shocks (COVID, January 6) and over-reacted to spectacles (debates). "
        "Averaging them doesn't cancel it, so reaction sizes come from measured shifts.",
        "So statistics set where each race starts and the simulation only moves it. The test bench cost $1.52. "
        "Forecasts go public on 12 October.",
    ], allow=("survey", "poll"))  # real survey answers (Kev's training data) and real polls (the weekly check)


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
    d.text("Before any model reads the news, we strip the outlet and rewrite each story as a short, neutral event "
           "card. People read the source as a clue too; a forecast can't afford to.",
           px=40, color=theme.ink2, after=1.2)
    d.text("Tomorrow: a model looked Republican because of the order we listed the answers in.", "serif", 600, 44)
    d.source("Forecasts go public on Monday 12 October.")

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

The models read the outlet as a clue about the story. People take the same shortcut; a forecast can't. So no model in our forecast ever sees an outlet's name: every story becomes a short, neutral event card first.

Forecasts go public on Monday 12 October.

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
    d.text("Next in Lab notes: the models know which way voters move, not how far.", "serif", 600, 44)
    d.source("Forecasts go public on Monday 12 October.")

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

So every question in our forecast is asked both ways. It doubles the cost of each answer, still a few cents per thousand. A fixed correction would have been cheaper, and it removed only two-thirds of the lean.

Forecasts go public on Monday 12 October.

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
