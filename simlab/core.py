"""Core plumbing: .env loading, response cache, spend ledger with a hard cap, API clients.

Every model call goes through `Decisions.ask` (Jev/Kev/Span, typed questions -> probabilities)
or `Chat.distribution` (a text LLM asked to return a probability distribution as JSON).
Responses are cached by a hash of (endpoint, model, payload), so re-running a test is free
and reproducible. Spend is read from the API's reported cost and written to a ledger; once
the cap is reached every new (uncached) call raises BudgetExceeded.
"""
from __future__ import annotations

import hashlib
import json
import os
import random
import sqlite3
import threading
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "runs"
RUNS.mkdir(exist_ok=True)


# ---------------------------------------------------------------- env
def load_env() -> None:
    """Load KEY=VALUE lines from the first .env found (SIMLAB_ENV, ./.env, ../.env)."""
    candidates = [os.environ.get("SIMLAB_ENV"), ROOT / ".env", ROOT.parent / ".env"]
    for c in candidates:
        if c and Path(c).is_file():
            for line in Path(c).read_text(encoding="utf-8-sig").splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
            return


load_env()
BUDGET_USD = float(os.environ.get("SIMLAB_BUDGET_USD", "9.0"))  # keep $1 headroom under the $10 key cap


# ---------------------------------------------------------------- cache
class Cache:
    def __init__(self, path: Path = RUNS / "cache.sqlite"):
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.db.execute("create table if not exists c (k text primary key, v text, ts real)")
        self.lock = threading.Lock()

    @staticmethod
    def key(*parts) -> str:
        return hashlib.sha256(json.dumps(parts, sort_keys=True, default=str).encode()).hexdigest()

    def get(self, k):
        with self.lock:
            r = self.db.execute("select v from c where k=?", (k,)).fetchone()
        return json.loads(r[0]) if r else None

    def put(self, k, v):
        with self.lock:
            self.db.execute("insert or replace into c values (?,?,?)", (k, json.dumps(v), time.time()))
            self.db.commit()


CACHE = Cache()


# ---------------------------------------------------------------- budget
class BudgetExceeded(RuntimeError):
    pass


class Ledger:
    path = RUNS / "spend.jsonl"
    lock = threading.Lock()

    @classmethod
    def total(cls) -> float:
        if not cls.path.exists():
            return 0.0
        return sum(json.loads(l)["usd"] for l in cls.path.read_text().splitlines() if l.strip())

    @classmethod
    def check(cls):
        if cls.total() >= BUDGET_USD:
            raise BudgetExceeded(f"spend cap ${BUDGET_USD:.2f} reached")

    @classmethod
    def add(cls, model: str, usd: float, tag: str = ""):
        with cls.lock:
            with cls.path.open("a") as f:
                f.write(json.dumps({"ts": time.time(), "model": model, "usd": usd, "tag": tag}) + "\n")


# ---------------------------------------------------------------- http
OR_BASE = "https://openrouter.ai"


def _post(url: str, payload: dict, headers: dict, tries: int = 5, timeout: int = 120) -> dict:
    for i in range(tries):
        try:
            r = requests.post(url, json=payload, headers=headers, timeout=timeout)
            if r.status_code in (429, 500, 502, 503, 504):
                raise requests.HTTPError(f"{r.status_code}: {r.text[:200]}")
            if r.status_code >= 400:
                raise ValueError(f"{r.status_code}: {r.text[:500]}")
            return r.json()
        except (requests.HTTPError, requests.ConnectionError, requests.Timeout):
            time.sleep(2 ** i + random.random())
    raise RuntimeError(f"giving up on {url}")


def _or_headers():
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise RuntimeError("OPENROUTER_API_KEY missing: add it to the .env file in the Sim Research folder")
    return {"Authorization": f"Bearer {key}", "HTTP-Referer": "https://scaliastudio.dev", "X-Title": "simlab"}


def _cost(resp: dict) -> float:
    u = resp.get("usage") or {}
    for k in ("cost", "total_cost"):
        if isinstance(u.get(k), (int, float)):
            return float(u[k])
    return 0.0


