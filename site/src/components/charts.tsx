import type { ReactNode } from "react";
import type { Band, Party } from "@/lib/types";
import { partyVar } from "@/lib/format";

// Hand-drawn SVG charts, rendered at build time. Colours are CSS tokens, so every chart follows light and dark mode.

const MONO = { fontFamily: "var(--font-sans)", fontSize: 11, fontWeight: 600, letterSpacing: "0.03em" } as const;

export function ProbBar({ p, left, height = 8 }: { p: number; left: Party; height?: number }) {
  const pct = Math.max(0, Math.min(100, p * 100));
  return (
    <div className="relative w-full overflow-hidden rounded-[2px]" style={{ height }} aria-hidden="true">
      <div className="absolute inset-y-0 left-0" style={{ width: `${pct}%`, background: partyVar(left) }} />
      <div className="absolute inset-y-0 right-0" style={{ width: `${100 - pct}%`, background: "var(--rep)" }} />
      <div className="absolute inset-y-[-2px] left-1/2 w-px bg-paper" />
    </div>
  );
}

// One dot per simulated election, stacked in 1.5-point bins along the margin axis.
export function DotPlot({ draws, left, leftName, rightName, w = 640 }: { draws: number[]; left: Party; leftName: string; rightName: string; w?: number }) {
  const W = w, pad = { l: 20, r: 20, t: 22, b: 34 };
  const lim = Math.max(10, Math.ceil(Math.max(...draws.map(Math.abs)) / 5) * 5);
  const x = (m: number) => pad.l + ((m + lim) / (2 * lim)) * (W - pad.l - pad.r);
  const r = W < 480 ? 3.4 : 4.2;
  const bin = ((2 * r + 1) / (W - pad.l - pad.r)) * 2 * lim;
  const stacks = new Map<number, number>();
  const placed = [...draws].sort((a, b) => a - b).map((m) => {
    const b = Math.round(m / bin);
    const k = stacks.get(b) ?? 0;
    stacks.set(b, k + 1);
    return { m, b, k };
  });
  const H = pad.t + pad.b + 16 + Math.max(...stacks.values()) * (r * 2 + 1.2);
  const dots = placed.map(({ m, b, k }) => ({ m, cx: x(b * bin), cy: H - pad.b - r - 1 - k * (r * 2 + 1.2) }));
  const ticks = W < 480 ? [-lim, 0, lim] : [-lim, -lim / 2, 0, lim / 2, lim];
  const leftWins = draws.filter((m) => m > 0).length;
  return (
    <figure>
      <svg viewBox={`0 0 ${W} ${H}`} className="h-auto w-full" role="img"
        aria-label={`${leftName} wins ${leftWins} and ${rightName} wins ${draws.length - leftWins} of ${draws.length} simulated elections shown.`}>
        <line x1={x(0)} x2={x(0)} y1={pad.t} y2={H - pad.b} stroke="var(--axis)" strokeDasharray="2 3" />
        <line x1={pad.l} x2={W - pad.r} y1={H - pad.b} y2={H - pad.b} stroke="var(--axis)" />
        {dots.map((d, i) => (
          <circle key={i} cx={d.cx} cy={d.cy} r={r} fill={d.m > 0 ? partyVar(left) : d.m < 0 ? "var(--rep)" : "var(--sim)"} />
        ))}
        {ticks.map((t) => (
          <text key={t} x={x(t)} y={H - pad.b + 16} textAnchor="middle" fill="var(--muted)" style={MONO}>
            {t === 0 ? "TIE" : `${t > 0 ? left : "R"}+${Math.abs(t)}`}
          </text>
        ))}
        <text x={x(-lim)} y={10} fill="var(--rep)" style={MONO}>{`← ${rightName.toUpperCase()} WINS`}</text>
        <text x={x(lim)} y={10} textAnchor="end" fill={partyVar(left)} style={MONO}>{`${leftName.toUpperCase()} WINS →`}</text>
      </svg>
    </figure>
  );
}

type RangeRow = { label: string; band?: Band; point?: number | null; color: string; strong?: boolean };

