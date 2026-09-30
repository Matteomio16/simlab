# Roadmap to 3 November

Written 28 Sep 2026 and updated the same day with Matteo's dates:
- build this week
- a private pilot from Monday 5 Oct
- the public full run from Monday 12 Oct

It turns `docs/plan.md` and `docs/infrastructure.md` (§12) into one task list with owners, and adds the content track.
The engine's design goes in `docs/engine-design.md`. Update the Status column as things land. Decisions still go into
CLAUDE.md §5.

## The shape

| Phase | Dates | Goal |
| --- | --- | --- |
| 1. Build | Mon 28 Sep – Sun 4 Oct | The forecast machine end to end for Ohio, North Carolina and Texas; the content plan; the accounts |
| 2. Pilot (private) | Mon 5 – Sun 11 Oct | The daily loop runs for OH, NC and TX. Forecasts stay internal; making-of posts can go out. The House seats are built alongside |
| 3. Full run (public) | Mon 12 Oct – Tue 3 Nov | All 35 Senate races and ~40 House seats, public daily forecasts, early-vote data, weekly scoring |
| 4. After | from 4 Nov | Score every race, run the blind track, publish what worked and what missed |

The full run is three weeks plus election day. Together, the pilot and the full run make about four weeks.

Fixed dates:
- Ohio early voting starts around 6 Oct, during the pilot.
- 12 Oct: first public forecast and code freeze. After the freeze, changes go in a public changelog and both the old and
  new versions are scored.
- North Carolina early voting starts 15 Oct, Texas around 19 Oct.
- Election day: 3 Nov.

Checkpoints and fallbacks:
- **Fri 2 Oct:** the chain runs end to end for Ohio. If not, the pilot starts with Ohio alone and NC and TX join during
  the week.
- **Fri 9 Oct:** the House is ready. If not, the 40 House seats launch on 12 Oct from statistics only, and the simulated
  voters join a week later.
- **Sun 11 Oct:** pilot review (criteria below), then go or no-go for the public launch.

## Where we are (28 Sep)

- **Done:**
  - the test bench, which found which model does which job (`docs/model-recipes.md`)
  - Kev fine-tunes on survey data (ces-v1 to v3)
  - test data: CES 2024, Census turnout, 46 real events with measured shifts, poll history
  - a prototype for labelling news
  - both GitHub repos, with the model-answer cache exported
  - the content research (`docs/research/`)
  - since 28 Sep: snapshots every 3 hours (A1), Senate starting levels (A3), the news pipeline (A4), the GLM harness
    (A5) and the daily job (A8)
  - Kev react-v1 (B1) and its verdict (B2): it failed as a second opinion on reactions, so GLM gives them alone
  - the Monte Carlo (A7), with the statistics step of the daily job (`simlab/statsday.py`)
  - the daily filter (A6), voter groups for all states and the persuadable and mobilisable shares (`simlab/pimu.json`)
- **Next on the critical path:** the Ohio end-to-end run for the 2 Oct checkpoint, and the 3–4 Oct rehearsals (A10).
  The snapshots still lack FEC, economy and early-vote files; early-vote and voter files are overwritten, so they
  can't be recovered later.
