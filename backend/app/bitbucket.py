"""Bitbucket Server / Data Center REST API 1.0 클라이언트.

인증은 HTTP access token(Personal Access Token)을 Bearer 헤더로 사용한다.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import httpx

from .config import Settings


def _ts(ms: int | None) -> datetime | None:
    """Bitbucket 의 epoch millis → tz-aware datetime."""
    if ms is None:
        return None
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc)


class BitbucketClient:
    def __init__(
        self,
        settings: Settings,
        transport: httpx.AsyncBaseTransport | None = None,
    ):
        # transport 는 테스트에서 가짜 Bitbucket(ASGI) 로 갈아끼우기 위한 주입구.
        # 운영에서는 None → 실제 네트워크.
        self._settings = settings
        self._base = settings.bitbucket_base_url.rstrip("/")
        self._project = settings.bitbucket_project_key

        # 구버전 Bitbucket(PAT 없음)은 아이디/비번(Basic), 최신은 토큰(Bearer).
        auth: httpx.Auth | None = None
        headers: dict[str, str] = {}
        if settings.use_basic_auth:
            auth = httpx.BasicAuth(
                settings.bitbucket_username, settings.bitbucket_password
            )
        else:
            headers["Authorization"] = f"Bearer {settings.bitbucket_token}"

        self._client = httpx.AsyncClient(
            base_url=self._base,
            headers=headers,
            auth=auth,
            timeout=30.0,
            transport=transport,
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    # --- 내부 헬퍼 ---------------------------------------------------------

    async def _get(self, endpoint: str, **params: Any) -> dict[str, Any]:
        # endpoint 로 이름을 둔 이유: Bitbucket 쿼리 파라미터 중 'path' 가 있어서
        # 첫 인자 이름이 path 면 **params 의 path 와 충돌한다.
        resp = await self._client.get(endpoint, params=params)
        resp.raise_for_status()
        return resp.json()

    async def _paged(self, endpoint: str, **params: Any) -> list[dict[str, Any]]:
        """Bitbucket 페이지네이션을 전부 순회해 values 를 모은다."""
        out: list[dict[str, Any]] = []
        start = 0
        while True:
            page = await self._get(endpoint, start=start, limit=100, **params)
            out.extend(page.get("values", []))
            if page.get("isLastPage", True):
                break
            start = page.get("nextPageStart", start + 100)
        return out

    def _repo_base(self, slug: str) -> str:
        return f"/rest/api/1.0/projects/{self._project}/repos/{slug}"

    # --- repo / 사이트 -----------------------------------------------------

    async def list_repos(self) -> list[dict[str, Any]]:
        return await self._paged(f"/rest/api/1.0/projects/{self._project}/repos")

    async def get_repo(self, slug: str) -> dict[str, Any]:
        return await self._get(self._repo_base(slug))

    # --- 태그 / 버전 -------------------------------------------------------

    async def list_tags(self, slug: str) -> list[dict[str, Any]]:
        return await self._paged(f"{self._repo_base(slug)}/tags")

    # --- 커밋 --------------------------------------------------------------

    async def list_commits(self, slug: str, until: str | None = None, limit: int = 25):
        params: dict[str, Any] = {"limit": limit}
        if until:
            params["until"] = until
        page = await self._get(f"{self._repo_base(slug)}/commits", **params)
        return page.get("values", [])

    async def get_commit(self, slug: str, commit_id: str) -> dict[str, Any]:
        return await self._get(f"{self._repo_base(slug)}/commits/{commit_id}")

    async def commits_for_path(
        self, slug: str, path: str, until: str | None = None, limit: int = 50
    ) -> list[dict[str, Any]]:
        """특정 파일 경로를 바꾼 커밋 이력 (= 그 패키지의 버전들)."""
        params: dict[str, Any] = {"path": path, "limit": limit}
        if until:
            params["until"] = until
        page = await self._get(f"{self._repo_base(slug)}/commits", **params)
        return page.get("values", [])

    # --- 디렉토리 / 파일 ---------------------------------------------------

    async def list_directory(
        self, slug: str, path: str = "", at: str | None = None
    ) -> list[dict[str, Any]]:
        """한 디렉토리의 바로 아래 자식들(파일/폴더)을 반환. 자식 페이지네이션 처리."""
        url = f"{self._repo_base(slug)}/browse/{path}" if path else f"{self._repo_base(slug)}/browse"
        out: list[dict[str, Any]] = []
        start = 0
        while True:
            params: dict[str, Any] = {"start": start, "limit": 1000}
            if at:
                params["at"] = at
            data = await self._get(url, **params)
            children = data.get("children", {})
            out.extend(children.get("values", []))
            if children.get("isLastPage", True):
                break
            start = children.get("nextPageStart", start + 1000)
        return out

    # --- 파일 (tar) --------------------------------------------------------

    async def last_modified(self, slug: str, path: str, at: str | None = None):
        """파일의 마지막 수정 커밋 정보."""
        params = {"at": at} if at else {}
        return await self._get(f"{self._repo_base(slug)}/last-modified/{path}", **params)

    async def file_size(self, slug: str, path: str, at: str | None = None) -> int | None:
        """browse API 로 파일 크기 조회. 없으면 None."""
        params: dict[str, Any] = {"size": "true"}
        if at:
            params["at"] = at
        try:
            data = await self._get(f"{self._repo_base(slug)}/browse/{path}", **params)
        except httpx.HTTPStatusError:
            return None
        return data.get("size")

    async def raw_stream(self, slug: str, path: str, at: str | None = None):
        """raw 파일 스트리밍 다운로드용 httpx 응답 컨텍스트."""
        params = {"at": at} if at else {}
        url = f"/projects/{self._project}/repos/{slug}/raw/{path}"
        return self._client.stream("GET", url, params=params)


__all__ = ["BitbucketClient", "_ts"]
