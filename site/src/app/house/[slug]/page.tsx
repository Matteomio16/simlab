import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import ArrivalWash from "@/components/ArrivalWash";
import HouseMap from "@/components/HouseMap";
import Reveal from "@/components/Reveal";
import SplitChance from "@/components/SplitChance";
import CountUp from "@/components/CountUp";
import { SimLabel } from "@/components/Brand";
import { HAS_FORECAST, IS_SAMPLE, houseDistricts, load, type District } from "@/lib/data";
import { in100, longDate, margin, partyVar, rating, surname } from "@/lib/format";
import { consensusName, seatOf } from "@/lib/house";
import { SHOW } from "@/lib/site";
import { STATES } from "@/lib/states";

export const dynamicParams = false;

const districts = () => (HAS_FORECAST && SHOW.chamberHome && SHOW.houseSeats ? houseDistricts() : []);

// Without House data, one placeholder keeps the static export happy and renders a 404.
export function generateStaticParams() {
  const ds = districts();
  return ds.length ? ds.map((d) => ({ slug: d.slug })) : [{ slug: "none" }];
}

export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }): Promise<Metadata> {
  const { slug } = await params;
  const d = districts().find((x) => x.slug === slug);
  return d ? { title: `${d.title} House race`, description: `The ${d.title} House race, played out 40,000 times a day by a social simulation.` } : {};
}

const TIER: Record<string, string> = {
  simulate: "Full simulation: voter personas react to each day's news in this race.",
  watch: "On watch: statistics, with the biggest stories checked every day.",
  statistics: "Statistics only: every benchmark calls this seat safe.",
};

function Range({ m, left }: { m: NonNullable<District["margin"]>; left: "D" | "I" }) {
  const lim = Math.max(10, Math.ceil(Math.max(Math.abs(m.p10), Math.abs(m.p90)) / 5) * 5);
  const x = (v: number) => 50 + (v / lim) * 50;
  const lo = Math.min(m.p10, m.p90);
  const hi = Math.max(m.p10, m.p90);
  return (
    <div>
      <div className="relative h-9">
        <div className="absolute inset-x-0 top-1/2 h-px bg-rule" />
        <div className="absolute top-1/2 h-8 w-px -translate-y-1/2 bg-axis" style={{ left: "50%" }} />
        <div
          className="absolute top-1/2 h-3 -translate-y-1/2 rounded-[2px]"
          style={{ left: `${x(lo)}%`, width: `${x(hi) - x(lo)}%`, background: `linear-gradient(90deg, var(--rep-3), var(--tossup-tile), ${left === "I" ? "var(--ind-3)" : "var(--dem-3)"})` }}
        />
        <div className="absolute top-1/2 h-6 w-[3px] -translate-x-1/2 -translate-y-1/2 bg-ink" style={{ left: `${x(m.p50)}%` }} />
      </div>
      <div className="mt-1 flex justify-between text-[0.75rem] font-semibold text-muted">
        <span>{`R+${lim}`}</span>
        <span>Even</span>
        <span>{`${left}+${lim}`}</span>
      </div>
    </div>
  );
}

