import type { Party, RaceMeta } from "./types";

export const in100 = (p: number) => Math.round(p * 100);

export const partyVar = (p: Party) => (p === "D" ? "var(--dem)" : p === "R" ? "var(--rep)" : "var(--ind)");
export const partyName = (p: Party) => (p === "D" ? "Democrat" : p === "R" ? "Republican" : "the independent");

// 35–65% is a toss-up (publishing.md). Lean, likely and safe cut points follow the usual 65/80/95 convention.
export type Rating = "Toss-up" | "Lean" | "Likely" | "Safe";
export function rating(p: number): Rating {
  const q = Math.max(p, 1 - p);
  if (q <= 0.65) return "Toss-up";
  if (q <= 0.8) return "Lean";
  if (q <= 0.95) return "Likely";
  return "Safe";
}

export function leader(p: number, meta: RaceMeta) {
  const left = p >= 0.5;
  return {
    name: left ? meta.candidates.left : meta.candidates.right,
    party: (left ? meta.left_party : "R") as Party,
    p: left ? p : 1 - p,
  };
}

export function margin(m: number, leftParty: Party) {
  if (Math.abs(m) < 0.05) return "Even";
  const side = m > 0 ? leftParty : "R";
  return `${side}+${Math.abs(m).toFixed(1)}`;
}

export const surname = (name: string) => name.split(" ").slice(-1)[0];

export const pct = (p: number) => `${Math.round(p * 100)}%`;

export function longDate(iso: string) {
  return new Date(`${iso}T12:00:00Z`).toLocaleDateString("en-GB", {
    weekday: "short", day: "numeric", month: "short", year: "numeric", timeZone: "UTC",
  });
}

export function daysTo(iso: string, target = "2026-11-03") {
  return Math.round((Date.parse(target) - Date.parse(iso)) / 86400000);
}
