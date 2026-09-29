import Link from "next/link";
import { TILES } from "@/lib/tiles";

export type Tile = { state: string; fill: string; ink: string; value?: string; href?: string; title: string; special?: boolean };

const S = 46;
const GAP = 3;

// One square per state; states with no Senate race this year stay blank.
export default function TileMap({ tiles, className = "" }: { tiles: Tile[]; className?: string }) {
  const byState = new Map(tiles.map((t) => [t.state, t]));
  const W = 12 * S + 11 * GAP;
  const H = 8 * S + 7 * GAP;
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className={`h-auto w-full ${className}`} role="img" aria-label="Map of the states, one square each">
      {Object.entries(TILES).map(([st, [c, r]]) => {
        const t = byState.get(st);
        const x = c * (S + GAP);
        const y = r * (S + GAP);
        const body = (
          <g>
            <title>{t ? t.title : `${st}: no Senate race in 2026`}</title>
            <rect x={t ? x : x + 0.5} y={t ? y : y + 0.5} width={t ? S : S - 1} height={t ? S : S - 1} fill={t ? t.fill : "var(--paper)"} stroke={t ? "none" : "var(--rule)"} />
            <text x={x + 5} y={y + 15} fill={t ? t.ink : "var(--axis)"} style={{ fontSize: 12.5, fontWeight: 700, letterSpacing: "0.02em" }}>
              {st}
            </text>
            {t?.special && <circle cx={x + S - 7} cy={y + 8} r={2.6} fill={t.ink} />}
            {t?.value && (
              <text x={x + S - 5} y={y + S - 6} textAnchor="end" fill={t.ink} style={{ fontSize: 13.5, fontWeight: 600 }}>
                {t.value}
              </text>
            )}
          </g>
        );
        return t?.href ? (
          <Link key={st} href={t.href} className="hover:opacity-80">
            {body}
          </Link>
        ) : (
          <g key={st}>{body}</g>
        );
      })}
    </svg>
  );
}

export function Legend({ items }: { items: { fill: string; label: string; border?: boolean }[] }) {
  return (
    <ul className="flex flex-wrap gap-x-4 gap-y-1.5 text-[0.78rem] text-ink-2">
      {items.map((i) => (
        <li key={i.label} className="flex items-center gap-1.5">
          <span className={`inline-block h-3 w-3 ${i.border ? "border border-rule" : ""}`} style={{ background: i.fill }} />
          {i.label}
        </li>
      ))}
    </ul>
  );
}
