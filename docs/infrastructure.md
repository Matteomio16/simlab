> Written in Claude Code on 27 Sep 2026 from eight parallel research sweeps (official docs and live API calls made
> today), the test bench, and `plan.md` / `field-guide.md`. Prices and limits are as of today; anything marked
> *(unverified)* needs a check before we depend on it. If this file and CLAUDE.md disagree, CLAUDE.md wins. Nothing
> here is decided until Matteo says so (see section 13).

# Midterm Engine: Infrastructure Blueprint

## 1. The stack on one page

| Layer | Recommended pick | Runs on | Est. $/month |
| --- | --- | --- | --- |
| Model gateway | OpenRouter: a dev key and a prod key, each with a spend cap; a guardrail that denies `anthropic/*` and `google/*` | — | see models |
| Voter reactions | GLM-5.3 Flash + Jev 1.13 blend, calibrated per state; GPT-6 Luna as a spot check; our fine-tuned Kev-4B if it earns a place | OpenRouter; Modal GPU | $10–20 |
| News labels | Jev 1.13 (hosted, pinned slug) | OpenRouter | ~$3 |
| Text jobs (event cards, auditor, baselines) | DeepSeek V4.1 Flash or GLM-5.3 Flash; GPT-6 Luna as the one US model; MiMo-V2.6 for the weekly auditor | OpenRouter | $1–5 |
| Embeddings | Qwen3-Embedding-8B | OpenRouter | < $0.50 |
| Engine code | Python 3.13 package (uv); OASIS arm in its own Python 3.11 env | GitHub Actions (public repo) | $0 |
| Kev fine-tune and serving | Kev repo's `kev_modal.py` (train on H100, serve on L40S, scale to zero) | Modal GPU | $5–25, inside free credit |
| Raw snapshots, cache exports | a private GitHub data repo (small files; aggregates, not raw voter files) | GitHub | $0 |
| Public data and post images | served by the site itself (no R2 for now) | Cloudflare | $0 |
| Website | Cloudflare Worker with static assets at `research.scaliastudio.dev/midterms`, linked from Scalia | Cloudflare | $0 |
| Scheduling | GitHub Actions in a public repo for the daily CPU jobs (unlimited minutes); Modal for GPU jobs | GitHub, Modal | $0 |
| Instagram | Meta Business Suite by hand, then the Instagram API with Instagram Login (own account, no app review) | — | $0 |
| X | x.com's free scheduler by hand, then Buffer's free plan; never paid X API credits | — | $0 |
| Extra channels | Threads API, Bluesky | — | $0 |
| Proof of timing | OpenTimestamps daily, signed git tag weekly, OSF pre-registration, Zenodo at milestones, Internet Archive capture | — | $0 |
| Monitoring | healthchecks.io (20 free checks) → Telegram / ntfy / email | — | $0 |
| Claude Max 5x | building (Claude Code), research and docs (Cowork), daily review and post drafting, optional routines; never inside the forecast | — | existing subscription |

**New spend:** about $5/month for the 3-state pilot and $15–35/month at full scale (35 Senate + 40 House seats),
with every publishing channel free. Modal work fits inside its $30/month free credit. Measured model costs per decision
are in `docs/scorecard.md`.

## 2. Ground rules this design keeps

- Paid inputs: Claude Max 5x, one OpenRouter account, Modal. Everything else is free or stays inside a free tier.
  Engine budget under $50/month.
- Model policy: no Gemini or Claude models in the engine; GPT-6 Luna is the only US model. In practice that also rules
  out NVIDIA's free Nemotron models (US), `openrouter/free` and `typesafe/jev-router` (routers that can pick any model,
  roster unpublished), `stealth/*` models (unknown origin) and `~...-latest` aliases (they change without notice).
- Claude builds, researches and reviews; it never produces forecast numbers.
- Free data only; no scraping of X or RealClearPolling; prediction markets are a benchmark, never an input.
- Organic posting only; "AI-simulated voters, not a poll" inside every image; Matteo approves every post.

**The clock (37 days)**

| Date | What |
| --- | --- |
| 4 Sep | North Carolina began mailing absentee ballots (NCSBE daily files already exist) |
| ~6 Oct | Ohio early in-person voting starts *(statutory: day after the 5 Oct registration deadline; confirm on the SOS site in a browser)* |
| 12 Oct | Target for the first public pilot forecast (plan) |
| ~13 Oct | Code freeze; later changes go in a public changelog, old and new versions both scored |
| 15–31 Oct | North Carolina in-person early voting |
| ~19–30 Oct | Texas early voting *(statutory: 17th day before, moved to Monday; confirm)* |
| 3 Nov | Election day |

## 3. How the pieces fit

```
EVERY 3 HOURS   snapshot → raw, immutable, hashed files in the private data repo + manifest
                polls · markets · news headlines · early-vote files · FEC · ratings · economy · pageviews

DAILY 09:17 UTC (GitHub Actions, public repo; Kev on Modal GPU when used)
  context       dedup + cluster (embeddings) → race tags → event labels (Jev) → short event cards (DeepSeek or GLM)
  baseline      partisan lean on new maps + national environment + candidates + poll average → starting levels
  electorate    CES archetypes per state, weighted to census, voter files and 2024 results
  agents        race × archetype × salient event → GLM + Jev → support shift + turnout shift
                → calibration curve → damping / decay / weights (system parameters, learned per state)
  filter        cheap Kalman update from new polls (no model calls)
  monte carlo   40,000 correlated draws → win probabilities, seat counts
  outputs       forecast.json · charts (web + JPEG + MP4) · draft captions · run manifest + hashes
      │                         │                                        │
  website             post kit → Matteo reviews with Claude       archive (hashes, timestamps, IA capture)
                      → Instagram · X · Threads · Bluesky

WEEKLY (fixed day and hour, US Eastern)
  ensemble Kalman update on the factor state + particle filter over agent parameters (per state and region)
  scoring vs snapshotted baselines (poll average, markets, ratings, stats-only engine) · auditor note · divergence calls
```

