"""One interface over decision models and text LLMs: ask(state, question) -> {option: prob}.

The question is always in System One shape ({type, instructions, criteria}) so the exact
same test items go to Jev, Kev (hosted or our fine-tune) and GLM / MiMo / DeepSeek / Luna.
Score questions return probabilities keyed by level index ("0".."4").
"""
from __future__ import annotations

import json
import os
import random
from collections import defaultdict
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


def _same(p: dict) -> dict:
    return p


def order_variants(question: dict, n_orders: int, seed: int = 0) -> list[tuple[dict, callable]]:
    """The versions of a question to ask so position bias cancels, each with a function mapping its answer back to
    the original labels. score: as given + reversed (reversed level j is level n-1-j). choice: as given + reversed
    (n_orders=2) or + seeded shuffles (n_orders=3, the original scheme, so cached answers stay valid). noul: as given."""
    t = question["type"]
    if n_orders <= 1 or t == "noul":
        return [(question, _same)]
    if t == "score":
        n = len(question["criteria"])
        back = lambda p: {(str(n - 1 - int(k)) if k.isdigit() else k): v for k, v in p.items()}
        return [(question, _same), (dict(question, criteria=question["criteria"][::-1]), back)]
    opts = list(question["criteria"].items())
    rng = random.Random(seed)
    others = [opts[::-1]] if n_orders == 2 else [rng.sample(opts, len(opts)) for _ in range(n_orders - 1)]
    return [(question, _same)] + [(dict(question, criteria=dict(o)), _same) for o in others]


def _average(ps: list[dict]) -> dict:
    out: dict = {}
    for p in ps:
        for k, v in p.items():
            out[k] = out.get(k, 0) + v / len(ps)
    return out


def order_avg(ask1, question: dict, n_orders: int, seed: int = 0) -> dict:
    """Average one question over its order variants so position bias cancels out."""
    return _average([back(ask1(q)) for q, back in order_variants(question, n_orders, seed)])


class DecisionAsker:
    def __init__(self, model: str = JEV, endpoint: str | None = None, api_key: str | None = None,
                 n_orders: int = 3, name: str | None = None):
        self.d = Decisions(model, endpoint, api_key)
        self.n_orders = n_orders
        self.name = name or model.split("/")[-1]

    def ask(self, state: str, question: dict, tag: str = "") -> dict:
        return order_avg(lambda q: self.d.probs(self.d.ask(state, {"q": q}, tag), "q"), question, self.n_orders)

    def ask_many(self, state: str, questions: dict[str, dict], tag: str = "", chunk: int = 48) -> dict[str, dict]:
        """All questions for one state in as few requests as possible. Jev bills ~430 tokens per request plus ~50 per
        question and answers each question independently, so every order variant rides in the same request."""
        variants = [(qid, i, vq, back) for qid, q in questions.items()
                    for i, (vq, back) in enumerate(order_variants(q, self.n_orders))]
        answers = defaultdict(list)
        for j in range(0, len(variants), chunk):
            part = variants[j:j + chunk]
            resp = self.d.ask(state, {f"{qid}__{i}": vq for qid, i, vq, _ in part}, tag)
            for qid, i, _, back in part:
                answers[qid].append(back(self.d.probs(resp, f"{qid}__{i}")))
        return {qid: _average(ps) for qid, ps in answers.items()}


MANY_PROMPT = (
    "You estimate how survey respondents answer. For the person described at the end, give the probability of each "
    "answer option to each question, as a calibrated forecaster would. Reply with JSON only: {question id: [percent "
    "for each option, in the order listed]}, whole numbers summing to 100 for each question."
)


def _options(q: dict) -> list[tuple[str, str]]:
    """(label, text) pairs in the order shown; noul is shown as a yes/no choice."""
    if q["type"] == "score":
        return [(str(i), lvl) for i, lvl in enumerate(q["criteria"])]
    if q["type"] == "choice":
        return [(k, v or k) for k, v in q["criteria"].items()]
    return [("true", "yes"), ("false", "no")]


class LLMAsker:
    def __init__(self, key: str, provider_order: list[str] | None = None, n_orders: int = 3, name: str | None = None):
        self.chat = Chat(LLMS[key], provider_order or HOSTS[key], reasoning=REASONING.get(key))
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

    def ask_many(self, state: str, questions: dict[str, dict], tag: str = "",
                 groups: list[list[str]] | None = None) -> dict[str, dict]:
        """All questions for one persona in one prompt per order variant. Unlike Jev, a text model reads every
        question in the prompt, so `groups` keeps apart questions that would leak into each other (asking how
        someone voted implies they voted, which inflates a turnout answer in the same prompt)."""
        out: dict = {}
        for g in groups or [list(questions)]:
            sub = {q: questions[q] for q in g if q in questions}
            if sub:
                out |= self._ask_group(state, sub, tag)
        return out

    def _ask_group(self, state: str, questions: dict[str, dict], tag: str) -> dict[str, dict]:
        """One prompt per order variant. The question block comes first and the persona last, so the shared prefix can
        be served from the provider's prompt cache; answers are compact percent lists, mapped back to labels and
        averaged over variants. noul questions get a reversed yes/no too."""
        per_q = {qid: order_variants({**q, "type": "choice", "criteria": {"true": "yes", "false": "no"}}
                                     if q["type"] == "noul" else q, self.n_orders)
                 for qid, q in questions.items()}
        answers = defaultdict(list)
        for i in range(max(len(v) for v in per_q.values())):
            asked = {f"q{n + 1}": (qid, *v[i]) for n, (qid, v) in enumerate(per_q.items()) if i < len(v)}
            block = "\n".join(f"{sid}. {vq['instructions']}\n   " + " | ".join(f"[{j}] {t}" for j, (_, t) in
                                                                        enumerate(_options(vq)))
                              for sid, (_, vq, _) in asked.items())
            user = f"QUESTIONS\n{block}\n\nPERSON\n{state}"
            text = self.chat.complete([{"role": "system", "content": MANY_PROMPT}, {"role": "user", "content": user}],
                                      tag, max_tokens=40 + 30 * len(asked))
            try:
                raw = json.loads(text[text.index("{"): text.rindex("}") + 1])
            except ValueError:
                raw = {}
            for sid, (qid, vq, back) in asked.items():
                labels = [lab for lab, _ in _options(vq)]
                vals = raw.get(sid)
                try:
                    vals = [max(0.0, float(x)) for x in vals]
                    tot = sum(vals)
                    assert len(vals) == len(labels) and tot > 0
                    p = {lab: v / tot for lab, v in zip(labels, vals)}
                except (TypeError, ValueError, AssertionError):
                    p = {lab: 1 / len(labels) for lab in labels} | {"_parse_error": 1.0}
                answers[qid].append(back(p))
        return {qid: _average(ps) for qid, ps in answers.items()}


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


def batch(asker, items: list[tuple[str, dict]], tag: str = "", workers: int = 16) -> list[dict]:
    """items = [(state, question), ...] -> list of prob dicts (order preserved). Spend is tagged '<tag>:<asker>'."""
    with ThreadPoolExecutor(workers) as ex:
        return list(ex.map(lambda it: asker.ask(it[0], it[1], f"{tag}:{asker.name}"), items))


def expected(probs: dict, values=(-2, -1, 0, 1, 2)) -> float:
    return sum(probs.get(str(i), 0.0) * v for i, v in enumerate(values))
