// Pages Matteo hasn't approved yet (30 Sep): left out of the public site, kept on the unlisted previews for review.
// Set a page to true once he approves it.
const APPROVED = { methods: false, labNotes: false };
const REVIEW = process.env.SITE_PREVIEW === "1";
export const SHOW = { methods: APPROVED.methods || REVIEW, labNotes: APPROVED.labNotes || REVIEW };

export const SITE = {
  name: "NotAPoll.org",
  url: "https://notapoll.org",
  label: "Social simulation, not a poll",
  electionDay: "2026-11-03",
  launchDay: "2026-10-12",
  studio: { name: "Scalia Studio", url: "https://scaliastudio.dev" },
  // Shown only once each account exists (Matteo's step, roadmap C3). Flip `live` to true per account.
  social: [
    { name: "Instagram", handle: "@notapoll.org", url: "https://www.instagram.com/notapoll.org", live: false },
    { name: "X", handle: "@notapoll", url: "https://x.com/notapoll", live: false },
    { name: "Threads", handle: "@notapoll.org", url: "https://www.threads.net/@notapoll.org", live: false },
    { name: "Bluesky", handle: "@notapoll.org", url: "https://bsky.app/profile/notapoll.org", live: false },
  ],
};
