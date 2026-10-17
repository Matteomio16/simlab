"""Reading the polls (18:00 Paris, from 5 Oct): one real poll or forecast from the day, what it measures, where it could
be overstating, why it could be right, and one hypothesis we check later. Fair to both sides and to pollsters
(communication.md): alternate which side the featured poll favours, never "polls are wrong".

    python -m simlab.publish.pollread --date 2026-10-05 --polls DIR      # DIR from python -m simlab.polls --out DIR
    python -m simlab.publish.pollread --candidates --polls DIR           # recent polls furthest from their race average

Each day's words are a STORIES entry, written the evening before and approved by Matteo with the rest of the day.
"""
from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

import pandas as pd

from . import text
from .frame import DISCLAIMER, LABEL, MARGIN, SITE, Slide, pt, typeset
from .launch import LIMIT, X_LINK
from .themes import LAB

ROOT = Path(__file__).parents[2]
KITS = ROOT / "kits"
SERIES = "Reading the polls"
ALLOW = ("poll", "polls", "pollster", "pollsters", "survey")
SHORT = {"New York Times/Siena University": "NYT/Siena", "Fabrizio Ward (R)/ Impact Research": "AARP",
         "Alaska Survey Research": "Alaska Survey Res.", "Rasmussen Reports": "Rasmussen",
         "Texas Public Opinion Research": "Texas Public Op.", "Texas Southern University": "Texas Southern",
         "Beacon Research (D)/ Shaw & Co. Research": "Fox News", "Pulse Decision Science": "Pulse Decision",
         "Stratus Intelligence": "Stratus", "Marist University": "Marist", "University of Texas/Texas Politics Project": "UT Texas Politics", "ReconMR/Siena University": "ReconMR/Siena", "Z to A Research": "Z to A", "Mitchell Research & Communications": "Mitchell", "Global Strategy Group": "Global Strategy", "Wedgewood Polls": "Wedgewood", "Guidant Polling & Strategy": "Guidant", "UMass Lowell/YouGov": "UMass Lowell", "Emerson College": "Emerson",
         "Bowling Green State University/YouGov": "BGSU/YouGov", "Suffolk University": "Suffolk", "Catawba College/YouGov": "Catawba/YouGov",
         "East Carolina University": "East Carolina", "High Point University": "High Point", "Opinion Diagnostics": "Opinion Diag."}

