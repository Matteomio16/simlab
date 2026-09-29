# Changelog: decisions and changes made in Claude Code

For Cowork to pick up. Newest first. Final decisions are also summarised in CLAUDE.md section 5.

## 2026-09-29 evening (Kev session): House fundamentals for all 435 seats; early vote for ME, IA and TX ready

- **House (A11), `simlab/house.py`** (4 tests). All 435 seats in the levels.json race shape: `house_levels.json`,
  with `fixed`, `tier`, `state` and `region` added, and `house_races.json` in the races.json shape.
  - Margin = c + 0.973 × lean + 4.45 × incumbent (× 0.7 on a map redrawn for 2026). Lean is the 2024
    presidential two-party margin on the 2026 lines minus the nation's (-1.68).
  - The fit (`python -m simlab.house fit`) uses the 2022 and 2024 contested seats on unchanged lines. Predicting
    each year from the other, given the national House vote, close seats missed by 4.7 (2022) and 4.7 (2024).
  - c is set daily so the seats add up to `levels.json` `national.E_hat`:
    - contested seats are weighted by 2024 presidential votes;
    - uncontested ones are fixed at ±100 and weighted by 0.71 of those votes (2024's ratio).
    On 2024 this anchoring leaves the contested seats unbiased (+0.03).
  - SD is 5.5 within 15 points and 9 beyond (Matteo, 29 Sep).
  - The Wikipedia House pages give the nominees, whether a sitting member runs (matched anywhere in the state), the
    uncontested seats (no Republican nominee means fixed D; a Republican facing only an independent, as in Alaska,
    stays contested with the independent on the left) and the ratings.
  - Simulated seats: consensus Toss-up/Tilt/Lean, then the closest by win chance, up to 40. "watch" covers win chance
    3-97% or a consensus Likely.
  - Inputs: simlab-data `house/inputs.json` (private), built by `python -m simlab.house inputs` from the Engine's
    `data/house/`.
  - First run (29 Sep): 219.6 expected Democratic seats (212 favoured) at a national House vote of D+4.5. 377 of 435
    districts are matched to nominees. The other 58 are California, whose two sub-pages the snapshot adds from its
    next run, and Louisiana, which has no nominees yet; their CSV incumbent is assumed to run. 11 seats are
    uncontested (all D).
  - Still to wire: statsday must call `house.run(day, data, levels)` and the Monte Carlo must add the seats
    (Statistics), and daily.yml must check out `/house/` (Engine). `house_groups.json` joins with the simulated
    seats' voter groups, due Tue 6 Oct.
- **Early vote:** Maine, Iowa and Texas are ready but off (`ENABLED` in `simlab/earlyvote.py`) until Matteo's OK:
  - ME: voter-level file, counts only; 4.4 MB today, about 37 MB by 3 Nov; the link is read from the voter-data page.
  - IA: daily PDFs by county and congressional district, as published, from about 14 Oct.
  - TX: the Civix election list (small JSON), to see when early-voting days start (about 19 Oct).
  Change detection uses Last-Modified, or the SHA-256 where there is none.
  - Ohio can't be scripted: the SOS site and most county sites sit behind Cloudflare's bot check, which we don't get
    around. The dashboard's Power BI layer answers plain requests, but its report link changes each cycle.
- **Snapshots:** GitHub started them only 6-9 hours apart on 29 Sep despite the 15-minute trigger. `snapshot.yml`
  now takes `scheduled=true` from the Engine's Cloudflare cron (ops/cron) and obeys the 150-minute rule. The cron
  also starts `earlyvote.yml` hourly. The snapshot now fetches California's two House sub-pages.

## 2026-09-29 (Website session): NotAPoll.org site, C6

Decided by Matteo (design in `docs/superpowers/specs/2026-09-29-notapoll-site-design.md`):
- **notapoll.org is the home**; labs.scaliastudio.dev/midterms redirects there. "By Scalia Studio" in every footer and
  on About.
- **Two launches.** Sat 3 Oct: home, methods, Lab notes, About, with no forecast numbers of any kind. Mon 12 Oct: Senate
  overview and race pages. Week of 19 Oct: track record, changelog, archive. Election-night page by 3 Nov.
- **Written for both audiences in layers**: a plain sentence and one number on top, the data below.
- **Look (redesigned the same day):** American newsroom and institutional: Libre Franklin and Source Serif 4, navy
  masthead, heavy section rules, hairline tables, light only; restrained motion (count-ups, filling squares, scroll
  reveals, hover cards, map tiles that zoom into the state before opening its race page). A tile map switchable
  between our simulation, Cook and the markets, and a national-swing simulator that recounts the stored draws.
- **Stack as scaliastudio.dev:** Next.js 16 static export on a Cloudflare Worker; charts are React SVG (not
  vega-embed).
- **Preview** on an unlisted workers.dev address with sample data; Cloudflare Access later. **Deploys** from GitHub
  Actions (`.github/workflows/site.yml`) with a token Matteo creates.
- **Lab notes** go on the site only after Matteo approves each one (`site/scripts/import-labnote.mjs`).

## 2026-09-29 (Kev session): early-vote snapshots (A12, NC first); Kev live in shadow mode; Iowa and Maine in the pilot

- **Matteo, 29 Sep ("yes to all"):**
  - voter-level early-vote files are kept as counts plus the raw file's hash, never raw (this also keeps them under
    GitHub's 100 MB limit);
  - NCSBE's two files are fetched daily;
  - the pilot races are OH-S, NC, TX, IA and ME;
  - early vote comes before the House work, with House fundamentals due Fri 2 Oct and the House finished by 9 Oct;
  - House seat error: SD 5.5 for seats forecast within 15 points, 9 beyond;
  - the 435 seats are anchored each day to the national House vote;
  - Kev serves shadow mode at full load. The Engine's count is about 3,400 requests a day, about 7 minutes of GPU
    time.
- **`simlab/earlyvote.py`** and `.github/workflows/earlyvote.yml` (every 30 minutes, a HEAD request per file, a
  download only when Last-Modified changes). The output goes to simlab-data `earlyvote/<state>/YYYY-MM-DD/HHMM/`.
  - NC's absentee file (one row per ballot; one-stop voting joins it from 15 Oct) is counted by county,
    congressional district, party, race, ethnicity, gender, age band, request type, delivery, return status, return
    date and same-day registration. Today it holds 13,705 ballots, 0.8 MB.
  - NCSBE's county request counts (22.9 MB) are kept as published: 0.9 MB gzipped.
  - Two tests check that no name, address or voter id survives the counting.
  - Ohio, Texas, Iowa and Maine join once their files and sizes are confirmed.
- **Kev react-v2-2 serves shadow mode:** https://mattemio9--kev-finetune-api.modal.run (bearer key: Modal secret
  `kev-serve`, GitHub secret `KEV_API_KEY`; L4, one container, 60 s idle).
  - About 9 requests/s warm; about 60 s cold start.
  - Answers match the scoring run (0.953 vs 0.954).
  - The Engine wired it into the daily job (b07decc). It runs once the `KEV_URL` repository variable is set.
