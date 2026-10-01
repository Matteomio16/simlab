import type { Metadata } from "next";
import { SITE } from "@/lib/site";

export const metadata: Metadata = {
  title: "About",
  description: "Who makes NotAPoll.org, and how it stays independent.",
};

export default function About() {
  return (
    <div className="mx-auto max-w-[1200px] px-4 pt-10 sm:px-6 sm:pt-12">
      <p className="label">About</p>
      <h1 className="mt-3 max-w-3xl text-[2.3rem] font-extrabold leading-[1.08] tracking-[-0.02em] sm:text-[2.9rem]">
        An independent research project
      </h1>
      <div className="mt-8 border-t-[3px] border-rule-strong pt-6">
        <div className="prose-np max-w-[680px]">
          <p>
            NotAPoll.org is a social simulation of the 2026 US midterm elections. It tests one question in public: can
            simulating how people react to the news add something to a forecast built from polls and past results?
          </p>
          <p>
            It is built by <strong>Matteo Mio</strong>, a student of economics and politics at the London School of
            Economics, and published by <a href={SITE.studio.url}>{SITE.studio.name}</a>. Its misses will be published
            too.
          </p>
          <h2>Independence</h2>
          <ul>
            <li>No campaign, party or political group funds, directs or reviews this work.</li>
            <li>No paid ads or boosted posts, and no coordination with any campaign.</li>
            <li>Prediction markets are shown as a benchmark and never feed into the forecast.</li>
          </ul>
          <h2>The name</h2>
          <p>
            Simulation results get reported as polls once they travel without their caption. The name carries the
            caption: these are voter personas and simulated elections. Nobody real was asked anything.
          </p>
          <h2>Contact</h2>
          <p>
            Corrections, questions and press: <a href="mailto:hello@notapoll.org">hello@notapoll.org</a>.
          </p>
        </div>
      </div>
    </div>
  );
}
