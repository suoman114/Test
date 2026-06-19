"""FastAPI 의존성: 요청 단위로 Bitbucket 클라이언트를 제공한다."""
from collections.abc import AsyncIterator

import httpx
from fastapi import Depends

from .bitbucket import BitbucketClient
from .config import Settings, get_settings

# 테스트에서 가짜 Bitbucket(ASGI) transport 를 끼우기 위한 전역 훅.
# 운영에서는 None → 실제 네트워크. build_client 가 호출 시점에 읽는다.
_test_transport: httpx.AsyncBaseTransport | None = None


def build_client(settings: Settings) -> BitbucketClient:
    """BitbucketClient 를 생성한다.

    요청-스코프 의존성(get_bitbucket)과, 스트리밍 다운로드처럼 응답 반환 이후까지
    살아 있어야 하는 경로가 모두 이 함수를 거치므로 테스트 transport 가 일관 적용된다.
    """
    return BitbucketClient(settings, transport=_test_transport)


async def get_bitbucket(
    settings: Settings = Depends(get_settings),
) -> AsyncIterator[BitbucketClient]:
    client = build_client(settings)
    try:
        yield client
    finally:
        await client.aclose()