- **Iowa and Maine pageviews:** Hinson, Turek, Collins and Troy Jackson (who replaced Platner as the Democratic
  nominee) join the snapshot's candidate pageviews. News for every race was already covered by newsraces.json.
- **House, first fit on the 2026 inputs.** The Engine's `data/house/` holds The Downballot's 2024 presidential results
  on the 2026 lines and ACS citizen adults by race and degree. Fitted on 2022 and 2024:
  - House margin minus the national House vote = 0.97 × presidential lean + 4.5 × incumbent;
  - predicting one cycle from the other, given the national swing, the error SD is 4.9 (2022) and 4.6 (2024) for
    seats within 15 points, and about 10 overall because safe seats vary more.

## 2026-09-29 evening (Engine session): news on GDELT alone; workflows started on time; Kev shadow wired

- **Matteo: Media Cloud's sign-up is stuck, so the engine must work on GDELT alone.** Built:
  - GDELT moved from the 3-hourly snapshot to its own news job every 15 minutes (`simlab/newsnap.py`,
    `.github/workflows/news.yml`, writing `simlab-data/news/`). GDELT refuses an address for several minutes after one
    success (seen from GitHub and from home), so each run asks only the most overdue queries within about 9 minutes,
    contested races and the nation first. A query saved in the last 6 hours isn't asked again; one that failed is
    asked by the next run, and every query covers 24 hours, so a refused query is filled later.
  - Every race gets a GDELT query, not just the pilot.
  - RSS from the state outlets that answer a declared bot and allow reuse: Signal Ohio, Signal Cleveland and the Texas
    Tribune. An item counts for a race only when it names one of that state's candidates in full. All 19 States
    Newsroom sites refused with 403, so they aren't used.
  - Media Cloud stays optional: if its key comes, it plugs in as planned.
  - Coverage on GDELT alone (articles naming the candidates, 22-29 Sep; 21 of 36 races measured, the rest were
    refused during the check):
    - simulate races: Iowa and Maine 250+ a week (60-80 a day), Alaska 170, North Carolina 150, Kansas 143, Florida
      54, Nebraska 52, New Hampshire 24, Minnesota 15; Ohio and Texas about 50 and 60-100 a day on 28-29 Sep. The
      median simulated race has 27 articles in the last day; the thinnest (Minnesota, New Hampshire, Nebraska) have
      3-4.
    - watch races: Georgia 102 a week, Arkansas 16, Idaho 8;
    - statistics races: 6-44 a week (they use no race news).
    So volume is enough for 12 Oct. The constraint is how often GDELT answers: about 2 queries per 9-minute run.
- **GitHub fires this repository's schedules only every 5-9 hours**, whatever the cron says (snapshot runs on 28-29
  Sep: 09:40, 20:44, 01:13, 07:28, 16:09; none of the 28 quarter-hour triggers in between). So neither the 09:47 daily
  job nor a 15-minute news job can rely on it. `ops/cron/` holds a Cloudflare Worker that starts the workflows on
  time through GitHub's API (news every 15 minutes, snapshots every 3 hours, the daily job at 09:47 with
  `scheduled=true`, so `PIPELINE_ON` and the once-a-day rule still apply). It needs Matteo: a fine-grained GitHub token
  that can only run Actions on the repo, and `npx wrangler deploy` on his Cloudflare account (steps in its README).
- **Kev shadow mode wired** (Matteo reopened it, 29 Sep). Kev react-v2-2 is served on Modal behind a key. The harness
  wakes its GPU with one long request, sends the key, and skips Kev for the day if it doesn't answer. Any model is
  dropped after 20 failed calls, so an outage can't stall GLM. Tested live: 28 groups in 13 s after a 51 s wake-up.
  The daily job passes it once the `KEV_URL` repository variable is set. The load is about 530 requests a day in the
  pilot and 3,400 at full scale (one request per group and story), so no sampling is needed.

## 2026-09-29 (Kev session): Kev's voter-group margins for all 51 states delivered (A11 request)

- Kev ces-v3b answered the 28 voter groups in all 51 states (`python -m simlab.kevdata groups`, then Modal
  `evaluate --run ces-v3b --name ces-v3b-groups`, about $0.50; `python -m simlab.kevdata answers ces-v3b-groups`). The
  persona text is the training strata's own, the pres24 question comes in 3 option orders averaged at temperature
  1.0, and d = (harris - trump) / (harris + trump).
- `python -m simlab.groups --kev kev-finetune/runs/ces-v3b-groups/answers.json` wrote `simlab/kev_groups.json`: 1,428
  pairs, none falling back to d0. statsday picks it up from the next run.
