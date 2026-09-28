# Statistics groundwork

Written 28 Sep 2026 by the Statistics session. It covers where each input comes from, what shape it has, what is
already on disk, and the simplest methods that meet the dates: a pilot version by 1–2 Oct and the fuller version by
12 Oct. Matteo took the decisions in §8 on 28 Sep, all as recommended, and approved the downloads in §4. File formats
between sessions will come from `docs/engine-design.md`; §9 lists what this work needs from it.

No forecast numbers appear here. Counts and dates describe the inputs; the defaults in §10 are starting assumptions
that the history fits in §5.10 replace.

Words used below:
- **Margin**: the Democrat's share of the two-party vote minus the Republican's, in points (D+3 = +3). Where the main
  challenger is an independent, that candidate takes the Democrat's place (§7).
- **House effect**: a pollster's steady lean compared with other pollsters.
- **Fundamentals**: what we expect before reading race polls: the state's partisan lean, the national mood,
  incumbency and the candidates.
- **Kalman filter**: a running average that knows how noisy each poll is and how fast opinion can drift. Each new
  poll updates both the estimate and its uncertainty.
- **Draw**: one simulated election in the Monte Carlo.

## 1. Summary

1. **Polls:** about 350 general-election polls sit in the Wikipedia tables for the actual nominee pairs, most of them
   in nine races (TX 42, NC 37, MI 37, OH 25, NH 24, IA 22, AK 22, GA 19, ME 17). Seven races have none: CO, DE, IL, NJ,
   OR, WV, WY. VoteHub has 239 entries for the nominee pairs, but it misses most polls in thinly polled races
   (Nebraska 1 against Wikipedia's 12, South Dakota 0 against 8). Neither source is complete alone, so the poll table
   merges both: VoteHub for its structured metadata, Wikipedia for coverage.
2. **Wikipedia traps:** the largest table on a page is not always the real race. Maine replaced its Democratic nominee
   in July, and Florida's biggest table is a hypothetical matchup. The parser must pick tables by nominee, never by
   size. About half the Wikipedia polls carry an "(R)" or "(D)" tag on the pollster name. VoteHub instead flags
   sponsored polls (17% of its entries). Which one counts as "partisan" (half weight) is decision D1.
3. **Likely voters:** this cycle's likely-voter screens lean Democratic (+1.0 median in 23 paired generic-ballot
   releases). In 2018 and 2022 they leaned Republican (−0.7 and −1.5). So the correction for registered-voter polls
   has to be measured on this year's polls, not copied from past midterms.
4. **Already on disk:** CES 2024, the CES cumulative file (2006–2025, with Senate and House vote, party ID, zip and
   district), the Census CPS turnout files for 2018, 2022 and 2024, VoteHub generic ballot and approval, and 538's
   generic-ballot archive. Since 28 Sep also: 538's poll errors and Senate, House and governor poll histories, MIT
   president and Senate results, and The Downballot's district results on the 2024 and 2026 lines (§4). Still
   missing: the MIT House file (it needs a guestbook form filled in by hand) and the new-map and ACS files (they need
   an account and a key).
5. **Pilot method (by 1–2 Oct):** one Kalman filter that tracks a national generic-ballot level plus each race's gap
   to it. It corrects for pollster house effects, likely voters and partisan polls. On election day it is blended with
   fundamentals by how uncertain each side is, including a shared poll error that never shrinks. A 40,000-draw Monte
   Carlo then runs with national, regional, state and race errors and fat tails. No new dependencies are needed.
6. **Fuller method (by 12 Oct):** the error sizes and blend fitted on 2006–2022 history; the factor state with
   demographic factors, poll-bias terms and per-state sensitivity dials; voter-group weights for all 35 states and the
   House districts on the new maps.
7. **The dial is linear.** A dial multiplies known reactions, so the weekly update can be done exactly with a plain
   Kalman update. The ensemble is only needed if a parameter enters non-linearly. This is a point for
   engine-design.md (§9).
8. **What beating the stats-only twin can mean:** where polls are dense, reactions can matter only in the days
   between polls. The simulation carries weight where polls are sparse (most Senate races and most House seats) and
   through the dials. Scores should be reported separately for poll-rich and poll-poor races.
9. **Fitted on history (28 Sep, §5.10):** the recipe holds up on past elections.
   - For well-polled, close Senate races, the best election-day weight on polls was 0.82 (the formula gives about 0.8).
   - Polls miss together nationally by about 3 points a year, plus 3.5 per race and 2.6 per state.
   - Races drift about 0.5 points a day.
   - Fundamentals alone miss by 7.5–8 points per race.
   - Sponsored polls lean about 4.7 points toward their sponsor.
   Four small choices followed from this (D9–D12), plus a data request (D13). Matteo approved all five on 28 Sep.
10. **Backtest (§5.11):** on the 2018–2022 Senate races, the stats-only chain scored better than 538's published
    forecasts at 35, 14 and 1 days out (eve Brier 0.040 against 0.048 for 538 deluxe).
    - The edge comes from 2020 and 2022; in 2018 we were slightly worse.
    - In 2024 it beat its own polls-only and fundamentals-only parts (eve 0.034; one wrong call, Pennsylvania).
    - Four elections are too few to call it real. But it is a demanding twin for the simulation to beat.

## 2. Inputs: where each comes from and its shape

### 2.1 Race list, nominees, seats not up

Source: Wikipedia "2026 United States Senate elections", read through the MediaWiki API (revision 1377122436,
28 Sep 00:25 UTC). The "Race summary" table lists state, Cook PVI, incumbent, status and every ballot candidate with
party. The Ohio and Florida specials sit in a separate table ("Special elections during the preceding Congress"). The
composition table gives the seats not up: 31 R, 32 D and 2 independents who caucus with the Democrats. Up for
election: 22 R and 13 D. Vice President Vance breaks ties, so Republicans keep control with 19 of the 35 races
(50 seats). Democrats need 17 (51 seats).

The page also carries a ratings table (Cook, DDHQ, Economist, FiftyPlusOne, Fox, Inside Elections, RCP, Sabato and
others). It is a scoring benchmark, not an input (D2). The snapshots, and the page's revision history for earlier
dates, give the ratings on any date.

### 2.2 Senate race polls

| | VoteHub API (metadata) | Wikipedia race pages (coverage) |
| --- | --- | --- |
| Access | `api.votehub.com/polls?poll_type=us-senator`, no key; in every snapshot | MediaWiki API `prop=revisions`, pin the revision id; titles "2026 United States Senate election in X", "...special election in Ohio/Florida"; in every snapshot |
| Licence | CC BY 4.0 (attribute) | CC BY-SA 4.0 (attribute; a published poll list derived from it must also be CC BY-SA) |
| Shape | JSON list, one entry per poll and population: `id, poll_type, pollster, sponsors[], partisan (REP/DEM/null), internal, population (lv/rv/a/v), sample_size, start_date, end_date, created_at, url, answers[{choice, pct}], seat_name, subject` | wikitext table: poll source (with "(R)"/"(D)" tags and footnotes), dates, sample "1,115 (LV)", margin of error, one column per candidate, Other, Undecided. The versions of one poll share cells through rowspan |
| Strength | sponsor, partisan and internal flags per poll; one entry per population | many polls VoteHub lacks; revision history gives the state of the table on any past date |

