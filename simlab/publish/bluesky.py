"""Post an approved kit to Bluesky directly (Buffer Free has no room for a fourth channel):
python -m simlab.publish.bluesky check | dry FOLDER | post FOLDER | schedule FOLDER "YYYY-MM-DD HH:MM" | due

Reads BLUESKY_HANDLE and BLUESKY_APP_PASSWORD from the environment or Sim Research/.env (an app password, never the
account password; never printed). `post` sends only folders named in kits/daily/APPROVED.json (or
kits/launch/APPROVED.json): the Bluesky text from single-post.md, up to four slides with their alt text, and
notapoll.org as a clickable link. Bluesky has no scheduler, so `post` sends at once. `schedule` (run after Matteo's
yes, next to the images) writes site/public/social/<folder>/bluesky.json with the Paris slot; the Bluesky workflow
runs `due` every 15 minutes and posts each scheduled folder whose time has come, once (Matteo, 23 Oct: the laptop
may be closed at the slot).
"""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

from .buffer import DAILY, PACK, approved, section

ROOT = Path(__file__).resolve().parents[2]
PDS = "https://bsky.social/xrpc"
MAX_IMAGES, MAX_BYTES = 4, 976_000


def creds() -> tuple[str, str]:
    import os
    env = {k: os.environ[k] for k in ("BLUESKY_HANDLE", "BLUESKY_APP_PASSWORD") if os.environ.get(k)}
    dotenv = ROOT.parent / ".env"
    for line in (dotenv.read_text(encoding="utf-8").splitlines() if len(env) < 2 and dotenv.exists() else []):
        if "=" in line and not line.lstrip().startswith("#"):
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"')
    if not env.get("BLUESKY_HANDLE") or not env.get("BLUESKY_APP_PASSWORD"):
        raise SystemExit("BLUESKY_HANDLE and BLUESKY_APP_PASSWORD are not in .env yet")
    return env["BLUESKY_HANDLE"], env["BLUESKY_APP_PASSWORD"]


def session() -> dict:
    handle, password = creds()
    r = requests.post(f"{PDS}/com.atproto.server.createSession", json={"identifier": handle, "password": password},
                      timeout=30)
    r.raise_for_status()
    return r.json()


def facets(text: str) -> list[dict]:
    """notapoll.org (and any https link) as clickable links; Bluesky counts positions in UTF-8 bytes."""
    out = []
    for m in re.finditer(r"(https?://\S+|notapoll\.org(?:/[\w\-/]*)?)", text):
        url = m.group(1).rstrip(".,")
        start = len(text[:m.start()].encode("utf-8"))
        out.append({"index": {"byteStart": start, "byteEnd": start + len(url.encode("utf-8"))},
                    "features": [{"$type": "app.bsky.richtext.facet#link",
                                  "uri": url if url.startswith("http") else f"https://{url}"}]})
    return out


def folder_path(folder: str) -> tuple[Path, dict]:
    for pack in (DAILY, PACK):
        if (pack / folder).exists():
            return pack / folder, approved(pack / "APPROVED.json")
    raise SystemExit(f"{folder}: no such kit folder")


def record(folder: str) -> tuple[dict, list[tuple[Path, str]]]:
    d, _ = folder_path(folder)
    text = section((d / "single-post.md").read_text(encoding="utf-8"), "Bluesky")
    if not text:
        raise SystemExit(f"{folder}: no Bluesky text in single-post.md")
    if len(text) > 300:
        raise SystemExit(f"{folder}: Bluesky text is {len(text)} characters (limit 300)")
    alts = dict(line.split(": ", 1) for line in (d / "alt-text.txt").read_text(encoding="utf-8").splitlines())
    slides = sorted(d.glob("slide-*.jpg"), key=lambda p: int(p.stem.split("-")[1]))[:MAX_IMAGES]
    for p in slides:
        if p.stat().st_size > MAX_BYTES:
            raise SystemExit(f"{p}: {p.stat().st_size} bytes, over Bluesky's image limit")
    rec = {"$type": "app.bsky.feed.post", "text": text, "facets": facets(text), "langs": ["en"],
           "createdAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")}
    return rec, [(p, alts.get(p.name, "")) for p in slides]


