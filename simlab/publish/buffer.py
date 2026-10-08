"""Queue approved posts in Buffer (roadmap C9): python -m simlab.publish.buffer channels | plan | queue | queued | delete ID
    python -m simlab.publish.buffer queue-daily FOLDER "YYYY-MM-DD HH:MM"    # a kits/daily post, Paris time

Buffer's GraphQL API (api.buffer.com, bearer key BUFFER_API_KEY from .env, never printed). What its schema allows
(checked 1 Oct 2026): createPost takes images only as public URLs (there is no upload), with alt text per image;
Instagram carousels (type "post" with several images; Buffer refuses "carousel"); X threads (metadata.twitter.thread, which lists every post
including the first); drafts (saveToDraft); customScheduled posts with dueAt in UTC. Buffer fetches images when the
post goes out, so the URLs must stay up until then (guides/hosting-media).

The approval flag: `queue` sends nothing unless kits/launch/APPROVED.json names the post, with the date of Matteo's
yes given directly in the Content & site session (kits/daily/APPROVED.json for daily posts). It also checks that
every image URL answers before it sends.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import requests

ROOT = Path(__file__).resolve().parents[2]
PACK = ROOT / "kits" / "launch"
APPROVED = PACK / "APPROVED.json"
DAILY = ROOT / "kits" / "daily"
API = "https://api.buffer.com"
LONDON = ZoneInfo("Europe/London")
PARIS = ZoneInfo("Europe/Paris")  # Buffer's time zone and Matteo's: shown first in every printout
WEEKEND = [("01-intro", "2026-10-03 13:00"), ("02-lab-notes-01", "2026-10-03 17:00"),
           ("03-lab-notes-02", "2026-10-04 15:00"), ("04-lab-notes-03", "2026-10-05 13:00")]
X_IMAGES = 4


def key() -> str:
    for line in (ROOT.parent / ".env").read_text(encoding="utf-8").splitlines():
        if line.startswith("BUFFER_API_KEY="):
            return line.split("=", 1)[1].strip().strip('"')
    raise SystemExit("BUFFER_API_KEY is not in .env")


def gql(query: str, variables: dict | None = None) -> dict:
    r = requests.post(API, json={"query": query, "variables": variables or {}},
                      headers={"Authorization": f"Bearer {key()}"}, timeout=60)
    r.raise_for_status()
    out = r.json()
    if out.get("errors"):
        raise RuntimeError(out["errors"][0].get("message", out["errors"]))
    return out["data"]


def channels() -> dict[str, dict]:
    """The organisation's connected channels by service (instagram, twitter, threads, ...)."""
    org = gql("query { account { organizations { id } } }")["account"]["organizations"][0]["id"]
    chs = gql("query($o: OrganizationId!) { channels(input: {organizationId: $o}) { id service name isDisconnected "
              "isQueuePaused } }", {"o": org})["channels"]
    return {c["service"]: c | {"organizationId": org} for c in chs if not c["isDisconnected"]}


def utc(local: str, tz: ZoneInfo = LONDON) -> str:
    return datetime.strptime(local, "%Y-%m-%d %H:%M").replace(tzinfo=tz).astimezone(ZoneInfo("UTC")) \
        .strftime("%Y-%m-%dT%H:%M:%S.000Z")


def shown(local: str) -> str:
    """ "Sat 3 Oct 14:00 Paris (13:00 UK, 08:00 ET)" for a UK time."""
    t = datetime.strptime(local, "%Y-%m-%d %H:%M").replace(tzinfo=LONDON)
    p, e = t.astimezone(PARIS), t.astimezone(ZoneInfo("America/New_York"))
    return f"{p:%a %d %b %H:%M} Paris ({t:%H:%M} UK, {e:%H:%M} ET)"


def section(md: str, name: str) -> str:
    """The text under '## <name> (...)' in single-post.md."""
    lines, out, on = md.splitlines(), [], False
    for line in lines:
        if line.startswith("## "):
            on = line[3:].startswith(name)
            continue
        if on and line.strip():
            out.append(line)
    return "\n".join(out).strip()


def image(url: str, alt: str) -> dict:
    return {"image": {"url": url, "metadata": {"altText": alt, "userTags": []}}}