STORIES = {
    "2026-10-05": {
        "race": "AK", "since": "2026-08-15", "focus": "New York Times/Siena University", "folder": "05-reading-polls-01",
        "left": "Peltola", "right": "Sullivan",
        "headline": "Alaska’s newest poll has Peltola up 7. The rest show a near tie.",
        "dek": "Eight Senate polls since August: Peltola (D) minus Sullivan (R), likely voters.",
        "source": "Polls ending 23 Aug – 1 Oct 2026. Data: VoteHub (CC BY 4.0) and Wikipedia (CC BY-SA 4.0).",
        "title2": "Too high, or early?",
        "against": ["504 voters: on a sample this size, the gap can swing about 9 points either way.",
                    "The seven other polls since August average Peltola +1.",
                    "Alaska is hard to poll: small, spread out, many voters hard to reach."],
        "for": "Siena has almost no historical lean, and adjusting the other pollsters for theirs moves them slightly "
               "toward Peltola, not away.",
        "hypothesis": "Our hypothesis: closer to Peltola +2. We’ll check it against the next three polls.",
        "caption": (
            "Alaska's newest Senate poll, from NYT/Siena, has Mary Peltola ahead of Dan Sullivan by 7 points, 50 to "
            "43. The seven other polls since August average about Peltola +1, so is this an early signal or "
            "noise?\n\n"
            "There are good reasons to read it carefully. It's 504 likely voters, and on a sample that size the gap can "
            "move about 9 points either way. Alaska is also one of the harder states to poll: small, spread out, with "
            "many voters who are hard to reach.\n\n"
            "But it could be right. Siena has almost no historical lean, and when we adjust the other pollsters for "
            "their usual lean, they move slightly toward Peltola, not away.\n\n"
            "Our hypothesis: the race is closer than +7, nearer Peltola +2. We'll check it against the next three "
            "polls and tell you how it went.\n\n"
            "#midterms2026 #Alaska #elections"),
        "short": ("Alaska's newest poll, NYT/Siena, has Peltola up 7 on Sullivan. The seven others since August "
                  "average about +1. Small sample, hard state to poll, but Siena has almost no historical lean. Our "
                  "hypothesis: nearer +2."),
        "more": (" We'll check it against the next three polls. Reading the polls."),
        "alt1": ("Dot chart of eight Alaska Senate polls since August, Peltola minus Sullivan. Seven sit between "
                 "Sullivan +2.5 and Peltola +5; the newest, NYT/Siena, is furthest out at Peltola +7."),
    },
    "2026-10-06": {
        "race": "TX", "since": "2026-09-15", "focus": "Pulse Decision Science", "folder": "06-reading-polls-02",
        "left": "Talarico", "right": "Paxton", "exclude": ["Slingshot Strategies"],  # the TPOR poll, listed twice
        "headline": "One Texas poll has Paxton up 3. Nine others have Talarico ahead or tied.",
        "dek": "Ten Senate polls since mid-September: Talarico (D) minus Paxton (R), likely and registered voters.",
        "source": "Polls ending 17–30 Sep 2026. Data: VoteHub (CC BY 4.0) and Wikipedia (CC BY-SA 4.0).",
        "title2": "Outlier, or early?",
        "against": ["It’s the only one of ten polls since mid-September with Paxton ahead.",
                    "Its pollster isn’t in the 2018–24 records we use, so its usual lean is unknown.",
                    "800 voters: the gap can swing about 7 points either way."],
        "for": "Texas voted for Trump by 14 points in 2024. If Republicans who haven’t decided come home late, a "
               "poll like this is where it would show first.",
        "hypothesis": "Our hypothesis: Talarico still narrowly ahead, about +3. We’ll check it against the next three "
                      "polls.",
        "caption": (
            "A new Texas Senate poll from Pulse Decision Science has Ken Paxton ahead of James Talarico by 3 points, "
            "48 to 45. Of the ten polls since mid-September, it's the only one with Paxton in front; the other nine "
            "have Talarico ahead or tied, by about 3 on average.\n\n"
            "So is it an outlier or an early sign? There are reasons for caution. Pulse Decision Science isn't in the "
            "2018 to 2024 polls we use to estimate each pollster's usual lean, so we can't tell which way it tends to "
            "lean. And with 800 voters, the gap can move about 7 points either way.\n\n"
            "But it could be right. Texas voted for Trump by 14 points in 2024. If Republicans who haven't made up "
            "their minds come home late, a poll like this is where it would show first.\n\n"
            "Our hypothesis: Talarico is still narrowly ahead, around +3. We'll check it against the next three polls "
            "and report back.\n\n"
            "#midterms2026 #Texas #elections"),
        "short": ("A new Texas poll has Paxton up 3 on Talarico. The nine others since mid-September have Talarico "
                  "ahead or tied, by about 3. New pollster, no track record, but Texas voted Trump +14 in 2024. Our "
                  "hypothesis: Talarico still about +3."),
        "more": " We'll check it against the next three polls. Reading the polls.",
        "alt1": ("Dot chart of ten Texas Senate polls since mid-September, Talarico minus Paxton. Nine sit between a "
                 "tie and Talarico +6; the Pulse Decision Science poll is the only one with Paxton ahead, by 3."),
    },
    "2026-10-07": {
        "race": "OH-S", "since": "2026-09-01", "focus": "Marist University", "folder": "07-reading-polls-03",
        "left": "Brown", "right": "Husted",
        "headline": "One Ohio poll has Brown up 8. The ten others average about +3.",
        "dek": "Eleven Senate polls since September: Brown (D) minus Husted (R).",
        "source": "Polls ending 9 Sep – 1 Oct 2026. Data: VoteHub (CC BY 4.0) and Wikipedia (CC BY-SA 4.0).",
        "title2": "Registered, or likely?",
        "against": ["It asked all registered voters; the other ten asked likely voters.",
                    "Marist has leaned about 2 points toward Democrats against the average pollster, 2018–24.",
                    "The ten likely-voter polls since September average Brown +3."],
        "for": "It’s a large sample, 1,298 voters, from an established pollster, and Brown has led in every Ohio "
               "poll this month.",
        "hypothesis": "Our hypothesis: nearer Brown +3. We’ll check it against the next three polls.",
        "caption": (
            "A new Ohio Senate poll from Marist has Sherrod Brown ahead of Jon Husted by 8 points, 51 to 43. The ten "
            "other polls since September average about Brown +3.\n\n"
            "The biggest difference is who was asked. Marist asked all registered voters; the other ten asked likely "
            "voters, the people expected to turn out, and in a midterm that group can look quite different. Marist "
            "has also leaned about 2 points toward Democrats compared with the average pollster in 2018 to 2024.\n\n"
            "But it's a large sample from an established pollster, and Brown has led in every Ohio poll this month, so "
            "the direction isn't in doubt. The size is.\n\n"
            "Our hypothesis: the race is closer to Brown +3, where the likely-voter polls sit. We'll check it against "
            "the next three polls and report back.\n\n"
            "#midterms2026 #Ohio #elections"),
        "short": ("A new Ohio poll, Marist, has Brown up 8 on Husted. The ten others since September average about +3. "
                  "Marist asked registered voters, the others likely voters, and it has leaned about 2 points "
                  "toward Democrats. Our hypothesis: nearer Brown +3."),
        "more": " We'll check it against the next three polls. Reading the polls.",
        "alt1": ("Dot chart of eleven Ohio Senate polls since September, Brown minus Husted. Ten likely-voter polls "
                 "sit between Brown +0.5 and Brown +5; Marist, of registered voters, is furthest out at Brown +8."),
    },
    "2026-10-08": {
        "race": "FL-S", "since": "2026-09-15", "focus": "Mason-Dixon", "folder": "08-reading-polls-04",
        "left": "Nixon", "right": "Moody",
        "headline": "A new Florida poll has Moody up 10. The five others average about +5.",
        "dek": "Six Senate polls since mid-September: Nixon (D) minus Moody (R), likely voters.",
        "source": "Polls ending 17 Sep – 5 Oct 2026. Data: VoteHub (CC BY 4.0) and Wikipedia (CC BY-SA 4.0).",
        "title2": "Too wide, or right?",
        "against": ["625 voters: on a sample this size, the gap can swing about 8 points either way.",
                    "YouGov polled the same week with 3,813 voters and found Moody +5.",
                    "The five other polls since mid-September average Moody +5."],
        "for": "Mason-Dixon has leaned less than a point in our 2018–24 records, Stetson also has Moody up 11, and "
               "Trump won Florida by 13 in 2024.",
        "hypothesis": "Our hypothesis: nearer Moody +6. We’ll check it against the next three polls.",
        "caption": (
            "Florida Senate poll: a new Mason-Dixon survey has Ashley Moody ahead of Angie Nixon by 10 points, 50 to "
            "40. The five other polls since mid-September average about Moody +5, from a tie to Moody +11.\n\n"
            "There are reasons to read it carefully. It's 625 likely voters, and on a sample that size the gap can "
            "move about 8 points either way. YouGov was in the field the same week with 3,813 voters and found Moody "
            "ahead by 5.\n\n"
            "But it could be right. Mason-Dixon has leaned less than a point compared with the average pollster in "
            "2018 to 2024, Stetson found a similar Moody +11 in September, and Trump won Florida by 13 points in "
            "2024.\n\n"
            "Our hypothesis: Moody is ahead, but nearer +6 than +10. We'll check it against the next three polls and "
            "report back.\n\n"
            "#midterms2026 #Florida #FloridaSenate #elections"),
        "short": ("A new Florida poll, Mason-Dixon, has Moody up 10 on Nixon. The five others since mid-September "
                  "average about +5, and YouGov found +5 the same week. Small sample, but Mason-Dixon barely leans. "
                  "Our hypothesis: nearer Moody +6."),
        "more": " We'll check it against the next three polls. Reading the polls.",
        "x": ("Mason-Dixon has Moody up 10 in Florida. YouGov, same week, 3,813 voters: Moody +5. Six polls since "
              "mid-September run from a tie to Moody +11. Our hypothesis: nearer +6, checked against the next three "
              "polls."),
        "threads": ("Two Florida Senate polls from the same week: Mason-Dixon has Ashley Moody up 10 on Angie Nixon, "
                    "YouGov has her up 5. Mason-Dixon barely leans in past cycles, but 625 voters is a small sample. "
                    "We think the race is nearer Moody +6, and we'll check it against the next three polls. If you "
                    "live in Florida, does this race feel close where you are?"),
        "topic": "2026 Midterms",
        "first_comment": "If you live in Florida, does this Senate race feel close where you are?",
        "alt1": ("Dot chart of six Florida Senate polls since mid-September, Nixon minus Moody. They run from a tie "
                 "to Moody +11; the newest Mason-Dixon poll, ringed, has Moody +10."),
    },
    "2026-10-12": {
        "race": "OH-S", "since": "2026-09-14", "focus": "co/efficient", "folder": "12-reading-polls-06",
        "left": "Brown", "right": "Husted",
        "headline": "One Ohio poll has Husted up 1. The ten others all have Brown ahead.",
        "dek": "Eleven Senate polls since mid-September: Brown (D) minus Husted (R).",
        "source": "Polls ending 16 Sep – 6 Oct 2026. Data: VoteHub (CC BY 4.0) and Wikipedia (CC BY-SA 4.0).",
        "title2": "Shift, or noise?",
        "against": ["In 2018–24, co/efficient leaned about 3 points toward Republicans.",
                    "SSRS, polling the same week, had Brown up 6.",
                    "Every other poll since mid-September has Brown ahead."],
        "for": "InsiderAdvantage and Quantus also had Brown up by a point or less in late September, and Trump won "
               "Ohio by 11 in 2024.",
        "hypothesis": "Our hypothesis: nearer Brown +3. We’ll check it against the next three polls.",
        "caption": (
            "Ohio Senate poll: a new co/efficient survey has Jon Husted ahead of Sherrod Brown by 1 point, 45 to 44. "
            "It's the only Husted lead in eleven polls since mid-September; the other ten all have Brown ahead, most "
            "by 3 or 4 points.\n\n"
            "Read it carefully. With 925 voters, the gap can move about 6 points either way. The pollster, "
            "co/efficient, has leaned about 3 points toward Republicans compared with the average pollster in 2018 "
            "to 2024, and SSRS, in the field the same week, had Brown up 6.\n\n"
            "But don't dismiss it. InsiderAdvantage and Quantus also found Brown ahead by a point or less in late "
            "September, and Trump won Ohio by 11 points in 2024.\n\n"
            "Our hypothesis: Brown is still ahead, nearer +3. It's the same number we gave last week for a Marist "
            "poll that had him up 8. We'll check it against the next three polls and report back.\n\n"
            "#midterms2026 #Ohio #OhioSenate #elections"),
        "short": ("A new Ohio poll, co/efficient, has Husted up 1 on Brown, the only Husted lead in eleven polls since "
                  "mid-September. It has leaned about 3 points toward Republicans, and SSRS had Brown +6 the same "
                  "week. Our hypothesis: nearer Brown +3."),
        "more": " We'll check it against the next three polls. Reading the polls.",
        "x": ("Ohio: co/efficient has Husted up 1, the only Husted lead in eleven polls since mid-September. SSRS, "
              "same week: Brown +6. Last week we read Marist's Brown +8 as nearer +3. Same hypothesis from the "
              "other side: nearer Brown +3."),
        "threads": ("A new Ohio Senate poll from co/efficient has Jon Husted up 1 on Sherrod Brown, the only Husted "
                    "lead since mid-September. Last week we looked at a Marist poll with Brown up 8 and said the race "
                    "was nearer Brown +3. We're saying the same now, from the other side, and we'll check it against the next "
                    "three polls. If you're in Ohio, does it feel this close?"),
        "topic": "2026 Midterms",
        "first_comment": "If you're in Ohio, does the Brown-Husted race feel close where you are?",
        "alt1": ("Dot chart of eleven Ohio Senate polls since mid-September, Brown minus Husted. Ten have Brown "
                 "ahead, from half a point to 8, with the likely-voter polls in the middle at Brown +3; the new "
                 "co/efficient poll, ringed, has Husted up 1."),
    },
    "2026-10-13": {
        "race": "TX", "since": "2026-09-20", "focus": "YouGov", "folder": "13-reading-polls-07",
        "left": "Talarico", "right": "Paxton",
        "exclude": ["Slingshot Strategies", "University of Massachusetts Lowell Center for Public Opinion/YouGov"],
        "headline": "Texas’s largest recent poll has Talarico up 6. The rest sit around +2.",
        "dek": "Twelve Senate polls since 20 September: Talarico (D) minus Paxton (R).",
        "source": "Polls ending 20 Sep – 8 Oct 2026. Data: VoteHub (CC BY 4.0) and Wikipedia (CC BY-SA 4.0).",
        "title2": "Big sample, big gap?",
        "against": ["YouGov has leaned about 1 point toward Democrats against the average pollster, 2018–24.",
                    "Trafalgar, polling right after, had Talarico up 3.",
                    "The other likely-voter polls since 20 September sit around Talarico +2."],
        "for": "3,625 voters is a huge sample: the gap can only swing about 3 points either way. And NYT/Siena also "
               "had Talarico up 6.",
        "hypothesis": "Our hypothesis: Talarico ahead, nearer +3 than +6. We’ll check it against the next three polls.",
        "caption": (
            "Texas Senate poll: a new YouGov survey of 3,625 likely voters, the largest Texas poll in weeks, has James "
            "Talarico ahead of Ken Paxton by 6 points, 50 to 44. The other polls since 20 September sit around "
            "Talarico +2.\n\n"
            "Read it carefully. YouGov has leaned about a point toward Democrats compared with the average pollster in "
            "2018 to 2024, and Trafalgar, in the field right after, had Talarico up 3.\n\n"
            "But a sample this size is hard to wave away: the gap can only move about 3 points either way, and "
            "NYT/Siena found the same +6 at the end of September.\n\n"
            "Our hypothesis: Talarico is ahead, but nearer +3 than +6. It's the number we gave on 6 October for a "
            "poll that had Paxton up 3. We'll check it against the next three polls and report back.\n\n"
            "#midterms2026 #Texas #TexasSenate #elections"),
        "short": ("A new Texas poll, YouGov with 3,625 voters, has Talarico up 6 on Paxton. The others since 20 "
                  "September sit around +2. YouGov leans slightly toward Democrats, but the sample is huge. Our "
                  "hypothesis: nearer +3."),
        "more": " We'll check it against the next three polls. Reading the polls.",
        "x": ("Texas: YouGov, 3,625 voters, has Talarico up 6. The others since 20 Sep sit around +2. On 6 Oct "
              "a poll had Paxton up 3 and we said nearer Talarico +3. Same answer from the other side."),
        "threads": ("The biggest Texas Senate poll in weeks, YouGov with 3,625 voters, has James Talarico up 6 on Ken "
                    "Paxton. The others since 20 September sit around +2. On 6 October a poll had Paxton up "
                    "3 and we said the race was nearer Talarico +3. We're saying the same now, from the other side. If "
                    "you're in Texas, does it feel close where you are?"),
        "topic": "2026 Midterms",
        "first_comment": "If you live in Texas, does this Senate race feel close where you are?",
        "alt1": ("Dot chart of twelve Texas Senate polls since 20 September, Talarico minus Paxton. The others "
                 "range from Paxton +3 to Talarico +6, with the middle around Talarico +2; the new YouGov poll, the largest, "
                 "has Talarico up 6."),
    },
    "2026-10-13-kansas": {
        "day": "2026-10-13", "race": "KS", "since": "2026-09-08", "focus": "InsiderAdvantage",
        "folder": "13-reading-polls-08", "left": "Hamilton", "right": "Marshall",
        "headline": "Kansas polls lean Hamilton. Our simulation leans Marshall.",
        "dek": "Nine Senate polls since September, and our expected result. Hamilton (D) minus Marshall (R).",
        "source": "Polls ending 10 Sep – 10 Oct 2026: VoteHub (CC BY 4.0), Wikipedia (CC BY-SA 4.0). Simulation: 13 Oct.",
        "title2": "Two numbers, two meanings.",
        "ours": {"margin": -1.92, "leans": "Marshall",
                 "vote": "51–49", "vote_label": "expected vote, Marshall first",
                 "chance": "66 in 100", "chance_label": "Marshall's chance to win",
                 "range": "Close, with a favourite: across 40,000 simulated elections the result runs from Marshall "
                          "+8 to Hamilton +5.",
                 "why": "We blend the polls with Kansas's record (Trump +16 in 2024), and some of Hamilton's lift "
                        "comes from news we expect to fade.",
                 "wrong": "Six of eight polls since mid-September have Hamilton ahead, this one from a pollster that "
                          "leans Republican."},
        "hypothesis": "Our forecast: Marshall 51–49. He wins 66 in 100 simulated elections.",
        "caption": (
            "Kansas Senate poll: a new InsiderAdvantage survey has Adam Hamilton ahead of Roger Marshall, 48 to 47. "
            "It isn't an outlier: six of the eight Kansas polls since mid-September have Hamilton slightly ahead.\n\n"
            "Our simulation leans the other way, and it's worth being precise about how. Our expected vote is Marshall "
            "about 51, Hamilton about 49: a close race. Across 40,000 simulated elections, Marshall wins 66 in every "
            "100. That 66 is a chance of winning, not a share of the vote.\n\n"
            "Why we lean Marshall when the polls don't: we blend the polls with Kansas's long voting record (Trump "
            "won it by 16 points in 2024), and part of Hamilton's recent lift comes from news our model expects to "
            "fade before 3 November.\n\n"
            "Why we might be wrong: the polls agree with each other, and this one comes from a pollster that has "
            "usually leaned about 3 points toward Republicans. We'll keep checking our number against new polls.\n\n"
            "#midterms2026 #Kansas #KansasSenate #elections"),
        "short": ("Kansas polls lean Hamilton: six of eight since mid-September have him ahead. Our simulation leans "
                  "Marshall: expected vote about 51-49, and he wins 66 of 100 simulated elections. A chance of winning, "
                  "not a vote share."),
        "more": " Reading the polls.",
        "x": ("Kansas: six of eight polls since mid-Sep have Hamilton ahead. Our simulation leans Marshall: expected "
              "vote about 51-49, and he wins 66 of 100 simulated elections. That's a chance of winning, not a vote "
              "share."),
        "threads": ("Kansas is a rare case where the polls and our simulation disagree. Six of the eight polls since "
                    "mid-September have Adam Hamilton ahead. We expect Roger Marshall to win about 51 to 49, and he "
                    "wins 66 of every 100 simulated elections: a chance of winning, not a share of the vote. Who do "
                    "you think is reading Kansas right?"),
        "topic": "2026 Midterms",
        "first_comment": "Who do you think is reading Kansas right, the polls or the simulation?",
        "alt1": ("Dot chart of nine Kansas Senate polls since September, Hamilton minus Marshall, with the polls' middle "
                 "at Hamilton +2 and a purple line for our expected result, Marshall +2. The new InsiderAdvantage poll "
                 "has Hamilton up 1."),
    },
    "2026-10-14": {
        "race": "MI", "since": "2026-09-24", "focus": "YouGov", "folder": "14-reading-polls-09",
        "left": "El-Sayed", "right": "Rogers",
        "headline": "Michigan’s largest recent poll has El-Sayed up just 1. Most others put him 4 to 7 ahead.",
        "dek": "Ten Senate polls since 24 September, El-Sayed (D) minus Rogers (R). Partisan polls left out.",
        "source": "Polls ending 24 Sep – 10 Oct 2026: VoteHub (CC BY 4.0), Wikipedia (CC BY-SA 4.0). Simulation: 14 Oct.",
        "title2": "Tightening, or noise?",
        "against_head": "Why it may be too close",
        "against": ["Five of the other nine polls since 24 September put El-Sayed 4 to 7 points ahead.",
                    "It was in the field for almost two weeks, from 22 September, while the race kept moving.",
                    "Of the four other close polls, Trafalgar and InsiderAdvantage usually lean Republican."],
        "for": "3,949 voters is a very large sample, YouGov has, if anything, leaned slightly toward Democrats in "
               "past cycles, and Fox News's poll also has the race at 1.",
        "hypothesis": "Our hypothesis: El-Sayed ahead by about 4. In our simulation he wins 80 in 100.",
        "caption": (
            "Michigan Senate poll: a new YouGov survey of 3,949 likely voters, the largest Michigan poll in weeks, has "
            "Abdul El-Sayed ahead of Mike Rogers by just 1 point, 49 to 48. Five of the other nine polls since 24 "
            "September put El-Sayed 4 to 7 points ahead.\n\n"
            "Read it carefully. YouGov was in the field for almost two weeks while the race kept moving, and of the "
            "four other close polls, Trafalgar and InsiderAdvantage usually lean Republican.\n\n"
            "But it's hard to dismiss: the sample is very large, YouGov has, if anything, leaned slightly toward "
            "Democrats in past cycles, and Fox News's poll also has the race at 1.\n\n"
            "Our hypothesis: El-Sayed is ahead by about 4. Our simulation agrees he's the favourite: he wins 80 of "
            "every 100 simulated elections, with an expected vote of 52–48. We'll check it against the next three "
            "polls.\n\n"
            "We leave out polls paid for by a party, a campaign or a partisan group.\n\n"
            "#midterms2026 #Michigan #MichiganSenate #elections"),
        "short": ("A new Michigan poll, YouGov with 3,949 voters, has El-Sayed up just 1 on Rogers. Five of the other "
                  "nine since 24 Sep put him 4 to 7 ahead. Our hypothesis: about +4. Our simulation: he wins 80 in 100."),
        "more": " We'll check it against the next three polls. Reading the polls.",
        "x": ("Michigan: YouGov, 3,949 voters, has El-Sayed up just 1. Five of the other nine polls since 24 Sep "
              "have him 4 to 7 ahead. Our hypothesis: about +4. Our simulation: he wins 80 in 100, expected vote 52–48."),
        "threads": ("Michigan's Senate race looks tighter in a new YouGov poll: Abdul El-Sayed up just 1 on Mike "
                    "Rogers, with nearly 4,000 voters. Most other recent polls have him 4 to 7 ahead, though Fox News "
                    "also has it at 1. We think he's ahead by about 4. If "
                    "you're in Michigan, does it feel this close?"),
        "topic": "2026 Midterms",
        "first_comment": "If you live in Michigan, does this Senate race feel close where you are?",
        "alt1": ("Dot chart of ten Michigan Senate polls since 24 September, El-Sayed minus Rogers, leaving out "
                 "partisan-sponsored polls. They sit between El-Sayed +1 and +7, with the middle around +4; the new YouGov poll, the largest, has El-Sayed "
                 "up 1."),
    },
    "2026-10-15": {
        "race": "IA", "since": "2026-09-24", "focus": "Marist University", "folder": "15-reading-polls-10",
        "left": "Turek", "right": "Hinson",
        "headline": "Marist has Turek up 7 in Iowa. Most other polls have it within 2.",
        "dek": "Nine Senate polls since 24 September, Turek (D) minus Hinson (R). Partisan polls left out.",
        "source": "Polls ending 28 Sep – 12 Oct 2026: VoteHub (CC BY 4.0), Wikipedia (CC BY-SA 4.0). Simulation: 15 Oct.",
        "title2": "Momentum, or method?",
        "against": ["It counts registered voters; likely voters often lean more Republican in midterms.",
                    "Marist's September poll had Turek up 8 too, when others had it close.",
                    "YouGov, at the same time with twice the sample, has Turek up 1."],
        "for": "Rasmussen and Suffolk, two very different pollsters, both have Turek up 4.",
        "hypothesis": "Our hypothesis: Hinson by about 1. Our simulation: Hinson wins 59 in 100.",
        "caption": (
            "Iowa Senate poll: a new Marist survey has Josh Turek ahead of Ashley Hinson by 7 points, 51 to 44, among "
            "registered voters. The other eight polls since late September range from Hinson +2 to Turek +4.\n\n"
            "Read it carefully. Marist counted registered voters, while most others count likely voters, who in a "
            "midterm often lean a little more Republican. Marist's September poll also had Turek up 8 when others had "
            "it close. And YouGov, in the field at the same time with twice the sample, has Turek up just 1.\n\n"
            "But it isn't alone in seeing Turek ahead: Rasmussen and Suffolk, two very different pollsters, both have "
            "him up 4.\n\n"
            "Our hypothesis: a race close to even, with Hinson ahead by about 1. In our simulation Hinson wins 59 of "
            "every 100 simulated elections, with an expected vote of 51–49. We'll check it against the next three "
            "polls.\n\n"
            "We leave out polls paid for by a party, a campaign or a partisan group.\n\n"
            "#midterms2026 #Iowa #IowaSenate #elections"),
        "short": ("A new Iowa poll, Marist, has Turek up 7 on Hinson among registered voters. The other eight since "
                  "late Sep range from Hinson +2 to Turek +4. Our hypothesis: close to even. Our simulation: Hinson "
                  "wins 59 in 100."),
        "more": " We'll check it against the next three polls. Reading the polls.",
        "x": ("Iowa: Marist has Turek up 7 among registered voters. The other eight polls since late Sep range from "
              "Hinson +2 to Turek +4; YouGov, twice the sample, has Turek +1. Our hypothesis: close to even. Our "
              "simulation: Hinson wins 59 in 100."),
        "threads": ("Iowa's Senate race in a new Marist poll: Josh Turek up 7 on Ashley Hinson. The other recent polls "
                    "sit between Hinson +2 and Turek +4, and Marist counted registered rather than likely voters. We "
                    "think it's close to even. If you're in Iowa, which way does it feel?"),
        "topic": "2026 Midterms",
        "first_comment": "If you live in Iowa, which way does this Senate race feel where you are?",
        "alt1": ("Dot chart of nine Iowa Senate polls since 24 September, Turek minus Hinson, leaving out "
                 "partisan-sponsored polls. Eight sit between Hinson +2 and Turek +4; the new Marist poll, of "
                 "registered voters, has Turek up 7."),
    },
    "2026-10-16": {
        "race": "TX", "since": "2026-09-24", "focus": "InsiderAdvantage", "folder": "16-reading-polls-11",
        "left": "Talarico", "right": "Paxton",
        "exclude": ["Slingshot Strategies", "University of Massachusetts Lowell Center for Public Opinion/YouGov"],
        "headline": "A new Texas poll has Paxton up 1. No other poll since September has him ahead.",
        "dek": "Fourteen Senate polls since 24 September, Talarico (D) minus Paxton (R). Partisan polls left out.",
        "source": "Polls ending 26 Sep – 14 Oct 2026: VoteHub (CC BY 4.0), Wikipedia (CC BY-SA 4.0). Simulation: 16 Oct.",
        "title2": "A shift, or a house lean?",
        "against_head": "Why it may be off",
        "against": ["Ten of the other thirteen polls have Talarico 2 to 6 points ahead.",
                    "InsiderAdvantage has usually leaned a little Republican in past cycles.",
                    "ActiVote, finishing the same day, has Talarico up 4."],
        "for": "It's the newest poll, with 1,200 voters, and Quantus had the race tied a few days earlier.",
        "hypothesis": "Our hypothesis: Talarico by about 3. Our simulation: Talarico wins 59 in 100.",
        "caption": (
            "Texas Senate poll: a new InsiderAdvantage survey of 1,200 likely voters, taken 13 and 14 October, has Ken "
            "Paxton ahead of James Talarico by 1 point, 49 to 48. It is the only poll since late September with "
            "Paxton in front: ten of the other thirteen have Talarico 2 to 6 points ahead.\n\n"
            "Read it carefully. InsiderAdvantage has usually leaned a little Republican in past cycles, and ActiVote, "
            "finishing the same day, has Talarico up 4.\n\n"
            "But it's the newest poll, with a solid sample, and Quantus had the race tied a few days earlier. If more "
            "polls follow it, the race is tightening.\n\n"
            "Our hypothesis: Talarico ahead by about 3. In our simulation Talarico wins 59 of every 100 simulated "
            "elections, with an expected vote of 51–49. We'll check it against the next three polls.\n\n"
            "We leave out polls paid for by a party, a campaign or a partisan group.\n\n"
            "#midterms2026 #Texas #TexasSenate #elections"),
        "short": ("A new Texas poll, InsiderAdvantage with 1,200 voters, has Paxton up 1 on Talarico. No other poll "
                  "since late Sep has him ahead. Our hypothesis: Talarico by about 3. Our simulation: Talarico wins 59 "
                  "in 100."),
        "more": " We'll check it against the next three polls. Reading the polls.",
        "x": ("Texas: InsiderAdvantage, 1,200 voters, has Paxton up 1. It's the only poll since late Sep with him "
              "ahead; ten of the other thirteen have Talarico 2 to 6 up. Our hypothesis: Talarico by about 3. Our "
              "simulation: Talarico wins 59 in 100."),
        "threads": ("A new Texas Senate poll has Ken Paxton up 1 on James Talarico, the first since late September "
                    "with Paxton ahead. Ten of the other thirteen have Talarico 2 to 6 points up, and this pollster "
                    "has usually leaned a little Republican. We think Talarico leads by about 3. Texans, does it feel "
                    "like it's tightening?"),
        "topic": "2026 Midterms",
        "first_comment": "If you're in Texas, does the Senate race feel like it's tightening?",
        "alt1": ("Dot chart of fourteen Texas Senate polls since 24 September, Talarico minus Paxton, leaving out "
                 "partisan-sponsored polls. Thirteen sit between even and Talarico +6; the new InsiderAdvantage poll "
                 "has Paxton up 1."),
    },
    "2026-10-17": {
        "race": "NC", "since": "2026-09-14", "focus": "SurveyUSA", "folder": "17-reading-polls-12",
        "left": "Cooper", "right": "Whatley", "design": "meter", "hyp": 9,
        "against_meter": ["Trafalgar, polling the same week, had Cooper up 8.",
                          "SurveyUSA has leaned slightly toward Democrats in past cycles."],
        "headline": "A new North Carolina poll has Cooper up 14. The others since mid-September sit around +9.",
        "dek": "Twelve Senate polls since mid-September, Cooper (D) minus Whatley (R). Partisan polls left out.",
        "source": "Polls ending 15 Sep – 11 Oct 2026: VoteHub (CC BY 4.0), Wikipedia (CC BY-SA 4.0). Simulation: 17 Oct.",
        "title2": "Breakaway, or noise?",
        "against_head": "Why it may be too high",
        "against": ["643 voters: the gap can swing about 8 points either way.",
                    "Trafalgar, polling the same week, had Cooper up 8.",
                    "SurveyUSA has leaned slightly toward Democrats in past cycles."],
        "for": "Leads this size aren’t new: in September Harper had Cooper up 15, and YouGov up 12.5.",
        "hypothesis": "Our hypothesis: Cooper by about 9. Our simulation: Cooper wins 94 in 100.",
        "caption": (
            "North Carolina Senate poll: a new SurveyUSA survey of 643 likely voters has Roy Cooper ahead of Michael "
            "Whatley by 14 points, 54 to 40. The other polls since mid-September sit around Cooper +9.\n\n"
            "Read it carefully. With 643 voters the gap can move about 8 points either way, Trafalgar, in the field the "
            "same week, had Cooper up 8, and SurveyUSA has leaned slightly toward Democrats in past cycles.\n\n"
            "But leads this size aren't new here: in September, Harper Polling had Cooper up 15 and YouGov's large "
            "poll had him up 12.5.\n\n"
            "Our hypothesis: Cooper ahead by about 9. In our simulation Cooper wins 94 of every 100 simulated "
            "elections, with an expected vote of 54–46. We'll check it against the next three polls.\n\n"
            "We leave out polls paid for by a party, a campaign or a partisan group.\n\n"
            "#midterms2026 #NorthCarolina #NCSenate #elections"),
        "short": ("A new North Carolina poll, SurveyUSA, has Cooper up 14 on Whatley. The other polls since "
                  "mid-September sit around +9. Our hypothesis: Cooper by about 9. Our simulation: Cooper wins 94 in "
                  "100."),
        "more": " We'll check it against the next three polls. Reading the polls.",
        "x": ("North Carolina: SurveyUSA has Cooper up 14. The other polls since mid-September sit around +9; "
              "Trafalgar, same week: +8. Our hypothesis: Cooper by about 9. Our simulation: Cooper wins 94 in 100, "
              "expected vote 54–46."),
        "threads": ("A new North Carolina Senate poll from SurveyUSA has Roy Cooper up 14 on Michael Whatley. The "
                    "other polls since mid-September sit around Cooper +9, and Trafalgar had him up 8 the same week. "
                    "We think the race is nearer +9, and we'll check it against the next three polls. If you're in "
                    "North Carolina, does it feel like a double-digit race?"),
        "topic": "2026 Midterms",
        "first_comment": "If you live in North Carolina, does this Senate race feel like a double-digit race?",
        "alt1": ("Dot chart of twelve North Carolina Senate polls since mid-September, Cooper minus Whatley, leaving "
                 "out partisan-sponsored polls. All have Cooper ahead, from 5 to 15 points, with the middle around +9; "
                 "the new SurveyUSA poll, ringed, has him up 14."),
    },
}


