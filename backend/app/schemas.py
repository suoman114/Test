from datetime import datetime

from pydantic import BaseModel


class Site(BaseModel):
    """하나의 사이트 = 하나의 Bitbucket repo. repo 안에 패키지(tar) 여러 개가 들어있다."""

    slug: str
    name: str
    description: str | None = None


class Package(BaseModel):
    """repo 안의 패키지 파일 하나 (tar 등). 버전은 이 파일의 커밋 이력으로 본다."""

    name: str                       # 파일명 (예: ansible.tar.gz)
    path: str                       # repo 루트 기준 전체 경로 (예: rpm/foo.tgz)
    size_bytes: int | None = None
    updated_at: datetime | None = None
    last_author: str | None = None
    last_commit_id: str | None = None
    last_message: str | None = None


class PackageVersion(BaseModel):
    """패키지 파일의 한 버전 = 그 파일을 바꾼 커밋 하나."""

    commit_id: str
    display_id: str | None = None
    message: str | None = None
    author: str | None = None
    created_at: datetime | None = None


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