def posts_for(folder: str, base: str, pack: Path = PACK) -> list[dict]:
    """The createPost inputs for one post, without channel ids: one per platform."""
    d = pack / folder
    slides = sorted(d.glob("slide-*.jpg"), key=lambda p: int(p.stem.split("-")[1]))
    alts = dict(line.split(": ", 1) for line in (d / "alt-text.txt").read_text(encoding="utf-8").splitlines())
    imgs = [image(f"{base}/{folder}/{p.name}", alts[p.name]) for p in slides]
    single = (d / "single-post.md").read_text(encoding="utf-8")
    meta = json.loads((d / "meta.json").read_text(encoding="utf-8")) if (d / "meta.json").exists() else {}
    ig = {"type": "post", "shouldShareToFeed": True}
    caption = (d / "caption.txt").read_text(encoding="utf-8")
    if meta.get("instagram_first_comment") and "\n\n#" in caption:  # Buffer Free has no first comment: the question
        head, tail = caption.split("\n\n#", 1)                       # goes in the caption, before the hashtags
        caption = f"{head}\n\n{meta['instagram_first_comment']}\n\n#{tail}"
    reel = meta.get("reel") and (d / "reel.mp4").exists()  # Instagram Reel and X video; Threads keeps the slides
    video = [{"video": {"url": f"{base}/{folder}/reel.mp4", "thumbnailUrl": f"{base}/{folder}/reel-cover.jpg"}}]
    if reel:
        ig["type"] = "reel"
    out = [{"service": "instagram", "text": caption, "assets": video if reel else imgs, "metadata": {"instagram": ig}}]
    if reel:
        out.append({"service": "twitter", "text": section(single, "X"), "assets": video})
    elif folder == "01-intro":  # the one Buffer thread (Buffer Free queues one at a time)
        parts = (d / "thread.txt").read_text(encoding="utf-8").split("\n\n---\n\n")
        # Buffer's thread list includes the first post, which also stays in `text` (examples/create-threaded-post)
        thread = [{"text": parts[0], "assets": imgs[:X_IMAGES]}] + [{"text": t, "assets": []} for t in parts[1:]]
        out.append({"service": "twitter", "text": parts[0], "assets": imgs[:X_IMAGES],
                    "metadata": {"twitter": {"thread": thread}}})
    else:
        out.append({"service": "twitter", "text": section(single, "X"), "assets": imgs[:X_IMAGES]})
    threads = {"service": "threads", "text": section(single, "Threads"), "assets": imgs[:10]}
    if meta.get("threads_topic"):
        threads["metadata"] = {"threads": {"topic": meta["threads_topic"]}}
    out.append(threads)
    return out


CREATE = """mutation($i: CreatePostInput!) { createPost(input: $i) {
  ... on PostActionSuccess { post { id dueAt channelService status } }
  ... on MutationError { message } } }"""


def create(p: dict, channel: str, due: str, draft: bool = False) -> dict:
    i = {"channelId": channel, "text": p["text"], "assets": p["assets"], "mode": "customScheduled", "dueAt": due,
         "schedulingType": "automatic", "needsApproval": False, "tagIds": [], "saveToDraft": draft}
    if p.get("metadata"):
        i["metadata"] = p["metadata"]
    return gql(CREATE, {"i": i})["createPost"]


def queued() -> list[dict]:
    chs = channels()
    org = next(iter(chs.values()))["organizationId"]
    # an empty channelIds list matches nothing, so pass every channel
    q = """query($o: OrganizationId!, $c: [ChannelId!]) { posts(first: 50, input: {organizationId: $o,
           filter: {channelIds: $c}}) { edges { node { id dueAt channelService status text } } } }"""
    nodes = [e["node"] for e in gql(q, {"o": org, "c": [c["id"] for c in chs.values()]})["posts"]["edges"]]
    return sorted((n for n in nodes if n["status"] == "scheduled"), key=lambda n: n["dueAt"])


def approved(path: Path = APPROVED) -> dict:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def send(folder: str, posts: list[dict], due: str, chs: dict) -> None:
    for p in posts:
        if p["service"] not in chs:
            print(f"skip {folder} {p['service']}: channel not connected in Buffer")
            continue
        urls = [u for a in p["assets"] for u in ((a.get("image") or a["video"])["url"],
                                                  (a.get("video") or {}).get("thumbnailUrl")) if u]
        dead = [u for u in urls if requests.head(u, timeout=20).status_code != 200]
        if dead:
            raise SystemExit(f"{folder}: images not reachable yet: {dead[:2]}")
        print(folder, p["service"], create(p, chs[p["service"]]["id"], due))


def main(argv: list[str]) -> int:
    cmd = argv[0] if argv else "plan"
    base = "https://notapoll.org/social"  # where the slides must be reachable before queueing
    if cmd == "channels":
        for s, c in channels().items():
            print(s, c["name"], "queue paused" if c["isQueuePaused"] else "")
    elif cmd == "plan":  # no network: what would be queued
        for folder, local in WEEKEND:
            for p in posts_for(folder, base):
                print(f"{shown(local)}  {p['service']:<9} {len(p['text']):>4} chars, {len(p['assets'])} "
                      f"images{' + thread' if 'twitter' in p.get('metadata', {}) else ''}  {folder}")
        print("approved:", approved() or "nothing yet")
    elif cmd == "queue":
        ok, chs = approved(), channels()
        for folder, local in WEEKEND:
            if folder not in ok:
                print(f"skip {folder}: not approved")
                continue
            send(folder, posts_for(folder, base), utc(local), chs)
    elif cmd == "queue-daily":
        folder, local = argv[1], argv[2]
        if folder not in approved(DAILY / "APPROVED.json"):
            raise SystemExit(f"{folder}: not in kits/daily/APPROVED.json")
        send(folder, posts_for(folder, base, DAILY), utc(local, PARIS), channels())
    elif cmd == "queued":
        for n in queued():
            due = datetime.fromisoformat(n["dueAt"].replace("Z", "+00:00")).astimezone(PARIS)
            print(f"{due:%a %d %b %H:%M} Paris", n["channelService"], n["id"], n["text"][:60].replace("\n", " "))
    elif cmd == "delete":
        print(gql("mutation($i: PostId!) { deletePost(input: {id: $i}) { __typename } }", {"i": argv[1]}))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
