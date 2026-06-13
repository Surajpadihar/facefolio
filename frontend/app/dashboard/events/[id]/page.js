"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import PortalShell from "../../../components/PortalShell";
import {
  getEvent,
  listPhotos,
  uploadPhotos,
  deletePhoto,
  reindexPhoto,
  getCollaborators,
  addCollaborator,
  removeCollaborator,
  fetchQrObjectUrl,
} from "../../../lib/portalApi";

const STATUS_STYLES = {
  uploaded: "bg-slate-100 text-slate-600",
  processing: "bg-blue-100 text-blue-700",
  ready: "bg-amber-100 text-amber-700",
  indexed: "bg-green-100 text-green-700",
  failed: "bg-red-100 text-red-700",
};

export default function EventDetailPage() {
  return (
    <PortalShell>
      <EventDetail />
    </PortalShell>
  );
}

function EventDetail() {
  const { id } = useParams();
  const [event, setEvent] = useState(null);
  const [photos, setPhotos] = useState([]);
  const [error, setError] = useState(null);
  const pollRef = useRef(null);

  const refreshPhotos = useCallback(async () => {
    try {
      const list = await listPhotos(id);
      setPhotos(list);
      const settling = list.some((p) => ["uploaded", "processing", "ready"].includes(p.status));
      if (!settling && pollRef.current) {
        clearInterval(pollRef.current);
        pollRef.current = null;
      }
      return settling;
    } catch (e) {
      setError(e.message);
    }
  }, [id]);

  useEffect(() => {
    getEvent(id).then(setEvent).catch((e) => setError(e.message));
    refreshPhotos();
    return () => pollRef.current && clearInterval(pollRef.current);
  }, [id, refreshPhotos]);

  function startPolling() {
    if (pollRef.current) return;
    pollRef.current = setInterval(refreshPhotos, 3000);
  }

  if (error) return <p className="text-red-600">{error}</p>;
  if (!event) return <p className="text-slate-400">Loading…</p>;

  const indexed = photos.filter((p) => p.status === "indexed").length;

  return (
    <div>
      <Link href="/dashboard" className="text-sm text-slate-500 hover:text-slate-700">← All events</Link>
      <div className="mt-2 mb-6 flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold">{event.name}</h1>
          <p className="text-sm text-slate-500">
            {event.date} · {photos.length} photos ({indexed} indexed) · expires {event.expires_at?.slice(0, 10)}
          </p>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="min-w-0 space-y-6 lg:col-span-1">
          <QrCard eventId={id} guestUrl={event.guest_url} />
          <CollaboratorsCard eventId={id} />
        </div>
        <div className="min-w-0 space-y-6 lg:col-span-2">
          <UploadCard eventId={id} onUploaded={() => { refreshPhotos(); startPolling(); }} />
          <PhotosCard photos={photos} onChange={refreshPhotos} />
        </div>
      </div>
    </div>
  );
}

function QrCard({ eventId, guestUrl }) {
  const [qr, setQr] = useState(null);
  const [copied, setCopied] = useState(false);
  useEffect(() => {
    fetchQrObjectUrl(eventId).then(setQr).catch(() => {});
  }, [eventId]);

  return (
    <div className="card">
      <h3 className="font-semibold">Guest QR code</h3>
      <p className="mb-3 text-sm text-slate-500">Print or share this so guests can find their photos.</p>
      {qr ? (
        <img src={qr} alt="event QR" className="mx-auto h-44 w-44 rounded-lg ring-1 ring-slate-200" />
      ) : (
        <div className="mx-auto grid h-44 w-44 place-items-center rounded-lg bg-slate-100 text-slate-400">…</div>
      )}
      <div className="mt-4 flex flex-wrap gap-2">
        {qr && (
          <a href={qr} download={`event-${eventId}-qr.png`} className="btn-ghost flex-1 whitespace-nowrap">Download PNG</a>
        )}
        <button
          className="btn-ghost flex-1 whitespace-nowrap"
          onClick={() => {
            navigator.clipboard?.writeText(guestUrl);
            setCopied(true);
            setTimeout(() => setCopied(false), 1500);
          }}
        >
          {copied ? "Copied!" : "Copy link"}
        </button>
      </div>
      <a href={guestUrl} target="_blank" rel="noreferrer" className="mt-2 block truncate text-center text-xs text-brand-600 hover:underline">
        {guestUrl}
      </a>
    </div>
  );
}

