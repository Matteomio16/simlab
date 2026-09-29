"use client";

import { useEffect, useMemo, useState } from "react";
import type { Party } from "@/lib/types";

type Race = { id: string; title: string; left: Party; leftName: string; rightName: string; p50: number };

const NOT_UP = { R: 31, D: 32, I: 2 };

// A what-if on our own simulated elections: every race moves by the same national swing, and the stored draws are
// recounted in the browser. King and Sanders (not up in 2026) count with the Democrats.
export default function Simulator({ races }: { races: Race[] }) {
  const [draws, setDraws] = useState<Record<string, number[]> | null>(null);
  const [swing, setSwing] = useState(0);

  useEffect(() => {
    fetch("/data/draws.json")
      .then((r) => r.json())
      .then((d) => setDraws(d.races))
      .catch(() => setDraws(null));
  }, []);

  const result = useMemo(() => {
    if (!draws) return null;
    const n = draws[races[0].id]?.length ?? 0;
    let r50 = 0, d51 = 0, ind = 0;
    const rSeats: number[] = [];
    for (let k = 0; k < n; k++) {
      let R = NOT_UP.R, D = NOT_UP.D, I = 0;
      for (const race of races) {
        const m = draws[race.id][k] + swing;
        if (m > 0) race.left === "I" ? I++ : D++;
        else R++;
      }
      const dCaucus = D + NOT_UP.I;
      if (R >= 50) r50++;
      if (dCaucus >= 51) d51++;
      if (I > 0 && R < 50 && dCaucus < 51) ind++;
      rSeats.push(R);
    }
    rSeats.sort((a, b) => a - b);
    return {
      r50: Math.round((r50 / n) * 100),
      d51: Math.round((d51 / n) * 100),
      ind: Math.round((ind / n) * 100),
      median: rSeats[Math.floor(n / 2)],
      lo: rSeats[Math.floor(n * 0.1)],
      hi: rSeats[Math.floor(n * 0.9)],
    };
  }, [draws, races, swing]);

  const flips = races
    .filter((r) => Math.sign(r.p50) !== Math.sign(r.p50 + swing) && swing !== 0)
    .sort((a, b) => Math.abs(a.p50) - Math.abs(b.p50));
  const label = (s: number) => (s === 0 ? "No change" : `${s > 0 ? "D" : "R"}+${Math.abs(s).toFixed(1)}`);

  return (
    <div className="grid gap-10 lg:grid-cols-[1fr_1fr]">
      <div>
        <label htmlFor="swing" className="label">National swing</label>
        <div className="mt-2 flex items-baseline justify-between">
          <span className="text-3xl font-bold" style={{ color: swing > 0 ? "var(--dem)" : swing < 0 ? "var(--rep)" : "var(--ink)" }}>
            {label(swing)}
          </span>
          {swing !== 0 && (
            <button onClick={() => setSwing(0)} className="text-sm font-semibold text-ink-2 underline underline-offset-4 hover:text-ink">
              Reset
            </button>
          )}
        </div>
        <input
          id="swing"
          type="range"
          min={-8}
          max={8}
          step={0.5}
          value={swing}
          onChange={(e) => setSwing(Number(e.target.value))}
          className="mt-4 w-full accent-[var(--sim)]"
          aria-valuetext={label(swing)}
        />
        <div className="mt-1 flex justify-between text-[0.75rem] font-semibold text-muted">
          <span className="text-rep">R+8</span>
          <span>No change</span>
          <span className="text-dem">D+8</span>
        </div>
        <p className="note mt-4 max-w-md">
          Moves every race&rsquo;s margin by the same amount and recounts our 1,000 stored simulated elections. A
          what-if for exploring, not a forecast.
        </p>
      </div>

      <div className="border-t border-rule pt-4 lg:border-l lg:border-t-0 lg:pl-10 lg:pt-0">
        {!result ? (
          <p className="text-ink-2">Loading the simulated elections…</p>
        ) : (
          <>
            <div className="grid grid-cols-3 gap-4">
              <div>
                <p className="label-muted">Republicans hold</p>
                <p className="mt-1 whitespace-nowrap text-3xl font-bold text-rep sm:text-4xl">{result.r50}<span className="ml-1 text-sm font-semibold text-muted">in 100</span></p>
              </div>
              <div>
                <p className="label-muted">Democrats reach 51</p>
                <p className="mt-1 whitespace-nowrap text-3xl font-bold text-dem sm:text-4xl">{result.d51}<span className="ml-1 text-sm font-semibold text-muted">in 100</span></p>
              </div>
              <div>
                <p className="label-muted">Independents decide</p>
                <p className="mt-1 whitespace-nowrap text-3xl font-bold text-ind sm:text-4xl">{result.ind}<span className="ml-1 text-sm font-semibold text-muted">in 100</span></p>
              </div>
            </div>
            <p className="mt-4 text-[0.95rem] text-ink-2">
              Republican seats: <strong className="text-ink">{result.median}</strong> in the middle simulation, {result.lo}–{result.hi} in 8 of 10.
            </p>
            <div className="mt-5 border-t border-rule pt-3">
              <p className="label-muted">Races that change leader at this swing</p>
              {flips.length === 0 ? (
                <p className="mt-2 text-sm text-ink-2">None.</p>
              ) : (
                <ul className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-sm">
                  {flips.map((r) => {
                    const leftAhead = r.p50 + swing > 0;
                    return (
                      <li key={r.id}>
                        <span className="font-semibold">{r.title}</span>{" "}
                        <span style={{ color: leftAhead ? (r.left === "I" ? "var(--ind)" : "var(--dem)") : "var(--rep)" }}>
                          to {leftAhead ? r.leftName : r.rightName}
                        </span>
                      </li>
                    );
                  })}
                </ul>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
