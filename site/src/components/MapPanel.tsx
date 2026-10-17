"use client";

import { useState, type ReactNode } from "react";
import TileMap, { Legend, type Tile } from "./TileMap";

type View = { key: string; label: string; short?: string; tiles: Tile[]; note: string };

// With a header (the forecast home's title, Matteo 12 Oct), the view switch sits at the right end of the title's line
// and the map is centred under it.
export default function MapPanel({ views, legend, header, mapClass = "" }: { views: View[]; legend: { fill: string; label: string; border?: boolean }[]; header?: ReactNode; mapClass?: string }) {
  const [k, setK] = useState(views[0].key);
  const view = views.find((v) => v.key === k) ?? views[0];
  return (
    <div>
      <div className={header ? "flex flex-col gap-4 border-b border-rule pb-4 lg:flex-row lg:items-center lg:justify-between lg:gap-10" : "flex"}>
        {header}
        <div role="tablist" aria-label="Map view" className={`seg seg-flat shrink-0 text-[0.8rem] ${header ? "self-start lg:self-center" : ""}`}>
          {views.map((v) => (
            <button key={v.key} role="tab" aria-selected={v.key === k} onClick={() => setK(v.key)}>
              <span className="sm:hidden">{v.short ?? v.label}</span>
              <span className="hidden sm:inline">{v.label}</span>
            </button>
          ))}
        </div>
      </div>
      <div className={`${header ? "mt-4" : "mt-6"} ${mapClass}`}>
        <TileMap tiles={view.tiles} />
      </div>
      <div className={`mt-4 flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between ${mapClass} ${header ? "px-3 sm:px-0" : ""}`}>
        <Legend items={legend} />
        <p className="note sm:max-w-xs sm:text-right">{view.note}</p>
      </div>
    </div>
  );
}
