"""The final-kit review page: python -m brand.final_page -> brand/explore/final.html (run brand.final first)."""
from __future__ import annotations

import base64
import io

from PIL import Image

from .final import AVATARS, OUT, ROOT


def uri(name: str, width: int | None = None) -> str:
    p = OUT / name
    if p.suffix == ".svg":
        return "data:image/svg+xml;base64," + base64.b64encode(p.read_bytes()).decode()
    im = Image.open(p)
    if width and im.width > width:
        im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    buf = io.BytesIO()
    if p.suffix == ".png":
        im.save(buf, "PNG", optimize=True)
        return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()
    im.convert("RGB").save(buf, "JPEG", quality=88)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def avatars() -> str:
    rows = [("avatar-centred", "A. Centred, indigo", False), ("avatar", "B. Landscape crop, indigo", True),
            ("avatar-centred-paper", "C. Centred, paper", False), ("avatar-paper", "D. Landscape crop, paper", False)]
    out = []
    for name, label, rec in rows:
        src = uri(f"{name}.svg")
        smalls = "".join(f'<img src="{src}" width="{n}" height="{n}" alt="">' for n in (48, 32, 20))
        out.append(f'<figure class="av"><img class="round" src="{src}" alt="{label}"><figcaption>'
                   f'<span class="lbl">{label}{" · exported as avatar.jpg" if rec else ""}</span>'
                   f'<span class="smalls">{smalls}</span></figcaption></figure>')
    return "".join(out)


def options() -> str:
    out = []
    for key, (_, note) in AVATARS.items():
        cells = []
        for tag, word in (("indigo", "indigo"), ("white", "white")):
            src = uri(f"avatar-options/{key}-{tag}.svg")
            smalls = "".join(f'<img src="{src}" width="{n}" height="{n}" alt="">' for n in (48, 32, 20))
            cells.append(f'<figure class="av"><img class="round" src="{src}" alt="{key} on {word}"><figcaption>'
                         f'<span class="pickname">{key} {word}</span><span class="smalls">{smalls}</span></figcaption></figure>')
        out.append(f'<div class="opt"><p><b>{key}</b> &middot; {note}</p><div class="avs two">{"".join(cells)}</div></div>')
    return "".join(out)


def xprofile(header: str, avatar: str, name: str) -> str:
    return (f'<div class="xprof"><div class="hwrap"><img class="hdr" src="{uri(header, 1500)}" alt="X header">'
            f'<img class="xav" src="{uri(avatar)}" alt=""></div><div class="xname"><b>NotAPoll.org</b>'
            f'<span>@notapoll</span><p>Democracy, rehearsed. The 2026 US midterms, simulated every day by synthetic '
            f'voters and played out 40,000 times. Not a poll. By Scalia Studio</p></div>'
            f'<span class="lbl">{name}</span></div>')


def build():
    html = TEMPLATE
    subs = {
        "%MARK_L%": uri("mark-light.svg"), "%MARK_D%": uri("mark-dark.svg"), "%MARK_M%": uri("mark-mono.svg"),
        "%LOCK_L%": uri("lockup-light.svg"), "%LOCK_D%": uri("lockup-dark.svg"),
        "%STACK_L%": uri("lockup-stacked-light.svg"), "%STACK_D%": uri("lockup-stacked-dark.svg"),
        "%AVATARS%": avatars(),
        "%OPTIONS%": options(),
        "%FONTS%": uri("font-compare.png"),
        "%XPROF%": xprofile("header-x.jpg", "avatar.svg", "X profile · header light, avatar B")
        + xprofile("header-x.jpg", "avatar-centred.svg", "X profile · header light, avatar A")
        + xprofile("header-x-dark.png", "avatar-paper.svg", "X profile · header dark, avatar D"),
        "%BSKY%": uri("banner-bluesky.jpg", 1500),
        "%FAV%": "".join(f'<img src="{uri(f"favicon-{n}.png")}" width="{n}" height="{n}" alt="">' for n in (16, 32, 48))
        + f'<img src="{uri("favicon-180.png")}" width="90" height="90" alt="">',
    }
    for k, v in subs.items():
        html = html.replace(k, v)
    out = ROOT / "explore" / "final.html"
    out.parent.mkdir(exist_ok=True)
    out.write_bytes(html.encode("ascii", "xmlcharrefreplace"))
    return out