def load(polls: Path, race: str, since: str, exclude=()) -> pd.DataFrame:
    s = pd.read_csv(polls / "senate.csv", parse_dates=["start", "end"])
    s = s[(s.race_id == race) & (s.end >= since) & ~s.pollster.isin(exclude)]
    s = s[~partisan(s)]  # Matteo, 13 Oct: polls paid for by a party, campaign or partisan group never go in
    s = once(s).sort_values("end").copy()
    s["gap"] = s.left - s.right
    return s


def partisan(s: pd.DataFrame) -> pd.Series:
    """Internal polls, and polls paid for by a party, campaign or partisan group (28 Sep rule): a partisan flag counts
    only with a sponsor named, since VoteHub also tags some pollsters themselves (Trafalgar) with no sponsor."""
    txt = lambda c: s[c].fillna("").astype(str).str.strip().ne("") if c in s else False
    return (txt("partisan") & (txt("sponsors") | txt("wiki_sponsor"))) | s.internal.fillna(False).astype(bool)


def once(s: pd.DataFrame) -> pd.DataFrame:
    """One poll listed twice under the same pollster (two sources): keep the version-averaged row."""
    return s.sort_values("versions", ascending=False).drop_duplicates(["race_id", "pollster", "end", "n"])


def candidates(polls: Path, days: int = 7) -> pd.DataFrame:
    """Recent polls furthest from the median of their race's likely-voter polls over three weeks (two-party margin).
    `past` counts the other polls that far out or further on the same side: feature a poll only when few are
    (Matteo, 12 Oct: one wide poll drags a plain average, so a poll in the middle of the pack can look like an
    outlier)."""
    s = pd.read_csv(polls / "senate.csv", parse_dates=["start", "end"])
    s = once(s[~partisan(s)])
    last = s.end.max()
    w = s[s.end >= last - pd.Timedelta(days=21)]
    mid = w[w.population == "lv"].groupby("race_id").margin.agg(["median", "count"])
    r = s[s.end >= last - pd.Timedelta(days=days)].join(mid, on="race_id")
    r["dev"] = r.margin - r["median"]

    def past(i, x) -> int:
        o = w[(w.race_id == x.race_id) & (w.index != i)].margin - x["median"]
        return int((o * (1 if x.dev > 0 else -1) >= abs(x.dev)).sum())

    r["past"] = [past(i, x) for i, x in r.iterrows()]
    return r.reindex(r.dev.abs().sort_values(ascending=False).index)[
        ["race_id", "pollster", "end", "population", "left", "right", "n", "tag", "margin", "median", "count", "dev",
         "past"]]


