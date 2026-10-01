Every day we forecast the 35 Senate races of 3 November 2026 by simulating the social dynamics of the campaign: how
the news moves different groups of voters.
Statistics set where each race starts. **Voter personas**, built from real survey answers, carry each day's events
into every race. Then each race is played out 40,000 times. It is a social simulation, not a poll: we don't ask
people what they think today, we model how they react. Each step below takes a few lines; open **In detail** for the full method.

## How a forecast is made

### Statistics set the starting line

Before any persona reacts, each race starts from a margin built from two estimates: the polls in that race, with each
pollster's usual lean taken out, and the fundamentals: the state's partisan lean, the national mood, incumbency and
the candidates' past results. The more a race is polled, the more its polls count, up to about 80%. A race without
polls starts from the fundamentals alone.

{{fig:blend}}

#### In detail

- **Fundamentals:** the state's lean (0.62 × the latest presidential margin plus 0.26 × the one before), the national
  mood (the generic ballot, lowered by 2.8 points, its average overstatement of Democrats since 2012, plus presidential
  approval), incumbency (about 5 points, half for an appointed senator) and 0.38 of the nominee's over- or
  under-performance in their last statewide race. The weights were fitted on the elections of 2012 to 2024.
- **Polls:** each pollster's house effect, its steady lean compared with other pollsters, is measured on 2018–24 polls
  and re-checked on this year's. Polls of registered voters or all adults are adjusted to a likely-voter basis.
  Versions of the same poll count once. Polls paid for by a party, campaign or partisan group count half and are
  shifted away from the sponsor by about 2.5 points. Older polls count less as the days pass.
- **The blend** follows how much each estimate is worth in that race, with polls capped at about 80%, so no race rests
  on its polls alone. Each race page shows how much its polls count.

### Voter personas carry the news into each race

Each state's electorate is split into 28 voter groups: seven levels of party identification, white or not, with a
four-year degree or not. Each group has a voter persona, built from real survey answers: how many such people live in
the state, how often they vote in midterms, how they split between the parties, and how many of them could still
change their mind. Every day, each persona reads a neutral summary of each story and reacts, on whom to vote for and
on whether to vote at all.

{{fig:groups}}

#### In detail

- **Share of the electorate:** Census data on who lives in each state, with party identification from the
  Cooperative Election Study (CES), matched to the state's 2024 result.
- **Midterm turnout:** the Census Current Population Survey, matched to each state's official count.
- **Vote split:** from Kev, an open model we fine-tuned on real survey answers about how each kind of voter voted in
  2024. All groups are then shifted together until they add up to the race's starting margin, so the split shapes the
  pattern across groups and never the race's level.
- **Who can still move:** the persuadable share (people who changed their mind or started undecided) and the
  mobilisable share (people whose turnout was uncertain), from people the CES interviewed before and after the 2018
  and 2022 midterms.
- **Stories** come from GDELT and Media Cloud. Each is reduced to a short, neutral summary with outlet names removed,
  and its attention comes from coverage data: outlets, articles, days in the news and page views. Stories about polls
  or forecasts get no reactions.

### Only voters who can still move, move the numbers

A strong reaction from firm partisans changes little; a mild one from undecided voters can change a race. A reaction
applies only to the share of a group that could still change: the persuadable share for vote choice, the mobilisable
share for turnout. The strongest possible reaction to a story with full attention moves about a fifth of those voters,
a scale fitted on 45 past events with measured shifts in opinion.

{{fig:movable}}

#### In detail

- **Sizes are ranges, not single numbers.** Each simulated election draws its own sizes in three layers: one overall
  scale, each state's sensitivity, and each story's strength, which can turn out about 40% stronger or weaker than
  simulated, as past events did. A national story's draw is shared by every race it reaches; a state story stays in its
  own race.
- **Every race shows** how its forecast changes if the news matters less or more.
- **Lean correction:** the model that gives the reactions sits slightly on the Republican side of real past opinion
  shifts, by about a quarter of a point per event. A small fixed correction takes that out, and it is re-estimated
  every week.

### News fades

Every story fades from the day it first appears, with a half-life of 5.5 days: about 41% of its effect is left after
a week, 17% after two and 7% after three. A one-off story, such as an endorsement or a debate, drops within about a
day once it leaves the news; lasting topics, such as prices or a war, keep only the slow fade.

{{fig:fade}}

#### In detail

- **Two numbers per race.** The 3 November forecast counts what each story should still be worth on election day.
  "If the election were today" counts everything in force now, and is less uncertain, because there is no time left
  for things to change.