**VoteHub Senate entries** (first snapshot, 28 Sep 00:36 UTC): 418 entries. `seat_name` is always empty; the race is
in `subject`: "2026 Michigan" for the general election, "2026 Texas Democratic" for a primary (60 primary entries). Of
the 358 general entries, 239 match the nominee pairs across 24 states. The rest are hypothetical or obsolete matchups
filed under the same subject (Moody v Vindman in Florida, for example), so VoteHub also has to be filtered by nominee
names. By population: 338 LV, 77 RV, 2 A. VoteHub flags 40 of the 239 as partisan (17%); `internal` is false for all.

VoteHub misses much of what Wikipedia has in thinly polled races (VoteHub against Wikipedia): Nebraska 1 v 12, South
Dakota 0 v 8, Idaho 1 v 7, South Carolina 1 v 6, Kansas 3 v 8, Ohio 18 v 25. It has a few that Wikipedia lacks. Neither
is complete, so the merge below matters.

**Coverage on Wikipedia today** (actual nominee pairs, revisions of 26–28 Sep; counted with a scratch parser):

| Polls | Races |
| --- | --- |
| 17–42 | TX 42, NC 37, MI 37, OH 25, NH 24, IA 22, AK 22 (four-way ranked-choice table), GA 19, ME 17 |
| 5–12 | NE 12, MT 12 (three-way), MA 11, MN 10, KS 8, SD 8, ID 7, SC 6, FL 5, AR 5 |
| 1–4 | MS 4, RI 4, VA 3, KY 2, LA 2, AL 1, NM 1, OK 1, TN 1 |
| none | CO, DE, IL, NJ, OR, WV, WY (only primary polls on their pages) |

About 70% of versions are likely-voter; about 6% have no population tag. In the matched tables, 105 of 215 polls carry
a party tag on the pollster (for example "Rasmussen Reports (R)", "Trafalgar Group (R)", "InsiderAdvantage (R)",
"Quantus Insights (R)" in Ohio).

**Wikipedia parse rules** (prototype tested on all 35 pages; no new dependency: wikitext tables are line-based, and the
HTML route would need lxml or bs4, which are not installed):
1. Read only the "General election → Polling" section. Skip the aggregate table ("Source of poll aggregation":
   270toWin, DDHQ, FiftyPlusOne, Race to the WH, RCP, Silver Bulletin).
2. Pick the table whose candidate columns contain both nominees from §2.1. Maine's page holds 28 polls of Collins v
   Platner (the replaced nominee) against 17 of Collins v Jackson. Florida's biggest table is Moody v Vindman
   (13 polls); the nominee is Angie Nixon (5).
3. Expand rowspans. Each row is one version of a poll: likely or registered voters, with or without leaners, with or
   without third-party names.
4. Strip templates (`{{party shading/...}}`, `{{efn|...}}`, `{{nbsp}}`; `{{sdash}}` means missing), refs, links and
   bold.
5. Dates come as "September 22–23, 2026", "August 26 – September 2, 2026" or single days. Keep start, end and
   midpoint.
6. The sample "1,115 (LV)" gives n and population. The margin of error is kept but not used (it is recomputed).
7. Keep the pollster tag "(R)"/"(D)" in its own column (D1).

**VoteHub habits** (seen in the files on disk): each population of a poll is its own entry (YouGov A and RV, for
example). `partisan` is set per poll by sponsor, not per pollster (Quantus: 5 of 21 generic-ballot polls flagged
REP). `internal` is false in every generic-ballot and approval entry; Senate campaign internals may differ.

**Merge:** match on race, normalised pollster name, end date within a day and sample size within 5%. VoteHub wins on
metadata. Wikipedia adds the polls VoteHub lacks. Any disagreement over 1 point in the margin is logged for a look.
Every row records the snapshot it was first seen in, so each day's filter, and later the blind track, uses only what
was known that day.

**Built 28 Sep:** `simlab/polls.py` (`python -m simlab.polls`, 28 tests in `tests/test_polls.py`).
- **Numbers and flags:** when a poll is in both sources, the numbers come from Wikipedia (its versions averaged) and
  the flags from VoteHub.
- **First run** (snapshot 28 Sep 09:41):
  - 35 races and 355 Senate polls: 186 in both sources, 129 Wikipedia only, 40 VoteHub only;
  - 12 disagreements over 1 point;
  - 441 generic-ballot and 836 approval polls.
- **Still to add:** first-seen dates across snapshots, Alaska's ranked-choice count, and Montana's three-way race.

### 2.3 Generic ballot and approval

On disk (`data/history/`, from VoteHub, 27 Sep): generic ballot, 544 polls from 11 Dec 2024 to 8 Sep 2026 (315 RV,
123 LV, 103 A); approval, 2,946 polls from Nov 2018 to 17 Sep 2026. The schema is as in §2.2 (`subject` "2026" or
"Donald Trump"; answers Dem/Rep or Approve/Disapprove). The snapshots now carry both, every 3 hours once scheduled.

Likely-voter minus registered-voter margin, from polls released both ways:

| Cycle | Pairs | Mean | Median |
| --- | --- | --- | --- |
| 2018 (538 archive) | 184 | −1.6 | −0.7 |
| 2022 (538 archive) | 40 | −1.3 | −1.5 |
| 2025–26 (VoteHub) | 23 | +1.4 | +1.0 |

Registered-voter and all-adult polls get this year's measured gap (capped at ±2, Field Guide). Pollsters with enough
pairs get their own gap in the fuller version.

### 2.4 538 history: house effects and poll-error sizes

On disk: generic-ballot polls 2018–22 (4,097 polls, 41 columns including pollster, sponsor, partisan, population and
sample size), Trump-first-term and Biden approval poll lists and averages, and the 2017–19 generic-ballot average.
Enough for generic-ballot house effects and the LV gap, not for race-level errors.

Needed (§4). All are still online and CC BY 4.0; 538's GitHub repos have been frozen since March 2025 but not
deleted:
- `pollster-ratings/raw_polls.csv`: polls from the last three weeks of each race, with the actual result: 20,466
  polls from 1998 to 2023, 5,006 of them Senate general elections. There is no 2024; its errors come from the 2024
  poll list below plus the MIT results. Used for poll-error sizes.
- `pollster-ratings-combined.csv` (the newest ratings, with a bias column) and `pollster-ratings/2023/pollster-ratings.csv`
  (the older layout with "House Effect" and "Mean-Reverted Bias"). Used for house-effect priors.
- The Senate, House and governor poll lists, through the Wayback Machine. The `*_polls_historical.csv` files hold
  2018–22 (Senate: 2,119 polls); the current-cycle `*_polls.csv` copies from late Nov / early Dec 2024 hold 2024
  (Senate: 890 polls). Later copies of `house_polls.csv` are empty. Used for drift, house effects 2018–24 and the
  LV-gap history. Long format: one row per poll question and candidate (`poll_id, pollster, population, partisan,
  sponsors, cycle, office_type, party, answer, pct` and more).
