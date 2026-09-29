"use client";

import { useEffect, useRef } from "react";

type Dot = { bx: number; by: number; x: number; y: number; vx: number; vy: number; r: number; c: number; phase: number; speed: number };

// Synthetic voters: a field of dots that drift, part from the cursor, and ease home. Canvas 2D, as SwarmField on
// scaliastudio.dev. Colours come from the CSS tokens, so the field follows light and dark mode. Colours carry no data.
export default function SwarmField({ spacing = 22, className = "" }: { spacing?: number; className?: string }) {
  const ref = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = ref.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const dark = window.matchMedia("(prefers-color-scheme: dark)");
    let palette: string[] = [];
    const readPalette = () => {
      const css = getComputedStyle(document.documentElement);
      palette = ["--ink", "--dem", "--rep", "--sim"].map((v) => css.getPropertyValue(v).trim() || "#1c2a4a");
    };
    readPalette();

    let dots: Dot[] = [];
    let w = 0, h = 0, raf = 0, t = 0;
    const mouse = { x: -9999, y: -9999 };

    const build = () => {
      const rect = canvas.getBoundingClientRect();
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      w = rect.width;
      h = rect.height;
      canvas.width = Math.round(w * dpr);
      canvas.height = Math.round(h * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      dots = [];
      const cols = Math.ceil(w / spacing) + 1;
      const rows = Math.ceil(h / spacing) + 1;
      for (let i = 0; i < rows; i++) {
        for (let j = 0; j < cols; j++) {
          const bx = j * spacing + (i % 2 ? spacing / 2 : 0) + (Math.random() - 0.5) * spacing * 0.5;
          const by = i * spacing + (Math.random() - 0.5) * spacing * 0.5;
          const u = Math.random();
          dots.push({
            bx, by, x: bx, y: by, vx: 0, vy: 0,
            r: 1.1 + Math.random() * 1.3,
            c: u < 0.8 ? 0 : u < 0.89 ? 1 : u < 0.98 ? 2 : 3,
            phase: Math.random() * Math.PI * 2,
            speed: 0.3 + Math.random() * 0.7,
          });
        }
      }
    };

    const draw = () => {
      ctx.clearRect(0, 0, w, h);
      for (const d of dots) {
        ctx.globalAlpha = d.c === 0 ? 0.16 : d.c === 3 ? 0.85 : 0.55;
        ctx.fillStyle = palette[d.c];
        ctx.beginPath();
        ctx.arc(d.x, d.y, d.c === 3 ? d.r + 0.8 : d.r, 0, Math.PI * 2);
        ctx.fill();
      }
      ctx.globalAlpha = 1;
    };

    const step = () => {
      t += 0.008;
      for (const d of dots) {
        const tx = d.bx + Math.sin(t * d.speed + d.phase) * 3.5;
        const ty = d.by + Math.cos(t * d.speed * 0.8 + d.phase) * 3.5;
        const dx = d.x - mouse.x, dy = d.y - mouse.y;
        const dist2 = dx * dx + dy * dy;
        if (dist2 < 110 * 110) {
          const f = (1 - Math.sqrt(dist2) / 110) * 1.6;
          const a = Math.atan2(dy, dx);
          d.vx += Math.cos(a) * f;
          d.vy += Math.sin(a) * f;
        }
        d.vx += (tx - d.x) * 0.02;
        d.vy += (ty - d.y) * 0.02;
        d.vx *= 0.86;
        d.vy *= 0.86;
        d.x += d.vx;
        d.y += d.vy;
      }
      draw();
      raf = requestAnimationFrame(step);
    };

    const onMove = (e: PointerEvent) => {
      const rect = canvas.getBoundingClientRect();
      mouse.x = e.clientX - rect.left;
      mouse.y = e.clientY - rect.top;
    };
    const onLeave = () => {
      mouse.x = mouse.y = -9999;
    };
    const onResize = () => {
      build();
      if (reduced) draw();
    };
    const onScheme = () => {
      readPalette();
      draw();
    };

    build();
    if (reduced) draw();
    else {
      raf = requestAnimationFrame(step);
      window.addEventListener("pointermove", onMove, { passive: true });
      document.addEventListener("pointerleave", onLeave);
    }
    window.addEventListener("resize", onResize);
    dark.addEventListener("change", onScheme);
    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("pointermove", onMove);
      document.removeEventListener("pointerleave", onLeave);
      window.removeEventListener("resize", onResize);
      dark.removeEventListener("change", onScheme);
    };
  }, [spacing]);

  return <canvas ref={ref} aria-hidden="true" className={`pointer-events-none block h-full w-full ${className}`} />;
}
