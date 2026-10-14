Every day we forecast the 35 Senate races of 3 November 2026 by simulating the social dynamics of the campaign: how
the news moves different groups of voters.
Statistics set where each race started, on 12 October. Since then, **voter personas**, built from real survey
answers, carry each day's events into every race, and polls only check us. Then each race is played out 40,000 times. It is a social simulation, not a poll: we don't ask
people what they think today, we model how they react. Each step below takes a few lines; open **In detail** for the full method.

Each voter persona is a language model given one group's profile, so its reactions are the model's estimates, not
anyone's real opinion. The profiles come from real people: about 60,000 who answered each of the 2018, 2022 and 2024
Cooperative Election Studies, and the Census Current Population Survey for turnout. The models and their jobs are
listed below. We read every post before it goes out, and check each day's site update, story summaries included,
the same day.

## How a forecast is made

### Statistics set the starting line, once

Before any persona reacts, each race starts from a margin built from two estimates: the polls in that race, with each
pollster's usual lean taken out, and the fundamentals: the state's partisan lean, the national mood, incumbency and
the candidates' past results. The more a race is polled, the more its polls count, up to about 80%. A race without
polls starts from the fundamentals alone. That starting point was fixed as published on 12 October. Polls don't move
it again: from then on, a race changes only when the news moves its voters.

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
  shifts, by about a quarter of a point per event. A small fixed correction takes that out.

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

### Every Sunday, the polls check us

Since 12 October, every move in a race comes from how voter personas react to the news. Polls and prediction markets
no longer feed in; we use them to check our work. Each Sunday we compare how far each race moved in our forecast with
how far its poll average moved that week, in either direction. A gap above 3 points is flagged and looked into; above
5, we investigate before the next run; above 6.5, and only if the investigation finds the week went wrong, we may undo
that race's week, back to where it stood the week before. That is never automatic: it is a decision we take and
explain in Monday's post. Where no new polls came out, we compare with the markets and only flag.

#### In detail

- **Nothing is re-fitted from polls.** The weekly step no longer adjusts any race's level or how strongly a state
  reacts to the news; it only reports. A change to how strongly a state reacts can come only out of an investigation,
  is dated in the changelog and is explained in a lab note.
- **Enough polls first:** a gap counts as more than a flag only when at least three new polls came out in that race
  that week.
- **What gets fixed:** an investigation can find a bug, a story summary that was wrong, a story matched to the wrong
  race or a state reacting too strongly. Each fix is dated in the changelog, and both versions are scored.
- **Early vote:** we save the counts North Carolina, Maine and Iowa publish, and Texas's from about 19 October. They
  don't feed the forecast or the weekly check yet; if they start to, the change will be dated here.

### Then each race is played out 40,000 times

Each simulated election draws its own errors, at four levels, so a bad night for one party in similar states happens
together, as it does in real elections. A candidate's chance is the share of simulated elections they win. Between 45
and 55 in 100 we call the race a toss-up; from 55 to 65 it leans to the leader, from 65 to 85 it is likely theirs,
and above 85 safe.

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
- **Few polls at the start.** Several Senate races had few or no polls on 12 October, so their starting points rest
  mostly on the fundamentals and carry wider ranges.

## Sources and credits

- CES 2024, via the Harvard Dataverse: voter groups' vote choice and party identification.
- Census Current Population Survey, November 2024: turnout by voter group.
- MIT Election Data and Science Lab, via the Harvard Dataverse: past election results.
- Wikipedia poll tables, used under CC BY-SA 4.0 with attribution.
- GDELT and Media Cloud: daily news discovery.
- State election offices' early-vote files: counts only.
- Kalshi and Polymarket: shown as benchmarks, never used as an input.
- The Cook Political Report: shown as a benchmark rating, never used as an input.
