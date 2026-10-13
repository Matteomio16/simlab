# Simulation only: polls set the start, then only the simulation moves races

Decided by Matteo, 13 Oct 2026, in the coordinator session. This supersedes engine-design §1 principle 1 ("new polls
correct it"), the daily filter's poll correction, and the weekly trend check rule decided earlier (4 / 6 / 7.5 points,
opposite moves only). It is a method change after the 12 Oct code freeze, so it goes in the public changelog, dated,
with both versions scored.

## The rule

1. **The start is fixed at the 12 Oct launch.** Each race's level (poll average plus fundamentals) as published on
   12 Oct is the starting point for the rest of the campaign. Polls never re-anchor it.
2. **After 12 Oct, only the simulation moves races.** A race's daily change is the sum of its stories' simulated
   reactions (the moves). No daily poll correction, and no weekly re-fit of the levels from polls. A race with no news
   that day does not move, apart from the fading of earlier stories.
3. **Polls and prediction markets only verify.** They are read every week to check the simulation, never fed in.

## The weekly check (Sunday evening)

It runs on Sunday after the daily run and goes to Matteo on Sunday evening. Per race, Senate and House:

- **Gap** = |our margin's change over the week − the poll average's change over the same week|, in points of margin.
  It covers every direction: opposite moves (polls +2, us −2: gap 4), over-moves (polls +0.5, us +5.5: gap 5) and
  under-moves (polls +5, us +0.5: gap 4.5).
- **Gap above 3: flag.** Listed for Matteo with the stories that drove our move.
- **Gap above 5: severe flag.** Investigated before Monday's run.
- **Gap above 6.5: that week is likely cancelled.** After investigation, and only with Matteo's yes, the race goes back
  to its level of the week before and the week's moves are erased for that race. Monday's post explains it.
- **No new polls that week:** compare with the prediction markets' weekly move instead (implied margin), flag only,
  never cancel.
- A correction found by the investigation (a bug, a bad story summary, a story on the wrong race, a state reacting too
  strongly) is a logged change with both versions scored, and is published in a lab note.

## The House

District news launches now (not 19 Oct): the ~40 closest seats (the `simulate` tier) get stories matched to their
district, with reactions as for the Senate. National stories still move every seat through the national mood. Budget:
Matteo raises the OpenRouter cap to $30, and the economy and polls-only thresholds move up with it (from $17 and $19 to
$27 and $29). Estimated cost: about +$0.30 and +45 minutes a run.

## What the public sees

- Each race shows our number, with "polls alone" (the stats-only twin) and the prediction markets small beside it.
- A weekly post shows where we and the polls disagree most, and any race whose week was flagged or cancelled.
- The methods page, the about page and the post templates say it plainly: polls set the starting point on 12 Oct;
  since then every move comes from how voter personas react to the news; polls are used only to check us. Wording goes
  to Matteo for his yes.

## How Statistics built it (13 Oct; Matteo's yes the same evening, live from 14 Oct)

- **The start is never moved again** (Matteo, 13 Oct): changes are made live while the forecast goes on, from their
  day on, as logged changes with both versions scored.

- **The start** is the launch forecast's own level, not the stats-only number: polls and fundamentals with each poll
  taken less the stories in force on its dates. A run dated 12 Oct under the new rule gives back the published launch
  forecast. Starting from the stats-only number instead would move every race about 0.9 points toward the
  Republicans on day one, from the method alone (CHANGELOG 13 Oct).
- **The headline** is that start plus every story's effect expected on 3 Nov. Stories fade within days, so the 3 Nov
  number will move little until the final week; the "today" view moves more.
- **Severe and cancel need 3 new polls** that week; with 1 or 2 a gap stays a flag. **The first weekly check** (18 Oct)
  covers 14-18 Oct, the rule's first days.
- **A cancelled week** is an entry in `simlab/cancelled_weeks.json` (only with Matteo's yes): that race drops the
  stories first seen in the week.
- **The 12 Oct start reads Wikipedia's sponsor footnotes** (Matteo's yes, 13 Oct): campaign and party-group polls get
  half weight and the sponsor shift, as decided on 28 Sep. VoteHub's partisan flag counts only with a named sponsor
  or an internal poll, from 14 Oct (not in the start).
- **The old rule runs daily** for scoring (`simlab.pollfilter`, `simlab-data/scoring/poll-filter/<date>/`).

## Who does what

- **Statistics:** freeze the levels at 12 Oct, take the poll correction out of the daily filter, keep the stats-only
  twin as the "polls alone" comparison, and rebuild the weekly check to the rule above (Sunday). Show Matteo the
  numbers before and after on today's data before it ships.
- **Engine:** district news for the `simulate`-tier House seats; budget thresholds to $27 and $29 once the cap is $30;
  split `cards_failed` into "not news" (every model said it isn't a specific event) and "broke the rules", so the
  failure count can be read.
- **Content & site:** the "polls alone" comparison on race pages, methods and about wording, the weekly post template,
  and the changelog entry. All for Matteo's yes.
- **Matteo:** raise the OpenRouter cap to $30.
