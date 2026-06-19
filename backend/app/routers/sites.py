"""사이트(= Bitbucket repo) 목록 / 상세 엔드포인트.

목록은 가볍게 repo 정보만 반환한다(패키지 스캔은 사이트 상세에서). repo 가 많을 때
목록 화면이 빨라야 하기 때문.
"""
import re

from fastapi import APIRouter, Depends

from ..bitbucket import BitbucketClient
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
    """프로젝트 내 repo 들을 사이트로 노출 (가벼운 메타만)."""
    repos = await bb.list_repos()
    flt = _slug_filter(settings)
    sites: list[Site] = []
    for repo in repos:
        slug = repo["slug"]
        if flt and not flt.search(slug):
            continue
        sites.append(
            Site(
                slug=slug,
                name=repo.get("name", slug),
                description=repo.get("description"),
            )
        )
    return sites


@router.get("/{slug}", response_model=Site)
async def get_site(
    slug: str,
    bb: BitbucketClient = Depends(get_bitbucket),
) -> Site:
    repo = await bb.get_repo(slug)
    return Site(
        slug=slug,
        name=repo.get("name", slug),
        description=repo.get("description"),
    )
