"""Reading the polls (18:00 Paris, from 5 Oct): one real poll or forecast from the day, what it measures, where it could
be overstating, why it could be right, and one hypothesis we check later. Fair to both sides and to pollsters
(communication.md): alternate which side the featured poll favours, never "polls are wrong".

    python -m simlab.publish.pollread --date 2026-10-05 --polls DIR      # DIR from python -m simlab.polls --out DIR
    python -m simlab.publish.pollread --candidates --polls DIR           # recent polls furthest from their race average

Each day's words are a STORIES entry, written the evening before and approved by Matteo with the rest of the day.
"""
from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

import pandas as pd

from . import text
from .frame import DISCLAIMER, LABEL, MARGIN, SITE, Slide, pt, typeset
from .launch import LIMIT, X_LINK
from .themes import LAB

ROOT = Path(__file__).parents[2]
KITS = ROOT / "kits"
SERIES = "Reading the polls"
ALLOW = ("poll", "polls", "pollster", "pollsters", "survey")
SHORT = {"New York Times/Siena University": "NYT/Siena", "Fabrizio Ward (R)/ Impact Research": "AARP",
         "Alaska Survey Research": "Alaska Survey Res.", "Rasmussen Reports": "Rasmussen",
         "Texas Public Opinion Research": "Texas Public Op.", "Texas Southern University": "Texas Southern",
         "Beacon Research (D)/ Shaw & Co. Research": "Fox News", "Pulse Decision Science": "Pulse Decision",
         "Stratus Intelligence": "Stratus", "Marist University": "Marist",
         "Bowling Green State University/YouGov": "BGSU/YouGov", "Suffolk University": "Suffolk"}

