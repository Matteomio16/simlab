import type { District } from "./data";
import type { Seat } from "@/components/HouseMap";
import { surname, tierColor } from "./format";

const pct = (p: number) => Math.round(p * 100);

// A seat's colour and hover line for the House map.
export function seatOf(d: District): Seat {
  const fill = d.p != null ? tierColor(d.p, d.left).fill : d.fixed === "R" ? "var(--rep-1)" : "var(--dem-1)";
  const title = d.p != null
    ? `${d.id}: ${d.dName ?? "Democrat"} ${pct(d.p)} in 100, ${d.rName ?? "Republican"} ${100 - pct(d.p)}`
    : `${d.id}: uncontested, ${d.fixed === "R" ? "Republican" : "Democratic"} seat`;
  const last = (n: string | null, fallback: string) => surname(n ?? fallback);
  const line = d.p != null
    ? `${last(d.dName, "Democrat")} ${pct(d.p)} · ${last(d.rName, "Republican")} ${100 - pct(d.p)}`
    : `Uncontested, ${d.fixed === "R" ? "Republican" : "Democratic"}`;
  return { id: d.id, slug: d.slug, state: d.state, fill, title, line };
}

// Expert ratings averaged (races.json ratings_consensus: +3 safe D to -3 safe R).
export function consensusName(c: number | null) {
  if (c == null) return null;
  const r = Math.round(c);
  if (r === 0) return "Toss-up";
  return `${["", "Lean", "Likely", "Safe"][Math.min(3, Math.abs(r))]} ${r > 0 ? "D" : "R"}`;
}
