import Link from "next/link";
import {
  fetchPackageVersions,
  packageDownloadUrl,
  formatDate,
} from "@/lib/api";

export default async function HistoryPage({
  params,
  searchParams,
}: {
  params: { slug: string };
  searchParams: { path?: string };
}) {
  const { slug } = params;
  const path = searchParams.path ?? "";

  let versions;
  let error: string | null = null;
  if (path) {
    try {
      versions = await fetchPackageVersions(slug, path);
    } catch (e) {
      error = e instanceof Error ? e.message : "알 수 없는 오류";
    }
  }

  return (
    <div>
      <Link
        href={`/sites/${slug}`}
        className="text-sm text-slate-500 hover:underline"
      >
        ← {slug}
      </Link>
      <h1 className="mt-2 text-2xl font-bold break-all">{path || "(경로 없음)"}</h1>
      <p className="mb-6 text-sm text-slate-400">버전 이력 (덮어쓴 커밋들)</p>

      {error && (
        <div className="rounded border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          이력을 불러오지 못했습니다: {error}
        </div>
      )}

      {versions && versions.length === 0 && (
        <p className="text-slate-500">커밋 이력이 없습니다.</p>
      )}

      {versions && versions.length > 0 && (
        <div className="overflow-hidden rounded-lg border bg-white">
          <table className="w-full text-sm">
            <thead className="border-b bg-slate-50 text-left text-slate-500">
              <tr>
                <th className="px-4 py-2 font-medium">커밋</th>
                <th className="px-4 py-2 font-medium">메시지</th>
                <th className="px-4 py-2 font-medium">작성자</th>
                <th className="px-4 py-2 font-medium">날짜</th>
                <th className="px-4 py-2 font-medium text-right">이 버전 받기</th>
              </tr>
            </thead>
            <tbody>
              {versions.map((v, i) => (
                <tr key={v.commit_id} className="border-b last:border-0">
                  <td className="px-4 py-2 font-mono text-xs text-slate-500">
                    {(v.display_id ?? v.commit_id).slice(0, 10)}
                    {i === 0 && (
                      <span className="ml-2 rounded bg-emerald-100 px-1.5 py-0.5 text-[10px] font-medium text-emerald-700">
                        최신
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-2 text-slate-700">{v.message ?? "—"}</td>
                  <td className="px-4 py-2 text-slate-600">{v.author ?? "—"}</td>
                  <td className="px-4 py-2 text-slate-600">
                    {formatDate(v.created_at)}
                  </td>
                  <td className="px-4 py-2 text-right">
                    <a
                      href={packageDownloadUrl(slug, path, v.commit_id)}
                      className="rounded bg-slate-900 px-3 py-1 text-xs font-medium text-white hover:bg-slate-700"
                    >
                      받기
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
