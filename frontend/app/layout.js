import "./globals.css";

export const metadata = {
  title: "FaceFolio",
  description: "Scan a QR, take a selfie, find your photos.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
