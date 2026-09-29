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
      <OgFrame kicker="2026 Senate forecast">
        <div style={{ display: "flex", fontSize: 88, fontWeight: 800, letterSpacing: -2, lineHeight: 1.02 }}>The forecast begins October 12.</div>
        <div style={{ display: "flex", marginTop: 24, fontSize: 32, fontWeight: 600, color: "#3d434c", maxWidth: 980 }}>
          Synthetic voters react to each day&apos;s news; simulated elections turn their reactions into chances for all 35 Senate races.
        </div>
      </OgFrame>,
      { ...size, fonts },
    );
  }
  const { forecast } = load();
  const s = forecast.senate;
  return new ImageResponse(
    <OgFrame kicker="2026 Senate forecast" date={longDate(forecast.date)} sample={IS_SAMPLE} bench={[`Statistics only: ${in100(s.stats_only.p_r_50plus)} in 100`, `Prediction market: ${s.benchmarks.market == null ? "n/a" : `${in100(s.benchmarks.market)}%`}`]}>
      <div style={{ display: "flex", fontSize: 40, fontWeight: 600, color: "#3d434c" }}>Republicans hold the Senate in</div>
      <div style={{ display: "flex", alignItems: "baseline", marginTop: 6 }}>
        <span style={{ fontSize: 190, fontWeight: 800, color: "#d1432f", letterSpacing: -6, lineHeight: 1 }}>{in100(s.p_r_50plus)}</span>
        <span style={{ fontSize: 52, fontWeight: 800, marginLeft: 20 }}>of 100 simulated elections</span>
      </div>
      <div style={{ display: "flex", marginTop: 18, fontSize: 30, fontWeight: 600, color: "#6b7280" }}>
        Democrats reach 51 in {in100(s.p_d_caucus_51)} · independents decide in {in100(s.p_independents_decide)}
      </div>
    </OgFrame>,
    { ...size, fonts },
  );
}
