#!/usr/bin/env node
// From 12 Oct, after Matteo's go: copy one day's public files into data/live and extend history.json.
//
//   node scripts/publish-day.mjs --from <simlab-data/derived/YYYY-MM-DD>
//
// Only the public files leave the private repo (engine-design §7): forecast.json, draws.json, and races.json
// (metadata the pages need). Never events.jsonl, news_private.jsonl or anything else.
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const SITE = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const i = process.argv.indexOf("--from");
if (i < 0) throw new Error("usage: publish-day.mjs --from <derived/YYYY-MM-DD>");
const src = process.argv[i + 1];
const OUT = path.join(SITE, "data", "live");
mkdirSync(OUT, { recursive: true });

const read = (f) => JSON.parse(readFileSync(path.join(src, f), "utf8"));
const forecast = read("forecast.json");
const races = read("races.json");
for (const v of Object.values(races)) if (v && typeof v === "object") delete v.tier_reasons;
writeFileSync(path.join(OUT, "forecast.json"), JSON.stringify(forecast));
writeFileSync(path.join(OUT, "draws.json"), JSON.stringify(read("draws.json")));
writeFileSync(path.join(OUT, "races.json"), JSON.stringify(races));

const hp = path.join(OUT, "history.json");
const history = existsSync(hp) ? JSON.parse(readFileSync(hp, "utf8")) : { schema: 1, races: {}, senate: [] };
const put = (list, row) => [...list.filter((r) => r.date !== row.date), row].sort((a, b) => a.date.localeCompare(b.date));
for (const [id, r] of Object.entries(forecast.races)) {
  history.races[id] = put(history.races[id] ?? [], { date: forecast.date, p_dem_win: r.p_dem_win, p50: r.margin.p50 });
}
history.senate = put(history.senate, { date: forecast.date, p_r_50plus: forecast.senate.p_r_50plus });
history.date = forecast.date;
writeFileSync(hp, JSON.stringify(history));

const archive = path.join(SITE, "public", "data", forecast.date);
mkdirSync(archive, { recursive: true });
writeFileSync(path.join(archive, "forecast.json"), JSON.stringify(forecast));
console.log(`published ${forecast.date} (${forecast.run_id}) to data/live and public/data/${forecast.date}`);
