> Snapshot exported from Claude Docs on 27 Sep 2026. Live version: https://claude.ai/code/artifact/673aa293-22c4-4d3a-806e-6a50c69f82cc (not readable from Claude Code). If this file and CLAUDE.md disagree, CLAUDE.md wins.

# Midterm Simulation Engine: Research Map

2026-09-27 · @Matteo Mio

The goal is to prove that simulation, not polling alone, can forecast an election. Data and statistics set each race's starting vote levels; AI voter agents then simulate how sentiment and turnout change as news arrives, and a weather-style filter reconciles the simulation with incoming evidence every week. The output is a pre-registered, daily forecast for 35 Senate races and 40 competitive House seats before 3 November.

## Hungary scorecard

The Hungary run called the winner but missed the size of the wave: TISZA was 16.5 points and 40 seats short of the real result. That gap is the most useful data point we have, because it shows exactly what the next engine must fix.

| Measure | Simulation (λ = 0.58) | Actual, 12 Apr 2026 | Miss |
| --- | --- | --- | --- |
| TISZA list vote | 36.7% | 53.2% | −16.5 pts |
| Fidesz list vote | 41.0% | 38.6% | +2.4 pts |
| Mi Hazánk | 3.9%, out | 5.6%, in (6 seats) | wrong side of threshold |
| DK / MKKP | 7.0% / 6.7%, both in | both below 5% | wrong side of threshold |
| TISZA seats | 101 | 141 (two-thirds) | −40 |
| Fidesz seats | 84 | 52 | +32 |
| Turnout | 69.2% | 79.0% | −9.8 pts |

For scale: Focaldata's statistical MRP model forecast 123 TISZA seats and 70 for Fidesz, but the real result still sat inside its 95% interval ([Focaldata](https://www.focaldata.com/blog/how-we-forecasted-the-hungarian-election)). The high-transfer scenario (λ = 0.80, 125 seats) was the closest thing the paper produced.

**What it teaches**

* **Agents stayed near their starting beliefs.** Real voters did something more extreme: DK and MKKP voters did not just transfer in constituencies, they abandoned those parties entirely. The simulation had no way to produce a wave that its seed priors did not already contain.
* **Mobilisation was the story, and it was not modelled.** Turnout jumped 9.4 points. Who turns out is the variable agent simulations should be best at, and ours treated it as a fixed survey answer.
* **Matching polls is not the same as being right.** The corrected shares landed within 1 point of Median's polling, and the website still frames accuracy that way. Scoring against the actual result, with uncertainty, is the standard the midterm project needs.
* **The corrections were manual.** Eleven fixes applied by judgement cannot be repeated at 470 races. They need to become an automatic calibration layer.
* **45 agents is statistically thin.** One run with 45 agents carries roughly ±7.5 points of sampling noise on a close split, before any model error, and the paper gave no probability.

None of this undermines the idea. It tells us to model change and turnout explicitly, to calibrate automatically, and to score honestly.

## The landscape

Five families of methods exist, and every serious midterm forecast today is built from the first three. Agent simulation is the only family nobody has yet made work live, which is exactly why it is the frontier.

