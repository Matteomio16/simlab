import gzip
import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

from simlab import polls

OHIO_TABLE = """{| class="wikitable" style="font-size:90%;text-align:center;"
|- valign=bottom
! Poll source
! Date(s)<br />administered
! Sample<br />size{{efn|Key:<br />A – all adults<br />LV – likely voters|name="Key"}}
! Margin<br />of error
! style="width:100px;"| Jon<br />Husted (R)
! style="width:100px;"| Sherrod<br />Brown (D)
! Other
! Undecided
|-
|style="text-align:left;|[[Rasmussen Reports]] (R)<ref>{{cite web |title=Election 2026 |url=https://example.org}}</ref>
|September 22–23, 2026
|1,115 (LV)
|±&nbsp;3.0%
|43%
|{{party shading/Democratic}}|'''46%'''
|5%{{Efn|Bill Redpath (L) with 3%; Greg Levy (I) with 2%}}
|7%
|-
|rowspan=2 style="text-align:left;"|Quantus Insights (R)<ref>{{Cite web |url=https://example.org/q}}</ref>
|rowspan=2|September 21–23, 2026
|rowspan=2|695 (LV)
|rowspan=2|±{{nbsp}}4.2%
|'''47%'''{{efn|name=lean|With voters who lean towards a given candidate}}
|'''47%'''
|4%
|2%
|-
|45%
|{{party shading/Democratic}}|'''46%'''
|4%
|6%
|-
|style="text-align:left;" rowspan="2"|[[Abacus Data]]<ref>x</ref>
|rowspan="2"|August 26–28, 2026
|306 (LV)
|{{sdash}}
|46%
|48%
|{{sdash}}
|6%
|-
|500 (RV)
|{{sdash}}
|44%
|47%
|{{sdash}}
|9%
|}"""


RYAN_ROWS = "".join(f"""|-
|Poll {i}
|March {i}, 2026
|600 (RV)
|±&nbsp;4.0%
|44%
|41%
|15%
""" for i in range(1, 7))

PAGE = """Intro.
== Republican primary ==
=== Polling ===
{| class="wikitable"
! Poll source
! Date(s)<br />administered
! Sample<br />size
! Margin<br />of error
! Jon<br />Husted
! Other
|-
|Primary Poll
|May 1–2, 2026
|400 (LV)
|±&nbsp;5%
|70%
|30%
|}
== General election ==
=== Predictions ===
Some text.
=== Polling ===
'''Aggregate polls'''
{| class="wikitable sortable"
!Source of poll<br/>aggregation
!Dates<br/>administered
! style="width:100px;" |Jon<br />Husted (R)
! style="width:100px;" |Sherrod<br />Brown (D)
|-
|[[270toWin]]
|September 10–24, 2026
|44.0%
|'''47.0%'''
|}

""" + OHIO_TABLE + """

;Jon Husted vs. Tim Ryan
{| class="wikitable"
! Poll source
! Date(s)<br />administered
! Sample<br />size
! Margin<br />of error
! Jon<br />Husted (R)
! Tim<br />Ryan (D)
! Undecided
""" + RYAN_ROWS + """|}
=== Results ===
Results table.
"""

OHIO = None  # set in setUpModule once polls.Race exists

