import { ROOT } from "@/lib/root";
import type { Metadata } from "next";
import { readFileSync } from "node:fs";
import path from "node:path";
import { headings, toHtml } from "@/lib/markdown";

export const metadata: Metadata = {
  title: "Methods",
  description: "How the NotAPoll.org social simulation works: starting levels, synthetic voters, news reactions, the weekly filter and simulated elections.",
};

export default function Methods() {
  const md = readFileSync(path.join(ROOT, "content", "methods.md"), "utf8");
  const title = /^#\s+(.*)$/m.exec(md)?.[1] ?? "How the simulation works";
  const body = md.replace(/^#\s+.*$/m, "");
  const toc = headings(body);
  return (
    <div className="mx-auto max-w-6xl px-4 pt-12 sm:px-6 sm:pt-16">
      <p className="kicker">Methods</p>
      <h1 className="mt-3 max-w-3xl font-serif text-4xl leading-tight text-ink sm:text-5xl">{title}</h1>
      <div className="mt-10 grid gap-12 lg:grid-cols-[1fr_220px]">
        <div className="prose-lab max-w-[68ch]" dangerouslySetInnerHTML={{ __html: toHtml(body) }} />
        <aside className="hidden lg:block">
          <nav aria-label="On this page" className="sticky top-24">
            <p className="kicker">On this page</p>
            <ul className="mt-3 space-y-2 border-l border-hairline text-sm">
              {toc.map((h) => (
                <li key={h.id}>
                  <a href={`#${h.id}`} className="-ml-px block border-l border-transparent pl-3 text-ink-2 hover:border-sim hover:text-ink">{h.text}</a>
                </li>
              ))}
            </ul>
          </nav>
        </aside>
      </div>
    </div>
  );
}
