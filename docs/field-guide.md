> Snapshot exported from Claude Docs on 27 Sep 2026. Live version: https://claude.ai/code/artifact/c640add2-61d5-4d74-8fa2-c39365d09819 (not readable from Claude Code). If this file and CLAUDE.md disagree, CLAUDE.md wins.

# Election Simulation Field Guide

Sep 27, 2026 · @Matteo Mio

Everything we need to know before building the midterm engine: what others have tried, the science of how voters change, the tools, the data, the rules, and the options worth exploring. Compiled from six parallel research reviews on 27 September; companion to the Midterm Simulation Engine research map.

## Executive brief

The niche is open. Nobody has a pre-registered, probabilistic, scored track record for an AI-agent election forecast, and the few who went on record (Aaru 2024, BYU 2024, an EU 2024 study) were wrong. The evidence points to one design: statistics set the levels, agents simulate change under heavy damping, a filter corrects against evidence, and everything is frozen, timestamped and scored.

Ten things an expert would tell us:

1. **Voters barely switch during campaigns; turnout is where the action is.** Only 4–8% switch party between elections, and 2018 and 2022 were decided mostly by who turned out. Agents should spend their energy on enthusiasm and turnout, not persuasion.
2. **LLMs overreact.** GPT-4 got the direction of 469 experimental effects right but overstated size; the authors recommend multiplying by \~0.56. Persona agents overshoot real belief change 5–7×. Every agent-proposed shift needs a learned damping factor. That evidence comes from GPT-4-era models; today's cheaper models may be better calibrated, so our own test will measure the damping rather than assume it.
3. **LLM biases point one way.** Left lean, squeezed populists and third parties, exaggerated group gaps (a 47.6-point simulated gender gap against \~2 real). One-directional bias is fixable by calibration and by mixing model families with opposite biases.
4. **Rich LLM-written backstories push electorates left** until every state votes Democrat. Keep personas to structured survey fields: party ID, issue attitudes, vote history.
5. **Polls move because of who answers, not only what people think.** Over half of a post-debate swing in 2012 was partisan non-response. The filter must model poll bias so agents never chase phantom swings.
6. **A particle filter over 75 races will collapse.** Use an ensemble Kalman update on a compact factor state (national, regional, state, demographic, race) and a small particle filter only over the handful of agent parameters, estimated separately by state and region so a finding in Ohio is never assumed to hold in Texas.
7. **Don't assimilate markets.** Beating them is a success criterion, so they stay a benchmark.
8. **Every 2018–2024 backtest is contaminated.** Today's models know those results, and telling them to forget closes only half the gap. Clean tests are post-cutoff contests, and 3 November itself.
9. **Budget works only with shared archetypes.** 1,000 agents in each of 35 states costs \~$90–100/month even on the cheapest models; \~12 shared state clusters costs \~$32–35; the 3-state pilot \~$8.
10. **Never call it a poll.** AAPOR's May 2026 guidance, Silver's "AI polls are fake polls" and the Axios/Aaru correction make labelling the reputational make-or-break.

The strongest predecessor is not an LLM project: Fudan's rule-based agent model forecast Taiwan 2020 within 0.8 points and 6/6 US states in 2020 live, by screening every candidate model against replays of past elections before trusting it. That discipline is the template.

## Who has tried this

About 30 relevant projects exist; almost none has a scorable live record. The successes all pair a structural model with strict data screening or correction, and the failures all used raw LLM opinion as the forecast.

