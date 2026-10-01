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
  `OPENROUTER_API_KEY=` (a **separate key capped at $10**). Never print keys.
- Modal: logged in via `python -m modal setup`; the token lives in `~/.modal.toml`, not `.env` (core.py would load empty
  `MODAL_TOKEN_*` lines into the environment, where they override the login). `python3` is the Microsoft Store stub
  and `modal.exe` isn't on PATH, so run every Modal command as `python -m modal ...`.
- Python ≥3.12 (Kev needs 3.12/3.13), `uv`. `pip install requests pandas numpy scipy scikit-learn`.
- Kev: fine-tune kit at `kev-finetune/` in this repo (jaredpalmer/kev @ 5920c5f, our changes in its SOURCE.md). Run
  `python -m modal run scripts/kev_modal.py::train|evaluate|compare|teardown` from the kit
  (record format in `references/data-format.md`: System One request + `label`, or soft `target` weights). Pass
  `--timeout` to `train` (the 3 h default bounds a run at $11.85 on an H100; a 4B run on ~1k records takes 12–15 min).
  Tear Modal resources down after use.
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

Decided in Claude Code, 27 Sep (reasons in `docs/CHANGELOG.md`):
- Every model gets option-order averaging: scales asked as written and reversed, choices in 3 orders; `<model>1`
  = single order (cached, free).
- Pinned hosts per LLM, one quantisation per model (GLM → InferenceNet with DeepInfra overflow, DeepSeek →
  DeepInfra, MiMo → Xiaomi + DeepInfra, Luna → OpenAI); GLM reasoning `effort: minimal` (can't be disabled, 0
  reasoning tokens).
- GLM hosts (Matteo, 1 Oct): OpenInference fp4 first, DeepInfra and InferenceNet fp4 as ordered fallbacks. This
  reverses the 27 Sep pin, because every host now makes GLM reason (11-36 tokens a call); same answers to the 64
  calibration events (correlation 0.95, directions unchanged), $0.000013 against $0.000031 a call.
- Fidelity targets: vote among CES validated voters (`vvweight_post`); turnout from the Census CPS 2024 November
  supplement (`simlab/cps.py`: self-reported, non-answerers dropped, each state reweighted to its official 2024
  turnout in `simlab/turnout2024.json`), demographic cells only. CES validated turnout is not used: it tracks
  voter-file match rates (correlation 0.99 across cells; young men of color at 5–15%) (Matteo, 27 Sep night).
- Test personas: 28 party-ID × race × degree strata, one real OH/NC/TX respondent each, balanced on gender, age,
  race and ideology (`simlab/archetypes.json`, built by `python -m simlab.ces`).

Decided by Matteo, 27 Sep evening (infrastructure; details in `docs/infrastructure.md`):
- Site at **notapoll.org** (Matteo, 29 Sep; `site/`, Next.js static export on a Cloudflare Worker, as scaliastudio.dev);
  `labs.scaliastudio.dev/midterms` redirects there. 3 Oct: no numbers; 12 Oct: forecast pages after Matteo's go.
  Brand domain notapoll.org, shown on every image; its own site comes later. Handles: Instagram and Threads
  @notapollorg (notapoll.org was taken; Matteo, 30 Sep), X @notapoll, Bluesky @notapoll.org. Scheduling on free tools only: Buffer Free for X, Threads and
  Bluesky; Instagram's own scheduler.
- No paid publishing tools: Instagram posting is free (Meta Business Suite by hand, official API later); X by hand or
  through Buffer's free plan, never paid X API credits. Threads and Bluesky optional. Social accounts created later.
