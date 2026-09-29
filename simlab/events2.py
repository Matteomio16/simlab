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
from .core import RUNS

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
    """Weekly Nationscape series by party identification (pid3: 1 Democrat, 2 Republican, 3 Independent) and overall:
    approve_<g> = % approving of Trump (pres_approval 1-2; not sure stays in the base); intent_<g> = % saying they
    will vote in November 2020 (vote_intention 1, among 1, 2 and 999; 3 = not eligible is dropped); margin_<g> =
    Biden minus Trump in the head-to-head (trump_biden 1 = Biden, 2 = Trump, 999 not sure in the base). Bare D/R/I/all
    columns keep the approval series for older callers."""
    out = []
    for f in sorted(glob.glob(str(HIST / "nationscape" / "ns*.tab"))):
        have = set(pd.read_csv(f, sep="\t", nrows=0).columns)  # some waves lack an item
        use = [c for c in ("start_date", "pres_approval", "vote_intention", "trump_biden", "pid3", "weight") if c in have]
        d = pd.read_csv(f, sep="\t", usecols=use, low_memory=False).dropna(subset=["weight"])
        row = {"date": pd.to_datetime(d.start_date).min().normalize()}
        for code, s in (("D", d[d.pid3 == 1]), ("R", d[d.pid3 == 2]), ("I", d[d.pid3 == 3]), ("all", d)):
            row[f"approve_{code}"] = row[code] = 100 * np.average(s.pres_approval.isin([1, 2]), weights=s.weight)
            e = s[s.vote_intention.isin([1, 2, 999])] if "vote_intention" in s else s.iloc[:0]
            row[f"intent_{code}"] = 100 * np.average(e.vote_intention == 1, weights=e.weight) if len(e) else np.nan
            h = s[s.trump_biden.notna()] if "trump_biden" in s else s.iloc[:0]
            row[f"margin_{code}"] = (100 * np.average((h.trump_biden == 1).astype(int) - (h.trump_biden == 2),
                                                      weights=h.weight) if len(h) else np.nan)
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
    # Nationscape noise from every week, events included: only 19 event-free weeks exist, and they underestimated it
    # (Democrats' turnout intention: SD 0.60 on quiet weeks vs 1.48 on all weeks), so all weeks is the safe choice.
    weeks = [t + pd.Timedelta(days=3) for t in ns.index[2:-3]]
    ns_noise = {c: float(np.nanstd([weekly_shift(ns, c, t) for t in weeks]))
                for c in ns.columns if c.startswith(("margin_", "intent_"))}
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
            rec["nationscape"] = {
                kind: {g_: {"shift": round(weekly_shift(ns, f"{kind}_{g_}", d), 2),
                            "z": round(weekly_shift(ns, f"{kind}_{g_}", d) / ns_noise[f"{kind}_{g_}"], 2)}
                       for g_ in ("D", "R", "I", "all")}
                for kind in ("margin", "intent")}
        out.append(rec)
    (HERE / "events2.json").write_text(json.dumps(out, indent=1))
    ok = [r for r in out if r["shift_toward_D"] is not None]
    print(f"{len(out)} events, {len(ok)} measured; noise SD approval {noise['approval']:.2f}, generic "
          f"{noise['generic']:.2f} pts; |z| >= 1.5: {sum(abs(r['z']) >= 1.5 for r in ok)}; with party shifts: "
          f"{sum('party' in r for r in out)}")
    print("Nationscape weekly noise SD (placebo):", {c: round(v, 2) for c, v in ns_noise.items()})
    for r in (r for r in out if "nationscape" in r):
        big = {f"{k}_{g}": v for k, gs in r["nationscape"].items() for g, v in gs.items() if abs(v["z"]) >= 2}
        print(f"  {r['id']:22} |z|>=2: {big or '-'}")
    for r in out:
        print(f"  {r['date']} {r['id']:22} {r['event_type']:13} shift {r['shift_toward_D']!s:>6}  "
              f"detrended {r['shift_detrended']!s:>6}  z {r['z']!s:>6}"
              + (f"  party {r['party']}" if "party" in r else ""))
    return out


TYPES_19 = {"E01": "debate", "E13": "debate", "E16": "debate", "E02": "scandal_legal", "E03": "scandal_legal",
            "E05": "scandal_legal", "E06": "scandal_legal", "E12": "scandal_legal", "E18": "scandal_legal",
            "E07": "shock_crisis", "E09": "shock_crisis", "E10": "shock_crisis", "E17": "economy", "E19": "shock_crisis",
            "E23": "economy", "E14": "security", "E20": "security", "E22": "security", "E11": "policy_court"}


