import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "CS202 — C Compiler Optimizer",
  description: "Static Analysis & Optimization Pipeline Visualizer",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-bg-primary text-slate-200 h-screen overflow-hidden">{children}</body>
    </html>
  );
}
