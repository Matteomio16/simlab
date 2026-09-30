import type { Metadata } from "next";
import { existsSync, readdirSync } from "node:fs";
import path from "node:path";
import { notFound } from "next/navigation";
import Reveal from "@/components/Reveal";
import { HAS_FORECAST } from "@/lib/data";
import { longDate } from "@/lib/format";
import { ROOT } from "@/lib/root";

export const metadata: Metadata = {
  title: "Archive",
  description: "Every daily NotAPoll.org forecast, as published, to download.",
};

// scripts/publish-day.mjs writes each day's forecast.json to public/data/YYYY-MM-DD/.
export default function Archive() {
  if (!HAS_FORECAST) notFound();
  const dir = path.join(ROOT, "public", "data");
  const days = existsSync(dir) ? readdirSync(dir).filter((d) => /^\d{4}-\d{2}-\d{2}$/.test(d)).sort().reverse() : [];
  return (
    <div className="mx-auto max-w-[1200px] px-4 pt-10 sm:px-6 sm:pt-12">
      <p className="label">Archive</p>
      <h1 className="rise mt-3 max-w-3xl text-[2.3rem] font-extrabold leading-[1.08] tracking-[-0.02em] sm:text-[2.9rem]">
        Every daily forecast, as published
      </h1>
      <p className="mt-4 max-w-3xl text-[1.2rem] leading-relaxed text-ink-2">
        Each day&rsquo;s forecast file stays here unchanged, so anyone can check what the simulation said and when. The same
        files are kept in the project&rsquo;s public code repository.
      </p>
      <Reveal as="section" className="mt-12 section-rule">
        <p className="label">Daily files</p>
        {days.length === 0 ? (
          <p className="mt-3 text-ink-2">The first daily file is published on Monday, October 12.</p>
        ) : (
          <ul className="mt-3">
            {days.map((d) => (
              <li key={d} className="flex items-baseline justify-between border-b border-rule py-3">
                <span className="font-semibold">{longDate(d)}</span>
                <a href={`/data/${d}/forecast.json`} className="link text-sm font-semibold" download>
                  forecast.json
                </a>
              </li>
            ))}
          </ul>
        )}
        <p className="note mt-3">Chances are shares of 40,000 simulated elections. The file format is described in the code repository.</p>
      </Reveal>
    </div>
  );
}
