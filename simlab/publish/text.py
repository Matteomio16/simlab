"""Post text rules (Field Guide, publishing): the label in every caption, and never "poll", "survey", "voters say" or
"% of voters" for what the model produces. check() returns the problems for the kit note; an empty list passes.

`allow` names words a post may use because it refers to a real survey or poll (e.g. the CES), stated in the note.
"""
from __future__ import annotations

import re

from .frame import DISCLAIMER, LABEL

ALLOWED = ("not a poll", "poll average", "polling average", "polls close", "polls closed", "polls open",
           "built from real survey answers")  # the last: the personas' real source, in the fixed disclaimer
BANNED = {"poll": r"\bpoll(s|ed|ing|ster|sters)?\b", "survey": r"\bsurvey(s|ed)?\b", "voters say": r"\bvoters say\b",
          "% of voters": r"%\s+of\s+voters"}
# Never, whatever the context (Matteo, 30 Sep): the markets are "prediction markets" or "markets", never betting.
NEVER = {"synthetic": r"\bsynthetic\b",  # Matteo, 1 Oct: "voter personas" instead
         # communication.md (1 Oct): never in posts
         "bots": r"\bbots?\b", "agents": r"\bagents?\b", "AI-powered": r"\bai[- ]powered\b",
         "revolutionary": r"\brevolutionar", "game-changer": r"\bgame[- ]chang", "Matteo": r"\bmatteo\b",
         "Hungary": r"\bhungar",
         # Settled with Matteo, 1 Oct: never a political label; personas don't interact with each other yet
         "reactionary": r"\breactionar", "social interactions": r"\bsocial interactions?\b",
         "betting": r"\bbet(s|ting|tor|tors)?\b|\bgambl\w*|\bwager\w*|\bbookmakers?\b|\bpunters?\b|\bbookies?\b"}


STYLE = {"AI": r"\bAIs?\b|artificial intelligence", "LLM": r"\bLLMs?\b", "movement": r"\bmovement\b",
         "respondents": r"\brespondents?\b"}


def style(s: str) -> list[str]:
    """Voice notes, not rule failures (Matteo, 28 Sep; 1 Oct): say social simulation and voter personas; keep
    "AI" for the methods page; "respondents" implies real people."""
    return [f'style: "{w}" (prefer voter personas or social simulation)' for w, pat in STYLE.items() if re.search(pat, s)]


def check(s: str, *, caption: bool = True, allow: tuple[str, ...] = ()) -> list[str]:
    out, low = [], s.lower()
    if caption and LABEL.lower() not in low and DISCLAIMER.lower() not in low:
        out.append(f'missing the disclaimer "{DISCLAIMER}" (or the label "{LABEL}")')
    scrubbed = low.replace(LABEL.lower(), " ").replace(DISCLAIMER.lower(), " ")
    for phrase in ALLOWED:
        scrubbed = scrubbed.replace(phrase, " ")
    for word, pattern in BANNED.items():
        if word not in allow and re.search(pattern, scrubbed):
            out.append(f'uses "{word}" (never for model outputs)')
    for word, pattern in NEVER.items():
        if re.search(pattern, low):
            hint = {"synthetic": 'say "voter personas"', "betting": 'say "prediction markets" or "markets"'}
            out.append(f'uses "{word}" ({hint.get(word, "never on NotAPoll, communication.md")})')
    return out


def slide_problems(slide, allow: tuple[str, ...] = ()) -> list[str]:
    """The same rules for the words drawn on an image (the label strip is part of it, so no label check)."""
    from matplotlib.text import Text
    words = " ".join(t.get_text() for t in slide.fig.findobj(Text) if t.get_text().strip())
    return check(words, caption=False, allow=allow)
