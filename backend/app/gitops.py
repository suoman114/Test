"""git 기반 버전 발행(publish) 유틸.

업로드된 tar 를 받아 사이트 repo 를 임시로 clone → tar 를 고정 경로에 쓰고
commit → annotated tag 생성 → branch/tag push 한다.

GitPython 의존성 없이 stdlib subprocess 로 git 을 직접 호출한다.
인증은 Bitbucket Server Personal Access Token 을 Bearer 헤더로 주입한다
(`-c http.extraHeader=Authorization: Bearer <token>`).
"""
from __future__ import annotations

import base64
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from .config import Settings
from .schemas import Version


class GitPublishError(RuntimeError):
    """git 작업 실패 시 raise. stderr 를 함께 담는다."""


def _auth_header(settings: Settings) -> tuple[str, str]:
    """git HTTP 요청에 넣을 Authorization 헤더 값과, 로그에서 가릴 비밀값을 만든다.

    REST 클라이언트와 동일한 규칙: username/password 가 있으면 Basic, 아니면 Bearer.
    """
    if settings.use_basic_auth:
        raw = f"{settings.bitbucket_username}:{settings.bitbucket_password}"
        b64 = base64.b64encode(raw.encode()).decode()
        return f"Authorization: Basic {b64}", settings.bitbucket_password
    return f"Authorization: Bearer {settings.bitbucket_token}", settings.bitbucket_token


def _run(
    args: list[str], cwd: str | None, auth_header: str, secret: str
) -> subprocess.CompletedProcess:
    """git 명령을 실행한다.

    인증을 Authorization 헤더로 주입하고, 실패 시 stderr 를 포함한 예외를 던진다.
    비밀값은 URL 이 아닌 헤더로만 들어가므로 process 인자에 평문 노출되지 않는다.
    """
    # `-c http.extraHeader=...` 는 모든 git HTTP 요청에 헤더를 추가한다.
    cmd = ["git", "-c", f"http.extraHeader={auth_header}", *args]
    proc = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        # 비밀값이 stderr 에 섞여 새지 않도록 마스킹.
        stderr = (proc.stderr or "").replace(secret, "***") if secret else (proc.stderr or "")
        raise GitPublishError(
            f"git {' '.join(args)} 실패 (exit {proc.returncode}): {stderr.strip()}"
        )
    return proc


def publish_version(
    settings: Settings,
    slug: str,
    version: str,
    tar_bytes: bytes,
    message: str | None = None,
    author_name: str | None = None,
    author_email: str | None = None,
) -> Version:
    """tar 를 새 버전(git tag)으로 발행한다.

    절차:
      1. 임시 디렉토리에 repo 를 clone (HTTPS + Bearer 토큰)
      2. tar_bytes 를 settings.package_tar_path 에 기록
      3. git add / commit (지정 author·message)
      4. annotated tag(=version) 생성
      5. branch + tag push
      6. 임시 디렉토리 정리 (finally)

    실패 시 GitPublishError 를 raise 한다.
    반환값은 생성된 버전을 표현하는 Version 스키마.
    """
    base = settings.bitbucket_base_url.rstrip("/")
    project = settings.bitbucket_project_key
    auth_header, secret = _auth_header(settings)
    # Bitbucket Server git HTTP URL: {base}/scm/{PROJECT_KEY}/{slug}.git
    clone_url = f"{base}/scm/{project}/{slug}.git"

    commit_message = message or f"Publish {version}"
    name = author_name or "PKG Dashboard"
    email = author_email or "pkg-dashboard@localhost"

    tmpdir = tempfile.mkdtemp(prefix=f"pkg-{slug}-")
    try:
        # 1. clone (depth=1 로 가볍게)
        _run(
            ["clone", "--depth", "1", clone_url, tmpdir],
            cwd=None,
            auth_header=auth_header, secret=secret,
        )

        # commit author/committer 환경값을 git config 로 고정.
        _run(["config", "user.name", name], cwd=tmpdir, auth_header=auth_header, secret=secret)
        _run(["config", "user.email", email], cwd=tmpdir, auth_header=auth_header, secret=secret)

        # 현재 브랜치명 확인 (push 시 사용).
        branch = _run(
            ["rev-parse", "--abbrev-ref", "HEAD"],
            cwd=tmpdir,
            auth_header=auth_header, secret=secret,
        ).stdout.strip() or "main"

        # 2. tar 기록 (중간 디렉토리 생성).
        tar_path = Path(tmpdir) / settings.package_tar_path
        tar_path.parent.mkdir(parents=True, exist_ok=True)
        tar_path.write_bytes(tar_bytes)

        # 3. add + commit
        _run(["add", settings.package_tar_path], cwd=tmpdir, auth_header=auth_header, secret=secret)
        _run(["commit", "-m", commit_message], cwd=tmpdir, auth_header=auth_header, secret=secret)

        # 4. annotated tag
        _run(
            ["tag", "-a", version, "-m", commit_message],
            cwd=tmpdir,
            auth_header=auth_header, secret=secret,
        )

        # 5. push branch + tag
        _run(["push", "origin", branch], cwd=tmpdir, auth_header=auth_header, secret=secret)
        _run(["push", "origin", version], cwd=tmpdir, auth_header=auth_header, secret=secret)

        # 새로 만든 커밋 해시.
        commit_id = _run(
            ["rev-parse", "HEAD"],
            cwd=tmpdir,
            auth_header=auth_header, secret=secret,
        ).stdout.strip()

        return Version(
            name=version,
            commit_id=commit_id,
            message=commit_message,
            author=name,
            created_at=datetime.now(tz=timezone.utc),
            size_bytes=len(tar_bytes),
        )
    finally:
        # 6. 임시 디렉토리 정리.
        shutil.rmtree(tmpdir, ignore_errors=True)


__all__ = ["publish_version", "GitPublishError"]
