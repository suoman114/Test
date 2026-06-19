"""버전(git tag) 목록 / tar 다운로드 엔드포인트."""
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from .. import db
from ..bitbucket import BitbucketClient, _ts
from ..config import Settings, get_settings
from ..deps import build_client, get_bitbucket
from ..schemas import Version

router = APIRouter(prefix="/api/sites/{slug}/versions", tags=["versions"])


@router.get("", response_model=list[Version])
async def list_versions(
    slug: str,
    bb: BitbucketClient = Depends(get_bitbucket),
    settings: Settings = Depends(get_settings),
) -> list[Version]:
    """사이트의 버전 목록. 각 태그 = 한 버전."""
    tags = await bb.list_tags(slug)
    versions: list[Version] = []
    for tag in tags:
        commit_id = tag["latestCommit"]
        commit = await bb.get_commit(slug, commit_id)
        size = await bb.file_size(slug, settings.package_tar_path, at=commit_id)
        versions.append(
            Version(
                name=tag["displayId"],
                commit_id=commit_id,
                message=commit.get("message"),
                author=(commit.get("author") or {}).get("name"),
                created_at=_ts(commit.get("authorTimestamp")),
                size_bytes=size,
            )
        )
    return versions


@router.get("/{version}/download")
async def download_version(
    slug: str,
    version: str,
    settings: Settings = Depends(get_settings),
):
    """특정 버전(tag)의 tar 를 스트리밍 다운로드.

    StreamingResponse 의 본문은 핸들러가 반환된 *뒤* 에 흘러나간다. 따라서
    요청-스코프 의존성(get_bitbucket)의 클라이언트를 쓰면 스트리밍 도중 클라이언트가
    닫혀버린다. 전용 클라이언트를 만들어 스트리머가 끝까지 들고 있다가 직접 닫는다.
    """
    path = settings.package_tar_path
    filename = f"{slug}-{version}.tar"
    db.record("download", slug, version, detail=filename)

    client = build_client(settings)

    async def streamer():
        try:
            async with await client.raw_stream(slug, path, at=version) as resp:
                resp.raise_for_status()
                async for chunk in resp.aiter_bytes():
                    yield chunk
        finally:
            await client.aclose()

    return StreamingResponse(
        streamer(),
        media_type="application/x-tar",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
