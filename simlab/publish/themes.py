"""Five candidate visual directions for NotAPoll (docs/creative-directions.md). Each palette's party blue, party red and
simulation colour pass the dataviz validator (all pairs, colour-blind simulation) on its own paper colour; independents
use a labelled neutral."""
from .frame import Theme

BROADSHEET = Theme(
    "The Broadsheet",
    paper="#F4F0E8", ink="#141414", ink2="#58544C", muted="#8C877D", hairline="#DDD6C8", baseline="#C2BBAC",
    strip_bg="#141414", strip_fg="#F4F0E8", accent="#141414",
    dem="#2B5C9E", rep="#C8412F", ind="#8C877D", ai="#0E8C7A", data="#3A3833",
)

LAB = Theme(
    "Lab Notebook",
    paper="#F7F7F2", ink="#1C2A4A", ink2="#4A5670", muted="#7E879A", hairline="#E1DFEC", baseline="#B9C3CF",
    strip_bg="#2A2152", strip_fg="#F7F7F2", accent="#E6DAF3",
    dem="#2F6DB5", rep="#D1432F", ind="#7E879A", ai="#6D2E8C", data="#1C2A4A",
    faces={"serif": "plexsans", "sans": "plexsans", "mono": "plexmono", "hero": "plexsans"},
    head_weight=600, hero_weight=700, head_leading=1.1, texture="grid", highlight="#E6DAF3", tossup="#EEE6F7",
    swing_band=True,
)

NIGHT = Theme(
    "Election Night",
    paper="#0E1218", ink="#F2F0EA", ink2="#B9B7B0", muted="#7D7B75", hairline="#222834", baseline="#3A4150",
    strip_bg="#F2C230", strip_fg="#0E1218", accent="#F2C230",
    dem="#4F8FF7", rep="#E8483C", ind="#7D7B75", ai="#13A08A", data="#D9D7D0",
    faces={"serif": "archivocond", "sans": "archivo", "mono": "plexmono", "hero": "archivocond"},
    head_weight=800, hero_weight=800, head_upper=True, head_leading=0.98, header="chip",
)

CIVIC = Theme(
    "Civic Grid",
    paper="#FAFAF8", ink="#0A0A0A", ink2="#4D4D4D", muted="#8A8A8A", hairline="#E3E3E0", baseline="#BDBDBA",
    strip_bg="#0A0A0A", strip_fg="#FAFAF8", accent="#0A0A0A",
    dem="#1F5FBF", rep="#D93A26", ind="#8A8A8A", ai="#E0A526", data="#2A2A2A",
    faces={"serif": "schibsted", "sans": "schibsted", "mono": "plexmono", "hero": "schibsted"},
    head_weight=800, hero_weight=900, head_leading=1.0, header="bar",
)

RISO = Theme(
    "Riso Print",
    paper="#F1ECDF", ink="#23305E", ink2="#4B5478", muted="#8A8C9E", hairline="#DCD5C4", baseline="#BDB5A2",
    strip_bg="#23305E", strip_fg="#F1ECDF", accent="#FF48B0",
    dem="#0078BF", rep="#E8474F", ind="#8A8C9E", ai="#E0A526", data="#23305E",
    faces={"serif": "bricolage", "sans": "bricolagetext", "mono": "plexmono", "hero": "bricolage"},
    head_weight=800, hero_weight=800, head_leading=1.0, texture="grain", overprint="#FF48B0",
)

DIRECTIONS = [BROADSHEET, LAB, NIGHT, CIVIC, RISO]

# Special editions (Sundays and special days; Matteo, 28 Sep). Party blue, party red and the toss-up purple pass the
# dataviz validator (all pairs, colour-blind simulation) on each paper.
BALLOT = Theme(
    "The Ballot",
    paper="#FBFAF6", ink="#141414", ink2="#4D4B45", muted="#8A877F", hairline="#E2DED4", baseline="#BDB8AC",
    strip_bg="#141414", strip_fg="#FBFAF6", accent="#141414",
    dem="#2F6DB5", rep="#D1432F", ind="#8A877F", ai="#6D2E8C", data="#141414",
    faces={"serif": "franklin", "sans": "franklin", "mono": "plexmono", "hero": "franklin"},
    head_weight=800, hero_weight=800, head_leading=1.02, swing_band=True,
)

FIGHT = Theme(
    "The Main Event",
    paper="#17112E", ink="#F4F1FA", ink2="#BDB6D1", muted="#8A83A3", hairline="#2E2652", baseline="#4A3F75",
    strip_bg="#F4F1FA", strip_fg="#17112E", accent="#9E4FC4",
    dem="#4F8FF7", rep="#F0554A", ind="#8A83A3", ai="#9E4FC4", data="#F4F1FA",
    faces={"serif": "archivocond", "sans": "archivo", "mono": "plexmono", "hero": "archivocond"},
    head_weight=800, hero_weight=800, head_upper=True, head_leading=0.95, swing_band=True,
)

CHAMBER = Theme(
    "The Chamber",
    paper="#F4F1EA", ink="#1B1A2E", ink2="#4E4C60", muted="#8B8898", hairline="#DFDACF", baseline="#BFB9AC",
    strip_bg="#1B1A2E", strip_fg="#F4F1EA", accent="#1B1A2E",
    dem="#2F6DB5", rep="#D1432F", ind="#8B8898", ai="#6D2E8C", data="#1B1A2E",
    faces={"serif": "newsreader", "sans": "plexsans", "mono": "plexmono", "hero": "newsreader"},
    head_weight=600, hero_weight=600, head_leading=1.02, swing_band=True,
)

SEISMO = Theme(
    "The Seismograph",
    paper="#FCF7F0", ink="#1A1A1A", ink2="#4F4B45", muted="#8C877E", hairline="#F0DCCB", baseline="#D9BFA8",
    strip_bg="#1A1A1A", strip_fg="#FCF7F0", accent="#1A1A1A",
    dem="#2F6DB5", rep="#D1432F", ind="#8C877E", ai="#6D2E8C", data="#1A1A1A", tossup="#EEE6F7",
    faces={"serif": "plexsans", "sans": "plexsans", "mono": "plexmono", "hero": "plexsans"},
    head_weight=600, hero_weight=700, head_leading=1.08, swing_band=True,
)

MAP = Theme(
    "The Map",
    paper="#0F1424", ink="#F2F1EC", ink2="#B7B9C4", muted="#7D8194", hairline="#232A40", baseline="#3A4260",
    strip_bg="#F2F1EC", strip_fg="#0F1424", accent="#9E4FC4",
    dem="#4F8FF7", rep="#F0554A", ind="#7D8194", ai="#9E4FC4", data="#F2F1EC",
    faces={"serif": "plexsans", "sans": "plexsans", "mono": "plexmono", "hero": "plexsans"},
    head_weight=700, hero_weight=700, head_leading=1.05, swing_band=True,
)

SPECIALS = [BALLOT, FIGHT, CHAMBER, SEISMO, MAP]
