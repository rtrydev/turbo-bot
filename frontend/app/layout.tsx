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

const themeColor = "#07070b";

export const metadata: Metadata = {
  title: "Turbo Bot — Admin Console",
  description: "Admin panel for the Turbo Discord music bot",
  applicationName: "Turbo Bot",
  appleWebApp: {
    capable: true,
    title: "Turbo Bot",
    statusBarStyle: "black-translucent",
  },
  formatDetection: { telephone: false },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
  viewportFit: "cover",
  themeColor,
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="overflow-hidden bg-[#07070b] text-zinc-100">
        <div
          aria-hidden
          className="pointer-events-none fixed inset-0 -z-10 bg-[radial-gradient(55rem_35rem_at_50%_-12%,rgba(139,92,246,0.07),transparent_70%)]"
        />
        {/* The shell is pinned to the viewport like langler-ui's AppShell. On an
            iOS PWA the CSS layout viewport (what 100% / 100dvh / the
            VisualViewport API resolve against) is smaller than the real
            window, so a body-sized shell leaves a blank strip below the tab
            bar; fixed inset-0 spans the full screen. The header and tab bar
            keep the notch and home indicator out via env(safe-area-inset-*). */}
        <div className="fixed inset-0 flex overflow-hidden">
          <Sidebar />
          <ToastProvider>
            <div className="flex min-h-0 min-w-0 flex-1 flex-col">
              <MobileHeader />
              <main className="min-h-0 flex-1 overflow-auto p-4 sm:p-6 lg:p-8">
                {children}
              </main>
              <MobileTabBar />
            </div>
          </ToastProvider>
        </div>
      </body>
    </html>
  );
}
