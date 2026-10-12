"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

// The main menu as the same frosted-glass control as the Senate | House switch, with the current page lit.
export default function NavLinks({ links, phoneHidden = [] }: { links: { href: string; label: string }[]; phoneHidden?: number[] }) {
  const path = usePathname() ?? "/";
  const here = (href: string) =>
    href === "/" ? path === "/" || /^\/(house|senate)(\/|$)/.test(path) : path === href || path.startsWith(`${href}/`);
  return (
    <nav aria-label="Main" className="seg seg-flat text-[0.8rem] sm:text-[0.86rem]">
      {links.map((l, i) => (
        <Link key={l.href} href={l.href} aria-current={here(l.href) ? "page" : undefined} className={phoneHidden.includes(i) ? "!hidden sm:!inline" : undefined}>
          {l.label}
        </Link>
      ))}
    </nav>
  );
}
