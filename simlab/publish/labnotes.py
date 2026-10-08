"""Lab notes, the making-of series (docs/content-plan.md §3): python -m simlab.publish.labnotes 1 2 3

Writes kits/labnotes/NN/: the slides (JPEG 1080x1350) and post.md with the Instagram caption, alt text, the thread for
X, Threads and Bluesky, and the rule checks. Drafts for Matteo's approval; nothing here posts anything.
Test-bench numbers come from runs/scorecard.jsonl; the outlet-name test was printed, not saved (CHANGELOG, 28 Sep).
"""
from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import matplotlib.pyplot as plt
from PIL import Image

from ..core import RUNS
from ..scorecard import latest
from . import charts, text
from .frame import DISCLAIMER, LABEL, MARGIN, SITE, Slide, Theme, pt, typeset
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
    short: str = ""  # X and Bluesky
    more: str = ""  # added for Threads
    platform: dict | None = None  # optional "x", "threads" texts and "topic", "first_comment"


def ep01(theme: Theme = LAB) -> Post:
    s, day = latest(), date(2026, 10, 3)
    null_jev = min(s[("null", "jev")]["support_p_no_change"], s[("null", "jev")]["turnout_p_no_change"])
    null_kev = 1 - s[("null", "kev")]["support_p_no_change"]
    glm_dir = s[("events", "glm")]["sign_accuracy_nonnull"]
    k = "Lab notes 01"
    new = lambda: Slide(day, "", theme, series=k)

    a = new().headline("Before forecasting a single race, we asked six models to behave like voters.", px=80)
    a.dek("Four tests, scored against what really happened.", px=40)
    a.at_bottom(charts.stats_height(rule=True))
    charts.stats(a, [("6", "models"), ("4", "tests"), ("$1.52", "total cost")], rule=True)
    a.source("Test bench, 27–28 Sep 2026.")

    b = new().headline("Four questions we asked every model.", px=84)
    b.y += 10
    for q in ["Does a football score move a Senate race?", "If the parties swap, does the reaction swap?",
              "Does it move the way people really moved?", "Does it know how groups voted in 2024?"]:
        b.text(q, "serif", 600, 46, after=0.7)
    b.source("Jev 1.13, Kev 4B, GLM-5.3 Flash, MiMo-V2.6 Flash, DeepSeek V4.1 Flash, GPT-6 Luna. 27–28 Sep 2026.")

    c = new().headline("Some got the direction right. None got the size.", px=80)
    charts.rows(c, [
        ("Ignore news that doesn’t matter", "Jev", f"{null_jev:.0%} of the time"),
        ("Which way a group moves", "GLM-5.3 Flash", f"{glm_dir * 13:.0f} of 13 events"),
        ("How far it moves", "None", "Sizes barely track reality"),
        ("How groups voted", "Plain statistics", "Better than every model"),
    ])
    c.source("Scores: null, mirror, events and fidelity tests, 27–28 Sep 2026. Off-the-shelf models.")

    d = new().headline("They all got the same things wrong.", px=84)
    d.text("Too calm about real shocks: COVID, January 6, the fall of Kabul. Too excited about spectacles: the "
           "debates.", px=40, color=theme.ink2, after=1.2)
    d.note("So the size of every reaction comes from how people really moved.", width=700)
    d.source("19 real events, 2012–2026. Errors correlate +0.88 to +0.97 between models.")

    e = new().headline("Real history sets the size of every reaction.", px=80)
    e.text("Statistics set where each race starts and the voter personas react to each day’s news. How far each "
           "group moves comes from how people really moved in past events.", px=38, color=theme.ink2, after=1.2)
    e.note("Tomorrow: one model changed 41% of its answers when we swapped “Fox News” for “MSNBC”.", width=760)
    e.source("How each group of voters usually splits between the parties: a model trained on real survey answers.")

    return Post(day, "Lab notes 01: six models, four tests, one shared blind spot", [
        (a, "Before forecasting a single race, we asked six models to behave like voters: four tests, scored against "
            "what really happened. Six models, four tests, $1.52 in total."),
        (b, "Four questions we asked every model: does a football score move a Senate race; if the parties swap, does "
            "the reaction swap; does it move the way people really moved; does it know how groups voted in 2024."),
        (c, f"Some got the direction right, none got the size: Jev ignores irrelevant news {null_jev:.0%} of the "
            f"time; GLM gets the direction right on {glm_dir * 13:.0f} of 13 events; no model gets the size right; "
            "plain statistics know how groups voted better than every model."),
        (d, "They all got the same things wrong: too calm about real shocks like COVID and January 6, too excited "
            "about the debates. So the size of every reaction comes from how people really moved."),
        (e, "Real history sets the size of every reaction. Statistics set where each race starts, the voter "
            "personas react to each day's news, and how far each group moves comes from past events."),
    ], f"""Before forecasting a single race, we wanted to know whether a model can react to the news the way a group of voters really would. We put six models through four tests. Does a football score move a Senate race? It shouldn't. If you swap the parties in a story, does the reaction swap too? Does the model move the way people actually moved on 19 real events since 2012? Does it know how groups voted in 2024?

Some got the direction right. Jev ignored irrelevant news {null_jev:.0%} of the time, and GLM-5.3 Flash read the direction of {glm_dir * 13:.0f} out of 13 real events correctly. None of them got the size of a reaction right.

They also failed in the same way. They stayed calm where people were shaken, like COVID and January 6, and got excited where people shrugged, like the debates. Averaging them doesn't fix that.

In our forecast, statistics set where each race starts, and a model trained on real survey answers estimates how each group of voters usually splits between the parties. The size of every reaction comes from how people really moved in past events, and the voter personas decide which way the news pushes each group.

The whole test cost $1.52. Tomorrow we'll show what happened when we put a different TV channel's name on the same headline.

#midterms2026 #elections

{DISCLAIMER}""", [
        f"Before forecasting a single race, we wanted to know whether a model can react to the news the way a group "
        f"of voters really would. So we tested six of them on four questions. {LABEL}.",
        f"Jev ignored irrelevant news {null_jev:.0%} of the time, and GLM-5.3 Flash read the direction of "
        f"{glm_dir * 13:.0f} of 13 real events. None of them got the size of a reaction right.",
        "They also failed the same way: calm where people were shaken (COVID, January 6), excited where people "
        "shrugged (the debates). Real history sets the size of every reaction instead.",
        f"The whole test cost $1.52, and an untuned Kev reacted to about 1 irrelevant story in {1 / null_kev:.0f}. "
        f"More in our Lab notes: {SITE}",
    ], allow=("survey", "poll"))  # real survey answers (the personas' source) and real polls (the poll average)


