import Link from "next/link";

// The approved lockup from the brand kit (brand/final, `python -m brand.final`): two hills on the wordmark's baseline,
// text outlined, so it needs no webfont. Swap the files in public/brand to change it.
export function Lockup({ dark = false, stacked = false, height = 38 }: { dark?: boolean; stacked?: boolean; height?: number }) {
  const src = `/brand/lockup-${stacked ? "stacked-" : ""}${dark ? "dark" : "light"}.svg`;
  return (
    <Link href="/" className="flex items-center" aria-label="NotAPoll.org home">
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img src={src} alt="NotAPoll.org" style={{ height, width: "auto" }} />
    </Link>
  );
}

export function SwingBand({ className = "h-1" }: { className?: string }) {
  return (
    <div
      aria-hidden="true"
      className={className}
      style={{ background: "linear-gradient(90deg, var(--dem) 0%, var(--dem) 30%, var(--sim) 50%, var(--rep) 70%, var(--rep) 100%)" }}
    />
  );
}

// The label every view with a number carries (publishing.md): the swing band over a navy strip.
export function SimLabel({ date, sample = false }: { date?: string; sample?: boolean }) {
  return (
    <div>
      <SwingBand className="h-[3px]" />
      <div className="flex flex-wrap items-center justify-between gap-x-4 gap-y-1 bg-navy px-3 py-1.5 text-[0.68rem] font-bold uppercase tracking-[0.08em] text-navy-fg">
        <span>Social simulation, not a poll</span>
        <span className="font-semibold opacity-80">
          {sample ? "Sample data · " : ""}
          {date}
        </span>
      </div>
    </div>
  );
}
