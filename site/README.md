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

Done 29 Sep: the Cloudflare API token (Workers Scripts and Account Settings on the account; Workers Routes, DNS and
Zone Read on notapoll.org) and the GitHub secrets `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ACCOUNT_ID`. Every push to
`site/` now updates two unlisted previews: https://notapoll-launch-preview.mattemio9.workers.dev (the launch page)
and https://notapoll-preview.mattemio9.workers.dev (the 12 Oct forecast pages, sample data).

1. **Done 30 Sep.** Put the launch page on notapoll.org (before the first post on Sat 3 Oct).
   - Cloudflare → notapoll.org → DNS: if there is an A, AAAA or CNAME record on `notapoll.org` or `www`, delete it.
     Leave MX and TXT records (email routing, Bluesky) alone.
   - GitHub → Matteomio16/simlab → Settings → Secrets and variables → Actions → Variables: `SITE_DEPLOY` = `on`,
     `SITE_MODE` = `prelaunch`.
   - Actions → Site → Run workflow. The deploy attaches notapoll.org and www.notapoll.org and creates their records.
2. **Done 30 Sep.** Contact address. Cloudflare → notapoll.org → Email → Email Routing → Routing rules: `hello@notapoll.org`
   forwarding to your inbox.
3. **Redirect from Scalia.** Cloudflare → scaliastudio.dev: DNS → add AAAA `labs` → `100::`, proxied; Rules →
   Redirect Rules → when Hostname equals `labs.scaliastudio.dev`, static redirect to `https://notapoll.org`, 301.
4. **11 Oct, after your go:** Variables `SITE_PUBLISH` = `on`, `SITE_MODE` = `forecast`, `SITE_DATA` = `live`. The site
   switches to the forecast by itself when the first daily publish lands on 12 Oct (about 10:05–10:45 UTC). Turn
   `SITE_PUBLISH` off before any test run of the daily job after 12 Oct.
5. **Optional:** Cloudflare Web Analytics for notapoll.org (free, no cookies); Cloudflare Access to put a login in
   front of the previews.

## Go-live checklist (3 Oct)

- [ ] **Matteo has read the methods page** (`content/methods.md`, http://localhost:4310/methods.html) and approved it.
- [ ] Lab note 01 approved and imported (`node scripts/import-labnote.mjs 01`), or the page says the first note is coming.
- [ ] Social links switched on in `src/lib/site.ts` for the accounts that exist.
- [x] `hello@notapoll.org` forwards to Matteo (Email Routing, 30 Sep).
- [x] Cloudflare: token and account ID in GitHub secrets (29 Sep).
- [x] Step 1 above done; notapoll.org and www show the launch page (30 Sep, Site run 36728357936).
- [ ] Redirect from labs.scaliastudio.dev/midterms to notapoll.org (rule and proxied record in the scaliastudio.dev zone).

## Defaults chosen while Matteo was away (29 Sep evening), easy to change

| Choice | Where | Change by |
| --- | --- | --- |
| Link-preview images (1200×630) for the home and every race page, with the label strip and the benchmarks | `src/app/opengraph-image.tsx`, `src/app/senate/[slug]/opengraph-image.tsx`, `src/lib/og.tsx` | editing the card layout; deleting the two files turns them off |
| Track record page reads `data/<live>/scores.json` in the Kev session's format (29 Sep): rows {date, model, target, office, races, mae, direction, brier, log_loss, note}, append-only; Brier and log loss only against results | `src/app/track-record/page.tsx` | Kev session changes the file; the page follows |
| Archive lists `public/data/YYYY-MM-DD/forecast.json` written by `publish-day.mjs` | `src/app/archive/page.tsx` | — |
| Public changelog, first entry dated 3 Oct | `content/changelog.md` | editing the file |
| Track record and archive appear from 12 Oct only; changelog from 3 Oct | `scripts/postbuild.mjs`, footer | moving routes in or out of the prelaunch drop list |
| House control block on the overview, shown once `forecast.json` has `house` (shape confirmed by Statistics, 29 Sep); House race pages come with the 12 Oct House launch | `src/app/_home/Overview.tsx`, `src/lib/types.ts` | — |
| Page colour white, not the kit's cream #F5F3EE (Matteo, 29 Sep) | `src/app/globals.css` (`--paper`) | — |