The daily job mostly waits on web requests, so it needs little compute (roughly 20–40 minutes on 2 CPUs). Each model
question is asked once per archetype and event; the ensemble's uncertainty lives in the system parameters, not in
repeated model calls. That is what keeps the cost flat as the ensemble grows.

## 4. Models

### 4.1 Roster (live OpenRouter data, 27 Sep)

| Role | Model (slug) | Price per M tokens, in / out | Context | Weights | Notes |
| --- | --- | --- | --- | --- | --- |
| Decisions | Jev 1.13 (`typesafe/jev-1.13`) | $0.042 / free | 32K | closed | One host (TypeSafe). `~typesafe/jev-latest` is only an alias for it; no newer Jev yet |
| Decisions | Kev-4B (`jaredpalmer/kev-4b`) | $0.042 / free | 8K | open, Apache-2.0 | Hosted by SiliconFlow in fp8 on a patched fork, so not identical to the open weights |
| Decisions (free) | Span-01-lite (`respan/span-01-lite:free`) | free | — | closed | Scores whether a behaviour is present; useful for dev tests |
| Text | DeepSeek V4.1 Flash | $0.035 / $0.29 (cached input $0.001) | 1M | open | Automatic prompt caching; our code pins DeepInfra fp8 |
| Text | GLM-5.3 Flash | $0.045 / $0.14 (cached $0.01) | 1.3M | open | Cheapest route is an InferenceNet promo that rate-limits upstream; reasoning can't be switched off ("minimal" used 0 tokens) |
| Text | MiMo-V2.6-Flash | $0.14 / $0.28 | 1M | open | No batch variant; caching unconfirmed |
| Text (US) | GPT-6 Luna | $0.05 / $0.25 on OpenAI's "flex" endpoint ($0.10 / $0.50 standard) | 1.05M | closed | The only US model allowed |
| Embeddings | Qwen3-Embedding-8B | $0.01 | 32K | open | Nebius or DeepInfra |
| Rerank | Qwen3-Reranker-8B | listed as $0 *(real price per search unverified)* | 41K | open | Optional, for race tagging |
| Dev only | Qwen3.8-27B (`:free`) | free | 262K | open | 20 requests/min; 1,000/day once $10 of credit has ever been bought |
| Weekly auditor | MiMo-V2.6-Pro ($0.435 / $0.87) or DeepSeek Pro | | | | a few calls a week |

### 4.2 What the tests say

Full results, including measured cost per decision, are in `docs/scorecard.md` (first full run, 27 Sep, $1.03 spent of
the $9 cap). What matters for routing:

| Test | Best | Everyone else |
| --- | --- | --- |
| Null: irrelevant news → "no change" (pass ≥ 0.90) | Jev 0.99 | DeepSeek, Luna, MiMo ~0.95; GLM 0.90 (borderline); base Kev fails (0.73–0.77) |
| Mirror: reaction flips when parties swap | Jev (flip correlation 0.69) | Kev and GLM 0.46, Luna 0.41, DeepSeek 0.32, MiMo 0.07 |
| Events: 19 real shifts, 2012–2026 | GLM (rank 0.81, right direction on all 13 non-null) | Luna 0.74, MiMo 0.70, DeepSeek 0.63, Jev 0.61, Kev 0.31 |
| Fidelity: 2024 vote and turnout shares | plain regression | LLMs 0.07–0.17 error, Jev and Kev 0.18–0.33 |

So: statistics set the levels (as designed); reactions come from a GLM + Jev blend, calibrated and damped per state,
with Luna as a spot check (it is neutral but costs about three times as much); base Kev is not usable, so Kev enters
only as our fine-tune. Most events predate the models' training, so the events scores may be partly memory.

### 4.3 Which model does which job

| Job | First choice | Fallback | Notes |
| --- | --- | --- | --- |
| Deduplicate and cluster news | Qwen3-Embedding-8B | — | |
| Which races a story touches | embedding shortlist, then Jev yes/no | reranker | |
| Event labels: type, side helped, salience, local vs national | Jev choice + score in one request | DeepSeek | gold labels from GLM + MiMo + Luna agreement, spot-checked by Matteo |
| Event cards (1–3 neutral sentences per event) | DeepSeek V4.1 Flash | GLM-5.3 Flash | kept short so Kev can read them |
| Archetype reactions (support shift, turnout shift) | GLM-5.3 Flash + Jev blend, 2 option orders, calibrated per state | Luna spot check; fine-tuned Kev on Modal | GLM pinned to two fp4 hosts (InferenceNet rate-limits) |
| Weekly auditor (explains filter surprises; never updates numbers) | MiMo-V2.6-Pro | DeepSeek Pro | |
| Plain LLM-forecaster baseline (background) | Luna (flex) | DeepSeek | |
| OASIS diffusion arm (weekly, if it earns its place) | DeepSeek V4.1 Flash (tool calling) | GLM-5.3 Flash | Python 3.11 env; ~3,400 input tokens per agent per step |
| Captions and alt text (outside the engine) | Claude, reviewed by Matteo, while posting is manual | Luna once automated | |

