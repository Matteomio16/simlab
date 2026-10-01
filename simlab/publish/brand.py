"""Profile images and the pinned first post: python -m simlab.publish.brand -> kits/brand/.

- avatar.jpg (1080x1080): the logomark, kept inside the circle crop; used by Instagram, Threads, X and Bluesky
- header-x.jpg (1500x500) and banner-bluesky.jpg (3000x1000): the simulated electorate as a dot map of the lower 48
- pinned/: the intro carousel (the post to pin) with its caption, alt text and thread (post.md), for approval
The avatar is too small to carry the label strip; every other image carries "Social simulation, not a poll".
"""
from __future__ import annotations

import math
from datetime import date
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.path import Path as MPath
from PIL import Image

from . import text
from . import frame
from .frame import DISCLAIMER, HILLS, HILLS_H, HILLS_W, LABEL, MARGIN, OVERLAP, SITE, Slide, face_file, font, hills, pt, typeset
from .geo import outline
from .labnotes import contact_sheet
from .themes import LAB

OUT = Path(__file__).resolve().parents[2] / "kits" / "brand"
KIT = Path(__file__).resolve().parents[2] / "brand" / "final"  # the logo kit (python -m brand.final)
LOWER48 = [s for s in ("AL AZ AR CA CO CT DE FL GA ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND "
                       "OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY DC").split()]
PINNED_DAY = date(2026, 10, 3)


def nation() -> list[np.ndarray]:
    """Lower-48 rings on one shared projection (states.json scales each state by its own latitude; undo that)."""
    rings = []
    for usps in LOWER48:
        rs = [np.array(r) for r in outline(usps)]
        k = math.cos(math.radians(-np.vstack(rs)[:, 1].mean()))
        rings += [np.column_stack([r[:, 0] / k * math.cos(math.radians(38)), r[:, 1]]) for r in rs]
    return rings


def electorate(ax, t, x: float, y: float, w: float, h: float, n: int = 1400, seed: int = 26):
    """The simulated electorate: dots inside the lower 48, mostly blue and red with purple swing voters."""
    rings = nation()
    pts = np.vstack(rings)
    (x0, y0), (x1, y1) = pts.min(0), pts.max(0)
    k = min(w / (x1 - x0), h / (y1 - y0))
    ox, oy = x + (w - (x1 - x0) * k) / 2, y + (h - (y1 - y0) * k) / 2
    rings = [np.column_stack([ox + (r[:, 0] - x0) * k, oy + (r[:, 1] - y0) * k]) for r in rings]
    area = sum(abs(np.dot(r[:, 0], np.roll(r[:, 1], 1)) - np.dot(r[:, 1], np.roll(r[:, 0], 1))) / 2 for r in rings)
    step = (area / n) ** 0.5
    gx, gy = np.meshgrid(np.arange(x, x + w, step) + step / 2, np.arange(y, y + h, step) + step / 2)
    grid = np.column_stack([gx.ravel(), gy.ravel()])
    inside = np.zeros(len(grid), bool)
    for r in rings:
        inside |= MPath(r).contains_points(grid)
    dots = grid[inside]
    rng = np.random.default_rng(seed)
    c = rng.choice([t.dem, t.rep, t.ai], size=len(dots), p=[0.44, 0.44, 0.12])
    ax.scatter(dots[:, 0], dots[:, 1], s=pt(step * 0.7) ** 2, c=c, lw=0, zorder=3)


def canvas(w: int, h: int, t, scale: int = 1):
    fig = plt.figure(figsize=(w / 100, h / 100), dpi=100 * scale)
    fig.patch.set_facecolor(t.paper)
    ax = fig.add_axes((0, 0, 1, 1))
    ax.set_xlim(0, w)
    ax.set_ylim(h, 0)
    ax.axis("off")
    return fig, ax


def put(ax, x, y, s, role, weight, px, color, t, **kw):
    return ax.text(x, y, typeset(s), fontproperties=font(role, weight, px, t), color=color, **kw)


