import type { ReactNode } from "react";

// The evidence beside each claim on the methods page. Every figure shows a rule or a fitted number from the method,
// never forecast data.

function Figure({ title, note, children }: { title: string; note?: string; children: ReactNode }) {
  return (
    <figure className="border-t-2 border-rule-strong pt-3">
      <figcaption className="text-[0.8rem] font-bold text-ink">{title}</figcaption>
      <div className="mt-4">{children}</div>
      {note && <p className="note mt-3">{note}</p>}
    </figure>
  );
}

function Blend() {
  const rows: [string, number][] = [
    ["A heavily polled race", 80],
    ["A race with no polls", 0],
  ];
  return (
    <Figure title="How much the polls can count in a race's starting line" note="The weight in between follows how many recent polls a race has.">
      <div className="space-y-4">
        {rows.map(([label, p]) => (
          <div key={label}>
            <p className="text-[0.85rem] text-ink-2">{label}</p>
            <div className="mt-1.5 flex h-7 gap-[2px]">
              {p > 0 && <div className="h-full bg-sim" style={{ width: `${p}%` }} title={`Polls: ${p}%`} />}
              <div className="h-full flex-1 bg-[var(--ind-3)]" title={`Fundamentals: ${100 - p}%`} />
            </div>
            <div className="mt-1 flex justify-between text-[0.78rem] font-semibold tabular-nums">
              <span className={p ? "text-ink" : "text-muted"}>{`Polls ${p}%`}</span>
              <span className="text-ink-2">{`Fundamentals ${100 - p}%`}</span>
            </div>
          </div>
        ))}
      </div>
    </Figure>
  );
}

const PARTY_ID: [string, string][] = [
  ["Strong Democrat", "var(--dem-1)"],
  ["Democrat", "var(--dem-2)"],
  ["Lean Democrat", "var(--dem-3)"],
  ["Independent", "var(--ind-3)"],
  ["Lean Republican", "var(--rep-3)"],
  ["Republican", "var(--rep-2)"],
  ["Strong Republican", "var(--rep-1)"],
];
const COLS = ["White, degree", "White, no degree", "Not white, degree", "Not white, no degree"];

function Groups() {
  return (
    <Figure title="The 28 voter groups in every state" note="Each group has its own voter persona, with its own size, turnout and party split in each state.">
      <div className="grid grid-cols-[auto_repeat(4,minmax(0,1fr))] items-center gap-[2px] text-[0.72rem]">
        <span />
        {COLS.map((c) => (
          <span key={c} className="pb-1 text-center font-semibold leading-tight text-ink-2">{c}</span>
        ))}
        {PARTY_ID.map(([p, fill]) => (
          <div key={p} className="contents">
            <span className="pr-3 text-right font-semibold text-ink-2">{p}</span>
            {COLS.map((c) => (
              <span key={c} className="block h-6" style={{ background: fill }} title={`${p}, ${c.toLowerCase()}`} />
            ))}
          </div>
        ))}
      </div>
    </Figure>
  );
}

function Movable() {
  return (
    <Figure title="How far one story can reach">
      <dl className="grid grid-cols-2 border-y border-rule">
        <div className="py-4 pr-4">
          <dt className="text-[0.78rem] font-semibold leading-snug text-muted">The most one story can move, of the voters who can still move</dt>
          <dd className="mt-2 text-[2.2rem] font-extrabold leading-none tracking-[-0.02em]">1 in 5</dd>
        </div>
        <div className="border-l border-rule py-4 pl-4">
          <dt className="text-[0.78rem] font-semibold leading-snug text-muted">Past events with measured shifts in opinion that set this scale</dt>
          <dd className="mt-2 text-[2.2rem] font-extrabold leading-none tracking-[-0.02em]">45</dd>
        </div>
      </dl>
    </Figure>
  );
}

function Fade() {
  const W = 480, H = 200, L = 36, R = 12, T = 12, B = 30, days = 21, half = 5.5;
  const x = (d: number) => L + (d / days) * (W - L - R);
  const y = (v: number) => T + (1 - v) * (H - T - B);
  const pts = Array.from({ length: 85 }, (_, i) => (i / 84) * days);
  const path = pts.map((d, i) => `${i ? "L" : "M"}${x(d).toFixed(1)},${y(0.5 ** (d / half)).toFixed(1)}`).join("");
  const marks = [7, 14, 21];
  return (
    <Figure title="Share of a story's effect left, by days since it first appeared" note="Half-life 5.5 days. A one-off story that leaves the news drops faster.">
      <svg viewBox={`0 0 ${W} ${H}`} className="h-auto w-full" role="img" aria-label="Fade curve: 41% left after 7 days, 17% after 14, 7% after 21">
        {[0, 0.5, 1].map((v) => (
          <g key={v}>
            <line x1={L} x2={W - R} y1={y(v)} y2={y(v)} stroke="var(--rule)" />
            <text x={L - 6} y={y(v) + 4} textAnchor="end" fill="var(--muted)" style={{ fontSize: 11 }}>{`${v * 100}%`}</text>
          </g>
        ))}
        {[0, 7, 14, 21].map((d) => (
          <text key={d} x={x(d)} y={H - 10} textAnchor="middle" fill="var(--muted)" style={{ fontSize: 11 }}>{d === 0 ? "Day 0" : `${d}`}</text>
        ))}
        <path d={path} fill="none" stroke="var(--sim)" strokeWidth={2} />
        {marks.map((d) => {
          const v = 0.5 ** (d / half);
          return (
            <g key={d}>
              <circle cx={x(d)} cy={y(v)} r={4.5} fill="var(--sim)" stroke="var(--paper)" strokeWidth={2}>
                <title>{`Day ${d}: ${Math.round(v * 100)}% left`}</title>
              </circle>
              <text x={x(d)} y={y(v) - 10} textAnchor="middle" fill="var(--ink)" style={{ fontSize: 12, fontWeight: 700 }}>{`${Math.round(v * 100)}%`}</text>
            </g>
          );
        })}
      </svg>
    </Figure>
  );
}

