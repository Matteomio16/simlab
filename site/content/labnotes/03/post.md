# Lab notes 03: one model looked Republican

Draft for Matteo's approval. Planned date: Mon 05 Oct 2026.

## Checks

- Website article: 573 words (aim 600–900)

## Style notes

- style: "respondents" (prefer voter personas or social simulation)

## Slides and alt text

1. `slide-1.jpg`: One model looked Republican. It was the order of the answers. We test every model for a built-in party lean: GLM's, as a share of a typical reaction, was −44% asked one way and −2% asked both ways.
2. `slide-2.jpg`: We tell every story twice, with the parties swapped; a fair model mirrors itself exactly. Then every question is asked in both orders.
3. `slide-3.jpg`: Dot chart of each model's built-in lean, as a share of a typical reaction, one way versus both ways averaged: GLM −44% → −2%, DeepSeek −65% → −16%, MiMo +70% → +27%; GPT-6 Luna and Jev near zero.
4. `slide-4.jpg`: Now every question is asked both ways. A fixed correction removed only about two-thirds of the lean.

## Instagram caption

For a while, one of our models looked Republican. Every model we use is tested for a built-in party lean: we tell each story twice with the parties swapped, and a fair model reacts the same way to both versions.

GLM didn't. Its lean was −44% of a typical reaction. The cause turned out to be the answer scale, which listed the Republican side first; some models favour whichever answer comes first.

We asked every question both ways, once in each order, and averaged the two. GLM's lean dropped to −2%, DeepSeek's went from −65% to −16% and MiMo's from +70% to +27%.

Now every question in our forecast is asked both ways. It costs a few cents per thousand answers and keeps the order of a question from tilting the numbers.

#midterms2026 #elections

A live experiment in social simulation, built from real survey answers. Method: notapoll.org

## Thread for X, Threads and Bluesky

1/ (178 characters) For a while, one of our models looked Republican, with a built-in lean of −44% of a typical reaction. It turned out to be the order of the answers. Social simulation, not a poll.
2/ (148 characters) Some models favour whichever answer comes first, and our scale listed the Republican side first. Asked both ways and averaged, the lean fell to −2%.
3/ (111 characters) DeepSeek went from −65% to −16%, MiMo from +70% to +27%. Now every question in our forecast is asked both ways.

## Website article

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

Asked one way, GLM-5.3 Flash leaned 44% of its typical reaction toward Republicans. Asked both ways and averaged, the lean fell to 2%. DeepSeek went from −65% to −16%, and MiMo, which leaned the other way, from +70% to +27%.

GPT-6 Luna barely leaned either way, and Jev's small lean hardly changed.

#### In detail
Negative numbers lean Republican and positive numbers lean Democratic. These are leans on stories built to be perfectly symmetric, so a fair model would score zero; they say nothing about which party any real event helps.

{{slide:4}}
So every question in our forecast is asked both ways.

It doubles the cost of each answer, which is still a few cents per thousand answers. We tried something cheaper first: measuring each model's lean once and subtracting a fixed correction. It removed only about two-thirds of GLM's lean, because the lean grows with the size of the reaction. Asking twice removes it where it happens.

That is a small engineering choice with a large consequence. A forecast that leans by a few points on every story, every day, drifts a long way over a month of campaign news.

It is also a reminder of why we test before we trust. A lean that comes from the layout of a question can look exactly like a political opinion. Without the mirror test we would have read it as one, and every reader of our forecast would have inherited it. Checks like this are part of the experiment, and we will keep publishing them, including the ones that don't go our way.

#### In detail
In practice, every scale question is asked as written and reversed, and every multiple-choice question in three different orders; the answers are averaged before anything enters the forecast. On the mirror test, GLM's leftover lean was −0.124 asked one way, −0.045 with the fixed correction, and −0.006 asked both ways. We keep the both-ways rule for every model in the forecast, including the ones that looked fair, so that no lean can creep in unnoticed as stories change.
