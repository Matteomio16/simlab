> Written in Claude Code on 27 Sep 2026 from eight parallel research sweeps (official docs and live API calls made
> today), the test bench, and `plan.md` / `field-guide.md`. Prices and limits are as of today; anything marked
> *(unverified)* needs a check before we depend on it. If this file and CLAUDE.md disagree, CLAUDE.md wins. Nothing
> here is decided until Matteo says so (see section 13).

# Midterm Engine: Infrastructure Blueprint

## 1. The stack on one page

| Layer | Recommended pick | Runs on | Est. $/month |
| --- | --- | --- | --- |
| Model gateway | OpenRouter: a dev key and a prod key, each with a spend cap; a guardrail that denies `anthropic/*` and `google/*` | — | see models |
| Decision questions (news labels, voter reactions) | Jev 1.13 (hosted, pinned slug) now; our fine-tuned Kev-4B if it wins the scorecard | OpenRouter; Modal GPU | $1–8 |
| Text jobs (event cards, auditor, baselines) | DeepSeek V4.1 Flash; GPT-6 Luna as the one US model; MiMo-V2.6-Flash and GLM-5.3 Flash for diversity and fallback | OpenRouter | $1–5 |
| Embeddings | Qwen3-Embedding-8B | OpenRouter | < $0.50 |
| Engine code | Python 3.13 package (uv); OASIS arm in its own Python 3.11 env | Modal CPU (cron) | ~$2, inside free credit |
| Kev fine-tune and serving | Kev repo's `kev_modal.py` (train on H100, serve on L40S, scale to zero) | Modal GPU | $5–25, inside free credit |
| Raw snapshots, cache backups | Modal Volume | Modal | $0 |
| Public data and post images | Cloudflare R2 bucket on `data.scaliastudio.dev` (or the site's own static files) | Cloudflare | $0 |
| Website | Cloudflare Worker with static assets at `midterms.scaliastudio.dev`, linked from Scalia | Cloudflare | $0 |
| Scheduling | Modal Cron (5 slots) for the pipeline; GitHub Actions for site deploys and as a backup | Modal, GitHub | $0 |
| Instagram | Meta Business Suite by hand, then the Instagram API with Instagram Login (own account, no app review) | — | $0 |
| X | x.com's free scheduler by hand, then Buffer's free API or X's pay-per-use API | — | $0–5 |
| Extra channels | Threads API, Bluesky | — | $0 |
| Proof of timing | OpenTimestamps daily, signed git tag weekly, OSF pre-registration, Zenodo at milestones, Internet Archive capture | — | $0 |
| Monitoring | healthchecks.io (20 free checks) → Telegram / ntfy / email | — | $0 |
| Claude Max 5x | building (Claude Code), research and docs (Cowork), daily review and post drafting, optional routines; never inside the forecast | — | existing subscription |

**New spend:** about $5/month for the 3-state pilot and $15–35/month at full scale (35 Senate + 40 House seats),
including $0–5 for X. Modal work fits inside its $30/month free credit.

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
EVERY 3 HOURS   snapshot → raw, immutable, hashed files on the Modal Volume + manifest
                polls · markets · news headlines · early-vote files · FEC · ratings · economy · pageviews

DAILY 09:17 UTC (Modal Cron)
  context       dedup + cluster (embeddings) → race tags → event labels (Jev) → short event cards (DeepSeek)
  baseline      partisan lean on new maps + national environment + candidates + poll average → starting levels
  electorate    CES archetypes per state, weighted to census, voter files and 2024 results
  agents        race × archetype × salient event → decision model → support shift + turnout shift
                → calibration curve → damping / decay / weights (system parameters, learned per state)
  filter        cheap Kalman update from new polls (no model calls)
  monte carlo   40,000 correlated draws → win probabilities, seat counts
  outputs       forecast.json · charts (web + JPEG + MP4) · draft captions · run manifest + hashes
      │                         │                                        │
  R2 + website        post kit → Matteo reviews with Claude       archive (hashes, timestamps, IA capture)
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

### 4.2 What the tests say so far

The full test bench (4 tests × 11 model variants) started at 17:29 today and was still running at 18:30 ($0.75 spent of
the $9 cap). Results for the parts that had finished, computed from the per-item files in `runs/`; the complete
scorecard lands in `runs/scorecard.jsonl` when the run ends.

**Null test** (28 personas × 20 irrelevant stories × 2 questions = 1,120 items per model; average probability on
"no change", pass ≥ 0.90): Jev 0.987 support / 0.999 turnout; MiMo 0.955 / 0.961; Luna 0.954 / 0.942; DeepSeek
0.950 / 0.949. All pass; GLM and Kev still running.

**Mirror test** (448 persona × story pairs; does the reaction flip when the parties are swapped?):

| Model | Flip correlation | Sign flips | Lean (+ = pro-D) | Mean reaction size (−2..+2 scale) |
| --- | --- | --- | --- | --- |
| Jev | 0.69 | 77% | −0.06 | 0.70 |
| Luna | 0.41 | 73% | 0.00 | 0.28 |

**Events test, Jev** (19 real events 2012–2026 with measured shifts): rank correlation 0.61; right direction on 85% of
the non-null events; about 5.4 points of real shift per unit of Jev's scale; error after scaling 3.0 points. It
under-predicts the big shocks (Jan 6: +9 measured vs +2.4; Afghanistan: −6 vs −0.9), misses the COVID emergency, and
gets the 2026 fuel spike's direction wrong.

**Fidelity, Jev** (reproduce real 2024 vote and turnout shares by demographic cell; weighted TVD, lower is better):
vote 0.24–0.33 and turnout 0.17–0.22, against the regression baseline's 0.04–0.14 and 0.03–0.07. Jev's probabilities
are confidence in a label, not population shares.

What this means for the infrastructure: statistics must set the levels (as designed); Jev is usable for reactions only
through a fitted calibration curve and learned damping; and a Kev fine-tuned on CES shares (soft targets) is the path
to a decision model whose probabilities mean shares, which makes the Modal fine-tune worth starting now.

### 4.3 Which model does which job (initial routing; final after the scorecard)

| Job | First choice | Fallback | Notes |
| --- | --- | --- | --- |
| Deduplicate and cluster news | Qwen3-Embedding-8B | — | |
| Which races a story touches | embedding shortlist, then Jev yes/no | reranker | |
| Event labels: type, side helped, salience, local vs national | Jev choice + score in one request | DeepSeek | gold labels from GLM + MiMo + Luna agreement, spot-checked by Matteo |
| Event cards (1–3 neutral sentences per event) | DeepSeek V4.1 Flash | GLM-5.3 Flash | kept short so Kev can read them |
| Archetype reactions (support shift, turnout shift) | Jev, 2 option orders | fine-tuned Kev on Modal; DeepSeek with cached prefix | decided by mirror, events and fidelity |
| Weekly auditor (explains filter surprises; never updates numbers) | MiMo-V2.6-Pro | DeepSeek Pro | |
| Plain LLM-forecaster baseline (background) | Luna (flex) | DeepSeek | |
| OASIS diffusion arm (weekly, if it earns its place) | DeepSeek V4.1 Flash (tool calling) | GLM-5.3 Flash | Python 3.11 env; ~3,400 input tokens per agent per step |
| Captions and alt text (outside the engine) | Claude, reviewed by Matteo, while posting is manual | Luna once automated | |

### 4.4 Call volumes and cost

Assumptions: 40 archetypes per state; 5 salient events a day in competitive states, 2 in safe ones; 2 option orders;
support and turnout asked in one request; about 500 input tokens per request (Kev needs short inputs anyway).

| Job | Pilot (OH, NC, TX) | Full scale | Model | Full $/month |
| --- | --- | --- | --- | --- |
| Voter reactions | 1,200 requests/day | ~9,800/day (≈12 competitive + 23 safe Senate states, 40 House districts) | Jev | ~$6 |
| News dedup and clustering | ~1,000 articles/day | ~3,000/day | Qwen embeddings | < $0.20 |
| Race tags and event labels | ~300 clusters/day | ~800/day | Jev | ~$3 |
| Event cards | ~20/day | ~300/day | DeepSeek | ~$1 |
| Auditor, LLM-forecaster baseline | weekly | weekly | MiMo-Pro, Luna | < $1 |
| OASIS arm (optional) | 3 states × 200 agents × 10 steps, weekly | same | DeepSeek | ~$4 |
| Development and re-tests | | | mixed | $2–5 |
| **OpenRouter total** | **~$3–5** | | | **~$15–20, up to ~$30 with 3 option orders or more archetypes** |

If money gets tight: full archetype sets only for competitive races; serve our Kev on Modal's free credit instead of
Jev; send weekly bulk jobs (re-tests, backtests, gold labels) through OpenRouter's batch API at about half price.

### 4.5 Kev: fine-tune and serve

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
  back it up daily (Modal Volume plus a private copy).
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
| `ops` | One entry point per job; run manifest (git SHA, config hash, model slugs, input hashes); heartbeat pings; spend check | — | modal | ledger and cache exist |

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
| Snapshot | Modal Cron | every 3 hours, at an odd minute | reliable; writes straight to the Volume |
| Daily pipeline | Modal Cron | 09:17 UTC (11:17 Berlin, 05:17 ET) | a 30-minute, 2-CPU run costs about $0.06 |
| Weekly filter and scoring | Modal Cron | fixed slot, e.g. Monday 13:17 UTC (09:17 ET) | same hour every week |
| Token refresh and health | Modal Cron | weekly | Instagram tokens die after 60 days |
| Kev fine-tune and serving | Modal GPU | on demand; one burst a day | covered by the $30 credit |
| Site deploys | GitHub Actions (`cloudflare/wrangler-action`) | on push | rare |
| Backup trigger | GitHub Actions cron | daily | only acts if Modal missed a run |
| Development, one-off analysis | laptop | — | Windows Task Scheduler only as a last resort (sleep, updates) |

Modal Starter limits to remember: 5 deployed crons, 10 GPUs at once, 24 hours max per function, logs kept 1 day (so the
pipeline writes its own logs to the Volume). GitHub's scheduled runs are best-effort (they can be delayed or dropped,
and are switched off after 60 days without commits), which is why GitHub is the backup, not the primary.

