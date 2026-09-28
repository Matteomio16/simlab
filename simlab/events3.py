"""More real events with measured opinion shifts (events3), so Kev react-v2 sees far more than events2's 26.

react-v1 learned its 26 training events almost perfectly (0.96 on new personas) but couldn't generalise to the 19
held-out events: too few distinct events. This adds 2001-2016 and campaign events, measured by events2's fixed rule
(`events2.shift` / `shift_detrended`: days +5..+14 after vs -7..-1 before, and the same against the pre-event trend) on:
- Gallup presidential approval (Bush 2001-09, Obama 2009-17; American Presidency Project, UCSB, from Gallup), one
  large pollster: readings are placed at their field midpoints and interpolated to days. Toward D = -change for Bush,
  +change for Obama.
- National presidential polls 2008-2024 (Wikipedia "Nationwide opinion polling" pages, pinned revisions, CC BY-SA):
  the D-R margin, averaged with events2's rule (latest poll per pollster in 14 days, weighted by sqrt of sample size).
Noise: the same statistic on every third day more than 21 days from any event, per series. Nothing within 14 days of a
held-out test event (events.json) is allowed; events within 14 days of each other, or of an events2 event, are
flagged as confounded. Descriptions say what happened, never how people reacted.

Downloaded with Matteo's OK (28 Sep 2026) into data/history/: ucsb_gallup_{obama,bush}.html and
wiki_polls_president_{2008,2012,2016,2020,2024}.json (API JSON with revision ids).

    python -m simlab.events3        # -> simlab/events3.json
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

from .events2 import EVENTS2, HIST, _avg, shift, shift_detrended

HERE = Path(__file__).parent
MONTHS = {m: i for i, m in enumerate(["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov",
                                      "dec"], start=1)}
# year: (Democratic nominee, Republican nominee, table indices on the pinned page)
CYCLES = {2008: ("Obama", "McCain", (0, 4)), 2012: ("Obama", "Romney", (0, 4)), 2016: ("Clinton", "Trump", (1, 2, 3)),
          2020: ("Biden", "Trump", (3, 4, 5, 6, 7)), 2024: ("Harris", "Trump", (2,))}
BIDEN_2024 = (12, 13)   # Biden vs Trump tables on the 2024 page, for events before 21 Jul 2024

# id, date, event type, series ("gallup" = presidential approval, "polls" = national presidential vote margin),
# neutral description (what happened, no reaction or poll information)
EVENTS3 = [
    ("sept11_attacks", "2001-09-11", "security", "gallup", "Hijackers crashed passenger planes into the World Trade Center and the Pentagon, killing nearly 3,000 people; a fourth plane crashed in Pennsylvania."),
    ("afghanistan_strikes", "2001-10-07", "security", "gallup", "The United States and Britain began air strikes on Taliban and al-Qaeda targets in Afghanistan."),
    ("enron_bankruptcy", "2001-12-02", "economy", "gallup", "The energy company Enron filed for bankruptcy after disclosures of accounting fraud, the largest corporate bankruptcy in U.S. history at the time."),
    ("axis_of_evil", "2002-01-29", "security", "gallup", "In his State of the Union address, President Bush called Iran, Iraq and North Korea an 'axis of evil'."),
    ("homeland_security_plan", "2002-06-06", "policy_court", "gallup", "President Bush proposed a new cabinet-level Department of Homeland Security combining parts of more than 20 agencies."),
    ("worldcom_fraud", "2002-06-25", "economy", "gallup", "The telecom company WorldCom disclosed that it had improperly booked nearly $4 billion of expenses."),
    ("iraq_war_resolution", "2002-10-10", "security", "gallup", "Congress passed a resolution authorizing President Bush to use military force against Iraq."),
    ("midterms_2002", "2002-11-05", "election", "gallup", "Republicans gained seats in both chambers in the midterm elections and won control of the Senate."),
    ("columbia_disaster", "2003-02-01", "shock_crisis", "gallup", "The Space Shuttle Columbia broke apart during re-entry over Texas, killing all seven astronauts."),
    ("powell_un_speech", "2003-02-05", "security", "gallup", "Secretary of State Colin Powell presented the administration's case to the UN Security Council that Iraq had weapons of mass destruction."),
    ("iraq_invasion", "2003-03-20", "security", "gallup", "U.S.-led forces invaded Iraq after an ultimatum to Saddam Hussein expired."),
    ("baghdad_falls", "2003-04-09", "security", "gallup", "U.S. forces took control of Baghdad, and a statue of Saddam Hussein was pulled down in Firdos Square."),
    ("mission_accomplished", "2003-05-01", "security", "gallup", "Aboard an aircraft carrier under a 'Mission Accomplished' banner, President Bush announced the end of major combat operations in Iraq."),
    ("saddam_captured", "2003-12-14", "security", "gallup", "The U.S. announced that its forces had captured former Iraqi leader Saddam Hussein near Tikrit."),
    ("abu_ghraib", "2004-04-28", "scandal_legal", "gallup", "Photographs of U.S. soldiers abusing Iraqi detainees at Abu Ghraib prison were broadcast on television."),
    ("bush_reelected", "2004-11-02", "election", "gallup", "President Bush won re-election over John Kerry, and Republicans gained seats in the House and Senate."),
    ("schiavo_law", "2005-03-21", "policy_court", "gallup", "President Bush signed a law passed by Congress to move the Terri Schiavo feeding-tube case to federal court."),
    ("katrina", "2005-08-29", "shock_crisis", "gallup", "Hurricane Katrina struck the Gulf Coast; levee failures flooded most of New Orleans, and thousands waited days for rescue and supplies."),
    ("miers_nomination", "2005-10-03", "policy_court", "gallup", "President Bush nominated White House counsel Harriet Miers to the Supreme Court."),
    ("libby_indicted", "2005-10-28", "scandal_legal", "gallup", "Scooter Libby, Vice President Cheney's chief of staff, was indicted for perjury and obstruction of justice in the CIA leak investigation."),
    ("cheney_hunting_accident", "2006-02-12", "scandal_legal", "gallup", "It was disclosed that Vice President Cheney had accidentally shot a companion during a quail hunt in Texas."),
    ("dubai_ports", "2006-02-21", "policy_court", "gallup", "President Bush threatened to veto any bill blocking a deal letting a Dubai state-owned company run operations at six major U.S. ports."),
    ("zarqawi_killed", "2006-06-08", "security", "gallup", "The U.S. announced that an airstrike had killed Abu Musab al-Zarqawi, the leader of al-Qaeda in Iraq."),
    ("foley_scandal", "2006-09-29", "scandal_legal", "gallup", "Republican Congressman Mark Foley resigned after sexually explicit messages he sent to teenage congressional pages became public."),
    ("midterms_2006", "2006-11-07", "election", "gallup", "Democrats won control of the House and the Senate in the midterm elections; Defense Secretary Donald Rumsfeld resigned the next day."),
    ("iraq_surge", "2007-01-10", "security", "gallup", "President Bush announced that more than 20,000 additional U.S. troops would be sent to Iraq."),
    ("walter_reed", "2007-02-18", "scandal_legal", "gallup", "Reports described neglect and poor living conditions for wounded soldiers at Walter Reed Army Medical Center."),
    ("virginia_tech", "2007-04-16", "shock_crisis", "gallup", "A gunman killed 32 people at Virginia Tech, then the deadliest shooting by a single gunman in U.S. history."),
    ("libby_commuted", "2007-07-02", "scandal_legal", "gallup", "President Bush commuted Scooter Libby's 30-month prison sentence."),
    ("bear_stearns", "2008-03-16", "economy", "gallup", "The investment bank Bear Stearns collapsed and was sold to JPMorgan Chase in a deal backed by the Federal Reserve."),
    ("obama_race_speech", "2008-03-18", "other", "polls", "Barack Obama gave a speech on race in America after controversy over sermons by his former pastor, Jeremiah Wright."),
    ("obama_clinches", "2008-06-03", "election", "polls", "Barack Obama secured enough delegates to win the Democratic presidential nomination after the final primaries."),
    ("obama_berlin_speech", "2008-07-24", "other", "polls", "Barack Obama spoke to a crowd of about 200,000 people in Berlin during a foreign tour."),
    ("biden_pick_2008", "2008-08-23", "election", "polls", "Barack Obama chose Senator Joe Biden as his running mate."),
    ("dnc_2008", "2008-08-28", "election", "polls", "Barack Obama accepted the Democratic nomination in a stadium speech in Denver."),
    ("palin_pick", "2008-08-29", "election", "polls", "John McCain chose Alaska Governor Sarah Palin as his running mate."),
    ("rnc_2008", "2008-09-04", "election", "polls", "John McCain accepted the Republican nomination at the party's convention in St. Paul."),
    ("lehman_collapse", "2008-09-15", "economy", "polls", "The investment bank Lehman Brothers filed for bankruptcy and stock markets fell sharply; the government took over the insurer AIG the next day."),
    ("mccain_suspends", "2008-09-24", "election", "polls", "John McCain announced he was suspending his campaign to return to Washington for negotiations on a financial rescue."),
    ("first_debate_2008", "2008-09-26", "debate", "polls", "Barack Obama and John McCain held their first presidential debate, on foreign policy and the economy."),
    ("vp_debate_2008", "2008-10-02", "debate", "polls", "Joe Biden and Sarah Palin held the vice-presidential debate."),
    ("tarp_signed", "2008-10-03", "economy", "polls", "Congress passed the $700 billion Troubled Asset Relief Program to rescue the banks, and President Bush signed it."),
    ("second_debate_2008", "2008-10-07", "debate", "polls", "Barack Obama and John McCain held a town-hall presidential debate."),
    ("third_debate_2008", "2008-10-15", "debate", "polls", "Barack Obama and John McCain held their third and final presidential debate."),
    ("powell_endorses_obama", "2008-10-19", "election", "polls", "Former Republican Secretary of State Colin Powell endorsed Barack Obama."),
    ("stimulus_signed", "2009-02-17", "policy_court", "gallup", "President Obama signed the $787 billion American Recovery and Reinvestment Act, passed with almost no Republican votes."),
    ("sotomayor_nominated", "2009-05-26", "policy_court", "gallup", "President Obama nominated appeals judge Sonia Sotomayor to the Supreme Court."),
    ("gm_bankruptcy", "2009-06-01", "economy", "gallup", "General Motors filed for bankruptcy in a government-led restructuring that left the federal government its majority owner."),
    ("gates_arrest_remarks", "2009-07-22", "other", "gallup", "At a news conference, President Obama said Cambridge police 'acted stupidly' in arresting Harvard professor Henry Louis Gates at his home."),
    ("health_care_speech", "2009-09-09", "policy_court", "gallup", "President Obama addressed a joint session of Congress on health care reform; Representative Joe Wilson shouted 'You lie!' during the speech."),
    ("nobel_prize", "2009-10-09", "other", "gallup", "President Obama was awarded the Nobel Peace Prize less than nine months into his presidency."),
    ("fort_hood", "2009-11-05", "security", "gallup", "An Army psychiatrist killed 13 people in a shooting at Fort Hood, Texas."),
    ("afghan_surge", "2009-12-01", "security", "gallup", "President Obama announced that 30,000 more U.S. troops would go to Afghanistan, with withdrawals to begin in 2011."),
    ("underwear_bomber", "2009-12-25", "security", "gallup", "A man tried to detonate explosives hidden in his underwear on a flight to Detroit before passengers subdued him."),
    ("scott_brown_wins", "2010-01-19", "election", "gallup", "Republican Scott Brown won the Massachusetts Senate special election for Ted Kennedy's former seat, ending the Democrats' 60-seat majority."),
    ("aca_passes", "2010-03-21", "policy_court", "gallup", "The House passed the Affordable Care Act 219-212 with no Republican votes; President Obama signed it two days later."),
    ("deepwater_horizon", "2010-04-20", "shock_crisis", "gallup", "The Deepwater Horizon oil rig exploded in the Gulf of Mexico, killing 11 workers and starting the largest marine oil spill in U.S. history."),
    ("midterms_2010", "2010-11-02", "election", "gallup", "Republicans gained 63 House seats and took control of the House in the midterm elections."),
    ("tucson_shooting", "2011-01-08", "shock_crisis", "gallup", "A gunman shot Representative Gabrielle Giffords and 18 others at a constituent event in Tucson, killing six."),
    ("bin_laden_killed", "2011-05-02", "security", "gallup", "President Obama announced that U.S. special forces had killed Osama bin Laden in Pakistan."),
    ("debt_ceiling_downgrade", "2011-08-02", "economy", "gallup", "After weeks of standoff, Congress raised the debt ceiling hours before a possible default; three days later S&P downgraded the U.S. credit rating for the first time."),
    ("gaddafi_killed", "2011-10-20", "security", "gallup", "Libyan leader Muammar Gaddafi was killed by rebel fighters after a NATO-backed campaign."),
    ("trayvon_remarks", "2012-03-23", "shock_crisis", "gallup", "President Obama spoke about the killing of Trayvon Martin, an unarmed Black teenager shot in Florida by a man who had not been charged."),
    ("obama_backs_marriage", "2012-05-09", "policy_court", "polls", "President Obama said he supports same-sex marriage, the first sitting president to do so."),
    ("daca_announced", "2012-06-15", "policy_court", "polls", "President Obama announced a policy to stop deporting some undocumented immigrants brought to the U.S. as children."),
    ("aca_upheld", "2012-06-28", "policy_court", "polls", "The Supreme Court upheld most of the Affordable Care Act, including the individual mandate, 5-4."),
    ("ryan_pick", "2012-08-11", "election", "polls", "Mitt Romney chose Representative Paul Ryan as his running mate."),
    ("rnc_2012", "2012-08-30", "election", "polls", "Mitt Romney accepted the Republican nomination at the party's convention in Tampa."),
    ("dnc_2012", "2012-09-06", "election", "polls", "Barack Obama accepted the Democratic nomination at the party's convention in Charlotte."),
    ("benghazi_attack", "2012-09-11", "security", "polls", "Attackers stormed the U.S. diplomatic compound in Benghazi, Libya, killing Ambassador Chris Stevens and three other Americans."),
    ("romney_47_percent", "2012-09-17", "scandal_legal", "polls", "A secretly recorded video showed Mitt Romney telling donors that 47 percent of Americans are dependent on government and will vote for Obama no matter what."),
    ("third_debate_2012", "2012-10-22", "debate", "polls", "Barack Obama and Mitt Romney held their third and final debate, on foreign policy."),
    ("hurricane_sandy", "2012-10-29", "shock_crisis", "polls", "Hurricane Sandy struck the Northeast, killing dozens and flooding parts of New York and New Jersey; President Obama and New Jersey Governor Chris Christie toured the damage together."),
    ("sandy_hook", "2012-12-14", "shock_crisis", "gallup", "A gunman killed 20 children and six staff members at Sandy Hook Elementary School in Newtown, Connecticut."),
    ("fiscal_cliff_deal", "2013-01-01", "economy", "gallup", "Congress passed a last-minute deal averting the 'fiscal cliff', raising taxes on high earners and delaying automatic spending cuts."),
    ("boston_bombing", "2013-04-15", "security", "gallup", "Two bombs exploded near the finish line of the Boston Marathon, killing three people and injuring hundreds."),
    ("irs_targeting", "2013-05-10", "scandal_legal", "gallup", "The IRS acknowledged that it had singled out conservative groups applying for tax-exempt status for extra scrutiny."),
    ("snowden_leaks", "2013-06-06", "scandal_legal", "gallup", "Leaked documents revealed that the National Security Agency was collecting the phone records of millions of Americans."),
    ("zimmerman_acquitted", "2013-07-13", "shock_crisis", "gallup", "A Florida jury acquitted George Zimmerman in the killing of Trayvon Martin."),
    ("syria_congress_vote", "2013-08-31", "security", "gallup", "After a chemical weapons attack near Damascus, President Obama said he would ask Congress to authorize military strikes on Syria."),
    ("shutdown_2013", "2013-10-01", "shock_crisis", "gallup", "The federal government shut down for 16 days over Republican demands to defund the Affordable Care Act; the same day, the HealthCare.gov website launched with widespread technical failures."),
    ("plan_cancellations", "2013-10-29", "policy_court", "gallup", "Millions of people received cancellation notices for individual health plans that did not meet the Affordable Care Act's standards, despite the president's earlier promise that people could keep their plans."),
    ("crimea_annexation", "2014-03-18", "security", "gallup", "Russia formally annexed Crimea after seizing the peninsula from Ukraine and holding a disputed referendum."),
    ("va_scandal", "2014-05-30", "scandal_legal", "gallup", "Veterans Affairs Secretary Eric Shinseki resigned after reports that VA hospitals kept secret waiting lists and veterans died waiting for care."),
    ("bergdahl_swap", "2014-05-31", "security", "gallup", "The U.S. freed five Taliban detainees held at Guantanamo in exchange for Army Sergeant Bowe Bergdahl, held captive in Afghanistan for five years."),
    ("ferguson", "2014-08-09", "shock_crisis", "gallup", "A police officer shot and killed Michael Brown, an unarmed Black 18-year-old, in Ferguson, Missouri, followed by protests and a heavily armed police response."),
    ("isis_foley_video", "2014-08-19", "security", "gallup", "ISIS released a video showing the beheading of the American journalist James Foley."),
    ("ebola_us_case", "2014-09-30", "shock_crisis", "gallup", "The first case of Ebola diagnosed in the United States was confirmed in Dallas."),
    ("midterms_2014", "2014-11-04", "election", "gallup", "Republicans won control of the Senate and expanded their House majority in the midterm elections."),
    ("immigration_action", "2014-11-20", "policy_court", "gallup", "President Obama announced executive actions shielding about four million undocumented immigrants from deportation."),
    ("baltimore_unrest", "2015-04-27", "shock_crisis", "gallup", "Protests over the death of Freddie Gray in police custody turned into riots in Baltimore, and the governor declared a state of emergency."),
    ("charleston_shooting", "2015-06-17", "shock_crisis", "gallup", "A white supremacist killed nine Black worshippers at Emanuel AME Church in Charleston, South Carolina."),
    ("obergefell", "2015-06-26", "policy_court", "gallup", "The Supreme Court ruled that same-sex couples have a constitutional right to marry, a day after upholding Affordable Care Act subsidies."),
    ("iran_deal", "2015-07-14", "security", "gallup", "The U.S. and five other world powers reached a deal with Iran limiting its nuclear program in exchange for sanctions relief."),
    ("paris_attacks", "2015-11-13", "security", "gallup", "Coordinated ISIS attacks in Paris killed 130 people."),
    ("san_bernardino", "2015-12-02", "security", "gallup", "A married couple inspired by ISIS killed 14 people at a holiday party in San Bernardino, California."),
    ("scalia_dies", "2016-02-13", "policy_court", "gallup", "Supreme Court Justice Antonin Scalia died; Senate Republican leaders said they would not consider any nominee until after the election."),
    ("garland_nominated", "2016-03-16", "policy_court", "gallup", "President Obama nominated Judge Merrick Garland to the Supreme Court."),
    ("trump_presumptive", "2016-05-03", "election", "polls", "Donald Trump became the presumptive Republican nominee after winning the Indiana primary, as his remaining rivals withdrew."),
    ("pulse_shooting", "2016-06-12", "security", "polls", "A gunman who pledged allegiance to ISIS killed 49 people at the Pulse nightclub in Orlando."),
    ("comey_no_charges", "2016-07-05", "scandal_legal", "polls", "FBI Director James Comey said Hillary Clinton had been 'extremely careless' with classified email but recommended no charges."),
    ("dallas_police_shooting", "2016-07-07", "shock_crisis", "polls", "A gunman killed five police officers during a protest march in Dallas."),
    ("rnc_2016", "2016-07-21", "election", "polls", "Donald Trump accepted the Republican nomination at the party's convention in Cleveland."),
    ("dnc_2016", "2016-07-28", "election", "polls", "Hillary Clinton accepted the Democratic nomination in Philadelphia, the first woman nominated by a major party."),
    ("clinton_deplorables_illness", "2016-09-11", "scandal_legal", "polls", "Hillary Clinton left a 9/11 memorial ceremony feeling unwell and was said to have pneumonia; two days earlier she had called half of Donald Trump's supporters a 'basket of deplorables'."),
    ("final_debate_2020", "2020-10-22", "debate", "polls", "Joe Biden and Donald Trump held their second and final presidential debate."),
    ("sotu_2024", "2024-03-07", "other", "polls", "President Biden delivered his State of the Union address."),
    ("trump_trial_opens", "2024-04-15", "scandal_legal", "polls", "Jury selection began in Donald Trump's New York criminal trial over hush-money payments."),
    ("walz_pick", "2024-08-06", "election", "polls", "Kamala Harris chose Minnesota Governor Tim Walz as her running mate."),
    ("dnc_2024", "2024-08-22", "election", "polls", "Kamala Harris accepted the Democratic nomination at the party's convention in Chicago."),
    ("vp_debate_2024", "2024-10-01", "debate", "polls", "JD Vance and Tim Walz held the vice-presidential debate."),
    ("msg_rally", "2024-10-27", "scandal_legal", "polls", "At a Donald Trump rally at Madison Square Garden, a comedian called Puerto Rico a 'floating island of garbage'."),
]


def gallup() -> pd.DataFrame:
    """Daily approve % with the president's party, from the UCSB Gallup tables: each day is the mean of the readings
    whose field midpoint falls in the previous 14 days, the one-pollster analogue of events2's poll average. Bush-era
    readings came every 10 days on average, so a single noisy reading would otherwise pass for an event's effect
    (Katrina: 45, 45, 40, 45, 46)."""
    out = []
    for who, party in (("bush", "R"), ("obama", "D")):
        html = (HIST / f"ucsb_gallup_{who}.html").read_text(encoding="utf-8", errors="replace")
        for row in re.findall(r"<tr[^>]*>(.*?)</tr>", html, re.S):
            cells = [re.sub(r"<[^>]+>|&nbsp;", " ", c).strip() for c in re.findall(r"<td[^>]*>(.*?)</td>", row, re.S)]
            if len(cells) >= 3 and re.match(r"\d\d/\d\d/\d{4}", cells[0]) and cells[2].isdigit():
                a, b = pd.to_datetime(cells[0]), pd.to_datetime(cells[1])
                out.append({"date": a + (b - a) / 2, "approve": float(cells[2]), "party": party})
    d = pd.DataFrame(out).groupby("date").agg(approve=("approve", "mean"), party=("party", "first")).sort_index()
    days = pd.date_range(d.index.min().normalize() + pd.Timedelta(days=14), d.index.max().normalize())
    mid = d.index.values
    s = pd.Series([d.approve.values[(mid > t - np.timedelta64(14, "D")) & (mid <= t)].mean()
                   if ((mid > t - np.timedelta64(14, "D")) & (mid <= t)).any() else np.nan for t in days.values],
                  index=days)
    return pd.DataFrame({"approve": s, "party": d.party.reindex(days, method="ffill")}).dropna()


def _clean(cell: str) -> str:
    cell = re.sub(r"<ref[^>]*/>|<ref[^>]*>.*?</ref>", "", cell, flags=re.S)
    cell = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]", r"\1", cell)
    while re.search(r"\{\{[^{}]*\}\}", cell):
        cell = re.sub(r"\{\{[^{}]*\}\}", "", cell)
    return re.sub(r"<[^>]+>|'''|''|&nbsp;", " ", cell)


def _cells(line: str) -> list[tuple[str, int]]:
    """A wikitext row line -> [(text, rowspan)]. The attribute part (before a single '|') is dropped but read for
    rowspan and data-sort-value, which some tables use to hold the full end date."""
    out = []
    for raw in re.split(r"\|\||!!", line):
        raw = raw.strip()
        attrs, text = "", raw
        m = re.match(r"^((?:[a-z-]+\s*=\s*(?:\"[^\"]*\"|'[^']*'|[^\s|]+)\s*|\{\{party shading/[^}]*\}\}\s*)+)\|(?!\|)(.*)$",
                     raw, re.S)
        if m:
            attrs, text = m.group(1), m.group(2)
        span = int(re.search(r"rowspan\s*=\s*\"?(\d+)", attrs).group(1)) if "rowspan" in attrs else 1
        sort = re.search(r"data-sort-value\s*=\s*\"([^\"]+)\"", attrs)
        out.append((((sort.group(1) + " ") if sort else "") + " ".join(_clean(text).split()), span))
    return out


def _table_rows(seg: str) -> tuple[list[str], list[list[str]]]:
    """Header texts and data rows of one wikitable, with row-spanning cells repeated."""
    header, rows, pending = [], [], {}
    for part in seg.split("\n|-")[0:]:
        lines = [ln for ln in part.split("\n") if ln.startswith(("|", "!")) and not ln.startswith(("|}", "|+", "{|"))]
        if not lines:
            continue
        if all(ln.startswith("!") for ln in lines) and not header:
            header = [t for ln in lines for t, _ in _cells(ln[1:])]
            continue
        cells, col = [], 0
        for ln in lines:
            for text, span in _cells(ln[1:]):
                while col in pending:
                    text_p, left = pending[col]
                    cells.append(text_p)
                    pending[col] = (text_p, left - 1) if left > 1 else None
                    if pending[col] is None:
                        del pending[col]
                    col += 1
                cells.append(text)
                if span > 1:
                    pending[col] = (text, span - 1)
                col += 1
        while col in pending:
            text_p, left = pending[col]
            cells.append(text_p)
            if left > 1:
                pending[col] = (text_p, left - 1)
            else:
                del pending[col]
            col += 1
        rows.append(cells)
    return header, rows


def _end_date(text: str, year: int) -> pd.Timestamp | None:
    """End of a field period: 'November 1–3, 2008', 'Oct 31 – Nov 2', 'October 30–November 1, 2008'; a leading
    data-sort-value date wins."""
    m = re.match(r"([A-Z][a-z]+) (\d{1,2}), (\d{4})", text)
    if m and m.group(1)[:3].lower() in MONTHS:
        return pd.Timestamp(int(m.group(3)), MONTHS[m.group(1)[:3].lower()], int(m.group(2)))
    y = re.findall(r"\b(20\d\d)\b", text)
    year = int(y[-1]) if y else year
    parts = re.split(r"\s*[–—-]\s*", re.sub(r",?\s*20\d\d", "", text).strip())
    last, month = parts[-1], None
    for p in parts:
        mm = re.match(r"([A-Za-z]+)\.?\s*(\d{1,2})?", p)
        if mm and mm.group(1)[:3].lower() in MONTHS:
            month = MONTHS[mm.group(1)[:3].lower()]
    day = re.findall(r"(\d{1,2})\s*$", last)
    if month is None or not day:
        return None
    try:
        return pd.Timestamp(year, month, int(day[0]))
    except ValueError:
        return None


def _num(text: str) -> float:
    m = re.search(r"(\d+(?:\.\d+)?)", text.replace(",", ""))
    return float(m.group(1)) if m else np.nan


def polls(year: int, dem: str | None = None, rep: str | None = None, tables: tuple | None = None) -> pd.DataFrame:
    """National polls of one cycle: end date, pollster, sample size and D-R margin."""
    d0, r0, idx = CYCLES[year]
    dem, rep, idx = dem or d0, rep or r0, tables or idx
    page = json.loads((HIST / f"wiki_polls_president_{year}.json").read_text(encoding="utf-8"))
    text = page["revisions"][0]["slots"]["main"]["content"]
    starts = [m.start() for m in re.finditer(r"^\{\|", text, re.M)]
    out = []
    for i in idx:
        header, rows = _table_rows(text[starts[i]:text.find("\n|}", starts[i])])
        low = [re.sub(r"\s+", "", h.lower()) for h in header]    # some headers lose the space where a <br /> was
        col = lambda *keys: next((j for j, h in enumerate(low) if any(k in h for k in keys)), None)
        src, date, n = col("pollsource", "pollingfirm", "source"), col("date"), col("sample")
        exact = lambda key: next((j for j, h in enumerate(low) if h == key), None)
        if col("democraticcandidate") is not None or exact("democrat") is not None:
            # 2012 style: name columns, each followed by a % column
            jd = col("democraticcandidate") if col("democraticcandidate") is not None else exact("democrat")
            jr = col("republicancandidate") if col("republicancandidate") is not None else exact("republican")
            named = True
        else:
            jd, jr, named = col(dem.lower()), col(rep.lower()), False
        if None in (src, date, jd, jr):
            continue
        for r in rows:
            if len(r) <= max(src, date, jd, jr) + (1 if named else 0):
                continue
            if named and not (dem in r[jd] and rep in r[jr]):
                continue
            pd_, pr_ = (_num(r[jd + 1]), _num(r[jr + 1])) if named else (_num(r[jd]), _num(r[jr]))
            end = _end_date(r[date], year)
            if (end is None or not pd.Timestamp(year - 2, 1, 1) <= end <= pd.Timestamp(year, 11, 8)
                    or not (15 <= pd_ <= 70 and 15 <= pr_ <= 70) or "election" in r[src].lower()):
                continue
            size = _num(r[n]) if n is not None and n < len(r) else np.nan
            out.append({"end": end, "pollster": re.split(r"\s*\(|/", r[src])[0].strip(), "n": size if size == size else 1000,
                        "margin": pd_ - pr_})
    return pd.DataFrame(out).drop_duplicates()


def build() -> list[dict]:
    test_dates = [pd.Timestamp(e["date"]) for e in json.loads((HERE / "events.json").read_text())]
    e2 = [(eid, pd.Timestamp(d)) for eid, d, *_ in EVENTS2]
    mine = [(eid, pd.Timestamp(d)) for eid, d, *_ in EVENTS3]
    g = gallup()
    margin = {y: _avg(polls(y), "margin") for y in CYCLES}
    margin["2024-biden"] = _avg(polls(2024, "Biden", "Trump", BIDEN_2024), "margin")

    def series(kind: str, d: pd.Timestamp) -> tuple[str, pd.Series, int]:
        if kind == "gallup":
            party = g.party.asof(d)
            return f"gallup-{'bush' if party == 'R' else 'obama'}", g.approve[g.party == party], -1 if party == "R" else 1
        key = "2024-biden" if d.year == 2024 and d < pd.Timestamp("2024-07-21") else d.year
        return f"polls-{key}", margin[key], 1

    avoid = [d for _, d in e2 + mine] + test_dates
    noise = {}
    for eid, date, etype, kind, text in EVENTS3:
        name, s, _ = series(kind, pd.Timestamp(date))
        if name not in noise:
            placebo = [v for t in s.index[::3] if min(abs((t - d).days) for d in avoid) > 21
                       for v in [shift(s, t)] if v == v]
            if len(placebo) < 20:   # a short series with events everywhere (Harris 2024): all days, events included
                placebo = [v for t in s.index[::3] for v in [shift(s, t)] if v == v]
            noise[name] = float(np.std(placebo))
    out = []
    for eid, date, etype, kind, text in EVENTS3:
        d = pd.Timestamp(date)
        if min(abs((d - t).days) for t in test_dates) < 14:
            raise ValueError(f"{eid} is within two weeks of a test event")
        name, s, sign = series(kind, d)
        val, tr = sign * shift(s, d), sign * shift_detrended(s, d)
        near = [e for e, dt in mine + e2 if e != eid and abs((dt - d).days) <= 14]
        measure = ("approval (Gallup" if kind == "gallup" else "margin (national presidential polls, D-R") + \
            "; days +5..+14 vs -7..-1)"
        out.append({"id": eid, "date": date, "event_type": etype, "measure": measure, "series": name,
                    "description": text, "shift_toward_D": round(val, 2) if val == val else None,
                    "shift_detrended": round(tr, 2) if tr == tr else None,
                    "z": round(val / noise[name], 2) if val == val else None,
                    "president_party": g.party.asof(d) if kind == "gallup" else None, "confounded_with": near})
    (HERE / "events3.json").write_text(json.dumps(out, indent=1))
    ok = [r for r in out if r["z"] is not None]
    clear = [r for r in ok if abs(r["z"]) >= 1 and r["shift_detrended"] is not None
             and r["shift_toward_D"] * r["shift_detrended"] > 0 and not r["confounded_with"]]
    print(f"{len(out)} events, {len(ok)} measured; noise SD by series: {({k: round(v, 2) for k, v in noise.items()})}")
    print(f"clear (|z| >= 1, detrended agrees, unconfounded): {len(clear)}; no change (|z| < 0.5): "
          f"{sum(abs(r['z']) < 0.5 for r in ok)}; confounded: {sum(bool(r['confounded_with']) for r in out)}")
    for r in out:
        print(f"  {r['date']} {r['id']:28} {r['series']:16} shift {r['shift_toward_D']!s:>6}  detr "
              f"{r['shift_detrended']!s:>6}  z {r['z']!s:>6}" + ("  confounded" if r["confounded_with"] else ""))
    return out


def check() -> None:
    for y in CYCLES:
        p = polls(y)
        print(y, len(p), "polls", p.end.min().date() if len(p) else None, "->", p.end.max().date() if len(p) else None,
              "final 2-week mean margin", round(p[p.end >= p.end.max() - pd.Timedelta(days=14)].margin.mean(), 1) if len(p) else None)
    b = polls(2024, "Biden", "Trump", BIDEN_2024)
    print("2024 Biden", len(b), b.end.min().date(), "->", b.end.max().date())
    g = gallup()
    print("gallup days", len(g), g.index.min().date(), "->", g.index.max().date(), g.approve.describe()[["min", "max"]].to_dict())


if __name__ == "__main__":
    import sys
    check() if sys.argv[1:] == ["check"] else build()
