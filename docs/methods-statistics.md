# Methods: the statistics layer, in plain language

For the website session (C6). Written by the Statistics session on 29 Sep 2026, in the vocabulary of
`docs/publishing.md`: social simulation, synthetic voters, simulated elections; never "poll", "survey" or "voters say"
for our outputs. Model names appear only where the methods page needs them. Numbers are the parameters in force on 29
Sep; `docs/stats-groundwork.md` and `docs/CHANGELOG.md` hold the details and sources. The last section lists changes
suggested for `site/content/methods.md`.

## What the statistics layer does

Statistics decide where each race starts and how uncertain it is. The synthetic voters then decide how the news moves
it. Statistics never use prediction markets or expert ratings: those are shown beside our numbers, never inside them.

## Where each race starts

Each race's starting margin blends two estimates.

- **Fundamentals:**
  - the state's partisan lean: 0.62 × the latest presidential margin plus 0.26 × the one before;
  - the national mood, from the generic ballot (lowered by 2.8 points, its average overstatement of Democrats) and
    presidential approval;
  - incumbency, worth about 5 points (half for an appointed senator);
  - 0.38 of the nominee's over- or under-performance in their last statewide race.
- **Polls:**
  - each pollster's steady lean (its house effect, measured over 2018–24 and re-checked on this year's polls) is
    taken out;
  - polls of registered voters or all adults are adjusted to a likely-voter basis;
  - versions of the same poll count as one;
  - polls paid for by a party, campaign or partisan group count half and are shifted away from the sponsor (about
    2.5 points);
  - the poll average can drift a little every day, so old polls count less as time passes.

The blend follows how much each estimate is worth in that race. A heavily polled race leans on its polls, but polls
never count for more than about 80%, because even a large poll average can miss (as in 2016 and 2020). A race without
polls starts from the fundamentals alone. Each race publishes how much its polls count.

## The voter groups' numbers

Each race splits its electorate into the same 28 groups: party identification (seven levels) × white or not × a
four-year degree or not. Each group carries:
- **its share of the electorate:** Census data on who lives in the state, with party identification from a large
  academic survey (CES), matched to the state's 2024 result;
- **its midterm turnout:** Census turnout figures from 2022, matched to the official count;
- **its vote split:** from Kev, a model we trained on real survey answers about how each kind of voter voted in 2024.
  All groups are shifted together until they add up to the race's starting margin, so the split only decides the
  pattern across groups, never the race's level. The survey's own numbers are kept beside Kev's, to check both
  against the 2026 results;
- **its persuadable share** (people who changed their mind or started undecided) and **its mobilisable share**
  (people whose turnout was uncertain), from survey respondents interviewed before and after the 2018 and 2022
  midterms.

## How the news and the polls fit together

- **News moves every race.** A race with polls and a race without them get the same effect from the same story.
- **Polls are read net of the news.** When a poll was taken while a story was moving voters, the story's simulated
  effect is taken out before the poll enters the average. That way a story isn't counted twice, once in the poll and
  once in the simulation.
- **Stories fade:**
  - every story fades from the day it first appears (a 5.5-day half-life: about 41% is left after a week, 17% after
    two);
  - one-off stories also drop within about a day once they leave the news;
  - lasting topics (prices, war) keep only the age fade.
- **Two numbers:**
  - **3 November** counts what each story should still be worth on election day;
  - **"if the election were today"** counts everything in force now. It is also less uncertain, because there is no
    time left for things to change.

## How big a reaction is

The synthetic voters give the direction and strength of a reaction; real events set its size. The scale was fitted on
45 past events with measured opinion shifts. The strongest possible reaction to a story with full attention moves
about a fifth of a group's persuadable voters, or of its mobilisable voters for turnout.

This isn't one fixed number. Each simulated election draws its own sizes around the fitted value, so the forecast
isn't tied to a single estimate. Each race shows how its forecast changes if the news matters less or more.

