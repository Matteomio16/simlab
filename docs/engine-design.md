# Engine design: the forecast machine

Agreed with Matteo on 28 Sep 2026. This file is the contract between the sessions: what each piece does, who builds it,
and the files they pass. Related files:
- Methods for the statistics pieces: `docs/stats-groundwork.md` §5.
- Model rules: `docs/model-recipes.md`.
- Dates and checkpoints: `docs/roadmap.md`.

If this file and CLAUDE.md disagree, CLAUDE.md wins.

## 1. Principles

1. **Statistics set levels; simulated reactions move them.** Statistics set each race's starting level. Simulated voter
   reactions move it day by day, new polls correct it, and a Monte Carlo turns it into chances. A stats-only twin, with
   reactions switched off, runs beside it every day.
2. **Reactions, not paper effects** (Matteo, 28 Sep). A story's effect is how each voter group reacts to it, including
   backlash and mobilisation, not who it helps on paper. A $30M super PAC for the Republican can fire up Democrats.
3. **Only people who can move count** (Matteo, 28 Sep). A reaction counts only for the share of a group that can still
   change. Voters sure of their choice don't change the outcome, however strongly they react. Mobilising a group that
   already votes at 95% barely changes turnout.
4. **Models give direction, data gives size.** Models give the direction and relative strength of a reaction, not its
   size. Sizes come from data:
   - how much of each group can still move (surveys)
   - how strongly real events moved opinion (calibration)
   - how responsive each state turns out to be (the filter's dials)
5. **Dated files.** Every step reads and writes dated files, so any day can be re-run from its saved inputs. The blind
   track depends on this.

## 2. The daily loop

| When (UK) | Step | Owner | Reads | Writes |
| --- | --- | --- | --- | --- |
| every 3 h | Snapshots | Engine schedules `simlab/snap.py` (built by the Kev session) | live sources | `snapshots/…` |
| 10:47 | 1. Polls | Statistics | snapshots | `polls.csv` |
| | 2. News | Engine | snapshots | `events.jsonl` |
| | 3. Reactions | Engine | events, personas | `reactions.jsonl` |
| | 4. Levels and voter groups | Statistics | polls, fundamentals, surveys | `levels.json`, `groups.json` |
| | 5. Moves | Statistics | reactions, groups, params | `moves.json` |
| | 6. Filter | Statistics | moves, polls, yesterday's state | `filter_state.json` |
| | 7. Monte Carlo | Statistics | filter state, snapshots (benchmarks) | `forecast.json`, `draws.json` |
| | 8. Post kit | Content & site | forecast, events | `post-kit/…` |
| Mondays | Weekly filter; scoring | Statistics; scoring by the Kev session | the week's files | `params.json`, `scores.json` |

The daily job (Engine) runs steps 1–8 in order on GitHub Actions and writes the run record. The weekly filter runs from
12 Oct and scoring from 19 Oct.

## 3. How the simulation moves the forecast

### 3.1 Voter groups

Each race's electorate is split into the 28 groups: 7-point party ID × white/non-white × degree. The ids are the `id`
strings in `simlab/archetypes.json`. For each race and group, Statistics provides (method in stats-groundwork §5.5):

| Field | Meaning | Source |
| --- | --- | --- |
| `n` | share of adult citizens | CPS × CES, tilted to the 2024 result |
| `t` | midterm turnout | CPS 2018/2022, scaled to official turnout |
| `d` | vote margin D − R within the group, at the starting level | Kev ces-v3b's 2024 presidential vote by group (the CES midterm Senate vote where Kev has no answer), shifted to the race's level (Matteo, 29 Sep) |
| `pi` | **persuadable share**: the part of the group that could still change its vote | see below |
| `mu` | **mobilisable share**: the part whose turnout is still open | see below |

How `pi` and `mu` are estimated:
- **`pi`:** from the CES pre- and post-election waves of the 2018 and 2022 midterms, with 2024 as a check. It is the share
  who were undecided before the election, plus the share whose post-election vote differed from their pre-election
  intention. It is pooled by group and shrunk toward the national value, so firm partisans come out near zero.
- **`mu`:** from the CES pre-election turnout-intention item against later turnout. It is the share who answered
  "probably", "undecided" or "don't know", plus intenders who didn't vote and non-intenders who did. It is validated
  where match rates allow; CPS can't give this.
- Both are 0–1. Statistics picks the exact variables and records them in the assumption register.

### 3.2 From reactions to group changes

For each story that passes Jev's gate for a race, GLM gives each group two numbers on the −2..+2 scales, averaged over
both option orders:
- `r_s`, support: positive means toward the Democrat.
- `r_t`, turnout: positive means more likely to vote.

The group's change that day:

```
Δd_g = 2 · pi_g · clip(c_s · k_s · r_s / 2, −1, 1) · a_e
Δt_g =     mu_g · clip(c_t · k_t · r_t / 2, −1, 1) · a_e
```

The terms:
- `r / 2` is how strongly the group reacts, from −1 to 1.
- `pi_g` and `mu_g` cap the effect at the part of the group that can actually move (principle 3).
- `2 · pi_g` is the margin change if every persuadable voter switched.
- `c_s` and `c_t` are the size calibrations. They are fitted on the 46 real events with this same formula: Engine supplies
  GLM's per-group answers on those events, and Statistics fits.
- `k_s` and `k_t` are the state's dials. They start at 1 and the weekly filter tunes them.
- `a_e` is the story's attention weight, from 0 to 1 (§4).

How long a story lasts (Matteo, 28–29 Sep; replaces the flat 10-day prior):
- Every story fades from the day it is first seen, with a 5.5-day half-life: about 40% left after a week, 17% after
  two, 7% after three (Matteo: 45% within a week, 15% after two weeks, under 10% after three).
- A one-off story (endorsements, scandals, debates, ads, candidates' policy news, other) that drops out of the news
  also fades within about a day (a 1-day half-life from `last_seen`).
- Lasting topics (`economy`: prices, jobs, gas; `national`: president, Congress, war, disasters) don't get that drop
  and keep fading at the age rate. The real calibration events' shifts held longer (stats-groundwork §10); the
  weekly filter checks the rate against polls.
- The 3 Nov forecast counts what is expected to remain of each story then, taking its coverage to end today.
- The weekly filter tunes the half-lives. `t` stays within [0, 1] and `d` within [−1, 1].

Each event counts once:
- The harness asks each event once per race. If an event is asked again, the earliest reactions are used.
- `a_e` is read fresh each day, so a story that keeps spreading grows its effect.
- Similar headlines are one story (§4), so a continuing story extends rather than stacks.

The sizes `c_s` and `c_t` are ranges, not single values (Matteo, 28 Sep evening):
- Every simulated election draws its own multipliers for the switching and turnout parts, averaging the fitted
  values; `c_t` equals `c_s` as a starting point.
- Their origin, route and updates are recorded in `simlab/move_params.json`.

The race's move comes from the formula in stats-groundwork §5.5:

```
Δm_r = Σ_g e_g·Δd_g + Σ_g e_g·(Δt_g / t_g)·(d_g − m_r),   e_g = n_g·t_g / Σ n·t
```

The first term is people switching; the second is turnout changing who votes. `moves.json` keeps the breakdown by group
and by story, so every move traces to named stories. The national move `Δ_N` uses the national group weights and the
national-scope reactions (§5).

### 3.3 Filter, Monte Carlo, stats-only twin

As stats-groundwork §5.6–5.8:
- **Daily update** (Matteo, 28 Sep evening: news moves every race, polls or not):
  - the statistical level is estimated from polls less the story effects in force on their dates;
  - each race's story effects go on top in full; a race without its own stories takes the nation's.

  `Δ` already includes the dials (§3.2), so they are not applied twice. `moves.json` also carries `delta_margin_base`
  (dials = 1) for the weekly re-tuning.
- **Weekly filter** (built 29 Sep, `simlab/weekly.py`). It runs on Mondays from 12 Oct inside the statistics step, or
  by hand with `python -m simlab.weekly`.
  - Each state, and the nation, has two dials: switching and turnout. 1 means the polls confirm the simulated effect;
    0 means they show none of it. The dials are learned from every poll since the stories began.
  - The dials only scale known effect paths, so the polls' likelihood is an exact quadratic in them. States pool with
    a national dial, so states with few polls borrow from it.
  - The same evidence weighs five fade speeds around 5.5 days.
  - A monitor flags states whose polls keep surprising the forecast (last 7 days, chi-squared p < 0.01) for the
    weekly auditor.
  - Each simulated election draws its dials from the result. Ensembles are used only if a non-linear parameter is
    added.
- **Monte Carlo:** 40,000 draws with Student-t errors (8 degrees of freedom) and a correlation floor of 0.25. Each draw
  also takes its own news-size multipliers (§3.2), so races with strong simulated reactions get wider, story-driven
  tails. A fixed sample of 1,000 draws is kept for one-dot-per-election charts.
- **Where the simulation runs** (Matteo, 28 Sep evening):
  - Statistics sets a daily `tier` per race in `races.json`: `simulate` (full), `watch` (the biggest stories only) or
    `statistics` (statistics and national news only).
  - A race runs on statistics alone only when the stats-only forecast (beyond 97/3), Cook ("Solid") and the market
    (beyond 95/5) all call it safe. The pilot races always simulate.
  - A race keeps its most competitive tier of the past week.
  - The harness reads the previous day's tiers.
- **Stats-only twin:** the same chain with Δ = 0.
- **Innovation monitor:** it flags states whose polls keep surprising the forecast. The weekly auditor (MiMo) explains
  them and never changes numbers.

### 3.4 Kev (Matteo, 29 Sep)

GLM gives the reactions on its own. Kev react-v1 failed the held-out checks on 28 Sep and react-v2 failed them on
29 Sep (direction 11 of 13 against GLM's 13; GLM and Kev averaged did worse than GLM alone). Matteo reopened shadow
mode the same day: Kev react-v2-2 answers the same questions every day as rows with `model: "kev"` and `shadow: true`,
never applied, and the weekly scoring compares it with GLM. It is served on Modal (B4) behind a bearer key, possibly on
a fixed daily sample sized to the serving budget. The harness's `--kev URL` option writes these rows; the daily job
passes it once the Kev session sends the URL, the key's secret name and the sample size.

## 4. The news pipeline (Engine)

- **Headlines** (29 Sep: the engine works on GDELT alone; Media Cloud plugs in if its key ever comes):
  - GDELT for every race and the nation, from its own job every 15 minutes (`simlab/newsnap.py`, writing
    `simlab-data/news/`). GDELT refuses an address for minutes after one success, so each run asks only the most
    overdue queries (contested races and the nation first) within about 9 minutes. A query saved in the last 6 hours
    isn't asked again; one that failed is asked by the next run, and every query covers 24 hours, so gaps fill.
  - RSS from state outlets that answer a declared bot and allow reuse: Signal Ohio, Signal Cleveland, the Texas
    Tribune, Carolina Public Press and The Maine Monitor (no Iowa outlet qualified). An item counts for a race only when it names one of that state's candidates in full. The States
    Newsroom sites refuse bots, so they aren't used.
  - Google News is not used (its terms; Matteo, 28 Sep). Headlines are cleaned, syndicated copies are merged, and
    similar headlines are clustered into stories.
- **The day's news** (29 Sep): every article first returned by a snapshot run that started between 09:30 UTC the day
  before and 09:30 UTC on the day. Each run is read by one day's job, so the US daytime news that arrives after a job
  is read by the next one, and an article a feed returns again counts only on its first day.
- **Race tags:** a race story belongs to its race. A national story goes to every race.
- **Jev labels** (Matteo, 28 Sep), all with outlet names removed first:
  - relevant to this race (this is the gate)
  - event type
  - who it helps on its face
  - whose voters it fires up or puts off (new; this catches backlash)
- **Attention `a_e`:** from coverage: distinct outlets, articles, days in the news, and candidate pageviews. Jev's
  salience only breaks ties, because both models overrated attention in the spot-check.
- **Event card:** 1–3 neutral sentences written by DeepSeek V4.1 Flash, with GLM as fallback and outlet names removed.
  The voter groups read the card, never the raw headlines.
- **Which stories get reactions** (A13, built 29 Sep): stories past the gate, best attention first, as many as the
  race's tier allows. The tier comes from the previous day's `races.json`; the pilot races always simulate.
  - simulate: 5 race stories and 3 national stories a day, the national ones asked with the state's personas;
  - watch: its 2 biggest race stories (attention at least 0.5) and no national ones;
  - statistics: none;
  - the nation ("US"): 3 national stories, asked once with state-neutral personas for `Δ_N`.
  National stories are gated for the simulated races and the nation. Until 11 Oct the daily job runs the pilot races
  only (`--scope pilot`); from 12 Oct every race in `simlab/newsraces.json`, which is rebuilt from `races.json` when
  candidates change or House seats are added (`python -m simlab.newsraces --races <races.json>`).
- **Stories about polls or forecasts get no reactions.** Polls already enter through the filter, so reacting to news
  about them would count them twice. This also keeps "poll" out of the movers' cards.
- **Each event counts once per race** (built 28 Sep):
  - Headlines under four words are dropped.
  - A story the card writer flags as "not a specific event" (a news round-up, a TV listing) is never selected.
  - A national story that repeats a race's own story loses its gate for that race.
  - Among each race's top 10 candidates, stories that report the same event in other words are checked in pairs by
    DeepSeek, and only the best-covered one is kept.
  - Across days: a story is first matched to the last 7 days' events by wording. A new candidate that doesn't match is
    then checked in pairs against the same race's recent events, most similar wording first. If it continues one, it
    takes that event's id, first sighting and labels, and extends its `last_seen` instead of stacking a second effect.
- **Cards:** no outlet names, and no "poll" or "survey" wording, so the Content & site caption checker passes them.

## 5. The reaction harness (Engine)

- **GLM-5.3 Flash, following the model-recipes rules:**
  - every scale asked both ways
  - one prompt per group per order, with the event card first and the persona last (for prompt caching)
  - turnout asked on its own, never alongside support
  - the persona's state set to the race's state
- **Wording: direct** (backlash test, 29 Sep). The reaction-aware wording lost accuracy on the real events. On the 45
  training events it got the direction right on 85% of those that moved opinion (direct: 92%) and its size-tracking
  fell from 0.26 to −0.11. On the 19 held-out events: 80% against 100%, error 3.22 against 3.05 points. The direct
  wording already produces backlash where it is real (Trump's money for Husted rallies Democrats). On 15 stories
  picked for possible backlash and 3 controls, the reaction-aware wording raised turnout moves everywhere (average
  size 0.52 against 0.30), as much on the controls as on the backlash stories, so it adds no backlash-specific signal
  (`runs/backlash__glm.jsonl`).
- **Scopes:** race (the race's state personas) and national (state-neutral personas).
- **House seats:** asked about "their district's U.S. House race", with personas in the seat's state.
- **Cost at full scale** (tiers of 28 Sep: 13 simulate, 7 watch): 13 × 8 + 7 × 2 + 3 ≈ 121 race-story pairs × 28
  groups × 2 questions × 2 orders ≈ 13,500 prompts on a day when every story is new; continuing stories aren't asked
  again. At the measured cost of 29 Sep ($0.024 for 504 group rows), that is about $0.16 a day. GLM answered about 270
  prompts a minute with 16 threads on 29 Sep, so about 50 minutes; `SIMLAB_THREADS` raises the thread count.

## 6. Snapshots and the daily job (Engine)

- **Snapshots:** `simlab/snap.py` (Kev session; first run 28 Sep 00:36 UTC) writes
  `simlab-data/snapshots/YYYY-MM-DD/HHMM/<source>/<name>.gz` plus `manifest.json` (URL, time, status, size, SHA-256).
  - Sources now: VoteHub polls; Wikipedia race pages, overview pages and the approval page, raw with revision ids;
    markets (benchmark only); Media Cloud for every race in `simlab/newsraces.json` if its key comes; pageviews.
  - News: GDELT and RSS come from the separate 15-minute news job (`.github/workflows/news.yml`) into
    `simlab-data/news/YYYY-MM-DD/HHMM/`, in the same format; the news step reads both folders.
  - Added later: the 2026 House page (Statistics' request), keyed sources (FEC, FRED, EIA) and early-vote files.
- **Schedule:** GitHub Actions in the public repo triggers every 15 minutes and takes a snapshot when the newest one is
  at least 150 minutes old, because GitHub drops most scheduled triggers (Kev session, 29 Sep). It pushes to the
  private data repo through a deploy key that can only write there (approved 28 Sep). Logs print nothing raw.
- **Daily job:** 09:47 UTC (10:47 UK until 25 Oct). It reads the snapshot runs that started before 09:30 UTC, runs
  steps 1–8 and commits private outputs to `simlab-data/derived/YYYY-MM-DD/`.
- **Publishing (from 12 Oct):** once Matteo switches the repository variable `SITE_PUBLISH` on after his 11 Oct go, a
  second job in `daily.yml` checks out only the day's `forecast.json`, `draws.json` and `races.json`. It copies them
  with `site/scripts/publish-day.mjs` to `site/data/live/` (`races.json` without `tier_reasons`, plus `history.json`)
  and `site/public/data/YYYY-MM-DD/`, commits them to the public repo and starts the Site workflow.
  - It publishes only when the statistics step passed; a failed post kit doesn't hold it back.
  - A day older than the one on the site is never published. A manual run of today's date publishes too, so switch
    `SITE_PUBLISH` off before a test run.
- **Run record:** `derived/YYYY-MM-DD/run.json` holds the git SHA, a hash of the settings, model slugs and hosts, input
  file hashes, spend, step timings and any fallbacks used.
- **Entry points the daily job calls, in order.** Each exits non-zero on failure, and its last stdout line is a
  one-line JSON summary that goes into `run.json`. A step whose module doesn't exist yet is skipped and logged.

  | Step | Command | Owner |
  | --- | --- | --- |
  | News | `python -m simlab.newsday --date D --snap <data>/snapshots --out <data>/derived --scope pilot\|all` | Engine (built) |
  | Reactions | `python -m simlab.harness --date D --out <data>/derived [--wording ...]` | Engine (built) |
  | Statistics | `python -m simlab.statsday --date D --data <data>`: polls, levels and groups, moves, filter, Monte Carlo | Statistics |
  | Post kit | `python -m simlab.publish.kit --date D --data <data>`, writing to `derived/D/post-kit/` in the pilot | Content & site |
- **Secrets:** the deploy key, and the OpenRouter key, which Matteo adds as a repository secret. The private pilot uses
  the test key.
- **When things fail:**
  - A failed step re-runs alone from the saved files, and cached model answers make re-runs free.
  - A failed source falls back to its last good file, flagged in the run record.
  - A missed run is caught by the 11:30 UK Claude check, which emails Matteo.

## 7. File contract

All dated files live in `simlab-data/derived/YYYY-MM-DD/` (private) unless marked public. Every JSON file carries
`date`, `run_id` and `schema` (a version number).

Race ids follow `simlab/polls.py`:
- `NC` is a regular Senate race; `OH-S` is a special.
- `TX-28` is a House district; `AK-AL` is an at-large seat.
- `US-S` and `US-H` are chamber control; `US` is the national scope.

Special elections and ranked-choice voting are also fields in `races.json`.

| File | Writer | Readers | Content |
| --- | --- | --- | --- |
| `races.json` (daily) | Statistics | all | `race_id → {state, office, district, special, rcv, candidates, left_party, incumbent_party, status, tier, tier_raw, tier_reasons}`. House seats (office `house`) come from Kev's `house_races.json` once its inputs are in, with its tiers and extra fields (`incumbent_running`, `checked`, `new_map`, `p_dem_stats`, `ratings_consensus`); their `left_party` is `D`, or `O` where no Democrat runs |
| `polls.csv` | Statistics | Statistics, scoring | one row per poll version (stats-groundwork §5.1) |
| `events.jsonl` | Engine | Statistics, Content | `{event_id, first_seen (UTC ISO), last_seen, scope, races, gate: {race_id: p}, type, helps_face, fires_up: {D, R}, puts_off: {D, R}, attention: {outlets, articles, days, pageviews, a}, card}`; raw headlines kept separately in `news_private.jsonl` |
| `reactions.jsonl` | Engine | Statistics, scoring | one row per race × event × group × model: `{race_id, event_id, group, model, shadow, wording, support, turnout}` (expected values, −2..+2) |
| `groups.json` | Statistics | Statistics, Content | `{units, d_source, race_id: {group: {n, t, d, pi, mu}}}`, all fractions (`d` from −1 to 1, the rest from 0 to 1), including a `US` entry and the simulated House seats (from `house_groups.json`, so `moves.json` covers them too); `d_source` (text) says where the pattern of `d` comes from |
| `moves.json` | Statistics | filter, Content, scoring | `{units, race_id: {delta_margin, delta_margin_base, delta_turnout, by_group: {group: {dd, dt}}, by_event: {event_id: today's change}, by_event_effect: {event_id: total effect so far}}}` for GLM, plus the same under `shadow` for Kev. Margins in points of two-party margin; turnout in percentage points. Each race's `events` block gives every story's `first_seen`, `last_seen`, type, half-life, full effect (and its switching and turnout parts) and `election_day` effect. `movers` in `forecast.json` read `election_day`, the story's effect on the 3 Nov margin |
| `params.json` (daily) | Statistics | Statistics, Engine | the parameters in force that day: `{c_s, c_t, dials: {state, US or default: {k_s, k_t, sd_s, sd_t}}, age_half_life_days, half_life_days, lasting_types, dial_prior, dial_posterior, fitted_on}` |
| `filter_weekly.json` (Mondays) | Statistics | Statistics, auditor | the weekly filter's output: `{polls, prior, fade: {grid, weights, half_life}, posterior: {labels, mean, cov, log_evidence}, dials, polls_alone, surprises: {race_id: {n, chi2, p, mean_z, flag}}}` |
| `levels.json`, `filter_state.json` | Statistics | Statistics | stats-groundwork §9 |
| `forecast.json` (public) | Statistics | Content | `{races: {race_id: {p_dem_win, margin: {p10, p50, p90}, stats_only: {p_dem_win, margin}, benchmarks: {poll_avg, market, cook}, movers: [{event_id, card, delta}], news: {effect, switching, turnout, if_weaker, if_stronger}, today: {p_dem_win, margin, stats_only, movers}}}, senate: {p_r_50plus, p_d_caucus_51, p_independents_decide, seats, news, today}, house: {p_d_majority, p_r_majority, majority, seats: {D, R, O}, stats_only, benchmarks: {market}, contested, fixed, races: {seat: {p_dem_win, margin, tier}}, today} or null until house.py's inputs are in, news_dials: {national: {mean, sd}, tau}}`; O counts seats won by a challenger other than a Democrat |
| `draws.json` (public) | Statistics | Content | the fixed 1,000-draw sample: every Senate race's margin, the seat totals (`seats: {senate, house}`) and the simulated House seats' margins (`house_races`) |
| `run.json` | Engine | all | run record (§6) |

A writer may add fields. Renaming or removing a field needs a note to the reading sessions and a `schema` bump.

## 8. Testing and checkpoints

- Each step is built test-first on saved example files. Re-running a saved day must reproduce identical numbers.
- **Backlash test (28 Sep):** decides the reaction wording (§5).
- **Before the pilot:** refit `c_s` and `c_t` on the 46 real events with the §3.2 formula.
- **Fri 2 Oct:** the whole chain runs end to end for Ohio. If not, the pilot starts with Ohio alone.
- **Sat 3 – Sun 4 Oct:** rehearsals on GitHub Actions.
- **Fri 9 Oct:** House check.
- **Sun 11 Oct:** go or no-go for the public launch (criteria in the roadmap).

## 9. Open items

| Item | Owner | By |
| --- | --- | --- |
| `pi` and `mu` estimates for OH, NC, TX (all 35 states by 12 Oct) | Statistics | Thu 1 Oct |
| Weights of the attention formula. The spot-check couldn't test them (29 Sep): 29 of the 32 stories Matteo rated had one outlet in the old Google News store, so the formula scored almost all of them the same. Re-check on about 20 GDELT and Media Cloud stories in the pilot week | Engine | Fri 9 Oct |
| Full-scale rehearsal (A13) once Media Cloud's key is in: time, spend and failures at `--scope all` | Engine | Fri 9 Oct |
