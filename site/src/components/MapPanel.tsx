"use client";

import { useState } from "react";
import TileMap, { Legend, type Tile } from "./TileMap";

type View = { key: string; label: string; tiles: Tile[]; note: string };

export default function MapPanel({ views, legend }: { views: View[]; legend: { fill: string; label: string; border?: boolean }[] }) {
  const [k, setK] = useState(views[0].key);
  const view = views.find((v) => v.key === k) ?? views[0];
  return (
    <div>
      <div role="tablist" aria-label="Map view" className="flex gap-6 border-b border-rule text-[0.9rem] font-semibold">
        {views.map((v) => (
          <button key={v.key} role="tab" aria-selected={v.key === k} onClick={() => setK(v.key)}
            className={`-mb-px border-b-[3px] pb-2 ${v.key === k ? "border-ink text-ink" : "border-transparent text-muted hover:text-ink"}`}>
            {v.label}
          </button>
        ))}
      </div>
      <div className="mt-6">
        <TileMap tiles={view.tiles} />
      </div>
      <div className="mt-4 flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
        <Legend items={legend} />
        <p className="note sm:max-w-xs sm:text-right">{view.note}</p>
      </div>
    </div>
  );
}
