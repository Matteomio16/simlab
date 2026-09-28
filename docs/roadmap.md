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
- **In progress:** Kev trained on real news reactions (react-v1, Kev session).
- **Overdue:** daily snapshots of live data. They feed the forecast and are the only input the blind track may use
  after the election. Some sources can't be recovered later: news feeds, and early-vote and voter files, which are
  overwritten.
- **Also missing:** the free API keys (only OpenRouter's key exists) and the social accounts.

## Track A: the engine

| # | Piece | What it does | Owner | Due | Status |
| --- | --- | --- | --- | --- | --- |
| A1 | Snapshots | Every 3 hours, saves raw polls, headlines, ratings, markets (benchmark only), early-vote files, FEC and economy data to the private data repo, with hashes | Kev (taken over 28 Sep at Matteo's request) | Tue 29 Sep | `simlab/snap.py` and the 3-hourly GitHub Actions job live since 28 Sep; FEC, economy and early-vote files join later |
| A2 | Download-now list | 538 poll histories, this week's NC and OH voter files, new House maps, 2024 results by new district | Engine | Wed 30 Sep | partly (538 approval and generic ballot) |
| A3 | Starting levels | Each race's starting vote and range: fundamentals plus a poll average with pollster house effects. Also the stats-only forecast the simulation must beat | Statistics | Thu 1 Oct (Senate) | not started |
| A4 | News pipeline | Daily headlines → stories → which race → Jev asks "does this change anything?" → labels → a neutral 1–3 sentence event card, outlet names removed | Engine | Thu 1 Oct | prototype (`news.py`) |
| A5 | GLM harness | Asks each voter group how its support and turnout move, following the model-recipes rules. Sizes come from real data, not the model. Logs proposed vs applied changes | Engine | Fri 2 Oct | asking, cache, spend cap exist |
| A6 | Filter | Daily update from new polls; weekly ensemble Kalman update, which re-tunes each state's sensitivity dials | Statistics | Fri 2 Oct (daily), Mon 12 Oct (weekly) | not started |
| A7 | Monte Carlo | 40,000 correlated simulated elections → "wins 7 in 10", ranges, Senate control, House seats | Statistics | Thu 1 Oct | not started |
| A8 | Daily job | One command a day on GitHub Actions, with a run record, a spend line and an alert if a run is missed | Engine | Sat 3 Oct | not started |
| A9 | Scoring | Weekly scores against the poll average, the markets, Cook and the stats-only forecast | Kev | first on Mon 19 Oct | test metrics exist |
| A10 | Rehearsals | Two full dry runs on GitHub Actions | all | Sat 3 – Sun 4 Oct | — |
| A11 | House seats | Voter groups re-weighted to each district on the new 2026 maps; district baselines and polls; the other ~395 seats from the fundamentals map | Statistics | Fri 9 Oct | not started |
| A12 | Early-vote data | NC absentee files now; NC in-person from 15 Oct; Texas from ~19 Oct; Ohio as published | Kev | from Mon 5 Oct | — |

## Track B: the models (who does which job)

| Job | Model | Why (measured) |
| --- | --- | --- |
| "Does this story change anything for this race?" | Jev | Says "no change" to 99–100% of irrelevant news; cheapest |
| Labels: event type, side helped, salience | Jev, confirmed or changed after Matteo's spot-check | Cheap. Outlet names are removed first, because they sway every model |
| Direction of each group's reaction | GLM-5.3 Flash, each scale asked both ways | Right direction on 92% of events that moved opinion |
| The most important stories (high salience, close races) | GLM and Kev, averaged; GLM alone if Kev fails B2 | Averaging only cancels bias if the two models' errors are independent |
| Size of reactions | Real past shifts, then tuned per state by the filter | No model tracks size |
| Starting levels | Statistics, with Kev as a check | Statistics beat every model |
| Event cards (short neutral text) | DeepSeek V4.1 Flash or GLM | A text job |
| Weekly auditor (explains surprises, never changes numbers) | MiMo | |

| # | Step | Due | Status |
| --- | --- | --- | --- |
| B1 | Kev react-v1: trained on real measured shifts and design rules, never on GLM's answers | Thu 1 Oct | building |
| B2 | Kev verdict on the 19 held-out events. Does it track size (GLM scores 0.26)? Are its errors independent of GLM's? Does Kev + GLM beat GLM alone? | Fri 2 Oct | — |
| B3 | Freeze the routing table above | Sat 3 Oct | draft |
| B4 | Kev serving on Modal (one GPU, scale to zero, one burst a day), if it passes B2 | Sun 11 Oct | kit ready |

## Track C: content and distribution

| # | Step | Who | Due | Status |
| --- | --- | --- | --- | --- |
| C1 | Research: political data accounts (incl. the Integrity Index), AI-simulation startups, AI showcase projects, platform rules | Claude | Mon 28 Sep | done (`docs/research/`) |
| C2 | Content plan: a menu of formats, cadence, tone; name and handles; on camera or voice-over | Content & site proposes, Matteo picks | Wed 30 Sep | draft for Matteo (`docs/content-plan.md`) |
| C3 | Accounts: Instagram professional (Creator) with Threads, X, Bluesky; TikTok and YouTube Shorts optional | Matteo | Fri 2 Oct | — |
| C4 | Making-of posts, starting with the test-bench findings | Content & site drafts, Matteo approves and posts | from Sat 3 Oct | — |
| C5 | Chart factory and daily post kit: slides (1080×1350), a 9:16 video, captions, alt text, an X thread | Content & site | Sun 4 Oct (the pilot makes internal kits daily) | — |
| C6 | Site at research.scaliastudio.dev/midterms: forecast, methods page, public scoring page | Content & site; Matteo sets up Cloudflare | Fri 9 Oct | — |
| C7 | Publishing and ethics review (Field Guide checklist); OSF pre-registration yes or no | Matteo with Claude | Sat 10 Oct | open task |
| C8 | Posting by hand: Meta Business Suite for Instagram, x.com's scheduler | Matteo | making-of from 3 Oct, forecasts from 12 Oct | — |
| C9 | Automated posting behind an approval flag: the Instagram API, and Buffer's free plan for X, Threads and Bluesky | Content & site; Matteo creates the apps and keys | 12–18 Oct | — |

## The pilot week (5–11 Oct, private)

The daily loop for Ohio, North Carolina and Texas:
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
| Engine (this one) | A1, A2, A4, A5, A8; the news spot-check page |
| Statistics | A3, A6, A7, A11 |
| Kev | B1–B4, then A9 and A12 |
| Content & site | C2, C4, C5, C6, C9 |
| Matteo | the list below |

Each session owns its own files. Edits to shared files (CLAUDE.md, CHANGELOG, pyproject) stay small. Four sessions at
once use up the Claude plan's limits faster. If the limits bite, pause Content & site before the others.

## What only Matteo can do

| When | What |
| --- | --- |
| Mon 28 Sep | News spot-check: about 100 labels, about 30 minutes |
| Wed 30 Sep | Pick the content formats and the project name |
| Thu 1 Oct | Put free API keys in `.env` (FEC, Census, FRED, EIA) and create a Redistricting Data Hub account |
| Fri 2 Oct | Create the accounts; give the Kev react-v1 verdict |
| Fri 9 Oct | Cloudflare: point research.scaliastudio.dev at the site |
| Sat 10 Oct | Publishing and ethics review; OSF yes or no; a production OpenRouter key with a monthly cap (the private pilot runs on the test key, which has about $8 left) |
| from 12 Oct | About 30 minutes a day approving posts |

GitHub access for the scheduled jobs: Claude sets up a deploy key that can only write to the private data repo
(approved 28 Sep).
