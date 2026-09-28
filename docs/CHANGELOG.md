# Changelog: decisions and changes made in Claude Code

For Cowork to pick up. Newest first. Final decisions are also summarised in CLAUDE.md section 5.

## 2026-09-28 (Content & site): human, social voice

- **Matteo:** mention AI as little as possible; say "social simulation", "synthetic voters", "simulated voters". Model
  names and "AI" stay on the methods page and in Lab notes about a specific model. Every post still says "synthetic"
  or "simulated", so nobody takes the voters for real people. "Virtual interactions" waits until voters actually
  interact (no social-network layer yet). Lab notes 1–3 rewritten; caption checker now adds style notes. Vocabulary
  in `docs/publishing.md`.

## 2026-09-28 (Statistics session): starting levels for 2026 (roadmap A3), built to engine-design.md

- The engine design approved by Matteo arrived (commit e5df5e9). Statistics' review asked for three clarifications,
  and the Engine session adopted them (commit 271af29):
  - the dials are applied once;
  - units are stated;
  - each story counts once, from first_seen.
- `simlab/levels.py` (`python -m simlab.levels`) was built test-first (`tests/test_levels.py`, 15 tests) and writes
  `levels.json` to `simlab-data/derived/<date>/`. For each race:
  - election-day margin, SD and poll weight;
  - the poll-only margin (the forecast's "poll_avg" benchmark);
  - fundamentals, with lean, incumbency and candidate-effect components.
- Method, as fitted: a relative Kalman average on house-effect-corrected polls, then fundamentals with D10–D12, then the
  inverse-variance blend.
  - Candidate records come from MIT Senate and at-large House races, plus `simlab/statewide_extra.json`: Cooper,
    Paxton and Moody's governor and attorney-general races, with Wikipedia revision ids.
  - Incumbency comes from the Wikipedia status column: running counts in full, an interim appointee nominated counts
    half, and an open seat counts zero. `polls.Race` now carries `incumbent` and `status`.
- First run (snapshot 28 Sep 09:41): 35 races, 28 with polls, poll weights 0.4–0.7. The 7 races without polls are pure
  fundamentals.
- Correction to stats-groundwork §2.3: the 2025–26 likely-voter gap of +1.0 is on raw margins. On the model's two-party
  scale it is median +0.2, mean +1.2, and the levels use the two-party median, recomputed daily.
- `calib.national_house_vote()` was split out of `senate_table`. `calib.house_effects` now copes with a batch that has
  no sponsored polls. The calibration outputs are unchanged (re-run checked).

## 2026-09-28 (Statistics session): poll table (roadmap A3, first part)

- `simlab/polls.py` (`python -m simlab.polls`) was built test-first (`tests/test_polls.py`, 28 tests). It reads one
  snapshot folder: VoteHub, the 35 Wikipedia race pages and the overview page.
- It writes the Senate, generic-ballot and approval poll tables to `data/polls/<date>_<time>/`, gitignored until
  engine-design.md sets the place. A meta file records the snapshot time, Wikipedia revision ids, source counts and
  licence.
- Rules as agreed:
  - nominees come from the overview page; the main challenger is the notable independent where there is one (NE, ID,
    SD, MT);
  - Wikipedia tables are picked by nominee names;
  - versions of one poll are averaged within a population, likely voters first;
  - sponsor and partisan flags come only from VoteHub (D1);
  - margins are two-party;
  - source disagreements over 1 point are flagged.
- First run (snapshot 28 Sep 09:41):
  - 35 races and 355 Senate polls: 186 in both sources, 129 Wikipedia only, 40 VoteHub only;
  - 12 disagreements, mostly different versions of one poll (Montana's three-way ballot against a head-to-head, for
    example);
  - 441 generic-ballot and 836 approval polls.
- Not yet done: first-seen dates across snapshots (for the blind track), ranked-choice handling for Alaska, and
  three-way handling for Montana.

## 2026-09-28 (Engine session): engine design agreed; news spot-check, labels, attention, backlash test

- **Engine design approved by Matteo:** `docs/engine-design.md`, the contract between the sessions.
  - GLM gives the news reactions in the pilot.
  - Kev runs in shadow mode: it answers the same questions every day, and its answers are scored but never applied.
  - The Kev session trains react-v2 on more real events, with a stricter bar for what counts as a clear shift and never
    on GLM's answers. It costs about $3 of Modal credit.
  - React-v2 joins the numbers on 12 Oct only if, on held-out events, its direction is at least as good as GLM's, its
    size-tracking is above zero, and GLM and Kev averaged beat GLM alone.
- **Matteo's rule: only people who can move count.** A reaction applies only to the share of each group that can still
  change: the persuadable share `pi` for vote choice and the mobilisable share `mu` for turnout, both estimated from CES
  pre- and post-election waves. Voters sure of their choice don't change the outcome, and mobilising a group that already
  votes at 95% barely changes turnout (engine-design §3).

- **News spot-check so far** (Matteo, 16 of 100 stories; more to come):
  - Jev matched his answers on 54 of 63 labels, GLM on 50.
  - Both models overrate how much attention a story gets: on 6 of 16 they said "some" where he said "very little".
  - Both models missed one story in the way his rule below describes. They labelled "Trump ramps up noncitizen voting
    prosecutions" as helping Republicans; he said it could cut either way.
- **Decided by Matteo:**
  - Jev labels the news: relevant or not, event type, and who it helps on its face.
  - Attention (salience) comes from coverage data: how many outlets carry the story, and lookups. The model's guess only
    breaks ties.
  - The spot-check can stop short of 100 stories.
- **Matteo's rule for news effects:** a story's effect is how each voter group reacts to it, including backlash and
  mobilisation, not who it helps on paper. For example, a $30M super PAC for the Republican can fire up Democrats.
  - Approved: a wording test comparing the current reaction question with one that asks how that kind of person feels
    about the news itself.
  - It runs on the real events and on about 15 everyday stories where backlash is plausible.
  - The new wording is adopted only if accuracy on the real events holds.
- **Kev react-v1** (Kev session, commit 35271c8): it learned the rules (ignore irrelevant news, flip on a party swap)
  but not how big an event's effect is. On the 19 held-out events, averaging it with GLM made the error worse (2.61 vs
  2.32 points). So it runs in shadow mode for now (see above).

