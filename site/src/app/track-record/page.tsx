import type { Metadata } from "next";
import { existsSync, readFileSync } from "node:fs";
import path from "node:path";
import { notFound } from "next/navigation";
import Reveal from "@/components/Reveal";
import { DATA, HAS_FORECAST } from "@/lib/data";
import { ROOT } from "@/lib/root";

export const metadata: Metadata = {
  title: "Track record",
  description: "How the NotAPoll.org forecast scores against the poll average, the prediction markets, Cook and its own statistics-only twin, on fixed dates.",
};

// Scores arrive from the scoring job as data/<live|sample>/scores.json (not yet in the file contract,
// docs/engine-design.md §7). Until then the page shows the schedule and the rules.
type Score = { date: string; model: string; brier: number; log_loss: number; races: number };
const SCORING_DATES = ["2026-10-19", "2026-10-26", "2026-11-02"];
const BASELINES = [
  ["Our social simulation", "The headline forecast: statistics plus synthetic voters, corrected by the weekly filter."],
  ["Statistics only", "The same chain with the simulation switched off: the number the simulation has to beat."],
  ["Poll average", "The polling average for each race, turned into a chance."],
  ["Prediction markets", "Kalshi and Polymarket prices, averaged."],
  ["Cook Political Report", "Cook's ratings, turned into chances."],
];

const short = (d: string) => new Date(`${d}T12:00:00Z`).toLocaleDateString("en-US", { month: "short", day: "numeric", timeZone: "UTC" });

export default function TrackRecord() {
  if (!HAS_FORECAST) notFound();
  const f = path.join(ROOT, "data", DATA, "scores.json");
  const scores: Score[] = existsSync(f) ? JSON.parse(readFileSync(f, "utf8")).scores ?? [] : [];
  return (
    <div className="mx-auto max-w-[1200px] px-4 pt-10 sm:px-6 sm:pt-12">
      <p className="label">Track record</p>
      <h1 className="rise mt-3 max-w-3xl text-[2.3rem] font-extrabold leading-[1.08] tracking-[-0.02em] sm:text-[2.9rem]">
        Every forecast is scored, including the misses
      </h1>
      <p className="mt-4 max-w-3xl font-serif text-[1.2rem] leading-relaxed text-ink-2">
        On fixed dates, every race&rsquo;s forecast is scored by the same rules as four benchmarks. Once results are in, the
        final scores use the real outcomes. Good weeks and bad weeks are both published here.
      </p>

      <Reveal as="section" className="mt-12 section-rule">
        <p className="label">Scores</p>
        {scores.length === 0 ? (
          <p className="mt-3 max-w-2xl text-ink-2">
            {`The first scores are published on Monday, October 19. Scoring dates: ${SCORING_DATES.map(short).join(", ")}, and the final score after the results are certified.`}
          </p>
        ) : (
          <table className="mt-4 w-full border-collapse text-[0.92rem]">
            <thead>
              <tr className="border-y-2 border-rule-strong text-left text-[0.7rem] font-bold uppercase tracking-[0.06em]">
                <th className="py-2 pr-3">Date</th>
                <th className="py-2 pr-3">Forecast</th>
                <th className="py-2 pr-3 text-right">Brier score</th>
                <th className="py-2 pr-3 text-right">Log loss</th>
                <th className="py-2 text-right">Races</th>
              </tr>
            </thead>
            <tbody>
              {scores.map((s) => (
                <tr key={`${s.date}-${s.model}`} className="border-b border-rule">
                  <td className="py-2 pr-3">{short(s.date)}</td>
                  <td className="py-2 pr-3 font-semibold">{s.model}</td>
                  <td className="py-2 pr-3 text-right">{s.brier.toFixed(3)}</td>
                  <td className="py-2 pr-3 text-right">{s.log_loss.toFixed(3)}</td>
                  <td className="py-2 text-right">{s.races}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Reveal>

      <Reveal as="section" className="mt-14 section-rule">
        <p className="label">What we compare</p>
        <table className="mt-4 w-full border-collapse text-[0.95rem]">
          <tbody>
            {BASELINES.map(([k, v]) => (
              <tr key={k} className="border-b border-rule align-top">
                <th className="w-56 py-3 pr-4 text-left font-bold">{k}</th>
                <td className="py-3 font-serif text-ink-2">{v}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Reveal>

      <Reveal as="section" className="mt-14 section-rule">
        <p className="label">How scoring works</p>
        <div className="prose-np mt-2 max-w-[680px]">
          <p>
            <strong>Brier score</strong> is the average squared gap between a forecast chance and what happened: 0 is perfect,
            and a coin flip on every race scores 0.25. <strong>Log loss</strong> punishes confident misses harder. Lower is
            better for both.
          </p>
          <p>
            Before results exist, each scoring date checks the forecasts against the evidence that arrived since the last
            date. The final score uses the certified result of every race.
          </p>
        </div>
      </Reveal>
    </div>
  );
}
