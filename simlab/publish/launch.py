"""The launch pack: python -m simlab.publish.launch -> kits/launch/, everything Matteo needs to go live, ready to paste.

00-profiles/        avatar, X header, Bluesky banner, one bio file per platform, where each goes
01-start-here/      the pinned carousel
02-lab-notes-01/ … 04-lab-notes-03/
Each post folder: slide-N.jpg, contact.jpg, caption.txt (Instagram), thread.txt (X, Threads, Bluesky; posts
separated by ---), alt-text.txt (one line per slide) and checks.txt. CHECKLIST.md is the posting order for 3–5 Oct.
Nothing here posts anything: Matteo approves and posts each one.
"""
from __future__ import annotations

import shutil
from pathlib import Path

from . import brand, labnotes, text
from .frame import LABEL
from .labnotes import contact_sheet

OUT = Path(__file__).resolve().parents[2] / "kits" / "launch"
LIMIT = {"x": 280, "bluesky": 300, "threads": 500}
MAX_IMAGES = {"x": 4, "bluesky": 4, "threads": 10}
# Buffer Free queues one thread at a time (Matteo, 1 Oct): "Start here" is that thread, on X; everything else goes out
# as single posts. UK times (BST); US Eastern is five hours behind.
SCHEDULE = [("Sat 3 Oct", "13:00", "01-start-here", "thread on X (the one Buffer thread); single post on Threads and "
                                                     "Bluesky; pin it on every platform when convenient"),
            ("Sat 3 Oct", "17:00", "02-lab-notes-01", "single posts"),
            ("Sun 4 Oct", "15:00", "03-lab-notes-02", "single posts"),
            ("Mon 5 Oct", "13:00", "04-lab-notes-03", "single posts")]


def singles() -> dict[str, dict[str, str]]:
    """One self-contained post per platform for each launch post: X and Bluesky share the short text."""
    from ..scorecard import latest
    s = latest()
    lean = lambda m: 100 * s[("mirror", m)]["mean_asymmetry"] / s[("mirror", m)]["mean_abs_reaction"]
    one, both = f"{abs(lean('glm1')):.0f}%", f"{abs(lean('glm')):.0f}%"
    out = {
        "01-start-here": (
            "We're forecasting the 2026 midterms with a society of synthetic voters, every day until 3 November, "
            "scored in public every Monday. In April we missed Hungary by 16 points. This time we show our work.",
            " It's not a poll: nobody is asked anything, so our number always sits beside the poll average, the "
            "prediction markets and Cook. notapoll.org"),
        "02-lab-notes-01": (
            "In April we simulated Hungary's election and missed by 16 points. So we tested six models first. Each was "
            "good at one thing, none at everything, and all were too calm about real shocks.",
            " They over-reacted to debates and spectacles too. So statistics set where each race starts, and reaction "
            "sizes come from shifts that were actually measured. Lab notes 01."),
        "03-lab-notes-02": (
            "We credited 80 real headlines to Fox News, then to MSNBC. Same words. One model changed its answer on which "
            "party the news helps 41% of the time.",
            " People read the source as a clue too; a forecast can't. So no model in our forecast ever sees an outlet's "
            "name: every story becomes a short, neutral event card first. Lab notes 02."),
        "04-lab-notes-03": (
            f"Our answer scale listed the Republican side first, and one model leaned Republican by {one} of its typical "
            f"reaction. Asked both ways and averaged: {both}. So every question in our forecast is asked both ways.",
            " Some models favour whichever answer comes first. It doubles the cost, still a few cents per thousand "
            "answers. Lab notes 03."),
    }
    label = f" {LABEL}."
    return {k: {"x": short + label, "bluesky": short + label, "threads": short + more + label}
            for k, (short, more) in out.items()}


def single_file(d: Path, posts: dict[str, str], slides: int) -> list[str]:
    lines, problems = [f"# Single posts (Buffer: X, Threads, Bluesky)", ""], []
    for k in ("x", "threads", "bluesky"):
        t, n = posts[k], min(slides, MAX_IMAGES[k])
        lines += [f"## {k.capitalize() if k != 'x' else 'X'} ({len(t)} of {LIMIT[k]} characters; attach slide-1 to "
                  f"slide-{n})", "", t, ""]
        problems += [f"{k}: {p}" for p in text.check(t)]
        problems += [f"{k}: {len(t)} characters (limit {LIMIT[k]})" for _ in [0] if len(t) > LIMIT[k]]
    (d / "single-post.md").write_bytes("\n".join(lines).encode("utf-8"))
    return problems


WHERE = {"instagram": "Instagram and Threads: Edit profile → Bio (Threads imports it)",
         "x": "X: Edit profile → Bio", "bluesky": "Bluesky: Edit profile → Description"}


