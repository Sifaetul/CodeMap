import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "CodeAtlas",
  description: "AI-Powered Codebase Architecture Platform",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="font-sans min-h-full flex flex-col">
        {children}
      </body>
    </html>
  );
}