def ep02(theme: Theme = LAB) -> Post:
    day, k = date(2026, 10, 4), "Lab notes 02"
    gap = {"GLM": 0.30, "Jev": 0.15}
    flips = {"GLM": 0.41, "Jev": 0.15}
    new = lambda: Slide(day, "", theme, series=k)

    a = new()
    a.y += 20
    a.text(f"{flips['GLM']:.0%}", "sans", 800, 300, leading=1.0, after=0.15)
    a.headline("of headlines got a different answer when we swapped “Fox News” for “MSNBC.”", px=76)
    a.dek("Same story, same words. We asked a model which party the news helps; only the outlet’s name changed.")
    a.source("80 real headlines about 2026 Senate races, September 2026. Model: GLM-5.3 Flash.")

    b = new().headline("The same headline, shown three ways.", px=84)
    b.y += 10
    for label, body in [("No outlet", "The headline on its own."), ("“Fox News”", "The same headline, credited to Fox."),
                        ("“MSNBC”", "The same headline, credited to MSNBC.")]:
        b.text(label, "serif", 600, 50, after=0.15)
        b.text(body, px=36, color=theme.ink2, after=0.9)
    b.note("Same event, so the answer shouldn’t move. Two models, 80 headlines each.", width=760)
    b.source("Headlines: Google News, September 2026. Question: which party does this news help?")

    c = new().headline("Credited to MSNBC, GLM leaned 30 points more Democratic.", px=76)
    charts.hbars(c, [(m, 100 * v, theme.data) for m, v in gap.items()], 50, lambda v: f"+{v:.0f} points",
                 title="Shift toward “helps Democrats” when the outlet is MSNBC instead of Fox")
    c.y += 20
    charts.hbars(c, [(m, 100 * v, theme.data) for m, v in flips.items()], 50, lambda v: f"{v:.0f}%",
                 title="Headlines where the top answer flipped")
    c.source("Shift: change in P(helps Democrats) minus P(helps Republicans), scale −100 to +100. 80 headlines.")

    d = new().headline("Our models never see an outlet’s name.", px=84)
    d.text("Before any model reads the news, we strip the outlet and rewrite the story as a short, neutral event "
           "card. A forecast shouldn’t care where you read the news.", px=40, color=theme.ink2, after=1.2)
    d.note("Tomorrow: a model looked Republican because of the order we listed the answers in.", width=760)
    d.source("Forecasts go public on Monday 12 October.")

    return Post(day, "Lab notes 02: the outlet name changed the answer", [
        (a, "41 percent of headlines got a different answer when we swapped Fox News for MSNBC. Same story; only the "
            "outlet's name changed."),
        (b, "The same headline, shown three ways: with no outlet, credited to Fox News, and credited to MSNBC."),
        (c, "Credited to MSNBC, GLM leaned 30 points more Democratic. Bar charts: shift toward helps Democrats, GLM "
            "plus 30 points, Jev plus 15; top answer flipped, GLM 41 percent, Jev 15 percent."),
        (d, "Our models never see an outlet's name: stories become short neutral event cards first."),
    ], f"""We took 80 real headlines about this year's Senate races and showed each one to two models three times: once on its own, once credited to Fox News and once credited to MSNBC. The words never changed. Then we asked which party the news helps.

If a model judges the event, the answer should stay put. It didn't. Credited to MSNBC instead of Fox, the same headline made GLM lean 30 points more towards "helps Democrats", and on 41% of headlines its answer flipped completely. Jev moved about half as much.

This says nothing about either channel. It shows that the models read the outlet as a clue about the story, the way many readers do.

Our models never see where a story came from. Each story is first rewritten as a short, neutral description of what happened, because a forecast shouldn't care where you read the news.

#midterms2026 #elections

{DISCLAIMER}""", [
        f"We showed two models the same 80 headlines, credited first to Fox News, then to MSNBC. One of them changed its "
        f"answer about which party the news helps on 41% of them. {LABEL}.",
        "It isn't about either channel. The models have learned to read the outlet as a clue about the story, the way "
        "many readers do.",
        "Our models never see where a story came from; each one becomes a short, neutral description first. A forecast "
        "shouldn't care where you read the news.",
    ])


