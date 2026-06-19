#!/usr/bin/env python3
"""실제 Bitbucket Server 에 대고 도는 라이브 스모크 테스트.

이 클라우드 세션은 사내 Bitbucket 에 네트워크로 닿지 못할 수 있으므로,
**사내망 안에서** 직접 실행하는 용도다. backend/.env 의 설정을 그대로 읽는다.

사용법:
    cd backend
    cp .env.example .env          # BITBUCKET_* 값 채우기
    python scripts/live_smoke.py                 # 사이트/버전 조회까지
    python scripts/live_smoke.py --download       # 첫 사이트 최신 tar 받기까지

읽기 전용이며(--download 도 받기만 함), 아무 것도 푸시/수정하지 않는다.
"""
from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

# backend/ 를 import 경로에 추가 (스크립트를 어디서 실행하든 동작).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.bitbucket import BitbucketClient, _ts  # noqa: E402
from app.config import get_settings  # noqa: E402


async def main(do_download: bool) -> int:
    settings = get_settings()
    print(f"→ Bitbucket: {settings.bitbucket_base_url}  project={settings.bitbucket_project_key}")
    if settings.bitbucket_token in ("", "changeme"):
        print("✗ BITBUCKET_TOKEN 이 설정되지 않았습니다 (.env 확인).")
        return 2

    bb = BitbucketClient(settings)
    try:
        repos = await bb.list_repos()
        print(f"✓ repos: {len(repos)}개")
        if not repos:
            print("  (프로젝트에 repo 가 없습니다)")
            return 0

        slug = repos[0]["slug"]
        print(f"→ 첫 사이트 '{slug}' 의 태그 조회")
        tags = await bb.list_tags(slug)
        print(f"✓ tags: {len(tags)}개  {[t['displayId'] for t in tags[:5]]}")

        if tags:
            latest = tags[0]
            commit = await bb.get_commit(slug, latest["latestCommit"])
            print(
                f"✓ 최신 '{latest['displayId']}' 커밋 {commit.get('displayId')} "
                f"by {(commit.get('author') or {}).get('name')} "
                f"@ {_ts(commit.get('authorTimestamp'))}"
            )
            size = await bb.file_size(slug, settings.package_tar_path, at=latest["latestCommit"])
            print(f"  {settings.package_tar_path} 크기: {size} bytes")

            if do_download:
                print(f"→ '{latest['displayId']}' tar 다운로드 시도")
                total = 0
                async with await bb.raw_stream(
                    slug, settings.package_tar_path, at=latest["displayId"]
                ) as resp:
                    resp.raise_for_status()
                    async for chunk in resp.aiter_bytes():
                        total += len(chunk)
                print(f"✓ 다운로드 OK: {total} bytes")

        print("\n모든 스모크 체크 통과 ✅")
        return 0
    finally:
        await bb.aclose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bitbucket 라이브 스모크 테스트")
    parser.add_argument("--download", action="store_true", help="첫 사이트 최신 tar 까지 받아본다")
    args = parser.parse_args()
    raise SystemExit(asyncio.run(main(args.download)))