def predict(model: str, events: list[dict]) -> np.ndarray:
    """Weighted mean expected shift (-2..+2 scale, toward D) over the 28 test personas, as in tests.events_test, but
    with all order variants of a persona's question in one request (Jev) or one prompt per variant (GLM)."""
    from concurrent.futures import ThreadPoolExecutor
    from .askers import DecisionAsker, LLMAsker, expected
    from .core import JEV
    from .probes import reaction_state
    from .tests import EVENT_Q
    arch = json.loads((HERE / "archetypes.json").read_text())
    asker = DecisionAsker(JEV, n_orders=2, name="jev") if model == "jev" else LLMAsker(model, n_orders=2, name=model)
    items = [(e, p) for e in events for p in arch]
    with ThreadPoolExecutor(16) as ex:
        preds = list(ex.map(lambda it: asker.ask_many(reaction_state(it[1]["text_events"],
                                                                     f"({it[0]['date']}) {it[0]['description']}"),
                                                      {"q": EVENT_Q}, f"events2:{model}")["q"], items))
    w = np.array([p["weight"] for p in arch])
    e = np.array([expected(p) for p in preds]).reshape(len(events), len(arch))
    return e @ w / w.sum()


def transfer(models: list[str]) -> None:
    """Fit each model's points-per-unit scale (one overall, and one per event type) on events2, apply it unchanged to
    the 19 held-out events: does the per-type calibration found on the 19 hold up when fitted elsewhere?"""
    ev2 = [e for e in json.loads((HERE / "events2.json").read_text()) if e["shift_toward_D"] is not None]
    ev19 = json.loads((HERE / "events.json").read_text())
    y2 = np.array([e["shift_toward_D"] for e in ev2]); t2 = np.array([e["event_type"] for e in ev2])
    y19 = np.array([e["shift_toward_D"] for e in ev19], float); w19 = np.array([e["weight"] for e in ev19])
    t19 = np.array([TYPES_19[e["id"][:3]] for e in ev19])
    err = lambda c: float(np.sqrt(np.average((c - y19) ** 2, weights=w19)))
    print(f"19 held-out events: always 'no change' error {err(np.zeros_like(y19)):.2f} pts")
    for m in models:
        x2 = predict(m, ev2)
        (RUNS / f"events2__{m}.jsonl").write_text("\n".join(
            json.dumps({"id": e["id"], "event_type": e["event_type"], "measured": e["shift_toward_D"],
                        "z": e["z"], "pred": round(float(x), 4)}) for e, x in zip(ev2, x2)))
        x19 = np.array([json.loads(l)["pred"]["all"] for l in (RUNS / f"events__{m}.jsonl").read_text().splitlines()])
        k = float(np.sum(x2 * y2) / np.sum(x2 * x2))
        kt = {t: float(np.sum(x2[t2 == t] * y2[t2 == t]) / np.sum(x2[t2 == t] ** 2)) for t in set(t2)
              if (t2 == t).sum() >= 3 and np.sum(x2[t2 == t] ** 2) > 0}
        typed = np.array([kt.get(t, k) * x for t, x in zip(t19, x19)])
        from scipy.stats import spearmanr
        print(f"{m}: events2 rank corr {spearmanr(x2, y2)[0]:.2f}, sign right {np.mean(np.sign(x2) == np.sign(y2)):.0%} "
              f"(|shift|>=1: {np.mean((np.sign(x2) == np.sign(y2))[np.abs(y2) >= 1]):.0%}) | on the 19: one scale "
              f"{k:.1f} -> error {err(k * x19):.2f}; per type -> {err(typed):.2f} | scales by type "
              f"{ {t: round(v, 1) for t, v in sorted(kt.items())} }")


EXPOSURE_Q = {"type": "score", "instructions": "How likely is it that this person heard or read about this news "
               "within a week?", "criteria": ["Almost certainly not", "Probably not", "Maybe", "Probably yes",
                                              "Almost certainly yes"]}
