import { ImageResponse } from "next/og";
import { IS_SAMPLE, load, senateRacesSafe } from "@/lib/data";
import { in100, leader, longDate, margin, surname } from "@/lib/format";
import { STATES } from "@/lib/states";
import { OG_SIZE, OgFrame, ogFonts } from "@/lib/og";

export const alt = "A NotAPoll.org Senate race forecast";
export const size = OG_SIZE;
export const contentType = "image/png";

const COLOR = { D: "#2f6db5", R: "#d1432f", I: "#7e879a" } as const;

export function generateStaticParams() {
  const races = senateRacesSafe();
  return races.length ? races.map((r) => ({ slug: r.slug })) : [{ slug: "soon" }];
}

export default async function Image({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const fonts = await ogFonts();
  const race = senateRacesSafe().find((r) => r.slug === slug);
  if (!race) {
    return new ImageResponse(<OgFrame kicker="2026 Senate forecast"><div style={{ display: "flex", fontSize: 80, fontWeight: 800 }}>NotAPoll.org</div></OgFrame>, { ...size, fonts });
  }
  const { forecast } = load();
  const { meta, f } = race;
  const lead = leader(f.p_dem_win, meta);
  const pL = in100(f.p_dem_win);
  const b = f.benchmarks;
  const bench = [
    `Poll avg. ${b.poll_avg == null ? "n/a" : margin(b.poll_avg, meta.left_party)}`,
    `Market ${b.market == null ? "n/a" : `${surname(meta.candidates.left)} ${Math.round(b.market * 100)}%`}`,
    `Cook ${b.cook?.replace("Tossup", "Toss-up").replace("Solid", "Safe") ?? "n/a"}`,
  ];
  return new ImageResponse(
    <OgFrame kicker={`${STATES[meta.state]} Senate${meta.special ? " · special" : ""}`} date={longDate(forecast.date)} sample={IS_SAMPLE} bench={bench}>
      <div style={{ display: "flex", fontSize: 64, fontWeight: 800, letterSpacing: -1.5, lineHeight: 1.05 }}>
        {`${surname(lead.name)} wins ${in100(lead.p)} of 100 simulated elections`}
      </div>
      <div style={{ display: "flex", justifyContent: "space-between", marginTop: 40, fontSize: 30, fontWeight: 600 }}>
        <span style={{ color: COLOR[meta.left_party] }}>{`${meta.candidates.left} (${meta.left_party}) ${pL}`}</span>
        <span style={{ color: COLOR.R }}>{`${100 - pL} ${meta.candidates.right} (R)`}</span>
      </div>
      <div style={{ display: "flex", marginTop: 14, height: 26, width: "100%" }}>
        <div style={{ width: `${pL}%`, background: COLOR[meta.left_party] }} />
        <div style={{ width: `${100 - pL}%`, background: COLOR.R }} />
      </div>
    </OgFrame>,
    { ...size, fonts },
  );
}
