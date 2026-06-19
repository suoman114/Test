"""FastAPI 의존성: 요청 단위로 Bitbucket 클라이언트를 제공한다."""
from collections.abc import AsyncIterator

from fastapi import Depends

from .bitbucket import BitbucketClient
from .config import Settings, get_settings


async def get_bitbucket(
    settings: Settings = Depends(get_settings),
) -> AsyncIterator[BitbucketClient]:
    client = BitbucketClient(settings)
    try:
        yield client
    finally:
        await client.aclose()
