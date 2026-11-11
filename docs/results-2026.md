# How NotAPoll did: the 2026 midterms against our forecast

Written 6 Nov 2026, three days after the election. **The results are provisional.** Alaska and Mississippi are uncalled,
about 25 House seats are still counting, and no state has certified. Vote shares come from AP, network and state counts,
gathered by three research passes on 6 Nov (files in the coordinator's scratchpad: `senate_results.json`,
`house_results.json`, `forecasters.json`). Recheck every number against certified results before the final scorecard.
Our numbers are the final 3 Nov run (`simlab-data/derived/2026-11-03/forecast.json`), compared with:
- the "polls alone" twin (stats only);
- the old poll-correcting rule (`scoring/poll-filter/2026-11-03`);
- the 12 Oct launch;
- prediction markets;
- Cook ratings, scored as Solid 97, Likely 85, Lean 70, Toss-up 50.

**Refresh, 11 Nov (second-source check):**
- **Alaska:** still uncalled. Peltola leads on first choices, about 48.6 to 47.5; the ranked-choice count is on 18 Nov.
- **Mississippi:** still uncalled. Colom (D) leads by about 2,600 votes (0.27 points). We gave Hyde-Smith 94 in 100, so if
  Colom wins it's a fourth wrong call.
- **House:** the Democratic majority is confirmed, with about 254 seats called.
- **Forecasters:** confirmed except the Economist: 53 via Vote-Scope on 2 Nov, against 56 on its own page on 27 Oct.
- **Model spend:** the $18 is the daily runs only. The key's total including tests is about $23.

## 1. What we did

- A live forecast for all 35 Senate races and all 435 House seats, every morning from 12 Oct to 3 Nov: 23 public runs,
  38 counting the pilot week.
- About 45,000 news articles read, and 135,000 reactions from voter personas built from real survey answers.
  Total model spend $18 across every run, $15.55 of it in the public period.
- From 14 Oct, simulation only: polls set the 12 Oct start, and after that only the simulation moved races. A weekly
  check compared our moves with the polls' moves.
- 128 posts across Instagram, Threads and X. About 90,000 views: Threads 48,090, Instagram 41,717 (26,270 accounts
  reached, summed per post), X 267. The website had 6,500 visits in its first 9 days.

## 2. The headline result

**Both chambers right, but we underestimated the size of the Democratic wave, and we were less confident than
everyone else.**

| | Our final forecast | Result (provisional) |
| --- | --- | --- |
| Senate | Democrats control in 59 of 100 (Republicans 50+ in 39) | Democrats 54, Republicans 46 (AK, MS uncalled) |
| Senate: Democrats at 54 or more | 6 in 100 | yes |
| House | Democrats win in 63 of 100; median 222 D seats (80% range 205–247) | Democrats about 256 (253 called): single source, not confirmed by a second check on 6 Nov |
| House: Democrats at 253 or more | 7 in 100 | yes |

Other forecasters' final chance of Democratic Senate control:
- Silver Bulletin 80, FiftyPlusOne 79, Split Ticket 77, Race to the WH 78, DDHQ 64, the Economist 53;
- Polymarket and Kalshi both 77.

We were the second least confident; only the Economist was lower. The markets gave Democrats 94 in 100 for the House;
we gave 63.

## 3. Senate, race by race (33 called races)

| Scored on the 33 called races | Right calls | Brier (lower is better) | Average margin error | Bias (− means Democrats underrated) |
| --- | --- | --- | --- | --- |
| Prediction markets | 32/33 | 0.039 | — | — |
| **Polls alone (our stats-only twin)** | 30/33 | 0.052 | 6.1 | −4.9 |
| Old rule (polls keep correcting) | 30/33 | 0.055 | 6.1 | −4.9 |
| **NotAPoll (simulation only, published)** | **30/33** | **0.060** | **6.3** | **−5.2** |
| Our 12 Oct launch numbers | 30/33 | 0.066 | 6.4 | −5.4 |
| Cook ratings | 27/33 + 5 toss-ups | 0.068 | — | — |
| Raw poll average (27 races with polls) | — | — | 5.9 | −3.6 |

The rows show New Mexico added by hand: a safe Democratic hold that every source called right and that the scoring
script skipped over a name mismatch. Its Brier is near zero, so the Brier values come from the script's 32 races.

The competitive races (left = the Democrat or independent challenger):

| Race | Our chance for the left candidate | Polls alone | Markets | Our margin | Actual margin | Our call |
| --- | --- | --- | --- | --- | --- | --- |
| NC | 95 | 96 | 98 | +8.8 | +20.0 | right |
| NH | 94 | 95 | 94 | +8.1 | +14.0 | right |
| MN | 86 | 88 | 91 | +5.4 | +10.4 | right |
| MI | 83 | 85 | 80 | +4.8 | +7.1 | right |
| ME | 63 | 74 | 73 | +1.7 | +6.9 | right |
| TX | 61 | 65 | 74 | +1.3 | +12.2 | right |
| OH special | 58 | 56 | 71 | +1.0 | +5.0 | right |
| KS | 43 | 47 | 63 | −0.9 | +5.2 | missed |
| IA | 43 | 42 | 53 | −0.9 | +4.2 | missed |
| NE | 21 | 20 | 32 | −4.6 | −7.2 | right |
| SC | 17 | 25 | 32 | −5.6 | +4.5 | missed |
| FL special | 13 | 8 | 15 | −5.8 | −2.9 | right |
| LA | 7 | 12 | 8 | −9.6 | −1.8 | right |

Uncalled:
- **Alaska:** we had Peltola at 48 in 100 with a margin of −0.3. The first count is +0.3, and the ranked-choice result
  may go to Sullivan. Either way, very close to us.
