"use client";

import { useEffect, useRef, useState } from "react";

// Counts from 0 to the value once it is on screen; the final number is in the HTML for readers without JavaScript.
export default function CountUp({ value, ms = 600 }: { value: number; ms?: number }) {
  const [n, setN] = useState(value);
  const ref = useRef<HTMLSpanElement>(null);
  useEffect(() => {
    const el = ref.current;
    if (!el || window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    setN(0);
    let raf = 0;
    const io = new IntersectionObserver(([e]) => {
      if (!e.isIntersecting) return;
      io.disconnect();
      const t0 = performance.now();
      const tick = (t: number) => {
        const k = Math.max(0, Math.min(1, (t - t0) / ms));
        setN(Math.round(value * (1 - Math.pow(1 - k, 3))));
        if (k < 1) raf = requestAnimationFrame(tick);
      };
      raf = requestAnimationFrame(tick);
    });
    io.observe(el);
    return () => (io.disconnect(), cancelAnimationFrame(raf));
  }, [value, ms]);
  return <span ref={ref}>{n}</span>;
}
