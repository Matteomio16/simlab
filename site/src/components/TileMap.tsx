"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, type MouseEvent } from "react";
import { TILES } from "@/lib/tiles";

export type Tile = { state: string; fill: string; ink: string; value?: string; href?: string; title: string; special?: boolean };

const S = 46;
const GAP = 3;
const W = 12 * S + 11 * GAP;
const H = 8 * S + 7 * GAP;
const ZOOM_MS = 520;

// One square per state; states with no Senate race this year stay blank. Selecting a state zooms the map into its
// square, then opens the race page (plain navigation for reduced motion and for new-tab clicks).
export default function TileMap({ tiles, className = "" }: { tiles: Tile[]; className?: string }) {
  const router = useRouter();
  const [zoom, setZoom] = useState<string | null>(null);
  const byState = new Map(tiles.map((t) => [t.state, t]));

  const open = (e: MouseEvent, st: string, href: string) => {
    if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey || e.button !== 0) return;
    e.preventDefault();
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return router.push(href);
    router.prefetch(href);
    setZoom(st);
    setTimeout(() => router.push(href), ZOOM_MS);
  };

  const z = zoom ? TILES[zoom] : null;
  const origin = z ? `${((z[0] * (S + GAP) + S / 2) / W) * 100}% ${((z[1] * (S + GAP) + S / 2) / H) * 100}%` : "50% 50%";

  return (
    <div className="overflow-hidden">
      <svg
        viewBox={`0 0 ${W} ${H}`}
        className={`h-auto w-full ${className}`}
        role="img"
        aria-label="Map of the states, one square each"
        style={{
          transformOrigin: origin,
          transform: zoom ? "scale(7)" : "none",
          transition: `transform ${ZOOM_MS}ms cubic-bezier(0.6, 0, 0.2, 1)`,
        }}
      >
        {Object.entries(TILES).map(([st, [c, r]]) => {
          const t = byState.get(st);
          const x = c * (S + GAP);
          const y = r * (S + GAP);
          const faded = zoom && zoom !== st;
          const body = (
            <g className={t ? "tile" : undefined} style={{ opacity: faded ? 0.08 : 1, transition: `opacity ${ZOOM_MS * 0.6}ms` }}>
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
            <Link key={st} href={t.href} onClick={(e) => open(e, st, t.href!)} aria-label={t.title}>
              {body}
            </Link>
          ) : (
            <g key={st}>{body}</g>
          );
        })}
      </svg>
    </div>
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
