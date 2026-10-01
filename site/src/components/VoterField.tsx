"use client";

import { useEffect, useRef, useState } from "react";

// An illustration of the method, not data: a field of squares standing for voters. Every few seconds a news story ripples out
// from a point. Persuadable voters (a minority) shift colour a little, mobilisable voters light up, firm partisans
// barely move; then the effect fades, as stories do. Canvas 2D; paused off screen and in background tabs; a still
// frame for reduced motion.
type Voter = { x: number; y: number; lean: number; pers: boolean; mob: boolean; shift: number; glow: number };

const STORIES = [
  "A debate night",
  "An endorsement",
  "A new ad on health costs",
  "Grocery prices rise again",
  "A candidate's scandal",
  "A plan on housing costs",
];

const DEM = [42, 120, 214];
const REP = [227, 73, 72];
const SIM = [122, 79, 192];

function mix(a: number[], b: number[], t: number) {
  return a.map((v, i) => Math.round(v + (b[i] - v) * t));
}

export default function VoterField({ className = "" }: { className?: string }) {
  const ref = useRef<HTMLCanvasElement>(null);
  const [story, setStory] = useState<string | null>(null);

  useEffect(() => {
    const canvas = ref.current;
    const ctx = canvas?.getContext("2d");
    if (!canvas || !ctx) return;
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    let voters: Voter[] = [];
    let w = 0, h = 0, cell = 0, raf = 0, visible = true, last = 0, nextPulse = 800;
    let pulse: { x: number; y: number; r: number; side: number; born: number } | null = null;
    let seed = 7;
    const rnd = () => ((seed = (seed * 16807) % 2147483647) / 2147483647);

    const build = () => {
      const rect = canvas.getBoundingClientRect();
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      w = rect.width;
      h = rect.height;
      canvas.width = Math.round(w * dpr);
      canvas.height = Math.round(h * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      cell = w < 520 ? 11 : 13;
      voters = [];
      seed = 7;
      for (let y = cell / 2; y < h; y += cell) {
        for (let x = cell / 2; x < w; x += cell) {
          const u = rnd();
          // Mostly firm partisans on either side, a band of persuadable voters in the middle.
          const lean = u < 0.44 ? -1 : u > 0.56 ? 1 : (u - 0.5) * 8;
          voters.push({ x, y, lean, pers: Math.abs(lean) < 1 || rnd() < 0.06, mob: rnd() < 0.18, shift: 0, glow: 0 });
        }
      }
    };

    const draw = () => {
      ctx.clearRect(0, 0, w, h);
      const s = cell * 0.62;
      for (const v of voters) {
        const l = Math.max(-1, Math.min(1, v.lean + v.shift));
        const base = l < -0.25 ? mix(SIM, DEM, Math.min(1, (-l - 0.25) / 0.5)) : l > 0.25 ? mix(SIM, REP, Math.min(1, (l - 0.25) / 0.5)) : SIM;
        const a = 0.42 + 0.55 * v.glow + (v.pers ? 0.15 : 0);
        ctx.fillStyle = `rgba(${base[0]},${base[1]},${base[2]},${Math.min(1, a)})`;
        const z = s * (1 + 0.35 * v.glow);
        ctx.fillRect(v.x - z / 2, v.y - z / 2, z, z);
      }
      if (pulse) {
        const age = (performance.now() - pulse.born) / 1000;
        ctx.strokeStyle = `rgba(17,17,16,${Math.max(0, 0.35 - age * 0.12)})`;
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        ctx.arc(pulse.x, pulse.y, pulse.r, 0, Math.PI * 2);
        ctx.stroke();
      }
    };

    const step = (t: number) => {
      const dt = Math.min(64, t - (last || t));
      last = t;
      nextPulse -= dt;
      if (nextPulse <= 0) {
        pulse = { x: w * (0.15 + 0.7 * Math.random()), y: h * (0.2 + 0.6 * Math.random()), r: 0, side: Math.random() < 0.5 ? -1 : 1, born: t };
        setStory(STORIES[Math.floor(Math.random() * STORIES.length)]);
        nextPulse = 3600;
      }
      if (pulse) {
        const prev = pulse.r;
        pulse.r += dt * 0.32;
        for (const v of voters) {
          const d = Math.hypot(v.x - pulse.x, v.y - pulse.y);
          if (d >= prev && d < pulse.r) {
            const reach = Math.max(0, 1 - d / (Math.max(w, h) * 0.7));
            if (v.pers) v.shift += pulse.side * 0.35 * reach * (0.5 + Math.random());
            else v.shift += pulse.side * 0.03 * reach;
            if (v.mob) v.glow = Math.min(1, v.glow + reach);
          }
        }
        if (pulse.r > Math.max(w, h) * 1.2) pulse = null;
      }
      // Stories fade: every effect decays back towards where the voter started.
      const k = Math.pow(0.5, dt / 2200);
      for (const v of voters) {
        v.shift *= k;
        v.glow *= k;
      }
      draw();
      raf = visible ? requestAnimationFrame(step) : 0;
    };

    build();
    draw();
    if (reduced) return;
    const io = new IntersectionObserver(([e]) => {
      visible = e.isIntersecting && !document.hidden;
      if (visible && !raf) raf = requestAnimationFrame(step);
    });
    io.observe(canvas);
    const onVis = () => {
      visible = !document.hidden;
      if (visible && !raf) raf = requestAnimationFrame(step);
    };
    const onResize = () => {
      build();
      draw();
    };
    document.addEventListener("visibilitychange", onVis);
    window.addEventListener("resize", onResize);
    return () => {
      cancelAnimationFrame(raf);
      io.disconnect();
      document.removeEventListener("visibilitychange", onVis);
      window.removeEventListener("resize", onResize);
    };
  }, []);

  return (
    <figure className={`flex flex-col ${className}`}>
      <div className="relative min-h-[280px] w-full flex-1">
        <canvas ref={ref} className="absolute inset-0 h-full w-full" aria-hidden="true" />
        <div className="pointer-events-none absolute left-3 top-3 flex items-center gap-2 bg-paper/90 px-2 py-1 text-[0.72rem] font-semibold">
          <span className="live-dot" aria-hidden="true" />
          <span>{story ? `News: ${story}` : "Illustration"}</span>
        </div>
      </div>
      <figcaption className="note mt-2">
        An illustration, not a forecast. The real personas: 28 voter groups in each state. When a story spreads,
        persuadable voters shift and voters unsure whether to vote light up; firm partisans barely move. Then the
        effect fades.
      </figcaption>
    </figure>
  );
}
