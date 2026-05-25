import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "RASIP — Rwanda Agricultural Spatial Intelligence Platform",
  description: "AI-powered crop suitability, yield prediction, district similarity, and climate forecasting for Rwanda agriculture.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