export default async function HouseSeat({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const all = districts();
  const d = all.find((x) => x.slug === slug);
  if (!d) notFound();
  const { forecast } = load();
  const state = STATES[d.state] ?? d.state;
  const seat = d.district ? `District ${d.district}` : "At-large district";
  const neighbours = all.filter((x) => x.state === d.state && x.id !== d.id && x.p != null).sort((a, b) => Math.abs(a.p! - 0.5) - Math.abs(b.p! - 0.5)).slice(0, 6);
  const leftName = d.dName ?? (d.left === "I" ? "Independent" : "Democrat");
  const rightName = d.rName ?? "Republican";
  const lead = d.p != null ? (d.p >= 0.5 ? { name: leftName, n: in100(d.p) } : { name: rightName, n: 100 - in100(d.p) }) : null;
  const r = d.p != null ? rating(d.p) : null;
  const side = d.p != null && d.p >= 0.5 ? (d.left === "I" ? "independent" : "Democratic") : "Republican";
  const incumbent = d.incumbent ? `${d.incumbent} (${d.incumbentParty ?? "?"})${d.open ? ", not running" : ""}` : "Open seat";

  return (
    <article className="mx-auto max-w-[1200px] px-4 pt-8 sm:px-6 sm:pt-10">
      <ArrivalWash state={d.id} />
      <nav className="text-[0.85rem] font-semibold text-ink-2">
        <Link href="/house" className="hover:underline">House forecast</Link> <span className="text-muted">/</span> {d.title}
      </nav>

      <header className="mt-6 grid gap-10 lg:grid-cols-[1fr_340px]">
        <div className="rise">
          <p className="label">{`${state} · ${seat}`}</p>
          <h1 className="mt-3 text-[2.1rem] font-extrabold leading-[1.08] tracking-[-0.02em] sm:text-[2.8rem]">
            {lead ? `${surname(lead.name)} wins ${lead.n} of 100 simulated elections` : `Uncontested: only a ${d.fixed === "R" ? "Republican" : "Democrat"} is on the ballot`}
          </h1>
          <p className="mt-4 max-w-3xl text-[1.2rem] leading-relaxed text-ink-2">
            {d.p != null && d.margin
              ? `The simulation rates ${d.id} ${r === "Toss-up" ? "a toss-up" : `${r!.toLowerCase()} ${side}`}. The middle simulated result is ${margin(d.margin.p50, d.left)}, and 8 in 10 fall between ${margin(d.margin.p10, d.left)} and ${margin(d.margin.p90, d.left)}.`
              : `This seat counts for the ${d.fixed === "R" ? "Republicans" : "Democrats"} in every simulated election.`}
          </p>
        </div>
        <div className="arrive hidden lg:block">
          <HouseMap seats={all.map(seatOf)} current={d.id} />
        </div>
      </header>

      {d.p != null && (
        <section className="rise mt-8 grid gap-10 border-t-[3px] border-rule-strong pt-6 lg:grid-cols-[1fr_1fr]">
          <div>
            <SplitChance p={d.p} left={d.left} render={(v) => <CountUp value={v} />} />
            <p className="mt-3 text-[0.9rem] text-ink-2">
              <span className="font-semibold" style={{ color: partyVar(d.left) }}>{`${leftName} (${d.left})`}</span>
              <span className="text-muted"> vs. </span>
              <span className="font-semibold text-rep">{`${rightName} (R)`}</span>
            </p>
            {d.margin && (
              <div className="mt-6">
                <p className="label-muted">Margin, 8 in 10 simulated elections</p>
                <div className="mt-2"><Range m={d.margin} left={d.left} /></div>
              </div>
            )}
          </div>
          <div className="border-t border-rule pt-6 lg:border-l lg:border-t-0 lg:pl-10 lg:pt-0">
            <p className="label">Beside the benchmarks</p>
            <dl className="mt-3 text-[0.92rem]">
              {[
                ["Our simulation, Nov. 3", `${surname(leftName)} ${in100(d.p)} in 100`],
                ["Statistics only, no simulation", d.statsP == null ? "–" : `${surname(leftName)} ${in100(d.statsP)} in 100`],
                ["Expert ratings, averaged", consensusName(d.consensus) ?? "–"],
                ["Incumbent", incumbent],
              ].map(([k, v], i) => (
                <div key={k} className="flex items-baseline justify-between gap-3 border-b border-rule py-2.5">
                  <dt className="flex items-center gap-2 text-ink-2">
                    {i === 0 && <span className="inline-block h-2 w-2 bg-sim" aria-hidden="true" />}
                    {k}
                  </dt>
                  <dd className="text-right font-semibold">{v}</dd>
                </div>
              ))}
            </dl>
            {d.tier && TIER[d.tier] && <p className="mt-4 bg-note px-4 py-3 text-[0.92rem] leading-relaxed text-ink">{TIER[d.tier]}</p>}
          </div>
        </section>
      )}

      {neighbours.length > 0 && (
        <Reveal as="section" className="mt-14 section-rule">
          <p className="label">{`Other seats in ${state}`}</p>
          <ul className="mt-4 grid gap-x-10 sm:grid-cols-2 lg:grid-cols-3">
            {neighbours.map((n) => (
              <li key={n.id} className="border-b border-rule py-4">
                <Link href={`/house/${n.slug}`} prefetch={false} className="text-[0.95rem] font-bold hover:underline">{n.title}</Link>
                <div className="mt-3"><SplitChance p={n.p!} left={n.left} size="sm" /></div>
              </li>
            ))}
          </ul>
        </Reveal>
      )}

      <div className="mt-10">
        <SimLabel date={longDate(forecast.date)} sample={IS_SAMPLE} />
      </div>
    </article>
  );
}