### 4.4 Call volumes and cost

Assumptions: 40 archetypes per state; 5 salient events a day in competitive states, 2 in safe ones; 2 option orders;
support and turnout asked in one request; about 500 input tokens per request (Kev needs short inputs anyway).

| Job | Pilot (OH, NC, TX) | Full scale | Model | Full $/month |
| --- | --- | --- | --- | --- |
| Voter reactions | ~1,200 decisions/day | ~10,000/day (≈12 competitive + 23 safe Senate states, 40 House districts) | GLM + Jev | ~$10–20 (measured: GLM $8.7, Jev $11.9 per 300k decisions with order averaging) |
| News dedup and clustering | ~1,000 articles/day | ~3,000/day | Qwen embeddings | < $0.20 |
| Race tags and event labels | ~300 clusters/day | ~800/day | Jev | ~$3 |
| Event cards | ~20/day | ~300/day | DeepSeek | ~$1 |
| Auditor, LLM-forecaster baseline | weekly | weekly | MiMo-Pro, Luna | < $1 |
| OASIS arm (optional) | 3 states × 200 agents × 10 steps, weekly | same | DeepSeek | ~$4 |
| Development and re-tests | | | mixed | $2–5 |
| **OpenRouter total** | **~$3–5** | | | **~$20–30; adding Luna as a full third member would add ~$15–29** |

If money gets tight: full archetype sets only for competitive races; serve our Kev on Modal's free credit instead of
Jev; send weekly bulk jobs (re-tests, backtests, gold labels) through OpenRouter's batch API at about half price.

### 4.5 Kev: fine-tune and serve

- **First result (`ces-v1`, 27 Sep, $3.08):** on held-out OH/NC/TX cells the fine-tuned Kev's raw probabilities match
  or beat the regression baseline (vote TVD 0.049 / 0.078 / 0.078 vs 0.047 / 0.093 / 0.138; turnout 0.062 / 0.067 /
  0.042 vs 0.071 / 0.059 / 0.036), against 0.16–0.26 for base Kev. Serve soft-target runs at temperature 1.0: Kev's
  own calibration sharpens shares (details in `docs/CHANGELOG.md`).
- **Serving rules:** one GPU at most, 60 s idle before scaling to zero, one batch of Kev questions a day
  (`KEV_SERVE_MAX_CONTAINERS`, `KEV_SERVE_IDLE_S`, `KEV_SERVE_TEMPERATURE` in the kit). Modal budget: October keeps
  at least $18 for serving; fine-tuning uses September's expiring credit first, then at most $12 in October.
- **Recipe exists:** `skills/kev-finetune/scripts/kev_modal.py` (`validate | train | evaluate | compare | pull |
  publish | teardown`). Start from `--init_from jaredpalmer/kev-4b` (a delta fine-tune; training from scratch did
  much worse). Sizes available: 0.8B, 4B, 9B, 27B.
- **Soft targets work:** each question may carry `target: {option: weight}`, and training uses cross-entropy against
  it. That is how CES population shares become the model's probabilities.
- **Input limits shape our data:** packed request ≤ 2,048 tokens, each question ≤ 1,024, and the "state" under about
  1,400 characters (~384 tokens). So personas stay short and structured, and news goes in as a 1–3 sentence event
  card, not a digest. Today's `reaction_state` (persona + one short story) already fits.
- **Cost:** on an H100, 12–15 minutes and about $1 per 400–1,000 records; a few thousand CES records per task costs
  $2–6. Built-in metrics: accuracy, Brier, log loss, calibration error (ECE), confident-error rate, and a paired
  bootstrap comparison between runs.
- **Serving:** the repo ships a FastAPI server with the same `POST /v1/systemone` shape that `askers.make("kev@<url>")`
  already expects. It is not vLLM (the pointer head needs Kev's own backend). Measured throughput on short prompts:
  L40S ~51 requests/s, H100 ~101; expect roughly half on our ~500-token prompts. Cold start ~35 s. L4 is too slow.
- **Daily serving cost at full scale:** ~10,000 questions ≈ 5–10 minutes on one L40S ($1.95/h) ≈ $0.20–0.35/day ≈
  $6–10/month, inside Modal's credit. Send the day's questions as one burst with many requests in parallel, then let
  it scale to zero. Load-test once with real prompts before relying on these numbers.
- **Gotchas:** exact-pinned kernels (`flash-linear-attention==0.5.2`, `triton>=3.7.1`), so build the Modal image once
  and reuse it for training and serving; `pip install kev` installs an unrelated package (install from git); don't
  judge our fine-tune against OpenRouter's fp8 Kev.
- **No-GPU fallbacks:** Kev runs on a laptop CPU but takes seconds per request, and there is no llama.cpp/Ollama path.
  Kaggle (~30 free GPU hours a week) can train, not serve.

### 4.6 OpenRouter facts that shape the code

- **The Decisions API is alpha** (`POST /api/alpha/decisions`): no stability promise; one state per request, many
  questions allowed (no stated limit); billed on input tokens only; no batch discount. So: ask support and turnout in
  one request, cache everything, and keep Kev (self-hosted) and a text-LLM path as fallbacks behind the same `ask()`.
- **Batch API** (`POST /api/v1/batches`, 24-hour window; median 7 minutes, 90% within about an hour, 99% within about
  10 hours): roughly half price per provider; available for DeepSeek, GLM and Luna, not MiMo, Jev or Kev. Good for
  weekly bulk jobs, too slow to trust on the daily critical path. Note the batch price is a discount on the batch
  provider's own rate, so it can exceed the cheapest non-batch route (GLM, DeepSeek).
- **Prompt caching** is automatic on DeepSeek and GLM; Luna needs prefixes of at least 1,024 tokens; MiMo unconfirmed.
  Put the shared event card first and the persona last so many agents reuse one cached prefix.
- **Free models:** 20 requests/minute; 50/day, or 1,000/day once at least $10 of credit has been bought. Development
  only.
- **Account controls:** per-key spend caps (daily, weekly or monthly), guardrails with model and provider deny lists,
  a zero-data-retention toggle, activity export, and per-call cost lookup (`/api/v1/generation?id=`) to reconcile
  our ledger.

### 4.7 Reproducibility and the blind track

- The response cache (`runs/cache.sqlite`) is the record of every model answer. Today it lives only on the laptop:
  export new answers daily to the private data repo.
- The post-election blind run needs the same models to exist, unchanged. Closed models (Jev, Luna) can be updated or
  retired; OpenRouter is retiring several DeepSeek and Qwen versions on 28 Sep and 9 Oct, for example. The
  open-weights models (DeepSeek V4.1 Flash, GLM-5.3 Flash, MiMo-V2.6-Flash, Kev) can be pulled from Hugging Face and
  run on Modal if a hosted version disappears. So: pin exact slugs and providers, never use aliases, and record each
  model's training cutoff from its model card (OpenRouter doesn't list them) in the assumption register.

