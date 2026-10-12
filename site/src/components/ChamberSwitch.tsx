import Link from "next/link";

// Senate | House, a small frosted-glass switch that stays at the top of the forecast while you scroll (Matteo, 12 Oct).
export default function ChamberSwitch({ active }: { active: "senate" | "house" }) {
  const items = [
    { k: "senate", label: "Senate", href: "/" },
    { k: "house", label: "House", href: "/house" },
  ] as const;
  return (
    <div className="pointer-events-none sticky top-3 z-30 flex justify-center">
      <nav
        aria-label="Chamber"
        className="pointer-events-auto inline-flex gap-0.5 rounded-full border border-white/70 bg-[rgba(246,246,243,0.62)] p-[3px] shadow-[0_6px_24px_rgba(17,17,16,0.10),inset_0_1px_0_rgba(255,255,255,0.8)] ring-1 ring-black/[0.06] backdrop-blur-xl backdrop-saturate-150"
      >
        {items.map((i) => (
          <Link
            key={i.k}
            href={i.href}
            aria-current={i.k === active ? "page" : undefined}
            className={`rounded-full px-4 py-1.5 text-[0.84rem] font-semibold transition-all ${
              i.k === active ? "bg-white text-ink shadow-[0_1px_3px_rgba(17,17,16,0.14)]" : "text-ink-2 hover:text-ink"
            }`}
          >
            {i.label}
          </Link>
        ))}
      </nav>
    </div>
  );
}