def ep03(theme: Theme = LAB) -> Post:
    s, day, k = latest(), date(2026, 10, 5), "Lab notes 03"
    lean = lambda m: s[("mirror", m)]["mean_asymmetry"] / s[("mirror", m)]["mean_abs_reaction"]
    order = ["glm", "deepseek", "mimo", "luna", "jev"]  # untuned Kev isn't used in the forecast (Matteo, 4 Oct)
    items = [(MODELS[m], 100 * lean(m + "1"), 100 * lean(m)) for m in order]
    pct = lambda v: f"{v:+.0f}%".replace("-", "−") if v else "0"
    glm = items[0]
    new = lambda: Slide(day, "", theme, series=k)

    a = new().headline("One model looked Republican. It was the order of the answers.", px=84)
    a.dek("We test every model for a built-in party lean.", px=40)
    a.at_bottom(charts.stats_height(150, rule=True) + 40 + 80)
    charts.stats(a, [(pct(glm[1]), "GLM, asked one way"), (pct(glm[2]), "asked both ways")], px=150, rule=True)
    a.text("Built-in lean toward Republicans, as a share of a typical reaction.", px=30, color=theme.ink2)
    a.source("Mirror test: 16 news stories, each with the parties swapped, 28 voter personas. Sep 2026.")

    b = new().headline("We tell every story twice, with the parties swapped.", px=80)
    b.text("A fair model mirrors itself exactly.", px=40, color=theme.ink2, after=1.0)
    b.note("Then every question in both orders. If the lean flips with the order, it isn’t politics.", width=760)
    b.source("Scale: strongly toward the Republican to strongly toward the Democrat, five steps.")

    c = new().headline("Averaging both orders cancels most of it.", px=80)
    charts.legend_dots(c, [("Asked one way", theme.data, False), ("Both ways, averaged", theme.ai, True)])
    c.y += 10
    charts.dumbbell(c, items, 80, 500, "leans Republican", "leans Democratic", pct)
    c.source("Lean = average of the two mirrored reactions, as a share of the model's typical reaction size.")

    d = new().headline("Now every question is asked both ways.", px=84)
    d.text("Asking twice costs a few cents per thousand answers. A fixed correction removed only two-thirds of "
           "the lean.", px=40, color=theme.ink2, after=1.2)
    d.note("Every question, both ways, for every model.", width=640)
    d.source("Forecasts go public on Monday 12 October.")

    names = ", ".join(f"{n} {pct(b1)} → {pct(b2)}" for n, b1, b2 in items[:3])
    return Post(day, "Lab notes 03: one model looked Republican", [
        (a, f"One model looked Republican. It was the order of the answers. We test every model for a built-in party "
            f"lean: GLM's, as a share of a typical reaction, was {pct(glm[1])} asked one way and {pct(glm[2])} asked "
            f"both ways."),
        (b, "We tell every story twice, with the parties swapped; a fair model mirrors itself exactly. Then every "
            "question is asked in both orders."),
        (c, f"Dot chart of each model's built-in lean, as a share of a typical reaction, one way versus both ways "
            f"averaged: {names}; GPT-6 Luna and Jev near zero."),
        (d, "Now every question is asked both ways. A fixed correction removed only about two-thirds of the lean."),
    ], f"""For a while, one of our models looked Republican. Every model we use is tested for a built-in party lean: we tell each story twice with the parties swapped, and a fair model reacts the same way to both versions.

GLM didn't. Its lean was {pct(glm[1])} of a typical reaction. The cause turned out to be the answer scale, which listed the Republican side first; some models favour whichever answer comes first.

We asked every question both ways, once in each order, and averaged the two. GLM's lean dropped to {pct(glm[2])}, DeepSeek's went from {pct(items[1][1])} to {pct(items[1][2])} and MiMo's from {pct(items[2][1])} to {pct(items[2][2])}.

Now every question in our forecast is asked both ways. It costs a few cents per thousand answers and keeps the order of a question from tilting the numbers.

#midterms2026 #elections

{DISCLAIMER}""", [
        f"For a while, one of our models looked Republican, with a built-in lean of {pct(glm[1])} of a typical "
        f"reaction. It turned out to be the order of the answers. {LABEL}.",
        "Some models favour whichever answer comes first, and our scale listed the Republican side first. Asked both "
        f"ways and averaged, the lean fell to {pct(glm[2])}.",
        f"DeepSeek went from {pct(items[1][1])} to {pct(items[1][2])}, MiMo from {pct(items[2][1])} to "
        f"{pct(items[2][2])}. Now every question in our forecast is asked both ways.",
    ])


def ep04(theme: Theme = LAB) -> Post:
    """Direction right, size wrong (content-plan §3, no. 4). Untuned Kev stays out (Matteo, 4 Oct)."""
    s, day, k = latest(), date(2026, 10, 6), "Lab notes 04"
    order = ["glm", "mimo", "luna", "jev", "deepseek"]
    hits = {m: round(13 * s[("events", m)]["sign_accuracy_nonnull"]) for m in order}
    scale = {m: s[("events", m)]["scale_points_per_unit"] for m in order}
    lo, hi = min(scale.values()), max(scale.values())
    others = sorted(hits[m] for m in order if m != "glm")
    new = lambda: Slide(day, "", theme, series=k)

    a = new().headline("The models knew which way voters would move.", px=84)
    a.dek("We checked them against 19 real events from 2012 to 2026, 13 of which moved opinion.", px=40)
    a.at_bottom(charts.stats_height(150, rule=True) + 40 + 80)
    charts.stats(a, [(f"{hits['glm']} of 13", "GLM, right direction"),
                     (f"{others[0]}–{others[-1]}", "the other four, of 13")], px=150, rule=True)
    a.text("Right direction: the model's reaction moved the same way real opinion did.", px=30, color=theme.ink2)
    a.source("Events test: 19 events with measured opinion shifts, 2012–2026. Test bench, 27–28 Sep 2026.")

    b = new().headline("Not how far.", px=104)
    b.text("One step on the same reaction scale was worth 5 real points for one model and 18 for another.", px=40,
           color=theme.ink2, after=1.0)
    charts.hbars(b, [(MODELS[m], scale[m], theme.ai) for m in sorted(order, key=scale.get)], 20,
                 lambda v: f"{v:.0f} pts", label_w=280)
    b.source("Points of real opinion shift per step of each model's answer, fitted on the same 19 events.")

    c = new().headline("So the size of every reaction comes from real history.", px=80)
    c.text("The models tell us which way a group reacts. How far it moves comes from 45 real past opinion shifts.",
           px=40, color=theme.ink2, after=1.2)
    c.note("From 12 October, a weekly check against the polls updates those sizes, state by state.", width=760)
    c.source("Forecasts go public on Monday 12 October.")

    return Post(day, "Lab notes 04: which way, not how far", [
        (a, f"The models knew which way voters would move. Against 19 real events from 2012 to 2026, 13 of which "
            f"moved opinion, GLM got the direction right {hits['glm']} times out of 13, and the other four "
            f"{others[0]} to {others[-1]}."),
        (b, f"Not how far: bar chart of how many real points one step of each model's answer was worth, from "
            f"{lo:.0f} to {hi:.0f}: " + ", ".join(f"{MODELS[m]} {scale[m]:.0f}" for m in sorted(order, key=scale.get))
            + "."),
        (c, "So the size of every reaction comes from real history: the models give the direction, 45 real past "
            "opinion shifts give the size, and from 12 October a weekly check against the polls updates it state by "
            "state."),
    ], f"""The models we tested are good at one thing and unreliable at another. We gave them 19 real events from 2012 to 2026, 13 of which measurably moved opinion, and asked how different voters would react.

They mostly got the direction right. GLM called it correctly for all {hits['glm']} events that moved opinion, and the other four models managed {others[0]} to {others[-1]}.

How far is another story. To turn a model's answer into real points, we had to fit a scale for each one, and one step on the same answer scale was worth {lo:.0f} points for one model and {hi:.0f} for another. The models agree on which way people move, not on how much.

So that's how our forecast splits the work. The models say which way each group of voters reacts to the news. How far they move comes from 45 real past opinion shifts, and from 12 October a weekly check against the polls updates those sizes, state by state.

All our Lab notes: notapoll.org/lab-notes

#midterms2026 #elections

{DISCLAIMER}""", [
        f"Our models knew which way voters would move: GLM got the direction right on {hits['glm']} of 13 real "
        f"events that moved opinion. {LABEL}.",
        f"Not how far: one step on the same answer scale was worth {lo:.0f} real points for one model and {hi:.0f} "
        "for another.",
        "So the models give the direction, and 45 real past opinion shifts give the size, checked against the polls "
        "every week from 12 October.",
    ], allow=("poll", "polls"), short=(f"Our models knew which way voters would move: GLM got the direction right on "
              f"all {hits['glm']} real events that moved opinion. Not how far: one step on the same scale was worth {lo:.0f} real points for one model, "
              f"{hi:.0f} for another. So sizes come from real history."),
        more=" More in our Lab notes: notapoll.org/lab-notes.")