## The weekly filter

Every Monday (first on 5 October, privately; the public run starts on 12 October), the filter compares how the
polls actually moved with what the simulated reactions predicted.
- **The dials:** it sets two dials per state, one for vote switching and one for turnout. A dial above 1 means the
  news moves that state more than simulated; below 1, less. It never changes a reaction's direction.
- **Borrowing strength:** states with few polls stay close to the national dial. The dials' uncertainty goes into
  every simulated election.
- **Fade speed:** it also checks how fast news fades, weighing half-lives from about 3 to 11 days.
- **Surprises:** it flags any state whose polls surprise the forecast in the latest week.
- **The reaction model's lean:** the model we use for reactions sits slightly on the Republican side of real past
  opinion shifts, by about a quarter of a point per event. A small fixed correction takes that out, and the filter
  re-estimates it every week.

## The simulated elections

- **40,000 elections a day,** drawn from each race's margin and uncertainty. The random numbers are fixed by the date,
  so a rerun of a day gives the same result.
- **Errors are shared,** so a bad night for one party tends to happen everywhere at once:
  - a national error, including polls missing in the same direction nationwide (about 3 points on its own);
  - a regional error, shared by states in the same census division;
  - a state error, shared by all races in a state;
  - each race's own error, which takes the rest.
- **Fat tails:** an unusually large swing is more likely than a bell curve would allow, and in the same simulated
  year for every race.
- **No two Senate races move independently:** each pair keeps at least a 0.25 correlation.
- **What is kept:** each race's chance of winning (the share of simulated elections won), its middle and 10–90% range,
  the seat totals, and a sample of 1,000 simulated elections.

## The House

- **All 435 seats** start from fundamentals:
  - the district's 2024 presidential result on the new 2026 lines;
  - incumbency (about 4.5 points);
  - a daily adjustment so the seats add up to the national House vote.
- **Simulated seats:** from 12 October, about 40 of the most competitive seats get the full simulation.
- **Uncertainty:** each seat's own uncertainty is 5.5 points for seats within 15 points and 9 for safer ones. The
  national, regional and state errors come on top, shared with the Senate races in the same simulated election.
- **Seat counts:** seats won by a challenger who isn't a Democrat are counted on their own.

## The headlines

- **Senate:** "Republicans hold 50+ seats" (the Vice President breaks a 50–50 tie). King and Sanders count with
  Democrats. The new independents are shown on their own, with the share of simulated elections in which they hold
  the balance.
- **House:** the chance that Democrats win a majority (218 seats), and the same for Republicans.
- **Beside every number:** the poll average (from the statistics-only twin, so no news is in it), the prediction
  market and the Cook Political Report rating.

## Suggested changes to `site/content/methods.md`

1. **Starting levels:** add incumbency (about 5 points; half for an appointed senator) and the likely-voter adjustment.
   Add that polls never count for more than about 80%.
2. **Voter groups:** say where the vote split comes from: Kev, trained on real survey answers about the 2024 vote,
   with all groups shifted to the race's starting margin.
3. **News and reactions:** add "polls are read net of the news", so no one thinks a story is counted twice.
4. **How big a reaction is:** "about 0.21 of a group's stated reaction" reads as 21% of the shift. Suggested: "the
   strongest possible reaction to a fully covered story moves about a fifth of a group's persuadable voters".
5. **The weekly filter:** it uses every poll, not only the week's. It borrows strength from the national dial, checks
   how fast news fades and flags surprising states.
6. **Simulated elections:** name the four shared errors, and the House seats sharing them.
7. **Add the House** once it is public (12 Oct).
8. **Approved by Matteo (29 Sep):** add the reaction model's lean to the weekly filter section: "The model we use for
   reactions sits slightly on the Republican side of real past opinion shifts, by about a quarter of a point per
   event; a small fixed correction takes that out, re-estimated every week." The filter runs every Monday; its first
   run (5 October) is private.
