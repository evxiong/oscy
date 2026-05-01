import type { Metadata } from "next";
import localFont from "next/font/local";
import Navbar from "./_components/Navbar";
import SearchRefContextProvider from "./_contexts/SearchRefContext";
import "./globals.css";

const figtree = localFont({
  src: [
    {
      path: "../../public/fonts/Figtree.woff2",
      style: "normal",
    },
    {
      path: "../../public/fonts/Figtree-Italic.woff2",
      style: "italic",
    },
  ],
  variable: "--font-figtree",
});

export const metadata: Metadata = {
  title: {
    template: "%s | oscy",
    default: "oscy",
  },
  metadataBase: process.env.VERCEL
    ? new URL(`https://${process.env.PROD_SITE_HOST}`)
    : new URL(`http://localhost:3000`),
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${figtree.variable} antialiased`}>
      <body className="min-h-screen scroll-smooth font-sans text-primary">
        <SearchRefContextProvider>
          <a
            href="#content"
            className="absolute left-0 top-0 z-50 -translate-x-full rounded-br-md bg-title px-2 py-1 text-sm font-medium text-background outline-offset-2 focus-visible:translate-x-0"
          >
            Skip to content
          </a>
          <Navbar />
          <main id="content">{children}</main>
        </SearchRefContextProvider>
      </body>
    </html>
  );
}
