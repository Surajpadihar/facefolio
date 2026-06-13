"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import {
  getEvent,
  acceptConsent,
  searchSelfie,
  getGallery,
  downloadOneUrl,
  downloadZip,
} from "../../lib/api";

export default function EventPage() {
  const { token } = useParams();
  const [event, setEvent] = useState(null);
  const [error, setError] = useState(null);
  const [stage, setStage] = useState("loading"); // loading | consent | capture | results
  const [consentId, setConsentId] = useState(null);
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState(null);
  const [gallery, setGallery] = useState(null);

  useEffect(() => {
    getEvent(token)
      .then((e) => { setEvent(e); setStage("consent"); })
      .catch((err) => setError(err.message));
  }, [token]);

  async function onAccept() {
    setBusy(true);
    try {
      const c = await acceptConsent(token);
      setConsentId(c.consent_id);
      setStage("capture");
    } catch (e) { setError(e.message); } finally { setBusy(false); }
  }
  function onPick(e) {
    const f = e.target.files?.[0];
    setFile(f || null);
    setPreview(f ? URL.createObjectURL(f) : null);
  }
  async function onSearch() {
    if (!file) return;
    setBusy(true); setResult(null);
    try { setResult(await searchSelfie(token, consentId, file)); setStage("results"); }
    catch (e) { setError(e.message); } finally { setBusy(false); }
  }
  async function onBrowse() {
    setBusy(true);
    try { setGallery(await getGallery(token)); } catch (e) { setError(e.message); } finally { setBusy(false); }
  }

  const Shell = ({ children }) => (
    <div className="min-h-screen">
      <div className="mx-auto max-w-3xl px-5 py-8">
        <div className="mb-6 flex items-center gap-2 font-bold">
          <span className="grid h-8 w-8 place-items-center rounded-lg bg-brand-600 text-white">F</span>
          FaceFolio
        </div>
        {children}
      </div>
    </div>
  );

  if (error) return <Shell><div className="card text-red-600">{error}</div></Shell>;
  if (stage === "loading") return <Shell><p className="text-slate-400">Loading…</p></Shell>;

  return (
    <Shell>
      <h1 className="text-2xl font-bold">{event.name}</h1>
      <p className="text-sm text-slate-500">{event.date} · {event.photo_count} photos</p>
      {event.still_processing && (
        <div className="mt-3 rounded-lg bg-amber-50 px-4 py-2.5 text-sm text-amber-700">
          ⏳ Some photos are still processing — search again shortly for complete results.
        </div>
      )}

      <div className="mt-5">
        {stage === "consent" && (
          <div className="card">
            <h2 className="text-lg font-semibold">Find your photos with a selfie</h2>
            <p className="mt-2 text-sm leading-relaxed text-slate-600">
              To find you, we’ll scan the selfie you provide to create a temporary face signature and
              compare it against this event’s photos. <strong>Your selfie and its face signature are used
              only for this search and are not saved.</strong> This event’s photos are automatically deleted
              after the organizer’s retention period.
            </p>
            <p className="mt-2 text-xs text-slate-400">⚠️ Placeholder consent text — pending legal review before launch.</p>
            <button className="btn-primary mt-4" disabled={busy} onClick={onAccept}>
              {busy ? "…" : "I agree — continue"}
            </button>
          </div>
        )}

        {stage === "capture" && (
          <div className="card">
            <h2 className="text-lg font-semibold">Take or upload a selfie</h2>
            <label className="mt-3 flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed border-slate-300 px-6 py-8 text-center hover:border-brand-400 hover:bg-brand-50/40">
              <span className="text-sm font-medium text-slate-700">Tap to take a selfie or choose a photo</span>
              <input type="file" accept="image/*" capture="user" className="hidden" onChange={onPick} />
            </label>
            {preview && <img src={preview} alt="preview" className="mx-auto mt-4 h-40 w-40 rounded-xl object-cover ring-1 ring-slate-200" />}
            <button className="btn-primary mt-4 w-full" disabled={!file || busy} onClick={onSearch}>
              {busy ? "Searching…" : "Find my photos"}
            </button>
          </div>
        )}

        {stage === "results" && result && (
          <div className="space-y-5">
            {result.no_face_detected && (
              <div className="card">
                <p className="text-slate-700">We couldn’t find a face in that photo. Try a clear, front-facing selfie.</p>
                <button className="btn-primary mt-3" onClick={() => setStage("capture")}>Try again</button>
              </div>
            )}
            {!result.no_face_detected && result.no_match && (
              <div className="card">
                <h2 className="text-lg font-semibold">No matches found</h2>
                <p className="mt-1 text-sm text-slate-500">We didn’t find you in this event’s photos yet.</p>
                <div className="mt-4 flex gap-2">
                  <button className="btn-primary" onClick={() => setStage("capture")}>Retry selfie</button>
                  <button className="btn-ghost" onClick={onBrowse} disabled={busy}>Browse full gallery</button>
                </div>
              </div>
            )}
            {!result.no_match && (
              <div>
                <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
                  <h2 className="text-lg font-semibold">Found you in {result.match_count} photo{result.match_count === 1 ? "" : "s"} 🎉</h2>
                  <button className="btn-primary" onClick={() => downloadZip(token, result.matches.map((m) => m.id), event.name)}>
                    Download all (ZIP)
                  </button>
                </div>
                <Grid token={token} photos={result.matches} />
                <button className="btn-ghost mt-2" onClick={() => setStage("capture")}>Search again</button>
              </div>
            )}
            {gallery && (
              <div>
                <h2 className="mb-3 text-lg font-semibold">Full gallery ({gallery.length})</h2>
                <Grid token={token} photos={gallery} />
              </div>
            )}
          </div>
        )}
      </div>
    </Shell>
  );
}

function Grid({ token, photos }) {
  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
      {photos.map((p) => (
        <a key={p.id} href={downloadOneUrl(token, p.id)} className="group relative block overflow-hidden rounded-xl ring-1 ring-slate-200" title="Download">
          <img src={p.thumbnail_url} alt="" className="aspect-square w-full object-cover transition group-hover:scale-105" />
          {typeof p.score === "number" && (
            <span className="badge absolute left-1.5 top-1.5 bg-white/90 text-slate-700">{(p.score * 100).toFixed(0)}% match</span>
          )}
          <span className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/50 to-transparent p-1.5 text-center text-xs font-medium text-white opacity-0 transition group-hover:opacity-100">
            ↓ Download
          </span>
        </a>
      ))}
    </div>
  );
}