LANDING_Q = {"type": "score", "instructions": "If this person heard about this news, how did it change how they feel "
             "about the two parties, if at all?", "criteria": ["Much more favorable to the Republicans",
                                                               "Somewhat more favorable to the Republicans",
                                                               "No change", "Somewhat more favorable to the Democrats",
                                                               "Much more favorable to the Democrats"]}


def exposure(models: list[str]) -> None:
    """Field Guide rule 5 ("ask who was exposed and how it landed, never 'would this change your vote'"):
    predicted shift = P(heard about it) x how it landed, vs the direct question, on both event sets."""
    from concurrent.futures import ThreadPoolExecutor
    from scipy.stats import spearmanr
    from .askers import DecisionAsker, LLMAsker, expected
    from .core import JEV
    from .probes import reaction_state
    arch = json.loads((HERE / "archetypes.json").read_text())
    w = np.array([p["weight"] for p in arch])
    ev2 = [e for e in json.loads((HERE / "events2.json").read_text()) if e["shift_toward_D"] is not None]
    ev19 = json.loads((HERE / "events.json").read_text())
    for m in models:
        asker = DecisionAsker(JEV, n_orders=2, name="jev") if m == "jev" else LLMAsker(m, n_orders=2, name=m)
        res = {}
        for name, evs in (("events2", ev2), ("events19", ev19)):
            items = [(e, p) for e in evs for p in arch]
            with ThreadPoolExecutor(16) as ex:
                preds = list(ex.map(lambda it: asker.ask_many(
                    reaction_state(it[1]["text_events"], f"({it[0]['date']}) {it[0]['description']}"),
                    {"exposure": EXPOSURE_Q, "landing": LANDING_Q}, f"exposure:{m}"), items))
            p_heard = np.array([expected(p["exposure"], values=(0, .25, .5, .75, 1)) for p in preds])
            landing = np.array([expected(p["landing"]) for p in preds])
            x = ((p_heard * landing).reshape(len(evs), len(arch)) @ w) / w.sum()
            heard = (p_heard.reshape(len(evs), len(arch)) @ w) / w.sum()
            y = np.array([e["shift_toward_D"] for e in evs], float)
            if name == "events2":
                direct = np.array([json.loads(l)["pred"] for l in (RUNS / f"events2__{m}.jsonl").read_text()
                                   .splitlines()])
            else:
                direct = np.array([json.loads(l)["pred"]["all"] for l in (RUNS / f"events__{m}.jsonl").read_text()
                                   .splitlines()])
            res[name] = (x, y, direct, heard)
            big = np.abs(y) >= 1
            print(f"{m} {name}: direction right (|shift|>=1) exposure-framed {np.mean(np.sign(x[big]) == np.sign(y[big])):.0%}"
                  f" vs direct {np.mean(np.sign(direct[big]) == np.sign(y[big])):.0%}; size-tracking "
                  f"{spearmanr(np.abs(x), np.abs(y))[0]:.2f} vs {spearmanr(np.abs(direct), np.abs(y))[0]:.2f}; "
                  f"P(heard) tracks size {spearmanr(heard, np.abs(y))[0]:.2f}")
        (x2, y2, d2, _), (x19, y19, d19, _) = res["events2"], res["events19"]
        w19 = np.array([e["weight"] for e in ev19])
        err = lambda c: float(np.sqrt(np.average((c - y19) ** 2, weights=w19)))
        k, kd = (x2 @ y2) / (x2 @ x2), (d2 @ y2) / (d2 @ d2)
        print(f"{m}: scale fitted on events2, error on the 19: exposure-framed {err(k * x19):.2f} vs direct "
              f"{err(kd * d19):.2f} ('no change' {err(np.zeros_like(y19)):.2f})")


REACTION_EVENT_Q = {"type": "score", "instructions": "How does hearing this news change this person's support "
                     "between the Democratic and Republican parties, if at all? Think about how someone like them "
                     "reacts to the news itself (for example anger, worry or enthusiasm that can rally them behind "
                     "their side or put them off a party), not only about who the news helps on paper.",
                     "criteria": ["Moves strongly toward the Republicans", "Moves slightly toward the Republicans",
                                  "No change", "Moves slightly toward the Democrats",
                                  "Moves strongly toward the Democrats"]}


