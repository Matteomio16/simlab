import Link from "next/link";
import type { Row } from "./RaceTable";

const color = (p: string) => (p === "D" ? "var(--dem)" : p === "R" ? "var(--rep)" : "var(--ind)");

// The closest races as cards: the leader's chance, the bar and the rating, one click from the race page.
export default function RaceCards({ rows }: { rows: Row[] }) {
  return (
    <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {rows.map((r) => {
        const lead = r.p >= 0.5;
        const n = Math.round((lead ? r.p : 1 - r.p) * 100);
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
              <p className="mt-4 leading-none">
                <span className="text-[2.2rem] font-extrabold tracking-[-0.02em]" style={{ color: color(r.leader) }}>{n}</span>
                <span className="ml-1 text-sm font-semibold text-muted">in 100</span>
              </p>
              <p className="mt-1 text-[0.8rem] font-semibold">{(lead ? r.left : r.right).split(" ").slice(-1)[0]} leads</p>
              <div className="relative mt-auto h-[6px] pt-4" aria-hidden="true">
                <div className="absolute bottom-0 left-0 h-[6px]" style={{ width: `${r.p * 100}%`, background: color(r.leftParty) }} />
                <div className="absolute bottom-0 right-0 h-[6px]" style={{ width: `${100 - r.p * 100}%`, background: "var(--rep)" }} />
                <div className="absolute -bottom-1 left-1/2 h-[14px] w-px bg-ink" />
              </div>
              <span className="mt-3 text-[0.78rem] font-semibold text-muted transition-colors group-hover:text-ink">Open the race →</span>
            </Link>
          </li>
        );
      })}
    </ul>
  );
}
