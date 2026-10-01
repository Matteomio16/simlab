import Link from "next/link";
import MapPanel from "@/components/MapPanel";
import RaceTable, { type Row } from "@/components/RaceTable";
import Simulator from "@/components/Simulator";
import Waffle from "@/components/Waffle";
import Reveal from "@/components/Reveal";
import CountUp from "@/components/CountUp";
import RaceCards from "@/components/RaceCards";
import { HistoryLine, Responsive, SeatHistogram } from "@/components/charts";
import { SimLabel } from "@/components/Brand";
import type { Tile } from "@/components/TileMap";
import { IS_SAMPLE, load, raceTitle, senateRaces } from "@/lib/data";
import { STATES } from "@/lib/states";
import { TIER_LEGEND, cookColor, daysTo, in100, leader, longDate, margin, surname, tierColor } from "@/lib/format";

function headline(pR: number, pD: number) {
  if (pR >= 0.85) return "Republicans are clear favorites to keep the Senate";
  if (pR >= 0.65) return "Republicans are favored to keep the Senate";
  if (pR >= 0.55) return "Republicans are slight favorites to keep the Senate";
  if (pD >= 0.55) return pD >= 0.65 ? "Democrats are favored to win the Senate" : "Democrats are slight favorites to win the Senate";
  return "Control of the Senate is a toss-up";
}

function Figure({ n, label, color }: { n: number; label: string; color: string }) {
  return (
    <div>
      <p className="label-muted">{label}</p>
      <p className="mt-1 whitespace-nowrap leading-none">
        <span className="text-[2.4rem] font-extrabold tracking-[-0.02em] sm:text-[3.25rem]" style={{ color }}><CountUp value={n} /></span>
        <span className="ml-1 text-sm font-semibold text-muted sm:ml-1.5 sm:text-lg">in 100</span>
      </p>
    </div>
  );
}

