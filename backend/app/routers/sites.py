"""사이트(= Bitbucket repo) 목록 / 상세 엔드포인트."""
import re

from fastapi import APIRouter, Depends

from ..bitbucket import BitbucketClient, _ts
from ..config import Settings, get_settings
from ..deps import get_bitbucket
from ..schemas import Site

router = APIRouter(prefix="/api/sites", tags=["sites"])


def _slug_filter(settings: Settings):
    pattern = settings.repo_slug_filter.strip()
    return re.compile(pattern) if pattern else None


@router.get("", response_model=list[Site])
async def list_sites(
    bb: BitbucketClient = Depends(get_bitbucket),
    settings: Settings = Depends(get_settings),
) -> list[Site]:
    """프로젝트 내 repo 들을 사이트로 노출. 각 사이트의 최신 버전/갱신일 포함."""
    repos = await bb.list_repos()
    flt = _slug_filter(settings)

    sites: list[Site] = []
    for repo in repos:
        slug = repo["slug"]
        if flt and not flt.search(slug):
            continue

        latest_version = None
        updated_at = None
        size_bytes = None

        tags = await bb.list_tags(slug)
        if tags:
            latest = tags[0]  # Bitbucket 은 최신 태그를 먼저 반환
            latest_version = latest["displayId"]
            try:
                lm = await bb.last_modified(slug, settings.package_tar_path, at=latest["latestCommit"])
                file_info = lm.get("files", {}).get(settings.package_tar_path, {})
                updated_at = _ts(file_info.get("authorTimestamp"))
            except Exception:
                pass
            size_bytes = await bb.file_size(slug, settings.package_tar_path, at=latest["latestCommit"])

        sites.append(
            Site(
                slug=slug,
                name=repo.get("name", slug),
                description=repo.get("description"),
                latest_version=latest_version,
                updated_at=updated_at,
                size_bytes=size_bytes,
            )
        )

    return sites


@router.get("/{slug}", response_model=Site)
async def get_site(
    slug: str,
    bb: BitbucketClient = Depends(get_bitbucket),
    settings: Settings = Depends(get_settings),
) -> Site:
    repo = await bb.get_repo(slug)
    tags = await bb.list_tags(slug)
    latest = tags[0]["displayId"] if tags else None
    return Site(
        slug=slug,
        name=repo.get("name", slug),
        description=repo.get("description"),
        latest_version=latest,
    )