def ep05(theme: Theme = LAB) -> Post:
    """Models flatten party differences (content-plan spare, swapped in for no. 5 by Matteo, 6 Oct). Numbers:
    docs/CHANGELOG.md, wider fidelity test (CES 2024, GLM asked both ways)."""
    day, k = date(2026, 10, 7), "Lab notes 05"
    rows = [("Democrats: approve of Biden", 83, 44), ("Democrats: economy got better", 53, 18),
            ("Republicans: approve of Biden", 4, 15), ("Democrats: voted Harris", 96, 93)]
    new = lambda: Slide(day, "", theme, series=k)

    a = new().headline("Ask a model how Democrats rate Biden, and they come out lukewarm.", px=80)
    a.dek("Approval of President Biden among Democrats, 2024.", px=40)
    a.at_bottom(charts.stats_height(150, rule=True) + 40 + 80)
    charts.stats(a, [("83%", "real survey answers"), ("44%", "GLM’s voter personas")], px=150, rule=True)
    a.text("Same people, same question: the gap between the parties shrank from 79 points to 29.", px=30, color=theme.ink2)
    a.source("Fidelity test: 14 questions from the 2024 Cooperative Election Study, Sep 2026.")

    b = new().headline("Strong views came out softer. Votes held up.", px=80)
    charts.legend_dots(b, [("Real survey answers", theme.data, False), ("GLM’s personas", theme.ai, True)])
    b.y += 10
    t = theme
    ax = b.chart(110 * len(rows), left=28, right=40)
    ax.set_xlim(0, 100)
    ax.set_ylim(len(rows) - 0.4, -0.75)
    ax.set_yticks([])
    ax.set_xticks([0, 25, 50, 75, 100], [typeset(f"{x}%") for x in (0, 25, 50, 75, 100)])
    for lab in ax.get_xticklabels():
        lab.set_fontproperties(b.font("sans", 400, 28))
    for x in (25, 50, 75):
        ax.axvline(x, color=t.hairline, lw=pt(1), zorder=0)
    for i, (name, real, model) in enumerate(rows):
        ax.text(0, i - 0.26, typeset(name), va="bottom", ha="left", color=t.ink, fontproperties=b.font("sans", 600, 30))
        ax.plot([real, model], [i, i], color=t.data, lw=pt(3), zorder=2, solid_capstyle="round")
        ax.scatter([real], [i], s=pt(26) ** 2, facecolor=t.paper, edgecolor=t.data, linewidth=pt(3), zorder=3)
        ax.scatter([model], [i], s=pt(26) ** 2, facecolor=t.ai, edgecolor=t.paper, linewidth=pt(3), zorder=4)
    b.y += 70
    b.source("Share answering yes in each party, 2024 Cooperative Election Study; GLM asked both ways and averaged.")

    c = new().headline("So each group’s views come from real survey answers.", px=80)
    c.text("A general model gets the direction of a vote right, but it smooths out how strongly groups feel. Our own "
           "model, trained on real survey answers, sets where each group starts.", px=40, color=theme.ink2, after=1.2)
    c.note("We never take a group’s opinions from a general model.", width=700)
    c.source("Forecasts go public on Monday 12 October.")

    return Post(day, "Lab notes 05: the model made partisans lukewarm", [
        (a, "Ask a model how Democrats rate Biden, and they come out lukewarm: 83% of Democrats approved of him in "
            "real 2024 survey answers, 44% among GLM's voter personas. Same people, same question."),
        (b, "Strong views came out softer, votes held up. Dot chart, real survey answers versus GLM's personas: "
            "Democrats approving of Biden 83% vs 44%; Democrats saying the economy got better 53% vs 18%; "
            "Republicans approving of Biden 4% vs 15%; Democrats who voted Harris 96% vs 93%."),
        (c, "So each group's views come from real survey answers: our own model, trained on them, sets where each "
            "group starts. We never take a group's opinions from a general model."),
    ], f"""Ask a general AI model to answer as a Democrat, and it gets the vote right but the feeling wrong. That's what we found when we gave GLM the same 14 questions real people answered in the 2024 Cooperative Election Study.

In the real answers, 83% of Democrats approved of President Biden. GLM's voter personas, built from the same people's survey answers, came out at 44%. Republicans went the other way: 4% approval in real life, 15% from the model. Democrats saying the economy had got better: 53% real, 18% from the model.

Votes held up much better. 96% of Democrats in the survey voted for Harris, and the model said 93%. So the model knows which side people are on, but it smooths out how strongly they feel, and in a forecast that's exactly the part that matters: how firmly each group holds its views decides how much the news can move it.

That's why we never take a group's opinions from a general model. Our own model, trained on real survey answers, sets where each group starts, and the general models only tell us which way groups react to the day's news.

All our Lab notes: notapoll.org/lab-notes

#midterms2026 #elections

{DISCLAIMER}""", [
        f"Ask a model how Democrats rate Biden: 83% approved in real 2024 survey answers, 44% among its voter "
        f"personas. {LABEL}.",
        "Votes held up (96% of Democrats voted Harris, the model said 93%), but strong views came out softer.",
        "So each group's views come from real survey answers, and general models only give the direction of a "
        "reaction.",
    ], allow=("survey",), short=("Ask a model how Democrats rate Biden: 83% approved in real 2024 survey answers, "
                                 "44% among its voter personas. Votes held up (96% vs 93%), strong views came out "
                                 "softer. So each group's views come from real survey answers."),
        more=" More in our Lab notes: notapoll.org/lab-notes.")


