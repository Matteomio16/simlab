import Link from "next/link";
import { Lockup } from "./Brand";

export default function Header({ forecast }: { forecast: boolean }) {
  const links = [
    ...(forecast ? [{ href: "/", label: "Senate", wide: true }] : []),
    { href: "/methods", label: "Methods" },
    { href: "/lab-notes", label: "Lab notes" },
    { href: "/about", label: "About" },
  ];
  return (
    <header className="border-b border-hairline bg-paper/85 backdrop-blur supports-[backdrop-filter]:bg-paper/70 sticky top-0 z-30">
      <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-4 sm:px-6">
        <Lockup />
        <nav aria-label="Main" className="flex items-center gap-3.5 whitespace-nowrap text-[0.84rem] text-ink-2 sm:gap-6 sm:text-sm">
          {links.map((l) => (
            <Link key={l.href} href={l.href} className={`transition-colors hover:text-ink ${"wide" in l ? "hidden sm:inline" : ""}`}>
              {l.label}
            </Link>
          ))}
        </nav>
      </div>
    </header>
  );
}
