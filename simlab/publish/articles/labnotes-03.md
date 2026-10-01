One of our first results looked like a political lean. A model seemed to tilt toward Republicans across a whole set of stories. It wasn't politics. It was the order of the answers.

Some models favour whichever answer comes first, the way some people tick the first box on a form. Our answer scale happened to list the Republican side first, so a model with that habit looked Republican.

{{slide:2}}
To find a built-in lean, we use what we call the mirror test.

Each news story is told twice, with the parties swapped: once about a Democrat, once about a Republican, same facts, same words. A fair model's reactions to the two versions should mirror each other exactly. Whatever is left over, once the mirror is folded, is a built-in lean.

Then we asked every question in both orders: the answer scale as written, and reversed. If the lean flips when the order flips, it comes from the order, not from politics.

#### In detail
The test used 16 stories and 28 voter personas, one real respondent for each mix of party, race and education. The answer scale had five steps, from strongly toward the Republican to strongly toward the Democrat. The lean is the average of the two mirrored reactions, as a share of the model's typical reaction size, so models that react strongly and models that react gently can be compared.

{{slide:3}}
Averaging both orders cancels most of it.

Asked one way, GLM-5.3 Flash leaned {glm1} of its typical reaction toward Republicans. Asked both ways and averaged, the lean fell to {glm2}. DeepSeek went from {ds1} to {ds2}, and MiMo, which leaned the other way, from {mimo1} to {mimo2}.

GPT-6 Luna barely leaned either way, and Jev's small lean hardly changed. One got worse: Kev, before any training of ours, leaned more after averaging. It had failed other checks too, which is part of why we trained our own version.

#### In detail
Negative numbers lean Republican and positive numbers lean Democratic. Kev untuned went from {kev1} to {kev2}. These are leans on stories built to be perfectly symmetric, so a fair model would score zero; they say nothing about which party any real event helps.

{{slide:4}}
So every question in our forecast is asked both ways.

It doubles the cost of each answer, which is still a few cents per thousand answers. We tried something cheaper first: measuring each model's lean once and subtracting a fixed correction. It removed only about two-thirds of GLM's lean, because the lean grows with the size of the reaction. Asking twice removes it where it happens.

That is a small engineering choice with a large consequence. A forecast that leans by a few points on every story, every day, drifts a long way over a month of campaign news.

It is also a reminder of why we test before we trust. A lean that comes from the layout of a question can look exactly like a political opinion. Without the mirror test we would have read it as one, and every reader of our forecast would have inherited it. Checks like this are part of the experiment, and we will keep publishing them, including the ones that don't go our way.

#### In detail
In practice, every scale question is asked as written and reversed, and every multiple-choice question in three different orders; the answers are averaged before anything enters the forecast. On the mirror test, GLM's leftover lean was −0.124 asked one way, −0.045 with the fixed correction, and −0.006 asked both ways. We keep the both-ways rule for every model in the forecast, including the ones that looked fair, so that no lean can creep in unnoticed as stories change.

Next in Lab notes: the models know which way voters move, but not how far, and what we use instead.
