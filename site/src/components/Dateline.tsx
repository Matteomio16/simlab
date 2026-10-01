import type { ReactNode } from "react";

// The label row that opens every page, as on the launch page: what the page is on the left, a second label on the right.
export default function Dateline({ left, right = "Democracy, rehearsed." }: { left: ReactNode; right?: ReactNode }) {
  return (
    <div className="flex items-baseline justify-between border-b border-rule pb-2 text-[0.72rem] font-bold uppercase tracking-[0.08em]">
      <span>{left}</span>
      {right && <span className="text-muted">{right}</span>}
    </div>
  );
}
