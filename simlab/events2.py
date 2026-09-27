"""Real events with measured opinion shifts (events2): training data for Kev's reactions and scales per event type.

The 19 events in events.json stay the held-out test set; nothing here overlaps them (events within two weeks of a test
event are left out too). Every shift is measured by one fixed rule, never judged by hand:
    shift = mean of the daily average over days +5..+14 after the event - mean over days -7..-1 before it,
signed toward the Democrats (presidential approval: minus the change for a Republican president, plus for a Democrat;
generic ballot: change in the D-R margin). The same rule on every non-event day gives the noise level; |z| < 1.5 counts
as no measurable effect. Party shifts (D/R/I) come from Nationscape's weekly waves (Jul 2019 - Jan 2021).

Series (data/history/, see history.py): 538 approval averages (Trump 2017-21, Biden 2021-25) and our own 14-day average
of VoteHub polls for Trump from 2025; generic ballot from 538 polls (2017-22) and VoteHub (Dec 2024 on).

    python -m simlab.events2        # -> simlab/events2.json
"""
from __future__ import annotations

import glob
import json
from pathlib import Path

import numpy as np
import pandas as pd

from .ces import DATA

HIST = DATA / "history"
HERE = Path(__file__).parent

# id, date, event type, primary series, neutral description (what happened, no reaction or poll information)
EVENTS2 = [
    ("travel_ban", "2017-01-27", "policy_court", "approval", "President Trump signed an executive order suspending entry to the United States for citizens of seven Muslim-majority countries and pausing refugee admissions. Protests formed at several airports and federal judges blocked parts of the order within days."),
    ("comey_fired", "2017-05-09", "scandal_legal", "approval", "President Trump fired FBI Director James Comey, who was leading the bureau's investigation into Russian interference in the 2016 election. The White House first cited Comey's handling of the Clinton email inquiry."),
    ("aca_repeal_fails", "2017-07-28", "policy_court", "approval", "The Senate rejected a Republican bill to repeal parts of the Affordable Care Act by 51 to 49, with Senator John McCain casting the deciding vote against it. President Trump had made repeal a central promise."),
    ("charlottesville", "2017-08-15", "scandal_legal", "approval", "Days after a white nationalist rally in Charlottesville, Virginia, where a counter-protester was killed, President Trump said there were 'very fine people on both sides'. Several business leaders left White House advisory councils."),
    ("las_vegas_shooting", "2017-10-01", "shock_crisis", "approval", "A gunman firing from a Las Vegas hotel killed 58 people at an outdoor country music festival, the deadliest mass shooting in modern U.S. history."),
    ("tax_cuts_pass", "2017-12-20", "policy_court", "approval", "Congress passed the Tax Cuts and Jobs Act on party lines, cutting the corporate tax rate to 21 percent and lowering individual rates through 2025. President Trump signed it two days later."),
    ("shutdown_2018_jan", "2018-01-20", "shock_crisis", "approval", "The federal government shut down for three days after Senate Democrats and Republicans failed to agree on funding and protections for young immigrants brought to the U.S. as children."),
    ("parkland", "2018-02-14", "shock_crisis", "approval", "A former student killed 17 people at Marjory Stoneman Douglas High School in Parkland, Florida. Surviving students began a national campaign for stricter gun laws."),
    ("singapore_summit", "2018-06-12", "security", "approval", "President Trump met North Korean leader Kim Jong Un in Singapore, the first meeting between a sitting U.S. president and a North Korean leader. They signed a short statement on working toward denuclearization."),
    ("family_separation", "2018-06-18", "policy_court", "approval", "Audio recordings of crying children separated from their parents at the U.S.-Mexico border were published, under the administration's zero-tolerance prosecution policy. Two days later President Trump signed an order to keep families together."),
    ("helsinki_summit", "2018-07-16", "security", "approval", "At a press conference with Vladimir Putin in Helsinki, President Trump declined to endorse U.S. intelligence findings that Russia interfered in the 2016 election, citing Putin's denial."),
    ("cohen_manafort", "2018-08-21", "scandal_legal", "approval", "Trump's former lawyer Michael Cohen pleaded guilty to campaign finance violations, saying he acted at the candidate's direction, and former campaign chairman Paul Manafort was convicted of fraud on the same day."),
    ("kavanaugh_hearing", "2018-09-27", "policy_court", "generic", "Supreme Court nominee Brett Kavanaugh and Christine Blasey Ford, who accused him of sexual assault when they were teenagers, testified before the Senate Judiciary Committee."),
    ("pittsburgh_synagogue", "2018-10-27", "shock_crisis", "generic", "A gunman killed 11 worshippers at the Tree of Life synagogue in Pittsburgh, days after pipe bombs were mailed to prominent Democrats and critics of the president."),
    ("shutdown_2018_dec", "2018-12-22", "shock_crisis", "approval", "A partial government shutdown began after President Trump refused to sign funding without $5.7 billion for a border wall. It became the longest shutdown in U.S. history, lasting 35 days."),
    ("wall_emergency", "2019-02-15", "policy_court", "approval", "President Trump declared a national emergency at the southern border to redirect military funds to building a wall after Congress declined to fund it."),
    ("mueller_report", "2019-04-18", "scandal_legal", "approval", "The Justice Department released a redacted version of Special Counsel Robert Mueller's report, detailing contacts between the Trump campaign and Russia and ten episodes of possible obstruction of justice."),
    ("go_back_tweets", "2019-07-14", "scandal_legal", "approval", "President Trump posted that four Democratic congresswomen of color should 'go back' to the countries they came from. The House later voted to condemn the remarks as racist."),
    ("el_paso_dayton", "2019-08-03", "shock_crisis", "approval", "Mass shootings in El Paso, Texas, and Dayton, Ohio, killed 31 people within 13 hours. The El Paso gunman had posted a manifesto against Hispanic immigration."),
    ("baghdadi_killed", "2019-10-27", "security", "approval", "President Trump announced that ISIS leader Abu Bakr al-Baghdadi died during a U.S. special forces raid in northwestern Syria."),
    ("impeachment_hearings", "2019-11-13", "scandal_legal", "approval", "Public impeachment hearings began in the House Intelligence Committee, with diplomats testifying about the pressure on Ukraine to announce investigations of the Bidens."),
    ("house_impeaches", "2019-12-18", "scandal_legal", "approval", "The House of Representatives impeached President Trump on charges of abuse of power and obstruction of Congress, largely along party lines."),
    ("soleimani_strike", "2020-01-03", "security", "approval", "A U.S. drone strike ordered by President Trump killed Iranian general Qassem Soleimani at Baghdad's airport. Iran fired missiles at U.S. bases in Iraq five days later."),
    ("senate_acquits", "2020-02-05", "scandal_legal", "approval", "The Senate acquitted President Trump on both articles of impeachment. Senator Mitt Romney was the only Republican to vote to convict on one article."),
    ("disinfectant_remarks", "2020-04-23", "scandal_legal", "approval", "At a coronavirus briefing, President Trump suggested researchers look into injecting disinfectant into the body to treat the virus. Manufacturers issued warnings against doing so."),
    ("george_floyd", "2020-05-25", "shock_crisis", "approval", "George Floyd, a Black man, died after a Minneapolis police officer knelt on his neck for more than nine minutes. Protests spread to hundreds of cities; on June 1 federal police cleared protesters near the White House."),
    ("rbg_dies", "2020-09-18", "policy_court", "approval", "Supreme Court Justice Ruth Bader Ginsburg died. President Trump and Senate Republicans said they would fill the seat before the November election."),
    ("first_debate_2020", "2020-09-29", "debate", "approval", "President Trump and Joe Biden met in Cleveland for their first debate, which was marked by constant interruptions, most of them by Trump. Asked to condemn white supremacist groups, Trump told the Proud Boys to 'stand back and stand by'."),
    ("trump_covid", "2020-10-02", "shock_crisis", "approval", "President Trump announced that he had tested positive for COVID-19. He was flown to Walter Reed hospital that evening and returned to the White House three days later."),
    ("rescue_plan", "2021-03-11", "policy_court", "approval", "President Biden signed the $1.9 trillion American Rescue Plan, including $1,400 payments to most Americans, passed without Republican votes."),
    ("infrastructure_law", "2021-11-15", "policy_court", "approval", "President Biden signed a $1.2 trillion bipartisan infrastructure law funding roads, bridges, broadband and water systems."),
    ("ukraine_invasion", "2022-02-24", "security", "approval", "Russia launched a full-scale invasion of Ukraine. The United States and its allies imposed sweeping sanctions and began sending weapons to Ukraine."),
    ("dobbs_leak", "2022-05-02", "policy_court", "generic", "Politico published a leaked draft Supreme Court opinion that would overturn Roe v. Wade. Chief Justice Roberts confirmed the draft was authentic."),
    ("uvalde", "2022-05-24", "shock_crisis", "approval", "A gunman killed 19 children and two teachers at an elementary school in Uvalde, Texas. Police waited more than an hour before entering the classroom."),
    ("inflation_peak_cpi", "2022-06-10", "economy", "approval", "The government reported that consumer prices rose 8.6 percent over the past year, the fastest pace since 1981, and the national average gasoline price passed $5 a gallon days later."),
    ("maralago_search", "2022-08-08", "scandal_legal", "generic", "FBI agents executed a search warrant at former President Trump's Mar-a-Lago home, seeking classified documents taken from the White House."),
    ("ira_signed", "2022-08-16", "policy_court", "approval", "President Biden signed the Inflation Reduction Act, with climate and clean-energy spending, Medicare drug price negotiation and a minimum corporate tax."),
    ("student_loans", "2022-08-24", "policy_court", "approval", "President Biden announced cancellation of up to $10,000 in federal student loan debt for most borrowers, and up to $20,000 for Pell Grant recipients."),
    ("biden_documents", "2023-01-12", "scandal_legal", "approval", "Attorney General Merrick Garland appointed a special counsel to investigate classified documents found at President Biden's former office and his Delaware home."),
    ("svb_collapse", "2023-03-10", "economy", "approval", "Silicon Valley Bank collapsed after a run on deposits, the second-largest bank failure in U.S. history. Regulators guaranteed all its deposits two days later."),
    ("trump_ny_indictment", "2023-03-30", "scandal_legal", "generic", "A Manhattan grand jury indicted former President Trump on charges related to hush money paid to an adult film actress before the 2016 election, the first criminal charges against a former president."),
    ("hamas_attack", "2023-10-07", "security", "approval", "Hamas fighters attacked Israel from Gaza, killing about 1,200 people and taking more than 240 hostages. Israel declared war and began bombing Gaza."),
    ("zelensky_oval_office", "2025-02-28", "security", "approval", "A White House meeting between President Trump, Vice President Vance and Ukrainian President Zelensky broke down in a public argument in the Oval Office, and a planned minerals agreement was not signed."),
    ("la_guard_deployment", "2025-06-07", "policy_court", "approval", "President Trump federalized the California National Guard and sent troops to Los Angeles over protests against immigration raids, over the objections of the state's governor."),
    ("iran_nuclear_strikes", "2025-06-21", "security", "approval", "U.S. aircraft bombed three Iranian nuclear sites, including the underground facility at Fordow. Iran fired missiles at a U.S. base in Qatar two days later, and a ceasefire with Israel followed."),
    ("nov_2025_elections", "2025-11-04", "election", "generic", "Democrats won the governor's races in Virginia and New Jersey by wide margins, and Zohran Mamdani was elected mayor of New York City."),
]


