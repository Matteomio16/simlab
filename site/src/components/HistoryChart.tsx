"use client";

import { useState } from "react";

const MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const fmt = (iso: string) => `${Number(iso.slice(8, 10))} ${MON[Number(iso.slice(5, 7)) - 1]}`;
const TEXT = { fontFamily: "var(--font-sans)", fontSize: 11, fontWeight: 600, letterSpacing: "0.02em" } as const;

// A chance over time, one point per published day (Matteo, 12 Oct: race histories). The toss-up band is shaded, the
// line takes the colour of whoever leads today, and hovering (or tapping) shows that day's value.
export default function HistoryChart({
  points, label, color = "var(--sim)", w = 640, who, today,
}: {
  points: { date: string; p: number }[];
  // "If the election were today" by date, drawn as a lighter dashed line (Matteo, 12 Oct).
  today?: Record<string, number>;
  label: string;
  color?: string;
  w?: number;
  who: string;
}) {
  const [hover, setHover] = useState<number | null>(null);
  if (points.length < 2) return null;
  const W = w, H = w < 480 ? 180 : 200, pad = { l: 30, r: 44, t: 14, b: 28 };
  const x = (i: number) => pad.l + (i / (points.length - 1)) * (W - pad.l - pad.r);
  const y = (p: number) => pad.t + (1 - p) * (H - pad.t - pad.b);
  const d = points.map((pt, i) => `${i ? "L" : "M"}${x(i).toFixed(1)},${y(pt.p).toFixed(1)}`).join("");
  const td = today
    ? points.map((pt, i) => [i, today[pt.date]] as const).filter(([, v]) => v != null).map(([i, v], k) => `${k ? "L" : "M"}${x(i).toFixed(1)},${y(v).toFixed(1)}`).join("")
    : "";
  const last = points.length - 1;
  const at = hover ?? last;
  const step = Math.max(1, Math.ceil(points.length / (w < 480 ? 3 : 6)));
  const ticks = points.map((_, i) => i).filter((i) => i % step === 0 || i === last);
  const n = Math.round(points[at].p * 100);
  const tv = today?.[points[at].date];
  const tip = `${fmt(points[at].date)} · ${who} ${n}${tv != null ? ` · today ${Math.round(tv * 100)}` : ""}`;
  const tw = Math.max(92, tip.length * 6.6 + 16);
  const tipX = Math.min(Math.max(x(at), pad.l + tw / 2), W - pad.r - tw / 2);

  return (
    <svg
      viewBox={`0 0 ${W} ${H}`}
      className="h-auto w-full touch-none select-none"
      role="img"
      aria-label={`${label}, from ${fmt(points[0].date)} to ${fmt(points[last].date)}: ${Math.round(points[0].p * 100)} to ${Math.round(points[last].p * 100)} in 100`}
      onMouseLeave={() => setHover(null)}
    >
      <rect x={pad.l} y={y(0.55)} width={W - pad.l - pad.r} height={y(0.45) - y(0.55)} fill="var(--tossup)" />
      {[0, 0.25, 0.5, 0.75, 1].map((p) => (
        <g key={p}>
          <line x1={pad.l} x2={W - pad.r} y1={y(p)} y2={y(p)} stroke={p === 0.5 ? "var(--axis)" : "var(--rule)"} strokeDasharray={p === 0.5 ? undefined : "2 3"} />
          <text x={pad.l - 6} y={y(p) + 3.5} textAnchor="end" fill="var(--muted)" style={TEXT}>{p * 100}</text>
        </g>
      ))}
      {ticks.map((i) => (
        <text key={i} x={x(i)} y={H - 8} textAnchor={i === 0 ? "start" : i === last ? "end" : "middle"} fill="var(--muted)" style={TEXT}>
          {fmt(points[i].date)}
        </text>
      ))}
      {td && <path d={td} fill="none" stroke={color} strokeWidth={1.6} strokeDasharray="4 3" opacity={0.55} strokeLinejoin="round" />}
      <path d={d} fill="none" stroke={color} strokeWidth={2} strokeLinejoin="round" strokeLinecap="round" />
      {points.map((pt, i) => (
        <circle key={pt.date} cx={x(i)} cy={y(pt.p)} r={points.length > 30 ? 0 : 2.5} fill={color} />
      ))}
      <circle cx={x(last)} cy={y(points[last].p)} r={4.5} fill={color} stroke="var(--paper)" strokeWidth={2} />
      <text x={x(last) + 8} y={y(points[last].p) + 4} fill="var(--ink)" style={{ ...TEXT, fontSize: 12.5, fontWeight: 700 }}>
        {Math.round(points[last].p * 100)}
      </text>

      {hover != null && (
        <g pointerEvents="none">
          <line x1={x(at)} x2={x(at)} y1={pad.t} y2={H - pad.b} stroke="var(--ink)" strokeWidth={1} />
          <circle cx={x(at)} cy={y(points[at].p)} r={5} fill={color} stroke="var(--paper)" strokeWidth={2} />
          <rect x={tipX - tw / 2} y={1} width={tw} height={19} rx={3} fill="var(--ink)" />
          <text x={tipX} y={14.5} textAnchor="middle" fill="#fff" style={{ ...TEXT, fontSize: 10.5 }}>
            {tip}
          </text>
        </g>
      )}

      {points.map((pt, i) => {
        const left = i === 0 ? pad.l : (x(i - 1) + x(i)) / 2;
        const right = i === last ? W - pad.r : (x(i) + x(i + 1)) / 2;
        return (
          <rect
            key={pt.date}
            x={left}
            y={pad.t}
            width={Math.max(1, right - left)}
            height={H - pad.t - pad.b}
            fill="transparent"
            onMouseEnter={() => setHover(i)}
            onTouchStart={() => setHover(i)}
          />
        );
      })}
    </svg>
  );
}
