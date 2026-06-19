"""통합 테스트 픽스처.

우리 FastAPI 앱(app.main)을 TestClient 로 띄우되, Bitbucket 클라이언트의
HTTP transport 를 가짜 Bitbucket(ASGI) 으로 갈아끼운다. 감사 로그 SQLite 는
임시 파일로 격리한다.
"""
from __future__ import annotations

from collections.abc import Iterator

import httpx
import pytest
from fastapi.testclient import TestClient

from app import db
from app import deps as deps_mod
from app.config import Settings, get_settings
from app.main import app

from .fake_bitbucket import PROJECT, create_fake_app


@pytest.fixture
def test_settings() -> Settings:
    return Settings(
        bitbucket_base_url="http://bitbucket.test",
        bitbucket_project_key=PROJECT,
        bitbucket_token="test-token",
        package_tar_path="package.tar",
        repo_slug_filter="",
        cors_origins="http://localhost:3000",
    )


@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch) -> Iterator[None]:
    """감사 로그 DB 를 테스트마다 임시 경로로 격리."""
    monkeypatch.setattr(db, "_DATA_DIR", tmp_path)
    monkeypatch.setattr(db, "_DB_PATH", tmp_path / "audit.db")
    monkeypatch.setattr(db, "_initialized", False)
    yield


@pytest.fixture
def client(test_settings, monkeypatch) -> Iterator[TestClient]:
    fake = create_fake_app()
    transport = httpx.ASGITransport(app=fake)

    # 모든 클라이언트 생성 경로(build_client)가 가짜 transport 를 쓰도록 주입.
    monkeypatch.setattr(deps_mod, "_test_transport", transport)
    app.dependency_overrides[get_settings] = lambda: test_settings
    try:
        with TestClient(app) as c:
            yield c
    finally:
        app.dependency_overrides.clear()
