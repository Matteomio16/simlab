# A10 rehearsals, Sat 3 - Sun 4 Oct: what to run, what passes, who checks

The baseline is the first run of the whole chain on GitHub Actions: 29 Sep, run 36629024522 (manual, day 2026-09-29,
the five pilot races). It passed every check below.

## Before Saturday

| Item | Who | State on 29 Sep |
| --- | --- | --- |
| The scheduler Worker (`ops/cron`) is deployed, so the news job runs every 15 minutes | Matteo | live since 29 Sep 21:13 UTC (first dispatches: earlyvote 21:13, news 21:15) |
| Secrets `OPENROUTER_API_KEY`, `KEV_API_KEY`, `SIMLAB_DATA_DEPLOY_KEY` | Matteo | all set |
| Variables `PIPELINE_ON=true` (any time: scheduled runs start on 1 Oct by themselves) and `KEV_URL` (Kev shadow) | Matteo | not set |
| The OpenRouter cap raised to $20, and `SIMLAB_BUDGET_USD=19` in `.env` (local lifetime cap); `daily.yml` keeps $2 per run | Matteo | cap raised; `.env` line to add |
| Every session has moved its local `simlab-data/derived/` aside, then pulled: the job commits `derived/<day>/` and untracked local copies block `git pull` | all | Engine done (backup in `simlab-data/derived_local/`) |
| The news job has run for at least a day: its page shows runs every 15 minutes, each saving the RSS feeds and 1-3 GDELT queries | Engine | one manual run on 29 Sep: 3 feeds and 2 GDELT queries saved |

## Saturday 3 Oct: the scheduled path

The Worker starts `daily.yml` at 09:47 UTC with `scheduled=true`. Nobody starts anything by hand.

| Step | Passes when | Baseline (29 Sep) |
| --- | --- | --- |
| Start | the run starts by 10:00 UTC, event `workflow_dispatch`, and the `Due?` step says run | manual start |
| News | ok; over 200 articles; each pilot race has at least one selected story; no label errors | 517 articles, 248 stories; selected OH-S 5, NC 5, TX 6, IA 3, ME 3, US 3; 26 cards; 47 s |
| Reactions | ok; `failed` 0; parse errors under 1% of rows; rows = 28 × the selected pairs not asked before | 700 rows, 0 failed, 1 parse error; 10.5 min |
| Kev shadow (if `KEV_URL` is set) | rows with `model: kev, shadow: true`, `failed` 0; the job passes even if Kev is down | tested locally: 28 rows in 13 s after a 51 s wake-up |
| Statistics | ok; `orphaned_events` 0; `deselected_pairs` 0; `ungrouped_races` 0 (reactions for a House seat without voter groups); 35 races | 25 stories, 35 races; 13 s |
| Post kit | ok; `problems` 0; the five pilot races featured | 35 races, 0 problems; 14 s |
| Whole job | under 45 minutes; spend under $0.50 (`run.json` → `spend`) | 12 min, $0.07 |
| Push | a "Daily run <day>" commit in simlab-data with `derived/<day>/run.json` | done |
| Once a day | GitHub's own fallback trigger later that morning is skipped ("has already run") | not yet seen |

## Sunday 4 Oct: failure drills

The scheduled run comes first. Sunday is the post kit's first video day (`--reel auto`: a 9:16 video of the first
featured race). Pass: the kit's summary has `"reel": true` and `problems` 0, and the job is still under 45 minutes.

Then run each drill by hand (Actions → daily → Run workflow, with the day).

1. **The same day again.** News gives the same event ids; the harness asks nothing new; statistics shows
   `deselected_pairs` 0. Pass: every step ok, no new reaction rows.
2. **Kev down.** Set `KEV_URL` to a wrong address for one run. Pass: the log says "kev: not asked today", GLM's rows
   are complete, the job passes. Put the right address back.
3. **No new news.** Run a day whose snapshot folders are empty. Pass: news ok with 0 selected, statistics and the kit
   run on the polls alone.
4. **Budget cap.** One run with `SIMLAB_BUDGET_USD` at 0.01. Expected: labels and cards fail softly, nothing is
   selected, the job still ends. Check that the summary makes the missing news obvious. If it doesn't, Engine adds an
   alert before 5 Oct.
5. **The weekly filter** (Statistics). It first runs for real on Mon 5 Oct, the pilot's first day, so force it once on
   Sunday's outputs: `python -m simlab.statsday --date 2026-10-04 --data ../simlab-data --weekly` on a scratch copy.
   Pass: it writes `filter_weekly.json`, the learned dials and the GLM support offset stay inside their priors, and
   the step takes under 5 minutes.