- **Also missing:** the free API keys (only OpenRouter's key exists) and the social accounts.

## Track A: the engine

| # | Piece | What it does | Owner | Due | Status |
| --- | --- | --- | --- | --- | --- |
| A1 | Snapshots | Every 3 hours, saves raw polls, headlines, ratings, markets (benchmark only), early-vote files, FEC and economy data to the private data repo, with hashes | Kev (taken over 28 Sep at Matteo's request) | Tue 29 Sep | `simlab/snap.py` and the 3-hourly GitHub Actions job live since 28 Sep; GitHub dropped 3 of the first 4 scheduled runs, trigger being fixed; FEC, economy and early-vote files join later |
| A2 | Download-now list | 538 poll histories, this week's NC and OH voter files, new House maps, 2024 results by new district | Engine | Wed 30 Sep | partly: 538 approval and generic ballot; 29 Sep, 2024 presidential results on the 2026 lines for all 435 districts (The Downballot) and ACS citizen adults by race and degree per district (`data/house/`, for A11). Voter files: counts only, no raw NC or OH files even locally (Matteo, 29 Sep), and the new plans' block files after 9 Oct, only for simulated seats in the 10 redrawn states (no Redistricting Data Hub, Matteo 29 Sep) |
| A3 | Starting levels | Each race's starting vote and range: fundamentals plus a poll average with pollster house effects. Also the stats-only forecast the simulation must beat | Statistics | Thu 1 Oct (Senate) | done 28 Sep: Senate levels (`simlab/levels.py`, 35 races, 28 with polls); voter groups with persuadable and mobilisable shares for all 50 states + DC (`simlab/groups.py`, b19b665); first-seen dates, Alaska checked (head-to-head polls), Montana kept two-way for the pilot pending Matteo (04b41f6) |
| A4 | News pipeline | Daily headlines → stories → which race → Jev asks "does this change anything?" → labels → a neutral 1–3 sentence event card, outlet names removed | Engine | Thu 1 Oct | built 28 Sep (`simlab/newsday.py`). 29 Sep: works on GDELT alone, from a 15-minute news job that fills refused queries later (`simlab/newsnap.py`), plus RSS from Signal Ohio, Signal Cleveland, the Texas Tribune, Carolina Public Press and The Maine Monitor; Media Cloud optional (its sign-up is stuck) |
| A5 | GLM harness | Asks each voter group how its support and turnout move, following the model-recipes rules. Sizes come from real data, not the model. Logs proposed vs applied changes | Engine | Fri 2 Oct | built 28 Sep (`simlab/harness.py`); first real run 28 Sep |
| A6 | Filter | Daily update from new polls; weekly ensemble Kalman update, which re-tunes each state's sensitivity dials | Statistics | Fri 2 Oct (daily), Mon 12 Oct (weekly) | daily filter built 28 Sep (47e1852; `simlab/moves.py`, story effects from group reactions, c_s fitted, headline and twin in the Monte Carlo); news fades with age (5.5-day half-life; one-off stories drop within a day once out of the news); weekly filter built 29 Sep (`simlab/weekly.py`, 8fe9c69): per-state news dials learned from the polls (exact update, pooled with a national dial), fade-speed grid, surprise monitor; runs Mondays from 12 Oct inside the statistics step. Left for Matteo: the demographic factor state |
| A7 | Monte Carlo | 40,000 correlated simulated elections → "wins 7 in 10", ranges, Senate control, House seats | Statistics | Thu 1 Oct | done 28 Sep (e7fb30f; `simlab/montecarlo.py`, run by `python -m simlab.statsday`, ~14 s, 35 races); `house` null until A11 |
| A8 | Daily job | One command a day on GitHub Actions, with a run record, a spend line and an alert if a run is missed | Engine | Sat 3 Oct | built 28 Sep (`simlab/daily.py`, `daily.yml`); `PIPELINE_ON` switched on Thu 1 Oct (Matteo, 29 Sep). 29 Sep: triggers every 15 minutes from 09:47 to 14:47 UTC and runs once a day, because GitHub drops most scheduled triggers |
| A9 | Scoring | Weekly scores against the poll average, the markets, Cook and the stats-only forecast | Kev | first on Mon 19 Oct | test metrics exist |
| A10 | Rehearsals | Two full dry runs on GitHub Actions | all, led by Engine | Sat 3 – Sun 4 Oct | the levels' gap is closed (frozen inputs in `simlab/levels_inputs.json`); the statistics chain writes everything in about 10 s but hasn't run on Actions yet. 29 Sep: the whole chain ran locally for 29 Sep (news 8 s, reactions 51 s, statistics 28 s, kit 11 s). Before the first run on Actions, every session moves its local `simlab-data/derived/` aside: the job commits `derived/<day>/` to the data repo, and untracked local copies would block `git pull`. 29 Sep evening: the first full run on Actions passed for the five pilot races (run 36629024522: news 47 s, reactions 10.5 min, statistics 13 s, kit 14 s; $0.07; outputs in simlab-data `derived/2026-09-29/`). What to run on 3-4 Oct and what passes: `docs/rehearsal.md` |
| A11 | House seats | Voter groups re-weighted to each district on the new 2026 maps; district baselines and polls; the other ~395 seats from the fundamentals map | Kev (moved from Statistics 28 Sep, Matteo's call); starts once A2's House maps and 2024 results by district land, ~Wed 30 Sep | Fri 9 Oct | fundamentals for all 435 seats done 29 Sep (`simlab/house.py`, 1a7520d), wired into statsday and the Monte Carlo (413ed7d, 8e686b0); runs daily from 30 Sep; House news (A13) built d1fce9d, from the 1 Oct run; per-seat news uncertainty before 12 Oct |
| A13 | Scale-up of news and reactions | News queries for all 35 Senate races and ~40 House seats (from `races.json`); a reaction budget that fits the day: national stories asked once with state-neutral personas, fewer groups for safe races, a minimum attention, OpenRouter's batch API if needed (GLM manages ~200 prompts a minute) | Engine | Fri 9 Oct | built 29 Sep (`simlab/newsraces.py`; selection by the previous day's tier: simulate 5 race + 3 national stories, watch its 2 biggest, statistics none; about 13,500 prompts and 50 minutes on a busy day). House seats built 29 Sep (Matteo's yes): the simulated seats come from the daily `races.json`, one GDELT query per state every 12 hours, each story gated for every seat in its state, national-story reactions cached per state. Still to do: the full-scale rehearsal (Senate and House) on Wed 7 Oct (Matteo's yes; `docs/rehearsal.md`); the query numbers checked against a full day of the news job |
| A12 | Early-vote data | NC absentee files now; NC in-person from 15 Oct; Texas from ~19 Oct; Ohio as published | Kev (it owns the snapshots); moves to Engine only if B2 slips | from Mon 5 Oct | live: NC (every 30 min, counts only), ME (counts only, raw file never stored), IA and TX switched on (publish from ~14 and ~19 Oct); Ohio skipped for the pilot (bot check; manual link route on record) |
| A14 | Pre-freeze code review | An independent review of the daily chain before the 12 Oct freeze | a new review session | Sat 10 – Sun 11 Oct | — |

## Track B: the models (who does which job)

| Job | Model | Why (measured) |
| --- | --- | --- |
| "Does this story change anything for this race?" | Jev | Says "no change" to 99–100% of irrelevant news; cheapest |
| Labels: event type, side helped, salience | Jev (Matteo's 32-story spot-check: 102 of 126 labels right, GLM 95; type 29 of 32, GLM 26) | Cheap. Outlet names are removed first, because they sway every model |
| Direction of each group's reaction | GLM-5.3 Flash, each scale asked both ways | Right direction on 92% of events that moved opinion |
| The most important stories (high salience, close races) | GLM alone (Kev failed B2 on 28 Sep) | Averaging only cancels bias if the two models' errors are independent |
| Size of reactions | Real past shifts, then tuned per state by the filter | No model tracks size |
| Starting levels | Statistics, with Kev as a check | Statistics beat every model |
| How each voter group splits at the start (the pattern only; each race's level stays statistical) | Kev ces-v3b in every race, the survey where Kev has no answer (Matteo, 29 Sep) | Closer than the survey on held-out 2024 votes (within noise); one source for House and Senate |
| Event cards (short neutral text) | DeepSeek V4.1 Flash or GLM | A text job |
| Weekly auditor (explains surprises, never changes numbers) | MiMo | |

| # | Step | Due | Status |
| --- | --- | --- | --- |
| B1 | Kev react-v1: trained on real measured shifts and design rules, never on GLM's answers | Thu 1 Oct | done 28 Sep (23 min, about $2.30; no loss of Kev's public skills) |
| B2 | Kev verdict on the 19 held-out events. Does it track size (GLM scores 0.26)? Are its errors independent of GLM's? Does Kev + GLM beat GLM alone? | Fri 2 Oct | done 28 Sep: fails. Size-tracking 0.00 (GLM 0.29, Jev 0.28); errors correlate 0.75 with GLM's; Kev + GLM 2.61 error vs GLM alone 2.32. Passes null (0.961) and is best on mirror (flip correlation 0.961, lean +0.002). Scores in `kev-finetune/runs/react-v1/react_scores_T1.json` |
| B3 | Freeze the routing table above | Sat 3 Oct | draft; after B2, reactions go to GLM alone (asked both ways), with Jev as the gate |
| B4 | Kev serving on Modal (one GPU, scale to zero, one burst a day), if it passes B2 | Sun 11 Oct | Matteo reopened it 29 Sep: react-v2-2 in shadow mode (answers daily, never applied, scored weekly against GLM); deploy waits on Matteo's Modal serving key |

## Track C: content and distribution

| # | Step | Who | Due | Status |
| --- | --- | --- | --- | --- |
| C1 | Research: political data accounts (incl. the Integrity Index), AI-simulation startups, AI showcase projects, platform rules | Claude | Mon 28 Sep | done (`docs/research/`) |
| C2 | Content plan: a menu of formats, cadence, tone; name and handles; on camera or voice-over | Content & site proposes, Matteo picks | Wed 30 Sep | draft for Matteo (`docs/content-plan.md`) |
| C3 | Accounts: Instagram professional (Creator) with Threads, X, Bluesky; TikTok and YouTube Shorts optional | Matteo | Fri 2 Oct | notapoll.org bought 28 Sep; setup in progress (email routing, then IG, Threads, X, Bluesky on @notapoll.org, Buffer free for X, Threads and Bluesky) |
| C4 | Making-of posts, starting with the test-bench findings | Content & site drafts, Matteo approves and posts | from Sat 3 Oct | Lab notes 1–3 drafted, shown to Matteo 28 Sep |
| C5 | Chart factory and daily post kit: slides (1080×1350), a 9:16 video, captions, alt text, an X thread | Content & site | Sun 4 Oct (the pilot makes internal kits daily) | daily kit command built (`python -m simlab.publish.kit`), layouts picked; 5 special editions drafted; 9:16 video built (`reel.py`, kit `--reel`) |
| C6 | Site at notapoll.org (labs.scaliastudio.dev/midterms redirects there): 3 Oct home, methods, Lab notes, About with no numbers; 12 Oct Senate overview, map, simulator and race pages; week of 19 Oct track record, changelog, archive; election-night page by 3 Nov | Website session; Matteo sets up Cloudflare (`site/README.md`) | 3 Oct, then 12 Oct | built 29 Sep in `site/` (Next.js static export, newsroom design approved by Matteo, sample data); methods text drafted for Matteo's review |
| C7 | Publishing and ethics review (Field Guide checklist); OSF pre-registration yes or no | Matteo with a new review session (not Content & site, which made the posts) | Sat 10 Oct | open task |
| C8 | Posting by hand: Meta Business Suite for Instagram, x.com's scheduler | Matteo | making-of from 3 Oct, forecasts from 12 Oct | — |
| C9 | Automated posting behind an approval flag: the Instagram API, and Buffer's free plan for X, Threads and Bluesky | Content & site; Matteo creates the apps and keys | 12–18 Oct | — |

## The pilot week (5–11 Oct, private)

The daily loop for Ohio, North Carolina and Texas, plus two more races (recommended Iowa and Maine; Matteo, 29 Sep):
1. data
2. news
3. reactions
4. filter
5. Monte Carlo
6. post kit (internal)

The stats-only twin runs beside it. Kev joins if it passed B2.

We go public on 12 Oct if all of these hold by 11 Oct:
- the daily run finished without hand fixes on at least 5 of 7 days
- spend stayed within the pilot budget (about $5/month)
- every move in a forecast traces to a poll or a named event
- the post kit comes out ready to review

Also during the pilot week:
- the House seats (A11)
- the site and methods page (C6)
- the ethics review and the OSF decision (C7)

## The full run (12 Oct – 3 Nov, public)

- All 35 Senate races and about 40 House seats from 12 Oct. The House runs from statistics only if the 9 Oct check fails.
- Daily public forecasts, posted by hand at first. Posting is automated behind the approval flag during the first week.
- Early-vote files: North Carolina from 15 Oct, Texas from about 19 Oct, Ohio as published.
- The weekly filter runs every Monday from 12 Oct, and weekly scoring from 19 Oct.
- Divergence calls declared in advance.
- A live page on election night.

## Who does what

| Session | Owns |
| --- | --- |
| Engine | A2, A4, A5, A8, A13; leads A10; the news spot-check page |
| Statistics | A3, A6, A7 |
| Kev | A1, B1–B4 (done), A11, then A9 and A12 |
| Content & site | C2, C4, C5, C9 |
| Daily check (scheduled task) | the 11:30 UK digest; drafts posts once forecasts exist |
| Website (new, 29 Sep) | C6 |
| Review (new, fresh sessions) | C7 on Sat 10 Oct; A14 on 10–11 Oct |
| Matteo | the list below |

Each session owns its own files. Edits to shared files (CLAUDE.md, CHANGELOG, pyproject) stay small. Four sessions at
once use up the Claude plan's limits faster. If the limits bite, pause Content & site before the others.

## What only Matteo can do

| When | What |
| --- | --- |
| Mon 28 Sep | News spot-check: about 100 labels, about 30 minutes |
| Wed 30 Sep | Pick the content formats and the project name |
| Thu 1 Oct | Done 29 Sep: Census key, Kev serving key, OpenRouter GitHub secret, Cloudflare timer (ops/cron). Dropped: FEC, FRED, EIA (not used yet) and Redistricting Data Hub (not needed). Media Cloud stuck at email verification; news runs on GDELT and RSS without it |
| Fri 2 Oct | Create the accounts (kits/launch/ has everything to paste); deploy the notapoll.org launch page with the website session's steps (a hype page until after the pilot, not a redirect; Matteo, 30 Sep) |
| Fri 9 Oct | Cloudflare: redirect labs.scaliastudio.dev/midterms to notapoll.org, the site's home (steps in `site/README.md`) |
| Sat 10 Oct | Publishing and ethics review; OSF yes or no; raise the OpenRouter cap to $30 (projection revised after the 30 Sep test run, `docs/rehearsal.md`: about $21 by 3 Nov, because GLM's hosts now make it reason; the test key stays; `SIMLAB_BUDGET_USD` follows the cap) |
| Sun 11 Oct, after the go | Set the repository variables `SITE_PUBLISH` to `on`, `SITE_MODE` to `forecast` and `SITE_DATA` to `live`, together. The site switches by itself when the 12 Oct run's forecast lands (about 10:05-10:45 UTC). After that, switch `SITE_PUBLISH` off before any test run of the daily job |
| from 12 Oct | About 30 minutes a day approving posts |

GitHub access for the scheduled jobs: Claude sets up a deploy key that can only write to the private data repo
(approved 28 Sep).
