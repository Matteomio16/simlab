import Link from "next/link";
import type { Row } from "./RaceTable";
import SplitChance from "./SplitChance";
import type { Party } from "@/lib/types";

const color = (p: string) => (p === "D" ? "var(--dem)" : p === "R" ? "var(--rep)" : "var(--ind)");

// The closest races as cards: the leader's chance, the bar and the rating, one click from the race page.
export default function RaceCards({ rows }: { rows: Row[] }) {
  return (
    <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {rows.map((r) => {
        return (
          <li key={r.id}>
            <Link href={`/senate/${r.slug}`} prefetch={false} className="card group flex h-full flex-col p-4">
              <div className="flex items-start justify-between gap-2">
                <span className="text-[1.05rem] font-bold leading-tight">{r.title}</span>
                <span className="whitespace-nowrap px-1.5 py-px text-[0.66rem] font-bold uppercase tracking-[0.05em]" style={{ background: r.tierFill, color: r.tierInk }}>
                  {r.rating}
                </span>
              </div>
              <p className="mt-1 text-[0.8rem] text-ink-2">
                <span style={{ color: color(r.leftParty) }}>{r.left.split(" ").slice(-1)[0]}</span>
                <span className="text-muted"> vs. </span>
                <span className="text-rep">{r.right.split(" ").slice(-1)[0]}</span>
              </p>
              <div className="mt-4 mb-auto">
                <SplitChance p={r.p} left={r.leftParty as Party} size="sm" />
              </div>
              <span className="mt-3 text-[0.78rem] font-semibold text-muted transition-colors group-hover:text-ink">Open the race →</span>
            </Link>
          </li>
        );
      })}
    </ul>
  );
}