- `checking-our-work-data`: 538's daily Senate forecasts with outcomes, 2008–2022 (`forecast_date, probwin,
  projected_voteshare, actual_voteshare`). Used to see how well calibrated a professional model was.

### 2.5 Results

- **By state, 2020 and 2024 presidential and all Senate races since 1976:** MIT Election Lab on Harvard Dataverse
  (CC0). All three files run through 2024: president updated 4 Sep 2026, Senate May 2026, House March 2026. This gives
  the partisan lean, incumbency effects and past candidate performance. Governor results (for candidates like Cooper)
  are not in the MIT sets; take them from Wikipedia for the few nominees who need them.
- **National House vote by year:** from the MIT House file (summing districts; uncontested seats need care) or the
  Clerk of the House statistics.
- **2024 presidential result by district on the new maps:** The Downballot's sheets (9 Jul 2026 release; cite and
  link, but don't reproduce whole sheets). Ten states have changed maps: TX, CA, NC, OH, MO, UT, AL, FL, LA and TN.
  They cover 181 districts, 145 of which changed. This is the backbone of the House fundamentals map.
- **Which map is in force:** Missouri's new map is reported blocked for 2026. The state supreme court ordered the old
  map while a referendum is on the 3 Nov ballot, and an appeal was pending in late September. Before building the
  House, confirm the map in force in each of the ten states (Wikipedia's 2026 House page or Ballotpedia). Where the
  old map stands, use old-line results.

### 2.6 New maps and demographics on the new lines

- **Redistricting Data Hub:** block assignment files for the enacted 2026 maps. Plans are posted for TX, NC, OH, MO,
  AL, FL, LA and TN; CA and UT did not turn up under the same naming and need a look after login. A free account is
  needed (on Matteo's list for Thu 1 Oct), and file sizes sit behind the login.
- **Census ACS 5-year (2020–24 vintage):** educational attainment by race for adults 25+ (the C15002 tables by race),
  at tract level, plus 2020 block populations to split tracts that cross a new line. Every Census API request has
  needed a free key since May 2026 (on Matteo's list for Thu 1 Oct). The citizen voting-age tabulation (CVAP 2020–24,
  block groups, 59 MB) is a fallback only.
- **Cook 2026 PVI by district:** a view-only check, quoting single values with credit. The site blocks automated
  reads.

### 2.7 Surveys for voter-group weights (all on disk)

| File | What | Use |
| --- | --- | --- |
| `data/CCES24_Common_OUTPUT_vv_topost_final.csv` (176 MB) | CES 2024, 60,000 respondents; validated vote, `pid7`, race, education, `cdid119`, county, zip | 2024 group vote; party ID by state |
| `data/cumulative_2006-2025.dta` (692 MB; a few columns read in about 10 s) | CES cumulative, 109 variables; about 60,000 a year in even years, 17,000 in 2025; `voted_sen_party`, `voted_rep_party`, `vv_turnout_gvm`, `pid7`, `approval_pres`, `cd`/`cd_up`, zip, county | midterm group vote for Senate and House (2018: 30,736 Senate voters; 2022: 28,907); party ID by state pooled over 2022–25 |
| `data/cps/` (nov18, nov22, nov24) | Census CPS November supplements; `simlab/cps.py` corrects self-reports to official turnout | group turnout by state for a midterm electorate (2018, 2022) |
| `simlab/turnout2018/2022/2024.json` | official turnout by state (UF Election Lab) | turnout calibration |
| `simlab/archetypes.json` | the 28 groups (7-point party ID × white/non-white × degree), national adult weights | group definitions |

### 2.8 VoteHub API details

Documented at votehub.com/polls/api (checked 28 Sep): `/polls` takes `poll_type, pollster, subject, from_date,
to_date, min_sample_size, population`; there are also `/polls/{id}`, `/pollsters`, `/subjects` and `/poll-types`. No
key is needed, no rate limit is documented, and the licence is CC BY 4.0. The date filters allow small incremental
pulls. The snapshotter pulls everything in one call (5,686 entries across all poll types on 28 Sep), which is fine at
this size.

### 2.9 Not inputs

Prediction markets (benchmark only), expert ratings (benchmark only, D2), RealClearPolling (terms bar scraping; its
averages also appear on Wikipedia and are skipped with the aggregate tables), X.

## 3. On disk now

| Have | Path | Enough for |
| --- | --- | --- |
| CES 2024 and cumulative 2006–25 | `data/` | voter-group weights, party ID, group vote in midterms |
| CPS 2018, 2022, 2024 | `data/cps/` | group turnout |
| Official turnout 2018, 2022, 2024 | `simlab/turnout*.json` | turnout levels |
| VoteHub generic ballot and approval | `data/history/votehub_*.json` | history to 27 Sep; the snapshots carry the live feed |
| 538 generic-ballot polls 2018–22, approval archives | `data/history/538_*.csv` | generic-ballot house effects, LV gap history |
| Nationscape 2019–21 | `data/history/nationscape/` | (events work, not needed here) |
| Snapshots | `simlab-data/snapshots/YYYY-MM-DD/HHMM/<source>/<name>.gz` + `manifest.json` | first run 28 Sep 00:36 UTC (`simlab/snap.py`, built by the Kev session): VoteHub, all polls; 38 Wikipedia pages as raw API JSON with revision ids; markets (benchmark); news; pageviews. The 3-hourly schedule waits for the deploy key |

Added on 28 Sep (§4): 538 poll errors and poll histories, MIT president and Senate results, The Downballot's district
results. Still missing: the MIT House file (guestbook), the new-map files, and ACS on the new lines.

## 4. Downloads

Approved by Matteo on 28 Sep; sizes were checked beforehand from file listings and headers. All are free.

**Status (28 Sep):** `python -m simlab.statsdata download` fetched #1, #2, #4, #5, #6 (Senate file only) and #7 into
`data/results/` and `data/history/`: 21 files, 23.7 MB, each with its URL, size, SHA-256 and fetch time in
`data/stats_downloads.json`. `python -m simlab.statsdata check` reports what each file covers. Where things stand on
the rest:
- #5 also includes 538's 2024-cycle poll files (Senate 1.5 MB, House 0.4, governor 0.5), because the "historical"
  files stop at 2022.
- #3, the MIT House file, sits behind a Dataverse guestbook form (name, email, purpose), which a script shouldn't fill
  in for someone. Download it by hand from the dataset page and save it as `data/results/1976-2024-house.tab`. The next
  `download` run then records it. Needed by Mon 5 Oct.
- #8 and #9 wait for the Redistricting Data Hub account and the Census key (Thu 1 Oct).

| # | What | Source, licence | Size | For | Needed by |
| --- | --- | --- | --- | --- | --- |
| 1 | U.S. President 1976–2024, by state | MIT Election Lab, doi:10.7910/DVN/42MVDX, CC0 | 0.5 MB | lean | Wed 30 Sep |
| 2 | U.S. Senate 1976–2024 | MIT, doi:10.7910/DVN/PEJ5QU, CC0 | 0.6 MB | incumbency, candidate effects, fundamentals fit | Wed 30 Sep |
| 3 | U.S. House 1976–2024 | MIT, doi:10.7910/DVN/IG0UN2, CC0 | 4.2 MB | national House vote by year, House incumbency | Mon 5 Oct |
| 4 | `raw_polls.csv`, `pollster-ratings-combined.csv`, `2023/pollster-ratings.csv` | github.com/fivethirtyeight/data, CC BY 4.0 | 5.0 + 0.04 + 0.1 MB | poll-error sizes, house-effect priors | Mon 5 Oct |
| 5 | `senate_`, `house_`, `governor_polls_historical.csv` | Wayback copies of projects.fivethirtyeight.com (3 Dec 2024), CC BY 4.0 | 3.0 + 1.5 + 2.5 MB | drift, house effects 2018–24 | Mon 5 Oct |
| 6 | `us_senate_elections.csv` (House file optional) | github.com/fivethirtyeight/checking-our-work-data, CC BY 4.0 | 8.0 MB (+42 MB) | calibration benchmark | Mon 5 Oct |
| 7 | 2024 presidential by district, old and new lines | The Downballot Google Sheet (cite, don't republish) | under 1 MB | House fundamentals map | Tue 6 Oct |
| 8 | Block assignment files, new maps (up to 10 states) | Redistricting Data Hub (free account) | behind login; typically a few MB per state | district weights | Tue 6 Oct |
| 9 | ACS 2020–24 tract tables, education by race, affected states | Census API (free key) | a few MB | district weights | Tue 6 Oct |

Not needed: MIT's 2024 precinct file (400 MB), the CVAP tabulation (59 MB, unless the tract route fails) and the
optional 538 House forecast file (42 MB). The VoteHub Senate and House polls and the Wikipedia pages arrive through the
snapshots, so they need no separate download.

## 5. Methods

### 5.1 One row per poll

From the merged table (§2.2):
1. Pick one population per poll: likely voters, else registered voters, else adults (brief).
2. Average the versions within that population (leaners, third-party names): they are one sample. Alternative (D7):
   take the version closest to the real ballot.
3. Two-party margin: `m = 100 × (D − R) / (D + R)`. The sampling variance comes from the decided respondents only:
   `s² = 4·10⁴ · p(1 − p) / n_decided`, with `p = D / (D + R)` and `n_decided = n × (D + R) / 100`.
4. Poll variance `v = s² + σ_ns²`. σ_ns is non-sampling error (weighting, mode, timing): 2.0 points, the middle of
   the fitted 1.2–3.2 (§5.10). It is refitted from this year's spread of polls around the average.
5. Partisan poll (D1): `v × 2`, which is half weight. History says sponsored polls also lean about 4.7 points toward
   their sponsor (§5.10), so they are also shifted against the sponsor (D9). With pollster house effects in the
   model, the shift is +2.2 (D) and −2.9 (R) from 2018–24, re-estimated on this year's polls. Several polls by one pollster in one race within 14
   days: `v × k` each, so together they weigh as one poll (Field Guide).
6. Dated at the field-period midpoint; entered on the day first seen.

### 5.2 Poll average (pilot)

Two layers, so that national moves reach every race:
- **N(t)**, the national environment: the generic-ballot margin. Generic-ballot polls measure it directly.
- **R_r(t)**, each race's gap to the national environment. A race poll measures `N(t) + R_r(t)`.

A race poll from August is thus read against the national level of August. If the generic ballot moves after that,
the race moves with it until new race polls arrive. That is what keeps poll-poor races current.

Each poll: `y = latent + house effect of its pollster + LV gap (if RV or A) + noise(v)`.
- **Drift:** N and each R_r follow random walks with daily SDs σ_N = 0.3 and σ_R = 0.5 points (fitted in §5.10;
  midterm Senate races drifted faster, 0.8, partly undecided voters breaking late).
- **House effects:** pooled across the generic ballot and all Senate races, and centred on the average pollster. Each
  pollster's prior is its 2018–24 lean (`simlab/house_effect_priors.json`, §5.10); new pollsters get N(0, 3²). Estimated by alternating three to five times: smooth the averages, take each poll's
  residual, then set each pollster's effect to its shrunken mean residual.
- **Run:** Kalman filter and smoother over the whole poll history, re-run from the first poll every day. At this size
  (about 1,000 polls) that takes milliseconds and gives the same answer as updating yesterday's state. Each day is
  then reproducible from its snapshot alone.

### 5.3 Fundamentals

For race r in state s, the fundamentals margin is the formula fitted in §5.10:

`M_r = 0.62 × lean(2024) + 0.26 × lean(2020) + 5.1 × incumbent + 0.71 × E + 0.38 × prior over-performance + 2.8`

The fundamentals guess for the gap to the national environment is then `F_r = M_r − N`.
- **Lean:** the state's two-party presidential margin minus the nation's. The weights are fitted: close to the
  Field Guide's 75/25, but summing to 0.88 (D11).
- **Incumbent:** +1 for a Democratic senator running again, −1 for a Republican. Appointed senators (Husted, Moody)
  get half. That is an assumption, because the fit only sees elected incumbents.
- **E**, the national House vote: the generic-ballot level N minus the generic ballot's historical overstatement of
  Democrats (D12).
- **Prior over-performance:** the nominee's own over- or under-performance in their last statewide race of the past
  12 years, beyond lean, national vote and incumbency. It covers incumbents, former senators and former governors.
  The share is the fitted 0.38 (D10). It is rule-based and logged, with no hand-set
  "quality" scores. Collins, Brown and Cooper are where it matters most.
- **Uncertainty:** SD σ_F = 7.5 points. It is fitted: 8.0 for races predicted within 15 in 2012–24, 7.4 in 2016–24.
  The national and regional parts are carried separately (§5.4, §5.8).

National environment: in the pilot, the generic-ballot level N alone. In the fuller version, approval enters as a
national fundamentals prior (president's party's House vote against net approval in past midterms), blended with N
the same way as below, and only if a leave-one-cycle-out test shows it helps (D4).

### 5.4 Starting level: the stats-only forecast

On election day T, for each race:
1. **From polls:** `R̂_r(t)` from the filter, with variance P_r. Project to T by adding drift `σ_R² × (T − t)`, then add
   the permanent race-level poll bias σ_bS² (fitted: 3.5 for races with 5+ recent polls, 5.9 for fewer). This error
   is shared by all polls of a race, so it never shrinks as polls pile up: `V_r = P_r + σ_R²(T − t) + σ_bS²`.
2. **From fundamentals:** `F_r` with variance σ_F².
3. **Blend by inverse variance:** `R̂_r(T) = w·R̂_r(t) + (1 − w)·F_r`, with `w = σ_F² / (σ_F² + V_r)`.
4. **National:** `N̂(T)` with variance `P_N + σ_N²(T − t) + σ_bN²`, where σ_bN is the national poll bias. It is
   fitted at 3.0: the Senate polls' shared miss per cycle, which is what polled races inherit. For unpolled races, the
   generic ballot's own spread (2.8) around its mean overstatement applies. In the fuller version N is blended with the
   approval prior if approval passes its test.
5. **Race margin:** `N̂(T) + R̂_r(T)`.

What this does: an unpolled race is all fundamentals (w = 0) and moves daily with N. A heavily polled race gets
mostly polls but never more than `σ_F² / (σ_F² + σ_bS²)`, about 0.8 with the fitted sizes. In 2006–22, the best
election-day weight on polls for such races was 0.82 (§5.10). About five weeks out, the remaining drift lowers it to
about 0.7. Each race publishes its poll weight w, so readers can see how much the polls count.

This is the stats-only forecast. The headline differs only through the reactions (§5.6).

### 5.5 Voter-group weights

**Per state** (pilot for OH, NC, TX by Fri 2 Oct; all 35 by 12 Oct). For each of the 28 groups g:
- **Population share** `n_g`: race × degree mix of adult citizens from CPS 2024, times party ID within race × degree
  from CES 2022–25 pooled (about 160,000 respondents). The party mix is shrunk toward the census division's
  (pseudo-count about 50, so small states borrow strength). Then it is tilted along the party axis until the groups
  reproduce the state's actual 2024 presidential margin. The tilt multiplies each party-ID level by `exp(θ × position)`,
  with position −3 (strong R) to +3 (strong D), and solves for θ.
- **Midterm turnout** `t_g`: CPS 2022 (and 2018) by race × degree in the state, shrunk, scaled to the official 2022
  turnout. The party gap within a demographic cell comes from CES validated turnout as an odds ratio. This is an
  assumption: CES validated turnout levels are unusable (match rates), but relative party gaps within a cell may be
  fine. Check it against the NC voter file's party registration by vote history.
- **Vote margin** `d_g` for race r: CES 2022 + 2018 Senate vote by group, pooled by region and shrunk to the state.
  Then every group is shifted equally on the logit scale until the electorate adds up to the race's starting level
  (§5.4).

Output per race: 28 rows (electorate share, turnout, D share, R share). These rows turn simulated group reactions into
a race move:

`Δm ≈ Σ_g e_g·Δd_g + Σ_g e_g·(Δt_g / t_g)·(d_g − m)`, where `e_g = n_g t_g / Σ n t` is the group's share of voters.

The first term is voters switching; the second is turnout changing the mix of who votes.

**Per House district** (the ~40 seats, by Fri 9 Oct):
- **Race × degree on the new lines:** ACS tract tables allocated to districts through the block assignment files.
  Split tracts go by 2020 block population.
- **Party ID within race × degree:** a multinomial logit on CES 2024 (scikit-learn, installed), with the respondent's
  district 2024 presidential margin as a predictor. Predict for each new district, then tilt to its 2024 result on the
  new lines (The Downballot).
- **Fallback** if the maps or the ACS pull slip: the state mix tilted to each district's 2024 result. The party mix is
  then right and the race × degree mix is the state average.

### 5.6 Daily filter (Fri 2 Oct)

State: N and R_r for every race (House seats join on 9 Oct). Each day:
1. **Forecast step:** every latent drifts, and the reactions move it: `N ← N + k_N·Δ_N`,
   `R_r ← R_r + k_s·(Δ_r − Δ_N)`. Δ_r is race r's simulated move from §5.5; Δ_N is the same reactions weighted to the
   national electorate. The k are the sensitivity dials: 1 until the weekly filter tunes them.
2. **Update step:** each new poll pulls N and R_r in proportion to how uncertain the state is against how noisy the
   poll is.
3. Then the blend (§5.4) and the Monte Carlo (§5.8).

The stats-only twin is the same code with Δ = 0.

**Innovation monitor:** each poll's surprise, scaled by its expected size, is summed weekly per state (a chi-squared
test). A state that stays surprising flags the auditor. The maths makes the update; the auditor only explains.

### 5.7 Weekly filter (from Mon 12 Oct)

The state takes the Field Guide's factor form: `R_r = region + state + Σ_k λ_rk·f_k + u_r`.
- **Demographic factors** `f_k` (about six: white non-college, Black, Hispanic, college suburban, rural, age). The
  loadings `λ_rk` are the race's electorate shares from §5.5, so polls in one race inform demographically similar
  races.
- **Permanent poll-bias terms:** national and per region.
- **Dials:** `k_s = k_nat + δ_s` with `δ_s ~ N(0, τ²)`, so states with few polls borrow from the national dial. Two
  dials per state (switching and turnout) if the reaction layer separates them.

Every Monday the week's polls update the state and re-tune the dials; the result is published and logged. Why a plain
Kalman update suffices is in §9.

### 5.8 Monte Carlo

- 40,000 draws. The seed is set from the run date and recorded.
- Each race's election-day margin = its mean (§5.4) + national + regional (the 9 census divisions) + state + race
  error. The national SD comes from §5.4. The regional and state parts are fitted: 1.1 and 2.6 (§5.10). All races in
  a state share the state term; the race error takes the rest of each race's variance. Census divisions carry little
  shared error; the fuller version's demographic factors should capture more of the regional pattern.
- **Fat tails:** a multivariate Student-t with 8 degrees of freedom. Each draw gets one shared scale, so an extreme
  year is extreme everywhere, and the correlations stay as specified.
- **Correlation floor:** check every pair at 0.25 or more each run. If any pair falls short (possible for two
  poorly known House seats in different regions), lift it in the correlation matrix and project to the nearest valid
  matrix (eigenvalue clipping in numpy). Correlations can't go negative by construction.
- **Outputs:** win chance per race; median and 10–90% margin range; the Senate seat distribution and control (seats
  not up plus seats won; tie goes to R); the House seat distribution and majority (218); and a fixed sample of 1,000
  draws (every 40th) with every race's margin and the seat totals, for one dot per simulated election. The same set
  is produced for the stats-only twin.
- **Size:** about 470 races × 40,000 draws is 19 million numbers, under a second in numpy.

### 5.9 House

- **~395 seats, fundamentals map:** district lean on the lines in force (2024 presidential from The Downballot, with
  2020 on the same lines at 25% if available) + N + incumbency. Incumbency uses the Field Guide rule (first-termers
  get half, × 0.7 where the district was redrawn) until it is fitted on the MIT House file, which is now on disk.
  Uncontested seats are fixed. District error SD 7–9 when unpolled, to be fitted the same way.
- **~40 seats:** the same, plus district polls (VoteHub `us-representative`, 104 entries on 28 Sep, plus Wikipedia),
  district voter-group weights (§5.5) and reactions.
- **Picking the 40:** the closest fundamentals margins, plus the consensus Toss-up and Lean seats from the Wikipedia
  ratings table. Ratings are used for selection only and never enter the numbers.

### 5.10 Calibration from history (fitted 28 Sep)

`python -m simlab.calib` reproduces everything below and writes `simlab/stats_params.json`. Margins are two-party,
D minus R; a poll error is poll minus result, so + means the polls overstated the Democrat.

**Poll errors** (538 `raw_polls`, polls in the last 21 days, 1998–2022; method of moments: national + race + poll):

| Senate races | Polls | Extra poll noise | Race-level shared error | National shared error |
| --- | --- | --- | --- | --- |
| All | 2,557 | 3.2 (sampling 4.0) | 5.9 | 3.0 (RMS 3.2) |
| 5+ polls, result within 15 | 1,653 | 1.7 | 3.6 | 3.5 |
| Same, 2006–2022 only | 1,319 | 1.2 | 3.3 | 2.6 |
| Fewer than 5 polls | 466 | 5.9 | 5.9 | 3.5 |
| 5+ polls, within 15, 22–61 days out | 1,428 | 2.5 | 5.0 | 3.8 |

- The national miss is shared across offices: its yearly values correlate 0.90–0.98 between Senate, governor and
  presidential polls, and only 0.38 with the generic ballot.
- **Generic ballot:** the final average overstated Democrats in 9 of 13 cycles; the mean is +2.8, the spread (SD) 2.8
  and the root-mean-square error 3.9 (by cycle: −0.8 to +7.6; 2018 −0.7, 2020 +5.4, 2022 +2.4). Part of this is the
  House vote itself (uncontested seats), which is why it tracks the Senate misses poorly.
- **Sponsored polls** sit 4.9 points more Democratic (D sponsor) or 4.6 more Republican (R sponsor) than the
  nonpartisan polls of the same race (medians 4.0 and 4.3).
- **Polls understate landslides:** in races won by 10 points or more, the final polls had the winner about 2 points
  short (undecided voters break toward the favourite). The blend with fundamentals pulls such races back.
- **Region and state:** with the national miss removed, statewide races' shared errors split into region (census
  division) SD 1.1, state SD 2.6 (all offices in one state miss together) and race-only SD 3.7.

**Drift** (538 poll lists, last 120 days, random walk plus poll noise by maximum likelihood; pollster-mix changes count
as drift, so these are upper bounds):

| Series | Races | Daily SD | Over 35 days |
| --- | --- | --- | --- |
| Senate 2018–2024 | 71 | 0.57 | 3.3 |
| Senate midterms 2018, 2022 | 37 | 0.81 | 4.8 |
| Senate 2024 | 17 | 0.41 | 2.4 |
| Generic ballot 2018–2022 | 3 cycles | 0.28 | 1.7 |

The same picture comes from the error sizes: race-level error grows from 3.6 to 5.0 between the last three weeks and
three to nine weeks out, about 0.4 of variance a day.

**Fundamentals** (MIT, Senate 2012–2024, 221 races with a Democrat and a Republican as the top two, Louisiana's
jungle races left out; each year predicted from the other years):

`margin = 0.62 × lean(latest) + 0.26 × lean(previous) + 5.1 × incumbent + 0.71 × national House vote + 0.38 × prior over-performance + 2.8`

- **Lean:** each state's presidential margin minus the nation's, the latest and the previous election. The weights are
  close to the recipe's 75/25 but add up to 0.88, not 1.
- **Incumbent:** +1 for a Democratic incumbent, −1 for a Republican. The effect is 4.1 on 2016–2024.
- **Prior over-performance:** the incumbent's previous win beyond lean, the national vote and incumbency.
- **Error when predicted from other years:** 8.9 points; 8.0 for races predicted within 15; 7.4 on 2016–2024. By year
  it falls from about 10.5 (2012–18) to 7.9, 6.4 and 5.6 (2020, 2022, 2024), as races nationalise.
- The big misses are real personal votes (Collins, Byrd, Conrad, Manchin), which is what the prior over-performance
  term catches.

**Blend check** (2006–2022, Senate races with 5+ polls in the last 21 days and a poll average within 15, national misses
removed): the weight on polls that minimised error was 0.82. Poll and fundamentals errors barely correlate (0.04). The
blend beat both parts: error 4.4, against 5.1 for polls alone and 9.1 for fundamentals alone. The inverse-variance
weight in §5.4 with the fitted sizes gives about 0.8. The recipe is confirmed on data it wasn't built from.

**Approval test** (D4; Gallup via the American Presidency Project, 538's average for 2022). The test predicts the
national House vote from the final generic-ballot average, with and without net approval signed toward the president's
party, holding out each cycle 1998–2022 in turn:

| | Generic ballot only | Plus approval | Approval only |
| --- | --- | --- | --- |
| All 13 cycles | 3.17 | 2.80 | 4.78 |
| 7 midterms | 3.21 | 3.09 | 5.88 |

- Approval passes the pre-agreed test (it beats the generic ballot alone in both rows), narrowly for midterms.
- It helped most in 2002 (Bush's post-9/11 approval) and hurt in 1998 (Clinton).
- **Fitted on all cycles:** `House vote = 0.69 × generic ballot + 0.084 × net approval (toward the president's party)
  − 2.3`. So 10 points of net approval is worth about 0.8 points.
- The fuller version uses this for the national environment (E in §5.3). The pilot keeps the generic ballot minus 2.8
  (D12).

**House-effect priors** (`simlab/house_effect_priors.json`; 538 poll lists 2018–24):
- **Data:** 6,054 general-election polls in the last 150 days, covering Senate, House, governor and generic ballot.
- **Method:** each poll is compared with a consensus of the other pollsters' polls of the same race at the same time.
  Each pollster's effect is its mean residual, shrunk toward zero (prior N(0, 3²)) and centred on the average
  pollster.
- **Lean Republican:** McLaughlin and Rasmussen −5.1, AtlasIntel and OnMessage −3.1, co/efficient and
  InsiderAdvantage −2.9, Trafalgar −1.8, Emerson −1.5.
- **Lean Democratic:** GBAO +2.0, Redfield & Wilton +1.8, Marist +1.7, CNN/SSRS +1.6, Quinnipiac +1.1, YouGov +0.95,
  Morning Consult +0.9.
- **Coverage:** 107 of VoteHub's 148 pollsters for 2025–26 (78% of their polls) match a 538 name, some through a
  short alias list. New pollsters (Quantus, Verasight, Tavern, Focaldata and others) start at no lean and are
  estimated from this year's polls.
- **Sponsor shift, measured on top of the pollster effects:** +2.2 for Democratic sponsors and −2.9 for Republican
  ones. That is smaller than the raw 4.7, because partisan pollsters' own lean already carries part of it. With house
  effects in the model, the shift to apply is this one (D9's "re-estimated" shift). Applying the raw 4.7 on top would
  count the lean twice.

### 5.11 Backtest: the stats-only chain on the 2018–2024 Senate races (28 Sep)

`python -m simlab.backtest` runs the chain of §5.1–5.4 as it would have run 35, 14 and 1 days before each election. It
scores it against the results and, for 2018–2022, against 538's own forecasts made on the same days (lite = polls,
classic = polls + fundamentals, deluxe = classic + expert ratings). 538's scoring file has no 2024. Per-race output:
`runs/backtest_senate_2018_2024.csv`.

**Races:** 122, those with a Democrat and a Republican as the top two. Left out: Georgia 2020 (both seats went to
runoffs), California's 2022 and 2024 specials (the same two candidates as the regular race on the same ballot),
Louisiana, and races with an independent as a finalist.

**No peeking:**
- a poll counts only once 538 had logged it by the forecast date;
- pollster house effects use that cycle's polls known by then, with priors from earlier cycles only;
- the fundamentals, the generic-ballot correction and every error size are refitted without the tested cycle.

The Brier score is the average squared error of the win probability: 0 is perfect, 0.25 a coin flip. "Competitive"
means races where a model in the comparison gave between 10% and 90%.

**2018–2022 against 538** (91 races):

| Model | 35 days: all | 35 days: competitive | 14 days: all | 14 days: competitive | Eve: all | Eve: competitive | Wrong calls on eve |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **Ours (stats-only)** | **0.042** | **0.102** | **0.041** | **0.097** | **0.040** | **0.097** | 5 |
| Polls only | 0.061 | 0.145 | 0.058 | 0.136 | 0.050 | 0.121 | 6 |
| Fundamentals only | 0.053 | 0.128 | 0.054 | 0.126 | 0.055 | 0.132 | 8 |
| 538 lite | 0.059 | 0.139 | 0.057 | 0.133 | 0.054 | 0.132 | 7 |
| 538 classic | 0.055 | 0.135 | 0.056 | 0.133 | 0.053 | 0.129 | 7 |
| 538 deluxe | 0.048 | 0.118 | 0.050 | 0.120 | 0.048 | 0.116 | 7 |

**2024** (31 races; no 538 comparison):
- Brier at 35 / 14 / 1 days: ours 0.041 / 0.036 / 0.034, polls only 0.048 / 0.041 / 0.036, fundamentals only 0.051 /
  0.052 / 0.053.
- **Wrong call on eve:** one, Pennsylvania. We gave Casey 83% on 136 polls; McCormick won by 0.2 points.

**All four cycles** (122 races): Brier on eve 0.038, against 0.046 for polls only and 0.054 for fundamentals only;
35 days out 0.042, against 0.058 and 0.053.

- **Margin on election eve**, average miss:
  - 2018–22: ours 4.5 points, 538 deluxe 4.9, polls only 5.4.
  - 2024: ours 3.5, polls only 4.6. Log loss ranks the models the same way.
- **By cycle** (eve Brier, ours against 538 deluxe):
  - 2018: 0.061 v 0.052, worse. Our own polls-only line did better that year.
  - 2020: 0.032 v 0.046, better. The fundamentals held back the big polling miss.
  - 2022: 0.023 v 0.044, better. 538 deluxe leaned 2.9 points Republican that year.
  - 2024: 0.034.
- **Our margin bias:** it leaned Democratic every year: +2.0 (2018), +3.9 (2020), +0.9 (2022), +3.3 (2024). It
  inherits the polls' recent tilt. Matteo decided on 28 Sep not to correct for it: Senate polls' yearly misses swing
  both ways over 1998–2022 (from −3.7 to +6.3), and the national error term (SD 3) is there to cover a miss of that
  size.
- **Calibration** (all cycles and dates pooled):
  - races we gave 10–30% went 0 of 27, and 30–50% went 23% (predicted 42%);
  - 50–70% went 59% (predicted 60%), 70–90% went 74% (predicted 81%).
  - Roughly right, with small samples.

How far to trust it:
- **Four elections:** too few to call an edge over 538 real. Gains and losses concentrate in a handful of races:
  - gains: North Dakota 2018, Iowa and Maine 2020, Georgia and Nevada 2022;
  - losses: Florida and West Virginia 2018, North Carolina 2022, Pennsylvania 2024.
- **Hindsight in the design:** the coefficients were fitted without the tested year, but the model's shape (the prior
  over-performance term, the 2012–24 window) was chosen after seeing these elections. 538's forecasts were published
  live.
- **What can be claimed:**
  - the stats-only chain is at least in 538's league on 2018–22;
  - blending beat both of its parts in every cycle except 2018;
  - it is a demanding twin: the simulation has to beat it, not a poll average.

Not yet backtested: the House.

Fitting the statistics on 1998–2024 is not the LLM-contamination problem; that applies to the agent layer.

## 6. What lands when

| Date | Piece | Version |
| --- | --- | --- |
| Tue 29 Sep | Poll table (VoteHub + Wikipedia) for 35 races and the generic ballot, tested on the first snapshots | pilot |
| Wed 30 Sep | House effects, LV gap, Kalman averages; fundamentals (needs the MIT results) | pilot |
| **Thu 1 Oct** | Blend into Senate levels for all 35 races; Monte Carlo with forecast and draw sample; stats-only twin | pilot, due |
| **Fri 2 Oct** | Daily filter taking reactions; voter-group weights for OH, NC, TX | pilot, due |
| Sat 3 – Sun 4 | Rehearsals and fixes | |
| Mon 5 – Wed 7 | Historical calibration (538 + MIT); weights for all 35 states | fuller |
| **Tue 6 – Fri 9** | House: fundamentals map for 435 seats; district weights and polls for ~40 | due 9 Oct |
| Thu 8 – Sun 11 | Weekly filter (factor state, dials, poll-bias terms), innovation monitor | fuller |
| **Mon 12 Oct** | First weekly update; code freeze | |

If the House slips, the ~40 seats launch on 12 Oct from the fundamentals map plus district polls (statistics only), as
the roadmap allows.

## 7. Special races

| Race | Issue | Handling |
| --- | --- | --- |
| Nebraska | Osborn (I) v Ricketts (R), no Democrat | Margin = Osborn − Ricketts. Fundamentals anchored on Osborn's 2024 Senate result plus the national shift, SD wider |
| Idaho, South Dakota | Independent v Republican (Achilles, Bengs) | Same margin definition; mostly fundamentals and the few polls, SD wider |
| Montana | Three-way: Alme (R), Bodnar (I), Bankhead (D); plurality | Model the top two if the third stays under ~10%; else simulate three shares (log-ratios) |
| Alaska | Top-four primary, ranked-choice general, two Republicans named Dan Sullivan | Use final-round head-to-heads where polls report them; else first choices with other Republicans transferred to Sullivan at an assumed rate |
| Maine | Ranked choice; nominee replaced in July | Head-to-head or final-round numbers; only Collins v Jackson polls |
| Georgia | Majority needed, else a December runoff | Pilot: the leader wins. Later: flag draws under 50% |
| Ohio, Florida | Specials with appointed incumbents | Incumbency at the appointed level (§5.3) |
| Louisiana, Texas | Incumbents lost renomination | Open seats |

## 8. Decisions

Matteo decided all of these on 28 Sep, as recommended (recorded in `docs/CHANGELOG.md`).

- **D1. What counts as a partisan poll (half weight)?** Recommend the sponsor rule: sponsored by a party, campaign or
  partisan group (VoteHub's flag, 538's rule; 17% of VoteHub's entries). Wikipedia's "(R)"/"(D)" pollster tags would
  halve about half of all polls, including Rasmussen, Trafalgar and InsiderAdvantage. Their lean is already corrected
  by house effects, so halving them too would count it twice.
- **D2. Ratings stay out of the numbers.** FLIPR gives ratings 6%. Recommend none, so "beat Cook" stays a clean
  comparison.
- **D3. Independents and Senate control.** If Osborn, Achilles, Bengs or Bodnar wins, who do they count for?
  Recommend a headline of "Republicans hold 50+" (clear either way), with independents shown in their own colour and
  "Democrats + independents who caucus with them reach 51" as a second line.
- **D4. Approval** enters the national environment in the fuller version only if it passes a leave-one-cycle-out test
  on past midterms. The pilot uses the generic ballot alone.
- **D5. Downloads** in §4.
- **D6. Candidate effect rule:** half of the nominee's last statewide over-performance (§5.3). Yes, or incumbency only?
- **D7. Versions within one poll:** average them (recommended; simple and neutral), or take the one closest to the
  ballot.
- **D8. Publishing the poll list:** the Wikipedia-derived part must be CC BY-SA, with attribution. Recommend a
  sources line on the methods page and CC BY-SA on any published poll table.

Raised by the fits (§5.10). Matteo approved all five on 28 Sep, as recommended:
- **D9. Sponsor shift.** Sponsored polls leaned 4.9 (D) and 4.6 (R) points toward their sponsor, against nonpartisan
  polls of the same race. Half weight shrinks that lean but doesn't remove it: a race polled mostly by one side's
  sponsors would still tilt. Recommend also shifting sponsored polls about 4.7 points against the sponsor (the Field
  Guide's "shifted against the sponsor"), re-estimated on this year's polls.
- **D10. Candidate-effect share.** Decided as half; history says 0.38 of a past over-performance carries over.
  Recommend the fitted 0.38. The rule stays the same; only the share changes.
- **D11. Lean weights.** The recipe says 0.75 × 2024 + 0.25 × 2020. History fits 0.62 and 0.26: the same split, but
  lopsided states count a little less. Recommend the fitted weights.
- **D12. Generic-ballot correction.** The final generic-ballot average overstated Democrats by 2.8 on average
  (1998–2022; 9 of 13 cycles). Recommend subtracting 2.8 where the generic ballot feeds the fundamentals, with its
  spread (2.8) as uncertainty. Polled races aren't affected: the correction cancels there. This mostly moves unpolled
  races.
- **D13. Approval data.** The approval test (D4) needs approval ratings for past midterms (1998–2014), which aren't on
  disk. The source would be the Gallup series from the UC Santa Barbara American Presidency Project, a web table of
  about 100 KB. Recommend fetching it for the fuller version; the pilot doesn't need it.
  - *Done 28 Sep:* approval passes the test (§5.10) and enters the fuller version's national environment.
  - *D9 in practice:* measured on top of pollster house effects, the sponsor shift is +2.2 (D) and −2.9 (R). This is
    the re-estimated shift D9 asked for; the raw 4.7 already includes partisan pollsters' own lean.

## 9. Notes for engine-design.md

- **Race ids:** one stable id per race across all files (state, office, seat or district), with special or ranked-choice
  as fields rather than id parts.
- **Reactions:** best delivered per voter group (the 28) and scope (national, state, race), per day, as changes in
  support (D − R) and turnout. Statistics owns the weights and the formula in §5.5, so it can aggregate them. If the
  Engine aggregates instead, it should read the weights file.
- **Levels (Statistics → Engine):** per race, the mean margin, SD and poll weight, plus the 28 group rows.
- **Filter state (Statistics):** latents, their covariance, dials, house effects and the parameter-file version.
- **Forecast (Statistics → site):** per race, Senate and House, the draw sample, the stats-only twin side by side,
  and the run manifest (code version, seed, input hashes).
- **Wikipedia snapshots:** the snapshotter already keeps the raw API JSON (wikitext, revision id, timestamp), which is
  what the parser reads. It also needs the 2026 House page for the ~40 seats' candidates.
- **The dial is linear.** A dial multiplies the day's reactions, which are known numbers: `x_next = x + k·Δ`. That is
  linear in the state and the dial together, so a Kalman update on the combined vector is exact, deterministic and
  free of ensemble noise. An ensemble adds only noise and cost. It earns its place when a parameter enters
  non-linearly (a threshold, or a dial inside the model's prompt) or when several model seeds must be carried.
  Recommend building the exact update first, keeping the ensemble code path for that case, and checking both on
  simulated data. The weekly clock can stay as a policy (re-tune dials on Mondays) even though the maths would allow
  daily updates.

## 10. Assumption register

Fitted values come from `python -m simlab.calib` (28 Sep; `simlab/stats_params.json`). The rest stay as assumptions and
are listed on the methods page.

| Parameter | Value | Source | Status |
| --- | --- | --- | --- |
| Partisan poll weight | 0.5 | brief, D1 | fixed |
| Sponsor shift | +2.2 (D) / −2.9 (R) on top of pollster effects; raw 4.7 | fitted | decided (D9); refit on 2026 polls |
| Pollster flooding | one weight per pollster per race per 14 days | Field Guide | fixed |
| House-effect prior | each pollster's 2018–24 lean; N(0, 3²) if new | fitted (`house_effect_priors.json`) | refit on 2026 polls |
| Approval in the national environment | 0.084 per point of net approval; generic-ballot weight 0.69 | fitted 1998–2022; passes D4 | fuller version |
| LV gap for RV/A polls | this year's paired mean, cap ±2 | §2.3 | refit weekly |
| Non-sampling poll error σ_ns | 2.0 | fitted 1.2–3.2 | refit on 2026 polls |
| Daily drift σ_N / σ_R | 0.3 / 0.5 | fitted 0.28 / 0.41–0.81 | refit with house effects removed |
| National poll bias σ_bN | 3.0 | fitted 2.6–3.5 (Senate polls' national miss) | fitted |
| Race-level poll bias σ_bS | 3.5 (5+ polls), 5.9 (fewer) | fitted | fitted |
| Generic-ballot overstatement of D | 2.8, spread 2.8 | fitted 1998–2022 | decided (D12) |
| Lean weights, latest / previous | 0.62 / 0.26 | fitted (recipe: 0.75 / 0.25) | decided (D11) |
| National House vote coefficient | 0.71 | fitted | fitted |
| Incumbency (per incumbent, margin points) | 5.1 (appointed: half) | fitted 4.1–5.1; appointed is an assumption | fitted |
| Candidate-effect share | 0.38 | fitted | decided (D10) |
| Fundamentals SD σ_F (race part) | 7.5 | fitted 7.4–8.0 | fitted |
| Regional / state / race-only SD | 1.1 / 2.6 / 3.7 | fitted (census divisions) | fitted |
| Tails | Student-t, 8 df | FiftyPlusOne (8–10) | fixed |
| Correlation floor | 0.25 | Economist model | fixed |
| Draws / published sample | 40,000 / 1,000 | brief | fixed |
| Dials before the first weekly update | 1 | assumption | weekly filter |
| Group turnout party gap | CES validated odds ratio within cell | assumption | check against NC voter file |