export default function Overview() {
  const { forecast, history } = load();
  const s = forecast.senate;
  const races = senateRaces();
  const rows: Row[] = races.map(({ id, meta, f, slug }) => {
    const t = tierColor(f.p_dem_win, meta.left_party);
    return {
      id, slug, title: raceTitle(meta), state: meta.state,
      left: meta.candidates.left, right: meta.candidates.right, leftParty: meta.left_party,
      p: f.p_dem_win, today: f.today?.p_dem_win ?? null,
      pollAvg: f.benchmarks.poll_avg == null ? null : margin(f.benchmarks.poll_avg, meta.left_party),
      market: f.benchmarks.market, cook: f.benchmarks.cook,
      rating: t.name, tierFill: t.fill, tierInk: t.ink, leader: leader(f.p_dem_win, meta).party,
    };
  });

  const tile = (id: string, fill: string, ink: string, value: string | undefined, title: string): Tile => {
    const r = races.find((x) => x.id === id)!;
    return { state: r.meta.state, fill, ink, value, href: `/senate/${r.slug}`, title, special: r.meta.special };
  };
  const simTiles = races.map(({ id, meta, f }) => {
    const t = tierColor(f.p_dem_win, meta.left_party);
    const l = leader(f.p_dem_win, meta);
    return tile(id, t.fill, t.ink, `${in100(l.p)}`, `${STATES[meta.state]}: ${surname(l.name)} wins ${in100(l.p)} in 100 simulated elections`);
  });
  const cookTiles = races.map(({ id, meta, f }) => {
    const c = cookColor(f.benchmarks.cook) ?? { fill: "var(--paper-2)", ink: "var(--muted)", name: "Not rated" };
    return tile(id, c.fill, c.ink, undefined, `${STATES[meta.state]}: Cook ${c.name}`);
  });
  const marketTiles = races.map(({ id, meta, f }) => {
    const m = f.benchmarks.market;
    if (m == null) return tile(id, "var(--paper-2)", "var(--muted)", undefined, `${STATES[meta.state]}: no market`);
    const t = tierColor(m, meta.left_party);
    const l = leader(m, meta);
    return tile(id, t.fill, t.ink, `${Math.round(l.p * 100)}`, `${STATES[meta.state]}: market prices ${surname(l.name)} at ${Math.round(l.p * 100)}%`);
  });

  const nR = in100(s.p_r_50plus);
  const nD = in100(s.p_d_caucus_51);
  const nI = in100(s.p_independents_decide);
  const moved = races
    .flatMap(({ meta, f, slug }) => f.movers.map((m) => ({ ...m, title: raceTitle(meta), slug, left: meta.left_party })))
    .sort((a, b) => Math.abs(b.delta) - Math.abs(a.delta))
    .slice(0, 6);
  const simRaces = races.map(({ id, meta, f }) => ({
    id, title: raceTitle(meta), left: meta.left_party,
    leftName: surname(meta.candidates.left), rightName: surname(meta.candidates.right), p50: f.margin.p50,
  }));

  return (
    <div className="mx-auto max-w-[1200px] px-4 sm:px-6">
      <section className="rise pt-10 sm:pt-12">
        <p className="label">2026 Senate forecast</p>
        <p className="note mt-1">Updated {longDate(forecast.date)} · {daysTo(forecast.date)} days to Election Day</p>
        <h1 className="mt-4 max-w-4xl text-[2.1rem] font-extrabold leading-[1.08] tracking-[-0.02em] sm:text-[2.9rem]">
          {headline(s.p_r_50plus, s.p_d_caucus_51)}
        </h1>
        <p className="mt-4 max-w-3xl text-[1.2rem] leading-relaxed text-ink-2">
          {`In ${forecast.draws.toLocaleString("en-US")} simulated elections, Republicans keep 50 or more seats, enough with the Vice President’s tie-break, in ${nR} of every 100. The simulation moves each race from its statistical starting line as voter personas react to the news.`}
        </p>

        <Reveal className="mt-10 grid gap-10 border-t-[3px] border-rule-strong pt-6 lg:grid-cols-[1.25fr_1fr]">
          <div>
            <div className="grid grid-cols-3 gap-4">
              <Figure n={nR} label="Republicans hold" color="var(--rep)" />
              <Figure n={nD} label="Democrats reach 51" color="var(--dem)" />
              <Figure n={nI} label="Independents decide" color="var(--ind)" />
            </div>
            <div className="mt-6">
              <Waffle r={nR} d={nD} i={nI} />
            </div>
            <p className="note mt-2">Each square is one simulated election in a hundred. Democrats include King and Sanders.</p>
          </div>
          <div className="border-t border-rule pt-6 lg:border-l lg:border-t-0 lg:pl-10 lg:pt-0">
            <p className="label">Republican seats</p>
            <div className="mt-3">
              <Responsive desktop={460} render={(w) => <SeatHistogram dist={s.seats.R.dist} w={w} />} />
            </div>
            <dl className="mt-4 text-[0.9rem]">
              {[
                ["If the election were today", s.today ? `${in100(s.today.p_r_50plus)} in 100` : "–"],
                ["Statistics only, no simulation", `${in100(s.stats_only.p_r_50plus)} in 100`],
                ["Prediction market", s.benchmarks.market == null ? "–" : `${in100(s.benchmarks.market)}%`],
                ["If news matters less / more", `${in100(s.news.if_weaker)} / ${in100(s.news.if_stronger)}`],
              ].map(([k, v]) => (
                <div key={k} className="flex items-baseline justify-between gap-3 border-b border-rule py-2">
                  <dt className="text-ink-2">{k}</dt>
                  <dd className="whitespace-nowrap font-semibold">{v}</dd>
                </div>
              ))}
            </dl>
            <p className="note mt-2">All figures are Republican control; the market is the Republican price.</p>
          </div>
        </Reveal>
        <div className="mt-6">
          <SimLabel date={longDate(forecast.date)} sample={IS_SAMPLE} />
        </div>
      </section>


      <Reveal as="section" className="mt-14">
        <div className="flex items-baseline justify-between gap-4">
          <p className="label">The closest races</p>
          <a href="#races" className="text-sm font-semibold underline underline-offset-4">All 35 races</a>
        </div>
        <div className="mt-4">
          <RaceCards rows={[...rows].sort((a, b) => Math.abs(a.p - 0.5) - Math.abs(b.p - 0.5)).slice(0, 4)} />
        </div>
      </Reveal>
      {forecast.house && (
        <Reveal as="section" className="mt-14 section-rule">
          <p className="label">House of Representatives</p>
          <div className="mt-3 flex flex-wrap items-baseline gap-x-10 gap-y-3">
            <p className="text-2xl font-bold tracking-[-0.01em]">
              {`Democrats win the House in ${in100(forecast.house.p_d_majority)} of 100 simulated elections`}
            </p>
            <p className="text-ink-2">
              {`Democratic seats: ${forecast.house.seats.D.p50} in the middle simulation, ${forecast.house.seats.D.p10}–${forecast.house.seats.D.p90} in 8 of 10. ${forecast.house.majority ?? 218} wins control. Republicans win it in ${in100(forecast.house.p_r_majority)} of 100.`}
            </p>
          </div>
        </Reveal>
      )}

      <Reveal as="section" className="mt-16 section-rule">
        <p className="label">The map</p>
        <h2 className="mt-2 text-2xl font-bold tracking-[-0.01em]">35 races, beside the benchmarks</h2>
        <p className="mt-2 max-w-2xl text-ink-2">
          Switch between our simulation, the Cook Political Report and the prediction markets. Numbers show the leader&rsquo;s
          chance in 100. Select a state for its race. A dot marks a special election.
        </p>
        <div className="mt-6 max-w-[860px]">
          <MapPanel
            legend={TIER_LEGEND}
            views={[
              { key: "sim", label: "Our simulation", tiles: simTiles, note: "Toss-up: 35 to 65 in 100." },
              { key: "cook", label: "Cook Political Report", tiles: cookTiles, note: "Cook's published ratings, for comparison." },
              { key: "market", label: "Prediction markets", tiles: marketTiles, note: "Kalshi and Polymarket prices, for comparison; never an input." },
            ]}
          />
        </div>
      </Reveal>

      <Reveal as="section" className="mt-16 section-rule">
        <p className="label">Simulator</p>
        <h2 className="mt-2 text-2xl font-bold tracking-[-0.01em]">What if the country shifts?</h2>
        <p className="mt-2 max-w-2xl text-ink-2">
          Polls can miss together, and late news can move every state at once. Drag the national swing to see how the
          Senate changes across our simulated elections.
        </p>
        <div className="mt-8">
          <Simulator races={simRaces} />
        </div>
      </Reveal>

      <Reveal as="section" className="mt-16 section-rule">
        <p className="label" id="races">Every race</p>
        <h2 className="mt-2 text-2xl font-bold tracking-[-0.01em]">Race by race</h2>
        <div className="mt-6">
          <RaceTable rows={rows} />
        </div>
      </Reveal>

      {moved.length > 0 && (
        <Reveal as="section" className="mt-16 section-rule">
          <p className="label">What moved</p>
          <h2 className="mt-2 text-2xl font-bold tracking-[-0.01em]">The stories behind today&rsquo;s changes</h2>
          <p className="mt-2 max-w-2xl text-ink-2">
            Each story&rsquo;s effect on the Nov. 3 margin, after the voter personas&rsquo; reactions and the fade with time.
            Stories are summarized neutrally, without outlet names.
          </p>
          <ul className="mt-6 grid gap-x-10 md:grid-cols-2">
            {moved.map((m) => (
              <li key={m.event_id} className="flex gap-4 border-b border-rule py-4">
                <span className="w-16 shrink-0 text-right font-bold" style={{ color: m.delta > 0 ? (m.left === "I" ? "var(--ind)" : "var(--dem)") : "var(--rep)" }}>
                  {m.delta > 0 ? m.left : "R"}+{Math.abs(m.delta).toFixed(1)}
                </span>
                <span>
                  <Link href={`/senate/${m.slug}`} prefetch={false} className="text-[0.8rem] font-bold uppercase tracking-[0.05em] hover:underline">{m.title}</Link>
                  <span className="mt-1 block text-[1.02rem] leading-snug text-ink-2">{m.card}</span>
                </span>
              </li>
            ))}
          </ul>
        </Reveal>
      )}

      {history.senate.length > 1 && (
        <Reveal as="section" className="mt-16 section-rule">
          <p className="label">Over time</p>
          <h2 className="mt-2 text-2xl font-bold tracking-[-0.01em]">Republican chance of keeping the Senate</h2>
          <div className="mt-6 max-w-[860px]">
            <Responsive desktop={860} render={(w) => <HistoryLine w={w} label="Chance Republicans hold the Senate" points={history.senate.map((h) => ({ date: h.date, p: h.p_r_50plus }))} />} />
          </div>
        </Reveal>
      )}
    </div>
  );
}