function UploadCard({ eventId, onUploaded }) {
  const [progress, setProgress] = useState(null);
  const [error, setError] = useState(null);
  const [summary, setSummary] = useState(null);
  const inputRef = useRef(null);

  async function onFiles(e) {
    const files = Array.from(e.target.files || []);
    if (!files.length) return;
    setError(null);
    setSummary(null);
    setProgress(0);
    try {
      const res = await uploadPhotos(eventId, files, setProgress);
      setSummary(`Uploaded ${res.created.length}` + (res.rejected.length ? `, ${res.rejected.length} rejected` : ""));
      onUploaded();
    } catch (err) {
      setError(err.message);
    } finally {
      setProgress(null);
      if (inputRef.current) inputRef.current.value = "";
    }
  }

  return (
    <div className="card">
      <h3 className="font-semibold">Upload photos</h3>
      <p className="mb-3 text-sm text-slate-500">JPEG, PNG, WebP or HEIC · up to 60 per batch, 30&nbsp;MB each · faces indexed automatically.</p>
      <label className="flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed border-slate-300 px-6 py-8 text-center hover:border-brand-400 hover:bg-brand-50/40">
        <span className="text-sm font-medium text-slate-700">Click to choose photos</span>
        <span className="text-xs text-slate-400">or drag them onto this box</span>
        <input ref={inputRef} type="file" accept="image/*" multiple className="hidden" onChange={onFiles} />
      </label>
      {progress !== null && (
        <div className="mt-3 h-2 overflow-hidden rounded-full bg-slate-100">
          <div className="h-full bg-brand-600 transition-all" style={{ width: `${progress}%` }} />
        </div>
      )}
      {summary && <p className="mt-3 text-sm text-green-700">{summary}</p>}
      {error && <p className="mt-3 text-sm text-red-600">{error}</p>}
    </div>
  );
}

function PhotosCard({ photos, onChange }) {
  async function onDelete(id) {
    await deletePhoto(id);
    onChange();
  }
  async function onReindex(id) {
    await reindexPhoto(id);
    onChange();
  }

  if (!photos.length) {
    return <div className="card text-center text-slate-400">No photos yet — upload some above.</div>;
  }
  return (
    <div className="card">
      <h3 className="mb-3 font-semibold">Photos ({photos.length})</h3>
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
        {photos.map((p) => (
          <div key={p.id} className="group relative overflow-hidden rounded-lg ring-1 ring-slate-200">
            {p.thumbnail_url ? (
              <img src={p.thumbnail_url} alt="" className="aspect-square w-full object-cover" />
            ) : (
              <div className="grid aspect-square w-full place-items-center bg-slate-100 text-xs text-slate-400">processing…</div>
            )}
            <div className="absolute left-1.5 top-1.5 flex gap-1">
              <span className={`badge ${STATUS_STYLES[p.status] || "bg-slate-100"}`}>{p.status}</span>
              {p.status === "indexed" && (
                <span className="badge bg-white/90 text-slate-700">{p.face_count} face{p.face_count === 1 ? "" : "s"}</span>
              )}
            </div>
            <div className="absolute inset-x-0 bottom-0 flex justify-end gap-1 bg-gradient-to-t from-black/50 to-transparent p-1.5 opacity-0 transition group-hover:opacity-100">
              {p.status === "failed" && (
                <button onClick={() => onReindex(p.id)} className="rounded bg-white/90 px-2 py-1 text-xs font-medium">Retry</button>
              )}
              <button onClick={() => onDelete(p.id)} className="rounded bg-white/90 px-2 py-1 text-xs font-medium text-red-600">Delete</button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function CollaboratorsCard({ eventId }) {
  const [list, setList] = useState([]);
  const [username, setUsername] = useState("");
  const [error, setError] = useState(null);

  const refresh = useCallback(() => {
    getCollaborators(eventId).then((d) => setList(d.collaborators || [])).catch(() => {});
  }, [eventId]);
  useEffect(() => { refresh(); }, [refresh]);

  async function onAdd(e) {
    e.preventDefault();
    setError(null);
    try {
      const d = await addCollaborator(eventId, username.trim());
      setList(d.collaborators || []);
      setUsername("");
    } catch (err) {
      setError(err.message);
    }
  }
  async function onRemove(u) {
    await removeCollaborator(eventId, u);
    refresh();
  }

  return (
    <div className="card">
      <h3 className="font-semibold">Collaborators</h3>
      <p className="mb-3 text-sm text-slate-500">Approved photographers who can also upload.</p>
      <ul className="mb-3 space-y-1.5">
        {list.length === 0 && <li className="text-sm text-slate-400">None yet.</li>}
        {list.map((u) => (
          <li key={u} className="flex items-center justify-between rounded-lg bg-slate-50 px-3 py-1.5 text-sm">
            <span>{u}</span>
            <button onClick={() => onRemove(u)} className="text-xs text-red-600 hover:underline">Remove</button>
          </li>
        ))}
      </ul>
      <form onSubmit={onAdd} className="flex gap-2">
        <input className="input" placeholder="username" value={username} onChange={(e) => setUsername(e.target.value)} />
        <button className="btn-ghost">Add</button>
      </form>
      {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
    </div>
  );
}