def ep06(theme: Theme = LAB) -> Post:
    """Plain statistics beat every model (content-plan §3, no. 6). docs/fidelity2.md: average TVD over 14 CES 2024
    items and 132 demographic cells; for yes/no items TVD is the gap in the headline share, so it reads as points."""
    day, k = date(2026, 10, 8), "Lab notes 06"
    bars = [("Statistics", 7), ("GLM", 14), ("Jev", 36)]
    new = lambda: Slide(day, "", theme, series=k)

    a = new().headline("Plain statistics beat every model.", px=92)
    a.dek("We asked each one to match how groups of Americans voted and what they thought in 2024.", px=40)
    a.at_bottom(charts.stats_height(150, rule=True) + 40 + 80)
    charts.stats(a, [("7", "points off: statistics"), ("14", "points off: best model")], px=150, rule=True)
    a.text("Average gap between predicted and real answers, 14 questions, 132 voter groups.", px=30,
           color=theme.ink2)
    a.source("Fidelity test against the 2024 Cooperative Election Study, Sep 2026.")

    b = new().headline("The models missed by two to five times as much.", px=80)
    charts.hbars(b, [(n, v, theme.data if n == "Statistics" else theme.ai) for n, v in bars], 40,
                 lambda v: f"{v:.0f} pts", label_w=260)
    b.text("One exception: GLM matched the 2024 Texas vote a little better (12 points off against 14).", px=34,
           color=theme.ink2)
    b.source("Average gap between predicted and real answer shares, per voter group and question.")

    c = new().headline("So statistics set where every race starts.", px=84)
    c.text("Past results, the poll average and each candidate's record set the starting point. The simulation only "
           "models how it changes as the news comes in.", px=40, color=theme.ink2, after=1.2)
    c.note("Starting point: statistics. What changes it: social simulation.", width=760)
    c.source("Forecasts go public on Monday 12 October.")

    return Post(day, "Lab notes 06: plain statistics beat every model", [
        (a, "Plain statistics beat every model: matching how groups of Americans voted and what they thought in 2024, "
            "statistics missed by 7 points on average, the best model, GLM, by 14."),
        (b, "Bar chart of the average miss: statistics 7 points, GLM 14, Jev 36. One exception: GLM matched the 2024 "
            "Texas vote a little better, 12 points off against 14."),
        (c, "So statistics set where every race starts, and the simulation only models how it changes as the news "
            "comes in."),
    ], f"""How well can a model answer like American voters? We asked two models to answer 14 real survey questions the way different groups of Americans did in 2024, from how they voted to what they thought of the economy, and compared them with plain statistics fitted on the same data.

Statistics won, and not narrowly. Its answers were about 7 points off the real ones on average. The best model, GLM, was 14 points off, and Jev 36. Across 132 voter groups and 14 questions, the models only beat statistics in a few places, like the 2024 vote in Texas.

That settled how our forecast is built. Where each race starts comes from statistics: past results, the poll average and each candidate's record. The simulation does the part statistics can't, modelling how different groups react as the news comes in.

All our Lab notes: notapoll.org/lab-notes

#midterms2026 #elections #datascience

{DISCLAIMER}""", [
        f"Plain statistics beat every model we tested: 7 points off real 2024 answers on average, against 14 for the "
        f"best model. {LABEL}.",
        "So statistics set where every race starts, and the simulation models how it changes with the news.",
    ], allow=("survey", "poll"), short=("Plain statistics beat every model we tested: about 7 points off real 2024 "
                                        "answers on average, against 14 for the best model. So statistics set where "
                                        "every race starts, and the simulation models how it changes."),
        more=" More in our Lab notes: notapoll.org/lab-notes.",
        platform={
            "x": ("We asked models to answer like groups of 2024 voters. Plain statistics beat them all: 7 points off "
                  "on average, against 14 for the best model. So statistics set where every race starts."),
            "threads": ("We asked two models to answer 14 real survey questions the way groups of 2024 voters did. "
                        "Plain statistics beat them: about 7 points off on average, against 14 for the best model and "
                        "36 for the other. So statistics set where every race starts, and the simulation handles how "
                        "it changes. Where would you trust a model over plain numbers?"),
            "topic": "2026 Midterms",
            "first_comment": "Where would you trust a model over plain statistics, and where not? Tell us below.",
        })


