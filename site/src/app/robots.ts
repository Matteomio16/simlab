import type { MetadataRoute } from "next";
import { PREVIEW } from "@/lib/data";
import { SITE } from "@/lib/site";

export const dynamic = "force-static";

export default function robots(): MetadataRoute.Robots {
  if (PREVIEW) return { rules: { userAgent: "*", disallow: "/" } };
  return { rules: { userAgent: "*", allow: "/" }, sitemap: `${SITE.url}/sitemap.xml` };
}
