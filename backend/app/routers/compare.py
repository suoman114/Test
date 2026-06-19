"""버전 비교 엔드포인트.

두 버전(git tag)의 tar 내부 파일 트리를 diff 하고, 두 태그 사이의 커밋
메타데이터를 함께 보여준다.
"""
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from ..bitbucket import BitbucketClient, _ts
from ..config import Settings, get_settings
from ..deps import get_bitbucket
from ..tarinspect import diff_members, list_members

router = APIRouter(prefix="/api/sites/{slug}/compare", tags=["compare"])


# --- 응답 모델 (schemas.py 는 건드리지 않고 여기서 정의) -------------------


class MemberDiff(BaseModel):
    """tar 멤버 하나의 diff. added/removed 일 때 한쪽 size 는 None."""

    name: str
    from_size: int | None = None
    to_size: int | None = None


class CompareCommit(BaseModel):
    id: str
    message: str | None = None
    author: str | None = None
    date: datetime | None = None


class CompareResult(BaseModel):
    from_version: str
    to_version: str
    added: list[MemberDiff]
    removed: list[MemberDiff]
    changed: list[MemberDiff]
    commits: list[CompareCommit]
    note: str | None = None


@router.get("", response_model=CompareResult)
async def compare_versions(
    slug: str,
    from_version: str = Query(..., alias="from_version"),
    to_version: str = Query(..., alias="to_version"),
    bb: BitbucketClient = Depends(get_bitbucket),
    settings: Settings = Depends(get_settings),
) -> CompareResult:
    """from_version → to_version 의 tar 파일 diff + 두 태그 사이 커밋 목록."""
    # tar 내부 멤버 비교
    a = await list_members(bb, slug, from_version, settings)
    b = await list_members(bb, slug, to_version, settings)
    added, removed, changed = diff_members(a, b)

    # from 태그를 커밋 해시로 먼저 해석한다. (태그 이름은 커밋 id 와 다르므로
    # 이름끼리 비교하면 절대 못 찾는다 → 태그→커밋 해석이 필요)
    from_commit_id: str | None = None
    for tag in await bb.list_tags(slug):
        if tag.get("displayId") == from_version:
            from_commit_id = tag.get("latestCommit")
            break

    # 커밋 목록: to 에서 도달 가능한 최근 커밋을 가져온 뒤, from 커밋이 보이면
    # 거기서 잘라 "from 이후 ~ to" 범위만 남긴다 (until=to).
    raw_commits = await bb.list_commits(slug, until=to_version, limit=100)
    commits: list[CompareCommit] = []
    note: str | None = None
    reached_from = False

    for c in raw_commits:
        cid = c.get("id", "")
        # from 커밋을 만나면 그 이전 이력은 from 에 이미 포함됨
        if from_commit_id and cid == from_commit_id:
            reached_from = True
            break
        commits.append(
            CompareCommit(
                id=cid,
                message=c.get("message"),
                author=(c.get("author") or {}).get("name"),
                date=_ts(c.get("authorTimestamp")),
            )
        )

    if not reached_from:
        if from_commit_id is None:
            note = (
                f"태그 '{from_version}' 를 찾지 못해 '{to_version}' 기준 "
                f"최근 커밋만 표시합니다."
            )
        else:
            note = (
                f"'{from_version}' 커밋을 최근 {len(raw_commits)}개 이력에서 찾지 못해, "
                f"'{to_version}' 기준 최근 커밋만 표시합니다."
            )

    return CompareResult(
        from_version=from_version,
        to_version=to_version,
        added=[MemberDiff(**m) for m in added],
        removed=[MemberDiff(**m) for m in removed],
        changed=[MemberDiff(**m) for m in changed],
        commits=commits,
        note=note,
    )
