"use client";

import { useEffect, useState } from "react";

// Live countdown in the reader's browser. The server render shows whole days, so the page reads right without
// JavaScript.
function parts(ms: number) {
  const s = Math.max(0, Math.floor(ms / 1000));
  return { d: Math.floor(s / 86400), h: Math.floor((s % 86400) / 3600), m: Math.floor((s % 3600) / 60), s: s % 60 };
}

export default function Countdown({ to, initialDays }: { to: string; initialDays: number }) {
  const [p, setP] = useState<ReturnType<typeof parts> | null>(null);
  useEffect(() => {
    const tick = () => setP(parts(Date.parse(to) - Date.now()));
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, [to]);
  const cells: [string, number | null][] = p
    ? [["days", p.d], ["hours", p.h], ["min", p.m], ["sec", p.s]]
    : [["days", initialDays], ["hours", null], ["min", null], ["sec", null]];
  return (
    <div className="flex gap-2" role="timer" aria-label={`${p?.d ?? initialDays} days to the first public forecast`}>
      {cells.map(([k, v]) => (
        <div key={k} className="min-w-[4.2rem] border border-rule bg-paper px-3 py-2 text-center">
          <p className="text-[2rem] font-extrabold leading-none tracking-[-0.02em] tabular-nums">{v == null ? "–" : String(v).padStart(2, "0")}</p>
          <p className="mt-1 text-[0.68rem] font-bold uppercase tracking-[0.08em] text-muted">{k}</p>
        </div>
      ))}
    </div>
  );
}
