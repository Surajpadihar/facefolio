"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import PortalShell from "../components/PortalShell";
import { listEvents, createEvent } from "../lib/portalApi";

export default function DashboardPage() {
  return (
    <PortalShell>
      <Dashboard />
    </PortalShell>
  );
}

function Dashboard() {
  const [events, setEvents] = useState(null);
  const [error, setError] = useState(null);
  const [showForm, setShowForm] = useState(false);

  async function refresh() {
    try {
      setEvents(await listEvents());
    } catch (e) {
      setError(e.message);
    }
  }
  useEffect(() => {
    refresh();
  }, []);

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Your events</h1>
          <p className="text-sm text-slate-500">Create an event, upload photos, share the QR code.</p>
        </div>
        <button className="btn-primary" onClick={() => setShowForm((v) => !v)}>
          {showForm ? "Close" : "+ New event"}
        </button>
      </div>

      {error && <div className="mb-4 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-600">{error}</div>}

      {showForm && (
        <CreateEventForm
          onCreated={() => {
            setShowForm(false);
            refresh();
          }}
        />
      )}

      {events === null ? (
        <p className="text-slate-400">Loading…</p>
      ) : events.length === 0 ? (
        <div className="card text-center text-slate-500">
          <p className="text-lg">No events yet.</p>
          <p className="text-sm">Click “New event” to create your first one.</p>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {events.map((ev) => (
            <Link key={ev.id} href={`/dashboard/events/${ev.id}`} className="card transition hover:shadow-md hover:ring-brand-200">
              <div className="flex items-start justify-between">
                <h3 className="font-semibold text-slate-900">{ev.name}</h3>
                {ev.is_expired ? (
                  <span className="badge bg-red-100 text-red-700">Expired</span>
                ) : (
                  <span className="badge bg-green-100 text-green-700">Active</span>
                )}
              </div>
              <p className="mt-1 text-sm text-slate-500">{ev.date}</p>
              <p className="mt-4 text-xs text-slate-400">Manage photos & QR →</p>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}

function CreateEventForm({ onCreated }) {
  const [form, setForm] = useState({ name: "", date: "", retention_days: 90 });
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);

  function set(k) {
    return (e) => setForm({ ...form, [k]: e.target.value });
  }
  async function onSubmit(e) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await createEvent({ ...form, retention_days: Number(form.retention_days) });
      onCreated();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="card mb-6 grid gap-4 sm:grid-cols-3">
      {error && <div className="sm:col-span-3 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-600">{error}</div>}
      <div className="sm:col-span-1">
        <label className="label">Event name</label>
        <input className="input" value={form.name} onChange={set("name")} placeholder="Sarah & Tom’s Wedding" required />
      </div>
      <div>
        <label className="label">Date</label>
        <input className="input" type="date" value={form.date} onChange={set("date")} required />
      </div>
      <div>
        <label className="label">Retention (days)</label>
        <input className="input" type="number" min="1" value={form.retention_days} onChange={set("retention_days")} required />
      </div>
      <div className="sm:col-span-3">
        <button className="btn-primary" disabled={busy}>{busy ? "Creating…" : "Create event"}</button>
      </div>
    </form>
  );
}
