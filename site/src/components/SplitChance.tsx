import type { ReactNode } from "react";
import { partyVar } from "@/lib/format";
import type { Party } from "@/lib/types";

// A race's chance as the posts show it (Matteo, 8 Oct): DEM WINS 58 | REP WINS 42 in party colours, the leader's
// number larger, a thin split bar underneath, then "of 100 simulations, 3 Nov".
export default function SplitChance({
  p,
  left,
  size = "lg",
  when = "3 Nov",
  render = (n) => n,
}: {
  p: number;
  left: Party;
  size?: "lg" | "sm";
  when?: string;
  render?: (n: number) => ReactNode;
}) {
  const l = Math.round(p * 100);
  const sides: [string, number, string][] = [
    [`${left === "I" ? "IND" : "DEM"} WINS`, l, partyVar(left)],
    ["REP WINS", 100 - l, "var(--rep)"],
  ];
  const big = size === "lg" ? "text-[3.6rem]" : "text-[2.3rem]";
  const small = size === "lg" ? "text-[2.6rem]" : "text-[1.6rem]";
  return (
    <div>
      <div className="grid grid-cols-[auto_auto] items-baseline justify-start gap-x-6">
        {sides.map(([label, , c]) => (
          <p key={label} className={`${size === "lg" ? "text-[0.8rem]" : "text-[0.66rem]"} font-bold tracking-[0.06em]`} style={{ color: c }}>{label}</p>
        ))}
        {sides.map(([label, n, c]) => (
          <p key={label} className={`mt-1 font-extrabold leading-none tracking-[-0.02em] tabular-nums ${n < 50 ? small : big}`} style={{ color: c }}>
            {render(n)}
          </p>
        ))}
      </div>
      <div className={`mt-3 flex ${size === "lg" ? "h-[6px]" : "h-[4px]"}`} aria-hidden="true">
        <div style={{ width: `${l}%`, background: partyVar(left) }} />
        <div style={{ width: `${100 - l}%`, background: "var(--rep)" }} />
      </div>
      <p className={`mt-2 ${size === "lg" ? "text-[0.9rem]" : "text-[0.75rem]"} text-ink-2`}>{`of 100 simulations, ${when}`}</p>
    </div>
  );
}
