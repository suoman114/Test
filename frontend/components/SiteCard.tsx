import Link from "next/link";
import { Site } from "@/lib/api";

export function SiteCard({ site }: { site: Site }) {
  return (
    <Link
      href={`/sites/${site.slug}`}
      className="block rounded-lg border bg-white p-5 shadow-sm transition hover:border-slate-400 hover:shadow"
    >
      <h2 className="font-semibold">{site.name}</h2>
      <p className="mt-1 font-mono text-xs text-slate-400">{site.slug}</p>
      {site.description && (
        <p className="mt-2 line-clamp-2 text-sm text-slate-500">
          {site.description}
        </p>
      )}
    </Link>
  );
}
