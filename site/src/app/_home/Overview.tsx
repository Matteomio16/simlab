import type { ReactNode } from "react";
import RaceTable, { type Row } from "@/components/RaceTable";
import { HistoryLine, Responsive, SeatHistogram } from "@/components/charts";
import { SimLabel } from "@/components/Brand";
import { IS_SAMPLE, load, raceCode, raceTitle, senateRaces } from "@/lib/data";
import { in100, leader, longDate, margin, rating, daysTo } from "@/lib/format";

function Stat({ label, value, note }: { label: string; value: ReactNode; note?: string }) {
  return (
    <div className="border-l border-hairline pl-4">
      <p className="kicker">{label}</p>
      <p className="mt-1 text-2xl font-semibold tabular-nums text-ink">{value}</p>
      {note && <p className="mt-1 text-xs text-muted">{note}</p>}
    </div>
  );
}

export default function Overview() {
  const { forecast, history } = load();
  const s = forecast.senate;
  const rows: Row[] = senateRaces().map(({ id, meta, f, slug }) => ({
    id, slug, title: raceTitle(meta), code: raceCode(id, meta),
    left: meta.candidates.left, right: meta.candidates.right, leftParty: meta.left_party,
    p: f.p_dem_win, today: f.today?.p_dem_win ?? null,
    pollAvg: f.benchmarks.poll_avg == null ? null : margin(f.benchmarks.poll_avg, meta.left_party),
    market: f.benchmarks.market, cook: f.benchmarks.cook,
    rating: rating(f.p_dem_win), leader: leader(f.p_dem_win, meta).party,
  }));
  const tossups = rows.filter((r) => r.rating === "Toss-up").length;
  const moved = senateRaces()
    .flatMap(({ meta, f, slug }) => f.movers.map((m) => ({ ...m, title: raceTitle(meta), slug, left: meta.left_party })))
    .sort((a, b) => Math.abs(b.delta) - Math.abs(a.delta))
    .slice(0, 4);
  const n = in100(s.p_r_50plus);
  const nToday = s.today ? in100(s.today.p_r_50plus) : null;

  return (
    <>
      <section className="mx-auto max-w-6xl px-4 pt-12 sm:px-6 sm:pt-16">
        <p className="kicker">Senate forecast · {longDate(forecast.date)} · {daysTo(forecast.date)} days to go</p>
        <div className="mt-5 grid gap-10 lg:grid-cols-[1.35fr_1fr] lg:items-end">
          <div>
            <h1 className="font-serif text-[2.4rem] leading-[1.08] tracking-[-0.01em] text-ink sm:text-[3.4rem]">
              Republicans hold the Senate in <span className="hl text-rep">{n} of 100</span> simulated elections.
            </h1>
            <p className="mt-5 max-w-xl text-lg leading-relaxed text-ink-2">
              {n >= 35 && n <= 65 ? "Control of the Senate is a toss-up. " : ""}
              {`${tossups} of ${rows.length} races are toss-ups in the simulation. `}
              Holding 50 seats is enough for Republicans, with the Vice President&rsquo;s tie-break.
            </p>
          </div>
          <div className="grid grid-cols-2 gap-6">
            <Stat label="If the election were today" value={nToday == null ? "–" : <>{nToday}<span className="text-base font-normal text-muted"> in 100</span></>} />
            <Stat label="Republican seats" value={`${s.seats.R.p50}`} note={`Range ${s.seats.R.p10}–${s.seats.R.p90}`} />
            <Stat label="Democrats reach 51" value={<>{in100(s.p_d_caucus_51)}<span className="text-base font-normal text-muted"> in 100</span></>} note="With King and Sanders" />
            <Stat label="Independents decide" value={<>{in100(s.p_independents_decide)}<span className="text-base font-normal text-muted"> in 100</span></>} note="Neither side reaches its mark" />
          </div>
        </div>

        <div className="mt-12 grid gap-8 lg:grid-cols-[1.35fr_1fr]">
          <div className="rounded-md border border-hairline bg-raised p-5">
            <div className="flex flex-wrap items-baseline justify-between gap-2">
              <h2 className="font-semibold text-ink">Republican seats across 40,000 simulated elections</h2>
              <span className="text-xs text-muted">
                <span className="text-rep">■</span> 50 or more &nbsp; <span className="text-dem">■</span> fewer
              </span>
            </div>
            <div className="mt-4">
              <Responsive render={(w) => <SeatHistogram dist={s.seats.R.dist} w={w} />} />
            </div>
          </div>
          <div className="rounded-md border border-hairline bg-raised p-5">
            <h2 className="font-semibold text-ink">Beside the benchmarks</h2>
            <dl className="mt-4 divide-y divide-hairline text-sm">
              <div className="flex items-center justify-between py-2.5">
                <dt className="text-ink-2"><span className="mr-2 inline-block h-2 w-2 rounded-full bg-sim" />Simulation, 3 Nov</dt>
                <dd className="font-semibold tabular-nums text-ink">{n} in 100</dd>
              </div>
              <div className="flex items-center justify-between py-2.5">
                <dt className="text-ink-2">Statistics only (no simulation)</dt>
                <dd className="tabular-nums text-ink">{in100(s.stats_only.p_r_50plus)} in 100</dd>
              </div>
              <div className="flex items-center justify-between py-2.5">
                <dt className="text-ink-2">Prediction market</dt>
                <dd className="tabular-nums text-ink">{s.benchmarks.market == null ? "–" : `${in100(s.benchmarks.market)}%`}</dd>
              </div>
              <div className="flex items-center justify-between py-2.5">
                <dt className="text-ink-2">If news matters less / more</dt>
                <dd className="tabular-nums text-ink">{in100(s.news.if_weaker)} / {in100(s.news.if_stronger)}</dd>
              </div>
            </dl>
            {history.senate.length > 1 && (
              <div className="mt-4">
                <p className="kicker mb-1">Republican control, chance in 100</p>
                <Responsive desktop={420} render={(w) => <HistoryLine w={w} label="Chance Republicans hold the Senate" points={history.senate.map((h) => ({ date: h.date, p: h.p_r_50plus }))} />} />
              </div>
            )}
          </div>
        </div>
        <div className="mt-6">
          <SimLabel date={longDate(forecast.date)} sample={IS_SAMPLE} />
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-4 pt-20 sm:px-6">
        <p className="kicker">All 35 Senate races</p>
        <h2 className="mt-3 font-serif text-3xl text-ink">Race by race</h2>
        <p className="mt-2 max-w-2xl text-ink-2">
          The chance each candidate wins in 100 simulated elections on 3 November, beside the poll average, the market
          and Cook. Between 35 and 65 is a toss-up.
        </p>
        <div className="mt-8">
          <RaceTable rows={rows} />
        </div>
      </section>

      {moved.length > 0 && (
        <section className="mx-auto max-w-6xl px-4 pt-20 sm:px-6">
          <p className="kicker">What moved</p>
          <h2 className="mt-3 font-serif text-3xl text-ink">The stories that moved races</h2>
          <p className="mt-2 max-w-2xl text-ink-2">
            How much each story shifts the 3 November margin, after the synthetic voters&rsquo; reactions and the fade
            with time. Stories are summarised neutrally, without outlet names.
          </p>
          <ul className="mt-8 grid gap-4 md:grid-cols-2">
            {moved.map((m) => (
              <li key={m.event_id} className="rounded-md border border-hairline bg-raised p-5">
                <div className="flex items-center justify-between gap-3">
                  <a href={`/senate/${m.slug}`} className="kicker hover:text-ink">{m.title}</a>
                  <span className="font-mono text-sm tabular-nums" style={{ color: m.delta > 0 ? (m.left === "I" ? "var(--ind)" : "var(--dem)") : "var(--rep)" }}>
                    {m.delta > 0 ? m.left : "R"}+{Math.abs(m.delta).toFixed(1)}
                  </span>
                </div>
                <p className="mt-3 text-sm leading-relaxed text-ink-2">{m.card}</p>
              </li>
            ))}
          </ul>
        </section>
      )}
    </>
  );
}
