"use client";

import { useState } from "react";
import Link from "next/link";
import { signup } from "../lib/auth";

export default function SignupPage() {
  const [form, setForm] = useState({ username: "", email: "", password: "" });
  const [error, setError] = useState(null);
  const [done, setDone] = useState(false);
  const [busy, setBusy] = useState(false);

  function set(k) {
    return (e) => setForm({ ...form, [k]: e.target.value });
  }

  async function onSubmit(e) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await signup(form.username, form.email, form.password);
      setDone(true);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="min-h-screen grid place-items-center px-5">
      <div className="w-full max-w-sm">
        <div className="mb-6 text-center">
          <div className="mx-auto mb-3 grid h-12 w-12 place-items-center rounded-xl bg-brand-600 text-xl font-bold text-white">F</div>
          <h1 className="text-2xl font-bold">Request an account</h1>
          <p className="text-sm text-slate-500">A FaceFolio admin approves new photographers</p>
        </div>

        {done ? (
          <div className="card text-center">
            <div className="mx-auto mb-3 grid h-12 w-12 place-items-center rounded-full bg-green-100 text-2xl">✓</div>
            <h2 className="text-lg font-semibold">Account created</h2>
            <p className="mt-1 text-sm text-slate-500">
              An admin needs to approve your account before you can create events and upload photos.
            </p>
            <Link href="/login" className="btn-primary mt-4 inline-flex">Go to sign in</Link>
          </div>
        ) : (
          <>
            <form onSubmit={onSubmit} className="card space-y-4">
              {error && <div className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-600">{error}</div>}
              <div>
                <label className="label">Username</label>
                <input className="input" value={form.username} onChange={set("username")} autoFocus required />
              </div>
              <div>
                <label className="label">Email</label>
                <input className="input" type="email" value={form.email} onChange={set("email")} required />
              </div>
              <div>
                <label className="label">Password</label>
                <input className="input" type="password" value={form.password} onChange={set("password")} minLength={8} required />
                <p className="mt-1 text-xs text-slate-400">At least 8 characters.</p>
              </div>
              <button className="btn-primary w-full" disabled={busy}>{busy ? "Creating…" : "Request account"}</button>
            </form>
            <p className="mt-4 text-center text-sm text-slate-500">
              Already have an account?{" "}
              <Link href="/login" className="font-semibold text-brand-600 hover:text-brand-700">Sign in</Link>
            </p>
          </>
        )}
      </div>
    </div>
  );
}
