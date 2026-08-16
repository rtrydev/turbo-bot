import type { Metadata, Viewport } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import Sidebar from "@/components/Sidebar";
import { MobileHeader } from "@/components/MobileHeader";
import { MobileTabBar } from "@/components/MobileTabBar";
import { ToastProvider } from "@/lib/toast";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Turbo Bot — Admin Console",
  applicationName: "Turbo Bot",
  description: "Admin panel for the Turbo Discord music bot",
  manifest: "/manifest.webmanifest",
  icons: {
    icon: "/icon.svg",
    apple: "/icon.svg",
  },
  appleWebApp: {
    capable: true,
    title: "Turbo Bot",
    statusBarStyle: "black-translucent",
  },
  formatDetection: {
    telephone: false,
  },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
  viewportFit: "cover",
  themeColor: "#09090b",
  colorScheme: "dark",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="app-body flex h-full overflow-hidden bg-[#07070b] text-zinc-100">
        <div
          aria-hidden
          className="pointer-events-none fixed inset-0 -z-10 bg-[radial-gradient(55rem_35rem_at_50%_-12%,rgba(139,92,246,0.07),transparent_70%)]"
        />
        <Sidebar />
        <ToastProvider>
          <div className="flex min-h-0 min-w-0 flex-1 flex-col">
            <MobileHeader />
            <main className="min-h-0 flex-1 overflow-auto p-4 sm:p-6 lg:p-8">{children}</main>
            <MobileTabBar />
          </div>
        </ToastProvider>
      </body>
    </html>
  );
}
