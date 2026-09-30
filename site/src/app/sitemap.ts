import type { MetadataRoute } from "next";
import { HAS_FORECAST, senateRacesSafe } from "@/lib/data";
import { allNotes } from "@/lib/labnotes";
import { SHOW, SITE } from "@/lib/site";

export const dynamic = "force-static";

export default function sitemap(): MetadataRoute.Sitemap {
  const pages = [
    "",
    ...(SHOW.methods ? ["/methods"] : []),
    ...(SHOW.labNotes ? ["/lab-notes"] : []),
    ...(SHOW.about ? ["/about"] : []),
    ...(SHOW.changelog ? ["/changelog"] : []),
    ...(SHOW.trackRecord ? ["/track-record"] : []),
    ...(HAS_FORECAST ? ["/archive"] : []),
  ];
  const notes = (SHOW.labNotes ? allNotes() : []).map((n) => `/lab-notes/${n.n}`);
  const races = HAS_FORECAST ? senateRacesSafe().map((r) => `/senate/${r.slug}`) : [];
  return [...pages, ...notes, ...races].map((p) => ({ url: `${SITE.url}${p}` }));
}
