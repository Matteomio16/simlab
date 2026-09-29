import Link from "next/link";
import DaysTo from "@/components/DaysTo";
import SwarmField from "@/components/SwarmField";
import { SwingBand } from "@/components/Brand";
import { allNotes } from "@/lib/labnotes";
import { SITE } from "@/lib/site";

const STEPS = [
  {
    k: "01",
    title: "Statistics set the starting line",
    body: "Each race starts from the numbers: past results on the 2026 maps, candidates’ records and the polls, corrected for each pollster’s lean.",
  },
  {
    k: "02",
    title: "Synthetic voters react to the news",
    body: "Every day, simulated voter groups read neutral summaries of the day’s stories. Only people who can still move count: the persuadable and the not-yet-motivated.",
  },
  {
    k: "03",
    title: "The evidence checks the simulation",
    body: "Once a week, new polls and early-vote data pull the simulation back towards reality, race by race and state by state.",
  },
  {
    k: "04",
    title: "40,000 simulated elections",
    body: "The simulation runs the election 40,000 times a day. A candidate who wins 62 of every 100 is a favourite, not a certainty.",
  },
];

const PRINCIPLES = [
  { title: "Beside the benchmarks", body: "Every number sits next to the poll average, the prediction market and the Cook Political Report." },
  { title: "Misses published", body: "Scored against the benchmarks on fixed dates from 19 October, with Brier scores and log loss, good weeks and bad." },
  { title: "Method in the open", body: "What the simulation does, which models do which job and what it can’t do, all on the methods page." },
];

export default function Prelaunch({ today }: { today: string }) {
  const days = Math.round((Date.parse(SITE.electionDay) - Date.parse(today)) / 86400000);
  const notes = allNotes().slice(0, 3);
  return (
    <>
      <section className="relative overflow-hidden border-b border-hairline">
        <div className="absolute inset-0 [mask-image:radial-gradient(ellipse_at_70%_40%,black_20%,transparent_75%)]">
          <SwarmField />
        </div>
        <div className="relative mx-auto max-w-6xl px-4 pb-24 pt-20 sm:px-6 sm:pb-32 sm:pt-28">
          <p className="kicker">US midterms · 3 November 2026</p>
          <h1 className="mt-5 max-w-3xl font-serif text-[2.6rem] leading-[1.05] tracking-[-0.01em] text-ink sm:text-6xl">
            A social simulation of the <span className="italic">2026 midterms</span>.
          </h1>
          <p className="mt-6 max-w-2xl text-lg leading-relaxed text-ink-2">
            Synthetic voters react to each day&rsquo;s news. Simulated elections turn their reactions into chances for every
            Senate race, shown beside the poll average, the prediction market and Cook. It is not a poll: nobody real was
            asked anything.
          </p>
          <div className="mt-10 flex flex-wrap items-center gap-x-8 gap-y-4">
            <div className="rounded-md border border-hairline bg-raised/80 px-4 py-3 backdrop-blur">
              <p className="kicker">Forecasts from</p>
              <p className="mt-1 text-xl font-semibold text-ink">Monday 12 October</p>
            </div>
            <div>
              <p className="kicker">Election day</p>
              <p className="mt-1 text-xl font-semibold text-ink">
                <DaysTo target={SITE.electionDay} initial={days} /> days
              </p>
            </div>
            <Link href="/methods" className="text-sm font-medium text-sim underline underline-offset-4">
              How it works →
            </Link>
          </div>
        </div>
        <SwingBand className="h-[3px]" />
      </section>

      <section className="mx-auto max-w-6xl px-4 py-20 sm:px-6">
        <p className="kicker">How it works</p>
        <h2 className="mt-3 max-w-2xl font-serif text-3xl leading-tight text-ink sm:text-4xl">
          The statistics set the level. The simulation moves it.
        </h2>
        <ol className="mt-12 grid gap-px overflow-hidden rounded-md border border-hairline bg-hairline sm:grid-cols-2 lg:grid-cols-4">
          {STEPS.map((s) => (
            <li key={s.k} className="bg-raised p-6">
              <span className="font-mono text-xs text-sim">{s.k}</span>
              <h3 className="mt-4 font-semibold leading-snug text-ink">{s.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-ink-2">{s.body}</p>
            </li>
          ))}
        </ol>
      </section>

      <section className="border-y border-hairline bg-raised/60">
        <div className="mx-auto grid max-w-6xl gap-10 px-4 py-16 sm:px-6 md:grid-cols-3">
          {PRINCIPLES.map((p) => (
            <div key={p.title}>
              <div className="h-px w-10 bg-sim" />
              <h3 className="mt-4 font-serif text-xl text-ink">{p.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-ink-2">{p.body}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-4 py-20 sm:px-6">
        <div className="flex items-end justify-between gap-4">
          <div>
            <p className="kicker">Lab notes</p>
            <h2 className="mt-3 font-serif text-3xl text-ink">The making-of, as it happens</h2>
          </div>
          {notes.length > 0 && (
            <Link href="/lab-notes" className="shrink-0 text-sm text-sim underline underline-offset-4">All notes →</Link>
          )}
        </div>
        {notes.length === 0 ? (
          <p className="mt-6 max-w-xl text-ink-2">
            The first Lab note comes out on Saturday 3 October: how we tested six models as synthetic voters before trusting
            any of them.
          </p>
        ) : (
          <div className="mt-8 grid gap-6 md:grid-cols-3">
            {notes.map((n) => (
              <Link key={n.n} href={`/lab-notes/${n.n}`} className="group block overflow-hidden rounded-md border border-hairline bg-raised">
                {n.slides[0] && (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img src={`/labnotes/${n.n}/${n.slides[0].file}`} alt={n.slides[0].alt} className="aspect-[4/5] w-full object-cover" />
                )}
                <div className="p-4">
                  <p className="kicker">Lab notes {n.n}</p>
                  <p className="mt-1 font-medium text-ink group-hover:underline">{n.title}</p>
                </div>
              </Link>
            ))}
          </div>
        )}
      </section>
    </>
  );
}
