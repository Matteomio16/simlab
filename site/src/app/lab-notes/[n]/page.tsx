import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { allNotes } from "@/lib/labnotes";

export const dynamicParams = false;

// Before the first approved note, one placeholder param keeps the static export happy and renders a 404.
export function generateStaticParams() {
  const notes = allNotes();
  return notes.length ? notes.map((n) => ({ n: n.n })) : [{ n: "00" }];
}

export async function generateMetadata({ params }: { params: Promise<{ n: string }> }): Promise<Metadata> {
  const { n } = await params;
  const note = allNotes().find((x) => x.n === n);
  return note ? { title: `Lab notes ${note.n}: ${note.title}`, description: note.caption.split("\n")[0] } : {};
}

export default async function LabNote({ params }: { params: Promise<{ n: string }> }) {
  const { n } = await params;
  const note = allNotes().find((x) => x.n === n);
  if (!note) notFound();
  return (
    <article className="mx-auto max-w-3xl px-4 pt-12 sm:px-6 sm:pt-16">
      <nav className="text-[0.85rem] font-semibold text-ink-2"><Link href="/lab-notes" className="hover:underline">Lab notes</Link> <span className="text-muted">/</span> Note {note.n}</nav>
      <h1 className="mt-4 text-[2.2rem] font-extrabold leading-[1.1] tracking-[-0.02em] sm:text-[2.7rem]">{note.title}</h1>
      {note.date && <p className="mt-3 text-sm text-muted">{note.date}</p>}
      <div className="mt-8 space-y-4 border-t-[3px] border-rule-strong pt-6 text-[1.15rem] leading-relaxed text-ink">
        {note.caption.split(/\n{2,}/).map((p, i) => (
          <p key={i} className="whitespace-pre-line">{p}</p>
        ))}
      </div>
      <div className="mt-12 grid gap-6 sm:grid-cols-2">
        {note.slides.map((s) => (
          <figure key={s.file}>
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img loading="lazy" decoding="async" src={`/labnotes/${note.n}/${s.file}`} alt={s.alt} className="w-full border border-rule" />
          </figure>
        ))}
      </div>
    </article>
  );
}