def mark(ax, x, y, size, color, centre):
    ax.add_patch(plt.Rectangle((x, y), size, size, fill=False, ec=color, lw=pt(size / 14), zorder=3))
    step, r = size / 4, size * 0.085
    for i in range(3):
        for j in range(3):
            ax.add_patch(plt.Circle((x + step * (j + 1), y + step * (i + 1)), r, color=centre if (i, j) == (1, 1)
                                    else color, lw=0, zorder=3))


def save(fig, path: Path, size: tuple[int, int]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, format="jpeg", facecolor=fig.get_facecolor(),
                pil_kwargs={"quality": 94, "subsampling": 0, "optimize": True})
    plt.close(fig)
    with Image.open(path) as im:
        if im.size != size:
            raise ValueError(f"{path}: {im.size}, expected {size}")
    return path


def avatar(t=LAB) -> Path:
    """The logomark alone on indigo, sized for the circular crop. With the H1 logo: the hills rising from the bottom
    edge, as in the logo kit's avatar."""
    fig, ax = canvas(1080, 1080, t)
    ax.add_patch(plt.Rectangle((0, 0), 1080, 1080, color=t.strip_bg, lw=0))
    if frame.LOGO == "hills":
        h = 1080 * .56
        hills(ax, (1080 - HILLS_W * h / HILLS_H) / 2, 1080 + h * .02, h, HILLS["dark"])
    else:
        mark(ax, 1080 / 2 - 260, 1080 / 2 - 260, 520, t.paper, "#B98AD6")
    return save(fig, OUT / "avatar.jpg", (1080, 1080))


def lockup(ax, t, x: float, baseline: float, px: int):
    """Mark and "NotAPoll.org" on one baseline, following the frame's logo and wordmark switches."""
    from PIL import ImageFont
    if frame.WORDMARK == "serif":
        f = face_file("newsreader", 560)
        fp, pf = frame.FontProperties(fname=f, size=pt(px)), ImageFont.truetype(str(f), px)
    else:
        from .frame import pil_font
        fp, pf = font("serif", 700, px, t), pil_font("serif", 700, px, t)
    if frame.LOGO == "hills":
        cap = frame.cap_height(fp.get_file()) * px
        h = 1.18 * cap
        hills(ax, x, baseline, h, (t.dem, t.rep, OVERLAP["light"]))
        x += HILLS_W * h / HILLS_H + 0.42 * cap
        tld = OVERLAP["light"]
    else:
        mark(ax, x, baseline - px * .9, px * 1.08, t.ink, t.ai)
        x += px * 1.46
        tld = t.ai
    ax.text(x, baseline, "NotAPoll", fontproperties=fp, color=t.ink, va="baseline")
    ax.text(x + pf.getlength("NotAPoll"), baseline, ".org", fontproperties=fp, color=tld, va="baseline")


def header(t=LAB, w: int = 1500, h: int = 500, scale: int = 1, name: str = "header-x.jpg") -> Path:
    """Wordmark and promise on the left (kept above the profile photo, which covers the bottom left), the simulated
    electorate on the right, the swing band along the bottom."""
    fig, ax = canvas(w, h, t, scale)
    for gx in np.arange(0, w + 1, 30):
        ax.plot([gx, gx], [0, h], color=t.hairline, lw=pt(1), zorder=0)
    for gy in np.arange(0, h + 1, 30):
        ax.plot([0, w], [gy, gy], color=t.hairline, lw=pt(1), zorder=0)
    x = 70
    lockup(ax, t, x, 112, 52)
    put(ax, x, 170, "The 2026 midterms,", "serif", 600, 56, t.ink, t, va="top")
    put(ax, x, 236, "simulated every day.", "serif", 600, 56, t.ink, t, va="top")
    put(ax, x, 324, LABEL.upper(), "mono", 600, 24, t.ai, t, va="top")
    electorate(ax, t, w * 0.53, 40, w * 0.43, h - 110)
    for i, c in enumerate((t.dem, t.ai, t.rep)):
        ax.add_patch(plt.Rectangle((w * i / 3, h - 12), w / 3, 12, color=c, lw=0, zorder=4))
    return save(fig, OUT / name, (w * scale, h * scale))


