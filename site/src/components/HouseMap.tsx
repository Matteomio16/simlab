import { TILES } from "@/lib/tiles";
import { tierColor } from "@/lib/format";
import type { District } from "@/lib/data";

const S = 46;
const GAP = 3;
const W = 12 * S + 11 * GAP;
const H = 8 * S + 7 * GAP;
const TOP = 13;

// The House on the same state grid as the Senate map: each state's square holds one small square per district,
// coloured by its forecast; uncontested seats are filled in their party's colour.
export default function HouseMap({ districts }: { districts: District[] }) {
  const byState = new Map<string, District[]>();
  for (const d of districts) byState.set(d.state, [...(byState.get(d.state) ?? []), d]);
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="h-auto w-full" role="img" aria-label="Map of the 435 House seats, grouped by state">
      {Object.entries(TILES).map(([st, [c, r]]) => {
        const x0 = c * (S + GAP);
        const y0 = r * (S + GAP);
        const ds = byState.get(st) ?? [];
        const cols = Math.max(1, Math.ceil(Math.sqrt(ds.length * 1.3)));
        const rows = Math.max(1, Math.ceil(ds.length / cols));
        const cell = Math.min(16, (S - 4) / cols, (S - TOP - 3) / rows);
        const gx = x0 + (S - cols * cell) / 2;
        const gy = y0 + TOP + (S - TOP - 2 - rows * cell) / 2;
        return (
          <g key={st}>
            <rect x={x0 + 0.5} y={y0 + 0.5} width={S - 1} height={S - 1} fill="var(--paper)" stroke="var(--rule)" />
            <text x={x0 + 4} y={y0 + 10.5} fill="var(--ink-2)" style={{ fontSize: 9.5, fontWeight: 700, letterSpacing: "0.02em" }}>{st}</text>
            {ds.map((d, i) => {
              const fill = d.p != null ? tierColor(d.p, d.left).fill : d.fixed === "R" ? "var(--rep-1)" : "var(--dem-1)";
              const who = d.p != null
                ? `${d.dName ?? "Democrat"} ${Math.round(d.p * 100)} in 100, ${d.rName ?? "Republican"} ${100 - Math.round(d.p * 100)}`
                : `uncontested, ${d.fixed === "R" ? "Republican" : "Democratic"} seat`;
              return (
                <rect key={d.id} x={gx + (i % cols) * cell + 0.4} y={gy + Math.floor(i / cols) * cell + 0.4} width={cell - 0.8} height={cell - 0.8} fill={fill}>
                  <title>{`${d.id}: ${who}`}</title>
                </rect>
              );
            })}
          </g>
        );
      })}
    </svg>
  );
}