## 2026-09-28 (Content & site): label line, visual identity, race cards

- **Label line (Matteo):** every image and caption now says "Social simulation, not a poll" instead of "AI-simulated
  voters, not a poll". Captions still say in the body that the voters are AI (the Axios/Aaru lesson). The Field Guide
  and infrastructure snapshots still show the old wording.
- **Visual identity (Matteo):** Lab Notebook by default, Riso Print now and then (`docs/creative-directions.md`).
- New recurring elements: the logomark (a ballot box holding a grid of simulated voters), the run stamp with the
  forecast's hash, and the race tag (the state outline filled with simulated voters in the race's split). Five race-card
  layouts drafted (`simlab/publish/racecards.py`), layout choice pending. State outlines from the Census Bureau's 2024
  1:20m boundary file (downloaded with Matteo's OK; raw file in `data/`, outlines in `simlab/publish/states.json`).

## 2026-09-28 (Statistics session): no correction for the polls' recent Democratic lean; poll table started

- Decided by Matteo: no fixed correction for the polls' recent Democratic lean. The backtest's margins leaned D by
  +2.0, +3.9, +0.9 and +3.3 in 2018–2024, but Senate polls' yearly misses swing both ways over 1998–2022, and the
  national error term covers a miss of that size. Summarised in CLAUDE.md §5.
- Matteo OK'd building the poll table now, before the engine design is agreed. It reads the snapshots and is built
  test-first; its output format will be aligned with `docs/engine-design.md` when that lands.

## 2026-09-28 (Statistics session): backtest extended to 2024

- With Matteo's OK, `simlab.statsdata` fetched 538's 2024 generic-ballot poll list from the Wayback Machine (3 Dec 2024
  copy, 735 polls, 0.33 MB). The backtest now covers 2018–2024: 122 races. California's 2022 and 2024 specials are
  left out, because each had the same two candidates as the regular race on the same ballot.
- **2024** (no 538 comparison: their scoring file stops at 2022). Brier at 35 / 14 / 1 days: ours 0.041 / 0.036 /
  0.034, polls only 0.048 / 0.041 / 0.036, fundamentals only 0.051 / 0.052 / 0.053. One wrong call on eve:
  Pennsylvania (we gave Casey 83%; McCormick won by 0.2).
- **2018–2022 against 538** barely moved (the error sizes now also learn from 2024). Eve 0.040 against 538 deluxe
  0.048; 35 days out 0.042 against 0.048.
- **Our margin leaned Democratic every cycle** (+2.0, +3.9, +0.9, +3.3), inheriting the polls' tilt. Not corrected: the
  polls' yearly misses swing both ways over 1998–2022, and the national error term covers a miss of that size.
- Per-race output is now `runs/backtest_senate_2018_2024.csv`; the 2018–2022 file is removed. Details in
  stats-groundwork §5.11.

## 2026-09-28 (Statistics session): backtest of the stats-only chain, Senate 2018–2022

- `python -m simlab.backtest` (new `simlab/backtest.py`; Matteo's go-ahead) runs the chain of stats-groundwork
  §5.1–5.4 as it would have run 35, 14 and 1 days before each election. It covers 91 Senate races (D v R finalists;
  Georgia 2020 left out) and scores them against the results and against 538's lite, classic and deluxe forecasts
  from the same days.
- No peeking:
  - polls count only once 538 had logged them;
  - house effects use that cycle's polls known by then, with priors from earlier cycles;
  - fundamentals, the generic-ballot correction and the error sizes are refitted without the tested cycle.
- Results (Brier; lower is better):
  - eve 0.039 for ours, against 538 deluxe 0.048, classic 0.053 and lite 0.054;
  - 35 days out 0.042 against 0.048;
  - competitive races on eve 0.096 against 0.116;
  - average margin miss on eve 4.4 points, against 4.9 for 538 deluxe.
- By cycle: worse than 538 deluxe in 2018 (0.061 v 0.052); better in 2020 (0.031 v 0.046) and 2022 (0.024 v 0.044).
  Gains concentrate in a few races. The model's shape was chosen after seeing these years, though its coefficients
  weren't fitted on the tested year.
- Reading: the stats-only chain is at least in 538's league; three elections can't show a real edge. Details in
  stats-groundwork §5.11. Per-race output in `runs/backtest_senate_2018_2022.csv`.
- `calib.house_effects` takes prior means; `calib.senate_table` keeps the special-election flag. The calibration
  outputs are unchanged (re-run checked).

## 2026-09-28 (Statistics session): decisions D9–D13; approval test; pollster house-effect priors

Decided by Matteo, as recommended in `docs/stats-groundwork.md` §8 (CLAUDE.md §5 updated):
- **D9:** sponsored polls are shifted against their sponsor, on top of half weight. Estimated together with the
  pollster house effects, the shift is +2.2 (D sponsor) / −2.9 (R sponsor) on 2018–24 polls, re-estimated on 2026 polls.
  The raw 4.7 would double-count partisan pollsters' own lean.
- **D10:** the candidate effect uses the fitted share, 0.38 of the last statewide over-performance.
- **D11:** the lean uses the fitted weights, 0.62 × latest + 0.26 × previous presidential margin.
- **D12:** where the generic ballot feeds the fundamentals, it is lowered by its historical overstatement of Democrats
  (2.8, spread 2.8).
- **D13:** Gallup approval fetched from the American Presidency Project's data sheet (15 president tabs, about 60 KB,
  into `data/history/`, via `simlab.statsdata`).

Results (`python -m simlab.calib`):
- **Approval test (D4) passes, modestly.** The test predicts the national House vote from the final generic ballot,
  holding out each cycle 1998–2022. Adding net approval (toward the president's party) cuts the error from 3.17 to
  2.80 over all cycles and from 3.21 to 3.09 over midterms. Fit: `0.69 × generic ballot + 0.084 × net approval − 2.3`.
  It enters the fuller version's national environment; the pilot keeps the generic ballot minus 2.8.
- **Pollster house effects, 2018–24** (6,054 polls; each against the other pollsters' consensus in the same race,
  shrunk toward zero). They are written to `simlab/house_effect_priors.json` as priors for the 2026 poll average.
  - Lean R: McLaughlin and Rasmussen −5.1, AtlasIntel −3.1, InsiderAdvantage −2.9, Trafalgar −1.8.
  - Lean D: Marist +1.7, CNN/SSRS +1.6, Quinnipiac +1.1.
  - Coverage: 78% of VoteHub's 2025–26 polls come from pollsters with a track record. New ones start at no lean.

## 2026-09-28 (Content & site): chart factory approved; Lab notes 1–3 drafted

- Matteo approved matplotlib for every post image and video frame (instead of the infrastructure doc's Altair +
  vl-convert split), and the new dependencies matplotlib 3.11 and imageio-ffmpeg 0.6. Fonts, on his brief of "the best
  ones for design, not vibe-coded": Newsreader, Libre Franklin and IBM Plex Mono (SIL Open Font License, Google Fonts'
  repository), instead of Inter.
- `simlab/publish/`: canvas with the label strip on every image, charts, caption rule check, and the Lab notes 1–3
  drafts (`kits/`, gitignored, awaiting Matteo's approval). Design and colours in `docs/publishing.md`.

## 2026-09-28 (Statistics session): statistics layer calibrated on past elections

- `python -m simlab.calib` (new `simlab/calib.py`) fits the sizes the filter, blend and Monte Carlo need and writes
  `simlab/stats_params.json`. Inputs: 538's polls with results (1998–2022), 538's poll lists (2018–24) and the MIT
  results. Details in `docs/stats-groundwork.md` §5.10; two-party margins throughout.
  - **Poll errors** (last three weeks):
    - Senate polls share a national miss of about 3 points a year.
    - Race-level error is 3.5 for well-polled close races and 5.9 with fewer than 5 polls.
    - Noise beyond sampling is 1.2–3.2.
    - Shared errors split into state 2.6, region 1.1 and race-only 3.7.
  - **Drift:** Senate races about 0.5 points a day (0.8 in the 2018 and 2022 midterms); generic ballot 0.3.
  - **Fundamentals** (Senate 2012–24): margin = 0.62 × lean(latest) + 0.26 × lean(previous) + 5.1 × incumbent + 0.71
    × national House vote + 0.38 × prior over-performance + 2.8. The error, predicting each year from the others, is
    8.0 for races predicted within 15, and 5.6 in 2024.
  - **Blend:** the best election-day weight on polls for well-polled close races was 0.82 (2006–22). The
    inverse-variance formula with the fitted sizes gives about 0.8.
  - **Other findings:** the final generic-ballot average overstated Democrats by 2.8 on average (1998–2022).
    Sponsored polls lean about 4.7 points toward their sponsor.
- New open choices for Matteo, in stats-groundwork §8:
  - D9: shift sponsored polls against their sponsor;
  - D10: fitted candidate share of 0.38 instead of half;
  - D11: fitted lean weights;
  - D12: generic-ballot correction for unpolled races;
  - D13: fetch past approval data for the approval test.
- Matteo downloaded the MIT House file by hand (it sits behind a Dataverse guestbook); `statsdata` now registers
  hand-downloaded files. Matteo OK'd the CLAUDE.md §5 summary of the 28 Sep decisions.

## 2026-09-28 (Statistics session): Matteo's decisions on the statistics layer; downloads

Decided by Matteo, all as recommended in `docs/stats-groundwork.md` §8:
- **Partisan polls** (half weight) are those sponsored by a party, campaign or partisan group: VoteHub's flag, 538's
  rule. Wikipedia's "(R)"/"(D)" pollster tags are kept as a field only, since house effects already correct a
  pollster's lean.
- **Expert ratings** stay out of both the headline and the stats-only chain (benchmark only), so "beat Cook" stays a
  clean test. They may still be used to pick which House seats get the full treatment.
- **Senate control:** the headline is "Republicans hold 50+". Independents who win (Osborn, Achilles, Bengs, Bodnar)
  are shown in their own colour. "Democrats + independents who caucus with them reach 51" is the second line.
- **Approval** enters the national environment only if it passes a leave-one-cycle-out test on past midterms. The
  pilot uses the generic ballot alone.
- **Candidate effect:** half of a nominee's own over- or under-performance in their last statewide race of the past 12
  years, rule-based and logged.
- **Versions within one poll** (leaners, third-party names) are averaged within the chosen population (LV, else RV,
  else A).
- **Attribution:** any published poll table built on Wikipedia data is CC BY-SA with attribution; the methods page
  carries a sources line.

Downloads (approved), via the new `simlab/statsdata.py` into gitignored `data/results/` and `data/history/`:
- 21 files, 23.7 MB, each with URL, size, SHA-256 and fetch time in `data/stats_downloads.json`:
  - MIT president and Senate results 1976–2024;
  - 538 `raw_polls` (1998–2023) and pollster ratings;
  - 538 Senate, House and governor poll lists (2018–22 "historical", plus the 2024-cycle files from post-election
    Wayback copies);
  - 538 Senate forecasts 2008–22;
  - The Downballot's 2024 and 2020 presidential results for all 435 districts on the 2024 lines and on the 2026 lines.
- The MIT House file needs a Dataverse guestbook form (name, email), so Matteo downloads it by hand.
- Map and ACS files wait for the Redistricting Data Hub account and the Census key.

## 2026-09-28 (Statistics session): statistics groundwork (research only, no decisions)

- `docs/stats-groundwork.md` covers the inputs and their shapes, what is on disk, and the downloads to approve, with
  sizes. It also sets out the methods for the pilot (1–2 Oct) and the fuller version (12 Oct): poll table, starting
  levels, voter-group weights, daily and weekly filter, Monte Carlo, House.
- Findings:
  - Wikipedia has about 350 polls for the actual nominee pairs and VoteHub 239. VoteHub misses most polls in thinly
    polled races, so the poll table merges both.
  - The largest table on a page can be an obsolete or hypothetical matchup (Maine, Florida), so tables are picked by
    nominee.
  - About half the Wikipedia polls carry an "(R)"/"(D)" pollster tag, against 17% of VoteHub entries flagged partisan
    by sponsor.
  - Likely-voter screens lean D this cycle (+1.0 median over 23 paired releases) after leaning R in 2018 and 2022.
- Open decisions for Matteo are in its §8. Note for engine-design.md: the sensitivity dial enters linearly, so the
  weekly update can be an exact Kalman update.

## 2026-09-28 (Kev session): snapshotter (roadmap A1)

- Matteo asked this session to build the snapshotter unless the data session already had it. A1 was "not started", no
  snapshot code existed, and the Engine session wasn't running, so the Kev session took it over (roadmap updated).
- `simlab/snap.py`: every run saves raw files to `simlab-data/snapshots/YYYY-MM-DD/HHMM/<source>/<name>.gz` plus a
  `manifest.json` (URL, UTC fetch time, HTTP status, raw size, SHA-256, or the error). Gzip has a fixed header, so a
  file that hasn't changed is byte-identical and git stores it once. Sources, all free with no key:
  - polls: VoteHub, every poll;
  - Wikipedia: 38 pages (the 35 Senate race pages, the Senate and House overviews with ratings and generic ballot,
    the approval polling page), wikitext with revision ids;
  - markets, benchmark only: PredictIt, Kalshi and Polymarket (Senate and House control and every Senate race);
  - news: Google News RSS and GDELT headlines for the three pilot races and national;
  - pageviews for the six pilot candidates.
  The script uses only `requests`, and logs print sizes and errors, never data, because the job runs in the public repo.
- First snapshot run by hand, 28 Sep 00:36 UTC: 48 of 51 files (GDELT rate-limited 3 queries), 9.3 MB raw, 1.5 MB
  stored, committed to the data repo.
- `.github/workflows/snapshot.yml` runs every 3 hours at :17 UTC (shallow partial clone, rebase-and-retry push). It was
  switched on 28 Sep with Matteo's OK: a deploy key that can write only to `simlab-data` (title "simlab snapshot job
  (GitHub Actions)"), stored as the public repo's secret `SIMLAB_DATA_DEPLOY_KEY`; no local copy was kept. FEC, FRED
  and EIA join once their keys exist; early-vote aggregates are A12.

## 2026-09-28 (Content & site): content choices

- Content plan in `docs/content-plan.md`. Matteo's picks: formats A–F (daily forecast, "every future" dot video, why it
  moved, the receipts, lab notes, early-vote watch); on camera twice (launch 12 Oct, results 4 Nov) and voice-over for
  the weekly Reels, no AI presenters or voices; Instagram, X, Threads and Bluesky only (no TikTok, YouTube Shorts or
  LinkedIn).
- Name: **NotAPoll.org** (Matteo, 28 Sep). Handles: @notapoll.org on Instagram and Threads, @notapoll on X (no dots
  allowed), @notapoll.bsky.social on Bluesky until the domain is bought ("maybe later"), then @notapoll.org. All were
  free on 28 Sep. Until the domain is owned, images show the wordmark "NotAPoll" and the real address
  research.scaliastudio.dev/midterms, never "notapoll.org".

## 2026-09-28 (night): Kev reaction fine-tune react-v1 (Matteo's go-ahead)

- Data (`python -m simlab.kevreact`, design agreed with the test-bench session; full rules in the module docstring):
  1,632 training + 288 calibration records. 11 events2 events with a clear shift and 15 with none, 40 real CES
  respondents each; 60 new irrelevant news items; 20 new party-swap templates. Targets: 4% background movers, plus
  m = min(0.04 × points × g, 0.5) moving toward the side the event helps. g is a Field Guide prior by party ID
  (strong 0.2, not very strong 0.6, lean 1.0, independent 1.6, weighted mean 1). Turnout: no-change examples only.
  Development = the null, mirror and events tests' exact items, scored offline through a lookup asker.
- Run: H100, 2 epochs, 1,000 replay records, 23 min, about $2.30. No forgetting on Kev's public checks (0.862).
- Results, raw probabilities (temperature 1):
  - Null test: P(no change) 0.961 support / 0.964 turnout, mean |shift| 0.003 / 0.006. Base Kev failed it (0.77).
  - Mirror test: flip correlation 0.961, sign flips 100%, lean +0.002. Best of any model (Jev 0.69, GLM 0.45).
  - Events test (19 held-out): rank correlation 0.53 and signs right on 10 of 13 clear events; GLM 0.81 and 13 of 13.
    Size-tracking (|pred| vs |measured|) 0.00, against GLM 0.29 and Jev 0.28. Error after one fitted scale 3.26 points
    (GLM 2.32). Errors correlate 0.75 with GLM's; averaging with GLM makes it worse (2.61).
  - Reading: from a few hundred records Kev learns clean rules and applies them to unseen items (irrelevant news means
    no change; swapping the party flips the reaction). 11 noisy real events can't teach which new events matter or
    how much, so on real events it predicts almost no movement. Reactions stay with GLM + Jev.
- Modal spend in September: $8.45 of the $30 credit (the summary API revised the earlier $6.94 reading to $6.15).

## 2026-09-28 (early morning, test bench): real events (events2), news labels, a correction

- **Correction:** the per-event-type scale does not hold up. Fitted on the 46 new events and applied unchanged to the
  19 held-out events, it gives no gain over one scale per model (GLM error 3.04 vs 3.05 points; Jev 3.33 vs 3.33;
  "no change" 3.56). The earlier 2.49 -> 1.91 gain was overfitting to 3-6 events per type. Don't use it.
- **Models give direction, not size.** On events2, both get the direction right for 92% of events that moved opinion by
  1 point or more. Jev's predicted size does not track the real size at all (rank correlation -0.03; it predicts
  the same size for no-effect and clear-effect events). GLM's barely does (0.26). Fitted points-per-unit differ by
  event set (GLM 3.4 on events2 vs 12.6 on the famous 19), so any fixed scale is unstable. Sizes must come from real
  data (the filter, per state), and this is where a Kev trained on measured shifts could add something GLM can't.
