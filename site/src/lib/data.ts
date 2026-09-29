import { ROOT } from "@/lib/root";
import { readFileSync, existsSync } from "node:fs";
import path from "node:path";
import type { Draws, Forecast, History, RaceMeta } from "./types";
import { STATES } from "./states";

// Build-time only. SITE_MODE=prelaunch builds no forecast pages at all (3 Oct); SITE_MODE=forecast needs Matteo's go
// for production. SITE_DATA picks data/sample (default) or data/live (written by the daily job from 12 Oct).
export const MODE = process.env.SITE_MODE === "forecast" ? "forecast" : "prelaunch";
export const DATA = process.env.SITE_DATA === "live" ? "live" : "sample";
export const IS_SAMPLE = DATA === "sample";
export const HAS_FORECAST = MODE === "forecast";

const dir = path.join(ROOT, "data", DATA);
const read = <T,>(name: string): T => JSON.parse(readFileSync(path.join(dir, `${name}.json`), "utf8"));

let cache: { forecast: Forecast; races: Record<string, RaceMeta>; draws: Draws; history: History } | null = null;

export function load() {
  if (!HAS_FORECAST) throw new Error("forecast data requested in prelaunch mode");
  if (cache) return cache;
  const racesFile = read<Record<string, unknown>>("races");
  const races: Record<string, RaceMeta> = {};
  for (const [k, v] of Object.entries(racesFile)) if (v && typeof v === "object") races[k] = v as RaceMeta;
  const history = existsSync(path.join(dir, "history.json")) ? read<History>("history") : { races: {}, senate: [] };
  cache = { forecast: read<Forecast>("forecast"), races, draws: read<Draws>("draws"), history };
  return cache;
}

// Race metadata only (states, candidates, parties): public facts, safe to show before launch.
export function loadRaceMeta(): Record<string, RaceMeta> {
  const file = read<Record<string, unknown>>("races");
  const out: Record<string, RaceMeta> = {};
  for (const [k, v] of Object.entries(file)) if (v && typeof v === "object") out[k] = v as RaceMeta;
  return out;
}

export function raceSlug(id: string, meta: RaceMeta) {
  const name = (STATES[meta.state] ?? meta.state).toLowerCase().replace(/\s+/g, "-");
  if (meta.office === "house") return `${name}-${meta.district ?? "at-large"}`;
  return meta.special ? `${name}-special` : name;
}

export function raceTitle(meta: RaceMeta) {
  const state = STATES[meta.state] ?? meta.state;
  if (meta.office === "house") return `${state} ${meta.district ?? "at-large"}`;
  return meta.special ? `${state} (special)` : state;
}

export function raceCode(id: string, meta: RaceMeta) {
  if (meta.office === "house") return id;
  return `${meta.state}-SEN${meta.special ? "-S" : ""}`;
}

export function senateRaces() {
  const { forecast, races } = load();
  return Object.keys(forecast.races)
    .filter((id) => races[id]?.office === "senate")
    .map((id) => ({ id, meta: races[id], f: forecast.races[id], slug: raceSlug(id, races[id]) }));
}

// The unlisted preview (workers.dev): never indexed.
export const PREVIEW = process.env.SITE_PREVIEW === "1";

export const senateRacesSafe = () => (HAS_FORECAST ? senateRaces() : []);
