import Link from "next/link";

export default function NotFound() {
  return (
    <div className="mx-auto max-w-[1200px] px-4 py-24 sm:px-6">
      <p className="label">Page not found</p>
      <h1 className="mt-3 text-[2.3rem] font-extrabold tracking-[-0.02em]">This page isn&rsquo;t here.</h1>
      <p className="mt-4 text-ink-2">
        <Link href="/" className="link font-semibold">Back to the forecast</Link>
      </p>
    </div>
  );
}
