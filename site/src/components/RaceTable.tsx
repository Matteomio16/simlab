"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import type { Party } from "@/lib/types";

export type Row = {
  id: string;
  slug: string;
  title: string;
  state: string;
  left: string;
  right: string;
  leftParty: Party;
  p: number;
  today: number | null;
  pollAvg: string | null;
  market: number | null;
  cook: string | null;
  rating: string;
  tierFill: string;
  tierInk: string;
  leader: Party;
};

const SORTS = {
  close: { label: "Closest", fn: (a: Row, b: Row) => Math.abs(a.p - 0.5) - Math.abs(b.p - 0.5) },
  left: { label: "Most Democratic", fn: (a: Row, b: Row) => b.p - a.p },
  right: { label: "Most Republican", fn: (a: Row, b: Row) => a.p - b.p },
  state: { label: "State", fn: (a: Row, b: Row) => a.title.localeCompare(b.title) },
} as const;

const color = (p: Party) => (p === "D" ? "var(--dem)" : p === "R" ? "var(--rep)" : "var(--ind)");

export default function RaceTable({ rows }: { rows: Row[] }) {
  const [sort, setSort] = useState<keyof typeof SORTS>("close");
  const [all, setAll] = useState(false);
  const sorted = useMemo(() => [...rows].sort(SORTS[sort].fn), [rows, sort]);
  const competitive = sorted.filter((r) => !r.rating.startsWith("Safe"));
  const shown = all ? sorted : competitive;

  return (
    <div>
      <div className="flex flex-wrap items-center gap-x-5 gap-y-2 text-[0.85rem]">
        <span className="label-muted">Sort</span>
        {(Object.keys(SORTS) as (keyof typeof SORTS)[]).map((k) => (
          <button key={k} onClick={() => setSort(k)} aria-pressed={sort === k}
            className={`font-semibold ${sort === k ? "text-ink underline decoration-2 underline-offset-[6px]" : "text-muted hover:text-ink"}`}>
            {SORTS[k].label}
          </button>
        ))}
      </div>
      <table className="mt-4 w-full border-collapse text-[0.92rem]">
        <thead>
          <tr className="border-y-2 border-rule-strong text-left text-[0.7rem] font-bold uppercase tracking-[0.06em]">
            <th className="py-2 pr-3">Race</th>
            <th className="py-2 pr-3">Chance of winning, Nov. 3</th>
            <th className="hidden py-2 pr-3 text-right md:table-cell">Today</th>
            <th className="hidden py-2 pr-3 text-right sm:table-cell">Poll avg.</th>
            <th className="hidden py-2 pr-3 text-right sm:table-cell">Market</th>
            <th className="hidden py-2 text-right lg:table-cell">Cook</th>
          </tr>
        </thead>
        <tbody>
          {shown.map((r) => {
            const lead = r.p >= 0.5;
            const n = Math.round((lead ? r.p : 1 - r.p) * 100);
            return (
              <tr key={r.id} className="border-b border-rule align-top hover:bg-paper-2">
                <td className="py-3 pr-3">
                  <Link href={`/senate/${r.slug}`} className="font-bold hover:underline">{r.title}</Link>
                  <span className="mt-0.5 block text-[0.8rem] text-ink-2">
                    <span style={{ color: color(r.leftParty) }}>{r.left}</span>
                    <span className="text-muted"> vs. </span>
                    <span style={{ color: "var(--rep)" }}>{r.right}</span>
                  </span>
                </td>
                <td className="py-3 pr-3">
                  <div className="flex items-baseline justify-between gap-3">
                    <span>
                      <span className="font-semibold">{(lead ? r.left : r.right).split(" ").slice(-1)[0]}</span>{" "}
                      <span className="font-bold" style={{ color: color(r.leader) }}>{n}</span>
                      <span className="text-muted"> in 100</span>
                    </span>
                    <span className="whitespace-nowrap px-1.5 py-px text-[0.68rem] font-bold uppercase tracking-[0.05em]"
                      style={{ background: r.tierFill, color: r.tierInk }}>
                      {r.rating}
                    </span>
                  </div>
                  <div className="relative mt-2 h-[6px]" aria-hidden="true">
                    <div className="absolute inset-y-0 left-0" style={{ width: `${r.p * 100}%`, background: color(r.leftParty) }} />
                    <div className="absolute inset-y-0 right-0" style={{ width: `${100 - r.p * 100}%`, background: "var(--rep)" }} />
                    <div className="absolute -inset-y-1 left-1/2 w-px bg-ink" />
                  </div>
                </td>
                <td className="hidden py-3 pr-3 text-right text-ink-2 md:table-cell">{r.today == null ? "–" : Math.round(r.today * 100)}</td>
                <td className="hidden py-3 pr-3 text-right text-ink-2 sm:table-cell">{r.pollAvg ?? "–"}</td>
                <td className="hidden py-3 pr-3 text-right text-ink-2 sm:table-cell">{r.market == null ? "–" : `${Math.round(r.market * 100)}%`}</td>
                <td className="hidden py-3 text-right text-ink-2 lg:table-cell">{r.cook?.replace("Tossup", "Toss-up").replace("Solid", "Safe") ?? "–"}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
      <div className="mt-3 flex flex-wrap items-start justify-between gap-3">
        <p className="note max-w-xl">
          Today: the Democrat&rsquo;s (or independent&rsquo;s) chance in 100 if the election were held today. Market: that
          candidate&rsquo;s price on Kalshi and Polymarket. Poll avg.: the margin. Markets and Cook are shown for comparison and never enter the forecast.
        </p>
        {rows.length > competitive.length && (
          <button onClick={() => setAll(!all)} className="text-sm font-semibold underline underline-offset-4">
            {all ? "Show competitive races only" : `Show all ${rows.length} races`}
          </button>
        )}
      </div>
    </div>
  );
}
