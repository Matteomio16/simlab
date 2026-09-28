# Content plan (draft for Matteo to choose from)

Content & site session, 28 Sep 2026. Built on `docs/research/`, the Field Guide's publishing rules, infrastructure §8
and the test bench. Nothing here is decided until Matteo picks.

**The pitch in one line:** the honest AI forecast. Every number sits beside the poll average, the market and Cook; every
miss gets published; the making-of is shown as it happens.

## 1. Your decisions (by Wed 30 Sep)

1. **Name and handles**
   - **Model Citizens** (my pick): a pun on AI models, so the name itself says "simulated". It reads well when quoted
     ("the Model Citizens forecast shows...").
   - **Sim Desk**: sounds like a news desk (Decision Desk HQ); serious, less memorable.
   - **Midterm Sim**: plain and searchable, but tied to this one election.
   - **Not A Poll**: the disclaimer is the name; memorable, but can read as anti-poll.
   - Keep "Scalia" out of the name: to US readers it means Justice Antonin Scalia, a conservative icon, which undercuts a
     neutral forecast. "By Scalia Studio" goes in the bio and on the site.
   - Handles: one handle everywhere, at most 15 characters (X's limit). I'll check which are free once you shortlist.
     Bluesky can use `@midterms.scaliastudio.dev` (one DNS record), which also verifies the account.
2. **On camera or voice-over**
   - **Mix** (my pick): on camera twice (launch on 12 Oct, results on 4 Nov), your voice over the weekly Reels.
   - Voice-over only: about 10 minutes per Reel; your face stays private.
   - On camera: the most trusted style in the research (the Integrity Index founder, Harry Enten); 30–45 minutes per
     video; your face becomes the brand and draws the abuse political accounts get.
   - Neither: captions and music only; least work, weakest Reels.
   - In every case: no AI presenters or AI voices.
3. **TikTok or YouTube Shorts**
   - **TikTok only** (my pick, unless you choose "neither" above): the same videos, posted by hand, about 5 minutes
     each, 2–3 a week. TikTok is the friendliest platform to new accounts. Before 12 Oct I'd check its current rules on
     unpaid political posts by non-US creators (the research found nothing either way).
   - Both: Shorts adds 5 minutes a video and grows new channels slowly.
   - Neither: Instagram, X, Threads and Bluesky only.
4. **LinkedIn (my addition):** the Lab notes from your own profile, weekly, by hand. That's where the AI, startup and VC
   audience is.
5. **Formats:** tick from the menu below. My pick: A to F; G if there's time.

## 2. Format menu

Videos bring new people (B, C), carousels keep them (A, D), Lab notes earn trust (E), and real early-vote data gives
news hooks (F).

| | Format | What it is | Inspired by | How we make it | Build / your time | Cadence | Where |
|---|---|---|---|---|---|---|---|
| A | **Daily forecast** | 4–6 slides: Senate and House control, the races that moved (or "no meaningful change"), a race of the day, each beside the poll average, market and Cook | Silver Bulletin's daily update; Enten's one number per clip; Cook's ratings | Chart factory reads the forecast file → JPEG 1080×1350; caption, alt text and X post from templates; I polish, you approve | 3 days (by 4 Oct) / 15 min a day | Daily from 12 Oct (internal kits from 5 Oct) | IG carousel; X, Threads, Bluesky (4 images) |
| B | **Every future** | 15–20 s video: 100 dots fall, one per simulated election, until the count reads "wins 7 in 10" | 538's and 50+1's one-dot-per-simulation charts | matplotlib animation → MP4 1080×1920 from the simulated elections; music added in the app when posting by hand | 1 day / 2 min (10 if voiced) | Sundays (Senate control) and after big moves | IG Reel; X video; TikTok, Shorts if added |
| C | **Why it moved** | The week's biggest move, traced: the news event → which simulated groups changed turnout or support → how much the engine kept → the new number, and the gap to statistics alone | Kornacki's big board; AI Village's weekly recaps | From the daily run log; I draft, you approve | 1 day / 20 min a week | Wednesdays from 14 Oct | IG Reel or carousel; X thread; Bluesky |
| D | **The receipts** | Every close race on one chart: ours, poll average, market, Cook, locked and timestamped; this week's divergence calls; scored after 3 Nov | The Field Guide ("disagreement is the content"); Split Ticket's contrarian calls; Aaru's lesson (commit before the result) | Chart from the forecast file and benchmark snapshots; the same numbers feed the site's scoring page | ½ day / 10 min a week | Mondays from 12 Oct | IG carousel; X thread; Bluesky; site |
| E | **Lab notes** | One finding, one chart: what we tested, what we found, what we changed | Epoch AI's one-chart posts; AI Village and Claude Plays Pokémon (the struggle is the story) | Test-bench numbers; I draft, you approve | none / 20 min a post | Daily 3–11 Oct, then Fridays | IG carousel; X thread; Bluesky; Threads |
| F | **Early-vote watch** | Real ballots, not AI: NC and TX early votes against 2022 by party and age, and where turnout runs ahead of the simulation | VoteHub and Election Twitter's trackers | Bars from the early-vote files the engine downloads | ½ day / 5 min a post | Tuesdays and Saturdays from 15 Oct | X, Bluesky, Threads; a slide in the IG daily post |
| G | **Ask the lab** | Three follower questions about the method, answered | Cook's live Q&As; Threads rewards replies | You pick the questions, I draft | none / 20 min a week | Thursdays | IG Stories; Threads |

Every format: "AI-simulated voters, not a poll" inside the image and in the caption; any forecast number sits beside the
poll average, market and Cook; ranges and "wins X in 10 simulations" before percentages; 35–65% called a toss-up; a
source line on every chart (the Integrity Index habit, without its donation asks); you approve every post.

## 3. Making-of series: Lab notes, 3–11 Oct

Test-bench findings first. Drafts reach you two days ahead, starting Thu 1 Oct.

| # | Date | Hook | The finding | What we changed |
|---|---|---|---|---|
| 1 | Sat 3 | We tested six AIs as voters before forecasting anything | Four checks for about $1.50 of model calls. Why test first: in April my Hungary simulation called the winner but missed its vote share by 16 points | Each model got one job |
| 2 | Sun 4 | Same headline, Fox News or MSNBC: the AI changed its answer | Crediting a headline to MSNBC instead of Fox moved one model's "helps Democrats" by 30 points; its top answer flipped on 41% of stories | Outlet names removed before any model reads the news |
| 3 | Mon 5 | Ask it backwards and the AI's lean disappears | Asked one way, a model's reactions leaned Republican by 44% of their size; asked both ways, by 2% | Every question asked both ways |
| 4 | Tue 6 | AI knows which way voters move, not how far | Right direction on 92% of real events that moved opinion; the predicted sizes barely track the real ones | Sizes come from real past shifts, re-tuned weekly for each state |
| 5 | Wed 7 | Six AIs, one blind spot | All under-react to big shocks (COVID, Jan 6, Afghanistan) and over-react to media spectacles (debates, Access Hollywood). Their errors move together, so averaging two AIs doesn't help | We trained our own model on measured shifts |
| 6 | Thu 8 | Plain statistics beat every AI | Matching how groups voted and what they thought in 2024, a simple statistical model beat the AIs on average on every question (the AIs won a few spots, like the Texas vote) | Statistics set the starting levels; the AI only simulates change |
| 7 | Fri 9 | Ask an AI how someone voted and it assumes they voted | Asking both in one prompt pushed turnout answers up 51 points in one test. And the survey's turnout data turned out to measure voter-file matching | Turnout asked on its own; turnout data from the Census |
| 8 | Sat 10 | We trained our own AI voter for $2.30 | 23 minutes on one GPU. It learned the rules perfectly: irrelevant news changed nothing, and swapping the parties flipped its reaction every time, the best of any model. But 11 real events couldn't teach it how much news matters | It stays out of the reactions for now; the two hosted models keep the job |
| 9 | Sun 11 | How to read our forecast, live tomorrow | "Wins X in 10", the toss-up band, us beside polls, market and Cook, timestamps, misses published | An example chart, stamped EXAMPLE |

Spares for Fridays after launch: our first correction (a fix that turned out to be overfitting); AI flattens party
differences (Democrats approving of Biden: 83% real, 44% AI); our own model on 2024 group voting (beat plain statistics
in NC and TX on states it had never seen, not on turnout); what the engine costs (about $5 a month in the pilot); why
markets are a benchmark and never an input; how every forecast gets timestamped.

## 4. Calendar, 3 Oct – 4 Nov

Posts go out at 07:00–09:00 US Eastern: 12:00–14:00 UK, except 11:00–13:00 from 25 to 31 Oct (the UK changes clocks a
week before the US).

| Dates | Public | Behind the scenes | Fixed dates |
|---|---|---|---|
| Wed 30 Sep – Fri 2 Oct | — | You pick; Lab notes 1–3 drafts on Thu 1; you create the accounts on Fri 2 | |
| Sat 3 – Sun 4 Oct | Lab notes 1–2 | Chart factory and daily kit ready (Sun 4) | |
| Mon 5 – Sun 11 Oct (private pilot) | Lab notes 3–9, one a day | Daily kits for OH, NC, TX stay internal; site ready Fri 9; ethics review Sat 10; go or no-go Sun 11 | Ohio early voting from about 6 Oct |
| Mon 12 – Sun 18 Oct (launch) | Mon 12: launch post, Senate Reel (on camera if chosen), first receipts. Then the weekly rhythm | Posting automation behind the approval flag | Code freeze 12 Oct; NC early voting 15 Oct (Early-vote watch starts) |
| Mon 19 – Sun 25 Oct | Weekly rhythm | | Texas early voting from about 19 Oct; UK clocks change 25 Oct |
| Mon 26 Oct – Sun 1 Nov | Weekly rhythm; Sat 31: every path to Senate control | | US clocks change 1 Nov |
| Mon 2 Nov | Final forecast, locked and timestamped | | Last scoring date |
| Tue 3 Nov | Morning: what to watch tonight, with poll-closing times in ET and UK; the site's live page; night posts only if you're up to approve them | | First polls close 23:00 UK |
| Wed 4 Nov | How we did, first look: every called race, misses first (on camera if chosen) | | |

Weekly rhythm from 12 Oct: the daily forecast every day, plus Mon receipts, Tue and Sat early-vote watch, Wed why it
moved, Thu ask the lab, Fri lab notes, Sun every future. About 25 minutes a day of your time.

## 5. Tone and distribution

- Calm and specific, like a lab notebook: numbers first, no hype, no emojis, the same wording for both parties, misses as
  prominent as hits. Never tag candidates or campaigns.
- X: the chart or video goes in the post and the link in the first reply (X shows posts with links to fewer people).
- Instagram: Reels for reach, carousels for saves. Pin Lab notes 1, Lab notes 9 and the launch post.
- Bluesky: ask to join the election-data starter packs ("Polls and Elections", "2026 Elections").
- Threads: answer replies; it rewards conversation.
