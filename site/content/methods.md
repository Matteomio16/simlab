NotAPoll.org forecasts the 3 November 2026 US midterms with a **social simulation**: statistics set where each race
starts, then **synthetic voters** react to the news as it happens, day by day, until election day. It is not a poll —
nobody is asked a question, and no output here should be read as "voters say" anything. Every number we publish sits
next to the poll average, the prediction market and the Cook Political Report rating, so you can see where we agree
and where we don't.

## How it works, in four steps

1. **Statistics set each race's starting level.** A blend of polls (corrected for pollster lean) and fundamentals
   (the state's partisan lean, the national mood and the candidates' past results) gives each Senate and House race a starting margin and an uncertainty
   range, before any simulation runs.
2. **Synthetic voter groups react to each day's news.** Twenty-eight synthetic voter groups per race read a neutral
   summary of the day's stories and react on vote choice and turnout. Only the people who can still move count: the
   *persuadable share* of a group for vote choice, and the *mobilisable share* for turnout. Firm partisans and
   habitual voters barely move the numbers, however strongly they react.
3. **A weekly filter checks the simulation against the evidence.** Every Monday, it compares how the polls actually
   moved with what the simulated reactions predicted, and tunes, state by state, how much the news moves each race.
4. **40,000 simulated elections turn it into chances.** Each race's uncertainty is drawn thousands of times, with
   realistic correlation between races and state, so a bad night for one party in similar states tends to happen
   together. The result: each race "wins X in 100 simulated elections." A result between 35 and 65 in 100 is called a
   toss-up.

## The details

### Starting levels

Each race's starting margin blends two estimates:
- **Fundamentals:** the state's partisan lean (0.62 × the latest presidential margin plus 0.26 × the one before), the
  national mood (the generic ballot, lowered by 2.8 points, its average overstatement of Democrats, and presidential
  approval), incumbency (worth about 5 points, half for an appointed senator), and 0.38 of the nominee's over- or
  under-performance in their last statewide race.
- **Polls:** each pollster's **house effect** (its steady lean compared with other pollsters, measured over 2018–24 and
  re-checked on this year's polls) is taken out. Polls of registered voters or all adults are adjusted to a
  likely-voter basis. Versions of the same poll count as one. Polls paid for by a party, campaign or partisan group
  count half and are shifted away from the sponsor by about 2.5 points. The average can drift a little every day, so
  older polls count less as time passes.

The blend follows how much each estimate is worth in that race. A heavily polled race leans on its polls, but polls
never count for more than about 80%, because even a large poll average can miss, as in 2016 and 2020. A race without
polls starts from the fundamentals alone. Each race shows how much its polls count.

### Voter groups

Each race splits its electorate into the same 28 synthetic voter groups: party identification (seven levels) × white
or not × a four-year degree or not. Each group carries:
- **its share of the electorate:** Census data on who lives in the state, with party identification from a large
  academic study of voters (CES), matched to the state's 2024 result;
- **its midterm turnout:** Census turnout figures, matched to the official count;
- **its vote split:** from Kev, a model we trained on real survey answers about how each kind of voter voted in 2024.
  All groups are then shifted together until they add up to the race's starting margin, so the split decides only
  the pattern across groups, never the race's level;
- **its persuadable share** (people who changed their mind or started undecided) and **its mobilisable share** (people
  whose turnout was uncertain), from survey respondents interviewed before and after the 2018 and 2022 midterms. These
  two numbers limit how much the news can move a group: firm partisans and habitual voters barely move it.

### News and reactions

Each day's stories come from GDELT and, once set up, Media Cloud. Every story is reduced to a short, neutral event
card, with outlet names removed before any model sees it. Stories about polls or forecasts get no reactions, because
polls already enter through the starting levels and the filter.

How much attention a story gets comes from coverage data (outlets, articles, days in the news and page views), not
from a model's guess, which only breaks ties.

- **News moves every race.** A race with polls and a race without them get the same effect from the same story.
- **Polls are read net of the news.** When a poll was taken while a story was moving voters, the story's simulated
  effect is taken out before the poll enters the average, so no story is counted twice: once in the polls and once in
  the simulation.
- **Stories fade.** Every story fades from the day it first appears, with a **5.5-day half-life**: about 41% is left
  after a week, 17% after two, 7% after three. A one-off story (an endorsement, a scandal, a debate, an ad) also drops
  within about a day once it leaves the news. Lasting topics, such as prices or a war, keep only the age fade.

### How big a reaction is

The synthetic voters give the direction and strength of a reaction; real events set its size. The scale was fitted on
45 past events with measured opinion shifts: the strongest possible reaction to a story with full attention moves
about a fifth of a group's persuadable voters, or of its mobilisable voters for turnout.

This isn't one fixed number. Each of the 40,000 simulated elections draws its own sizes around the fitted value, so no
single estimate drives the forecast, a lesson from an earlier project that got a result's direction right but badly
understated its size (see "What this can't do"). Each race shows how its forecast changes if the news matters less or
more.

### The weekly filter

Every Monday, the filter compares how all the polls actually moved with what the simulated reactions
predicted.
- **Dials:** it sets two dials per state, one for vote switching and one for turnout. A dial above 1 means the news
  moves that state more than simulated; below 1, less. It never changes a reaction's direction.
- **Borrowing strength:** states with few polls stay close to the national dial, and the dials' uncertainty goes into
  every simulated election.