def _avg(polls: pd.DataFrame, value: str, days: int = 14) -> pd.Series:
    """Daily average of poll values ending within the last `days` days: latest poll per pollster in the window,
    weighted by sqrt(sample size)."""
    polls = polls.dropna(subset=[value]).sort_values("end")
    out = {}
    for t in pd.date_range(polls.end.min() + pd.Timedelta(days=days), polls.end.max()):
        w = polls[(polls.end > t - pd.Timedelta(days=days)) & (polls.end <= t)].drop_duplicates("pollster", keep="last")
        if len(w) >= 3:
            out[t] = np.average(w[value], weights=np.sqrt(w.n.clip(100, 5000)))
    return pd.Series(out)


def approval() -> pd.DataFrame:
    """Daily approve % of the sitting president, with the president's party."""
    t1 = pd.read_csv(HIST / "538_trump1_approval_topline.csv")
    t1 = t1[t1.subgroup == "All polls"].assign(date=lambda d: pd.to_datetime(d.modeldate, format="%m/%d/%Y"))
    b = pd.read_csv(HIST / "538_biden_approval_topline.csv")
    b = b[b.subgroup == "All polls"].assign(date=lambda d: pd.to_datetime(d.end_date))
    vh = pd.DataFrame([{"end": pd.Timestamp(p["end_date"]), "pollster": p["pollster"], "n": p.get("sample_size") or 1000,
                        "approve": next((a["pct"] for a in p["answers"] if a["choice"] == "Approve"), np.nan)}
                       for p in json.loads((HIST / "votehub_approval.json").read_text())
                       if p.get("subject") == "Donald Trump" and p.get("end_date", "") >= "2025-01-20"])
    t2 = _avg(vh, "approve")
    rows = [pd.DataFrame({"date": t1.date, "approve": t1.approve_estimate, "party": "R"}),
            pd.DataFrame({"date": b.date, "approve": b.approve_estimate, "party": "D"}),
            pd.DataFrame({"date": t2.index, "approve": t2.values, "party": "R"})]
    return pd.concat(rows).drop_duplicates("date").set_index("date").sort_index()