def post(folder: str) -> str:
    _, ok = folder_path(folder)
    if folder not in ok:
        raise SystemExit(f"{folder}: not approved (APPROVED.json)")
    rec, images = record(folder)
    return send(rec, images)


SOCIAL = ROOT / "site" / "public" / "social"


def schedule(folder: str, local: str) -> Path:
    """After Matteo's yes: the post's Bluesky text, alt texts and Paris slot beside its public images."""
    from zoneinfo import ZoneInfo
    _, ok = folder_path(folder)
    if folder not in ok:
        raise SystemExit(f"{folder}: not approved (APPROVED.json)")
    rec, images = record(folder)
    if not all((SOCIAL / folder / p.name).exists() for p, _ in images):
        raise SystemExit(f"{folder}: copy the slides to site/public/social/{folder}/ first")
    at = datetime.strptime(local, "%Y-%m-%d %H:%M").replace(tzinfo=ZoneInfo("Europe/Paris")).astimezone(timezone.utc)
    out = SOCIAL / folder / "bluesky.json"
    out.write_text(json.dumps({"at": at.isoformat().replace("+00:00", "Z"), "text": rec["text"],
                               "images": [[p.name, alt] for p, alt in images]}, indent=1, ensure_ascii=False) + "\n",
                   encoding="utf-8", newline="\n")
    return out


def due(now: datetime | None = None) -> list[str]:
    """Posts every scheduled folder whose time has come in the last 24 hours and that isn't on the feed yet."""
    from datetime import timedelta
    now = now or datetime.now(timezone.utc)
    feed = None
    out = []
    for f in sorted(SOCIAL.glob("*/bluesky.json")):
        job = json.loads(f.read_text(encoding="utf-8"))
        at = datetime.fromisoformat(job["at"].replace("Z", "+00:00"))
        if not now - timedelta(hours=24) <= at <= now:
            continue
        if feed is None:
            feed = [x["post"]["record"]["text"] for x in requests.get(
                "https://public.api.bsky.app/xrpc/app.bsky.feed.getAuthorFeed",
                params={"actor": "notapoll.org", "limit": 30}, timeout=30).json()["feed"]]
        if any(t[:80] == job["text"][:80] for t in feed):
            continue
        rec = {"$type": "app.bsky.feed.post", "text": job["text"], "facets": facets(job["text"]), "langs": ["en"],
               "createdAt": now.isoformat().replace("+00:00", "Z")}
        out.append(f"{f.parent.name}: {send(rec, [(f.parent / name, alt) for name, alt in job['images']])}")
    return out


def send(rec: dict, images: list[tuple[Path, str]]) -> str:
    s = session()
    auth = {"Authorization": f"Bearer {s['accessJwt']}"}
    embeds = []
    for path, alt in images:
        r = requests.post(f"{PDS}/com.atproto.repo.uploadBlob", data=path.read_bytes(),
                          headers=auth | {"Content-Type": "image/jpeg"}, timeout=60)
        r.raise_for_status()
        embeds.append({"alt": alt, "image": r.json()["blob"], "aspectRatio": {"width": 1080, "height": 1350}})
    if embeds:
        rec["embed"] = {"$type": "app.bsky.embed.images", "images": embeds}
    r = requests.post(f"{PDS}/com.atproto.repo.createRecord", headers=auth, timeout=30,
                      json={"repo": s["did"], "collection": "app.bsky.feed.post", "record": rec})
    r.raise_for_status()
    rkey = r.json()["uri"].rsplit("/", 1)[1]
    return f"https://bsky.app/profile/{s['handle']}/post/{rkey}"


def main(argv: list[str]) -> int:
    cmd = argv[0] if argv else "check"
    if cmd == "check":  # logs in and prints the handle, nothing else
        print("logged in as", session()["handle"])
    elif cmd == "dry":
        rec, images = record(argv[1])
        print(json.dumps(rec, indent=1, ensure_ascii=False))
        print([f"{p.name}: {a[:60]}" for p, a in images])
    elif cmd == "post":
        print(post(argv[1]))
    elif cmd == "schedule":
        print(schedule(argv[1], argv[2]))
    elif cmd == "due":
        import os
        if not (os.environ.get("BLUESKY_HANDLE") or (ROOT.parent / ".env").exists()):
            print("no Bluesky login configured; nothing posted")
            return 0
        print("\n".join(due()) or "nothing due")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
