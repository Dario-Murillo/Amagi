import type { Metadata } from "next";
import { Bebas_Neue, DM_Mono } from "next/font/google";
import "./globals.css";

const dmMono = DM_Mono({
  variable: "--font-dm-mono",
  subsets: ["latin"],
  weight: ["300", "400", "500"],
});

const bebasNeue = Bebas_Neue({
  variable: "--font-bebas-neue",
  subsets: ["latin"],
  weight: ["400"],
});

export const metadata: Metadata = {
  title: "AMAGI",
  description: "Encrypted, real-time, minimal chat.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="en"
      className={`${dmMono.variable} ${bebasNeue.variable} h-full antialiased`}
    >
      <body className="h-full">{children}</body>
    </html>
  );
}