def _map_resilient(fn, items: list, workers: int = 6, retries: int = 5, pause: float = 25.0) -> list:
    """Like ThreadPoolExecutor(workers).map(fn, items), but items that raise (the upstream host's own 429 retries
    in core.py's _post exhausted during a burst of rate-limiting) are retried a few more rounds, pausing between
    rounds, instead of failing the whole batch over one stubborn item. Raises only if items are still failing after
    all rounds."""
    from concurrent.futures import ThreadPoolExecutor
    import time
    results: list = [None] * len(items)
    todo = list(range(len(items)))
    for attempt in range(retries + 1):
        if not todo:
            break
        failed = []
        with ThreadPoolExecutor(workers) as ex:
            futs = {ex.submit(fn, items[i]): i for i in todo}
            for fut, i in futs.items():
                try:
                    results[i] = fut.result()
                except Exception:
                    failed.append(i)
        if failed and attempt < retries:
            print(f"  {len(failed)}/{len(todo)} items failed (attempt {attempt + 1}/{retries + 1}); "
                  f"retrying after {pause:.0f}s")
            time.sleep(pause)
        todo = failed
    if todo:
        raise RuntimeError(f"{len(todo)} of {len(items)} items still failing after {retries + 1} attempts")
    return results


def reaction_events(models: list[str]) -> dict:
    """Part 1 of the reaction-wording test (Matteo approved 28 Sep): REACTION_EVENT_Q asks the model to weigh how a
    kind of person reacts to the news itself (anger, worry, enthusiasm), not only who it helps on paper. Same
    predicted-shift setup as exposure(), compared against the direct EVENT_Q wording cached in events2__<m>.jsonl
    and events__<m>.jsonl (field pred / pred["all"])."""
    from scipy.stats import spearmanr
    from .askers import LLMAsker, expected
    from .probes import reaction_state
    arch = json.loads((HERE / "archetypes.json").read_text())
    w = np.array([p["weight"] for p in arch])
    ev2 = [e for e in json.loads((HERE / "events2.json").read_text()) if e["shift_toward_D"] is not None]
    ev19 = json.loads((HERE / "events.json").read_text())
    out = {}
    for m in models:
        asker = LLMAsker(m, n_orders=2, name=m)
        res = {}
        for name, evs in (("events2", ev2), ("events19", ev19)):
            items = [(e, p) for e in evs for p in arch]
            preds = _map_resilient(lambda it: asker.ask_many(
                reaction_state(it[1]["text_events"], f"({it[0]['date']}) {it[0]['description']}"),
                {"q": REACTION_EVENT_Q}, f"backlash:{m}")["q"], items)
            x = (np.array([expected(p) for p in preds]).reshape(len(evs), len(arch)) @ w) / w.sum()
            y = np.array([e["shift_toward_D"] for e in evs], float)
            if name == "events2":
                direct = np.array([json.loads(l)["pred"]
                                   for l in (RUNS / f"events2__{m}.jsonl").read_text().splitlines()])
            else:
                direct = np.array([json.loads(l)["pred"]["all"]
                                   for l in (RUNS / f"events__{m}.jsonl").read_text().splitlines()])
            res[name] = (x, y, direct)
            big = np.abs(y) >= 1
            dir_r = float(np.mean(np.sign(x[big]) == np.sign(y[big])))
            dir_d = float(np.mean(np.sign(direct[big]) == np.sign(y[big])))
            sp_r, sp_d = float(spearmanr(np.abs(x), np.abs(y))[0]), float(spearmanr(np.abs(direct), np.abs(y))[0])
            out.setdefault(m, {})[name] = {"direction_right_reaction": dir_r, "direction_right_direct": dir_d,
                                            "spearman_reaction": sp_r, "spearman_direct": sp_d, "n": len(evs)}
            print(f"{m} {name}: direction right (|shift|>=1) reaction-worded {dir_r:.0%} vs direct {dir_d:.0%}; "
                  f"size-tracking {sp_r:.2f} vs {sp_d:.2f}")
        (x2, y2, d2), (x19, y19, d19) = res["events2"], res["events19"]
        w19 = np.array([e["weight"] for e in ev19])
        err = lambda c: float(np.sqrt(np.average((c - y19) ** 2, weights=w19)))
        k, kd = (x2 @ y2) / (x2 @ x2), (d2 @ y2) / (d2 @ d2)
        err_r, err_d, err_0 = err(k * x19), err(kd * d19), err(np.zeros_like(y19))
        out[m]["error19"] = {"reaction": err_r, "direct": err_d, "no_change": err_0,
                              "scale_reaction": float(k), "scale_direct": float(kd)}
        print(f"{m}: scale fitted on events2, error on the 19: reaction-worded {err_r:.2f} vs direct {err_d:.2f} "
              f"('no change' {err_0:.2f})")
    return out