def ep07(theme: Theme = LAB) -> Post:
    """Turnout asked on its own (content-plan §3, no. 7). docs/model-recipes.md (+51 points when bundled) and
    docs/CHANGELOG.md (CES validated turnout tracks voter-file match rates, correlation 0.99 across cells)."""
    day, k = date(2026, 10, 9), "Lab notes 07"
    new = lambda: Slide(day, "", theme, series=k)

    a = new().headline("Ask a model how someone voted, and it assumes they voted.", px=80)
    a.dek("Asking about the vote and about turnout in the same question changed the turnout answers.", px=40)
    a.at_bottom(charts.stats_height(160, rule=True) + 40 + 80)
    charts.stats(a, [("+51", "points of turnout, in one test")], px=160, rule=True)
    a.text("Same voter personas, same model: only the questions were bundled.", px=30, color=theme.ink2)
    a.source("Turnout check, test bench, Sep 2026.")

    b = new().headline("The survey’s turnout data had a catch too.", px=84)
    b.text("Its turnout records followed how well each group could be matched to the voter rolls, not whether they "
           "voted.", px=40, color=theme.ink2, after=1.0)
    b.at_bottom(charts.stats_height(160, rule=True) + 40)
    charts.stats(b, [("0.99", "correlation with match rates")], px=160, rule=True)
    b.source("Across voter groups, 2024 Cooperative Election Study.")

    c = new().headline("So turnout is asked on its own and checked against the Census.", px=80)
    c.text("Turnout targets come from the Census Bureau’s survey of who voted in 2024, adjusted to each state’s "
           "official turnout.", px=40, color=theme.ink2, after=1.2)
    c.note("In a midterm, who shows up decides as much as who people prefer.", width=760)
    c.source("Forecasts go public on Monday 12 October.")

    return Post(day, "Lab notes 07: the model assumed everyone voted", [
        (a, "Ask a model how someone voted and it assumes they voted: bundling the vote question with the turnout "
            "question pushed turnout answers up 51 points in one test."),
        (b, "The survey's turnout data had a catch too: its records followed how well each group could be matched to "
            "the voter rolls (correlation 0.99), not whether they voted."),
        (c, "So turnout is asked on its own and checked against the Census Bureau's survey of who voted in 2024, "
            "adjusted to each state's official turnout."),
    ], f"""Who turns out decides a midterm as much as who people prefer, so we tested turnout twice as hard, and found two traps.

The first was in how we asked. When the question about someone's vote sat next to the question about whether they voted, the model read "how did this person vote" as proof that they voted. In one test that pushed turnout answers up by 51 points.

The second was in the data. The survey we use for opinions also records turnout, but those records followed how well each group could be matched to the voter rolls, almost perfectly (a correlation of 0.99), rather than whether people actually voted.

So turnout is now asked on its own, and our turnout targets come from the Census Bureau's survey of who voted in 2024, adjusted to each state's official turnout.

All our Lab notes: notapoll.org/lab-notes

#midterms2026 #elections #turnout

{DISCLAIMER}""", [
        f"Ask a model how someone voted and it assumes they voted: bundling the two questions pushed turnout answers "
        f"up 51 points. {LABEL}.",
        "So turnout is asked on its own, and checked against the Census Bureau's survey of who voted in 2024.",
    ], allow=("survey",), short=("Ask a model how someone voted and it assumes they voted: bundling the two questions "
                                 "pushed turnout answers up 51 points in one test. So turnout is asked on its own and "
                                 "checked against the Census."),
        more=" More in our Lab notes: notapoll.org/lab-notes.",
        platform={
            "x": ("Ask a model how someone voted, and it assumes they voted. In one test, that pushed turnout answers "
                  "up 51 points. So turnout is asked on its own and checked against the Census."),
            "threads": ("Small wording, big effect: when we asked a model how someone voted and whether they voted in "
                        "the same question, it assumed everyone voted. Turnout answers jumped 51 points in one test. "
                        "Now turnout is asked on its own and checked against the Census. In a midterm, what do you "
                        "think decides who shows up?"),
            "topic": "2026 Midterms",
            "first_comment": "In a midterm, what do you think decides who actually shows up to vote?",
        })