def strip_chart(s: Slide, p: pd.DataFrame, focus: str, left: str, right: str, lim: float | None = None,
                row: float | None = None, ours: float | None = None) -> dict:
    """One row per poll, oldest at the top: a dot at the gap (left minus right), the featured poll ringed, and a
    dashed line at the middle (median) of the other likely-voter polls, its value written on it. Returns the artists,
    so the reel can reveal them one by one."""
    t = s.t
    lim = lim or (10 if p.gap.abs().max() <= 8 else 20)
    s.y += 40  # room for the value on the dashed line
    ax = s.chart((row or min(54, 440 / len(p))) * len(p), left=340, right=40)
    ax.set_xlim(-lim, lim)
    ax.set_ylim(len(p) - 0.5, -0.5)
    ax.set_yticks([])
    ticks = [-lim, -lim / 2, 0, lim / 2, lim]
    ax.set_xticks(ticks, [typeset(f"+{abs(x):.0f}" if x else "Even") for x in ticks])
    for lab in ax.get_xticklabels():
        lab.set_fontproperties(s.font("sans", 400, 28))
    ax.axvline(0, color=t.ink, lw=pt(3), zorder=1)
    for x in ticks:
        if x:
            ax.axvline(x, color=t.hairline, lw=pt(1), zorder=0)
    rest = p[p.pollster != focus]
    lv = rest[rest.population == "lv"]
    ref = lv if len(lv) else rest
    others = ref.gap.median()
    lead = f"{left} +{others:.0f}" if round(others) > 0 else f"{right} +{-others:.0f}" if round(others) < 0 else "even"
    avg = ax.axvline(others, color=t.ink2, lw=pt(2), ls=(0, (3, 3)), zorder=1)
    # with our expected result on the chart too, the two labels sit on either side of their lines
    side = None if ours is None else ("left" if others >= ours else "right")
    mark = ax.annotate(typeset(f"polls: {lead}" if side else f"middle: {lead}"), (others, -0.5),
                       xytext=({"left": -6, "right": 6, None: 0}[side] * -1 if side else 0, 8),
                       textcoords="offset pixels", ha={"left": "left", "right": "right", None: "center"}[side],
                       va="bottom", color=t.ink2, fontproperties=s.font("sans", 600, 26))
    extra = []
    if ours is not None:  # the simulation's expected margin, in the simulation colour (Matteo, 12 Oct: show both)
        us = f"{left} +{ours:.0f}" if round(ours) > 0 else f"{right} +{-ours:.0f}" if round(ours) < 0 else "even"
        extra.append(ax.axvline(ours, color=t.ai, lw=pt(4), zorder=2))
        extra.append(ax.annotate(typeset(f"our forecast: {us}"), (ours, -0.5), xytext=(6 if side == "left" else -6, 8),
                                 textcoords="offset pixels", ha="right" if side == "left" else "left", va="bottom",
                                 color=t.ai, fontproperties=s.font("sans", 700, 26)))
    rows = []
    for i, row in enumerate(p.itertuples()):
        c = t.dem if row.gap > 0 else t.rep if row.gap < 0 else t.data
        hot = row.pollster == focus
        dot = ax.scatter([row.gap], [i], s=pt(34 if hot else 24) ** 2, facecolor=c,
                         edgecolor=t.ink if hot else t.paper, linewidth=pt(4 if hot else 3), zorder=4 if hot else 3)
        name = f"{SHORT.get(row.pollster, row.pollster)}, {row.end.day} {row.end:%b}"
        label = ax.text(-lim * 1.04, i, typeset(name), va="center", ha="right", color=t.ink,
                        fontproperties=s.font("sans", 600 if hot else 400, 27))
        tag = None
        if hot:
            who = left if row.gap > 0 else right
            # beside its own dot, on the side with more room, so it never sits on the row above (Kansas, 12 Oct)
            right_side = row.gap <= lim * 0.35
            tag = ax.text(row.gap + (lim * 0.09 if right_side else -lim * 0.09), i, typeset(f"{who} +{abs(row.gap):.0f}"),
                          va="center", ha="left" if right_side else "right", color=t.ink,
                          fontproperties=s.font("sans", 600, 28), zorder=2,  # over the lines, under dots
                          bbox={"facecolor": t.paper, "edgecolor": "none", "pad": 1})
        rows.append({"dot": dot, "label": label, "tag": tag, "hot": hot})
    s.y += 50
    x0, x1 = MARGIN + 340, s.w - MARGIN
    arrow = s.pil("mono", 400, 26).getlength("← ")
    s._put(x0, s.y, "← ", "mono", 400, 26, t.ink2, va="top")
    s._put(x0 + arrow, s.y, f"{right} ahead", "sans", 400, 26, t.ink2, va="top")
    s._put(x1, s.y, " →", "mono", 400, 26, t.ink2, ha="right", va="top")
    s._put(x1 - arrow, s.y, f"{left} ahead", "sans", 400, 26, t.ink2, ha="right", va="top")
    s.y += 44
    kind = " likely-voter" if 0 < len(lv) < len(rest) else ""
    avg_text = s._put(x0, s.y, f"- - -  middle of the other {len(ref)}{kind} polls", "sans", 400, 26, t.ink2,
                      va="top")
    s.y += 40
    if ours is not None:
        extra.append(s._put(x0, s.y, "——  our expected result on 3 Nov", "sans", 600, 26, t.ai, va="top"))
        s.y += 40
    s.y += 10
    return {"rows": rows, "avg": [avg, mark, avg_text] + extra, "others": others}