// Margin ranges (10th to 90th percentile) on one axis, with the poll average as a single tick.
export function MarginRanges({ rows, left, w = 640 }: { rows: RangeRow[]; left: Party; w?: number }) {
  const narrow = w < 480;
  const W = w, rowH = narrow ? 46 : 34, pad = { l: narrow ? 22 : 170, r: 22, t: 8, b: 26 };
  const H = pad.t + rows.length * rowH + pad.b;
  const vals = rows.flatMap((r) => (r.band ? [r.band.p10, r.band.p90] : r.point != null ? [r.point] : []));
  const lim = Math.max(10, Math.ceil(Math.max(...vals.map(Math.abs)) / 5) * 5);
  const x = (m: number) => pad.l + ((m + lim) / (2 * lim)) * (W - pad.l - pad.r);
  const ticks = narrow ? [-lim, 0, lim] : [-lim, -lim / 2, 0, lim / 2, lim];
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="h-auto w-full" role="img" aria-label="Margin ranges beside the poll average">
      {ticks.map((t) => (
        <g key={t}>
          <line x1={x(t)} x2={x(t)} y1={pad.t} y2={H - pad.b} stroke={t === 0 ? "var(--axis)" : "var(--rule)"} strokeDasharray={t === 0 ? "" : "2 3"} />
          <text x={x(t)} y={H - 8} textAnchor="middle" fill="var(--muted)" style={MONO}>
            {t === 0 ? "TIE" : `${t > 0 ? left : "R"}+${Math.abs(t)}`}
          </text>
        </g>
      ))}
      {rows.map((r, i) => {
        const cy = pad.t + i * rowH + rowH / 2 + (narrow ? 7 : 0);
        return (
          <g key={r.label}>
            <text x={0} y={narrow ? cy - 13 : cy + 4} fill={r.strong ? "var(--ink)" : "var(--ink-2)"} style={{ fontSize: 12.5, fontWeight: r.strong ? 600 : 400 }}>
              {r.label}
            </text>
            {r.band && (
              <>
                <rect x={x(r.band.p10)} y={cy - 6} width={Math.max(2, x(r.band.p90) - x(r.band.p10))} height={12} rx={2} fill={r.color} opacity={r.strong ? 0.28 : 0.2} />
                <circle cx={x(r.band.p50)} cy={cy} r={r.strong ? 6 : 5} fill={r.color} stroke="var(--paper)" strokeWidth={2} />
              </>
            )}
            {!r.band && r.point != null && (
              <rect x={x(r.point) - 1.5} y={cy - 9} width={3} height={18} fill={r.color} />
            )}
            {!r.band && r.point == null && (
              <text x={x(0)} y={cy + 4} textAnchor="middle" fill="var(--muted)" style={MONO}>NO RECENT POLLS</text>
            )}
          </g>
        );
      })}
    </svg>
  );
}

// Republican seat totals across the simulated elections; 50 or more (with the Vice President) keeps control.
// Seats across simulated elections (Matteo, 12 Oct: colouring the bars by party misread as Democratic seats). The bars
// are neutral; the background says who controls the chamber on each side of the line. Defaults are the Senate's
// (Republican seats, 50 for control); the House passes Democratic seats and 218.
export function SeatHistogram({
  dist, w = 640, line = 50, span = 8, every,
  axis = "Republican seats", left = { label: "Democrats control", color: "var(--dem)" }, right = { label: "Republicans keep control", color: "var(--rep)" },
  label = "Distribution of Republican Senate seats across simulated elections",
}: {
  dist: Record<string, number>; w?: number; line?: number; span?: number; every?: number; axis?: string;
  left?: { label: string; color: string }; right?: { label: string; color: string }; label?: string;
}) {
  const entries = Object.entries(dist).map(([k, v]) => [Number(k), v] as const).filter(([, v]) => v > 0.0005);
  const lo = Math.min(line - span, ...entries.map(([k]) => k));
  const hi = Math.max(line + span, ...entries.map(([k]) => k));
  const W = w, H = w < 480 ? 196 : 226, pad = { l: 8, r: 8, t: 30, b: 48 };
  const n = hi - lo + 1;
  const bw = (W - pad.l - pad.r) / n;
  const max = Math.max(...entries.map(([, v]) => v));
  const y = (v: number) => (v / max) * (H - pad.t - pad.b);
  const x = (k: number) => pad.l + (k - lo) * bw;
  const base = H - pad.b;
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="h-auto w-full" role="img" aria-label={label}>
      <rect x={pad.l} y={pad.t - 22} width={x(line) - pad.l} height={base - pad.t + 22} fill={left.color} opacity={0.07} />
      <rect x={x(line)} y={pad.t - 22} width={W - pad.r - x(line)} height={base - pad.t + 22} fill={right.color} opacity={0.07} />
      <text x={x(line) - 6} y={pad.t - 9} textAnchor="end" fill={left.color} style={{ ...MONO, fontWeight: 700 }}>{`← ${left.label}`}</text>
      <text x={x(line) + 6} y={pad.t - 9} fill={right.color} style={{ ...MONO, fontWeight: 700 }}>{`${right.label} →`}</text>
      {entries.map(([k, v]) => (
        <rect key={k} x={x(k) + (bw > 3 ? 1 : 0)} y={base - y(v)} width={Math.max(0.6, bw - (bw > 3 ? 2 : 0.3))} height={y(v)} rx={bw > 3 ? 1.5 : 0} fill="var(--ink-2)" opacity={0.8}>
          <title>{`${k} ${axis.toLowerCase()}: ${(v * 100).toFixed(1)}% of simulated elections`}</title>
        </rect>
      ))}
      <line x1={x(line) - 0.5} x2={x(line) - 0.5} y1={pad.t - 22} y2={base} stroke="var(--sim)" strokeWidth={1.5} />
      <line x1={pad.l} x2={W - pad.r} y1={base} y2={base} stroke="var(--axis)" />
      {Array.from({ length: n }, (_, i) => lo + i).filter((k) => k % (every ?? (W < 480 ? 4 : 2)) === 0).map((k) => (
        <text key={k} x={x(k) + bw / 2} y={base + 16} textAnchor="middle" fill={k === line ? "var(--sim)" : "var(--muted)"} style={{ ...MONO, fontWeight: k === line ? 700 : 400 }}>{k}</text>
      ))}
      <text x={W / 2} y={H - 8} textAnchor="middle" fill="var(--ink-2)" style={{ ...MONO, fontWeight: 600 }}>{`${axis} (${line} for control)`}</text>
    </svg>
  );
}

