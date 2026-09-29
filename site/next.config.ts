import type { NextConfig } from "next";

// Static export, served by a Cloudflare Worker with no adapter (same setup as scaliastudio.dev).
const nextConfig: NextConfig = {
  output: "export",
  images: { unoptimized: true },
};

export default nextConfig;
