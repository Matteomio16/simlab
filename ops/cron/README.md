# simlab-cron: start the workflows on time

GitHub fires this repository's scheduled workflows only every 5-9 hours (28-29 Sep 2026), whatever the cron says. It
does run a workflow at once when asked through its API. This Cloudflare Worker asks at fixed times (free plan):

| When (UTC) | Workflow | Notes |
| --- | --- | --- |
| every 15 minutes | `news.yml` | GDELT's most overdue queries and the RSS feeds |
| every 3 hours at :07 | `snapshot.yml` | polls, Wikipedia, markets, pageviews |
| 09:47 | `daily.yml` | with `scheduled=true`: runs only if `PIPELINE_ON` is `true` and the day hasn't run yet |

GitHub's own schedules stay in the workflows as a fallback.

## Setup (Matteo, once, about 10 minutes)

1. GitHub → Settings → Developer settings → Fine-grained tokens → Generate new token:
   repository access "Only select repositories" → `Matteomio16/simlab`; permissions → Actions: Read and write.
   Nothing else. Copy the token.
2. In this folder:
   ```
   npx wrangler login
   npx wrangler deploy
   npx wrangler secret put GH_TOKEN
   ```
   (paste the token when asked; it never goes into a file or a chat).
3. Check the next quarter-hour: the news workflow's runs page shows a run started by `workflow_dispatch`.

To stop it: `npx wrangler delete`, or remove a line from `crons` in `wrangler.toml` and deploy again.
