# Lab notes 01: six models, four tests, one shared blind spot

Draft for Matteo's approval. Planned date: Sat 03 Oct 2026.

## Checks

- All rules pass.

## Style notes

- style: "respondents" (prefer voter personas or social simulation)

## Slides and alt text

1. `slide-1.jpg`: Before forecasting a single race, we asked six models to behave like voters: four tests, scored against what really happened. Six models, four tests, $1.52 in total.
2. `slide-2.jpg`: Four questions we asked every model: does a football score move a Senate race; if the parties swap, does the reaction swap; does it move the way people really moved; does it know how groups voted in 2024.
3. `slide-3.jpg`: Some got the direction right, none got the size: Jev ignores irrelevant news 99% of the time; GLM gets the direction right on 13 of 13 events; no model gets the size right; plain statistics know how groups voted better than every model.
4. `slide-4.jpg`: They all got the same things wrong: too calm about real shocks like COVID and January 6, too excited about the debates. So the size of every reaction comes from how people really moved.
5. `slide-5.jpg`: Real history sets the size of every reaction. Statistics set where each race starts, the voter personas react to each day's news, and how far each group moves comes from past events.

## Instagram caption

Before forecasting a single race, we wanted to know whether a model can react to the news the way a group of voters really would. We put six models through four tests. Does a football score move a Senate race? It shouldn't. If you swap the parties in a story, does the reaction swap too? Does the model move the way people actually moved on 19 real events since 2012? Does it know how groups voted in 2024?

Some got the direction right. Jev ignored irrelevant news 99% of the time, and GLM-5.3 Flash read the direction of 13 out of 13 real events correctly. None of them got the size of a reaction right.

They also failed in the same way. They stayed calm where people were shaken, like COVID and January 6, and got excited where people shrugged, like the debates. Averaging them doesn't fix that.

In our forecast, statistics set where each race starts, and a model trained on real survey answers estimates how each group of voters usually splits between the parties. The size of every reaction comes from how people really moved in past events, and the voter personas decide which way the news pushes each group.

The whole test cost $1.52. Tomorrow we'll show what happened when we put a different TV channel's name on the same headline.

#midterms2026 #elections

A live experiment in social simulation, built from real survey answers. Method: notapoll.org

## Thread for X, Threads and Bluesky

1/ (204 characters) Before forecasting a single race, we wanted to know whether a model can react to the news the way a group of voters really would. So we tested six of them on four questions. Social simulation, not a poll.
2/ (153 characters) Jev ignored irrelevant news 99% of the time, and GLM-5.3 Flash read the direction of 13 of 13 real events. None of them got the size of a reaction right.
3/ (179 characters) They also failed the same way: calm where people were shaken (COVID, January 6), excited where people shrugged (the debates). Real history sets the size of every reaction instead.
4/ (123 characters) The whole test cost $1.52, and an untuned Kev reacted to about 1 irrelevant story in 4. More in our Lab notes: notapoll.org

## Website article

Before we forecast a single race of the 2026 midterms, we wanted to know one thing: can a language model stand in for a group of voters and react to the news the way that group really would? So we asked six of them to try, and scored them against what actually happened.

The test bench ran on 27 and 28 September. It cost $1.52 in total. What it taught us shaped every part of the forecast you will see from 12 October.

{{slide:2}}
We asked every model the same four questions, in the same words, with the same voter personas.

Does a football score move a Senate race? It shouldn't. We showed each model 20 stories that shouldn't change anyone's vote, from sports results to a new seasonal croissant, and checked whether it stayed still.

If you swap the parties in a story, does the reaction swap with them? We told 16 stories twice, once with a Democrat at the centre and once with a Republican, and looked for any lean left over.

Does it move the way people actually moved? We used 19 real events since 2012 whose effect on opinion was measured at the time, and asked whether each model saw the right direction, and the right size.

Does it know how groups of Americans voted in 2024? We compared its answers with the real vote, group by group.

#### In detail
The six models were Jev 1.13, Kev 4B before any training of ours, GLM-5.3 Flash, MiMo-V2.6 Flash, DeepSeek V4.1 Flash and GPT-6 Luna, all reached through OpenRouter. Every question was asked twice, with the answer scale in both orders, for reasons we explain in Lab notes 03. The voter personas came from real respondents to the 2024 Cooperative Election Study, chosen to span party, race and education.

{{slide:3}}
No model was good at everything. Each was good at one thing, or at nothing.

Jev, a small decision model, was the best at ignoring news that doesn't matter: it said "no change" 99% of the time. GLM-5.3 Flash was the best at reading which way a group moves: it got the direction right on 13 of 13 real events that shifted opinion.

None of them got the size of a reaction right. GLM's sizes barely tracked reality, with a correlation of 0.26 between what it predicted and what was measured.

And on the most basic question, how groups voted in 2024, plain statistics beat every model we tried.

#### In detail
On that last test we measured the gap between each model's answers and the real vote across demographic groups. A simple statistical model built on the same survey answers was about twice as close as the best language model. An untuned Kev, the model we later trained ourselves, reacted to about 1 irrelevant story in 4, which is why it got no job in this round.

{{slide:4}}
The most useful finding was a shared one. The models didn't just make mistakes; they made the same mistakes.

All of them were too calm about real shocks: the early weeks of COVID, January 6, the fall of Kabul. All of them were too excited about media spectacles, like the Access Hollywood tape and the presidential debates. A story that dominated television moved them more than a crisis that changed how people lived.

Because the errors line up, averaging several models doesn't cancel them out. So in our forecast, the size of every reaction comes from shifts that were actually measured in past events, never from a model's guess.

#### In detail
Across the 19 events, the models' errors correlate between +0.88 and +0.97 with each other. Averaging any two of them never beat GLM alone. We use the models for what they do well, the direction of a reaction, and real data for everything else.

{{slide:5}}
So this is how the forecast is put together.

Statistics set each race's starting line: past results, the economy and the poll average. How each group of voters usually splits between the parties comes from Kev, a model we trained on real survey
answers, which came out slightly closer to the real 2024 vote than the plain statistics on three states it had never seen.

Then, every day, the voter personas react to each day's news, and the model's job is narrow: which way does this story push each group? How far it pushes comes from measured history. Every week, the latest poll average decides how much of that shift to keep.

Tomorrow in Lab notes: what happened when we told the same story with a different newspaper's name on it.
