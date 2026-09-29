import type { Metadata } from "next";
import { IBM_Plex_Mono, IBM_Plex_Sans, Newsreader } from "next/font/google";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import SampleBanner from "@/components/SampleBanner";
import { HAS_FORECAST, IS_SAMPLE, PREVIEW } from "@/lib/data";
import { SITE } from "@/lib/site";
import "./globals.css";

const plexSans = IBM_Plex_Sans({ variable: "--font-plex-sans", subsets: ["latin"], weight: ["400", "500", "600", "700"] });
const plexMono = IBM_Plex_Mono({ variable: "--font-plex-mono", subsets: ["latin"], weight: ["400", "500"] });
const newsreader = Newsreader({ variable: "--font-newsreader", subsets: ["latin"], weight: ["400", "500"], style: ["normal", "italic"] });

export const metadata: Metadata = {
  metadataBase: new URL(SITE.url),
  title: { default: "NotAPoll.org: a social simulation of the 2026 midterms", template: "%s · NotAPoll.org" },
  description:
    "Synthetic voters react to each day's news; simulated elections turn their reactions into chances for every Senate race, beside the poll average, the market and Cook. Not a poll.",
  openGraph: { siteName: SITE.name, type: "website", locale: "en_US" },
  twitter: { card: "summary_large_image" },
  robots: PREVIEW ? { index: false, follow: false } : undefined,
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className={`${plexSans.variable} ${plexMono.variable} ${newsreader.variable}`}>
      <body className="min-h-screen font-sans">
        {HAS_FORECAST && IS_SAMPLE && <SampleBanner />}
        <Header forecast={HAS_FORECAST} />
        <main>{children}</main>
        <Footer />
      </body>
    </html>
  );
}
