import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { JetBrains_Mono, Silkscreen } from "next/font/google";
import { Logomark } from "@/components/Brand";
import MapPanel from "@/components/MapPanel";
import RaceCards from "@/components/RaceCards";
import Simulator from "@/components/Simulator";
import Waffle from "@/components/Waffle";
import Reveal from "@/components/Reveal";
import CountUp from "@/components/CountUp";
import type { Row } from "@/components/RaceTable";
import { HAS_FORECAST, IS_SAMPLE, load, raceTitle, senateRaces } from "@/lib/data";
import { STATES } from "@/lib/states";
import { TIER_LEGEND, cookColor, in100, leader, margin, surname, tierColor } from "@/lib/format";
import Clock from "./Clock";
import "./terminal.css";

// Experimental skin of the forecast home in the style of situation-room dashboards (Matteo, 29 Sep). Preview only:
// not linked, not indexed, and not built before launch.
const mono = JetBrains_Mono({ variable: "--font-term-mono", subsets: ["latin"], weight: ["400", "500", "700"] });
const pixel = Silkscreen({ variable: "--font-term-pixel", subsets: ["latin"], weight: ["400", "700"] });

export const metadata: Metadata = { title: "Senate situation room (experimental)", robots: { index: false, follow: false } };

function level(pR: number) {
  const q = Math.max(pR, 1 - pR);
  const side = pR >= 0.5 ? "Republicans" : "Democrats";
  if (q <= 0.6) return { n: 1, color: "#f0554a", text: "Control in play", sub: "Senate control is a toss-up" };
  if (q <= 0.7) return { n: 2, color: "#f2b33d", text: `${side} slight favorites`, sub: "Control could flip on a normal polling miss" };
  if (q <= 0.85) return { n: 3, color: "#e6d23f", text: `${side} favored`, sub: "A flip needs a sizeable miss" };
  return { n: 4, color: "#3ecf6e", text: `${side} clear favorites`, sub: "Control looks settled" };
}

