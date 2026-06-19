"use client";

import { useEffect, useState } from "react";

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

interface AuditEvent {
  id: number;
  action: string;
  slug: string;
  version: string;
  user?: string | null;
  detail?: string | null;
  created_at?: string | null;
}

function formatDate(iso?: string | null): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleString();
}

export default function AuditPage() {
  const [events, setEvents] = useState<AuditEvent[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${API_BASE}/api/audit`, { cache: "no-store" })
      .then((res) => {
        if (!res.ok) throw new Error(`API /api/audit 실패: ${res.status}`);
        return res.json() as Promise<AuditEvent[]>;
      })
      .then(setEvents)
      .catch((e) =>
        setError(e instanceof Error ? e.message : "알 수 없는 오류"),
      );
  }, []);

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold">감사 로그</h1>
        <span className="text-sm text-slate-400">
          {events ? `${events.length}건` : ""}
        </span>
      </div>

      {error && (
        <div className="rounded border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          백엔드에 연결하지 못했습니다: {error}
          <br />
          <span className="text-red-500">
            backend 가 실행 중인지, NEXT_PUBLIC_API_BASE 가 올바른지 확인하세요.
          </span>
        </div>
      )}

      {events && events.length === 0 && (
        <p className="text-slate-500">기록된 로그가 없습니다.</p>
      )}

      {events && events.length > 0 && (
        <div className="overflow-x-auto rounded border border-slate-200 bg-white">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b bg-slate-50 text-left text-slate-500">
                <th className="px-4 py-2 font-medium">동작</th>
                <th className="px-4 py-2 font-medium">사이트</th>
                <th className="px-4 py-2 font-medium">버전</th>
                <th className="px-4 py-2 font-medium">사용자</th>
                <th className="px-4 py-2 font-medium">일시</th>
              </tr>
            </thead>
            <tbody>
              {events.map((ev) => (
                <tr key={ev.id} className="border-b last:border-0">
                  <td className="px-4 py-2">
                    <span
                      className={
                        ev.action === "upload"
                          ? "rounded bg-emerald-100 px-2 py-0.5 text-xs text-emerald-700"
                          : "rounded bg-sky-100 px-2 py-0.5 text-xs text-sky-700"
                      }
                    >
                      {ev.action}
                    </span>
                  </td>
                  <td className="px-4 py-2 font-medium">{ev.slug}</td>
                  <td className="px-4 py-2">{ev.version}</td>
                  <td className="px-4 py-2 text-slate-600">{ev.user ?? "—"}</td>
                  <td className="px-4 py-2 text-slate-500">
                    {formatDate(ev.created_at)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