## 5. Engine: what to build

| Module | Job | Inputs → outputs | Libraries | Status |
| --- | --- | --- | --- | --- |
| `snap` | Fetch every live source on schedule; store raw, immutable, hashed | APIs and files → `snapshots/<date>/<source>` + manifest | requests, feedparser | build first |
| `context` | News → clusters → race tags → labels → event cards; state profiles and issue maps | snapshots → events table | Qwen embeddings, Jev, DeepSeek, DuckDB | to build |
| `baseline` | Starting levels: lean on new maps, national environment, candidate effects, poll average with house effects | results, maps, VoteHub, FEC → per-race mean, SD and factor loadings | pandas, statsmodels or PyMC | to build (it is also the "stats-only" ablation) |
| `electorate` | CES archetypes per state and district, weights raked to ACS, voter files and 2024 results | CES 2024 (+ cumulative) → archetype table | pandas, balance | cells and 28 test personas exist (`ces.py`) |
| `agents` | Reaction questions per race, archetype and event → calibrated, damped shifts; logs proposed vs applied | event cards + archetypes → deltas | `simlab.askers` | ask, cache and ledger exist |
| `filter` | Daily Kalman from polls; weekly EnKF (~100-number factor state, inflation, poll-bias terms) + particle filter over 5–8 agent parameters per state; innovation monitor | deltas + polls → updated state | numpy/scipy (hand-written), DAPPER to cross-check, particles | to build |
| `mc` | 40,000 correlated Student-t draws (national, regional, state, race; correlation floor 0.25) → probabilities and seat distributions | state → forecast | numpy | to build |
| `evaluate` | Weekly scoring vs snapshotted baselines; divergence-call register | forecasts + baselines → scores | scoringrules | test metrics exist |
| `publish` | forecast.json, charts (web, JPEG, MP4), caption drafts, site files, post kit, posting clients behind an approval gate | forecast → files and posts | Altair + vl-convert, Pillow, imageio-ffmpeg, requests | to build |
| `ops` | One entry point per job; run manifest (git SHA, config hash, model slugs, input hashes); heartbeat pings; spend check | — | GitHub Actions workflows | ledger and cache exist |

**Python environments.** Main: Python 3.13 via uv (versions checked on PyPI today: numpy 2.5, scipy 1.18, pandas 3.0,
DuckDB 1.5, Polars 1.44, scoringrules 0.11, DAPPER 1.8, scikit-learn 1.9, statsmodels 0.15, PyMC 6.3, balance 0.23,
Altair 6.3, vl-convert 1.9, modal 1.5.5). A separate Python 3.11 env for OASIS (`camel-oasis` 0.2.5 needs < 3.12) and
AutoEmulate (< 3.13) if we use them. Kev's environment is defined by its Modal image. Avoid `filterpy` (unmaintained
since 2018), `properscoring` (archived) and tweepy for media upload (no v2 support).

**Charts: one definition for the web and the posts.** Build each chart once in Altair (Vega-Lite). The site renders the
spec with vega-embed; vl-convert renders the same spec to PNG with no browser (Plotly's Kaleido v1 needs Chrome
installed); Pillow converts to JPEG for Instagram. Reels: matplotlib animation → MP4 (H.264, 1080×1920) through
imageio-ffmpeg. Canva (connected to Claude) is optional for a branded cover slide; charts stay code-made so they are
reproducible.

## 6. Infrastructure

### 6.1 Where things run

| Job | Where | When | Why |
| --- | --- | --- | --- |
| Snapshot | GitHub Actions (public repo) | every 3 hours, at an odd minute | free, unlimited minutes |
| Daily pipeline | GitHub Actions | 09:17 UTC (10:17 UK until 25 Oct, 05:17 ET) | 20–40 minutes on a standard runner |
| Weekly filter and scoring | GitHub Actions | fixed slot, e.g. Monday 13:17 UTC (09:17 ET) | same hour every week |
| Token refresh and health | GitHub Actions | weekly | Instagram tokens die after 60 days |
| Site deploy | GitHub Actions (`cloudflare/wrangler-action`) | after each daily run | ships the day's JSON and images |
| Kev fine-tune and serving | Modal GPU | on demand; one burst a day when used | GitHub has no GPUs; the $30 credit covers it |
| Development, one-off analysis | laptop | — | |

