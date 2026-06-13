const API = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export default function Home() {
  return (
    <main style={{ maxWidth: 640, margin: "10vh auto", padding: "0 1.5rem" }}>
      <h1 style={{ fontSize: "2.5rem", marginBottom: ".25rem" }}>FaceFolio</h1>
      <p style={{ color: "#555", fontSize: "1.1rem" }}>
        Scan an event QR code, take a selfie, and find every photo you appear in.
      </p>
      <p style={{ color: "#888", marginTop: "2rem" }}>
        🚧 Frontend scaffold (Phase 1). The photographer portal and guest selfie flow
        arrive in later phases.
      </p>
      <ul style={{ color: "#666", lineHeight: 1.8 }}>
        <li>
          API health: <code>{API}/api/health/</code>
        </li>
        <li>
          Admin: <code>{API.replace(/:\d+$/, ":8000")}/admin/</code>
        </li>
      </ul>
    </main>
  );
}
