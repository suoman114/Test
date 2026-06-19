from datetime import datetime

from pydantic import BaseModel


class Site(BaseModel):
    """하나의 패키지 사이트 = 하나의 Bitbucket repo."""

    slug: str
    name: str
    description: str | None = None
    latest_version: str | None = None
    updated_at: datetime | None = None
    size_bytes: int | None = None


class Version(BaseModel):
    """사이트의 한 버전. git tag 기반."""

    name: str          # tag 이름 (예: v1.2.0)
    commit_id: str
    message: str | None = None
    author: str | None = None
    created_at: datetime | None = None
    size_bytes: int | None = None


class CommitInfo(BaseModel):
    id: str
    display_id: str
    message: str
    author: str | None = None
    author_email: str | None = None
    committed_at: datetime | None = None