def generic() -> pd.Series:
    """Daily D-R generic-ballot margin."""
    h = pd.read_csv(HIST / "538_generic_ballot_polls_historical.csv", low_memory=False)
    h = pd.DataFrame({"end": pd.to_datetime(h.end_date, format="%m/%d/%y"), "pollster": h.pollster,
                      "n": h.sample_size.fillna(1000), "margin": h.dem - h.rep})
    vh = pd.DataFrame([{"end": pd.Timestamp(p["end_date"]), "pollster": p["pollster"], "n": p.get("sample_size") or 1000,
                        "margin": sum(a["pct"] * {"Dem": 1, "Rep": -1}.get(a["choice"], 0) for a in p["answers"])}
                       for p in json.loads((HIST / "votehub_generic-ballot.json").read_text())])
    return pd.concat([_avg(h, "margin"), _avg(vh, "margin")]).sort_index()


def nationscape() -> pd.DataFrame:
    """Weekly Trump approval by party identification (pid3: 1 Democrat, 2 Republican, 3 Independent), Nationscape
    main waves. pres_approval 1-2 = approve; 999 (not sure) counts in the base."""
    out = []
    for f in sorted(glob.glob(str(HIST / "nationscape" / "ns*.tab"))):
        d = pd.read_csv(f, sep="\t", usecols=["start_date", "pres_approval", "pid3", "weight"], low_memory=False)
        d = d.dropna(subset=["weight"])
        row = {"date": pd.to_datetime(d.start_date).min().normalize()}
        for code, g in (("D", 1), ("R", 2), ("I", 3)):
            s = d[d.pid3 == g]
            row[code] = 100 * np.average(s.pres_approval.isin([1, 2]), weights=s.weight)
        s = d
        row["all"] = 100 * np.average(s.pres_approval.isin([1, 2]), weights=s.weight)
        out.append(row)
    return pd.DataFrame(out).set_index("date").sort_index()


