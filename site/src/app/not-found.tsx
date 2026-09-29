import Link from "next/link";

export default function NotFound() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-32 sm:px-6">
      <p className="kicker">404</p>
      <h1 className="mt-3 font-serif text-4xl text-ink">This page isn&rsquo;t in the simulation.</h1>
      <p className="mt-4 text-ink-2">
        <Link href="/" className="text-sim underline underline-offset-4">Back to the start</Link>
      </p>
    </div>
  );
}
