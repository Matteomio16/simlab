"""The comparison pages for the logo rounds: python -m brand.explore [3|4] -> brand/explore/round<N>.html.

Every candidate in brand.marks at 16 and 32 px, in a circle crop, on paper and on indigo, locked up with the
wordmark, and in context (Instagram profile, X feed, a Lab notes slide). Kit images come from the main checkout's
kits/ folder (gitignored), embedded as small JPEGs.
"""
from __future__ import annotations

import base64
import io
import json
from pathlib import Path

from PIL import Image

from . import marks as m
from . import round4

ROOT = Path(__file__).resolve().parent
KITS = next(p / "kits" for p in [ROOT.parent, *ROOT.parents] if (p / "kits" / "labnotes").exists())
DIRECTIONS3 = {
    "A": ("The synthetic voter", "A character, like 538's fox: a person visibly made of voters, who can react in posts."),
    "B": ("The swing N", "The letter N drawn as voters, its diagonal the swing voters crossing from one side to the other."),
    "C": ("The broken pie", "A poll's pie chart coming apart into individual voters: what we do that a poll doesn't."),
    "D": ("The overlap", "Blue and red overlap in purple, the brand colour; it says why the brand is purple."),
}
DIRECTIONS4 = {
    "C3": ("The voter pie, developed", "You kept C3. The pie is the thing a poll reports; ours is made of individual voters, "
           "and one slice is pulled out."),
    "D3": ("The dotted overlap, developed", "You kept D3. Two electorates made of voters; purple where they share ground."),
    "E": ("Logic notation", "A new language: type, no dots. The name written the way a logician writes \"not P\". "
          "It says rigour and lab, and it's a sign nobody in politics owns."),
    "F": ("Forecast lines", "A new language: lines. The spaghetti plot and the cone from hurricane forecasts, which "
          "every American has seen on TV. It says forecast, many futures, uncertainty shown honestly."),
    "G": ("Opinion map", "A new language: cartography. The electorate drawn as a landscape with contour lines. "
          "It says mapping the social dynamics, in your words."),
}


def roster4():
    return {k: (n, d, f or m.MARKS[k][2]) for k, (n, d, f) in round4.MARKS.items()}


ROUNDS = {
    "3": ("NotAPoll Logo Round 3", DIRECTIONS3, lambda: m.MARKS, "intro_round3.html", "A2"),
    "4": ("NotAPoll Logo Round 4", DIRECTIONS4, roster4, "intro_round4.html", "C3.2"),
}
TILES = ["brand/pinned/slide-1.jpg", "labnotes/01/slide-1.jpg", "specials/3-chamber.jpg", "labnotes/02/slide-1.jpg",
         "brand/pinned/slide-2.jpg", "specials/1-ballot.jpg", "labnotes/03/slide-1.jpg", "specials/4-seismograph.jpg",
         "brand/pinned/slide-3.jpg"]
STANDINS = [("538", "#1A1A1A", "#F28E2B", "538", "@FiveThirtyEight"), ("SB", "#0D2B45", "#FFFFFF", "Silver Bulletin",
            "@SilverBulletin"), ("P", "#1652F0", "#FFFFFF", "Polymarket", "@Polymarket"),
            ("K", "#0B0B0B", "#28D17C", "Kalshi", "@Kalshi"), ("T", "#FFFFFF", "#111111", "NYT Politics", "@nytpolitics")]


def jpeg(rel: str, width: int, q: int = 78) -> str:
    im = Image.open(KITS / rel).convert("RGB")
    im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=q, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def poses() -> list[tuple[str, str]]:
    base = {"lean": 0, "lift": 0, "head_role": "accent"}
    rows = [("Neutral", {}), ("Leans one way", {"lean": -9}), ("Leans the other", {"lean": 9}),
            ("Fired up: will vote", {"lift": 8}), ("Switched off: stays home", {"lift": -3, "head_role": "faint"})]
    return [(label, m.svg(m.voter_head(**{**base, **kw}), m.LIGHT, .1, True)) for label, kw in rows]


def lockup(svg: str, dark: bool) -> str:
    return (f'<div class="lockup {"on-dark" if dark else "on-light"}"><span class="lk-mark">{svg}</span>'
            f'<span class="wm">NotAPoll<span class="tld">.org</span></span></div>')


