export const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

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
