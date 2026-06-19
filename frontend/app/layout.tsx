import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "PKG Dashboard",
  description: "Bitbucket 기반 사내 패키지 관리 대시보드",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ko">
      <body>
        <header className="border-b bg-white">
          <div className="mx-auto flex max-w-6xl items-center gap-3 px-6 py-4">
            <Link href="/" className="text-lg font-semibold">
              📦 PKG Dashboard
            </Link>
            <span className="text-sm text-slate-400">사내 패키지 관리</span>
          </div>
        </header>
        <main className="mx-auto max-w-6xl px-6 py-8">{children}</main>
      </body>
    </html>
  );
}
