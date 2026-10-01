"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState, type MouseEvent } from "react";
import { TILES } from "@/lib/tiles";

export type Tile = { state: string; fill: string; ink: string; value?: string; href?: string; title: string; special?: boolean };

const S = 46;
const GAP = 3;
const W = 12 * S + 11 * GAP;
const H = 8 * S + 7 * GAP;
const ZOOM_MS = 520;
const WASH_DELAY_MS = 180;
// Read by ArrivalWash on the race page, so the colour carries across the page change.
export const ARRIVE_KEY = "np-arrive";

// One square per state; states with no Senate race this year stay blank. Selecting a state dives into its square: the
// map zooms until the square fills it, the square's colour washes over the screen from the click, and the race page
// opens under the same colour (plain navigation for reduced motion and for new-tab clicks). Hovering a square fetches
// its page ahead, so the page is ready when the dive ends.
export default function TileMap({ tiles, className = "" }: { tiles: Tile[]; className?: string }) {
  const router = useRouter();
  const [zoom, setZoom] = useState<string | null>(null);
  const [wash, setWash] = useState<{ x: number; y: number; fill: string } | null>(null);
  const washRef = useRef<HTMLDivElement>(null);
  const byState = new Map(tiles.map((t) => [t.state, t]));

  useEffect(() => {
    if (!wash || !washRef.current) return;
    washRef.current.animate(
      [{ clipPath: `circle(0px at ${wash.x}px ${wash.y}px)` }, { clipPath: `circle(150vmax at ${wash.x}px ${wash.y}px)` }],
      { duration: ZOOM_MS - WASH_DELAY_MS + 60, delay: WASH_DELAY_MS, easing: "cubic-bezier(0.5, 0, 0.3, 1)", fill: "both" },
    );
  }, [wash]);

  const open = (e: MouseEvent, t: Tile) => {
    if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey || e.button !== 0) return;
    e.preventDefault();
    const href = t.href!;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return router.push(href);
    router.prefetch(href);
    try {
      sessionStorage.setItem(ARRIVE_KEY, JSON.stringify({ state: t.state, fill: t.fill, t: Date.now() }));
    } catch {}
    setZoom(t.state);
    setWash({ x: e.clientX, y: e.clientY, fill: t.fill });
    setTimeout(() => router.push(href), ZOOM_MS + 60);
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
          transform: zoom ? `scale(${(W / S) * 1.12})` : "none",
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
            <Link
              key={st}
              href={t.href}
              prefetch={false}
              onClick={(e) => open(e, t)}
              onMouseEnter={() => router.prefetch(t.href!)}
              onFocus={() => router.prefetch(t.href!)}
              aria-label={t.title}
            >
              {body}
            </Link>
          ) : (
            <g key={st}>{body}</g>
          );
        })}
      </svg>
      {wash && <div ref={washRef} className="pointer-events-none fixed inset-0 z-50" style={{ background: wash.fill, clipPath: "circle(0px at 0 0)" }} aria-hidden="true" />}
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
