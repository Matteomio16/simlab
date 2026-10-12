// The change marker beside each chamber's headline (Matteo, 12 Oct): how many points of chance a party gained over
// the last week, from the published history. Hidden until there are three days of forecasts.
const MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

export default function Trend({ points, up, down }: { points: { date: string; p: number }[]; up: "Democrats" | "Republicans"; down: "Democrats" | "Republicans" }) {
  if (points.length < 3) return null;
  const last = points[points.length - 1];
  const weekAgo = new Date(Date.parse(`${last.date}T12:00:00Z`) - 7 * 86400000).toISOString().slice(0, 10);
  const base = [...points].reverse().find((p) => p.date <= weekAgo) ?? points[0];
  const delta = Math.round((last.p - base.p) * 100);
  const since = base.date <= weekAgo ? "this week" : `since ${Number(base.date.slice(8, 10))} ${MON[Number(base.date.slice(5, 7)) - 1]}`;
  const party = delta > 0 ? up : down;
  const color = party === "Democrats" ? "var(--dem)" : "var(--rep)";
  return (
    <span
      className="ml-3 inline-flex -translate-y-[0.2em] items-center whitespace-nowrap rounded-full bg-paper-2 px-2.5 py-0.5 align-middle text-[0.78rem] font-bold tracking-normal"
      style={{ color: delta === 0 ? "var(--muted)" : color }}
    >
      {delta === 0 ? `No change ${since}` : `+${Math.abs(delta)} for ${party} ${since}`}
    </span>
  );
}
