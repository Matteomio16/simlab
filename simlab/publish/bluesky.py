"""Post an approved kit to Bluesky directly (Buffer Free has no room for a fourth channel):
python -m simlab.publish.bluesky check | dry FOLDER | post FOLDER

Reads BLUESKY_HANDLE and BLUESKY_APP_PASSWORD from Sim Research/.env (an app password, never the account password;
never printed). `post` sends only folders named in kits/daily/APPROVED.json (or kits/launch/APPROVED.json): the
Bluesky text from single-post.md, up to four slides with their alt text, and notapoll.org as a clickable link.
Bluesky has no scheduler, so a post goes out when this runs.
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
    env = {}
    for line in (ROOT.parent / ".env").read_text(encoding="utf-8").splitlines():
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
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
