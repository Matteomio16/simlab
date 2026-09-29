#!/usr/bin/env node
// Publish one Lab note on the site, only after Matteo approves it: copies kits/labnotes/NN/post.md into
// content/labnotes/NN/ and the slides into public/labnotes/NN/. Commit the result.
//
//   node scripts/import-labnote.mjs 01 [--kits <path to kits/labnotes>]
import { copyFileSync, existsSync, mkdirSync, readdirSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const SITE = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const n = process.argv[2];
if (!/^\d+$/.test(n ?? "")) throw new Error("usage: import-labnote.mjs NN [--kits path]");
const i = process.argv.indexOf("--kits");
const kits = i > 0 ? process.argv[i + 1] : path.join(SITE, "..", "kits", "labnotes");
const src = path.join(kits, n.padStart(2, "0"));
if (!existsSync(path.join(src, "post.md"))) throw new Error(`no post.md in ${src}`);

const id = n.padStart(2, "0");
const content = path.join(SITE, "content", "labnotes", id);
const pub = path.join(SITE, "public", "labnotes", id);
mkdirSync(content, { recursive: true });
mkdirSync(pub, { recursive: true });
copyFileSync(path.join(src, "post.md"), path.join(content, "post.md"));
const slides = readdirSync(src).filter((f) => /^slide-\d+\.(jpe?g|png)$/.test(f));
for (const f of slides) copyFileSync(path.join(src, f), path.join(pub, f));
console.log(`Lab notes ${id}: post.md and ${slides.length} slides copied. Review, then commit.`);