SUPPORT_REACTION_Q = {"type": "score", "instructions": "How does hearing this news change this person's "
                       "preference in their state's Senate race, if at all? Think about how someone like them "
                       "reacts to the news itself (for example anger, worry or enthusiasm that can rally them "
                       "behind their side or put them off a candidate), not only about who the news helps on "
                       "paper.", "criteria": ["Moves strongly toward the Republican candidate",
                       "Moves slightly toward the Republican candidate", "No change",
                       "Moves slightly toward the Democratic candidate",
                       "Moves strongly toward the Democratic candidate"]}
TURNOUT_REACTION_Q = {"type": "score", "instructions": "How does hearing this news change this person's "
                       "likelihood of voting in November, if at all? Think about how someone like them reacts to "
                       "the news itself (for example whether it fires them up, alarms them or discourages them), "
                       "not only about who the news helps on paper.",
                       "criteria": ["Much less likely to vote", "Somewhat less likely to vote", "No change",
                                    "Somewhat more likely to vote", "Much more likely to vote"]}

BACKLASH_STORIES = [
    ("OH0002", "money", False), ("OH0183", "money", False), ("TE0022", "money", False),
    ("NA0052", "legal", False), ("TE0021", "legal", False), ("TE0092", "legal", False),
    ("NO0000", "surrogate", False), ("NA0150", "surrogate", False),
    ("TE0058", "former_ally", False), ("TE0067", "former_ally", False),
    ("TE0200", "endorsement", False), ("NO0108", "endorsement", False), ("OH0160", "endorsement", False),
    ("TE0158", "endorsement", False), ("OH0014", "endorsement", False),
    ("OH0001", "control", True), ("NO0167", "control", True), ("TE0110", "control", True),
]


def backlash_stories() -> list[dict]:
    """The 15 Part 2 stories where a news story's effect on voters could differ from who it helps on paper (big
    money, prosecutions, polarising surrogates, attack ads from former allies, controversial endorsements), plus 3
    controls where backlash is implausible. Picked by hand from news.latest() on 28 Sep 2026."""
    import re
    from .news import NEWS
    dated = sorted(p for p in NEWS.iterdir() if p.is_dir() and re.fullmatch(r"\d{4}-\d{2}-\d{2}", p.name))
    by_id = {s["story_id"]: s for s in map(json.loads, (dated[-1] / "stories.jsonl").read_text(encoding="utf-8")
                                           .splitlines())}
    out = [{"id": sid, "race": by_id[sid]["race"], "title": by_id[sid]["title"], "category": cat, "control": ctrl}
           for sid, cat, ctrl in BACKLASH_STORIES]
    (RUNS / "backlash_stories.json").write_text(json.dumps(out, indent=1))
    return out


def _story_state(persona: str, story: dict) -> str:
    """Persona text with "State: <OH/NC/TX>" swapped for the story's state, so "their state's Senate race" points
    at the right race; national stories keep the persona's own state."""
    from .news import RACES
    from .probes import reaction_state
    if story["race"] in ("Ohio", "North Carolina", "Texas"):
        _, _, rest = persona.partition("\n")
        persona = f"State: {story['race']}\n{rest}"
    return reaction_state(persona, f"{story['title']}\n{RACES[story['race']][1]}")