function Layers() {
  const rows: [string, string][] = [
    ["National", "Shared by every race, including polls missing the same way nationwide: about 3 points on its own."],
    ["Regional", "Shared by states in the same census division."],
    ["State", "Shared by every race in a state."],
    ["Race", "Each race's own, which takes the rest."],
  ];
  return (
    <Figure title="Where a simulated election's errors come from">
      <ol className="space-y-[2px]">
        {rows.map(([k, v], i) => (
          <li key={k} className="bg-paper-2 py-2.5 pr-3" style={{ marginLeft: `${i * 6}%`, paddingLeft: "0.75rem", borderLeft: "3px solid var(--ink)" }}>
            <p className="text-[0.85rem] font-bold">{k}</p>
            <p className="text-[0.82rem] leading-snug text-ink-2">{v}</p>
          </li>
        ))}
      </ol>
    </Figure>
  );
}

const BENCH: [string, string, boolean?][] = [
  ["Our social simulation", "Statistics plus voter personas, checked every Monday.", true],
  ["Statistics only", "Our twin: the same model with the voter personas switched off. The number to beat."],
  ["Poll average", "The average of published polls in each race."],
  ["Prediction markets", "Kalshi and Polymarket prices, averaged. Never an input."],
  ["Cook Political Report", "Expert race ratings. Never an input."],
];

const MODELS: [string, string, string][] = [
  ["Labels each day's news: is it about this race, and what kind of event is it", "Jev, a decision model", "Said \"no change\" to 99% of irrelevant stories, and flipped most cleanly when the parties were swapped."],
  ["Writes the short, neutral summary of each story", "DeepSeek V4.1 Flash", "Neutral, short summaries at the lowest cost."],
  ["Gives each persona's reaction", "GLM-5.3 Flash", "Ranked 19 real events best of all models tested, with the right direction on every one that moved opinion."],
  ["Sets each voter group's party split", "Kev, fine-tuned by us", "Trained on real survey answers, so its numbers mean shares of people, not confidence."],
  ["Explains, every Monday, why a state surprised us", "MiMo-V2.6-Pro", "Writes the weekly audit. Never changes a number."],
  ["Spot-checks reactions and labels", "GPT-6 Luna", "An independent second reader."],
];

function Table({ head, rows, boldFirst = true }: { head: string[]; rows: ReactNode[][]; boldFirst?: boolean }) {
  return (
    <table className="w-full border-collapse text-[0.9rem]">
      <thead>
        <tr className="border-y-2 border-rule-strong text-left text-[0.7rem] font-bold uppercase tracking-[0.06em]">
          {head.map((h) => (
            <th key={h} className="py-2 pr-4">{h}</th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.map((r, i) => (
          <tr key={i} className="border-b border-rule align-top">
            {r.map((c, j) => (
              <td key={j} className={`py-3 pr-4 ${j === 0 && boldFirst ? "font-bold text-ink" : "text-ink-2"}`}>{c}</td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function Benchmarks() {
  return (
    <Table
      head={["Forecast", "What it is"]}
      rows={BENCH.map(([k, v, ours]) => [
        <span key={k} className="whitespace-nowrap">
          {ours && <span className="mr-2 inline-block h-2 w-2 bg-sim align-middle" aria-hidden="true" />}
          {k}
        </span>,
        v,
      ])}
    />
  );
}

function Models() {
  return <Table boldFirst={false} head={["Job", "Model", "Why this one"]} rows={MODELS.map(([a, b, c]) => [a, <span key={b} className="whitespace-nowrap font-semibold text-ink">{b}</span>, c])} />;
}

export const FIGURES: Record<string, () => ReactNode> = {
  blend: Blend,
  groups: Groups,
  movable: Movable,
  fade: Fade,
  layers: Layers,
  benchmarks: Benchmarks,
  models: Models,
};
// Tables read better across the full width than beside a short claim.
export const WIDE = new Set(["benchmarks", "models"]);
