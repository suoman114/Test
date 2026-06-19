// 서버 컴포넌트(Node 런타임)에서는 컨테이너 내부 주소(INTERNAL_API_BASE)를,
// 브라우저에서는 공개 주소(NEXT_PUBLIC_API_BASE, 리버스 프록시 사용 시 빈 문자열=상대경로)를 쓴다.
// 둘 다 없으면 로컬 개발 기본값(localhost:8000).
export const API_BASE =
  typeof window === "undefined"
    ? process.env.INTERNAL_API_BASE ??
      process.env.NEXT_PUBLIC_API_BASE ??
      "http://localhost:8000"
    : process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

export interface Site {
  slug: string;
  name: string;
  description?: string | null;
}

// repo 안의 패키지 파일 하나
export interface Package {
  name: string;
  path: string;
  size_bytes?: number | null;
  updated_at?: string | null;
  last_author?: string | null;
  last_commit_id?: string | null;
  last_message?: string | null;
}

// 패키지 파일의 한 버전 = 그 파일을 바꾼 커밋
export interface PackageVersion {
  commit_id: string;
  display_id?: string | null;
  message?: string | null;
  author?: string | null;
  created_at?: string | null;
}

export interface AuditEvent {
  id: number;
  action: string;
  slug: string;
  version: string;
  user?: string | null;
  detail?: string | null;
  created_at?: string | null;
}

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, { cache: "no-store" });
  if (!res.ok) {
    throw new Error(`API ${path} 실패: ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export const fetchSites = () => get<Site[]>("/api/sites");

export const fetchPackages = (slug: string) =>
  get<Package[]>(`/api/sites/${slug}/packages`);

export const fetchPackageVersions = (slug: string, path: string) =>
  get<PackageVersion[]>(
    `/api/sites/${slug}/packages/versions?path=${encodeURIComponent(path)}`,
  );

// 패키지 다운로드 URL. at(커밋 id) 주면 특정 버전.
export const packageDownloadUrl = (slug: string, path: string, at?: string) => {
  const qs = new URLSearchParams({ path });
  if (at) qs.set("at", at);
  return `${API_BASE}/api/sites/${slug}/packages/download?${qs.toString()}`;
};

export const fetchAuditEvents = (limit = 200, slug?: string) => {
  const qs = new URLSearchParams();
  qs.set("limit", String(limit));
  if (slug) qs.set("slug", slug);
  return get<AuditEvent[]>(`/api/audit?${qs.toString()}`);
};

export function formatBytes(bytes?: number | null): string {
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

export function formatDate(iso?: string | null): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleString();
}
