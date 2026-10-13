import Link from "next/link";

// Senate | House, a small frosted-glass switch that stays at the top of the forecast while you scroll (Matteo, 12 Oct).
export default function ChamberSwitch({ active }: { active: "senate" | "house" }) {
  const items = [
    { k: "senate", label: "Senate", href: "/" },
    { k: "house", label: "House", href: "/house" },
  ] as const;
  return (
    <div className="pointer-events-none sticky top-3 z-30 flex justify-center">
      <nav aria-label="Chamber" className="seg pointer-events-auto text-[0.84rem]">
        {items.map((i) => (
          <Link key={i.k} href={i.href} aria-current={i.k === active ? "page" : undefined} className="!px-4">
            {i.label}
          </Link>
        ))}
      </nav>
    </div>
  );
}
