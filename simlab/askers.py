"""One interface over decision models and text LLMs: ask(state, question) -> {option: prob}.

The question is always in System One shape ({type, instructions, criteria}) so the exact
same test items go to Jev, Kev (hosted or our fine-tune) and GLM / MiMo / DeepSeek / Luna.
Score questions return probabilities keyed by level index ("0".."4").
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

from .core import Chat, Decisions, LLMS, JEV, KEV

SYSTEM_PROMPT = (
    "You are a careful survey-research model. You are given a description of one person (and sometimes "
    "news they saw) and a question with a fixed set of answers. Estimate the probability of each answer for "
    "this person, as a calibrated forecaster would: most people's views are stable, and most news changes "
    "nothing. Reply with JSON only, mapping every answer label exactly as written to a probability, summing to 1."
)


def _labels(question: dict) -> list[str]:
    t = question["type"]
    if t == "noul":
        return ["true", "false"]
    if t == "choice":
        return list(question["criteria"].keys())
    return [str(i) for i in range(len(question["criteria"]))]


class DecisionAsker:
    def __init__(self, model: str = JEV, endpoint: str | None = None, api_key: str | None = None,
                 n_orders: int = 3, name: str | None = None):
        self.d = Decisions(model, endpoint, api_key)
        self.n_orders = n_orders
        self.name = name or model.split("/")[-1]

    def ask(self, state: str, question: dict, tag: str = "") -> dict:
        return self.d.choice_avg(state, "q", question, n_orders=self.n_orders, tag=tag)


class LLMAsker:
    def __init__(self, key: str, provider_order: list[str] | None = None):
        self.chat = Chat(LLMS[key], provider_order)
        self.name = key

    def ask(self, state: str, question: dict, tag: str = "") -> dict:
        labels = _labels(question)
        if question["type"] == "score":
            opts = "\n".join(f'"{i}": {lvl}' for i, lvl in enumerate(question["criteria"]))
        elif question["type"] == "choice":
            opts = "\n".join(f'"{k}": {v or k}' for k, v in question["criteria"].items())
        else:
            opts = '"true": yes\n"false": no'
        user = f"{state}\n\nQUESTION: {question['instructions']}\nANSWERS (label: meaning):\n{opts}\n\nReturn JSON {{label: probability}}."
        return self.chat.distribution(SYSTEM_PROMPT, user, labels, tag)


def make(name: str):
    """'jev', 'kev', 'kev@<url>' (our Modal deployment), or an LLM key: glm, mimo, deepseek, luna."""
    if name == "jev":
        return DecisionAsker(JEV, name="jev")
    if name == "jev1":  # single option order, to measure what averaging buys
        return DecisionAsker(JEV, n_orders=1, name="jev1")
    if name == "kev":
        return DecisionAsker(KEV, name="kev")
    if name.startswith("kev@"):
        import os
        return DecisionAsker("kev-latest", endpoint=name[4:].rstrip("/") + "/v1/systemone",
                             api_key=os.environ.get("KEV_API_KEY"), name="kev-ft")
    return LLMAsker(name)


def batch(asker, items: list[tuple[str, dict]], tag: str = "", workers: int = 8) -> list[dict]:
    """items = [(state, question), ...] -> list of prob dicts (order preserved)."""
    with ThreadPoolExecutor(workers) as ex:
        return list(ex.map(lambda it: asker.ask(it[0], it[1], tag), items))


def expected(probs: dict, values=(-2, -1, 0, 1, 2)) -> float:
    return sum(probs.get(str(i), 0.0) * v for i, v in enumerate(values))