STORIES = {
    "2026-10-05": {
        "race": "AK", "since": "2026-08-15", "focus": "New York Times/Siena University", "folder": "05-reading-polls-01",
        "left": "Peltola", "right": "Sullivan",
        "headline": "Alaska’s newest poll has Peltola up 7. The rest show a near tie.",
        "dek": "Eight Senate polls since August: Peltola (D) minus Sullivan (R), likely voters.",
        "source": "Polls ending 23 Aug – 1 Oct 2026. Data: VoteHub (CC BY 4.0) and Wikipedia (CC BY-SA 4.0).",
        "title2": "Too high, or early?",
        "against": ["504 voters: on a sample this size, the gap can swing about 9 points either way.",
                    "The seven other polls since August average Peltola +1.",
                    "Alaska is hard to poll: small, spread out, many voters hard to reach."],
        "for": "Siena has almost no historical lean, and adjusting the other pollsters for theirs moves them slightly "
               "toward Peltola, not away.",
        "hypothesis": "Our hypothesis: closer to Peltola +2. We’ll check it against the next three polls.",
        "caption": (
            "Alaska's newest Senate poll, from NYT/Siena, has Mary Peltola ahead of Dan Sullivan by 7 points, 50 to "
            "43. The seven other polls since August average about Peltola +1, so is this an early signal or "
            "noise?\n\n"
            "There are good reasons to read it carefully. It's 504 likely voters, and on a sample that size the gap can "
            "move about 9 points either way. Alaska is also one of the harder states to poll: small, spread out, with "
            "many voters who are hard to reach.\n\n"
            "But it could be right. Siena has almost no historical lean, and when we adjust the other pollsters for "
            "their usual lean, they move slightly toward Peltola, not away.\n\n"
            "Our hypothesis: the race is closer than +7, nearer Peltola +2. We'll check it against the next three "
            "polls and tell you how it went.\n\n"
            "#midterms2026 #Alaska #elections"),
        "short": ("Alaska's newest poll, NYT/Siena, has Peltola up 7 on Sullivan. The seven others since August "
                  "average about +1. Small sample, hard state to poll, but Siena has almost no historical lean. Our "
                  "hypothesis: nearer +2."),
        "more": (" We'll check it against the next three polls. Reading the polls."),
        "alt1": ("Dot chart of eight Alaska Senate polls since August, Peltola minus Sullivan. Seven sit between "
                 "Sullivan +2.5 and Peltola +5; the newest, NYT/Siena, is furthest out at Peltola +7."),
    },
    "2026-10-06": {
        "race": "TX", "since": "2026-09-15", "focus": "Pulse Decision Science", "folder": "06-reading-polls-02",
        "left": "Talarico", "right": "Paxton", "exclude": ["Slingshot Strategies"],  # the TPOR poll, listed twice
        "headline": "One Texas poll has Paxton up 3. Nine others have Talarico ahead or tied.",
        "dek": "Ten Senate polls since mid-September: Talarico (D) minus Paxton (R), likely and registered voters.",
        "source": "Polls ending 17–30 Sep 2026. Data: VoteHub (CC BY 4.0) and Wikipedia (CC BY-SA 4.0).",
        "title2": "Outlier, or early?",
        "against": ["It’s the only one of ten polls since mid-September with Paxton ahead.",
                    "Its pollster isn’t in the 2018–24 records we use, so its usual lean is unknown.",
                    "800 voters: the gap can swing about 7 points either way."],
        "for": "Texas voted for Trump by 14 points in 2024. If Republicans who haven’t decided come home late, a "
               "poll like this is where it would show first.",
        "hypothesis": "Our hypothesis: Talarico still narrowly ahead, about +3. We’ll check it against the next three "
                      "polls.",
        "caption": (
            "A new Texas Senate poll from Pulse Decision Science has Ken Paxton ahead of James Talarico by 3 points, "
            "48 to 45. Of the ten polls since mid-September, it's the only one with Paxton in front; the other nine "
            "have Talarico ahead or tied, by about 3 on average.\n\n"
            "So is it an outlier or an early sign? There are reasons for caution. Pulse Decision Science isn't in the "
            "2018 to 2024 polls we use to estimate each pollster's usual lean, so we can't tell which way it tends to "
            "lean. And with 800 voters, the gap can move about 7 points either way.\n\n"
            "But it could be right. Texas voted for Trump by 14 points in 2024. If Republicans who haven't made up "
            "their minds come home late, a poll like this is where it would show first.\n\n"
            "Our hypothesis: Talarico is still narrowly ahead, around +3. We'll check it against the next three polls "
            "and report back.\n\n"
            "#midterms2026 #Texas #elections"),
        "short": ("A new Texas poll has Paxton up 3 on Talarico. The nine others since mid-September have Talarico "
                  "ahead or tied, by about 3. New pollster, no track record, but Texas voted Trump +14 in 2024. Our "
                  "hypothesis: Talarico still about +3."),
        "more": " We'll check it against the next three polls. Reading the polls.",
        "alt1": ("Dot chart of ten Texas Senate polls since mid-September, Talarico minus Paxton. Nine sit between a "
                 "tie and Talarico +6; the Pulse Decision Science poll is the only one with Paxton ahead, by 3."),
    },
    "2026-10-07": {
        "race": "OH-S", "since": "2026-09-01", "focus": "Marist University", "folder": "07-reading-polls-03",
        "left": "Brown", "right": "Husted",
        "headline": "One Ohio poll has Brown up 8. The ten others average about +3.",
        "dek": "Eleven Senate polls since September: Brown (D) minus Husted (R).",
        "source": "Polls ending 9 Sep – 1 Oct 2026. Data: VoteHub (CC BY 4.0) and Wikipedia (CC BY-SA 4.0).",
        "title2": "Registered, or likely?",
        "against": ["It asked all registered voters; the other ten asked likely voters.",
                    "Marist has leaned about 2 points toward Democrats against the average pollster, 2018–24.",
                    "The ten likely-voter polls since September average Brown +3."],
        "for": "It’s a large sample, 1,298 voters, from an established pollster, and Brown has led in every Ohio "
               "poll this month.",
        "hypothesis": "Our hypothesis: nearer Brown +3. We’ll check it against the next three polls.",
        "caption": (
            "A new Ohio Senate poll from Marist has Sherrod Brown ahead of Jon Husted by 8 points, 51 to 43. The ten "
            "other polls since September average about Brown +3.\n\n"
            "The biggest difference is who was asked. Marist asked all registered voters; the other ten asked likely "
            "voters, the people expected to turn out, and in a midterm that group can look quite different. Marist "
            "has also leaned about 2 points toward Democrats compared with the average pollster in 2018 to 2024.\n\n"
            "But it's a large sample from an established pollster, and Brown has led in every Ohio poll this month, so "
            "the direction isn't in doubt. The size is.\n\n"
            "Our hypothesis: the race is closer to Brown +3, where the likely-voter polls sit. We'll check it against "
            "the next three polls and report back.\n\n"
            "#midterms2026 #Ohio #elections"),
        "short": ("A new Ohio poll, Marist, has Brown up 8 on Husted. The ten others since September average about +3. "
                  "Marist asked registered voters, the others likely voters, and it has leaned about 2 points "
                  "toward Democrats. Our hypothesis: nearer Brown +3."),
        "more": " We'll check it against the next three polls. Reading the polls.",
        "alt1": ("Dot chart of eleven Ohio Senate polls since September, Brown minus Husted. Ten likely-voter polls "
                 "sit between Brown +0.5 and Brown +5; Marist, of registered voters, is furthest out at Brown +8."),
    },
    "2026-10-08": {
        "race": "FL-S", "since": "2026-09-15", "focus": "Mason-Dixon", "folder": "08-reading-polls-04",
        "left": "Nixon", "right": "Moody",
        "headline": "A new Florida poll has Moody up 10. The five others average about +5.",
        "dek": "Six Senate polls since mid-September: Nixon (D) minus Moody (R), likely voters.",
        "source": "Polls ending 17 Sep – 5 Oct 2026. Data: VoteHub (CC BY 4.0) and Wikipedia (CC BY-SA 4.0).",
        "title2": "Too wide, or right?",
        "against": ["625 voters: on a sample this size, the gap can swing about 8 points either way.",
                    "YouGov polled the same week with 3,813 voters and found Moody +5.",
                    "The five other polls since mid-September average Moody +5."],
        "for": "Mason-Dixon has leaned less than a point in our 2018–24 records, Stetson also has Moody up 11, and "
               "Trump won Florida by 13 in 2024.",
        "hypothesis": "Our hypothesis: nearer Moody +6. We’ll check it against the next three polls.",
        "caption": (
            "Florida Senate poll: a new Mason-Dixon survey has Ashley Moody ahead of Angie Nixon by 10 points, 50 to "
            "40. The five other polls since mid-September average about Moody +5, from a tie to Moody +11.\n\n"
            "There are reasons to read it carefully. It's 625 likely voters, and on a sample that size the gap can "
            "move about 8 points either way. YouGov was in the field the same week with 3,813 voters and found Moody "
            "ahead by 5.\n\n"
            "But it could be right. Mason-Dixon has leaned less than a point compared with the average pollster in "
            "2018 to 2024, Stetson found a similar Moody +11 in September, and Trump won Florida by 13 points in "
            "2024.\n\n"
            "Our hypothesis: Moody is ahead, but nearer +6 than +10. We'll check it against the next three polls and "
            "report back.\n\n"
            "#midterms2026 #Florida #FloridaSenate #elections"),
        "short": ("A new Florida poll, Mason-Dixon, has Moody up 10 on Nixon. The five others since mid-September "
                  "average about +5, and YouGov found +5 the same week. Small sample, but Mason-Dixon barely leans. "
                  "Our hypothesis: nearer Moody +6."),
        "more": " We'll check it against the next three polls. Reading the polls.",
        "x": ("Mason-Dixon has Moody up 10 in Florida. YouGov, same week, 3,813 voters: Moody +5. Six polls since "
              "mid-September run from a tie to Moody +11. Our hypothesis: nearer +6, checked against the next three "
              "polls."),
        "threads": ("Two Florida Senate polls from the same week: Mason-Dixon has Ashley Moody up 10 on Angie Nixon, "
                    "YouGov has her up 5. Mason-Dixon barely leans in past cycles, but 625 voters is a small sample. "
                    "We think the race is nearer Moody +6, and we'll check it against the next three polls. If you "
                    "live in Florida, does this race feel close where you are?"),
        "topic": "2026 Midterms",
        "first_comment": "If you live in Florida, does this Senate race feel close where you are?",
        "alt1": ("Dot chart of six Florida Senate polls since mid-September, Nixon minus Moody. They run from a tie "
                 "to Moody +11; the newest Mason-Dixon poll, ringed, has Moody +10."),
    },
}


