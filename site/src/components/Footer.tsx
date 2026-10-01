import Link from "next/link";
import { SHOW, SITE } from "@/lib/site";
import { Lockup, SwingBand } from "./Brand";

export default function Footer({ forecast }: { forecast: boolean }) {
  const social = SITE.social.filter((s) => s.live);
  return (
    <footer className="mt-28">
      <SwingBand className="h-[3px]" />
      <div className="bg-navy text-navy-fg">
        <div className="mx-auto grid max-w-[1200px] gap-10 px-4 py-12 text-sm sm:px-6 md:grid-cols-[2fr_1fr_1fr]">
          <div>
            <Lockup dark stacked height={72} />
            <p className="mt-3 max-w-md leading-relaxed">
              A forecast of the 2026 US midterms built by social simulation. Voter personas and simulated elections;
              every number beside the poll average, the prediction markets and the Cook Political Report.
            </p>
          </div>
          <div>
            <p className="font-bold uppercase tracking-[0.07em] text-[0.7rem] text-white">Project</p>
            <ul className="mt-3 space-y-2">
              {SHOW.methods && <li><Link href="/methods" className="hover:text-white">Methods</Link></li>}
              {SHOW.labNotes && <li><Link href="/lab-notes" className="hover:text-white">Lab notes</Link></li>}
              {SHOW.changelog && <li><Link href="/changelog" className="hover:text-white">Changelog</Link></li>}
              {SHOW.trackRecord && <li><Link href="/track-record" className="hover:text-white">Track record</Link></li>}
              {forecast && <li><Link href="/archive" className="hover:text-white">Archive</Link></li>}
              {SHOW.about && <li><Link href="/about" className="hover:text-white">About</Link></li>}
              <li><a href="mailto:hello@notapoll.org" className="hover:text-white">hello@notapoll.org</a></li>
            </ul>
          </div>
          <div>
            <p className="font-bold uppercase tracking-[0.07em] text-[0.7rem] text-white">Follow</p>
            <ul className="mt-3 space-y-2">
              {social.length === 0 && <li className="opacity-70">Accounts open soon</li>}
              {social.map((s) => (
                <li key={s.name}>
                  <a href={s.url} rel="noopener" target="_blank" className="hover:text-white">{s.name} <span className="opacity-60">{s.handle}</span></a>
                </li>
              ))}
            </ul>
          </div>
        </div>
        <div className="border-t border-white/10">
          <div className="mx-auto flex max-w-[1200px] flex-wrap justify-between gap-3 px-4 py-5 text-xs opacity-80 sm:px-6">
            <span>
              Independent; not affiliated with any campaign or party.
            </span>
            <span>Poll data from Wikipedia, CC BY-SA 4.0.</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
