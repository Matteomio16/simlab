import Link from "next/link";

// The earlier ballot-box mark, kept only for places too small for the hills.
export function Logomark({ size = 28 }: { size?: number }) {
  const step = size / 4;
  const r = size * 0.085;
  const sw = Math.max(1.5, size / 14);
  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} aria-hidden="true" className="shrink-0">
      <rect x={sw / 2} y={sw / 2} width={size - sw} height={size - sw} fill="none" stroke="currentColor" strokeWidth={sw} />
      {[1, 2, 3].flatMap((i) =>
        [1, 2, 3].map((j) => (
          <circle key={`${i}${j}`} cx={step * j} cy={step * i} r={r} fill={i === 2 && j === 2 ? "var(--sim)" : "currentColor"} />
        )),
      )}
    </svg>
  );
}

// The locked wordmark (publishing.md): "NotAPoll" in IBM Plex Sans 700, ".org" in the simulation purple.
export function Wordmark({ className = "" }: { className?: string }) {
  return (
    <span className={`font-brand font-bold tracking-[-0.01em] ${className}`}>
      NotAPoll<span className="text-sim">.org</span>
    </span>
  );
}

// The approved lockup from the brand kit (brand/final, `python -m brand.final`): two hills on the wordmark's baseline,
// text outlined, so it needs no webfont. Swap the files in public/brand to change it.
export function Lockup({ dark = false, height = 38 }: { dark?: boolean; height?: number }) {
  return (
    <Link href="/" className="flex items-center" aria-label="NotAPoll.org home">
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img src={dark ? "/brand/lockup-dark.svg" : "/brand/lockup-light.svg"} alt="NotAPoll.org" style={{ height, width: "auto" }} />
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