# ---------------------------------------------------------------- decision models (Jev / Kev / Span)
class Decisions:
    """TypeSafe System One shaped calls.

    `endpoint` is OpenRouter's decisions API by default; pass a Kev server URL
    (e.g. a Modal deployment of our fine-tuned Kev) to use the same code path.
    """

    def __init__(self, model: str = "typesafe/jev-1.13", endpoint: str | None = None, api_key: str | None = None):
        self.model = model
        self.endpoint = endpoint or f"{OR_BASE}/api/alpha/decisions"
        self.api_key = api_key

    def _headers(self):
        if self.api_key:
            return {"Authorization": f"Bearer {self.api_key}"}
        return _or_headers()

    def ask(self, state, questions: dict, tag: str = "") -> dict:
        payload = {"model": self.model, "state": state, "questions": questions}
        k = Cache.key("decisions", self.endpoint, payload)
        hit = CACHE.get(k)
        if hit is not None:
            return hit
        Ledger.check()
        resp = _post(self.endpoint, payload, self._headers())
        Ledger.add(self.model, _cost(resp), tag)
        CACHE.put(k, resp)
        return resp

    @staticmethod
    def probs(resp: dict, qid: str) -> dict:
        a = resp["answers"][qid]
        if a.get("type") == "noul" or "noul" in a:
            p = float(a["noul"])
            return {"true": p, "false": 1 - p}
        return {str(k): float(v) for k, v in a["probabilities"].items()}


# ---------------------------------------------------------------- text LLMs asked for a distribution
class Chat:
    def __init__(self, model: str, provider_order: list[str] | None = None, temperature: float = 0.0,
                 reasoning: dict | None = None):
        self.model = model
        self.provider_order = provider_order
        self.temperature = temperature
        self.reasoning = reasoning or {"enabled": False}

    def complete(self, messages: list[dict], tag: str = "", max_tokens: int = 300, json_mode: bool = True) -> str:
        payload = {"model": self.model, "messages": messages, "temperature": self.temperature,
                   "max_tokens": max_tokens, "usage": {"include": True},
                   "reasoning": self.reasoning}
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        if self.provider_order:
            payload["provider"] = {"order": self.provider_order, "allow_fallbacks": False}
        k = Cache.key("chat", self.model, payload)
        hit = CACHE.get(k)
        if hit is not None:
            return hit
        Ledger.check()
        resp = _post(f"{OR_BASE}/api/v1/chat/completions", payload, _or_headers())
        Ledger.add(self.model, _cost(resp), tag)
        text = resp["choices"][0]["message"]["content"] or ""
        CACHE.put(k, text)
        return text

    def distribution(self, system: str, user: str, options: list[str], tag: str = "") -> dict:
        """Ask for {option: probability}; parse robustly and renormalise."""
        text = self.complete([{"role": "system", "content": system}, {"role": "user", "content": user}], tag)
        try:
            s = text[text.index("{"): text.rindex("}") + 1]
            raw = json.loads(s)
            raw = raw.get("probabilities", raw)
        except Exception:
            return {o: 1 / len(options) for o in options} | {"_parse_error": 1.0}
        out = {}
        for o in options:
            v = raw.get(o, raw.get(o.lower(), 0))
            try:
                out[o] = max(0.0, float(str(v).strip("%")))
            except ValueError:
                out[o] = 0.0
        tot = sum(out.values())
        if tot <= 0:
            return {o: 1 / len(options) for o in options} | {"_parse_error": 1.0}
        return {o: v / tot for o, v in out.items()}


# Model roster (no Gemini, no Claude; GPT-6 Luna is the only US model allowed)
JEV = "typesafe/jev-1.13"
KEV = "jaredpalmer/kev-4b"
LLMS = {
    "glm": "z-ai/glm-5.3-flash",
    "mimo": "xiaomi/mimo-v2.6-flash",
    "deepseek": "deepseek/deepseek-v4.1-flash",
    "luna": "openai/gpt-6-luna",
}
# One host per model so a run never mixes quantisations (cheapest working host, probed 27 Sep 2026;
# InferenceNet serves GLM at fp4). DeepSeek's own endpoint is excluded by the account's guardrail.
HOSTS = {"glm": "InferenceNet", "mimo": "Xiaomi", "deepseek": "InferenceNet", "luna": "OpenAI"}
# GLM can't turn reasoning off; "minimal" used 0 reasoning tokens in the probe. Others: off.
REASONING = {"glm": {"effort": "minimal"}}