def ep08(theme: Theme = LAB) -> Post:
    """We trained our own model (content-plan §3, no. 8), kept positive and factual (Matteo, 4 Oct). docs/CHANGELOG.md:
    Kev ces-v3b answers the 28 voter groups in all 51 states (1,428 group starting points); the reaction version's
    null and party-swap checks (no change 0.955/0.965, every sign flips); shadow mode, scored weekly."""
    day, k = date(2026, 10, 10), "Lab notes 08"
    new = lambda: Slide(day, "", theme, series=k)

    a = new().headline("We trained our own model on real survey answers.", px=84)
    a.dek("An open model, fine-tuned on how real Americans answered in 2024.", px=40)
    a.at_bottom(charts.stats_height(150, rule=True) + 40 + 80)
    charts.stats(a, [("28", "voter groups"), ("51", "states and DC")], px=150, rule=True)
    a.text("It sets where each group starts: 1,428 starting points in all.", px=30, color=theme.ink2)
    a.source("Fine-tuned on the 2024 Cooperative Election Study, Sep 2026.")

    b = new().headline("It passes both fairness checks.", px=88)
    b.at_bottom(charts.stats_height(150, rule=True) + 40 + 80)
    charts.stats(b, [("96%", "ignored irrelevant news"), ("16", "of 16 flipped, parties swapped")], px=150,
                 rule=True)
    b.text("The two fairness checks every model has to pass before it touches a forecast.", px=30, color=theme.ink2)
    b.source("Null test: 20 irrelevant stories. Mirror test: 16 stories told twice, parties swapped. Sep 2026.")

    c = new().headline("Next, it has to earn the reaction job.", px=84)
    c.text("For now a hosted model gives the reactions to the news. Ours answers alongside it every day and is scored "
           "each week against what really happened.", px=40, color=theme.ink2, after=1.2)
    c.note("A model only takes over a job when it does it better.", width=700)
    c.source("Forecasts go public on Monday 12 October.")

    return Post(day, "Lab notes 08: we trained our own model", [
        (a, "We trained our own model on real survey answers from 2024. It sets 1,428 starting points: 28 voter groups "
            "in every state and DC."),
        (b, "It passes both fairness checks: no reaction to irrelevant news 96% of the time, and its reaction flipped "
            "on all 16 stories when we swapped the parties."),
        (c, "Next, it has to earn the reaction job: it answers alongside the hosted model every day and is scored "
            "each week against what really happened."),
    ], f"""This is the part of NotAPoll we built ourselves: our own model, trained on how real Americans answered a 2024 election survey.

We took an open model and fine-tuned it on how real Americans answered the 2024 Cooperative Election Study. It now sets where each of 28 voter groups starts in every state and DC, 1,428 starting points in all.

It also passes both of our fairness checks. Shown 20 news stories that shouldn't matter to anyone, it reacted to almost none of them. Shown 16 stories twice, once as written and once with the parties swapped, its reaction flipped every single time, exactly what a model with no built-in lean should do.

Reactions to the daily news are the next job. For now a hosted model gives them, and ours answers alongside it every day, scored each week against what really happened. A model only takes over a job when it does it better.

All our Lab notes: notapoll.org/lab-notes

#midterms2026 #opensource #elections

{DISCLAIMER}""", [
        f"We trained our own model on real 2024 survey answers. It sets 1,428 starting points: 28 voter groups in "
        f"every state and DC. {LABEL}.",
        "It passes both fairness checks: its reaction flipped on all 16 stories when we swapped the parties.",
        "Next it has to earn the reaction job, scored every week against what really happened.",
    ], allow=("survey",), short=("We trained our own model on real 2024 survey answers. It sets 1,428 starting "
                                 "points, and it passes both fairness checks: its reaction flipped on all 16 stories "
                                 "when we swapped the parties."),
        more=" More in our Lab notes: notapoll.org/lab-notes.",
        platform={
            "x": ("We trained our own model on real 2024 survey answers. Swap the parties in a story and its reaction "
                  "flips: 16 times out of 16. Now it sets 1,428 starting points across every state."),
            "threads": ("We trained our own model on how real Americans answered a big 2024 election survey. It now "
                        "sets where 28 voter groups start in every state and DC. And it passes our fairness checks: "
                        "tell it a story twice with the parties swapped, and its reaction flips every time. "
                        "What check would you want a model to pass before you trusted it?"),
            "topic": "2026 Midterms",
            "first_comment": "What test would you want a model to pass before you trusted it with a forecast?",
        })


