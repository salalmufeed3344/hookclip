import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Hookclip — GTA VI clips that get watched",
  description:
    "GTA VI launches Nov 19, 2026 — and clippers get paid per 1,000 views. Hookclip is the $9/mo tool that turns long GTA VI streams into ranked, captioned vertical clips. Free 60 minutes a month.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