- Checks:
  - the 60 held-out OH/NC/TX pairs match the test's answers within 3.5 points (other option orders);
  - Kev's margins never break the party order (strong > leaner > weak > independent, each side) by more than 5
    points, against 23 breaks in d0;
  - Kev puts independents at -0.14 on average (d0 +0.06), leaners and weak Republicans further right (-0.95 and
    -0.76 against -0.80 and -0.62), and Democrats about the same.
  The groups, moves and levels tests pass (59).

## 2026-09-29 (Statistics session): Kev's voter-group margins for the Senate too

- **Matteo, 29 Sep:** every race, House and Senate, takes each voter group's starting margin from Kev ces-v3b. The
  survey numbers (d0) are kept alongside for the check after 3 Nov. This replaces the split agreed earlier today (Kev
  for House districts only).
- **Why:**
  - One source for the whole forecast. The case for the split, that surveys are thin in districts, was wrong: Kev only
    knows the state, so its district numbers are its state numbers shifted to each district, as d0's would be.
  - Kev was closer on the only test (held-out OH, NC and TX against their 2024 votes): 4.2 against 5.1 points per
    group once both are shifted to the state's level, within noise.
  - It changes little. A group's margin enters only the turnout part of news effects, and only as a pattern, since
    each race's groups are shifted to its level. On 29 Sep data, today's news effect in the three pilot races changes
    by 1–5%, and the 3 Nov forecast doesn't change. The two sources differ mainly on independents and weak partisans.
  - Caveat: the test scored the vote Kev learned (2024 presidential), while d0 comes from midterm Senate races.
- **Built** (`simlab/groups.py`, `simlab/statsday.py`; 3 tests):
  - `groups.build` takes Kev's margin wherever `simlab/kev_groups.json` has the state and group, and d0 elsewhere.
    `groups.json` names its source in `d_source`.
  - `python -m simlab.groups --kev ANSWERS` turns Kev's answers (`{run, states: {state: {group: d}}}`) into that
    file and adds the nation's: the states' margins weighted by 2024 presidential votes times the group's share of
    midterm voters.
  - statsday reads the file when it exists. Until the Kev session delivers it, every race stays on d0.
  - A trial run of 29 Sep on a copy of the data matches the real run exactly without the file.

## 2026-09-29 (Kev session): Kev back in; Kev's voter groups tested; House incumbency and district error fitted

