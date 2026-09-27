"""Question sets and hand-written probe news for the reaction tests.

The same question wording is used for Jev, Kev and the text LLMs so results compare.
"""
from __future__ import annotations

# 5-point scales, low -> high. Values used to compute an expected shift.
SUPPORT_LEVELS = [
    "Moves strongly toward the Republican candidate",
    "Moves slightly toward the Republican candidate",
    "No change",
    "Moves slightly toward the Democratic candidate",
    "Moves strongly toward the Democratic candidate",
]
TURNOUT_LEVELS = [
    "Much less likely to vote",
    "Somewhat less likely to vote",
    "No change",
    "Somewhat more likely to vote",
    "Much more likely to vote",
]
LEVEL_VALUES = [-2, -1, 0, 1, 2]

REACTION_QUESTIONS = {
    "support": {
        "type": "score",
        "instructions": "After this news, how does this person's preference in their state's Senate race change, if at all?",
        "criteria": SUPPORT_LEVELS,
    },
    "turnout": {
        "type": "score",
        "instructions": "After this news, how does this person's likelihood of voting in November change, if at all?",
        "criteria": TURNOUT_LEVELS,
    },
}


def reaction_state(persona: str, news: str) -> str:
    return f"VOTER PROFILE\n{persona}\n\nNEWS THIS PERSON SAW TODAY\n{news}"


# ------------------------------------------------ null probes: politically irrelevant news
NULL_NEWS = [
    "The Cincinnati Bengals beat the Pittsburgh Steelers 27-20 on Sunday after a late interception.",
    "Forecasters expect a sunny, mild weekend across the region with highs in the low 70s.",
    "A new study finds that octopuses may dream, based on changes in their skin patterns during sleep.",
    "A popular bakery chain is adding a pumpkin spice croissant to its fall menu starting Monday.",
    "The city's main bridge will close one lane overnight next week for routine resurfacing work.",
    "A pop star announced a 30-city world tour beginning next spring, with tickets on sale Friday.",
    "Astronomers spotted a comet that will be visible to the naked eye in the northern sky next month.",
    "A local high school's marching band won first place at a regional competition on Saturday.",
    "A zoo welcomed twin red panda cubs, the first born there in over a decade.",
    "A smartphone maker released a software update that fixes a battery-drain bug.",
    "The national spelling bee champion correctly spelled 'ecchymosis' to win the title.",
    "A marathon drew 18,000 runners downtown on Sunday; the winner finished in 2 hours 9 minutes.",
    "Scientists sequenced the genome of a rare deep-sea fish found off the coast of Japan.",
    "A streaming service announced a new season of its most-watched cooking competition show.",
    "Apple orchards report a strong harvest this year thanks to a wet spring.",
    "A chess grandmaster set a record by playing 100 simultaneous games blindfolded.",
    "The state fair reported record attendance of 950,000 visitors over twelve days.",
    "A museum unveiled a restored 17th-century Dutch painting after a two-year conservation project.",
    "A cruise line added a new route to Alaska for next summer.",
    "Researchers found that houseplants may slightly improve indoor humidity in winter.",
]

# ------------------------------------------------ mirror probes: identical events, party swapped
# {P} = party of the actor, {C} = the actor's role. Each is asked once with P=Democratic, once with P=Republican.
MIRROR_TEMPLATES = [
    "The {P} Senate candidate was indicted today on federal bribery charges related to a construction contract.",
    "A video surfaced showing the {P} Senate candidate mocking disabled veterans at a private fundraiser.",
    "The {P} Senate candidate won the endorsement of the state's largest police union and firefighters' union.",
    "The {P} Senate candidate unveiled a plan to cut grocery and gas prices that independent economists called credible.",
    "Reports revealed the {P} Senate candidate failed to pay property taxes on a vacation home for six years.",
    "The {P} Senate candidate delivered a widely praised debate performance, with snap polls calling it a clear win.",
    "The {P} Senate candidate's campaign manager resigned after admitting to misusing campaign funds.",
    "A popular former governor from the {P} Party held a rally with the {P} Senate candidate, drawing 20,000 people.",
    "The {P} Senate candidate said in an interview that Social Security should be gradually privatized.",
    "The {P} Senate candidate was endorsed by the state's largest newspaper for the first time in 30 years.",
    "Leaked emails show the {P} Senate candidate lobbied for a company that later shut down a local factory.",
    "The {P} Senate candidate refused to commit to accepting the election result if they lose.",
    "The {P} Senate candidate announced a bipartisan bill with a member of the other party to lower insulin prices.",
    "The {P} Senate candidate called voters in rural counties 'backward' in a recording released today.",
    "The {P} Senate candidate raised a record $40 million last quarter, mostly from small donors in the state.",
    "The {P} Senate candidate skipped the only scheduled debate, citing a scheduling conflict.",
]


def mirror_pair(i: int) -> tuple[str, str]:
    t = MIRROR_TEMPLATES[i]
    return t.format(P="Democratic"), t.format(P="Republican")


# ------------------------------------------------ fidelity questions (CES targets)
def vote_question(options: dict) -> dict:
    return {"type": "choice",
            "instructions": "How did this person vote in the 2024 presidential election?",
            "criteria": options}


TURNOUT_Q = {"type": "noul", "instructions": "Did this person actually vote in the November 2024 general election?"}

# ------------------------------------------------ news classification
EVENT_TYPES = {
    "scandal": "Allegations, investigations, indictments or embarrassing revelations about a candidate",
    "policy": "A candidate's or party's policy proposal, vote or position",
    "economy": "Economic news: prices, jobs, gas, markets, layoffs",
    "endorsement": "Endorsements, rallies with surrogates, union or newspaper backing",
    "debate": "Debates, forums, interviews and their reception",
    "poll": "News about polls or forecasts",
    "fundraising_ads": "Fundraising totals or advertising campaigns",
    "national": "National events (president, Congress, war, disasters) not specific to the race",
    "other": "Anything else",
}
NEWS_QUESTIONS = {
    "type": {"type": "choice", "instructions": "What kind of election news is this?", "criteria": EVENT_TYPES},
    "helps": {"type": "choice", "instructions": "Which side does this news most likely help in this Senate race?",
              "criteria": {"democrat": None, "republican": None, "neither": "Neutral or no clear effect",
                           "unclear": "Could cut either way"}},
    "salience": {"type": "score", "instructions": "How much attention will ordinary voters in the state pay to this?",
                 "criteria": ["None", "Very little", "Some", "A lot", "Dominates the news"]},
    "relevant": {"type": "noul", "instructions": "Is this news relevant to how people might vote in this Senate race?"},
}