def _others(p: pd.DataFrame, focus: str) -> tuple[pd.DataFrame, pd.Series, pd.DataFrame]:
    rest = p[p.pollster != focus]
    lv = rest[rest.population == "lv"]
    return rest, p[p.pollster == focus].iloc[-1], (lv if len(lv) else rest)


def _scale(p: pd.DataFrame, x0: float, x1: float, extra=()) -> tuple[float, float, callable]:
    """A margin axis padded to whole fives that always shows Even; returns lo, hi and the pixel mapping."""
    import math
    lo = 5 * math.floor((min(0.0, p.gap.min(), *extra) - 3) / 5)
    hi = 5 * math.ceil((max(0.0, p.gap.max(), *extra) + 3) / 5)
    return lo, hi, lambda v: x0 + (v - lo) / (hi - lo) * (x1 - x0)


def _lead(v: float, left: str, right: str) -> str:
    n = f"{abs(v):.1f}".removesuffix(".0")
    return f"{left} +{n}" if v > 0.25 else f"{right} +{n}" if v < -0.25 else "even"


def _ticks(s: Slide, y: float, lo: float, hi: float, X, left: str, right: str):
    t = s.t
    for v in range(int(lo), int(hi) + 1, 5):
        s._put(X(v), y, "Even" if v == 0 else f"+{abs(v)}", "sans", 400, 26, t.ink2, ha="center", va="top")
    arrow = s.pil("mono", 400, 24).getlength("← ")
    x0, x1 = X(lo), X(hi)
    s._put(x0, y + 40, "← ", "mono", 400, 24, t.ink2, va="top")
    s._put(x0 + arrow, y + 40, f"{right} ahead", "sans", 400, 24, t.ink2, va="top")
    s._put(x1, y + 40, " →", "mono", 400, 24, t.ink2, ha="right", va="top")
    s._put(x1 - arrow, y + 40, f"{left} ahead", "sans", 400, 24, t.ink2, ha="right", va="top")


