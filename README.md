# simlab — Jev / Kev / LLM test bench for the midterm engine

Tests whether decision models (Jev, Kev, our fine-tuned Kev) and cheap LLMs (GLM, MiMo, DeepSeek, GPT-6 Luna)
can do each job in the simulation. Same questions, same items, same metrics for every model.

## The four checks

| Test | What it asks | Pass looks like |
| --- | --- | --- |
| fidelity | Reproduce real CES 2024 vote and turnout shares for demographic cells | Low weighted TVD; high correlation with real shares |
| null | Irrelevant news (sports, weather...) | P(no change) ≥ 0.9, near-zero expected shift |
| mirror | Same event with the party swapped | Reaction flips sign; no built-in lean |
| events | 19 real events 2012–2026 with measured opinion shifts (`simlab/events.json`) | Right direction, right ranking, nulls stay near zero, a stable points-per-unit scale |

Plus news classification (event type, which side it helps, salience, relevance) once the news feed is in.

## Setup

1. `.env` in the Sim Research folder: `OPENROUTER_API_KEY=...` (capped key), `MODAL_TOKEN_ID=...`, `MODAL_TOKEN_SECRET=...`
2. `uv sync` (creates `.venv` from `pyproject.toml`)
3. Network: openrouter.ai, dataverse.harvard.edu, huggingface.co, modal.com must be reachable.

Spend is logged to `runs/spend.jsonl` and hard-capped at `SIMLAB_BUDGET_USD` (default $9). Every response is cached
in `runs/cache.sqlite`, so re-running a test is free and reproducible.

## Layout

- `simlab/core.py` – .env, cache, spend cap, OpenRouter Decisions + Chat clients, model roster (no Gemini/Claude)
- `simlab/askers.py` – one `ask(state, question)` interface over Jev/Kev and LLMs; option-order averaging for Jev
- `simlab/probes.py` – question wording, null news, mirror templates, news-classification questions
- `simlab/events.json` – past events with measured shifts (sources in the Field Guide / research notes)
- `simlab/tests.py` – the four tests and their metrics
- `simlab/ces.py` – CES 2024 download and demographic cells
- Kev fine-tuning uses `jaredpalmer/kev` (`skills/kev-finetune/scripts/kev_modal.py`) on Modal, ~$1 per Kev-4B run.
