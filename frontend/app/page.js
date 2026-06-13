import Link from "next/link";

export default function Home() {
  return (
    <div className="min-h-screen">
      <header className="mx-auto flex max-w-5xl items-center justify-between px-5 py-4">
        <div className="flex items-center gap-2 font-bold">
          <span className="grid h-8 w-8 place-items-center rounded-lg bg-brand-600 text-white">F</span>
          FaceFolio
        </div>
        <nav className="flex items-center gap-3 text-sm">
          <Link href="/login" className="font-medium text-slate-600 hover:text-slate-900">Sign in</Link>
          <Link href="/signup" className="btn-primary !py-2">Request account</Link>
        </nav>
      </header>

      <main className="mx-auto max-w-3xl px-5 py-20 text-center">
        <span className="badge bg-brand-100 text-brand-700">Self-hosted event photography</span>
        <h1 className="mt-4 text-4xl font-extrabold tracking-tight text-slate-900 sm:text-5xl">
          Find your photos with a selfie.
        </h1>
        <p className="mx-auto mt-4 max-w-xl text-lg text-slate-600">
          Photographers upload an event’s photos. Guests scan a QR code, take a selfie, and instantly
          see every shot they’re in — free to download, no account needed.
        </p>
        <div className="mt-8 flex justify-center gap-3">
          <Link href="/signup" className="btn-primary">Get started as a photographer</Link>
          <Link href="/login" className="btn-ghost">Sign in</Link>
        </div>

        <div className="mx-auto mt-16 grid max-w-2xl gap-4 sm:grid-cols-3 text-left">
          {[
            ["1 · Upload", "Batch-upload your event photos. Faces are indexed automatically."],
            ["2 · Share QR", "Each event gets a unique QR code to print or share with guests."],
            ["3 · Selfie", "Guests scan, snap a selfie, and download every photo they appear in."],
          ].map(([t, d]) => (
            <div key={t} className="card">
              <h3 className="font-semibold text-brand-700">{t}</h3>
              <p className="mt-1 text-sm text-slate-500">{d}</p>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}