def noise_meter(s: Slide, p: pd.DataFrame, focus: str, left: str, right: str, hyp: float | None = None):
    """Slide 2 of the meter design (Matteo, 17 Oct; slide 1 stays the dot chart): one bar, the new poll with its margin of error as a band, the middle of the other
    polls (and our hypothesis) marked, so "breakaway, or noise?" is answered by eye."""
    t, ax = s.t, s.ax
    rest, hot, ref = _others(p, focus)
    x0, x1 = MARGIN + 24, s.w - MARGIN - 24
    g, mid = float(hot.gap), ref.gap.median()
    moe = 2 * 1.96 * (0.25 / float(hot.n)) ** 0.5 * 100
    lo, hi, X = _scale(p, x0, x1, (g - moe + 3, g + moe - 3))
    c = t.dem if g > 0 else t.rep if g < 0 else t.data
    label = f"{SHORT.get(hot.pollster, hot.pollster)}: {_lead(g, left, right)}, give or take {moe:.0f}"
    w = s.pil("sans", 600, 32).getlength(label)
    cx = min(max(X(g), MARGIN + w / 2), s.w - MARGIN - w / 2)
    s._put(cx, s.y, label, "sans", 600, 32, c, ha="center", va="top")
    bar = s.y + 70
    ax.add_patch(plt_rect((x0, bar), x1 - x0, 34, t.hairline, z=0.6))
    a, b = X(max(lo, g - moe)), X(min(hi, g + moe))
    ax.add_patch(plt_rect((a, bar - 10), b - a, 54, c, z=0.8, alpha=0.28))
    for x in (a, b):
        ax.plot([x, x], [bar - 10, bar + 44], color=c, lw=pt(3), zorder=2)
    ax.plot([X(0), X(0)], [bar - 18, bar + 52], color=t.ink, lw=pt(3), zorder=2)
    ax.scatter([X(g)], [bar + 17], s=pt(40) ** 2, color=c, edgecolor=t.ink, linewidth=pt(5), zorder=5)
    ax.plot([X(mid), X(mid)], [bar - 18, bar + 52], color=t.ink, lw=pt(3), ls=(0, (2, 2)), zorder=3)
    _ticks(s, bar + 62, lo, hi, X, left, right)
    same = hyp is not None and abs(hyp - mid) < 1
    mark = (f"Dashed: the middle of the other {len(ref)} polls, {_lead(mid, left, right)}"
            + (", and our hypothesis" if same else ""))
    s.y = bar + 146
    s.text(mark, "sans", 600, 26, t.ink2, after=0.4)
    if hyp is not None and not same:
        ax.scatter([X(hyp)], [bar + 17], marker="D", s=pt(22) ** 2, color=t.note, edgecolor=t.ink, zorder=6)
    inside = min(g - moe, g + moe) <= mid <= max(g - moe, g + moe)
    s.text("Its margin of error reaches the middle of the other polls." if inside else
           "Even with its margin of error, it sits apart from the other polls.", "serif", 600, 34, after=0.7)