GitHub's scheduled runs are best effort: they can start late or, occasionally, be skipped, and scheduled workflows switch
off after 60 days without commits (the daily archive commit keeps them alive). healthchecks.io alerts on a missed run,
and any job can be re-run by hand from the Actions tab. Public repos show their run logs to everyone, so jobs print
summaries, never raw data or keys (GitHub masks stored secrets). The code lives in the same public repo because GitHub's
terms expect Actions minutes to serve the project in that repo; Modal's scheduler (5 cron slots, about $2/month of
the credit) is the fallback if GitHub's runners ever fall short.

### 6.2 Storage

| What | Where | Size by 3 Nov | Public? |
| --- | --- | --- | --- |
| Engine code and workflows | the public repo | small | yes |
| Forecast history, manifests, timestamp proofs, site source | the public repo | < 100 MB | yes: a public, timestamped record; also Zenodo's GitHub integration |
| Raw snapshots (headlines, polls, markets, early-vote files, FEC) | private data repo; voter files only as aggregates | ~1–2 GB (GitHub: 100 MB per file, keep repos under a few GB) | no (some sources can't be republished; voter records never) |
| Model-response cache and spend ledger | private data repo, exported daily as compressed JSON lines | < 300 MB | no |
| Kev checkpoints | Modal Volume | ~1 GB per run | no |
| Site data and post images | shipped with the site as Cloudflare static files (20,000 files, 25 MiB each) | < 1 GB | yes (Instagram needs a public JPEG URL) |

Cloudflare R2 (file storage with public links, 10 GB free) is only needed if the site's own static files stop being
enough.

### 6.3 Website

A Cloudflare Worker with static assets (Cloudflare's current advice for new static sites; Pages still works) on the
subdomain `research.scaliastudio.dev`, with the forecast under `/midterms`, in the existing zone and linked from
scaliastudio.dev (which already deploys from
`Matteomio16/scaliastudio` through Cloudflare). Plain HTML plus vega-embed reading `forecast.json`: overview (Senate
map, House control), race pages, methods ("simulation-based forecast, not a poll", sources, models and versions, what
the agents change), track record and scoring, changelog, archive. Cloudflare Web Analytics is free and cookieless.
Free-plan limits (100,000 Worker requests a day; static file requests are free) sit far above our traffic.

### 6.4 Secrets

Local `.env` (never printed); GitHub Actions secrets for the scheduled jobs; Modal Secrets for GPU jobs. Keys: OpenRouter
(dev key capped at $10, prod key with a monthly cap), Modal tokens, a Cloudflare API token limited to Workers, a token
with write access to the private data repo, the Instagram long-lived token and user ID, the Buffer API key, a Bluesky
app password, free keys for FEC, Census, FRED and EIA, and healthchecks ping URLs.

### 6.5 Proof of timing (daily routine)

1. Hash the day's output bundle and input manifest (SHA-256); stamp the hash with OpenTimestamps (`ots stamp`; free,
   anchored in Bitcoin); commit the bundle and the `.ots` proof to the public archive repo.
2. Capture the live forecast page with the Internet Archive's Save Page Now API.
3. Weekly signed git tag; a Zenodo deposit (with a DOI) at milestones: launch, method changes, final forecast.
4. Once, before the first public forecast: OSF pre-registration of metrics, baselines, scoring dates and the
   divergence-call rule (an embargo of up to 4 years is allowed).

### 6.6 Monitoring

healthchecks.io (free, 20 checks): one check per cron job; a missed or failed ping alerts through a Telegram bot or
ntfy (both free) and email. The daily job also writes a freshness report (age of every feed) and a spend line; anything
stale or over budget appears at the top of the post kit, so Matteo sees it before posting.

## 7. Data

### 7.1 Daily feeds (live signals, checked today)

| Signal | Source | Access | Licence / terms | Notes |
| --- | --- | --- | --- | --- |
| Polls, race level | VoteHub API: `api.votehub.com/polls?poll_type=us-senator` (also `us-representative`, `generic-ballot`, `approval`) | no key | CC BY 4.0 | 418 Senate polls (OH 18, NC 38, TX 42; latest 17–23 Sep) and 90 House districts; fields include partisan, internal, sponsors and population. Primary poll feed |
| Polls cross-check, expert ratings | Wikipedia via the MediaWiki API (pin `oldid`) | no key; descriptive User-Agent, ~1 request/s | CC BY-SA 4.0 | Use canonical titles ("...special election in Ohio"). Its ratings tables are the clean legal route to Cook, Sabato and Inside Elections |
| Early vote, NC | NCSBE daily absentee and one-stop files (S3 `dl.ncsbe.gov`) | no key | public record | Record level with party, race, age, district; publish aggregates only |
| Early vote, TX | Secretary of State daily turnout (JavaScript dashboard at `goelect.txelections.civixapps.com`) | no key | public | No raw data endpoint found yet: find its JSON feed or download by hand |
| Early vote, OH | Secretary of State absentee data page | blocks automated requests (403) | public | Download by hand, or use county boards |
| News discovery | GDELT DOC 2.0 API | no key; 1 request per 5 s | open | Metadata and links |
| Local news | RSS: Signal Ohio, Signal Cleveland, The Assembly (NC), Texas Tribune; Google News RSS queries | no key | store headline + snippet + link | AP and Reuters RSS, Ohio Capital Journal, NC Newsline and Carolina Journal block bots; Media Cloud unverified. Full text only for internal features, and only from outlets with free-republish licences (States Newsroom, Texas Tribune) |
| Money | FEC API | free key (1,000 requests/hour; DEMO_KEY 40/hour) | public domain | NC Senate `S6NC00365`, TX `S6TX00578`; the Ohio special needs filtering |
| Economy | BLS (no key); FRED and EIA (free keys) | | public | EIA has weekly regional gas prices |
| Approval | VoteHub approval polls; UC Santa Barbara American Presidency Project (Gallup) | no key | attribution | |
| Salience | Wikipedia Pageviews API; Bluesky Jetstream | no key | open | Reddit (paid since May 2026) and Google Trends (no public API) are out |
| Markets (benchmark only) | Kalshi (host moved to `api.elections.kalshi.com`), Polymarket Gamma and CLOB, PredictIt (still alive) | no key | check terms before republishing | Snapshot daily at a fixed hour for scoring |

### 7.2 Structural and training data

| Need | Source | Access | Licence |
| --- | --- | --- | --- |
| Voter archetypes | CES 2024 (downloaded) + CES cumulative 2006–2024 (doi:10.7910/DVN/II2DB6) | no key | CC0 |
| Extra survey checks | ANES 2024; AP VoteCast 2018–24 *(access terms unverified)* | registration | research use |
| Past results | MIT Election Lab (Dataverse) | no key | CC0 |
| New 2026 maps | Redistricting Data Hub block files; TX, NC, OH, CA, MO and UT redrew (Missouri faces a referendum drive) | free account | open with attribution |
| 2024 presidential vote by new district | The Downballot sheets | no key | cite; don't republish whole sheets |
| Demographics on new lines | Census ACS 5-year (the API now needs a free key) + 2020 PL 94-171 blocks + TIGER shapes | key | public domain |
| Candidates | unitedstates/congress-legislators (YAML), Voteview, FEC; DIME *(reuse terms unclear)* | no key | CC0 / cite |
| Race list and nominees | Wikipedia "2026 United States Senate elections" via the API | no key | CC BY-SA. An LLM-assembled list had wrong rows, so always pull from the source |
| Voter files (aggregates only) | NC weekly (party, vote history, race, age); OH daily by county (no party registration); TX is paid, so skipped | no key | public record |
| Persona texture (optional) | Nemotron-Personas-USA (1M rows, CC BY 4.0); ACS PUMS | no key | no party field; join from CES |
| Backtests | 538 checking-our-work-data (CC BY 4.0); 538 historical polls via the Wayback Machine; 2025 VA and NJ governors; 2025–26 specials; Polymarket and Kalshi price history | no key | |

**Free keys and accounts to register now:** FEC, Census, FRED, EIA (instant); Redistricting Data Hub (free account).
Optional: BEA, Congress.gov, YouTube Data API (10,000 units a day), Media Cloud, ANES and AP VoteCast.

**Download now, before it moves or disappears:** 538 historical polls
(`web.archive.org/web/20241011032652/https://projects.fivethirtyeight.com/polls/data/senate_polls_historical.csv`),
the `fivethirtyeight/data` and `checking-our-work-data` repos; this week's NC and OH voter files (each release
overwrites the last); the current Missouri and Utah map files; `whyalwaysrose/midterms-forecast` (its licence is
custom, so read it before any reuse). And from today, the daily snapshots themselves: the blind track depends on them.

