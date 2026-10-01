import { ImageResponse } from "next/og";
import { HAS_FORECAST, IS_SAMPLE, load } from "@/lib/data";
import { in100, longDate } from "@/lib/format";
import { OG_SIZE, OgFrame, ogFonts } from "@/lib/og";

export const dynamic = "force-static";
export const alt = "NotAPoll.org: the 2026 Senate forecast by social simulation";
export const size = OG_SIZE;
export const contentType = "image/png";

export default async function Image() {
  const fonts = await ogFonts();
  if (!HAS_FORECAST) {
    return new ImageResponse(
      <OgFrame kicker="Democracy, rehearsed.">
        <div style={{ display: "flex", fontSize: 96, fontWeight: 800, letterSpacing: -3, lineHeight: 1 }}>The 2026 midterms,</div>
        <div style={{ display: "flex", fontSize: 96, fontWeight: 800, letterSpacing: -3, lineHeight: 1.05, color: "#7a4fc0" }}>simulated every day.</div>
        <div style={{ display: "flex", marginTop: 26, fontSize: 32, fontWeight: 600, color: "#3d434c", maxWidth: 1000 }}>
          Not a poll. Voter personas, 40,000 simulated elections. Forecasts go public October 12.
        </div>
      </OgFrame>,
      { ...size, fonts },
    );
  }
  const { forecast } = load();
  const s = forecast.senate;
  return new ImageResponse(
    <OgFrame kicker="2026 Senate forecast" date={longDate(forecast.date)} sample={IS_SAMPLE} bench={[`Statistics only: ${in100(s.stats_only.p_r_50plus)} in 100`, `Prediction markets: ${s.benchmarks.market == null ? "n/a" : `${in100(s.benchmarks.market)}%`}`]}>
      <div style={{ display: "flex", fontSize: 40, fontWeight: 600, color: "#3d434c" }}>Republicans hold the Senate in</div>
      <div style={{ display: "flex", alignItems: "baseline", marginTop: 6 }}>
        <span style={{ fontSize: 190, fontWeight: 800, color: "#e34948", letterSpacing: -6, lineHeight: 1 }}>{in100(s.p_r_50plus)}</span>
        <span style={{ fontSize: 52, fontWeight: 800, marginLeft: 20 }}>of 100 simulated elections</span>
      </div>
      <div style={{ display: "flex", marginTop: 18, fontSize: 30, fontWeight: 600, color: "#6b7280" }}>
        Democrats reach 51 in {in100(s.p_d_caucus_51)} · independents decide in {in100(s.p_independents_decide)}
      </div>
    </OgFrame>,
    { ...size, fonts },
  );
}
