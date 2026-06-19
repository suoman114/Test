"use client";

import Link from "next/link";
import { use, useState } from "react";
import { useSearchParams } from "next/navigation";

// lib/api.ts 를 수정할 수 없어 여기서 API_BASE 를 직접 읽는다.
const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

interface MemberDiff {
  name: string;
  from_size?: number | null;
  to_size?: number | null;
}

interface CompareCommit {
  id: string;
  message?: string | null;
  author?: string | null;
  date?: string | null;
}

interface CompareResult {
  from_version: string;
  to_version: string;
  added: MemberDiff[];
  removed: MemberDiff[];
  changed: MemberDiff[];
  commits: CompareCommit[];
  note?: string | null;
}

function formatBytes(bytes?: number | null): string {
  if (bytes == null) return "—";
  const units = ["B", "KB", "MB", "GB"];
  let n = bytes;
  let i = 0;
  while (n >= 1024 && i < units.length - 1) {
    n /= 1024;
    i++;
  }
  return `${n.toFixed(i === 0 ? 0 : 1)} ${units[i]}`;
}

function formatDate(iso?: string | null): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleString();
}

export default function ComparePage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = use(params);
  const search = useSearchParams();

  const [fromVersion, setFromVersion] = useState(
    search.get("from_version") ?? ""
  );
  const [toVersion, setToVersion] = useState(search.get("to_version") ?? "");
  const [result, setResult] = useState<CompareResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function runCompare() {
    if (!fromVersion || !toVersion) {
      setError("두 버전을 모두 입력하세요.");
      return;
    }
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const qs = new URLSearchParams({
        from_version: fromVersion,
        to_version: toVersion,
      });
      const res = await fetch(
        `${API_BASE}/api/sites/${slug}/compare?${qs.toString()}`,
        { cache: "no-store" }
      );
      if (!res.ok) {
        throw new Error(`API 실패: ${res.status}`);
      }
      setResult((await res.json()) as CompareResult);
    } catch (e) {
      setError(e instanceof Error ? e.message : "알 수 없는 오류");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <Link
        href={`/sites/${slug}`}
        className="text-sm text-slate-500 hover:underline"
      >
        ← {slug} 버전 이력
      </Link>
      <h1 className="mt-2 text-2xl font-bold">버전 비교</h1>
      <p className="mb-6 text-sm text-slate-400">
        두 버전(git tag)의 tar 내용물과 커밋을 비교합니다.
      </p>

      <div className="mb-6 flex flex-wrap items-end gap-3">
        <label className="flex flex-col text-sm">
          <span className="mb-1 text-slate-500">from (이전)</span>
          <input
            value={fromVersion}
            onChange={(e) => setFromVersion(e.target.value)}
            placeholder="v1.0.0"
            className="rounded border px-3 py-1.5"
          />
        </label>
        <label className="flex flex-col text-sm">
          <span className="mb-1 text-slate-500">to (이후)</span>
          <input
            value={toVersion}
            onChange={(e) => setToVersion(e.target.value)}
            placeholder="v1.1.0"
            className="rounded border px-3 py-1.5"
          />
        </label>
        <button
          onClick={runCompare}
          disabled={loading}
          className="rounded bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-50"
        >
          {loading ? "비교 중…" : "비교"}
        </button>
      </div>

      {error && (
        <div className="mb-6 rounded border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          {error}
        </div>
      )}

      {result && (
        <div className="space-y-8">
          {result.note && (
            <div className="rounded border border-amber-200 bg-amber-50 p-3 text-sm text-amber-700">
              {result.note}
            </div>
          )}

          <DiffSection
            title="추가된 파일"
            color="text-emerald-700"
            rows={result.added}
            kind="added"
          />
          <DiffSection
            title="삭제된 파일"
            color="text-red-700"
            rows={result.removed}
            kind="removed"
          />
          <DiffSection
            title="변경된 파일"
            color="text-amber-700"
            rows={result.changed}
            kind="changed"
          />

          <section>
            <h2 className="mb-2 text-lg font-semibold">
              커밋{" "}
              <span className="text-sm font-normal text-slate-400">
                ({result.commits.length})
              </span>
            </h2>
            {result.commits.length === 0 ? (
              <p className="text-sm text-slate-500">표시할 커밋이 없습니다.</p>
            ) : (
              <div className="overflow-hidden rounded-lg border bg-white">
                <table className="w-full text-sm">
                  <thead className="border-b bg-slate-50 text-left text-slate-500">
                    <tr>
                      <th className="px-4 py-2 font-medium">커밋</th>
                      <th className="px-4 py-2 font-medium">메시지</th>
                      <th className="px-4 py-2 font-medium">작성자</th>
                      <th className="px-4 py-2 font-medium">날짜</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.commits.map((c) => (
                      <tr key={c.id} className="border-b last:border-0">
                        <td className="px-4 py-2 font-mono text-xs text-slate-500">
                          {c.id.slice(0, 8)}
                        </td>
                        <td className="px-4 py-2 text-slate-700">
                          {c.message?.split("\n")[0] ?? "—"}
                        </td>
                        <td className="px-4 py-2 text-slate-600">
                          {c.author ?? "—"}
                        </td>
                        <td className="px-4 py-2 text-slate-600">
                          {formatDate(c.date)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        </div>
      )}
    </div>
  );
}

function DiffSection({
  title,
  color,
  rows,
  kind,
}: {
  title: string;
  color: string;
  rows: MemberDiff[];
  kind: "added" | "removed" | "changed";
}) {
  return (
    <section>
      <h2 className={`mb-2 text-lg font-semibold ${color}`}>
        {title}{" "}
        <span className="text-sm font-normal text-slate-400">
          ({rows.length})
        </span>
      </h2>
      {rows.length === 0 ? (
        <p className="text-sm text-slate-500">없음</p>
      ) : (
        <div className="overflow-hidden rounded-lg border bg-white">
          <table className="w-full text-sm">
            <thead className="border-b bg-slate-50 text-left text-slate-500">
              <tr>
                <th className="px-4 py-2 font-medium">파일</th>
                {kind === "changed" ? (
                  <>
                    <th className="px-4 py-2 font-medium text-right">이전</th>
                    <th className="px-4 py-2 font-medium text-right">이후</th>
                  </>
                ) : (
                  <th className="px-4 py-2 font-medium text-right">크기</th>
                )}
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.name} className="border-b last:border-0">
                  <td className="px-4 py-2 font-mono text-xs">{r.name}</td>
                  {kind === "changed" ? (
                    <>
                      <td className="px-4 py-2 text-right text-slate-600">
                        {formatBytes(r.from_size)}
                      </td>
                      <td className="px-4 py-2 text-right text-slate-600">
                        {formatBytes(r.to_size)}
                      </td>
                    </>
                  ) : (
                    <td className="px-4 py-2 text-right text-slate-600">
                      {formatBytes(
                        kind === "added" ? r.to_size : r.from_size
                      )}
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
