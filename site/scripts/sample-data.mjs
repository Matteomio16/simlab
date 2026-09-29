#!/usr/bin/env node
// Sample data for the site: the shape of forecast.json, draws.json and races.json (engine-design §7), with every
// number invented from a seeded random walk. Only race metadata (states, candidates, parties) is read from a real
// races.json; no forecast number, tier reason or benchmark is copied.
//
//   node scripts/sample-data.mjs --races <path to races.json> [--date 2026-10-12] [--seed 7]

import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const args = Object.fromEntries(
  process.argv.slice(2).reduce((acc, a, i, all) => (a.startsWith("--") ? [...acc, [a.slice(2), all[i + 1]]] : acc), []),
);
const DATE = args.date ?? "2026-10-12";
const SEED = Number(args.seed ?? 7);
const OUT = path.join(ROOT, "data", "sample");
const DRAWS = 1000;
const HISTORY_DAYS = 21;
const NOT_UP = { R: 31, D: 32, I: 2 };

let s = SEED >>> 0;
const rand = () => {
  s = (s + 0x6d2b79f5) >>> 0;
  let t = s;
  t = Math.imul(t ^ (t >>> 15), t | 1);
  t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
  return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
};
const normal = () => Math.sqrt(-2 * Math.log(1 - rand())) * Math.cos(2 * Math.PI * rand());
const phi = (x) => 0.5 * (1 + erf(x / Math.SQRT2));
function erf(x) {
  const t = 1 / (1 + 0.3275911 * Math.abs(x));
  const y = 1 - ((((1.061405429 * t - 1.453152027) * t + 1.421413741) * t - 0.284496736) * t + 0.254829592) * t * Math.exp(-x * x);
  return x >= 0 ? y : -y;
}
const r1 = (x) => Math.round(x * 10) / 10;
const r2 = (x) => Math.round(x * 100) / 100;
const r4 = (x) => Math.round(x * 10000) / 10000;
const Z90 = 1.2816;
const SD = 5.5;

const CARDS = [
  "Sample story: a candidate released a television ad about the cost of health care.",
  "Sample story: the two candidates met for their only scheduled debate.",
  "Sample story: a former governor endorsed one of the candidates.",
  "Sample story: a report on campaign spending drew attention to outside groups.",
  "Sample story: a candidate announced a plan on housing costs.",
  "Sample story: new figures showed grocery prices rising again.",
];

const racesIn = JSON.parse(readFileSync(args.races, "utf8"));
const ids = Object.keys(racesIn).filter((k) => racesIn[k] && typeof racesIn[k] === "object").sort();

const cook = (m) => {
  const a = Math.abs(m), side = m > 0 ? "D" : "R";
  if (a < 3) return "Tossup";
  return `${a < 7 ? "Lean" : a < 12 ? "Likely" : "Solid"} ${side}`;
};
const tierOf = (p) => (p > 0.97 || p < 0.03 ? "statistics" : p > 0.9 || p < 0.1 ? "watch" : "simulate");

const races = { date: DATE, run_id: `${DATE}-sample`, schema: 1 };
const forecastRaces = {};
const drawRaces = {};
const statsDrawRaces = {};
const history = { date: DATE, schema: 1, races: {}, senate: [] };
const national = Array.from({ length: DRAWS }, () => normal() * 3);

for (const id of ids) {
  const meta = racesIn[id];
  const c = normal() * 13;
  const today = c + normal() * 1.2;
  const so = c + normal() * 1.5;
  const p = phi(c / SD);
  const effect = normal() * 0.6;
  const w = 0.4 + rand() * 0.4;
  const tier = tierOf(p);
  races[id] = {
    state: meta.state, office: meta.office, district: meta.district ?? null, special: !!meta.special, rcv: !!meta.rcv,
    candidates: meta.candidates, left_party: meta.left_party, incumbent_party: meta.incumbent_party,
    status: meta.status, tier, tier_raw: tier, tier_reasons: ["sample data"],
  };
  const band = (m) => ({ p10: r2(m - Z90 * SD), p50: r2(m), p90: r2(m + Z90 * SD) });
  const movers = tier === "simulate"
    ? Array.from({ length: 1 + Math.floor(rand() * 3) }, (_, i) => ({
        event_id: `${id}-SAMPLE-${i + 1}`, card: CARDS[Math.floor(rand() * CARDS.length)], delta: r2(normal() * 0.5),
      }))
    : [];
  forecastRaces[id] = {
    p_dem_win: r4(p), margin: band(c),
    stats_only: { p_dem_win: r4(phi(so / SD)), margin: band(so) },
    left_party: meta.left_party, w_polls: r2(w),
    benchmarks: {
      poll_avg: rand() < 0.2 ? null : r2(c + normal() * 2.5),
      market: r4(phi((c + normal() * 2) / 6)),
      cook: cook(c + normal() * 2),
    },
    movers,
    news: {
      effect: r2(effect), switching: r2(effect * 0.55), turnout: r2(effect * 0.45),
      if_weaker: { multipliers: { s: 0.465, t: 0.289 }, p_dem_win: r4(phi((c - effect * 0.6) / SD)) },
      if_stronger: { multipliers: { s: 1.675, t: 1.974 }, p_dem_win: r4(phi((c + effect * 0.8) / SD)) },
    },
    today: { p_dem_win: r4(phi(today / SD)), margin: band(today), stats_only: { p_dem_win: r4(phi(so / SD)), margin: band(so) } },
  };
  drawRaces[id] = national.map((n) => r1(c + n + normal() * Math.sqrt(SD * SD - 9)));
  statsDrawRaces[id] = national.map((n) => r1(so + n + normal() * Math.sqrt(SD * SD - 9)));

  let m = c - normal() * 3;
  const walk = [];
  for (let d = HISTORY_DAYS - 1; d >= 0; d--) {
    const day = new Date(Date.parse(DATE) - d * 86400000).toISOString().slice(0, 10);
    m = d === 0 ? c : m + (c - m) / (d + 1) + normal() * 0.5;
    walk.push({ date: day, p_dem_win: r4(phi(m / SD)), p50: r2(m) });
  }
  history.races[id] = walk;
}

