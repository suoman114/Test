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
  latest_version?: string | null;
  updated_at?: string | null;
  size_bytes?: number | null;
}

export interface Version {
  name: string;
  commit_id: string;
  message?: string | null;
  author?: string | null;
  created_at?: string | null;
  size_bytes?: number | null;
}

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, { cache: "no-store" });
  if (!res.ok) {
    throw new Error(`API ${path} 실패: ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export const fetchSites = () => get<Site[]>("/api/sites");
export const fetchVersions = (slug: string) =>
  get<Version[]>(`/api/sites/${slug}/versions`);

export const downloadUrl = (slug: string, version: string) =>
  `${API_BASE}/api/sites/${slug}/versions/${version}/download`;

// --- 업로드 (신규 버전 발행) ------------------------------------------------

export async function uploadVersion(
  slug: string,
  data: {
    file: File;
    version: string;
    message?: string;
    author_name?: string;
    author_email?: string;
  },
): Promise<Version> {
  const form = new FormData();
  form.append("file", data.file);
  form.append("version", data.version);
  if (data.message) form.append("message", data.message);
  if (data.author_name) form.append("author_name", data.author_name);
  if (data.author_email) form.append("author_email", data.author_email);
  const res = await fetch(`${API_BASE}/api/sites/${slug}/versions`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) {
    let detail = `${res.status}`;
    try {
      const b = await res.json();
      if (b?.detail) detail = b.detail;
    } catch {}
    throw new Error(`업로드 실패: ${detail}`);
  }
  return res.json() as Promise<Version>;
}

// --- 버전 비교 --------------------------------------------------------------

export interface MemberDiff {
  name: string;
  from_size?: number | null;
  to_size?: number | null;
}

export interface CompareCommit {
  id: string;
  message?: string | null;
  author?: string | null;
  date?: string | null;
}

export interface CompareResult {
  from_version: string;
  to_version: string;
  added: MemberDiff[];
  removed: MemberDiff[];
  changed: MemberDiff[];
  commits: CompareCommit[];
  note?: string | null;
}

export const fetchCompare = (
  slug: string,
  fromVersion: string,
  toVersion: string,
) =>
  get<CompareResult>(
    `/api/sites/${slug}/compare?from_version=${encodeURIComponent(
      fromVersion,
    )}&to_version=${encodeURIComponent(toVersion)}`,
  );

// --- 감사 로그 --------------------------------------------------------------

export interface AuditEvent {
  id: number;
  action: string; // 'download' | 'upload'
  slug: string;
  version: string;
  user?: string | null;
  detail?: string | null;
  created_at?: string | null;
}

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
