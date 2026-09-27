# CLAUDE.md — Midterm Simulation Engine (handoff from Claude Cowork, 27 Sep 2026)

You are picking up a research build started in Claude Cowork. Read this whole file first. The owner is Matteo Mio
(Scalia Studio, LSE Econ & Politics). He works in voice-dictated messages; be concise, explain jargon plainly, and ask
before any spend beyond the budget below.

## 1. The project in one paragraph

Build an AI **simulation engine** that forecasts the US midterms on **3 November 2026**: all **35 Senate races + ~40
competitive House seats** (the other House seats come from a fundamentals map, re-checked regularly). Pilots:
**Ohio** (Brown v Husted special), **North Carolina** (Cooper v Whatley), **Texas** (Talarico v Paxton). The north star
is to **prove that simulation (not just polling) works**. Statistics and data set each race's **starting vote levels**;
AI voter agents simulate how **sentiment and turnout change** as daily news arrives; a weekly **assimilation filter**
reconciles the simulation with evidence; Monte Carlo turns it into win probabilities. Forecasts are published daily
(Scalia site on Cloudflare Pages, Instagram, X) with method public; open-sourcing code is undecided.

Background: Matteo's April 2026 MiroFish (45 LLM agents) simulation of Hungary called the winner but badly missed the
size (TISZA 36.7% sim vs 53.2% actual; 101 vs 141 seats; turnout 69% vs 79%). Lessons: agents stayed near priors,
turnout wasn't modelled, accuracy was judged against polls not results, corrections were manual. MiroFish is **not**
used here.

## 2. The immediate task: the Jev / Kev test bench

Before building the pilot, find out **which model can do which job**, cheaply and accurately:

- **Jev** (TypeSafe, `typesafe/jev-1.13` on OpenRouter): a *decision model* — no text generation; you send a `state`
  and typed questions (`choice` up to 255 options, `score` up to 10 ordered levels, `noul` yes/no) and get a
  probability per option. $0.042/M input, output free. **Closed weights: cannot be fine-tuned.** We "tune the system
  around it": question wording, option-order averaging (order shifts its answers), and a calibration curve fitted on
  real data. Caveat: its probabilities mean "how sure I am of the label", not "how a population splits".
- **Kev** (Jared Palmer, `jaredpalmer/kev-4b` on OpenRouter; repo github.com/jaredpalmer/kev, Apache-2.0): open-weights
  Jev twin (LoRA + pointer head on Qwen3.5). **This is the model we fine-tune** ("our own Jev"). Kev's trainer supports
  **soft targets**, so training on real survey respondents makes its probabilities mean population shares.
- **Text LLMs** for jobs that need text or as comparison: **GLM-5.3 Flash**, **MiMo-V2.6-Flash**, **DeepSeek V4.1
  Flash**, **GPT-6 Luna**.

### Model policy (hard rule)
**Never use Gemini or Claude models in the engine.** GPT-6 Luna is the only US model allowed. Prefer Chinese open
models (GLM, MiMo, DeepSeek) and Jev/Kev wherever a decision model can do the job. Route each job to the cheapest
specialised model (decision models, embeddings, rerankers, small LLMs) rather than one general LLM. Use free model
requests where useful (development, tests). Keep LLM reasoning off (it bills as output).

### The four checks (identical items and metrics for every model)
| Test | What | Pass looks like |
|---|---|---|
| fidelity | Reproduce real CES 2024 vote/turnout shares for demographic cells (national + OH/NC/TX) | low weighted TVD, high correlation |
| null | 20 politically irrelevant news items | P(no change) ≥ 0.9, ~0 expected shift |
| mirror | 16 events asked twice with the party swapped | reaction flips sign; no built-in lean |
| events | 19 real events 2012–2026 with measured opinion shifts (`simlab/events.json`) | right direction and ranking, nulls ~0, stable points-per-unit scale |
Plus **news classification** (event type, which side it helps, salience, relevance) — gold labels from GLM+MiMo+Luna
consensus, spot-checked by Matteo.

