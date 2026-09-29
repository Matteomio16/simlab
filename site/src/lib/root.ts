import { existsSync } from "node:fs";
import path from "node:path";

// The site folder, whether Next runs from site/ (npm scripts, CI) or from the repo root (`next dev site`).
export const ROOT = existsSync(path.join(process.cwd(), "site", "next.config.ts")) ? path.join(process.cwd(), "site") : process.cwd();
