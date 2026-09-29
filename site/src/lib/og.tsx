import type { ReactNode } from "react";

// Link-preview cards (1200×630), drawn at build time by next/og. Fonts are fetched once per build from Google Fonts,
// which serves static TrueType files to Node.
export const OG_SIZE = { width: 1200, height: 630 };

let fonts: Promise<{ name: string; data: ArrayBuffer; weight: 600 | 800 | 700; style: "normal" }[]> | null = null;

async function ttf(family: string, weight: number) {
  const css = await (await fetch(`https://fonts.googleapis.com/css2?family=${family}:wght@${weight}`)).text();
  const url = /url\((https:[^)]+\.ttf)\)/.exec(css)?.[1];
  if (!url) throw new Error(`no TrueType file for ${family} ${weight}`);
  return (await fetch(url)).arrayBuffer();
}

export function ogFonts() {
  fonts ??= Promise.all([
    ttf("Libre+Franklin", 600).then((data) => ({ name: "Franklin", data, weight: 600 as const, style: "normal" as const })),
    ttf("Libre+Franklin", 800).then((data) => ({ name: "Franklin", data, weight: 800 as const, style: "normal" as const })),
    ttf("IBM+Plex+Sans", 700).then((data) => ({ name: "Plex", data, weight: 700 as const, style: "normal" as const })),
  ]);
  return fonts;
}

const INK = "#121417";
const SIM = "#6d2e8c";

// The card frame: wordmark on top, content, and the label strip every image carries (publishing.md).
export function OgFrame({ kicker, children, date, sample, bench }: { kicker: string; children: ReactNode; date?: string; sample?: boolean; bench?: string[] }) {
  return (
    <div style={{ width: "100%", height: "100%", display: "flex", flexDirection: "column", background: "#ffffff", fontFamily: "Franklin", color: INK }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "40px 64px 0" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
          <div style={{ width: 40, height: 40, border: `3px solid ${INK}`, display: "flex", flexDirection: "column", justifyContent: "space-around", padding: "3px 0" }}>
            {[0, 1, 2].map((r) => (
              <div key={r} style={{ display: "flex", justifyContent: "space-around" }}>
                {[0, 1, 2].map((c) => (
                  <div key={c} style={{ width: 6, height: 6, borderRadius: 6, background: r === 1 && c === 1 ? SIM : INK }} />
                ))}
              </div>
            ))}
          </div>
          <div style={{ display: "flex", fontFamily: "Plex", fontWeight: 700, fontSize: 34 }}>
            NotAPoll<span style={{ color: SIM }}>.org</span>
          </div>
        </div>
        <div style={{ display: "flex", fontSize: 22, fontWeight: 600, letterSpacing: 2, textTransform: "uppercase", color: "#6b7280" }}>{kicker}</div>
      </div>
      <div style={{ display: "flex", flexDirection: "column", flexGrow: 1, padding: "28px 64px 0", borderTop: `6px solid ${INK}`, margin: "28px 64px 0", paddingLeft: 0, paddingRight: 0 }}>
        {children}
        {bench && (
          <div style={{ display: "flex", gap: 36, marginTop: "auto", marginBottom: 30, fontSize: 24, fontWeight: 600, color: "#3d434c" }}>
            {bench.map((b) => (
              <span key={b}>{b}</span>
            ))}
          </div>
        )}
      </div>
      <div style={{ display: "flex", height: 6, background: "linear-gradient(90deg, #2f6db5 0%, #2f6db5 30%, #6d2e8c 50%, #d1432f 70%, #d1432f 100%)" }} />
      <div style={{ display: "flex", justifyContent: "space-between", background: "#14213d", color: "#e9ecf3", padding: "14px 64px", fontSize: 22, fontWeight: 800, letterSpacing: 2, textTransform: "uppercase" }}>
        <span>Social simulation, not a poll</span>
        <span style={{ fontWeight: 600 }}>{sample ? "Sample data · " : ""}{date ?? "notapoll.org"}</span>
      </div>
    </div>
  );
}