// Chance over time; the toss-up zone (45–55%) is shaded.
export function HistoryLine({ points, label, w = 640 }: { points: { date: string; p: number }[]; label: string; w?: number }) {
  if (points.length < 2) return null;
  const W = w, H = w < 480 ? 160 : 180, pad = { l: 34, r: 40, t: 12, b: 26 };
  const x = (i: number) => pad.l + (i / (points.length - 1)) * (W - pad.l - pad.r);
  const y = (p: number) => pad.t + (1 - p) * (H - pad.t - pad.b);
  const d = points.map((pt, i) => `${i ? "L" : "M"}${x(i).toFixed(1)},${y(pt.p).toFixed(1)}`).join("");
  const last = points[points.length - 1];
  const MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  const fmt = (iso: string) => `${Number(iso.slice(8, 10))} ${MON[Number(iso.slice(5, 7)) - 1]}`;
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="h-auto w-full" role="img" aria-label={`${label}, from ${fmt(points[0].date)} to ${fmt(last.date)}`}>
      <rect x={pad.l} y={y(0.55)} width={W - pad.l - pad.r} height={y(0.45) - y(0.55)} fill="var(--tossup)" />
      {[0, 0.5, 1].map((p) => (
        <g key={p}>
          <line x1={pad.l} x2={W - pad.r} y1={y(p)} y2={y(p)} stroke={p === 0.5 ? "var(--axis)" : "var(--rule)"} />
          <text x={pad.l - 6} y={y(p) + 3} textAnchor="end" fill="var(--muted)" style={MONO}>{p * 100}</text>
        </g>
      ))}
      <text x={W - pad.r + 4} y={y(0.5) + 3} fill="var(--muted)" style={MONO}>TOSS</text>
      <path d={d} fill="none" stroke="var(--sim)" strokeWidth={2.2} strokeLinejoin="round" />
      <circle cx={x(points.length - 1)} cy={y(last.p)} r={4} fill="var(--sim)" />
      <text x={pad.l} y={H - 8} fill="var(--muted)" style={MONO}>{fmt(points[0].date).toUpperCase()}</text>
      <text x={W - pad.r} y={H - 8} textAnchor="end" fill="var(--muted)" style={MONO}>{fmt(last.date).toUpperCase()}</text>
    </svg>
  );
}

// Charts are drawn twice, for phone and for wider screens, so text stays readable at both sizes.
export function Responsive({ render, desktop = 640 }: { render: (w: number) => ReactNode; desktop?: number }) {
  return (
    <>
      <div className="sm:hidden">{render(360)}</div>
      <div className="hidden sm:block">{render(desktop)}</div>
    </>
  );
}