## 8. Publishing on Instagram and X (free, organic)

### 8.1 The daily post kit

The pipeline writes one folder a day: 1–10 JPEG slides (1080×1350), a 9:16 MP4 when useful, the Instagram caption,
alt text for every image, the X post (and thread), and a short "what changed and why" note with the numbers. Every
image carries "AI-simulated voters, not a poll" and the date. Charts show margin ranges and "wins X in 10
simulations", with ours beside the poll average, markets and Cook. Anything between 35% and 65% is called a toss-up,
and posts say "no meaningful change" when that is true.

### 8.2 Instagram

- **Now, by hand:** create an Instagram professional (Creator) account and start posting build-in-public content early,
  so the account isn't brand new at launch. Schedule in Meta Business Suite (free; up to 75 days ahead; carousels and
  Reels).
- **Later, automated:** the Instagram API with Instagram Login. No Facebook Page, no app review and no business
  verification when the app only publishes to our own account (add it as an Instagram tester under Standard Access).
  Flow: create containers from public JPEG URLs → wait until ready → publish. Limits: 100 API posts per 24 hours; 10
  items per carousel through the API; **JPEG only** (convert the PNGs); alt text on images (not Reels); captions up to
  2,200 characters and 30 hashtags; no scheduling through the API (our cron does the timing). Tokens last 60 days, so
  refresh weekly. Use plain `requests`, never unofficial libraries such as instagrapi (ban risk).
- **Rules:** organic posts by a non-US person are fine; only ads and boosts need US authorisation, and we never boost.
  Meta's "AI info" labels target photorealistic synthetic people and events, not code-made charts (our reading; Meta
  has no explicit ruling on charts). Since January 2025, political content is recommended to non-followers by default
  *(secondary sources)*.

### 8.3 X

- **The free API tier is gone** (since 6 Feb 2026). Posting through the API is pay-per-use: about $0.015 per post, $0.20
  if the post contains a link. The old v1.1 media upload shut down in June 2025, and tweepy has no v2 media upload.
- **Now, by hand:** x.com's composer schedules single posts for free (desktop web); threads go out by hand. X Premium
  isn't needed, and X Pro (the old TweetDeck) now requires Premium+ at $40/month.