OVERVIEW = """== Race summary ==
=== Special elections during the preceding Congress ===
{| class="wikitable sortable"
|- valign=bottom
! colspan=2 | Constituency
! rowspan=2 | Candidates
|-
! [[2026 United States Senate special election in Ohio|Ohio]]<br />(Class 3)
| {{Shading PVI|R|5}}
| [[Jon Husted]]
| {{Party shading/Republican}} | Republican
| 2025 {{small|(appointed)}}
| data-sort-value=0 | Interim appointee nominated
| nowrap | {{Plainlist |
*{{Party stripe|Democratic Party (US)}}[[Sherrod Brown]] (Democratic)
*{{Party stripe|Republican Party (US)}}[[Jon Husted]] (Republican)
*{{Party stripe|Independent}}Greg Levy (Independent)
*{{Party stripe|Libertarian Party (US)}}William Redpath (Libertarian)
}}
|}
=== Elections leading to the next Congress ===
{| class="wikitable sortable sticky-header-multi"
|- valign=bottom
! colspan=2 | Constituency
! rowspan=2 class="unsortable" | Candidates
|-
! [[2026 United States Senate election in Alabama|Alabama]]
| {{Shading PVI|R|15}}
| {{sortname|Tommy|Tuberville}}
| {{Party shading/Republican}} | Republican
| {{Party shading/Hold}} data-sort-value=-1 | Incumbent retiring<br />to [[2026 Alabama gubernatorial election|run for governor]]
| nowrap | {{Plainlist |
*{{Party stripe|Republican Party (US)}}[[Barry Moore (American politician)|Barry Moore]] (Republican)<ref name="AL2026R">{{#invoke:cite|web|title=Qualified}}</ref>
*{{Party stripe|Democratic Party (US)}}Everett Wess (Democratic)<ref name="AL2026D" />
}}
|-
! [[2026 United States Senate election in Georgia|Georgia]]
| {{Shading PVI|R|1}}
| {{sortname|Jon|Ossoff}}
| {{Party shading/Democratic}} | Democratic
| data-sort-value=1 | Incumbent renominated
| nowrap | {{Plainlist |*{{Party stripe|Republican Party (US)}}[[Mike Collins (politician)|Mike Collins]] (Republican)<ref name="GA2026" />
*{{Party stripe|Democratic Party (United States)}}[[Jon Ossoff]] (Democratic)<ref name="GA2026">{{#invoke:cite|web|title=Q}}</ref>
}}
|-
! [[2026 United States Senate election in Montana|Montana]]
| nowrap | {{Plainlist |
*{{Party stripe|Republican Party (US)}}[[Kurt Alme]] (Republican)
*{{Party stripe|Libertarian Party (US)}}Kyle Austin (Libertarian)
*{{Party stripe|Democratic Party (US)}}Alani Bankhead (Democratic)
*{{Party stripe|Independent}}[[Seth Bodnar]] (Independent)
}}
|-
! [[2026 United States Senate election in Nebraska|Nebraska]]
| nowrap | {{Plainlist |
*{{Party stripe|America First Party}}Chuck Conboy (America First)
*{{Party stripe|Independent}}[[Dan Osborn]] (Independent)
*{{Party stripe|Republican Party (US)}}[[Pete Ricketts]] (Republican)
}}
|-
! [[2026 United States Senate election in West Virginia|West Virginia]]
| nowrap | {{Plainlist |
*{{Party stripe|Democratic Party (US)}}Rachel Fetty Anderson (Democratic)
*{{Party stripe|Republican Party (US)}}[[Shelley Moore Capito]] (Republican)
*{{Party stripe|Constitution Party (US)}}[[S. Marshall Wilson]] (Constitution)
}}
|}
== Alabama ==
"""


def vh(id_, subject, pollster, answers, start, end, population="lv", n=1000, partisan=None, sponsors=(),
       poll_type="us-senator"):
    return {"id": id_, "poll_type": poll_type, "subject": subject, "pollster": pollster, "sponsors": list(sponsors),
            "partisan": partisan, "internal": False, "population": population, "sample_size": n,
            "start_date": start, "end_date": end, "created_at": end, "url": f"https://example.org/{id_}",
            "answers": [{"choice": c, "pct": p} for c, p in answers.items()], "seat_name": None}


