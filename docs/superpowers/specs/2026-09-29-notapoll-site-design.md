# NotAPoll.org site (C6): design

Approved by Matteo, 29 Sep 2026 (website session).

## Decisions
- **Home:** notapoll.org. labs.scaliastudio.dev/midterms redirects there. "By Scalia Studio" in every footer (link to
  scaliastudio.dev) and on About; the header shows only NotAPoll.
- **Launch in two steps.** Sat 3 Oct: home ("forecasts from 12 October"), methods, Lab notes, About, with no forecast
  numbers of any kind. Mon 12 Oct (after Matteo's go on 11 Oct): Senate overview, race pages, House. Week of 19 Oct:
  track record, changelog, archive. By 3 Nov: election-night page.
- **Audience in layers:** a plain sentence and one number at the top of each page; ranges, benchmarks, movers and
  data downloads below. Methods is written for the data crowd.
- **Look:** clarity of 538 / Silver Bulletin, an editorial touch (Newsreader headlines), the post kit's Lab Notebook
  identity (tokens in `docs/publishing.md`, "For the website session"), research-lab calm, nothing salesy. Slot for
  the logo being redesigned in its own session.
- **Stack (as scaliastudio.dev):** Next.js 16 static export, React 19, Tailwind 4, TypeScript in `site/`. A Cloudflare
  Worker serves `site/out` with no adapter. Charts are React SVG components (no chart library). The home swarm is
  Canvas 2D (three.js/WebGL maybe later).
- **Data:** pages read `site/data/{forecast,races,draws}.json` at build time. Until 12 Oct these are sample data,
  scrambled from the real files' shape (`site/scripts/sample-data.mjs`); no real number leaves the private repo.
- **Preview:** an unlisted workers.dev Worker (`notapoll-preview`) with `X-Robots-Tag: noindex` and a "SAMPLE DATA"
  watermark. Cloudflare Access can come later (Matteo's step).
- **Deploys:** GitHub Actions with a Cloudflare API token Matteo creates (`CLOUDFLARE_API_TOKEN` secret). DNS, custom
  domain and redirect rule are Matteo's steps (`site/README.md`).
- **Lab notes:** only notes Matteo approved, copied from `kits/labnotes/NN/` into `site/content/labnotes/NN/` by
  `site/scripts/import-labnote.mjs` and committed. The post.md format is agreed with Content & site.
- **Addresses:** state names: `/senate/ohio-special`, `/house/texas-28`.
- **Methods text:** drafted from `docs/engine-design.md` and `docs/stats-groundwork.md`; Matteo reviews before 3 Oct,
  C7 review on 10 Oct.

## Rules the site keeps (from publishing.md and CLAUDE.md)
- "Social simulation, not a poll" and the swing band on every view with a number.
- Our number always beside the poll average, the market and Cook. 35–65% is a toss-up.
- The 3 Nov number is the headline; "if the election were today" (`races[rid].today`, `senate.today`) beside it.
- "The independent" where `left_party` is "I". Only event `card` text, never `news_private.jsonl`.
- No "poll", "survey", "voters say" or "% of voters" for our outputs. Minimal "AI".
- Senate headline "Republicans hold 50+"; independents shown separately.

## Gate
A `SITE_MODE` build flag: `prelaunch` (3 Oct: no forecast routes are built at all) or `forecast` (12 Oct). The preview
builds `forecast` mode on sample data. Switching production to `forecast` needs Matteo's go.
