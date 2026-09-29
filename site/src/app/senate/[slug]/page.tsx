import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { SimLabel } from "@/components/Brand";
import { DotPlot, HistoryLine, MarginRanges, ProbBar, Responsive } from "@/components/charts";
import { HAS_FORECAST, IS_SAMPLE, load, raceCode, raceTitle, senateRacesSafe } from "@/lib/data";
import { in100, leader, longDate, margin, partyName, partyVar, rating, surname } from "@/lib/format";

export const dynamicParams = false;

// Prelaunch builds no race pages: one placeholder param keeps the static export happy and renders a 404.
export function generateStaticParams() {
  const races = senateRacesSafe();
  return races.length ? races.map((r) => ({ slug: r.slug })) : [{ slug: "soon" }];
}

function find(slug: string) {
  if (!HAS_FORECAST) return null;
  return senateRacesSafe().find((r) => r.slug === slug) ?? null;
}

export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }): Promise<Metadata> {
  const race = find((await params).slug);
  if (!race) return {};
  const lead = leader(race.f.p_dem_win, race.meta);
  return {
    title: `${raceTitle(race.meta)} Senate`,
    description: `${lead.name} wins ${in100(lead.p)} in 100 simulated elections. Social simulation, not a poll.`,
  };
}

export default async function RacePage({ params }: { params: Promise<{ slug: string }> }) {
  const race = find((await params).slug);
  if (!race) notFound();
  const { forecast, draws, history } = load();
  const { id, meta, f } = race;
  const L = meta.left_party;
  const lead = leader(f.p_dem_win, meta);
  const today = f.today ? leader(f.today.p_dem_win, meta) : null;
  const r = rating(f.p_dem_win);
  const sample = (draws.races[id] ?? []).filter((_, i) => i % 10 === 0);
  const hist = (history.races[id] ?? []).map((h) => ({ date: h.date, p: h.p_dem_win }));
  const leftShort = surname(meta.candidates.left);
  const rightShort = surname(meta.candidates.right);
  const b = f.benchmarks;

  return (
    <article className="mx-auto max-w-6xl px-4 pt-10 sm:px-6 sm:pt-14">
      <nav className="kicker"><Link href="/" className="hover:text-ink">Senate</Link> / {raceCode(id, meta)}</nav>

      <header className="mt-5 grid gap-10 lg:grid-cols-[1.35fr_1fr] lg:items-end">
        <div>
          <p className="text-sm text-ink-2">
            {raceTitle(meta)} Senate{meta.special ? " special election" : ""}
            {meta.rcv ? " · ranked-choice voting" : ""} · incumbent party {meta.incumbent_party}
          </p>
          <h1 className="mt-3 font-serif text-[2.3rem] leading-[1.08] tracking-[-0.01em] text-ink sm:text-[3.2rem]">
            <span style={{ color: partyVar(lead.party) }}>{lead.name}</span> wins{" "}
            <span className="hl">{in100(lead.p)} of 100</span> simulated elections.
          </h1>
          <p className="mt-4 text-lg text-ink-2">
            {r === "Toss-up" ? "A toss-up. " : `${r} ${lead.party === "I" ? "independent" : lead.party === "D" ? "Democratic" : "Republican"}. `}
            Median margin {margin(f.margin.p50, L)}, with 8 in 10 simulated elections between{" "}
            {margin(f.margin.p10, L)} and {margin(f.margin.p90, L)}.
          </p>
        </div>
        <div className="rounded-md border border-hairline bg-raised p-5">
          <div className="flex items-baseline justify-between text-sm">
            <span style={{ color: partyVar(L) }}>{meta.candidates.left} ({L})</span>
            <span style={{ color: "var(--rep)" }}>{meta.candidates.right} (R)</span>
          </div>
          <div className="mt-1 flex items-baseline justify-between">
            <span className="text-3xl font-semibold tabular-nums" style={{ color: partyVar(L) }}>{in100(f.p_dem_win)}</span>
            <span className="kicker">in 100, 3 Nov</span>
            <span className="text-3xl font-semibold tabular-nums" style={{ color: "var(--rep)" }}>{100 - in100(f.p_dem_win)}</span>
          </div>
          <div className="mt-3"><ProbBar p={f.p_dem_win} left={L} height={10} /></div>
          {today && f.today && (
            <p className="mt-4 border-t border-hairline pt-3 text-sm text-ink-2">
              If the election were today: <span className="font-semibold text-ink">{surname(today.name)} {in100(today.p)} in 100</span>
            </p>
          )}
        </div>
      </header>

      <section className="mt-12 rounded-md border border-hairline bg-raised p-5">
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <h2 className="font-semibold text-ink">100 of the 40,000 simulated elections</h2>
          <span className="text-xs text-muted">Each dot is one simulated election, placed by its margin</span>
        </div>
        <div className="mt-4">
          <Responsive render={(w) => <DotPlot w={w} draws={sample} left={L} leftName={leftShort} rightName={rightShort} />} />
        </div>
      </section>

      <section className="mt-8 grid gap-8 lg:grid-cols-[1.35fr_1fr]">
        <div className="rounded-md border border-hairline bg-raised p-5">
          <h2 className="font-semibold text-ink">Margin, beside the poll average</h2>
          <p className="mt-1 text-xs text-muted">Bars run from the 10th to the 90th percentile; the dot is the median.</p>
          <div className="mt-4">
            <Responsive desktop={500} render={(w) => (
              <MarginRanges w={w} left={L} rows={[
                { label: "Simulation, 3 Nov", band: f.margin, color: "var(--sim)", strong: true },
                ...(f.today ? [{ label: "If the election were today", band: f.today.margin, color: "var(--sim)" }] : []),
                { label: "Statistics only", band: f.stats_only.margin, color: "var(--muted)" },
                { label: "Poll average", point: b.poll_avg, color: "var(--ink)" },
              ]} />
            )} />
          </div>
        </div>
        <div className="rounded-md border border-hairline bg-raised p-5">
          <h2 className="font-semibold text-ink">Beside the benchmarks</h2>
          <dl className="mt-3 divide-y divide-hairline text-sm">
            {[
              ["Simulation, 3 Nov", `${leftShort} ${in100(f.p_dem_win)} in 100`, true],
              ["Statistics only", `${leftShort} ${in100(f.stats_only.p_dem_win)} in 100`, false],
              ["Prediction market", b.market == null ? "–" : `${leftShort} ${Math.round(b.market * 100)}%`, false],
              ["Poll average", b.poll_avg == null ? "No recent polls" : margin(b.poll_avg, L), false],
              ["Cook Political Report", b.cook ?? "–", false],
            ].map(([k, v, strong]) => (
              <div key={k as string} className="flex items-center justify-between gap-3 py-2.5">
                <dt className="text-ink-2">{strong && <span className="mr-2 inline-block h-2 w-2 rounded-full bg-sim" />}{k}</dt>
                <dd className={`text-right tabular-nums ${strong ? "font-semibold text-ink" : "text-ink"}`}>{v}</dd>
              </div>
            ))}
          </dl>
        </div>
      </section>

      <section className="mt-8 grid gap-8 lg:grid-cols-2">
        <div className="rounded-md border border-hairline bg-raised p-5">
          <h2 className="font-semibold text-ink">What moved it</h2>
          {f.movers.length === 0 ? (
            <p className="mt-3 text-sm text-ink-2">
              No story moved this race today. {meta.tier === "simulate" ? "" : "It runs on statistics, with the news on watch."}
            </p>
          ) : (
            <ul className="mt-3 divide-y divide-hairline">
              {f.movers.map((m) => (
                <li key={m.event_id} className="flex gap-4 py-3">
                  <span className="w-16 shrink-0 font-mono text-sm tabular-nums" style={{ color: m.delta > 0 ? partyVar(L) : "var(--rep)" }}>
                    {m.delta > 0 ? L : "R"}+{Math.abs(m.delta).toFixed(1)}
                  </span>
                  <span className="text-sm leading-relaxed text-ink-2">{m.card}</span>
                </li>
              ))}
            </ul>
          )}
          <div className="mt-4 border-t border-hairline pt-3 text-sm text-ink-2">
            <p>
              All news so far moves the 3 Nov margin by{" "}
              <span className="font-semibold text-ink">{f.news.effect >= 0 ? L : "R"}+{Math.abs(f.news.effect).toFixed(1)}</span>{" "}
              ({Math.abs(f.news.switching).toFixed(1)} from switching, {Math.abs(f.news.turnout).toFixed(1)} from turnout).
            </p>
            <p className="mt-2">
              If news matters less: {leftShort} {in100(f.news.if_weaker.p_dem_win)} in 100. If it matters more:{" "}
              {in100(f.news.if_stronger.p_dem_win)} in 100.
            </p>
          </div>
        </div>
        <div className="rounded-md border border-hairline bg-raised p-5">
          <h2 className="font-semibold text-ink">Over time</h2>
          <p className="mt-1 text-xs text-muted">{leftShort}&rsquo;s chance in 100 on 3 November; the shaded band is the toss-up zone.</p>
          <div className="mt-3">
            {hist.length > 1 ? (
              <Responsive desktop={480} render={(w) => <HistoryLine w={w} points={hist} label={`${leftShort}'s chance`} />} />
            ) : (
              <p className="text-sm text-ink-2">The line starts after a few daily runs.</p>
            )}
          </div>
        </div>
      </section>

      <p className="mt-8 max-w-3xl text-sm text-ink-2">
        {meta.candidates.left} is the {partyName(L)}{L === "I" ? " (counted separately from both parties)" : ""}.{" "}
        {meta.status}. <Link href="/methods" className="text-sim underline underline-offset-4">How the simulation works</Link>.
      </p>
      <div className="mt-6">
        <SimLabel date={longDate(forecast.date)} sample={IS_SAMPLE} />
      </div>
    </article>
  );
}