def load(polls: Path, race: str, since: str, exclude=()) -> pd.DataFrame:
    s = pd.read_csv(polls / "senate.csv", parse_dates=["start", "end"])
    s = s[(s.race_id == race) & (s.end >= since) & ~s.pollster.isin(exclude)].sort_values("end").copy()
    s["gap"] = s.left - s.right
    return s


def candidates(polls: Path, days: int = 7) -> pd.DataFrame:
    """Recent polls furthest from their race's three-week average (two-party margin), newest first."""
    s = pd.read_csv(polls / "senate.csv", parse_dates=["start", "end"])
    last = s.end.max()
    avg = s[s.end >= last - pd.Timedelta(days=21)].groupby("race_id").margin.agg(["mean", "count"])
    r = s[s.end >= last - pd.Timedelta(days=days)].join(avg, on="race_id")
    r["dev"] = r.margin - r["mean"]
    return r.reindex(r.dev.abs().sort_values(ascending=False).index)[
        ["race_id", "pollster", "end", "population", "left", "right", "n", "tag", "margin", "mean", "count", "dev"]]


def strip_chart(s: Slide, p: pd.DataFrame, focus: str, left: str, right: str, lim: float | None = None,
                row: float | None = None) -> dict:
    """One row per poll, oldest at the top: a dot at the gap (left minus right), the featured poll ringed. Returns
    the artists, so the reel can reveal them one by one."""
    t = s.t
    lim = lim or (10 if p.gap.abs().max() <= 8 else 20)
    ax = s.chart((row or min(54, 480 / len(p))) * len(p), left=340, right=40)
    ax.set_xlim(-lim, lim)
    ax.set_ylim(len(p) - 0.5, -0.5)
    ax.set_yticks([])
    ticks = [-lim, -lim / 2, 0, lim / 2, lim]
    ax.set_xticks(ticks, [typeset(f"+{abs(x):.0f}" if x else "Even") for x in ticks])
    for lab in ax.get_xticklabels():
        lab.set_fontproperties(s.font("sans", 400, 28))
    ax.axvline(0, color=t.baseline, lw=pt(2), zorder=1)
    for x in ticks:
        if x:
            ax.axvline(x, color=t.hairline, lw=pt(1), zorder=0)
    others = p[p.pollster != focus].gap.mean()
    avg = ax.axvline(others, color=t.ink2, lw=pt(2), ls=(0, (3, 3)), zorder=1)
    rows = []
    for i, row in enumerate(p.itertuples()):
        c = t.dem if row.gap > 0 else t.rep if row.gap < 0 else t.data
        hot = row.pollster == focus
        dot = ax.scatter([row.gap], [i], s=pt(34 if hot else 24) ** 2, facecolor=c,
                         edgecolor=t.ink if hot else t.paper, linewidth=pt(4 if hot else 3), zorder=4 if hot else 3)
        name = f"{SHORT.get(row.pollster, row.pollster)}, {row.end.day} {row.end:%b}"
        label = ax.text(-lim * 1.04, i, typeset(name), va="center", ha="right", color=t.ink,
                        fontproperties=s.font("sans", 600 if hot else 400, 27))
        tag = None
        if hot:
            who = left if row.gap > 0 else right
            tag = ax.text(row.gap, i - 0.62, typeset(f"{who} +{abs(row.gap):.0f}"), va="bottom", ha="center",
                          color=t.ink, fontproperties=s.font("sans", 600, 28))
        rows.append({"dot": dot, "label": label, "tag": tag, "hot": hot})
    s.y += 50
    x0, x1 = MARGIN + 340, s.w - MARGIN
    arrow = s.pil("mono", 400, 26).getlength("← ")
    s._put(x0, s.y, "← ", "mono", 400, 26, t.ink2, va="top")
    s._put(x0 + arrow, s.y, f"{right} ahead", "sans", 400, 26, t.ink2, va="top")
    s._put(x1, s.y, " →", "mono", 400, 26, t.ink2, ha="right", va="top")
    s._put(x1 - arrow, s.y, f"{left} ahead", "sans", 400, 26, t.ink2, ha="right", va="top")
    s.y += 44
    lead = f"{left} +{others:.0f}" if round(others) > 0 else f"{right} +{-others:.0f}" if round(others) < 0 else "even"
    avg_text = s._put(x0, s.y, f"- - -  average of the other {len(p) - 1}: {lead}", "sans", 400, 26, t.ink2,
                      va="top")
    s.y += 50
    return {"rows": rows, "avg": [avg, avg_text], "others": others}