| Family | Needs polls? | What it does well | Where it breaks | Who does it now |
| --- | --- | --- | --- | --- |
| **Fundamentals** (structural models) | No | Generic ballot, approval and seat exposure explain over 80% of House seat swings since 1946 | Says nothing about individual races or candidates | [Abramowitz](https://centerforpolitics.org/crystalball/generic-ballot-model-gives-democrats-strong-chance-to-take-back-house-in-2026/), [thermostatic model](https://matthewg.org/thermostatic.pdf) |
| **Bayesian poll models** | Yes | Fundamentals prior, polls update it daily, correlated errors across states | Inherits poll bias (2022 averages missed by ~2–3 pts) | [Silver Bulletin FLIPR](https://www.natesilver.net/p/flipr-midterms-model-methodology), [FiftyPlusOne](https://blog.fiftyplusone.news/p/no-president-has-gone-into-a-midterm), [DDHQ](https://votes.decisiondeskhq.com/forecast/2026), The Economist |
| **MRP** (statistical microsimulation) | Yes, large samples | District-level estimates from demographics | Expensive; static snapshot | YouGov, [Focaldata](https://www.focaldata.com/blog/how-we-forecasted-the-hungarian-election) |
| **Markets and AI forecasters** | Indirectly | Liquid markets beat most models; AI bots reached rough parity with superforecasters in 2026 | Markets price in polls; bots trail markets on the same questions | [Polymarket](https://polymarket.com/event/which-party-will-win-the-senate-in-2026), Kalshi, [Mantic](https://techstartups.com/2026/09/18/british-ai-startup-mantic-raises-25m-to-build-superhuman-ai-forecasting-after-metaculus-win/), [Metaculus bots](https://www.greaterwrong.com/posts/wZBbDqzfBjYG58CxK/futureeval-spring-results-pros-beat-bots-but-the-gap-is) |
| **Agent simulation** (classic and LLM) | Optional | Models *why* and *how* opinion moves; can test counterfactuals | No validated live election record; LLM agents drift and converge | [Aaru](https://techcrunch.com/2025/12/05/ai-synthetic-research-startup-aaru-raised-a-series-a-at-a-1b-headline-valuation), [Simile](https://www.unite.ai/simile-raises-more-than-200-million-at-a-2-billion-valuation-to-scale-human-behavior-simulations/), [MiroFish](https://github.com/666ghj/MiroFish), [OASIS](https://arxiv.org/abs/2411.11581), [AgentTorch](https://arxiv.org/abs/2409.10568), academic papers |

The field is well funded but unproven. Aaru raised at a $1B headline valuation and Simile at $2B, yet Aaru's one public presidential call (Harris, 2024) was wrong and Simile publishes no election forecasts. Current consensus for 3 November is a Democratic House (models 72–98%, markets ~92%) and a Democratic-leaning Senate (54–69%).

## What the evidence says

LLM agents are good at reproducing *average* opinions of well-documented groups and at ranking how people react to messages. They are bad at levels, variance, small parties, turnout and anything after their training cutoff.

**What works**

* **Richer individual data beats clever prompts.** Agents built from 2-hour interviews matched 85% of people's own test-retest consistency; demographics-only agents reached 74% ([Park et al. 2024](https://arxiv.org/abs/2411.10109)).
* **Fine-tuning on survey data.** Training on 70K subpopulation-response pairs closed up to 46% of the gap to real distributions ([SubPOP](https://arxiv.org/abs/2502.16761)).
* **Predicting reactions, not levels.** GPT-4 predicted treatment effects across 70 experiments as well as pooled human experts, even for unpublished studies, though it overstated effect sizes ([Ashokkumar et al., Nature 2026](https://www.nature.com/articles/s41586-026-10742-x)). This is the capability our news-reaction layer needs.
* **Anchoring personas to real respondents.** Matching each synthetic voter to similar ANES respondents cut wrong 2016/2020 states from 8 to 2 ([Jiang et al.](https://arxiv.org/abs/2411.01582)).
* **Scale through archetypes.** Query the LLM once per *type* of voter, then apply the answers to millions of simulated people; 8.4M-agent runs with gradient-based calibration ([AgentTorch](https://arxiv.org/abs/2409.10568)).

**What fails**

* **Out-of-the-box vote levels.** Nine LLM setups overstated Harris's 2024 favourability by 10–40 points; adding web search did not help ([Parikh et al. 2026](https://www.arxiv.org/pdf/2602.06302)).
* **Variance collapse.** Synthetic samples are far too uniform; 48% of regression coefficients differed from human data ([Bisbee et al.](https://www.cambridge.org/core/journals/political-analysis/article/synthetic-replacements-for-human-survey-data-the-perils-of-large-language-models/B92267DC26195C7F36E63EA04A47D2FE)).
* **Networks of LLM agents converge.** Talking agents drift toward consensus unless bias is injected ([Chuang et al.](https://arxiv.org/abs/2311.09618)), which explains the "stayed near priors" and urban-convergence effects in the Hungary run.
* **Small parties and legislatures.** A Korean agent model got 3/3 presidents right but 0/2 legislatures, predicting a third party at 0.9% against 21.4% actual ([Dynamo-K](https://arxiv.org/html/2605.18395)).
* **Leakage.** Telling a model "pretend it is October 2024" closes only 48% of the knowledge-leak gap, and reasoning models are worst ([Li et al. 2026](https://arxiv.org/html/2601.13717v1)). Most published "accurate" backtests are contaminated.
* **Validation by vibes.** Most frameworks, MiroFish included, have no quantitative validation; the field mostly checks whether output looks believable ([Larooij & Törnberg](https://arxiv.org/abs/2504.03274)).

The single best recent LLM election result is modest: 330K ANES-based personas with GPT-4o got 9 of 11 swing states and a 3.5-point weighted error on 2024, but published after the election ([Yu et al.](https://arxiv.org/html/2412.15291v2)).

## The frontier

Five open problems are within reach of a two-person team in 37 days, ranked by how much they would move the field. The first two together would be a genuine first.

1. **A live, pre-registered, probabilistic agent-simulation forecast, publicly scored.** Nobody in the literature has published one with uncertainty, timestamped before the election and scored with Brier scores against the result. This is the headline contribution.
2. **Data assimilation for LLM social simulations.** Weather forecasting keeps a simulation honest by nudging it toward each new observation with an ensemble Kalman or particle filter. It has been used for flu forecasting, but no one has applied it to LLM agent electorates. Your weekly "flag the inconsistency and learn" idea is exactly this, and it has a name and a mathematics.
3. **Does social interaction add anything?** Compare static personas against the same agents talking in an OASIS-style network, under identical calibration. Nobody knows whether the "social" part of social simulation improves forecasts. Either answer is publishable.
4. **Modelling change and turnout, not levels.** Use agents only for the deltas they are good at (reaction to news, mobilisation, strategic switching) and take levels from data. This directly targets the Hungary failure.
5. **Leakage-controlled backtests.** Test on elections after each model's training cutoff (Hungary 2026, Virginia and New Jersey 2025) and report how much apparent accuracy is leakage. The field badly needs an honest benchmark.

## Recommended engine

Build a four-layer engine: statistics set where each race starts, simulation drives how it moves. Each layer uses the best tool for its job, and the highlighted filter is where the research novelty lives.

Proposed engine · 4 layers, 3 inputs, 1 feedback loop

* **Synthetic electorate and starting levels.** Cluster Cooperative Election Study respondents into archetypes and weight them to each state's census and 2024 results (remapped to the new districts). A statistical baseline (fundamentals, past results, polling where available) sets each archetype's starting vote and turnout. Each archetype gets a narrative persona (e.g. NVIDIA's Nemotron-Personas) and a media diet.
* **Voter agents simulate change.** Agents read each day's events for their race and state how their support and likelihood of voting shift, drawing on how similar events moved similar voters in past cycles. Answers are collected as distributions (semantic-similarity scoring or direct distribution prompts) to avoid the variance collapse LLMs are known for. Agents interacting in an OASIS network is the intended core; it stays core if it beats static personas in the ablation, otherwise a better simulation-driven method replaces it.
* **Assimilation filter.** Run hundreds of perturbed copies of the electorate. When evidence arrives, keep and multiply the copies that agree with it and drop the rest. What does not match becomes a logged "innovation" that an auditor agent diagnoses.
* **Mechanics.** Monte Carlo over correlated state and district errors turns simulated vote shares into win probabilities. The other ~395 House seats come from a fundamentals map (district lean plus national environment) that we re-check regularly.

**Budget: under $50 a month.** That rules out a full simulation of every race every day. The plan: a full ensemble run once a week, daily incremental runs only for races with meaningful new events, one shared news digest per race (prompt caching makes "same news, many agents" cheap), a low-cost or open model, and batch APIs. Spend rises only when a pilot result justifies it.

## Your loop, made rigorous

Your idea (simulate daily from the news, check weekly against polls, investigate disagreements) is data assimilation, the method that makes weather forecasts work. Four refinements turn it from a good instinct into a defensible method.

1. **Flag only real disagreements.** Polls have their own error: generic-ballot averages have missed by 3.9 points on average since 1998 ([ABC/538](https://abcnews.com/538/2024-predictor-polls-special-elections/story?id=107369614)). A flag fires only when the gap exceeds the combined uncertainty of both sides.
2. **Learn parameters, not answers.** When a flag fires, re-tune the few dials (how strongly each archetype reacts to each event type, turnout elasticity), never the forecast directly. Otherwise the engine quietly becomes a slow poll average.
3. **Let an agent diagnose, let maths decide.** An auditor LLM can explain *which* archetype or event caused the gap, but the update itself follows the filter's rules and is logged. That log is also your paper's most interesting section.
4. **Two clocks.** The reaction layer runs daily; the filter assimilates polls weekly (your chosen day) and optionally markets daily.

**The no-polls question: the assimilated simulation is the headline, the blind one a research track**

| Track | Sees | Role |
| --- | --- | --- |
| **Assimilated (headline)** | Structure, news, polls and markets folded in weekly by the filter | The public forecast: can a simulation that sees the same data beat pure aggregation? |
| **Blind (research)** | Structure, news, special elections, fundraising; no 2026 horse-race polls or markets | How much of an election can be simulated without asking anyone? |

Be precise about "no polling": the synthetic electorate is still built from past surveys, and the LLM was trained on text that includes polls. The honest claim is "no contemporaneous 2026 horse-race polls".

The blind track's strongest non-poll signal is special elections: 110 contests since January 2025 show Democrats running 12.5 points ahead of Harris's 2024 margin, a figure that historically overstates the November result by 3–5 points ([The Downballot](https://www.the-downballot.com/p/100-specials-since-trumps-return)). Fundamentals add approval (net −22) and seat exposure ([Abramowitz](https://centerforpolitics.org/crystalball/generic-ballot-model-gives-democrats-strong-chance-to-take-back-house-in-2026/)).

## Pilot race

Start with the Ohio Senate special (Brown v Husted), and run North Carolina alongside as a validation twin. Ohio is a true toss-up with a free voter file; North Carolina has the densest polling to check the engine against.

| Race | State of play (late Sep) | Voter file | Why | Risk |
| --- | --- | --- | --- | --- |
| **Ohio special**: Brown (D) v Husted (R) | Toss-up; latest Quantus 45.6–45.3 Brown; markets near 50–50 | Free statewide | Clean two-way race; Brown's 2006–2024 races give crossover history; governor race on same ballot tests correlation | Fewer polls than NC |
| **North Carolina**: Cooper (D) v Whatley (R) | Lean/Likely D; Cooper +8 to +15 | Free, with vote history | Best validation: 11+ polls since June | Lopsided, so less to learn about toss-ups |
| **Texas**: Talarico (D) v Paxton (R) | Toss-up; TPOR Talarico +5, Emerson Paxton +1 | Paid | Sharp age split suits agent modelling; liquid markets | Weaker pollsters; costly data |

Avoid Maine (nominee replaced in July, ranked-choice), Alaska (ranked-choice, four candidates) and Nebraska (independent v Republican) for the pilot. Texas joins as a third pilot, using CES, AP VoteCast and census data instead of the ~$1.5k statewide voter file, plus the free UT/Texas Politics Project poll microdata. Once Ohio runs end-to-end, the same code extends to all 35 Senate races, then to the House through district-level archetype weights. Sources: [Newsweek on Ohio](https://www.newsweek.com/jon-husted-in-dead-heat-against-sherrod-brown-as-he-breaks-with-trump-12485030), [Carolina Journal](https://www.carolinajournal.com/polls/september-2026-roy-coopers-lead-grows-to-15-points-in-nc-senate-race/), [TPOR](https://texaspublicopinionresearch.substack.com/p/new-poll-in-texas-general-election-662), [Cook](https://www.cookpolitical.com/analysis/senate/senate-overview/fight-senate-true-toss-three-races-shift-toward-democrats).

## Data and infrastructure

Everything the engine needs is free; the full inventory is in the next section. The stack is small enough to run on a laptop plus a daily scheduled job.

| Need | Source | Access |
| --- | --- | --- |
| Voter archetypes | [Cooperative Election Study](https://tischcollege.tufts.edu/research-faculty/research-centers/cooperative-election-study/data-downloads) (2006–2024 cumulative, validated vote), ANES 2024, AP VoteCast | Free |
| Population weights | Census ACS API; Ohio and North Carolina voter files | Free |
| Past results and new maps | MIT Election Lab; Redistricting Data Hub; Dave's Redistricting | Free |
| Money | FEC API | Free key |
| News | GDELT, Media Cloud, RSS | Free |
| Markets | Kalshi, Polymarket, PredictIt APIs | Free, no auth for prices |
| Polls | Wikipedia tables via the MediaWiki API; [VoteHub API](https://votehub.com/polls/api/) (generic ballot, approval); pollster releases | Free |
| Daily LLM calls | A low-cost model via OpenRouter or batch APIs | Under $50/month target |
| Leak-free backtests | OLMo 3 (Dec 2024 cutoff) or other open models with known cutoffs | Free |

**Build:** Python, DuckDB for the data, a scheduled daily job (Cowork scheduled task or GitHub Actions), and a live forecast page on scaliastudio.dev. Reuse OASIS from MiroFish only for the social-network arm; MiroFish's own report layer is where most Hungary artefacts came from, and it is AGPL-licensed.

## Free data stack

Every input the engine needs has a free source, except the Texas voter file and live ad-spend data. Advocacy-linked sources are used only for cross-checks, never as model inputs.

| Category | Free sources | Notes |
| --- | --- | --- |
| Polls | Wikipedia tables (MediaWiki API, CC BY-SA); [VoteHub API](https://votehub.com/polls/api/) (generic ballot, approval, CC BY); [UT/Texas Politics Project](https://texaspolitics.utexas.edu/polling-data-archive) raw microdata; Emerson, Elon, High Point, Baldwin Wallace, Siena, Marist crosstabs | RealClearPolling's terms bar scraping, so manual cross-check only |
| Opinion microdata | [CES](https://tischcollege.tufts.edu/research-faculty/research-centers/cooperative-election-study/data-downloads) cumulative, ANES 2024, [AP VoteCast](https://apnorc.org/projects/ap-votecast-puf/) 2018–2024, Nationscape, GSS | VoteCast gives state-level voter and non-voter data, the free stand-in for exit polls |
| Results and maps | [MIT Election Lab](https://electionlab.mit.edu/data) (precinct 2016–2024); [Redistricting Data Hub](https://redistrictingdatahub.org/data/whats-new/) new-map files for TX, NC, OH; DRA; OpenElections; [The Downballot](https://www.the-downballot.com/p/data) district results and specials Big Board | All House baselines must use the new 2026 lines |
| Voter files | [North Carolina](https://s3.amazonaws.com/dl.ncsbe.gov/data/ncvoter_Statewide.zip) (weekly, with party and race); [Ohio](https://www6.ohiosos.gov/ords/f?p=VOTERFTP%3ASTWD%3A%3A%3A) | Texas costs ~$1.5k, so skipped |
| Money | FEC API and bulk files | Source of truth for all finance features |
| Candidates | Congress.gov API, Voteview (ideology scores), unitedstates/congress-legislators | ProPublica's Congress API is discontinued |
| Economy | BLS, BEA, FRED, EIA (state gas prices), UMich sentiment | All official, free keys |
| News | GDELT, Media Cloud (includes local news), Common Crawl News |  |
| Markets | Kalshi, PredictIt (NC, TX, OH Senate markets), Polymarket | Metaculus now needs a free token |
| Expert ratings | Cook, Sabato, Inside Elections, Split Ticket via [270toWin consensus](https://www.270towin.com/2026-senate-election/consensus-2026-senate-forecast) | Snapshot daily from now to 3 Nov for scoring |
| Benchmarks | 538 archive on GitHub, Economist model | Download now; ABC redirected 538 links in May 2026 |

**The Integrity Index.** The organisation you mentioned is the [Integrity Index](https://integrityindex.us/), run by the [Political Integrity Project](https://politicalintegrity.us/), a small-donor hybrid PAC. It grades every member of Congress and 2026 candidate on money in politics and tracks congressional stock trades. Its grade is value-laden by design: it penalises corporate PAC money and stock trading and gives bonus points for signing its own pledge ([methodology](https://integrityindex.us/methodology)), so it will likely correlate with party. Neutral use: rebuild the raw components (FEC receipts, stock disclosures) ourselves and use the site only as a cross-check. It has no API, so it would need careful scraping.

Other advocacy-linked sources get the same treatment: Issue One and End Citizens United (the latter a Democratic-aligned PAC), Catalist reports (Democratic-aligned firm), and Democracy Fund datasets (check funder framing).

## Software worth exploring

The open-source ecosystem already covers every layer, and two 2026 projects are close enough to be prior art we should cite and beat. Ranked by what to try first:

| # | Tool | Layer | Why it matters |
| --- | --- | --- | --- |
| 1 | [whyalwaysrose/midterms-forecast](https://github.com/whyalwaysrose/midterms-forecast) + VoteHub | Baseline | A working 2026 PyMC Senate/House poll model that refits daily: the benchmark our simulation must beat |
| 2 | [ccesMRPprep](https://github.com/kuriwaki/ccesMRPprep) + Meta's [balance](https://github.com/facebookresearch/balance) | Electorate | Clean CES into archetypes and weight them to census targets |
| 3 | [Nemotron-Personas-USA](https://huggingface.co/datasets/nvidia/Nemotron-Personas-USA) | Electorate | 6M census-aligned US personas for agent texture (no party field, so join from CES) |
| 4 | [OASIS](https://github.com/camel-ai/oasis) | Agents | The social-network arm; scales to 1M agents with feeds and follow graphs |
| 5 | [SGLang](https://github.com/sgl-project/sglang) + [instructor](https://github.com/567-labs/instructor) | Agents | Prefix caching makes "same news, many agents" cheap; schema-safe outputs. Key to the budget |
| 6 | [semantic-similarity-rating](https://github.com/pymc-labs/semantic-similarity-rating) | Agents | Turns agents' free-text answers into probability distributions, fixing variance collapse |
| 7 | [SubPOP](https://github.com/JosephJeesungSuh/subpop) LoRAs | Agents | Open models fine-tuned to predict subgroup opinion distributions; a check on prompted agents |
| 8 | [particles](https://github.com/nchopin/particles) + [DAPPER](https://github.com/nansencenter/DAPPER) | Filter | Particle filter and ensemble Kalman implementations to compare for the weekly step |
| 9 | [sbi](https://github.com/sbi-dev/sbi) / [BayesFlow](https://github.com/bayesflow-org/bayesflow) | Filter | Calibrate agent parameters on 2018–2024 cycles; re-infer weekly in milliseconds |
| 10 | [scoringrules](https://github.com/frazane/scoringrules) + Prefect + [Observable Framework](https://github.com/observablehq/framework) | Evaluation, publishing | Brier/CRPS scoring, daily orchestration, and a static live-forecast site |

**Prior art to cite and beat:** [ElectionSim](https://github.com/amazingljy1206/ElectionSim) and [SocioVerse](https://github.com/FudanDISC/SocioVerse) (LLM US election simulations), and [whoshowsup](https://github.com/kurtawirth/whoshowsup) (a 2026 turnout-first model).

**Wildcards:**

* [AgentTorch](https://github.com/AgentTorch/AgentTorch): differentiable agent simulation with LLM archetypes, calibrated by gradient. Closest to our design; AGPL licence conflicts with keeping code private, so use as reference.
* [AgentSociety2](https://github.com/tsinghua-fib-lab/AgentSociety): a Ray-scaled alternative to OASIS, released this week.
* [Concordia](https://github.com/google-deepmind/concordia): a "game master" for scripted campaign shocks (debates, scandals).
* Leak-free backtest models: OLMo 3 (Dec 2024 cutoff), Point-in-Time LLMs with monthly checkpoints to 2024.
* [Centaur-70B](https://www.nature.com/articles/s41586-025-09215-4): a model fine-tuned on human decisions as an agent backbone.
* [AutoEmulate](https://github.com/alan-turing-institute/autoemulate): emulate the LLM simulation with a cheap surrogate to cut calls ~100×.
* [pmxt](https://github.com/pmxt-dev/pmxt): one API across Kalshi, Polymarket and others.
* Graph neural networks (PyTorch Geometric Temporal) for county-to-county swing diffusion.

Watch licences: AgentTorch is AGPL, PersonaHub data is non-commercial, and properscoring was archived this month (use scoringrules).

## 37-day plan

The calendar is tight, so the rule is: a crude end-to-end forecast for Ohio first, public and timestamped by 12 October, then improve it in the open.

37-day build plan · 9 workstreams

Every published forecast gets a timestamp and a hash, so nobody (including us) can quietly revise it. Scaling to the House leans on district partisan lean plus the national environment, with agents used for the ~40 most competitive seats.

## Evaluation

We win the research argument only if the engine is scored against the result, against strong baselines, with probabilities. Beating nothing is not a result. Success means all four: beat poll averages, match or beat markets, beat expert ratings, and correctly call races where polls were wrong.

* **Scores:** Brier score and log loss on every race's win probability; mean absolute error on vote share; a calibration chart (do our 70% calls come true ~70% of the time?); CRPS on seat counts.
* **Baselines to beat:** a plain poll average; prediction-market prices (recalibrated, since political contracts are underconfident: a 70¢ contract a week out resolves yes ~83% of the time, per [Le 2026](https://arxiv.org/pdf/2602.19520)); an Abramowitz-style fundamentals model; Cook ratings.
* **Ablations:** blind v assimilated; static personas v social network; LLM reaction layer switched off (fundamentals + filter only). Each isolates what the AI actually adds.
* **Leakage control:** backtests only on elections after the model's training cutoff; telling a model to forget is not enough.
* **Honest reporting:** publish misses as prominently as hits. A combination of methods has historically beaten every single component ([PollyVote](https://en.wikipedia.org/wiki/PollyVote)), so "our engine improved the ensemble" is a legitimate win even if it does not beat markets alone.

## Decisions made

* **North star:** prove that simulation works; accuracy matters, but the forecast must be genuinely simulation-driven.
* **Scope:** 35 Senate races + 40 competitive House seats; other House seats from a fundamentals map, re-checked regularly.
* **Pilots:** Ohio and North Carolina, with Texas as a third on free data.
* **Agents:** statistics and data set starting levels; agents simulate how sentiment and turnout change with the news. Agents interacting is core if it wins the ablation.
* **Headline:** the poll-assimilated simulation; the blind track is secondary research.
* **Success bar:** beat poll averages, match or beat markets, beat expert ratings, and catch what polls miss.
* **Engine:** Python + OASIS, no MiroFish.
* **Data:** free only; scrape Wikipedia tables and pollster releases, no paid feeds.
* **Budget:** under $50/month, more only with a good reason.
* **Team:** solo to start, others if needed.
* **Openness:** methodology and forecasts public; open-sourcing the code decided later.
* **Publishing:** daily updates on the Scalia site, Instagram and X, building in public; produced here with Claude at first, automated later.
* **Hungary:** no website changes; focus stays on the midterms.

## Sources

**Your work:** The Simulation of Democracy (Mio, April 2026, Sim Research folder); [scaliastudio.dev/projects/hungary-2026](https://scaliastudio.dev/projects/hungary-2026); [2026 Hungarian election results](https://en.wikipedia.org/wiki/2026_Hungarian_parliamentary_election).

**LLM simulation:** [Argyle et al. 2023](https://www.cambridge.org/core/journals/political-analysis/article/abs/out-of-one-many-using-language-models-to-simulate-human-samples/035D7C8A55B237942FB6DBAD7CAA4E49) · [Santurkar et al.](https://arxiv.org/abs/2303.17548) · [Bisbee et al.](https://www.cambridge.org/core/journals/political-analysis/article/synthetic-replacements-for-human-survey-data-the-perils-of-large-language-models/B92267DC26195C7F36E63EA04A47D2FE) · [Park et al., 1,000 people](https://arxiv.org/abs/2411.10109) · [SubPOP](https://arxiv.org/abs/2502.16761) · [Ashokkumar et al., Nature 2026](https://www.nature.com/articles/s41586-026-10742-x) · [Gong et al. 2026, distributions v individuals](https://arxiv.org/html/2603.20229) · [Parikh et al. 2026](https://www.arxiv.org/pdf/2602.06302) · [Chuang et al., consensus drift](https://arxiv.org/abs/2311.09618) · [Li et al., simulated ignorance](https://arxiv.org/html/2601.13717v1) · [Zhang & Stadie, leakage](https://arxiv.org/html/2608.02985) · [Larooij & Törnberg review](https://arxiv.org/abs/2504.03274)

**Election simulations:** [Yu et al.](https://arxiv.org/html/2412.15291v2) · [Jiang et al.](https://arxiv.org/abs/2411.01582) · [ElectionSim](https://arxiv.org/abs/2410.20746) · [Dynamo-K](https://arxiv.org/html/2605.18395) · [Aaru on 2024](https://www.semafor.com/article/11/06/2024/ai-startup-aaru-defends-using-artificial-intelligence-for-polling) · [Silver, AI polls are fake polls](https://www.natesilver.net/p/ai-polls-are-fake-polls) · [Fernández-Gracia et al., voter model](https://arxiv.org/abs/1309.1131)

**Frameworks and calibration:** [OASIS](https://github.com/camel-ai/oasis) · [MiroFish](https://github.com/666ghj/MiroFish) · [AgentSociety](https://arxiv.org/abs/2502.08691) · [Concordia](https://github.com/google-deepmind/concordia) · [AgentTorch](https://github.com/AgentTorch/AgentTorch) · [Dyer et al., simulation-based inference for ABMs](https://www.sciencedirect.com/science/article/pii/S0165188924000198) · [Shaman & Karspeck, flu data assimilation](https://www.pnas.org/doi/10.1073/pnas.1208772109)

**Forecasting:** [Linzer 2013](https://votamatic.org/wp-content/uploads/2013/07/Linzer-JASA13.pdf) · [Halawi et al.](https://arxiv.org/html/2402.18563v1) · [ForecastBench parity](https://forecastingresearch.substack.com/p/ai-models-have-likely-reached-parity) · [Rothschild & Wolfers, expectations](https://www.brookings.edu/research/forecasting-elections-voter-intentions-versus-expectations/) · [Split Ticket on 2022](https://split-ticket.org/2022/12/12/estimating-2022s-generic-ballot/)

**2026 landscape:** [Silver Bulletin generic ballot](https://www.natesilver.net/p/generic-ballot-average-2026-nate-silver-bulletin-congress-polls) · [Silver Bulletin approval](https://www.natesilver.net/p/trump-approval-ratings-nate-silver-bulletin) · [2025–26 redistricting](https://en.wikipedia.org/wiki/2025%E2%80%932026_United_States_redistricting) · [2026 Senate elections](https://en.wikipedia.org/wiki/2026_United_States_Senate_elections) · [DeFi Rate market tracker](https://defirate.com/prediction-markets/2026-midterms/)