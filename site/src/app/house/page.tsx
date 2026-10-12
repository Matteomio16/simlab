import type { Metadata } from "next";
import { notFound } from "next/navigation";
import ChamberSwitch from "@/components/ChamberSwitch";
import Dateline from "@/components/Dateline";
import HouseMap from "@/components/HouseMap";
import Reveal from "@/components/Reveal";
import SplitChance from "@/components/SplitChance";
import { Legend } from "@/components/TileMap";
import { Responsive, SeatHistogram } from "@/components/charts";
import { SimLabel } from "@/components/Brand";
import { HAS_FORECAST, IS_SAMPLE, houseDistricts, load } from "@/lib/data";
import { TIER_LEGEND, daysTo, in100, longDate } from "@/lib/format";
import { SHOW } from "@/lib/site";
import { seatOf } from "@/lib/house";
import Link from "next/link";

export const metadata: Metadata = {
  title: "House forecast",
  description: "The state of the House: every seat, played out 40,000 times a day by a social simulation.",
};

function headline(pD: number) {
  if (pD >= 0.85) return "Democrats are clear favorites to win the House";
  if (pD >= 0.65) return "Democrats are favored to win the House";
  if (pD >= 0.55) return "Democrats are slight favorites to win the House";
  if (pD <= 0.15) return "Republicans are clear favorites to keep the House";
  if (pD <= 0.35) return "Republicans are favored to keep the House";
  if (pD <= 0.45) return "Republicans are slight favorites to keep the House";
  return "Control of the House is a toss-up";
}

// The House home (Matteo, 12 Oct): the state of the House first, the map of every seat straight after.
export default function House() {
  if (!HAS_FORECAST || !SHOW.chamberHome) notFound();
  const { forecast } = load();
  const h = forecast.house;
  if (!h) notFound();
  const districts = houseDistricts();
  const nD = in100(h.p_d_majority);
  const maj = h.majority ?? 218;
  const D = h.seats.D;
  const closest = districts
    .filter((d) => d.p != null)
    .sort((a, b) => Math.abs(a.p! - 0.5) - Math.abs(b.p! - 0.5))
    .slice(0, 12);

  return (
    <div className="mx-auto max-w-[1200px] px-4 sm:px-6">
      <div className="pt-3"><ChamberSwitch active="house" /></div>
      <section className="rise pt-3">
        <Dateline left="The state of the House" right={`Updated ${longDate(forecast.date)} · ${daysTo(forecast.date)} days to go`} />
        <h1 className="mt-3 border-b border-rule pb-4 text-[1.6rem] font-extrabold leading-[1.1] tracking-[-0.02em] sm:text-[1.9rem]">{headline(h.p_d_majority)}</h1>
        <div className="mx-auto mt-4 max-w-[720px]">
          <HouseMap seats={districts.map(seatOf)} clickable={SHOW.houseSeats} />
          <div className="mt-4 flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
            <Legend items={TIER_LEGEND.filter((t) => t.label !== "Independent")} />
            <p className="note sm:max-w-xs sm:text-right">{SHOW.houseSeats ? "One square per seat. Select a square for its race." : "One square per seat. Hover a square for its race."}</p>
          </div>
        </div>
      </section>

      <Reveal as="section" className="mt-14 grid gap-10 border-t-[3px] border-rule-strong pt-6 lg:grid-cols-[1fr_1.25fr]">
        <div>
          <p className="label">Control</p>
          <div className="mt-4">
            <SplitChance p={h.p_d_majority} left="D" />
          </div>
          <p className="mt-4 text-[0.95rem] leading-relaxed text-ink-2">
            {`Democrats win ${maj} or more seats in ${nD} of every 100 simulated elections. The middle result is ${D.p50} Democratic seats; 8 in 10 fall between ${D.p10} and ${D.p90}.`}
          </p>
          <dl className="mt-6 text-[0.9rem]">
            {[
              ["If the election were today", h.today ? `Democrats ${in100(h.today.p_d_majority)} in 100` : "–"],
              ["Statistics only, no simulation", h.stats_only ? `Democrats ${in100(h.stats_only.p_d_majority)} in 100` : "–"],
            ].map(([k, v]) => (
              <div key={k} className="flex items-baseline justify-between gap-3 border-b border-rule py-2">
                <dt className="text-ink-2">{k}</dt>
                <dd className="whitespace-nowrap font-semibold">{v}</dd>
              </div>
            ))}
          </dl>
        </div>
        <div className="border-t border-rule pt-6 lg:border-l lg:border-t-0 lg:pl-10 lg:pt-0">
          <p className="label">Democratic seats</p>
          <div className="mt-3">
            <Responsive
              desktop={560}
              render={(w) => (
                <SeatHistogram dist={D.dist ?? {}} w={w} line={maj} span={20} every={w < 480 ? 20 : 10} axis="Democratic seats" left={{ label: "Republicans keep control", color: "var(--rep)" }} right={{ label: "Democrats win control", color: "var(--dem)" }} label="Distribution of Democratic House seats across simulated elections" />
              )}
            />
          </div>
        </div>
      </Reveal>

      <Reveal as="section" className="mt-16 section-rule">
        <p className="label">The closest seats</p>
        <ul className="mt-4 grid gap-x-10 sm:grid-cols-2 lg:grid-cols-3">
          {closest.map((d) => (
            <li key={d.id} className="border-b border-rule py-4">
              {SHOW.houseSeats ? (
                <Link href={`/house/${d.slug}`} prefetch={false} className="text-[0.95rem] font-bold hover:underline">{d.title}</Link>
              ) : (
                <p className="text-[0.95rem] font-bold">{d.title}</p>
              )}
              <p className="mt-0.5 text-[0.8rem] text-ink-2">{`${d.dName ?? "Democrat"} (D) vs. ${d.rName ?? "Republican"} (R)`}</p>
              <div className="mt-3"><SplitChance p={d.p!} left={d.left} size="sm" /></div>
            </li>
          ))}
        </ul>
      </Reveal>

      <div className="mt-10">
        <SimLabel date={longDate(forecast.date)} sample={IS_SAMPLE} />
      </div>
    </div>
  );
}
