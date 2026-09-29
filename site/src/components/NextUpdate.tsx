"use client";

import { useEffect, useState } from "react";

// The daily job runs at 09:47 UTC (CLAUDE.md §5); this counts down to the next run in the reader's browser.
export default function NextUpdate() {
  const [text, setText] = useState("");
  useEffect(() => {
    const tick = () => {
      const now = new Date();
      const next = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate(), 9, 47));
      if (next <= now) next.setUTCDate(next.getUTCDate() + 1);
      const m = Math.floor((next.getTime() - now.getTime()) / 60000);
      setText(`Next update in ${Math.floor(m / 60)}h ${String(m % 60).padStart(2, "0")}m`);
    };
    tick();
    const id = setInterval(tick, 30000);
    return () => clearInterval(id);
  }, []);
  return (
    <span className="flex items-center gap-2">
      <span className="live-dot" aria-hidden="true" />
      {text || "Updated daily"}
    </span>
  );
}
