import type { Metadata } from "next";
import { Libre_Franklin } from "next/font/google";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import SampleBanner from "@/components/SampleBanner";
import { HAS_FORECAST, IS_SAMPLE, PREVIEW } from "@/lib/data";
import { SITE } from "@/lib/site";
import "./globals.css";

// Libre Franklin (the Franklin Gothic family of US newspapers and ballots), one variable file for every weight. The
// wordmark is the brand kit's outlined lockup, so it needs no font.
const franklin = Libre_Franklin({ variable: "--font-franklin", subsets: ["latin"], display: "swap" });

export const metadata: Metadata = {
  metadataBase: new URL(SITE.url),
  title: { default: "NotAPoll.org: the 2026 midterms, simulated every day", template: "%s · NotAPoll.org" },
  description:
    "A forecast of the 2026 US midterms built by social simulation: synthetic voters react to each day's news, and every number sits beside the poll average, the market and Cook. Not a poll.",
  openGraph: { siteName: SITE.name, type: "website", locale: "en_US" },
  twitter: { card: "summary_large_image" },
  robots: PREVIEW ? { index: false, follow: false } : undefined,
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className={`${franklin.variable}`}>
      <body className="min-h-screen font-sans text-ink">
        {HAS_FORECAST && IS_SAMPLE && <SampleBanner />}
        <Header forecast={HAS_FORECAST} />
        <main>{children}</main>
        <Footer forecast={HAS_FORECAST} />
      </body>
    </html>
  );
}
