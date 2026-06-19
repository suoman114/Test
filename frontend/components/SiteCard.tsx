import Link from "next/link";
import { Site, formatBytes, formatDate } from "@/lib/api";

export function SiteCard({ site }: { site: Site }) {
  return (
    <Link
      href={`/sites/${site.slug}`}
      className="block rounded-lg border bg-white p-5 shadow-sm transition hover:border-slate-400 hover:shadow"
    >
      <div className="flex items-start justify-between">
        <h2 className="font-semibold">{site.name}</h2>
        {site.latest_version && (
          <span className="rounded bg-emerald-100 px-2 py-0.5 text-xs font-medium text-emerald-700">
            {site.latest_version}
          </span>
        )}
      </div>
      {site.description && (
        <p className="mt-1 line-clamp-2 text-sm text-slate-500">
          {site.description}
        </p>
      )}
      <dl className="mt-4 grid grid-cols-2 gap-2 text-xs text-slate-500">
        <div>
          <dt className="text-slate-400">크기</dt>
          <dd>{formatBytes(site.size_bytes)}</dd>
        </div>
        <div>
          <dt className="text-slate-400">갱신</dt>
          <dd>{formatDate(site.updated_at)}</dd>
        </div>
      </dl>
    </Link>
  );
}
