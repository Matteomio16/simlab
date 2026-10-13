import { ImageResponse } from "next/og";
import { HAS_FORECAST, IS_SAMPLE, houseDistricts, load } from "@/lib/data";
import { in100, longDate, margin, surname } from "@/lib/format";
import { consensusName } from "@/lib/house";
import { SHOW } from "@/lib/site";
import { OG_SIZE, OgFrame, ogFonts } from "@/lib/og";

export const alt = "A NotAPoll.org House race forecast";
export const size = OG_SIZE;
export const contentType = "image/png";

const COLOR = { D: "#2a78d6", R: "#e34948", I: "#7e879a" } as const;
const seats = () => (HAS_FORECAST && SHOW.chamberHome && SHOW.houseSeats ? houseDistricts() : []);

export function generateStaticParams() {
  const ds = seats();
  return ds.length ? ds.map((d) => ({ slug: d.slug })) : [{ slug: "none" }];
}

// The same card as a Senate race's, for each House seat.
export default async function Image({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const fonts = await ogFonts();
  const d = seats().find((x) => x.slug === slug);
  if (!d) {
    return new ImageResponse(<OgFrame kicker="2026 House forecast"><div style={{ display: "flex", fontSize: 80, fontWeight: 800 }}>NotAPoll.org</div></OgFrame>, { ...size, fonts });
  }
  const { forecast } = load();
  const kicker = `${d.title} · House`;
  if (d.p == null) {
    return new ImageResponse(
      <OgFrame kicker={kicker} date={longDate(forecast.date)} sample={IS_SAMPLE}>
        <div style={{ display: "flex", fontSize: 64, fontWeight: 800, letterSpacing: -1.5, lineHeight: 1.05 }}>
          {`Uncontested: only a ${d.fixed === "R" ? "Republican" : "Democrat"} is on the ballot`}
        </div>
      </OgFrame>,
      { ...size, fonts },
    );
  }
  const left = d.dName ?? (d.left === "I" ? "Independent" : "Democrat");
  const right = d.rName ?? "Republican";
  const pL = in100(d.p);
  const lead = pL >= 50 ? { name: left, n: pL } : { name: right, n: 100 - pL };
  const bench = [
    `Middle result ${d.margin ? margin(d.margin.p50, d.left) : "n/a"}`,
    `Statistics only ${d.statsP == null ? "n/a" : `${surname(left)} ${in100(d.statsP)}`}`,
    `Experts ${consensusName(d.consensus) ?? "n/a"}`,
  ];
  return new ImageResponse(
    <OgFrame kicker={kicker} date={longDate(forecast.date)} sample={IS_SAMPLE} bench={bench}>
      <div style={{ display: "flex", fontSize: 64, fontWeight: 800, letterSpacing: -1.5, lineHeight: 1.05 }}>
        {`${surname(lead.name)} wins ${lead.n} of 100 simulated elections`}
      </div>
      <div style={{ display: "flex", justifyContent: "space-between", marginTop: 40, fontSize: 30, fontWeight: 600 }}>
        <span style={{ color: COLOR[d.left] }}>{`${left} (${d.left}) ${pL}`}</span>
        <span style={{ color: COLOR.R }}>{`${100 - pL} ${right} (R)`}</span>
      </div>
      <div style={{ display: "flex", marginTop: 14, height: 26, width: "100%" }}>
        <div style={{ width: `${pL}%`, background: COLOR[d.left] }} />
        <div style={{ width: `${100 - pL}%`, background: COLOR.R }} />
      </div>
    </OgFrame>,
    { ...size, fonts },
  );
}