def ep09(theme: Theme = LAB) -> Post:
    """How to read our forecast (content-plan §3, no. 9): an example card, stamped EXAMPLE, with invented numbers."""
    from . import racecards as rc
    day, k = date(2026, 10, 11), "Lab notes 09"
    new = lambda: Slide(day, "", theme, series=k)
    r = rc.RACE | {"today": 0.61, "kicker": "EXAMPLE · INVENTED NUMBERS",
                   "source": "EXAMPLE: invented numbers, not a forecast. Real cards from Monday 12 October."}
    card_path = KITS.parent / "daily" / "11-lab-notes-09" / "example-card.png"
    card_path.parent.mkdir(parents=True, exist_ok=True)
    rc.stamped(theme, r).save(card_path)

    a = new().headline("From tomorrow, every Senate race gets a card like this.", px=68)
    img = Image.open(card_path)
    cw = 600
    ch = cw * img.height / img.width
    x0, y0 = MARGIN, a.y + 6
    a.ax.imshow(img, extent=(x0, x0 + cw, y0 + ch, y0), zorder=2)
    a.ax.add_patch(plt.Rectangle((x0, y0), cw, ch, fill=False, ec=theme.hairline, lw=pt(2), zorder=3))
    rc.stamp(a, x0 + cw + 150, y0 + 170, "Example", px=52, rot=-8, color=theme.rep)
    tx = x0 + cw + 40
    a.y = y0 + 320
    a.text("Invented numbers. Real forecasts start Monday 12 October.", "sans", 600, 32, theme.ink2,
           x=tx, width=a.w - MARGIN - tx)
    a.y = y0 + ch + 20
    a.source("Our daily race card, with invented numbers.")

    b = new().headline("How to read it.", px=96)
    points = ["58 | 42: the Democrat wins 58 of every 100 simulated elections, the Republican 42. A chance of "
              "winning, not a vote share.",
              "Anywhere from 35 to 65 in 100, we call the race a toss-up.",
              "Beside our number: the poll average, the prediction markets and Cook.",
              "Today and 3 November can differ: most news fades before election day."]
    for n, line in enumerate(points, 1):
        top = b.y
        b._put(MARGIN, top - 6, str(n), "hero", theme.hero_weight, 64, theme.ai, va="top")
        b.text(line, "serif", 600, 38, x=MARGIN + 76, width=b.width - 76, after=0.7)
    b.source("Each card: 40,000 simulated elections per race, run every morning.")

    c = new().headline("Every forecast is timestamped. Every miss is published.", px=80)
    c.text("Each card carries its run code and date. From 19 October, every Monday, we score our calls against the "
           "poll average, the markets and Cook, misses first.", px=40, color=theme.ink2, after=1.2)
    c.note("First forecasts: tomorrow, Monday 12 October.", width=700)
    c.source("notapoll.org")

    return Post(day, "Lab notes 09: how to read our forecast", [
        (a, "From tomorrow, every Senate race gets a card like this. An example race card for Ohio with invented numbers, "
            "stamped EXAMPLE: 58 in 100 simulated elections won by the Democrat, a toss-up, with the poll average, "
            "the market and Cook beside it. Real forecasts start Monday 12 October."),
        (b, "How to read it: 58 in 100 means the Democrat wins 58 of every 100 simulated elections, about 6 in 10, not a "
            "vote share. From 35 to 65 in 100 we call it a toss-up. Beside our number: the poll average, the "
            "prediction markets and Cook. Today and 3 November can differ, because most news fades before election "
            "day."),
        (c, "Every forecast is timestamped and every miss is published: each card carries its run code and date, and "
            "from 19 October we score our calls every Monday against the poll average, the markets and Cook, misses "
            "first. First forecasts: Monday 12 October."),
    ], f"""How to read the 2026 midterm forecast we start publishing tomorrow, Monday 12 October. Here's a race card with invented numbers, so you know what you're looking at when the real ones arrive.

The big number is how many of our simulated elections a candidate wins. "58 in 100" means the Democrat won 58 of every 100 times we played the race out, about 6 in 10. It's a chance of winning, not a share of the vote. Anything from 35 to 65 in 100 we call a toss-up.

Our number never stands alone. Each card shows the poll average, the prediction markets and the Cook Political Report beside it, so you can see where we agree and where we don't.

There are two numbers in time: if the election were today, and on 3 November. They can differ, because most news fades before election day.

And every forecast is timestamped. From 19 October, every Monday, we'll score our calls against the polls, the markets and Cook, misses first.

All our Lab notes: notapoll.org/lab-notes

#midterms2026 #elections #forecast

{DISCLAIMER}""", [
        f"From tomorrow, every Senate race gets a card like this one (invented numbers). {LABEL}.",
        "58 in 100 means the Democrat wins 58 of every 100 simulated elections: about 6 in 10, not a vote share. 35 to "
        "65 is a toss-up.",
        "Beside our number: the poll average, the markets and Cook. Every Monday from 19 October, we score our calls, "
        "misses first.",
    ], allow=("poll", "polls"), short=("From tomorrow, every Senate race gets a card like this. 58 in 100 means the "
                                       "Democrat wins 58 of every 100 simulated elections, not 58% of the vote. Beside "
                                       "it: the poll average, the markets and Cook. Example, invented numbers."),
        more=" First forecasts: Monday 12 October. More: notapoll.org/lab-notes.",
        platform={
            "x": ("From tomorrow, every Senate race gets a card like this (invented numbers here). 58 in 100 = wins "
                  "58 of every 100 simulated elections, not 58% of the vote. And it always sits beside the polls, the "
                  "markets and Cook."),
            "threads": ("Tomorrow we start publishing our 2026 midterm forecast. Here's how to read a race card, with "
                        "invented numbers: 58 in 100 means a candidate wins 58 of every 100 simulated elections, not 58% "
                        "of the vote, and 35 to 65 is a toss-up. Our number always sits beside the poll average, the "
                        "markets and Cook. Which race do you most want to see first?"),
            "topic": "2026 Midterms",
            "first_comment": "Which Senate race do you most want to see first tomorrow?",
        })


EPISODES = {1: ep01, 2: ep02, 3: ep03, 4: ep04, 5: ep05, 6: ep06, 7: ep07, 8: ep08, 9: ep09}


def daily(n: int, folder: str, theme: Theme = LAB) -> tuple[Path, list[str]]:
    """A Lab note as a Buffer-ready kits/daily/<folder> (slides, caption.txt, alt-text.txt, single-post.md,
    checks.txt), the same layout as the launch posts and Reading the polls."""
    from .launch import LIMIT, X_LINK
    from .pollread import end
    post = EPISODES[n](theme)
    out = KITS.parent / "daily" / folder
    out.mkdir(parents=True, exist_ok=True)
    probs = []
    for i, (sl, _) in enumerate(post.slides, 1):
        probs += [f"slide {i}: {x}" for x in sl.layout_problems() + sl.missing_glyphs()
                  + text.slide_problems(sl, post.allow)]
        sl.save(out / f"slide-{i}.jpg")
    (out / "caption.txt").write_text(post.instagram, encoding="utf-8")
    (out / "alt-text.txt").write_text("".join(f"slide-{i}.jpg: {a}\n" for i, (_, a) in enumerate(post.slides, 1)),
                                      encoding="utf-8")
    pf = post.platform or {}
    posts = {"x": f'{pf.get("x", post.short)} {LABEL}.',  # no link on X: it cuts reach
             "bluesky": end(post.short, LIMIT["bluesky"]),
             "threads": end(pf.get("threads", post.short + post.more), LIMIT["threads"])}
    meta = {k2: pf[k1] for k1, k2 in (("topic", "threads_topic"), ("first_comment", "instagram_first_comment"))
            if pf.get(k1)}
    (out / "meta.json").write_text(json.dumps(meta, indent=1, ensure_ascii=False), encoding="utf-8")
    lines = ["# Single posts (X and Threads through Buffer; Bluesky by hand)", ""]
    for k in ("x", "threads", "bluesky"):
        t = posts[k]
        size = len(t) + (t.count("notapoll.org") * (X_LINK - len("notapoll.org")) if k == "x" else 0)
        lines += [f"## {'X' if k == 'x' else k.capitalize()} ({size} of {LIMIT[k]} characters; attach slide-1 to "
                  f"slide-{len(post.slides)})", "", t, ""]
        probs += [f"{k}: {size} characters" for _ in [0] if size > LIMIT[k]]
    (out / "single-post.md").write_text("\n".join(lines), encoding="utf-8")
    for name, t in [("caption", post.instagram), *posts.items()]:
        probs += [f"{name}: {x}" for x in text.check(t, caption=True, allow=post.allow)]
    (out / "checks.txt").write_text("\n".join(probs) or "all rules pass", encoding="utf-8")
    return out, probs


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
