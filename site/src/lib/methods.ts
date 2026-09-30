import { readFileSync } from "node:fs";
import path from "node:path";
import { slugify } from "./markdown";
import { ROOT } from "./root";

// content/methods.md, split into the blocks the methods page lays out: the lede, then each ## section with its ###
// subsections. The page decides how each block looks; the text stays in one Markdown file.
export type Sub = { title: string; id: string; body: string };
export type Section = { title: string; id: string; body: string; subs: Sub[] };

export function loadMethods() {
  const md = readFileSync(path.join(ROOT, "content", "methods.md"), "utf8").replace(/\r/g, "");
  const [lede, ...parts] = md.split(/^## /m);
  const sections: Section[] = parts.map((part) => {
    const [titleLine, ...rest] = part.split("\n");
    const [body, ...subParts] = rest.join("\n").split(/^### /m);
    const subs = subParts.map((sp) => {
      const [t, ...b] = sp.split("\n");
      return { title: t.trim(), id: slugify(t), body: b.join("\n").trim() };
    });
    return { title: titleLine.trim(), id: slugify(titleLine), body: body.trim(), subs };
  });
  return { lede: lede.replace(/^#\s+.*$/m, "").trim(), sections };
}

// Top-level list items of a Markdown block, continuation lines joined; and the text around the list.
export function listItems(md: string) {
  const items: string[] = [];
  const before: string[] = [];
  const after: string[] = [];
  let inList = false;
  for (const line of md.split("\n")) {
    const m = /^(?:-|\d+\.)\s+(.*)$/.exec(line);
    if (m) {
      items.push(m[1]);
      inList = true;
    } else if (inList && /^\s{2,}\S/.test(line)) {
      items[items.length - 1] += ` ${line.trim()}`;
    } else if (line.trim() && items.length) {
      inList = false;
      after.push(line);
    } else if (!items.length) {
      before.push(line);
    } else {
      after.push(line);
    }
  }
  return { before: before.join("\n").trim(), items, after: after.join("\n").trim() };
}

// "**Title.** Body" -> { title, body }.
export function splitBold(item: string) {
  const m = /^\*\*(.+?)\*\*[.:]?\s*(.*)$/.exec(item);
  return m ? { title: m[1].replace(/[.:]$/, ""), body: m[2] } : { title: "", body: item };
}
