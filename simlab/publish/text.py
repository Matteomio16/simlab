"""Post text rules (Field Guide, publishing): the label in every caption, and never "poll", "survey", "voters say" or
"% of voters" for what the model produces. check() returns the problems for the kit note; an empty list passes.

`allow` names words a post may use because it refers to a real survey or poll (e.g. the CES), stated in the note.
"""
from __future__ import annotations

import re

from .frame import LABEL

ALLOWED = ("not a poll", "poll average", "polling average", "polls close", "polls closed", "polls open")
BANNED = {"poll": r"\bpoll(s|ed|ing|ster|sters)?\b", "survey": r"\bsurvey(s|ed)?\b", "voters say": r"\bvoters say\b",
          "% of voters": r"%\s+of\s+voters"}
# Never, whatever the context (Matteo, 30 Sep): the markets are "prediction markets" or "markets", never betting.
NEVER = {"betting": r"\bbet(s|ting|tor|tors)?\b|\bgambl\w*|\bwager\w*|\bbookmakers?\b|\bpunters?\b|\bbookies?\b"}


STYLE = {"AI": r"\bAIs?\b|artificial intelligence", "bot": r"\bbots?\b", "LLM": r"\bLLMs?\b",
         "respondents": r"\brespondents?\b"}


def style(s: str) -> list[str]:
    """Voice notes, not rule failures (Matteo, 28 Sep): say social simulation, synthetic or simulated voters; keep
    "AI" for the methods page; "respondents" implies real people."""
    return [f'style: "{w}" (prefer synthetic or simulated voters)' for w, pat in STYLE.items() if re.search(pat, s)]


def check(s: str, *, caption: bool = True, allow: tuple[str, ...] = ()) -> list[str]:
    out, low = [], s.lower()
    if caption and LABEL.lower() not in low:
        out.append(f'missing the label "{LABEL}"')
    scrubbed = low.replace(LABEL.lower(), " ")
    for phrase in ALLOWED:
        scrubbed = scrubbed.replace(phrase, " ")
    for word, pattern in BANNED.items():
        if word not in allow and re.search(pattern, scrubbed):
            out.append(f'uses "{word}" (never for model outputs)')
    for word, pattern in NEVER.items():
        if re.search(pattern, low):
            out.append(f'uses "{word}" (say "prediction markets" or "markets")')
    return out


def slide_problems(slide, allow: tuple[str, ...] = ()) -> list[str]:
    """The same rules for the words drawn on an image (the label strip is part of it, so no label check)."""
    from matplotlib.text import Text
    words = " ".join(t.get_text() for t in slide.fig.findobj(Text) if t.get_text().strip())
    return check(words, caption=False, allow=allow)