def plt_rect(xy, w, h, color, z=1.0, alpha=1.0):
    import matplotlib.pyplot as plt
    return plt.Rectangle(xy, w, h, color=color, lw=0, zorder=z, alpha=alpha)


def end(t: str, limit: int, link: int = 0) -> str:
    fits = len(t) + 1 + len(DISCLAIMER) + (link - len(SITE) if link else 0) <= limit
    return f"{t} {DISCLAIMER}" if fits else f"{t} {LABEL}."


def build(day: str, polls: Path, theme=LAB) -> tuple[Path, list[str]]:
    st = STORIES[day]
    d = date.fromisoformat(st.get("day", day))  # a second story on one day has its own key
    p = load(polls, st["race"], st["since"], st.get("exclude", ()))
    a = Slide(d, "", theme, series=SERIES)
    a.headline(st["headline"], px=64)
    a.dek(st["dek"], px=34)
    strip_chart(a, p, st["focus"], st["left"], st["right"], ours=(st.get("ours") or {}).get("margin"))
    a.source(st["source"])

    b = Slide(d, "", theme, series=SERIES)
    if st.get("design") == "meter":  # the margin of error is drawn, so the reasons skip it (no point twice)
        b.headline(st["title2"], px=72)
        noise_meter(b, p, st["focus"], st["left"], st["right"], st.get("hyp"))
        for head, items in ((st.get("against_head", "Why it may be too high"), st.get("against_meter", st["against"])),
                            (st.get("for_head", "Why it may be right"), [st["for"]])):
            b.text(head, "sans", 600, 26, theme.ink2, after=0.35)
            for line in items:
                b.ax.scatter([MARGIN + 9], [b.y + 19], s=pt(12) ** 2, color=theme.ai, zorder=3)
                b.text(line, "serif", 600, 30, x=MARGIN + 32, width=b.width - 32, after=0.4)
            b.y += 12
        b.note(st["hypothesis"], width=760)
        b.source(st["source"])
    elif st.get("ours"):  # polls agree with each other but not with us: show both of our numbers, clearly named
        o = st["ours"]
        b.headline(st["title2"], px=80)
        from . import charts
        charts.stats(b, [(o["vote"], o["vote_label"]), (o["chance"], o["chance_label"])], px=110, rule=True)
        b.text(o["range"], px=32, color=theme.ink2, after=1.0)
        for head, body in (("Why we lean " + o["leans"], o["why"]), ("Why we might be wrong", o["wrong"])):
            b.text(head, "sans", 600, 30, theme.ink2, after=0.4)
            b.text(body, "serif", 600, 36, after=0.8)
        b.source(st["source"])
    else:
        b.headline(st["title2"], px=88)
        b.text(st.get("against_head", "Why it may be too high"), "sans", 600, 30, theme.ink2, after=0.5)
        for n, line in enumerate(st["against"], 1):
            top = b.y
            b._put(MARGIN, top - 6, str(n), "hero", theme.hero_weight, 64, theme.ai, va="top")
            b.text(line, "serif", 600, 38, x=MARGIN + 76, width=b.width - 76, after=0.7)
        b.y += 10
        b.text(st.get("for_head", "Why it may be right"), "sans", 600, 30, theme.ink2, after=0.5)
        b.text(st["for"], "serif", 600, 38, after=0.9)
        b.note(st["hypothesis"], width=760)
        b.source(st["source"])

    out = KITS / "daily" / st["folder"]
    out.mkdir(parents=True, exist_ok=True)
    problems = []
    for i, s in enumerate((a, b), 1):
        problems += [f"slide {i}: {x}" for x in s.layout_problems() + s.missing_glyphs()]
        problems += [f"slide {i}: {x}" for x in text.slide_problems(s, ALLOW)]
        s.save(out / f"slide-{i}.jpg")
    caption = f"{st['caption']}\n\n{DISCLAIMER}"
    posts = {"x": f'{st.get("x", st["short"])} {LABEL}.',  # no link on X: it cuts reach
             "bluesky": end(st["short"], LIMIT["bluesky"]),
             "threads": end(st.get("threads", st["short"] + st["more"]), LIMIT["threads"])}
    meta = {k2: st[k1] for k1, k2 in (("topic", "threads_topic"), ("first_comment", "instagram_first_comment"))
            if st.get(k1)}
    (out / "meta.json").write_text(json.dumps(meta, indent=1, ensure_ascii=False), encoding="utf-8")
    if meta.get("instagram_first_comment"):
        problems += [f"first comment: {x}" for x in text.check(meta["instagram_first_comment"], caption=False,
                                                                allow=ALLOW)]
    if st.get("ours"):
        o = st["ours"]
        alt2 = " ".join([st["title2"], f"{o['vote']}: {o['vote_label']}.", f"{o['chance']}: {o['chance_label']}.",
                         o["range"], f"Why we lean {o['leans']}: {o['why']}", f"Why we might be wrong: {o['wrong']}"])
    else:
        alt2 = " ".join([st["title2"], st.get("against_head", "Why it may be too high") + ":", *st["against"],
                         st.get("for_head", "Why it may be right") + ":", st["for"],
                         st["hypothesis"]])
    (out / "caption.txt").write_text(caption, encoding="utf-8")
    (out / "alt-text.txt").write_text(f"slide-1.jpg: {st['alt1']}\nslide-2.jpg: {alt2}\n", encoding="utf-8")
    lines = ["# Single posts (X and Threads through Buffer; Bluesky by hand)", ""]
    for k in ("x", "threads", "bluesky"):
        n = len(posts[k]) + (X_LINK - len(SITE) if k == "x" and SITE in posts[k] else 0)
        lines += [f"## {'X' if k == 'x' else k.capitalize()} ({n} of {LIMIT[k]} characters; attach slide-1 to slide-2)",
                  "", posts[k], ""]
        problems += [f"{k}: {n} characters" for _ in [0] if n > LIMIT[k]]
    (out / "single-post.md").write_text("\n".join(lines), encoding="utf-8")
    for name, s in [("caption", caption), *posts.items()]:
        problems += [f"{name}: {x}" for x in text.check(s, caption=True, allow=ALLOW)]
    (out / "checks.txt").write_text("\n".join(problems) or "all rules pass", encoding="utf-8")
    return out, problems


