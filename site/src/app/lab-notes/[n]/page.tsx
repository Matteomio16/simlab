import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { allNotes, type LabNote } from "@/lib/labnotes";
import { toHtml } from "@/lib/markdown";

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

const html = (md: string) => ({ __html: toHtml(md) });

function Slide({ note, i }: { note: LabNote; i: number }) {
  const s = note.slides[i - 1];
  if (!s) return null;
  return (
    <figure>
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img loading="lazy" decoding="async" src={`/labnotes/${note.n}/${s.file}`} alt={s.alt} className="w-full border border-rule" />
    </figure>
  );
}

function Prose({ md }: { md: string }) {
  const [plain, detail] = md.split(/^#### In detail\s*$/m);
  return (
    <>
      <div className="prose-np text-[1.08rem]" dangerouslySetInnerHTML={html(plain.trim())} />
      {detail?.trim() && (
        <details className="group mt-5 border-t border-rule">
          <summary className="flex cursor-pointer list-none items-center gap-2 py-3 text-[0.9rem] font-semibold text-ink">
            <span className="inline-block w-3 text-center transition-transform group-open:rotate-90" aria-hidden="true">›</span>
            In detail
          </summary>
          <div className="prose-np pb-2 text-[0.95rem]" dangerouslySetInnerHTML={html(detail.trim())} />
        </details>
      )}
    </>
  );
}

// The web version of a note: an article, each slide set beside the claim it shows (Matteo, 1 Oct).
function Article({ note }: { note: LabNote }) {
  const [intro, ...rest] = note.article.split(/\{\{slide:(\d+)\}\}/);
  const blocks: { slide: number; md: string }[] = [];
  for (let i = 0; i < rest.length; i += 2) blocks.push({ slide: Number(rest[i]), md: rest[i + 1] ?? "" });
  return (
    <>
      {intro.trim() && (
        <div className="mt-8 max-w-[680px] text-[1.2rem] leading-relaxed text-ink-2 [&_strong]:text-ink" dangerouslySetInnerHTML={html(intro.trim())} />
      )}
      {blocks.map((b, i) => (
        <section key={i} className="mt-10 grid gap-8 border-t border-rule pt-8 lg:grid-cols-[1fr_440px] lg:gap-14">
          <div className="max-w-[640px]"><Prose md={b.md} /></div>
          <div className="lg:sticky lg:top-8 lg:self-start"><Slide note={note} i={b.slide} /></div>
        </section>
      ))}
    </>
  );
}

function CaptionAndSlides({ note }: { note: LabNote }) {
  return (
    <>
      <div className="mt-8 max-w-[680px] space-y-4 text-[1.15rem] leading-relaxed text-ink">
        {note.caption.split(/\n{2,}/).map((p, i) => (
          <p key={i} className="whitespace-pre-line">{p}</p>
        ))}
      </div>
      <div className="mt-12 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {note.slides.map((_, i) => <Slide key={i} note={note} i={i + 1} />)}
      </div>
    </>
  );
}

export default async function LabNotePage({ params }: { params: Promise<{ n: string }> }) {
  const { n } = await params;
  const note = allNotes().find((x) => x.n === n);
  if (!note) notFound();
  return (
    <article className="mx-auto max-w-[1200px] px-4 pt-10 sm:px-6 sm:pt-12">
      <div className="flex items-baseline justify-between border-b border-rule pb-2 text-[0.72rem] font-bold uppercase tracking-[0.08em]">
        <Link href="/lab-notes" className="hover:underline">Lab notes · Note {note.n}</Link>
        {note.date && <span className="text-muted">{note.date}</span>}
      </div>
      <h1 className="mt-6 max-w-4xl text-[2.2rem] font-extrabold leading-[1.08] tracking-[-0.022em] sm:text-[2.8rem]">{note.title}</h1>
      {note.article ? <Article note={note} /> : <CaptionAndSlides note={note} />}
    </article>
  );
}