- **Exposure wording (Field Guide rule 5) doesn't help:** predicted shift = P(heard about it) x how it landed was slightly worse than the direct question for GLM on every measure (direction on events2 85% vs 92%, size-tracking 0.09 vs 0.26, error on the 19 3.13 vs 3.05); for Jev it helped direction on the famous 19 (87% vs 73%) but not on events2 or size. P(heard) doesn't track event size (-0.19 to 0.33). Keep the direct question. Rules collected in `docs/model-recipes.md`.
- Jev and GLM errors on events2 correlate 0.94 (0.88-0.97 across hosted models on the 19): averaging them does not
  cancel errors.
- **events2** (`simlab/events2.json`): 46 events, 45 measured, 10 with |z| >= 1.5; 11 pass the directional filter
  (|z| >= 1, raw and detrended agree, no confounders) and 15 are no-change (|z| < 0.5). Nationscape party, turnout-intent
  and vote-margin shifts for 12 events are noise (2 of 96 reach |z| >= 2), so Kev's turnout gets only no-change
  examples and party responsiveness stays a Field Guide prior.
- **News labels** (480 stories, Google News RSS, Jev and GLM): same event type 70%, same "helps" 74%. Both change
  "which side does this help" with the outlet name alone: the same headline attributed to MSNBC instead of Fox News moves
  P(helps D) - P(helps R) by +0.30 for GLM (top label flips on 41%) and +0.15 for Jev (15%). The engine must strip
  outlet names; Kev training gets source-swap pairs if a source is ever shown. Model salience does not track coverage
  breadth (r ~ 0.05; weak test, most stories have 1-3 outlets).