- **Mississippi:** we had Hyde-Smith at 94 in 100 with a margin of −10.4. It's a near tie. This is our biggest margin
  miss, whoever wins.

Interval check: the actual margin fell inside our 80% range in 24 of 32 races, so we were slightly too narrow. All 8
races outside the range missed on the Democratic side, including Republican wins in Alabama, Tennessee and West Virginia
that were closer than our range allowed.

## 4. What the simulation got right and wrong

This is the experiment's real question.

- **Direction: right on the national picture.** The simulation's news effects pointed toward the Democrat or
  independent challenger in 29 of 32 races. The results beat the polls toward the same side in 28 of 32.
- **Race by race: no signal.** Which races the simulation pushed harder had nothing to do with which races beat their
  polls more: the correlation is −0.01. The personas sensed the national mood, but not where it would land hardest.
  Part of the uniform tilt may come from the correction we add for GLM's measured Republican lean (+0.08 on its support
  scale for every group).
- **Size: about ten times too small.** In the ten competitive races, the simulation moved races by 0.4 points on
  average; the results beat our polls-alone number by 4.5. Three design choices kept moves small:
  - stories fade with a 5.5-day half-life;
  - only the persuadable and mobilisable share of each group counts;
  - sizes are calibrated on historical events, averaging 0.21.
  Together they damp everything. This is the Hungary lesson again: the simulation stayed close to where it started.
- **The start locked in the polling miss.** The 12 Oct start already underrated Democrats by 5.4 points. The polls
  missed by 3.6 points in the same direction (Texas by 9.5, Georgia by 9.4, North Carolina by 8.6). Our fundamentals
  blend added more Republican lean on top. One suspect: the generic ballot is lowered by its historical 2.8-point
  overstatement of Democrats where it feeds the fundamentals; in 2026 it understated them.
- **Simulation only against polls alone: roughly level, slightly behind on confidence.**
  - Same calls: 30 of 33 each. Both had Iowa and Kansas just under a coin flip (we had 43 and 43; polls alone 42 and
    47), and both missed South Carolina.
  - On margins it's nearly a tie: average miss 6.3 points against 6.1, and the simulation was closer in 19 of 32 races.
  - On the probability score, polls alone did slightly better (Brier 0.052 against 0.060). The gap is small but
    consistent: in 99% of resamples, polls alone came out ahead.
  - Four races make up most of the gap: South Carolina, Maine, Kansas and Texas. In each, the polls moved toward the
    Democrat after 12 Oct, while our start stayed frozen and the simulation moved too little to follow.
  - Fair public line: "we finished level with polls on the calls and slightly behind on confidence; both missed the size
    of the wave."

## 5. House

- **Control right:** Democrats at 63 in 100. **Size well short:** median 222 D seats against about 256.
- On the 45 competitive seats we have results for, we called 20 right. All 25 misses were Democratic wins in seats we
  leaned Republican: NJ-2, TX-23, CO-5, KY-6, NV-2, OH-10, PA-8, MT-1, MO-2, WI-3, MI-4, the three Iowa seats and others.
- On the 15 seats with margins so far, Democrats beat our margin by about 9 points.
- District news only began on 15 Oct, and only for the 40 closest seats.
- The House data is the least complete. Recheck it before posting seat-level claims.

## 6. How to improve it

1. **Re-fit the size of moves on 2026.** We now have three weeks of reactions and the results. Fit the scale and the
   fade so that news can build a lasting national mood instead of fading within days. Test it on the blind track (no
   2026 polls) that CLAUDE.md planned.
2. **Race-specific signal.**
   - Score it with the race-level correlation, which is zero today.
   - Use more local news and state-specific personas.
   - Check whether Kev's shadow answers had race signal where GLM had none. The Kev rows exist for every day.
3. **The starting point.**
   - Drop or re-check the 2.8-point generic-ballot correction.
   - Let early-vote data move the start. Early vote showed Democrats 39.5% to 32.4% across 47 states, and we had NC and
     TX files.
   - Treat the national environment as something the simulation estimates, not a fixed input.
4. **Turnout.** The wave was driven by enthusiasm and turnout, which is exactly what the personas were meant to
   capture, yet our turnout moves were small. Give turnout reactions their own calibration.
5. **Wider national uncertainty.** Our 80% ranges held 75% of results, and every miss went the same way.
6. **Operations:**
   - Switch off `PIPELINE_ON`: it's still running after the election, and the 5 Nov run failed.
   - Fix the GLM host-drift alarm.
   - The daily-approval bottleneck left 3 silent days (18–20 Oct).

## 7. What to post (closure)

Proposed series, all for Matteo's yes:
1. **"Our report card"** (carousel), the day results are final enough, with "provisional" on it:
   - both chambers right;
   - 30 of 33 called Senate races right;
   - missed Iowa, Kansas and South Carolina;
   - underestimated the wave.
2. **"How we compare"**: the Brier ladder in plain words. Markets best, then our polls-alone twin, then us, then Cook.
   Say plainly that the simulation-only version did slightly worse than polls alone.
3. **"What the voter personas sensed"**: they leaned the right way in 29 of 32 races, but moved about a tenth as far as
   the voters did, and didn't know which races would move most.
4. **"What we'd change"**: the five fixes above, in human words.
5. **Final scorecard on the site's track record page** after certification (AK, MS and the House count). Use one honest
   line in every post: "provisional results, final scorecard after certification".

Wording rules: no dunking on polls (they missed too, by 3.6 points), and no overclaiming the direction finding (it was a
national tilt, not race skill).
