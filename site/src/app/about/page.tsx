import type { Metadata } from "next";
import { SITE } from "@/lib/site";

export const metadata: Metadata = {
  title: "About",
  description: "Who makes NotAPoll.org, and how it stays independent.",
};

export default function About() {
  return (
    <div className="mx-auto max-w-3xl px-4 pt-12 sm:px-6 sm:pt-16">
      <p className="kicker">About</p>
      <h1 className="mt-3 font-serif text-4xl leading-tight text-ink sm:text-5xl">An independent research project</h1>
      <div className="prose-lab mt-8">
        <p>
          NotAPoll.org is a social simulation of the 2026 US midterm elections. It tests one question in public: can
          simulating how people react to the news add something to a forecast built from polls and past results?
        </p>
        <p>
          It is built by <strong>Matteo Mio</strong>, a student of economics and politics at the London School of
          Economics, and published by <a href={SITE.studio.url}>{SITE.studio.name}</a>. An earlier simulation of
          Hungary&rsquo;s April 2026 election called the winner but badly missed the size of the win. This project is
          designed around that lesson, and its misses will be published too.
        </p>
        <h2>Independence</h2>
        <ul>
          <li>No campaign, party or political group funds, directs or reviews this work.</li>
          <li>No paid ads or boosted posts. Nothing here coordinates with any campaign.</li>
          <li>The prediction markets are shown as a benchmark and never feed into the forecast.</li>
        </ul>
        <h2>The name</h2>
        <p>
          Simulation results get reported as polls once they travel without their caption. The name carries the caption:
          these are synthetic voters and simulated elections. Nobody real was asked anything.
        </p>
        <h2>Contact</h2>
        <p>
          Corrections, questions and press: <a href="mailto:hello@notapoll.org">hello@notapoll.org</a>.
        </p>
      </div>
    </div>
  );
}
