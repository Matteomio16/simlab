import type { Metadata } from "next";
import Link from "next/link";
import { allNotes } from "@/lib/labnotes";
import Dateline from "@/components/Dateline";

export const metadata: Metadata = {
  title: "Lab notes",
  description: "The making-of series: how the NotAPoll.org social simulation is built and tested, as it happens.",
};

export default function LabNotes() {
  const notes = allNotes();
  return (
    <div className="mx-auto max-w-[1200px] px-4 pt-10 sm:px-6 sm:pt-12">
      <Dateline left="Lab notes" />
      <h1 className="mt-6 max-w-3xl text-[2.3rem] font-extrabold leading-[1.08] tracking-[-0.02em] sm:text-[2.9rem]">
        The making-of, published as we go
      </h1>
      <p className="mt-4 max-w-2xl text-[1.2rem] leading-relaxed text-ink-2">
        What we tested, what failed and what we changed. A short version of each runs on Instagram, Threads and X.
      </p>
      <div className="mt-8 border-t-[3px] border-rule-strong">
        {notes.length === 0 ? (
          <p className="pt-6 text-ink-2">The first note comes out on Saturday, October 3.</p>
        ) : (
          <ul>
            {notes.map((n) => (
              <li key={n.n} className="border-b border-rule">
                <Link href={`/lab-notes/${n.n}`} className="group grid gap-4 py-5 sm:grid-cols-[120px_1fr_96px] sm:items-center">
                  <span className="label-muted">Note {n.n}{n.date ? ` · ${n.date}` : ""}</span>
                  <span className="text-xl font-bold tracking-[-0.01em] group-hover:underline">{n.title}</span>
                  {n.slides[0] && (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img loading="lazy" decoding="async" src={`/labnotes/${n.n}/${n.slides[0].file}`} alt="" className="hidden w-24 border border-rule sm:block" />
                  )}
                </Link>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