- No Cloudflare R2 for now: the site hosts post images and JSON; GitHub holds the public archive.
- One public GitHub repo holds the engine code, the workflows and the published forecasts (unlimited Actions minutes,
  within GitHub's terms); raw data, the model-answer cache and keys stay private (private data repo, GitHub secrets).
  Repos: `github.com/Matteomio16/simlab` (public; this folder) and `github.com/Matteomio16/simlab-data` (private;
  local clone at `Sim Research/simlab-data`, rules in its README). No licence chosen yet for the public code.
- Modal is for GPU work (Kev fine-tuning and serving); daily CPU jobs run on GitHub Actions.
- Kev fine-tune approved: `ces-v1` (CES cells, soft targets, OH/NC/TX held out), trained 27 Sep on Modal ($3.08).
- Kev serving (kit settings in `kev-finetune/scripts/kev_modal.py`): at most one GPU (`KEV_SERVE_MAX_CONTAINERS=1`,
  extra requests queue), 60 s idle before scaling to zero (`KEV_SERVE_IDLE_S`), and one batch of Kev questions per
  day. Serve soft-target runs with `KEV_SERVE_TEMPERATURE=1.0`: Kev's fitted temperature sharpens the probabilities
  away from population shares (ces-v1 at its fitted 0.30 triples the share error; raw is already share-calibrated).
- Modal credit ($30/month, no rollover): October keeps at least $18 for serving; fine-tuning spends September's
  expiring credit first, then at most $12 in October. Every training run is capped with `--timeout` (≤ 3000 s) and
  preceded by `python -m modal billing summary`.
- Daily Claude check at 11:30 UK: desktop scheduled task `midterm-daily-check` (runs while the app is open); emails
  Matteo a digest, and drafts posts once forecasts exist.

Decided by Matteo, 28 Sep (statistics layer; details in `docs/stats-groundwork.md` §8 and `docs/CHANGELOG.md`):
- Partisan polls are those sponsored by a party, campaign or partisan group, not Wikipedia's "(R)"/"(D)" pollster tags.
  They get half weight and a shift against the sponsor, estimated alongside the pollster house effects (about 2.5
  points on 2018–24 polls; re-estimated on 2026 polls). Expert ratings stay out of the numbers.
- Senate headline: "Republicans hold 50+", with independents shown separately.
- Approval enters only if it passes a leave-one-cycle-out test.
- Fundamentals use the weights fitted on 2012–24 (`simlab/stats_params.json`): lean 0.62 × latest + 0.26 × previous
  presidential margin, and 0.38 of the nominee's last statewide over-performance. The generic ballot is lowered by its
  historical 2.8-point overstatement of Democrats where it feeds the fundamentals.
- The versions of one poll are averaged.
- No fixed correction for the polls' recent Democratic lean: the national error term (SD about 3) covers a miss of
  that size.
- A published poll table built on Wikipedia data is CC BY-SA.

Decided by Matteo, 28 Sep (engine; details in `docs/engine-design.md`, `docs/roadmap.md` and `docs/CHANGELOG.md`):
- **Dates:** build until 4 Oct; a private pilot for OH, NC, TX, IA and ME from 5–11 Oct (Iowa and Maine added by
  Matteo, 29 Sep); the public full run from 12 Oct, with all 35 Senate races and ~40 House seats. If the House isn't
  ready on 9 Oct, it starts from statistics only.
- **Design:** the forecast machine is a chain of steps that pass dated files. `docs/engine-design.md` is the contract
  between the sessions (Engine, Statistics, Kev, Content & site).
- **News effects are voter reactions**, including backlash and mobilisation, not who a story helps on paper. Only the
  voter groups' reactions move numbers.
- **Only people who can move count.** A reaction applies only to the share of a group that can still change: the
  persuadable share for vote choice and the mobilisable share for turnout, both estimated from CES pre- and
  post-election waves.
- **Models:** GLM gives the reactions on its own. Kev react-v1 failed the held-out test on 28 Sep (size-tracking 0.00,
  errors correlated 0.75 with GLM's, averaging worse than GLM alone); react-v2 failed too on 29 Sep (direction 11/13,
  averaging worse). Matteo reopened it on 29 Sep: Kev react-v2-2 runs in shadow mode (answers every day, never applied,
  scored weekly against GLM), served on Modal (B4); Kev weights are kept. No further reaction training runs.
- **News:**
  - Jev labels the news, with outlet names removed.
  - Attention comes from coverage data; the model's guess only breaks ties.
  - Stories about polls get no reactions, because polls enter through the filter.
  - Sources are GDELT and Media Cloud. Google News is not used: its feed's terms allow only personal news readers.
- **Daily job:** it runs on GitHub Actions at 09:47 UTC and writes its outputs to the private data repo. Its schedule is
  switched on at the pilot (repository variable `PIPELINE_ON`); manual runs work any time.

Decided by Matteo, 28 Sep evening (statistics; details in `docs/stats-groundwork.md` §8, D14–D23, and `docs/CHANGELOG.md`):
- **News sizes are ranges, not single values.** Each simulated election draws its own switching and turnout sizes:
  they average the fitted 0.21, turnout equals switching as a starting point, and they can go well up or down. No
  single data point drives the result (the Hungary lesson).
  - Each race shows how its forecast changes if news matters less or more.
  - `simlab/move_params.json` records where the sizes come from, the files they pass through and what updates them:
    the weekly filter, every Monday from 5 Oct (the first run is a private pilot rehearsal; Matteo, 29 Sep).
  - The news uncertainty has three layers (Matteo, 29 Sep): one overall scale; each state's sensitivity (its own
    draw); and each story's strength. A story's strength is drawn once per simulated election (sd 0.42 of its effect,
    from 45 past events). A national story's draw is shared by every race it reaches; a state story's stays in its
    own race.
