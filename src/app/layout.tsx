import type { Metadata } from "next";
import { Albert_Sans } from "next/font/google";
import "./globals.css";
import Navbar from "./_components/navbar";

const albertSans = Albert_Sans({
  variable: "--font-albert-sans",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "oscy",
  description: "Oscars database",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${albertSans.variable} antialiased`}>
      <body className="scroll-smooth font-sans text-zinc-800">
        <Navbar />
        <main>{children}</main>
      </body>
    </html>
  );
}
