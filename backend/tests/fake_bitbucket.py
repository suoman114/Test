"""테스트용 가짜 Bitbucket Server (REST API 1.0).

실제 Bitbucket Server 가 돌려주는 응답 모양을 흉내내서, 우리 클라이언트
(app/bitbucket.py)와 라우터들이 end-to-end 로 동작하는지 검증한다.

시드 데이터
- project key: PKG
- repos: site-a (태그 2개), site-b (태그 0개)
- site-a: v1.1.0(commit c2, 최신) / v1.0.0(commit c1)
  각 태그의 package.tar 내용물이 달라서 버전 비교가 added/removed/changed 를 낸다.
"""
from __future__ import annotations

import io
import tarfile

from fastapi import FastAPI, HTTPException, Response

PROJECT = "PKG"
TAR_PATH = "package.tar"


def _make_tar(files: dict[str, bytes]) -> bytes:
    """{이름: 내용} 으로 in-memory tar 바이트를 만든다."""
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as tf:
        for name, content in files.items():
            info = tarfile.TarInfo(name=name)
            info.size = len(content)
            tf.addfile(info, io.BytesIO(content))
    return buf.getvalue()


# 버전별 tar 내용물 (비교 결과를 명확히 만들기 위해 의도적으로 다르게 구성)
_TAR_V1 = _make_tar(
    {
        "app.py": b"print('v1')\n",            # changed (크기 다름)
        "config.ini": b"mode=old\n",            # removed (v2 에 없음)
        "shared.txt": b"same\n",                # 동일
    }
)
_TAR_V2 = _make_tar(
    {
        "app.py": b"print('version 1.1')\n",    # changed
        "README.md": b"# hello\n",              # added (v1 에 없음)
        "shared.txt": b"same\n",                # 동일
    }
)

# 커밋: 최신순. c2(v1.1.0) → c1(v1.0.0)
_COMMITS = {
    "site-a": [
        {
            "id": "c2" * 20,
            "displayId": "c2c2c2c",
            "message": "Publish v1.1.0",
            "author": {"name": "alice", "emailAddress": "alice@corp"},
            "authorTimestamp": 1_700_000_200_000,
        },
        {
            "id": "c1" * 20,
            "displayId": "c1c1c1c",
            "message": "Publish v1.0.0",
            "author": {"name": "bob", "emailAddress": "bob@corp"},
            "authorTimestamp": 1_700_000_100_000,
        },
    ],
    "site-b": [],
}

_TAGS = {
    "site-a": [
        {"displayId": "v1.1.0", "latestCommit": "c2" * 20},
        {"displayId": "v1.0.0", "latestCommit": "c1" * 20},
    ],
    "site-b": [],
}

# (slug, commit_id) -> tar 바이트
_TAR_BY_REF = {
    ("site-a", "c1" * 20): _TAR_V1,
    ("site-a", "v1.0.0"): _TAR_V1,
    ("site-a", "c2" * 20): _TAR_V2,
    ("site-a", "v1.1.0"): _TAR_V2,
}

_REPOS = {
    "site-a": {"slug": "site-a", "name": "Site A", "description": "사이트 A 패키지"},
    "site-b": {"slug": "site-b", "name": "Site B", "description": None},
}


def _page(values: list) -> dict:
    return {
        "values": values,
        "size": len(values),
        "isLastPage": True,
        "start": 0,
        "limit": 100,
    }


def create_fake_app() -> FastAPI:
    app = FastAPI()
    base = f"/rest/api/1.0/projects/{PROJECT}/repos"

    @app.get(base)
    def list_repos():
        return _page(list(_REPOS.values()))

    @app.get(base + "/{slug}")
    def get_repo(slug: str):
        if slug not in _REPOS:
            raise HTTPException(404, "repo not found")
        return _REPOS[slug]

    @app.get(base + "/{slug}/tags")
    def list_tags(slug: str):
        return _page(_TAGS.get(slug, []))

    @app.get(base + "/{slug}/commits")
    def list_commits(slug: str, until: str | None = None, limit: int = 25):
        return _page(_COMMITS.get(slug, [])[:limit])

    @app.get(base + "/{slug}/commits/{commit_id}")
    def get_commit(slug: str, commit_id: str):
        for c in _COMMITS.get(slug, []):
            if c["id"] == commit_id or c["id"].startswith(commit_id):
                return c
        raise HTTPException(404, "commit not found")

    @app.get(base + "/{slug}/last-modified/{path:path}")
    def last_modified(slug: str, path: str, at: str | None = None):
        commits = _COMMITS.get(slug, [])
        commit = commits[0] if commits else {"authorTimestamp": 0}
        return {"files": {path: commit}, "latestCommit": commit}

    @app.get(base + "/{slug}/browse/{path:path}")
    def browse(slug: str, path: str, at: str | None = None, size: str | None = None):
        tar = _TAR_BY_REF.get((slug, at or ""))
        if tar is None:
            raise HTTPException(404, "file not found")
        return {"size": len(tar)}

    @app.get("/projects/{project}/repos/{slug}/raw/{path:path}")
    def raw(project: str, slug: str, path: str, at: str | None = None):
        tar = _TAR_BY_REF.get((slug, at or ""))
        if tar is None:
            raise HTTPException(404, "file not found")
        return Response(content=tar, media_type="application/x-tar")

    return app