VOTEHUB = [
    vh("a1", "2026 Ohio", "Quantus Insights", {"Jon Husted": 46.0, "Sherrod Brown": 46.5}, "2026-09-21", "2026-09-23",
       n=695, partisan="REP", sponsors=["Some PAC"]),
    vh("a2", "2026 Ohio", "Emerson College", {"Jon Husted": 44.0, "Sherrod Brown": 48.0}, "2026-09-15", "2026-09-16"),
    vh("a3", "2026 Ohio Democratic", "Emerson College", {"Sherrod Brown": 80.0, "Other": 5.0}, "2026-04-01", "2026-04-02"),
    vh("a4", "2026 Ohio", "Emerson College", {"Jon Husted": 45.0, "Tim Ryan": 40.0}, "2026-03-01", "2026-03-02"),
    vh("g1", "2026", "YouGov", {"Dem": 45.0, "Rep": 42.0}, "2026-09-20", "2026-09-22", population="rv",
       poll_type="generic-ballot"),
    vh("g2", "2026", "YouGov", {"Dem": 46.0, "Rep": 42.0}, "2026-09-20", "2026-09-22", population="lv",
       poll_type="generic-ballot"),
    vh("p1", "Donald Trump", "Gallup", {"Approve": 42.0, "Disapprove": 55.0}, "2026-09-01", "2026-09-10",
       population="a", poll_type="approval"),
]


class HelperTest(unittest.TestCase):
    def test_clean_strips_refs_links_templates_and_bold(self):
        raw = "[[Rasmussen Reports]] (R)<ref>{{cite web |title=x}}</ref> '''46%'''{{efn|a note}}<!-- hidden -->"
        self.assertEqual(polls.clean(raw), "Rasmussen Reports (R) 46%")

    def test_clean_keeps_link_label_and_spaces(self):
        self.assertEqual(polls.clean("[[Sherrod Brown|Brown]]<br />{{nbsp}}x"), "Brown x")

    def test_sample_size_and_population(self):
        self.assertEqual(polls.sample("1,115 (LV)"), (1115, "lv"))
        self.assertEqual(polls.sample("500 (RV)"), (500, "rv"))
        self.assertEqual(polls.sample("2,000 (A)"), (2000, "a"))
        self.assertEqual(polls.sample("–"), (None, None))

    def test_dates_within_and_across_months_and_years(self):
        self.assertEqual(polls.dates("September 22–23, 2026"), (date(2026, 9, 22), date(2026, 9, 23)))
        self.assertEqual(polls.dates("August 26 – September 2, 2026"), (date(2026, 8, 26), date(2026, 9, 2)))
        self.assertEqual(polls.dates("September 10, 2026"), (date(2026, 9, 10), date(2026, 9, 10)))
        self.assertEqual(polls.dates("December 28, 2025 – January 3, 2026"), (date(2025, 12, 28), date(2026, 1, 3)))

    def test_month_only_dates_cover_the_month(self):
        self.assertEqual(polls.dates("July 2026"), (date(2026, 7, 1), date(2026, 7, 31)))
        self.assertEqual(polls.dates("February 2026"), (date(2026, 2, 1), date(2026, 2, 28)))

    def test_pollster_tag_split(self):
        self.assertEqual(polls.pollster_tag("Quantus Insights (R)"), ("Quantus Insights", "R"))
        self.assertEqual(polls.pollster_tag("Bowling Green State University/YouGov"),
                         ("Bowling Green State University/YouGov", ""))

    def test_percent(self):
        self.assertEqual(polls.pct("46%"), 46.0)
        self.assertEqual(polls.pct("4.5%"), 4.5)
        self.assertIsNone(polls.pct("–"))


class TableTest(unittest.TestCase):
    def test_header_names_are_cleaned(self):
        header, _ = polls.parse_table(OHIO_TABLE)
        self.assertEqual(header[:4], ["Poll source", "Date(s) administered", "Sample size", "Margin of error"])
        self.assertEqual(header[4:6], ["Jon Husted (R)", "Sherrod Brown (D)"])

    def test_rowspan_cells_repeat_on_following_rows(self):
        _, rows = polls.parse_table(OHIO_TABLE)
        self.assertEqual(len(rows), 5)
        self.assertEqual(rows[2][:3], ["Quantus Insights (R)", "September 21–23, 2026", "695 (LV)"])
        self.assertEqual(rows[2][4:6], ["45%", "46%"])
        self.assertEqual(rows[4][:3], ["Abacus Data", "August 26–28, 2026", "500 (RV)"])

    def test_attributes_before_a_single_pipe_are_dropped(self):
        _, rows = polls.parse_table(OHIO_TABLE)
        self.assertEqual(rows[0][0], "Rasmussen Reports (R)")
        self.assertEqual(rows[0][5], "46%")


