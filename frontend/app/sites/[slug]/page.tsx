import Link from "next/link";
import {
  fetchVersions,
  downloadUrl,
  formatBytes,
  formatDate,
} from "@/lib/api";

export default async function SitePage({
  params,
}: {
  params: { slug: string };
}) {
  const { slug } = params;
  let versions;
  let error: string | null = null;
  try {
    versions = await fetchVersions(slug);
  } catch (e) {
    error = e instanceof Error ? e.message : "알 수 없는 오류";
  }

  return (
    <div>
      <Link href="/" className="text-sm text-slate-500 hover:underline">
        ← 사이트 목록
      </Link>
      <div className="mt-2 flex items-center justify-between">
        <h1 className="text-2xl font-bold">{slug}</h1>
        <div className="flex gap-2">
          <Link
            href={`/sites/${slug}/compare`}
            className="rounded border border-slate-300 px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-100"
          >
            버전 비교
          </Link>
          <Link
            href={`/sites/${slug}/upload`}
            className="rounded bg-slate-900 px-3 py-1.5 text-xs font-medium text-white hover:bg-slate-700"
          >
            tar 업로드
          </Link>
        </div>
      </div>
      <p className="mb-6 text-sm text-slate-400">버전 이력 (git tag)</p>

      {error && (
        <div className="rounded border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          버전을 불러오지 못했습니다: {error}
        </div>
      )}

      {versions && versions.length === 0 && (
        <p className="text-slate-500">등록된 버전(tag)이 없습니다.</p>
      )}

      {versions && versions.length > 0 && (
        <div className="overflow-hidden rounded-lg border bg-white">
          <table className="w-full text-sm">
            <thead className="border-b bg-slate-50 text-left text-slate-500">
              <tr>
                <th className="px-4 py-2 font-medium">버전</th>
                <th className="px-4 py-2 font-medium">커밋</th>
                <th className="px-4 py-2 font-medium">작성자</th>
                <th className="px-4 py-2 font-medium">날짜</th>
                <th className="px-4 py-2 font-medium">크기</th>
                <th className="px-4 py-2 font-medium text-right">다운로드</th>
              </tr>
            </thead>
            <tbody>
              {versions.map((v) => (
                <tr key={v.name} className="border-b last:border-0">
                  <td className="px-4 py-2 font-medium">{v.name}</td>
                  <td className="px-4 py-2 font-mono text-xs text-slate-500">
                    {v.commit_id.slice(0, 8)}
                  </td>
                  <td className="px-4 py-2 text-slate-600">{v.author ?? "—"}</td>
                  <td className="px-4 py-2 text-slate-600">
                    {formatDate(v.created_at)}
                  </td>
                  <td className="px-4 py-2 text-slate-600">
                    {formatBytes(v.size_bytes)}
                  </td>
                  <td className="px-4 py-2 text-right">
                    <a
                      href={downloadUrl(slug, v.name)}
                      className="rounded bg-slate-900 px-3 py-1 text-xs font-medium text-white hover:bg-slate-700"
                    >
                      tar 받기
                    </a>
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
