"""tar 업로드 → 신규 버전(git tag) 발행 엔드포인트.

versions.py 의 `GET /api/sites/{slug}/versions` 와 같은 리소스 경로에
`POST` 를 추가한다(prefix 충돌 방지를 위해 별도 라우터로 분리).
"""
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from .. import db, gitops
from ..config import Settings, get_settings
from ..schemas import Version

router = APIRouter(prefix="/api/sites/{slug}/versions", tags=["uploads"])


@router.post("", response_model=Version, status_code=201)
async def upload_version(
    slug: str,
    file: UploadFile = File(...),
    version: str = Form(...),
    message: str | None = Form(None),
    author_name: str | None = Form(None),
    author_email: str | None = Form(None),
    settings: Settings = Depends(get_settings),
) -> Version:
    """업로드된 tar 를 받아 새 버전(tag)으로 발행한다."""
    tar_bytes = await file.read()
    if not tar_bytes:
        raise HTTPException(status_code=400, detail="빈 파일은 업로드할 수 없습니다.")

    try:
        published = gitops.publish_version(
            settings=settings,
            slug=slug,
            version=version,
            tar_bytes=tar_bytes,
            message=message,
            author_name=author_name,
            author_email=author_email,
        )
    except gitops.GitPublishError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    db.record("upload", slug, version, user=author_name, detail=message)
    return published
