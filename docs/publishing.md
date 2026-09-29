# Publishing: chart factory and post kits

Content & site session. Design approved by Matteo on 28 Sep: matplotlib draws every image and video frame. The content
plan is `docs/content-plan.md`; the rules come from the Field Guide (publishing) and CLAUDE.md.

## Brand

- **Name:** NotAPoll.org. Handles in `docs/content-plan.md` §1. Every image's header wordmark reads "NotAPoll.org", the
  ".org" in purple, so the address travels with every screenshot (`frame.SITE`).
- **Logo** (Matteo, 29 Sep; the logo kit is `brand/`, masters in `brand/final/`, rebuilt by `python -m brand.final`):
  H1, "two hills", a blue and a red hill with a purple overlap, beside the wordmark "NotAPoll.org" in Newsreader 560
  (".org" purple). On images the mark is drawn natively (`frame.hills`): hills 1.18 × cap height on the wordmark's
  baseline, 0.42 × cap height from the N; blue and red are the theme's party colours, the overlap and ".org" are
  `#7A4FC0` on paper and `#B98DD6` on dark themes. The ballot-box mark is retired (still behind
  `NOTAPOLL_LOGO=grid`, `NOTAPOLL_WORDMARK=theme`).
- **Profile images and pinned post:** `python -m simlab.publish.brand` → `kits/brand/`: avatar (the logo kit's, D on
  white), X header and Bluesky banner (the logo kit's, as approved), the "Start here" carousel and `post.md` with
  the bios (Instagram 150, X 160, Bluesky 256 characters, counted by the script). The avatar alone carries no label:
  at profile size it can't.
- **Type** (SIL Open Font License, unmodified files in `simlab/publish/fonts/`, from Google Fonts' repository):
  Lab Notebook (every daily post) uses IBM Plex Sans for headlines, text and numbers and IBM Plex Mono for kickers, sources and the label strip. Newsreader, Libre Franklin, Archivo and
  Bricolage belong to the special editions and the retired directions only. The static weights matplotlib needs are cut
  from the variable fonts on first use (`fonts/_static/`, not committed).
- **Colours and type per theme:** `simlab/publish/themes.py` and `docs/creative-directions.md`. Lab Notebook: graph
  paper `#F7F7F2` with lilac rules, navy ink `#1C2A4A`, Dem `#2F6DB5`, Rep `#D1432F`, and election purple `#6D2E8C`
  for the simulation's own number and for toss-ups (zone fill `#EEE6F7`, lilac highlighter `#E6DAF3`, verdict stamps
  purple for toss-ups, blue or red otherwise); deep indigo label strip `#2A2152`; IBM Plex Sans and Plex Mono. Independents use a labelled neutral grey. Each
  theme's party and simulation colours pass the dataviz validator's colour-blind checks on its paper, all pairs.
- **Theme:** Lab Notebook every day. Riso Print is retired (Matteo, 28 Sep, later that day); Sundays and special days
  use the special editions below.
- **Swing band:** every theme draws a blue, purple, red band along the top of the label strip: the brand's election
  signature.
- **Every image:** the logo (H1 and the wordmark) at the top right; the
  strip "SOCIAL SIMULATION, NOT A POLL" with the date at the bottom; a source line above it. The strip is drawn by the
  canvas itself, so no image can leave without it.
- **Forecast images** also carry the run stamp ("RUN <hash> · 40,000 SIMULATED ELECTIONS") and the race tag: the
  state outline filled with simulated voters, exactly the race's share of them blue, with the race code (OH-SEN).
  Outlines: Census 2024 cartographic boundaries, 1:20m, public domain (`geo.py` → `states.json`).

## Voice: human and social (Matteo, 28 Sep)

We simulate human behaviour, so posts sound close to people, not machines. Keep "AI" and model names for the methods
page and for Lab notes that are about a specific model; `text.style()` flags them elsewhere as notes, not failures.

| Say | Avoid | Never (rules) |
| --- | --- | --- |
| social simulation, synthetic voters, simulated voters, the simulated electorate, simulated elections, the simulation | AI voters, bots, LLM, agents, AI-simulated | poll, survey, voters say, % of voters, respondents, anything implying real people answered |

"Virtual interactions" only once voters actually interact: today each group reacts on its own (no social-network layer
in `docs/engine-design.md`). "Synthetic" or "simulated" must stay in every post, so no reader mistakes the voters for
real people.

## Code (`simlab/publish/`)

| File | Job |
| --- | --- |
| `frame.py` | The canvas (1080×1350), fonts, typesetting (curly apostrophes, minus signs), line breaks. `save()` refuses a missing glyph, text outside the margins, content running into the footer, or the wrong size |
| `charts.py` | Stat tiles, question rows, horizontal bars, dumbbells |
| `text.py` | Rule check for captions and posts: the label, and no "poll", "survey", "voters say" or "% of voters" for model outputs |
| `specials.py` | The five special editions: `python -m simlab.publish.specials` → `kits/specials/` |
| `labnotes.py` | The making-of series: `python -m simlab.publish.labnotes 1 2 3` → `kits/labnotes/NN/` (slides, contact sheet, `post.md`) |
| `kit.py` | The daily kit from the forecast file (below) |
| `reel.py` | "Every future", the 9:16 video: `python -m simlab.publish.reel NC TX` → `kits/reels/`; the kit adds it with `--reel` |
| `brand.py` | Profile images, the pinned post and bios |

Tests: `python -m unittest tests.test_publish`.

## Special editions (Sundays and special days)

Each has its own layout and palette (`themes.SPECIALS`; party blue, red and purple validated on each paper). Names and
numbers only: no photos or drawings of candidates. Race numbers still sit beside the poll average, market and Cook.

| Edition | Focus | Palette | Memorable element |
| --- | --- | --- | --- |
| The Ballot | a race's two candidates | ballot white, black, Franklin Gothic (the typeface of real US ballots) | a specimen ballot "counted 40,000 times"; each oval pencilled in as far as that candidate's share of simulated wins |
| The Main Event | a race's two candidates | deep purple night, condensed Archivo | fight-card poster: surnames as tall as the page, the score (58–42), the days left |
| The Seismograph | one race's fortnight | chart-paper cream, Plex | the forecast as a seismograph trace; numbered tremors tied to the neutral event cards |
| The Chamber | Senate control | marble cream, Newsreader | all 100 seats in a half circle, seats not up pale, toss-ups purple, the 50-seat line |
| The Map | all 35 races | night navy, Plex | one tile per state; a ring marks each race where Cook disagrees with us |

Layouts are examples until Matteo picks; they need `races.json` candidates, the forecast history, Senate holdover
seats and the Senate-control market price from the engine before they can run daily.

## Every future (the 9:16 video)

1080×1920, 30 fps, H.264 with `+faststart`, no sound (music added in the Instagram app when posting by hand), 16 s,
about 0.8 MB, about a minute to render. The race's 100 simulated elections land one by one as dots, slowly at first and
then faster, while the counter reads "N of M simulated elections won by the Democrat"; the closing card adds the
verdict label, the "if the election were today" number, and the poll average, market and Cook. Content stays inside
the Reels safe area (220 px top, 340 px bottom), the label strip included. The closing frame goes through the same
layout guard as the slides, and the last frame is saved as the cover. The kit renders it for the first featured race
with `--reel` (`reel.mp4`, `reel-cover.jpg`, alt text in `alt_text.json`); a failed video becomes a problem in
`note.md` and blocks approval, not the kit. When (Matteo, 29 Sep): Sundays, the first featured race; and any day a
featured race's win chance moved 10 points or more in a week, that race (`--reel auto`, the default; `always` or
`never` override).

