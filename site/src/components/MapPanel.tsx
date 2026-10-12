"use client";

import { useState, type ReactNode } from "react";
import TileMap, { Legend, type Tile } from "./TileMap";

type View = { key: string; label: string; tiles: Tile[]; note: string };

// With a header (the forecast home's title, Matteo 12 Oct), the view switch sits at the right end of the title's line
// and the map is centred under it.
export default function MapPanel({ views, legend, header, mapClass = "" }: { views: View[]; legend: { fill: string; label: string; border?: boolean }[]; header?: ReactNode; mapClass?: string }) {
  const [k, setK] = useState(views[0].key);
  const view = views.find((v) => v.key === k) ?? views[0];
  return (
    <div>
      <div className={header ? "flex flex-col gap-4 border-b border-rule pb-4 lg:flex-row lg:items-center lg:justify-between lg:gap-10" : ""}>
        {header}
        <div role="tablist" aria-label="Map view" className={`flex shrink-0 text-[0.9rem] font-semibold ${header ? "gap-1 self-start rounded-full bg-paper-2 p-[3px] lg:self-center" : "gap-6 border-b border-rule"}`}>
          {views.map((v) => (
            <button key={v.key} role="tab" aria-selected={v.key === k} onClick={() => setK(v.key)}
              className={header
                ? `rounded-full px-3 py-1 text-[0.8rem] transition-all ${v.key === k ? "bg-white text-ink shadow-[0_1px_3px_rgba(17,17,16,0.14)]" : "text-muted hover:text-ink"}`
                : `-mb-px border-b-[3px] pb-2 ${v.key === k ? "border-ink text-ink" : "border-transparent text-muted hover:text-ink"}`}>
              {v.label}
            </button>
          ))}
        </div>
      </div>
      <div className={`${header ? "mt-4" : "mt-6"} ${mapClass}`}>
        <TileMap tiles={view.tiles} />
      </div>
      <div className={`mt-4 flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between ${mapClass}`}>
        <Legend items={legend} />
        <p className="note sm:max-w-xs sm:text-right">{view.note}</p>
      </div>
    </div>
  );
}
