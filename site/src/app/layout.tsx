import type { Metadata } from "next";
import { IBM_Plex_Sans, Libre_Franklin, Source_Serif_4 } from "next/font/google";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import SampleBanner from "@/components/SampleBanner";
import { HAS_FORECAST, IS_SAMPLE, PREVIEW } from "@/lib/data";
import { SITE } from "@/lib/site";
import "./globals.css";

// Libre Franklin (the Franklin Gothic family of US newspapers and ballots) for headings, data and interface; Source
// Serif 4 for reading text. IBM Plex Sans only draws the locked wordmark.
const franklin = Libre_Franklin({ variable: "--font-franklin", subsets: ["latin"], weight: ["400", "500", "600", "700", "800"] });
const serif = Source_Serif_4({ variable: "--font-source-serif", subsets: ["latin"], weight: ["400", "600"], style: ["normal", "italic"] });
const plex = IBM_Plex_Sans({ variable: "--font-plex-sans", subsets: ["latin"], weight: ["700"] });

export const metadata: Metadata = {
  metadataBase: new URL(SITE.url),
  title: { default: "NotAPoll.org: 2026 Senate forecast by social simulation", template: "%s · NotAPoll.org" },
  description:
    "A forecast of the 2026 US midterms built by social simulation: synthetic voters react to each day's news, and every number sits beside the poll average, the market and Cook. Not a poll.",
  openGraph: { siteName: SITE.name, type: "website", locale: "en_US" },
  twitter: { card: "summary_large_image" },
  robots: PREVIEW ? { index: false, follow: false } : undefined,
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className={`${franklin.variable} ${serif.variable} ${plex.variable}`} suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: "document.documentElement.classList.add('js')" }} />
      </head>
      <body className="min-h-screen font-sans text-ink">
        {HAS_FORECAST && IS_SAMPLE && <SampleBanner />}
        <Header forecast={HAS_FORECAST} />
        <main>{children}</main>
        <Footer />
      </body>
    </html>
  );
}