### Then
1. Jev system tuning (wording variants, 1 vs 3 option orders, isotonic/temperature calibration on a train split).
2. Kev fine-tunes on Modal (~$1 per Kev-4B run on an H100), starting from `--init_from jaredpalmer/kev-4b`:
   (a) vote + turnout from CES respondents (soft targets), (b) news classification, (c) **one multi-task model**.
   Evaluate with **state held out** (train on others, test on OH/NC/TX) to decide: per-task vs one model, per-state vs
   national.
3. Scorecard: for each simulation job, which model wins on accuracy and cost. Then build the **context layer**
   (scraping, news digests, state profiles and issue maps that every model reads from) and run the pilot.

## 3. What already exists (in this folder)

```
simlab/
  README.md
  simlab/core.py      .env loading, sqlite response cache, spend ledger + hard cap, OpenRouter Decisions + Chat clients, model roster
  simlab/askers.py    one ask(state, question) interface for Jev/Kev/LLMs; Jev option-order averaging; batch(); expected()
  simlab/probes.py    question wording (5-level support/turnout scales), NULL_NEWS, MIRROR_TEMPLATES, news-classification questions
  simlab/events.json  19 events with measured shifts (shift_toward_D, party breakdowns, weights by source quality)
  simlab/tests.py     fidelity(), null_test(), mirror_test(), events_test() -> metrics + runs/<test>__<model>.jsonl
  simlab/personas.py  structured persona text (survey fields only; NO LLM-written backstories — they drift left)
  simlab/ces.py       CES 2024 download from Harvard Dataverse (doi:10.7910/DVN/X11EP6) + column auto-detection
  _to_delete/         stray empty dirs; ignore or delete
```
**Written but never run** (the Cowork sandbox had no network). Expect small fixes. Known gaps to handle first:
- The OpenRouter Decisions API response shape (`answers[qid].probabilities`, `usage.cost`) is assumed from docs and
  Kev's README — verify with one real call and adjust `Decisions.probs()` / `_cost()`. Endpoint:
  `POST https://openrouter.ai/api/alpha/decisions` with `{model, state, questions}`.
- `ces.py` only downloads and detects columns; write the cell builder after inspecting the real CES 2024 codebook
  (vote24 item, validated turnout, weight names). Targets must not be used as persona inputs.
- No `run.py` CLI yet; add one (e.g. `python -m simlab.run null --models jev,kev,glm,mimo`).
- Persona sample for null/mirror/events: ~24–30 weighted CES archetypes spanning party ID; events need party D/R/I.
- `Chat.distribution` has a harmless no-op line (`if tot > 1.5: tot = tot`); normalisation already handles percents.

## 4. Setup

- `.env` in the parent `Sim Research` folder (core.py also checks `simlab/.env`):
  `OPENROUTER_API_KEY=` (a **separate key capped at $10**), `MODAL_TOKEN_ID=`, `MODAL_TOKEN_SECRET=`. Never print keys.
- Python ≥3.12 (Kev needs 3.12/3.13), `uv`. `pip install requests pandas numpy scipy scikit-learn`.
- Kev: `git clone https://github.com/jaredpalmer/kev` — fine-tuning recipe in `skills/kev-finetune/`
  (`scripts/kev_modal.py::train|evaluate|compare|teardown`; record format in `references/data-format.md`:
  System One request + `label`, or soft `target` weights). Tear Modal resources down after use.
- Budget: **$10 total** for the test phase on OpenRouter (code caps at $9 via `SIMLAB_BUDGET_USD`); Modal on the free
  $30/month credit. Overall engine budget target: under $50/month, lowest cost at highest performance.
- Every response is cached (`runs/cache.sqlite`); spend logged to `runs/spend.jsonl`. Keep both out of git.

## 5. Design decisions already made (don't relitigate without asking)

- Levels from statistics (FLIPR/538-style baseline on the **new 2026 maps**); agents simulate **change**.
- Most news reactions go to **enthusiasm/turnout**; vote switching mainly among **undecided** voters, a little among
  cross-pressured groups; firm partisans barely switch.
