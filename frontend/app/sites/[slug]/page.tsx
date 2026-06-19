import Link from "next/link";
import {
  fetchPackages,
  packageDownloadUrl,
  formatBytes,
  formatDate,
} from "@/lib/api";

export default async function SitePage({
  params,
}: {
  params: { slug: string };
}) {
  const { slug } = params;
  let packages;
  let error: string | null = null;
  try {
    packages = await fetchPackages(slug);
  } catch (e) {
    error = e instanceof Error ? e.message : "알 수 없는 오류";
  }

  return (
    <div>
      <Link href="/" className="text-sm text-slate-500 hover:underline">
        ← 사이트 목록
      </Link>
      <h1 className="mt-2 text-2xl font-bold">{slug}</h1>
      <p className="mb-6 text-sm text-slate-400">
        패키지 파일 (tar 등) — 클릭 시 버전 이력
      </p>

      {error && (
        <div className="rounded border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          패키지를 불러오지 못했습니다: {error}
        </div>
      )}

      {packages && packages.length === 0 && (
        <p className="text-slate-500">이 repo 에서 패키지 파일을 찾지 못했습니다.</p>
      )}

      {packages && packages.length > 0 && (
        <div className="overflow-hidden rounded-lg border bg-white">
          <table className="w-full text-sm">
            <thead className="border-b bg-slate-50 text-left text-slate-500">
              <tr>
                <th className="px-4 py-2 font-medium">패키지</th>
                <th className="px-4 py-2 font-medium">크기</th>
                <th className="px-4 py-2 font-medium">최근 수정</th>
                <th className="px-4 py-2 font-medium">작성자</th>
                <th className="px-4 py-2 font-medium text-right">받기 / 이력</th>
              </tr>
            </thead>
            <tbody>
              {packages.map((p) => (
                <tr key={p.path} className="border-b last:border-0">
                  <td className="px-4 py-2">
                    <div className="font-medium">{p.name}</div>
                    {p.path !== p.name && (
                      <div className="font-mono text-xs text-slate-400">
                        {p.path}
                      </div>
                    )}
                  </td>
                  <td className="px-4 py-2 text-slate-600">
                    {formatBytes(p.size_bytes)}
                  </td>
                  <td className="px-4 py-2 text-slate-600">
                    {formatDate(p.updated_at)}
                  </td>
                  <td className="px-4 py-2 text-slate-600">
                    {p.last_author ?? "—"}
                  </td>
                  <td className="px-4 py-2 text-right">
                    <a
                      href={packageDownloadUrl(slug, p.path)}
                      className="rounded bg-slate-900 px-3 py-1 text-xs font-medium text-white hover:bg-slate-700"
                    >
                      받기
                    </a>
                    <Link
                      href={`/sites/${slug}/history?path=${encodeURIComponent(
                        p.path,
                      )}`}
                      className="ml-2 rounded border border-slate-300 px-3 py-1 text-xs font-medium text-slate-700 hover:bg-slate-100"
                    >
                      이력
                    </Link>
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