def post_folder(d: Path, slides, caption: str, thread: list[str], allow=()) -> list[str]:
    d.mkdir(parents=True, exist_ok=True)
    for old in d.glob("slide-*.jpg"):
        old.unlink()
    drawn = [f"slide {i}: {p}" for i, (s, _) in enumerate(slides, 1) for p in text.slide_problems(s, allow)]
    paths = [s.save(d / f"slide-{i}.jpg") for i, (s, _) in enumerate(slides, 1)]
    contact_sheet(paths, d / "contact.jpg", scale=0.3)
    (d / "caption.txt").write_bytes(caption.encode("utf-8"))
    (d / "thread.txt").write_bytes("\n\n---\n\n".join(thread).encode("utf-8"))
    (d / "alt-text.txt").write_bytes("\n".join(f"slide-{i}.jpg: {alt}" for i, (_, alt) in enumerate(slides, 1))
                                     .encode("utf-8"))
    problems = drawn + [f"caption: {p}" for p in text.check(caption, allow=allow)]
    problems += [f"caption: {len(caption)} characters" for _ in [0] if len(caption) > 2200]
    problems += [f"thread {i}: {p}" for i, t in enumerate(thread, 1)
                 for p in text.check(t, caption=i == 1, allow=allow)]
    problems += [f"thread {i}: {len(t)} characters" for i, t in enumerate(thread, 1) if len(t) > 280]
    (d / "checks.txt").write_bytes(("\n".join(problems) or "All rules pass.").encode("utf-8"))
    return problems


def build(out: Path = OUT) -> dict:
    brand.write()
    prof = out / "00-profiles"
    prof.mkdir(parents=True, exist_ok=True)
    for n in ("avatar.jpg", "header-x.jpg", "banner-bluesky.jpg"):
        shutil.copy(brand.OUT / n, prof / n)
    for k, (bio, limit) in brand.BIOS.items():
        (prof / f"bio-{k}.txt").write_bytes(bio.encode("utf-8"))
    readme = ["# Profiles", "", "- avatar.jpg: every platform's profile photo" +
              ("" if brand.AVATAR_PICKED else " (placeholder until Matteo picks D, D+ or E)"),
              "- header-x.jpg: X header (1500×500)", "- banner-bluesky.jpg: Bluesky banner (3000×1000)",
              "- Link: notapoll.org in the Instagram and X website fields (Bluesky's handle is the domain itself)", ""]
    readme += [f"- bio-{k}.txt ({len(b)} of {n} characters): {WHERE[k]}" for k, (b, n) in brand.BIOS.items()]
    (prof / "README.md").write_bytes(("\n".join(readme) + "\n").encode("utf-8"))

    report, single = {}, singles()
    slides, caption, thread = brand.pinned()
    report["01-start-here"] = post_folder(out / "01-start-here", slides, caption, thread)
    report["01-start-here"] += single_file(out / "01-start-here", single["01-start-here"], len(slides))
    for n in (1, 2, 3):
        p = getattr(labnotes, f"ep0{n}")()
        k = f"0{n + 1}-lab-notes-0{n}"
        report[k] = post_folder(out / k, p.slides, p.instagram, p.thread, p.allow)
        report[k] += single_file(out / k, single[k], len(p.slides))
    rows = ["# Posting schedule, Sat 3 – Mon 5 Oct (UK time)", "",
            "Queue everything once Matteo has approved each post: Instagram in the Instagram app (Advanced settings "
            "→ Schedule; add each slide's alt text first), the rest in Buffer (set Buffer's time zone to "
            "Europe/London). Buffer Free holds one thread at a time and 10 posts per channel: this plan uses one "
            "thread and four posts per channel.", "",
            "| Day | UK time (ET) | Post | Instagram | X, Threads, Bluesky |", "|---|---|---|---|---|"]
    for day, hhmm, k, how in SCHEDULE:
        et = f"{int(hhmm[:2]) - 5:02d}:{hhmm[3:]}"
        rows.append(f"| {day} | {hhmm} ({et}) | `{k}` | carousel, caption.txt | {how} (single-post.md) |")
    (out / "SCHEDULE.md").write_bytes(("\n".join(rows) + "\n").encode("utf-8"))
    (out / "CHECKLIST.md").write_bytes(CHECKLIST.encode("utf-8"))
    (prof / "REDIRECT.md").unlink(missing_ok=True)  # retired: notapoll.org serves a launch page (Matteo, 30 Sep)
    return report


CHECKLIST = """# Posting checklist, Sat 3 Oct (then the same for 4 and 5 Oct)

Only after Matteo has approved each post. Around 13:00–15:00 UK (8–10 am US Eastern) is a common choice. Before the
first post: the notapoll.org launch page is live (the website session's steps in site/README.md, "Matteo's steps").

1. Instagram: new post → the slides of 01-start-here in order → paste caption.txt → Advanced settings →
   Accessibility → paste each slide's alt text from alt-text.txt → Share. Then pin it to the profile grid.
2. X: "Start here" goes out as the thread (thread.txt, split at ---; slides 1–4 on the first post): Buffer Free holds
   only one scheduled thread. Threads and Bluesky, and every Lab note on all three: single-post.md, one post each.
3. 02-lab-notes-01 at 17:00 the same way: Instagram with all slides, single posts elsewhere. All times: SCHEDULE.md.
4. Check every image shows "SOCIAL SIMULATION, NOT A POLL" and the caption ends with the label line; no boosts.
5. Sun 4 Oct: 03-lab-notes-02. Mon 5 Oct: 04-lab-notes-03. Each can be scheduled the day before (Instagram's own
   scheduler; Buffer for the rest), each only with Matteo's yes.
"""


if __name__ == "__main__":
    for folder, problems in build().items():
        print(f"{folder}: " + ("; ".join(problems) or "all rules pass"))
    print(OUT)
