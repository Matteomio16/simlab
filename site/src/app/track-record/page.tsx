import type { Metadata } from "next";
import { existsSync, readFileSync } from "node:fs";
import path from "node:path";
import Reveal from "@/components/Reveal";
import Dateline from "@/components/Dateline";
import { DATA, HAS_FORECAST } from "@/lib/data";
import { ROOT } from "@/lib/root";

export const metadata: Metadata = {
  title: "Track record",
  description: "How the NotAPoll.org forecast scores against the poll average, the prediction markets, Cook and its own statistics-only twin, on fixed dates.",
};

// data/<live|sample>/scores.json, written by the Kev session's scoring job (roadmap A9, 29 Sep): every metric key is
// always present (null when it does not apply) and rows are append-only; a correction is a new row with a note.
// Before launch the page shows only the schedule and the rules.
type Score = {
  date: string;
  model: "simulation" | "stats_only" | "market" | "cook";
  target: "polls_next_week" | "result";
  office?: "senate" | "house" | "all";
  races: number;
  mae: number | null;
  direction: number | null;
  brier: number | null;
  log_loss: number | null;
  note?: string;
};

const MODEL = { simulation: "Social simulation", stats_only: "Statistics only", market: "Prediction markets", cook: "Cook Political Report" };
const TARGET = { polls_next_week: "Polls of the following week", result: "Election results" };
const OFFICE = { senate: "Senate", house: "House", all: "All races" };
const SCORING_DATES = ["2026-10-19", "2026-10-26", "2026-11-02"];
const BASELINES = [
  ["Social simulation", "The headline forecast: statistics plus voter personas, checked against the evidence every Monday."],
  ["Statistics only", "The same chain with the simulation switched off: the number the simulation has to beat."],
  ["Prediction markets", "Kalshi and Polymarket prices, averaged."],
  ["Cook Political Report", "Cook's ratings, turned into chances."],
];

const short = (d: string) => new Date(`${d}T12:00:00Z`).toLocaleDateString("en-US", { month: "short", day: "numeric", timeZone: "UTC" });
const num = (v: number | null, digits: number) => (v == null ? "–" : v.toFixed(digits));
const share = (v: number | null) => (v == null ? "–" : `${Math.round(v * 100)}%`);

export default function TrackRecord() {
  const f = path.join(ROOT, "data", DATA, "scores.json");
  const scores: Score[] = HAS_FORECAST && existsSync(f) ? JSON.parse(readFileSync(f, "utf8")).scores ?? [] : [];
  const offices = [...new Set(scores.map((s) => s.office ?? "all"))];
  const hasResults = scores.some((s) => s.target === "result");

  return (
    <div className="mx-auto max-w-[1200px] px-4 pt-10 sm:px-6 sm:pt-12">
      <Dateline left="Track record" />
      <h1 className="rise mt-6 max-w-3xl text-[2.3rem] font-extrabold leading-[1.08] tracking-[-0.02em] sm:text-[2.9rem]">
        Every forecast is scored, including the misses
      </h1>
      <p className="mt-4 max-w-3xl text-[1.2rem] leading-relaxed text-ink-2">
        Every week, the forecast is checked against what happened next, by the same rules as its benchmarks. After the
        election, it is scored against the results. Published scores are never rewritten; a correction is added as a new,
        dated line.
      </p>

      {offices.length === 0 ? (
        <Reveal as="section" className="mt-12 section-rule">
          <p className="label">Scores</p>
          <p className="mt-3 max-w-2xl text-ink-2">
            {`The first scores are published on Monday, October 19. Weekly scoring dates: ${SCORING_DATES.map(short).join(", ")}; then the results.`}
          </p>
        </Reveal>
      ) : (
        offices.map((o) => (
          <Reveal as="section" key={o} className="mt-12 section-rule">
            <p className="label">{offices.length > 1 ? OFFICE[o] : "Scores"}</p>
            <div className="mt-4 overflow-x-auto">
              <table className="w-full min-w-[640px] border-collapse text-[0.92rem]">
                <thead>
                  <tr className="border-y-2 border-rule-strong text-left text-[0.7rem] font-bold uppercase tracking-[0.06em]">
                    <th className="py-2 pr-3">Week to</th>
                    <th className="py-2 pr-3">Forecast</th>
                    <th className="py-2 pr-3">Scored against</th>
                    <th className="py-2 pr-3 text-right">Races</th>
                    <th className="py-2 pr-3 text-right">Error, pts</th>
                    <th className="py-2 pr-3 text-right">Moves called</th>
                    {hasResults && <th className="py-2 pr-3 text-right">Brier</th>}
                    {hasResults && <th className="py-2 text-right">Log loss</th>}
                  </tr>
                </thead>
                <tbody>
                  {scores
                    .filter((s) => (s.office ?? "all") === o)
                    .map((s, i) => (
                      <tr key={i} className={`border-b border-rule align-top ${s.model === "simulation" ? "font-semibold" : ""}`}>
                        <td className="py-2 pr-3">{short(s.date)}</td>
                        <td className="py-2 pr-3">
                          {MODEL[s.model] ?? s.model}
                          {s.note && <span className="block text-[0.78rem] font-normal text-muted">{s.note}</span>}
                        </td>
                        <td className="py-2 pr-3 font-normal text-ink-2">{TARGET[s.target] ?? s.target}</td>
                        <td className="py-2 pr-3 text-right">{s.races}</td>
                        <td className="py-2 pr-3 text-right">{num(s.mae, 1)}</td>
                        <td className="py-2 pr-3 text-right">{share(s.direction)}</td>
                        {hasResults && <td className="py-2 pr-3 text-right">{num(s.brier, 3)}</td>}
                        {hasResults && <td className="py-2 text-right">{num(s.log_loss, 3)}</td>}
                      </tr>
                    ))}
                </tbody>
              </table>
            </div>
          </Reveal>
        ))
      )}

      <Reveal as="section" className="mt-14 section-rule">
        <p className="label">What we compare</p>
        <table className="mt-4 w-full border-collapse text-[0.95rem]">
          <tbody>
            {BASELINES.map(([k, v]) => (
              <tr key={k} className="border-b border-rule align-top">
                <th className="w-56 py-3 pr-4 text-left font-bold">{k}</th>
                <td className="py-3 text-ink-2">{v}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Reveal>

      <Reveal as="section" className="mt-14 section-rule">
        <p className="label">How scoring works</p>
        <div className="prose-np mt-2 max-w-[680px]">
          <p>
            <strong>Before the election</strong> there are no results, so each week&rsquo;s forecast is checked against the
            polls published in the following week: the <strong>error</strong> is the average gap in margin points, and
            <strong> moves called</strong> is the share of races where the forecast moved the same way the polls later did.
          </p>
          <p>
            <strong>After the election</strong>, every forecast is scored against the results. The <strong>Brier score</strong>{" "}
            is the average squared gap between a forecast chance and what happened: 0 is perfect, and a coin flip on every race
            scores 0.25. <strong>Log loss</strong> punishes confident misses harder. Lower is better for both.
          </p>
        </div>
      </Reveal>
    </div>
  );
}
