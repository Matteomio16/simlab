import Link from "next/link";
import DaysTo from "@/components/DaysTo";
import Reveal from "@/components/Reveal";
import TileMap, { Legend } from "@/components/TileMap";
import { loadRaceMeta, raceTitle } from "@/lib/data";
import { allNotes } from "@/lib/labnotes";
import { SITE } from "@/lib/site";
import { STATES } from "@/lib/states";

const STEPS = [
  ["Starting line", "Each race starts from statistics: past results, the candidates’ records and the polls, corrected for each pollster’s lean. The simulation never sets these numbers."],
  ["Daily news", "Every day, 28 groups of synthetic voters in each state read neutral summaries of the day’s stories. Only people who can still move count: the persuadable, and those not yet sure to vote."],
  ["Weekly check", "Once a week, new polls and early-vote data pull the simulation back towards the evidence, state by state."],
  ["Chances", "The election is simulated 40,000 times a day. A candidate who wins 62 of every 100 is favored, not certain."],
];

const PARTY = { D: "var(--dem)", R: "var(--rep)", I: "var(--ind)" } as const;

export default function Prelaunch({ today }: { today: string }) {
  const days = Math.round((Date.parse(SITE.electionDay) - Date.parse(today)) / 86400000);
  const meta = loadRaceMeta();
  const ids = Object.keys(meta).filter((id) => meta[id].office === "senate");
  const races = ids.map((id) => ({ id, m: meta[id] })).sort((a, b) => raceTitle(a.m).localeCompare(raceTitle(b.m)));
  const held = { D: 0, R: 0, I: 0 };
  for (const { m } of races) held[m.incumbent_party] += 1;
  const tiles = races.map(({ m }) => ({
    state: m.state,
    fill: PARTY[m.incumbent_party],
    ink: "#ffffff",
    special: m.special,
    title: `${STATES[m.state]}${m.special ? " (special)" : ""}: seat held by ${m.incumbent_party === "D" ? "Democrats" : m.incumbent_party === "R" ? "Republicans" : "an independent"}`,
  }));
  const notes = allNotes().slice(0, 3);

  return (
    <div className="mx-auto max-w-[1200px] px-4 sm:px-6">
      <section className="grid gap-10 pt-10 sm:pt-14 lg:grid-cols-[1fr_1.15fr] lg:gap-14">
        <div>
          <p className="label">2026 Senate forecast</p>
          <h1 className="mt-4 text-[2.3rem] font-extrabold leading-[1.05] tracking-[-0.02em] sm:text-[3.1rem]">
            The forecast begins October&nbsp;12.
          </h1>
          <p className="mt-5 font-serif text-[1.2rem] leading-relaxed text-ink-2">
            NotAPoll.org forecasts the 2026 midterms with a social simulation. Synthetic voters react to each day&rsquo;s
            news, and simulated elections turn their reactions into chances for every Senate race. Each number will sit
            beside the poll average, the prediction market and the Cook Political Report.
          </p>
          <dl className="mt-8 grid grid-cols-3 border-y-[3px] border-rule-strong">
            {[
              ["Senate races", `${races.length}`],
              ["Forecast from", "Oct. 12"],
              ["Days to Nov. 3", <DaysTo key="d" target={SITE.electionDay} initial={days} />],
            ].map(([k, v], i) => (
              <div key={i} className={`py-3 ${i ? "border-l border-rule pl-4" : ""}`}>
                <dt className="label-muted">{k}</dt>
                <dd className="mt-1 text-2xl font-bold">{v}</dd>
              </div>
            ))}
          </dl>
          <p className="mt-6 text-[0.95rem]">
            <Link href="/methods" className="link font-semibold">Read how the simulation works</Link>
          </p>
        </div>

        <div>
          <p className="label">Seats up in 2026, by the party that holds them</p>
          <div className="mt-4">
            <TileMap tiles={tiles} />
          </div>
          <div className="mt-3 flex flex-wrap items-center justify-between gap-2">
            <Legend items={[
              { fill: "var(--rep)", label: `Republican, ${held.R}` },
              { fill: "var(--dem)", label: `Democratic, ${held.D}` },
              { fill: "var(--paper)", label: "No race", border: true },
            ]} />
            <p className="note">A dot marks a special election.</p>
          </div>
        </div>
      </section>

      <Reveal as="section" className="mt-16 section-rule">
        <p className="label">How the forecast works</p>
        <ol className="mt-4 grid gap-x-10 md:grid-cols-2 lg:grid-cols-4">
          {STEPS.map(([title, body], i) => (
            <li key={title} className="border-b border-rule py-4 lg:border-b-0">
              <p className="text-[0.95rem] font-bold">
                <span className="text-sim">{i + 1}.</span> {title}
              </p>
              <p className="mt-2 font-serif text-[1.02rem] leading-relaxed text-ink-2">{body}</p>
            </li>
          ))}
        </ol>
      </Reveal>

      <Reveal as="section" className="mt-16 section-rule">
        <div className="flex items-baseline justify-between gap-4">
          <p className="label">The races</p>
          <p className="note">Democrats and independents listed first</p>
        </div>
        <table className="mt-4 w-full border-collapse text-[0.92rem]">
          <thead>
            <tr className="border-y-2 border-rule-strong text-left text-[0.7rem] font-bold uppercase tracking-[0.06em]">
              <th className="py-2 pr-3">State</th>
              <th className="py-2 pr-3">Candidates</th>
              <th className="hidden py-2 pr-3 md:table-cell">Seat held by</th>
              <th className="hidden py-2 lg:table-cell">Status</th>
            </tr>
          </thead>
          <tbody>
            {races.map(({ id, m }) => (
              <tr key={id} className="border-b border-rule align-top">
                <td className="py-2.5 pr-3 font-bold">{raceTitle(m)}</td>
                <td className="py-2.5 pr-3">
                  <span style={{ color: PARTY[m.left_party] }}>{m.candidates.left} ({m.left_party})</span>
                  <span className="text-muted"> vs. </span>
                  <span style={{ color: "var(--rep)" }}>{m.candidates.right} (R)</span>
                </td>
                <td className="hidden py-2.5 pr-3 md:table-cell">
                  <span className="mr-2 inline-block h-2.5 w-2.5 align-middle" style={{ background: PARTY[m.incumbent_party] }} />
                  {m.incumbent_party === "D" ? "Democrats" : m.incumbent_party === "R" ? "Republicans" : "Independent"}
                </td>
                <td className="hidden py-2.5 text-ink-2 lg:table-cell">{m.status}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <p className="note mt-3">Candidates as nominated or expected; updated as primaries and appointments settle.</p>
      </Reveal>

      <Reveal as="section" className="mt-16 section-rule">
        <div className="flex items-baseline justify-between gap-4">
          <p className="label">Lab notes</p>
          {notes.length > 0 && <Link href="/lab-notes" className="text-sm font-semibold underline underline-offset-4">All notes</Link>}
        </div>
        <h2 className="mt-2 text-2xl font-bold tracking-[-0.01em]">The making-of, published as we go</h2>
        {notes.length === 0 ? (
          <p className="mt-3 max-w-2xl font-serif text-[1.1rem] leading-relaxed text-ink-2">
            The first note comes out on Saturday, October 3: how six models were tested as synthetic voters before any of
            them was trusted with a forecast.
          </p>
        ) : (
          <ul className="mt-4">
            {notes.map((n) => (
              <li key={n.n} className="border-b border-rule">
                <Link href={`/lab-notes/${n.n}`} className="group flex items-baseline gap-4 py-4">
                  <span className="label-muted w-24 shrink-0">Note {n.n}</span>
                  <span className="text-lg font-semibold group-hover:underline">{n.title}</span>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </Reveal>
    </div>
  );
}
