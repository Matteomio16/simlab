import type { Metadata } from "next";
import { readFileSync } from "node:fs";
import path from "node:path";
import { headings, toHtml } from "@/lib/markdown";
import { ROOT } from "@/lib/root";

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
    <div className="mx-auto max-w-[1200px] px-4 pt-10 sm:px-6 sm:pt-12">
      <p className="label">Methods</p>
      <h1 className="mt-3 max-w-3xl text-[2.3rem] font-extrabold leading-[1.08] tracking-[-0.02em] sm:text-[2.9rem]">{title}</h1>
      <div className="mt-8 grid gap-12 border-t-[3px] border-rule-strong pt-2 lg:grid-cols-[1fr_240px]">
        <div className="prose-np max-w-[680px] [&>h2:first-child]:mt-4" dangerouslySetInnerHTML={{ __html: toHtml(body) }} />
        <aside className="hidden lg:block">
          <nav aria-label="On this page" className="sticky top-8 pt-4">
            <p className="label">On this page</p>
            <ul className="mt-3 space-y-2.5 text-[0.9rem]">
              {toc.map((h) => (
                <li key={h.id}>
                  <a href={`#${h.id}`} className="text-ink-2 hover:text-ink hover:underline">{h.text}</a>
                </li>
              ))}
            </ul>
          </nav>
        </aside>
      </div>
    </div>
  );
}
