import APPROVED from "./approved.json";

// Only the launch page is public until Matteo approves each page's content and layout (30 Sep). Unapproved pages stay
// on the unlisted previews for review; set a page to true in approved.json after his yes (postbuild reads it too).
const REVIEW = process.env.SITE_PREVIEW === "1";
export const SHOW = Object.fromEntries(Object.entries(APPROVED).map(([k, v]) => [k, v || REVIEW])) as Record<keyof typeof APPROVED, boolean>;

export const SITE = {
  name: "NotAPoll.org",
  url: "https://notapoll.org",
  label: "Social simulation, not a poll",
  electionDay: "2026-11-03",
  launchDay: "2026-10-12",
  studio: { name: "Scalia Studio", url: "https://scaliastudio.dev" },
  // Shown only once each account exists (Matteo's step, roadmap C3). Flip `live` to true per account.
  social: [
    { name: "Instagram", handle: "@notapollorg", url: "https://www.instagram.com/notapollorg/", live: true },
    { name: "X", handle: "@notapoll", url: "https://x.com/notapoll", live: true },
    { name: "Threads", handle: "@notapollorg", url: "https://www.threads.net/@notapollorg", live: true },
    { name: "Bluesky", handle: "@notapoll.org", url: "https://bsky.app/profile/notapoll.org", live: false },
  ],
};