def card(key: str, entry) -> str:
    name, note, fn = entry
    s = fn()
    cells = [
        ("Paper", m.svg(s, m.LIGHT, .14, True), "big"),
        ("Avatar", m.svg(s, m.DARK, .3, True, True), "big round"),
        ("Avatar, paper", m.svg(s, m.LIGHT, .3, True, True), "big round"),
    ]
    small = "".join(
        f'<div class="px"><div class="px-row">'
        f'<span style="width:{n}px;height:{n}px">{m.svg(s, m.LIGHT, .08, True)}</span>'
        f'<span style="width:{n}px;height:{n}px">{m.svg(s, m.DARK, .3, True, True)}</span>'
        f'<span style="width:{n}px;height:{n}px">{m.svg(s, m.LIGHT, .3, True, True)}</span>'
        f'</div><span class="lbl">{n} px</span></div>' for n in (32, 16))
    big = "".join(f'<figure class="cell {cls}">{svg}<figcaption class="lbl">{lab}</figcaption></figure>'
                  for lab, svg, cls in cells)
    return (f'<article class="cand" id="{key}"><header><span class="code">{key}</span><h3>{name}</h3>'
            f'<p>{note}</p></header><div class="tests">{big}<div class="smalls">{small}</div>'
            f'<div class="locks">{lockup(m.svg(s, m.LIGHT), False)}{lockup(m.svg(s, m.DARK), True)}</div></div></article>')


def build(rnd: str = "4") -> Path:
    title, directions, roster, intro, first = ROUNDS[rnd]
    marks = roster()
    data = {k: {"name": v[0], "light": m.svg(v[2](), m.LIGHT, .3, True, True), "dark": m.svg(v[2](), m.DARK, .3, True, True),
                "bare_light": m.svg(v[2](), m.LIGHT), "bare_dark": m.svg(v[2](), m.DARK)} for k, v in marks.items()}
    sections = []
    for d, (head, pitch) in directions.items():
        keys = [k for k in marks if k.startswith(d)]
        extra = ""
        if d == "A":
            extra = ('<div class="poses"><h4>How Nota (A2) reacts in posts</h4><div class="pose-row">' +
                     "".join(f'<figure>{svg}<figcaption class="lbl">{lab}</figcaption></figure>' for lab, svg in poses())
                     + '</div><p class="aside">Direction of the lean is the vote; the head rising or fading is '
                     'turnout, the two things the engine simulates.</p></div>')
        sections.append(f'<section class="dir"><div class="dir-head"><span class="code">{d}</span><h2>{head}</h2>'
                        f'<p>{pitch}</p></div>{"".join(card(k, marks[k]) for k in keys)}{extra}</section>')
    lineup = "".join(f'<button class="lu" data-k="{k}" aria-label="{k} {v[0]}">{data[k]["dark"]}'
                     f'<span class="lbl">{k}</span></button>' for k, v in marks.items())
    tiles = "".join(f'<img src="{jpeg(t, 300)}" alt="">' for t in TILES)
    slide = jpeg("labnotes/01/slide-1.jpg", 1080, 84)
    standins = "".join(f'<div class="xpost"><span class="xav" style="background:{bg};color:{fg}">{txt}</span>'
                       f'<div class="xbody"><div class="xmeta"><b>{nm}</b> <span>{h} · 3h</span></div>'
                       f'<p>{"Senate forecast update: our model now gives Democrats a 41 in 100 chance." if i == 0 else "Who wins the Senate? Trading is open on all 35 races." if i == 2 else "The midterms are 36 days away. Here is where the key races stand."}</p></div></div>'
                       for i, (txt, bg, fg, nm, h) in enumerate(STANDINS[:3]))
    html = TEMPLATE.replace("%TITLE%", title).replace("%INTRO%", (ROOT / intro).read_text(encoding="utf-8"))         .replace('let first = "A2"', f'let first = "{first}"').replace("%SECTIONS%", "".join(sections)).replace("%LINEUP%", lineup).replace("%TILES%", tiles) \
        .replace("%SLIDE%", slide).replace("%STANDINS%", standins).replace("%DATA%", json.dumps(data))
    out = ROOT / "explore" / f"round{rnd}.html"
    out.parent.mkdir(exist_ok=True)
    out.write_bytes(html.encode("ascii", "xmlcharrefreplace"))
    return out


TEMPLATE = (ROOT / "explore_template.html").read_text(encoding="utf-8") if (ROOT / "explore_template.html").exists() else ""

if __name__ == "__main__":
    import sys
    print(build(sys.argv[1] if len(sys.argv) > 1 else "4"))
