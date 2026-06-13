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

const wrap = { maxWidth: 880, margin: "0 auto", padding: "2rem 1.25rem", fontFamily: "system-ui, sans-serif" };
const btn = { background: "#111", color: "#fff", border: 0, borderRadius: 8, padding: ".7rem 1.2rem", fontSize: "1rem", cursor: "pointer" };
const btnLight = { ...btn, background: "#eee", color: "#111" };
const card = { border: "1px solid #e5e5e5", borderRadius: 12, padding: "1.25rem", background: "#fff" };

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
    try {
      setResult(await searchSelfie(token, consentId, file));
      setStage("results");
    } catch (e) { setError(e.message); } finally { setBusy(false); }
  }

  async function onBrowse() {
    setBusy(true);
    try { setGallery(await getGallery(token)); } catch (e) { setError(e.message); } finally { setBusy(false); }
  }

  if (error) return <main style={wrap}><h1>FaceFolio</h1><p style={{ color: "#b00" }}>{error}</p></main>;
  if (stage === "loading") return <main style={wrap}><p>Loading…</p></main>;

  return (
    <main style={wrap}>
      <h1 style={{ marginBottom: ".25rem" }}>{event.name}</h1>
      <p style={{ color: "#777", marginTop: 0 }}>{event.date} · {event.photo_count} photos</p>
      {event.still_processing && (
        <p style={{ background: "#fff7e6", padding: ".6rem .9rem", borderRadius: 8, color: "#8a6d3b" }}>
          ⏳ Some photos are still being processed — search again shortly for complete results.
        </p>
      )}

      {stage === "consent" && (
        <div style={card}>
          <h2 style={{ marginTop: 0 }}>Find your photos with a selfie</h2>
          <p style={{ color: "#444", lineHeight: 1.6 }}>
            To find you, we’ll scan the selfie you provide to create a temporary face signature and
            compare it against this event’s photos. <strong>Your selfie and its face signature are used
            only for this search and are not saved.</strong> This event’s photos are automatically deleted
            after the organizer’s retention period.
          </p>
          <p style={{ color: "#999", fontSize: ".85rem" }}>
            ⚠️ Placeholder consent text — must be reviewed for BIPA/GDPR before launch.
          </p>
          <button style={btn} disabled={busy} onClick={onAccept}>{busy ? "…" : "I agree — continue"}</button>
        </div>
      )}

      {stage === "capture" && (
        <div style={card}>
          <h2 style={{ marginTop: 0 }}>Take or upload a selfie</h2>
          <input type="file" accept="image/*" capture="user" onChange={onPick} />
          {preview && <div style={{ marginTop: "1rem" }}><img src={preview} alt="selfie preview" style={{ maxWidth: 220, borderRadius: 12 }} /></div>}
          <div style={{ marginTop: "1rem" }}>
            <button style={btn} disabled={!file || busy} onClick={onSearch}>{busy ? "Searching…" : "Find my photos"}</button>
          </div>
        </div>
      )}

      {stage === "results" && result && (
        <div>
          {result.no_face_detected && (
            <div style={card}>
              <p>We couldn’t find a face in that photo. Try a clear, front-facing selfie.</p>
              <button style={btn} onClick={() => setStage("capture")}>Try again</button>
            </div>
          )}
          {!result.no_face_detected && result.no_match && (
            <div style={card}>
              <h2 style={{ marginTop: 0 }}>No matches found</h2>
              <p style={{ color: "#444" }}>We didn’t find you in this event’s photos yet.</p>
              <button style={btn} onClick={() => setStage("capture")}>Retry selfie</button>{" "}
              <button style={btnLight} onClick={onBrowse}>Browse full gallery</button>
            </div>
          )}
          {!result.no_match && (
            <div>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <h2>Found you in {result.match_count} photo{result.match_count === 1 ? "" : "s"} 🎉</h2>
                <button style={btn} onClick={() => downloadZip(token, result.matches.map((m) => m.id), event.name)}>
                  Download all (ZIP)
                </button>
              </div>
              <Grid token={token} photos={result.matches} />
              <button style={btnLight} onClick={() => setStage("capture")}>Search again</button>
            </div>
          )}
          {gallery && (
            <div style={{ marginTop: "2rem" }}>
              <h2>Full gallery ({gallery.length})</h2>
              <Grid token={token} photos={gallery} />
            </div>
          )}
        </div>
      )}
    </main>
  );
}

function Grid({ token, photos }) {
  return (
    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(150px, 1fr))", gap: "0.75rem", margin: "1rem 0" }}>
      {photos.map((p) => (
        <a key={p.id} href={downloadOneUrl(token, p.id)} style={{ display: "block" }} title="Download">
          <img src={p.thumbnail_url} alt="" style={{ width: "100%", borderRadius: 10, display: "block", aspectRatio: "1", objectFit: "cover" }} />
          {typeof p.score === "number" && (
            <span style={{ fontSize: ".7rem", color: "#888" }}>match {(p.score * 100).toFixed(0)}%</span>
          )}
        </a>
      ))}
    </div>
  );
}