- **The fade is checked** every week against half-lives from about 3 to 11 days.
- **No story counts twice.** When a poll was taken while a story was moving voters, the story's simulated effect is
  taken out before the poll enters the average.

### Every Monday, the evidence checks the simulation

Each Monday we compare how each state's polls actually moved with what the personas' reactions predicted, and tune two
dials per state: how much the news moves vote choice there, and how much it moves turnout. A dial can make reactions
larger or smaller; it never changes their direction. Where states publish early-vote counts, the real counts check the
simulated turnout.

#### In detail

- **Borrowing strength:** states with few polls stay close to the national dial, and the dials' own uncertainty goes
  into every simulated election.
- **Surprises** are flagged for any state whose polls moved against the forecast in the latest week.
- **Early vote:** North Carolina and Maine publish counts now; Iowa and Texas from mid-October. Only counts are used.

### Then each race is played out 40,000 times

Each simulated election draws its own errors, at four levels, so a bad night for one party in similar states happens
together, as it does in real elections. A candidate's chance is the share of simulated elections they win. Between 35
and 65 in 100 is a toss-up.

{{fig:layers}}

#### In detail

- **Fat tails:** an unusually large swing is more likely than a bell curve allows, and when it happens it happens in
  every race at once.
- **A floor of 0.25:** any two Senate races share at least that much of their polling and fundamentals error. The news
  never gets the floor: a story about one state moves only that state's race.
- **Repeatable:** the random numbers are fixed by the date, so rerunning a day gives the same result.
- **The Senate headline** is "Republicans hold 50+ seats", since the Vice President breaks a 50–50 tie. King and
  Sanders count with Democrats, as they caucus with them today. New independent candidates are shown on their own,
  with the share of simulated elections in which they hold the balance.

## How we keep score

### Every number sits beside four others

Each forecast is published next to four benchmarks, so you can see where we agree and where we don't. The most
important is our own twin: the same model with the voter personas switched off. If the simulation can't beat it, we
say so.

{{fig:benchmarks}}

### Scored in public, right or wrong

From 19 October, every Monday, each week's forecast is checked against the polls published in the following week:
the average error in margin points, and the share of races where the forecast moved the same way the polls later did.
After the election, every forecast is scored against the results. Published scores are never rewritten.

#### In detail

- **Brier score:** the average squared error of a win probability. 0 is a perfect call; 0.25 is what a coin flip
  scores.
- **Log loss:** a similar score that penalises confident wrong calls more heavily.
- **Divergence calls:** where our forecast differs most from the benchmarks, we name the race before the result is in.

## The models, and why each one

### Small models, each doing one narrow job

Several small, specialised models each do one job in the chain, each chosen on our own test bench for accuracy and
cost, not for size or fame. The rule behind all of them: the simulation never sets a race's starting numbers. It only
moves them.

{{fig:models}}

#### In detail

- **The test bench:** every model faced the same four checks: reproduce how real groups voted in 2024; stay still on
  20 irrelevant stories; flip its reaction when the parties in a story are swapped; and rank 19 real events from 2012
  to 2026 by their measured effect on opinion.
- **No model got the size of reactions right,** which is why sizes come from data rather than from any model.
- **We avoid Google and Anthropic models** in the engine, so the forecast doesn't inherit one lab's assumptions.

## What this can't do

- **Voter personas are not people.** Each stands for a group of real people and is built from real survey answers.
  A persona's reaction is an estimate, not a measurement.
- **Models remember.** Some models were trained on text about past elections, so a test on an old race can partly
  measure memory rather than reasoning. We flag this rather than claim clean validation on past years.
- **Models lean.** Telling the same story with the parties swapped shows most models keep a small, sometimes uneven,
  lean. We measure it, correct it and publish it.
- **Few polls early on.** Several Senate races have few or no polls yet, so their forecasts rest mostly on the
  fundamentals and carry wider ranges until more polling arrives.

## Sources and credits

- CES 2024, via the Harvard Dataverse: voter groups' vote choice and party identification.
- Census Current Population Survey, November 2024: turnout by voter group.
- MIT Election Data and Science Lab, via the Harvard Dataverse: past election results.
- Wikipedia poll tables, used under CC BY-SA 4.0 with attribution.
- GDELT and Media Cloud: daily news discovery.
- State election offices' early-vote files: counts only.
- Kalshi and Polymarket: shown as benchmarks, never used as an input.
- The Cook Political Report: shown as a benchmark rating, never used as an input.
