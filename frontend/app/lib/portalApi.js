"use client";

import { API_BASE } from "./api";
import { authFetch, getAccess } from "./auth";

async function json(res, action) {
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || `${action} failed (${res.status}).`);
  }
  return res.status === 204 ? null : res.json();
}

export async function listEvents() {
  const data = await json(await authFetch("/api/events/"), "Load events");
  return Array.isArray(data) ? data : data.results || [];
}

export async function getEvent(id) {
  return json(await authFetch(`/api/events/${id}/`), "Load event");
}

export async function createEvent({ name, date, retention_days }) {
  return json(
    await authFetch("/api/events/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, date, retention_days }),
    }),
    "Create event",
  );
}

export async function listPhotos(eventId) {
  const data = await json(await authFetch(`/api/photos/?event=${eventId}`), "Load photos");
  return Array.isArray(data) ? data : data.results || [];
}

export async function uploadPhotos(eventId, files, onProgress) {
  // XHR for upload progress.
  return new Promise((resolve, reject) => {
    const form = new FormData();
    for (const f of files) form.append("files", f);
    const xhr = new XMLHttpRequest();
    xhr.open("POST", `${API_BASE}/api/events/${eventId}/upload/`);
    xhr.setRequestHeader("Authorization", `Bearer ${getAccess()}`);
    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable && onProgress) onProgress(Math.round((e.loaded / e.total) * 100));
    };
    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) resolve(JSON.parse(xhr.responseText));
      else reject(new Error(`Upload failed (${xhr.status}).`));
    };
    xhr.onerror = () => reject(new Error("Upload failed."));
    xhr.send(form);
  });
}

export async function deletePhoto(photoId) {
  return json(await authFetch(`/api/photos/${photoId}/`, { method: "DELETE" }), "Delete photo");
}

export async function reindexPhoto(photoId) {
  return json(await authFetch(`/api/photos/${photoId}/reindex/`, { method: "POST" }), "Reindex");
}

export async function getCollaborators(eventId) {
  return json(await authFetch(`/api/events/${eventId}/collaborators/`), "Load collaborators");
}

export async function addCollaborator(eventId, username) {
  return json(
    await authFetch(`/api/events/${eventId}/collaborators/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username }),
    }),
    "Add collaborator",
  );
}

export async function removeCollaborator(eventId, username) {
  return json(
    await authFetch(`/api/events/${eventId}/collaborators/${username}/`, { method: "DELETE" }),
    "Remove collaborator",
  );
}

export async function fetchQrObjectUrl(eventId) {
  const res = await authFetch(`/api/events/${eventId}/qr/`);
  if (!res.ok) throw new Error("Could not load QR code.");
  const blob = await res.blob();
  return URL.createObjectURL(blob);
}
