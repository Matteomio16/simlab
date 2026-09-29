import type { Metadata } from "next";
import Link from "next/link";
import { allNotes } from "@/lib/labnotes";

export const metadata: Metadata = {
  title: "Lab notes",
  description: "The making-of series: how the NotAPoll.org social simulation is built and tested, as it happens.",
};

export default function LabNotes() {
  const notes = allNotes();
  return (
    <div className="mx-auto max-w-6xl px-4 pt-12 sm:px-6 sm:pt-16">
      <p className="kicker">Lab notes</p>
      <h1 className="mt-3 font-serif text-4xl text-ink sm:text-5xl">The making-of, as it happens</h1>
      <p className="mt-4 max-w-2xl text-lg text-ink-2">
        What we tested, what failed and what we changed, published as we go. The same notes run on Instagram, Threads,
        X and Bluesky.
      </p>
      {notes.length === 0 ? (
        <p className="mt-12 text-ink-2">The first Lab note comes out on Saturday 3 October.</p>
      ) : (
        <ul className="mt-12 divide-y divide-hairline border-y border-hairline">
          {notes.map((n) => (
            <li key={n.n}>
              <Link href={`/lab-notes/${n.n}`} className="group flex items-center gap-6 py-6">
                {n.slides[0] && (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img src={`/labnotes/${n.n}/${n.slides[0].file}`} alt="" className="hidden w-24 rounded-sm border border-hairline sm:block" />
                )}
                <div>
                  <p className="kicker">Lab notes {n.n}{n.date ? ` · ${n.date}` : ""}</p>
                  <p className="mt-1 font-serif text-2xl text-ink group-hover:underline">{n.title}</p>
                </div>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