def shift(series: pd.Series, date: pd.Timestamp) -> float:
    pre = series[(series.index >= date - pd.Timedelta(days=7)) & (series.index <= date - pd.Timedelta(days=1))]
    post = series[(series.index >= date + pd.Timedelta(days=5)) & (series.index <= date + pd.Timedelta(days=14))]
    return float(post.mean() - pre.mean()) if len(pre) >= 3 and len(post) >= 3 else float("nan")


def shift_detrended(series: pd.Series, date: pd.Timestamp) -> float:
    """Same windows, but measured against the pre-event trend (a line fitted on days -21..-1 and projected forward),
    so a slow drift already under way (e.g. falling gas prices) doesn't count as the event's effect."""
    pre = series[(series.index >= date - pd.Timedelta(days=21)) & (series.index <= date - pd.Timedelta(days=1))]
    post = series[(series.index >= date + pd.Timedelta(days=5)) & (series.index <= date + pd.Timedelta(days=14))]
    if len(pre) < 10 or len(post) < 3:
        return float("nan")
    x = (pre.index - date).days.values
    slope, icpt = np.polyfit(x, pre.values, 1)
    return float(np.mean(post.values - (icpt + slope * (post.index - date).days.values)))


def weekly_shift(df: pd.DataFrame, col: str, date: pd.Timestamp) -> float:
    pre = df[(df.index >= date - pd.Timedelta(days=14)) & (df.index < date)][col]
    post = df[(df.index >= date + pd.Timedelta(days=3)) & (df.index <= date + pd.Timedelta(days=17))][col]
    return float(post.mean() - pre.mean()) if len(pre) and len(post) else float("nan")


