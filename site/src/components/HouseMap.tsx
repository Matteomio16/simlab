"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState, type MouseEvent } from "react";
import { TILES } from "@/lib/tiles";
import { ARRIVE_KEY } from "./TileMap";

const S = 46;
const GAP = 3;
const W = 12 * S + 11 * GAP;
const H = 8 * S + 7 * GAP;
const TOP = 13;
const ZOOM_MS = 520;

export type Seat = { id: string; slug: string; state: string; fill: string; title: string };

// The House on the same state grid as the Senate map: each state's square holds one small square per seat, coloured
// by its forecast. Selecting a seat dives into its state's square, its colour washes over the screen, and the seat's
// page opens under it, as on the Senate map (plain navigation for reduced motion and new-tab clicks).
export default function HouseMap({ seats, current, clickable = true }: { seats: Seat[]; current?: string; clickable?: boolean }) {
  const router = useRouter();
  const [zoom, setZoom] = useState<string | null>(null);
  const [wash, setWash] = useState<{ x: number; y: number; fill: string } | null>(null);
  const washRef = useRef<HTMLDivElement>(null);
  const here = current ? seats.find((s) => s.id === current)?.state : undefined;
  const byState = new Map<string, Seat[]>();
  for (const s of seats) byState.set(s.state, [...(byState.get(s.state) ?? []), s]);

  useEffect(() => {
    if (!wash || !washRef.current) return;
    washRef.current.animate(
      [{ clipPath: `circle(0px at ${wash.x}px ${wash.y}px)` }, { clipPath: `circle(150vmax at ${wash.x}px ${wash.y}px)` }],
      { duration: ZOOM_MS - 120, delay: 180, easing: "cubic-bezier(0.5, 0, 0.3, 1)", fill: "both" },
    );
  }, [wash]);

  const open = (e: MouseEvent, s: Seat) => {
    if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey || e.button !== 0) return;
    e.preventDefault();
    const href = `/house/${s.slug}`;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return router.push(href);
    router.prefetch(href);
    try {
      sessionStorage.setItem(ARRIVE_KEY, JSON.stringify({ state: s.id, fill: s.fill, t: Date.now() }));
    } catch {}
    setZoom(s.state);
    setWash({ x: e.clientX, y: e.clientY, fill: s.fill });
    setTimeout(() => router.push(href), ZOOM_MS + 60);
  };

  const z = zoom ? TILES[zoom] : null;
  const origin = z ? `${((z[0] * (S + GAP) + S / 2) / W) * 100}% ${((z[1] * (S + GAP) + S / 2) / H) * 100}%` : "50% 50%";

  return (
    <div className="overflow-hidden">
      <svg
        viewBox={`0 0 ${W} ${H}`}
        className="h-auto w-full"
        role="img"
        aria-label="Map of the 435 House seats, grouped by state"
        style={{ transformOrigin: origin, transform: zoom ? `scale(${(W / S) * 1.12})` : "none", transition: `transform ${ZOOM_MS}ms cubic-bezier(0.6, 0, 0.2, 1)` }}
      >
        {Object.entries(TILES).map(([st, [c, r]]) => {
          const x0 = c * (S + GAP);
          const y0 = r * (S + GAP);
          const ds = byState.get(st) ?? [];
          const cols = Math.max(1, Math.ceil(Math.sqrt(ds.length * 1.3)));
          const rows = Math.max(1, Math.ceil(ds.length / cols));
          const cell = Math.min(16, (S - 4) / cols, (S - TOP - 3) / rows);
          const gx = x0 + (S - cols * cell) / 2;
          const gy = y0 + TOP + (S - TOP - 2 - rows * cell) / 2;
          const faded = zoom && zoom !== st;
          return (
            <g key={st} style={{ opacity: faded ? 0.08 : 1, transition: `opacity ${ZOOM_MS * 0.6}ms` }}>
              <rect x={x0 + 0.5} y={y0 + 0.5} width={S - 1} height={S - 1} fill="var(--paper)" stroke={st === here ? "var(--ink)" : "var(--rule)"} strokeWidth={st === here ? 2 : 1} />
              <text x={x0 + 4} y={y0 + 10.5} fill="var(--ink-2)" style={{ fontSize: 9.5, fontWeight: 700, letterSpacing: "0.02em" }}>{st}</text>
              {ds.map((s, i) => {
                const x = gx + (i % cols) * cell + 0.4;
                const y = gy + Math.floor(i / cols) * cell + 0.4;
                const on = current === s.id;
                const square = (
                  <rect x={x} y={y} width={cell - 0.8} height={cell - 0.8} fill={s.fill} className={clickable ? "tile" : undefined} stroke={on ? "var(--ink)" : "none"} strokeWidth={on ? 1.6 : 0}>
                    <title>{s.title}</title>
                  </rect>
                );
                if (!clickable) return <g key={s.id}>{square}</g>;
                return (
                  <Link
                    key={s.id}
                    href={`/house/${s.slug}`}
                    prefetch={false}
                    onClick={(e) => open(e, s)}
                    onMouseEnter={() => router.prefetch(`/house/${s.slug}`)}
                    aria-label={s.title}
                  >
                    {square}
                  </Link>
                );
              })}
            </g>
          );
        })}
      </svg>
      {wash && <div ref={washRef} className="pointer-events-none fixed inset-0 z-50" style={{ background: wash.fill, clipPath: "circle(0px at 0 0)" }} aria-hidden="true" />}
    </div>
  );
}
