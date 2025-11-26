import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "LLM JSON Streaming Demo",
  description: "Real-time structured JSON streaming with LLMs",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${inter.className} antialiased bg-slate-50 min-h-screen text-slate-900 selection:bg-indigo-100 selection:text-indigo-700`}>
        {children}
      </body>
    </html>
  );
}
