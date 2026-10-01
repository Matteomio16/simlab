#!/usr/bin/env node
// Vocabulary check on the built pages (publishing.md): our outputs are never a poll or a survey, and nobody "says"
// anything. Words about real polls (poll average, pollster, "not a poll") are allowed.
import { readdirSync, readFileSync, statSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const OUT = path.join(path.dirname(path.dirname(fileURLToPath(import.meta.url))), "out");
const ALLOWED = /("voters say"|survey answers|real respondents|Current Population Survey|\breal poll\w*|\breal survey respondents|\bnot a poll|same poll|poll avg|a poll was taken|the poll enters|real survey answers|survey respondents interviewed|poll averages?|polls? (?:average|aggregat)|pollsters?|real polls|new polls|the polls|polls with|polls,|polls\.|polls get|polls enter|polls from|about polls|of polls|and polls|2026 polls|poll-bias|poll table|poll tables|poll data|poll scarcity|polls or|polls and|polls are|polls in)/gi;
const BANNED = [/\bpoll\b/i, /\bsurvey(?:ed|s)?\b/i, /\bvoters say\b/i, /\b% of voters\b/i, /\brespondents\b/i, /\bAI voters\b/i, /\bsynthetic\b/i, /\bHungar/i, /\breactionary\b/i, /\bsocial interactions?\b/i];

const files = [];
const walk = (d) => readdirSync(d).forEach((f) => {
  const p = path.join(d, f);
  if (statSync(p).isDirectory()) walk(p);
  else if (p.endsWith(".html")) files.push(p);
});
walk(OUT);

let bad = 0;
for (const f of files) {
  const text = readFileSync(f, "utf8").replace(/<script[\s\S]*?<\/script>/g, "").replace(/<[^>]+>/g, " ").replace(/&[a-z]+;|&#\d+;/g, " ");
  const cleaned = text.replace(ALLOWED, "");
  for (const re of BANNED) {
    const m = cleaned.match(new RegExp(`.{0,50}${re.source}.{0,50}`, "i"));
    if (m) {
      bad++;
      console.log(`${path.relative(OUT, f)}: ${m[0].replace(/\s+/g, " ").trim()}`);
    }
  }
}
console.log(bad ? `${bad} copy notes to review` : `copy check: ${files.length} pages clean`);
process.exitCode = bad ? 1 : 0;
