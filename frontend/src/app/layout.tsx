import type { Metadata } from "next";
import { DM_Serif_Display, DM_Sans, JetBrains_Mono } from "next/font/google";
import "./globals.css";

const dmSerif = DM_Serif_Display({ weight: "400", subsets: ["latin"], variable: "--font-dm-serif" });
const dmSans = DM_Sans({ subsets: ["latin"], variable: "--font-dm-sans" });
const jetBrains = JetBrains_Mono({ subsets: ["latin"], variable: "--font-jetbrains-mono" });

export const metadata: Metadata = {
    title: "Meridian — Smart Meeting Scheduler",
    description: "Multi-agent AI scheduling powered by Google Cloud",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
    return (
        <html lang="en" className={`${dmSerif.variable} ${dmSans.variable} ${jetBrains.variable}`}>
            <body>{children}</body>
        </html>
    );
}