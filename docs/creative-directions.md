# Creative directions (28 Sep 2026, for Matteo to choose)

Five visual identities, each rendered on the same four posts: a Lab notes cover, a Lab notes chart, the daily forecast
card and a frame of the 9:16 "every future" video. Rebuild with `python -m simlab.publish.directions`; the boards are
`kits/directions/board-1.jpg` to `board-5.jpg` (the last two posts use invented example numbers, stamped EXAMPLE).
Themes live in `simlab/publish/themes.py`; switching direction changes one line.

**Fixed in every direction:** the black-or-ink label strip with the date (now "SOCIAL SIMULATION, NOT A POLL"); party blue
and red (Republican red leans vermilion so colour-blind readers can tell it from blue); one colour reserved for the
simulation's own contribution ("AI" below); independents in a labelled neutral grey. Every palette's blue, red and AI
colour pass the dataviz validator's colour-blind checks on its own background. Fonts are all free (SIL OFL); none of
the fonts the research flags as "AI template" tells (Inter, Poppins, Montserrat, Raleway, Space Grotesk, Outfit).

| # | Direction | Idea | Inspired by | Palette | Type | Signature | Best for | Risk |
|---|---|---|---|---|---|---|---|---|
| 1 | **The Broadsheet** | A serious newspaper page | FT's paper tone, NYT graphics (Franklin labels) | paper #F4F0E8, ink #141414, Dem #2B5C9E, Rep #C8412F, AI teal #0E8C7A | Newsreader / Libre Franklin / IBM Plex Mono | Masthead rule and black strip | Credibility with press and academics | Close to what serious outlets already do; less ownable |
| 2 | **Lab Notebook** | The forecast as an open lab book | Lab notebooks, technical drawings; our Lab notes series | graph paper #F7F7F2, navy pen #1C2A4A, Dem #2F6DB5, Rep #D1432F, AI ochre #D4A017, highlighter #F3E27A | IBM Plex Sans / Plex Mono | Graph-paper grid and highlighter behind key numbers | Making-of, methods, scorecards; the disclosure reads as a lab annotation | Grid adds texture that small charts must not fight |
| 3 | **Election Night** | Broadcast desk on results night | TV election graphics, Bloomberg's dark "terminal" look | night #0E1218, ink #F2F0EA, Dem #4F8FF7, Rep #E8483C, AI teal #13A08A, amber strip #F2C230 | Archivo Condensed caps / Archivo / Plex Mono | Amber kicker chip and amber strip on near-black | Reels, the daily number, election night | Dark all day can feel loud; amber strip must not read as "breaking news" hype |
| 4 | **Civic Grid** | Swiss public-information poster | International Typographic Style, government info design | white #FAFAF8, ink #0A0A0A, Dem #1F5FBF, Rep #D93A26, AI amber #E0A526 | Schibsted Grotesk (built for a news publisher) / Plex Mono | Solid black top bar, flush-left heavy type | Maximum legibility at thumbnail size | Can look corporate or cold |
| 5 | **Riso Print** | Hand-printed election zine | Risograph printing, indie data zines | cream #F1ECDF, riso navy #23305E, Dem #0078BF, Rep #E8474F, AI amber #E0A526, fluorescent pink overprint #FF48B0 | Bricolage Grotesque / Plex Mono | Pink second-ink offset behind big numbers, paper grain | Standing out in feed; clearly human-made, not AI | Playful register can undercut research credibility; pink offset needs restraint |

**Recommendation:** Lab Notebook for the feed, plus a dark version of the same system (Plex on navy, same strip) for
Reels and election night. It is the most ownable direction: it matches the Lab notes series, and it turns the required
disclosure into part of the look. Broadsheet is the safe alternative if credibility with press matters most.
