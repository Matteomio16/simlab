# simlab-cron: start the workflows on time

GitHub fires this repository's scheduled workflows only every 5-9 hours (28-29 Sep 2026), whatever the cron says. It
does run a workflow at once when asked through its API. This Cloudflare Worker asks at fixed times (Workers Free):

| When (UTC) | Workflow | Notes |
| --- | --- | --- |
| every 15 minutes | `news.yml` | GDELT's most overdue queries and the RSS feeds |
| every 3 hours at :07 | `snapshot.yml` | with `scheduled=true`: obeys the 150-minute rule |
| 09:47 | `daily.yml` | with `scheduled=true`: runs only if `PIPELINE_ON` is `true` and the day hasn't run yet |
| every hour at :13 | `earlyvote.yml` | downloads only files that changed |

GitHub's own schedules stay in the workflows as a fallback. The Worker has no public URL (`workers_dev: false`).

## Setup (Matteo, once, about 10 minutes)

1. **The token.** GitHub → Settings → Developer settings → Personal access tokens → Fine-grained tokens →
   Generate new token. Name `simlab-cron`; expiration: after 30 Nov 2026; Repository access: "Only select
   repositories" → `Matteomio16/simlab`; Repository permissions → Actions: "Read and write" (Metadata: read-only is
   added automatically). Nothing else. Generate and copy it.
2. **The Worker.** In a terminal:
   ```
   cd "C:\Users\matte\Documents\Sim Research\simlab\ops\cron"
   npx wrangler login
   npx wrangler deploy
   npx wrangler secret put GH_TOKEN
   ```
   - `npx` may ask to install wrangler: answer `y`.
   - `login` opens the browser: allow access for the Cloudflare account that hosts notapoll.org.
   - `secret put` asks for the value: paste the token. It never goes into a file or a chat.
3. **Check.** Cron changes take up to 15 minutes to reach Cloudflare. After that, the news workflow's page
   (github.com/Matteomio16/simlab/actions/workflows/news.yml) shows runs started by `workflow_dispatch` every
   15 minutes.

The free plan allows 5 cron triggers per account; this Worker uses 4. If your account already has cron triggers
elsewhere, tell the Engine session first.

To stop it: `npx wrangler delete` in this folder, or remove a line from `crons` in `wrangler.jsonc` and deploy again.
