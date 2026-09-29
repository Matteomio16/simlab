# Lab notes 01: we tested six models as synthetic voters

Planned date: Sat 03 Oct 2026.

## Checks

- All rules pass.

## Style notes

- None.

## Slides and alt text

1. `slide-1.jpg`: Title slide: Before forecasting the midterms, we tested six models as synthetic voters. Six models, four checks, $1.52 total cost.
2. `slide-2.jpg`: Bar chart of TISZA's vote share in Hungary, April 2026: simulated 36.7 percent, actual 53.2 percent. Right direction, 16 points short.
3. `slide-3.jpg`: The four checks: ignore irrelevant news; no built-in party lean; react correctly to 19 real events; match how groups voted and turned out in 2024.
4. `slide-4.jpg`: Results table. Relevance: Jev. Direction of reactions: GLM-5.3 Flash. Starting numbers: plain statistics. Size of reactions: no model.
5. `slide-5.jpg`: Statistics set where each race starts; the simulation moves it. Statistics and the poll average set each race's starting numbers, each voter group's starting split comes from a model trained on real survey answers, and synthetic voters simulate how news shifts support and turnout.

## Instagram caption

Before we forecast a single race, we tested six models as synthetic voters.

The question: can a synthetic voter react to news the way real groups of people do? Four checks, identical for every model:
1. Ignore irrelevant news
2. No built-in party lean
3. React correctly to 19 real events since 2012
4. Match how groups actually voted and turned out in 2024

No model was good at everything, so each got one job, or none. Jev is best at spotting news that doesn't matter. GLM gets the direction of reactions right. And plain statistics had smaller errors than every off-the-shelf model at matching how groups voted nationwide, so statistics and the poll average set each race's starting numbers. Each voter group's starting split comes from Kev, a model we trained on real survey answers (more in a later Lab note). The simulation then plays out how the news moves them.

Why test first? In April, our first simulation called Hungary's winner but came up 16 points short on the size.

Total cost of these tests: $1.52. The forecast goes public on Monday 12 October.

Social simulation, not a poll.

#midterms2026 #elections #socialsimulation #dataviz

## Thread for X, Threads and Bluesky

1/ (245 characters) Before forecasting the 2026 midterms, we tested six models as synthetic voters: can they react to news like real groups of people? Four checks, identical questions for every model. Here's what each one is good for. Social simulation, not a poll.
2/ (119 characters) Irrelevant news should change nothing. Jev said “no change” to 99% of it. An untuned Kev reacted to about 1 story in 4.
3/ (119 characters) Which way does a group react to real news? GLM-5.3 Flash got the direction right on 13 of 13 events that moved opinion.
4/ (248 characters) Where does each race start? Plain statistics beat every off-the-shelf model at matching how groups voted in 2024, so statistics and the poll average set each race's starting numbers. Group splits come from a model we trained on real survey answers.
5/ (108 characters) Total cost of the tests: $1.52. The forecast goes public on 12 October; the making-of runs daily until then.
