# Cowork session log — 27 September 2026 (Sim Research project)

> Reconstructed record of the Claude Cowork conversation that started this project, written for Claude Code.
> It is not a verbatim transcript: each turn gives what Matteo said (paraphrased closely; he dictates by voice, so
> transcription slips like "Myrofish" = MiroFish, "Jev/Java/Jeff" = Jev, "Kev" = Kev are normalised) and what was
> done or decided. Where this log and CLAUDE.md disagree, CLAUDE.md wins (it holds the final decisions).
> Deliverables referenced: `docs/plan.md` (research map), `docs/field-guide.md` (expert review), `CLAUDE.md`.

---

## Turn 1 — The brief

**Matteo:** Read the Sim Research folder, his site scaliastudio.dev, his memory and Goldfish. He used MiroFish a few
times and ran a simulation of Hungary's April 2026 election (from data a week before, simulating how it converts to
the result); the answer was close "only once we recalibrated how many voters of one party went to another" (the λ
strategic-transfer parameter). Now he wants to do research in AI **simulation engines for political prediction** —
AI that *simulates* rather than polls — and build a broader engine to predict the **US midterms** (Senate and
House). Not tied to MiroFish. Ideally little or no polling, but polls are allowed. His sketch: focus on one state
first to find bottlenecks, then expand; the model predicts a likelihood of a candidate winning (not just poll
averages); every day it scrapes and reads the news and many factors (not only local), runs a simulation, and updates
the likelihood; once a week, on a fixed day, it compares with polling averages, and if they diverge (e.g. polls
50→54% but model down) it flags the inconsistency, works out why and improves itself. Open to any other approach
(any AI, not just LLMs: social sim, data sim, analysis). Two goals: (1) a simulation engine for political prediction
that actually works; (2) a model that successfully predicts the midterms and most races. Wants deep research on
methods, what exists, and **where the frontier is**, because institutions still mostly poll.

**Done:** read the Hungary paper ("The Simulation of Democracy", 45 agents, 100 rounds, Gemini Flash Lite via
OpenRouter, Neo4j, BrainInTheFish, 11 post-hoc bias corrections, Chronicler-v2 seat model, λ=0.58 → TISZA 101 /
Fidesz 84), the MiroFish memory notes, the site, Goldfish. Checked the actual Hungary result: **TISZA 53.2% list vote,
141 seats (two-thirds); Fidesz 38.6%, 52; Mi Hazánk 5.6% in; DK/MKKP out; turnout 79%** — the sim got the winner
but missed the magnitude (TISZA −16.5 pts, −40 seats). Ran 3 research agents (LLM social simulation; forecasting
methods and AI forecasters; 2026 midterm landscape and data). Created the plan doc (now `docs/plan.md`): Hungary
scorecard, landscape of 5 method families, evidence on what works/fails, frontier, a 4-layer engine design
(synthetic electorate → LLM reaction layer → assimilation filter → Monte Carlo), his weekly-check idea reframed as
data assimilation, pilot = Ohio (+NC), data, 37-day plan, evaluation, decisions.

## Turn 2 — First round of decisions + more research + "ask me questions"

**Matteo:** Scope = **35 Senate + ~40 competitive House seats**; non-competitive House seats assumed in the final map
and re-checked regularly. Pilots **Ohio and North Carolina**, and **Texas** too depending on data. Engine: no
MiroFish needed — **Python + OASIS**. Wants a sub-agent to find **other software** that could push the frontier
(whether or not used). Won't pay for FiftyPlusOne; **scrape Wikipedia tables**, use free institutional/organisational
data. Mentioned the **"political integrity index"** org (money in politics) — useful but advocacy-biased, so use
neutrally. **Don't update the Hungary website**; focus on midterms. Then: ask him questions to align the plan with
his vision.

**Done:** 2 agents (software discovery; free data sources). Identified the org as the **Integrity Index**
(integrityindex.us, Political Integrity Project; grades reward signing its own pledge → likely correlates with party →
cross-check only, rebuild raw components from FEC/disclosures). Asked alignment questions. Answers:
- North star: **prove simulation works**.
- Social simulation (agents talking): core **if genuinely useful**; if better simulation/AI-driven methods exist, use
  them — simulation + AI must be the core, not just stats.
- Audience: **Scalia live page, social/press, and an Instagram page building in public** (showing predictions/results).
- Headline: **poll-assimilated simulation**; blind (no-polls) track secondary.
- Success bar: **beat poll averages, catch what polls miss, match/beat markets, beat expert ratings** (all four).
- Budget: **under $50/month**, more only for good reasons. Team: solo first, others if needed.
- (Briefly chose "agents own levels" — **corrected in Turn 3**.) Openness: open method, closed code (later relaxed).
  Cadence: daily everywhere.

Plan doc updated with decisions, a "Free data stack" and "Software worth exploring" section.

## Turn 3 — Correction + "huge check" to become an expert