## Lab notes file format (read by the website session)

`kits/labnotes/NN/post.md` keeps this shape; tell the website session before changing it: first line
`# Lab notes NN: <title>`; a `Planned date: <Day DD Mon YYYY>` line; `## Slides and alt text` with items
``N. `slide-N.jpg`: <alt text>``; `## Instagram caption` with the caption body.

## For the website session (C6 moved there, 29 Sep)

The site should read as the same brand as the posts. Shared pieces, all in `simlab/publish/`:
- **Tokens** (`themes.py`, LAB): paper `#F7F7F2`, grid lines `#E1DFEC`, ink `#1C2A4A`, secondary ink `#4A5670`, muted
  `#7E879A`, Dem `#2F6DB5`, Rep `#D1432F`, independent grey `#7E879A`, purple `#6D2E8C` (our number and toss-ups),
  toss-up fill `#EEE6F7`, highlighter `#E6DAF3`, indigo strip `#2A2152`. Dark mode: the special-edition night colours in
  `themes.MAP` (Dem `#4F8FF7`, Rep `#F0554A`, purple `#9E4FC4` on `#0F1424`), which pass the same colour-blind checks.
- **Type on the site differs from the posts** (Matteo, 29 Sep, website session): the site uses Libre Franklin for
  headings, data and UI and Source Serif 4 for reading text, no mono, after he found Plex with mono labels
  "vibe-coded" on the web. The posts keep IBM Plex Sans and Plex Mono; the wordmark is Newsreader 560 on both. Shared:
  the logo, colours, label strip and swing band.
