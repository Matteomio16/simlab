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
| Statistics | ok; `orphaned_events` 0; `deselected_pairs` 0; 35 races | 25 stories, 35 races; 13 s |
| Post kit | ok; `problems` 0; the five pilot races featured | 35 races, 0 problems; 14 s |
| Whole job | under 45 minutes; spend under $0.50 (`run.json` → `spend`) | 12 min, $0.07 |
| Push | a "Daily run <day>" commit in simlab-data with `derived/<day>/run.json` | done |
| Once a day | GitHub's own fallback trigger later that morning is skipped ("has already run") | not yet seen |

## Sunday 4 Oct: failure drills

Run each by hand (Actions → daily → Run workflow, with the day), after the day's scheduled run.

1. **The same day again.** News gives the same event ids; the harness asks nothing new; statistics shows
   `deselected_pairs` 0. Pass: every step ok, no new reaction rows.
2. **Kev down.** Set `KEV_URL` to a wrong address for one run. Pass: the log says "kev: not asked today", GLM's rows
   are complete, the job passes. Put the right address back.
3. **No new news.** Run a day whose snapshot folders are empty. Pass: news ok with 0 selected, statistics and the kit
   run on the polls alone.
4. **Budget cap.** One run with `SIMLAB_BUDGET_USD` at 0.01. Expected: labels and cards fail softly, nothing is
   selected, the job still ends. Check that the summary makes the missing news obvious. If it doesn't, Engine adds an
   alert before 5 Oct.

## Who checks what

| Session | Checks |
| --- | --- |
| Engine | the Worker and the news job, the news and reactions steps, `run.json`, spend, drills 1-4 |
| Statistics | the statistics step: `forecast.json`, `moves.json`, orphaned and deselected counts, whether the numbers make sense |
| Content & site | the post kit: slides, captions, `problems` 0 |
| Kev | Kev's shadow rows, the snapshot and early-vote jobs |
| Matteo | go or no-go for the pilot on Mon 5 Oct, after both days |