- **Kev reaction targets** (design agreed with the infrastructure session, awaiting Matteo): 11 directional + 15 no-change
  events; movers share m = min(0.04 * s * g, 0.5), s in points of people moving toward D, g = Field Guide party
  responsiveness prior (support only); 4% background movement; rule records (new irrelevant news, new mirror pairs);
  offline scoring with the test bench's metrics; report Kev's error correlation with GLM.

## 2026-09-27 (late night, test bench): fidelity turnout targets switched to the Census CPS

- Matteo approved downloading the CPS November supplements (2024, 2022, 2018; census.gov, public, no account); they are
  in `data/cps/` (gitignored). `cps.py` (infrastructure session) turns them into citizen respondents with self-reported
  turnout, non-answerers dropped (Hur and Achen) and each state reweighted to its official VEP turnout.
- `cells.json` (first fidelity test) and `cells2.json` (wider test) now take turnout targets and the turnout regression
  baseline from CPS 2024: 77 national, 8 OH, 11 NC, 24 TX turnout cells; turnout is asked only on demographic cells
  (CPS has no party ID). Vote and opinion targets stay CES; archetypes unchanged. Weighted CPS turnout: national 0.651,
  OH 0.654, NC 0.707, TX 0.568. All models re-scored (cached answers reused; new cells asked fresh).
