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
from .labnotes import contact_sheet

OUT = Path(__file__).resolve().parents[2] / "kits" / "launch"
WHERE = {"instagram": "Instagram and Threads: Edit profile → Bio (Threads imports it)",
         "x": "X: Edit profile → Bio", "bluesky": "Bluesky: Edit profile → Description"}


def post_folder(d: Path, slides, caption: str, thread: list[str], allow=()) -> list[str]:
    d.mkdir(parents=True, exist_ok=True)
    for old in d.glob("slide-*.jpg"):
        old.unlink()
    paths = [s.save(d / f"slide-{i}.jpg") for i, (s, _) in enumerate(slides, 1)]
    contact_sheet(paths, d / "contact.jpg", scale=0.3)
    (d / "caption.txt").write_bytes(caption.encode("utf-8"))
    (d / "thread.txt").write_bytes("\n\n---\n\n".join(thread).encode("utf-8"))
    (d / "alt-text.txt").write_bytes("\n".join(f"slide-{i}.jpg: {alt}" for i, (_, alt) in enumerate(slides, 1))
                                     .encode("utf-8"))
    problems = [f"caption: {p}" for p in text.check(caption, allow=allow)]
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
              "- header-x.jpg: X header (1500×500)", "- banner-bluesky.jpg: Bluesky banner (3000×1000)", ""]
    readme += [f"- bio-{k}.txt ({len(b)} of {n} characters): {WHERE[k]}" for k, (b, n) in brand.BIOS.items()]
    (prof / "README.md").write_bytes(("\n".join(readme) + "\n").encode("utf-8"))

    report = {}
    slides, caption, thread = brand.pinned()
    report["01-start-here"] = post_folder(out / "01-start-here", slides, caption, thread)
    for n in (1, 2, 3):
        p = getattr(labnotes, f"ep0{n}")()
        report[f"0{n + 1}-lab-notes-0{n}"] = post_folder(out / f"0{n + 1}-lab-notes-0{n}", p.slides, p.instagram,
                                                          p.thread, p.allow)
    (out / "CHECKLIST.md").write_bytes(CHECKLIST.encode("utf-8"))
    (prof / "REDIRECT.md").write_bytes(REDIRECT.encode("utf-8"))
    return report


CHECKLIST = """# Posting checklist, Sat 3 Oct (then the same for 4 and 5 Oct)

Only after Matteo has approved each post. Around 13:00–15:00 UK (8–10 am US Eastern) is a common choice. Before the
first post: the notapoll.org redirect (00-profiles/REDIRECT.md).

1. Instagram: new post → the slides of 01-start-here in order → paste caption.txt → Advanced settings →
   Accessibility → paste each slide's alt text from alt-text.txt → Share. Then pin it to the profile grid.
2. X, Threads, Bluesky (by hand or Buffer): paste thread.txt, one post per part (split at ---); attach slides 1–4 to
   the first post (X and Bluesky take 4 images per post); pin the first post on each.
3. A few hours later, 02-lab-notes-01 the same way (Instagram with all slides; on X and Bluesky put slides 1–4 on the
   first post and the rest on the next).
4. Check every image shows "SOCIAL SIMULATION, NOT A POLL" and the caption ends with the label line; no boosts.
5. Sun 4 Oct: 03-lab-notes-02. Mon 5 Oct: 04-lab-notes-03. Each can be scheduled the day before (Instagram's own
   scheduler; Buffer for the rest), each only with Matteo's yes.
"""


REDIRECT = """# notapoll.org → the Instagram profile (until the site is live)

Matteo, 29 Sep. In the Cloudflare dashboard, zone notapoll.org:

1. DNS → Records → Add record: type A, name `@`, IPv4 `192.0.2.1`, Proxy status on (orange cloud). Add a second one:
   type CNAME, name `www`, target `notapoll.org`, proxied. (192.0.2.1 is a placeholder address: Cloudflare answers
   before it is ever reached. Redirects only work on proxied records. The email and `_atproto` records stay as they
   are.)
2. Rules → Redirect Rules → Create rule. Name: `to instagram`. If incoming requests match: Custom filter expression,
   Hostname equals `notapoll.org`, Or, Hostname equals `www.notapoll.org`.
3. Then: Type Static, URL `https://www.instagram.com/notapoll.org/`, Status code 302 (temporary, so browsers don't
   remember it once the site replaces it), Preserve query string off. Deploy.
4. Test: open https://notapoll.org and https://www.notapoll.org in a private window; both should land on the
   Instagram profile.
5. When the site goes live, delete this rule (and the placeholder A record if the site uses its own).
"""


if __name__ == "__main__":
    for folder, problems in build().items():
        print(f"{folder}: " + ("; ".join(problems) or "all rules pass"))
    print(OUT)
