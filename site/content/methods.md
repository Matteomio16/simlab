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
3. **A weekly filter checks the simulation against new polls and evidence.** Once a week, the run compares what the
   simulated voters produced against that week's real poll movement, and adjusts how much each state's simulation is
   trusted going forward.
4. **40,000 simulated elections turn it into chances.** Each race's uncertainty is drawn thousands of times, with
   realistic correlation between races and state, so a bad night for one party in similar states tends to happen
   together. The result: each race "wins X in 100 simulated elections." A result between 35 and 65 in 100 is called a
   toss-up.

## The details

### Starting levels

Each race's starting margin blends two things:
- **Fundamentals**: the state's partisan lean (0.62 × the latest presidential margin plus 0.26 × the one before it),
  the national political mood, and 0.38 of a candidate's own past over- or under-performance in their last
  statewide race.
- **Polls**, corrected for each pollster's **house effect** (a pollster's steady lean compared with other
  pollsters, measured across its history). Several versions of the same poll (with and without leaners, for example)
  are averaged into one entry. Polls sponsored by a party, campaign or partisan group count at half weight and are
  shifted back toward the middle by about 2.5 points, because sponsored polls have historically leaned toward
  whoever paid for them. Where the national generic ballot feeds into the fundamentals, it is lowered by 2.8 points,
  its average historical overstatement of Democrats.

The two are combined by how reliable each is for that race: heavily polled races lean mostly on polls, thinly polled
races lean mostly on fundamentals. A race with no recent polls starts from the fundamentals alone.

### Voter groups

The electorate in each race is split into 28 synthetic voter groups, defined by party identification (a seven-point
scale), race and education. Each group carries its share of the electorate, its expected turnout, its vote split, and
— the two numbers that limit how much news can move it — its persuadable share and its mobilisable share. Both are
estimated from real survey respondents interviewed before and after past midterm elections, so we know roughly how
many people in a group actually changed their mind or their turnout, rather than assuming everyone is up for grabs.

### News and reactions

Each day's stories come from two sources: GDELT, and (once set up) Media Cloud's national news collection. Every
story is reduced to a short, neutral event card, with outlet names removed before any model sees it, so nobody is
reacting to who published something. Stories about polls or forecasts get no reactions at all — polls already enter
through the weekly filter, so reacting to news about them would double-count the same information.

How much attention a story gets comes mainly from coverage data — outlets, articles, days in the news, and page
views — not from a model's guess, which only breaks ties between similarly covered stories.

How long a story's effect lasts:
- Every story fades from the day it is first seen, with a **5.5-day half-life** — about 41% of its effect remains
  after a week, 17% after two weeks, 7% after three.
- A one-off story (an endorsement, a scandal, a debate, an ad, a candidate's policy announcement) also fades within
  about a day once it drops out of the news, on top of the age-based fade.
- Lasting topics — the economy and prices, and national events such as a war or a disaster — keep fading at the
  age-based rate without that extra one-day drop, so they stay relevant for longer while still fading.

### How big a reaction is

A model's answer gives the direction and relative strength of a reaction, not its size. The size — how many points
of margin or turnout a reaction is worth — comes from data: real-world events with measured opinion shifts. On
average the switching effect is calibrated at about 0.21 of a group's stated reaction; the turnout effect starts from
the same value. This isn't one fixed number: every one of the 40,000 simulated elections draws its own size from a
range around that average, so no single data point can drive the whole forecast — a lesson from an earlier project
that got a result's direction right but badly understated its size (see "What this can't do"). Each race also shows
how its forecast would change if news mattered less, or more, than the central estimate assumes.

### The weekly filter

From 12 October, a weekly update compares the week's real poll movement against what the simulation produced, and
retunes — separately for each state — how much of the simulated reaction to trust going forward. It is a statistical
filter, not a model: it adjusts a dial, it does not overrule the simulated voters' direction.

### Simulated elections and uncertainty

The final step draws 40,000 simulated elections from each race's estimated margin and uncertainty. The draws use
**fat tails** (a statistical shape where a much bigger swing than usual is more likely than a plain bell curve would
suggest), because elections occasionally move further than recent history implies. A national error term, with a
standard deviation of about 3 points, covers the risk that polls miss in the same direction everywhere at once, as
they have in several recent cycles.

### The statistics-only twin

Every day, the same chain also runs with the news-reaction step switched off — statistics and polls only, no
synthetic voters. This is the benchmark the simulation has to beat: if the full simulation can't forecast better than
its own statistics-only twin, that is reported honestly, not hidden.

### Two numbers: 3 November and "if the election were today"

Because news effects fade over time, a story that is fresh today will have partly or fully faded by 3 November. Each
race therefore carries two numbers: the 3 November forecast, which counts only what a story is expected to still be
worth by election day, and "if the election were today," which counts everything in force right now.

### The Senate headline

The headline framing is "Republicans hold 50+ [of 100 seats]" (the Vice President breaks a 50-50 tie), because that
framing is clear regardless of how independents behave. Independent Senators King and Sanders are counted with
Democrats, as they caucus with them today. The newer independent candidates on the 2026 ballot are shown as
independents in their own right, with a separate figure for the share of simulated elections in which they hold the
balance of power.

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
Political Report's ratings. Accuracy is scored on fixed weekly dates using the **Brier score** (the average squared
error of a win probability — 0 is a perfect call, 0.25 is what a coin flip scores) and **log loss** (a similar score
that penalises confident wrong calls more heavily), starting 19 October. When we're wrong, the misses are published,
not quietly dropped.

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

This page is a draft reviewed by Matteo Mio before launch. Last updated 29 Sep 2026.
