"""Profile images and the pinned first post: python -m simlab.publish.brand -> kits/brand/.

- avatar.jpg (1080x1080): the logomark, kept inside the circle crop; used by Instagram, Threads, X and Bluesky
- header-x.jpg (1500x500) and banner-bluesky.jpg (3000x1000): the simulated electorate as a dot map of the lower 48
- pinned/: the "Start here" carousel with its caption, alt text and thread (post.md), for Matteo's approval
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
from .frame import HILLS, HILLS_H, HILLS_W, LABEL, MARGIN, OVERLAP, SITE, Slide, face_file, font, hills, pt, typeset
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
    """The Start here carousel."""
    k = "START HERE"
    a = Slide(PINNED_DAY, k, t)
    a.headline("The 2026 midterms, simulated every day.", px=92)
    a.dek("Synthetic voters react to each day's news. Then we play every race out 40,000 times.", px=38)
    electorate(a.ax, t, MARGIN, a.y + 10, a.width, 430, n=1100)
    a.y += 470
    a.text("Swipe for how it works.", "mono", 600, 30, t.ai)

    b = Slide(PINNED_DAY, f"{k} · HOW IT WORKS", t)
    b.headline("Three steps, every morning.", px=80)
    steps = [("Where each race starts", "Real statistics: past results, the economy and the poll average."),
             ("How the news moves it", "Synthetic voters, built from real data on how groups of Americans "
                                       "vote, react to the day's events."),
             ("Who wins, and how often", "Each race is played out 40,000 times. The share won is the chance.")]
    for n, (head, body) in enumerate(steps, 1):
        b.y += 10
        top = b.y
        b._put(MARGIN, top - 8, str(n), "hero", t.hero_weight, 96, t.ai, va="top")
        b.text(head, "serif", 600, 46, x=MARGIN + 100, width=b.width - 100, after=0.2)
        b.text(body, px=34, color=t.ink2, x=MARGIN + 100, width=b.width - 100, after=0.9)

    c = Slide(PINNED_DAY, f"{k} · WHAT IT ISN'T", t)
    c.headline("Not a poll. Nobody was asked anything.", px=88)
    c.text("Our voters are synthetic. They stand in for groups of people; they are not people.", px=38,
           color=t.ink2, after=1.0)
    c.text("So every number we post sits beside three others:", "serif", 600, 44, after=0.5)
    for item in ("the poll average", "the betting markets", "the Cook Political Report"):
        c.text(f"—  {item}", px=40, after=0.3)
    c.y += 30
    c.text("Anything from 35% to 65% we call a toss-up.", "serif", 600, 44)

    d = Slide(PINNED_DAY, f"{k} · WHAT YOU'LL SEE", t)
    d.headline("What we post.", px=88)
    rows = [("Daily", "Where the races stand, and what moved them."),
            ("Sundays", "Special editions: the Senate map, the chamber, a race up close."),
            ("Weekly", "Our score against the poll average, the markets and Cook. Misses included."),
            ("Now", "The making-of. Forecasts go public on 12 October.")]
    for head, body in rows:
        d.rule(t.hairline, after=22)
        top = d.y
        d._put(MARGIN, top, head.upper(), "mono", 600, 28, t.ai, va="top")
        d.text(body, px=38, x=MARGIN + 220, width=d.width - 220, after=0.8)
    d.rule(t.hairline)
    d.at_bottom(50)
    d.text(f"Follow along: {SITE}", "serif", 600, 40)
    slides = [(a, "A dot map of the United States, each dot a synthetic voter in blue, red or purple. Headline: the "
                  "2026 midterms, simulated every day."),
              (b, "Three steps: statistics set where each race starts; synthetic voters react to the news; each race "
                  "is played out 40,000 times."),
              (c, "Not a poll: nobody was asked anything. Every number sits beside the poll average, the betting "
                  "markets and the Cook Political Report. 35% to 65% is a toss-up."),
              (d, "What we post: daily race updates, Sunday special editions, a weekly score including misses, and "
                  "the making-of until forecasts go public on 12 October.")]
    for s, _ in slides:
        s.source("NotAPoll by Scalia Studio.")
    caption = (
        "Start here.\n\n"
        "NotAPoll simulates the 2026 US midterms every day. Synthetic voters, built from real data on how "
        "groups of Americans vote, react to each day's news. Then we play every Senate race and about 40 House races "
        "out 40,000 times. The share each side wins is its chance.\n\n"
        "It is not a poll: nobody was asked anything. That's why every number we post sits beside the poll average, "
        "the betting markets and the Cook Political Report, and why we publish our score every week, misses "
        "included.\n\n"
        "Until 12 October: the making-of. Then: daily forecasts.\n\n"
        f"{LABEL}.\n\n#midterms2026 #elections #socialsimulation #dataviz")
    thread = [f"Start here: NotAPoll simulates the 2026 US midterms every day. {LABEL}.",
              "Synthetic voters, built from real data on how groups vote, react to each day's news. Then every race is played "
              "out 40,000 times; the share each side wins is its chance.",
              "Nobody is asked anything. So every number sits beside the poll average, the betting markets and "
              "Cook, and we publish our score weekly, misses included.",
              f"Making-of posts until 12 October, daily forecasts after that. {SITE}"]
    return slides, caption, thread


BIOS = {
    "instagram": ("Democracy, rehearsed.\nThe 2026 midterms, simulated every day by synthetic voters.\n"
                  "Not a poll. By Scalia Studio", 150),
    "x": ("Democracy, rehearsed. The 2026 US midterms, simulated every day by synthetic voters and played out 40,000 "
          "times. Not a poll. By Scalia Studio", 160),
    "bluesky": ("Democracy, rehearsed.\n\nThe 2026 US midterms, simulated every day: synthetic voters react to the "
                "news, then every race is played out 40,000 times.\n\nNot a poll. Shown beside the poll average, "
                "markets and Cook; scored weekly.\n\nBy Scalia Studio", 256),
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
    problems = [f"caption: {p}" for p in text.check(caption)] + [f"thread 1: {p}" for p in text.check(thread[0])]
    problems += [f"thread {i}: {p}" for i, t in enumerate(thread, 1) for p in text.check(t, caption=False)]
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
