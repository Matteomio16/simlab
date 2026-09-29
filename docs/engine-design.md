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
| 10:17 | 1. Polls | Statistics | snapshots | `polls.csv` |
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
| `d` | vote margin D − R within the group, at the starting level | CES midterm Senate vote, shifted to the race's level |
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
- One-off stories (endorsements, scandals, debates, ads, candidates' policy news, other) keep their full effect while
  in the news, from `first_seen` to `last_seen`, then fade with a 1-day half-life.
- Lasting topics (`economy`: prices, jobs, gas; `national`: president, Congress, war, disasters) fade from their
  first day, even while in the news, with a 10-day half-life. They are important at first, not that important after
  three weeks, and over by about 30 days (Matteo, 29 Sep). The real calibration events' shifts held longer
  (stats-groundwork §10); the weekly filter checks this against polls.
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
- **Weekly re-tuning of the dials from 12 Oct.** Because the dials are linear, this is an exact Kalman update. Ensembles
  are used only if a non-linear parameter is added.
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

### 3.4 Kev in shadow mode (Matteo, 28 Sep)

Kev answers the same group questions every day. Its rows go to `reactions.jsonl` with `model: "kev"` and `shadow: true`.
Statistics computes Kev's moves alongside GLM's but never applies them. Every week, the scoring checks which model's
moves better matched the following polls.

Kev react-v2 joins the numbers on 12 Oct only if it passes three checks on held-out events:
- its direction is at least as good as GLM's
- its size-tracking is above zero
- GLM and Kev averaged beat GLM alone

## 4. The news pipeline (Engine)

- **Headlines:** from the snapshots. Google News RSS per race and nationally; GDELT when it answers. They are cleaned,
  syndicated copies are merged, and similar headlines are clustered into stories (`news.build`).
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
- **Which stories get reactions:** every story that passes the gate, capped at the top 5 per race per day by attention.
  National stories count for every race, and are also asked once with state-neutral personas for `Δ_N`.
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
- **Wording:** the direct wording, unless the backlash test (running 28 Sep) shows the reaction-aware wording keeps
  accuracy on the real events.
- **Scopes:** race (the race's state personas) and national (state-neutral personas).
- **Cost at full scale:** about 35 races × (5 race + 3 national stories) × 28 groups × 2 questions × 2 orders ≈ 31,000
  prompts a day. At the measured $0.03 per 1,000 decisions asked both ways, that is about $0.5 a day, or $15 a month;
  House seats add about half. The ledger checks this during the pilot.
- **Kev shadow:** the same questions go to Kev on Modal once a day, as one burst.

## 6. Snapshots and the daily job (Engine)

- **Snapshots:** `simlab/snap.py` (Kev session; first run 28 Sep 00:36 UTC) writes
  `simlab-data/snapshots/YYYY-MM-DD/HHMM/<source>/<name>.gz` plus `manifest.json` (URL, time, status, size, SHA-256).
  - Sources now: VoteHub polls; Wikipedia race pages, overview pages and the approval page, raw with revision ids;
    markets (benchmark only); news; pageviews.
  - Added later: the 2026 House page (Statistics' request), keyed sources (FEC, FRED, EIA) and early-vote files.
- **Schedule:** GitHub Actions in the public repo runs every 3 hours at minute 17. It pushes to the private data repo
  through a deploy key that can only write there (approved 28 Sep). Logs print nothing raw.
- **Daily job:** 09:17 UTC (10:17 UK until 25 Oct). It runs steps 1–8, commits private outputs to
  `simlab-data/derived/YYYY-MM-DD/`, and writes public outputs to `simlab/public/forecasts/YYYY-MM-DD/`. Public outputs
  are only pushed from 12 Oct, after Matteo's go.
- **Run record:** `derived/YYYY-MM-DD/run.json` holds the git SHA, a hash of the settings, model slugs and hosts, input
  file hashes, spend, step timings and any fallbacks used.
- **Entry points the daily job calls, in order.** Each exits non-zero on failure, and its last stdout line is a
  one-line JSON summary that goes into `run.json`. A step whose module doesn't exist yet is skipped and logged.

  | Step | Command | Owner |
  | --- | --- | --- |
  | News | `python -m simlab.newsday --date D --snap <data>/snapshots --out <data>/derived` | Engine (built) |
  | Reactions | `python -m simlab.harness --date D --out <data>/derived [--wording ...] [--kev URL]` | Engine (built) |
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
| `races.json` (daily) | Statistics | all | `race_id → {state, office, district, special, rcv, candidates, left_party, incumbent_party, status, tier, tier_raw, tier_reasons}` |
| `polls.csv` | Statistics | Statistics, scoring | one row per poll version (stats-groundwork §5.1) |
| `events.jsonl` | Engine | Statistics, Content | `{event_id, first_seen (UTC ISO), last_seen, scope, races, gate: {race_id: p}, type, helps_face, fires_up: {D, R}, puts_off: {D, R}, attention: {outlets, articles, days, pageviews, a}, card}`; raw headlines kept separately in `news_private.jsonl` |
| `reactions.jsonl` | Engine | Statistics, scoring | one row per race × event × group × model: `{race_id, event_id, group, model, shadow, wording, support, turnout}` (expected values, −2..+2) |
| `groups.json` | Statistics | Statistics, Content | `{units, race_id: {group: {n, t, d, pi, mu}}}`, all fractions (`d` from −1 to 1, the rest from 0 to 1), including a `US` entry |
| `moves.json` | Statistics | filter, Content, scoring | `{units, race_id: {delta_margin, delta_margin_base, delta_turnout, by_group: {group: {dd, dt}}, by_event: {event_id: today's change}, by_event_effect: {event_id: total effect so far}}}` for GLM, plus the same under `shadow` for Kev. Margins in points of two-party margin; turnout in percentage points. Each race's `events` block gives every story's `first_seen`, `last_seen`, type, half-life, full effect (and its switching and turnout parts) and `election_day` effect. `movers` in `forecast.json` read `election_day`, the story's effect on the 3 Nov margin |
| `params.json` (weekly) | Statistics | Statistics, Engine | `{c_s, c_t, dials: {state: {k_s, k_t}}, half_life_days: {type: days}, fitted_on}` |
| `levels.json`, `filter_state.json` | Statistics | Statistics | stats-groundwork §9 |
| `forecast.json` (public) | Statistics | Content | `{races: {race_id: {p_dem_win, margin: {p10, p50, p90}, stats_only: {p_dem_win, margin}, benchmarks: {poll_avg, market, cook}, movers: [{event_id, card, delta}], news: {effect, switching, turnout, if_weaker, if_stronger}}}, senate: {p_r_50plus, p_d_caucus_51, p_independents_decide, seats, news}, house: {p_d_majority, seats}}` |
| `draws.json` (public) | Statistics | Content | the fixed 1,000-draw sample: every race's margin and the seat totals |
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
| Reaction wording (backlash test) | Engine | Tue 29 Sep |
| Weights of the attention formula, checked against Matteo's spot-check answers | Engine | Thu 1 Oct |
| Kev react-v2 and its three checks | Kev session | ~10 Oct |
