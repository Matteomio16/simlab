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
    paper="#F7F7F2", ink="#1C2A4A", ink2="#4A5670", muted="#7E879A", hairline="#DCE5EA", baseline="#B9C3CF",
    strip_bg="#1C2A4A", strip_fg="#F7F7F2", accent="#F3E27A",
    dem="#2F6DB5", rep="#D1432F", ind="#7E879A", ai="#D4A017", data="#1C2A4A",
    faces={"serif": "plexsans", "sans": "plexsans", "mono": "plexmono", "hero": "plexsans"},
    head_weight=600, hero_weight=700, head_leading=1.1, texture="grid", highlight="#F3E27A",
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
