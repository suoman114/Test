import { fetchSites } from "@/lib/api";
import { SiteCard } from "@/components/SiteCard";

export default async function HomePage() {
  let sites;
  let error: string | null = null;
  try {
    sites = await fetchSites();
  } catch (e) {
    error = e instanceof Error ? e.message : "알 수 없는 오류";
  }

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold">사이트</h1>
        <span className="text-sm text-slate-400">
          {sites ? `${sites.length}개` : ""}
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

      {sites && sites.length === 0 && (
        <p className="text-slate-500">표시할 사이트가 없습니다.</p>
      )}

      {sites && sites.length > 0 && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {sites.map((site) => (
            <SiteCard key={site.slug} site={site} />
          ))}
        </div>
      )}
    </div>
  );
}