- **Logo:** H1 and the wordmark as above; use the SVG masters in `brand/final/` (text outlined, no font dependency).
- **Signature details:** the blue, purple, red swing band; the label "Social simulation, not a poll" on every view that
  shows a number; the state outline filled with simulated voters (`charts.state_voters`, outlines in `states.json`).
- **Rules that apply on the site too:** our number always beside the poll average, the market and Cook; 35–65% is a
  toss-up; "the independent" where `left_party` is "I"; only event `card` text, never `news_private.jsonl`; no "poll",
  "survey" or "voters say" for our outputs (`text.check` can lint page copy).

## The daily kit (due Sun 4 Oct)

Command for the daily job (roadmap A8): `python -m simlab.publish.kit --date YYYY-MM-DD --data <simlab-data>`. It
writes `derived/<date>/post-kit/`, exits 1 if the kit can't be built, and prints a one-line JSON summary last
(`ok`, `races`, `slides`, `problems`, `approvable`, `out`). Before 12 Oct every slide's kicker says "PILOT · INTERNAL,
NOT FOR POSTING". Layouts: The Stamp, Where everyone stands, 100 futures (Matteo, 28 Sep). A slide
takes about 1 s to render. Featured races: the pilot five (OH, NC, TX, IA, ME) before 12 Oct; from 12 Oct the three closest races plus the
biggest 7-day mover (`--races NC,GA` overrides). `note.md` still lists every race. The summary adds `featured`.
Tests: `python -m unittest tests.test_kit`.

- **Independents:** where `left_party` is "I" (NE, ID, SD, MT in 2026) the cards say "the independent", use I+ margins
  and draw that side in the neutral independent grey instead of blue.
- **Two views** (Matteo, 29 Sep): the headline number is 3 Nov; "if the election were today" (`races[rid].today`) sits beside it: a ledger row on The Stamp, and in the caption, thread, alt text and note. Captions count "in 100" so the two numbers can differ visibly. `senate.today` waits for The Chamber.
- **Movers** (`movers[].delta`, 28 Sep): each story's effect on the 3 Nov margin. Captions quote a story only at 0.5 points or more (`MOVER_MIN`); `note.md` lists all of them, plus each race's news effect, its win chance if news matters less or more, and its tier.
- **Senate control, still to wire** (The Chamber): `p_r_50plus`, `p_d_caucus_51` and `p_independents_decide` add to 1; new independents are shown as independents (Matteo); the final presentation is decided later.
- **Layout guard:** `save()` also refuses text whose glyphs touch other text. Text over shapes is checked by eye on
  the review boards.

- **Input** (`docs/engine-design.md` §7, approved 28 Sep): `forecast.json` (per race `p_dem_win`, margin p10/p50/p90,
  `stats_only`, `benchmarks` {poll_avg, market, cook}, `movers` [{event_id, card, delta}]; Senate and House control) and
  `draws.json` (the fixed 1,000-draw sample, for dot charts), from `simlab-data/derived/YYYY-MM-DD/`; public copies
  under `simlab/public/forecasts/` only from 12 Oct. Race names from `races.json`. Race ids map to tag codes: `NC` →
  NC-SEN, `OH-S` → OH-SEN (special), `TX-28` → TX-28.
- **Rules for these inputs:** posts quote the neutral event `card`, never raw headlines. `moves.json` breakdowns by
  voter group describe the simulation's reasoning ("Why it moved"), never public opinion: no "young voters think".
- **Output:** `kits/<date>/`: slides, `reel.mp4` when useful, `caption_instagram.txt`, `alt_text.json`, `thread.txt`,
  `note.md` (what changed and why, rule checks first), `manifest.json` (input and file hashes). `kits/` is gitignored:
  kits stay internal during the pilot.
- **Checks on top of `text.py`:** every forecast number beside the poll average, market and Cook; 35–65% called a
  toss-up; "no meaningful change" when the 7-day change is small; character limits (Instagram 2,200, thread posts
  280). A failed check will block the approval flag once posting is automated.