- **Fade speed:** it also checks how fast news fades, weighing half-lives from about 3 to 11 days.
- **Surprises:** it flags any state whose polls surprised the forecast in the latest week.
- **Lean correction:** the model we use for reactions sits slightly on the Republican side of real past opinion
  shifts, by about a quarter of a point per event; a small fixed correction takes that out, re-estimated every week.

### Simulated elections and uncertainty

Every day, 40,000 elections are drawn from each race's margin and uncertainty. The random numbers are fixed by the
date, so rerunning a day gives the same result. Errors are shared, so a bad night for one party tends to happen
everywhere at once:
- a **national** error, including polls missing in the same direction nationwide (about 3 points on its own);
- a **regional** error, shared by states in the same census division;
- a **state** error, shared by all races in a state;
- each race's **own** error, which takes the rest.

The draws have **fat tails**: an unusually large swing is more likely than a bell curve would allow, and it happens in
the same simulated year for every race. No two Senate races move independently; each pair keeps at least a 0.25
correlation.

### The statistics-only twin

Every day, the same chain also runs with the news reactions switched off: statistics and polls only, no synthetic
voters. This is the benchmark the simulation has to beat, and if it can't, that is reported.

### Two numbers: 3 November and "if the election were today"

Because news effects fade, a story that is fresh today will have partly faded by 3 November. Each race carries two
numbers: the **3 November** forecast, which counts what each story should still be worth on election day, and **"if
the election were today"**, which counts everything in force now. The second is also less uncertain, because there is
no time left for things to change.

### The Senate headline

The headline is "Republicans hold 50+ seats" (the Vice President breaks a 50–50 tie). King and Sanders count with
Democrats, as they caucus with them today. The new independent candidates are shown on their own, with the share of
simulated elections in which they hold the balance.

## Models

Several specialised models do narrow jobs in the pipeline, each chosen for measured accuracy and cost on our own test
bench, not for being the biggest or best-known AI model:

- **Jev** (a decision model, not a text generator) labels the day's news — is this story relevant to this race, and
  what kind of event is it — because it passed our null test almost perfectly (99% "no change" on irrelevant news)
  and flipped its reactions most cleanly when the parties in a story were swapped.
- **GLM-5.3 Flash** turns each event card into a reaction from each synthetic voter group, because it ranked 19 real
  events from 2012 to 2026 best of all tested models and got the direction right on every one that moved opinion. No
  model got the size of reactions right, which is why sizes come from data (see above).
- **DeepSeek V4.1 Flash** writes the short, neutral event cards that voter groups read.
- **Kev**, an open decision model we fine-tuned on real survey answers about the 2024 vote, sets how each voter group
  splits between the parties. The split is then shifted to the race's statistical starting line, so it never sets the
  race's level.
- **MiMo-V2.6-Pro** runs the weekly auditor role, which explains why a state's polls have been surprising the model — it
  never changes any number itself.
- **GPT-6 Luna** spot-checks reactions and helps set the reference labels for news; it is the only US-built model
  in the pipeline. The engine deliberately avoids Google and Anthropic models, so the forecast doesn't inherit any single
  lab's assumptions.

The hard rule behind all of this: **the simulation never sets the starting numbers — it only moves them.** Statistics
always sets where a race begins; models only ever supply the day-to-day change on top.

## What we compare against

Every forecast is shown next to three independent benchmarks: the average of published polls, prediction markets
(Kalshi and Polymarket — used only as a comparison; their prices are never fed into the simulation), and the Cook
Political Report's ratings. From 19 October, every Monday, each week's forecast is checked against the polls published
in the following week: the average error in margin points, and the share of races where the forecast moved the same
way the polls later did. After the election, every forecast is scored against the results with the **Brier score**
(the average squared error of a win probability: 0 is a perfect call, 0.25 is what a coin flip scores) and **log
loss** (a similar score that penalises confident wrong calls more heavily). Published scores are never rewritten, and
the misses are published too. See the [track record](/track-record).

## What this can't do

- **Training-data leakage.** Some models were trained on data covering past elections and events, so backtests
  before 2026 can be partly the model remembering how something turned out, not reasoning about it. We flag this
  rather than claim clean validation on older data.
- **Simulated voters are not real people.** They are statistical constructs built from real survey respondents, not
  a panel of actual people who were asked anything. Their reactions are an estimate, not a measurement.
- **Models can carry hidden bias.** Testing every model with the same story told with the parties swapped shows most
  keep a small, sometimes uneven, lean; we measure and publish this rather than assume neutrality.
- **Poll scarcity early on.** Several 2026 Senate races have few or no polls yet, so their early forecasts rest mostly
  on fundamentals and carry wider uncertainty until more polling arrives.
- **The Hungary lesson.** An earlier social-simulation project (April 2026, on Hungary's election) correctly called
  the winner but badly understated the size of the result — the simulated vote share was about 16 points short of
  the actual outcome, and turnout was also badly off. That is why this project sets starting levels from statistics
  rather than the simulation itself, and treats reaction sizes as ranges, not single numbers.

## Sources and credits

- CES 2024, via the Harvard Dataverse — voter-group vote choice and demographics.
- Census CPS 2024 November supplement — turnout by demographic group.
- MIT Election Lab, via the Harvard Dataverse — historical election results.
- Wikipedia poll tables, used under CC BY-SA 4.0 with attribution.
- GDELT — daily news discovery.
- Media Cloud — planned as a second news source, pending API access.
- Kalshi and Polymarket — shown as benchmarks only, never as an input.
- The Cook Political Report — shown as a benchmark rating only, never as an input.

This page is a draft reviewed by Matteo Mio before launch. Last updated 29 Sep 2026, with the Statistics session's summary.