- **GLM's lean is corrected (Matteo, 29 Sep).** GLM's reactions sit slightly on the Republican side of real past
  opinion shifts (−0.27 ± 0.22 points per event), so moves adds +0.08 on its support scale for every group; Kev's shadow
  rows stay raw. The weekly filter re-estimates it, and a negative estimate goes to Matteo.
- **Correlation floor (Matteo, 29 Sep):** no two Senate races move together less than 0.25. The floor touches only the
  polling and fundamentals error, never the news: a story about one state stays in that state (a Maine story doesn't
  move Alaska). House seats keep the shared national, regional and state errors without the floor.
- **Fat tails keep the fitted spread**, and extremes also follow the simulated dynamics.
- **News moves every race by its full effect, polls or not.** Polls correct the statistical level underneath.
- **How long news lasts (Matteo, 29 Sep): news fades fast.**
  - Every story fades from the day it is first seen, with a 5.5-day half-life: about 40% left after a week, 17% after
    two, 7% after three.
  - A one-off story (endorsements, scandals, debates, ads, candidates' policy news) that drops out of the news also
    fades within about a day.
  - Lasting topics (the economy and prices; national events such as war) keep fading at the same age rate after the
    news moves on.
  - The 3 Nov forecast counts only what is expected to remain by then. The forecast also shows "if the election were
    today" (Matteo, 29 Sep).
- **Senate:** King and Sanders count with Democrats. The new independents (Osborn, Achilles, Bengs, Bodnar) are shown
  as independents, with the share of simulations where they hold the balance. The final presentation is decided
  later.
- **The simulation runs only where races are contested.** Statistics runs for every race.
  - A daily tier per race (full simulation, watch, statistics only) is set in `races.json`.
  - A race runs on statistics alone only when the stats-only forecast, Cook and the market all call it safe: an
    unsimulated flip would count against the simulation.
- **Montana:** no three-way model while it isn't competitive; it is on the watch list.
- **Voter groups (Matteo, 29 Sep):** each group's starting split comes from Kev ces-v3b in every race, House and
  Senate, with the survey numbers where Kev has no answer; each race's level stays statistical. The survey numbers are
  kept for the check after 3 Nov.

## 6. Reference material (read, don't duplicate)

Local snapshots (read these; Claude Code cannot open claude.ai links):
- `docs/field-guide.md` — the expert review: prior projects, voter-change science and priors, starting levels,
  calibration/assimilation defaults, decision models (Jev/Kev) and routing, stack and costs, data kits, evaluation
  protocol, publishing rules, dos & don'ts, ranked possibilities, review outcomes and open tasks.
- `docs/plan.md` — the research map: Hungary scorecard, landscape, engine design, pilot choice, free data stack.
- Hungary paper: `../The Simulation of Democracy - Final15.pdf`.
- `docs/infrastructure.md` — infrastructure blueprint (27 Sep): model roster and routing, engine modules, where each
  job runs, data feeds, Instagram/X publishing, Claude Max 5x role, budget, risks, open decisions.

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
