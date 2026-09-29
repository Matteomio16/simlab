# NotAPoll.org site (roadmap C6)

Next.js 16 static export, React 19, Tailwind 4, TypeScript: the same setup as scaliastudio.dev. A Cloudflare Worker
serves `out/` with no adapter and no server code. Design: `docs/superpowers/specs/2026-09-29-notapoll-site-design.md`.

## Modes

| Variable | Values | Meaning |
| --- | --- | --- |
| `SITE_MODE` | `prelaunch` (default), `forecast` | prelaunch builds no forecast pages and shows no numbers (3 Oct). forecast adds the Senate overview and race pages (12 Oct, after Matteo's go). |
| `SITE_DATA` | `sample` (default), `live` | `data/sample/` holds invented numbers; `data/live/` is written by `scripts/publish-day.mjs` from 12 Oct. |
| `SITE_PREVIEW` | `1` | The unlisted preview: no-index headers and robots, and the "Sample data" banner. |

## Commands (from `site/`)

```
npm ci
npm run dev                                  # prelaunch, http://localhost:3000
SITE_MODE=forecast npm run dev               # forecast pages on sample data
npm run build                                # static export to out/, then out/_headers
node scripts/check-copy.mjs                  # vocabulary check on the built pages
node scripts/sample-data.mjs --races <races.json> [--date 2026-10-12] [--seed 7]
node scripts/import-labnote.mjs 01           # only after Matteo approves Lab notes 01
node scripts/publish-day.mjs --from <simlab-data/derived/YYYY-MM-DD>   # from 12 Oct
```

PowerShell sets variables with `$env:SITE_MODE = "forecast"; npm run dev`.

## Deploys

`.github/workflows/site.yml` runs on pushes to `main` that touch `site/`, and by hand:
- **Preview** (`notapoll-preview` Worker, `wrangler.preview.jsonc`): forecast mode on sample data, on the account's
  workers.dev address. Unlisted, never indexed. Not secret: anyone with the address can open it.
- **Production** (`notapoll-site` Worker, `wrangler.jsonc`, notapoll.org and www): only while the repository
  variable `SITE_DEPLOY` is `on`. It refuses forecast mode unless `SITE_DATA` is `live`.

## Matteo's steps (Cloudflare and GitHub)

1. **API token.** Cloudflare dashboard → My Profile → API Tokens → Create Token → template **Edit Cloudflare
   Workers**. Account resources: your account. Zone resources: **notapoll.org** only. Add one permission row:
   Zone · DNS · Edit (for the custom domain). Create, copy the token once.
2. **Account ID.** Dashboard → Workers & Pages → the Account ID on the right. Copy it.
3. **GitHub secrets** (github.com/Matteomio16/simlab → Settings → Secrets and variables → Actions → Secrets):
   `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ACCOUNT_ID`. The next push to `site/` deploys the preview; its address
   (`notapoll-preview.<your-subdomain>.workers.dev`) is in the workflow log.
4. **Go live on 3 Oct.** First remove the rule that sends notapoll.org to Instagram (Rules → Redirect Rules in the notapoll.org zone). Then, in the same GitHub tab → Variables: `SITE_DEPLOY` = `on`, `SITE_MODE` = `prelaunch`. Then Actions → Site →
   Run workflow. The first deploy attaches notapoll.org and www.notapoll.org to the Worker and creates their DNS
   records. If the dashboard already has an A, AAAA or CNAME record on `notapoll.org` or `www`, delete it first. Leave
   the MX and TXT records (email routing, Bluesky) alone.
5. **Redirect from Scalia.** In the scaliastudio.dev zone:
   - DNS → Add record: type AAAA, name `labs`, address `100::`, proxied (orange cloud). It only exists so the rule
     below can fire.
   - Rules → Redirect Rules → Create rule "labs to notapoll": when *Hostname* equals `labs.scaliastudio.dev`, then
     Static redirect to `https://notapoll.org`, status 301, preserve query string.
6. **Contact address.** Email → Email Routing → Routing rules: add `hello@notapoll.org` forwarding to your inbox
   (the About page shows it).
7. **Optional analytics.** Analytics & Logs → Web Analytics → add notapoll.org (free, no cookies). Enabling it on a
   proxied site needs no code change.
8. **12 Oct, after your go on 11 Oct:** `SITE_DATA` = `live`, `SITE_MODE` = `forecast`, and the daily job runs
   `publish-day.mjs` and pushes `site/data/live/`.
9. **Later:** Cloudflare Access (Zero Trust → Access → Applications) can put an email login in front of the preview.

## Defaults chosen while Matteo was away (29 Sep evening), easy to change

| Choice | Where | Change by |
| --- | --- | --- |
| Link-preview images (1200×630) for the home and every race page, with the label strip and the benchmarks | `src/app/opengraph-image.tsx`, `src/app/senate/[slug]/opengraph-image.tsx`, `src/lib/og.tsx` | editing the card layout; deleting the two files turns them off |
| Track record page (owned by Kev, roadmap A9; shape to confirm with Kev) reads `data/<live>/scores.json` (`{scores: [{date, model, brier, log_loss, races}]}`); scoring dates 19 Oct, 26 Oct, 2 Nov, then certified results | `src/app/track-record/page.tsx` | agreeing the file with Statistics; editing `SCORING_DATES` |
| Archive lists `public/data/YYYY-MM-DD/forecast.json` written by `publish-day.mjs` | `src/app/archive/page.tsx` | — |
| Public changelog, first entry dated 3 Oct | `content/changelog.md` | editing the file |
| Track record and archive appear from 12 Oct only; changelog from 3 Oct | `scripts/postbuild.mjs`, footer | moving routes in or out of the prelaunch drop list |
| House control block on the overview, shown once `forecast.json` has `house` (shape confirmed by Statistics, 29 Sep); House race pages come with the 12 Oct House launch | `src/app/_home/Overview.tsx`, `src/lib/types.ts` | — |
