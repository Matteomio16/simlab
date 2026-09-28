# Accounts setup (Matteo)

Written 28 Sep for the making-of posts from about 3 Oct. Matteo does every step: Claude never creates accounts or types
credentials. Images, bios and the pinned post are in `kits/brand/` (`post.md` has the bios with character counts).
Nothing is posted until Matteo approves each post.

Before you start: install an authenticator app on your phone (free: 2FAS, Aegis, Google Authenticator or Microsoft
Authenticator). Save every platform's backup codes offline, not in the same email inbox.

## 1. Email aliases (Cloudflare Email Routing)

1. Cloudflare dashboard → notapoll.org → Email → Email Routing → Enable. Accept the MX and SPF records it adds.
2. Destination addresses → add your own inbox and click the verification link Cloudflare sends.
3. Routing rules → custom addresses, each forwarding to that inbox: `ig@notapoll.org`, `x@notapoll.org`,
   `bsky@notapoll.org` (and `buffer@notapoll.org` if you want Buffer separate).
4. Send a test email to each alias and check it arrives.

Optional but advised before the first post: since images show notapoll.org and the site comes later, add a redirect
rule (Rules → Redirect Rules) from notapoll.org to labs.scaliastudio.dev/midterms, or a one-page holding site, so
the address never leads nowhere.

## 2. Instagram, then Threads

1. Sign up with `ig@notapoll.org`. Username `notapoll.org`, name `NotAPoll`.
2. Settings → Account type and tools → Switch to professional account → **Creator**. Category: Education (or Science &
   Technology). Hide the category label on the profile if you prefer.
3. Profile: avatar `kits/brand/avatar.jpg`, bio from `post.md`, link: leave empty until the redirect or site works.
4. Accounts Center → Password and security → Two-factor authentication → Authentication app.
5. Threads: open the Threads app, log in with Instagram, import the profile. Same handle, same avatar and bio.
6. Do not boost posts or turn on ads: organic only.

## 3. X

1. Sign up with `x@notapoll.org`. Handle `@notapoll`, name `NotAPoll`.
2. Profile: avatar `avatar.jpg`, header `kits/brand/header-x.jpg`, bio from `post.md`, website notapoll.org once it
   resolves.
3. Settings → Security and account access → Security → Two-factor authentication → Authentication app (SMS is for paid
   accounts only; the app is free).
4. Nothing paid: no Premium, no API credits.

## 4. Bluesky (with the domain handle)

1. Sign up with `bsky@notapoll.org`; you start as `notapoll.bsky.social`.
2. Settings → Account → Handle → "I have my own domain" → enter `notapoll.org`. Bluesky shows a TXT record.
3. Cloudflare → notapoll.org → DNS → Add record: type TXT, name `_atproto`, content exactly as Bluesky shows
   (`did=did:plc:…`). Save, then press Verify in Bluesky. The handle becomes `@notapoll.org`.
4. Profile: avatar `avatar.jpg`, banner `kits/brand/banner-bluesky.jpg`, bio from `post.md`.
5. Settings → Privacy and security → turn on two-factor authentication (Bluesky's own option; check whether it offers an
   authenticator app or only email codes).

## 5. Buffer (X, Threads, Bluesky)

1. Sign up at buffer.com (your own inbox or `buffer@notapoll.org`). Choose **Free**, not the 14-day trial: the trial
   asks for a card.
2. Connect three channels: X, Threads, Bluesky. Instagram stays on its own scheduler (the Instagram app or Meta Business
   Suite), which keeps Buffer inside its 3 free channels.
3. Turn on two-factor authentication in Buffer's account settings.
4. The API key comes later (roadmap C9, 12–18 Oct), when posting is automated behind the approval flag.

## 6. When done

Tell the Content & site session the four handles are live. It then prepares the first posts (the pinned "Start
here" carousel and Lab notes 1–3) for your approval; you post them, or approve each one for scheduling.
