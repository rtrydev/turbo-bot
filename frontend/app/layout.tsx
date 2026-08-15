import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import Sidebar from "@/components/Sidebar";
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
  description: "Admin panel for the Turbo Discord music bot",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="flex h-full overflow-hidden bg-[#07070b] text-zinc-100">
        <div aria-hidden className="pointer-events-none fixed inset-0 -z-10 overflow-hidden">
          <div className="absolute -left-40 -top-48 h-[34rem] w-[34rem] rounded-full bg-violet-600/[0.13] blur-[120px]" />
          <div className="absolute -right-40 top-1/4 h-[30rem] w-[30rem] rounded-full bg-fuchsia-600/[0.1] blur-[120px]" />
          <div className="absolute -bottom-48 left-1/3 h-[30rem] w-[30rem] rounded-full bg-cyan-500/[0.07] blur-[120px]" />
        </div>
        <Sidebar />
        <ToastProvider>
          <main className="flex-1 overflow-auto p-6 lg:p-8">{children}</main>
        </ToastProvider>
      </body>
    </html>
  );
}
