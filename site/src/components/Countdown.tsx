"use client";

import { useEffect, useState } from "react";

// Live countdown in the reader's browser, set as a line of figures. The server render shows whole days, so the page
// reads right without JavaScript.
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
    ? [["days", p.d], ["hr", p.h], ["min", p.m], ["sec", p.s]]
    : [["days", initialDays], ["hr", null], ["min", null], ["sec", null]];
  return (
    <span className="inline-flex items-baseline gap-4 tabular-nums" role="timer" aria-label={`${p?.d ?? initialDays} days to the first public forecast`}>
      {cells.map(([k, v]) => (
        <span key={k} className="inline-flex items-baseline gap-1">
          <span className="text-[1.6rem] font-bold leading-none tracking-[-0.01em] text-ink">{v == null ? "–" : String(v).padStart(2, "0")}</span>
          <span className="text-[0.75rem] font-semibold text-muted">{k}</span>
        </span>
      ))}
    </span>
  );
}
