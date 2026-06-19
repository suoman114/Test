"""패키지(repo 안 tar 파일) 목록 / 버전 이력 / 다운로드.

경로(path)는 하위 폴더를 포함할 수 있어 슬래시가 들어가므로 쿼리 파라미터로 받는다.
"""
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse

from .. import db, packages
from ..bitbucket import BitbucketClient
from ..config import Settings, get_settings
from ..deps import build_client, get_bitbucket
from ..schemas import Package, PackageVersion

router = APIRouter(prefix="/api/sites/{slug}/packages", tags=["packages"])


@router.get("", response_model=list[Package])
async def list_packages(
    slug: str,
    bb: BitbucketClient = Depends(get_bitbucket),
    settings: Settings = Depends(get_settings),
) -> list[Package]:
    """repo 를 recursive 스캔해 패키지 파일 목록을 반환."""
    return await packages.scan_packages(bb, slug, settings.package_extension_list)


@router.get("/versions", response_model=list[PackageVersion])
async def list_package_versions(
    slug: str,
    path: str = Query(..., description="repo 루트 기준 패키지 파일 경로"),
    bb: BitbucketClient = Depends(get_bitbucket),
) -> list[PackageVersion]:
    """특정 패키지 파일의 버전(커밋) 이력."""
    return await packages.list_versions(bb, slug, path)


@router.get("/download")
async def download_package(
    slug: str,
    path: str = Query(..., description="패키지 파일 경로"),
    at: str | None = Query(None, description="버전(커밋 id). 없으면 최신"),
    settings: Settings = Depends(get_settings),
):
    """패키지 파일을 스트리밍 다운로드. at 으로 특정 버전(커밋) 지정 가능."""
    filename = path.rsplit("/", 1)[-1]
    db.record("download", slug, at or "latest", detail=path)

    client = build_client(settings)

    async def streamer():
        try:
            async with await client.raw_stream(slug, path, at=at) as resp:
                resp.raise_for_status()
                async for chunk in resp.aiter_bytes():
                    yield chunk
        finally:
            await client.aclose()

    return StreamingResponse(
        streamer(),
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