def pinned(t=LAB):
    """The intro carousel, the post to pin (communication.md): a live experiment, people first, short slides; the
    method lives on the website. No "start here" wording anywhere (Matteo, 1 Oct)."""
    a = Slide(PINNED_DAY, "THE 2026 MIDTERMS", t)
    a.headline("Democracy, rehearsed.", px=104)
    a.dek("A live experiment: forecasting the 2026 midterms by modelling how groups of voters react to the news. "
          "Every day until 3 November.", px=38)
    electorate(a.ax, t, MARGIN, a.y + 6, a.width, 300, n=900)
    a.y += 320
    a.text("Illustration, not a forecast.", px=28, color=t.ink2)

    b = Slide(PINNED_DAY, "HOW IT WORKS", t)
    b.headline("Voter groups, reacting to the news.", px=80)
    for n, line in enumerate(["We start from past results and the poll average.",
                              "More than a thousand voter personas react to each day’s events.",
                              "Each race is played out 40,000 times."], 1):
        b.y += 10
        top = b.y
        b._put(MARGIN, top - 8, str(n), "hero", t.hero_weight, 88, t.ai, va="top")
        b.text(line, "serif", 600, 44, x=MARGIN + 96, width=b.width - 96, after=0.9)
    b.note("The full method, step by step: notapoll.org", y=b.y + 30, width=620)

    c = Slide(PINNED_DAY, "WHAT IT ISN’T", t)
    c.headline("Not a poll. Nobody is asked anything.", px=88)
    c.text("Our number always sits beside the poll average, the prediction markets and the Cook Political Report.",
           px=40, color=t.ink2, after=1.2)
    c.note("Between 35 and 65 in 100, we call it a toss-up.", width=640)

    d = Slide(PINNED_DAY, "KEEPING SCORE", t)
    d.headline("Right or wrong, you’ll see it.", px=88)
    rows = [("Daily", "Where the races are heading, and why."),
            ("Mondays", "From 19 October: our record against the poll average, the markets and Cook."),
            ("3 Nov", "The final forecast. Then the results decide.")]
    for head, body in rows:
        d.rule(t.hairline, after=22)
        top = d.y
        d._put(MARGIN, top, head.upper(), "mono", 600, 28, t.ai, va="top")
        d.text(body, px=38, x=MARGIN + 220, width=d.width - 220, after=0.8)
    d.rule(t.hairline)
    slides = [(a, "Democracy, rehearsed. A live experiment forecasting the 2026 midterms by modelling how groups of "
                  "voters react to the news, over an illustrative dot map of the United States."),
              (b, "How it works: start from past results and the poll average; more than a thousand voter personas "
                  "react to each day's events; each race is played out 40,000 times. Full method at notapoll.org."),
              (c, "Not a poll: nobody is asked anything. Our number always sits beside the poll average, the "
                  "prediction markets and the Cook Political Report. 35 to 65 in 100 is a toss-up."),
              (d, "Keeping score: daily updates, a public record every Monday from 19 October, the final forecast on "
                  "3 November.")]
    for s, _ in slides:
        s.source("Forecasts go public on Monday 12 October.")
    caption = (
        "Democracy, rehearsed.\n\n"
        "From 12 October we'll forecast every Senate race and about 40 House races of the 2026 midterms, every day "
        "until 3 November. Not by asking people, but by modelling how groups of voters react to each day's news.\n\n"
        "More than a thousand voter personas, built from real survey answers by party, race and education in each "
        "state, take in the day's events. Then every race is played out 40,000 times.\n\n"
        "Our number always sits beside the poll average, the prediction markets and Cook. From 19 October, every "
        "Monday, we publish how we're doing against all of them. Right or wrong, you'll see it.\n\n"
        f"#midterms2026 #elections\n\n{DISCLAIMER}")
    thread = [f"Democracy, rehearsed. A live experiment: forecasting the 2026 midterms by modelling how groups of "
              f"voters react to the news, every day until 3 November. {LABEL}.",
              "More than a thousand voter personas, built from real survey answers, take in each day's events. Then "
              "every race is played out 40,000 times.",
              "Our number always sits beside the poll average, prediction markets and Cook. Every Monday from 19 Oct "
              "we publish our record against them. Right or wrong.",
              f"Forecasts from 12 October. How it works: {SITE}"]
    return slides, caption, thread


