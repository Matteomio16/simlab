"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import type { Party } from "@/lib/types";

export type Row = {
  id: string;
  slug: string;
  title: string;
  code: string;
  left: string;
  right: string;
  leftParty: Party;
  p: number;
  today: number | null;
  pollAvg: string | null;
  market: number | null;
  cook: string | null;
  rating: string;
  leader: Party;
};

const SORTS = {
  close: { label: "Closest first", fn: (a: Row, b: Row) => Math.abs(a.p - 0.5) - Math.abs(b.p - 0.5) },
  left: { label: "Most Democratic", fn: (a: Row, b: Row) => b.p - a.p },
  right: { label: "Most Republican", fn: (a: Row, b: Row) => a.p - b.p },
  state: { label: "State A–Z", fn: (a: Row, b: Row) => a.title.localeCompare(b.title) },
} as const;

const color = (p: Party) => (p === "D" ? "var(--dem)" : p === "R" ? "var(--rep)" : "var(--ind)");

function Chip({ rating, party }: { rating: string; party: Party }) {
  if (rating === "Toss-up")
    return <span className="whitespace-nowrap rounded-sm bg-tossup px-1.5 py-0.5 font-mono text-[0.66rem] uppercase tracking-wider text-sim">Toss-up</span>;
  return (
    <span className="whitespace-nowrap rounded-sm px-1.5 py-0.5 font-mono text-[0.66rem] uppercase tracking-wider"
      style={{ color: color(party), background: party === "R" ? "var(--rep-soft)" : "var(--dem-soft)" }}>
      {rating} {party}
    </span>
  );
}

export default function RaceTable({ rows }: { rows: Row[] }) {
  const [sort, setSort] = useState<keyof typeof SORTS>("close");
  const [all, setAll] = useState(false);
  const sorted = useMemo(() => [...rows].sort(SORTS[sort].fn), [rows, sort]);
  const shown = all ? sorted : sorted.filter((r) => r.rating !== "Safe");
  const hidden = rows.length - rows.filter((r) => r.rating !== "Safe").length;

  return (
    <div>
      <div className="mb-3 flex flex-wrap items-center gap-2 text-sm">
        {(Object.keys(SORTS) as (keyof typeof SORTS)[]).map((k) => (
          <button key={k} onClick={() => setSort(k)} aria-pressed={sort === k}
            className={`rounded-full border px-3 py-1 transition-colors ${sort === k ? "border-ink bg-ink text-paper" : "border-hairline text-ink-2 hover:border-baseline"}`}>
            {SORTS[k].label}
          </button>
        ))}
      </div>
      <div className="overflow-hidden rounded-md border border-hairline bg-raised">
        <table className="w-full border-collapse text-sm">
          <thead>
            <tr className="border-b border-hairline text-left font-mono text-[0.66rem] uppercase tracking-[0.08em] text-muted">
              <th className="px-3 py-2.5 font-normal">Race</th>
              <th className="px-3 py-2.5 font-normal">Simulation, 3 Nov</th>
              <th className="hidden px-3 py-2.5 text-right font-normal md:table-cell">Today</th>
              <th className="hidden px-3 py-2.5 text-right font-normal sm:table-cell">Poll avg</th>
              <th className="hidden px-3 py-2.5 text-right font-normal sm:table-cell">Market</th>
              <th className="hidden px-3 py-2.5 text-right font-normal lg:table-cell">Cook</th>
            </tr>
          </thead>
          <tbody>
            {shown.map((r) => {
              const lead = r.p >= 0.5;
              const n = Math.round((lead ? r.p : 1 - r.p) * 100);
              return (
                <tr key={r.id} className="group border-b border-hairline last:border-0 hover:bg-paper">
                  <td className="px-3 py-3 align-top">
                    <Link href={`/senate/${r.slug}`} className="block">
                      <span className="font-medium text-ink group-hover:underline">{r.title}</span>
                      <span className="mt-0.5 block text-xs text-muted">
                        <span style={{ color: color(r.leftParty) }}>{r.left}</span> v <span style={{ color: "var(--rep)" }}>{r.right}</span>
                      </span>
                    </Link>
                  </td>
                  <td className="px-3 py-3 align-top">
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-ink">
                        <span className="font-semibold tabular-nums" style={{ color: color(r.leader) }}>{n}</span>
                        <span className="text-muted"> in 100 · </span>
                        <span className="text-ink-2">{(lead ? r.left : r.right).split(" ").slice(-1)[0]}</span>
                      </span>
                      <Chip rating={r.rating} party={r.leader} />
                    </div>
                    <div className="relative mt-2 h-1.5 overflow-hidden rounded-[2px]" aria-hidden="true">
                      <div className="absolute inset-y-0 left-0" style={{ width: `${r.p * 100}%`, background: color(r.leftParty) }} />
                      <div className="absolute inset-y-0 right-0" style={{ width: `${100 - r.p * 100}%`, background: "var(--rep)" }} />
                      <div className="absolute inset-y-0 left-1/2 w-px bg-raised" />
                    </div>
                  </td>
                  <td className="hidden px-3 py-3 text-right align-top tabular-nums text-ink-2 md:table-cell">
                    {r.today == null ? "–" : `${Math.round(r.today * 100)}`}
                  </td>
                  <td className="hidden px-3 py-3 text-right align-top tabular-nums text-ink-2 sm:table-cell">{r.pollAvg ?? "–"}</td>
                  <td className="hidden px-3 py-3 text-right align-top tabular-nums text-ink-2 sm:table-cell">
                    {r.market == null ? "–" : `${Math.round(r.market * 100)}%`}
                  </td>
                  <td className="hidden px-3 py-3 text-right align-top text-ink-2 lg:table-cell">{r.cook ?? "–"}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <div className="mt-3 flex flex-wrap items-center justify-between gap-2 text-xs text-muted">
        <span>
          Today: the Democrat&rsquo;s (or independent&rsquo;s) chance in 100 if the election were held today. Market: their
          price. Poll avg: the margin.
        </span>
        {hidden > 0 && (
          <button onClick={() => setAll(!all)} className="underline underline-offset-2 hover:text-ink">
            {all ? "Hide safe races" : `Show ${hidden} safe races`}
          </button>
        )}
      </div>
    </div>
  );
}
