import type { Metadata } from "next";
import Reveal from "@/components/Reveal";
import { inline, toHtml } from "@/lib/markdown";
import { listItems, loadMethods, splitBold, type Section } from "@/lib/methods";

export const metadata: Metadata = {
  title: "Methods",
  description: "How the NotAPoll.org social simulation works: starting levels, synthetic voters, news reactions, the weekly filter and simulated elections.",
};

// Key figures, each stated in the methods text below (content/methods.md).
const FACTS = [
  { n: "40,000", label: "simulated elections a day", color: "var(--sim)" },
  { n: "28", label: "synthetic voter groups in every race", color: "var(--dem)" },
  { n: "5.5 days", label: "half-life of a news story", color: "var(--rep)" },
  { n: "80%", label: "most weight polls ever get", color: "var(--ink)" },
  { n: "45", label: "past events that set reaction sizes", color: "var(--sim)" },
  { n: "0.25", label: "least correlation between Senate races", color: "var(--dem)" },
];

const html = (md: string) => ({ __html: toHtml(md) });

function Steps({ s }: { s: Section }) {
  const { items } = listItems(s.body);
  return (
    <ol className="mt-6 grid gap-px overflow-hidden border border-rule bg-rule sm:grid-cols-2 lg:grid-cols-4">
      {items.map((it, i) => {
        const { title, body } = splitBold(it);
        return (
          <li key={i} className="relative bg-paper p-5">
            <span className="flex h-8 w-8 items-center justify-center bg-ink text-sm font-bold text-white">{i + 1}</span>
            <p className="mt-4 font-bold leading-snug text-ink" dangerouslySetInnerHTML={{ __html: inline(title) }} />
            <p className="mt-2 text-[0.95rem] leading-relaxed text-ink-2" dangerouslySetInnerHTML={{ __html: inline(body) }} />
          </li>
        );
      })}
    </ol>
  );
}

function Cards({ s }: { s: Section }) {
  const { before, items, after } = listItems(s.body);
  return (
    <>
      {before && <div className="prose-np mt-4 max-w-3xl" dangerouslySetInnerHTML={html(before)} />}
      <ul className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {items.map((it, i) => {
          const { title, body } = splitBold(it);
          return (
            <li key={i} className="card p-5">
              <p className="text-lg font-bold text-ink" dangerouslySetInnerHTML={{ __html: inline(title) }} />
              <p className="mt-2 text-[0.95rem] leading-relaxed text-ink-2" dangerouslySetInnerHTML={{ __html: inline(body) }} />
            </li>
          );
        })}
      </ul>
      {after && <div className="prose-np mt-6 max-w-3xl" dangerouslySetInnerHTML={html(after)} />}
    </>
  );
}

// A two-column row: the title stays in view on the left while its text scrolls on the right.
function Row({ index, title, id, children }: { index: string; title: string; id: string; children: React.ReactNode }) {
  return (
    <div id={id} className="grid scroll-mt-24 gap-3 border-t border-rule py-8 lg:grid-cols-[260px_1fr] lg:gap-12">
      <div>
        <div className="lg:sticky lg:top-8">
          <p className="text-[0.75rem] font-bold tracking-[0.06em] text-sim">{index}</p>
          <h3 className="mt-1 text-[1.2rem] font-bold leading-snug tracking-[-0.01em] text-ink">{title}</h3>
        </div>
      </div>
      <div className="prose-np max-w-[700px]">{children}</div>
    </div>
  );
}

export default function Methods() {
  const { lede, sections } = loadMethods();
  return (
    <div className="mx-auto max-w-[1200px] px-4 pt-10 sm:px-6 sm:pt-12">
      <header className="rise">
        <p className="label">Methods</p>
        <h1 className="mt-3 max-w-3xl text-[2.3rem] font-extrabold leading-[1.06] tracking-[-0.02em] sm:text-[3rem]">
          How the simulation works
        </h1>
        <div className="mt-5 max-w-3xl text-[1.15rem] leading-relaxed text-ink-2 [&_strong]:font-semibold [&_strong]:text-ink" dangerouslySetInnerHTML={html(lede)} />
      </header>

      <section aria-label="Key figures" className="mt-10 grid grid-cols-2 gap-px border border-rule bg-rule sm:grid-cols-3 lg:grid-cols-6">
        {FACTS.map((f) => (
          <div key={f.label} className="bg-paper p-4">
            <div className="h-[3px] w-8" style={{ background: f.color }} />
            <p className="mt-3 text-[1.7rem] font-extrabold leading-none tracking-[-0.02em] text-ink">{f.n}</p>
            <p className="mt-2 text-[0.8rem] leading-snug text-ink-2">{f.label}</p>
          </div>
        ))}
      </section>

      <nav aria-label="On this page" className="mt-8 flex flex-wrap gap-x-6 gap-y-2 text-[0.9rem] font-semibold">
        {sections.map((s) => (
          <a key={s.id} href={`#${s.id}`} className="text-ink-2 hover:text-ink hover:underline">
            {s.title.replace(", in four steps", "")}
          </a>
        ))}
      </nav>

      {sections.map((s, i) => {
        const n = String(i + 1).padStart(2, "0");
        const steps = /^How it works/i.test(s.title);
        const cards = /^Models/i.test(s.title);
        return (
          <Reveal as="section" key={s.id} className="mt-16">
            <div id={s.id} className="scroll-mt-24 border-t-[3px] border-rule-strong pt-3">
              <p className="text-[0.75rem] font-bold tracking-[0.06em] text-sim">{n}</p>
              <h2 className="mt-1 text-[1.75rem] font-extrabold leading-tight tracking-[-0.015em]">{s.title}</h2>
            </div>
            {steps ? (
              <Steps s={s} />
            ) : cards ? (
              <Cards s={s} />
            ) : s.subs.length ? (
              <>
                {s.body && <div className="prose-np mt-4 max-w-3xl" dangerouslySetInnerHTML={html(s.body)} />}
                <div className="mt-4">
                  {s.subs.map((sub, j) => (
                    <Row key={sub.id} index={`${n}.${j + 1}`} title={sub.title} id={sub.id}>
                      <div dangerouslySetInnerHTML={html(sub.body)} />
                    </Row>
                  ))}
                </div>
              </>
            ) : (
              <div className="prose-np mt-5 max-w-[760px]" dangerouslySetInnerHTML={html(s.body)} />
            )}
          </Reveal>
        );
      })}
    </div>
  );
}
