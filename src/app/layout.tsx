import type { Metadata } from "next";
import { Nav } from "@/components/Nav";
import "./globals.css";
import { LayoutClient } from "./layout-client";

export const metadata: Metadata = {
  title: "ROOTSIGHT | AI Incident Intelligence",
  description: "Real-time automated root cause analysis & response orchestration",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="font-sans min-h-screen bg-[--bg-primary] text-[--text-primary]">
        <LayoutClient>
          <Nav />
          <main className="min-h-screen pt-14">{children}</main>
        </LayoutClient>
      </body>
    </html>
  );
}
