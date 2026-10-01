"""Lab notes, the making-of series (docs/content-plan.md §3): python -m simlab.publish.labnotes 1 2 3

Writes kits/labnotes/NN/: the slides (JPEG 1080x1350) and post.md with the Instagram caption, alt text, the thread for
X, Threads and Bluesky, and the rule checks. Drafts for Matteo's approval; nothing here posts anything.
Test-bench numbers come from runs/scorecard.jsonl; the outlet-name test was printed, not saved (CHANGELOG, 28 Sep).
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from PIL import Image

from ..core import RUNS
from ..scorecard import latest
from . import charts, text
from .frame import DISCLAIMER, LABEL, SITE, Slide, Theme
from .themes import LAB

KITS = RUNS.parent / "kits" / "labnotes"
ARTICLES = Path(__file__).parent / "articles"  # the website versions (labnotes-NN.md), read by the site from post.md
WORDS = (600, 900)  # Matteo, 1 Oct: web articles of about 600-900 words, slides beside the claims
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

    a = Slide(day, k, theme).headline("Before forecasting a single race, we asked six models to behave like "
                                      "voters.", px=80)
    a.dek("Four tests, scored against what really happened.", px=40)
    a.at_bottom(charts.stats_height(rule=True))
    charts.stats(a, [("6", "models"), ("4", "tests"), ("$1.52", "total cost")], rule=True)
    a.source("Test bench, 27–28 Sep 2026.")

    b = Slide(day, f"{k} · THE TESTS", theme).headline("Four questions.", px=88)
    b.y += 10
    for n, q in enumerate(["Does a football score move a Senate race?", "If the parties swap, does the reaction swap?",
                           "Does it move the way people really moved?", "Does it know how groups voted in 2024?"], 1):
        b.text(f"{n}  {q}", "serif", 600, 46, after=0.7)
    b.source("Jev 1.13, Kev 4B, GLM-5.3 Flash, MiMo-V2.6 Flash, DeepSeek V4.1 Flash, GPT-6 Luna. 27–28 Sep 2026.")

    c = Slide(day, f"{k} · WHAT WE FOUND", theme).headline("Each was good at one thing. None at everything.", px=80)
    charts.rows(c, [
        ("Ignore news that doesn’t matter", "Jev", f"{null_jev:.0%} of the time"),
        ("Which way a group moves", "GLM-5.3 Flash", f"{glm_dir * 13:.0f} of 13 events"),
        ("How far it moves", "None", "Sizes barely track reality"),
        ("How groups voted", "Plain statistics", "Better than every model"),
    ])
    c.source("Scores: null, mirror, events and fidelity tests, 27–28 Sep 2026. Off-the-shelf models.")

    d = Slide(day, f"{k} · THE BLIND SPOT", theme).headline("They all got the same things wrong.", px=84)
    d.text("Too calm about real shocks: COVID, January 6, the fall of Kabul. Too excited about spectacles: the "
           "debates.", px=40, color=theme.ink2, after=1.2)
    d.note("So the size of every reaction comes from shifts that were actually measured.", width=700)
    d.source("19 real events, 2012–2026. Errors correlate +0.88 to +0.97 between models.")

    e = Slide(day, f"{k} · WHAT IT MEANS", theme).headline("Statistics set the starting line. The simulation "
                                                           "moves it.", px=80)
    e.text("Each day the voter personas react to the news. Each week the latest poll average decides how much of "
           "that shift to keep.", px=38, color=theme.ink2, after=1.2)
    e.note("Tomorrow: one model changed 41% of its answers when we swapped “Fox News” for “MSNBC”.", width=760)
    e.source("Race starting points: statistics. Each voter group's starting split: a model trained on real survey "
             "answers.")

    return Post(day, "Lab notes 01: six models, four tests, one shared blind spot", [
        (a, "Before forecasting a single race, we asked six models to behave like voters: four tests, scored against "
            "what really happened. Six models, four tests, $1.52 in total."),
        (b, "Four questions: does a football score move a Senate race; if the parties swap, does the reaction swap; "
            "does it move the way people really moved; does it know how groups voted in 2024."),
        (c, f"What we found: Jev ignores irrelevant news {null_jev:.0%} of the time; GLM gets the direction right on "
            f"{glm_dir * 13:.0f} of 13 events; no model gets the size right; plain statistics know how groups voted "
            "better than every model."),
        (d, "They all got the same things wrong: too calm about real shocks like COVID and January 6, too excited "
            "about the debates. So reaction sizes come from shifts that were actually measured."),
        (e, "Statistics set the starting line; the simulation moves it. Voter personas react to each day's news, and "
            "each week the poll average decides how much of the shift to keep."),
    ], f"""Before forecasting a single race, we asked six models to behave like voters.

