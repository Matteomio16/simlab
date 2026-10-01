import type { Metadata } from "next";
import Link from "next/link";
import { SHOW } from "@/lib/site";
import { notFound } from "next/navigation";
import { SimLabel } from "@/components/Brand";
import { DotPlot, HistoryLine, MarginRanges, ProbBar, Responsive } from "@/components/charts";
import { HAS_FORECAST, IS_SAMPLE, load, raceCode, raceTitle, senateRacesSafe } from "@/lib/data";
import { in100, leader, longDate, margin, partyName, partyVar, surname, tierColor } from "@/lib/format";
import { STATES } from "@/lib/states";
import TileMap from "@/components/TileMap";
import ArrivalWash from "@/components/ArrivalWash";
import Reveal from "@/components/Reveal";
import CountUp from "@/components/CountUp";
import RaceCards from "@/components/RaceCards";
import type { Row } from "@/components/RaceTable";

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
  const tier = tierColor(f.p_dem_win, L);
  const ratingWords = tier.name === "Toss-up" ? "a toss-up" : tier.name.replace(/ D$/, " Democratic").replace(/ R$/, " Republican").replace(/ I$/, " independent").replace(/^\w+/, (w) => w.toLowerCase());
  const sample = (draws.races[id] ?? []).filter((_, i) => i % 10 === 0);
  const hist = (history.races[id] ?? []).map((h) => ({ date: h.date, p: h.p_dem_win }));
  const leftShort = surname(meta.candidates.left);
  const rightShort = surname(meta.candidates.right);
  const b = f.benchmarks;
  const others: Row[] = senateRacesSafe()
    .filter((x) => x.id !== id)
    .sort((x, y) => Math.abs(x.f.p_dem_win - 0.5) - Math.abs(y.f.p_dem_win - 0.5))
    .slice(0, 4)
    .map((x) => {
      const t = tierColor(x.f.p_dem_win, x.meta.left_party);
      return {
        id: x.id, slug: x.slug, title: raceTitle(x.meta), state: x.meta.state, left: x.meta.candidates.left,
        right: x.meta.candidates.right, leftParty: x.meta.left_party, p: x.f.p_dem_win, today: null, pollAvg: null,
        market: null, cook: null, rating: t.name, tierFill: t.fill, tierInk: t.ink, leader: leader(x.f.p_dem_win, x.meta).party,
      };
    });
  const bench: [string, string, boolean][] = [
    ["Our simulation, Nov. 3", `${leftShort} ${in100(f.p_dem_win)} in 100`, true],
    ["Statistics only, no simulation", `${leftShort} ${in100(f.stats_only.p_dem_win)} in 100`, false],
    ["Prediction market", b.market == null ? "–" : `${leftShort} ${Math.round(b.market * 100)}%`, false],
    ["Poll average", b.poll_avg == null ? "No recent polls" : margin(b.poll_avg, L), false],
    ["Cook Political Report", b.cook?.replace("Tossup", "Toss-up").replace("Solid", "Safe") ?? "–", false],
  ];
  const eff = `${f.news.effect >= 0 ? L : "R"}+${Math.abs(f.news.effect).toFixed(1)}`;
  const newsLine = `All news so far moves the Nov. 3 margin by ${eff} (${Math.abs(f.news.switching).toFixed(1)} from switching, ${Math.abs(f.news.turnout).toFixed(1)} from turnout). If news matters less, ${leftShort} wins ${in100(f.news.if_weaker.p_dem_win)} in 100; if it matters more, ${in100(f.news.if_stronger.p_dem_win)}.`;

  return (
    <article className="mx-auto max-w-[1200px] px-4 pt-8 sm:px-6 sm:pt-10">
      <ArrivalWash state={meta.state} />
      <nav className="text-[0.85rem] font-semibold text-ink-2">
        <Link href="/" className="hover:underline">Senate forecast</Link> <span className="text-muted">/</span> {raceTitle(meta)}
      </nav>

      <header className="mt-6 grid gap-10 lg:grid-cols-[1fr_300px]">
        <div className="rise">
          <p className="label">
            {STATES[meta.state]} Senate{meta.special ? " · special election" : ""}{meta.rcv ? " · ranked-choice voting" : ""}
          </p>
          <h1 className="mt-3 text-[2.1rem] font-extrabold leading-[1.08] tracking-[-0.02em] sm:text-[2.8rem]">
            {`${surname(lead.name)} wins ${in100(lead.p)} of 100 simulated elections`}
          </h1>
          <p className="mt-4 max-w-3xl text-[1.2rem] leading-relaxed text-ink-2">
            {`The simulation rates ${STATES[meta.state]} ${ratingWords}. The middle simulated result is ${margin(f.margin.p50, L)}, and 8 in 10 fall between ${margin(f.margin.p10, L)} and ${margin(f.margin.p90, L)}.`}
          </p>
        </div>
        <div className="arrive hidden lg:block">
          <TileMap tiles={[{ state: meta.state, fill: tier.fill, ink: tier.ink, title: STATES[meta.state] }]} />
        </div>
      </header>

      <section className="rise mt-8 grid gap-10 border-t-[3px] border-rule-strong pt-6 lg:grid-cols-[1fr_1fr]">
        <div>
          <div className="flex items-end justify-between">
            <div>
              <p className="label-muted">{meta.candidates.left} ({L})</p>
              <p className="mt-1 text-[3rem] font-extrabold leading-none tracking-[-0.02em]" style={{ color: partyVar(L) }}><CountUp value={in100(f.p_dem_win)} /></p>
            </div>
            <p className="label-muted pb-2">Chance in 100, Nov. 3</p>
            <div className="text-right">
              <p className="label-muted">{meta.candidates.right} (R)</p>
              <p className="mt-1 text-[3rem] font-extrabold leading-none tracking-[-0.02em] text-rep"><CountUp value={100 - in100(f.p_dem_win)} /></p>
            </div>
          </div>
          <div className="mt-4"><ProbBar p={f.p_dem_win} left={L} height={12} /></div>
          {today && (
            <p className="mt-4 border-t border-rule pt-3 text-[0.95rem] text-ink-2">
              If the election were today: <strong className="text-ink">{`${surname(today.name)}, ${in100(today.p)} in 100`}</strong>
            </p>
          )}
        </div>
        <div className="border-t border-rule pt-6 lg:border-l lg:border-t-0 lg:pl-10 lg:pt-0">
          <p className="label">Beside the benchmarks</p>
          <table className="mt-3 w-full text-[0.92rem]">
            <tbody>
              {bench.map(([k, v, strong]) => (
                <tr key={k as string} className="border-b border-rule">
                  <th className="py-2 pr-3 text-left font-normal text-ink-2">{strong && <span className="mr-2 inline-block h-2.5 w-2.5 bg-sim align-middle" />}{k}</th>
                  <td className={`py-2 text-right ${strong ? "font-bold" : "font-semibold"}`}>{v}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <Reveal as="section" className="mt-14 section-rule">
        <p className="label">The spread</p>
        <h2 className="mt-2 text-2xl font-bold tracking-[-0.01em]">{`100 of the ${forecast.draws.toLocaleString("en-US")} simulated elections`}</h2>
        <p className="mt-2 text-ink-2">Each dot is one simulated election, placed by its margin.</p>
        <div className="mt-6">
          <Responsive desktop={1100} render={(w) => <DotPlot w={w} draws={sample} left={L} leftName={leftShort} rightName={rightShort} />} />
        </div>
      </Reveal>

      <Reveal as="section" className="mt-14 grid gap-12 lg:grid-cols-2">
        <div className="section-rule">
          <p className="label">Margin</p>
          <h2 className="mt-2 text-xl font-bold">Our range beside the poll average</h2>
          <p className="note mt-1">Bars run from the 10th to the 90th percentile; the dot is the middle result.</p>
          <div className="mt-4">
            <Responsive desktop={500} render={(w) => (
              <MarginRanges w={w} left={L} rows={[
                { label: "Simulation, Nov. 3", band: f.margin, color: "var(--sim)", strong: true },
                ...(f.today ? [{ label: "If the election were today", band: f.today.margin, color: "var(--sim)" }] : []),
                { label: "Statistics only", band: f.stats_only.margin, color: "var(--muted)" },
                { label: "Poll average", point: b.poll_avg, color: "var(--ink)" },
              ]} />
            )} />
          </div>
        </div>
        <div className="section-rule">
          <p className="label">Over time</p>
          <h2 className="mt-2 text-xl font-bold">{`${leftShort}'s chance in 100`}</h2>
          <p className="note mt-1">The shaded band is the toss-up zone, 35 to 65.</p>
          <div className="mt-4">
            {hist.length > 1 ? (
              <Responsive desktop={500} render={(w) => <HistoryLine w={w} points={hist} label={`${leftShort}'s chance`} />} />
            ) : (
              <p className="text-ink-2">The line starts after a few daily runs.</p>
            )}
          </div>
        </div>
      </Reveal>

      <Reveal as="section" className="mt-14 section-rule">
        <p className="label">What moved it</p>
        <h2 className="mt-2 text-xl font-bold">The news, as the voter personas reacted to it</h2>
        {f.movers.length === 0 ? (
          <p className="mt-3 text-ink-2">
            {`No story moved this race today.${meta.tier === "simulate" ? "" : " It runs on statistics, with the biggest stories on watch."}`}
          </p>
        ) : (
          <ul className="mt-3 max-w-3xl">
            {f.movers.map((m) => (
              <li key={m.event_id} className="flex gap-4 border-b border-rule py-3">
                <span className="w-16 shrink-0 text-right font-bold" style={{ color: m.delta > 0 ? partyVar(L) : "var(--rep)" }}>
                  {`${m.delta > 0 ? L : "R"}+${Math.abs(m.delta).toFixed(1)}`}
                </span>
                <span className="text-[1.05rem] leading-snug text-ink-2">{m.card}</span>
              </li>
            ))}
          </ul>
        )}
        <p className="mt-5 max-w-3xl bg-note px-4 py-3 text-[0.95rem] leading-relaxed text-ink">
          <strong className="mr-2 font-bold">What the news is worth.</strong>
          {newsLine}
        </p>
      </Reveal>

      <Reveal as="section" className="mt-14 section-rule">
        <p className="label">Other close races</p>
        <div className="mt-4">
          <RaceCards rows={others} />
        </div>
      </Reveal>

      <p className="mt-10 max-w-3xl text-[0.9rem] text-ink-2">
        {`${meta.candidates.left} is the ${partyName(L)}${L === "I" ? ", counted apart from both parties" : ""}. ${meta.status}. `}
        {SHOW.methods && <Link href="/methods" className="link font-semibold">How the simulation works</Link>}
      </p>
      <div className="mt-6">
        <SimLabel date={longDate(forecast.date)} sample={IS_SAMPLE} />
      </div>
    </article>
  );
}
