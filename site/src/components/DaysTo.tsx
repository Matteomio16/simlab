"use client";

import { useEffect, useState } from "react";

// Counted in the reader's browser, so a static page stays right between builds.
export default function DaysTo({ target, initial }: { target: string; initial: number }) {
  const [days, setDays] = useState(initial);
  useEffect(() => {
    const now = new Date();
    const today = Date.UTC(now.getFullYear(), now.getMonth(), now.getDate());
    setDays(Math.max(0, Math.round((Date.parse(target) - today) / 86400000)));
  }, [target]);
  return <span className="tabular-nums">{days}</span>;
}
