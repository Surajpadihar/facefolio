export const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8088";

export async function getEvent(token) {
  const res = await fetch(`${API_BASE}/api/public/events/${token}/`);
  if (res.status === 410) throw new Error("This event has expired.");
  if (!res.ok) throw new Error("Event not found.");
  return res.json();
}

export async function acceptConsent(token) {
  const res = await fetch(`${API_BASE}/api/public/events/${token}/consent/`, { method: "POST" });
  if (!res.ok) throw new Error("Could not record consent.");
  return res.json();
}

export async function searchSelfie(token, consentId, file) {
  const form = new FormData();
  form.append("consent_id", consentId);
  form.append("selfie", file);
  const res = await fetch(`${API_BASE}/api/public/events/${token}/search/`, { method: "POST", body: form });
  if (!res.ok) throw new Error("Search failed. Please try again.");
  return res.json();
}

export async function getGallery(token) {
  const res = await fetch(`${API_BASE}/api/public/events/${token}/gallery/`);
  if (!res.ok) throw new Error("Could not load gallery.");
  return res.json();
}

export function downloadOneUrl(token, photoId) {
  return `${API_BASE}/api/public/events/${token}/photos/${photoId}/download/`;
}

export async function downloadZip(token, photoIds, eventName) {
  const res = await fetch(`${API_BASE}/api/public/events/${token}/download-zip/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ photo_ids: photoIds }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Download failed.");
  }
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `${eventName || "photos"}.zip`;
  a.click();
  URL.revokeObjectURL(url);
}