def build() -> list[dict]:
    test_dates = [pd.Timestamp(e["date"]) for e in json.loads((HERE / "events.json").read_text())]
    ap, gb, ns = approval(), generic(), nationscape()
    all_dates = [pd.Timestamp(d) for _, d, *_ in EVENTS2] + test_dates
    noise = {}
    for name, s in (("approval", ap.approve), ("generic", gb)):
        placebo = [shift(s, t) for t in s.index[::3] if min(abs((t - d).days) for d in all_dates) > 21]
        noise[name] = float(np.nanstd(placebo))
    out = []
    for eid, date, etype, primary, text in EVENTS2:
        d = pd.Timestamp(date)
        if min(abs((d - t).days) for t in test_dates) < 14:
            raise ValueError(f"{eid} is within two weeks of a test event")
        near = [e for e, dt, *_ in EVENTS2 if e != eid and abs((pd.Timestamp(dt) - d).days) <= 14]
        party = ap.party.asof(d) if d >= ap.index.min() else None
        a = shift(ap.approve, d)
        a_d = -a if party == "R" else a
        g = shift(gb, d)
        val = a_d if primary == "approval" else g
        tr = shift_detrended(ap.approve, d) if primary == "approval" else shift_detrended(gb, d)
        tr = -tr if primary == "approval" and party == "R" else tr
        rec = {"id": eid, "date": date, "event_type": etype, "measure": f"{primary} (days +5..+14 vs -7..-1)",
               "description": text, "shift_toward_D": round(val, 2) if val == val else None,
               "shift_detrended": round(tr, 2) if tr == tr else None,
               "approval_shift_toward_D": round(a_d, 2) if a_d == a_d else None,
               "generic_margin_shift": round(g, 2) if g == g else None,
               "z": round(val / noise[primary], 2) if val == val else None, "president_party": party,
               "confounded_with": near}
        if ns.index.min() - pd.Timedelta(days=14) <= d <= ns.index.max():
            sign = -1  # Trump approval: a rise is a shift toward the Republicans
            rec["party"] = {g_: round(sign * weekly_shift(ns, g_, d), 2) for g_ in ("D", "R", "I")}
        out.append(rec)
    (HERE / "events2.json").write_text(json.dumps(out, indent=1))
    ok = [r for r in out if r["shift_toward_D"] is not None]
    print(f"{len(out)} events, {len(ok)} measured; noise SD approval {noise['approval']:.2f}, generic "
          f"{noise['generic']:.2f} pts; |z| >= 1.5: {sum(abs(r['z']) >= 1.5 for r in ok)}; with party shifts: "
          f"{sum('party' in r for r in out)}")
    for r in out:
        print(f"  {r['date']} {r['id']:22} {r['event_type']:13} shift {r['shift_toward_D']!s:>6}  "
              f"detrended {r['shift_detrended']!s:>6}  z {r['z']!s:>6}"
              + (f"  party {r['party']}" if "party" in r else ""))
    return out


if __name__ == "__main__":
    build()
