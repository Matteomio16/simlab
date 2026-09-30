import Link from "next/link";
import Countdown from "@/components/Countdown";
import Reveal from "@/components/Reveal";
import TileMap, { Legend } from "@/components/TileMap";
import VoterField from "@/components/VoterField";
import { SwingBand } from "@/components/Brand";
import { loadRaceMeta, raceTitle } from "@/lib/data";
import { allNotes } from "@/lib/labnotes";
import { SITE } from "@/lib/site";
import { STATES } from "@/lib/states";

// The launch page (Matteo, 30 Sep): what NotAPoll is, why it is different, when the forecasts start. No forecast
// numbers until 12 October; the pilot is private.
const LAUNCH = "2026-10-12T11:00:00Z";

// The same three steps as the pinned post (Content & site, 30 Sep), so the site and the posts say one thing.
const STEPS = [
  {
    q: "Where each race starts",
    a: "Real statistics.",
    b: "Past results, the economy and the poll average set every race's starting line. The simulation never invents it.",
  },
  {
    q: "How the news moves it",
    a: "Synthetic voters react.",
    b: "Built from real data on how groups of Americans vote, they react to each day's events. Only those who could still change their mind, or still decide whether to vote, move the numbers, and every story fades.",
  },
  {
    q: "Who wins, and how often",
    a: "40,000 simulated elections.",
    b: "Each race is played out 40,000 times a day. The share a candidate wins is their chance; between 35 and 65 in 100 is a toss-up.",
  },
];

const BENCHMARKS: [string, string, boolean?][] = [
  ["Our social simulation", "Statistics plus synthetic voters, corrected every Monday.", true],
  ["Statistics only", "The same model with the simulation switched off: the number to beat."],
  ["Poll average", "The average of published polls in each race."],
  ["Prediction markets", "Kalshi and Polymarket prices, averaged."],
  ["Cook Political Report", "Expert race ratings."],
];

const TIMELINE = [
  { d: "Oct 3", t: "The making-of begins", b: "Lab notes: what we tested, what failed, what we changed." },
  { d: "Oct 5–11", t: "Private rehearsal", b: "The full daily run in five states. Nothing published." },
  { d: "Oct 12", t: "Forecasts go public", b: "All 35 Senate races, updated every day.", hot: true },
  { d: "Oct 19", t: "First public score", b: "Then every Monday, good weeks and bad." },
  { d: "Nov 3", t: "Election Day", b: "The final forecast. Then the results decide." },
];

const PARTY = { D: "var(--dem)", R: "var(--rep)", I: "var(--ind)" } as const;