def _leak_check(asker, stories: list[dict], arch: list[dict]) -> bool:
    """Ask the direct and reaction support wording bundled in one prompt vs each in its own prompt, on a small
    sample of stories and archetypes. True (leakage) if bundling makes the two answers suspiciously close, so the
    full run should ask each wording in its own prompt instead."""
    from .askers import expected
    from .probes import REACTION_QUESTIONS
    picks_a = [a for party in "DIR" for a in [x for x in arch if x["party"] == party][:2]]
    picks_s = [s for s in stories if not s["control"]][:2] + [s for s in stories if s["control"]][:1]
    states = [_story_state(a["text"], s) for s in picks_s for a in picks_a]
    qs = {"d": REACTION_QUESTIONS["support"], "r": SUPPORT_REACTION_Q}
    bundled = _map_resilient(lambda st: asker.ask_many(st, qs, f"backlash:{asker.name}", groups=[["d", "r"]]),
                             states, workers=6)
    separate = _map_resilient(lambda st: asker.ask_many(st, qs, f"backlash:{asker.name}", groups=[["d"], ["r"]]),
                              states, workers=6)
    bd, br = np.array([expected(p["d"]) for p in bundled]), np.array([expected(p["r"]) for p in bundled])
    sd, sr = np.array([expected(p["d"]) for p in separate]), np.array([expected(p["r"]) for p in separate])
    gap_b, gap_s = float(np.mean(np.abs(br - bd))), float(np.mean(np.abs(sr - sd)))
    corr_b = float(np.corrcoef(bd, br)[0, 1]) if bd.std() > 0 and br.std() > 0 else 0.0
    corr_s = float(np.corrcoef(sd, sr)[0, 1]) if sd.std() > 0 and sr.std() > 0 else 0.0
    print(f"backlash leak check ({len(states)} items): bundled |reaction-direct| {gap_b:.2f} (corr {corr_b:.2f}) "
          f"vs separate {gap_s:.2f} (corr {corr_s:.2f})")
    return gap_b < 0.6 * gap_s or (corr_b - corr_s) > 0.2


def backlash_test(model: str = "glm") -> list[dict]:
    """Part 2 of the reaction-wording test: 28 archetypes on backlash_stories(), direct vs reaction wording on
    support and turnout (never bundling turnout with support), tagged backlash:<model>. Writes
    runs/backlash__<model>.jsonl (one row per story and archetype) and prints each story's party-weighted means."""
    from .askers import LLMAsker, expected
    from .probes import REACTION_QUESTIONS
    arch = json.loads((HERE / "archetypes.json").read_text())
    stories = backlash_stories()
    asker = LLMAsker(model, n_orders=2, name=model)
    questions = {"support_direct": REACTION_QUESTIONS["support"], "support_reaction": SUPPORT_REACTION_Q,
                 "turnout_direct": REACTION_QUESTIONS["turnout"], "turnout_reaction": TURNOUT_REACTION_Q}
    leaking = _leak_check(asker, stories, arch)
    groups = ([["support_direct"], ["support_reaction"], ["turnout_direct"], ["turnout_reaction"]] if leaking else
              [["support_direct", "support_reaction"], ["turnout_direct", "turnout_reaction"]])
    print(f"backlash_test: {'separate' if leaking else 'bundled'} prompts for direct vs reaction wording")
    items = [(s, a) for s in stories for a in arch]
    preds = _map_resilient(lambda it: asker.ask_many(_story_state(it[1]["text"], it[0]), questions,
                                                     f"backlash:{model}", groups=groups), items)
    rows = [{"story_id": s["id"], "race": s["race"], "category": s["category"], "control": s["control"],
             "archetype": a["id"], "party": a["party"], "weight": a["weight"],
             "support_direct": expected(p["support_direct"]), "support_reaction": expected(p["support_reaction"]),
             "turnout_direct": expected(p["turnout_direct"]), "turnout_reaction": expected(p["turnout_reaction"])}
            for (s, a), p in zip(items, preds)]
    (RUNS / f"backlash__{model}.jsonl").write_text("\n".join(json.dumps(r) for r in rows))
    keys = ("support_direct", "support_reaction", "turnout_direct", "turnout_reaction")
    agg: dict = {}
    for r in rows:
        a = agg.setdefault((r["story_id"], r["party"]), {k: [0.0, 0.0] for k in keys})
        for k in keys:
            a[k][0] += r[k] * r["weight"]
            a[k][1] += r["weight"]
    print(f"{len(rows)} rows -> runs/backlash__{model}.jsonl")
    for s in stories:
        print(f"{s['id']:8} {s['category']:12} {s['title'][:70]}")
        for party in "DIR":
            v = agg[(s["id"], party)]
            print("    " + party + ": " + " ".join(f"{k}={v[k][0] / v[k][1]:+.2f}" for k in keys))
    return rows


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "transfer":
        transfer(sys.argv[2].split(",") if len(sys.argv) > 2 else ["jev", "glm"])
    elif len(sys.argv) > 1 and sys.argv[1] == "exposure":
        exposure(sys.argv[2].split(",") if len(sys.argv) > 2 else ["jev", "glm"])
    elif len(sys.argv) > 1 and sys.argv[1] == "backlash":
        reaction_events(["glm"])
        backlash_test("glm")
    else:
        build()
