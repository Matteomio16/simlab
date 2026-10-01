import type { Metadata } from "next";
import { readFileSync } from "node:fs";
import path from "node:path";
import { toHtml } from "@/lib/markdown";
import { ROOT } from "@/lib/root";
import Dateline from "@/components/Dateline";

export const metadata: Metadata = {
  title: "Changelog",
  description: "Every change to the NotAPoll.org method, dated.",
};

export default function Changelog() {
  const md = readFileSync(path.join(ROOT, "content", "changelog.md"), "utf8");
  return (
    <div className="mx-auto max-w-[1200px] px-4 pt-10 sm:px-6 sm:pt-12">
      <Dateline left="Changelog" />
      <h1 className="rise mt-6 max-w-3xl text-[2.3rem] font-extrabold leading-[1.08] tracking-[-0.02em] sm:text-[2.9rem]">
        Every change to the method, dated
      </h1>
      <div className="mt-8 border-t-[3px] border-rule-strong">
        <div className="prose-np max-w-[680px] [&>h2:first-child]:mt-4" dangerouslySetInnerHTML={{ __html: toHtml(md) }} />
      </div>
    </div>
  );
}
