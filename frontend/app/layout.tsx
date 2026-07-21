import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "RepoTwin — Software Digital Twin",
  description: "A living, interactive model of your software system.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="font-sans">{children}</body>
    </html>
  );
}