**Matteo:** Correction — **starting vote levels are set by data and statistics**; the simulation then reads the news
and works out how **voter sentiment changes** (also looking at how things went in the past). Daily posting will be
done manually here with Claude for now, automated later. Code may be open later. Now run a **huge check** of the whole
possible infrastructure — software, data sources, what similar projects did and what to learn, to-dos and not-to-dos,
all possibilities — to become an expert on every field discussed. Review before starting.

**Done:** fixed the plan (levels from stats; agents simulate change). Ran 6 parallel research agents (similar
projects & lessons; science of voter change; baseline/calibration/uncertainty; software & infra & cost; data &
archives & legal; evaluation, publishing ethics & pitfalls). Wrote the **Election Simulation Field Guide** (now
`docs/field-guide.md`). Headline findings: no AI-agent election forecast has a pre-registered scored record (Aaru
2024 wrong, BYU 2024 wrong, EU-2024 study failed); Fudan's rule-based ABM (Taiwan 2020, 6/6 US states) is the template
via replay screening; voters rarely switch (4–8%), turnout decides midterms; LLMs overstate effects (GPT-4 ×0.56;
personas 5–7× overshoot); LLM-written backstories drift left; phantom swings from nonresponse; particle filter over
75 races collapses → EnKF on a factor state + small PF over agent params; don't assimilate markets; 2018–24 backtests
contaminated; budget only works with shared archetypes; never call it a poll.

## Turn 4 — Review of the Field Guide, part 1 (Jev appears)

**Matteo:** Agrees with all points. GPT-4 is far worse than today's cheapest models, so overreaction evidence may be
dated. Wants to use **GPT-6 Luna, GLM**, and especially **Jev** — "skip the text generation part and just run
probabilistic predictions and social simulations", potentially cutting cost to a minimum; also a newer similar
model ("**Kev**"). LLM biases must be corrected; personas unbiased. Point 6 is important: **differentiate filters by
state and parameter**, don't generalise findings across states/regions. Never assimilate markets. Budget is the main
worry. Idea: **route between model types via OpenRouter** — embeddings, classifiers, scoring models, Jev — using the
most fine-tuned model per task instead of a general LLM, to cut cost and raise performance.

**Done:** verified Jev (TypeSafe, `typesafe/jev-1.13`, launched 15 Sep 2026): no text generation; typed Choice /
Score / Noul questions → probabilities; $0.042/M input, output free; OpenRouter Decisions API. Kev
(`jaredpalmer/kev-4b`, 25 Sep 2026): open-weights Apache-2.0 twin on Qwen3.5-4B. Caveat: Jev's probabilities are
confidence in a label, not a population split. Added a "Decision models and model routing" section (job → model →
cost; routed design ~$7–30/month, likely ~$15; test plan: fidelity, reaction size, null, mirror, mapping).

## Turn 5 — Review part 2

**Matteo:** Priors must be **state-specific**, not generic — they can end up defining the result; keep assumptions
minimal and let the news calibrate them; question whether "max 1–2 pts per event" is justified (sometimes it could
be 10) — don't assume unless really unreasonable otherwise. News reactions mostly into **enthusiasm/turnout**; vote
switching mainly for **undecided voters**. Agrees with rules 4–6 (low-partisanship persuasion, ask about exposure,
confirmation bias in networks). Starting levels should use each state's **main issues** mapped to effects on
undecideds, sentiment, turnout and the few switchers. **Model policy: never Gemini, never Claude; the only American
model maybe GPT-6 Luna; mostly Chinese models (MiMo, GLM, Flash tiers); Jev wherever possible.** Principle: simulate
people with models but **fine-tune the system so the model has little freedom** — the system decides how to use the
model's answers. Fidelity test is great; use free model requests when useful. Amazed that public repos get unlimited
GitHub Actions minutes. Fixed scoring dates **weekly**. Evaluation protocol and publishing ethics: look at later.

**Done:** priors table rewritten as weak, per-state starting ranges with an assumption register; no hard caps
(heavy-tailed, big shifts need corroboration); design rule "constrain the model, free the system"; state issue map;
model policy and cost table updated (DeepSeek ~$32, GLM-5.3 Flash ~$31, MiMo-V2.6-Flash ~$62, GPT-6 Luna batch ~$35
per month at 12 state clusters); weekly scoring.

## Turn 6 — Review part 3 (possibilities and questions)

**Matteo:** Fine-tuning Kev (or Jev) is exciting. Bot tournament only if it opens real opportunities. Bluesky feed
interesting. Turnout-first agents with **live early-vote files** great; divergence calls near election day; stats-only
vs stats+agents side by side; learned news-sensitivity in the filter; model routing — yes. Weekly check against real
data trends and whether the blind run does better is an interesting tension. Plain LLM forecaster baseline: low
effort, run in background. Replay screening: didn't understand — fine as a background method. AutoEmulate: decide
after the pilot and explain it better. **No academic write-up with an LSE collaborator.** Review answers: scale →
whatever gives the lowest cost at the highest performance (maybe Jev/Kev); timeline → run the pilot and see;
backtests → state- and model-dependent (training cutoffs); early vote → input, benchmark and trigger to recalibrate
pre-October data (NC, TX, OH); **blind track not in parallel** — freeze data and run it after the election; model
favourites Jev, Kev, GLM, MiMo, GPT-6 Luna; **no research-credit sponsor**; hosting **Cloudflare**, linked from Scalia;
OSF + git tags → explain later (task); Schoenegger outreach → probably not useful, decide later (task).