- **Minimal assumptions**: priors are weak starting ranges, **state-specific**, recalibrated by news and the filter;
  keep an **assumption register**; **no hard caps** on single-event shifts (heavy-tailed; large shifts need
  corroboration).
- **Constrain the model, free the system**: models answer narrow structured questions; the system (filter-learned,
  per state) decides how much of each answer to apply.
- Per-state **issue map** (main issues → which archetypes → effect on undecideds, turnout, sentiment, switchers).
- Filter: ensemble Kalman update on a ~100-dim factor state (national, regional, state, demographic, race) + a small
  particle filter over 5–8 agent parameters, **estimated per state and region**; permanent poll-bias term.
- **Never assimilate prediction markets** (they are a benchmark). Headline = poll-assimilated simulation. Blind
  (no-2026-polls) track runs **after** the election on frozen daily data snapshots with models whose cutoff is before
  3 Nov — so **save daily raw snapshots from now**.
- Early vote (NC daily absentee files, TX county totals, OH): input + benchmark + trigger to recalibrate.
- Backtests: 2018–2024 are contaminated by LLM training data; judge leakage state by state and model by model.
- Evaluation: fixed weekly scoring dates; Brier/log loss/CRPS; baselines = poll average, markets, Cook ratings,
  stats-only engine (agents off), plain LLM forecaster; pre-declared "divergence calls". Never call outputs a "poll".
- Free data only; attribute Wikipedia (CC BY-SA); no RealClearPolling/X scraping; aggregate voter-file data only.
- Hosting on Cloudflare Pages, linked from scaliastudio.dev. No paid ads/boosts, no campaign coordination
  (Matteo is a non-US national).

## 6. Reference material (read, don't duplicate)

Local snapshots (read these; Claude Code cannot open claude.ai links):
- `docs/field-guide.md` — the expert review: prior projects, voter-change science and priors, starting levels,
  calibration/assimilation defaults, decision models (Jev/Kev) and routing, stack and costs, data kits, evaluation
  protocol, publishing rules, dos & don'ts, ranked possibilities, review outcomes and open tasks.
- `docs/plan.md` — the research map: Hungary scorecard, landscape, engine design, pilot choice, free data stack.
- Hungary paper: `../The Simulation of Democracy - Final15.pdf`.

The live docs are edited in Claude Cowork (plan: https://claude.ai/code/artifact/673aa293-22c4-4d3a-806e-6a50c69f82cc,
Field Guide: https://claude.ai/code/artifact/c640add2-61d5-4d74-8fa2-c39365d09819). The snapshots don't update
themselves: when Matteo says the docs changed, ask him to re-export them from Cowork into `docs/`. Decisions made
in Claude Code go into this CLAUDE.md (section 5) and a short `docs/CHANGELOG.md`, so Cowork can pick them up.

## 7. Key data sources (all free)

CES 2024 + cumulative (Dataverse), ANES 2024, AP VoteCast; MIT Election Lab; Redistricting Data Hub (new-map block
files) + The Downballot 2024 results by new district; NC & Ohio voter files; FEC API; GDELT, Media Cloud, local RSS;
Kalshi/Polymarket/PredictIt APIs (benchmark only); Wikipedia poll tables via MediaWiki API (pin `oldid`, sequential
requests); VoteHub API (generic ballot/approval); 538 `checking-our-work-data` + Wayback poll archives for backtests;
Stanford DIME, Voteview; NCSBE absentee files. Details and caveats: Field Guide → Data.

## 8. Working agreements

- Report results as a scorecard per job (model × metric × cost), with what you'd route where and why.
- Ask Matteo before: exceeding the $10 test budget, paid data, anything touching his accounts, publishing anything.
- Open tasks he wants explained later (don't block on them): OSF pre-registration + timestamped git tags; replay
  screening; AutoEmulate (after the pilot); whether contacting Philipp Schoenegger (LSE) is worth it; review of the
  evaluation protocol before pre-registration and of publishing/ethics before the first post.
- First moves: verify network + keys → one real Jev call and one GLM call → CES download + cells → run null & mirror
  on jev, jev1, kev, glm, mimo, deepseek, luna → events → fidelity → share the first scorecard.