def reel(day: str, polls: Path, theme=LAB) -> dict:
    """The 9:16 Reel of the day's story (Instagram Reel, X video): each poll lands in date order, then the middle
    line, then the featured poll, then the hypothesis. 30 fps, H.264, no sound; the cover is the last frame."""
    import imageio_ffmpeg
    import matplotlib.pyplot as plt
    import numpy as np
    from PIL import Image

    st = STORIES[day]
    d = date.fromisoformat(st.get("day", day))  # a second story on one day has its own key
    p = load(polls, st["race"], st["since"], st.get("exclude", ()))
    w, h, fps = 1080, 1920, 30
    s = Slide(d, "", theme, size=(w, h), series=SERIES)
    s.headline(st["headline"], px=64)  # no dek: the axis labels say what the dots are
    s.y += 10
    art = strip_chart(s, p, st["focus"], st["left"], st["right"], row=min(48, 420 / len(p)),
                      ours=(st.get("ours") or {}).get("margin"))
    s.source(st["source"])
    n_patches, n_texts = len(s.ax.patches), len(s.ax.texts)
    s.note(st["hypothesis"], width=900, px=34)
    note = s.ax.patches[n_patches:] + s.ax.texts[n_texts:]
    if bad := s.layout_problems() + s.missing_glyphs() + text.slide_problems(s, ALLOW):
        raise ValueError(f"reel layout: {bad}")

    start, step = 0.8, 0.45
    calm = [r for r in art["rows"] if not r["hot"]]
    hot = [r for r in art["rows"] if r["hot"]]
    times = {id(r): start + i * step for i, r in enumerate(calm)}
    t_avg = start + len(calm) * step + 0.3
    for r in hot:
        times[id(r)] = t_avg + 0.9
    t_note, total = t_avg + 2.3, t_avg + 5.2
    base = {id(r): r["dot"].get_sizes()[0] for r in art["rows"]}

    out = KITS / "daily" / st["folder"] / "reel.mp4"
    out.parent.mkdir(parents=True, exist_ok=True)
    writer = imageio_ffmpeg.write_frames(str(out), (w, h), fps=fps, codec="libx264", quality=8, macro_block_size=8,
                                         pix_fmt_in="rgb24", pix_fmt_out="yuv420p",
                                         output_params=["-movflags", "+faststart"])
    writer.send(None)
    frame = None
    for f in range(int(total * fps)):
        now = f / fps
        for r in art["rows"]:
            t0 = times[id(r)]
            on = now >= t0
            for a in (r["dot"], r["label"], r["tag"]):
                if a is not None:
                    a.set_visible(on)
            if on:  # a short pop: lands at 1.8x its size, settles in 0.25 s
                u = min((now - t0) / 0.25, 1)
                r["dot"].set_sizes([base[id(r)] * (1.8 - 0.8 * u * u)])
        for a in art["avg"]:
            a.set_visible(now >= t_avg)
        for a in note:
            a.set_visible(now >= t_note)
        s.fig.canvas.draw()
        frame = np.asarray(s.fig.canvas.buffer_rgba())[:, :, :3]
        writer.send(np.ascontiguousarray(frame))
    writer.close()
    cover = out.with_name("reel-cover.jpg")
    Image.fromarray(frame).save(cover, quality=92, subsampling=0)
    plt.close(s.fig)
    meta_path = out.with_name("meta.json")  # tells buffer.py to send the Reel to Instagram and X
    meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
    meta_path.write_text(json.dumps(meta | {"reel": True}, indent=1, ensure_ascii=False), encoding="utf-8")
    return {"video": out, "cover": cover, "seconds": round(total, 1)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date")
    ap.add_argument("--polls", type=Path, required=True)
    ap.add_argument("--candidates", action="store_true")
    ap.add_argument("--reel", action="store_true")
    a = ap.parse_args()
    if a.candidates:
        print(candidates(a.polls).head(25).to_string())
        return
    out, problems = build(a.date, a.polls)
    print(out, "; ".join(problems) or "all rules pass")
    if a.reel:
        print(reel(a.date, a.polls))


if __name__ == "__main__":
    main()