class PageTest(unittest.TestCase):
    race = polls.Race("OH", True, "Jon Husted", "Sherrod Brown", "D",
                      "2026 United States Senate special election in Ohio") if hasattr(polls, "Race") else None

    def test_general_election_tables_skip_primaries_and_aggregates(self):
        tables = polls.poll_tables(PAGE)
        self.assertEqual([len(rows) for _, rows in tables], [5, 6])

    def test_nominee_table_is_chosen_by_names_not_size(self):
        header, rows = polls.nominee_table(polls.poll_tables(PAGE), "Husted", "Brown")
        self.assertIn("Sherrod Brown (D)", header)
        self.assertEqual(len(rows), 5)

    def test_wiki_polls_one_row_per_version(self):
        df = polls.wiki_polls(PAGE, self.race)
        self.assertEqual(len(df), 5)
        r = df.iloc[0]
        self.assertEqual((r.pollster, r.tag, r.n, r.population), ("Rasmussen Reports", "R", 1115, "lv"))
        self.assertEqual((r.left, r.right, r.other, r.undecided), (46.0, 43.0, 5.0, 7.0))
        self.assertEqual((r.start, r.end), (date(2026, 9, 22), date(2026, 9, 23)))
        abacus_rv = df.iloc[4]
        self.assertEqual((abacus_rv.n, abacus_rv.population, abacus_rv.left, abacus_rv.right), (500, "rv", 47.0, 44.0))
        self.assertTrue(abacus_rv.other != abacus_rv.other)  # missing -> NaN

    def test_row_missing_trailing_cells_is_kept(self):
        short = PAGE.replace("|44%\n|47%\n|{{sdash}}\n|9%\n|}", "|44%\n|47%\n|}")
        df = polls.wiki_polls(short, self.race)
        self.assertEqual(len(df), 5)
        self.assertEqual((df.iloc[4].left, df.iloc[4].right), (47.0, 44.0))
        self.assertTrue(df.iloc[4].undecided != df.iloc[4].undecided)

    def test_no_general_polling_section_gives_empty_frame(self):
        self.assertEqual(len(polls.wiki_polls("== General election ==\n=== Results ===\n", self.race)), 0)


class RacesTest(unittest.TestCase):
    def setUp(self):
        self.races = {r.race_id: r for r in polls.races(OVERVIEW)}

    def test_first_candidate_on_the_list_opening_line_is_read(self):
        self.assertEqual((self.races["GA"].right, self.races["GA"].left), ("Mike Collins", "Jon Ossoff"))

    def test_special_and_regular_races_with_ids(self):
        self.assertEqual(sorted(self.races), ["AL", "GA", "MT", "NE", "OH-S", "WV"])
        oh = self.races["OH-S"]
        self.assertEqual((oh.right, oh.left, oh.left_party), ("Jon Husted", "Sherrod Brown", "D"))
        self.assertEqual(oh.title, "2026 United States Senate special election in Ohio")

    def test_incumbent_party_and_status(self):
        self.assertEqual((self.races["OH-S"].incumbent, self.races["OH-S"].status), ("R", "Interim appointee nominated"))
        self.assertEqual((self.races["GA"].incumbent, self.races["GA"].status), ("D", "Incumbent renominated"))
        self.assertEqual(self.races["AL"].status, "Incumbent retiring")

    def test_unlinked_democrat_when_no_other_notable_challenger(self):
        self.assertEqual((self.races["AL"].right, self.races["AL"].left), ("Barry Moore", "Everett Wess"))
        self.assertEqual(self.races["WV"].left, "Rachel Fetty Anderson")

    def test_notable_independent_is_the_main_challenger(self):
        self.assertEqual((self.races["NE"].left, self.races["NE"].left_party), ("Dan Osborn", "I"))
        self.assertEqual((self.races["MT"].left, self.races["MT"].left_party), ("Seth Bodnar", "I"))