def end(t: str, limit: int, link: int = 0) -> str:
    fits = len(t) + 1 + len(DISCLAIMER) + (link - len(SITE) if link else 0) <= limit
    return f"{t} {DISCLAIMER}" if fits else f"{t} {LABEL}."


def build(day: str, polls: Path, theme=LAB) -> tuple[Path, list[str]]:
    st, d = STORIES[day], date.fromisoformat(day)
    p = load(polls, st["race"], st["since"], st.get("exclude", ()))
    a = Slide(d, "", theme, series=SERIES)
    a.headline(st["headline"], px=64)
    a.dek(st["dek"], px=34)
    strip_chart(a, p, st["focus"], st["left"], st["right"])
    a.source(st["source"])

    b = Slide(d, "", theme, series=SERIES)
    b.headline(st["title2"], px=88)
    b.text("Why it may be too high", "sans", 600, 30, theme.ink2, after=0.5)
    for n, line in enumerate(st["against"], 1):
        top = b.y
        b._put(MARGIN, top - 6, str(n), "hero", theme.hero_weight, 64, theme.ai, va="top")
        b.text(line, "serif", 600, 38, x=MARGIN + 76, width=b.width - 76, after=0.7)
    b.y += 10
    b.text("Why it may be right", "sans", 600, 30, theme.ink2, after=0.5)
    b.text(st["for"], "serif", 600, 38, after=0.9)
    b.note(st["hypothesis"], width=760)
    b.source(st["source"])

    out = KITS / "daily" / st["folder"]
    out.mkdir(parents=True, exist_ok=True)
    problems = []
    for i, s in enumerate((a, b), 1):
        problems += [f"slide {i}: {x}" for x in s.layout_problems() + s.missing_glyphs()]
        problems += [f"slide {i}: {x}" for x in text.slide_problems(s, ALLOW)]
        s.save(out / f"slide-{i}.jpg")
    caption = f"{st['caption']}\n\n{DISCLAIMER}"
    posts = {"x": f'{st.get("x", st["short"])} {LABEL}.',  # no link on X: it cuts reach
             "bluesky": end(st["short"], LIMIT["bluesky"]),
             "threads": end(st.get("threads", st["short"] + st["more"]), LIMIT["threads"])}
    meta = {k2: st[k1] for k1, k2 in (("topic", "threads_topic"), ("first_comment", "instagram_first_comment"))
            if st.get(k1)}
    (out / "meta.json").write_text(json.dumps(meta, indent=1, ensure_ascii=False), encoding="utf-8")
    if meta.get("instagram_first_comment"):
        problems += [f"first comment: {x}" for x in text.check(meta["instagram_first_comment"], caption=False,
                                                                allow=ALLOW)]
    alt2 = " ".join([st["title2"], "Why it may be too high:", *st["against"], "Why it may be right:", st["for"],
                     st["hypothesis"]])
    (out / "caption.txt").write_text(caption, encoding="utf-8")
    (out / "alt-text.txt").write_text(f"slide-1.jpg: {st['alt1']}\nslide-2.jpg: {alt2}\n", encoding="utf-8")
    lines = ["# Single posts (X and Threads through Buffer; Bluesky by hand)", ""]
    for k in ("x", "threads", "bluesky"):
        n = len(posts[k]) + (X_LINK - len(SITE) if k == "x" and SITE in posts[k] else 0)
        lines += [f"## {'X' if k == 'x' else k.capitalize()} ({n} of {LIMIT[k]} characters; attach slide-1 to slide-2)",
                  "", posts[k], ""]
        problems += [f"{k}: {n} characters" for _ in [0] if n > LIMIT[k]]
    (out / "single-post.md").write_text("\n".join(lines), encoding="utf-8")
    for name, s in [("caption", caption), *posts.items()]:
        problems += [f"{name}: {x}" for x in text.check(s, caption=True, allow=ALLOW)]
    (out / "checks.txt").write_text("\n".join(problems) or "all rules pass", encoding="utf-8")
    return out, problems


