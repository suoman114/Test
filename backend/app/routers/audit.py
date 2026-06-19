"""감사 로그 조회 엔드포인트. 누가 언제 무엇을 받아갔나/올렸나."""
from datetime import datetime

from fastapi import APIRouter, Query
from pydantic import BaseModel

from .. import db

router = APIRouter(prefix="/api/audit", tags=["audit"])


class AuditEvent(BaseModel):
    """감사 로그 한 건."""

    id: int
    action: str          # 'download' | 'upload'
    slug: str
    version: str
    user: str | None = None
    detail: str | None = None
    created_at: datetime | None = None


@router.get("", response_model=list[AuditEvent])
def list_audit(
    limit: int = Query(200, ge=1, le=1000),
    slug: str | None = None,
) -> list[AuditEvent]:
    """최근 감사 로그 목록. slug 로 필터링 가능."""
    return [AuditEvent(**row) for row in db.list_events(limit=limit, slug=slug)]
