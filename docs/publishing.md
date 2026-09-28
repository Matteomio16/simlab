# Publishing: chart factory and post kits

Content & site session. Design approved by Matteo on 28 Sep: matplotlib draws every image and video frame. The content
plan is `docs/content-plan.md`; the rules come from the Field Guide (publishing) and CLAUDE.md.

## Brand

- **Name:** NotAPoll. Handles in `docs/content-plan.md` §1. Until the domain is bought, images show the wordmark and
  research.scaliastudio.dev/midterms, never "notapoll.org".
- **Type** (SIL Open Font License, unmodified files in `simlab/publish/fonts/`, from Google Fonts' repository):
  Newsreader for headlines and the wordmark, Libre Franklin for text and numbers, IBM Plex Mono for kickers, sources and
  the label strip. The static weights matplotlib needs are cut from the variable fonts on first use
  (`fonts/_static/`, not committed).
- **Colours:** paper `#F5F3EE`, ink `#111110`, secondary ink `#55534E`. Party blue `#2a78d6`, red `#e34948`, amber
  `#eda100` for independents (low contrast, so always labelled). Violet `#4a3aa7` marks the simulation's own
  contribution; graphite `#3B3A36` marks real data and statistics. Blue, red and violet pass the dataviz validator's
  colour-blind checks on the paper colour, all pairs.
- **Theme:** Lab Notebook by default, Riso Print now and then (`simlab/publish/themes.py`; Matteo, 28 Sep).
- **Every image:** the logomark (a ballot box holding a 3x3 grid of simulated voters) and wordmark at the top; the
  strip "SOCIAL SIMULATION, NOT A POLL" with the date at the bottom; a source line above it. The strip is drawn by the
  canvas itself, so no image can leave without it.
- **Forecast images** also carry the run stamp ("RUN <hash> · 40,000 SIMULATED ELECTIONS") and the race tag: the
  state outline filled with simulated voters, exactly the race's share of them blue, with the race code (OH-SEN).
  Outlines: Census 2024 cartographic boundaries, 1:20m, public domain (`geo.py` → `states.json`).

## Code (`simlab/publish/`)

| File | Job |
| --- | --- |
| `frame.py` | The canvas (1080×1350), fonts, typesetting (curly apostrophes, minus signs), line breaks. `save()` refuses a missing glyph, text outside the margins, content running into the footer, or the wrong size |
| `charts.py` | Stat tiles, question rows, horizontal bars, dumbbells |
| `text.py` | Rule check for captions and posts: the label, and no "poll", "survey", "voters say" or "% of voters" for model outputs |
| `labnotes.py` | The making-of series: `python -m simlab.publish.labnotes 1 2 3` → `kits/labnotes/NN/` (slides, contact sheet, `post.md`) |
| to build | `kit.py` (the daily kit from the forecast file), `reel.py` (the 9:16 video) |

Tests: `python -m unittest tests.test_publish`.

## The daily kit (due Sun 4 Oct)

- **Input:** the day's forecast file (format in `docs/engine-design.md`, pending). Until it exists, a fixture shaped like
  the Monte Carlo outputs in `docs/stats-groundwork.md` §5.8 (win chance, 10–90% margin range, seat distributions, the
  1,000-draw sample, the stats-only twin), plus the poll average, market and Cook, and the day's events.
- **Output:** `kits/<date>/`: slides, `reel.mp4` when useful, `caption_instagram.txt`, `alt_text.json`, `thread.txt`,
  `note.md` (what changed and why, rule checks first), `manifest.json` (input and file hashes). `kits/` is gitignored:
  kits stay internal during the pilot.
- **Checks on top of `text.py`:** every forecast number beside the poll average, market and Cook; 35–65% called a
  toss-up; "no meaningful change" when the 7-day change is small; character limits (Instagram 2,200, thread posts
  280). A failed check will block the approval flag once posting is automated.
