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
from .frame import DISCLAIMER, LABEL, SITE, Slide, Theme, pt, typeset
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


EPISODES = {1: ep01, 2: ep02, 3: ep03, 4: ep04, 5: ep05}


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
    posts = {"x": end(post.short, LIMIT["x"], X_LINK), "bluesky": end(post.short, LIMIT["bluesky"]),
             "threads": end(post.short + post.more, LIMIT["threads"])}
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