### 6.2 Storage

| What | Where | Size by 3 Nov | Public? |
| --- | --- | --- | --- |
| Code | GitHub private repo `simlab` (no remote yet) | small | no, until the open-source decision |
| Forecast history, manifests, timestamp proofs | GitHub public repo, e.g. `midterms-forecast-archive` | < 100 MB | yes: a public, timestamped record without opening the code; also unlimited Actions minutes and Zenodo's GitHub integration |
| Raw snapshots | Modal Volume (the pricing page lists 1 TiB free, then $0.09/GiB-month) | ~2–5 GB, mostly the weekly NC voter file (~0.85 GB zipped) | no (some sources can't be republished) |
| Model-response cache and spend ledger | Modal Volume + a daily copy off the machine | < 1 GB | no |
| Site data and post images | R2 bucket on `data.scaliastudio.dev` (free: 10 GB, zero egress), or the site's static files | < 1 GB | yes (Instagram needs a public JPEG URL) |

R2 may ask for a payment method on activation even though our usage stays free *(check in the dashboard)*. If that is
unwelcome, ship JSON and images as the Worker's static files instead (redeployed daily; limits are 20,000 files and
25 MiB per file).

### 6.3 Website

A Cloudflare Worker with static assets (Cloudflare's current advice for new static sites; Pages still works) on the
subdomain `midterms.scaliastudio.dev`, in the existing zone and linked from scaliastudio.dev (which already deploys from
`Matteomio16/scaliastudio` through Cloudflare). Plain HTML plus vega-embed reading `forecast.json`: overview (Senate
map, House control), race pages, methods ("simulation-based forecast, not a poll", sources, models and versions, what
the agents change), track record and scoring, changelog, archive. Cloudflare Web Analytics is free and cookieless.
Free-plan limits (100,000 Worker requests a day; static file requests are free) sit far above our traffic.

### 6.4 Secrets

Local `.env` (never printed); Modal Secrets for scheduled jobs; GitHub Actions secrets for deploys. Keys: OpenRouter
(dev key capped at $10, prod key with a monthly cap), Modal tokens, a Cloudflare API token limited to Workers and R2, R2
access keys, the Instagram long-lived token and user ID, X OAuth 1.0a tokens or the Buffer API key, a Bluesky app
password, free keys for FEC, Census, FRED and EIA, and healthchecks ping URLs.

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
- **Later, automated, cheapest first:**
  1. **Buffer's free plan:** 3 channels (X, Instagram, Threads and Bluesky are all supported), 10 queued posts per
     channel, and 1 API key with 3,000 requests a month (official pricing page, last updated Nov 2025). Buffer absorbs
     X's API cost. Its GraphQL API (`api.buffer.com`, bearer key) has a `createPost` mutation with an `assets` field for
     images and video, `addToQueue` or `customScheduled` (with `dueAt`) timing, and threads for X, Bluesky and Threads
     through `metadata` *(whether media goes in as a URL or an upload: check on first use)*.
  2. **Direct X API:** OAuth 1.0a user tokens (they don't expire), `requests` + `requests-oauthlib`, chunked v2 media
     upload, then `POST /2/tweets`. About 90 posts a month ≈ $1.50–5. Keep links out of post bodies (put the site in
     the bio or a reply). Test one image post first: there is an open report of 403 errors after a few media posts.
- **Rules:** scheduling your own content is explicitly allowed. Once posting is unattended, turn on the "Automated" label
  and name the human operator in the bio. The civic-integrity policy targets false voting information and the
  synthetic-media policy targets fake depictions of real people, so labelled forecast charts are fine. No AI images of
  candidates.

### 8.4 Free extras

Threads (same Meta app; 250 posts per 24 hours) and Bluesky (app password, no review, images uploaded directly, up to 4
per post; a domain handle such as `@midterms.scaliastudio.dev` needs one DNS record). Both reuse the post kit at no cost.

### 8.5 Daily rhythm (Berlin time)

11:17 the pipeline runs → ~12:00 the post kit is ready and an alert goes out → Matteo reviews with Claude (numbers,
wording, rules checklist) → approves → posts go out 13:00–15:00 (07:00–09:00 ET). Once posting is automated, approving
flips a flag and the posting job publishes to every channel; nothing publishes without it. Times shift by an hour when
Europe changes clocks (25 Oct) and again when the US does (1 Nov).

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
| OpenRouter (engine models) | $3–5 | $15–30 |
| Modal (pipeline CPU ~$2, Kev fine-tunes and serving) | $0, inside the $30 credit | $0, inside the credit |
| X posting | $0 (by hand or Buffer) | $0–5 (direct API) |
| Cloudflare, GitHub, healthchecks, OSF, Zenodo, OpenTimestamps, Meta, Bluesky | $0 | $0 |
| **Total new spend** | **~$5** | **~$15–35** |
| Claude Max 5x | existing | existing |

## 11. Risks and fallbacks

| Risk | Effect | Fallback |
| --- | --- | --- |
| Jev: alpha API, 12 days old, one host | reaction layer stalls or drifts | cache; self-hosted Kev behind the same interface; text-LLM path |
| Upstream rate limits (GLM through InferenceNet) | slow runs | pin two hosts where the quantisation matches; run early; retries resume from the cache |
| A model is updated or retired before the blind run | blind track can't be re-run | cache everything; open weights on Modal; pinned slugs |
| GitHub drops a scheduled run | a missed day | Modal Cron as primary; healthchecks alert |
| Instagram token expires (60 days) | posting stops | weekly refresh job + alert |
| X API costs or 403 errors | automation fails | Buffer's free plan; the free scheduler by hand |
| A scraper breaks (Wikipedia layout, bot walls) | stale inputs | VoteHub as primary poll feed; daily freshness report; manual routes for OH and TX early vote |
| Laptop asleep | nothing runs | the pipeline lives on Modal; the laptop is for development |
| Spend runaway | budget blown | per-key caps, the ledger's hard cap, a daily spend line |
| Output mistaken for a poll, or an error goes out | reputation | labels in every image, caption rules, human approval gate, public corrections |
| Kev kernels break after an image rebuild | the fine-tune can't serve | build the image once, pin versions, keep the Jev path live |
| The 37-day clock | half-built system at launch | snapshots first, manual posting first, automate only what repeats |

## 12. Build order (infrastructure view)

1. **27–28 Sep:** push `simlab` to a private GitHub repo; snapshotter live on Modal Cron (VoteHub, Wikipedia pages and
   ratings, markets, GDELT and RSS headlines, FEC, BLS and EIA, pageviews, NCSBE); the download-now list; register the
   free keys; create the Instagram, X and Bluesky accounts; back up the cache.
2. **By 30 Sep:** full scorecard from the running bench → routing decision; first Kev fine-tune on CES vote and turnout
   (soft targets) on Modal.
3. **By 4 Oct:** baseline, archetypes and context layer for OH, NC and TX.
4. **By 10 Oct:** agent layer, daily Kalman update, Monte Carlo; site skeleton on Cloudflare; chart factory and post
   kit; methods page; OSF pre-registration; public archive repo with OpenTimestamps.
5. **12 Oct:** first public pilot forecast, posted by hand.
6. **13–20 Oct:** code freeze and public changelog; scale to 35 Senate + 40 House; NC early-vote ingestion (from 15 Oct)
   and Texas (from 19 Oct); weekly EnKF and scoring; automate Instagram (API) and X (Buffer) behind the approval gate.
7. **20 Oct–3 Nov:** daily operations, weekly scoring, divergence calls.
8. **After 3 Nov:** results, scoring, and the blind track on the frozen snapshots.

## 13. Decisions for Matteo

1. **Repos:** a private code repo plus a public archive repo for forecasts and timestamp proofs? (recommended)
2. **Site address:** `midterms.scaliastudio.dev` (recommended) or a path on scaliastudio.dev?
3. **X automation:** Buffer's free plan (recommended), the direct pay-per-use API (~$1.50–5/month), or by hand only?
4. **Handles:** names for the Instagram, X and Bluesky accounts; creating them now gives them time to warm up.
5. **R2:** fine to activate (it may ask for a payment method; usage stays free)? Otherwise images and JSON ship with
   the site.
6. **Scheduler:** Modal Cron as the primary? (recommended)
7. **Kev:** start the first fine-tune now, in parallel with the scorecard? (recommended; about $1–6 of Modal credit)
8. **Claude routines:** a daily scheduled check that drafts the post kit and emails it to you?

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
  [R2 pricing](https://developers.cloudflare.com/r2/pricing/);
  [R2 public buckets](https://developers.cloudflare.com/r2/buckets/public-buckets/)
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
