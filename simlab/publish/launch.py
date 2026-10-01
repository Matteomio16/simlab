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
# Buffer Free: Instagram, X and Threads, one queued thread at a time, 10 posts per channel (Matteo, 1 Oct). "Start
# here" is the thread, on X; everything else goes out as single posts. Bluesky is outside Buffer: by hand until the C9
# poster exists. Times are stored as UK time (BST) and shown as Paris time first (Matteo thinks in it, 1 Oct), with UK
# and US Eastern in brackets: Paris = UK + 1, Eastern = UK - 5.
SCHEDULE = [("Sat 3 Oct", "13:00", "01-start-here", "thread on X (the one Buffer thread); single post on Threads; "
                                                     "pin it everywhere when convenient"),
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
            "We're forecasting the 2026 midterms with voter personas built from real survey answers, every day until "
            "3 November, scored in public every Monday. We'll publish what we get wrong too.",
            " It's not a poll: nobody is asked anything, so our number always sits beside the poll average, the "
            "prediction markets and Cook. notapoll.org"),
        "02-lab-notes-01": (
            "Before forecasting a single race, we asked six models to behave like voters. Each was good at one thing, "
            "none at everything, and all were too calm about real shocks.",
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


def single_file(d: Path, posts: dict[str, str], slides: int, allow=()) -> list[str]:
    lines, problems = ["# Single posts (X and Threads through Buffer; Bluesky by hand)", ""], []
    for k in ("x", "threads", "bluesky"):
        t, n = posts[k], min(slides, MAX_IMAGES[k])
        lines += [f"## {k.capitalize() if k != 'x' else 'X'} ({len(t)} of {LIMIT[k]} characters; attach slide-1 to "
                  f"slide-{n})", "", t, ""]
        problems += [f"{k}: {p}" for p in text.check(t, allow=allow)]
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
    report["01-start-here"] = post_folder(out / "01-start-here", slides, caption, thread, brand.ALLOW)
    report["01-start-here"] += single_file(out / "01-start-here", single["01-start-here"], len(slides), brand.ALLOW)
    for n in (1, 2, 3):
        p = getattr(labnotes, f"ep0{n}")()
        k = f"0{n + 1}-lab-notes-0{n}"
        report[k] = post_folder(out / k, p.slides, p.instagram, p.thread, p.allow)
        report[k] += single_file(out / k, single[k], len(p.slides), p.allow)
    rows = ["# Posting schedule, Sat 3 – Mon 5 Oct (Paris time; UK and US Eastern in brackets)", "",
            "Queue everything in Buffer once Matteo has approved each post (set Buffer's time zone to "
            "Europe/London): the Instagram carousel with caption.txt, X and Threads from single-post.md. Buffer "
            "Free holds one thread at a time and 10 posts per channel; this plan uses one thread and four posts per "
            "channel. Instagram alt text: in Buffer's Instagram options if offered, otherwise on Instagram after it "
            "posts (… → Edit → Edit alt text). Bluesky is outside Buffer: post its single-post.md text by hand at "
            "the same time, once the account exists.", "",
            "| Day | Paris (UK, ET) | Post | Instagram (Buffer) | X, Threads (Buffer); Bluesky (by hand) |",
            "|---|---|---|---|---|"]
    for day, hhmm, k, how in SCHEDULE:
        h, m = int(hhmm[:2]), hhmm[3:]
        rows.append(f"| {day} | {h + 1:02d}:{m} ({hhmm} UK, {h - 5:02d}:{m} ET) | `{k}` | carousel, caption.txt | "
                    f"{how} (single-post.md) |")
    (out / "SCHEDULE.md").write_bytes(("\n".join(rows) + "\n").encode("utf-8"))
    (out / "CHECKLIST.md").write_bytes(CHECKLIST.encode("utf-8"))
    (prof / "REDIRECT.md").unlink(missing_ok=True)  # retired: notapoll.org serves a launch page (Matteo, 30 Sep)
    return report


CHECKLIST = """# Posting checklist, Sat 3 Oct (then the same for 4 and 5 Oct)

Only after Matteo has approved each post. Times in SCHEDULE.md: Paris first (Buffer's time zone), UK and US Eastern
in brackets. Before the
first post: the notapoll.org launch page is live (the website session's steps in site/README.md, "Matteo's steps").

1. Buffer, Instagram channel: the slides of 01-start-here in order, caption.txt, alt text from alt-text.txt (in
   Buffer if it offers it, otherwise on Instagram after posting). Pin it to the profile grid once it's up.
2. Buffer, X: "Start here" as the thread (thread.txt, split at ---; slides 1–4 on the first post); Buffer Free holds
   only one scheduled thread. Buffer, Threads, and every Lab note on X and Threads: single-post.md, one post each.
3. Bluesky (outside Buffer, once the account exists): the Bluesky text from single-post.md, by hand, at the same time.
4. Check every image shows "SOCIAL SIMULATION, NOT A POLL" and every caption ends with the label line; no boosts.
5. Lab notes 01, 02 and 03 the same way at the times in SCHEDULE.md; all can be queued today, each only with
   Matteo's yes.
"""


if __name__ == "__main__":
    for folder, problems in build().items():
        print(f"{folder}: " + ("; ".join(problems) or "all rules pass"))
    print(OUT)
