import Link from "next/link";
import { SITE } from "@/lib/site";
import { Logomark, SwingBand, Wordmark } from "./Brand";

export default function Footer() {
  const social = SITE.social.filter((s) => s.live);
  return (
    <footer className="mt-24">
      <SwingBand className="h-[3px]" />
      <div className="bg-strip text-strip-fg">
        <div className="mx-auto grid max-w-6xl gap-10 px-4 py-12 sm:px-6 md:grid-cols-[1.4fr_1fr_1fr]">
          <div>
            <div className="flex items-center gap-2.5">
              <Logomark size={24} />
              <Wordmark className="text-lg" />
            </div>
            <p className="mt-4 max-w-sm text-sm leading-relaxed opacity-80">
              A social simulation of the 2026 US midterms. Synthetic voters, simulated elections, every number beside
              the poll average, the market and Cook.
            </p>
            <p className="mt-6 font-mono text-[0.7rem] uppercase tracking-[0.1em] opacity-70">{SITE.label}</p>
          </div>
          <div className="text-sm">
            <p className="font-mono text-[0.7rem] uppercase tracking-[0.1em] opacity-60">Read</p>
            <ul className="mt-3 space-y-2 opacity-90">
              <li><Link href="/methods" className="hover:underline">Methods</Link></li>
              <li><Link href="/lab-notes" className="hover:underline">Lab notes</Link></li>
              <li><Link href="/about" className="hover:underline">About</Link></li>
            </ul>
          </div>
          <div className="text-sm">
            <p className="font-mono text-[0.7rem] uppercase tracking-[0.1em] opacity-60">Follow</p>
            <ul className="mt-3 space-y-2 opacity-90">
              {social.length === 0 && <li className="opacity-70">Accounts open soon</li>}
              {social.map((s) => (
                <li key={s.name}>
                  <a href={s.url} rel="noopener" target="_blank" className="hover:underline">
                    {s.name} <span className="opacity-60">{s.handle}</span>
                  </a>
                </li>
              ))}
            </ul>
          </div>
        </div>
        <div className="border-t border-white/10">
          <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-4 py-5 text-xs opacity-75 sm:px-6">
            <span>
              By{" "}
              <a href={SITE.studio.url} className="underline underline-offset-2 hover:opacity-100">
                {SITE.studio.name}
              </a>
            </span>
            <span>Poll data from Wikipedia under CC BY-SA 4.0. Not affiliated with any campaign or party.</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
