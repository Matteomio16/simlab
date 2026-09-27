# Roadmap to 3 November

Written 28 Sep 2026, 36 days before the election. It turns `docs/plan.md` (37-day plan) and `docs/infrastructure.md`
(§12 build order) into one task list with owners, and adds the content track. Update the Status column as things land;
decisions still go into CLAUDE.md §5.

## The shape

| Phase | Dates | Goal |
| --- | --- | --- |
| 1. Build | 28 Sep – 11 Oct | Three tracks in parallel: the engine, the models, content and distribution |
| 2. Pilot | 12 – 18 Oct | Ohio, North Carolina and Texas forecast daily, public and labelled "pilot", posted by hand |
| 3. Full run | 19 Oct – 3 Nov | 35 Senate races + ~40 House seats, early-vote data, weekly scoring, automated posting behind approval |
| 4. After | from 4 Nov | Score every race, run the blind track, publish what worked and what missed |

Fixed dates:
- Ohio early voting starts around 6 Oct.
- First public forecast: 12 Oct.
- Code freeze around 13 Oct. After it, changes go in a public changelog and both the old and new versions are scored.
- North Carolina early voting starts 15 Oct, Texas around 19 Oct.
- Election day: 3 Nov.

Fallback if the engine is behind on 8 Oct: launch Ohio alone on 12 Oct (the plan's "crude end-to-end forecast for
Ohio first") and add North Carolina and Texas during the pilot week.

## Where we are (28 Sep)

- **Done:**
  - the test bench, which found which model does which job (`docs/model-recipes.md`)
  - Kev fine-tunes on survey data (ces-v1 to v3)
  - test data: CES 2024, Census turnout, 46 real events with measured shifts, poll history
  - a prototype for labelling news
  - both GitHub repos, with the model-answer cache exported
- **In progress:** Kev trained on real news reactions (react-v1, in the Kev session).
- **Overdue:** daily snapshots of live data. They feed the forecast, and they are the only input the blind track may use
  after the election. Some sources can't be recovered later: news feeds, and early-vote and voter files, which are
  overwritten.
- **Also missing:** the free API keys (only OpenRouter's key exists) and the social accounts.

## Track A: the engine

| # | Piece | What it does | Due | Status |
| --- | --- | --- | --- | --- |
| A1 | Snapshots | Every 3 hours, saves raw polls, headlines, ratings, markets (benchmark only), early-vote files, FEC and economy data to the private data repo, with hashes | 30 Sep | not started |
| A2 | Download-now list | 538 Senate poll history; this week's NC and OH voter files; new House maps; the whyalwaysrose model (check its licence) | 30 Sep | partly (538 approval and generic ballot) |
| A3 | Starting levels | Each race's starting vote and range: poll average with pollster house effects, plus fundamentals. Also serves as the stats-only forecast the simulation must beat | 4 Oct | not started |
| A4 | News pipeline | Daily headlines → stories → which race → Jev asks "does this change anything?" → labels → a neutral 1–3 sentence event card, outlet names removed | 4 Oct | prototype (`news.py`) |
| A5 | Reaction harness | Asks each archetype how its support and turnout move, following the model-recipes rules. Sizes come from real data, not the model. Logs proposed vs applied changes | 8 Oct | asking, cache, spend cap exist |
| A6 | Filter | Daily update from new polls; weekly ensemble Kalman update from 19 Oct | 8 Oct | not started |
| A7 | Monte Carlo | 40,000 correlated draws → "wins 7 in 10 simulations", seat counts | 8 Oct | not started |
| A8 | Daily job | One command a day on GitHub Actions, with a run record, a spend line and an alert if a run is missed | 10 Oct | not started |
| A9 | Scoring | Weekly scores against the poll average, the markets, Cook and the stats-only forecast | 19 Oct | test metrics exist |
| A10 | Rehearsal | Two full private dry runs | 10–11 Oct | — |

Scaling risk: the House. Forty districts need archetype weights on the new 2026 maps. Fallback: House seats come from the
fundamentals map only, and agents run on the Senate only.

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
| B1 | Kev react-v1: trained on real measured shifts and design rules, never on GLM's answers | 1 Oct | building |
| B2 | Kev verdict on the 19 held-out events. Does it track size (GLM scores 0.26)? Are its errors independent of GLM's? Does Kev + GLM beat GLM alone? | 2 Oct | — |
| B3 | Freeze the routing table above | 3 Oct | draft |
| B4 | Kev serving on Modal (one GPU, scale to zero, one burst a day), if it passes B2 | 8 Oct | kit ready |

## Track C: content and distribution

| # | Step | Who | Due | Status |
| --- | --- | --- | --- | --- |
| C1 | Research: what the Integrity Index, forecasters (Silver Bulletin, Split Ticket, Cook...), AI-simulation startups and AI showcase projects post, and why it works | Claude | 29 Sep | running |
| C2 | Content plan: formats, how often, tone, name and handles, and whether Matteo appears on camera or does voice-over | Matteo picks from options | 1 Oct | — |
| C3 | Accounts: Instagram professional (Creator) with Threads, X, Bluesky | Matteo | 2 Oct | — |
| C4 | Build-in-public posts before launch, starting with the test-bench findings | Claude drafts, Matteo approves and posts | from 3 Oct | — |
| C5 | Chart factory and daily post kit: slides (1080×1350), a 9:16 video, captions, alt text, an X thread | Claude | 8 Oct | — |
| C6 | Site at research.scaliastudio.dev/midterms: forecast, methods page, public scoring page | Claude; Matteo sets up Cloudflare | 10 Oct | — |
| C7 | Publishing and ethics review (Field Guide checklist); OSF pre-registration yes or no | Matteo with Claude | 10 Oct | open task |
| C8 | Posting by hand: Meta Business Suite for Instagram, x.com's scheduler | Matteo | from 3 Oct | — |
| C9 | Automated posting behind an approval flag: the Instagram API, and Buffer's free plan for X, Threads and Bluesky | Claude; Matteo creates the apps and keys | 13–20 Oct | — |

## The pilot week (12–18 Oct)

The daily loop for Ohio, North Carolina and Texas:
1. data
2. news
3. reactions
4. filter
5. Monte Carlo
6. post kit
7. Matteo's review (about 30 minutes)
8. posts by hand

The stats-only forecast runs beside it.

We're ready to scale up if all of these hold by 18 Oct:
- the daily run finished without hand fixes on at least 5 of 7 days
- spend stayed within the pilot budget (about $5/month)
- every move in a forecast traces to a poll or a named event
- review and posting fit in 30 minutes a day

## The full run (19 Oct – 3 Nov)

- All 35 Senate races and about 40 House seats.
- Early-vote files: North Carolina from 15 Oct, Texas from about 19 Oct.
- The weekly filter and scoring every Monday.
- Divergence calls declared in advance.
- Posting automated behind the approval flag.
- A live page on election night.

## Who does what (proposal)

| Session | Owns |
| --- | --- |
| This one (test bench → engine) | A1, A2, A4, A5, A8; content research C1 |
| Kev session | B1–B4, then A9 and the early-vote data |
| New: statistical core | A3, A6, A7 |
| New: content and site | C2 options, C4, C5, C6, C9 |
| Matteo | the list below |

Each session owns its own files. Edits to shared files (CLAUDE.md, CHANGELOG, pyproject) stay small. Four sessions at
once use up the Claude plan's limits faster. If the limits bite, run the content session after the statistical core
rather than alongside it.

## What only Matteo can do

| When | What |
| --- | --- |
| 30 Sep | GitHub: create one fine-grained token so the scheduled jobs can write to the private data repo (5 minutes; steps provided) |
| 2 Oct | Put free API keys in `.env` (FEC, Census, FRED, EIA) and create a Redistricting Data Hub account |
| this week | News spot-check: about 100 labels, about 30 minutes, on a click-through page |
| ~2 Oct | Kev react-v1 verdict |
| 1–2 Oct | Pick the content formats and the name; create the accounts |
| by 8 Oct | Cloudflare: point research.scaliastudio.dev at the site |
| by 10 Oct | A production OpenRouter key with a monthly cap (pilot ~$5, full run ~$20–30, inside the $50 plan); the publishing and ethics review; OSF yes or no |
| from 3 Oct | About 30 minutes a day approving posts |