export default function Terminal() {
  if (!HAS_FORECAST) notFound();
  const { forecast } = load();
  const s = forecast.senate;
  const races = senateRaces();
  const nR = in100(s.p_r_50plus), nD = in100(s.p_d_caucus_51), nI = in100(s.p_independents_decide);
  const lv = level(s.p_r_50plus);
  const rows: Row[] = races.map(({ id, meta, f, slug }) => {
    const t = tierColor(f.p_dem_win, meta.left_party);
    return {
      id, slug, title: raceTitle(meta), state: meta.state, left: meta.candidates.left, right: meta.candidates.right,
      leftParty: meta.left_party, p: f.p_dem_win, today: f.today?.p_dem_win ?? null,
      pollAvg: f.benchmarks.poll_avg == null ? null : margin(f.benchmarks.poll_avg, meta.left_party),
      market: f.benchmarks.market, cook: f.benchmarks.cook, rating: t.name, tierFill: t.fill, tierInk: t.ink,
      leader: leader(f.p_dem_win, meta).party,
    };
  });
  const tile = (id: string, fill: string, ink: string, value: string | undefined, title: string) => {
    const r = races.find((x) => x.id === id)!;
    return { state: r.meta.state, fill, ink, value, href: `/senate/${r.slug}`, title, special: r.meta.special };
  };
  const simTiles = races.map(({ id, meta, f }) => {
    const t = tierColor(f.p_dem_win, meta.left_party);
    const l = leader(f.p_dem_win, meta);
    return tile(id, t.fill, "#ffffff", `${in100(l.p)}`, `${STATES[meta.state]}: ${surname(l.name)} ${in100(l.p)} in 100`);
  });
  const cookTiles = races.map(({ id, meta, f }) => {
    const c = cookColor(f.benchmarks.cook) ?? { fill: "var(--paper-2)", ink: "var(--muted)", name: "Not rated" };
    return tile(id, c.fill, "#ffffff", undefined, `${STATES[meta.state]}: Cook ${c.name}`);
  });
  const feed = races
    .flatMap(({ meta, f }) => f.movers.map((m) => ({ ...m, code: `${meta.state}-SEN${meta.special ? "-S" : ""}`, left: meta.left_party })))
    .sort((a, b) => Math.abs(b.delta) - Math.abs(a.delta))
    .slice(0, 7);
  const simRaces = races.map(({ id, meta, f }) => ({
    id, title: raceTitle(meta), left: meta.left_party, leftName: surname(meta.candidates.left), rightName: surname(meta.candidates.right), p50: f.margin.p50,
  }));
  const tossups = rows.filter((r) => r.rating === "Toss-up").length;

  return (
    <div className={`terminal ${mono.variable} ${pixel.variable} -mb-28 pb-20`}>
      <div className="border-b border-rule text-[0.72rem] uppercase tracking-[0.06em] text-ink-2">
        <div className="mx-auto flex max-w-[1240px] flex-wrap items-center gap-x-5 gap-y-2 px-4 py-2.5 sm:px-6">
          <span className="chip"><Clock /></span>
          <span className="chip" style={{ color: "var(--green)", borderColor: "#1f5f36" }}>Status: operational</span>
          <span className="flex items-center gap-2"><span className="live-dot" /> 35 races monitored</span>
          <span>{forecast.draws.toLocaleString("en-US")} simulated elections / run</span>
          <span className="ml-auto">{IS_SAMPLE ? "Sample data" : `Run ${forecast.run_id}`}</span>
        </div>
      </div>

      <div className="mx-auto max-w-[1240px] px-4 sm:px-6">
        <header className="flex flex-wrap items-center gap-5 pt-10">
          <span className="text-[var(--sim)]"><Logomark size={46} /></span>
          <div>
            <h1 className="pixel text-[2.1rem] font-bold leading-none sm:text-[3.4rem]">SENATE SIM INDEX</h1>
            <p className="mt-2 text-[0.85rem] text-ink-2">Social simulation, not a poll <span className="text-muted">|</span> synthetic voters, simulated elections</p>
          </div>
        </header>

        <section className="panel crt glow mt-8 p-5 sm:p-6" style={{ ["--level" as string]: lv.color }}>
          <div className="flex flex-wrap items-end justify-between gap-6">
            <div>
              <p className="pixel level-text text-[2.2rem] font-bold leading-none sm:text-[3rem]">SENATECON {lv.n}</p>
              <p className="mt-2 text-[0.8rem] uppercase tracking-[0.08em]" style={{ color: lv.color }}>{lv.text} · {lv.sub}</p>
            </div>
            <div className="flex gap-8 text-right">
              {[["R hold", nR, "var(--rep)"], ["D reach 51", nD, "var(--dem)"], ["Ind. decide", nI, "var(--ind)"]].map(([k, v, c]) => (
                <div key={k as string}>
                  <p className="text-[0.7rem] uppercase tracking-[0.08em] text-muted">{k}</p>
                  <p className="pixel text-[2.4rem] font-bold leading-none" style={{ color: c as string }}><CountUp value={v as number} /></p>
                </div>
              ))}
            </div>
          </div>
          <div className="mt-5">
            <Waffle r={nR} d={nD} i={nI} />
          </div>
          <p className="mt-2 text-[0.72rem] text-muted">1 square = 1 simulated election in 100 · levels: 1 toss-up · 2 lean · 3 likely · 4 settled</p>
        </section>

        <div className="mt-6 grid gap-6 lg:grid-cols-[1.1fr_1fr]">
          <Reveal as="section" className="panel p-5">
            <div className="flex items-center justify-between">
              <p className="flex items-center gap-2 text-[0.85rem] font-bold uppercase tracking-[0.06em]"><span className="live-dot" /> Sim feed</p>
              <span className="chip text-muted">What moved races</span>
            </div>
            <ul className="mt-4 space-y-3 text-[0.82rem]">
              {feed.length === 0 && <li className="text-muted">No story moved a race today.</li>}
              {feed.map((m) => (
                <li key={m.event_id} className="grid grid-cols-[88px_62px_1fr] gap-3 border-b border-rule pb-3">
                  <span className="text-muted">{m.code}</span>
                  <span className="font-bold" style={{ color: m.delta > 0 ? (m.left === "I" ? "var(--ind)" : "var(--dem)") : "var(--rep)" }}>
                    {`${m.delta > 0 ? m.left : "R"}+${Math.abs(m.delta).toFixed(1)}`}
                  </span>
                  <span className="text-ink-2">{m.card}</span>
                </li>
              ))}
              <li className="cursor text-muted">awaiting next run</li>
            </ul>
          </Reveal>
          <Reveal as="section" className="panel p-5">
            <p className="text-[0.85rem] font-bold uppercase tracking-[0.06em]">Chamber map</p>
            <div className="mt-3">
              <MapPanel legend={TIER_LEGEND} views={[
                { key: "sim", label: "Simulation", tiles: simTiles, note: `${tossups} toss-ups · 35 to 65 in 100` },
                { key: "cook", label: "Cook", tiles: cookTiles, note: "Cook ratings, for comparison" },
              ]} />
            </div>
          </Reveal>
        </div>

        <Reveal as="section" className="mt-6">
          <p className="text-[0.85rem] font-bold uppercase tracking-[0.06em]">Closest races</p>
          <div className="mt-3">
            <RaceCards rows={[...rows].sort((a, b) => Math.abs(a.p - 0.5) - Math.abs(b.p - 0.5)).slice(0, 8)} />
          </div>
        </Reveal>

        <Reveal as="section" className="panel mt-6 p-5 sm:p-6">
          <p className="text-[0.85rem] font-bold uppercase tracking-[0.06em]">Scenario console · national swing</p>
          <div className="mt-5">
            <Simulator races={simRaces} />
          </div>
        </Reveal>

        <p className="mt-8 text-center text-[0.72rem] uppercase tracking-[0.1em] text-muted">
          Experimental view · NotAPoll.org · social simulation, not a poll · markets and Cook never enter the forecast
        </p>
      </div>
    </div>
  );
}
