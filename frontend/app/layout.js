export const metadata = {
  title: "FaceFolio",
  description: "Scan a QR, take a selfie, find your photos.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body style={{ fontFamily: "system-ui, sans-serif", margin: 0 }}>{children}</body>
    </html>
  );
}