| Project | Approach | Live? | Result | Lesson for us |
| --- | --- | --- | --- | --- |
| [Fudan ABM](https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0270194) (Tang et al.), 2020 | Rule-based agents, no polls; models screened by replaying past elections | Yes | Taiwan within 0.8 pts; 6/6 US states | Screen by historical replay; treat agent rules as ranges |
| [Aaru](https://www.semafor.com/article/11/06/2024/ai-startup-aaru-defends-using-artificial-intelligence-for-polling), 2024 | AI characters fed tailored news | Yes | Called Harris; wrong | Publish vote shares with intervals, not a headline call |
| [BYU distribution method](https://arxiv.org/html/2411.03486v1), 2024 | LLM token probabilities as electorate | Yes, 4 Nov | Harris 303 EV; wrong. 2020 backtest error <0.45 pts | Pre-cutoff backtests are worthless (leakage) |
| [EU Parliament 2024](https://arxiv.org/abs/2409.09045) | 3 LLMs predict 26,000 real voters | Yes | "Largely fail" | Demographics alone fail; seed attitudes |
| ["Promise with a Catch"](https://arxiv.org/abs/2503.16527), 2025 | \~1M LLM-written personas | Retro | More persona text → every state Democrat | Minimal structured personas |
| [Yu et al.](https://arxiv.org/html/2412.15291v2), 2024 | 330K ANES personas, GPT-4o, ideology step | Retro | 3.5% error vs 21% demographics-only; 47.6-pt fake gender gap | Calibrate subgroup gaps, not just toplines |
| [Matching-LLM](https://arxiv.org/pdf/2411.01582), 2024 | LLM answers matched to real ANES rows | Unclear | Trump 309 EV vs 312 | Anchoring to real respondents fixes errors |
| [Dynamo-K](https://arxiv.org/html/2605.18395v1), Korea 2026 | Census agents, 4 model families | Retro + 1 held-out | 3/3 presidents, 0/2 legislatures; two models biased +11.8 and −17.2 | Ensemble opposite-bias models; audit ballot order |
| [Ipsos AI personas](https://www.research-live.com/article/features/a-new-lens-how-ai-personas-helped-ipsos-understand-the-2024-election/id/5147403), UK 2024 | 5 undecided personas through campaign | Yes, qualitative | 3/5 matched local winner; personas went stale | Refresh agent memory weekly |
| [Kronaxis](https://kronaxis.co.uk/blog/election-prediction-paper), UK 2026 | Census personas, 9 pipeline versions | Method pre-registered | 7.0-pt error after tuning on 8 races | Freeze the pipeline; don't overfit |
| [Focaldata](https://www.focaldata.com/blog/how-we-forecasted-the-hungarian-election), Hungary 2026 | Statistical MRP ensemble | Yes | TISZA 123 seats vs 141 | Same miss direction as ours: late turnout surge |
| [Metaculus bots](https://www.lesswrong.com/posts/wZBbDqzfBjYG58CxK/futureeval-spring-results-pros-beat-bots-but-the-gap-is), 2026 | LLM + news search forecasters | Yes | Near parity with pro humans | A plain LLM forecaster is a baseline we must beat |
| [Prediction Arena](https://arxiv.org/html/2604.07355v1), 2026 | Frontier LLMs trading real money | Yes | All lost 16–31% on Kalshi | "Beat markets" is a very high bar |
| [CDC FluSight](https://www.medrxiv.org/content/10.64898/2026.06.05.26354941v1), 10 years | Many models + ensemble | Yes | Ensemble near the top every year | Ensembles and persistence win |
| [INET Oxford COVID ABM](https://csh.ac.at/news/predicting-the-economic-downturn-during-the-pandemic/), 2020 | Economic agent model | Yes | UK Q2 GDP −21.5% vs −22.1% | Agent models shine on big structural shocks |

Not found anywhere: documented AI-agent forecasts for UK 2024, India 2024, Canada or Australia 2025, NJ/VA 2025, or any other Hungary 2026 attempt. The absence is itself the finding.

**People worth contacting:** Philipp Schoenegger (LSE, "wisdom of the silicon crowd"), Robb Willer's group (LLM effect prediction, [treatmenteffect.app](https://www.treatmenteffect.app/)), Leah von der Heyde and Anna-Carolina Haensch ([paper list](https://github.com/CaroHaensch/public_opinion_llms)), Shiping Tang (Fudan), Doyne Farmer (INET Oxford), Nicholas Reich (forecast hubs), Ezra Karger (ForecastBench).

## Modelling voter change

Real campaigns move votes through three channels: who turns out, a slow drift toward fundamentals, and small persuasion effects that fade within days. The agent layer should mirror that split and be heavily damped on persuasion, but not on turnout.

**What the science says**

- **Campaigns mostly "enlighten" voters toward fundamentals** rather than create new preferences ([Gelman & King 1993](https://www.cambridge.org/core/journals/british-journal-of-political-science/article/abs/why-are-american-presidential-election-campaign-polls-so-variable-when-votes-are-so-predictable/7936B534442ECC90D60934A450721E8F)). In midterms the out party gains \~5 points from February to November, mostly before Labor Day ([Bafumi, Erikson & Wlezien](https://digitalcommons.dartmouth.edu/cgi/viewcontent.cgi?article=3365&context=facoa)).
- **Persuasion in general elections is roughly zero** across 49 field experiments ([Kalla & Broockman](https://escholarship.org/uc/item/103775sx)); TV ads moved vote choice \~0.7 points, not significant ([Coppock et al.](https://alexandercoppock.com/coppock_hill_vavreck_2020.pdf)). Down-ballot ad effects have a half-life of 1–2 days.
- **Debates and disasters don't move vote choice** across 62 elections ([Le Pennec & Pons](https://www.nber.org/papers/w26572)). Trump's 2024 conviction had virtually no panel effect.
- **Phantom swings.** After the first 2012 debate, only 3% of panel respondents changed their answer; half the apparent swing was who chose to answer ([Gelman et al.](https://sites.stat.columbia.edu/gelman/research/published/swingers.pdf)).
- **Turnout decides midterms.** In 2022, turnout differences, not switching, drove Republican gains; only 6% of repeat voters crossed over ([Pew](https://www.pewresearch.org/politics/2023/07/12/republican-gains-in-2022-midterms-driven-mostly-by-turnout-advantage/)). Past vote history predicts turnout \~2.5× better than stated intent.
- **Candidates still matter a bit.** Incumbency is worth \~2–4 points and falling; Republican nominees in 2022 underperformed by \~6.6 points of margin. Sherrod Brown ran 7.6 points ahead of Harris in Ohio in 2024 and still lost.

**Starting ranges, not rules.** History supplies weak, wide starting points only. Every value is set per state, and the news and the filter recalibrate it as the campaign unfolds; what happens between now and 3 November is what should move the forecast. A prior stays only if the engine can't work without it.

| Quantity | Weak starting range | How it gets set per state and updated |
| --- | --- | --- |
| Share of voters open to switching | 4–8% nationally | Per state from CES panel and voter-file history; filter updates weekly |
| Where persuasion happens | Undecided and cross-pressured archetypes, \~10–15% nationally | Per-state share from CES; firm partisans near zero |
| Persuasion from ads or contact | Small by default (Kalla & Broockman; Coppock) | Loosened when polls move in ways fundamentals can't explain |
| How long a news effect lasts | Typically 1–2 days down-ballot (Hill et al.) | Learned per event type; persists if it changes fundamentals (approval, candidate quality, a scandal) |
| Size of a single event's shift | **No hard cap.** Heavy-tailed: most events move < 1–2 pts, rare shocks up to \~10 | Large shifts accepted when corroborated by several sources or by poll movement (e.g. a nominee swap like Maine's in July) |
| Weekly movement of true margin | Estimated, not assumed | From each state's own 2026 poll and early-vote history |
| Out-party midterm drift | +3–5 pts as a national prior (Bafumi et al.) | Overridden by current state data |
| Partisan turnout gap | 3–5 pts in past midterms (Pew) | Per state from early-vote files, specials and vote history |
| Economy to approval | Weak (e.g. gas prices, [G. Elliott Morris](https://www.gelliottmorris.com/p/2026-04-10-gas-price-approval-cotw)) | State-level prices and issue salience |
| How much to damp agent answers | Unknown for current models; GPT-4 needed ×0.56 ([Ashokkumar et al.](https://www.nature.com/articles/s41586-026-10742-x)) | Measured by our fidelity test, then learned per model and per state by the filter |

**Design rules for the agent layer**

1. **Constrain the model, free the system.** Models answer narrow, structured questions; the system decides how much of each answer to apply (damping, decay, weights), and the filter learns those settings per state. That is how we make the model accurate without giving it free rein.
2. Split each archetype's state into a fundamentals anchor, slow drift, decaying shocks, and turnout propensity.
3. Route most news reactions into enthusiasm and turnout. Vote switching happens mainly among undecided voters, and a little among cross-pressured archetypes; firm partisans barely switch.
4. No hard caps. Use heavy-tailed priors so a big shock can register, require corroboration for large shifts, and log what agents proposed versus what the system applied.
5. Ask "who was exposed and how did it land", never "would this change your vote": hypothetical questions overstate effects the same way LLMs do.
6. If agents interact in a network, add confirmation bias and homophily, or they will converge to consensus.
7. Keep an assumption register: every prior is state-specific, sourced and justified, and dropped if the engine works without it.

## Starting levels

Every professional model converges on the same baseline recipe, so ours should copy it rather than reinvent it: district partisan lean plus the national environment, adjusted for candidates, then blended with polls as they arrive.

**The recipe**

- **Partisan lean:** the last two presidential results relative to the nation, weighted 75–80% to 2024, on the new district lines ([The Downballot](https://www.the-downballot.com/p/the-downballot-releases-presidential) has 2024 results for all 145 redrawn districts).
- **National environment:** generic ballot and presidential approval, with special elections as a heavily discounted signal (Democrats are running \~13 points over Harris in specials against a \~D+6–8 generic ballot; specials historically overstate).
- **Candidate adjustments:** incumbency (half credit for first-termers, 70% kept after redistricting), prior elected experience (\~1.3 pts House, \~0.9 Senate), share of individual donations (in-state weighted up), scandals.
- **Polls-poor races:** borrow from similar districts. Silver's CANTOR scores every pair of districts on lean, race, education, religion, region and urbanisation, and lets polled races inform unpolled look-alikes.
- **Blend over time:** on election day, heavily polled Senate races are \~58% polls, 36% fundamentals, 6% ratings; House races \~50/40/10; unpolled races lean on fundamentals and ratings.

**State issue map.** For each state, identify the main issues (from CES state subsamples, local news, candidates' ads and poll issue questions), which archetypes care about each, and how each issue is likely to move undecided voters, sentiment, turnout and the few genuine switchers. This map sets each state's agent sensitivities, so Ohio's agents react to Ohio's campaign rather than to a national average.

| Model | Distinctive idea to borrow | Link |
| --- | --- | --- |
| Silver Bulletin FLIPR | Lite / Classic / Deluxe versions; CANTOR similarity; de-biased expert ratings | [methodology](https://www.natesilver.net/p/flipr-midterms-model-methodology) |
| FiftyPlusOne | Ensemble weighted by out-of-sample error; time-varying coefficients; excludes AI polls | [methodology](https://blog.fiftyplusone.news/p/2026-forecast-methodology) |
| 538 (archived) | National, regional and state error split; weights by poll count | [2024 Senate](https://abcnews.com/538/538s-2024-senate-election-forecast-works/story?id=114997770) |
| Split Ticket | Demographic swing from monthly microdata; candidate WAR score | [method](https://www.theargumentmag.com/p/split-ticket-2026-midterms-model) |
| Race to the WH | Partisan polls at half weight; top-two primaries as signals | [method](https://www.racetothewh.com/house/methodology) |
| DDHQ | Only major model blending in markets | [intro](https://decisiondeskhq.substack.com/p/2026-election-forecast-intro-part-1-senate-house-overall-redistricting) |

**Poll handling defaults:** weight by √(n / median n) capped at 10,000; one pollster's polls within 14 days share one weight; house-effect prior N(0, 3 pts); likely-voter adjustment capped at ±2; partisan-sponsored polls at half weight, shifted 2–4 points against the sponsor; recency decay \~3%/day early, 7–14%/day in the last two weeks. House-effect models neutralised most of the 2022 "red wave" poll flooding.

## Calibration, assimilation and uncertainty

The filter should work on a small factor-based state, not on every race separately, and it must keep a permanent term for shared poll bias so it never collapses into a poll average.

**The state.** Each race's margin = baseline + national environment + regional term + state term (shared by all races in the state) + demographic factors (≈6: white non-college, Black, Hispanic, suburban college, rural, age) + race-specific term, plus latent poll-bias terms. About 100–120 numbers in total. Unpolled races learn from polled look-alikes automatically through the demographic factors.

**The weekly cycle**

1. **Forecast step:** run 20–50 agent ensemble members with different agent parameters and seeds; they propose shifts to the environment, factors and races from the week's news. Add process noise sized to historical drift.
2. **Analysis step:** an ensemble Kalman update on the state, with covariance inflation (small ensembles are overconfident) and localisation through the factor structure.
3. **Agent parameters** (news sensitivity, persuasion rate, turnout elasticity; 5–8 of them) get their own small particle filter of 500–2,000 particles, resampled when effective sample size drops below half. This is where the filter learns how much the agents overreact. Parameters are indexed by state and region, pooled toward a shared value only where a state has too little data, so findings don't generalise by default.
4. **Daily between runs:** cheap Kalman updates from new polls, no LLM calls.
5. **Monitor innovations** with a chi-squared test; persistent excess means the simulator is biased and triggers an auditor review.

**Why not a full particle filter:** particle filters collapse in high dimensions; an agent-based model with only 30–40 agents needed \~10,000 particles ([Malleson et al.](https://www.jasss.org/23/3/3.html)).

**Calibrating the agents without leakage:** fit the statistical layer on 2006–2024 with nested splits; calibrate the LLM layer only on contests after the model's cutoff (2025–26 specials, 2026 primaries, Hungary). Use history matching with an emulator rather than thousands of LLM runs ([UQ-for-ABM tutorial](https://arxiv.org/html/2409.16776)).

**Uncertainty defaults (points of margin)**

| Parameter | Default | Source |
| --- | --- | --- |
| National election-day error SD | 3.5–4.8 | 538; generic ballot error 3.9 |
| Regional SD | 2.5–2.8 | 538 |
| Race SD, well-polled Senate | 4–5 | 538 |
| Race SD, unpolled House / Senate | 9 / 8 | FiftyPlusOne |
| Tails | Student-t, 8–10 degrees of freedom | FiftyPlusOne |
| Single poll total error | \~2× reported margin of error | [Shirani-Mehr et al.](https://sites.stat.columbia.edu/gelman/research/published/polling-errors.pdf) |
| Average poll error, final 3 weeks | Senate 5.4, House 6.2 | 538, 1998–2018 |
| Pairwise correlation floor | \~0.25 | [Economist model code](https://github.com/TheEconomist/us-potus-model) |
| Simulations | 40,000 | FLIPR, FiftyPlusOne |

**Lessons from past calibration:** 2016 models at 98–99% treated state errors as independent; 538 in 2018 was underconfident (Lean favourites won 83% vs 67% expected). Set bands from multi-cycle out-of-sample errors and check that correlations never go negative (538's 2020 model had Washington and Mississippi at −0.42).

## Software and infrastructure

The budget holds only if archetypes are shared across states and the daily opinion update is a plain batched call, with OASIS reserved for an optional weekly social-diffusion round. Everything else in the stack is free.

**LLM cost per month** (one call per agent per day; 1,500-token cached news digest, 800-token persona, 200-token output; prices as of 27 Sep, several models released this month, so re-check)

| Scenario | Calls/month | DeepSeek V4.1 Flash | GLM-5.3 Flash (discounted provider) | MiMo-V2.6-Flash | GPT-6 Luna (batch) |
| --- | --- | --- | --- | --- | --- |
| Pilot: 3 states × 1,000 agents | 90K | $8 | $8 | $16 | $9 |
| 1,000 archetypes × 12 state clusters | 360K | $32 | $31 | $62 | $35 |
| 35 states × 1,000 agents | 1.05M | $92 | $91 | $181 | $102 |

**Model policy:** no Gemini or Claude models; the only American model we may use is GPT-6 Luna. Default to Chinese open models (DeepSeek, GLM, MiMo Flash tiers) and to Jev or Kev wherever a decision model can do the job. Output tokens dominate the cost, so short structured outputs matter more than the input price. Sources: [DeepSeek V4.1 Flash](https://openrouter.ai/deepseek/deepseek-v4.1-flash), [GLM-5.3 Flash](https://openrouter.ai/z-ai/glm-5.3-flash) ($0.04 in / $0.50 out list; \~$0.045 / $0.14 on inference.net), [MiMo-V2.6-Flash](https://openrouter.ai/xiaomi/mimo-v2.6-flash) ($0.14 / $0.28), [GPT-6 Luna](https://openrouter.ai/openai/gpt-6-luna). Keep reasoning off: reasoning tokens bill as output and multiply cost 5–10×.

**Model choice matters more than price.** On [SimBench](https://arxiv.org/abs/2510.17516) the best model scores only 40.8/100 at simulating people, ten models score below random, and fidelity tracks general knowledge (r = 0.94). Small open 7–8B models are for development only. Before choosing, run our own 200-question fidelity test on CES/ANES items for 3 candidate models.

**Free requests where they help:** OpenRouter free models (1,000 requests/day after a one-off $10 top-up) for development, prompt tests and the fidelity test; Groq and Cerebras free tiers for open models; Kaggle (\~30 GPU-hours/week) and Modal ($30/month free, academic grants up to $10K) for running Kev or other open weights ourselves; [OpenAI Researcher Access](https://help.openai.com/en/articles/10139500-researcher-access-program-faq) (up to $1,000, faculty sponsor needed) if we lean on GPT-6 Luna.

**Recommended stack**

| Layer | Pick | Why |
| --- | --- | --- |
| Decision questions | Jev, with Kev as the open fallback | Probabilities with no text generation; output free |
| Production LLM | DeepSeek V4.1 Flash or GLM-5.3 Flash (pinned provider); GPT-6 Luna batch as the one US option | Cheapest with caching; mix families to cancel biases |
| Embeddings | qwen3-embedding-8b or pplx-embed | News dedup, relevance, semantic-similarity rating |
| Structured output | instructor + Pydantic | Validated JSON |
| Agent loop | Plain async Python; OASIS for weekly diffusion only | Batch-compatible and replayable |
| Data store | Parquet + DuckDB | Free, versionable, SQL |
| LLM cache | SHA-256 of model, provider, parameters and prompt → stored response | Hosted models aren't deterministic; the cache is the record |
| Filter and Monte Carlo | numpy, particles, dynamax | Already chosen |
| Scoring | scoringrules | properscoring was archived this month |
| Orchestration | GitHub Actions cron (unlimited free minutes on a public repo, 2,000/month private) | Free |
| Tracking | MLflow (local) | Every run's config and prompt hash |
| Archiving | Signed git tag + OpenTimestamps + OSF pre-registration | Independent proof of when each forecast was made |
| Charts | Plotly or matplotlib → 1080×1350 PNG from the same data as the site | One source for web and Instagram |
| Hosting | Cloudflare Pages or GitHub Pages subdomain | Vercel Hobby forbids commercial use; a studio domain may count |

**OASIS in practice:** camel-oasis 0.2.5, Apache-2.0, needs Python 3.10–3.11 and a model that supports tool calling; about 3,356 input tokens per agent per step; live async calls, so batch discounts don't apply; SQLite only; open recommender bugs. Measure opinions with its INTERVIEW action, and never add INTERVIEW to agents' available actions.

## Decision models and model routing

Jev is what we hoped: it generates no text and returns typed answers with a probability for every option, at $0.042 per million input tokens with free output. It is ideal for classifying news and a strong candidate for agent reactions, but only after a test, because its probabilities mean "how sure I am of the right label", not "how a population would split".

**The decision models**

| Model | What it is | Price | Notes |
| --- | --- | --- | --- |
| [Jev 1.13](https://openrouter.ai/typesafe/jev-1.13) (TypeSafe) | Proprietary "System One" decision model: Choice (up to 255 options), Score (up to 10 levels), Noul (yes/no) | $0.042/M in, output free | Launched 15 Sep 2026; one host; \~0.2–0.4s; order of options shifts answers; no public benchmarks ([guide](https://openrouter.ai/docs/guides/community/jev)) |
| [Kev 4B](https://openrouter.ai/jaredpalmer/kev-4b) (Jared Palmer) | Open-weights Jev alternative on Qwen3.5-4B, Apache-2.0 | $0.042/M in, output free | Calibration error \~0.09; 8K context; fine-tunable on our own data ([repo](https://github.com/jaredpalmer/kev)) |
| [Span-01](https://openrouter.ai/respan/span-01) (Respan) | Scores whether defined behaviours are present in text | $0.02/M; Lite free | Built for evaluation, less suited to events |

Both use OpenRouter's Decisions API (`POST /api/alpha/decisions` with a state and typed questions), not the chat endpoint, so they plug into our existing OpenRouter key.

**Which model for which job**

| Job | Model | Est. $/month |
| --- | --- | --- |
| Deduplicate and cluster \~2,000 articles/day | Embeddings (qwen3-embedding-8b, $0.01/M) | \~$0.4 |
| Which races a story affects | Embedding shortlist, then Jev yes/no on the top 5 | <$0.2 |
| Event type, salience, partisan direction | Jev Choice + Score in one request | <$0.3 |
| Archetype reaction and turnout | Jev (options shuffled, averaged over 3 orders) **or** DeepSeek Flash with cached digest returning a distribution | $5–27 |
| Daily post draft | GPT-6 Luna, one call | \~$0.1 |
| Weekly auditor diagnosis | Stronger LLM, gated by Jev | $0.5–2 |

Total routed design: **\~$7–30/month, most likely \~$15**, against $32–35 for an all-LLM design. The saving comes mostly from routing and short inputs; on the reaction job a well-cached DeepSeek Flash costs about the same as Jev. What Jev adds is no parsing, native probabilities, speed and stable repeat answers.

**Test before trusting it for reactions (\~$1–3, 2–3 days)**

1. **Fidelity:** 200 demographic cells × 15 CES/ANES items (vote, approval, turnout). Compare Jev, Kev, DeepSeek asked to describe a distribution, semantic-similarity rating, and a plain regression baseline.
2. **Reaction size:** \~15 past events with measured subgroup shifts; check direction, size, a null test (sports and weather news should mean "no change") and a mirror test (swap party labels, the shift should flip).
3. **Mapping:** fit a calibration curve from Jev's outputs to real shift and turnout percentages, and let the filter absorb the rest.

**Risks:** Jev is 12 days old with a single host and no long-term support promise, so pin `jev-1.13`, cache every response and keep Kev as an open fallback we control. TypeSafe says it doesn't train on prompts. A top Jev user on OpenRouter is an app called "mirasim", so others may already be trying simulation with it.

**The frontier angle:** Kev is open, so we could fine-tune it on CES and ANES to predict real subgroup distributions. A cheap, calibrated, election-specific decision model would be a genuine contribution, best done after November.

## Data

Everything we need is free, and two recent releases make the House layer feasible: 2024 presidential results for every redrawn district, and block files for the new maps. Two old workhorses are gone: 538's poll URLs now redirect to ABC News, and Google Trends' pytrends library is dead.

**Core live sources:** Wikipedia poll tables (MediaWiki API), [VoteHub API](https://votehub.com/polls/api/) (generic ballot, approval), pollster releases, CES, ANES, AP VoteCast, MIT Election Lab, FEC, GDELT, Media Cloud, Kalshi, Polymarket, PredictIt, BLS/FRED/EIA, plus the NC and Ohio voter files. The full list with access terms is in the plan doc's Free data stack.

**Backtest kit** (always filtered to data timestamped before each simulated date)

| Need | Source | Notes |
| --- | --- | --- |
| Benchmark forecasts | [538 checking-our-work-data](https://github.com/fivethirtyeight/checking-our-work-data) | Daily 2018 and 2022 House and Senate probabilities with outcomes, CC BY |
| Historical polls | 538 `*_historical.csv` via [Wayback](http://web.archive.org/web/20250306062822/https://projects.fivethirtyeight.com/polls/data/senate_polls_historical.csv); [raw\_polls.csv](https://github.com/fivethirtyeight/data/tree/master/pollster-ratings) | Download now; the live links are dead |
| Ratings as of any date | Wikipedia revision history | MediaWiki `prop=revisions` |
| Specials | [Downballot Big Boards](https://www.the-downballot.com/p/data), 2017–18 to 2025–26 | Cite and link; don't republish whole sheets |
| Market history | Polymarket and Kalshi candlestick endpoints | PredictIt only via Wayback |
| News history | GDELT (from 2015), GDELT TV, Guardian and NYT APIs | Free keys |

**House 40-seat kit**

| Need | Source |
| --- | --- |
| 2024 presidential vote on new lines | [The Downballot](https://www.the-downballot.com/p/the-downballot-releases-presidential), all 145 redrawn districts |
| Demographics on new lines | [Redistricting Data Hub](https://redistrictingdatahub.org/data/whats-new/) block files (16 Sep 2026) joined to ACS block groups |
| Partisan lean check | [Cook 2026 PVI](https://www.cookpolitical.com/cook-pvi/2026-partisan-voting-index/district-map-and-list) (view only, quote with credit) |
| Candidates and experience | Wikipedia, Ballotpedia (GFDL), FEC |
| Candidate ideology | [Stanford DIME](https://data.stanford.edu/dime) CFscores, Voteview |
| Ads | [Google political ads in BigQuery](https://cloud.google.com/blog/topics/developers-practitioners/how-get-started-political-ads-transparency-report-dataset) (free); Meta Ad Library API (ID verification takes days, start now) |

**Turnout signals now live:** North Carolina publishes record-level absentee and early-vote files daily ([NCSBE](https://www.ncsbe.gov/results-data/absentee-and-provisional-data)), with party, race, age and district; Texas publishes daily early-vote totals by county; the [UF Election Lab](https://election.lab.ufl.edu/early-vote/2026-early-voting/) aggregates states (non-commercial, no derivatives licence).

**Social signals:** Bluesky's Jetstream firehose is free and the best option; YouTube API is free; Reddit needs approval since June 2026; X has no free tier; TikTok's research API needs a US faculty sponsor.

**Legal and licence limits**

| Source | Allowed | Not allowed |
| --- | --- | --- |
| Wikipedia | Reuse with attribution under CC BY-SA | Presenting copied tables as all-rights-reserved |
| RealClearPolling | Reading as a reference | Scraping, caching or republishing |
| Cook PVI, AdImpact | Quoting single values with credit | Redistributing lists or screenshots |
| NC, Ohio voter files | Research and aggregate publication | Publishing any individual voter's details |
| Texas voter file | Research with a notarised affidavit (\~$1.5k) | Commercial use (a misdemeanour) |
| X, Reddit | Following their terms | Scraping X; training models on Reddit data |

## Evaluation and backtesting

The 75 races are not 75 independent tests: one national polling miss moves a dozen close races together, so 2026 is effectively one draw of the national environment plus regional and race noise. We should pre-register modest, specific claims and lean on the comparisons that can be read cleanly.

**Protocol**

1. **Fixed scoring dates:** every week on a fixed day and hour (US Eastern), plus T−1 on 2 November, averaged over the campaign, not just the final call.
2. **Metrics:** Brier score on win probability (headline), log loss capped at \[0.01, 0.99\], CRPS on the full margin distribution. Report competitive races separately; safe seats flatter everyone.
3. **Baselines, snapshotted at the same hour:** poll average converted to probability by a pre-declared rule; market mid-price; expert ratings mapped to probabilities (Solid 97%, Likely 85%, Lean 70%, Toss-up 50%); public models; and our own **stats-only engine with agents switched off**. That last one is the real test of whether simulation adds value.
4. **"Catch what polls miss" rule:** before each scoring date, publish divergence calls (our margin differs from the poll average by ≥3 points or our probability by ≥15). Score hit rate and Brier gain on those races only. Divergences found afterwards don't count.
5. **Significance:** block bootstrap by state and region; report a "national swing removed" score that separates getting the environment right from getting the relative races right. Say "not distinguishable" when the interval crosses zero.
6. **Calibration with few events:** 3–5 wide bins with bootstrap bands, plus predicted-versus-actual margin plots.
7. **Markets:** also report a betting-style test (would our probabilities have profited against the market?), but never claim to have beaten markets from one cycle.
8. **Code freeze** around 13 October; every later change goes in a public changelog, with old and new versions both kept running and scored.

**Backtesting honestly:** any 2018–2024 backtest is contaminated because the model knows the results ([Paleka et al., ICLR 2026](https://arxiv.org/abs/2506.00723)); label it that way. Clean tests: contests after each model's cutoff, frozen offline news snapshots ([Bench to the Future](https://arxiv.org/abs/2506.21558)), canary questions about post-cutoff events to measure leakage, and 3 November itself.

## Publishing, ethics and disclosure

Free, unpaid forecasting appears permissible for a non-US national; paid political ads and any coordination with campaigns are the lines not to cross. The bigger risk is reputational: being lumped in with "AI polls". These are research notes, not legal advice.

**The standards landscape**

- [AAPOR, May 2026](https://aapor.org/wp-content/uploads/2026/05/Responsible-AI-Integration-In-Survey-Research.pdf): AI output is "a model-based approximation", not an observation; words like "poll" and "survey" imply human respondents.
- Axios cited Aaru "findings" in March 2026 without saying the respondents were AI, then had to add an editor's note.
- [Silver Bulletin](https://www.natesilver.net/p/ai-polls-are-fake-polls): "silicon sampling produces no new data"; [FiftyPlusOne](https://blog.fiftyplusone.news/p/why-501-isnt-collecting-synthetic) refuses to aggregate synthetic results.

| Do | Don't |
| --- | --- |
| Call it a "simulation-based forecast" and put "AI-simulated voters, not a poll" inside every graphic | Use "poll", "survey", "voters say" or "% of voters" for agent outputs |
| Publish a methods page: sources, how many real poll respondents sit behind the inputs, models and versions, what agents change, a changelog | Let agent "opinion" breakdowns circulate as public-opinion findings |
| Keep a public scoring page from day one and publish every race | Delete or quietly revise past forecasts |
| Post organically on Instagram and X | Boost posts about US elections on Meta (that is political advertising, needs US authorisation) |
| Stay unpaid, independent and non-partisan | Take money from, coordinate with, or run ads for campaigns, parties or PACs |
| Have a named human review every published text (EU AI Act Article 50, in force since 2 Aug 2026) | Auto-publish LLM commentary unreviewed |
| Use charts and text | Make realistic AI images or video of real candidates (state deepfake laws) |

**Communication rules**

- Lead with margin ranges and "wins 7 in 10 simulations", not bare percentages; win probabilities make races feel more certain than they are ([Westwood, Messing & Lelkes](https://www.asc.upenn.edu/news-events/news/probabilistic-forecasting-can-mislead-voters-about-certainty-election-outcomes)).
- Call anything between 35% and 65% a toss-up.
- Show us beside the poll average, the market and Cook every time; disagreement is the content.
- Daily posts show the 7-day change and say "no meaningful change" when true, so followers don't read noise.
- Build in public the way Split Ticket grew: publish your own misses and reasoned contrarian calls.

**Before monetising, sponsoring or running any ads:** check with a US election lawyer (the press exemption for foreign-owned outlets is a grey area) and any visa terms that apply to you.

## Do and don't

These are the build rules, distilled from every section above.

| Area | Do | Don't |
| --- | --- | --- |
| Levels | Set starting levels with a FLIPR/538-style statistical baseline on the new maps | Let agents invent vote levels |
| Agents | Seed with structured survey fields (party ID, attitudes, vote history) | Generate rich LLM backstories (they drift left) |
| Agents | Damp persuasion hard; let turnout and enthusiasm move | Over-damp turnout (the Hungary miss) |
| Agents | Decay shocks at rates learned per event type and state; demand corroboration for big shifts | Hard-cap shifts, or accept a large uncorroborated shift from one day's news |
| Agents | Route each job to the cheapest specialised model (Jev or Kev, embeddings, small LLMs), mix families with opposite biases, and pick by our own fidelity test | Assume the newest or biggest model is best |
| Agents | Refresh agent memory weekly | Let personas go stale |
| Network | Add confirmation bias and homophily if agents interact | Let the network converge to consensus |
| Filter | Ensemble Kalman on a factor state; particle filter only for agent parameters, estimated per state and region | Run a particle filter over 100+ dimensions |
| Filter | Keep a permanent poll-bias term and inflation | Let the engine collapse into a poll average |
| Filter | Treat markets as a benchmark | Assimilate the markets we want to beat |
| Polls | House effects, partisan polls at half weight, likely-voter caps | Read raw poll swings as persuasion |
| Uncertainty | Correlated national, regional and state errors, fat tails, correlation floor | Treat races as independent or allow negative correlations |
| Backtests | Use post-cutoff contests and frozen news; label the rest contaminated | Trust any 2018–2024 backtest at face value |
| Process | Freeze code \~13 October, public changelog, timestamp every forecast | Tweak the model near election day or revise history |
| Evaluation | Pre-register metrics, baselines and divergence calls | Cherry-pick races or metrics afterwards |
| Cost | Share archetypes across \~12 state clusters, batch, cache, reasoning off | Run 1,000 agents per state daily |
| Publishing | "Simulation-based forecast", caveat inside every image | Say "poll", boost posts, or coordinate with campaigns |
| Data | Attribute Wikipedia (CC BY-SA), cite The Downballot, publish aggregates only | Scrape RealClearPolling or X, publish individual voter data |

## Possibilities to explore

Prioritised after our 27 September review. "Core" items prove what simulation adds; "Background" items run quietly to show where value is or what we're missing; "Later" items wait for pilot data.

| # | Possibility | Why it matters | Priority |
| --- | --- | --- | --- |
| 1 | **Stats-only vs stats + agents, scored side by side** | The cleanest proof of what simulation adds | Core |
| 2 | **Model routing with Jev and Kev** for most jobs, GLM, MiMo, DeepSeek and GPT-6 Luna where text is needed | Lowest cost at the highest performance, if the fidelity test confirms it | Core |
| 3 | **Learned news-sensitivity in the filter**, per state | Fixes model overreaction; unpublished | Core |
| 4 | **Turnout-first agents fed by live early-vote files** (NC, Texas, Ohio): input, benchmark, and trigger to recalibrate pre-October assumptions | Turnout decides midterms and was our Hungary miss | Core |
| 5 | **Divergence calls** closer to election day | Makes "catch what polls miss" scorable | Core |
| 6 | Weekly check of the simulation against real data trends | Shows whether data should adjust the simulation or only validate it | Core |
| 7 | Weekly OASIS diffusion arm vs static personas | Tests whether social simulation adds value | Core |
| 8 | Plain LLM-forecaster baseline ([Metaculus forecasting-tools](https://github.com/Metaculus/forecasting-tools)) | Cheap check that simulation beats "model + news" | Background |
| 9 | Replay screening on post-cutoff contests | Tests candidate settings against contests the models can't know | Background |
| 10 | Bluesky Jetstream sentiment and salience feed | Free real-time signal | Background |
| 11 | Blind track, run after the election on frozen data snapshots | Poll-free comparison without the running cost | Later (after 3 Nov) |
| 12 | Emulator of the agent layer ([AutoEmulate](https://github.com/alan-turing-institute/autoemulate)) | Could cut calibration calls \~100× | Later (decide after pilot) |
| 13 | **Fine-tune Kev** (open weights) on CES and ANES | A cheap, calibrated, election-specific decision model | Later (after November) |
| 14 | Metaculus FutureEval bot tournament | External scoring | Low, only if it opens a real opportunity |
| — | Academic write-up with an LSE collaborator | — | Dropped |

## Review outcomes and open tasks

**Answered on 27 September**

- **Scale under budget:** whatever reaches the lowest cost at the highest performance; decide after testing Jev and Kev against the LLM options.
- **Timeline:** run the pilot first, then set pre-registration and freeze dates.
- **Backtests:** judged state by state and model by model, based on each model's training cutoff.
- **Early vote:** used as an input, a benchmark, and a trigger to recalibrate pre-October assumptions in NC, Texas and Ohio.
- **Blind track:** not run in parallel. Freeze daily data snapshots now and run it after the election. Pin model versions with training cutoffs before 3 November so the blind run can't know the result.
- **Model families:** Jev and Kev first; GLM, MiMo and GPT-6 Luna as favourites; DeepSeek as an option.
- **Credits:** no faculty sponsor available.
- **Hosting:** Cloudflare Pages, linked from the Scalia site.

**Open tasks**

- [ ] Explain OSF pre-registration and timestamped git tags, then decide.
- [ ] Explain replay screening in more detail.
- [ ] After the pilot: explain the emulator (AutoEmulate) and decide whether to add it.
- [ ] Decide whether contacting Philipp Schoenegger (LSE) is worth it.
- [ ] Review the evaluation and backtesting protocol before pre-registration.
- [ ] Review publishing, ethics and disclosure before the first public post.

## Sources

Sources are linked inline in each section. Key references by area:

- **Projects:** [Fudan ABM](https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0270194) · [Aaru post-mortem](https://www.semafor.com/article/11/06/2024/ai-startup-aaru-defends-using-artificial-intelligence-for-polling) · [BYU 2024](https://arxiv.org/html/2411.03486v1) · [Persona drift](https://arxiv.org/abs/2503.16527) · [Dynamo-K](https://arxiv.org/html/2605.18395v1) · [Focaldata Hungary](https://www.focaldata.com/blog/how-we-forecasted-the-hungarian-election) · [FluSight review](https://www.medrxiv.org/content/10.64898/2026.06.05.26354941v1)
- **Voter change:** [Kalla & Broockman](https://escholarship.org/uc/item/103775sx) · [Coppock, Hill & Vavreck](https://alexandercoppock.com/coppock_hill_vavreck_2020.pdf) · [Le Pennec & Pons](https://www.nber.org/papers/w26572) · [Gelman et al., phantom swings](https://sites.stat.columbia.edu/gelman/research/published/swingers.pdf) · [Pew 2022 turnout](https://www.pewresearch.org/politics/2023/07/12/republican-gains-in-2022-midterms-driven-mostly-by-turnout-advantage/) · [Ashokkumar et al.](https://www.nature.com/articles/s41586-026-10742-x)
- **Statistics:** [FLIPR](https://www.natesilver.net/p/flipr-midterms-model-methodology) · [FiftyPlusOne](https://blog.fiftyplusone.news/p/2026-forecast-methodology) · [Linzer](https://votamatic.org/wp-content/uploads/2013/07/Linzer-JASA13.pdf) · [Economist code](https://github.com/TheEconomist/us-potus-model) · [Shirani-Mehr et al.](https://sites.stat.columbia.edu/gelman/research/published/polling-errors.pdf)
- **Infrastructure:** [SimBench](https://arxiv.org/abs/2510.17516) · [OASIS](https://github.com/camel-ai/oasis) · [OpenRouter limits](https://openrouter.ai/docs/api-reference/limits)
- **Data:** [538 checking-our-work](https://github.com/fivethirtyeight/checking-our-work-data) · [Downballot new-district results](https://www.the-downballot.com/p/the-downballot-releases-presidential) · [Redistricting Data Hub](https://redistrictingdatahub.org/data/whats-new/) · [NCSBE absentee](https://www.ncsbe.gov/results-data/absentee-and-provisional-data)
- **Evaluation and publishing:** [Paleka et al.](https://arxiv.org/abs/2506.00723) · [Gelman et al., forecasting review](https://sites.stat.columbia.edu/gelman/research/published/2024_Election_Forecasting_Review.pdf) · [AAPOR AI guidance](https://aapor.org/wp-content/uploads/2026/05/Responsible-AI-Integration-In-Survey-Research.pdf) · [FEC foreign nationals](https://www.fec.gov/updates/foreign-nationals)

Several figures are marked as judgement or unverified in the text; model prices change weekly and should be re-checked before committing.