- CLAUDE.md section 5 updated (Matteo's OK): fidelity turnout now from CPS; the hosts line now matches the current
  pins (it still listed DeepSeek on InferenceNet).

## 2026-09-27 (late night): Kev ces-v2 results; Census CPS turnout; ces-v3 test

- Kev `ces-v2` (H100, 2 epochs, 1,000 replay records, ~21 min, $1.52). 1,356 training records from 48 states: 2024
  demographic cells, party-ID × white/non-white × degree strata and 2020-vote cells (2024 vote), plus 2018/2022
  turnout and the 2022 House vote from the CES cumulative file. Held-out OH / NC / TX, weighted TVD against real shares
  at temperature 1.0 (`python -m simlab.kevscore ces-v2`):
  - 2024 vote, demographic cells: 0.070 / 0.094 / 0.090, worse than ces-v1 on the same cells (0.049 / 0.078 / 0.078).
  - New no-model baseline, the same cell pooled over the 48 training states: 0.055 / 0.079 / 0.138. It beats Kev in
    OH and NC; Kev wins in TX (regression baseline 0.047 / 0.093 / 0.138).
  - Party strata 0.032 / 0.034 / 0.040 (pooled 0.027 / 0.027 / 0.044); 2020-vote cells 0.041 / 0.028 / 0.048 (pooled
    0.031 / 0.022 / 0.045); 2022 House vote 0.067 / 0.087 / 0.074 (pooled 0.066 / 0.077 / 0.156).
  - Turnout outputs not used: trained on CES turnout, which tracks voter-file matching.
- New `simlab/cps.py`: Census CPS November Voting and Registration Supplements 2018, 2022 and 2024 (downloaded by the
  test-bench session with Matteo's OK) → `cps.respondents(year)`, adult civilian citizens with `ces.load`'s cell
  fields. Hur and Achen (2013): people who didn't answer the vote question (14% in 2024) are dropped, then voters and
  non-voters are reweighted per state so every state matches its official VEP turnout. Checks: the 2018 fixed-width
  reader matches the techdoc's counts; the Census convention reproduces the published 53.4% / 52.2% / 65.3%. Dropping
  non-answers instead of counting them as non-voters moves groups by 0.03 at most (2024 ages 18-29: 0.488 vs 0.504).
  `ces.STATE_NAMES` moved from `kevdata.STATES`.
- Kev `ces-v3a` / `ces-v3b` ($2.22 for both; H100, 2 epochs, 1,000 replay records): ces-v2's records with CPS turnout
  on demographic cells only (v3a) or with no turnout questions (v3b); same records, option orders and split
  (`python -m simlab.kevdata v3`). Held-out cells that every run answers with the same target, OH/NC/TX pooled,
  weighted TVD, 95% intervals from resampling cells (`python -m simlab.kevscore ces-v1 ces-v2 ces-v3a ces-v3b`):
  - 2024 vote, demographic cells (37): v3a 0.064, v3b 0.064, v1 0.070, v2 0.085; pooled baseline 0.102. v3a and v3b
    tie (0.000 [−0.011, +0.011]); both beat v2 (v2 − v3b +0.021 [+0.002, +0.039]); v3 − v1 −0.005, not significant.
    By state (v3b): 0.052 / 0.085 / 0.063 against pooled 0.055 / 0.079 / 0.138 and regression 0.047 / 0.093 / 0.138.
  - Party strata (60 cells): v3b 0.031, v3a 0.032, v2 0.037, pooled 0.035. 2022 House vote (42): v3b 0.061, v3a
    0.065, v2 0.075, pooled 0.112. 2020-vote cells (27): v3b 0.038, v3a 0.038, v2 0.041, pooled 0.036.
  - Reading: turnout questions don't interfere with the vote task (v3a = v3b), and the extra record types didn't dilute
    it (v3 at least as good as v1); ces-v2's drop came from the CES turnout targets. One multi-task Kev is fine so
    far. Single training runs, so run-to-run noise isn't measured.
  - CPS turnout, 2024 (v3a): 0.054 / 0.041 / 0.078 against pooled 0.040 / 0.056 / 0.055 and regression
    0.044 / 0.051 / 0.061. Kev doesn't beat the simple baselines on turnout levels.
  - Modal spend in September: $6.94 of the $30 credit.

## 2026-09-27 (night): Kev ces-v1 results; serving and Modal budget rules

- Repos created: `github.com/Matteomio16/simlab` (public, full history, scanned for keys and personal data first) and
  `github.com/Matteomio16/simlab-data` (private; first off-laptop copy of the 34,099 cached model answers, the spend
  ledger and the ces-v1 data).
- Kev `ces-v1` (H100, 2 epochs, ~27 min, $3.08 including the pre-flight). Held-out OH/NC/TX cells, weighted TVD
  against real shares, raw probabilities: vote 0.049 / 0.078 / 0.078, turnout 0.062 / 0.067 / 0.042. Regression
  baseline: vote 0.047 / 0.093 / 0.138, turnout 0.071 / 0.059 / 0.036. Base Kev: 0.16–0.26. Best hosted LLM (GLM):
  0.08–0.12. Kev's own report: accuracy on the most likely answer 0.73 → 0.84 (significant), no forgetting on its
  public regression set (0.862 → 0.871).
- Kev's calibration step fits a temperature to hard labels (0.30 here), which sharpens probabilities away from
  population shares (TVD 0.13–0.20); fitted against the soft targets the best temperature is 1.02, so the raw model is
  already share-calibrated. The kit now takes `KEV_SERVE_TEMPERATURE` (1.0 = raw) for serving.
- Kit serving settings (Matteo's decision): `KEV_SERVE_MAX_CONTAINERS` (default 1) and `KEV_SERVE_IDLE_S` (default
  60 s, was 300); one batch of Kev questions a day. Modal budget: October keeps at least $18 for serving; fine-tuning
  uses September's expiring credit first, then at most $12 in October.

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

## 2026-09-27 (night, test bench): batching, wider fidelity, GLM controls, turnout data problem

- **Batched asking** (`askers.ask_many`): Jev bills ~430 tokens per request + ~50 per question and answers each
  question on its own, so all questions and their order variants go in one request (A/B on 30 personas: answers
  unchanged, ~3× cheaper, 20× faster). GLM gets one compact prompt per order variant (questions first for prompt
  caching, persona last, percent lists back). Text models read the whole prompt, so vote-choice questions must not
  share a prompt with turnout ("how did this person vote" implied they voted and pushed turnout answers up).
- **GLM hosts:** InferenceNet fp4 plus DeepInfra fp4 as overflow (InferenceNet kept returning upstream 429s).
- **Wider fidelity test** (`docs/fidelity2.md`; 14 CES 2024 items, 132 demographic cells incl. OH/NC/TX and 138
  national cells with party ID; 3,461 answers per model; Jev $0.024, GLM $0.054):
  - Average TVD: demographic cells Jev 0.36, GLM 0.14, regression 0.07; party-ID cells Jev 0.25, GLM 0.16,
    regression 0.05. The regression wins every item, so levels stay statistical.
  - Jev's multi-option answers are label confidence (approval and economy TVD 0.6–0.8); fine on yes/no items and on
    vote once party ID is in the persona.
  - GLM flattens partisan differences on evaluative items: Democrats approving of Biden, real 83% vs GLM 44%
    (Republicans 4% vs 15%); Democrats saying the economy got better 53% vs 18%. Vote and hot-button issues are close
    (Democrats voting Harris 96% vs 93%; Republicans backing the wall 93% vs 76%). Party-specific heterogeneity has to
    come from data (or a Kev trained on it), not from GLM.
  - Jev and GLM errors correlate 0.6–0.96 on most items; averaging helps only for vote with party ID (errors
    anti-correlated) and a few yes/no items.
- **GLM controls (from existing runs):** a fixed order correction removes only ~2/3 of GLM's one-order lean (mirror
  −0.124 → −0.045 vs −0.006 asked both ways), because the order effect grows with the reaction; keep asking both
  ways. Jev needs no scale averaging. A points-per-unit scale per event type cuts GLM's leave-one-out event error from
  2.49 to 1.91 points (shocks/crises ~24 per unit, scandals ~7, debates ~9); the news labels' event type selects it.
- **All hosted models share the event blind spots:** errors on the 19 events correlate +0.88 to +0.97 and averaging
  any pair never beats GLM alone; all under-react to structural shocks (COVID rally, Jan 6, Afghanistan, fuel spike)
  and over-react to media spectacles (Access Hollywood, debates). Matteo's rule: Kev's reaction training comes from
  real measured shifts and design rules, never from GLM answers, so Kev can be an independent second opinion.
- **Turnout data problem:** CES validated turnout tracks voter-file match rates (corr 0.99 across cells); 18-29 Black
  men without a degree: match 0.09, turnout 0.05. Turnout targets in cells.json, cells2.json and Kev ces-v1/v2 inherit
  it. Proposal pending Matteo's OK: Census CPS November supplements (2018, 2022, 2024), reweighted to official state
  VEP turnout (`simlab/cps.py`, other session), with CES kept for vote choice and opinions.
- **Ownership (agreed with the infrastructure session):** this session owns `simlab/events2.json` (expanded real
  events; the original 19 stay the held-out test) and `simlab/news.py` + `data/news/`; the other owns `cps.py`, Kev
  datasets and training. AllSides ratings (CC BY-NC 4.0, 2019 community copy) stay in `data/news/`, never in the public
  repo.