ALLOW = ("survey",)  # "real survey answers": the real respondents the personas are built from, not our output


BIOS = {
    "instagram": ("Democracy, rehearsed.\nThe 2026 midterms, simulated every day with voter personas built from "
                  "real survey answers.\nNot a poll.", 150),
    "x": ("Democracy, rehearsed. The 2026 midterms, simulated every day with voter personas built from real survey "
          "answers, each race played out 40,000 times. Not a poll.", 160),
    "bluesky": ("Democracy, rehearsed.\n\nThe 2026 US midterms, simulated every day: voter personas built from real "
                "survey answers react to the "
                "news, then every race is played out 40,000 times.\n\nNot a poll. Shown beside the poll average, "
                "markets and Cook; scored weekly.", 256),
}


def headers() -> list[Path]:
    """The X header and Bluesky banner: the logo kit's approved files when present (Matteo, 29 Sep), else ours."""
    import shutil
    if frame.LOGO == "hills" and (KIT / "header-x.jpg").exists() and (KIT / "banner-bluesky.jpg").exists():
        OUT.mkdir(parents=True, exist_ok=True)
        return [Path(shutil.copy(KIT / n, OUT / n)) for n in ("header-x.jpg", "banner-bluesky.jpg")]
    return [header(), header(w=1500, h=500, scale=2, name="banner-bluesky.jpg")]


AVATAR_PICKED = True  # Matteo, 29 Sep: D on white; brand/final/avatar.jpg is copied (file name stays if it changes)


def write():
    import shutil
    if frame.LOGO != "hills":
        out = [avatar()]
    elif AVATAR_PICKED:
        out = [Path(shutil.copy(KIT / "avatar.jpg", OUT / "avatar.jpg"))]
    else:
        out = []  # kits/brand/avatar.jpg stays as it is until the pick
    out += headers()
    slides, caption, thread = pinned()
    paths = [s.save(OUT / "pinned" / f"slide-{i}.jpg") for i, (s, _) in enumerate(slides, 1)]
    contact_sheet(paths, OUT / "pinned" / "contact.jpg", scale=0.3)
    problems = [f"caption: {p}" for p in text.check(caption, allow=ALLOW)]
    problems += [f"thread 1: {p}" for p in text.check(thread[0], allow=ALLOW)]
    problems += [f"thread {i}: {p}" for i, t in enumerate(thread, 1) for p in text.check(t, caption=False, allow=ALLOW)]
    problems += [f"bio {k}: {p}" for k, (b, _) in BIOS.items() for p in text.check(b, caption=False, allow=ALLOW)]
    problems += [f"thread {i}: {len(t)} characters" for i, t in enumerate(thread, 1) if len(t) > 280]
    problems += [f"bio {k}: {len(b)} of {n} characters" for k, (b, n) in BIOS.items() if len(b) > n]
    notes = sorted({n for s in [caption, *thread, *(b for b, _ in BIOS.values())] for n in text.style(s)})
    md = ["# Brand kit and pinned post", "", "Drafts for Matteo's approval. Nothing here is posted.", "", "## Checks", ""]
    md += [f"- {p}" for p in problems] or ["- All rules pass."]
    md += ["", "## Style notes", ""] + ([f"- {n}" for n in notes] or ["- None."])
    md += ["", "## Bios", ""]
    for k, (b, n) in BIOS.items():
        md += [f"**{k}** ({len(b)} of {n} characters)", "", "```", b, "```", ""]
    md += ["## Pinned post: slides and alt text", ""]
    md += [f"{i}. `slide-{i}.jpg`: {alt}" for i, (_, alt) in enumerate(slides, 1)]
    md += ["", "## Instagram caption", "", caption, "", "## Thread for X, Threads and Bluesky", ""]
    md += [f"{i}/ ({len(t)} characters) {t}" for i, t in enumerate(thread, 1)]
    (OUT / "post.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"{OUT}: {len(out)} profile images, {len(paths)} slides; " + ("; ".join(problems) or "all rules pass"))


if __name__ == "__main__":
    write()