export default function Prelaunch({ today }: { today: string }) {
  const initialDays = Math.max(0, Math.round((Date.parse(LAUNCH) - Date.parse(today)) / 86400000));
  const meta = loadRaceMeta();
  const races = Object.keys(meta)
    .filter((id) => meta[id].office === "senate")
    .map((id) => ({ id, m: meta[id] }))
    .sort((a, b) => raceTitle(a.m).localeCompare(raceTitle(b.m)));
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
  const social = SITE.social.filter((s) => s.live);

  return (
    <div className="mx-auto max-w-[1200px] px-4 sm:px-6">
      <section className="grid gap-10 pb-14 pt-8 sm:pt-12 lg:grid-cols-[1fr_1fr] lg:gap-14">
        <div className="rise flex flex-col">
          <div className="flex items-baseline justify-between border-b border-rule pb-2 text-[0.72rem] font-bold uppercase tracking-[0.08em]">
            <span>Democracy, rehearsed.</span>
            <span className="text-muted">U.S. Senate · 2026</span>
          </div>
          <h1 className="mt-7 text-[2.45rem] font-extrabold leading-[1.04] tracking-[-0.022em] sm:text-[3.25rem]">
            The 2026 midterms, simulated every day.
          </h1>
          <p className="mt-5 max-w-[34rem] text-[1.15rem] leading-relaxed text-ink-2">
            Synthetic voters react to each day&rsquo;s news, and 40,000 simulated elections turn their reactions into chances
            for all 35 Senate races.
          </p>
          <p className="mt-4 flex items-center gap-2 text-[0.95rem] font-semibold">
            <span className="inline-block h-2 w-2 bg-sim" aria-hidden="true" />
            Not a poll. Nobody was asked anything.
          </p>

          <dl className="mt-8 grid grid-cols-3 border-y-2 border-rule-strong">
            {[
              ["Senate races", "35"],
              ["Simulated elections a day", "40,000"],
              ["First public forecast", "Oct 12"],
            ].map(([k, v], i) => (
              <div key={k} className={`py-3 ${i ? "border-l border-rule pl-4" : ""}`}>
                <dt className="text-[0.72rem] font-semibold leading-tight text-muted">{k}</dt>
                <dd className="mt-1 text-[1.5rem] font-bold leading-none tracking-[-0.01em]">{v}</dd>
              </div>
            ))}
          </dl>
          <div className="mt-4 flex flex-wrap items-baseline gap-x-4 gap-y-2">
            <span className="text-[0.72rem] font-bold uppercase tracking-[0.08em] text-muted">Forecasts in</span>
            <Countdown to={LAUNCH} initialDays={initialDays} />
          </div>

          <div className="mt-8 flex flex-wrap gap-x-8 gap-y-2 text-[0.95rem] font-semibold lg:mt-auto lg:pt-8">
            <Link href="/methods" className="link">How the simulation works →</Link>
            {notes[0] && <Link href={`/lab-notes/${notes[0].n}`} className="link">Lab note {notes[0].n} →</Link>}
          </div>
        </div>
        <VoterField className="h-[340px] sm:h-[420px] lg:h-auto" />
      </section>
      <SwingBand className="-mx-4 h-[3px] sm:-mx-6" />

      <Reveal as="section" className="mt-14">
        <p className="label">How it works</p>
        <h2 className="mt-2 max-w-3xl text-[1.9rem] font-extrabold leading-tight tracking-[-0.02em]">
          Polls ask people. We simulate how people react.
        </h2>
        <ol className="mt-8 grid gap-8 md:grid-cols-3 md:gap-10">
          {STEPS.map((s, i) => (
            <li key={s.q} className="border-t-2 border-rule-strong pt-4">
              <p className="text-[0.72rem] font-bold uppercase tracking-[0.08em] text-muted">{`Step ${i + 1}`}</p>
              <p className="mt-1 text-[1.25rem] font-bold leading-snug tracking-[-0.01em]">{s.q}</p>
              <p className="mt-3 leading-relaxed text-ink-2">
                <strong className="font-semibold text-ink">{s.a}</strong> {s.b}
              </p>
            </li>
          ))}
        </ol>
      </Reveal>

      <Reveal as="section" className="mt-16 grid gap-10 border-t-[3px] border-rule-strong pt-6 lg:grid-cols-[1fr_1.3fr]">
        <div>
          <p className="label">Scored in public</p>
          <h2 className="mt-2 text-[1.9rem] font-extrabold leading-tight tracking-[-0.02em]">Every number, beside the benchmarks.</h2>
          <p className="mt-4 max-w-md text-[1.05rem] leading-relaxed text-ink-2">
            Each forecast sits next to four others, and every Monday from October 19 all of them are scored by the same
            rules. The misses get published too. Where states publish early-vote counts, the real counts check the
            simulated turnout.
          </p>
          <Link href="/track-record" className="link mt-5 inline-block font-semibold">How scoring works →</Link>
        </div>
        <table className="w-full self-start border-collapse text-[0.95rem]">
          <thead>
            <tr className="border-y-2 border-rule-strong text-left text-[0.7rem] font-bold uppercase tracking-[0.06em]">
              <th className="py-2 pr-4">Forecast</th>
              <th className="py-2">What it is</th>
            </tr>
          </thead>
          <tbody>
            {BENCHMARKS.map(([k, v, ours]) => (
              <tr key={k} className="border-b border-rule align-top">
                <th className="whitespace-nowrap py-3 pr-4 text-left font-bold">
                  {ours && <span className="mr-2 inline-block h-2 w-2 bg-sim align-middle" aria-hidden="true" />}
                  {k}
                </th>
                <td className="py-3 text-ink-2">{v}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Reveal>

      <Reveal as="section" className="mt-16 border-t-[3px] border-rule-strong pt-6">
        <p className="label">The road to November 3</p>
        <ol className="relative mt-8 grid gap-6 sm:grid-cols-5 sm:gap-4">
          <span className="absolute left-[5px] top-2 bottom-2 w-px bg-rule sm:left-0 sm:right-0 sm:top-[5px] sm:bottom-auto sm:h-px sm:w-auto" aria-hidden="true" />
          {TIMELINE.map((s) => (
            <li key={s.d} className="relative pl-7 sm:pl-0 sm:pt-7">
              <span
                className={`absolute left-0 top-1 h-[11px] w-[11px] sm:top-0 ${s.hot ? "bg-sim" : "border-2 border-ink bg-paper"}`}
                aria-hidden="true"
              />
              <p className={`text-[0.78rem] font-bold uppercase tracking-[0.07em] ${s.hot ? "text-sim" : "text-muted"}`}>{s.d}</p>
              <p className="mt-1 font-bold leading-snug">{s.t}</p>
              <p className="mt-1 text-[0.9rem] leading-relaxed text-ink-2">{s.b}</p>
            </li>
          ))}
        </ol>
      </Reveal>

      <Reveal as="section" className="mt-16 grid gap-10 border-t-[3px] border-rule-strong pt-6 lg:grid-cols-[1fr_1.15fr]">
        <div>
          <p className="label">The map</p>
          <h2 className="mt-2 text-[1.9rem] font-extrabold leading-tight tracking-[-0.02em]">35 Senate seats are up.</h2>
          <p className="mt-4 max-w-md text-[1.05rem] leading-relaxed text-ink-2">
            {`Republicans hold ${held.R} of them and Democrats ${held.D}. Republicans need 50 seats to keep the chamber, with the Vice President's tie-break. From October 12, every square gets a forecast.`}
          </p>
        </div>
        <div>
          <TileMap tiles={tiles} />
          <div className="mt-3 flex flex-wrap items-center justify-between gap-2">
            <Legend items={[
              { fill: "var(--rep)", label: "Held by Republicans" },
              { fill: "var(--dem)", label: "Held by Democrats" },
              { fill: "var(--paper)", label: "No race", border: true },
            ]} />
            <p className="note">A dot marks a special election.</p>
          </div>
        </div>
      </Reveal>

      <Reveal as="section" className="mt-16 border-t-[3px] border-rule-strong pt-6">
        <details className="group">
          <summary className="flex cursor-pointer list-none items-baseline justify-between gap-4">
            <span>
              <span className="label">The races</span>
              <span className="mt-2 block text-[1.9rem] font-extrabold leading-tight tracking-[-0.02em]">Who is running</span>
            </span>
            <span className="shrink-0 text-sm font-semibold underline underline-offset-4 group-open:hidden">Show all 35</span>
            <span className="hidden shrink-0 text-sm font-semibold underline underline-offset-4 group-open:inline">Hide</span>
          </summary>
          <table className="mt-5 w-full border-collapse text-[0.92rem]">
            <thead>
              <tr className="border-y-2 border-rule-strong text-left text-[0.7rem] font-bold uppercase tracking-[0.06em]">
                <th className="py-2 pr-3">State</th>
                <th className="py-2 pr-3">Candidates</th>
                <th className="hidden py-2 lg:table-cell">Status</th>
              </tr>
            </thead>
            <tbody>
              {races.map(({ id, m }) => (
                <tr key={id} className="border-b border-rule align-top transition-colors hover:bg-paper-2">
                  <td className="py-2.5 pr-3 font-bold">{raceTitle(m)}</td>
                  <td className="py-2.5 pr-3">
                    <span style={{ color: PARTY[m.left_party] }}>{`${m.candidates.left} (${m.left_party})`}</span>
                    <span className="text-muted"> vs. </span>
                    <span style={{ color: "var(--rep)" }}>{`${m.candidates.right} (R)`}</span>
                  </td>
                  <td className="hidden py-2.5 text-ink-2 lg:table-cell">{m.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="note mt-3">Candidates as nominated or expected; updated as primaries and appointments settle.</p>
        </details>
      </Reveal>

      {notes.length > 0 && (
        <Reveal as="section" className="mt-16 border-t-[3px] border-rule-strong pt-6">
          <div className="flex items-baseline justify-between gap-4">
            <p className="label">Lab notes</p>
            <Link href="/lab-notes" className="text-sm font-semibold underline underline-offset-4">All notes</Link>
          </div>
          <ul className="mt-4">
            {notes.map((n) => (
              <li key={n.n} className="border-b border-rule">
                <Link href={`/lab-notes/${n.n}`} className="group flex items-baseline gap-4 py-4">
                  <span className="label-muted w-20 shrink-0">Note {n.n}</span>
                  <span className="text-lg font-semibold group-hover:underline">{n.title}</span>
                </Link>
              </li>
            ))}
          </ul>
        </Reveal>
      )}

      <Reveal as="section" className="mt-16 grid gap-6 border-t-[3px] border-rule-strong pt-6 md:grid-cols-[1fr_1fr]">
        <div>
          <p className="label">Follow the build</p>
          <p className="mt-2 max-w-md text-[1.05rem] leading-relaxed text-ink-2">
            Lab notes go out from October 3: what we tested, what failed, what we changed. Then the forecasts, every day.
          </p>
        </div>
        <ul className="self-end text-[0.95rem] font-semibold">
          {social.map((s) => (
            <li key={s.name} className="border-b border-rule">
              <a href={s.url} rel="noopener" target="_blank" className="flex justify-between py-3 hover:text-sim">
                <span>{s.name}</span>
                <span className="font-normal text-ink-2">{s.handle} →</span>
              </a>
            </li>
          ))}
          <li className="border-b border-rule">
            <a href="mailto:hello@notapoll.org" className="flex justify-between py-3 hover:text-sim">
              <span>Email</span>
              <span className="font-normal text-ink-2">hello@notapoll.org →</span>
            </a>
          </li>
        </ul>
      </Reveal>
    </div>
  );
}