def reel(day: str, polls: Path, theme=LAB) -> dict:
    """The 9:16 Reel of the day's story (Instagram Reel, X video): each poll lands in date order, then the average
    line, then the featured poll, then the hypothesis. 30 fps, H.264, no sound; the cover is the last frame."""
    import imageio_ffmpeg
    import matplotlib.pyplot as plt
    import numpy as np
    from PIL import Image

    st, d = STORIES[day], date.fromisoformat(day)
    p = load(polls, st["race"], st["since"], st.get("exclude", ()))
    w, h, fps = 1080, 1920, 30
    s = Slide(d, "", theme, size=(w, h), series=SERIES)
    s.headline(st["headline"], px=64)  # no dek: the axis labels say what the dots are
    s.y += 10
    art = strip_chart(s, p, st["focus"], st["left"], st["right"], row=min(48, 460 / len(p)))
    s.source(st["source"])
    n_patches, n_texts = len(s.ax.patches), len(s.ax.texts)
    s.note(st["hypothesis"], width=900, px=34)
    note = s.ax.patches[n_patches:] + s.ax.texts[n_texts:]
    if bad := s.layout_problems() + s.missing_glyphs() + text.slide_problems(s, ALLOW):
        raise ValueError(f"reel layout: {bad}")

    start, step = 0.8, 0.45
    calm = [r for r in art["rows"] if not r["hot"]]
    hot = [r for r in art["rows"] if r["hot"]]
    times = {id(r): start + i * step for i, r in enumerate(calm)}
    t_avg = start + len(calm) * step + 0.3
    for r in hot:
        times[id(r)] = t_avg + 0.9
    t_note, total = t_avg + 2.3, t_avg + 5.2
    base = {id(r): r["dot"].get_sizes()[0] for r in art["rows"]}

    out = KITS / "daily" / st["folder"] / "reel.mp4"
    out.parent.mkdir(parents=True, exist_ok=True)
    writer = imageio_ffmpeg.write_frames(str(out), (w, h), fps=fps, codec="libx264", quality=8, macro_block_size=8,
                                         pix_fmt_in="rgb24", pix_fmt_out="yuv420p",
                                         output_params=["-movflags", "+faststart"])
    writer.send(None)
    frame = None
    for f in range(int(total * fps)):
        now = f / fps
        for r in art["rows"]:
            t0 = times[id(r)]
            on = now >= t0
            for a in (r["dot"], r["label"], r["tag"]):
                if a is not None:
                    a.set_visible(on)
            if on:  # a short pop: lands at 1.8x its size, settles in 0.25 s
                u = min((now - t0) / 0.25, 1)
                r["dot"].set_sizes([base[id(r)] * (1.8 - 0.8 * u * u)])
        for a in art["avg"]:
            a.set_visible(now >= t_avg)
        for a in note:
            a.set_visible(now >= t_note)
        s.fig.canvas.draw()
        frame = np.asarray(s.fig.canvas.buffer_rgba())[:, :, :3]
        writer.send(np.ascontiguousarray(frame))
    writer.close()
    cover = out.with_name("reel-cover.jpg")
    Image.fromarray(frame).save(cover, quality=92, subsampling=0)
    plt.close(s.fig)
    meta_path = out.with_name("meta.json")  # tells buffer.py to send the Reel to Instagram and X
    meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
    meta_path.write_text(json.dumps(meta | {"reel": True}, indent=1, ensure_ascii=False), encoding="utf-8")
    return {"video": out, "cover": cover, "seconds": round(total, 1)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date")
    ap.add_argument("--polls", type=Path, required=True)
    ap.add_argument("--candidates", action="store_true")
    ap.add_argument("--reel", action="store_true")
    a = ap.parse_args()
    if a.candidates:
        print(candidates(a.polls).head(25).to_string())
        return
    out, problems = build(a.date, a.polls)
    print(out, "; ".join(problems) or "all rules pass")
    if a.reel:
        print(reel(a.date, a.polls))


if __name__ == "__main__":
    main()
