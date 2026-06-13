"use client";

import { API_BASE } from "./api";

const ACCESS = "ff_access";
const REFRESH = "ff_refresh";

export function setTokens({ access, refresh }) {
  if (access) localStorage.setItem(ACCESS, access);
  if (refresh) localStorage.setItem(REFRESH, refresh);
}
export function clearTokens() {
  localStorage.removeItem(ACCESS);
  localStorage.removeItem(REFRESH);
}
export function getAccess() {
  return typeof window !== "undefined" ? localStorage.getItem(ACCESS) : null;
}
export function isAuthed() {
  return !!getAccess();
}

export async function login(username, password) {
  const res = await fetch(`${API_BASE}/api/auth/login/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  if (!res.ok) throw new Error("Invalid username or password.");
  const data = await res.json();
  setTokens({ access: data.access, refresh: data.refresh });
  return data;
}

export async function signup(username, email, password) {
  const res = await fetch(`${API_BASE}/api/auth/signup/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, email, password }),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const msg = data.username?.[0] || data.email?.[0] || data.password?.[0] || data.detail || "Sign-up failed.";
    throw new Error(msg);
  }
  return data;
}

async function refreshAccess() {
  const refresh = localStorage.getItem(REFRESH);
  if (!refresh) return false;
  const res = await fetch(`${API_BASE}/api/auth/refresh/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh }),
  });
  if (!res.ok) return false;
  const data = await res.json();
  setTokens({ access: data.access, refresh: data.refresh });
  return true;
}

/** fetch with Bearer auth; transparently retries once after refreshing on 401. */
export async function authFetch(path, options = {}) {
  const doFetch = () => {
    const headers = new Headers(options.headers || {});
    const token = getAccess();
    if (token) headers.set("Authorization", `Bearer ${token}`);
    return fetch(`${API_BASE}${path}`, { ...options, headers });
  };
  let res = await doFetch();
  if (res.status === 401 && (await refreshAccess())) {
    res = await doFetch();
  }
  return res;
}

export async function getMe() {
  const res = await authFetch("/api/auth/me/");
  if (!res.ok) return null;
  return res.json();
}

export async function logout() {
  const refresh = localStorage.getItem(REFRESH);
  if (refresh) {
    await authFetch("/api/auth/logout/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh }),
    }).catch(() => {});
  }
  clearTokens();
}
