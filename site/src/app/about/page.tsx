import type { Metadata } from "next";
import { SITE } from "@/lib/site";
import Dateline from "@/components/Dateline";

export const metadata: Metadata = {
  title: "About",
  description: "NotAPoll.org is a live experiment in independent, transparent election forecasting, scored in public.",
};

// The about page in one breath (communication guide, 1 Oct): what we want, how we do it, and that it is a live
// experiment scored in public. "We" throughout; nobody's personal story.
const PARTS = [
  {
    k: "What we want",
    t: "Forecasting that is independent, transparent and built on human reactions: how the news moves different groups of voters. Polls can be biased or inaccurate; we show where and why our engine sees something different.",
  },
  {
    k: "How we do it",
    t: "Voter personas built from real survey answers, one for each voter group in each state, react to the day's news. Every race is then played out 40,000 times.",
  },
  {
    k: "How you can check",
    t: "It is a live experiment, and you can follow its progress on our map, updated every day from October 12, race by race. Every forecast is scored in public every Monday from October 19, against the same benchmarks, right or wrong.",
  },
];

export default function About() {
  return (
    <div className="mx-auto max-w-[1200px] px-4 pt-10 sm:px-6 sm:pt-12">
      <Dateline left="About" />
      <h1 className="mt-6 max-w-4xl text-[2.2rem] font-extrabold leading-[1.08] tracking-[-0.022em] sm:text-[2.9rem]">
        A live experiment in forecasting elections by how people react.
      </h1>

      <ol className="mt-10 grid gap-8 md:grid-cols-3 md:gap-10">
        {PARTS.map((p) => (
          <li key={p.k} className="border-t-2 border-rule-strong pt-4">
            <p className="text-[0.72rem] font-bold uppercase tracking-[0.08em] text-muted">{p.k}</p>
            <p className="mt-2 text-[1.2rem] font-semibold leading-snug tracking-[-0.01em]">{p.t}</p>
          </li>
        ))}
      </ol>

      <section className="mt-16 grid gap-10 border-t-[3px] border-rule-strong pt-6 lg:grid-cols-[1fr_1.4fr]">
        <div>
          <p className="label">Fair to every side</p>
          <h2 className="mt-2 text-[1.6rem] font-extrabold leading-tight tracking-[-0.02em]">
            We show what the engine sees, and why. You judge.
          </h2>
        </div>
        <ul className="divide-y divide-rule border-y border-rule text-[1.02rem] leading-relaxed text-ink-2">
          <li className="py-3">No campaign, party or political group funds, directs or reviews this work.</li>
          <li className="py-3">No paid ads or boosted posts, and no coordination with any campaign.</li>
          <li className="py-3">We never take sides. Where our numbers differ from others, we show where and why.</li>
          <li className="py-3">Prediction markets are shown beside every forecast, and never feed into it.</li>
          <li className="py-3">When a part of the engine doesn&rsquo;t work, we say so, and say what we changed.</li>
        </ul>
      </section>

      <section className="mt-16 grid gap-10 border-t-[3px] border-rule-strong pt-6 lg:grid-cols-[1fr_1.4fr]">
        <div>
          <p className="label">Who we are</p>
          <h2 className="mt-2 text-[1.6rem] font-extrabold leading-tight tracking-[-0.02em]">A small, independent lab.</h2>
        </div>
        <div className="max-w-[640px] text-[1.02rem] leading-relaxed text-ink-2">
          <p>
            Our work is built on long-term research focused on social dynamics. NotAPoll.org is published by{" "}
            <a href={SITE.studio.url} className="link font-semibold text-ink">{SITE.studio.name}</a>. The name says what this
            is: not a poll. We don&rsquo;t ask people what they think today; we model how they react.
          </p>
          <p className="mt-4">
            Corrections, questions and press:{" "}
            <a href="mailto:hello@notapoll.org" className="link font-semibold text-ink">hello@notapoll.org</a>
          </p>
        </div>
      </section>
    </div>
  );
}
