"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { getMe, logout, isAuthed } from "../lib/auth";

export default function PortalShell({ children }) {
  const router = useRouter();
  const [me, setMe] = useState(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (!isAuthed()) {
      router.replace("/login");
      return;
    }
    getMe().then((u) => {
      if (!u) {
        router.replace("/login");
      } else {
        setMe(u);
        setReady(true);
      }
    });
  }, [router]);

  async function onLogout() {
    await logout();
    router.replace("/login");
  }

  if (!ready) {
    return <div className="min-h-screen grid place-items-center text-slate-400">Loading…</div>;
  }

  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-10 border-b border-slate-200 bg-white/80 backdrop-blur">
        <div className="mx-auto flex max-w-5xl items-center justify-between gap-2 px-5 py-3.5">
          <Link href="/dashboard" className="flex shrink-0 items-center gap-2 font-bold text-slate-900">
            <span className="grid h-8 w-8 place-items-center rounded-lg bg-brand-600 text-white">F</span>
            FaceFolio
          </Link>
          <div className="flex min-w-0 items-center gap-2 text-sm sm:gap-3">
            {!me.is_approved && !me.is_superuser && (
              <span className="badge shrink-0 bg-amber-100 text-amber-700">Pending</span>
            )}
            <span className="hidden truncate text-slate-500 sm:inline">{me.username}</span>
            <button onClick={onLogout} className="btn-ghost shrink-0 !py-1.5 !px-3">Log out</button>
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-5xl px-5 py-8">{children}</main>
    </div>
  );
}