- **Matteo, 29 Sep:**
  - keep Kev's weights;
  - Kev react-v2-2 runs in shadow mode on Modal (pilot first, then a daily sample sized to October's $18 serving reserve);
  - test ces-v3 against Statistics' voter-group numbers, then use it for the House districts;
  - reaction training stays closed, with shadow mode supplying the evidence;
  - start the House seats (A11).
  The serving key is Matteo's to create (Modal secret `kev-serve` and GitHub secret `KEV_API_KEY`); no deploy before it
  exists.
- **Kev's voter groups against Statistics'** (`python -m simlab.kevscore --groups ces-v3b`). The test covers the 28 party-ID x
  white/non-white x degree groups in OH, NC and TX: 60 of the 84 group-state pairs, those with at least 20 CES
  validated 2024 voters. It
  measures the error of each group's D-R margin in points, weighted by the group's voters (n x t):

  | | Kev ces-v3b | Statistics (d0) | Kev minus Statistics, 95% |
  |---|---|---|---|
  | as given | 5.1 | 7.3 | -4.4 to -0.4 |
  | both shifted to the state's level (as the engine uses them) | 4.2 | 5.1 | -2.1 to +0.3 |
  | by state, shifted: OH / NC / TX | 3.9 / 1.9 / 6.7 | 4.3 / 4.1 / 6.9 | |

  Kev is better in every state, but the engine-relevant (shifted) gap isn't conclusive. Averaging the two doesn't beat
  Kev alone (4.4). ces-v3a is close behind (4.5). Caveat: this scores 2024 presidential votes, and d0 comes from the
  2018/2022 midterms, while Kev learned 2024 patterns in the other 47 states. Part of Kev's edge is knowing 2024's
  shifts (Texas above all).
- **House fit** (`python -m simlab.housefit` → `simlab/house_params.json`; MIT House 1976-2024, 3,856 district pairs
  on unchanged lines). Model: margin = year effect + b × last margin + psi × incumbent + c × last incumbent.
  Incumbents are matched by person across the state, so renumbered districts keep their member. Each year is
  predicted from the others, given the national swing.
  - Incumbency is worth 4.4 points on 2014-2024 (7.4 on 1996-2024, 90% interval 5.6-9.3), shrinking over time. It
    agrees with the Senate's 4.1.
  - First-termers and senior members get the same effect (7.5 and 7.3; 4.9 and 4.2 on 2014-2024), so the Field
    Guide's "first-termers get half" isn't supported.
  - District error when unpolled, 2014-2024: SD 8.5 (90% 7.6-9.4); 7.9 with an incumbent running, 11.3 for open
    seats, 8.4 for seats predicted within 15. That fits the placeholder 7-9, with open seats wider.
  - These errors come from a model built on the previous House result. The forecast uses presidential lean on the
    current lines, so treat them as a guide until house.py is checked on 2024.

## 2026-09-29 (Engine session): every race by tier from 12 Oct; the daily job can't be skipped; poll stories caught

- **Scale-up built (roadmap A13).** `simlab/newsraces.json`, built from Statistics' `races.json`, gives every race its
  description and news queries. The news step selects by the previous day's tier:
  - simulate: 5 race stories and 3 national stories a day;
  - watch: its 2 biggest race stories, and the nation's move for national news (Statistics built that part);
  - statistics: none.
  House seats get "their district's U.S. House race" wording once Statistics adds them. The daily job runs the pilot
  races until 11 Oct and every race from 12 Oct. On a busy day that is about 13,500 GLM prompts, about 50 minutes and
  $0.16. Media Cloud asks for every race once its key is in. GDELT stays on the pilot races and the nation, because
  from GitHub it rate-limits a run's later queries: 1 or 2 of its 4 failed in each run of 28-29 Sep.
- **The daily job can't silently skip a day.** GitHub fired only 3 of about 17 hourly snapshot triggers on 28 Sep, so
  the daily job now triggers every 15 minutes from 09:47 to 14:47 UTC and runs once. A trigger delayed past midnight
  can't run the new day before its news window closes.
- **Poll stories caught.** Jev typed an approval-rating story as national news, and 2 of the 9 spot-check headlines
  that name a poll as something else. A story whose main headline is about a poll, a survey, an approval rating or a
  forecast is now a poll story, so it gets no reactions.
- **Cards no longer say "according to the headline"** (4 of 24 did on 29 Sep).
- **Reaction wording stays direct** (the backlash test Matteo approved on 28 Sep). Asking groups to think about how
  they react to the news itself lost accuracy on real events:
  - direction right on 85% of the 45 training events that moved opinion, against 92% for the direct wording;
  - on the 19 held-out events, 80% against 100%, and an error of 3.22 against 3.05 points;
  - size-tracking fell from 0.26 to −0.11.
  The direct wording already shows backlash where it's real: on 28 Sep, Trump's backing of Husted moved strong
  Democrats toward Brown and raised their turnout. On 15 stories picked for possible backlash (big money, prosecutions,
  polarising surrogates, former allies, controversial endorsements) and 3 controls, both wordings moved Democratic
  groups toward the Democrat and raised their turnout on Republican-helping money stories. The reaction-aware wording
  mostly added turnout everywhere (average size 0.52 against 0.30), as much on the controls as on the backlash stories.
  So it adds no signal specific to backlash. Results: `runs/backlash__glm.jsonl`; code: `simlab/events2.py backlash`.
- **A national copy of a race's own story counts for that race only** when its headline names that race's
  candidates. The national feed carried "Paxton, Talarico spar over gas tax", and Jev gated it relevant to Ohio.
- **Spot-check: all 32 of Matteo's stories count.** All 32 were saved on the page; the local copy held only the 16
  exported on 28 Sep, and now holds all 32. On all 32:
  - Jev matched 102 of 126 labels and GLM 95 (on the first 16: 54 and 50 of 63);
  - event type: Jev 29 of 32, GLM 26 (Jev's misses: two "other" stories typed national, one endorsement typed other);
  - relevant: Jev 29 of 30, GLM 28 (two "unsure" answers left out); side helped on its face: Jev 26 of 32, GLM 24;
  - attention: both overrate it. They said "some" where Matteo said "very little" on 10 (Jev) and 13 (GLM) of 32.
  So Jev keeps the labels (Matteo's decision of 28 Sep).
- **Attention weights:** the spot-check couldn't test them. 29 of the 32 stories had one outlet in the old Google News
  store, so the coverage formula gave almost all of them the same score. To re-check in the pilot week on real
  coverage.
- **House data for A11** (without the Redistricting Data Hub, Matteo 29 Sep), in `data/house/` (local):
  - 2024 presidential results on the lines used in 2026, for all 435 districts, from The Downballot (9 Jul 2026). That
    includes the 181 seats in the 10 states with new maps: TX, MO, NC, AL, FL, LA, TN, OH, CA and UT;
  - ACS 2024 citizen adults by race and degree per district, from the Census API. These are the 2024 lines, so in
    the redrawn states a district number there is the old district. The Kev session says that is enough for 9 Oct.
  - The new plans' block files wait until after 9 Oct, and only for simulated seats in redrawn states.
- **Kev shadow mode** (Matteo reopened it, 29 Sep): the harness already writes shadow rows with `--kev URL`. The daily
  job will pass it once the Kev session sends the URL, the key's secret name and the daily sample size.

## 2026-09-29 (Statistics session): the weekly filter (roadmap A6, weekly part)

Matteo: "go ahead with the weekly filter". Built to stats-groundwork §5.7 and engine-design §3.3 (`simlab/weekly.py`):
- **News dials.** Each state, and the nation, gets two dials, switching and turnout: 1 means the polls confirm the
  simulated effect, 0 means they show none of it. They are learned from every poll since the stories began.
  - The likelihood is an exact quadratic in the dials; states pool with a national dial in closed form.
  - The prior matches the approved size ranges.
  - The Monte Carlo now draws each simulated election's dials from the result, replacing the fixed ranges, so the
    ranges tighten or move as the polls speak.
- **Fade speed:** the polls weigh five half-lives around Matteo's 5.5 days.
- **Surprise monitor:** flags races whose last week of polls surprised the forecast (p < 0.01), for the auditor.
- **Schedule:** Mondays from 12 Oct inside the statistics step; `python -m simlab.weekly` or `statsday --weekly` by
  hand. Output in `filter_weekly.json`; the dials in force go in each day's `params.json`.
- **Dry run on 29 Sep:** nothing learned yet, correctly: every story so far began after the last poll.
- **Fixes found on the way:**
  - races with no stories of their own weren't getting the national stories' effect, because empty story lists
    blocked the fallback; all 32 now carry it;
  - watch-tier races (from 12 Oct) keep the nation's national stories, and simulated races aren't counted twice (the
    Engine's point).
- **For Content:** `races[rid].today.movers` (today's stories, by today's effect), `forecast.news_dials`, and
  `if_weaker`/`if_stronger` now use the national dial's 10th/90th percentile.
- **Not built:** the demographic factor state and regional poll-bias terms, left for Matteo's call.
- The daily step takes about 36 seconds (12 level runs: two views, each with the parts per dial).

## 2026-09-29 (Engine session): the news day, a broken spending ledger, one story counted once

- **Every model call failed from the afternoon of 28 Sep.** Two programs wrote to the spending ledger
  (`runs/spend.jsonl`) at the same moment and left a broken line. Every paid call checks the ledger first, so every
  label failed and no story was selected. The ledger now skips a broken line. Lifetime spend is $1.67, which matches
  the key's usage on OpenRouter.
- **News between two daily jobs was never read.** The job read only its own day's snapshots, so news from about 09:00
  to 18:00 UTC the day before (the US morning and early afternoon) was lost. A day's news is now every article first
  returned by a snapshot run that started between 09:30 UTC the day before and 09:30 UTC that day, so each run is read
  once. The statistics step uses the same cutoff for polls.
- **GDELT rate-limits most of each run's queries.** On 28 Sep, North Carolina got nothing all day. Each query now asks
  for the last 24 hours, so one success a day covers a race, and the query order rotates each run. Media Cloud joins
  once its key is in.
- **One story was selected three times** (Trump travelling to Ohio for Husted). The same-event check only looked at the
  top 10 stories of both scopes together, and national stories pushed the copies out of it. It now checks every story
  the selection could pick.
- **Re-runs.** 28 Sep news was re-run on the new window (3 Texas stories). Its old reactions pointed at story ids from
  the Google News version, so they are kept aside as `reactions_dev5_old_event_ids.jsonl`. For 29 Sep: 517 articles,
  248 stories, 19 selected, 504 reactions from GLM, $0.05 in all.

## 2026-09-29 (Kev session): react-v2 failed; Kev stays out of reactions (Matteo's rule 4 of 28 Sep)

- First attempt (`react-v2`) was lost at step 420/598 when the laptop slept (container gone, no checkpoint), cost
  $0.97. Rerun as `react-v2-2` (run names cannot be reused), same data, $2.53. Total react-v2 spend $3.50 of the $5.
- On the 19 held-out real events, against GLM (the three checks for Kev to join the forecast):

  | check | GLM | react-v1 | react-v2-2 | pass? |
  |---|---|---|---|---|
  | direction on 13 clear events | 13/13 | 10/13 | 11/13 | no |
  | size-tracking (Spearman) | 0.287 | 0.00 | 0.20 | yes |
  | error after scaling (RMSE, points) | 2.32 | 3.26 | 3.30 | |
  | GLM + Kev averaged | | 2.61 | 2.63 | no (worse than 2.32) |

  Misses: Dobbs and the 2024 assassination attempt (Kev predicts no change; also missed by react-v1), and the 2026
  fuel spike (wrong way). Errors correlate 0.75 with GLM's, so averaging adds noise, not information.
- Null and party-swap checks still pass: no-change 0.955/0.965 on non-events; flip correlation 0.93, all signs flip,
  lean -0.016. Regression check on the base task: accuracy 0.865 on 417 public records.
- Four times the events (40 clear against 11) moved size-tracking from 0.00 to 0.20 but not direction or the averaged
  error, and a second run would not be "close" by the 28 Sep rule. Per rule 4, no further reaction runs before the
  election; GLM stays the only reaction model. This agrees with Matteo's 29 Sep
  call in CLAUDE.md (recorded at 10:42, after this run had finished): no Kev shadow mode and no Kev serving (B4) unless
  he reopens it.
- Files: `kev-finetune/runs/react-v2-2/`, `runs/{events,mirror,null}__kev-react-v2-2.jsonl`; data, reports and both
  console logs backed up to simlab-data `kev/react-v2/`.

## 2026-09-29 (Statistics session): news fades fast (5.5-day half-life for every story)

- **Matteo, 29 Sep:** news fades more than the 10-day curve. A long story goes from 100% to about 45% within a week,
  about 15% after two weeks and under 10% after three.
- **Built:**
  - every story now fades from its first day with a 5.5-day half-life, the closest single curve (41%, 17%, 7%; 2% by
    day 30);
  - a one-off story that drops out of the news also fades within about a day;
  - the economy and national events keep fading at the age rate after the news moves on.
- **Why the change also covers one-off stories:** under the previous rule, a one-off story kept full strength for as
  long as it stayed in the news, so a scandal covered for three weeks would have outweighed economic news.
- `simlab/move_params.json`: `age_half_life_days` 5.5, `half_life_days` {default: 1} (the drop once out of the news),
  `lasting_types` [economy, national]. On record in CLAUDE.md §5, engine-design §3.2 and stats-groundwork D19.

## 2026-09-29 (Statistics session): lasting topics fade from day one; "if the election were today"

Matteo, 29 Sep:
- **Fade times: yes, with lasting topics at 30 days, their importance falling throughout.** High in the first days,
  "after 3 weeks already not that important" but still a bit relevant. A literal 30-day half-life would still leave
  60% after three weeks, so lasting topics (`economy`, `national`) now fade from their first day, even while in the
  news, with a 10-day half-life:
  - full strength at first, about 60% after a week, a quarter after three weeks, an eighth after 30 days;
  - one-off stories are unchanged: full while in the news, then a 1-day half-life;
  - on the 3 Nov forecast this means stories from the last two weeks carry most of the simulation's effect.
- **Posts show both "if the election were today" and "on 3 Nov": yes.** `forecast.json` adds a `today` block to every
  race and to the Senate: win chance, margin range and the stats-only twin, with election day set to today (no time
  for opinion to drift, stories at today's strength). The daily step now takes about 20 seconds.

Also:
- **Orphaned reactions.** The Engine re-ran the 28 Sep news step at 17:19, after the harness had asked at 13:32. The
  story ids changed, so 19 of the 22 stories with reactions no longer match any news file and can't be placed in
  time. `moves.json` now lists them under `orphaned_events`, and the daily summary counts them. Flagged to the Engine.
- **Same snapshot on re-runs.** The statistics step reads the day's latest snapshot run before 09:30 UTC, the Engine's
  news cutoff, so a re-run later in the day reads the same polls as the day's job.

## 2026-09-28 (Statistics session): how long news lasts, independents, simulation tiers; decisions on record

Matteo's answers, later on 28 Sep (stats-groundwork §8):
- **How long news lasts (D19).** Matteo: most news lasts about a day unless it stays in the news; long-running topics
  (war, prices) last longer; an endorsement or a small scandal doesn't. Built:
  - a story keeps its full effect while it is in the news (`first_seen` to `last_seen`), then fades;
  - half-life 1 day for one-off types, 60 days for `economy` and `national`;
  - the 3 Nov forecast counts what is expected to remain of each story then; `story_effect` gives today's;
  - `movers` now rank stories by their effect on 3 Nov.

  On 28 Sep, most of the pilot races' stories were one-off (ads, candidates' policy news, endorsements), so the
  forecast now carries mainly the national and economic ones.
- **Senate independents (D16).** King and Sanders count with Democrats; the new independents are shown as
  independents. `forecast.json` adds `p_independents_decide`, the share of simulations where they hold the balance.
  The final presentation is decided later.
- **Simulation tiers (D20).** Statistics runs for every race; the simulation only where races are contested. Built:
  - a daily `tier` in `races.json` (simulate, watch, statistics);
  - a race runs on statistics alone only when the stats-only forecast, Cook and the market all call it safe;
  - the pilot races always simulate, and a race keeps its most competitive tier of the past week;
  - on 28 Sep: 13 simulate, 7 watch (Montana among them), 15 statistics only.

  The Engine's harness reads the previous day's tiers.
- **On record** (Matteo's OK): CLAUDE.md §5 block "Decided by Matteo, 28 Sep evening (statistics)"; engine-design
  §3.2 (how long news lasts, size ranges), §3.3 (daily update, Monte Carlo, tiers) and §7 (new fields).

## 2026-09-28 (Kev session): Matteo's answers on Kev react-v2; more real events (events3)

- Matteo, 28 Sep, "yes to all four":
  1. download UCSB's Gallup approval tables (Bush, Obama; 0.6 MB);
  2. download the Wikipedia national poll lists for 2008-2024 (1.9 MB, CC BY-SA);
  3. a Modal budget of at most $5 for react-v2: one run of about $2 after offline checks, a second only if the first
     comes close;
  4. if react-v2 still fails, Kev stays out of reactions, with no further reaction runs before the election.
  He also confirmed that the House seats (A11) are this session's.
- Diagnosis behind react-v2: react-v1 fitted its 26 training events at 0.96 on new personas (size rank 0.84) but not
  the 19 held-out ones, so the lever is the number of distinct events.
- New `simlab/events3.py` → `simlab/events3.json`: 112 events 2001-2024, none within 14 days of a test event. Measured
  with events2's fixed rule (days +5..+14 vs -7..-1, detrended, z from quiet days) on:
  - Gallup approval (each day is the mean of the last 14 days' readings, the one-pollster analogue of a poll average);
  - the national D-R margin from the Wikipedia poll lists, with events2's average.
  29 clear (|z| >= 1, detrended agrees, unconfounded), 34 no change, 38 confounded. With events2: 40 clear and 49
  no-change events, against react-v1's 11 and 15.
- `simlab/kevreact.py` builds `react-v2`:
  - events2 + events3, with 20 personas per event instead of 40;
  - 4 personas per null item and 5 per party-swap template;
  - 1,887 training records, 500 replay records;
  - the development file (the test bench) identical to react-v1's.
  Training started 28 Sep; Modal spend in September before it was $7.71 of $30.

## 2026-09-28 (Statistics session): Matteo's answers on the statistics decisions; news sizes as ranges; news moves every race

Matteo's answers, 28 Sep evening (stats-groundwork §8, D14–D20):
1. **Turnout size = switching size (0.21): yes, as a starting point only.** The sizes must stay flexible:
   - a range that can go up or down with evidence;
   - a traceable origin and route through the chain;
   - results not tied to one data point (the Hungary lesson).

   Built:
   - Each simulated election draws its own multipliers for the switching and turnout parts of every story effect,
     shared by all races in that election. They average 1; the 90% ranges are c_s 0.08–0.41 and c_t 0.05–0.53.
   - Each race in `forecast.json` gets a `news` block: its story effect, split into switching and turnout, and its
     win chance if news matters less or more (the 10th and 90th percentiles of both multipliers). The Senate block
     has the same for control.
   - `simlab/move_params.json` records where each size comes from, the files it passes through and what updates it:
     the weekly filter, from 12 Oct.
2. **Fat tails keep the fitted spread: yes**, with extremes tied to what the simulation says. The multipliers give
   races with strong simulated reactions wider, story-driven tails.
3. **"Democrats reach 51": brief first**, then Matteo decides. Options given: King and Sanders only; all independents;
   or three outcomes, with "the new independents decide" as the third. Recommended: three outcomes.
4. **Montana:** no three-way work while it isn't competitive; flagged, revisit if it tightens. The focus stays on
   competitive races.
5. **News should move races, polls or not.** Built: each race's story effects now go on top of the statistical level
   in full, where before they were scaled by the poll weight. Polls correct the level; a race without its own stories
   takes the nation's.
- **Matteo's question:** should the simulation run only where races are competitive, to save credits and compute?
  Proposed three tiers set daily from the stats-only forecast. Safe races would run on statistics and national news
  and be promoted automatically if they tighten. Open.
- **New evidence on how long news lasts** (`python -m simlab.moves --lasting`, stored in `simlab/move_params.json`):
  - for 44 calibration events, the shift seen 1–2 weeks after the event was still there 3–7 weeks later (share left
    1.01–1.11, 90% ranges 0.84–1.31);
  - moves on random dates kept 0.83–0.92;
  - the design's 10-day half-life would fade 90% of an effect in five weeks. Decision for Matteo (D19).

## 2026-09-28 (Statistics session): voter groups, moves and the daily filter (roadmap A3 groups, A6 daily)

- **Voter groups** (`simlab/groups.py`, 11 tests; `python -m simlab.groups --fit`) for all 50 states, DC and the
  nation.
  - `simlab/pimu.json`: persuadable and mobilisable shares (engine-design §9, due Thu 1 Oct) by state and group, from
    the CES 2018 and 2022 pre- and post-election waves, shrunk state → census division → nation.
    - pi: Senate voters who were unsure before or whose vote differed from their intention.
    - mu: registered respondents who were unsure about voting, or whose validated vote contradicted their intention.
    - Firm partisans come out at 3–9% persuadable and 6–15% mobilisable; independents at 26–42% and 17–50%.
    - The 2024 check is a little lower (a presidential year); self-reported turnout gives nearly the same mu.
    - Kev's House districts read this table.
  - `simlab/groups_base.json`: population share, midterm turnout and Senate vote for each group (stats-groundwork
    §5.5).
    - CPS citizens by white/non-white × degree, times the CES party mix, tilted to each state's 2024 result;
    - 2022 turnout with CES party odds ratios;
    - reproduces official 2022 turnout exactly.
  - `groups.json` shifts each race's group vote to its level daily.
- **Moves** (`simlab/moves.py`, 9 tests):
  - GLM's group reactions go through the §3.2 formula into race moves; each story counts once from `first_seen` and
    fades with a 10-day half-life.
  - Kev's shadow rows go under `shadow` and never move the forecast.
  - c_s is fitted on the 45 calibration events at 0.21 (0.19–0.23 leaving any one event out; typical miss 0.9 points).
    GLM's direction explains about a sixth of the variation between events.
  - c_t has no data yet: set equal to c_s as a prior (`simlab/move_params.json`). It needs Matteo's call.
- **Daily filter** (roadmap A6, due Fri 2 Oct):
  - It re-runs the poll average each day with every poll compared against the latent less the story effects in force
    on its date, then adds today's effects back.
  - This matches the recursive filter of stats-groundwork §5.6 for this linear model. Late polls land on their field
    dates, re-runs reproduce exactly, and the stats-only twin is the same code with no moves.
  - The result is `filter_state.json`; the Monte Carlo now runs the headline on it and the twin on `levels.json`, with
    the same random numbers. Movers come from the stories' effects so far; the poll-average benchmark comes from the
    twin.
- **The daily step** (`python -m simlab.statsday`, about 10 seconds) now writes the whole chain: polls, races, levels,
  groups, params, moves, filter state, forecast and draws. On 28 Sep, 27 story effects reached OH, NC, TX and the
  nation, each a fraction of a point.
- **Rehearsal gap closed:** the levels read their fixed inputs from `simlab/levels_inputs.json`, frozen from the MIT and
  538 files with `python -m simlab.levels --freeze`; the output is identical. The daily job needs no gitignored file.
- **Poll table (A3 leftovers):**
  - Every row now carries `first_seen`, the snapshot where our engine first saw it, carried day to day.
  - Two VoteHub entries for Montana listed Bodnar 50, Alme 50: placeholders, now dropped.
  - Alaska's polls are head-to-heads, so they need no transfer rule.
  - Montana stays two-way (Bodnar v Alme) for the pilot although Bankhead polls about 25%; Alme leads both by about
    20 points (stats-groundwork §7).
- **Known limits:**
  - Race-specific story effects reach only races with polls, scaled by the poll weight. Races without polls move only
    with the nation, through the fundamentals.
  - Moves add no uncertainty of their own.

## 2026-09-28 (Statistics session): Monte Carlo and the statistics daily step (roadmap A7)

- `simlab/montecarlo.py` was built test-first (`tests/test_montecarlo.py`, 20 tests) to stats-groundwork §5.8 and
  engine-design §3.3 and §7:
  - 40,000 draws, seeded from the run date. A race's margin = its level + national + census-division (1.1) + state
    (2.6) + race-only error. The national variance and each race's SD come from `levels.json`; the race-only error
    takes the rest.
  - Student-t with 8 df and one shared scale per draw. The scale keeps each race's fitted SD, so only the tails fatten
    (unscaled, every SD would grow 15%).
  - Correlation floor 0.25: pairs below it are lifted, then the matrix is projected back to a valid one. On 28 Sep, 21
    pairs were lifted, all involving races without polls.
  - Benchmarks, display only:
    - `poll_avg` from the levels;
    - `market`: the challenger's Kalshi and Polymarket bid-ask midpoints, normalised over the race's candidates and
      averaged across the two;
    - `cook`: the Cook column of the Wikipedia predictions table.
  - Senate: `p_r_50plus` counts the Vice President's tie-break. The second line, `p_d_caucus_51`, counts only King and
    Sanders as caucusing with Democrats; new independents are shown on their own. Seats not up: 31 R, 32 D, 2 I.
  - Added fields: `left_party` (D, or I where the challenger is an independent) and `w_polls` per race; `house` stays
    null until A11. `draws.json` holds every 40th draw in the shape the post kit reads.
- `simlab/statsday.py` (`python -m simlab.statsday --date D --data <data>`, 6 tests) is the daily job's statistics step:
  - It reads the day's latest snapshot run, or `--snapshot HHMM` to re-run a saved day exactly.
  - It writes `polls.csv`, `races.json`, `levels.json`, `forecast.json` and `draws.json` to `derived/D/` in about
    14 seconds.
  - Until the filter exists, the headline and the stats-only twin run on the same levels; `forecast.json` flags this.
- First run: 35 races. Win chances match the analytic Student-t within simulation error, and every draw totals 100
  seats. The post kit read both files; its only flags were the 7 races without polls and a caption too long for 35
  races.
- **House seats (A11) moved to the Kev session** (Matteo's call, recorded by the roadmap session). The interface is
  agreed with Kev:
  - `house_levels.json` holds all 435 seats in the `levels.json` race shape, on the same national block;
  - `house_groups.json` and `house_races.json`;
  - `simlab/house.py` `run(day, data, levels)`, which statsday calls right after the levels.
  - Persuadable and mobilisable shares will come from a state table, `simlab/pimu.json`, for all 50 states: many
    competitive seats are in states without a Senate race.
- Gap before the GitHub Actions rehearsals (3 Oct): the levels read the MIT files, which are gitignored. Their fixed
  inputs (lean, candidate records, the national House vote by year) need to be frozen into a committed file.

## 2026-09-28 (Content & site): labs.scaliastudio.dev

Matteo confirmed (relayed by the roadmap session): the Scalia-side address is labs.scaliastudio.dev, replacing
research.scaliastudio.dev. The forecast site goes at labs.scaliastudio.dev/midterms; notapoll.org's own website comes
later, and images keep showing notapoll.org. Updated content-plan.md, accounts-setup.md, infrastructure.md and
research/content-ai-tech.md (older entries below keep the old address as history). CLAUDE.md §5 still says research.;
its edit waits for Matteo's own OK.

## 2026-09-28 (Content & site): notapoll.org on every image; profile kit

Matteo's decisions, relayed by the roadmap session (evening): he bought notapoll.org; images and videos show it; the
site comes later and the social accounts first; Instagram Creator @notapoll.org with Threads, X @notapoll, Bluesky
@notapoll.org via a `_atproto` TXT record; scheduling on Buffer's free plan (X, Threads, Bluesky) and Instagram's own
scheduler. This reverses the earlier "never notapoll.org" rule and today's "Scalia domain" answer.
- The header wordmark on every image now reads "NotAPoll.org" (`frame.SITE = "notapoll.org"`).
- `simlab/publish/brand.py`: avatar, X header, Bluesky banner, the pinned "Start here" carousel, bios.
- `docs/accounts-setup.md`: the setup checklist for Matteo.
- Open: labs.scaliastudio.dev or research.scaliastudio.dev for the Scalia-side address (unchanged until Matteo says).

## 2026-09-28 (Content & site): layouts picked, election purple, special editions, Scalia domain

Matteo's answers, later on 28 Sep:
- **Daily race cards:** The Stamp, Where everyone stands, 100 futures (the kit's default).
- **Palette:** Lab Notebook stays the daily theme but takes more of the election colours: purple `#6D2E8C` replaces
  ochre as the simulation's own colour and marks toss-ups (zone fill, lilac highlighter, purple verdict stamps), the
  label strip goes deep indigo, and a blue-purple-red swing band runs along it. Purple passes the colour-blind check
  beside the party blue and red (deutan ΔE 9.5); lighter violets failed it.
- **Riso Print retired.** Sundays and special days get five special editions instead, each with its own layout and
  palette (`simlab/publish/specials.py`, `docs/publishing.md`): The Ballot, The Main Event, The Seismograph, The Chamber,
  The Map. Drafts with invented numbers, for Matteo to pick from.
- **Domain:** no notapoll.org; the project stays on research.scaliastudio.dev/midterms.
- **Bio tagline:** Matteo wants it more epic and iconic; options proposed.

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

## 2026-09-28 (Engine session): Matteo's answers on news sources, CLAUDE.md, push, secrets, schedule

Matteo answered yes to all five:
1. **News sources:** GDELT and Media Cloud replace Google News, because Google News's feed terms allow only personal
   news readers. Google News is dropped from the snapshots and the pipeline; the files already saved are ignored. Matteo
   creates the free Media Cloud account and adds the key.
2. **CLAUDE.md §5:** gets the engine decisions of 28 Sep.
3. **Push:** the local commits go to the public repo, as planned.
4. **OpenRouter key:** Matteo adds it as the GitHub secret `OPENROUTER_API_KEY`.
5. **Schedule:** the daily job's schedule is switched on at the pilot on 5 Oct (`PIPELINE_ON`), with his OK then.

## 2026-09-28 (Engine session): news pipeline built (A4)

- `simlab/newsday.py` turns each day's snapshots into `derived/<date>/events.jsonl`, the engine-design §7 contract, plus
  `news_private.jsonl` with the raw headlines. It has 19 unit tests and runs in about 2 minutes.
  - Stories are clustered, carried over across days with stable ids, and labelled by Jev with outlet names removed.
  - The labels include the new "whose voters it fires up or puts off".
  - Attention comes from coverage and pageviews.
  - DeepSeek writes neutral cards, with GLM as fallback.
- **First run** (28 Sep snapshots): 325 articles became 227 stories. 8 per pilot race and 3 national stories were
  selected for reactions. Cost was $0.03, and about $0.02–0.03 a day from now on.
- **Fixes after that run.** It showed double counting and junk, so:
  - Headlines under four words are dropped.
  - Non-events (round-ups, TV listings) are flagged by the card writer and never selected.
  - National copies of a race's own story don't count twice.
  - Same-event duplicates in other words are checked in pairs, which merged the three reports of Trump's Ohio trip.
  - Asking the model to group a whole list at once over-merged stories on the same topic, so it was replaced by the
    pairwise check.
- **Known limits:**
  - One near-duplicate is left: two reports of Brown's Mahoning Valley visit.
  - The "puts off" label seems to be read as "dislikes the news" rather than "less likely to vote". It is descriptive
    only and doesn't move numbers.
  - The attention weights are a first guess.
  - News queries cover only the pilot races until `snap.py` is scaled up.
  - The development runs used the Google News items already saved; the pilot's sources depend on Matteo's decision.

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
