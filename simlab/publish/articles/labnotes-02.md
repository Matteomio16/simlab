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
