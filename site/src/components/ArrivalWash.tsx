"use client";

import { useEffect, useState } from "react";
import { ARRIVE_KEY } from "./TileMap";

// The other half of the map's dive: arriving from a map click, the page opens under the state's colour, which then
// lifts to show the race. Nothing happens on a direct visit.
function arrival(state: string) {
  try {
    const a = JSON.parse(sessionStorage.getItem(ARRIVE_KEY) ?? "null");
    sessionStorage.removeItem(ARRIVE_KEY);
    return a && a.state === state && Date.now() - a.t < 4000 ? (a.fill as string) : null;
  } catch {
    return null;
  }
}

export default function ArrivalWash({ state }: { state: string }) {
  const [fill, setFill] = useState(() => arrival(state));
  // Never leave the colour over the page, even if the animation doesn't run.
  useEffect(() => {
    if (!fill) return;
    const id = setTimeout(() => setFill(null), 1200);
    return () => clearTimeout(id);
  }, [fill]);
  if (!fill) return null;
  return (
    <div
      className="wash-out pointer-events-none fixed inset-0 z-50"
      style={{ background: fill }}
      onAnimationEnd={() => setFill(null)}
      aria-hidden="true"
    />
  );
}
