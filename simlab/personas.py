"""Structured persona text. Survey fields only, no LLM-written backstory (those drift left)."""
from __future__ import annotations

FIELD_ORDER = ["state", "age", "gender", "race", "education", "income", "religion", "area",
               "party_id", "ideology", "vote_2020", "news_diet"]
LABELS = {"state": "State", "age": "Age", "gender": "Gender", "race": "Race/ethnicity",
          "education": "Education", "income": "Family income", "religion": "Religion", "area": "Lives in",
          "party_id": "Party identification", "ideology": "Ideology", "vote_2020": "2020 presidential vote",
          "news_diet": "Main news sources"}


def render(p: dict, drop: tuple = ()) -> str:
    lines = [f"{LABELS[k]}: {p[k]}" for k in FIELD_ORDER if k in p and p[k] not in (None, "") and k not in drop]
    return "\n".join(lines)


def swap_party(text: str) -> str:
    """Swap Democratic <-> Republican mentions (for mirror tests)."""
    tmp = text.replace("Democratic", "\x00D").replace("Democrat", "\x01D").replace("Republican", "Democratic")
    return tmp.replace("\x00D", "Republican").replace("\x01D", "Republican")
