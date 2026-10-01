import { ROOT } from "@/lib/root";
import { existsSync, readdirSync, readFileSync } from "node:fs";
import path from "node:path";

// Lab notes are copied here only once Matteo approves them (scripts/import-labnote.mjs). post.md format: see
// docs/publishing.md, "Lab notes file format".
const DIR = path.join(ROOT, "content", "labnotes");

export type LabNote = {
  n: string;
  title: string;
  date: string | null;
  slides: { file: string; alt: string }[];
  caption: string;
  // Optional "## Website article" (Matteo, 1 Oct): the full web version, with {{slide:N}} placing slide N beside the
  // text that follows it and "#### In detail" opening a fold. Without it the page shows the caption and the slides.
  article: string;
};

function section(md: string, name: string) {
  const part = md.split(/^## /m).find((p) => p.startsWith(name));
  return part ? part.slice(name.length).trim() : "";
}

export function parse(n: string, raw: string): LabNote {
  const md = raw.replace(/\r/g, "");
  const title = /^#\s+Lab notes \d+:\s*(.*)$/m.exec(md)?.[1]?.trim() ?? `Lab notes ${n}`;
  const date = /Planned date:\s*([^.\n]+)/.exec(md)?.[1]?.trim() ?? null;
  const slides = [...section(md, "Slides and alt text").matchAll(/^\d+\.\s+`([^`]+)`:\s*(.*)$/gm)].map((m) => ({
    file: m[1], alt: m[2].trim(),
  }));
  const caption = section(md, "Instagram caption")
    .split("\n")
    .filter((l) => !/^#\w/.test(l.trim()))
    .join("\n")
    .trim();
  const article = section(md, "Website article");
  return { n, title: title.charAt(0).toUpperCase() + title.slice(1), date, slides, caption, article };
}

export function allNotes(): LabNote[] {
  if (!existsSync(DIR)) return [];
  return readdirSync(DIR)
    .filter((d) => /^\d+$/.test(d) && existsSync(path.join(DIR, d, "post.md")))
    .sort()
    .reverse()
    .map((d) => parse(d, readFileSync(path.join(DIR, d, "post.md"), "utf8")));
}
