"use client";

import { useEffect, useRef, type ReactNode } from "react";

// Eases its children in when they scroll into view. Content is visible from the first paint; only blocks that start
// below the screen are held back, and only once the script runs, so nothing waits for JavaScript to appear.
export default function Reveal({ children, className = "", as: Tag = "div" }: { children: ReactNode; className?: string; as?: "div" | "section" }) {
  const ref = useRef<HTMLElement>(null);
  useEffect(() => {
    const el = ref.current;
    if (!el || window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    if (el.getBoundingClientRect().top < window.innerHeight) return;
    el.classList.add("pending");
    const io = new IntersectionObserver(
      (entries) => entries.forEach((e) => e.isIntersecting && (e.target.classList.add("in"), io.unobserve(e.target))),
      // A huge top margin counts anything already scrolled past as seen, so a fast scroll or a jump link never skips it.
      { rootMargin: "100000px 0px -8% 0px" },
    );
    io.observe(el);
    return () => io.disconnect();
  }, []);
  return (
    <Tag ref={ref as never} className={`reveal ${className}`}>
      {children}
    </Tag>
  );
}
