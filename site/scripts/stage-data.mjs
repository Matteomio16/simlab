#!/usr/bin/env node
// Before dev and build: in forecast mode, stage the public files the browser fetches (the simulator reads draws.json)
// into public/data/; in prelaunch mode, make sure none are there.
import { copyFileSync, mkdirSync, rmSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const SITE = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const pub = path.join(SITE, "public", "data");
const src = path.join(SITE, "data", process.env.SITE_DATA === "live" ? "live" : "sample");
for (const f of ["forecast.json", "draws.json"]) rmSync(path.join(pub, f), { force: true });
if (process.env.SITE_MODE === "forecast") {
  mkdirSync(pub, { recursive: true });
  for (const f of ["forecast.json", "draws.json"]) copyFileSync(path.join(src, f), path.join(pub, f));
  console.log(`stage-data: ${path.relative(SITE, src)} -> public/data`);
}
