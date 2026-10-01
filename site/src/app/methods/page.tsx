import type { Metadata } from "next";
import Reveal from "@/components/Reveal";
import Dateline from "@/components/Dateline";
import { FIGURES, WIDE } from "@/components/MethodFigures";
import { inline, toHtml } from "@/lib/markdown";
import { listItems, loadMethods, splitBold, type Sub } from "@/lib/methods";

export const metadata: Metadata = {
  title: "Methods",
  description: "How the NotAPoll.org forecast works: statistics set each race's starting line, voter personas built from real survey answers react to the news, and every race is played out 40,000 times.",
};

// Layered, as Matteo asked (1 Oct): each claim in a few plain lines with its evidence beside it, the full method in an
// "In detail" fold underneath. The text lives in content/methods.md; {{fig:name}} places a figure from MethodFigures.
const html = (md: string) => ({ __html: toHtml(md) });

function parts(body: string) {
  const [plain, detail = ""] = body.split(/^#### In detail\s*$/m);
  const figs = [...plain.matchAll(/\{\{fig:(\w+)\}\}/g)].map((m) => m[1]);
  return { plain: plain.replace(/\{\{fig:\w+\}\}/g, "").trim(), detail: detail.trim(), figs };
}

function Detail({ md }: { md: string }) {
  return (
    <details className="group mt-5 border-t border-rule">
      <summary className="flex cursor-pointer list-none items-center gap-2 py-3 text-[0.9rem] font-semibold text-ink">
        <span className="inline-block w-3 text-center transition-transform group-open:rotate-90" aria-hidden="true">›</span>
        In detail
      </summary>
      <div className="prose-np max-w-[700px] pb-2 text-[0.95rem]" dangerouslySetInnerHTML={html(md)} />
    </details>
  );
}

function Claim({ sub }: { sub: Sub }) {
  const { plain, detail, figs } = parts(sub.body);
  const side = figs.filter((f) => !WIDE.has(f));
  const wide = figs.filter((f) => WIDE.has(f));
  return (
    <div id={sub.id} className="scroll-mt-24 border-t border-rule py-9">
      <div className={`grid gap-8 ${side.length ? "lg:grid-cols-[1fr_1fr] lg:gap-14" : ""}`}>
        <div className="max-w-[640px]">
          <h3 className="text-[1.45rem] font-extrabold leading-snug tracking-[-0.015em]">{sub.title}</h3>
          <div className="prose-np mt-3 text-[1.05rem]" dangerouslySetInnerHTML={html(plain)} />
          {detail && <Detail md={detail} />}
        </div>
        {side.length > 0 && (
          <div className="space-y-8 lg:pt-1">
            {side.map((f) => {
              const F = FIGURES[f];
              return F ? <F key={f} /> : null;
            })}
          </div>
        )}
      </div>
      {wide.map((f) => {
        const F = FIGURES[f];
        return F ? <div key={f} className="mt-6"><F /></div> : null;
      })}
    </div>
  );
}

function List({ md }: { md: string }) {
  const { items } = listItems(md);
  return (
    <ul className="mt-4 divide-y divide-rule border-y border-rule">
      {items.map((it, i) => {
        const { title, body } = splitBold(it);
        return (
          <li key={i} className="grid gap-1 py-4 lg:grid-cols-[280px_1fr] lg:gap-10">
            {title && <p className="font-bold text-ink" dangerouslySetInnerHTML={{ __html: inline(title) }} />}
            <p className={`leading-relaxed text-ink-2 ${title ? "" : "lg:col-span-2"}`} dangerouslySetInnerHTML={{ __html: inline(body) }} />
          </li>
        );
      })}
    </ul>
  );
}

export default function Methods() {
  const { lede, sections } = loadMethods();
  return (
    <div className="mx-auto max-w-[1200px] px-4 pt-10 sm:px-6 sm:pt-12">
      <header className="rise">
        <Dateline left="Methods" />
        <h1 className="mt-6 max-w-4xl text-[2.3rem] font-extrabold leading-[1.06] tracking-[-0.022em] sm:text-[3rem]">
          How the forecast works
        </h1>
        <div className="mt-5 max-w-3xl text-[1.15rem] leading-relaxed text-ink-2 [&_strong]:font-semibold [&_strong]:text-ink" dangerouslySetInnerHTML={html(lede)} />
        <nav aria-label="On this page" className="mt-8 flex flex-wrap gap-x-6 gap-y-2 border-y-2 border-rule-strong py-3 text-[0.9rem] font-semibold">
          {sections.map((s) => (
            <a key={s.id} href={`#${s.id}`} className="text-ink-2 hover:text-ink hover:underline">{s.title}</a>
          ))}
        </nav>
      </header>

      {sections.map((s) => (
        <Reveal as="section" key={s.id} className="mt-16">
          <h2 id={s.id} className="scroll-mt-24 text-[2rem] font-extrabold leading-tight tracking-[-0.02em]">{s.title}</h2>
          {s.subs.length ? (
            <div className="mt-6">
              {s.subs.map((sub) => <Claim key={sub.id} sub={sub} />)}
            </div>
          ) : (
            <List md={s.body} />
          )}
        </Reveal>
      ))}
    </div>
  );
}