class MergeTest(unittest.TestCase):
    race = PageTest.race

    def setUp(self):
        self.wiki = polls.wiki_polls(PAGE, self.race).assign(race_id="OH-S")
        self.vh = polls.votehub_polls(VOTEHUB, [self.race])
        self.table = polls.merge(self.wiki, self.vh).set_index("pollster")

    def test_votehub_keeps_general_election_nominee_polls_only(self):
        self.assertEqual(sorted(self.vh.votehub_id), ["a1", "a2"])
        a1 = self.vh.set_index("votehub_id").loc["a1"]
        self.assertEqual((a1.left, a1.right, a1.partisan, a1.sponsors), (46.5, 46.0, "REP", "Some PAC"))

    def test_poll_in_both_sources_takes_wikipedia_numbers_and_votehub_metadata(self):
        q = self.table.loc["Quantus Insights"]
        self.assertEqual((q.source, q.versions, q.votehub_id, q.partisan), ("both", 2, "a1", "REP"))
        self.assertEqual((q.left, q.right), (46.5, 46.0))

    def test_single_source_polls_are_kept(self):
        self.assertEqual(self.table.loc["Emerson College"].source, "votehub")
        self.assertEqual((self.table.loc["Rasmussen Reports"].source, self.table.loc["Rasmussen Reports"].partisan),
                         ("wikipedia", ""))

    def test_likely_voters_win_over_registered_voters(self):
        abacus = self.table.loc[["Abacus Data"]]
        self.assertEqual(list(abacus.population), ["lv"])

    def test_two_party_margin(self):
        r = self.table.loc["Rasmussen Reports"]
        self.assertAlmostEqual(r.margin, 100 * 3 / 89)
        self.assertEqual(r.decided, 89.0)

    def test_disagreement_between_sources_is_flagged(self):
        off = [dict(e, answers=[{"choice": "Jon Husted", "pct": 44.0}, {"choice": "Sherrod Brown", "pct": 48.0}])
               if e["id"] == "a1" else e for e in VOTEHUB]
        q = polls.merge(self.wiki, polls.votehub_polls(off, [self.race])).set_index("pollster").loc["Quantus Insights"]
        self.assertTrue(q.disagree)
        self.assertAlmostEqual(q.vh_margin, 100 * 4 / 92)


class NationalTest(unittest.TestCase):
    def test_generic_ballot_prefers_likely_voters(self):
        gb = polls.generic_ballot(VOTEHUB)
        self.assertEqual(len(gb), 1)
        self.assertEqual(gb.iloc[0].population, "lv")
        self.assertAlmostEqual(gb.iloc[0].margin, 100 * 4 / 88)

    def test_approval_net(self):
        ap = polls.approval(VOTEHUB)
        self.assertEqual((ap.iloc[0].approve, ap.iloc[0].disapprove, ap.iloc[0].net), (42.0, 55.0, -13.0))


class BuildTest(unittest.TestCase):
    def test_build_reads_a_snapshot_folder(self):
        def page(title, text, revid):
            return {"title": title, "revisions": [{"revid": revid, "timestamp": "2026-09-28T03:00:00Z",
                                                   "slots": {"main": {"content": text}}}]}

        def put(path, obj):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(gzip.compress(json.dumps(obj).encode()))

        with tempfile.TemporaryDirectory() as d:
            snap = Path(d) / "2026-09-28" / "0941"
            put(snap / "wikipedia" / "2026-united-states-senate-elections.gz",
                page("2026 United States Senate elections", OVERVIEW, 1))
            put(snap / "wikipedia" / "2026-united-states-senate-special-election-in-ohio.gz",
                page("2026 United States Senate special election in Ohio", PAGE, 123))
            put(snap / "polls" / "votehub.gz", VOTEHUB)
            out = polls.build(snap)
        self.assertEqual(set(out["senate"].race_id), {"OH-S"})
        self.assertEqual(len(out["senate"]), 4)
        self.assertEqual(out["revisions"]["OH-S"], 123)
        self.assertIn("GA", out["missing_pages"])
        self.assertEqual(len(out["generic_ballot"]), 1)
        self.assertEqual(len(out["approval"]), 1)
        self.assertEqual(out["snapshot"], "2026-09-28 09:41")


if __name__ == "__main__":
    unittest.main()