Four questions. Does a football score move a Senate race? It shouldn't. If you swap the parties in a story, does the reaction swap? Does a model move the way people actually moved on 19 events since 2012? Does it know how groups voted in 2024?

Each model was good at one thing and none at everything. And they all failed the same way: too calm about real shocks like COVID and January 6, too excited about spectacles like debates.

So statistics set where each race starts, a model trained on real survey answers sets each voter group's starting split, and the size of every reaction comes from shifts that were actually measured. The voter personas decide which way the news pushes each group.

The whole test bench cost $1.52.

#midterms2026 #elections

{DISCLAIMER}""", [
        f"Before forecasting the 2026 midterms, we asked six models to behave like voters and tested them on four "
        f"questions. What we found. {LABEL}.",
        f"Ignoring news that doesn't matter: Jev, {null_jev:.0%} of the time. An untuned Kev reacted to about 1 story "
        f"in {1 / null_kev:.0f}.",
        f"Which way a group moves: GLM-5.3 Flash was right on {glm_dir * 13:.0f} of 13 real events. How far: no model.",
        "Every model was too calm about real shocks (COVID, January 6) and too excited about spectacles (debates). So "
        "reaction sizes come from shifts that were actually measured.",
        f"Statistics set the starting line; the simulation moves it. The test bench cost $1.52. How it works: {SITE}",
    ], allow=("survey", "poll"))  # real survey answers (the personas' source) and real polls (the poll average)


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
    d.note("Tomorrow: a model looked Republican because of the order we listed the answers in.", width=760)
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

#midterms2026 #elections

{DISCLAIMER}""", [
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
    d.note("Next in Lab notes: the models know which way voters move, not how far.", width=760)
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

#midterms2026 #elections

{DISCLAIMER}""", [
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


def signed(v: float) -> str:
    return f"{'−' if v < 0 else '+'}{abs(v):.0f}%"


def article_values(n: int) -> dict[str, str]:
    """The numbers the website articles quote, from the same scorecard as the slides."""
    s = latest()
    if n == 1:
        return {"null_jev": f"{min(s[('null', 'jev')]['support_p_no_change'], s[('null', 'jev')]['turnout_p_no_change']):.0%}",
                "glm_dir": f"{s[('events', 'glm')]['sign_accuracy_nonnull'] * 13:.0f}",
                "kev_noise": f"{1 / (1 - s[('null', 'kev')]['support_p_no_change']):.0f}"}
    if n == 3:
        lean = lambda m: 100 * s[("mirror", m)]["mean_asymmetry"] / s[("mirror", m)]["mean_abs_reaction"]
        return {"glm1": f"{abs(lean('glm1')):.0f}%", "glm2": f"{abs(lean('glm')):.0f}%",
                "ds1": signed(lean("deepseek1")), "ds2": signed(lean("deepseek")),
                "mimo1": signed(lean("mimo1")), "mimo2": signed(lean("mimo")),
                "kev1": signed(lean("kev1")), "kev2": signed(lean("kev"))}
    return {}


def article(n: int) -> str:
    """The note's website article with its numbers filled in; {{slide:N}} markers are left for the site."""
    path = ARTICLES / f"labnotes-{n:02d}.md"
    if not path.exists():
        return ""
    values = article_values(n)
    return re.sub(r"(?<!\{)\{(\w+)\}(?!\})", lambda m: values[m.group(1)], path.read_text(encoding="utf-8")).strip()


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
    art = article(n)
    if art:
        problems += [f"Website article: {p}" for p in text.check(art, caption=False, allow=post.allow)]
        words = len(re.sub(r"\{\{slide:\d+\}\}|#### In detail", " ", art).split())
        if not WORDS[0] <= words <= WORDS[1]:
            problems.append(f"Website article: {words} words (aim {WORDS[0]}–{WORDS[1]})")
    lines += ["## Checks", ""] + ([f"- {p}" for p in problems] or ["- All rules pass."]) + [""]
    notes = sorted({n for t in [post.instagram, *post.thread, art] + [a for _, a in post.slides] for n in text.style(t)})
    lines += ["## Style notes", ""] + ([f"- {n}" for n in notes] or ["- None."]) + [""]
    lines += ["## Slides and alt text", ""] + [f"{i}. `slide-{i}.jpg`: {alt}" for i, (_, alt) in
                                             enumerate(post.slides, 1)] + [""]
    lines += ["## Instagram caption", "", post.instagram, ""]
    lines += ["## Thread for X, Threads and Bluesky", ""]
    lines += [f"{i}/ ({len(t)} characters) {t}" for i, t in enumerate(post.thread, 1)] + [""]
    if art:
        lines += ["## Website article", "", art, ""]
    (out / "post.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"{out}: {len(post.slides)} slides; " + ("; ".join(problems) if problems else "all rules pass"))
    return out


if __name__ == "__main__":
    for arg in sys.argv[1:] or ["1", "2", "3"]:
        write(int(arg))