## Wednesday 7 Oct: the full-scale rehearsal (Matteo, 29 Sep)

Every Senate race and every simulated House seat, once, before the full run starts on 12 Oct. After the day's scheduled
pilot run has finished, Engine starts Actions → daily → Run workflow with the day 2026-10-07 and `full_rehearsal`
ticked. The run works on a copy of the data and saves to `rehearsal/2026-10-07-all/` in simlab-data: the pilot's record
for the day stays as it was, and a rehearsal is never published.

| Step | Passes when |
| --- | --- |
| News | ok; every simulated race and House seat has at least one selected story (national ones count); stories from a state's House query selected only for the seats they are about; no label errors |
| Reactions | ok; `failed` 0; parse errors under 1% of rows |
| Kev shadow | rows for Senate races and House seats; the job passes even if Kev is down |
| Statistics | ok; `orphaned_events` 0; `deselected_pairs` 0; `ungrouped_races` 0; the simulated House seats in `moves.json` |
| Post kit | ok; `problems` 0 |
| Whole job | spend under the $2 per-run cap (`run.json` → `spend`); its length sets when the site updates each day from 12 Oct |

If the spend comes near $2 or the job runs past about 2 hours, Engine raises the per-run cap or the thread count
before 12 Oct and tells Matteo.

## Spend and the OpenRouter key's $20 cap (projection of 30 Sep, after the test run)

The cap stays at $20 and everything must fit inside $19 (Matteo, 30 Sep). Spent so far: $2.20 (OpenRouter's own
count for the key, 30 Sep afternoon). The 30 Sep pilot-scale test run cost $0.135: news $0.03, reactions $0.105.

| Period | Days | GLM on today's hosts | GLM on OpenInference first |
| --- | --- | --- | --- |
| Pilot and dry runs, 1-11 Oct | 11 | about $1.30 | about $0.80 |
| Full-scale rehearsal, 7 Oct (every story new) | 1 | about $1.10 | about $0.60 |
| Full run, 12 Oct - 3 Nov (about $0.66 or $0.41 a day) | 23 | about $15.20 | about $9.40 |
| Total by 3 Nov, with what is spent | | about $19.80: economy from about 28 Oct | about $13 |

- **Why the costs rose.** Since about 30 Sep GLM's hosts require reasoning ("mandatory for this endpoint", 11-36
  tokens a call), so a group row (4 prompts) costs $0.000134, against $0.00005 on 29 Sep. The answers held: re-asked
  the 64 historical events of 27 Sep, they correlate 0.96 (training) and 0.94 (held-out) with the old ones.
- **The cheaper host (Matteo's decision).** OpenInference runs the same model at the same 4-bit precision for
  $0.000013 a call instead of $0.000031. Its answers to the same 64 events correlate 0.95 with the 27 Sep ones on both
  sets, with the direction right on 92% (training) and 100% (held-out) of the events that moved opinion, the same as
  on 27 Sep. It limits how fast we can ask, so today's hosts stay as fallbacks. It saves about $0.25 a day at full
  scale.
- **Built (30 Sep):**
  - A state's House seats are asked each story once.
  - Only the 50 best-covered new national stories a day are labeled.
  - The safeguard: from $17 of lifetime spend the day runs in economy (watch races get no stories; 3 race and 2
    national stories for a simulated race), and from $19 on the polls alone (no model calls). The day's mode and
    the key's spend are in `run.json` → `budget`.
- **Ruled out:**
  - Asking each question in one option order: it halves GLM's cost, but on the 19 held-out events it got the
    direction right on 87% instead of 100%.
  - Kev duplicates: Kev runs on Modal, not on this key.
- **Small levers left:** 25 national stories a day instead of 50 (about $0.02 a day), and watch races on
  statistics alone (about $0.01). Economy mode uses both.
- **Check:** the 7 Oct rehearsal's `run.json` → `spend` is the full run's first and busiest day.

## Who checks what

| Session | Checks |
| --- | --- |
| Engine | the Worker and the news job, the news and reactions steps, `run.json`, spend, drills 1-4, the 7 Oct full-scale rehearsal |
| Statistics | the statistics step: `forecast.json`, `moves.json`, orphaned and deselected counts, whether the numbers make sense; drill 5 |
| Content & site | the post kit: slides, captions, `problems` 0 |
| Kev | Kev's shadow rows, the snapshot and early-vote jobs |
| Matteo | go or no-go for the pilot on Mon 5 Oct, after both days |