TEMPLATE = """<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>NotAPoll Brand Kit</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Newsreader:opsz,wght@6..72,400;6..72,560&family=IBM+Plex+Sans:wght@400;500&family=IBM+Plex+Mono:wght@500&display=swap">
<style>
:root{--paper:#F5F3EE;--sheet:#FBFAF7;--ink:#111110;--muted:#67635B;--rule:#DAD6CC;--accent:#7A4FC0;
  --serif:"Newsreader",Georgia,serif;--sans:"IBM Plex Sans",system-ui,sans-serif;--mono:"IBM Plex Mono",ui-monospace,monospace}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--paper:#16122B;--sheet:#1E1938;--ink:#F1EEF7;--muted:#A8A2C2;--rule:#322A56;--accent:#C4A0E0;color-scheme:dark}}
:root[data-theme="dark"]{--paper:#16122B;--sheet:#1E1938;--ink:#F1EEF7;--muted:#A8A2C2;--rule:#322A56;--accent:#C4A0E0;color-scheme:dark}
*{box-sizing:border-box}
body{background:var(--paper);color:var(--ink);font:15px/1.55 var(--sans);padding-inline:clamp(16px,4vw,48px);padding-block:32px 80px}
main{max-width:1180px;margin:0 auto;display:grid;gap:52px}
h1,h2{font-family:var(--serif);font-weight:560;margin:0;line-height:1.1;text-wrap:balance}
h1{font-size:clamp(34px,5vw,54px)}h2{font-size:28px}
p{margin:0;max-width:68ch}
.lbl{font:500 11px/1.3 var(--mono);letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
section{display:grid;gap:16px}
.head{border-top:2px solid var(--ink);padding-top:14px;display:grid;gap:6px}
.head p{color:var(--muted)}
.duo{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:16px}
.tile{display:grid;place-items:center;padding:36px 24px;min-height:220px}
.tile img{max-width:100%;max-height:170px}
.on-l{background:#F5F3EE}.on-d{background:#2A2152}
.avs{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:20px}
.av{margin:0;display:grid;gap:10px}
.av .round{width:100%;max-width:240px;border-radius:50%;display:block}
.av figcaption{display:grid;gap:8px}
.smalls{display:flex;gap:10px;align-items:center}
.smalls img{border-radius:50%}
.xprofs{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:24px}
.xprof{background:#fff;color:#0F1419;border:1px solid var(--rule);position:relative;font:14px/1.4 system-ui,sans-serif;padding-bottom:14px}
.xprof .hdr{width:100%;display:block;aspect-ratio:3/1;object-fit:cover}
.hwrap{position:relative}
.xprof .xav{position:absolute;left:14px;bottom:0;width:22%;border-radius:50%;border:4px solid #fff;transform:translateY(50%)}
.xprof .xname{padding:12% 14px 8px;display:grid;gap:2px}
.xprof .xname span{color:#536471}
.xprof .lbl{padding:0 14px;color:#536471}
.wide img{width:100%;display:block;border:1px solid var(--rule)}
.favs{display:flex;gap:18px;align-items:end;flex-wrap:wrap}
.opt{display:grid;gap:10px;padding-bottom:18px;border-bottom:1px solid var(--rule)}
.avs.two{grid-template-columns:repeat(auto-fit,minmax(220px,300px))}
.pickname{font:600 20px/1.2 var(--serif)}
.pick{background:var(--sheet);border:1px solid var(--rule);padding:20px;display:grid;gap:10px}
.pick ol{margin:0;padding-left:20px;display:grid;gap:8px;max-width:84ch}
.files{font:13px/1.6 var(--mono);color:var(--muted);columns:2 280px}
</style>
<main>
  <section>
    <span class="lbl">Brand kit &middot; H1 &middot; 29 Sep 2026 &middot; for Matteo</span>
    <h1>NotAPoll.org, final kit</h1>
    <p>The mark is H1: a blue hill and a red hill, purple where they overlap. Side on, they are the two electorates'
      opinion curves. Below are the mark, two ways to set it with the wordmark, four avatar backgrounds, the X header,
      the Bluesky banner and the favicon. Everything is drawn from one geometry, so the PNGs match the SVG masters
      exactly, and the wordmark is outlined Newsreader, so no file depends on an installed font.</p>
    <div class="pick"><span class="lbl">My read</span><ol>
      <li><b>Lockup: horizontal, on a shared ground.</b> The hills stand on the same baseline as the letters, a little taller than a capital, so the name and the landscape share one ground line. The stacked version is for square spaces: the site's footer, the end card of a video.</li>
      <li><b>Avatar: B, the landscape crop on indigo.</b> The hills rise from the bottom of the circle and run off its edge. At 32 px it's the most readable of the four and the most confident, the way a fashion house crops its monogram. A is the safe option.</li>
      <li><b>Headers on paper.</b> The paper header sets off the indigo avatar, and the hills stand on the bottom edge on the right, clear of where X puts the avatar.</li>
    </ol></div>
  </section>

  <section id="avatar"><div class="head"><h2>Avatar: pick one</h2><p>Bigger hills, blue and red with the purple overlap in the middle, each on indigo and on white. B and D from the last sheet were the same crop on indigo and on white, so they are both D here. Answer in two words, for example "D white".</p></div>
    %OPTIONS%</section>

  <section id="font"><div class="head"><h2>Wordmark font: A or B?</h2><p>A is the kit's Newsreader, the serif you locked. B is IBM Plex Sans Bold, which the Lab Notebook slides set today. Same hills, same colours; the bottom two rows are a slide header at actual size. One word is enough: A or B.</p></div>
    <div class="wide"><img src="%FONTS%" alt="Newsreader and IBM Plex Sans wordmarks side by side"></div></section>

  <section><div class="head"><h2>The mark</h2><p>On paper, on indigo, and in one colour for print and places that can't take the party colours.</p></div>
    <div class="duo"><div class="tile on-l"><img src="%MARK_L%" alt="Mark on paper"></div>
      <div class="tile on-d"><img src="%MARK_D%" alt="Mark on indigo"></div>
      <div class="tile on-l"><img src="%MARK_M%" alt="Mark in one colour"></div></div></section>

  <section><div class="head"><h2>With the wordmark</h2><p>Horizontal: the hills share the letters' baseline. Stacked: the hills centred over the name.</p></div>
    <div class="duo"><div class="tile on-l"><img src="%LOCK_L%" alt="Horizontal lockup on paper"></div>
      <div class="tile on-d"><img src="%LOCK_D%" alt="Horizontal lockup on indigo"></div>
      <div class="tile on-l"><img src="%STACK_L%" alt="Stacked lockup on paper"></div>
      <div class="tile on-d"><img src="%STACK_D%" alt="Stacked lockup on indigo"></div></div></section>

  <section><div class="head"><h2>Avatar backgrounds</h2><p>Circle crop, then 48, 32 and 20 px.</p></div>
    <div class="avs">%AVATARS%</div></section>

  <section><div class="head"><h2>X profile</h2><p>The header at 1500 &times; 500 with the avatar overlapping it the way X does.</p></div>
    <div class="xprofs">%XPROF%</div></section>

  <section><div class="head"><h2>Bluesky banner</h2><p>3000 &times; 1000, the same layout.</p></div>
    <div class="wide"><img src="%BSKY%" alt="Bluesky banner"></div></section>

  <section><div class="head"><h2>Favicon</h2><p>An indigo tile with the hills standing on it: 16, 32, 48 and 180 px (the last for phones' home screens).</p></div>
    <div class="favs">%FAV%</div></section>

  <section><div class="head"><h2>Files</h2><p>In <code>brand/final/</code>, rebuilt by <code>python -m brand.final</code>.</p></div>
    <div class="files">mark-light.svg / .png<br>mark-dark.svg / .png<br>mark-mono.svg / .png<br>lockup-light.svg / .png<br>lockup-dark.svg / .png<br>lockup-stacked-light.svg / .png<br>lockup-stacked-dark.svg / .png<br>avatar.svg / .png / .jpg (1080, option B)<br>avatar-centred, avatar-centred-paper, avatar-paper (.svg / .png)<br>header-x.svg / .png / .jpg (1500 &times; 500)<br>header-x-dark.svg / .png<br>banner-bluesky.svg / .png / .jpg (3000 &times; 1000)<br>favicon.svg, favicon.ico, favicon-16/32/48/180.png</div></section>
</main>
"""

if __name__ == "__main__":
    print(build())