function chamber(drawsByRace) {
  const R = [], D = [], I = [];
  for (let k = 0; k < DRAWS; k++) {
    const seats = { ...NOT_UP };
    for (const id of ids) {
      const leftWins = drawsByRace[id][k] > 0;
      seats[leftWins ? (races[id].left_party === "I" ? "I" : "D") : "R"] += 1;
    }
    R.push(seats.R); D.push(seats.D); I.push(seats.I);
  }
  return { R, D, I };
}
function summary(list) {
  const sorted = [...list].sort((a, b) => a - b);
  const q = (x) => sorted[Math.min(sorted.length - 1, Math.floor(x * sorted.length))];
  const dist = {};
  for (const v of list) dist[v] = (dist[v] ?? 0) + 1 / list.length;
  for (const k in dist) dist[k] = r4(dist[k]);
  return { mean: r2(list.reduce((a, b) => a + b, 0) / list.length), p10: q(0.1), p50: q(0.5), p90: q(0.9), dist };
}
function control(ch) {
  let r50 = 0, d51 = 0, ind = 0;
  for (let k = 0; k < DRAWS; k++) {
    // King and Sanders (2 of the not-up independents) caucus with Democrats; new independents decide when neither side has 50.
    const dCaucus = ch.D[k] + NOT_UP.I;
    const newI = ch.I[k] - NOT_UP.I;
    if (ch.R[k] >= 50) r50++;
    if (dCaucus >= 51) d51++;
    if (newI > 0 && ch.R[k] < 50 && dCaucus < 51) ind++;
  }
  return { p_r_50plus: r4(r50 / DRAWS), p_d_caucus_51: r4(d51 / DRAWS), p_independents_decide: r4(ind / DRAWS) };
}

const ch = chamber(drawRaces);
const chSo = chamber(statsDrawRaces);
const senate = {
  ...control(ch),
  seats: { R: summary(ch.R), D: summary(ch.D), I: summary(ch.I) },
  not_up: NOT_UP,
  stats_only: control(chSo),
  benchmarks: { market: r4(0.35 + rand() * 0.3) },
  news: { if_weaker: 0, if_stronger: 0 },
  today: { ...control(ch), stats_only: control(chSo) },
};
senate.news.if_weaker = r4(senate.p_r_50plus + normal() * 0.01);
senate.news.if_stronger = r4(senate.p_r_50plus + normal() * 0.01);
senate.today.p_r_50plus = r4(Math.min(1, Math.max(0, senate.p_r_50plus + normal() * 0.03)));

let pr = senate.p_r_50plus + normal() * 0.08;
for (let d = HISTORY_DAYS - 1; d >= 0; d--) {
  const day = new Date(Date.parse(DATE) - d * 86400000).toISOString().slice(0, 10);
  pr = d === 0 ? senate.p_r_50plus : pr + (senate.p_r_50plus - pr) / (d + 1) + normal() * 0.012;
  history.senate.push({ date: day, p_r_50plus: r4(Math.min(1, Math.max(0, pr))) });
}

const units = "two-party margin, D (or independent challenger) minus R, points";
const forecast = {
  date: DATE, run_id: `${DATE}-sample`, schema: 1, units, seed: SEED, draws: 40000,
  races: forecastRaces, senate, house: null, snapshot: `${DATE} 07:30`, sample: true,
};
const draws = {
  date: DATE, run_id: `${DATE}-sample`, schema: 1, units, seed: SEED, every: 40,
  races: drawRaces, seats: { senate: { R: ch.R, D: ch.D, I: ch.I } },
  stats_only: { races: statsDrawRaces, seats: { senate: { R: chSo.R, D: chSo.D, I: chSo.I } } },
};

mkdirSync(OUT, { recursive: true });
for (const [name, obj] of Object.entries({ forecast, draws, races, history })) {
  writeFileSync(path.join(OUT, `${name}.json`), JSON.stringify(obj));
}
console.log(`sample data for ${ids.length} races, ${DATE}, seed ${SEED} -> ${path.relative(process.cwd(), OUT)}`);
