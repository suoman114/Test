"""repo 안의 패키지(tar 등) 파일을 찾아 메타데이터를 모으는 로직.

실제 구조: repo 1개 안에 tar.gz 가 여러 개, 하위 폴더에도 존재. 버전은 덮어쓰기
이므로 각 파일의 커밋 이력이 곧 버전 목록이 된다.
"""
from __future__ import annotations

from typing import Any

from .bitbucket import BitbucketClient, _ts
from .schemas import Package, PackageVersion


def _matches(name: str, extensions: list[str]) -> bool:
    low = name.lower()
    return any(low.endswith(ext) for ext in extensions)


async def scan_packages(
    bb: BitbucketClient,
    slug: str,
    extensions: list[str],
    ref: str | None = None,
    max_dirs: int = 500,
) -> list[Package]:
    """repo 를 recursive 하게 훑어 확장자에 맞는 파일을 패키지로 수집한다.

    - 디렉토리 walk: browse 로 자식 목록(파일 크기 포함)을 얻는다.
    - 매칭 파일마다 마지막 커밋 1건을 조회해 갱신일/작성자를 채운다.
    """
    packages: list[Package] = []
    stack: list[str] = [""]  # 루트부터
    visited = 0

    while stack and visited < max_dirs:
        dir_path = stack.pop()
        visited += 1
        children = await bb.list_directory(slug, dir_path, at=ref)
        for child in children:
            name = child.get("path", {}).get("name", "")
            ctype = child.get("type")
            full = f"{dir_path}/{name}" if dir_path else name
            if ctype == "DIRECTORY":
                stack.append(full)
            elif ctype == "FILE" and _matches(name, extensions):
                pkg = Package(name=name, path=full, size_bytes=child.get("size"))
                # 마지막 커밋(=최신 버전) 메타 채우기
                commits = await bb.commits_for_path(slug, full, until=ref, limit=1)
                if commits:
                    c = commits[0]
                    pkg.updated_at = _ts(c.get("authorTimestamp"))
                    pkg.last_author = (c.get("author") or {}).get("name")
                    pkg.last_commit_id = c.get("id")
                    pkg.last_message = c.get("message")
                packages.append(pkg)

    packages.sort(key=lambda p: p.path)
    return packages


async def list_versions(
    bb: BitbucketClient, slug: str, path: str, limit: int = 50
) -> list[PackageVersion]:
    """한 패키지 파일의 버전 목록 = 그 경로를 바꾼 커밋 이력."""
    commits = await bb.commits_for_path(slug, path, limit=limit)
    versions: list[PackageVersion] = []
    for c in commits:
        versions.append(
            PackageVersion(
                commit_id=c.get("id", ""),
                display_id=c.get("displayId"),
                message=c.get("message"),
                author=(c.get("author") or {}).get("name"),
                created_at=_ts(c.get("authorTimestamp")),
            )
        )
    return versions


__all__ = ["scan_packages", "list_versions"]
