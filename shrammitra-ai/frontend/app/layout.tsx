import type { Metadata } from "next";
import "./globals.css";
import { Providers } from "./providers";

export const metadata: Metadata = {
  title: "ShramMitra AI — Migrant Worker Rights Assistant",
  description:
    "Free AI assistant for migrant workers in India. Know your rights, minimum wages, safety laws, and government schemes in 7 languages.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-gray-50 text-gray-900">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