**Done:** possibilities re-prioritised (Core / Background / Later / Low / Dropped); review outcomes and open tasks
written into the Field Guide. Explained OSF (timestamped, uneditable pre-registration) and replay screening (keep
only settings that reproduce post-cutoff contests) briefly.

## Turn 7 — Build and test Jev/Kev

**Matteo:** Main action now: find out whether we can use Jev/Kev or a similar model and **fine-tune** it. Build a
fine-tuned version, run the tests (survey reproduction, reaction size vs known past shifts, stays at no-change for
irrelevant news, flips when party labels are swapped), improve over the tests until a version works for a task;
repeat for enough tasks to know where Jev can and can't be used. Decide whether we need **separate fine-tunes per
task and per state, a few larger ones, or one fine-tune** for the whole job with routed decisions. Agents can use Jev
or route to LLMs (GLM, MiMo). Build a **context layer** (scraping, news, data, state differences) that all models
read from. Test for a day or two, then run the pilot with the best infrastructure.

**Done / found:**
- **Jev cannot be fine-tuned** (closed weights) → tune the system around it; **fine-tune Kev** (Kev repo has a
  Modal fine-tune skill, ~$1 per Kev-4B run on an H100, supports **soft targets** → train on CES respondents so
  probabilities = population shares).
- Both the Cowork cloud workspace and the device sandbox **blocked** openrouter.ai, huggingface.co,
  dataverse.harvard.edu, wikipedia.org, modal.com (only PyPI/GitHub open). No GPU anywhere.
- Matteo chose: **allow all domains**, **new OpenRouter key capped at $10** in `.env`, **Modal** for GPU, **$10** test
  budget.
- Built the test bench `simlab/` (never run): core (env, cache, $9 cap, Decisions + Chat clients), askers, probes
  (null news, mirror templates, questions), `events.json` (19 real events 2012–2026 with measured shifts from a
  research agent: e.g. Biden→Harris panel +6, Jan 6 −9 approval/−17 among Republicans, Trump conviction ~2 (near
  null), June 2024 debate +3 R, Dobbs +3 D, Afghanistan −6, Liberation Day tariffs ~−3, 2026 fuel spike −4; nulls:
  Mueller summary, Harris–Trump debate, Iran strikes, Maduro capture), tests (fidelity, null, mirror, events),
  CES downloader.
- Network change didn't reach the session.

## Turn 8 — Cowork or Claude Code?

**Matteo:** Should the project be built in Cowork or Claude Code?
**Answer:** hybrid — **build and run the engine in Claude Code** (his machine's network, git, Modal, long runs, test
loops); keep **Cowork** for research, living docs, project memory, and producing daily posts. Link via `CLAUDE.md`
and results in `simlab/runs/`.

## Turn 9 — Handoff

**Matteo:** Give everything needed to pass this to Claude Code in a handoff file.
**Done:** `simlab/CLAUDE.md` (project, immediate task, model policy, four checks, existing code + known gaps, setup,
all decisions, data sources, working agreements, first moves).

## Turn 10 — Access to the Field Guide

**Matteo:** Does Claude Code have access to the Field Guide and its updates?
**Answer/Done:** no (claude.ai doc links aren't readable from Claude Code) → exported `docs/field-guide.md` and
`docs/plan.md` as snapshots; CLAUDE.md points to them; re-export on request after edits; Claude Code logs its own
decisions in CLAUDE.md §5 and `docs/CHANGELOG.md` so Cowork can pick them up.

## Turn 11 — This file

**Matteo:** Export the whole conversation as a markdown file so Claude Code knows what was covered and brainstormed.

---

## Ideas raised but not yet decided or built (brainstorm backlog)

- Instagram page tracking the project, building in public (daily posts; charts 1080×1350; "simulation, not a poll").
- Weekly comparison of simulation vs real data trends: should data *adjust* the simulation or only *validate* it?
  And does the blind track end up doing better? (an explicit research tension to report).
- Bluesky Jetstream as a free sentiment/salience feed.
- Plain LLM-forecaster baseline running quietly in the background.
- Replay screening on post-cutoff contests (2025 VA/NJ governor, 2025–26 specials, 2026 primaries).
- AutoEmulate surrogate of the agent layer (decide after pilot; explain first).
- Fine-tuning Kev on CES/ANES as a genuine contribution (a cheap, calibrated, election-specific decision model).
- Metaculus FutureEval bot tournament (low priority).
- Research credits: none available (no faculty sponsor).
- Open explanations owed to Matteo: OSF + timestamped git tags; replay screening in depth; AutoEmulate (post-pilot);
  whether contacting Philipp Schoenegger (LSE) is worth it.
