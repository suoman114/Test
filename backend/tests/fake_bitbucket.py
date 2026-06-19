"""테스트용 가짜 Bitbucket Server (REST API 1.0) — 실제 구조 반영.

repo 1개 안에 tar 가 여러 개(루트 + 하위 폴더), 버전은 파일별 커밋 이력.

site-a 구조:
  /ansible.tar.gz        (size 100)  커밋 c2(최신) c1
  /README.md             (패키지 아님)
  /sub/                   (디렉토리)
      bash_vcs.tgz       (size 50)   커밋 c3
"""
from __future__ import annotations

from fastapi import FastAPI, HTTPException, Response, Request

PROJECT = "PKG"

_REPOS = {
    "site-a": {"slug": "site-a", "name": "Site A", "description": "사이트 A"},
    "site-b": {"slug": "site-b", "name": "Site B", "description": None},
}

# 디렉토리별 자식 목록 (key = 디렉토리 경로, "" = 루트)
_TREE: dict[str, dict[str, list]] = {
    "site-a": {
        "": [
            {"path": {"name": "ansible.tar.gz", "toString": "ansible.tar.gz"},
             "type": "FILE", "size": 100},
            {"path": {"name": "README.md", "toString": "README.md"},
             "type": "FILE", "size": 10},
            {"path": {"name": "sub", "toString": "sub"}, "type": "DIRECTORY"},
        ],
        "sub": [
            {"path": {"name": "bash_vcs.tgz", "toString": "sub/bash_vcs.tgz"},
             "type": "FILE", "size": 50},
        ],
    },
    "site-b": {"": []},
}

def _commit(cid, msg, author, ts):
    return {"id": cid * 8, "displayId": cid + "0000", "message": msg,
            "author": {"name": author, "emailAddress": f"{author}@corp"},
            "authorTimestamp": ts}

# 파일 경로별 커밋 이력 (최신순)
_COMMITS_BY_PATH = {
    "site-a": {
        "ansible.tar.gz": [
            _commit("c2", "update ansible", "alice", 1_700_000_200_000),
            _commit("c1", "init ansible", "bob", 1_700_000_100_000),
        ],
        "sub/bash_vcs.tgz": [
            _commit("c3", "add bash_vcs", "carol", 1_700_000_300_000),
        ],
    }
}

# (slug, path) -> 파일 바이트
_RAW = {
    ("site-a", "ansible.tar.gz"): b"ANSIBLE-TAR-CONTENT",
    ("site-a", "sub/bash_vcs.tgz"): b"BASHVCS",
}


def _page(values: list) -> dict:
    return {"values": values, "size": len(values), "isLastPage": True,
            "start": 0, "limit": 1000}


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

    @app.get(base + "/{slug}/commits")
    def commits(slug: str, path: str | None = None, until: str | None = None,
                limit: int = 25):
        hist = _COMMITS_BY_PATH.get(slug, {})
        if path is not None:
            return _page(hist.get(path, [])[:limit])
        # 경로 없이 호출되면 전체(여기선 사용 안 함)
        allc = [c for cs in hist.values() for c in cs]
        return _page(allc[:limit])

    # browse 루트와 하위 경로 둘 다 처리
    @app.get(base + "/{slug}/browse")
    @app.get(base + "/{slug}/browse/{path:path}")
    def browse(slug: str, path: str = "", at: str | None = None,
               start: int = 0, limit: int = 1000):
        tree = _TREE.get(slug, {})
        if path not in tree:
            raise HTTPException(404, "path not found")
        return {"children": _page(tree[path])}

    @app.get("/projects/{project}/repos/{slug}/raw/{path:path}")
    def raw(project: str, slug: str, path: str, at: str | None = None):
        data = _RAW.get((slug, path))
        if data is None:
            raise HTTPException(404, "file not found")
        return Response(content=data, media_type="application/octet-stream")

    return app
