#!/usr/bin/env node
// Runs after `next build`: writes out/_headers, and removes the placeholder pages that the static export needs while
// there are no race pages or Lab notes yet, so nothing half-built is ever served.
import { readFileSync, rmSync, writeFileSync, existsSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const OUT = path.join(path.dirname(path.dirname(fileURLToPath(import.meta.url))), "out");
const preview = process.env.SITE_PREVIEW === "1";
const forecast = process.env.SITE_MODE === "forecast";

const drop = (p) => existsSync(path.join(OUT, p)) && rmSync(path.join(OUT, p), { recursive: true, force: true });
if (!forecast)
  ["senate", "senate.html", "senate.txt", "archive", "archive.html", "archive.txt"].forEach(drop);
["lab-notes/00.html", "lab-notes/00.txt", "lab-notes/00"].forEach(drop);
// Pages Matteo hasn't approved (src/lib/approved.json) stay off the public site.
const route = (r) => [r, `${r}.html`, `${r}.txt`];
const unapproved = {
  methods: route("methods"),
  labNotes: [...route("lab-notes"), "labnotes"],
  about: route("about"),
  trackRecord: route("track-record"),
  changelog: route("changelog"),
};
const approved = JSON.parse(readFileSync(path.join(OUT, "..", "src", "lib", "approved.json"), "utf8"));
if (!preview) for (const [k, paths] of Object.entries(unapproved)) if (!approved[k]) paths.forEach(drop);

const headers = [
  "/*",
  "  X-Content-Type-Options: nosniff",
  "  Referrer-Policy: strict-origin-when-cross-origin",
  "  Permissions-Policy: camera=(), microphone=(), geolocation=()",
  ...(preview ? ["  X-Robots-Tag: noindex, nofollow"] : []),
  "/_next/static/*",
  "  Cache-Control: public, max-age=31536000, immutable",
  "/data/*",
  "  Access-Control-Allow-Origin: *",
  "/opengraph-image",
  "  Content-Type: image/png",
  "/senate/:slug/opengraph-image",
  "  Content-Type: image/png",
  "",
].join("\n");
writeFileSync(path.join(OUT, "_headers"), headers);
console.log(`postbuild: ${forecast ? "forecast" : "prelaunch"}${preview ? " preview" : ""}`);
