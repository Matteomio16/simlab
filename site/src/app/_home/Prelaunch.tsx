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
    k: "1 · Where each race starts",
    t: "Real statistics",
    b: "Past results, the economy and the poll average set every race's starting line. The simulation never invents it.",
    c: "var(--dem)",
  },
  {
    k: "2 · How the news moves it",
    t: "Synthetic voters react",
    b: "Synthetic voters, built from real data on how groups of Americans vote, react to each day's events. Only those who could still change their mind, or still decide whether to vote, move the numbers, and every story fades.",
    c: "var(--sim)",
  },
  {
    k: "3 · Who wins, and how often",
    t: "40,000 simulated elections",
    b: "Each race is played out 40,000 times a day. The share a candidate wins is their chance: between 35 and 65 in 100 is a toss-up.",
    c: "var(--rep)",
  },
];

const BENCHMARKS = ["Poll average", "Prediction markets", "Cook Political Report", "Statistics only, no simulation"];

const TIMELINE = [
  { d: "Oct 3", t: "The making-of begins", b: "Lab notes: what we tested, what failed, what we changed." },
  { d: "Oct 5–11", t: "Private rehearsal", b: "The full daily run, five states, nothing published." },
  { d: "Oct 12", t: "Forecasts go public", b: "All 35 Senate races, updated every day.", hot: true },
  { d: "Oct 19", t: "First public score", b: "Then every Monday, good weeks and bad." },
  { d: "Nov 3", t: "Election Day", b: "The final forecast, then the results decide." },
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
    <>
      <section className="border-b border-rule">
        <div className="mx-auto grid max-w-[1200px] gap-10 px-4 pb-12 pt-10 sm:px-6 sm:pt-14 lg:grid-cols-[1fr_1.05fr] lg:gap-14">
          <div className="rise">
            <p className="label">Democracy, rehearsed.</p>
            <h1 className="mt-4 text-[2.6rem] font-extrabold leading-[1.02] tracking-[-0.025em] sm:text-[3.6rem]">
              The 2026 midterms,
              <br />
              <span className="text-sim">simulated every day.</span>
            </h1>
            <p className="mt-5 max-w-xl text-[1.2rem] leading-relaxed text-ink-2">
              Synthetic voters react to each day&rsquo;s news, and 40,000 simulated elections turn their reactions into
              chances for all 35 Senate races.
            </p>
            <p className="mt-3 text-[1.05rem] font-bold">Not a poll. Nobody was asked anything.</p>
            <div className="mt-8">
              <p className="label-muted">Forecasts go public October 12</p>
              <div className="mt-2">
                <Countdown to={LAUNCH} initialDays={initialDays} />
              </div>
            </div>
            <div className="mt-8 flex flex-wrap items-center gap-x-6 gap-y-3 text-[0.95rem] font-semibold">
              <Link href="/methods" className="bg-ink px-4 py-2.5 text-white transition-colors hover:bg-sim">
                How it works
              </Link>
              {notes[0] ? (
                <Link href={`/lab-notes/${notes[0].n}`} className="link">Read the first Lab note</Link>
              ) : (
                <Link href="/lab-notes" className="link">Lab notes from Oct 3</Link>
              )}
            </div>
          </div>
          <VoterField className="h-[340px] sm:h-[420px] lg:h-auto" />
        </div>
        <SwingBand className="h-[3px]" />
      </section>

      <div className="mx-auto max-w-[1200px] px-4 sm:px-6">
        <Reveal as="section" className="mt-16">
          <p className="label">How it works</p>
          <h2 className="mt-2 max-w-3xl text-[2rem] font-extrabold leading-tight tracking-[-0.02em]">
            Polls ask people. We simulate how people react.
          </h2>
          <div className="mt-8 grid gap-4 md:grid-cols-3">
            {STEPS.map((d) => (
              <div key={d.k} className="card p-6">
                <div className="h-[3px] w-10" style={{ background: d.c }} />
                <p className="label-muted mt-4">{d.k}</p>
                <p className="mt-2 text-[1.25rem] font-bold leading-snug tracking-[-0.01em]">{d.t}</p>
                <p className="mt-3 leading-relaxed text-ink-2">{d.b}</p>
              </div>
            ))}
          </div>
        </Reveal>

        <Reveal as="section" className="mt-16 grid gap-10 border-t-[3px] border-rule-strong pt-6 lg:grid-cols-[1fr_1.1fr]">
          <div>
            <p className="label">Scored in public</p>
            <h2 className="mt-2 text-[2rem] font-extrabold leading-tight tracking-[-0.02em]">Every number, beside the benchmarks.</h2>
            <p className="mt-4 max-w-md text-[1.05rem] leading-relaxed text-ink-2">
              Each forecast sits next to four others, and every Monday from October 19 all of them are scored by the same
              rules. The misses get published too.
            </p>
            <Link href="/track-record" className="link mt-5 inline-block font-semibold">How scoring works</Link>
          </div>
          <div className="grid grid-cols-2 gap-px self-start border border-rule bg-rule">
            <div className="col-span-2 bg-paper p-5">
              <p className="label-muted">Our social simulation</p>
              <p className="mt-2 text-[2.2rem] font-extrabold leading-none text-sim">Oct 12</p>
            </div>
            {BENCHMARKS.map((b) => (
              <div key={b} className="bg-paper p-5">
                <p className="label-muted">{b}</p>
                <p className="mt-2 text-[1.4rem] font-bold leading-none text-ink-2">Side by side</p>
              </div>
            ))}
          </div>
        </Reveal>

        <Reveal as="section" className="mt-16 border-t-[3px] border-rule-strong pt-6">
          <p className="label">The road to November 3</p>
          <ol className="mt-6 grid gap-px border border-rule bg-rule sm:grid-cols-5">
            {TIMELINE.map((s) => (
              <li key={s.d} className={`p-5 ${s.hot ? "bg-ink text-white" : "bg-paper"}`}>
                <p className={`text-[0.78rem] font-bold uppercase tracking-[0.07em] ${s.hot ? "text-[#c9b4ee]" : "text-sim"}`}>{s.d}</p>
                <p className="mt-2 font-bold leading-snug">{s.t}</p>
                <p className={`mt-1 text-[0.9rem] leading-relaxed ${s.hot ? "text-white/75" : "text-ink-2"}`}>{s.b}</p>
              </li>
            ))}
          </ol>
        </Reveal>

        <Reveal as="section" className="mt-16 grid gap-10 border-t-[3px] border-rule-strong pt-6 lg:grid-cols-[1fr_1.15fr]">
          <div>
            <p className="label">The map</p>
            <h2 className="mt-2 text-[2rem] font-extrabold leading-tight tracking-[-0.02em]">35 Senate seats are up.</h2>
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
                <span className="mt-2 block text-[2rem] font-extrabold leading-tight tracking-[-0.02em]">Who is running</span>
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
      </div>

      <Reveal as="section" className="mx-auto mt-16 max-w-[1200px] px-4 sm:px-6">
        <div className="bg-navy px-6 py-10 text-navy-fg sm:px-10">
          <p className="text-[0.72rem] font-bold uppercase tracking-[0.08em] text-[#c9b4ee]">Follow the build</p>
          <p className="mt-3 max-w-2xl text-[1.8rem] font-extrabold leading-tight tracking-[-0.02em] text-white">
            Watch the simulation being built, then watch it get scored.
          </p>
          <div className="mt-6 flex flex-wrap gap-3 text-[0.95rem] font-semibold">
            {social.map((s) => (
              <a key={s.name} href={s.url} rel="noopener" target="_blank" className="bg-white px-4 py-2.5 text-ink transition-colors hover:bg-[#c9b4ee]">
                {`${s.name} ${s.handle}`}
              </a>
            ))}
            <a href="mailto:hello@notapoll.org" className="border border-white/40 px-4 py-2.5 text-white transition-colors hover:border-white">
              hello@notapoll.org
            </a>
          </div>
        </div>
      </Reveal>
    </>
  );
}
