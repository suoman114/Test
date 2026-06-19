"use client";

import Link from "next/link";
import { useState } from "react";
import { useParams } from "next/navigation";

// lib/api.ts 를 수정할 수 없으므로 API_BASE 를 인라인으로 읽는다.
const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

export default function UploadPage() {
  const params = useParams<{ slug: string }>();
  const slug = params.slug;

  const [file, setFile] = useState<File | null>(null);
  const [version, setVersion] = useState("");
  const [message, setMessage] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSuccess(null);

    if (!file) {
      setError("tar 파일을 선택하세요.");
      return;
    }
    if (!version.trim()) {
      setError("버전(tag)을 입력하세요.");
      return;
    }

    const form = new FormData();
    form.append("file", file);
    form.append("version", version.trim());
    if (message.trim()) {
      form.append("message", message.trim());
    }

    setSubmitting(true);
    try {
      const res = await fetch(
        `${API_BASE}/api/sites/${slug}/versions`,
        { method: "POST", body: form }
      );
      if (!res.ok) {
        let detail = `${res.status}`;
        try {
          const body = await res.json();
          if (body?.detail) detail = body.detail;
        } catch {
          // JSON 파싱 실패는 무시.
        }
        throw new Error(detail);
      }
      const created = await res.json();
      setSuccess(`버전 ${created.name} 이(가) 발행되었습니다.`);
      setFile(null);
      setVersion("");
      setMessage("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "업로드에 실패했습니다.");
    } finally {
      setSubmitting(false);
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
      <h1 className="mt-2 text-2xl font-bold">tar 업로드</h1>
      <p className="mb-6 text-sm text-slate-400">
        새 tar 를 업로드해 신규 버전(git tag)으로 발행합니다.
      </p>

      {error && (
        <div className="mb-4 rounded border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          업로드 실패: {error}
        </div>
      )}
      {success && (
        <div className="mb-4 rounded border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-700">
          {success}{" "}
          <Link
            href={`/sites/${slug}`}
            className="font-medium underline hover:no-underline"
          >
            버전 이력 보기
          </Link>
        </div>
      )}

      <form
        onSubmit={handleSubmit}
        className="max-w-lg space-y-5 rounded-lg border bg-white p-6"
      >
        <div>
          <label className="mb-1 block text-sm font-medium text-slate-700">
            tar 파일
          </label>
          <input
            type="file"
            accept=".tar"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            className="block w-full text-sm text-slate-600 file:mr-4 file:rounded file:border-0 file:bg-slate-900 file:px-3 file:py-2 file:text-sm file:font-medium file:text-white hover:file:bg-slate-700"
          />
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium text-slate-700">
            버전 (tag)
          </label>
          <input
            type="text"
            value={version}
            onChange={(e) => setVersion(e.target.value)}
            placeholder="예: v1.2.0"
            className="w-full rounded border border-slate-300 px-3 py-2 text-sm focus:border-slate-500 focus:outline-none"
          />
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium text-slate-700">
            커밋 메시지 (선택)
          </label>
          <textarea
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="릴리스 노트 등"
            rows={3}
            className="w-full rounded border border-slate-300 px-3 py-2 text-sm focus:border-slate-500 focus:outline-none"
          />
        </div>

        <button
          type="submit"
          disabled={submitting}
          className="rounded bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {submitting ? "발행 중…" : "버전 발행"}
        </button>
      </form>
    </div>
  );
}
