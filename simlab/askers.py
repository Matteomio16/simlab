"""One interface over decision models and text LLMs: ask(state, question) -> {option: prob}.

The question is always in System One shape ({type, instructions, criteria}) so the exact
same test items go to Jev, Kev (hosted or our fine-tune) and GLM / MiMo / DeepSeek / Luna.
Score questions return probabilities keyed by level index ("0".."4").
"""
from __future__ import annotations

import os
import random
from concurrent.futures import ThreadPoolExecutor

from .core import Chat, Decisions, HOSTS, LLMS, JEV, KEV, REASONING

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


def order_avg(ask1, question: dict, n_orders: int, seed: int = 0) -> dict:
    """Average one question over option orders so position bias cancels out.
    choice: as given + (n_orders - 1) shuffles. score: as given + reversed (reversed level j is level n-1-j)."""
    t = question["type"]
    if n_orders <= 1 or t == "noul":
        return ask1(question)
    if t == "score":
        n = len(question["criteria"])
        fwd = ask1(question)
        rev = ask1(dict(question, criteria=question["criteria"][::-1]))
        rev = {(str(n - 1 - int(k)) if k.isdigit() else k): v for k, v in rev.items()}
        return {k: (fwd.get(k, 0) + rev.get(k, 0)) / 2 for k in fwd.keys() | rev.keys()}
    opts = list(question["criteria"].items())
    rng = random.Random(seed)
    orders = [opts] + [rng.sample(opts, len(opts)) for _ in range(n_orders - 1)]
    acc: dict = {}
    for o in orders:
        for k, v in ask1(dict(question, criteria=dict(o))).items():
            acc[k] = acc.get(k, 0) + v / len(orders)
    return acc


class DecisionAsker:
    def __init__(self, model: str = JEV, endpoint: str | None = None, api_key: str | None = None,
                 n_orders: int = 3, name: str | None = None):
        self.d = Decisions(model, endpoint, api_key)
        self.n_orders = n_orders
        self.name = name or model.split("/")[-1]

    def ask(self, state: str, question: dict, tag: str = "") -> dict:
        return order_avg(lambda q: self.d.probs(self.d.ask(state, {"q": q}, tag), "q"), question, self.n_orders)


class LLMAsker:
    def __init__(self, key: str, provider_order: list[str] | None = None, n_orders: int = 3, name: str | None = None):
        self.chat = Chat(LLMS[key], provider_order or [HOSTS[key]], reasoning=REASONING.get(key))
        self.n_orders = n_orders
        self.name = name or key

    def ask(self, state: str, question: dict, tag: str = "") -> dict:
        return order_avg(lambda q: self._ask1(state, q, tag), question, self.n_orders)

    def _ask1(self, state: str, question: dict, tag: str) -> dict:
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
    """'jev', 'kev', 'kev@<url>' (our Modal deployment), or an LLM key: glm, mimo, deepseek, luna.
    A trailing '1' (jev1, glm1, ...) asks in one option order only, to measure what averaging buys;
    its calls are a subset of the averaged run's, so they come from the cache."""
    base, n = (name[:-1], 1) if name[:-1] in ("jev", "kev", *LLMS) and name.endswith("1") else (name, 3)
    if base == "jev":
        return DecisionAsker(JEV, n_orders=n, name=name)
    if base == "kev":
        return DecisionAsker(KEV, n_orders=n, name=name)
    if base.startswith("kev@"):
        return DecisionAsker("kev-latest", endpoint=base[4:].rstrip("/") + "/v1/systemone",
                             api_key=os.environ.get("KEV_API_KEY"), name="kev-ft")
    return LLMAsker(base, n_orders=n, name=name)


def batch(asker, items: list[tuple[str, dict]], tag: str = "", workers: int = 8) -> list[dict]:
    """items = [(state, question), ...] -> list of prob dicts (order preserved)."""
    with ThreadPoolExecutor(workers) as ex:
        return list(ex.map(lambda it: asker.ask(it[0], it[1], tag), items))


def expected(probs: dict, values=(-2, -1, 0, 1, 2)) -> float:
    return sum(probs.get(str(i), 0.0) * v for i, v in enumerate(values))
