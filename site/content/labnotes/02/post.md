# Lab notes 02: the outlet name changed the answer

Draft for Matteo's approval. Planned date: Sun 04 Oct 2026.

## Checks

- All rules pass.

## Style notes

- None.

## Slides and alt text

1. `slide-1.jpg`: 41 percent of headlines got a different answer when we swapped Fox News for MSNBC. Same story; only the outlet's name changed.
2. `slide-2.jpg`: The same headline, shown three ways: with no outlet, credited to Fox News, and credited to MSNBC.
3. `slide-3.jpg`: Credited to MSNBC, GLM leaned 30 points more Democratic. Bar charts: shift toward helps Democrats, GLM plus 30 points, Jev plus 15; top answer flipped, GLM 41 percent, Jev 15 percent.
4. `slide-4.jpg`: Our models never see an outlet's name: stories become short neutral event cards first.

## Instagram caption

We took 80 real headlines about this year's Senate races and showed each one to two models three times: once on its own, once credited to Fox News and once credited to MSNBC. The words never changed. Then we asked which party the news helps.

If a model judges the event, the answer should stay put. It didn't. Credited to MSNBC instead of Fox, the same headline made GLM lean 30 points more towards "helps Democrats", and on 41% of headlines its answer flipped completely. Jev moved about half as much.

This says nothing about either channel. It shows that the models read the outlet as a clue about the story, the way many readers do.

Our models never see where a story came from. Each story is first rewritten as a short, neutral description of what happened, because a forecast shouldn't care where you read the news.

#midterms2026 #elections

A live experiment in social simulation, built from real survey answers. Method: notapoll.org

## Thread for X, Threads and Bluesky

1/ (197 characters) We showed two models the same 80 headlines, credited first to Fox News, then to MSNBC. One of them changed its answer about which party the news helps on 41% of them. Social simulation, not a poll.
2/ (125 characters) It isn't about either channel. The models have learned to read the outlet as a clue about the story, the way many readers do.
3/ (149 characters) Our models never see where a story came from; each one becomes a short, neutral description first. A forecast shouldn't care where you read the news.

## Website article

People read the news through its source. The same headline lands differently when it comes from Fox News or from MSNBC, and that is part of how real opinion works. But a forecast has to judge the event itself. So we checked whether our models do the same thing people do, and how much.

They do, and one of them a lot.

{{slide:2}}
We took 80 real headlines about the 2026 Senate races, from September, and wrote each one three ways. Once on its own. Once credited to Fox News. Once credited to MSNBC. The words of the headline never changed.

Then we asked two models the same question every time: which party does this news help?

If a model judges the event, its answer should stay put across the three versions. If it judges the messenger, the answer should drift with the outlet's name.

#### In detail
The 80 headlines were real ones about the 2026 Senate races, collected in September. The question asked which party, if either, the news helps. We asked GLM-5.3 Flash, the model we use for the direction of reactions, and Jev, the small model we use to sort relevant news from noise.

{{slide:3}}
Both models moved. One moved a lot.

When the same headline was credited to MSNBC instead of Fox News, GLM's lean toward "helps Democrats" rose by 30 points on a scale from −100 to +100. On 41% of the headlines its top answer flipped outright: the same story became good news for the other party.

Jev moved too, about half as much: 15 points, with its top answer flipping on 15% of headlines.

It's worth being clear about what this does not show. It says nothing about whether Fox News or MSNBC reports fairly. The headlines were identical; only the label changed. What it shows is that the models have learned an association between each outlet and each party, and they let that association decide what a story means. A person who distrusts one outlet might do the same. A forecast that wants to be fair to both sides can't.

#### In detail
The lean is the probability a model gives to "helps Democrats" minus the probability it gives to "helps Republicans", measured on each version of each headline. The flip rate counts headlines whose most likely answer changed between the Fox and MSNBC versions.

{{slide:4}}
So no model in our forecast ever sees an outlet's name.

Before any model reads the news, we strip the outlet and rewrite each story as a short, neutral event card: what happened, who was involved, in which race. Then the voter personas react to the event, not to the brand on top of it.

That matters for fairness as much as for accuracy. A forecast that quietly gives more weight to one side's media would tilt every number it publishes, and readers would never know.

It also changes what the voter personas react to. A story about a candidate's plan on prices should move the voters who care about prices, whether it was first reported on a conservative channel, a liberal one or a local paper. Stripping the outlet keeps the personas' attention on what happened. How much attention a story gets still comes from how widely it was covered, across outlets of every kind.

#### In detail
The event cards go through a neutrality check before they are used. Phrases that pass judgment instead of describing, such as calling something "a blow to" a party or "good news for" a candidate, are rejected. Only those neutral cards ever appear in our posts; the original headlines stay in our private records.

Tomorrow in Lab notes: a model that looked Republican, because of the order in which we listed the answers.
