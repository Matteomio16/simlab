import Link from "next/link";
import { Lockup } from "./Brand";
import NextUpdate from "./NextUpdate";
import { SHOW } from "@/lib/site";

export default function Header({ forecast }: { forecast: boolean }) {
  const pages = [
    ...(SHOW.methods ? [{ href: "/methods", label: "Methods" }] : []),
    ...(SHOW.labNotes ? [{ href: "/lab-notes", label: "Lab notes" }] : []),
    ...(SHOW.about ? [{ href: "/about", label: "About" }] : []),
  ];
  const links = pages.length ? [{ href: "/", label: forecast ? "Senate" : "Home" }, ...pages] : [];
  return (
    <header>
      <div className="bg-navy text-navy-fg">
        <div className="mx-auto flex h-8 max-w-[1200px] items-center justify-between px-4 text-[0.7rem] font-semibold uppercase tracking-[0.08em] sm:px-6">
          <span>U.S. Midterms · November 3, 2026</span>
          <span className="flex items-center gap-5">
            {forecast && <NextUpdate />}
            <span className="hidden sm:inline">Social simulation, not a poll</span>
          </span>
        </div>
      </div>
      <div className="border-b border-rule">
        <div className="mx-auto flex h-16 max-w-[1200px] items-center justify-between px-4 sm:px-6">
          <Lockup />
          <nav aria-label="Main" className="flex items-center gap-4 whitespace-nowrap text-[0.84rem] font-semibold sm:gap-7 sm:text-[0.9rem]">
            {links.map((l, i) => (
              <Link key={l.href} href={l.href} className={`text-ink-2 hover:text-ink ${i === 0 ? "hidden sm:inline" : ""}`}>
                {l.label}
              </Link>
            ))}
          </nav>
        </div>
      </div>
    </header>
  );
}
