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
    return out
