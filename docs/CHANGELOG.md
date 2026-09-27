# Changelog: decisions and changes made in Claude Code

For Cowork to pick up. Newest first. Final decisions are also summarised in CLAUDE.md section 5.

## 2026-09-27 (evening): Matteo's infrastructure decisions; Kev training data

- Decisions recorded in CLAUDE.md section 5: site at `research.scaliastudio.dev/midterms`; no paid publishing tools (X
  by hand or Buffer's free plan); no R2 for now; the repo that runs Actions is public; Modal for GPU work; Kev fine-tune
  approved; daily Claude check wanted.
- Routing from the full scorecard (`docs/scorecard.md`): reactions default to GLM + Jev (GLM best on real events, Jev
  best on the mirror and null tests, both cheap), Luna as a spot check (neutral but ~3× the cost); base Kev is not
  usable (fails the null test); vote and turnout levels stay statistical.
- New `simlab/kevdata.py` → `data/kev/ces-v1/`: one record per state demographic cell (age × gender × race × degree)
  with the cell's weighted 2024 vote and turnout shares as soft targets, the exact fidelity-test questions, and the
  vote question in 3 option orders. Train 423 / calibration 75 records from 48 states (cells n ≥ 20); development 53
  records = the OH, NC and TX fidelity cells, never trained on (targets match `cells.json` exactly). Kev's validator:
  551 valid records, no conflicts. Fine-tune kit copied to `../kev-finetune/` (jaredpalmer/kev @ 5920c5f, Apache-2.0).
- Turnout targets now shifted per state (Matteo's decision): CES validated turnout varies by state with voter-file
  matching (raw: Utah 0.29, Montana 0.74; OH 0.54, NC 0.57, TX 0.49), so one national shift left state distortions.
  `ces.turnout_shift(df, state)` now shifts each state's cells to its official 2024 VEP turnout from
  `simlab/turnout2024.json` (UF Election Lab v0.4, 2 Mar 2026; OH 65.4%, NC 70.65%, TX 56.83%); national cells go to
  64.3% (v0.4) instead of 63.9%. Logit shifts: national +0.43, OH +0.61, NC +0.88, TX +0.40, Utah +1.89. Vote targets
  and archetypes unchanged; turnout targets moved by 0.034 (OH), 0.071 (NC), 0.002 (TX) on average. The regression
  baseline gets the same shift (the real stats layer knows past state turnout).
- Fidelity re-scored for every model from the cache ($0): turnout error in NC fell for GLM (0.134 → 0.083) and rose for
  DeepSeek (0.132 → 0.160), MiMo (0.127 → 0.158) and Jev (0.222 → 0.257); the regression baseline still leads
  (0.03–0.07). `docs/scorecard.md` regenerated.
- Kev `ces-v1` launched on Modal (H100, 2 epochs, 2,000 replay records, 1.5 h timeout = $5.92 cost bound), data
  rebuilt with the per-state turnout targets; Kev's Modal pre-flight passed (inputs ~30 tokens, limit 384).

## 2026-09-27: infrastructure blueprint (research only, no decisions)

- New `docs/infrastructure.md`: model roster and routing, engine modules, where each job runs, data feeds, Instagram and
  X publishing, the Claude Max 5x role, budget, risks, build order, and 8 open decisions for Matteo.
- Findings that change earlier assumptions: X ended its free API tier on 6 Feb 2026 (API posting is pay-per-use; Buffer's
  free plan is the free automated route); OpenRouter's Decisions API is alpha and has no batch mode; a fine-tuned Kev
  needs short inputs (state under ~384 tokens); VoteHub's free API has race-level Senate and House polls (CC BY 4.0);
  the Census API now needs a key; Kalshi's API host moved to `api.elections.kalshi.com`.

## 2026-09-27: test bench made runnable

**Setup**
- Moved to Claude Code. Git repo in `simlab/` (first commit = the Cowork snapshot); Python 3.13 venv via `uv sync`.

**Models and API (verified with real calls)**
- Jev and Kev answers match what `core.py` assumed (`answers[q].probabilities`, `noul`, `usage.cost`); the spend
  ledger agrees with OpenRouter's own usage to the cent.
- Kev on OpenRouter is served by SiliconFlow in fp8 with an 8K context, so hosted Kev is not exactly the
  full-precision model we will fine-tune.
- One host per LLM so a run never mixes quantisations: GLM → InferenceNet (fp4, the $0.045/$0.14 price the Field
  Guide assumes), DeepSeek → InferenceNet, MiMo → Xiaomi, Luna → OpenAI. DeepSeek's own endpoint is excluded by the
  account's guardrail.
- GLM-5.3 Flash cannot turn reasoning off; `effort: minimal` produced 0 reasoning tokens, so cost is unaffected.
  InferenceNet returns intermittent 429s (upstream rate limit): retries wait up to 60 s, and a re-run resumes from
  the cache.

**Test design**
- Option-order averaging for every model, not only Jev: 5-level scales are asked as written and reversed, choice
  questions in 3 orders. `jev1`, `glm1`, ... are single-order variants (a cached subset, free). Reason: the support
  scale lists the Republican side first, so a first-position bias would look like a party lean in the mirror test.
- Bug fixed: the cache key sorted option names, so shuffled choice orders were served from the cache and the
  averaging never happened for Jev/Kev.

**CES 2024 data**
- Downloaded the CSV (175 MB) and guide PDF, not the 947 MB Stata file. Dataverse rejects the default
  python-requests user agent. Every code-to-label map was checked by matching category counts to the guide (the
  guide's listing order is not the code order).
- Fidelity target `vote24`: 2024 presidential vote among validated voters, weighted with `vvweight_post` (CES's
  own recommendation). Reproduces the result: Trump 49.9, Harris 48.2, other 1.8.
- Fidelity target `turnout`: validated vote among citizens (`commonweight`), unmatched respondents counted as
  non-voters (guide specification 1: 56%), then one logit shift (+0.41) to the official 63.9% VEP turnout
  (UF Election Lab). **Assumption for the register:** voter-file match failures are spread evenly across cells on
  the logit scale. The unshifted rate is kept in each cell as `raw_true`.
- Cells: national = age (4) × gender × race (5) × degree, n ≥ 50 (59 vote cells, 78 turnout cells); OH/NC/TX =
  age (2) × gender × race (4) × degree, n ≥ 30.
- Personas for null/mirror/events: 28 strata = 7-point party ID × white/non-white × degree, weighted by national
  adult share. Each is one real OH/NC/TX respondent (every persona has a 2026 Senate race), drawn in proportion to
  survey weight; the best of 3,000 draws on gender, age, race and ideology balance is kept (picking each stratum's
  most typical respondent had skewed the set to 70% women). The events test drops the 2020 vote from the persona.

**Next, from the Field Guide**
- Plain regression baseline for fidelity (demographics only, cross-fitted by state).
- Exposure-framed wording ("who was exposed and how did it land", design rule 5) as a wording variant of the
  reaction questions in the Jev tuning step.

**Later the same day**
- Hosts revised after throttling: DeepSeek → DeepInfra fp8 (InferenceNet returned 429 on 2 of 3 calls); MiMo →
  Xiaomi + DeepInfra, both fp8, load-balanced (Xiaomi alone queued at 5–15 s per call). Requests now use
  `provider.only`, so they can never fall back to a host outside the list. 16 parallel calls per model.
- Regression baseline added (Field Guide): weighted logistic regression on age, gender, race and degree,
  cross-fitted over 5 folds of states (each state predicted by a model that never saw it). Cell predictions are
  stored as `baseline` in `simlab/cells.json` and scored as the pseudo-model `regression`. Weighted TVD: vote
  national 0.042, OH 0.047, NC 0.093, TX 0.138; turnout national 0.028, OH 0.072, NC 0.059, TX 0.036. This is the
  bar a model must beat on levels.

**First scorecard** (`docs/scorecard.md`, regenerate with `python -m simlab.scorecard`)
- Null: Jev 0.99 / 1.00 "no change"; MiMo, DeepSeek, Luna 0.94–0.96; GLM 0.90 / 0.93 (borderline); untuned Kev
  fails (0.77 / 0.73).
- Mirror: Luna has no lean (−1% of its reaction size); Jev −9% but mirrors most consistently (flip correlation 0.69);
  DeepSeek −16%; MiMo +27% and barely mirrors (0.07); GLM −2% once both directions are averaged (−44% on one
  order); Kev +29%. Averaging both scale directions removes most of the text
  models' apparent lean (DeepSeek −65% → −16%, MiMo +70% → +27%); for Jev it changes little.
- Events (19): GLM ranks best (0.81, 90% interval 0.64–0.90; 13/13 directions; 2.3 pts error vs 3.6 for "no
  change"), then Luna 0.74, MiMo 0.70, DeepSeek 0.63, Jev 0.61, Kev 0.31. Intervals overlap except Kev's; most
  events predate the models' cutoffs (possible leakage). No model gets party-level shifts right.
- Fidelity: the regression beats every model nationally; text models beat it in Texas (and GLM in NC). Jev and Kev
  give label confidence, not shares (vote TVD 0.24–0.33); turnout bias: Jev −14, Kev −11, GLM +10, Luna +10,
  MiMo 0, DeepSeek −1 points.
- Cost per 1,000 decisions (both directions): Kev $0.016, GLM $0.030, Jev $0.040, MiMo $0.076, Luna $0.095,
  DeepSeek $0.111 (DeepInfra).
