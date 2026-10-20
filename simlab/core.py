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
        self.db.execute("pragma journal_mode=wal")
        self.db.execute("pragma synchronous=normal")
        self.db.execute("create table if not exists c (k text primary key, v text, ts real)")
        self.lock = threading.Lock()

    @staticmethod
    def key(*parts) -> str:
        # no sort_keys: option order inside `criteria` is part of the question (we average over it)
        return hashlib.sha256(json.dumps(parts, default=str).encode()).hexdigest()

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
    _total: float | None = None  # read from the file once per process, then kept in memory

    @classmethod
    def _entries(cls) -> list[dict]:
        """Every readable line. Processes appending at once on Windows can leave a broken one (28 Sep: a lone "}")."""
        out = []
        for line in cls.path.read_text().splitlines() if cls.path.exists() else []:
            try:
                out.append(json.loads(line))
            except ValueError:
                continue
        return out

    @classmethod
    def total(cls) -> float:
        if cls._total is None:
            cls._total = sum(e["usd"] for e in cls._entries())
        return cls._total

    @classmethod
    def spent(cls, tag: str, since: float = 0.0) -> float:
        return sum(e["usd"] for e in cls._entries() if e["tag"] == tag and e["ts"] >= since)

    @classmethod
    def check(cls):
        if cls.total() >= BUDGET_USD:
            raise BudgetExceeded(f"spend cap ${BUDGET_USD:.2f} reached")

    @classmethod
    def add(cls, model: str, usd: float, tag: str = ""):
        with cls.lock:
            cls._total = cls.total() + usd
            with cls.path.open("a") as f:
                f.write(json.dumps({"ts": time.time(), "model": model, "usd": usd, "tag": tag}) + "\n")


# ---------------------------------------------------------------- http
OR_BASE = "https://openrouter.ai"


class CallLog:
    """One line per model call (runs/calls.jsonl): host, tokens (reasoning included), cost, seconds, every attempt's
    status, or a cache hit. Counts and timings only, never prompts or answers; daily.py summarises it into run.json."""
    path = RUNS / "calls.jsonl"
    lock = threading.Lock()

    @classmethod
    def add(cls, model: str, tag: str, resp: dict | None = None, info: dict | None = None, cached: bool = False):
        u = (resp or {}).get("usage") or {}
        rec = {"ts": time.time(), "model": model, "tag": tag, "cached": cached}
        if not cached:
            rec |= {"provider": (resp or {}).get("provider"), "in": u.get("prompt_tokens"),
                    "out": u.get("completion_tokens"),
                    "reasoning": (u.get("completion_tokens_details") or {}).get("reasoning_tokens"),
                    "cached_in": (u.get("prompt_tokens_details") or {}).get("cached_tokens"), "usd": _cost(resp or {}),
                    **(info or {})}
        with cls.lock, cls.path.open("a") as f:
            f.write(json.dumps(rec) + "\n")


def _post(url: str, payload: dict, headers: dict, tries: int = 8, timeout: int = 120, info: dict | None = None) -> dict:
    """`info`, when given, receives each attempt's status ("timeout"/"connection" for no reply) and the seconds spent."""
    last, t0 = None, time.time()
    statuses = info.setdefault("attempts", []) if info is not None else []
    for i in range(tries):
        try:
            try:
                r = requests.post(url, json=payload, headers=headers, timeout=timeout)
            except requests.Timeout:
                statuses.append("timeout")
                raise
            except (requests.ConnectionError, requests.exceptions.ChunkedEncodingError):
                statuses.append("connection")
                raise
            statuses.append(r.status_code)
            if r.status_code in (429, 500, 502, 503, 504):
                raise requests.HTTPError(f"{r.status_code}: {r.text[:200]}")
            if r.status_code >= 400:
                raise ValueError(f"{r.status_code}: {r.text[:500]}")
            data = r.json()
            if isinstance(data, dict) and "error" in data and not ({"choices", "answers"} & data.keys()):
                raise requests.HTTPError(f"{r.status_code} with an error body: {str(data['error'])[:200]}")
            if info is not None:
                info["seconds"] = round(time.time() - t0, 3)
            return data
        except (requests.HTTPError, requests.ConnectionError, requests.Timeout,
                requests.exceptions.ChunkedEncodingError) as e:  # a connection dropped mid-reply
            last = e
            time.sleep(min(2 ** i, 30) + random.random())
    raise RuntimeError(f"giving up on {url} after {tries} tries; last error: {str(last)[:300]}")


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
            CallLog.add(self.model, tag, cached=True)
            return hit
        Ledger.check()
        info: dict = {}
        resp = _post(self.endpoint, payload, self._headers(), info=info)
        Ledger.add(self.model, _cost(resp), tag)
        CallLog.add(self.model, tag, resp, info)
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
        """The reply's text. A model that must reason gets REASONING_ROOM more tokens, because its hosts count the
        reasoning against max_tokens; an empty reply is asked again (twice at most) and never cached (1 Oct: 7% of
        GLM's reaction rows were unreadable, cut off at 70 tokens or empty from the fallback host)."""
        payload = {"model": self.model, "messages": messages, "temperature": self.temperature,
                   "max_tokens": max_tokens + (REASONING_ROOM if self.reasoning.get("effort") else 0),
                   "usage": {"include": True}, "reasoning": self.reasoning}
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        if self.provider_order:
            payload["provider"] = ({"order": self.provider_order, "only": self.provider_order}
                                   if self.model in {LLMS[m] for m in ORDERED} else {"only": self.provider_order})
        k = Cache.key("chat", self.model, payload)
        hit = CACHE.get(k)
        if hit:
            CallLog.add(self.model, tag, cached=True)
            return hit
        for _ in range(3):
            Ledger.check()
            info: dict = {}
            resp = _post(f"{OR_BASE}/api/v1/chat/completions", payload, _or_headers(), timeout=CHAT_TIMEOUT_S,
                         info=info)
            Ledger.add(self.model, _cost(resp), tag)
            CallLog.add(self.model, tag, resp, info)
            text = resp["choices"][0]["message"]["content"] or ""
            if text.strip():
                CACHE.put(k, text)
                break
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
# Allowed hosts per model, all at the same quantisation, so a run never mixes precisions (probed 27 Sep 2026).
# GLM: InferenceNet fp4 first, DeepInfra fp4 when it refuses (20 Oct). OpenInference (first from 1 Oct) began ignoring
# effort "minimal" between 17 and 20 Oct: about 3,800 characters of reasoning a call, 7 s, billed at max_tokens, and
# turnout answers 0.2 higher than the 16 Oct rows, which InferenceNet still matches. DeepSeek: InferenceNet was
# 429ing most calls and DeepSeek's own endpoint is excluded by the account's guardrail, so DeepInfra fp8. MiMo: two
# fp8 hosts, load-balanced.
HOSTS = {"glm": ["InferenceNet", "DeepInfra"], "mimo": ["Xiaomi", "DeepInfra"],
         "deepseek": ["DeepInfra"], "luna": ["OpenAI"]}
ORDERED = {"glm"}  # hosts tried in the listed order; the others are load-balanced by OpenRouter
# GLM can't turn reasoning off: "minimal" used 0 reasoning tokens on 27 Sep, 11-36 a call since 30 Sep (up to 70 on
# OpenInference, counted against max_tokens: Chat.complete adds REASONING_ROOM). Others: off.
REASONING = {"glm": {"effort": "minimal"}}
REASONING_ROOM = 200
CHAT_TIMEOUT_S = 45  # a text call takes 1-15 s; a stalled one is retried instead of holding a thread for 2 minutes