- **Later, automated (decided: free only):** Buffer's free plan: 3 channels (X, Threads and Bluesky; Instagram goes
  through its own free API), 10 queued posts per channel, and 1 API key with 3,000 requests a month (official pricing
  page, last updated Nov 2025; paid plans are $5 or $10 per channel per month and aren't needed). Buffer absorbs X's API
  cost. Its GraphQL API (`api.buffer.com`, bearer key) has a `createPost` mutation with an `assets` field for images and
  video, `addToQueue` or `customScheduled` (with `dueAt`) timing, and threads for X, Bluesky and Threads through
  `metadata` *(whether media goes in as a URL or an upload: check on first use)*. The direct X API is not used (paid).
- **Rules:** scheduling your own content is explicitly allowed. Once posting is unattended, turn on the "Automated" label
  and name the human operator in the bio. The civic-integrity policy targets false voting information and the
  synthetic-media policy targets fake depictions of real people, so labelled forecast charts are fine. No AI images of
  candidates.

### 8.4 Free extras

Threads (same Meta app; 250 posts per 24 hours) and Bluesky (app password, no review, images uploaded directly, up to 4
per post; a domain handle such as `@research.scaliastudio.dev` needs one DNS record). Both reuse the post kit at no cost.
Threads is Meta's X-style app attached to the Instagram account (extra reach for no extra work). Bluesky is an
independent X-style network with an open, free API; its audience leans towards journalists, academics and election-data
people. Both optional.

### 8.5 Daily rhythm (UK time)

10:17 the pipeline runs → ~11:00 the post kit is ready and an alert goes out → Matteo reviews with Claude (numbers,
wording, rules checklist) → approves → posts go out 12:00–14:00 (07:00–09:00 ET). Once posting is automated, approving
flips a flag and the posting job publishes to every channel; nothing publishes without it. UK clocks change on 25 Oct
and US clocks on 1 Nov, so the ET times shift by an hour in the last week.

## 9. Claude Max 5x: where it fits

| Use | Surface | Notes |
| --- | --- | --- |
| Building the engine | Claude Code | Sonnet for routine work, Opus for design and debugging; subagents for research |
| Research and living docs | Cowork / claude.ai, Claude Docs | where the plan and field guide live |
| Daily review and drafting | Claude Code or Cowork | reads the post kit, checks numbers and rules, drafts captions, alt text and threads; Matteo approves |
| Faster posting by hand | Claude in Chrome | works in Matteo's logged-in browser; he approves each action; it stops at CAPTCHAs; 10 MB upload cap |
| Scheduled checks (optional) | Cloud routines (research preview) or GitHub Actions `claude-code-action` with a `claude setup-token` token | can clone the private repo, run scripts, commit to `claude/` branches and email via the Gmail connector; secrets stay in a host-scoped proxy |
| Private ops dashboard (optional) | an Artifact that a routine republishes | |

**Boundaries.** The subscription covers running Claude Code itself: interactive sessions, `claude -p`, routines and the
GitHub action. Building our own agent with the Agent SDK requires an API key, so we don't. Claude never produces
forecast numbers or sits in the engine (model policy). Usage runs on a 5-hour window plus a weekly cap; Anthropic
publishes no exact numbers (see claude.ai/settings/usage).

## 10. Monthly budget

| Item | Pilot | Full scale |
| --- | --- | --- |
| OpenRouter (engine models) | $3–5 | $20–30 |
| Modal (Kev fine-tunes and serving; daily jobs too if the code stays private) | $0, inside the $30 credit | $0, inside the credit |
| Publishing (Instagram, X via Buffer free, Threads, Bluesky) | $0 | $0 |
| Cloudflare, GitHub, healthchecks, OSF, Zenodo, OpenTimestamps | $0 | $0 |
| **Total new spend** | **~$5** | **~$20–30** |
| Claude Max 5x | existing | existing |

## 11. Risks and fallbacks

| Risk | Effect | Fallback |
| --- | --- | --- |
| Jev: alpha API, 12 days old, one host | reaction layer stalls or drifts | cache; self-hosted Kev behind the same interface; text-LLM path |
| Upstream rate limits (GLM through InferenceNet) | slow runs | pin two hosts where the quantisation matches; run early; retries resume from the cache |
| A model is updated or retired before the blind run | blind track can't be re-run | cache everything; open weights on Modal; pinned slugs |
| GitHub delays or skips a scheduled run | a late or missed day | healthchecks alert; re-run by hand from the Actions tab |
| Instagram token expires (60 days) | posting stops | weekly refresh job + alert |
| Buffer's free plan changes or its X link breaks | X automation stops | the free x.com scheduler by hand |
| A scraper breaks (Wikipedia layout, bot walls) | stale inputs | VoteHub as primary poll feed; daily freshness report; manual routes for OH and TX early vote |
| Laptop asleep | nothing runs | the pipeline lives on GitHub Actions; the laptop is for development |
| Spend runaway | budget blown | per-key caps, the ledger's hard cap, a daily spend line |
| Output mistaken for a poll, or an error goes out | reputation | labels in every image, caption rules, human approval gate, public corrections |
| Kev kernels break after an image rebuild | the fine-tune can't serve | build the image once, pin versions, keep the Jev path live |
| The 37-day clock | half-built system at launch | snapshots first, manual posting first, automate only what repeats |

## 12. Build order (infrastructure view)

1. **27–29 Sep:** create the GitHub repos (the public repo for workflows, archive and site, plus the private data repo);
   snapshotter live on GitHub Actions (VoteHub, Wikipedia pages and ratings, markets, GDELT and RSS headlines, FEC, BLS
   and EIA, pageviews, NCSBE); the download-now list; register the free keys; export the cache.
2. **By 30 Sep:** routing from the scorecard (done: GLM + Jev); first Kev fine-tune (`ces-v1`, data ready) on Modal
   as soon as Modal is set up. Social accounts any time before 12 Oct.
3. **By 4 Oct:** baseline, archetypes and context layer for OH, NC and TX.
4. **By 10 Oct:** agent layer, daily Kalman update, Monte Carlo; site skeleton on Cloudflare; chart factory and post
   kit; methods page; OSF pre-registration; public archive repo with OpenTimestamps.
5. **12 Oct:** first public pilot forecast, posted by hand.
6. **13–20 Oct:** code freeze and public changelog; scale to 35 Senate + 40 House; NC early-vote ingestion (from 15 Oct)
   and Texas (from 19 Oct); weekly EnKF and scoring; automate Instagram (API) and X (Buffer) behind the approval gate.
7. **20 Oct–3 Nov:** daily operations, weekly scoring, divergence calls.
8. **After 3 Nov:** results, scoring, and the blind track on the frozen snapshots.

## 13. Decisions

Decided by Matteo on 27 Sep (also in CLAUDE.md section 5):
- Site at `research.scaliastudio.dev/midterms`.
- Publishing is free only: Instagram by hand then its official API; X by hand then Buffer's free plan; Threads and
  Bluesky optional; accounts created later.
- No R2 for now. One public repo holds the engine code, workflows and published forecasts (unlimited free minutes,
  within GitHub's terms); raw data, the model-answer cache and keys stay private. Modal is for GPU work.
- Kev fine-tune approved and launched (`ces-v1`, 27 Sep).
- Daily Claude check at 11:30 UK (desktop scheduled task `midterm-daily-check`).
- Turnout targets shifted per state to each state's official 2024 turnout (fixes CES voter-file matching differences).

Nothing is open right now; the next decisions come with the Kev results and the first pilot forecast.

## Sources

- OpenRouter: live model list and endpoints (`openrouter.ai/api/v1/models`, `/api/v1/models/{id}/endpoints`);
  [Decisions API / Jev guide](https://openrouter.ai/docs/guides/community/jev);
  [batch quickstart](https://openrouter.ai/docs/batch-quickstart);
  [prompt caching](https://openrouter.ai/docs/guides/best-practices/prompt-caching);
  [limits](https://openrouter.ai/docs/api_reference/limits); [guardrails](https://openrouter.ai/docs/guides/features/guardrails)
- Kev: [github.com/jaredpalmer/kev](https://github.com/jaredpalmer/kev) (README, model card, `skills/kev-finetune`,
  `kev/serve.py`, read from a local clone)
- Modal: [pricing](https://modal.com/pricing); [cron](https://modal.com/docs/guide/cron);
  [timeouts](https://modal.com/docs/guide/timeouts)
- Cloudflare: [Workers static assets](https://developers.cloudflare.com/workers/static-assets/);
  [Workers limits](https://developers.cloudflare.com/workers/platform/limits/);
  [R2 pricing](https://developers.cloudflare.com/r2/pricing/)
- GitHub terms: [Actions section of the additional product terms](https://docs.github.com/en/site-policy/github-terms/github-terms-for-additional-products-and-features)
- GitHub Actions: [billing](https://docs.github.com/en/billing/concepts/product-billing/github-actions);
  [limits](https://docs.github.com/en/actions/reference/limits)
- Instagram and Meta: [Instagram Platform](https://developers.facebook.com/docs/instagram-platform);
  [How Meta is preparing for the 2026 US midterms](https://about.fb.com/news/2026/02/meta-prepares-for-2026-us-midterms/);
  [Threads API](https://developers.facebook.com/docs/threads)
- X: [pricing](https://docs.x.com/x-api/getting-started/pricing);
  [chunked media upload](https://docs.x.com/x-api/media/quickstart/media-upload-chunked);
  [automation rules](https://help.x.com/en/rules-and-policies/x-automation);
  [civic integrity](https://help.x.com/en/rules-and-policies/election-integrity-policy);
  [authenticity](https://help.x.com/en/rules-and-policies/authenticity)
- Buffer: [pricing](https://buffer.com/pricing); [developer docs](https://developers.buffer.com/)
- Bluesky: [get started](https://docs.bsky.app/docs/get-started)
- Claude: [feature availability](https://code.claude.com/docs/en/feature-availability);
  [routines](https://code.claude.com/docs/en/routines); [headless](https://code.claude.com/docs/en/headless);
  [GitHub Actions](https://code.claude.com/docs/en/github-actions);
  [legal and compliance](https://code.claude.com/docs/en/legal-and-compliance);
  [Chrome](https://code.claude.com/docs/en/chrome)
- Data: [VoteHub API](https://votehub.com/polls/api/) (tested live);
  [NCSBE absentee data](https://www.ncsbe.gov/results-data/absentee-and-provisional-data);
  [FEC API](https://api.open.fec.gov/developers/); [GDELT](https://www.gdeltproject.org/);
  [MIT Election Lab](https://electionlab.mit.edu/data); [Redistricting Data Hub](https://redistrictingdatahub.org/);
  [The Downballot data](https://www.the-downballot.com/p/data);
  [538 checking-our-work](https://github.com/fivethirtyeight/checking-our-work-data);
  [Nemotron-Personas-USA](https://huggingface.co/datasets/nvidia/Nemotron-Personas-USA)
